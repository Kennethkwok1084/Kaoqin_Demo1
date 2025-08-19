"""
Attendance models for daily attendance tracking and exception management.
Includes attendance records, exceptions, and related enums.
"""

from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Boolean, Column, Date, DateTime
from sqlalchemy import Float, ForeignKey, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import ENUM as PgEnum
from sqlalchemy.orm import Mapped, relationship

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.member import Member


class AttendanceExceptionStatus(Enum):
    """考勤异常状态枚举"""

    PENDING = "pending"  # 待审核
    APPROVED = "approved"  # 已批准
    REJECTED = "rejected"  # 已拒绝


class AttendanceRecord(BaseModel):
    """
    Daily attendance record model.

    Records daily check-in/check-out times and calculates work hours.
    """

    __tablename__ = "attendance_records"

    # Member reference
    member_id = Column(
        Integer,
        ForeignKey("members.id"),
        nullable=False,
        index=True,
        comment="Member ID",
    )

    # Attendance date
    attendance_date = Column(
        Date, nullable=False, index=True, comment="Attendance date"
    )

    # Check-in/out times
    checkin_time = Column(DateTime, nullable=True, comment="Check-in time")

    checkout_time = Column(DateTime, nullable=True, comment="Check-out time")

    # Calculated work hours
    work_hours = Column(Float, default=0.0, comment="Total work hours")

    # Status and location
    status = Column(String(20), default="未签到", comment="Attendance status")

    location = Column(String(200), nullable=True, comment="Check-in/out location")

    notes = Column(Text, nullable=True, comment="Attendance notes")

    # Late check-in tracking
    is_late_checkin = Column(
        Boolean, default=False, comment="Whether check-in was late"
    )

    late_checkin_minutes = Column(
        Integer, nullable=True, comment="Minutes late for check-in"
    )

    # Early checkout tracking
    is_early_checkout = Column(
        Boolean, default=False, comment="Whether checkout was early"
    )

    early_checkout_minutes = Column(
        Integer, nullable=True, comment="Minutes early for checkout"
    )

    # Relationships
    member: Mapped["Member"] = relationship(
        "Member", back_populates="attendance_records"
    )

    # Indexes and constraints
    __table_args__ = (
        UniqueConstraint(
            "member_id", "attendance_date", name="uq_attendance_member_date"
        ),
        Index("idx_attendance_date_member", "attendance_date", "member_id"),
    )

    def __repr__(self) -> str:
        return (
            f"<AttendanceRecord(member_id={self.member_id}, "
            f"date={self.attendance_date})>"
        )


class AttendanceException(BaseModel):
    """
    Attendance exception request model.

    Handles requests for attendance anomalies like late arrival,
    early departure, missed check-in/out, leave requests, etc.
    """

    __tablename__ = "attendance_exceptions"

    # Member reference
    member_id = Column(
        Integer,
        ForeignKey("members.id"),
        nullable=False,
        index=True,
        comment="Member ID who made the request",
    )

    # Exception details
    exception_type = Column(
        String(50),
        nullable=False,
        comment="Type of exception (迟到/早退/忘记打卡/请假等)",
    )

    exception_date = Column(
        Date, nullable=False, index=True, comment="Date of the exception"
    )

    reason = Column(Text, nullable=False, comment="Reason for the exception")

    supporting_documents = Column(
        Text, nullable=True, comment="Supporting documents or evidence"
    )

    # Request status and processing
    status: AttendanceExceptionStatus = Column(
        PgEnum(
            AttendanceExceptionStatus,
            name="attendanceexceptionstatus",
            create_type=False,
        ),
        default=AttendanceExceptionStatus.PENDING,
        nullable=False,
        index=True,
        comment="Processing status",
    )

    applied_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
        comment="When the request was submitted",
    )

    # Review information
    reviewer_id = Column(
        Integer,
        ForeignKey("members.id"),
        nullable=True,
        comment="ID of the reviewer (admin)",
    )

    reviewer_comments = Column(
        Text, nullable=True, comment="Comments from the reviewer"
    )

    reviewed_at = Column(
        DateTime, nullable=True, comment="When the request was reviewed"
    )

    # Relationships
    member: Mapped["Member"] = relationship(
        "Member", back_populates="attendance_exceptions", foreign_keys=[member_id]
    )

    reviewer: Mapped[Optional["Member"]] = relationship(
        "Member", foreign_keys=[reviewer_id], post_update=True
    )

    # Indexes
    __table_args__ = (
        Index("idx_exception_member_date", "member_id", "exception_date"),
        Index("idx_exception_status_date", "status", "applied_at"),
    )

    def __repr__(self) -> str:
        return (
            f"<AttendanceException(member_id={self.member_id}, "
            f"type={self.exception_type}, date={self.exception_date})>"
        )


