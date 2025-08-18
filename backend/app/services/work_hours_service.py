"""
工时计算服务
基于 readme.md 和 agents_updated.md 的新考勤规则实现
支持多标签累计计算、异常扣时逻辑、爆单标记等功能
"""

import logging
from calendar import monthrange
from datetime import date, datetime
from typing import Dict, List, Optional

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.attendance import MonthlyAttendanceSummary
from app.models.member import Member
from app.models.task import (
    AssistanceTask,
    MonitoringTask,
    RepairTask,
    TaskStatus,
    TaskTag,
    TaskTagType,
    TaskType,
)

logger = logging.getLogger(__name__)


class WorkHoursCalculationService:
    """工时计算服务 - 实现新的考勤规则"""

    def __init__(self, db: AsyncSession):
        self.db = db

        # 基础工时配置（分钟）
        self.ONLINE_TASK_MINUTES = 40  # 线上任务
        self.OFFLINE_TASK_MINUTES = 100  # 线下任务
        self.RUSH_TASK_MINUTES = 15  # 爆单任务额外时长
        self.POSITIVE_REVIEW_MINUTES = 30  # 非默认好评额外时长

        # 异常扣时配置（分钟）
        self.LATE_RESPONSE_PENALTY = 30  # 超时响应扣时
        self.LATE_COMPLETION_PENALTY = 30  # 超时处理扣时
        self.NEGATIVE_REVIEW_PENALTY = 60  # 差评扣时

        # 时间阈值
        self.RESPONSE_TIMEOUT_HOURS = 24  # 响应超时阈值
        self.COMPLETION_TIMEOUT_HOURS = 48  # 处理超时阈值

    async def calculate_task_work_minutes(self, task: RepairTask) -> Dict[str, int]:
        """
        计算单个任务的工时（分钟）- 重构版
        实现爆单任务独立计算逻辑

        Args:
            task: 报修任务对象

        Returns:
            Dict: 包含各类工时明细的字典

        Raises:
            ValueError: 输入参数无效
            RuntimeError: 计算过程出现错误
        """
        # 输入校验
        if not task:
            logger.error("Task object is None or empty")
            raise ValueError("任务对象不能为空")

        if not hasattr(task, "id") or task.id is None:
            logger.error("Task ID is None or invalid")
            raise ValueError("任务ID无效")

        if not hasattr(task, "task_type") or task.task_type is None:
            logger.error(f"Task {task.id} has invalid task_type")
            raise ValueError(f"任务 {task.id} 的任务类型无效")

        if not hasattr(task, "report_time") or task.report_time is None:
            logger.error(f"Task {task.id} has invalid report_time")
            raise ValueError(f"任务 {task.id} 的报修时间无效")

        # 确保task有tags属性
        if not hasattr(task, "tags"):
            logger.warning(
                f"Task {task.id} has no tags attribute, will refresh from DB"
            )
            try:
                await self.db.refresh(task, ["tags"])
            except Exception as e:
                logger.error(f"Failed to refresh task {task.id} tags: {str(e)}")
                raise RuntimeError(f"无法加载任务 {task.id} 的标签信息")

        try:
            # 检查是否为爆单任务（优先使用模型字段）
            is_rush_order = getattr(task, "is_rush_order", False)

            # 如果模型字段未设置，检查标签
            if not is_rush_order:
                await self.db.refresh(task, ["tags"])
                for tag in task.tags:
                    if tag.tag_type == TaskTagType.RUSH_ORDER and tag.is_active:
                        is_rush_order = True
                        break

            # 爆单任务独立计算逻辑
            if is_rush_order:
                # 爆单任务固定15分钟，但仍可与异常扣时叠加
                rush_base_minutes = 15
                penalty_minutes = 0

                # 计算异常扣时
                late_response_penalty = 0
                late_completion_penalty = 0
                negative_review_penalty = 0

                # 从标签中统计异常扣时
                for tag in task.tags:
                    if tag.is_active and tag.is_penalty_tag():
                        if tag.tag_type == TaskTagType.TIMEOUT_RESPONSE:
                            late_response_penalty = abs(tag.work_minutes_modifier)
                        elif tag.tag_type == TaskTagType.TIMEOUT_PROCESSING:
                            late_completion_penalty = abs(tag.work_minutes_modifier)
                        elif tag.tag_type == TaskTagType.BAD_RATING:
                            negative_review_penalty = abs(tag.work_minutes_modifier)

                # 检查实时异常情况
                if self._is_response_overdue(task):
                    late_response_penalty = max(
                        late_response_penalty, self.LATE_RESPONSE_PENALTY
                    )

                if self._is_completion_overdue(task):
                    late_completion_penalty = max(
                        late_completion_penalty, self.LATE_COMPLETION_PENALTY
                    )

                if self._is_negative_review(task):
                    negative_review_penalty = max(
                        negative_review_penalty, self.NEGATIVE_REVIEW_PENALTY
                    )

                penalty_minutes = (
                    late_response_penalty
                    + late_completion_penalty
                    + negative_review_penalty
                )
                total_minutes = max(0, rush_base_minutes - penalty_minutes)

                return {
                    "is_rush_order": True,
                    "base_minutes": 0,
                    "rush_minutes": rush_base_minutes,
                    "positive_review_minutes": 0,
                    "penalty_minutes": penalty_minutes,
                    "late_response_penalty": late_response_penalty,
                    "late_completion_penalty": late_completion_penalty,
                    "negative_review_penalty": negative_review_penalty,
                    "total_minutes": total_minutes,
                }

            # 非爆单任务：传统叠加计算
            base_minutes = (
                self.ONLINE_TASK_MINUTES
                if task.task_type == TaskType.ONLINE
                else self.OFFLINE_TASK_MINUTES
            )

            # 奖励工时
            positive_review_minutes = 0

            # 惩罚扣时
            penalty_minutes = 0
            late_response_penalty = 0
            late_completion_penalty = 0
            negative_review_penalty = 0

            # 从标签中统计奖励和扣时
            for tag in task.tags:
                if tag.is_active:
                    if tag.tag_type == TaskTagType.NON_DEFAULT_RATING:
                        positive_review_minutes += tag.work_minutes_modifier or 0
                    elif tag.is_penalty_tag():
                        if tag.tag_type == TaskTagType.TIMEOUT_RESPONSE:
                            late_response_penalty += abs(tag.work_minutes_modifier or 0)
                        elif tag.tag_type == TaskTagType.TIMEOUT_PROCESSING:
                            late_completion_penalty += abs(tag.work_minutes_modifier or 0)
                        elif tag.tag_type == TaskTagType.BAD_RATING:
                            negative_review_penalty += abs(tag.work_minutes_modifier or 0)
                        elif tag.tag_type == TaskTagType.PENALTY:
                            penalty_minutes += abs(tag.work_minutes_modifier or 0)

            # 检查实时异常情况
            if self._is_response_overdue(task):
                late_response_penalty = max(
                    late_response_penalty, self.LATE_RESPONSE_PENALTY
                )

            if self._is_completion_overdue(task):
                late_completion_penalty = max(
                    late_completion_penalty, self.LATE_COMPLETION_PENALTY
                )

            if self._is_negative_review(task):
                negative_review_penalty = max(
                    negative_review_penalty, self.NEGATIVE_REVIEW_PENALTY
                )

            total_penalty = (
                penalty_minutes
                + late_response_penalty
                + late_completion_penalty
                + negative_review_penalty
            )

            # 计算总工时（确保不小于0）
            total_minutes = max(
                0, base_minutes + positive_review_minutes - total_penalty
            )

            return {
                "is_rush_order": False,
                "base_minutes": base_minutes,
                "rush_minutes": 0,
                "positive_review_minutes": positive_review_minutes,
                "penalty_minutes": total_penalty,
                "late_response_penalty": late_response_penalty,
                "late_completion_penalty": late_completion_penalty,
                "negative_review_penalty": negative_review_penalty,
                "total_minutes": total_minutes,
            }

        except ValueError:
            # Re-raise validation errors as-is
            raise
        except RuntimeError:
            # Re-raise runtime errors as-is
            raise
        except Exception as e:
            logger.error(
                f"Unexpected error calculating task "
                f"{task.id if hasattr(task, 'id') else 'unknown'} work minutes: {str(e)}"
            )
            raise RuntimeError(f"工时计算过程发生未预期错误: {str(e)}")

    async def calculate_monthly_work_hours(
        self, member_id: int, year: int, month: int
    ) -> Dict[str, float]:
        """
        计算成员月度工时汇总

        Args:
            member_id: 成员ID
            year: 年份
            month: 月份

        Returns:
            Dict: 月度工时统计数据

        Raises:
            ValueError: 输入参数无效
            RuntimeError: 计算过程出现错误
        """
        # 输入校验
        if not isinstance(member_id, int) or member_id <= 0:
            logger.error(f"Invalid member_id: {member_id}")
            raise ValueError("成员ID必须为正整数")

        if not isinstance(year, int) or year < 2020 or year > 2050:
            logger.error(f"Invalid year: {year}")
            raise ValueError("年份必须在2020-2050范围内")

        if not isinstance(month, int) or month < 1 or month > 12:
            logger.error(f"Invalid month: {month}")
            raise ValueError("月份必须在1-12范围内")

        # 验证成员是否存在
        try:
            member_query = select(Member).where(Member.id == member_id)
            member_result = await self.db.execute(member_query)
            member = member_result.scalar_one_or_none()

            if not member:
                logger.error(f"Member {member_id} not found")
                raise ValueError(f"成员 {member_id} 不存在")

            if not member.is_active:
                logger.warning(
                    f"Member {member_id} is inactive, but allowing calculation"
                )

        except ValueError:
            raise
        except Exception as e:
            logger.error(f"Error validating member {member_id}: {str(e)}")
            raise RuntimeError(f"验证成员信息时出错: {str(e)}")

        try:
            # 计算月份范围
            first_day = date(year, month, 1)
            last_day = date(year, month, monthrange(year, month)[1])

            # 查询报修任务
            repair_tasks_query = (
                select(RepairTask)
                .options(selectinload(RepairTask.tags))
                .where(
                    and_(
                        RepairTask.member_id == member_id,
                        RepairTask.report_time >= first_day,
                        RepairTask.report_time <= last_day,
                        RepairTask.status.in_(
                            [TaskStatus.COMPLETED, TaskStatus.IN_PROGRESS]
                        ),
                    )
                )
            )
            repair_result = await self.db.execute(repair_tasks_query)
            repair_tasks = list(repair_result.scalars().all())

            # 计算报修任务工时
            repair_stats = await self._calculate_repair_tasks_hours(repair_tasks)

            # 查询监控任务
            monitoring_tasks_query = select(MonitoringTask).where(
                and_(
                    MonitoringTask.member_id == member_id,
                    MonitoringTask.start_time >= first_day,
                    MonitoringTask.start_time <= last_day,
                    MonitoringTask.status == TaskStatus.COMPLETED,
                )
            )
            monitoring_result = await self.db.execute(monitoring_tasks_query)
            monitoring_tasks = monitoring_result.scalars().all()

            # 计算监控任务工时
            monitoring_hours = (
                sum(task.work_minutes for task in monitoring_tasks) / 60.0
            )

            # 查询协助任务
            assistance_tasks_query = select(AssistanceTask).where(
                and_(
                    AssistanceTask.member_id == member_id,
                    AssistanceTask.start_time >= first_day,
                    AssistanceTask.start_time <= last_day,
                    AssistanceTask.status == TaskStatus.COMPLETED,
                )
            )
            assistance_result = await self.db.execute(assistance_tasks_query)
            assistance_tasks = assistance_result.scalars().all()

            # 计算协助任务工时
            assistance_hours = (
                sum(task.work_minutes for task in assistance_tasks) / 60.0
            )

            # 查询上月结转时长
            prev_month = month - 1 if month > 1 else 12
            prev_year = year if month > 1 else year - 1

            prev_summary_query = select(MonthlyAttendanceSummary).where(
                and_(
                    MonthlyAttendanceSummary.member_id == member_id,
                    MonthlyAttendanceSummary.year == prev_year,
                    MonthlyAttendanceSummary.month == prev_month,
                )
            )
            prev_result = await self.db.execute(prev_summary_query)
            prev_summary = prev_result.scalar_one_or_none()

            carried_hours = prev_summary.remaining_hours if prev_summary else 0.0

            # 计算总工时
            total_hours = (
                repair_stats["total_hours"]
                + monitoring_hours
                + assistance_hours
                + carried_hours
            )

            # 计算可结转工时（满勤30小时/月，超出部分可结转）
            monthly_requirement = 30.0
            remaining_hours = max(0.0, total_hours - monthly_requirement)

            return {
                # 核心工时字段
                "repair_task_hours": repair_stats["total_hours"],
                "monitoring_hours": monitoring_hours,
                "assistance_hours": assistance_hours,
                "carried_hours": carried_hours,
                "total_hours": total_hours,
                "remaining_hours": remaining_hours,
                # 详细分类统计
                "online_repair_hours": repair_stats["online_hours"],
                "offline_repair_hours": repair_stats["offline_hours"],
                "rush_task_hours": repair_stats["rush_hours"],
                "positive_review_hours": repair_stats["positive_review_hours"],
                # 惩罚统计
                "penalty_hours": repair_stats["penalty_hours"],
                "late_response_penalty_hours": repair_stats[
                    "late_response_penalty_hours"
                ],
                "late_completion_penalty_hours": repair_stats[
                    "late_completion_penalty_hours"
                ],
                "negative_review_penalty_hours": repair_stats[
                    "negative_review_penalty_hours"
                ],
                # 统计数据
                "repair_task_count": len(repair_tasks),
                "monitoring_task_count": len(monitoring_tasks),
                "assistance_task_count": len(assistance_tasks),
                "monthly_requirement": monthly_requirement,
                "is_full_attendance": total_hours >= monthly_requirement,
            }

        except Exception as e:
            logger.error(f"Calculate monthly work hours error: {str(e)}")
            raise

    async def update_monthly_summary(
        self, member_id: int, year: int, month: int
    ) -> MonthlyAttendanceSummary:
        """
        更新或创建月度考勤汇总

        Args:
            member_id: 成员ID
            year: 年份
            month: 月份

        Returns:
            MonthlyAttendanceSummary: 更新后的月度汇总记录

        Raises:
            ValueError: 输入参数无效
            RuntimeError: 更新过程出现错误
        """
        # 输入校验
        if not isinstance(member_id, int) or member_id <= 0:
            logger.error(f"Invalid member_id: {member_id}")
            raise ValueError("成员ID必须为正整数")

        if not isinstance(year, int) or year < 2020 or year > 2050:
            logger.error(f"Invalid year: {year}")
            raise ValueError("年份必须在2020-2050范围内")

        if not isinstance(month, int) or month < 1 or month > 12:
            logger.error(f"Invalid month: {month}")
            raise ValueError("月份必须在1-12范围内")

        try:
            # 计算工时数据
            work_hours_data = await self.calculate_monthly_work_hours(
                member_id, year, month
            )

            # 查询现有记录
            existing_query = select(MonthlyAttendanceSummary).where(
                and_(
                    MonthlyAttendanceSummary.member_id == member_id,
                    MonthlyAttendanceSummary.year == year,
                    MonthlyAttendanceSummary.month == month,
                )
            )
            existing_result = await self.db.execute(existing_query)
            summary = existing_result.scalar_one_or_none()

            if summary:
                # 更新现有记录
                for key, value in work_hours_data.items():
                    if hasattr(summary, key) and not key.endswith("_count"):
                        setattr(summary, key, value)
                summary.updated_at = datetime.utcnow()  # type: ignore[assignment]
            else:
                # 创建新记录
                summary = MonthlyAttendanceSummary(
                    member_id=member_id,
                    year=year,
                    month=month,
                    **{
                        k: v
                        for k, v in work_hours_data.items()
                        if not k.endswith("_count")
                    },
                )
                self.db.add(summary)

            await self.db.commit()
            await self.db.refresh(summary)

            logger.info(
                f"Updated monthly summary for member {member_id}, {year}-{month:02d}"
            )
            return summary

        except ValueError:
            # Re-raise validation errors as-is
            raise
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Update monthly summary error: {str(e)}")
            raise RuntimeError(f"更新月度汇总时出错: {str(e)}")

    async def batch_update_monthly_summaries(
        self, year: int, month: int, member_ids: Optional[List[int]] = None
    ) -> Dict[str, int]:
        """
        批量更新月度考勤汇总

        Args:
            year: 年份
            month: 月份
            member_ids: 要更新的成员ID列表，None表示更新所有成员

        Returns:
            Dict: 更新结果统计

        Raises:
            ValueError: 输入参数无效
            RuntimeError: 批量更新过程出现错误
        """
        # 输入校验
        if not isinstance(year, int) or year < 2020 or year > 2050:
            logger.error(f"Invalid year: {year}")
            raise ValueError("年份必须在2020-2050范围内")

        if not isinstance(month, int) or month < 1 or month > 12:
            logger.error(f"Invalid month: {month}")
            raise ValueError("月份必须在1-12范围内")

        if member_ids is not None:
            if not isinstance(member_ids, list):
                logger.error(f"member_ids must be a list, got {type(member_ids)}")
                raise ValueError("成员ID列表必须为列表类型")

            for member_id in member_ids:
                if not isinstance(member_id, int) or member_id <= 0:
                    logger.error(f"Invalid member_id in list: {member_id}")
                    raise ValueError(f"成员ID必须为正整数: {member_id}")

        try:
            # 获取要更新的成员列表
            if member_ids:
                members_query = select(Member).where(Member.id.in_(member_ids))
            else:
                members_query = select(Member).where(Member.is_active.is_(True))

            members_result = await self.db.execute(members_query)
            members = members_result.scalars().all()

            updated_count = 0
            failed_count = 0

            for member in members:
                try:
                    await self.update_monthly_summary(member.id, year, month)
                    updated_count += 1
                except Exception as e:
                    logger.warning(
                        f"Failed to update summary for member {member.id}: {str(e)}"
                    )
                    failed_count += 1

            return {
                "updated": updated_count,
                "failed": failed_count,
                "total": len(members),
            }

        except ValueError:
            # Re-raise validation errors as-is
            raise
        except Exception as e:
            logger.error(f"Batch update monthly summaries error: {str(e)}")
            raise RuntimeError(f"批量更新月度汇总时出错: {str(e)}")

    async def apply_group_penalties(
        self, task: RepairTask, penalty_type: str
    ) -> List[int]:
        """
        应用组内惩罚（超时响应、差评等影响组内所有成员）

        Args:
            task: 触发惩罚的任务
            penalty_type: 惩罚类型 ("late_response", "negative_review")

        Returns:
            List[int]: 受影响的成员ID列表

        Raises:
            ValueError: 输入参数无效
            RuntimeError: 应用惩罚过程出现错误
        """
        # 输入校验
        if not task:
            logger.error("Task object is None or empty")
            raise ValueError("任务对象不能为空")

        if not hasattr(task, "id") or task.id is None:
            logger.error("Task ID is None or invalid")
            raise ValueError("任务ID无效")

        if not hasattr(task, "member") or task.member is None:
            logger.error(f"Task {task.id} has no associated member")
            raise ValueError(f"任务 {task.id} 没有关联的成员")

        valid_penalty_types = {"late_response", "late_completion", "negative_review"}
        if not isinstance(penalty_type, str) or penalty_type not in valid_penalty_types:
            logger.error(f"Invalid penalty_type: {penalty_type}")
            raise ValueError(f"惩罚类型无效，必须为: {', '.join(valid_penalty_types)}")

        try:
            # 获取任务处理人所在的组/部门的所有成员
            member_query = select(Member).where(
                and_(
                    Member.department == task.member.department,
                    Member.is_active,
                )
            )
            member_result = await self.db.execute(member_query)
            group_members = member_result.scalars().all()

            affected_member_ids = []

            # 为每个组成员添加惩罚标签
            for member in group_members:
                # 创建惩罚标签（如果不存在）
                _ = await self._get_or_create_penalty_tag(penalty_type)

                # 为该成员的当月汇总添加惩罚时长
                task_month = task.report_time.month
                task_year = task.report_time.year

                await self._apply_member_penalty(
                    member.id,
                    task_year,
                    task_month,
                    penalty_type,
                    self._get_penalty_minutes(penalty_type),
                )

                affected_member_ids.append(member.id)

            logger.info(
                f"Applied {penalty_type} penalty to {len(affected_member_ids)} members"
            )
            return affected_member_ids  # type: ignore[return-value]

        except ValueError:
            # Re-raise validation errors as-is
            raise
        except Exception as e:
            logger.error(f"Apply group penalties error: {str(e)}")
            raise RuntimeError(f"应用组内惩罚时出错: {str(e)}")

    # 私有方法

    async def _calculate_repair_tasks_hours(
        self, tasks: List[RepairTask]
    ) -> Dict[str, float]:
        """计算报修任务工时统计"""
        stats = {
            "total_hours": 0.0,
            "online_hours": 0.0,
            "offline_hours": 0.0,
            "rush_hours": 0.0,
            "positive_review_hours": 0.0,
            "penalty_hours": 0.0,
            "late_response_penalty_hours": 0.0,
            "late_completion_penalty_hours": 0.0,
            "negative_review_penalty_hours": 0.0,
        }

        for task in tasks:
            work_minutes = await self.calculate_task_work_minutes(task)

            # 累计各类工时
            stats["total_hours"] += work_minutes["total_minutes"] / 60.0

            if task.task_type == TaskType.ONLINE:
                stats["online_hours"] += work_minutes["base_minutes"] / 60.0
            else:
                stats["offline_hours"] += work_minutes["base_minutes"] / 60.0

            stats["rush_hours"] += work_minutes["rush_minutes"] / 60.0
            stats["positive_review_hours"] += (
                work_minutes["positive_review_minutes"] / 60.0
            )
            stats["penalty_hours"] += work_minutes["penalty_minutes"] / 60.0
            stats["late_response_penalty_hours"] += (
                work_minutes["late_response_penalty"] / 60.0
            )
            stats["late_completion_penalty_hours"] += (
                work_minutes["late_completion_penalty"] / 60.0
            )
            stats["negative_review_penalty_hours"] += (
                work_minutes["negative_review_penalty"] / 60.0
            )

        return stats

    def _is_response_overdue(self, task: RepairTask) -> bool:
        """检查是否超时响应"""
        if task.response_time or task.status != TaskStatus.PENDING:
            return False

        hours_since_report = (
            datetime.utcnow() - task.report_time
        ).total_seconds() / 3600
        return hours_since_report > self.RESPONSE_TIMEOUT_HOURS

    def _is_completion_overdue(self, task: RepairTask) -> bool:
        """检查是否超时处理"""
        if task.completion_time or not task.response_time:
            return False

        hours_since_response = (
            datetime.utcnow() - task.response_time
        ).total_seconds() / 3600
        return hours_since_response > self.COMPLETION_TIMEOUT_HOURS

    def _is_negative_review(self, task: RepairTask) -> bool:
        """检查是否为差评"""
        return task.rating is not None and task.rating <= 2

    async def _get_or_create_penalty_tag(self, penalty_type: str) -> TaskTag:
        """获取或创建惩罚标签"""
        tag_configs = {
            "late_response": {
                "name": "超时响应",
                "tag_type": TaskTagType.TIMEOUT_RESPONSE,
                "factory_method": "create_timeout_response_tag",
            },
            "late_completion": {
                "name": "超时处理",
                "tag_type": TaskTagType.TIMEOUT_PROCESSING,
                "factory_method": "create_timeout_processing_tag",
            },
            "negative_review": {
                "name": "差评",
                "tag_type": TaskTagType.BAD_RATING,
                "factory_method": "create_bad_rating_tag",
            },
        }

        config = tag_configs.get(penalty_type)
        if not config:
            raise ValueError(f"Unknown penalty type: {penalty_type}")

        tag_name = config["name"]

        # 查询现有标签
        query = select(TaskTag).where(TaskTag.name == tag_name)
        result = await self.db.execute(query)
        tag = result.scalar_one_or_none()

        if not tag:
            # 使用TaskTag的工厂方法创建标签
            factory_method_name = config["factory_method"]
            tag = getattr(TaskTag, factory_method_name)()
            self.db.add(tag)
            await self.db.commit()
            await self.db.refresh(tag)

        return tag

    def _get_penalty_minutes(self, penalty_type: str) -> int:
        """获取惩罚分钟数"""
        penalties = {
            "late_response": self.LATE_RESPONSE_PENALTY,
            "late_completion": self.LATE_COMPLETION_PENALTY,
            "negative_review": self.NEGATIVE_REVIEW_PENALTY,
        }
        return penalties.get(penalty_type, 0)

    async def _apply_member_penalty(
        self,
        member_id: int,
        year: int,
        month: int,
        penalty_type: str,
        penalty_minutes: int,
    ):
        """为成员应用惩罚时长"""
        # 获取或创建月度汇总
        summary_query = select(MonthlyAttendanceSummary).where(
            and_(
                MonthlyAttendanceSummary.member_id == member_id,
                MonthlyAttendanceSummary.year == year,
                MonthlyAttendanceSummary.month == month,
            )
        )
        summary_result = await self.db.execute(summary_query)
        summary = summary_result.scalar_one_or_none()

        if not summary:
            summary = MonthlyAttendanceSummary(
                member_id=member_id, year=year, month=month
            )
            self.db.add(summary)

        # 添加惩罚时长
        penalty_hours = penalty_minutes / 60.0
        summary.penalty_hours += penalty_hours

        if penalty_type == "late_response":
            summary.late_response_penalty_hours += penalty_hours
        elif penalty_type == "late_completion":
            summary.late_completion_penalty_hours += penalty_hours
        elif penalty_type == "negative_review":
            summary.negative_review_penalty_hours += penalty_hours

        # 重新计算总工时
        summary.total_hours = max(
            0.0,
            summary.repair_task_hours
            + summary.monitoring_hours
            + summary.assistance_hours
            + summary.carried_hours
            - summary.penalty_hours,
        )

        await self.db.commit()


