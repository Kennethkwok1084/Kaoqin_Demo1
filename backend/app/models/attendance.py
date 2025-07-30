"""
Attendance models for daily attendance tracking and exception management.
Includes attendance records, exceptions, and related enums.
"""

from datetime import datetime, date, time
from typing import TYPE_CHECKING, Optional
from enum import Enum

from sqlalchemy import (
    Column, Float, ForeignKey, Integer, String, UniqueConstraint, Index, Text,
    Boolean, Date, DateTime, Time, Enum as SQLEnum
)
from sqlalchemy.orm import relationship, Mapped

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.member import Member


class AttendanceExceptionStatus(Enum):
    """考勤异常状态枚举"""
    PENDING = "pending"      # 待审核
    APPROVED = "approved"    # 已批准
    REJECTED = "rejected"    # 已拒绝


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
        comment="Member ID"
    )
    
    # Attendance date
    attendance_date = Column(
        Date,
        nullable=False,
        index=True,
        comment="Attendance date"
    )
    
    # Check-in/out times
    checkin_time = Column(
        DateTime,
        nullable=True,
        comment="Check-in time"
    )
    
    checkout_time = Column(
        DateTime,
        nullable=True,
        comment="Check-out time"
    )
    
    # Calculated work hours
    work_hours = Column(
        Float,
        default=0.0,
        comment="Total work hours"
    )
    
    # Status and location
    status = Column(
        String(20),
        default="未签到",
        comment="Attendance status"
    )
    
    location = Column(
        String(200),
        nullable=True,
        comment="Check-in/out location"
    )
    
    notes = Column(
        Text,
        nullable=True,
        comment="Attendance notes"
    )
    
    # Late check-in tracking
    is_late_checkin = Column(
        Boolean,
        default=False,
        comment="Whether check-in was late"
    )
    
    late_checkin_minutes = Column(
        Integer,
        nullable=True,
        comment="Minutes late for check-in"
    )
    
    # Early checkout tracking
    is_early_checkout = Column(
        Boolean,
        default=False,
        comment="Whether checkout was early"
    )
    
    early_checkout_minutes = Column(
        Integer,
        nullable=True,
        comment="Minutes early for checkout"
    )
    
    # Relationships
    member: Mapped["Member"] = relationship(
        "Member",
        back_populates="attendance_records"
    )
    
    # Indexes and constraints
    __table_args__ = (
        UniqueConstraint(
            "member_id", "attendance_date",
            name="uq_attendance_member_date"
        ),
        Index("idx_attendance_date_member", "attendance_date", "member_id"),
    )
    
    def __repr__(self) -> str:
        return f"<AttendanceRecord(member_id={self.member_id}, date={self.attendance_date})>"


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
        comment="Member ID who made the request"
    )
    
    # Exception details
    exception_type = Column(
        String(50),
        nullable=False,
        comment="Type of exception (迟到/早退/忘记打卡/请假等)"
    )
    
    exception_date = Column(
        Date,
        nullable=False,
        index=True,
        comment="Date of the exception"
    )
    
    reason = Column(
        Text,
        nullable=False,
        comment="Reason for the exception"
    )
    
    supporting_documents = Column(
        Text,
        nullable=True,
        comment="Supporting documents or evidence"
    )
    
    # Request status and processing
    status = Column(
        SQLEnum(AttendanceExceptionStatus),
        default=AttendanceExceptionStatus.PENDING,
        nullable=False,
        index=True,
        comment="Processing status"
    )
    
    applied_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
        comment="When the request was submitted"
    )
    
    # Review information
    reviewer_id = Column(
        Integer,
        ForeignKey("members.id"),
        nullable=True,
        comment="ID of the reviewer (admin)"
    )
    
    reviewer_comments = Column(
        Text,
        nullable=True,
        comment="Comments from the reviewer"
    )
    
    reviewed_at = Column(
        DateTime,
        nullable=True,
        comment="When the request was reviewed"
    )
    
    # Relationships
    member: Mapped["Member"] = relationship(
        "Member",
        back_populates="attendance_exceptions",
        foreign_keys=[member_id]
    )
    
    reviewer: Mapped[Optional["Member"]] = relationship(
        "Member",
        foreign_keys=[reviewer_id],
        post_update=True
    )
    
    # Indexes
    __table_args__ = (
        Index("idx_exception_member_date", "member_id", "exception_date"),
        Index("idx_exception_status_date", "status", "applied_at"),
    )
    
    def __repr__(self) -> str:
        return f"<AttendanceException(member_id={self.member_id}, type={self.exception_type}, date={self.exception_date})>"


class MonthlyAttendanceSummary(BaseModel):
    """
    Monthly attendance summary model.
    
    Stores calculated work hours and attendance statistics for each member by month.
    This is derived from daily attendance records and task completion data.
    """
    
    __tablename__ = "monthly_attendance_summaries"
    
    # Member reference
    member_id = Column(
        Integer,
        ForeignKey("members.id"),
        nullable=False,
        index=True,
        comment="Member ID"
    )
    
    # Time period
    year = Column(
        Integer,
        nullable=False,
        comment="Year"
    )
    
    month = Column(
        Integer,
        nullable=False,
        comment="Month (1-12)"
    )
    
    # Work hour categories (in hours, float for precision)
    repair_task_hours = Column(
        Float,
        default=0.0,
        comment="Hours from repair tasks"
    )
    
    monitoring_task_hours = Column(
        Float,
        default=0.0,
        comment="Hours from monitoring tasks"
    )
    
    assistance_task_hours = Column(
        Float,
        default=0.0,
        comment="Hours from assistance tasks"
    )
    
    overtime_hours = Column(
        Float,
        default=0.0,
        comment="Overtime hours"
    )
    
    bonus_hours = Column(
        Float,
        default=0.0,
        comment="Bonus hours (rush tasks, positive reviews)"
    )
    
    penalty_hours = Column(
        Float,
        default=0.0,
        comment="Penalty hours (late response, negative reviews)"
    )
    
    # Calculated totals
    total_work_hours = Column(
        Float,
        default=0.0,
        comment="Total calculated work hours"
    )
    
    total_attendance_hours = Column(
        Float,
        default=0.0,
        comment="Total hours from attendance records"
    )
    
    # Attendance statistics
    total_work_days = Column(
        Integer,
        default=0,
        comment="Total work days in the month"
    )
    
    attended_days = Column(
        Integer,
        default=0,
        comment="Days with attendance records"
    )
    
    late_days = Column(
        Integer,
        default=0,
        comment="Days with late check-in"
    )
    
    early_checkout_days = Column(
        Integer,
        default=0,
        comment="Days with early checkout"
    )
    
    # Performance metrics
    task_completion_count = Column(
        Integer,
        default=0,
        comment="Number of completed tasks"
    )
    
    average_task_rating = Column(
        Float,
        nullable=True,
        comment="Average rating for completed tasks"
    )
    
    # Summary and notes
    summary_notes = Column(
        Text,
        nullable=True,
        comment="Monthly summary notes"
    )
    
    # Relationships
    member: Mapped["Member"] = relationship(
        "Member",
        back_populates="monthly_summaries"
    )
    
    # Constraints and indexes
    __table_args__ = (
        UniqueConstraint(
            "member_id", "year", "month",
            name="uq_attendance_summary_member_month"
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
        return (self.attended_days / self.total_work_days) * 100
    
    def __repr__(self) -> str:
        return f"<MonthlyAttendanceSummary(member_id={self.member_id}, month={self.month_string})>"