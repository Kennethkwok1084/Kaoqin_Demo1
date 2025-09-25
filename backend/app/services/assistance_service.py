"""
协助任务业务逻辑服务。
负责跨部门支援任务的业务处理。
"""

import logging
from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional

from sqlalchemy import and_, desc, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

from app.core.exceptions import PermissionDeniedError
from app.models.member import Member, UserRole
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


class AssistanceService:
    """协助任务服务"""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        # Import needed services to avoid circular imports
        from app.services.work_hours_service import WorkHoursCalculationService

        self.work_hours_service = WorkHoursCalculationService(db)
        # For rush_task_service, we'll use TaskService
        self.rush_task_service: RushTaskMarkingService = RushTaskMarkingService(db)

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
            )

            # Set enum values after instantiation to avoid constructor issues
            task.status = TaskStatus.COMPLETED

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
            total_work_minutes = sum(t.work_minutes or 0 for t in tasks)
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
                        data.get("work_order_id") or ""
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
        marked_by: Optional[int] = None,
    ) -> Dict[str, Any]:
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
            start_date = datetime.strptime(date_from, "%Y-%m-%d")
            end_date = datetime.strptime(date_to, "%Y-%m-%d")

            # Use rush_task_service for rush task operations
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
        match_index: Dict[str, List[int]] = {}

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
        # 查找或创建成员
        member_id = await self._find_or_create_member_for_task(data)

        # 创建任务
        task = RepairTask(
            task_id=data.get(
                "work_order_id", f"ASSIST_{int(datetime.utcnow().timestamp())}"
            ),
            title=data.get("title", "维修任务"),
            description=data.get("description", ""),
            location=data.get("location", ""),
            member_id=member_id,
            report_time=data.get("report_time", datetime.utcnow()),
            response_time=data.get("response_time"),
            completion_time=data.get("complete_time"),
            reporter_name=data.get("contact_person"),
            reporter_contact=data.get("contact_phone"),
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
    ) -> None:
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
                    work_minutes_modifier=int(str(config["modifier"])),
                    is_active=True,
                )
                self.db.add(tag)
                await self.db.flush()

        return tag

    async def _update_existing_maintenance_task(
        self, task: RepairTask, data: Dict[str, Any]
    ) -> None:
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
    ) -> None:
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
        self,
        start_date: datetime,
        end_date: datetime,
        task_ids: Optional[List[int]] = None,
    ) -> None:
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
            if task.report_time:
                members_to_update.add(
                    (task.member_id, task.report_time.year, task.report_time.month)
                )

        await self.db.commit()

        # 更新月度汇总
        for member_id, year, month in members_to_update:
            try:
                if member_id is not None:
                    await self.work_hours_service.update_monthly_summary(
                        member_id, year, month
                    )
            except Exception as e:
                logger.warning(
                    f"Failed to update monthly summary after rush task marking: {str(e)}"
                )

    async def recalculate_task_work_hours(self, task_id: int) -> bool:
        """
        重新计算单个任务的工时

        Args:
            task_id: 任务ID

        Returns:
            bool: 是否成功重新计算
        """
        try:
            # 获取任务
            query = select(RepairTask).where(RepairTask.id == task_id)
            result = await self.db.execute(query)
            task = result.scalar_one_or_none()

            if not task:
                logger.warning(f"Task not found: {task_id}")
                return False

            # 保存旧的工时
            old_work_minutes = task.work_minutes

            # 重新计算工时
            task.update_work_minutes()

            # 检查是否有变化
            if old_work_minutes != task.work_minutes:
                await self.db.commit()

                # 更新月度汇总
                if task.report_time and task.member_id:
                    try:
                        await self.work_hours_service.update_monthly_summary(
                            task.member_id,
                            task.report_time.year,
                            task.report_time.month,
                        )
                    except Exception as e:
                        logger.warning(
                            f"Failed to update monthly summary for task {task_id}: {str(e)}"
                        )

                logger.info(
                    f"Task {task_id} work hours recalculated: "
                    f"{old_work_minutes} -> {task.work_minutes} minutes"
                )
                return True
            else:
                logger.debug(
                    f"Task {task_id} work hours unchanged: {old_work_minutes} minutes"
                )
                return False

        except Exception as e:
            logger.error(
                f"Failed to recalculate task work hours for {task_id}: {str(e)}"
            )
            await self.db.rollback()
            return False

    async def _bulk_add_rush_tags(
        self, tasks: List[RepairTask], marker_id: int
    ) -> Dict[str, Any]:
        """
        批量为任务添加爆单标签的内部方法

        Args:
            tasks: 任务列表
            marker_id: 标记者ID

        Returns:
            Dict: 操作结果统计
        """
        try:
            success_count = 0
            failed_count = 0
            errors = []

            # 获取或创建爆单标签
            rush_tag = await self._get_or_create_rush_tag()

            for task in tasks:
                try:
                    # 检查任务状态是否允许标记爆单
                    if task.status not in [
                        TaskStatus.COMPLETED,
                        TaskStatus.IN_PROGRESS,
                    ]:
                        errors.append(f"任务{task.id}状态不允许标记爆单")
                        failed_count += 1
                        continue

                    # 检查是否已经标记为爆单
                    if task.is_rush_order:
                        errors.append(f"任务{task.id}已被标记为爆单")
                        failed_count += 1
                        continue

                    # 添加爆单标签
                    task.is_rush_order = True
                    if rush_tag not in task.tags:
                        task.tags.append(rush_tag)

                    # 重新计算工时
                    task.update_work_minutes()

                    success_count += 1

                except Exception as e:
                    error_msg = f"任务{task.id}标记失败: {str(e)}"
                    errors.append(error_msg)
                    failed_count += 1
                    logger.warning(error_msg)

            # 提交数据库更改
            await self.db.commit()

            return {
                "success": success_count,
                "failed": failed_count,
                "errors": errors,
                "total": len(tasks),
            }

        except Exception as e:
            await self.db.rollback()
            logger.error(f"Bulk add rush tags error: {str(e)}")
            return {
                "success": 0,
                "failed": len(tasks),
                "errors": [f"批量操作失败: {str(e)}"],
                "total": len(tasks),
            }

    async def _get_or_create_rush_tag(self) -> TaskTag:
        """获取或创建爆单标签"""
        try:
            # 查找现有爆单标签
            tag_query = select(TaskTag).where(
                and_(
                    TaskTag.name == "爆单任务",
                    TaskTag.tag_type == TaskTagType.RUSH_ORDER,
                )
            )
            result = await self.db.execute(tag_query)
            tag = result.scalar_one_or_none()

            if tag:
                return tag

            # 创建新的爆单标签
            tag = TaskTag.create_rush_order_tag()
            self.db.add(tag)
            await self.db.flush()
            return tag

        except Exception as e:
            logger.error(f"Get or create rush tag error: {str(e)}")
            raise
