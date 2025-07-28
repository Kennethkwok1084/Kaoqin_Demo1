"""
Attendance model for monthly attendance tracking.
Calculates and stores work hour summaries for each member.
"""

from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import (
    Column, Float, ForeignKey, Integer, String, UniqueConstraint, Index, Text
)
from sqlalchemy.orm import relationship

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.member import Member


class AttendanceRecord(BaseModel):
    """
    Monthly attendance record model.
    
    Stores calculated work hours for each member by month.
    Includes all task types and carries forward remaining hours.
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
    
    # Time period
    month = Column(
        String(7),  # YYYY-MM format
        nullable=False,
        index=True,
        comment="Month in YYYY-MM format"
    )
    
    # Work hour categories (in hours, float for precision)
    repair_task_hours = Column(
        Float,
        default=0.0,
        nullable=False,
        comment="Repair task hours for the month"
    )
    
    monitoring_hours = Column(
        Float,
        default=0.0,
        nullable=False,
        comment="Monitoring task hours for the month"
    )
    
    assistance_hours = Column(
        Float,
        default=0.0,
        nullable=False,
        comment="Assistance task hours for the month"
    )
    
    # Carried hours from previous month
    carried_hours = Column(
        Float,
        default=0.0,
        nullable=False,
        comment="Hours carried from previous month"
    )
    
    # Calculated totals
    total_hours = Column(
        Float,
        default=0.0,
        nullable=False,
        comment="Total work hours (all categories + carried)"
    )
    
    # Hours that can be carried to next month
    remaining_hours = Column(
        Float,
        default=0.0,
        nullable=False,
        comment="Remaining hours for next month"
    )
    
    # Detailed breakdown (JSON-like text field for flexibility)
    details = Column(
        Text,
        nullable=True,
        comment="Detailed calculation breakdown (JSON format)"
    )
    
    # Calculation metadata
    calculation_date = Column(
        "calculation_date",
        nullable=True,
        comment="When the calculation was performed"
    )
    
    is_final = Column(
        "is_final",
        default=False,
        nullable=False,
        comment="Whether this record is finalized"
    )
    
    # Relationships
    member: "Member" = relationship("Member", back_populates="attendance_records")
    
    # Constraints and indexes
    __table_args__ = (
        UniqueConstraint('member_id', 'month', name='uq_attendance_member_month'),
        Index('idx_attendance_month', 'month'),
        Index('idx_attendance_member_month', 'member_id', 'month'),
        {'comment': 'Monthly attendance records table'}
    )
    
    def __repr__(self) -> str:
        """String representation."""
        return f"<AttendanceRecord(id={self.id}, member_id={self.member_id}, month='{self.month}', total_hours={self.total_hours})>"
    
    @property
    def year(self) -> int:
        """Get year from month string."""
        return int(self.month.split('-')[0])
    
    @property
    def month_number(self) -> int:
        """Get month number from month string."""
        return int(self.month.split('-')[1])
    
    @property
    def month_datetime(self) -> datetime:
        """Get datetime object for the month."""
        return datetime(self.year, self.month_number, 1)
    
    def calculate_total_hours(self) -> float:
        """Calculate total hours from all categories."""
        return (
            self.repair_task_hours +
            self.monitoring_hours +
            self.assistance_hours +
            self.carried_hours
        )
    
    def update_total_hours(self) -> None:
        """Update total hours calculation."""
        self.total_hours = self.calculate_total_hours()
    
    def get_work_hours_breakdown(self) -> dict:
        """Get breakdown of work hours by category."""
        return {
            "repair_tasks": round(self.repair_task_hours, 1),
            "monitoring": round(self.monitoring_hours, 1),
            "assistance": round(self.assistance_hours, 1),
            "carried": round(self.carried_hours, 1),
            "total": round(self.total_hours, 1),
            "remaining": round(self.remaining_hours, 1)
        }
    
    def minutes_to_hours(self, minutes: int) -> float:
        """Convert minutes to hours (rounded to 1 decimal)."""
        return round(minutes / 60.0, 1)
    
    def hours_to_minutes(self, hours: float) -> int:
        """Convert hours to minutes."""
        return int(hours * 60)
    
    @classmethod
    def get_month_string(cls, year: int, month: int) -> str:
        """Get month string in YYYY-MM format."""
        return f"{year:04d}-{month:02d}"
    
    @classmethod
    def get_current_month_string(cls) -> str:
        """Get current month string."""
        now = datetime.utcnow()
        return cls.get_month_string(now.year, now.month)
    
    @classmethod
    def get_previous_month_string(cls, month_str: str) -> str:
        """Get previous month string."""
        year, month = map(int, month_str.split('-'))
        if month == 1:
            return cls.get_month_string(year - 1, 12)
        else:
            return cls.get_month_string(year, month - 1)
    
    @classmethod
    def get_next_month_string(cls, month_str: str) -> str:
        """Get next month string."""
        year, month = map(int, month_str.split('-'))
        if month == 12:
            return cls.get_month_string(year + 1, 1)
        else:
            return cls.get_month_string(year, month + 1)


class AttendanceConfiguration(BaseModel):
    """
    Configuration for attendance calculations.
    
    Stores system-wide settings for work hour calculations.
    """
    
    __tablename__ = "attendance_configurations"
    
    # Configuration key
    config_key = Column(
        String(50),
        unique=True,
        nullable=False,
        index=True,
        comment="Configuration key"
    )
    
    # Configuration value
    config_value = Column(
        String(200),
        nullable=False,
        comment="Configuration value"
    )
    
    # Description
    description = Column(
        Text,
        nullable=True,
        comment="Configuration description"
    )
    
    # Data type hint
    value_type = Column(
        String(20),
        default="string",
        nullable=False,
        comment="Value data type (int, float, string, bool)"
    )
    
    # Whether this config is active
    is_active = Column(
        "is_active",
        default=True,
        nullable=False,
        comment="Whether this configuration is active"
    )
    
    # Constraints
    __table_args__ = (
        UniqueConstraint('config_key', name='uq_attendance_config_key'),
        {'comment': 'Attendance calculation configurations'}
    )
    
    def __repr__(self) -> str:
        """String representation."""
        return f"<AttendanceConfiguration(key='{self.config_key}', value='{self.config_value}')>"
    
    def get_typed_value(self):
        """Get value converted to appropriate type."""
        if self.value_type == "int":
            return int(self.config_value)
        elif self.value_type == "float":
            return float(self.config_value)
        elif self.value_type == "bool":
            return self.config_value.lower() in ("true", "1", "yes", "on")
        else:
            return self.config_value
    
    @classmethod
    def get_config(cls, session, key: str, default=None):
        """Get configuration value by key."""
        config = session.query(cls).filter(
            cls.config_key == key,
            cls.is_active == True
        ).first()
        
        if config:
            return config.get_typed_value()
        return default
    
    @classmethod
    def set_config(cls, session, key: str, value, description: str = None, value_type: str = "string"):
        """Set configuration value."""
        config = session.query(cls).filter(cls.config_key == key).first()
        
        if config:
            config.config_value = str(value)
            config.description = description or config.description
            config.value_type = value_type
            config.is_active = True
        else:
            config = cls(
                config_key=key,
                config_value=str(value),
                description=description,
                value_type=value_type,
                is_active=True
            )
            session.add(config)
        
        return config


# Predefined configuration keys
ATTENDANCE_CONFIG_KEYS = {
    "online_task_minutes": {
        "default": 40,
        "description": "Base minutes for online tasks",
        "type": "int"
    },
    "offline_task_minutes": {
        "default": 100,
        "description": "Base minutes for offline tasks",
        "type": "int"
    },
    "rush_task_bonus": {
        "default": 15,
        "description": "Bonus minutes for rush tasks",
        "type": "int"
    },
    "positive_review_bonus": {
        "default": 30,
        "description": "Bonus minutes for positive reviews",
        "type": "int"
    },
    "late_response_penalty": {
        "default": 30,
        "description": "Penalty minutes for late response",
        "type": "int"
    },
    "late_completion_penalty": {
        "default": 30,
        "description": "Penalty minutes for late completion",
        "type": "int"
    },
    "negative_review_penalty": {
        "default": 60,
        "description": "Penalty minutes for negative reviews",
        "type": "int"
    },
    "response_timeout_hours": {
        "default": 24,
        "description": "Hours before response is considered late",
        "type": "int"
    },
    "completion_timeout_hours": {
        "default": 48,
        "description": "Hours before completion is considered late",
        "type": "int"
    }
}