class RushTaskMarkingService:
    """爆单标记服务"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def mark_rush_tasks_by_date(
        self,
        date_from: date,
        date_to: date,
        task_ids: Optional[List[int]] = None,
        marked_by: int = None,
    ) -> Dict[str, int]:
        """
        按日期批量标记爆单任务（重构版）
        同时更新任务的is_rush_order字段

        Args:
            date_from: 开始日期
            date_to: 结束日期
            task_ids: 指定的任务ID列表
            marked_by: 标记人ID

        Returns:
            Dict: 标记结果统计

        Raises:
            ValueError: 输入参数无效
            RuntimeError: 标记过程出现错误
        """
        # 输入校验
        if not isinstance(date_from, date):
            logger.error(f"date_from must be date object, got {type(date_from)}")
            raise ValueError("开始日期必须为date对象")

        if not isinstance(date_to, date):
            logger.error(f"date_to must be date object, got {type(date_to)}")
            raise ValueError("结束日期必须为date对象")

        if date_from > date_to:
            logger.error(f"date_from {date_from} is after date_to {date_to}")
            raise ValueError("开始日期不能晚于结束日期")

        if task_ids is not None:
            if not isinstance(task_ids, list):
                logger.error(f"task_ids must be list, got {type(task_ids)}")
                raise ValueError("任务ID列表必须为列表类型")

            for task_id in task_ids:
                if not isinstance(task_id, int) or task_id <= 0:
                    logger.error(f"Invalid task_id in list: {task_id}")
                    raise ValueError(f"任务ID必须为正整数: {task_id}")

        if marked_by is not None and (not isinstance(marked_by, int) or marked_by <= 0):
            logger.error(f"Invalid marked_by: {marked_by}")
            raise ValueError("标记人ID必须为正整数")

        try:
            # 构建查询
            query = (
                select(RepairTask)
                .options(selectinload(RepairTask.tags))
                .where(
                    and_(
                        RepairTask.report_time >= date_from,
                        RepairTask.report_time <= date_to,
                        RepairTask.status.in_(
                            [TaskStatus.COMPLETED, TaskStatus.IN_PROGRESS]
                        ),
                    )
                )
            )

            if task_ids:
                query = query.where(RepairTask.id.in_(task_ids))

            result = await self.db.execute(query)
            tasks = result.scalars().all()

            # 获取或创建爆单标签
            rush_tag = await self._get_or_create_rush_tag()

            marked_count = 0
            updated_count = 0

            for task in tasks:
                # 检查是否已经是爆单任务
                already_marked = task.is_rush_order or any(
                    tag.tag_type == TaskTagType.RUSH_ORDER
                    for tag in task.tags
                    if tag.is_active
                )

                if not already_marked:
                    # 标记为爆单任务
                    task.is_rush_order = True  # type: ignore[assignment]

                    # 添加爆单标签（如果还没有）
                    if rush_tag not in task.tags:
                        task.tags.append(rush_tag)

                    # 重新计算工时
                    task.update_work_minutes()

                    marked_count += 1

                # 确保工时计算正确（对于已标记的任务也重新计算）
                task.update_work_minutes()
                updated_count += 1

            await self.db.commit()

            logger.info(
                f"Marked {marked_count} new rush tasks, updated {updated_count} tasks total"
            )
            return {
                "marked": marked_count,
                "updated": updated_count,
                "total": len(tasks),
            }

        except ValueError:
            # Re-raise validation errors as-is
            raise
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Mark rush tasks error: {str(e)}")
            raise RuntimeError(f"标记爆单任务时出错: {str(e)}")

    async def _get_or_create_rush_tag(self) -> TaskTag:
        """获取或创建爆单标签（重构版）"""
        query = select(TaskTag).where(
            and_(TaskTag.name == "爆单任务", TaskTag.tag_type == TaskTagType.RUSH_ORDER)
        )
        result = await self.db.execute(query)
        tag = result.scalar_one_or_none()

        if not tag:
            # 使用TaskTag的工厂方法创建爆单标签
            tag = TaskTag.create_rush_order_tag()
            self.db.add(tag)
            await self.db.commit()
            await self.db.refresh(tag)

        return tag

    async def batch_recalculate_work_hours(
        self, date_from: date, date_to: date, member_ids: Optional[List[int]] = None
    ) -> Dict[str, int]:
        """
        批量重新计算工时（重构版）
        用于重构后工时逻辑的批量更新

        Args:
            date_from: 开始日期
            date_to: 结束日期
            member_ids: 指定的成员ID列表

        Returns:
            Dict: 重算结果统计

        Raises:
            ValueError: 输入参数无效
            RuntimeError: 重算过程出现错误
        """
        # 输入校验
        if not isinstance(date_from, date):
            logger.error(f"date_from must be date object, got {type(date_from)}")
            raise ValueError("开始日期必须为date对象")

        if not isinstance(date_to, date):
            logger.error(f"date_to must be date object, got {type(date_to)}")
            raise ValueError("结束日期必须为date对象")

        if date_from > date_to:
            logger.error(f"date_from {date_from} is after date_to {date_to}")
            raise ValueError("开始日期不能晚于结束日期")

        if member_ids is not None:
            if not isinstance(member_ids, list):
                logger.error(f"member_ids must be list, got {type(member_ids)}")
                raise ValueError("成员ID列表必须为列表类型")

            for member_id in member_ids:
                if not isinstance(member_id, int) or member_id <= 0:
                    logger.error(f"Invalid member_id in list: {member_id}")
                    raise ValueError(f"成员ID必须为正整数: {member_id}")

        try:
            # 构建查询
            query = (
                select(RepairTask)
                .options(selectinload(RepairTask.tags))
                .where(
                    and_(
                        RepairTask.report_time >= date_from,
                        RepairTask.report_time <= date_to,
                    )
                )
            )

            if member_ids:
                query = query.where(RepairTask.member_id.in_(member_ids))

            result = await self.db.execute(query)
            tasks = result.scalars().all()

            recalculated_count = 0

            for task in tasks:
                try:
                    # 重新计算工时
                    old_work_minutes = task.work_minutes
                    task.update_work_minutes()

                    if old_work_minutes != task.work_minutes:
                        logger.debug(
                            f"Task {task.id} work minutes updated: "
                            f"{old_work_minutes} -> {task.work_minutes}"
                        )

                    recalculated_count += 1

                except Exception as e:
                    logger.warning(
                        f"Failed to recalculate work hours for task {task.id}: {str(e)}"
                    )

            await self.db.commit()

            # 更新相关成员的月度汇总
            affected_members = set(task.member_id for task in tasks)
            affected_months = set(
                (task.report_time.year, task.report_time.month) for task in tasks
            )

            updated_summaries = 0
            work_hours_service = WorkHoursCalculationService(self.db)

            for member_id in affected_members:
                for year, month in affected_months:
                    try:
                        await work_hours_service.update_monthly_summary(
                            member_id, year, month
                        )
                        updated_summaries += 1
                    except Exception as e:
                        logger.warning(
                            f"Failed to update summary for member {member_id}, "
                            f"{year}-{month}: {str(e)}"
                        )

            logger.info(
                f"Batch recalculated {recalculated_count} tasks, "
                f"updated {updated_summaries} summaries"
            )
            return {
                "recalculated_tasks": recalculated_count,
                "updated_summaries": updated_summaries,
                "total_tasks": len(tasks),
                "affected_members": len(affected_members),
            }

        except ValueError:
            # Re-raise validation errors as-is
            raise
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Batch recalculate work hours error: {str(e)}")
            raise RuntimeError(f"批量重新计算工时时出错: {str(e)}")