class MonthlyAttendanceSummary(BaseModel):
    """
    Monthly attendance summary model.

    Stores calculated work hours and attendance statistics for each member by month.
    Based on new attendance rules from readme.md and agents_updated.md
    """

    __tablename__ = "monthly_attendance_summaries"

    # Member reference
    member_id = Column(
        Integer,
        ForeignKey("members.id"),
        nullable=False,
        index=True,
        comment="Member ID",
    )

    # Time period
    year = Column(Integer, nullable=False, comment="Year")

    month = Column(Integer, nullable=False, comment="Month (1-12)")

    # Core work hour categories (按agents_updated.md六、工时字段定义)
    repair_task_hours = Column(
        Float, default=0.0, comment="本月报修任务累计时长（小时）"
    )

    monitoring_hours = Column(
        Float, default=0.0, comment="本月监控任务累计时长（小时）"
    )

    assistance_hours = Column(
        Float, default=0.0, comment="本月协助任务累计时长（小时）"
    )

    carried_hours = Column(Float, default=0.0, comment="上月结转的剩余时长（小时）")

    total_hours = Column(Float, default=0.0, comment="实际总工时（小时）")

    remaining_hours = Column(Float, default=0.0, comment="扣除后可结转至下月的剩余工时")

    # 详细分类统计（用于分析和展示）
    online_repair_hours = Column(
        Float, default=0.0, comment="线上报修任务时长（40分钟/单）"
    )

    offline_repair_hours = Column(
        Float, default=0.0, comment="线下报修任务时长（100分钟/单）"
    )

    rush_task_hours = Column(
        Float, default=0.0, comment="爆单任务额外时长（15分钟/单）"
    )

    positive_review_hours = Column(
        Float, default=0.0, comment="非默认好评额外时长（30分钟/单）"
    )

    # 惩罚扣时统计
    penalty_hours = Column(Float, default=0.0, comment="异常扣时总计（小时）")

    late_response_penalty_hours = Column(
        Float, default=0.0, comment="超时响应扣时（30分钟/单/人）"
    )

    late_completion_penalty_hours = Column(
        Float, default=0.0, comment="超时处理扣时（30分钟/人）"
    )

    negative_review_penalty_hours = Column(
        Float, default=0.0, comment="差评扣时（60分钟/单/人）"
    )

    # Attendance statistics
    total_work_days = Column(Integer, default=0, comment="Total work days in the month")

    attended_days = Column(Integer, default=0, comment="Days with attendance records")

    late_days = Column(Integer, default=0, comment="Days with late check-in")

    early_checkout_days = Column(Integer, default=0, comment="Days with early checkout")

    # Performance metrics
    task_completion_count = Column(
        Integer, default=0, comment="Number of completed tasks"
    )

    average_task_rating = Column(
        Float, nullable=True, comment="Average rating for completed tasks"
    )

    # Summary and notes
    summary_notes = Column(Text, nullable=True, comment="Monthly summary notes")

    # Relationships
    member: Mapped["Member"] = relationship(
        "Member", back_populates="monthly_summaries"
    )

    # Constraints and indexes
    __table_args__ = (
        UniqueConstraint(
            "member_id", "year", "month", name="uq_attendance_summary_member_month"
        ),
        Index("idx_summary_year_month", "year", "month"),
        Index("idx_summary_member_year", "member_id", "year"),
    )

    @property
    def month_string(self) -> str:
        """Get month in YYYY-MM format."""
        return f"{self.year:04d}-{self.month:02d}"

    @property
    def attendance_rate(self) -> float:
        """Calculate attendance rate."""
        if self.total_work_days == 0:
            return 0.0
        return float(((self.attended_days or 0) / (self.total_work_days or 1)) * 100)

    def __repr__(self) -> str:
        return (
            f"<MonthlyAttendanceSummary(member_id={self.member_id}, "
            f"month={self.month_string})>"
        )
