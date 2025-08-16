"""
Celery配置和任务定义
处理异步任务和定时任务调度
"""

import logging
from typing import Any, Dict

from celery import Celery  # type: ignore[import-untyped]
from celery.schedules import crontab  # type: ignore[import-untyped]

from app.core.config import settings

logger = logging.getLogger(__name__)

# 创建Celery应用
celery_app = Celery(
    "attendance_system",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["app.core.celery_tasks"],
)

# Celery配置
celery_app.conf.update(
    # 时区设置
    timezone="Asia/Shanghai",
    enable_utc=True,
    # 任务序列化
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    # 结果过期时间
    result_expires=3600,
    # 任务路由配置
    task_routes={
        "app.core.celery_tasks.schedule_overdue_detection": {"queue": "automation"},
        "app.core.celery_tasks.process_review_bonuses": {"queue": "automation"},
        "app.core.celery_tasks.send_notifications": {"queue": "notifications"},
        "app.core.celery_tasks.cleanup_expired_data": {"queue": "maintenance"},
    },
    # 定时任务配置
    beat_schedule={
        # 每小时检测超时任务
        "detect-overdue-tasks": {
            "task": "app.core.celery_tasks.schedule_overdue_detection",
            "schedule": crontab(minute=0),  # 每小时的0分执行
            "options": {"queue": "automation"},
        },
        # 每30分钟处理评价奖励
        "process-review-bonuses": {
            "task": "app.core.celery_tasks.process_review_bonuses",
            "schedule": crontab(minute="*/30"),  # 每30分钟执行
            "options": {"queue": "automation"},
        },
        # 每15分钟发送通知
        "send-overdue-notifications": {
            "task": "app.core.celery_tasks.send_notifications",
            "schedule": crontab(minute="*/15"),  # 每15分钟执行
            "options": {"queue": "notifications"},
        },
        # 每天凌晨2点清理过期数据
        "cleanup-expired-data": {
            "task": "app.core.celery_tasks.cleanup_expired_data",
            "schedule": crontab(hour=2, minute=0),  # 每天凌晨2点执行
            "options": {"queue": "maintenance"},
        },
        # 每天凌晨3点生成统计报告
        "generate-daily-stats": {
            "task": "app.core.celery_tasks.generate_daily_statistics",
            "schedule": crontab(hour=3, minute=0),  # 每天凌晨3点执行
            "options": {"queue": "maintenance"},
        },
        # 每周日凌晨4点进行批量工时重算
        "weekly-recalculation": {
            "task": "app.core.celery_tasks.weekly_work_hour_recalculation",
            "schedule": crontab(hour=4, minute=0, day_of_week=0),  # 每周日凌晨4点执行
            "options": {"queue": "maintenance"},
        },
    },
    # Worker配置
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    worker_max_tasks_per_child=1000,
    # 队列配置
    task_default_queue="default",
    task_create_missing_queues=True,
)


# 健康检查任务
@celery_app.task(bind=True)
def health_check(self: Any) -> Dict[str, Any]:
    """Celery健康检查任务"""
    try:
        return {"status": "healthy", "task_id": self.request.id, "timestamp": "now"}
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return {"status": "unhealthy", "error": str(e), "task_id": self.request.id}


# 获取Celery应用实例
def get_celery_app() -> Celery:
    """获取Celery应用实例"""
    return celery_app


# Celery信号处理
@celery_app.on_after_configure.connect
def setup_periodic_tasks(sender: Any, **kwargs: Any) -> None:
    """设置周期性任务"""
    logger.info("Setting up periodic tasks...")

    # 可以在这里添加动态的周期性任务


@celery_app.on_after_finalize.connect
def setup_queues(sender: Any, **kwargs: Any) -> None:
    """设置队列"""
    logger.info("Setting up task queues...")


if __name__ == "__main__":
    celery_app.start()
