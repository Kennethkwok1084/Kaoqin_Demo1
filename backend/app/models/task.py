"""
Task models for the attendance system.
Includes repair tasks, monitoring tasks, and assistance tasks.
"""

import enum
from datetime import datetime
from typing import List, TYPE_CHECKING, Optional

from sqlalchemy import (
    Boolean, Column, DateTime, Enum, ForeignKey, Integer, String, Text, Table,
    Float, UniqueConstraint, Index
)
from sqlalchemy.orm import relationship, Mapped

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.member import Member


class TaskCategory(enum.Enum):
    """Task category enumeration."""
    NETWORK_REPAIR = "network_repair"      # 网络维修
    HARDWARE_REPAIR = "hardware_repair"    # 硬件维修
    SOFTWARE_SUPPORT = "software_support"  # 软件支持
    MONITORING = "monitoring"              # 日常监控
    ASSISTANCE = "assistance"              # 协助任务
    OTHER = "other"                        # 其他


class TaskPriority(enum.Enum):
    """Task priority enumeration."""
    LOW = "low"           # 低优先级
    MEDIUM = "medium"     # 中优先级
    HIGH = "high"         # 高优先级
    URGENT = "urgent"     # 紧急


class TaskStatus(enum.Enum):
    """Task status enumeration."""
    PENDING = "pending"         # 待处理
    IN_PROGRESS = "in_progress" # 处理中
    COMPLETED = "completed"     # 已完成
    CANCELLED = "cancelled"     # 已取消
    ON_HOLD = "on_hold"        # 暂停


class TaskType(enum.Enum):
    """Task type for work hour calculation."""
    ONLINE = "online"     # 线上任务 (40分钟)
    OFFLINE = "offline"   # 线下任务 (100分钟)


# Association table for task tags (many-to-many)
task_tag_association = Table(
    'task_tag_associations',
    BaseModel.metadata,
    Column('task_id', Integer, ForeignKey('repair_tasks.id'), primary_key=True),
    Column('tag_id', Integer, ForeignKey('task_tags.id'), primary_key=True),
    comment='Association table for tasks and tags'
)


class TaskTag(BaseModel):
    """
    Task tag model for categorizing and calculating work hours.
    
    Used to apply bonuses/penalties and categorize tasks.
    Examples: 爆单任务, 非默认好评, 超时响应, etc.
    """
    
    __tablename__ = "task_tags"
    
    name = Column(
        String(50),
        unique=True,
        nullable=False,
        index=True,
        comment="Tag name"
    )
    
    description = Column(
        Text,
        nullable=True,
        comment="Tag description"
    )
    
    work_minutes_modifier = Column(
        Integer,
        default=0,
        nullable=False,
        comment="Work minutes modifier (+/- minutes)"
    )
    
    is_active = Column(
        Boolean,
        default=True,
        nullable=False,
        comment="Whether the tag is active"
    )
    
    # Tag type for categorization
    tag_type = Column(
        String(30),
        nullable=True,
        comment="Tag type (bonus, penalty, category)"
    )
    
    # Relationships
    tasks: Mapped[List["RepairTask"]] = relationship(
        "RepairTask",
        secondary=task_tag_association,
        back_populates="tags",
        lazy="dynamic"
    )
    
    def __repr__(self) -> str:
        """String representation."""
        return f"<TaskTag(id={self.id}, name='{self.name}', modifier={self.work_minutes_modifier})>"


