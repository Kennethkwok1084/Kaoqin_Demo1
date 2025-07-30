"""
任务管理业务逻辑服务
处理任务的业务逻辑，包括工时计算、状态管理、标签处理等
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func, desc, update
from sqlalchemy.orm import selectinload, joinedload

from app.models.task import (
    RepairTask, MonitoringTask, AssistanceTask, TaskTag, TaskStatus, 
    TaskType, TaskPriority, TaskCategory, task_tag_association
)
from app.models.member import Member
from app.core.config import settings

logger = logging.getLogger(__name__)


class TaskService:
    """任务管理服务"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create_repair_task(
        self,
        task_data: Dict[str, Any],
        creator_id: int
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
                location=task_data.get("location"),
                member_id=task_data.get("assigned_to"),
                report_time=datetime.utcnow(),
                reporter_name=task_data.get("reporter_name"),
                reporter_contact=task_data.get("reporter_contact"),
                status=TaskStatus.PENDING
            )
            
            # 设置基础工时
            task.base_work_minutes = task.get_base_work_minutes()
            
            self.db.add(task)
            await self.db.flush()
            
            # 添加标签
            if "tag_ids" in task_data and task_data["tag_ids"]:
                await self._add_tags_to_task(task, task_data["tag_ids"])
            
            # 如果是紧急任务，添加紧急标签
            if task_data.get("is_rush", False):
                await self._add_rush_tag(task)
            
            # 计算工时
            task.update_work_minutes()
            
            await self.db.commit()
            await self.db.refresh(task)
            
            logger.info(f"Repair task created: {task.task_id}")
            return task
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Create repair task error: {str(e)}")
            raise
    
    async def update_task_status(
        self,
        task_id: int,
        new_status: TaskStatus,
        user_id: int,
        completion_note: Optional[str] = None,
        actual_minutes: Optional[int] = None
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
            query = select(RepairTask).options(
                selectinload(RepairTask.tags)
            ).where(RepairTask.id == task_id)
            
            result = await self.db.execute(query)
            task = result.scalar_one_or_none()
            
            if not task:
                raise ValueError("任务不存在")
            
            old_status = task.status
            
            # 验证状态转换
            if not self._is_valid_status_transition(old_status, new_status):
                raise ValueError(f"不能从 {old_status.value} 状态转换到 {new_status.value} 状态")
            
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
                    task.description += f"\n\n{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - {completion_note}"
                else:
                    task.description = completion_note
            
            # 重新计算工时
            task.update_work_minutes()
            
            await self.db.commit()
            await self.db.refresh(task)
            
            logger.info(f"Task {task_id} status updated from {old_status.value} to {new_status.value}")
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
        assignment_note: Optional[str] = None
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
                assignment_log = f"\n\n{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - 任务分配：{assignment_note}"
                if task.description:
                    task.description += assignment_log
                else:
                    task.description = assignment_note
            
            await self.db.commit()
            await self.db.refresh(task)
            
            logger.info(f"Task {task_id} assigned from {old_member_id} to {assigned_to}")
            return task
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Assign task error: {str(e)}")
            raise
    
    async def add_task_feedback(
        self,
        task_id: int,
        rating: int,
        feedback: Optional[str] = None
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
            query = select(RepairTask).options(
                selectinload(RepairTask.tags)
            ).where(RepairTask.id == task_id)
            
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
        date_to: Optional[datetime] = None
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
            completed_tasks = len([t for t in tasks if t.status == TaskStatus.COMPLETED])
            pending_tasks = len([t for t in tasks if t.status == TaskStatus.PENDING])
            in_progress_tasks = len([t for t in tasks if t.status == TaskStatus.IN_PROGRESS])
            
            total_work_minutes = sum(t.work_minutes for t in tasks)
            total_work_hours = round(total_work_minutes / 60.0, 2)
            
            # 类型分布
            online_tasks = len([t for t in tasks if t.task_type == TaskType.ONLINE])
            offline_tasks = len([t for t in tasks if t.task_type == TaskType.OFFLINE])
            
            # 评分统计
            rated_tasks = [t for t in tasks if t.rating is not None]
            avg_rating = 0.0
            if rated_tasks:
                avg_rating = round(sum(t.rating for t in rated_tasks) / len(rated_tasks), 2)
            
            # 延迟统计
            overdue_response = len([t for t in tasks if t.is_overdue_response])
            overdue_completion = len([t for t in tasks if t.is_overdue_completion])
            
            return {
                "member_id": member_id,
                "period": {
                    "from": date_from.isoformat() if date_from else None,
                    "to": date_to.isoformat() if date_to else None
                },
                "task_counts": {
                    "total": total_tasks,
                    "completed": completed_tasks,
                    "pending": pending_tasks,
                    "in_progress": in_progress_tasks
                },
                "work_hours": {
                    "total_minutes": total_work_minutes,
                    "total_hours": total_work_hours
                },
                "task_types": {
                    "online": online_tasks,
                    "offline": offline_tasks
                },
                "quality": {
                    "avg_rating": avg_rating,
                    "rated_tasks": len(rated_tasks),
                    "overdue_response": overdue_response,
                    "overdue_completion": overdue_completion
                }
            }
            
        except Exception as e:
            logger.error(f"Get member task summary error: {str(e)}")
            raise
    
    # 私有方法
    
    async def _generate_task_id(self) -> str:
        """生成任务编号"""
        today = datetime.now().strftime("%Y%m%d")
        
        # 查询今天已有的任务数量
        count_query = select(func.count()).where(
            RepairTask.task_id.like(f"R{today}%")
        )
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
    
    async def _get_or_create_tag(self, name: str, modifier: int, tag_type: str) -> TaskTag:
        """获取或创建标签"""
        tag_query = select(TaskTag).where(TaskTag.name == name)
        tag_result = await self.db.execute(tag_query)
        tag = tag_result.scalar_one_or_none()
        
        if not tag:
            tag = TaskTag(
                name=name,
                work_minutes_modifier=modifier,
                tag_type=tag_type,
                is_active=True
            )
            self.db.add(tag)
            await self.db.flush()
        
        return tag
    
    def _is_valid_status_transition(self, old_status: TaskStatus, new_status: TaskStatus) -> bool:
        """验证状态转换是否有效"""
        valid_transitions = {
            TaskStatus.PENDING: [TaskStatus.IN_PROGRESS, TaskStatus.CANCELLED],
            TaskStatus.IN_PROGRESS: [TaskStatus.COMPLETED, TaskStatus.ON_HOLD, TaskStatus.CANCELLED],
            TaskStatus.ON_HOLD: [TaskStatus.IN_PROGRESS, TaskStatus.CANCELLED],
            TaskStatus.COMPLETED: [],
            TaskStatus.CANCELLED: []
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
        
        completion_hours = (task.completion_time - task.response_time).total_seconds() / 3600
        return completion_hours > 48  # 超过48小时为延迟完成
    
    def _is_default_feedback(self, feedback: str) -> bool:
        """检查是否为默认反馈"""
        if not feedback:
            return True
        
        default_keywords = ["系统默认好评", "默认", "自动好评", "满意"]
        feedback_lower = feedback.lower()
        return any(keyword in feedback_lower for keyword in default_keywords)


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
        end_time: Optional[datetime] = None
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
                status=TaskStatus.COMPLETED
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
        date_to: Optional[datetime] = None
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
                "type_distribution": type_stats
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
        end_time: Optional[datetime] = None
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
                status=TaskStatus.COMPLETED
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
        date_to: Optional[datetime] = None
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
                "department_distribution": dept_stats
            }
            
        except Exception as e:
            logger.error(f"Get assistance summary error: {str(e)}")
            raise