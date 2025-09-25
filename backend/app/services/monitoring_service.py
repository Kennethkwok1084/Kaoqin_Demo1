"""
监控任务业务逻辑服务。
负责巡检与监控类任务的业务处理。
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


class MonitoringService:
    """监控任务服务"""

    def __init__(self, db: AsyncSession) -> None:
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
            )

            # Set enum values after instantiation to avoid constructor issues
            task.status = TaskStatus.COMPLETED

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
            total_work_minutes = sum(t.work_minutes or 0 for t in tasks)
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
