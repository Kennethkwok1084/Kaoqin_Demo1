"""
Database models package.
Imports all model classes for easy access.
"""

from app.models.attendance import (
    AttendanceException,
    AttendanceExceptionStatus,
    AttendanceRecord,
    MonthlyAttendanceSummary,
)
from app.models.auth_refresh_token import AuthRefreshToken
from app.models.base import Base, BaseModel, TimestampMixin
from app.models.member import Member, UserRole
from app.models.system_config import SystemConfig
from app.models.task import (
    AssistanceTask,
    MonitoringTask,
    RepairTask,
    TaskCategory,
    TaskPriority,
    UrgencyLevel,
    TaskStatus,
    TaskTag,
    TaskType,
    task_tag_association,
)

# All model classes for easy import
__all__ = [
    # Base classes
    "Base",
    "BaseModel",
    "TimestampMixin",
    # Member models
    "Member",
    "UserRole",
    # System config models
    "SystemConfig",
    # Task models
    "RepairTask",
    "MonitoringTask",
    "AssistanceTask",
    "TaskTag",
    "task_tag_association",
    # Task enums
    "TaskCategory",
    "TaskPriority",
    "UrgencyLevel",
    "TaskStatus",
    "TaskType",
    # Attendance models
    "AttendanceRecord",
    "AttendanceException",
    "AttendanceExceptionStatus",
    "MonthlyAttendanceSummary",
    # Auth token models
    "AuthRefreshToken",
]
