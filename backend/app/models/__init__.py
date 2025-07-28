"""
Database models package.
Imports all model classes for easy access.
"""

from app.models.base import Base, BaseModel, TimestampMixin
from app.models.member import Member, UserRole
from app.models.task import (
    RepairTask, MonitoringTask, AssistanceTask, TaskTag,
    TaskCategory, TaskPriority, TaskStatus, TaskType,
    task_tag_association
)
from app.models.attendance import (
    AttendanceRecord, AttendanceConfiguration,
    ATTENDANCE_CONFIG_KEYS
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
    
    # Task models
    "RepairTask",
    "MonitoringTask", 
    "AssistanceTask",
    "TaskTag",
    "task_tag_association",
    
    # Task enums
    "TaskCategory",
    "TaskPriority", 
    "TaskStatus",
    "TaskType",
    
    # Attendance models
    "AttendanceRecord",
    "AttendanceConfiguration",
    "ATTENDANCE_CONFIG_KEYS",
]