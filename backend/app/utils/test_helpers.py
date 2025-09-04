"""
Test helper utilities for model creation and testing
"""

from datetime import date, datetime
from typing import Any, Dict

from app.models.attendance import AttendanceRecord
from app.models.member import Member, UserRole
from app.models.task import RepairTask, TaskPriority, TaskStatus, TaskType


def create_test_member(**kwargs: Any) -> Member:
    """Create a test member with all required fields."""
    defaults = {
        "username": "test_user",
        "name": "Test User",
        "student_id": "TEST001",
        "department": "信息化建设处",
        "class_name": "Test Class",
        "password_hash": "$2b$12$test_hash",
        "role": UserRole.MEMBER,
        "is_active": True,
        "profile_completed": False,
        "is_verified": False,
        "login_count": 0,
    }
    defaults.update(kwargs)
    return Member(**defaults)


def create_test_repair_task(**kwargs: Any) -> RepairTask:
    """Create a test repair task with all required fields."""
    defaults = {
        "task_id": f"TEST_{id(kwargs)}",
        "member_id": 1,
        "title": "Test Repair Task",
        "task_type": TaskType.ONLINE,
        "status": TaskStatus.PENDING,
        "priority": TaskPriority.MEDIUM,
        "report_time": datetime.utcnow(),
    }
    defaults.update(kwargs)
    return RepairTask(**defaults)


def create_test_attendance_record(**kwargs: Any) -> AttendanceRecord:
    """Create a test attendance record with all required fields."""
    defaults = {
        "member_id": 1,
        "attendance_date": date.today(),
        "work_hours": 8.0,
        "status": "正常",
    }
    defaults.update(kwargs)
    return AttendanceRecord(**defaults)


def create_minimal_member(**kwargs: Any) -> Dict[str, Any]:
    """Create minimal member data for API tests."""
    defaults = {
        "username": "test_user",
        "name": "Test User",
        "class_name": "Test Class",
    }
    defaults.update(kwargs)
    return defaults


def create_minimal_task_data(**kwargs: Any) -> Dict[str, Any]:
    """Create minimal task data for API tests."""
    defaults = {
        "title": "Test Task",
        "task_type": "online",
        "priority": "medium",
    }
    defaults.update(kwargs)
    return defaults
