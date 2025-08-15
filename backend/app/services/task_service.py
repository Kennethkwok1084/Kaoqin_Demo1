"""
任务管理业务逻辑服务
处理任务的业务逻辑，包括工时计算、状态管理、标签处理等
集成新的考勤规则和工时计算逻辑
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from sqlalchemy import and_, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

from app.models.member import Member
from app.models.task import (
    AssistanceTask,
    MonitoringTask,
    RepairTask,
    TaskCategory,
    TaskPriority,
    TaskStatus,
    TaskTag,
    TaskTagType,
    TaskType,
    task_tag_association,
)
from app.services.work_hours_service import (
    RushTaskMarkingService,
    WorkHoursCalculationService,
)

logger = logging.getLogger(__name__)


class TaskService:
    """任务管理服务"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.work_hours_service = WorkHoursCalculationService(db)
        self.rush_task_service = RushTaskMarkingService(db)

    async def create_repair_task(
        self, task_data: Dict[str, Any], creator_id: int
    ) -> RepairTask:
        """
        创建维修任务

        Args:
            task_data: 任务数据
            creator_id: 创建者ID

        Returns:
            RepairTask: 创建的任务
        """
        try:
            # 生成任务编号
            task_id = await self._generate_task_id()

            # 创建任务
            task = RepairTask(
                task_id=task_id,
                title=task_data["title"],
                description=task_data.get("description"),
                category=task_data.get("category", TaskCategory.NETWORK_REPAIR),
                priority=task_data.get("priority", TaskPriority.MEDIUM),
                task_type=task_data.get("task_type", TaskType.ONLINE),
                status=task_data.get("status", TaskStatus.PENDING),
                location=task_data.get("location"),
                member_id=task_data.get("assigned_to"),
                report_time=task_data.get("report_time", datetime.utcnow()),
                response_time=task_data.get("response_time"),
                completion_time=task_data.get("completion_time"),
                due_date=task_data.get("due_date"),
                reporter_name=task_data.get("reporter_name"),
                reporter_contact=task_data.get("reporter_contact"),
                rating=task_data.get("rating"),
                feedback=task_data.get("feedback"),
                repair_form=task_data.get("repair_form"),
                work_order_status=task_data.get("work_order_status"),
                is_rush_order=task_data.get("is_rush_order", False),
            )

            # 设置基础工时
            task.base_work_minutes = task.get_base_work_minutes()

            self.db.add(task)
            await self.db.flush()

            # 添加标签
            if "tag_ids" in task_data and task_data["tag_ids"]:
                await self._add_tags_to_task(task, task_data["tag_ids"])

            # 如果是紧急任务，添加紧急标签
            if task_data.get("is_rush", False) or task_data.get("is_rush_order", False):
                await self._add_rush_tag(task)

            # 自动检测并添加异常扣时标签
            await self._auto_add_penalty_tags(task, task_data)

            # 自动检测并添加奖励标签
            await self._auto_add_bonus_tags(task, task_data)

            # 不在创建时计算工时，因为标签关系还未正确加载
            # 工时计算将在后续操作中进行

            await self.db.commit()
            await self.db.refresh(task)

            logger.info(f"Repair task created: {task.task_id}")
            return task

        except Exception as e:
            await self.db.rollback()
            logger.error(f"Create repair task error: {str(e)}")
            raise

    async def create_monitoring_task(
        self, task_data: Dict[str, Any], creator_id: int
    ) -> MonitoringTask:
        """
        创建监控任务（手动登记）

        Args:
            task_data: 任务数据，包含title, description, location, monitoring_type,
                      start_time, end_time, member_id等
            creator_id: 创建者ID

        Returns:
            MonitoringTask: 创建的监控任务
        """
        try:
            # 验证时间范围
            start_time = task_data["start_time"]
            end_time = task_data["end_time"]

            if end_time <= start_time:
                raise ValueError("结束时间必须晚于开始时间")

            # 计算工作时长
            duration = end_time - start_time
            work_minutes = int(duration.total_seconds() / 60)

            if work_minutes <= 0:
                raise ValueError("工作时长必须大于0")

            # 创建监控任务
            task = MonitoringTask(
                member_id=task_data["member_id"],
                title=task_data["title"],
                description=task_data.get("description"),
                location=task_data.get("location"),
                monitoring_type=task_data.get("monitoring_type", "巡检"),
                start_time=start_time,
                end_time=end_time,
                work_minutes=work_minutes,
                status=TaskStatus.COMPLETED,  # 监控任务创建时即为完成状态
            )

            self.db.add(task)
            await self.db.commit()
            await self.db.refresh(task)

            # 更新对应成员的月度工时汇总
            await self.work_hours_service.update_monthly_summary(
                task.member_id, start_time.year, start_time.month
            )

            logger.info(
                f"Monitoring task created: {task.id}, work_minutes: {work_minutes}"
            )
            return task

        except Exception as e:
            await self.db.rollback()
            logger.error(f"Create monitoring task error: {str(e)}")
            raise

    async def create_assistance_task(
        self, task_data: Dict[str, Any], creator_id: int
    ) -> AssistanceTask:
        """
        创建协助任务

        Args:
            task_data: 任务数据
            creator_id: 创建者ID

        Returns:
            AssistanceTask: 创建的协助任务
        """
        try:
            # 验证时间范围
            start_time = task_data["start_time"]
            end_time = task_data["end_time"]

            if end_time <= start_time:
                raise ValueError("结束时间必须晚于开始时间")

            # 计算工作时长
            duration = end_time - start_time
            work_minutes = int(duration.total_seconds() / 60)

            # 特殊处理：推文更新任务固定4小时
            if task_data.get("assistance_type") == "推文更新":
                work_minutes = 240  # 4小时 = 240分钟

            # 创建协助任务
            task = AssistanceTask(
                member_id=task_data["member_id"],
                title=task_data["title"],
                description=task_data.get("description"),
                assisted_department=task_data.get("assisted_department"),
                assisted_person=task_data.get("assisted_person"),
                start_time=start_time,
                end_time=end_time,
                work_minutes=work_minutes,
                status=TaskStatus.COMPLETED,
            )

            self.db.add(task)
            await self.db.commit()
            await self.db.refresh(task)

            # 更新对应成员的月度工时汇总
            await self.work_hours_service.update_monthly_summary(
                task.member_id, start_time.year, start_time.month
            )

            logger.info(
                f"Assistance task created: {task.id}, work_minutes: {work_minutes}"
            )
            return task

        except Exception as e:
            await self.db.rollback()
            logger.error(f"Create assistance task error: {str(e)}")
            raise

    async def update_task_status(
        self,
        task_id: int,
        new_status: TaskStatus,
        user_id: int,
        completion_note: Optional[str] = None,
        actual_minutes: Optional[int] = None,
    ) -> RepairTask:
        """
        更新任务状态

        Args:
            task_id: 任务ID
            new_status: 新状态
            user_id: 操作用户ID
            completion_note: 完成备注
            actual_minutes: 实际工时

        Returns:
            RepairTask: 更新后的任务
        """
        try:
            # 查询任务
            query = (
                select(RepairTask)
                .options(selectinload(RepairTask.tags))
                .where(RepairTask.id == task_id)
            )

            result = await self.db.execute(query)
            task = result.scalar_one_or_none()

            if not task:
                raise ValueError("任务不存在")

            old_status = task.status

            # 验证状态转换
            if not self._is_valid_status_transition(old_status, new_status):
                raise ValueError(
                    f"不能从 {old_status.value} 状态转换到 {new_status.value} 状态"
                )

            # 更新状态
            task.status = new_status

            # 更新时间戳
            if new_status == TaskStatus.IN_PROGRESS and not task.response_time:
                task.response_time = datetime.utcnow()
                # 检查是否延迟响应
                if await self._is_late_response(task):
                    await self._add_penalty_tag(task, "延迟响应", -30)

            elif new_status == TaskStatus.COMPLETED:
                if not task.completion_time:
                    task.completion_time = datetime.utcnow()

                # 检查是否延迟完成
                if await self._is_late_completion(task):
                    await self._add_penalty_tag(task, "延迟完成", -30)

                # 记录实际工时（用于分析对比）
                if actual_minutes is not None:
                    # 可以在这里记录实际工时与预估工时的差异
                    pass

            # 添加备注
            if completion_note:
                if task.description:
                    task.description += (
                        f"\n\n{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - "
                        f"{completion_note}"
                    )
                else:
                    task.description = completion_note

            # 重新计算工时
            task.update_work_minutes()

            await self.db.commit()
            await self.db.refresh(task)

            logger.info(
                f"Task {task_id} status updated from {old_status.value} to {new_status.value}"
            )
            return task

        except Exception as e:
            await self.db.rollback()
            logger.error(f"Update task status error: {str(e)}")
            raise

    async def assign_task(
        self,
        task_id: int,
        assigned_to: int,
        assigner_id: int,
        assignment_note: Optional[str] = None,
    ) -> RepairTask:
        """
        分配任务

        Args:
            task_id: 任务ID
            assigned_to: 分配给的成员ID
            assigner_id: 分配者ID
            assignment_note: 分配备注

        Returns:
            RepairTask: 更新后的任务
        """
        try:
            # 查询任务
            query = select(RepairTask).where(RepairTask.id == task_id)
            result = await self.db.execute(query)
            task = result.scalar_one_or_none()

            if not task:
                raise ValueError("任务不存在")

            # 验证目标成员
            member_query = select(Member).where(Member.id == assigned_to)
            member_result = await self.db.execute(member_query)
            member = member_result.scalar_one_or_none()

            if not member or not member.is_active:
                raise ValueError("指定的成员不存在或已被禁用")

            # 更新分配
            old_member_id = task.member_id
            task.member_id = assigned_to

            # 添加分配记录
            if assignment_note:
                assignment_log = (
                    f"\n\n{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - "
                    f"任务分配：{assignment_note}"
                )
                if task.description:
                    task.description += assignment_log
                else:
                    task.description = assignment_note

            await self.db.commit()
            await self.db.refresh(task)

            logger.info(
                f"Task {task_id} assigned from {old_member_id} to {assigned_to}"
            )
            return task

        except Exception as e:
            await self.db.rollback()
            logger.error(f"Assign task error: {str(e)}")
            raise

    async def add_task_feedback(
        self, task_id: int, rating: int, feedback: Optional[str] = None
    ) -> RepairTask:
        """
        添加任务反馈

        Args:
            task_id: 任务ID
            rating: 评分 (1-5)
            feedback: 反馈内容

        Returns:
            RepairTask: 更新后的任务
        """
        try:
            # 查询任务
            query = (
                select(RepairTask)
                .options(selectinload(RepairTask.tags))
                .where(RepairTask.id == task_id)
            )

            result = await self.db.execute(query)
            task = result.scalar_one_or_none()

            if not task:
                raise ValueError("任务不存在")

            # 更新评分和反馈
            task.rating = rating
            task.feedback = feedback

            # 根据评分添加相应标签
            if rating <= 2:
                # 差评惩罚
                await self._add_penalty_tag(task, "差评", -60)
            elif rating >= 4 and feedback and not self._is_default_feedback(feedback):
                # 非默认好评奖励
                await self._add_bonus_tag(task, "非默认好评", 30)

            # 重新计算工时
            task.update_work_minutes()

            await self.db.commit()
            await self.db.refresh(task)

            logger.info(f"Feedback added to task {task_id}: rating={rating}")
            return task

        except Exception as e:
            await self.db.rollback()
            logger.error(f"Add task feedback error: {str(e)}")
            raise

    async def get_member_task_summary(
        self,
        member_id: int,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """
        获取成员任务汇总

        Args:
            member_id: 成员ID
            date_from: 开始时间
            date_to: 结束时间

        Returns:
            Dict: 任务汇总数据
        """
        try:
            # 构建基础查询
            base_query = select(RepairTask).where(RepairTask.member_id == member_id)

            if date_from:
                base_query = base_query.where(RepairTask.report_time >= date_from)
            if date_to:
                base_query = base_query.where(RepairTask.report_time <= date_to)

            # 获取所有任务
            result = await self.db.execute(base_query)
            tasks = result.scalars().all()

            # 统计计算
            total_tasks = len(tasks)
            completed_tasks = len(
                [t for t in tasks if t.status == TaskStatus.COMPLETED]
            )
            pending_tasks = len([t for t in tasks if t.status == TaskStatus.PENDING])
            in_progress_tasks = len(
                [t for t in tasks if t.status == TaskStatus.IN_PROGRESS]
            )

            total_work_minutes = sum(t.work_minutes for t in tasks)
            total_work_hours = round(total_work_minutes / 60.0, 2)

            # 类型分布
            online_tasks = len([t for t in tasks if t.task_type == TaskType.ONLINE])
            offline_tasks = len([t for t in tasks if t.task_type == TaskType.OFFLINE])

            # 评分统计
            rated_tasks = [t for t in tasks if t.rating is not None]
            avg_rating = 0.0
            if rated_tasks:
                avg_rating = round(
                    sum(t.rating for t in rated_tasks) / len(rated_tasks), 2
                )

            # 延迟统计
            overdue_response = len([t for t in tasks if t.is_overdue_response])
            overdue_completion = len([t for t in tasks if t.is_overdue_completion])

            return {
                "member_id": member_id,
                "period": {
                    "from": date_from.isoformat() if date_from else None,
                    "to": date_to.isoformat() if date_to else None,
                },
                "task_counts": {
                    "total": total_tasks,
                    "completed": completed_tasks,
                    "pending": pending_tasks,
                    "in_progress": in_progress_tasks,
                },
                "work_hours": {
                    "total_minutes": total_work_minutes,
                    "total_hours": total_work_hours,
                },
                "task_types": {"online": online_tasks, "offline": offline_tasks},
                "quality": {
                    "avg_rating": avg_rating,
                    "rated_tasks": len(rated_tasks),
                    "overdue_response": overdue_response,
                    "overdue_completion": overdue_completion,
                },
            }

        except Exception as e:
            logger.error(f"Get member task summary error: {str(e)}")
            raise

    # 爆单管理功能（重构新增）

    async def batch_mark_rush_tasks(
        self,
        date_from: datetime,
        date_to: datetime,
        task_ids: Optional[List[int]] = None,
        marker_id: int = None,
    ) -> Dict[str, Any]:
        """
        批量标记爆单任务

        Args:
            date_from: 开始时间
            date_to: 结束时间
            task_ids: 指定任务ID列表
            marker_id: 标记人ID

        Returns:
            Dict: 标记结果
        """
        try:
            result = await self.rush_task_service.mark_rush_tasks_by_date(
                date_from.date(), date_to.date(), task_ids, marker_id
            )

            # 记录操作日志
            logger.info(f"Batch rush task marking by user {marker_id}: {result}")

            return {
                "success": True,
                "marked_count": result["marked"],
                "updated_count": result.get("updated", 0),
                "total_count": result["total"],
                "period": {"from": date_from.isoformat(), "to": date_to.isoformat()},
                "marked_by": marker_id,
            }

        except Exception as e:
            logger.error(f"Batch mark rush tasks error: {str(e)}")
            raise

    async def get_rush_tasks_list(
        self,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        member_id: Optional[int] = None,
        page: int = 1,
        page_size: int = 50,
    ) -> Dict[str, Any]:
        """
        获取爆单任务列表

        Args:
            date_from: 开始时间
            date_to: 结束时间
            member_id: 成员ID筛选
            page: 页码
            page_size: 每页大小

        Returns:
            Dict: 爆单任务列表和统计
        """
        try:
            # 构建查询
            query = (
                select(RepairTask)
                .options(selectinload(RepairTask.tags), joinedload(RepairTask.member))
                .where(RepairTask.is_rush_order)
            )

            if date_from:
                query = query.where(RepairTask.report_time >= date_from)
            if date_to:
                query = query.where(RepairTask.report_time <= date_to)
            if member_id:
                query = query.where(RepairTask.member_id == member_id)

            # 获取总数
            count_query = select(func.count()).select_from(query.subquery())
            count_result = await self.db.execute(count_query)
            total = count_result.scalar()

            # 分页查询
            offset = (page - 1) * page_size
            query = (
                query.order_by(desc(RepairTask.report_time))
                .limit(page_size)
                .offset(offset)
            )

            result = await self.db.execute(query)
            tasks = result.scalars().all()

            # 转换为字典格式
            task_list = []
            for task in tasks:
                task_data = {
                    "id": task.id,
                    "task_id": task.task_id,
                    "title": task.title,
                    "member": {"id": task.member.id, "name": task.member.name},
                    "task_type": task.task_type.value,
                    "status": task.status.value,
                    "report_time": task.report_time.isoformat(),
                    "work_minutes": task.work_minutes,
                    "is_rush_order": task.is_rush_order,
                    "rush_info": (
                        task.get_rush_order_info()
                        if hasattr(task, "get_rush_order_info")
                        else None
                    ),
                }
                task_list.append(task_data)

            # 计算统计信息
            total_work_minutes = sum(task.work_minutes for task in tasks)

            return {
                "tasks": task_list,
                "pagination": {
                    "page": page,
                    "page_size": page_size,
                    "total": total,
                    "pages": (total + page_size - 1) // page_size,
                },
                "statistics": {
                    "total_rush_tasks": total,
                    "current_page_count": len(tasks),
                    "total_work_hours": round(total_work_minutes / 60.0, 2),
                },
            }

        except Exception as e:
            logger.error(f"Get rush tasks list error: {str(e)}")
            raise

    async def get_rush_tasks_statistics(
        self, date_from: Optional[datetime] = None, date_to: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        获取爆单任务统计报表

        Args:
            date_from: 开始时间
            date_to: 结束时间

        Returns:
            Dict: 统计数据
        """
        try:
            # 构建基础查询
            base_query = (
                select(RepairTask)
                .options(joinedload(RepairTask.member))
                .where(RepairTask.is_rush_order)
            )

            if date_from:
                base_query = base_query.where(RepairTask.report_time >= date_from)
            if date_to:
                base_query = base_query.where(RepairTask.report_time <= date_to)

            result = await self.db.execute(base_query)
            rush_tasks = result.scalars().all()

            # 总体统计
            total_tasks = len(rush_tasks)
            total_work_minutes = sum(task.work_minutes for task in rush_tasks)
            total_work_hours = round(total_work_minutes / 60.0, 2)

            # 按状态统计
            status_stats = {}
            for status in TaskStatus:
                status_stats[status.value] = len(
                    [t for t in rush_tasks if t.status == status]
                )

            # 按任务类型统计
            type_stats = {
                "online": len(
                    [t for t in rush_tasks if t.task_type == TaskType.ONLINE]
                ),
                "offline": len(
                    [t for t in rush_tasks if t.task_type == TaskType.OFFLINE]
                ),
            }

            # 按成员统计
            member_stats = {}
            for task in rush_tasks:
                member_name = task.member.name
                if member_name not in member_stats:
                    member_stats[member_name] = {"task_count": 0, "work_minutes": 0}
                member_stats[member_name]["task_count"] += 1
                member_stats[member_name]["work_minutes"] += task.work_minutes

            # 转换为列表格式
            member_list = [
                {
                    "member_name": name,
                    "task_count": stats["task_count"],
                    "work_hours": round(stats["work_minutes"] / 60.0, 2),
                }
                for name, stats in member_stats.items()
            ]
            member_list.sort(key=lambda x: x["task_count"], reverse=True)

            # 按月份统计
            month_stats = {}
            for task in rush_tasks:
                month_key = task.report_time.strftime("%Y-%m")
                if month_key not in month_stats:
                    month_stats[month_key] = 0
                month_stats[month_key] += 1

            return {
                "period": {
                    "from": date_from.isoformat() if date_from else None,
                    "to": date_to.isoformat() if date_to else None,
                },
                "summary": {
                    "total_tasks": total_tasks,
                    "total_work_hours": total_work_hours,
                    "average_task_hours": (
                        round(total_work_hours / total_tasks, 2)
                        if total_tasks > 0
                        else 0
                    ),
                },
                "by_status": status_stats,
                "by_type": type_stats,
                "by_member": member_list,
                "by_month": month_stats,
            }

        except Exception as e:
            logger.error(f"Get rush tasks statistics error: {str(e)}")
            raise

    async def remove_rush_task_marking(
        self, task_ids: List[int], remover_id: int = None
    ) -> Dict[str, Any]:
        """
        移除爆单任务标记

        Args:
            task_ids: 任务ID列表
            remover_id: 操作人ID

        Returns:
            Dict: 操作结果
        """
        try:
            # 查询指定任务
            query = (
                select(RepairTask)
                .options(selectinload(RepairTask.tags))
                .where(RepairTask.id.in_(task_ids))
            )

            result = await self.db.execute(query)
            tasks = result.scalars().all()

            # 获取爆单标签
            rush_tag_query = select(TaskTag).where(
                and_(
                    TaskTag.tag_type == TaskTagType.RUSH_ORDER,
                    TaskTag.name == "爆单任务",
                )
            )
            rush_tag_result = await self.db.execute(rush_tag_query)
            rush_tag = rush_tag_result.scalar_one_or_none()

            removed_count = 0

            for task in tasks:
                if task.is_rush_order:
                    # 取消爆单标记
                    task.is_rush_order = False

                    # 移除爆单标签
                    if rush_tag and rush_tag in task.tags:
                        task.tags.remove(rush_tag)

                    # 重新计算工时
                    task.update_work_minutes()

                    removed_count += 1

            await self.db.commit()

            logger.info(
                f"Removed rush marking from {removed_count} tasks by user {remover_id}"
            )

            return {
                "success": True,
                "removed_count": removed_count,
                "total_count": len(tasks),
                "removed_by": remover_id,
            }

        except Exception as e:
            await self.db.rollback()
            logger.error(f"Remove rush task marking error: {str(e)}")
            raise

    # 私有方法

    async def _generate_task_id(self) -> str:
        """生成任务编号"""
        today = datetime.now().strftime("%Y%m%d")

        # 查询今天已有的任务数量
        count_query = select(func.count()).where(RepairTask.task_id.like(f"R{today}%"))
        count_result = await self.db.execute(count_query)
        count = count_result.scalar()

        return f"R{today}{str(count + 1).zfill(4)}"

    async def _add_tags_to_task(self, task: RepairTask, tag_ids: List[int]):
        """为任务添加标签"""
        if not tag_ids:
            return

        tag_query = select(TaskTag).where(TaskTag.id.in_(tag_ids))
        tag_result = await self.db.execute(tag_query)
        tags = tag_result.scalars().all()

        for tag in tags:
            if tag.is_active:
                task.tags.append(tag)

    async def _add_rush_tag(self, task: RepairTask):
        """添加紧急任务标签"""
        await self._add_bonus_tag(task, "紧急任务", 15)

    async def _add_bonus_tag(self, task: RepairTask, tag_name: str, bonus: int):
        """添加奖励标签"""
        tag = await self._get_or_create_tag(tag_name, bonus, "bonus")
        if tag not in task.tags:
            task.tags.append(tag)

    async def _add_penalty_tag(self, task: RepairTask, tag_name: str, penalty: int):
        """添加惩罚标签"""
        tag = await self._get_or_create_tag(tag_name, penalty, "penalty")
        if tag not in task.tags:
            task.tags.append(tag)

    async def _get_or_create_tag(
        self, name: str, modifier: int, tag_type: str
    ) -> TaskTag:
        """获取或创建标签"""
        tag_query = select(TaskTag).where(TaskTag.name == name)
        tag_result = await self.db.execute(tag_query)
        tag = tag_result.scalar_one_or_none()

        if not tag:
            tag = TaskTag(
                name=name,
                work_minutes_modifier=modifier,
                tag_type=tag_type,
                is_active=True,
            )
            self.db.add(tag)
            await self.db.flush()

        return tag

    def _is_valid_status_transition(
        self, old_status: TaskStatus, new_status: TaskStatus
    ) -> bool:
        """验证状态转换是否有效"""
        valid_transitions = {
            TaskStatus.PENDING: [TaskStatus.IN_PROGRESS, TaskStatus.CANCELLED],
            TaskStatus.IN_PROGRESS: [
                TaskStatus.COMPLETED,
                TaskStatus.ON_HOLD,
                TaskStatus.CANCELLED,
            ],
            TaskStatus.ON_HOLD: [TaskStatus.IN_PROGRESS, TaskStatus.CANCELLED],
            TaskStatus.COMPLETED: [],
            TaskStatus.CANCELLED: [],
        }

        return new_status in valid_transitions.get(old_status, [])

    async def _is_late_response(self, task: RepairTask) -> bool:
        """检查是否延迟响应"""
        if not task.response_time or not task.report_time:
            return False

        response_hours = (task.response_time - task.report_time).total_seconds() / 3600
        return response_hours > 24  # 超过24小时为延迟响应

    async def _is_late_completion(self, task: RepairTask) -> bool:
        """检查是否延迟完成"""
        if not task.completion_time or not task.response_time:
            return False

        completion_hours = (
            task.completion_time - task.response_time
        ).total_seconds() / 3600
        return completion_hours > 48  # 超过48小时为延迟完成

    def _is_default_feedback(self, feedback: str) -> bool:
        """检查是否为默认反馈"""
        if not feedback:
            return True

        default_keywords = ["系统默认好评", "默认", "自动好评", "满意"]
        feedback_lower = feedback.lower()
        return any(keyword in feedback_lower for keyword in default_keywords)

    async def _auto_add_penalty_tags(
        self, task: RepairTask, task_data: Dict[str, Any]
    ) -> None:
        """自动添加异常扣时标签"""
        try:
            report_time = task.report_time
            response_time = task.response_time
            completion_time = task.completion_time
            rating = task.rating

            # 检查响应超时 (>24小时)
            if report_time and response_time:
                response_hours = (response_time - report_time).total_seconds() / 3600
                if response_hours > 24:
                    await self._add_standard_tag(task, "超时响应")

            # 检查处理超时 (>48小时)
            if response_time and completion_time:
                processing_hours = (
                    completion_time - response_time
                ).total_seconds() / 3600
                if processing_hours > 48:
                    await self._add_standard_tag(task, "超时处理")

            # 检查差评 (≤2星)
            if rating is not None and rating <= 2:
                await self._add_standard_tag(task, "差评")

        except Exception as e:
            logger.warning(f"Error adding penalty tags to task {task.id}: {str(e)}")

    async def _auto_add_bonus_tags(
        self, task: RepairTask, task_data: Dict[str, Any]
    ) -> None:
        """自动添加奖励标签"""
        try:
            rating = task.rating
            feedback = task.feedback

            # 检查非默认好评 (≥4星且有非默认反馈)
            if rating is not None and rating >= 4 and feedback:
                if not self._is_default_feedback(feedback):
                    await self._add_standard_tag(task, "非默认好评")

        except Exception as e:
            logger.warning(f"Error adding bonus tags to task {task.id}: {str(e)}")

    async def _add_standard_tag(self, task: RepairTask, tag_name: str) -> None:
        """添加标准标签"""
        try:
            # 查找现有标签
            tag_query = select(TaskTag).where(TaskTag.name == tag_name)
            tag_result = await self.db.execute(tag_query)
            tag = tag_result.scalar_one_or_none()

            if not tag:
                # 创建标准标签
                if tag_name == "超时响应":
                    tag = TaskTag.create_timeout_response_tag()
                elif tag_name == "超时处理":
                    tag = TaskTag.create_timeout_processing_tag()
                elif tag_name == "差评":
                    tag = TaskTag.create_bad_rating_tag()
                elif tag_name == "非默认好评":
                    tag = TaskTag.create_non_default_rating_tag()
                else:
                    return

                self.db.add(tag)
                await self.db.flush()

            # 检查标签是否已存在
            existing_query = select(task_tag_association).where(
                and_(
                    task_tag_association.c.task_id == task.id,
                    task_tag_association.c.tag_id == tag.id,
                )
            )
            existing_result = await self.db.execute(existing_query)
            existing = existing_result.scalar_one_or_none()

            if not existing:
                # 添加标签关联
                from sqlalchemy import insert

                stmt = insert(task_tag_association).values(
                    task_id=task.id, tag_id=tag.id
                )
                await self.db.execute(stmt)
                logger.info(f"Added {tag_name} tag to task {task.id}")

        except Exception as e:
            logger.warning(
                f"Error adding standard tag {tag_name} to task {task.id}: {str(e)}"
            )


class MonitoringTaskService:
    """监控任务服务"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_monitoring_task(
        self,
        member_id: int,
        title: str,
        description: Optional[str] = None,
        location: Optional[str] = None,
        monitoring_type: str = "inspection",
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> MonitoringTask:
        """
        创建监控任务

        Args:
            member_id: 执行成员ID
            title: 任务标题
            description: 任务描述
            location: 监控地点
            monitoring_type: 监控类型
            start_time: 开始时间
            end_time: 结束时间

        Returns:
            MonitoringTask: 创建的监控任务
        """
        try:
            if not start_time:
                start_time = datetime.utcnow()
            if not end_time:
                end_time = start_time + timedelta(hours=1)  # 默认1小时

            task = MonitoringTask(
                member_id=member_id,
                title=title,
                description=description,
                location=location,
                monitoring_type=monitoring_type,
                start_time=start_time,
                end_time=end_time,
                status=TaskStatus.COMPLETED,
            )

            # 计算工时
            task.update_work_minutes()

            self.db.add(task)
            await self.db.commit()
            await self.db.refresh(task)

            logger.info(f"Monitoring task created for member {member_id}")
            return task

        except Exception as e:
            await self.db.rollback()
            logger.error(f"Create monitoring task error: {str(e)}")
            raise

    async def get_monitoring_summary(
        self,
        member_id: Optional[int] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """
        获取监控任务汇总

        Args:
            member_id: 成员ID
            date_from: 开始时间
            date_to: 结束时间

        Returns:
            Dict: 监控任务汇总
        """
        try:
            base_query = select(MonitoringTask)

            if member_id:
                base_query = base_query.where(MonitoringTask.member_id == member_id)
            if date_from:
                base_query = base_query.where(MonitoringTask.start_time >= date_from)
            if date_to:
                base_query = base_query.where(MonitoringTask.start_time <= date_to)

            result = await self.db.execute(base_query)
            tasks = result.scalars().all()

            total_tasks = len(tasks)
            total_work_minutes = sum(t.work_minutes for t in tasks)
            total_work_hours = round(total_work_minutes / 60.0, 2)

            # 按类型统计
            type_stats = {}
            for task in tasks:
                monitoring_type = task.monitoring_type
                if monitoring_type not in type_stats:
                    type_stats[monitoring_type] = 0
                type_stats[monitoring_type] += 1

            return {
                "total_tasks": total_tasks,
                "total_work_minutes": total_work_minutes,
                "total_work_hours": total_work_hours,
                "type_distribution": type_stats,
            }

        except Exception as e:
            logger.error(f"Get monitoring summary error: {str(e)}")
            raise


class AssistanceTaskService:
    """协助任务服务"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_assistance_task(
        self,
        member_id: int,
        title: str,
        description: Optional[str] = None,
        assisted_department: Optional[str] = None,
        assisted_person: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> AssistanceTask:
        """
        创建协助任务

        Args:
            member_id: 协助成员ID
            title: 任务标题
            description: 任务描述
            assisted_department: 被协助部门
            assisted_person: 被协助人员
            start_time: 开始时间
            end_time: 结束时间

        Returns:
            AssistanceTask: 创建的协助任务
        """
        try:
            if not start_time:
                start_time = datetime.utcnow()
            if not end_time:
                end_time = start_time + timedelta(hours=1)  # 默认1小时

            task = AssistanceTask(
                member_id=member_id,
                title=title,
                description=description,
                assisted_department=assisted_department,
                assisted_person=assisted_person,
                start_time=start_time,
                end_time=end_time,
                status=TaskStatus.COMPLETED,
            )

            # 计算工时
            task.update_work_minutes()

            self.db.add(task)
            await self.db.commit()
            await self.db.refresh(task)

            logger.info(f"Assistance task created for member {member_id}")
            return task

        except Exception as e:
            await self.db.rollback()
            logger.error(f"Create assistance task error: {str(e)}")
            raise

    async def get_assistance_summary(
        self,
        member_id: Optional[int] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """
        获取协助任务汇总

        Args:
            member_id: 成员ID
            date_from: 开始时间
            date_to: 结束时间

        Returns:
            Dict: 协助任务汇总
        """
        try:
            base_query = select(AssistanceTask)

            if member_id:
                base_query = base_query.where(AssistanceTask.member_id == member_id)
            if date_from:
                base_query = base_query.where(AssistanceTask.start_time >= date_from)
            if date_to:
                base_query = base_query.where(AssistanceTask.start_time <= date_to)

            result = await self.db.execute(base_query)
            tasks = result.scalars().all()

            total_tasks = len(tasks)
            total_work_minutes = sum(t.work_minutes for t in tasks)
            total_work_hours = round(total_work_minutes / 60.0, 2)

            # 按部门统计
            dept_stats = {}
            for task in tasks:
                dept = task.assisted_department or "未指定"
                if dept not in dept_stats:
                    dept_stats[dept] = 0
                dept_stats[dept] += 1

            return {
                "total_tasks": total_tasks,
                "total_work_minutes": total_work_minutes,
                "total_work_hours": total_work_hours,
                "department_distribution": dept_stats,
            }

        except Exception as e:
            logger.error(f"Get assistance summary error: {str(e)}")
            raise

    async def import_maintenance_orders(
        self,
        maintenance_data: List[Dict[str, Any]],
        importer_id: int,
        auto_match: bool = True,
    ) -> Dict[str, Any]:
        """
        批量导入维修单（支持A/B表匹配）

        Args:
            maintenance_data: 维修单数据列表
            importer_id: 导入者ID
            auto_match: 是否启用A/B表自动匹配

        Returns:
            Dict: 导入结果统计
        """
        try:
            import_batch_id = (
                f"import_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{importer_id}"
            )

            created_count = 0
            updated_count = 0
            matched_count = 0
            failed_count = 0
            errors = []

            # 如果启用自动匹配，先进行A/B表匹配
            if auto_match and len(maintenance_data) > 1:
                maintenance_data = await self._perform_ab_table_matching(
                    maintenance_data
                )
                matched_count = len(
                    [item for item in maintenance_data if item.get("_matched", False)]
                )

            for data in maintenance_data:
                try:
                    # 检查是否已存在相同工单
                    existing_task = await self._find_existing_task_by_work_order_id(
                        data.get("work_order_id")
                    )

                    if existing_task:
                        # 更新现有任务
                        await self._update_existing_maintenance_task(
                            existing_task, data
                        )
                        updated_count += 1
                    else:
                        # 创建新任务
                        await self._create_maintenance_task(
                            data, importer_id, import_batch_id
                        )
                        created_count += 1

                except Exception as e:
                    error_msg = (
                        f"导入工单 {data.get('work_order_id', 'N/A')} 失败: {str(e)}"
                    )
                    errors.append(error_msg)
                    failed_count += 1
                    logger.warning(error_msg)

            await self.db.commit()

            # 更新相关成员的月度工时汇总
            await self._update_monthly_summaries_for_import(maintenance_data)

            result = {
                "success": created_count + updated_count,
                "failed": failed_count,
                "created": created_count,
                "updated": updated_count,
                "matched": matched_count,
                "errors": errors,
                "import_batch_id": import_batch_id,
            }

            logger.info(f"Maintenance orders import completed: {result}")
            return result

        except Exception as e:
            await self.db.rollback()
            logger.error(f"Import maintenance orders error: {str(e)}")
            raise

    async def mark_rush_tasks(
        self,
        date_from: str,
        date_to: str,
        task_ids: Optional[List[int]] = None,
        marked_by: int = None,
    ) -> Dict[str, int]:
        """
        批量标记爆单任务

        Args:
            date_from: 开始日期
            date_to: 结束日期
            task_ids: 指定任务ID列表
            marked_by: 标记人ID

        Returns:
            Dict: 标记结果统计
        """
        try:
            from datetime import datetime

            # 转换日期格式
            start_date = datetime.strptime(date_from, "%Y-%m-%d").date()
            end_date = datetime.strptime(date_to, "%Y-%m-%d").date()

            result = await self.rush_task_service.mark_rush_tasks_by_date(
                start_date, end_date, task_ids, marked_by
            )

            # 更新影响的任务的工时
            if result["marked"] > 0:
                await self._recalculate_work_hours_for_marked_tasks(
                    start_date, end_date, task_ids
                )

            return result

        except Exception as e:
            logger.error(f"Mark rush tasks error: {str(e)}")
            raise

    # 私有方法 - A/B表匹配逻辑

    async def _perform_ab_table_matching(
        self, maintenance_data: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """执行A/B表匹配逻辑"""
        # 创建匹配索引：联系人+联系方式
        match_index = {}

        for i, data in enumerate(maintenance_data):
            contact_person = data.get("contact_person", "").strip()
            contact_phone = data.get("contact_phone", "").strip()

            if contact_person and contact_phone:
                match_key = f"{contact_person}_{contact_phone}"

                if match_key not in match_index:
                    match_index[match_key] = []
                match_index[match_key].append(i)

        # 执行匹配：相同匹配键的记录进行合并
        matched_data = []
        processed_indices = set()

        for match_key, indices in match_index.items():
            if len(indices) > 1:
                # 找到匹配的记录，进行合并
                primary_record = None
                secondary_records = []

                for idx in indices:
                    if idx in processed_indices:
                        continue

                    record = maintenance_data[idx]

                    # B表特征：有检修形式或处理说明
                    if record.get("solution") or record.get("processing_note"):
                        if not primary_record:
                            primary_record = record.copy()
                        else:
                            secondary_records.append(record)
                    else:
                        secondary_records.append(record)

                # 合并记录
                if primary_record:
                    for secondary in secondary_records:
                        primary_record = self._merge_maintenance_records(
                            primary_record, secondary
                        )

                    primary_record["_matched"] = True
                    matched_data.append(primary_record)
                    processed_indices.update(indices)
            else:
                # 单个记录，无法匹配
                idx = indices[0]
                if idx not in processed_indices:
                    record = maintenance_data[idx].copy()
                    record["_matched"] = False
                    # A表无B表匹配默认为线上任务
                    if not record.get("task_type"):
                        record["task_type"] = "online_repair"
                    matched_data.append(record)
                    processed_indices.add(idx)

        # 添加未处理的记录
        for i, data in enumerate(maintenance_data):
            if i not in processed_indices:
                record = data.copy()
                record["_matched"] = False
                if not record.get("task_type"):
                    record["task_type"] = "online_repair"
                matched_data.append(record)

        return matched_data

    def _merge_maintenance_records(
        self, primary: Dict[str, Any], secondary: Dict[str, Any]
    ) -> Dict[str, Any]:
        """合并维修记录（A/B表合并）"""
        merged = primary.copy()

        # 优先使用primary的技术信息，secondary的基础信息
        fields_to_merge = {
            "work_order_id": secondary.get("work_order_id")
            or primary.get("work_order_id"),
            "company": secondary.get("company") or primary.get("company"),
            "location": secondary.get("location") or primary.get("location"),
            "contact_person": secondary.get("contact_person")
            or primary.get("contact_person"),
            "contact_phone": secondary.get("contact_phone")
            or primary.get("contact_phone"),
            "report_time": secondary.get("report_time") or primary.get("report_time"),
            # 技术信息优先使用primary
            "solution": primary.get("solution") or secondary.get("solution"),
            "processing_note": primary.get("processing_note")
            or secondary.get("processing_note"),
            "assignee": primary.get("assignee") or secondary.get("assignee"),
            "actual_hours": primary.get("actual_hours")
            or secondary.get("actual_hours"),
        }

        merged.update({k: v for k, v in fields_to_merge.items() if v})

        # 根据检修形式判断任务类型
        if primary.get("type"):
            type_text = primary["type"].lower()
            if "线上" in type_text or "远程" in type_text:
                merged["task_type"] = "online_repair"
            elif "线下" in type_text or "现场" in type_text:
                merged["task_type"] = "offline_repair"

        return merged

    async def _find_existing_task_by_work_order_id(
        self, work_order_id: str
    ) -> Optional[RepairTask]:
        """根据工单编号查找现有任务"""
        if not work_order_id:
            return None

        query = select(RepairTask).where(RepairTask.task_id == work_order_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def _create_maintenance_task(
        self, data: Dict[str, Any], importer_id: int, batch_id: str
    ) -> RepairTask:
        """创建维修任务"""
        # 确定任务类型
        task_type = TaskType.ONLINE
        if data.get("task_type") == "offline_repair":
            task_type = TaskType.OFFLINE

        # 查找或创建成员
        member_id = await self._find_or_create_member_for_task(data)

        # 创建任务
        task = RepairTask(
            task_id=data.get("work_order_id", await self._generate_task_id()),
            title=data.get("title", "维修任务"),
            description=data.get("description", ""),
            location=data.get("location", ""),
            task_type=task_type,
            member_id=member_id,
            report_time=data.get("report_time", datetime.utcnow()),
            response_time=data.get("response_time"),
            completion_time=data.get("complete_time"),
            reporter_name=data.get("contact_person"),
            reporter_contact=data.get("contact_phone"),
            status=(
                TaskStatus.COMPLETED
                if data.get("complete_time")
                else TaskStatus.PENDING
            ),
            import_batch_id=batch_id,
            is_matched=data.get("_matched", False),
        )

        # 设置评价信息
        if data.get("customer_rating"):
            task.feedback = data.get("customer_rating")
        if data.get("satisfaction"):
            task.rating = int(data["satisfaction"])

        self.db.add(task)
        await self.db.flush()  # 获取任务ID

        # 添加标签
        await self._add_tags_for_maintenance_task(task, data)

        # 计算工时
        task.update_work_minutes()

        return task

    async def _find_or_create_member_for_task(self, data: Dict[str, Any]) -> int:
        """为任务查找或创建成员"""
        assignee = data.get("assignee")
        if not assignee:
            # 如果没有指定处理人，使用默认成员
            return 1

        # 根据姓名查找成员
        member_query = select(Member).where(Member.name == assignee)
        member_result = await self.db.execute(member_query)
        member = member_result.scalar_one_or_none()

        if member:
            return member.id
        else:
            # 创建临时成员（简化处理）
            return 1

    async def _add_tags_for_maintenance_task(
        self, task: RepairTask, data: Dict[str, Any]
    ):
        """为维修任务添加标签"""
        tags_to_add = []

        # 检查非默认好评
        if data.get("customer_rating") and data["customer_rating"] not in [
            "默认好评",
            "系统默认",
        ]:
            if data.get("satisfaction", 0) >= 4:
                tags_to_add.append("非默认好评")

        # 添加其他标签
        for tag_name in tags_to_add:
            tag = await self._get_or_create_tag(tag_name)
            if tag:
                task.tags.append(tag)

    async def _get_or_create_tag(self, tag_name: str) -> Optional[TaskTag]:
        """获取或创建标签"""
        query = select(TaskTag).where(TaskTag.name == tag_name)
        result = await self.db.execute(query)
        tag = result.scalar_one_or_none()

        if not tag:
            # 创建标签
            tag_configs = {
                "非默认好评": {"modifier": 30, "type": "bonus"},
                "爆单任务": {"modifier": 15, "type": "bonus"},
                "超时响应": {"modifier": -30, "type": "penalty"},
                "超时处理": {"modifier": -30, "type": "penalty"},
                "差评任务": {"modifier": -60, "type": "penalty"},
            }

            if tag_name in tag_configs:
                config = tag_configs[tag_name]
                tag = TaskTag(
                    name=tag_name,
                    description=f"自动创建的{tag_name}标签",
                    work_minutes_modifier=config["modifier"],
                    tag_type=config["type"],
                    is_active=True,
                )
                self.db.add(tag)
                await self.db.flush()

        return tag

    async def _update_existing_maintenance_task(
        self, task: RepairTask, data: Dict[str, Any]
    ):
        """更新现有维修任务"""
        # 更新基本信息
        if data.get("description"):
            task.description = data["description"]
        if data.get("location"):
            task.location = data["location"]
        if data.get("complete_time"):
            task.completion_time = data["complete_time"]
            task.status = TaskStatus.COMPLETED

        # 更新评价信息
        if data.get("customer_rating"):
            task.feedback = data["customer_rating"]
        if data.get("satisfaction"):
            task.rating = int(data["satisfaction"])

        # 重新计算工时
        task.update_work_minutes()

    async def _update_monthly_summaries_for_import(
        self, maintenance_data: List[Dict[str, Any]]
    ):
        """为导入的数据更新月度工时汇总"""
        # 收集需要更新的成员和月份
        updates_needed = set()

        for data in maintenance_data:
            if data.get("assignee") and data.get("report_time"):
                # 查找成员
                member_query = select(Member).where(Member.name == data["assignee"])
                member_result = await self.db.execute(member_query)
                member = member_result.scalar_one_or_none()

                if member:
                    report_time = data["report_time"]
                    if isinstance(report_time, str):
                        report_time = datetime.fromisoformat(report_time)

                    updates_needed.add((member.id, report_time.year, report_time.month))

        # 批量更新月度汇总
        for member_id, year, month in updates_needed:
            try:
                await self.work_hours_service.update_monthly_summary(
                    member_id, year, month
                )
            except Exception as e:
                logger.warning(
                    f"Failed to update monthly summary for member {member_id}, "
                    f"{year}-{month}: {str(e)}"
                )

    async def _recalculate_work_hours_for_marked_tasks(
        self, start_date, end_date, task_ids: Optional[List[int]] = None
    ):
        """重新计算被标记任务的工时"""
        # 查询被标记的任务
        query = select(RepairTask).where(
            and_(
                RepairTask.report_time >= start_date, RepairTask.report_time <= end_date
            )
        )

        if task_ids:
            query = query.where(RepairTask.id.in_(task_ids))

        result = await self.db.execute(query)
        tasks = result.scalars().all()

        # 收集需要更新月度汇总的成员
        members_to_update = set()

        for task in tasks:
            task.update_work_minutes()  # 重新计算工时
            members_to_update.add(
                (task.member_id, task.report_time.year, task.report_time.month)
            )

        await self.db.commit()

        # 更新月度汇总
        for member_id, year, month in members_to_update:
            try:
                await self.work_hours_service.update_monthly_summary(
                    member_id, year, month
                )
            except Exception as e:
                logger.warning(
                    f"Failed to update monthly summary after rush task marking: {str(e)}"
                )