class RepairTask(BaseModel):
    """
    Repair task model.
    
    Represents wireless/network repair tasks submitted by users.
    Core entity for work hour calculation and attendance tracking.
    """
    
    __tablename__ = "repair_tasks"
    
    # Task identification
    task_id = Column(
        String(50),
        unique=True,
        nullable=False,
        index=True,
        comment="External task ID from work order system"
    )
    
    # Assignment
    member_id = Column(
        Integer,
        ForeignKey("members.id"),
        nullable=False,
        index=True,
        comment="Assigned member ID"
    )
    
    # Task details
    title = Column(
        String(200),
        nullable=False,
        comment="Task title"
    )
    
    description = Column(
        Text,
        nullable=True,
        comment="Detailed task description"
    )
    
    location = Column(
        String(200),
        nullable=True,
        comment="Task location"
    )
    
    # Task categorization
    category = Column(
        Enum(TaskCategory),
        default=TaskCategory.NETWORK_REPAIR,
        nullable=False,
        comment="Task category"
    )
    
    priority = Column(
        Enum(TaskPriority),
        default=TaskPriority.MEDIUM,
        nullable=False,
        comment="Task priority"
    )
    
    status = Column(
        Enum(TaskStatus),
        default=TaskStatus.PENDING,
        nullable=False,
        index=True,
        comment="Task status"
    )
    
    task_type = Column(
        Enum(TaskType),
        default=TaskType.ONLINE,
        nullable=False,
        comment="Task type (online/offline)"
    )
    
    # Time tracking
    report_time = Column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
        comment="Task report time"
    )
    
    response_time = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="Task response time"
    )
    
    completion_time = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="Task completion time"
    )
    
    # User feedback
    feedback = Column(
        Text,
        nullable=True,
        comment="User feedback"
    )
    
    rating = Column(
        Integer,
        nullable=True,
        comment="User rating (1-5 stars)"
    )
    
    # Reporter information
    reporter_name = Column(
        String(50),
        nullable=True,
        comment="Reporter name"
    )
    
    reporter_contact = Column(
        String(100),
        nullable=True,
        comment="Reporter contact information"
    )
    
    # Work hour calculation
    work_minutes = Column(
        Integer,
        default=0,
        nullable=False,
        comment="Calculated work minutes"
    )
    
    base_work_minutes = Column(
        Integer,
        default=0,
        nullable=False,
        comment="Base work minutes before modifiers"
    )
    
    # Import tracking
    import_batch_id = Column(
        String(50),
        nullable=True,
        comment="Import batch ID for tracking"
    )
    
    is_matched = Column(
        Boolean,
        default=False,
        nullable=False,
        comment="Whether task was matched during import"
    )
    
    # Relationships
    member: Mapped["Member"] = relationship("Member", back_populates="repair_tasks")
    
    tags: Mapped[List[TaskTag]] = relationship(
        TaskTag,
        secondary=task_tag_association,
        back_populates="tasks",
        lazy="dynamic"
    )
    
    # Constraints and indexes
    __table_args__ = (
        UniqueConstraint('task_id', name='uq_repair_task_task_id'),
        Index('idx_repair_task_report_time', 'report_time'),
        Index('idx_repair_task_member_status', 'member_id', 'status'),
        Index('idx_repair_task_import_batch', 'import_batch_id'),
        {'comment': 'Repair tasks table'}
    )
    
    def __repr__(self) -> str:
        """String representation."""
        return f"<RepairTask(id={self.id}, task_id='{self.task_id}', status='{self.status.value}')>"
    
    @property
    def is_overdue_response(self) -> bool:
        """Check if response is overdue (>24 hours)."""
        if self.response_time or self.status != TaskStatus.PENDING:
            return False
        
        hours_since_report = (datetime.utcnow() - self.report_time).total_seconds() / 3600
        return hours_since_report > 24
    
    @property
    def is_overdue_completion(self) -> bool:
        """Check if completion is overdue (>48 hours from response)."""
        if self.completion_time or not self.response_time:
            return False
        
        hours_since_response = (datetime.utcnow() - self.response_time).total_seconds() / 3600
        return hours_since_response > 48
    
    @property
    def is_positive_review(self) -> bool:
        """Check if task has positive review (>=4 stars)."""
        return self.rating is not None and self.rating >= 4
    
    @property
    def is_negative_review(self) -> bool:
        """Check if task has negative review (<=2 stars)."""
        return self.rating is not None and self.rating <= 2
    
    @property
    def is_non_default_positive_review(self) -> bool:
        """Check if task has non-default positive review."""
        if not self.is_positive_review or not self.feedback:
            return False
        
        # Check if feedback is not default
        default_keywords = ["系统默认好评", "默认", "自动好评"]
        feedback_lower = self.feedback.lower()
        return not any(keyword in feedback_lower for keyword in default_keywords)
    
    def get_base_work_minutes(self) -> int:
        """Get base work minutes based on task type."""
        from app.core.config import settings
        
        if self.task_type == TaskType.ONLINE:
            return settings.DEFAULT_ONLINE_TASK_MINUTES
        else:
            return settings.DEFAULT_OFFLINE_TASK_MINUTES
    
    def calculate_work_minutes(self) -> int:
        """Calculate total work minutes including modifiers."""
        # Start with base minutes
        base_minutes = self.get_base_work_minutes()
        total_minutes = base_minutes
        
        # Apply tag modifiers
        for tag in self.tags:
            if tag.is_active:
                total_minutes += tag.work_minutes_modifier
        
        # Apply time-based penalties
        if self.is_overdue_response:
            from app.core.config import settings
            total_minutes -= settings.LATE_RESPONSE_PENALTY_MINUTES
        
        if self.is_overdue_completion:
            from app.core.config import settings
            total_minutes -= settings.LATE_COMPLETION_PENALTY_MINUTES
        
        if self.is_negative_review:
            from app.core.config import settings
            total_minutes -= settings.NEGATIVE_REVIEW_PENALTY_MINUTES
        
        # Ensure minimum 0 minutes
        return max(0, total_minutes)
    
    def update_work_minutes(self) -> None:
        """Update calculated work minutes."""
        self.base_work_minutes = self.get_base_work_minutes()
        self.work_minutes = self.calculate_work_minutes()
    
    def add_tag(self, tag: TaskTag) -> None:
        """Add a tag to the task."""
        if tag not in self.tags:
            self.tags.append(tag)
            self.update_work_minutes()
    
    def remove_tag(self, tag: TaskTag) -> None:
        """Remove a tag from the task."""
        if tag in self.tags:
            self.tags.remove(tag)
            self.update_work_minutes()


