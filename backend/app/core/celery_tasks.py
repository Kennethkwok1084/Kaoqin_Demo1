"""
Celery异步任务定义
包含所有的后台任务和定时任务
"""

import asyncio
import concurrent.futures
import logging
from datetime import datetime, timedelta
from typing import Any, Awaitable, Callable, Dict, List, Optional

from app.core.celery_app import celery_app
from app.core.database import AsyncSessionLocal
from app.services.stats_service import StatisticsService
from app.services.work_hour_automation import WorkHourAutomationService

logger = logging.getLogger(__name__)


def run_async_task(
    async_func: Callable[..., Awaitable[Any]], *args: Any, **kwargs: Any
) -> Any:
    """运行异步任务的辅助函数"""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # 如果事件循环正在运行，创建新的事件循环
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future: concurrent.futures.Future[Any] = executor.submit(
                    asyncio.run, async_func(*args, **kwargs)  # type: ignore[arg-type]
                )
                return future.result()
        else:
            return loop.run_until_complete(async_func(*args, **kwargs))
    except RuntimeError:
        # 创建新的事件循环
        return asyncio.run(async_func(*args, **kwargs))  # type: ignore[arg-type]


@celery_app.task(bind=True, name="app.core.celery_tasks.schedule_overdue_detection")
def schedule_overdue_detection(self: Any) -> Dict[str, Any]:
    """
    定时检测超时任务
    每小时执行一次，检测延迟响应和延迟完成的任务
    """
    try:
        logger.info(f"Starting overdue detection task (ID: {self.request.id})")

        async def _detect_overdue() -> Dict[str, Any]:
            async with AsyncSessionLocal() as db:
                automation_service = WorkHourAutomationService(db)
                result = await automation_service.schedule_overdue_detection()
                return result

        result = run_async_task(_detect_overdue)

        logger.info(f"Overdue detection completed: {result}")
        return dict(result) if result else {}

    except Exception as e:
        logger.error(f"Overdue detection task failed: {str(e)}")
        # 重试机制
        raise self.retry(exc=e, countdown=300, max_retries=3)


@celery_app.task(bind=True, name="app.core.celery_tasks.process_review_bonuses")
def process_review_bonuses(self: Any) -> Dict[str, Any]:
    """
    处理评价奖励
    每30分钟执行一次，处理最近的任务评价
    """
    try:
        logger.info(f"Starting review bonus processing task (ID: {self.request.id})")

        async def _process_bonuses() -> Dict[str, Any]:
            async with AsyncSessionLocal() as db:
                automation_service = WorkHourAutomationService(db)
                result = await automation_service.process_review_bonuses()
                return result

        result = run_async_task(_process_bonuses)

        logger.info(f"Review bonus processing completed: {result}")
        return dict(result) if result else {}

    except Exception as e:
        logger.error(f"Review bonus processing task failed: {str(e)}")
        raise self.retry(exc=e, countdown=180, max_retries=3)


@celery_app.task(bind=True, name="app.core.celery_tasks.send_notifications")
def send_notifications(self: Any) -> Dict[str, Any]:
    """
    发送超时提醒通知
    每15分钟执行一次，发送即将超时的任务提醒
    """
    try:
        logger.info(f"Starting notification sending task (ID: {self.request.id})")

        async def _send_notifications() -> Dict[str, Any]:
            async with AsyncSessionLocal() as db:
                automation_service = WorkHourAutomationService(db)
                result = await automation_service.send_overdue_notifications()
                return result

        result = run_async_task(_send_notifications)

        logger.info(f"Notification sending completed: {result}")
        return dict(result) if result else {}

    except Exception as e:
        logger.error(f"Notification sending task failed: {str(e)}")
        raise self.retry(exc=e, countdown=120, max_retries=3)


@celery_app.task(bind=True, name="app.core.celery_tasks.cleanup_expired_data")
def cleanup_expired_data(self: Any, days_to_keep: int = 90) -> Dict[str, Any]:
    """
    清理过期数据
    每天凌晨2点执行，清理过期的任务数据
    """
    try:
        logger.info(
            f"Starting data cleanup task (ID: {
                self.request.id}, days_to_keep: {days_to_keep})"
        )

        async def _cleanup_data() -> Dict[str, Any]:
            async with AsyncSessionLocal() as db:
                automation_service = WorkHourAutomationService(db)
                result = await automation_service.cleanup_expired_data(days_to_keep)
                return result

        result = run_async_task(_cleanup_data)

        logger.info(f"Data cleanup completed: {result}")
        return dict(result) if result else {}

    except Exception as e:
        logger.error(f"Data cleanup task failed: {str(e)}")
        raise self.retry(exc=e, countdown=3600, max_retries=2)


