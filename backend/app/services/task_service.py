"""
任务服务聚合（兼容旧引用）。

该模块保留历史导入路径，并重定向到拆分后的专用服务类：
- RepairService：负责维修任务业务逻辑
- MonitoringService：负责监控任务业务逻辑
- AssistanceService：负责协助任务业务逻辑
"""

from app.services.assistance_service import AssistanceService
from app.services.monitoring_service import MonitoringService
from app.services.repair_service import RepairService


class TaskService(RepairService):
    """向后兼容的别名，建议改用 RepairService。"""


class MonitoringTaskService(MonitoringService):
    """向后兼容的别名，建议改用 MonitoringService。"""


class AssistanceTaskService(AssistanceService):
    """向后兼容的别名，建议改用 AssistanceService。"""


__all__ = [
    "RepairService",
    "MonitoringService",
    "AssistanceService",
    "TaskService",
    "MonitoringTaskService",
    "AssistanceTaskService",
]
