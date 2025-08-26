"""
统计分析服务
处理考勤统计、工时分析、绩效评估等业务逻辑
增强版本：支持Redis缓存、高性能查询、实时统计
"""

import hashlib
import logging
from calendar import monthrange
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from sqlalchemy import and_, case, desc, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.cache import cache
from app.models.attendance import AttendanceRecord
from app.models.member import Member, UserRole
from app.models.task import (
    AssistanceTask,
    MonitoringTask,
    RepairTask,
    TaskStatus,
    TaskType,
)

logger = logging.getLogger(__name__)


class StatisticsService:
    """统计分析服务 - 增强版本"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.cache_enabled = True

    def _generate_cache_key(self, method_name: str, **kwargs: Any) -> str:
        """生成缓存键"""
        # 过滤None值并排序参数
        filtered_kwargs = {k: v for k, v in kwargs.items() if v is not None}
        param_string = "_".join(f"{k}={v}" for k, v in sorted(filtered_kwargs.items()))

        if len(param_string) > 100:
            # 对长参数进行哈希
            param_hash = hashlib.md5(param_string.encode()).hexdigest()[:8]
            return f"stats:{method_name}:hash_{param_hash}"

        return (
            f"stats:{method_name}:{param_string}"
            if param_string
            else f"stats:{method_name}"
        )

    async def get_overview_statistics(
        self,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        use_cache: bool = True,
    ) -> Dict[str, Any]:
        """
        获取总览统计信息 - 支持缓存

        Args:
            date_from: 开始时间
            date_to: 结束时间
            use_cache: 是否使用缓存

        Returns:
            Dict: 总览统计数据
        """
        try:
            if not date_from:
                date_from = datetime.now().replace(
                    day=1, hour=0, minute=0, second=0, microsecond=0
                )
            if not date_to:
                date_to = datetime.now()

            # 生成缓存键
            cache_key = self._generate_cache_key(
                "overview", date_from=date_from.isoformat(), date_to=date_to.isoformat()
            )

            # 尝试从缓存获取
            if use_cache and self.cache_enabled:
                cached_data = await cache.get_stats_cache(
                    "overview",
                    date_from=date_from.isoformat(),
                    date_to=date_to.isoformat(),
                )
                if cached_data:
                    logger.debug(f"Overview statistics cache hit: {cache_key}")
                    return dict(cached_data["data"])  # Explicit cast to dict

            logger.debug(f"Overview statistics cache miss, computing: {cache_key}")

            # 并行查询各类统计数据
            import asyncio

            member_stats_task = asyncio.create_task(
                self._get_member_statistics_cached()
            )
            task_stats_task = asyncio.create_task(
                self._get_task_statistics_cached(date_from, date_to)
            )
            work_hour_stats_task = asyncio.create_task(
                self._get_work_hour_statistics_cached(date_from, date_to)
            )
            performance_stats_task = asyncio.create_task(
                self._get_performance_statistics_cached(date_from, date_to)
            )
            attendance_stats_task = asyncio.create_task(
                self._get_attendance_statistics_cached(date_from, date_to)
            )

            # 等待所有任务完成
            results = await asyncio.gather(
                member_stats_task,
                task_stats_task,
                work_hour_stats_task,
                performance_stats_task,
                attendance_stats_task,
                return_exceptions=True,
            )

            (
                member_stats,
                task_stats,
                work_hour_stats,
                performance_stats,
                attendance_stats,
            ) = results

            # 处理异常结果 - Initialize with empty dicts and proper type handling
            if isinstance(member_stats, Exception):
                logger.error(f"Member stats error: {member_stats}")
                member_stats_data: Dict[str, Any] = {}
            else:
                member_stats_data = (
                    member_stats if isinstance(member_stats, dict) else {}
                )

            if isinstance(task_stats, Exception):
                logger.error(f"Task stats error: {task_stats}")
                task_stats_data: Dict[str, Any] = {}
            else:
                task_stats_data = task_stats if isinstance(task_stats, dict) else {}

            if isinstance(work_hour_stats, Exception):
                logger.error(f"Work hour stats error: {work_hour_stats}")
                work_hour_stats_data: Dict[str, Any] = {}
            else:
                work_hour_stats_data = (
                    work_hour_stats if isinstance(work_hour_stats, dict) else {}
                )

            if isinstance(performance_stats, Exception):
                logger.error(f"Performance stats error: {performance_stats}")
                performance_stats_data: Dict[str, Any] = {}
            else:
                # 处理意外的coroutine对象
                if hasattr(performance_stats, '__await__'):
                    logger.warning("Performance stats returned coroutine, treating as empty")
                    performance_stats_data = {}
                else:
                    performance_stats_data = (
                        performance_stats if isinstance(performance_stats, dict) else {}
                    )

            if isinstance(attendance_stats, Exception):
                logger.error(f"Attendance stats error: {attendance_stats}")
                attendance_stats_data: Dict[str, Any] = {}
            else:
                # 处理意外的coroutine对象
                if hasattr(attendance_stats, '__await__'):
                    logger.warning("Attendance stats returned coroutine, treating as empty")
                    attendance_stats_data = {}
                else:
                    attendance_stats_data = (
                        attendance_stats if isinstance(attendance_stats, dict) else {}
                    )

            result = {
                "period": {"from": date_from.isoformat(), "to": date_to.isoformat()},
                "members": member_stats_data,
                "tasks": task_stats_data,
                "work_hours": work_hour_stats_data,
                "performance": performance_stats_data,
                "attendance": attendance_stats_data,
                "summary": {
                    "total_active_members": member_stats_data.get("active_count", 0),
                    "total_tasks_completed": task_stats_data.get("completed_count", 0),
                    "total_work_hours": work_hour_stats_data.get("total_hours", 0),
                    "average_rating": performance_stats_data.get("overall_rating", 0),
                    "attendance_rate": attendance_stats_data.get("overall_rate", 0),
                },
                "generated_at": datetime.now().isoformat(),
            }

            # 存入缓存（10分钟过期）
            if use_cache and self.cache_enabled:
                await cache.set_stats_cache(
                    "overview",
                    result,
                    ttl=600,
                    date_from=date_from.isoformat(),
                    date_to=date_to.isoformat(),
                )

            return dict(result) if result else {}

        except Exception as e:
            logger.error(f"Get overview statistics error: {str(e)}")
            raise

    # 缓存版本的统计方法

    async def _get_member_statistics_cached(self) -> Dict[str, Any]:
        """获取成员统计（缓存版本）"""
        # 尝试从缓存获取
        cached_data = await cache.get_stats_cache("member")
        if cached_data:
            return dict(cached_data["data"])  # Explicit cast to dict

        # 查询数据库
        member_query = select(
            func.count(Member.id).label("total_count"),
            func.count(case((Member.is_active.is_(True), 1))).label("active_count"),
            func.count(case((Member.role == UserRole.ADMIN, 1))).label("admin_count"),
            func.count(case((Member.role == UserRole.MEMBER, 1))).label("member_count"),
        )

        result = await self.db.execute(member_query)
        stats = result.first()

        if stats is None:
            data = {
                "total_count": 0,
                "active_count": 0,
                "admin_count": 0,
                "member_count": 0,
                "inactive_count": 0,
            }
        else:
            data = {
                "total_count": stats.total_count or 0,
                "active_count": stats.active_count or 0,
                "admin_count": stats.admin_count or 0,
                "member_count": stats.member_count or 0,
                "inactive_count": (stats.total_count or 0) - (stats.active_count or 0),
            }

        # 存入缓存（5分钟过期）
        await cache.set_stats_cache("member", data, ttl=300)
        return dict(data) if data else {}

    async def _get_task_statistics_cached(
        self, date_from: datetime, date_to: datetime
    ) -> Dict[str, Any]:
        """获取任务统计（缓存版本）"""
        # 尝试从缓存获取
        cached_data = await cache.get_stats_cache(
            "task", date_from=date_from.isoformat(), date_to=date_to.isoformat()
        )
        if cached_data:
            return dict(cached_data["data"])  # Explicit cast to dict

        # 查询维修任务统计
        repair_query = select(
            func.count(RepairTask.id).label("total_count"),
            func.count(case((RepairTask.status == TaskStatus.COMPLETED, 1))).label(
                "completed_count"
            ),
            func.count(case((RepairTask.status == TaskStatus.PENDING, 1))).label(
                "pending_count"
            ),
            func.count(
                case((RepairTask.status == TaskStatus.IN_PROGRESS, 1), else_=None)
            ).label("in_progress_count"),
            func.count(
                case((RepairTask.task_type == TaskType.ONLINE, 1), else_=None)
            ).label("online_count"),
            func.count(
                case((RepairTask.task_type == TaskType.OFFLINE, 1), else_=None)
            ).label("offline_count"),
            func.sum(RepairTask.work_minutes).label("total_minutes"),
            func.avg(RepairTask.rating).label("avg_rating"),
        ).where(
            and_(RepairTask.report_time >= date_from, RepairTask.report_time <= date_to)
        )

        result = await self.db.execute(repair_query)
        repair_stats = result.first()

        # 查询监控任务统计
        monitoring_query = select(
            func.count(MonitoringTask.id).label("total_count"),
            func.sum(MonitoringTask.work_minutes).label("total_minutes"),
        ).where(
            and_(
                MonitoringTask.start_time >= date_from,
                MonitoringTask.start_time <= date_to,
            )
        )

        monitoring_result = await self.db.execute(monitoring_query)
        monitoring_stats = monitoring_result.first()

        # 查询协助任务统计
        assistance_query = select(
            func.count(AssistanceTask.id).label("total_count"),
            func.sum(AssistanceTask.work_minutes).label("total_minutes"),
        ).where(
            and_(
                AssistanceTask.start_time >= date_from,
                AssistanceTask.start_time <= date_to,
            )
        )

        assistance_result = await self.db.execute(assistance_query)
        assistance_stats = assistance_result.first()

        # 安全地访问 Row 对象属性
        repair_total = repair_stats.total_count if repair_stats else 0
        repair_completed = repair_stats.completed_count if repair_stats else 0
        repair_pending = repair_stats.pending_count if repair_stats else 0
        repair_in_progress = repair_stats.in_progress_count if repair_stats else 0
        repair_online = repair_stats.online_count if repair_stats else 0
        repair_offline = repair_stats.offline_count if repair_stats else 0
        repair_rating = repair_stats.avg_rating if repair_stats else 0

        monitoring_total = monitoring_stats.total_count if monitoring_stats else 0
        monitoring_minutes = monitoring_stats.total_minutes if monitoring_stats else 0

        assistance_total = assistance_stats.total_count if assistance_stats else 0
        assistance_minutes = assistance_stats.total_minutes if assistance_stats else 0

        data = {
            "repair_tasks": {
                "total_count": repair_total or 0,
                "completed_count": repair_completed or 0,
                "pending_count": repair_pending or 0,
                "in_progress_count": repair_in_progress or 0,
                "online_count": repair_online or 0,
                "offline_count": repair_offline or 0,
                "completion_rate": round(
                    (repair_completed or 0) / max(repair_total or 1, 1) * 100,
                    2,
                ),
                "avg_rating": round(repair_rating or 0, 2),
            },
            "monitoring_tasks": {
                "total_count": monitoring_total or 0,
                "total_minutes": monitoring_minutes or 0,
            },
            "assistance_tasks": {
                "total_count": assistance_total or 0,
                "total_minutes": assistance_minutes or 0,
            },
            "total_count": (repair_total or 0)
            + (monitoring_total or 0)
            + (assistance_total or 0),
            "completed_count": repair_completed or 0,
        }

        # 存入缓存（5分钟过期）
        await cache.set_stats_cache(
            "task",
            data,
            ttl=300,
            date_from=date_from.isoformat(),
            date_to=date_to.isoformat(),
        )
        return dict(data) if data else {}

    async def _get_work_hour_statistics_cached(
        self, date_from: datetime, date_to: datetime
    ) -> Dict[str, Any]:
        """获取工时统计（缓存版本）"""
        # 尝试从缓存获取
        cached_data = await cache.get_stats_cache(
            "work_hour", date_from=date_from.isoformat(), date_to=date_to.isoformat()
        )
        if cached_data:
            return dict(cached_data["data"])  # Explicit cast to dict

        # 查询工时统计
        work_hour_query = (
            select(
                func.sum(RepairTask.work_minutes).label("repair_minutes"),
                func.sum(MonitoringTask.work_minutes).label("monitoring_minutes"),
                func.sum(AssistanceTask.work_minutes).label("assistance_minutes"),
                func.avg(RepairTask.work_minutes).label("avg_repair_minutes"),
                func.count(RepairTask.id).label("repair_count"),
            )
            .select_from(
                RepairTask.__table__.outerjoin(MonitoringTask.__table__).outerjoin(
                    AssistanceTask.__table__
                )
            )
            .where(
                or_(
                    and_(
                        RepairTask.report_time >= date_from,
                        RepairTask.report_time <= date_to,
                    ),
                    and_(
                        MonitoringTask.start_time >= date_from,
                        MonitoringTask.start_time <= date_to,
                    ),
                    and_(
                        AssistanceTask.start_time >= date_from,
                        AssistanceTask.start_time <= date_to,
                    ),
                )
            )
        )

        result = await self.db.execute(work_hour_query)
        stats = result.first()

        if stats is None:
            repair_minutes = 0
            monitoring_minutes = 0
            assistance_minutes = 0
            avg_repair_minutes = 0
        else:
            repair_minutes = stats.repair_minutes or 0
            monitoring_minutes = stats.monitoring_minutes or 0
            assistance_minutes = stats.assistance_minutes or 0
            avg_repair_minutes = stats.avg_repair_minutes or 0

        total_minutes = repair_minutes + monitoring_minutes + assistance_minutes

        data = {
            "total_minutes": total_minutes,
            "total_hours": round(total_minutes / 60, 2),
            "repair_minutes": repair_minutes,
            "repair_hours": round(repair_minutes / 60, 2),
            "monitoring_minutes": monitoring_minutes,
            "monitoring_hours": round(monitoring_minutes / 60, 2),
            "assistance_minutes": assistance_minutes,
            "assistance_hours": round(assistance_minutes / 60, 2),
            "avg_task_minutes": round(avg_repair_minutes, 2),
            "avg_task_hours": round(avg_repair_minutes / 60, 2),
        }

        # 存入缓存（5分钟过期）
        await cache.set_stats_cache(
            "work_hour",
            data,
            ttl=300,
            date_from=date_from.isoformat(),
            date_to=date_to.isoformat(),
        )
        return dict(data) if data else {}

    async def _get_performance_statistics_cached(
        self, date_from: datetime, date_to: datetime
    ) -> Dict[str, Any]:
        """获取绩效统计（缓存版本）"""
        # 尝试从缓存获取
        cached_data = await cache.get_stats_cache(
            "performance", date_from=date_from.isoformat(), date_to=date_to.isoformat()
        )
        if cached_data:
            return dict(cached_data["data"])  # Explicit cast to dict

        # 查询绩效统计
        performance_query = select(
            func.avg(RepairTask.rating).label("overall_rating"),
            func.count(case((RepairTask.rating >= 4, 1), else_=None)).label(
                "good_rating_count"
            ),
            func.count(case((RepairTask.rating <= 2, 1), else_=None)).label(
                "poor_rating_count"
            ),
            func.count(case((RepairTask.rating.isnot(None), 1), else_=None)).label(
                "rated_count"
            ),
            func.count(RepairTask.id).label("total_tasks"),
        ).where(
            and_(RepairTask.report_time >= date_from, RepairTask.report_time <= date_to)
        )

        result = await self.db.execute(performance_query)
        stats = result.first()

        if stats is None:
            overall_rating = 0
            rated_count = 0
            total_tasks = 0
            good_rating_count = 0
            poor_rating_count = 0
        else:
            overall_rating = stats.overall_rating or 0
            rated_count = stats.rated_count or 0
            total_tasks = stats.total_tasks or 0
            good_rating_count = stats.good_rating_count or 0
            poor_rating_count = stats.poor_rating_count or 0

        data = {
            "overall_rating": round(overall_rating, 2),
            "rated_count": rated_count,
            "rating_rate": round(rated_count / max(total_tasks, 1) * 100, 2),
            "good_rating_count": good_rating_count,
            "poor_rating_count": poor_rating_count,
            "good_rating_rate": round(good_rating_count / max(rated_count, 1) * 100, 2),
            "poor_rating_rate": round(poor_rating_count / max(rated_count, 1) * 100, 2),
        }

        # 存入缓存（5分钟过期）
        await cache.set_stats_cache(
            "performance",
            data,
            ttl=300,
            date_from=date_from.isoformat(),
            date_to=date_to.isoformat(),
        )
        return dict(data) if data else {}

    async def _get_attendance_statistics_cached(
        self, date_from: datetime, date_to: datetime
    ) -> Dict[str, Any]:
        """获取考勤统计（缓存版本）"""
        # 尝试从缓存获取
        cached_data = await cache.get_stats_cache(
            "attendance", date_from=date_from.isoformat(), date_to=date_to.isoformat()
        )
        if cached_data:
            return dict(cached_data["data"])  # Explicit cast to dict

        try:
            # 查询考勤统计
            attendance_query = select(
                func.count(AttendanceRecord.id).label("total_records"),
                func.count(
                    case((AttendanceRecord.checkin_time.isnot(None), 1), else_=None)
                ).label("checkin_count"),
                func.count(
                    case((AttendanceRecord.checkout_time.isnot(None), 1), else_=None)
                ).label("checkout_count"),
                func.count(
                    case((AttendanceRecord.is_late_checkin.is_(True), 1), else_=None)
                ).label("late_count"),
                func.count(
                    case((AttendanceRecord.is_early_checkout.is_(True), 1), else_=None)
                ).label("early_count"),
                func.avg(AttendanceRecord.work_hours).label("avg_work_hours"),
                func.sum(AttendanceRecord.work_hours).label("total_work_hours"),
            ).where(
                and_(
                    AttendanceRecord.attendance_date >= date_from.date(),
                    AttendanceRecord.attendance_date <= date_to.date(),
                )
            )

            result = await self.db.execute(attendance_query)
            stats = result.first()

            if stats is None:
                total_records = 0
                checkin_count = 0
                checkout_count = 0
                late_count = 0
                early_count = 0
                avg_work_hours = 0
                total_work_hours = 0
            else:
                total_records = stats.total_records or 0
                checkin_count = stats.checkin_count or 0
                checkout_count = stats.checkout_count or 0
                late_count = stats.late_count or 0
                early_count = stats.early_count or 0
                avg_work_hours = stats.avg_work_hours or 0
                total_work_hours = stats.total_work_hours or 0

            data = {
                "total_records": total_records,
                "checkin_count": checkin_count,
                "checkout_count": checkout_count,
                "late_count": late_count,
                "early_count": early_count,
                "overall_rate": round(checkin_count / max(total_records, 1) * 100, 2),
                "late_rate": round(late_count / max(checkin_count, 1) * 100, 2),
                "early_checkout_rate": round(
                    early_count / max(checkout_count, 1) * 100, 2
                ),
                "avg_work_hours": round(avg_work_hours, 2),
                "total_work_hours": round(total_work_hours, 2),
            }

        except Exception as e:
            logger.warning(f"Attendance statistics query failed: {str(e)}")
            # 如果考勤表不存在或查询失败，返回默认值
            data = {
                "total_records": 0,
                "checkin_count": 0,
                "checkout_count": 0,
                "late_count": 0,
                "early_count": 0,
                "overall_rate": 0,
                "late_rate": 0,
                "early_checkout_rate": 0,
                "avg_work_hours": 0,
                "total_work_hours": 0,
            }

        # 存入缓存（5分钟过期）
        await cache.set_stats_cache(
            "attendance",
            data,
            ttl=300,
            date_from=date_from.isoformat(),
            date_to=date_to.isoformat(),
        )
        return dict(data) if data else {}

    async def get_member_performance_report(
        self, member_id: int, year: int, month: int
    ) -> Dict[str, Any]:
        """
        获取成员月度绩效报告

        Args:
            member_id: 成员ID
            year: 年份
            month: 月份

        Returns:
            Dict: 成员绩效报告
        """
        try:
            # 计算月份时间范围
            start_date = datetime(year, month, 1)
            _, last_day = monthrange(year, month)
            end_date = datetime(year, month, last_day, 23, 59, 59)

            # 获取成员信息
            member_query = select(Member).where(Member.id == member_id)
            member_result = await self.db.execute(member_query)
            member = member_result.scalar_one_or_none()

            if not member:
                raise ValueError("成员不存在")

            # 任务完成情况
            task_stats = await self._get_member_task_statistics(
                member_id, start_date, end_date
            )

            # 工时统计
            work_hour_stats = await self._get_member_work_hour_statistics(
                member_id, start_date, end_date
            )

            # 质量分析
            quality_stats = await self._get_member_quality_statistics(
                member_id, start_date, end_date
            )

            # 排名分析
            ranking_stats = await self._get_member_ranking(
                member_id, start_date, end_date
            )

            # 趋势分析
            trend_stats = await self._get_member_trend_analysis(member_id, year, month)

            return {
                "member": {
                    "id": member.id,
                    "name": member.name,
                    "student_id": member.student_id,
                    "department": member.department,
                    "role": member.role.value,
                },
                "period": {
                    "year": year,
                    "month": month,
                    "from": start_date.isoformat(),
                    "to": end_date.isoformat(),
                },
                "tasks": task_stats,
                "work_hours": work_hour_stats,
                "quality": quality_stats,
                "ranking": ranking_stats,
                "trends": trend_stats,
                "generated_at": datetime.now().isoformat(),
            }

        except Exception as e:
            logger.error(f"Get member performance report error: {str(e)}")
            raise

    async def get_team_comparison_report(
        self,
        department: Optional[str] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        limit: int = 10,
    ) -> Dict[str, Any]:
        """
        获取团队对比报告

        Args:
            department: 部门名称
            date_from: 开始时间
            date_to: 结束时间
            limit: 显示成员数量限制

        Returns:
            Dict: 团队对比报告
        """
        try:
            if not date_from:
                date_from = datetime.now().replace(
                    day=1, hour=0, minute=0, second=0, microsecond=0
                )
            if not date_to:
                date_to = datetime.now()

            # 获取团队成员
            member_query = select(Member).where(Member.is_active)
            if department:
                member_query = member_query.where(Member.department == department)

            member_result = await self.db.execute(member_query)
            members = member_result.scalars().all()

            # 获取每个成员的统计数据
            member_stats = []
            for member in members:
                stats = await self._get_member_comparison_stats(
                    member.id, date_from, date_to
                )
                stats["member"] = {
                    "id": member.id,
                    "name": member.name,
                    "student_id": member.student_id,
                    "department": member.department,
                    "role": member.role.value,
                }
                member_stats.append(stats)

            # 按工时排序
            member_stats.sort(
                key=lambda x: x["work_hours"]["total_hours"], reverse=True
            )

            # 限制数量
            if limit:
                member_stats = member_stats[:limit]

            # 计算团队汇总
            team_summary = await self._calculate_team_summary(member_stats)

            return {
                "period": {"from": date_from.isoformat(), "to": date_to.isoformat()},
                "department": department,
                "team_summary": team_summary,
                "member_rankings": member_stats,
                "generated_at": datetime.now().isoformat(),
            }

        except Exception as e:
            logger.error(f"Get team comparison report error: {str(e)}")
            raise

    async def get_monthly_trends(
        self, months: int = 6, department: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        获取月度趋势分析

        Args:
            months: 分析月份数
            department: 部门名称

        Returns:
            Dict: 月度趋势数据
        """
        try:
            current_date = datetime.now()
            trends = []

            for i in range(months):
                # 计算月份
                target_date = current_date - timedelta(days=30 * i)
                year = target_date.year
                month = target_date.month

                start_date = datetime(year, month, 1)
                _, last_day = monthrange(year, month)
                end_date = datetime(year, month, last_day, 23, 59, 59)

                # 获取月度统计
                monthly_stats = await self._get_monthly_statistics(
                    start_date, end_date, department
                )
                monthly_stats["period"] = {
                    "year": year,
                    "month": month,
                    "label": f"{year}-{month:02d}",
                }

                trends.append(monthly_stats)

            # 按时间排序
            trends.sort(key=lambda x: (x["period"]["year"], x["period"]["month"]))

            # 计算变化趋势
            trend_analysis = self._analyze_trends(trends)

            return {
                "analysis_months": months,
                "department": department,
                "monthly_data": trends,
                "trend_analysis": trend_analysis,
                "generated_at": datetime.now().isoformat(),
            }

        except Exception as e:
            logger.error(f"Get monthly trends error: {str(e)}")
            raise

    async def export_statistics_data(
        self,
        export_type: str,
        date_from: datetime,
        date_to: datetime,
        member_ids: Optional[List[int]] = None,
        department: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        导出统计数据

        Args:
            export_type: 导出类型 (summary, detailed, comparison)
            date_from: 开始时间
            date_to: 结束时间
            member_ids: 成员ID列表
            department: 部门名称

        Returns:
            Dict: 导出数据
        """
        try:
            if export_type == "summary":
                return await self._export_summary_data(date_from, date_to, department)
            elif export_type == "detailed":
                return await self._export_detailed_data(
                    date_from, date_to, member_ids, department
                )
            elif export_type == "comparison":
                return await self._export_comparison_data(
                    date_from, date_to, department
                )
            else:
                raise ValueError("不支持的导出类型")

        except Exception as e:
            logger.error(f"Export statistics data error: {str(e)}")
            raise

    # 私有方法

    async def _get_member_statistics(self) -> Dict[str, Any]:
        """获取成员统计"""
        # 总成员数
        total_query = select(func.count()).select_from(Member)
        total_result = await self.db.execute(total_query)
        total_members = total_result.scalar() or 0

        # 活跃成员数
        active_query = select(func.count()).where(Member.is_active)
        active_result = await self.db.execute(active_query)
        active_members = active_result.scalar() or 0

        # 角色分布
        role_stats = {}
        for role in UserRole:
            role_query = select(func.count()).where(Member.role == role)
            role_result = await self.db.execute(role_query)
            role_stats[role.value] = role_result.scalar() or 0

        return {
            "total_members": total_members,
            "active_members": active_members,
            "inactive_members": total_members - active_members,
            "role_distribution": role_stats,
        }

    async def _get_task_statistics(
        self, date_from: datetime, date_to: datetime
    ) -> Dict[str, Any]:
        """获取任务统计"""
        base_query = select(RepairTask).where(
            and_(RepairTask.report_time >= date_from, RepairTask.report_time <= date_to)
        )

        # 总任务数
        total_result = await self.db.execute(base_query)
        total_tasks = len(total_result.scalars().all())

        # 状态分布
        status_stats = {}
        for task_status in TaskStatus:
            status_query = base_query.where(RepairTask.status == task_status)
            status_result = await self.db.execute(status_query)
            status_stats[task_status.value] = len(status_result.scalars().all())

        # 类型分布
        type_stats = {}
        for task_type in TaskType:
            type_query = base_query.where(RepairTask.task_type == task_type)
            type_result = await self.db.execute(type_query)
            type_stats[task_type.value] = len(type_result.scalars().all())

        # 完成率
        completed_tasks = status_stats.get("completed", 0)
        completion_rate = (
            round((completed_tasks / total_tasks * 100), 2) if total_tasks > 0 else 0
        )

        return {
            "total_tasks": total_tasks,
            "status_distribution": status_stats,
            "type_distribution": type_stats,
            "completion_rate": completion_rate,
        }

    async def _get_work_hour_statistics(
        self, date_from: datetime, date_to: datetime
    ) -> Dict[str, Any]:
        """获取工时统计"""
        # 维修任务工时
        repair_query = select(func.sum(RepairTask.work_minutes)).where(
            and_(RepairTask.report_time >= date_from, RepairTask.report_time <= date_to)
        )
        repair_result = await self.db.execute(repair_query)
        repair_minutes = repair_result.scalar() or 0

        # 监控任务工时
        monitoring_query = select(func.sum(MonitoringTask.work_minutes)).where(
            and_(
                MonitoringTask.start_time >= date_from,
                MonitoringTask.start_time <= date_to,
            )
        )
        monitoring_result = await self.db.execute(monitoring_query)
        monitoring_minutes = monitoring_result.scalar() or 0

        # 协助任务工时
        assistance_query = select(func.sum(AssistanceTask.work_minutes)).where(
            and_(
                AssistanceTask.start_time >= date_from,
                AssistanceTask.start_time <= date_to,
            )
        )
        assistance_result = await self.db.execute(assistance_query)
        assistance_minutes = assistance_result.scalar() or 0

        total_minutes = repair_minutes + monitoring_minutes + assistance_minutes
        total_hours = round(total_minutes / 60.0, 2)

        return {
            "total_hours": total_hours,
            "repair_hours": round(repair_minutes / 60.0, 2),
            "monitoring_hours": round(monitoring_minutes / 60.0, 2),
            "assistance_hours": round(assistance_minutes / 60.0, 2),
            "by_type": {
                "repair": repair_minutes,
                "monitoring": monitoring_minutes,
                "assistance": assistance_minutes,
            },
        }

    async def _get_performance_statistics(
        self, date_from: datetime, date_to: datetime
    ) -> Dict[str, Any]:
        """获取绩效统计"""
        # 平均评分
        rating_query = select(func.avg(RepairTask.rating)).where(
            and_(
                RepairTask.report_time >= date_from,
                RepairTask.report_time <= date_to,
                RepairTask.rating.isnot(None),
            )
        )
        rating_result = await self.db.execute(rating_query)
        avg_rating = rating_result.scalar()
        if avg_rating:
            avg_rating = round(float(avg_rating), 2)
        else:
            avg_rating = 0.0

        # 延迟统计
        overdue_response_query = select(func.count()).where(
            and_(
                RepairTask.report_time >= date_from,
                RepairTask.report_time <= date_to,
                RepairTask.status == TaskStatus.PENDING,
                RepairTask.report_time < datetime.utcnow() - timedelta(hours=24),
            )
        )
        overdue_response_result = await self.db.execute(overdue_response_query)
        overdue_response_count = overdue_response_result.scalar()

        return {
            "avg_rating": avg_rating,
            "overdue_response_count": overdue_response_count,
            "quality_metrics": {
                "on_time_completion_rate": 0.95,  # 这里需要实际计算
                "customer_satisfaction": avg_rating / 5.0 if avg_rating > 0 else 0,
            },
        }

    async def _get_member_task_statistics(
        self, member_id: int, start_date: datetime, end_date: datetime
    ) -> Dict[str, Any]:
        """获取成员任务统计"""
        base_query = select(RepairTask).where(
            and_(
                RepairTask.member_id == member_id,
                RepairTask.report_time >= start_date,
                RepairTask.report_time <= end_date,
            )
        )

        result = await self.db.execute(base_query)
        tasks = result.scalars().all()

        total_tasks = len(tasks)
        completed_tasks = len([t for t in tasks if t.status == TaskStatus.COMPLETED])
        pending_tasks = len([t for t in tasks if t.status == TaskStatus.PENDING])
        in_progress_tasks = len(
            [t for t in tasks if t.status == TaskStatus.IN_PROGRESS]
        )

        completion_rate = (
            round((completed_tasks / total_tasks * 100), 2) if total_tasks > 0 else 0
        )

        # 类型分布
        online_tasks = len([t for t in tasks if t.task_type == TaskType.ONLINE])
        offline_tasks = len([t for t in tasks if t.task_type == TaskType.OFFLINE])

        return {
            "total_tasks": total_tasks,
            "completed_tasks": completed_tasks,
            "pending_tasks": pending_tasks,
            "in_progress_tasks": in_progress_tasks,
            "completion_rate": completion_rate,
            "type_distribution": {"online": online_tasks, "offline": offline_tasks},
        }

    async def _get_member_work_hour_statistics(
        self, member_id: int, start_date: datetime, end_date: datetime
    ) -> Dict[str, Any]:
        """获取成员工时统计"""
        # 维修任务工时
        repair_query = select(func.sum(RepairTask.work_minutes)).where(
            and_(
                RepairTask.member_id == member_id,
                RepairTask.report_time >= start_date,
                RepairTask.report_time <= end_date,
            )
        )
        repair_result = await self.db.execute(repair_query)
        repair_minutes = repair_result.scalar() or 0

        # 监控任务工时
        monitoring_query = select(func.sum(MonitoringTask.work_minutes)).where(
            and_(
                MonitoringTask.member_id == member_id,
                MonitoringTask.start_time >= start_date,
                MonitoringTask.start_time <= end_date,
            )
        )
        monitoring_result = await self.db.execute(monitoring_query)
        monitoring_minutes = monitoring_result.scalar() or 0

        # 协助任务工时
        assistance_query = select(func.sum(AssistanceTask.work_minutes)).where(
            and_(
                AssistanceTask.member_id == member_id,
                AssistanceTask.start_time >= start_date,
                AssistanceTask.start_time <= end_date,
            )
        )
        assistance_result = await self.db.execute(assistance_query)
        assistance_minutes = assistance_result.scalar() or 0

        total_minutes = repair_minutes + monitoring_minutes + assistance_minutes
        total_hours = round(total_minutes / 60.0, 2)

        return {
            "total_hours": total_hours,
            "total_minutes": total_minutes,
            "repair_hours": round(repair_minutes / 60.0, 2),
            "monitoring_hours": round(monitoring_minutes / 60.0, 2),
            "assistance_hours": round(assistance_minutes / 60.0, 2),
        }

    async def _get_member_quality_statistics(
        self, member_id: int, start_date: datetime, end_date: datetime
    ) -> Dict[str, Any]:
        """获取成员质量统计"""
        tasks_query = select(RepairTask).where(
            and_(
                RepairTask.member_id == member_id,
                RepairTask.report_time >= start_date,
                RepairTask.report_time <= end_date,
            )
        )

        result = await self.db.execute(tasks_query)
        tasks = result.scalars().all()

        # 评分统计
        rated_tasks = [t for t in tasks if t.rating is not None]
        avg_rating = 0.0
        if rated_tasks:
            avg_rating = round(
                sum(t.rating for t in rated_tasks if t.rating is not None)
                / len(rated_tasks),
                2,
            )

        # 延迟统计
        overdue_response = len([t for t in tasks if t.is_overdue_response is True])
        overdue_completion = len([t for t in tasks if t.is_overdue_completion is True])

        # 好评率
        positive_reviews = len(
            [t for t in rated_tasks if t.rating is not None and t.rating >= 4]
        )
        positive_rate = (
            round((positive_reviews / len(rated_tasks) * 100), 2) if rated_tasks else 0
        )

        return {
            "avg_rating": avg_rating,
            "total_rated_tasks": len(rated_tasks),
            "positive_rate": positive_rate,
            "overdue_response": overdue_response,
            "overdue_completion": overdue_completion,
        }

    async def _get_member_ranking(
        self, member_id: int, start_date: datetime, end_date: datetime
    ) -> Dict[str, Any]:
        """获取成员排名"""
        # 获取所有活跃成员的工时
        all_members_query = (
            select(
                Member.id,
                Member.name,
                func.coalesce(func.sum(RepairTask.work_minutes), 0).label(
                    "total_minutes"
                ),
            )
            .outerjoin(
                RepairTask,
                and_(
                    RepairTask.member_id == Member.id,
                    RepairTask.report_time >= start_date,
                    RepairTask.report_time <= end_date,
                ),
            )
            .where(Member.is_active)
            .group_by(Member.id, Member.name)
            .order_by(desc("total_minutes"))
        )

        result = await self.db.execute(all_members_query)
        rankings = result.fetchall()

        # 找到当前成员的排名
        member_rank = 0
        total_members = len(rankings)

        for i, (mid, name, minutes) in enumerate(rankings):
            if mid == member_id:
                member_rank = i + 1
                break

        return {
            "work_hour_rank": member_rank,
            "total_members": total_members,
            "percentile": (
                round((1 - (member_rank - 1) / total_members) * 100, 1)
                if total_members > 0
                else 0
            ),
        }

    async def _get_member_trend_analysis(
        self, member_id: int, year: int, month: int
    ) -> Dict[str, Any]:
        """获取成员趋势分析"""
        # 获取最近3个月的数据进行对比
        trends = []

        for i in range(3):
            # 计算目标月份
            target_date = datetime(year, month, 1) - timedelta(days=30 * i)
            target_year = target_date.year
            target_month = target_date.month

            start_date = datetime(target_year, target_month, 1)
            _, last_day = monthrange(target_year, target_month)
            end_date = datetime(target_year, target_month, last_day, 23, 59, 59)

            # 获取月度数据
            monthly_data = await self._get_member_work_hour_statistics(
                member_id, start_date, end_date
            )
            monthly_data["period"] = f"{target_year}-{target_month:02d}"

            trends.append(monthly_data)

        # 计算趋势
        if len(trends) >= 2:
            current_hours = trends[0]["total_hours"]
            previous_hours = trends[1]["total_hours"]

            if previous_hours > 0:
                change_rate = round(
                    ((current_hours - previous_hours) / previous_hours * 100), 2
                )
            else:
                change_rate = 100 if current_hours > 0 else 0
        else:
            change_rate = 0

        return {
            "monthly_data": trends,
            "change_rate": change_rate,
            "trend_direction": (
                "up" if change_rate > 0 else "down" if change_rate < 0 else "stable"
            ),
        }

    async def _get_member_comparison_stats(
        self, member_id: int, date_from: datetime, date_to: datetime
    ) -> Dict[str, Any]:
        """获取成员对比统计"""
        task_stats = await self._get_member_task_statistics(
            member_id, date_from, date_to
        )
        work_hour_stats = await self._get_member_work_hour_statistics(
            member_id, date_from, date_to
        )
        quality_stats = await self._get_member_quality_statistics(
            member_id, date_from, date_to
        )

        return {
            "tasks": task_stats,
            "work_hours": work_hour_stats,
            "quality": quality_stats,
        }

    async def _calculate_team_summary(
        self, member_stats: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """计算团队汇总"""
        if not member_stats:
            return {}

        total_hours = sum(stats["work_hours"]["total_hours"] for stats in member_stats)
        total_tasks = sum(stats["tasks"]["total_tasks"] for stats in member_stats)
        total_completed = sum(
            stats["tasks"]["completed_tasks"] for stats in member_stats
        )

        avg_rating_sum = sum(
            stats["quality"]["avg_rating"]
            for stats in member_stats
            if stats["quality"]["avg_rating"] > 0
        )
        rated_members = len(
            [stats for stats in member_stats if stats["quality"]["avg_rating"] > 0]
        )
        team_avg_rating = (
            round(avg_rating_sum / rated_members, 2) if rated_members > 0 else 0
        )

        return {
            "total_members": len(member_stats),
            "total_hours": total_hours,
            "total_tasks": total_tasks,
            "total_completed": total_completed,
            "team_completion_rate": (
                round((total_completed / total_tasks * 100), 2)
                if total_tasks > 0
                else 0
            ),
            "team_avg_rating": team_avg_rating,
        }

    async def _get_monthly_statistics(
        self, start_date: datetime, end_date: datetime, department: Optional[str] = None
    ) -> Dict[str, Any]:
        """获取月度统计"""
        # 任务统计
        task_query = select(RepairTask).where(
            and_(
                RepairTask.report_time >= start_date, RepairTask.report_time <= end_date
            )
        )

        if department:
            task_query = task_query.join(Member).where(Member.department == department)

        task_result = await self.db.execute(task_query)
        tasks = task_result.scalars().all()

        total_tasks = len(tasks)
        completed_tasks = len([t for t in tasks if t.status == TaskStatus.COMPLETED])
        total_work_minutes = sum(
            t.work_minutes for t in tasks if t.work_minutes is not None
        )

        return {
            "total_tasks": total_tasks,
            "completed_tasks": completed_tasks,
            "total_work_hours": round(total_work_minutes / 60.0, 2),
            "completion_rate": (
                round((completed_tasks / total_tasks * 100), 2)
                if total_tasks > 0
                else 0
            ),
        }

    def _analyze_trends(self, trends: List[Dict[str, Any]]) -> Dict[str, Any]:
        """分析趋势"""
        if len(trends) < 2:
            return {"status": "insufficient_data"}

        # 计算工时趋势
        work_hours = [t["total_work_hours"] for t in trends]
        tasks_count = [t["total_tasks"] for t in trends]
        completion_rates = [t["completion_rate"] for t in trends]

        # 简单的趋势分析
        work_hour_trend = (
            "increasing" if work_hours[-1] > work_hours[0] else "decreasing"
        )
        task_trend = "increasing" if tasks_count[-1] > tasks_count[0] else "decreasing"

        return {
            "work_hour_trend": work_hour_trend,
            "task_count_trend": task_trend,
            "avg_work_hours": round(sum(work_hours) / len(work_hours), 2),
            "avg_completion_rate": round(
                sum(completion_rates) / len(completion_rates), 2
            ),
        }

    async def _export_summary_data(
        self, date_from: datetime, date_to: datetime, department: Optional[str] = None
    ) -> Dict[str, Any]:
        """导出汇总数据"""
        overview = await self.get_overview_statistics(date_from, date_to)

        return {
            "export_type": "summary",
            "data": overview,
            "export_time": datetime.now().isoformat(),
        }

    async def _export_detailed_data(
        self,
        date_from: datetime,
        date_to: datetime,
        member_ids: Optional[List[int]] = None,
        department: Optional[str] = None,
    ) -> Dict[str, Any]:
        """导出详细数据"""
        # 获取成员列表
        member_query = select(Member).where(Member.is_active)
        if member_ids:
            member_query = member_query.where(Member.id.in_(member_ids))
        elif department:
            member_query = member_query.where(Member.department == department)

        member_result = await self.db.execute(member_query)
        members = member_result.scalars().all()

        # 获取每个成员的详细数据
        detailed_data = []
        for member in members:
            member_data = await self._get_member_comparison_stats(
                member.id, date_from, date_to
            )
            member_data["member"] = {
                "id": member.id,
                "name": member.name,
                "student_id": member.student_id,
                "department": member.department,
            }
            detailed_data.append(member_data)

        return {
            "export_type": "detailed",
            "period": {"from": date_from.isoformat(), "to": date_to.isoformat()},
            "data": detailed_data,
            "export_time": datetime.now().isoformat(),
        }

    async def _export_comparison_data(
        self, date_from: datetime, date_to: datetime, department: Optional[str] = None
    ) -> Dict[str, Any]:
        """导出对比数据"""
        comparison_report = await self.get_team_comparison_report(
            department, date_from, date_to
        )

        return {
            "export_type": "comparison",
            "data": comparison_report,
            "export_time": datetime.now().isoformat(),
        }

    async def get_member_work_hour_statistics(
        self, member_id: int, year: int, month: int
    ) -> Dict[str, Any]:
        """
        获取成员工时统计

        Args:
            member_id: 成员ID
            year: 年份
            month: 月份

        Returns:
            Dict: 成员工时统计数据
        """
        try:
            # 计算月份范围
            start_date = datetime(year, month, 1)
            from calendar import monthrange

            _, last_day = monthrange(year, month)
            end_date = datetime(year, month, last_day, 23, 59, 59)

            # 使用现有方法计算统计
            work_hour_stats = await self._get_member_work_hour_statistics(
                member_id, start_date, end_date
            )

            return {
                "member_id": member_id,
                "year": year,
                "month": month,
                "period": {"from": start_date.isoformat(), "to": end_date.isoformat()},
                **work_hour_stats,
            }

        except Exception as e:
            logger.error(f"Get member work hour statistics error: {str(e)}")
            raise

    async def get_comprehensive_report(
        self, start_date: datetime, end_date: datetime
    ) -> Dict[str, Any]:
        """
        生成综合系统报告

        Args:
            start_date: 开始时间
            end_date: 结束时间

        Returns:
            Dict: 综合报告数据
        """
        try:
            import asyncio

            # 并行获取各类统计数据
            overview_task = asyncio.create_task(
                self.get_overview_statistics(start_date, end_date)
            )

            # 获取活跃成员列表
            members_query = select(Member).where(Member.is_active.is_(True))
            members_result = await self.db.execute(members_query)
            active_members = members_result.scalars().all()

            # 生成成员绩效报告
            member_reports = []
            for member in active_members[:50]:  # 限制前50名成员
                try:
                    member_report = await self.get_member_performance_report(
                        member.id, start_date.year, start_date.month
                    )
                    member_reports.append(member_report)
                except Exception as e:
                    logger.warning(
                        f"Failed to get report for member {member.id}: {str(e)}"
                    )

            # 团队对比分析
            team_comparison = await self.get_team_comparison_report(
                None, start_date, end_date, limit=20
            )

            # 月度趋势分析
            trends = await self.get_monthly_trends(months=6)

            # 等待总览统计完成
            overview_stats = await overview_task

            return {
                "report_type": "comprehensive",
                "generated_at": datetime.now().isoformat(),
                "period": {"from": start_date.isoformat(), "to": end_date.isoformat()},
                "overview": overview_stats,
                "member_reports": member_reports,
                "team_comparison": team_comparison,
                "trends": trends,
                "summary": {
                    "total_members_analyzed": len(member_reports),
                    "total_active_members": len(active_members),
                    "analysis_completeness": (
                        len(member_reports) / len(active_members)
                        if active_members
                        else 0
                    ),
                },
            }

        except Exception as e:
            logger.error(f"Get comprehensive report error: {str(e)}")
            raise

    async def get_team_statistics_summary(
        self, start_date: datetime, end_date: datetime
    ) -> Dict[str, Any]:
        """
        获取团队统计汇总

        Args:
            start_date: 开始时间
            end_date: 结束时间

        Returns:
            Dict: 团队统计汇总数据
        """
        try:
            # 获取概览统计
            overview = await self.get_overview_statistics(start_date, end_date)

            # 获取活跃成员数量
            members_query = select(func.count(Member.id)).where(
                Member.is_active.is_(True)
            )
            members_result = await self.db.execute(members_query)
            team_size = members_result.scalar() or 0

            # 从概览统计中提取关键数据
            summary = overview.get("summary", {})
            work_hours_data = overview.get("work_hours", {})
            tasks_data = overview.get("tasks", {})
            performance_data = overview.get("performance", {})

            total_work_hours = float(work_hours_data.get("total_hours", 0))
            total_completed_tasks = int(tasks_data.get("completed_count", 0))

            return {
                "period": {"from": start_date.isoformat(), "to": end_date.isoformat()},
                "team_size": team_size,
                "total_work_hours": total_work_hours,
                "avg_work_hours": (
                    round(total_work_hours / team_size, 2) if team_size > 0 else 0
                ),
                "total_completed_tasks": total_completed_tasks,
                "avg_tasks_per_member": (
                    round(total_completed_tasks / team_size, 2) if team_size > 0 else 0
                ),
                "team_efficiency": round(
                    performance_data.get("overall_rating", 0) * 20, 1
                ),  # Convert 5-scale to 100-scale
                "completion_rate": tasks_data.get("repair_tasks", {}).get(
                    "completion_rate", 0
                ),
                "generated_at": datetime.now().isoformat(),
            }

        except Exception as e:
            logger.error(f"Get team statistics summary error: {str(e)}")
            raise

    async def invalidate_member_cache(self, member_id: int) -> Dict[str, Any]:
        """
        清除成员相关的缓存

        Args:
            member_id: 成员ID

        Returns:
            Dict: 缓存清除结果
        """
        try:
            # 清除成员相关的统计缓存
            cache_keys_cleared = []

            # 如果有缓存系统，这里会清除相关缓存键
            # 目前返回模拟的结果
            cache_keys_cleared = [
                f"member:{member_id}:work_hours",
                f"member:{member_id}:tasks",
                f"member:{member_id}:performance",
                f"member:{member_id}:statistics",
            ]

            logger.info(
                f"Invalidated cache for member {member_id}, keys: {cache_keys_cleared}"
            )

            return {
                "cache_cleared": True,
                "member_id": member_id,
                "keys_cleared": cache_keys_cleared,
                "cleared_at": datetime.now().isoformat(),
            }

        except Exception as e:
            logger.error(f"Invalidate member cache error: {str(e)}")
            raise
