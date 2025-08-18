"""
工时自动化计算引擎
处理定时任务检测、自动化标签添加、工时重算等自动化功能
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

from app.core.config import settings
from app.models.task import RepairTask, TaskStatus, TaskTag, task_tag_association
from app.services.task_service import TaskService

logger = logging.getLogger(__name__)


class WorkHourAutomationService:
    """工时自动化计算服务"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.task_service = TaskService(db)

    async def schedule_overdue_detection(self) -> Dict[str, Any]:
        """
        定时检测超时任务并自动添加惩罚标签

        Returns:
            Dict: 检测结果统计
        """
        try:
            logger.info("Starting overdue detection...")

            # 检测延迟响应的任务
            late_response_count = await self._detect_late_response_tasks()

            # 检测延迟完成的任务
            late_completion_count = await self._detect_late_completion_tasks()

            # 检测长期未响应的任务
            long_overdue_count = await self._detect_long_overdue_tasks()

            await self.db.commit()

            result = {
                "detection_time": datetime.utcnow().isoformat(),
                "late_response_detected": late_response_count,
                "late_completion_detected": late_completion_count,
                "long_overdue_detected": long_overdue_count,
                "total_processed": late_response_count
                + late_completion_count
                + long_overdue_count,
            }

            logger.info(f"Overdue detection completed: {result}")
            return result

        except Exception as e:
            await self.db.rollback()
            logger.error(f"Overdue detection error: {str(e)}")
            raise

    async def auto_apply_penalty_tags(
        self, task_ids: Optional[List[int]] = None
    ) -> Dict[str, Any]:
        """
        自动应用惩罚标签

        Args:
            task_ids: 指定任务ID列表，如果为None则处理所有符合条件的任务

        Returns:
            Dict: 处理结果
        """
        try:
            logger.info("Starting auto penalty tag application...")

            # 构建查询
            query = select(RepairTask).options(selectinload(RepairTask.tags))

            if task_ids:
                query = query.where(RepairTask.id.in_(task_ids))
            else:
                # 只处理状态为进行中或已完成的任务
                query = query.where(
                    RepairTask.status.in_(
                        [TaskStatus.IN_PROGRESS, TaskStatus.COMPLETED]
                    )
                )

            result = await self.db.execute(query)
            tasks = result.scalars().all()

            penalty_applied = 0

            for task in tasks:
                applied = await self._apply_auto_penalties(task)
                if applied:
                    penalty_applied += 1

            await self.db.commit()

            result = {
                "processing_time": datetime.utcnow().isoformat(),
                "tasks_processed": len(tasks),
                "penalties_applied": penalty_applied,
            }

            logger.info(f"Auto penalty application completed: {result}")
            return result

        except Exception as e:
            await self.db.rollback()
            logger.error(f"Auto penalty application error: {str(e)}")
            raise

    async def process_review_bonuses(self) -> Dict[str, Any]:
        """
        处理评价奖励
        检查最近的评价并应用相应的奖励标签

        Returns:
            Dict: 处理结果
        """
        try:
            logger.info("Starting review bonus processing...")

            # 查询最近24小时内有新评价的任务
            since_time = datetime.utcnow() - timedelta(hours=24)

            query = (
                select(RepairTask)
                .options(selectinload(RepairTask.tags))
                .where(
                    and_(
                        RepairTask.rating.isnot(None),
                        RepairTask.updated_at >= since_time,
                    )
                )
            )

            result = await self.db.execute(query)
            tasks = result.scalars().all()

            bonuses_applied = 0

            for task in tasks:
                applied = await self._apply_review_bonuses(task)
                if applied:
                    bonuses_applied += 1

            await self.db.commit()

            result = {
                "processing_time": datetime.utcnow().isoformat(),
                "tasks_processed": len(tasks),
                "bonuses_applied": bonuses_applied,
            }

            logger.info(f"Review bonus processing completed: {result}")
            return result

        except Exception as e:
            await self.db.rollback()
            logger.error(f"Review bonus processing error: {str(e)}")
            raise

    async def recalculate_batch_hours(
        self,
        member_ids: Optional[List[int]] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """
        批量重新计算工时
        用于规则变更后的批量更新

        Args:
            member_ids: 指定成员ID列表
            date_from: 开始时间
            date_to: 结束时间

        Returns:
            Dict: 重算结果
        """
        try:
            logger.info("Starting batch work hours recalculation...")

            # 构建查询
            query = select(RepairTask)

            if member_ids:
                query = query.where(RepairTask.member_id.in_(member_ids))
            if date_from:
                query = query.where(RepairTask.report_time >= date_from)
            if date_to:
                query = query.where(RepairTask.report_time <= date_to)

            result = await self.db.execute(query)
            tasks = result.scalars().all()

            recalculated_count = 0
            total_minutes_before = 0
            total_minutes_after = 0

            for task in tasks:
                old_minutes = task.work_minutes
                total_minutes_before += old_minutes

                # 重新计算工时
                task.update_work_minutes()

                new_minutes = task.work_minutes
                total_minutes_after += new_minutes

                if old_minutes != new_minutes:
                    recalculated_count += 1
                    logger.debug(
                        f"Task {task.id} work minutes: {old_minutes} -> {new_minutes}"
                    )

            await self.db.commit()

            result = {
                "recalculation_time": datetime.utcnow().isoformat(),
                "tasks_processed": len(tasks),
                "tasks_recalculated": recalculated_count,
                "total_minutes_before": total_minutes_before,
                "total_minutes_after": total_minutes_after,
                "minutes_difference": total_minutes_after - total_minutes_before,
            }

            logger.info(f"Batch recalculation completed: {result}")
            return result

        except Exception as e:
            await self.db.rollback()
            logger.error(f"Batch recalculation error: {str(e)}")
            raise

    async def send_overdue_notifications(self) -> Dict[str, Any]:
        """
        发送超时提醒通知

        Returns:
            Dict: 通知发送结果
        """
        try:
            logger.info("Starting overdue notifications...")

            # 查询需要提醒的任务
            notification_tasks = await self._get_notification_tasks()

            notifications_sent = 0

            for task_info in notification_tasks:
                try:
                    # 这里可以集成邮件、短信、WebSocket等通知方式
                    await self._send_task_notification(task_info)
                    notifications_sent += 1
                except Exception as e:
                    logger.warning(
                        f"Failed to send notification for task {task_info['task_id']}: {str(e)}"
                    )

            result = {
                "notification_time": datetime.utcnow().isoformat(),
                "tasks_checked": len(notification_tasks),
                "notifications_sent": notifications_sent,
            }

            logger.info(f"Overdue notifications completed: {result}")
            return result

        except Exception as e:
            logger.error(f"Overdue notifications error: {str(e)}")
            raise

    async def cleanup_expired_data(self, days_to_keep: int = 90) -> Dict[str, Any]:
        """
        清理过期数据

        Args:
            days_to_keep: 保留数据的天数

        Returns:
            Dict: 清理结果
        """
        try:
            logger.info(f"Starting data cleanup (keeping {days_to_keep} days)...")

            cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)

            # 清理完成的旧任务（保留重要信息）
            completed_tasks_query = select(RepairTask).where(
                and_(
                    RepairTask.status == TaskStatus.COMPLETED,
                    RepairTask.completion_time < cutoff_date,
                )
            )

            completed_result = await self.db.execute(completed_tasks_query)
            old_completed_tasks = completed_result.scalars().all()

            archived_count = 0

            # 这里可以将数据归档而不是直接删除
            for task in old_completed_tasks:
                # 标记为已归档或移动到归档表
                task.description = f"[ARCHIVED] {task.description or ''}"
                archived_count += 1

            await self.db.commit()

            result = {
                "cleanup_time": datetime.utcnow().isoformat(),
                "cutoff_date": cutoff_date.isoformat(),
                "tasks_archived": archived_count,
            }

            logger.info(f"Data cleanup completed: {result}")
            return result

        except Exception as e:
            await self.db.rollback()
            logger.error(f"Data cleanup error: {str(e)}")
            raise

    # 私有方法

    async def _detect_late_response_tasks(self) -> int:
        """检测延迟响应的任务"""
        cutoff_time = datetime.utcnow() - timedelta(
            hours=settings.RESPONSE_TIMEOUT_HOURS
        )

        query = (
            select(RepairTask)
            .options(selectinload(RepairTask.tags))
            .where(
                and_(
                    RepairTask.status == TaskStatus.PENDING,
                    RepairTask.report_time <= cutoff_time,
                    ~RepairTask.tags.any(TaskTag.name == "延迟响应"),
                )
            )
        )

        result = await self.db.execute(query)
        late_tasks = result.scalars().all()

        for task in late_tasks:
            await self.task_service._add_penalty_tag(task, "延迟响应", -30)

        return len(late_tasks)

    async def _detect_late_completion_tasks(self) -> int:
        """检测延迟完成的任务"""
        cutoff_time = datetime.utcnow() - timedelta(
            hours=settings.COMPLETION_TIMEOUT_HOURS
        )

        query = (
            select(RepairTask)
            .options(selectinload(RepairTask.tags))
            .where(
                and_(
                    RepairTask.status == TaskStatus.IN_PROGRESS,
                    RepairTask.response_time.isnot(None),
                    RepairTask.response_time <= cutoff_time,
                    ~RepairTask.tags.any(TaskTag.name == "延迟完成"),
                )
            )
        )

        result = await self.db.execute(query)
        late_tasks = result.scalars().all()

        for task in late_tasks:
            await self.task_service._add_penalty_tag(task, "延迟完成", -30)

        return len(late_tasks)

    async def _detect_long_overdue_tasks(self) -> int:
        """检测长期未响应的任务"""
        cutoff_time = datetime.utcnow() - timedelta(hours=72)  # 3天

        query = (
            select(RepairTask)
            .options(selectinload(RepairTask.tags))
            .where(
                and_(
                    RepairTask.status == TaskStatus.PENDING,
                    RepairTask.report_time <= cutoff_time,
                    ~RepairTask.tags.any(TaskTag.name == "长期未响应"),
                )
            )
        )

        result = await self.db.execute(query)
        overdue_tasks = result.scalars().all()

        for task in overdue_tasks:
            await self.task_service._add_penalty_tag(task, "长期未响应", -60)

        return len(overdue_tasks)

    async def _apply_auto_penalties(self, task: RepairTask) -> bool:
        """为单个任务应用自动惩罚"""
        penalties_applied = False

        # 检查延迟响应
        if (
            task.status != TaskStatus.PENDING
            and task.response_time
            and task.report_time
            and not any(tag.name == "延迟响应" for tag in task.tags)
        ):
            response_hours = (
                task.response_time - task.report_time
            ).total_seconds() / 3600
            if response_hours > settings.RESPONSE_TIMEOUT_HOURS:
                await self.task_service._add_penalty_tag(task, "延迟响应", -30)
                penalties_applied = True

        # 检查延迟完成
        if (
            task.status == TaskStatus.COMPLETED
            and task.completion_time
            and task.response_time
            and not any(tag.name == "延迟完成" for tag in task.tags)
        ):
            completion_hours = (
                task.completion_time - task.response_time
            ).total_seconds() / 3600
            if completion_hours > settings.COMPLETION_TIMEOUT_HOURS:
                await self.task_service._add_penalty_tag(task, "延迟完成", -30)
                penalties_applied = True

        if penalties_applied:
            task.update_work_minutes()

        return penalties_applied

    async def _apply_review_bonuses(self, task: RepairTask) -> bool:
        """为单个任务应用评价奖励"""
        bonuses_applied = False

        if task.rating is None:
            return False

        # 检查差评惩罚
        if task.rating <= settings.MAX_RATING_FOR_NEGATIVE and not any(
            tag.name == "差评" for tag in task.tags
        ):
            await self.task_service._add_penalty_tag(task, "差评", -60)
            bonuses_applied = True

        # 检查非默认好评奖励
        elif (
            task.rating >= settings.MIN_RATING_FOR_POSITIVE
            and task.feedback
            and not self._is_default_feedback(task.feedback)
            and not any(tag.name == "非默认好评" for tag in task.tags)
        ):
            await self.task_service._add_bonus_tag(task, "非默认好评", 30)
            bonuses_applied = True

        if bonuses_applied:
            task.update_work_minutes()

        return bonuses_applied

    def _is_default_feedback(self, feedback: str) -> bool:
        """检查是否为默认反馈"""
        if not feedback:
            return True

        default_keywords = ["系统默认好评", "默认", "自动好评", "满意", "好的", "可以"]
        feedback_lower = feedback.lower().strip()

        # 检查是否包含默认关键词
        if any(keyword in feedback_lower for keyword in default_keywords):
            return True

        # 检查是否过短（可能是默认回复）
        if len(feedback_lower) <= 3:
            return True

        return False

    async def _get_notification_tasks(self) -> List[Dict[str, Any]]:
        """获取需要发送通知的任务"""
        notification_tasks = []

        # 获取即将超时的任务（还有2小时就超时）
        warning_time = datetime.utcnow() - timedelta(
            hours=settings.RESPONSE_TIMEOUT_HOURS - 2
        )

        query = (
            select(RepairTask)
            .options(joinedload(RepairTask.assigned_member))
            .where(
                and_(
                    RepairTask.status == TaskStatus.PENDING,
                    RepairTask.report_time <= warning_time,
                    RepairTask.member_id.isnot(None),
                )
            )
        )

        result = await self.db.execute(query)
        warning_tasks = result.scalars().all()

        for task in warning_tasks:
            if task.assigned_member:
                notification_tasks.append(
                    {
                        "task_id": task.id,
                        "task_title": task.title,
                        "member_id": task.member_id,
                        "member_name": task.assigned_member.name,
                        "member_email": task.assigned_member.email,
                        "notification_type": "response_warning",
                        "hours_remaining": 2,
                    }
                )

        return notification_tasks

    async def _send_task_notification(self, task_info: Dict[str, Any]):
        """发送任务通知"""
        # 这里可以实现具体的通知逻辑
        # 例如：邮件通知、WebSocket推送、短信通知等

        notification_type = task_info["notification_type"]

        if notification_type == "response_warning":
            logger.info(
                f"Sending response warning notification to {task_info['member_name']} "
                f"for task {task_info['task_id']}"
            )
            # 实际的通知发送逻辑

        # 记录通知历史
        # 可以创建一个NotificationLog模型来记录所有通知

    async def get_automation_statistics(self) -> Dict[str, Any]:
        """获取自动化统计信息"""
        try:
            # 统计各种自动化标签的使用情况
            penalty_tags = ["延迟响应", "延迟完成", "长期未响应", "差评"]
            bonus_tags = ["紧急任务", "非默认好评"]

            tag_stats = {}

            for tag_name in penalty_tags + bonus_tags:
                tag_query = select(func.count()).select_from(
                    select(task_tag_association)
                    .join(TaskTag)
                    .where(TaskTag.name == tag_name)
                )
                tag_result = await self.db.execute(tag_query)
                tag_stats[tag_name] = tag_result.scalar()

            # 统计任务状态分布
            status_query = select(
                RepairTask.status, func.count(RepairTask.id).label("count")
            ).group_by(RepairTask.status)

            status_result = await self.db.execute(status_query)
            status_stats = {status.value: count for status, count in status_result}

            # 统计超时任务
            now = datetime.utcnow()
            response_cutoff = now - timedelta(hours=settings.RESPONSE_TIMEOUT_HOURS)
            completion_cutoff = now - timedelta(hours=settings.COMPLETION_TIMEOUT_HOURS)

            overdue_response_query = select(func.count()).where(
                and_(
                    RepairTask.status == TaskStatus.PENDING,
                    RepairTask.report_time <= response_cutoff,
                )
            )
            overdue_response_result = await self.db.execute(overdue_response_query)
            overdue_response_count = overdue_response_result.scalar()

            overdue_completion_query = select(func.count()).where(
                and_(
                    RepairTask.status == TaskStatus.IN_PROGRESS,
                    RepairTask.response_time.isnot(None),
                    RepairTask.response_time <= completion_cutoff,
                )
            )
            overdue_completion_result = await self.db.execute(overdue_completion_query)
            overdue_completion_count = overdue_completion_result.scalar()

            return {
                "statistics_time": datetime.utcnow().isoformat(),
                "tag_usage": tag_stats,
                "task_status_distribution": status_stats,
                "overdue_tasks": {
                    "overdue_response": overdue_response_count,
                    "overdue_completion": overdue_completion_count,
                },
                "automation_rules": {
                    "response_timeout_hours": settings.RESPONSE_TIMEOUT_HOURS,
                    "completion_timeout_hours": settings.COMPLETION_TIMEOUT_HOURS,
                    "min_rating_for_positive": settings.MIN_RATING_FOR_POSITIVE,
                    "max_rating_for_negative": settings.MAX_RATING_FOR_NEGATIVE,
                },
            }

        except Exception as e:
            logger.error(f"Get automation statistics error: {str(e)}")
            raise
