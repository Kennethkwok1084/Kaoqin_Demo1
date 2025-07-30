"""
Member model for team members in the attendance system.
Represents university network maintenance team members.
"""

import enum
from typing import List, TYPE_CHECKING

from sqlalchemy import (
    Boolean, Column, DateTime, Enum, ForeignKey, Integer, String, Text, UniqueConstraint
)
from sqlalchemy.orm import relationship, Mapped

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.task import RepairTask, MonitoringTask, AssistanceTask
    from app.models.attendance import AttendanceRecord, AttendanceException, MonthlyAttendanceSummary


class UserRole(enum.Enum):
    """User roles in the system."""
    ADMIN = "admin"              # 系统管理员
    GROUP_LEADER = "group_leader"  # 组长
    MEMBER = "member"            # 普通成员
    GUEST = "guest"              # 访客


class Member(BaseModel):
    """
    Team member model.
    
    Represents a member of the university network maintenance team.
    Includes personal information, authentication data, and role.
    """
    
    __tablename__ = "members"
    
    # Basic Information
    name = Column(
        String(50),
        nullable=False,
        index=True,
        comment="Member name"
    )
    
    student_id = Column(
        String(20),
        unique=True,
        nullable=False,
        index=True,
        comment="Student ID (unique identifier)"
    )
    
    # Group and Class Information
    group_id = Column(
        Integer,
        nullable=True,
        comment="Group ID (work group assignment)"
    )
    
    class_name = Column(
        String(50),
        nullable=True,
        comment="Class name"
    )
    
    # Personal Information (encrypted)
    dormitory = Column(
        Text,
        nullable=True,
        comment="Dormitory information (encrypted)"
    )
    
    phone = Column(
        Text,
        nullable=True,
        comment="Phone number (encrypted)"
    )
    
    email = Column(
        String(100),
        nullable=True,
        index=True,
        comment="Email address"
    )
    
    # Authentication
    password_hash = Column(
        String(255),
        nullable=False,
        comment="Hashed password"
    )
    
    # Role and Status
    role = Column(
        Enum(UserRole),
        default=UserRole.MEMBER,
        nullable=False,
        comment="User role"
    )
    
    is_active = Column(
        Boolean,
        default=True,
        nullable=False,
        comment="Whether the member is active"
    )
    
    is_verified = Column(
        Boolean,
        default=False,
        nullable=False,
        comment="Whether the member email is verified"
    )
    
    # Login tracking
    last_login = Column(
        DateTime,
        nullable=True,
        comment="Last login timestamp"
    )
    
    login_count = Column(
        Integer,
        default=0,
        nullable=False,
        comment="Total login count"
    )
    
    # Relationships
    repair_tasks: Mapped[List["RepairTask"]] = relationship(
        "RepairTask",
        back_populates="member",
        cascade="all, delete-orphan",
        lazy="dynamic"
    )
    
    monitoring_tasks: Mapped[List["MonitoringTask"]] = relationship(
        "MonitoringTask",
        back_populates="member",
        cascade="all, delete-orphan",
        lazy="dynamic"
    )
    
    assistance_tasks: Mapped[List["AssistanceTask"]] = relationship(
        "AssistanceTask",
        back_populates="member",
        cascade="all, delete-orphan",
        lazy="dynamic"
    )
    
    attendance_records: Mapped[List["AttendanceRecord"]] = relationship(
        "AttendanceRecord",
        back_populates="member",
        cascade="all, delete-orphan",
        lazy="dynamic"
    )
    
    attendance_exceptions: Mapped[List["AttendanceException"]] = relationship(
        "AttendanceException",
        back_populates="member",
        foreign_keys="AttendanceException.member_id",
        cascade="all, delete-orphan",
        lazy="dynamic"
    )
    
    monthly_summaries: Mapped[List["MonthlyAttendanceSummary"]] = relationship(
        "MonthlyAttendanceSummary",
        back_populates="member",
        cascade="all, delete-orphan",
        lazy="dynamic"
    )
    
    # Constraints
    __table_args__ = (
        UniqueConstraint('student_id', name='uq_member_student_id'),
        {'comment': 'Team members table'}
    )
    
    def __repr__(self) -> str:
        """String representation."""
        return f"<Member(id={self.id}, name='{self.name}', student_id='{self.student_id}')>"
    
    @property
    def is_admin(self) -> bool:
        """Check if member is admin."""
        return self.role == UserRole.ADMIN
    
    @property
    def is_group_leader(self) -> bool:
        """Check if member is group leader."""
        return self.role == UserRole.GROUP_LEADER
    
    @property
    def can_manage_group(self) -> bool:
        """Check if member can manage group."""
        return self.role in [UserRole.ADMIN, UserRole.GROUP_LEADER]
    
    @property
    def can_import_data(self) -> bool:
        """Check if member can import data."""
        return self.role == UserRole.ADMIN
    
    @property
    def can_mark_rush_tasks(self) -> bool:
        """Check if member can mark rush tasks."""
        return self.role == UserRole.ADMIN
    
    def get_display_name(self) -> str:
        """Get display name for UI."""
        return f"{self.name} ({self.student_id})"
    
    def get_safe_dict(self) -> dict:
        """Get safe dictionary without sensitive data."""
        return {
            "id": self.id,
            "name": self.name,
            "student_id": self.student_id,
            "group_id": self.group_id,
            "class_name": self.class_name,
            "email": self.email,
            "role": self.role.value,
            "is_active": self.is_active,
            "is_verified": self.is_verified,
            "last_login": self.last_login.isoformat() if self.last_login else None,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }
    
    def update_login_info(self) -> None:
        """Update login information."""
        from datetime import datetime
        self.last_login = datetime.utcnow()
        self.login_count += 1