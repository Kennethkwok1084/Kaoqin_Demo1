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
from app.models.app_user import AppUser, AppUserRole, AppUserStatus
from app.models.auth_refresh_token import AuthRefreshToken
from app.models.base import Base, BaseModel, TimestampMixin
from app.models.biz_operation_log import BizOperationLog
from app.models.building import Building, DormRoom
from app.models.media_file import MediaFile
from app.models.member import Member, UserRole
from app.models.review_log import ReviewLog
from app.models.inspection_record import InspectionRecord
from app.models.sampling_record import SamplingRecord
from app.models.sampling_scan_detail import SamplingScanDetail
from app.models.sampling_test_detail import SamplingTestDetail
from app.models.import_batch import ImportBatch
from app.models.import_repair_row import ImportRepairRow
from app.models.repair_match_application import RepairMatchApplication
from app.models.repair_ticket import RepairTicket
from app.models.repair_ticket_member import RepairTicketMember
from app.models.sys_config import SysConfig
from app.models.system_config import SystemConfig
from app.models.task_inspection import TaskInspection
from app.models.task_inspection_point import TaskInspectionPoint
from app.models.task_inspection_user import TaskInspectionUser
from app.models.task_sampling import TaskSampling
from app.models.task_sampling_room import TaskSamplingRoom
from app.models.task_sampling_user import TaskSamplingUser
from app.models.task_coop import TaskCoop
from app.models.task_coop_attendance import TaskCoopAttendance
from app.models.task_coop_signup import TaskCoopSignup
from app.models.task_coop_slot import TaskCoopSlot
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
from app.models.todo_item import TodoItem
from app.models.user_profile import UserProfile
from app.models.workhour_entry import WorkhourEntry
from app.models.workhour_entry_tag import WorkhourEntryTag
from app.models.workhour_rule import WorkhourRule
from app.models.workhour_tag import WorkhourTag

# All model classes for easy import
__all__ = [
    # Base classes
    "Base",
    "BaseModel",
    "TimestampMixin",
    # New app user models
    "AppUser",
    "AppUserRole",
    "AppUserStatus",
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
    # User profile models
    "UserProfile",
    # Docs baseline foundation models
    "SysConfig",
    "Building",
    "DormRoom",
    "MediaFile",
    "WorkhourRule",
    "WorkhourTag",
    "ReviewLog",
    "TodoItem",
    "BizOperationLog",
    "TaskCoop",
    "TaskCoopSlot",
    "TaskCoopSignup",
    "TaskCoopAttendance",
    "TaskInspection",
    "TaskInspectionUser",
    "TaskInspectionPoint",
    "InspectionRecord",
    "TaskSampling",
    "TaskSamplingUser",
    "TaskSamplingRoom",
    "SamplingRecord",
    "SamplingScanDetail",
    "SamplingTestDetail",
    "RepairTicket",
    "RepairTicketMember",
    "ImportBatch",
    "ImportRepairRow",
    "RepairMatchApplication",
    "WorkhourEntry",
    "WorkhourEntryTag",
]
