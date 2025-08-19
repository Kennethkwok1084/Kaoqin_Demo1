from datetime import date

from app.models.attendance import AttendanceRecord
from app.models.task import TaskTag, TaskTagType


def test_create_rush_order_tag() -> None:
    tag = TaskTag.create_rush_order_tag()
    assert tag.tag_type == TaskTagType.RUSH_ORDER
    assert tag.work_minutes_modifier == 15


def test_attendance_record_instantiation() -> None:
    record = AttendanceRecord(
        member_id=1,
        attendance_date=date.today(),
        work_hours=0.0,
        status="未签到",
    )
    assert record.member_id == 1
    assert record.status == "未签到"