@celery_app.task(bind=True, name="app.core.celery_tasks.generate_daily_statistics")
def generate_daily_statistics(self: Any) -> Dict[str, Any]:
    """
    生成每日统计报告
    每天凌晨3点执行，生成前一天的统计数据
    """
    try:
        logger.info(
            f"Starting daily statistics generation task (ID: {self.request.id})"
        )

        async def _generate_stats() -> Dict[str, Any]:
            async with AsyncSessionLocal() as db:
                stats_service = StatisticsService(db)

                # 生成昨天的统计数据
                yesterday = datetime.utcnow().date() - timedelta(days=1)
                start_time = datetime.combine(yesterday, datetime.min.time())
                end_time = datetime.combine(yesterday, datetime.max.time())

                # 生成各种统计报告
                daily_overview = await stats_service.get_overview_statistics(
                    start_time, end_time
                )
                member_stats = await stats_service._get_member_statistics()
                task_stats = await stats_service._get_task_statistics(
                    date_from=start_time, date_to=end_time
                )

                return {
                    "date": yesterday.isoformat(),
                    "daily_overview": daily_overview,
                    "member_count": len(member_stats),
                    "task_stats": task_stats,
                }

        result = run_async_task(_generate_stats)

        logger.info(f"Daily statistics generation completed: {result}")
        return dict(result) if result else {}

    except Exception as e:
        logger.error(f"Daily statistics generation task failed: {str(e)}")
        raise self.retry(exc=e, countdown=1800, max_retries=2)


@celery_app.task(bind=True, name="app.core.celery_tasks.weekly_work_hour_recalculation")
def weekly_work_hour_recalculation(self: Any) -> Dict[str, Any]:
    """
    每周工时重算
    每周日凌晨4点执行，重新计算上周的所有任务工时
    """
    try:
        logger.info(
            f"Starting weekly work hour recalculation task (ID: {self.request.id})"
        )

        async def _recalculate_hours() -> Dict[str, Any]:
            async with AsyncSessionLocal() as db:
                automation_service = WorkHourAutomationService(db)

                # 计算上周的时间范围
                today = datetime.utcnow().date()
                days_since_monday = today.weekday()
                last_monday = today - timedelta(days=days_since_monday + 7)
                last_sunday = last_monday + timedelta(days=6)

                date_from = datetime.combine(last_monday, datetime.min.time())
                date_to = datetime.combine(last_sunday, datetime.max.time())

                result = await automation_service.recalculate_batch_hours(
                    date_from=date_from, date_to=date_to
                )

                return {
                    "week_start": last_monday.isoformat(),
                    "week_end": last_sunday.isoformat(),
                    **result,
                }

        result = run_async_task(_recalculate_hours)

        logger.info(f"Weekly work hour recalculation completed: {result}")
        return dict(result) if result else {}

    except Exception as e:
        logger.error(f"Weekly work hour recalculation task failed: {str(e)}")
        raise self.retry(exc=e, countdown=3600, max_retries=2)


@celery_app.task(bind=True, name="app.core.celery_tasks.batch_apply_penalties")
def batch_apply_penalties(
    self: Any, task_ids: Optional[List[int]] = None
) -> Dict[str, Any]:
    """
    批量应用惩罚标签
    手动触发或定时执行，对指定任务批量应用惩罚
    """
    try:
        logger.info(f"Starting batch penalty application task (ID: {self.request.id})")

        async def _apply_penalties() -> Dict[str, Any]:
            async with AsyncSessionLocal() as db:
                automation_service = WorkHourAutomationService(db)
                result = await automation_service.auto_apply_penalty_tags(task_ids)
                return result

        result = run_async_task(_apply_penalties)

        logger.info(f"Batch penalty application completed: {result}")
        return dict(result) if result else {}

    except Exception as e:
        logger.error(f"Batch penalty application task failed: {str(e)}")
        raise self.retry(exc=e, countdown=300, max_retries=3)