class MonitoringTask(BaseModel):
    """
    Monitoring task model.
    
    Represents daily monitoring and inspection tasks.
    Members manually log these tasks with time tracking.
    """
    
    __tablename__ = "monitoring_tasks"
    
    # Assignment
    member_id = Column(
        Integer,
        ForeignKey("members.id"),
        nullable=False,
        index=True,
        comment="Assigned member ID"
    )
    
    # Task details
    title = Column(
        String(200),
        nullable=False,
        comment="Task title"
    )
    
    description = Column(
        Text,
        nullable=True,
        comment="Task description"
    )
    
    location = Column(
        String(200),
        nullable=True,
        comment="Monitoring location"
    )
    
    # Task categorization
    monitoring_type = Column(
        String(50),
        nullable=False,
        comment="Monitoring type (inspection, maintenance, etc.)"
    )
    
    # Time tracking
    start_time = Column(
        DateTime(timezone=True),
        nullable=False,
        comment="Task start time"
    )
    
    end_time = Column(
        DateTime(timezone=True),
        nullable=False,
        comment="Task end time"
    )
    
    work_minutes = Column(
        Integer,
        nullable=False,
        comment="Actual work minutes"
    )
    
    # Status
    status = Column(
        Enum(TaskStatus),
        default=TaskStatus.COMPLETED,
        nullable=False,
        comment="Task status"
    )
    
    # Relationships
    member: Mapped["Member"] = relationship("Member", back_populates="monitoring_tasks")
    
    # Constraints and indexes
    __table_args__ = (
        Index('idx_monitoring_task_member_time', 'member_id', 'start_time'),
        {'comment': 'Monitoring tasks table'}
    )
    
    def __repr__(self) -> str:
        """String representation."""
        return f"<MonitoringTask(id={self.id}, member_id={self.member_id}, work_minutes={self.work_minutes})>"
    
    def calculate_duration_minutes(self) -> int:
        """Calculate duration in minutes."""
        if self.end_time and self.start_time:
            duration = self.end_time - self.start_time
            return int(duration.total_seconds() / 60)
        return 0
    
    def update_work_minutes(self) -> None:
        """Update work minutes based on duration."""
        self.work_minutes = self.calculate_duration_minutes()


class AssistanceTask(BaseModel):
    """
    Assistance task model.
    
    Represents tasks where members assist other departments or teams.
    """
    
    __tablename__ = "assistance_tasks"
    
    # Assignment
    member_id = Column(
        Integer,
        ForeignKey("members.id"),
        nullable=False,
        index=True,
        comment="Assisting member ID"
    )
    
    # Task details
    title = Column(
        String(200),
        nullable=False,
        comment="Assistance task title"
    )
    
    description = Column(
        Text,
        nullable=True,
        comment="Task description"
    )
    
    assisted_department = Column(
        String(100),
        nullable=True,
        comment="Assisted department/team"
    )
    
    assisted_person = Column(
        String(50),
        nullable=True,
        comment="Assisted person name"
    )
    
    # Time tracking
    start_time = Column(
        DateTime(timezone=True),
        nullable=False,
        comment="Task start time"
    )
    
    end_time = Column(
        DateTime(timezone=True),
        nullable=False,
        comment="Task end time"
    )
    
    work_minutes = Column(
        Integer,
        nullable=False,
        comment="Assistance work minutes"
    )
    
    # Status
    status = Column(
        Enum(TaskStatus),
        default=TaskStatus.COMPLETED,
        nullable=False,
        comment="Task status"
    )
    
    # Relationships
    member: Mapped["Member"] = relationship("Member", back_populates="assistance_tasks")
    
    # Constraints and indexes
    __table_args__ = (
        Index('idx_assistance_task_member_time', 'member_id', 'start_time'),
        {'comment': 'Assistance tasks table'}
    )
    
    def __repr__(self) -> str:
        """String representation."""
        return f"<AssistanceTask(id={self.id}, member_id={self.member_id}, work_minutes={self.work_minutes})>"
    
    def calculate_duration_minutes(self) -> int:
        """Calculate duration in minutes."""
        if self.end_time and self.start_time:
            duration = self.end_time - self.start_time
            return int(duration.total_seconds() / 60)
        return 0
    
    def update_work_minutes(self) -> None:
        """Update work minutes based on duration."""
        self.work_minutes = self.calculate_duration_minutes()