@celery_app.task(bind=True, name="app.core.celery_tasks.export_statistics_report")
def export_statistics_report(
    self: Any,
    report_type: str,
    date_from: str,
    date_to: str,
    member_ids: Optional[List[int]] = None,
) -> Dict[str, Any]:
    """
    导出统计报告
    异步生成和导出各种格式的统计报告
    """
    try:
        logger.info(
            f"Starting statistics report export task (ID: {
                self.request.id}, type: {report_type})"
        )

        async def _export_report() -> Dict[str, Any]:
            async with AsyncSessionLocal() as db:
                stats_service = StatisticsService(db)

                start_date = datetime.fromisoformat(date_from)
                end_date = datetime.fromisoformat(date_to)

                if report_type == "overview":
                    data = await stats_service.get_overview_statistics(
                        start_date, end_date
                    )
                elif report_type == "member":
                    data = await stats_service._get_member_statistics()
                elif report_type == "task":
                    data = await stats_service._get_task_statistics(
                        date_from=start_date, date_to=end_date
                    )
                else:
                    raise ValueError(f"Unknown report type: {report_type}")

                # 这里可以实现报告导出逻辑（Excel、PDF等）
                # 目前返回JSON数据
                return {
                    "report_type": report_type,
                    "date_range": {"from": date_from, "to": date_to},
                    "data": data,
                    "exported_at": datetime.utcnow().isoformat(),
                }

        result = run_async_task(_export_report)

        logger.info(
            f"Statistics report export completed: {
                result['report_type'] if result else 'unknown'}"
        )
        return dict(result) if result else {}

    except Exception as e:
        logger.error(f"Statistics report export task failed: {str(e)}")
        raise self.retry(exc=e, countdown=600, max_retries=2)


@celery_app.task(bind=True, name="app.core.celery_tasks.system_health_check")
def system_health_check(self: Any) -> Dict[str, Any]:
    """
    系统健康检查
    定期检查系统各组件的健康状态
    """
    try:
        logger.info(f"Starting system health check task (ID: {self.request.id})")

        async def _health_check() -> Dict[str, Any]:
            health_status = {
                "timestamp": datetime.utcnow().isoformat(),
                "database": "unknown",
                "redis": "unknown",
                "task_queue": "healthy",
            }

            # 检查数据库连接
            try:
                async with AsyncSessionLocal() as db:
                    from sqlalchemy import text

                    await db.execute(text("SELECT 1"))
                    health_status["database"] = "healthy"
            except Exception as e:
                health_status["database"] = f"unhealthy: {str(e)}"

            # 检查Redis连接（如果配置了）
            try:
                # 这里可以添加Redis健康检查
                health_status["redis"] = "healthy"
            except Exception as e:
                health_status["redis"] = f"unhealthy: {str(e)}"

            return health_status

        result = run_async_task(_health_check)

        logger.info(f"System health check completed: {result}")
        return dict(result) if result else {}

    except Exception as e:
        logger.error(f"System health check task failed: {str(e)}")
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "status": "failed",
            "error": str(e),
        }


# 任务监控和管理函数


def get_task_status(task_id: str) -> Dict[str, Any]:
    """获取任务状态"""
    try:
        result = celery_app.AsyncResult(task_id)
        return {
            "task_id": task_id,
            "status": result.status,
            "result": result.result,
            "traceback": result.traceback,
            "date_done": result.date_done.isoformat() if result.date_done else None,
        }
    except Exception as e:
        return {"task_id": task_id, "status": "ERROR", "error": str(e)}


def cancel_task(task_id: str) -> bool:
    """取消任务"""
    try:
        celery_app.control.revoke(task_id, terminate=True)
        return True
    except Exception as e:
        logger.error(f"Failed to cancel task {task_id}: {str(e)}")
        return False


def get_active_tasks() -> List[Dict[str, Any]]:
    """获取活跃任务列表"""
    try:
        inspect = celery_app.control.inspect()
        active_tasks = inspect.active()

        if not active_tasks:
            return []

        tasks = []
        for worker, task_list in active_tasks.items():
            for task in task_list:
                tasks.append(
                    {
                        "worker": worker,
                        "task_id": task["id"],
                        "task_name": task["name"],
                        "args": task["args"],
                        "kwargs": task["kwargs"],
                        "time_start": task["time_start"],
                    }
                )

        return tasks

    except Exception as e:
        logger.error(f"Failed to get active tasks: {str(e)}")
        return []


def get_scheduled_tasks() -> List[Dict[str, Any]]:
    """获取计划任务列表"""
    try:
        inspect = celery_app.control.inspect()
        scheduled_tasks = inspect.scheduled()

        if not scheduled_tasks:
            return []

        tasks = []
        for worker, task_list in scheduled_tasks.items():
            for task in task_list:
                tasks.append(
                    {
                        "worker": worker,
                        "task_id": task["request"]["id"],
                        "task_name": task["request"]["task"],
                        "eta": task["eta"],
                        "priority": task["priority"],
                    }
                )

        return tasks

    except Exception as e:
        logger.error(f"Failed to get scheduled tasks: {str(e)}")
        return []
