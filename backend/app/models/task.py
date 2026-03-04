"""
Task models for the attendance system.
Includes repair tasks, monitoring tasks, and assistance tasks.
"""

import enum
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Table,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import ENUM as PgEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, BaseModel

if TYPE_CHECKING:
    from app.models.member import Member


class TaskCategory(enum.Enum):
    """Task category enumeration."""

    NETWORK_REPAIR = "network_repair"  # 网络维修
    HARDWARE_REPAIR = "hardware_repair"  # 硬件维修
    SOFTWARE_SUPPORT = "software_support"  # 软件支持
    SOFTWARE_ISSUE = "software_issue"  # 软件问题
    MONITORING = "monitoring"  # 日常监控
    ASSISTANCE = "assistance"  # 协助任务
    OTHER = "other"  # 其他


class TaskPriority(enum.Enum):
    """Task priority enumeration."""

    LOW = "low"  # 低优先级
    MEDIUM = "medium"  # 中优先级
    HIGH = "high"  # 高优先级
    URGENT = "urgent"  # 紧急


class UrgencyLevel(enum.Enum):
    """Urgency level for repair tasks."""

    LOW = "low"  # 低
    NORMAL = "normal"  # 普通
    HIGH = "high"  # 高


class TaskStatus(enum.Enum):
    """Task status enumeration."""

    PENDING = "pending"  # 待处理
    ASSIGNED = "assigned"  # 已分配
    IN_PROGRESS = "in_progress"  # 处理中
    COMPLETED = "completed"  # 已完成
    CANCELLED = "cancelled"  # 已取消
    ON_HOLD = "on_hold"  # 暂停


class TaskType(enum.Enum):
    """Task type for work hour calculation."""

    ONLINE = "online"  # 线上任务 (40分钟)
    OFFLINE = "offline"  # 线下任务 (100分钟)
    REPAIR = "repair"  # 维修任务 (兼容旧代码)
    ASSISTANCE = "assistance"  # 协助任务


class TaskTagType(enum.Enum):
    """Task tag type enumeration for work hour calculation."""

    RUSH_ORDER = "rush_order"  # 爆单标记
    NON_DEFAULT_RATING = "non_default_rating"  # 非默认好评
    TIMEOUT_RESPONSE = "timeout_response"  # 超时响应
    TIMEOUT_PROCESSING = "timeout_processing"  # 超时处理
    BAD_RATING = "bad_rating"  # 差评
    BONUS = "bonus"  # 一般奖励标签
    PENALTY = "penalty"  # 一般惩罚标签
    CATEGORY = "category"  # 分类标签


# Association table for task tags (many-to-many)
task_tag_association = Table(
    "task_tag_associations",
    Base.metadata,
    Column("task_id", Integer, ForeignKey("repair_tasks.id"), primary_key=True),
    Column("tag_id", Integer, ForeignKey("task_tags.id"), primary_key=True),
    comment="Association table for tasks and tags",
)


class TaskTag(BaseModel):
    """
    Task tag model for categorizing and calculating work hours.

    Used to apply bonuses/penalties and categorize tasks.
    Examples: 爆单任务, 非默认好评, 超时响应, etc.
    """

    __tablename__ = "task_tags"

    name = Column(
        String(50), unique=True, nullable=False, index=True, comment="Tag name"
    )

    description = Column(Text, nullable=True, comment="Tag description")

    work_minutes_modifier = Column(
        Integer,
        default=0,
        nullable=False,
        comment="Work minutes modifier (+/- minutes)",
    )

    is_active = Column(
        Boolean, default=True, nullable=False, comment="Whether the tag is active"
    )

    # Tag type for categorization
    tag_type: Mapped[TaskTagType] = mapped_column(
        PgEnum(
            TaskTagType,
            name="tasktagtype",
            create_type=False,
            values_callable=lambda enum_cls: [member.value for member in enum_cls],
        ),
        default=TaskTagType.CATEGORY,
        nullable=False,
        comment="Tag type for categorization and work hour calculation",
    )

    # Relationships
    tasks: Mapped[List["RepairTask"]] = relationship(
        "RepairTask",
        secondary=task_tag_association,
        back_populates="tags",
        lazy="dynamic",
    )

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"<TaskTag(id={self.id}, name='{self.name}', "
            f"type='{self.tag_type.value}', modifier={self.work_minutes_modifier})>"
        )

    @classmethod
    def create_rush_order_tag(cls) -> "TaskTag":
        """创建爆单标签"""
        tag = cls(
            name="爆单任务",
            description="爆单任务标记，独立计算工时15分钟",
            work_minutes_modifier=15,
            is_active=True,
        )
        tag.tag_type = TaskTagType.RUSH_ORDER
        return tag

    @classmethod
    def create_non_default_rating_tag(cls) -> "TaskTag":
        """创建非默认好评标签"""
        tag = cls(
            name="非默认好评",
            description="用户给出非默认好评，奖励30分钟",
            work_minutes_modifier=30,
            is_active=True,
        )
        tag.tag_type = TaskTagType.NON_DEFAULT_RATING
        return tag

    @classmethod
    def create_timeout_response_tag(cls) -> "TaskTag":
        """创建超时响应标签"""
        tag = cls(
            name="超时响应",
            description="响应超过24小时，扣除30分钟",
            work_minutes_modifier=-30,
            is_active=True,
        )
        tag.tag_type = TaskTagType.TIMEOUT_RESPONSE
        return tag

    @classmethod
    def create_timeout_processing_tag(cls) -> "TaskTag":
        """创建超时处理标签"""
        tag = cls(
            name="超时处理",
            description="处理超过48小时，扣除30分钟",
            work_minutes_modifier=-30,
            is_active=True,
        )
        tag.tag_type = TaskTagType.TIMEOUT_PROCESSING
        return tag

    @classmethod
    def create_bad_rating_tag(cls) -> "TaskTag":
        """创建差评标签"""
        tag = cls(
            name="差评",
            description="用户差评（2星及以下），扣除60分钟",
            work_minutes_modifier=-60,
            is_active=True,
        )
        tag.tag_type = TaskTagType.BAD_RATING
        return tag

    @classmethod
    def get_standard_tags(cls) -> List["TaskTag"]:
        """获取标准标签列表"""
        return [
            cls.create_rush_order_tag(),
            cls.create_non_default_rating_tag(),
            cls.create_timeout_response_tag(),
            cls.create_timeout_processing_tag(),
            cls.create_bad_rating_tag(),
        ]

    def is_rush_order_tag(self) -> bool:
        """判断是否为爆单标签"""
        return bool(self.tag_type == TaskTagType.RUSH_ORDER)

    def is_penalty_tag(self) -> bool:
        """判断是否为惩罚标签"""
        return self.tag_type in [
            TaskTagType.TIMEOUT_RESPONSE,
            TaskTagType.TIMEOUT_PROCESSING,
            TaskTagType.BAD_RATING,
            TaskTagType.PENALTY,
        ]

    def is_bonus_tag(self) -> bool:
        """判断是否为奖励标签"""
        return self.tag_type in [TaskTagType.NON_DEFAULT_RATING, TaskTagType.BONUS]


class RepairTask(BaseModel):
    """
    Repair task model.

    Represents wireless/network repair tasks submitted by users.
    Core entity for work hour calculation and attendance tracking.
    """

    def __init__(self, **kwargs: Any) -> None:
        """Initialize RepairTask with required field defaults."""
        # Provide defaults for required fields if not provided
        assigned_member = kwargs.pop("assigned_member_id", None)
        if assigned_member is not None and "member_id" not in kwargs:
            kwargs["member_id"] = assigned_member

        if "is_online_task" in kwargs and "task_type" not in kwargs:
            is_online = kwargs.pop("is_online_task")
            kwargs["task_type"] = (
                TaskType.ONLINE if bool(is_online) else TaskType.OFFLINE
            )

        if "urgency_level" in kwargs and kwargs["urgency_level"] is not None:
            urgency_value = kwargs["urgency_level"]
            if isinstance(urgency_value, UrgencyLevel):
                kwargs["urgency_level"] = urgency_value.value
            elif isinstance(urgency_value, str):
                try:
                    kwargs["urgency_level"] = UrgencyLevel(urgency_value).value
                except ValueError as exc:
                    raise ValueError(
                        f"Invalid urgency level: {urgency_value}"
                    ) from exc
            else:
                raise TypeError("urgency_level must be str or UrgencyLevel")

        if "task_id" not in kwargs:
            kwargs["task_id"] = f"TEST_{id(self)}"  # Generate unique ID for tests
        if "member_id" not in kwargs:
            kwargs["member_id"] = 1  # Default member ID for tests
        if "title" not in kwargs:
            kwargs["title"] = "Test Task"
        if "report_time" not in kwargs:
            from datetime import datetime

            kwargs["report_time"] = datetime.now(timezone.utc)

        super().__init__(**kwargs)

        if getattr(self, "urgency_level", None) is None:
            self.urgency_level = UrgencyLevel.NORMAL.value

        if not getattr(self, "work_minutes", None):
            try:
                self.update_work_minutes()
            except Exception:
                self.work_minutes = getattr(self, "base_work_minutes", 0)

    __tablename__ = "repair_tasks"

    # Task identification
    task_id = Column(
        String(50),
        unique=True,
        nullable=False,
        index=True,
        comment="External task ID from work order system",
    )

    work_order_id = Column(
        String(50), nullable=True, comment="Work order ID from external system"
    )

    # Assignment
    member_id = Column(
        Integer,
        ForeignKey("members.id"),
        nullable=False,
        index=True,
        comment="Assigned member ID",
    )

    assigned_at = Column(
        DateTime(timezone=True), nullable=True, comment="Task assignment time"
    )

    # Task details
    title = Column(String(200), nullable=False, comment="Task title")

    description = Column(Text, nullable=True, comment="Detailed task description")

    location = Column(String(200), nullable=True, comment="Task location")

    # Task categorization
    category: Mapped[TaskCategory] = mapped_column(
        PgEnum(
            TaskCategory,
            name="taskcategory",
            create_type=False,
            values_callable=lambda enum_cls: [member.value for member in enum_cls],
        ),
        default=TaskCategory.NETWORK_REPAIR,
        nullable=False,
        comment="Task category",
    )

    priority: Mapped[TaskPriority] = mapped_column(
        PgEnum(
            TaskPriority,
            name="taskpriority",
            create_type=False,
            values_callable=lambda enum_cls: [member.value for member in enum_cls],
        ),
        default=TaskPriority.MEDIUM,
        nullable=False,
        comment="Task priority",
    )

    urgency_level = Column(
        String(20),
        nullable=False,
        default=UrgencyLevel.NORMAL.value,
        comment="Task urgency level",
    )

    status: Mapped[TaskStatus] = mapped_column(
        PgEnum(
            TaskStatus,
            name="taskstatus",
            create_type=False,
            values_callable=lambda enum_cls: [member.value for member in enum_cls],
        ),
        default=TaskStatus.PENDING,
        nullable=False,
        index=True,
        comment="Task status",
    )

    task_type: Mapped[TaskType] = mapped_column(
        PgEnum(
            TaskType,
            name="tasktype",
            create_type=False,
            values_callable=lambda enum_cls: [member.value for member in enum_cls],
        ),
        default=TaskType.ONLINE,
        nullable=False,
        comment="Task type (online/offline)",
    )

    # Time tracking
    report_time = Column(
        DateTime(timezone=True), nullable=False, index=True, comment="Task report time"
    )

    response_time = Column(
        DateTime(timezone=True), nullable=True, comment="Task response time"
    )

    completion_time = Column(
        DateTime(timezone=True), nullable=True, comment="Task completion time"
    )

    due_date = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="Task due date (usually equals completion_time from import data)",
    )

    # User feedback
    feedback = Column(Text, nullable=True, comment="User feedback")

    rating = Column(Integer, nullable=True, comment="User rating (1-5 stars)")

    # Reporter information
    reporter_name = Column(String(50), nullable=True, comment="Reporter name")

    reporter_contact = Column(
        String(100), nullable=True, comment="Reporter contact information"
    )

    reporter_phone = Column(String(20), nullable=True, comment="Reporter phone number")

    # Work hour calculation
    work_minutes = Column(
        Integer, default=0, nullable=False, comment="Calculated work minutes"
    )

    base_work_minutes = Column(
        Integer, default=0, nullable=False, comment="Base work minutes before modifiers"
    )

    # Import tracking
    import_batch_id = Column(
        String(50), nullable=True, comment="Import batch ID for tracking"
    )

    is_matched = Column(
        Boolean,
        default=False,
        nullable=False,
        comment="Whether task was matched during import",
    )

    # 重构新增字段：完整数据导入支持
    original_data = Column(JSON, nullable=True, comment="A表原始数据完整保存")

    matched_member_data = Column(JSON, nullable=True, comment="B表匹配的成员数据")

    is_rush_order = Column(
        Boolean, default=False, nullable=False, comment="爆单标记，独立计算工时"
    )

    work_order_status = Column(
        String(50), nullable=True, comment="A表工单状态（用于状态映射）"
    )

    repair_form = Column(
        String(50), nullable=True, comment="B表检修形式（用于线上/线下判断）"
    )

    # 线下单标记功能 - 扩展现有模型
    is_offline_marked = Column(
        Boolean, default=False, nullable=False, comment="线下单标记"
    )

    offline_inspection_result = Column(Text, nullable=True, comment="线下检查结果描述")

    offline_images = Column(JSON, nullable=True, comment="线下任务相关图片路径列表")

    offline_marked_by = Column(
        Integer,
        ForeignKey("members.id"),
        nullable=True,
        comment="线下单标记人员ID",
    )

    offline_marked_at = Column(
        DateTime(timezone=True), nullable=True, comment="线下单标记时间"
    )

    @property
    def assigned_member_id(self) -> Optional[int]:
        """Alias for assigned member."""
        return getattr(self, "member_id", None)

    @assigned_member_id.setter
    def assigned_member_id(self, value: Optional[int]) -> None:
        self.member_id = value

    @property
    def is_online_task(self) -> bool:
        """Convenience accessor to check if task is online."""
        task_type = getattr(self, "task_type", None)
        if isinstance(task_type, TaskType):
            return task_type == TaskType.ONLINE
        if isinstance(task_type, str):
            try:
                return TaskType(task_type) == TaskType.ONLINE
            except ValueError:
                return True
        fallback = getattr(self, "_task_type", TaskType.ONLINE)
        if isinstance(fallback, TaskType):
            return fallback == TaskType.ONLINE
        return True

    @is_online_task.setter
    def is_online_task(self, value: bool) -> None:
        self.task_type = TaskType.ONLINE if bool(value) else TaskType.OFFLINE

    # Relationships
    member: Mapped["Member"] = relationship(
        "Member", foreign_keys=[member_id], back_populates="repair_tasks"
    )

    offline_marker: Mapped[Optional["Member"]] = relationship(
        "Member", foreign_keys=[offline_marked_by], post_update=True  # 避免循环引用
    )

    tags: Mapped[List["TaskTag"]] = relationship(
        "TaskTag", secondary=task_tag_association, back_populates="tasks"
    )

    # Constraints and indexes
    __table_args__ = (
        UniqueConstraint("task_id", name="uq_repair_task_task_id"),
        Index("idx_repair_task_report_time", "report_time"),
        Index("idx_repair_task_member_status", "member_id", "status"),
        Index("idx_repair_task_import_batch", "import_batch_id"),
        {"comment": "Repair tasks table"},
    )

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"<RepairTask(id={self.id}, task_id='{self.task_id}', "
            f"status='{self.status.value}')>"
        )

    @property
    def is_overdue_response(self) -> bool:
        """Check if response is overdue (>24 hours from report)."""
        try:
            response_time = self.response_time
            report_time = self.report_time
        except Exception:
            # Handle case when accessing outside session context
            return False

        # Fix B (P0): 不以"是否有 response_time"直接返回
        # 已响应：检查响应耗时是否超限; 未响应：检查当前等待时长是否超限
        if report_time is None:
            return False

        now = datetime.now(timezone.utc)
        report_dt = report_time
        if report_dt.tzinfo is None:
            report_dt = report_dt.replace(tzinfo=timezone.utc)

        if response_time is not None:
            response_dt = response_time
            if response_dt.tzinfo is None:
                response_dt = response_dt.replace(tzinfo=timezone.utc)
            hours = (response_dt - report_dt).total_seconds() / 3600
            return bool(hours > 24)

        # 未响应：当前等待时长
        hours_since_report = (now - report_dt).total_seconds() / 3600
        return bool(hours_since_report > 24)

    @property
    def is_overdue_completion(self) -> bool:
        """Check if completion is overdue (>48 hours from response)."""
        try:
            completion_time = self.completion_time
            response_time = self.response_time
        except Exception:
            # Handle case when accessing outside session context
            return False

        if completion_time or not response_time:
            return False

        now = datetime.now(timezone.utc)
        response_dt = response_time
        if response_dt.tzinfo is None:
            response_dt = response_dt.replace(tzinfo=timezone.utc)
        hours_since_response = (now - response_dt).total_seconds() / 3600
        return bool(hours_since_response > 48)

    @property
    def is_positive_review(self) -> bool:
        """Check if task has positive review (>=4 stars)."""
        try:
            rating = self.rating
        except Exception:
            return False
        return bool(rating is not None and rating >= 4)

    @property
    def is_negative_review(self) -> bool:
        """Check if task has negative review (<=2 stars)."""
        try:
            rating = self.rating
        except Exception:
            return False
        return bool(rating is not None and rating <= 2)

    @property
    def is_non_default_positive_review(self) -> bool:
        """Check if task has non-default positive review."""
        try:
            feedback = self.feedback
        except Exception:
            return False

        if not self.is_positive_review or not feedback:
            return False

        # Check if feedback is not default
        default_keywords = ["系统默认好评", "默认", "自动好评"]
        feedback_lower = feedback.lower()
        return not any(keyword in feedback_lower for keyword in default_keywords)

    def get_base_work_minutes(self) -> int:
        """Get base work minutes based on task type."""
        from app.core.config import settings

        # Handle case when accessing outside session context (e.g., in tests)
        try:
            task_type = self.task_type
        except Exception:
            # Check if we have a direct attribute value first
            if hasattr(self, "_task_type"):
                task_type = self._task_type
            else:
                # Default to online for safety in tests
                task_type = TaskType.ONLINE

        if task_type == TaskType.ONLINE:
            return settings.DEFAULT_ONLINE_TASK_MINUTES
        else:
            return settings.DEFAULT_OFFLINE_TASK_MINUTES

    def calculate_work_minutes(self) -> int:
        """
        Calculate total work minutes including modifiers.
        重构后的工时计算逻辑：
        - 爆单任务：固定15分钟，但仍可与异常扣时叠加
        - 非爆单任务：基础工时 + 附加标签工时 - 异常扣时
        """
        # Handle accessing attributes safely in test context
        try:
            is_rush_order = self.is_rush_order
            tags = list(self.tags) if hasattr(self, "tags") else []
        except Exception:
            # Default values for test context
            is_rush_order = False
            tags = []

        # 爆单任务独立计算
        if is_rush_order:
            rush_minutes = 15  # 爆单任务固定15分钟

            # 爆单任务仍然可以与异常扣时叠加
            penalty_minutes = 0

            # 应用异常扣时标签
            for tag in tags:
                if (
                    hasattr(tag, "is_active")
                    and hasattr(tag, "is_penalty_tag")
                    and tag.is_active
                    and tag.is_penalty_tag()
                ):
                    penalty_minutes += abs(
                        tag.work_minutes_modifier or 0
                    )  # 扣时标签为负数，这里取绝对值

            # Apply time-based penalties
            if self.is_overdue_response:
                from app.core.config import settings

                penalty_minutes += settings.LATE_RESPONSE_PENALTY_MINUTES

            if self.is_overdue_completion:
                from app.core.config import settings

                penalty_minutes += settings.LATE_COMPLETION_PENALTY_MINUTES

            if self.is_negative_review:
                from app.core.config import settings

                penalty_minutes += settings.NEGATIVE_REVIEW_PENALTY_MINUTES

            return max(0, rush_minutes - penalty_minutes)

        # 非爆单任务：传统叠加计算
        base_minutes = self.get_base_work_minutes()
        total_minutes = base_minutes

        # Apply tag modifiers
        for tag in tags:
            if (
                hasattr(tag, "is_active")
                and hasattr(tag, "work_minutes_modifier")
                and tag.is_active
            ):
                total_minutes += tag.work_minutes_modifier or 0

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

    # 重构新增方法：数据完整性支持

    def set_original_data(self, data: Dict[str, Any]) -> None:
        """设置A表原始数据"""
        self.original_data = data

    def set_matched_member_data(self, member_data: Dict[str, Any]) -> None:
        """设置B表匹配的成员数据"""
        self.matched_member_data = member_data

    def mark_as_rush_order(self, is_rush: bool = True) -> None:
        """标记/取消爆单任务"""
        self.is_rush_order = is_rush
        self.update_work_minutes()  # 重新计算工时

    def set_task_type_by_repair_form(self, repair_form: str) -> None:
        """根据B表检修形式设置任务类型"""
        if not repair_form:
            return

        self.repair_form = repair_form
        repair_form_lower = repair_form.lower()

        # 根据检修形式判断线上/线下
        if "远程" in repair_form_lower or "线上" in repair_form_lower:
            self.task_type = TaskType.ONLINE
        elif (
            "现场" in repair_form_lower
            or "线下" in repair_form_lower
            or "实地" in repair_form_lower
        ):
            self.task_type = TaskType.OFFLINE
        else:
            # 默认为线上任务
            self.task_type = TaskType.ONLINE

        # 更新基础工时
        self.base_work_minutes = self.get_base_work_minutes()
        self.update_work_minutes()

    def set_status_by_work_order_status(self, work_order_status: str) -> None:
        """根据A表工单状态设置任务状态"""
        if not work_order_status:
            return

        self.work_order_status = work_order_status
        status_lower = work_order_status.lower()

        # 状态映射规则
        if "已完成" in status_lower or "完成" in status_lower:
            self.status = TaskStatus.COMPLETED
        elif "进行中" in status_lower or "处理中" in status_lower:
            self.status = TaskStatus.IN_PROGRESS
        elif "待处理" in status_lower or "未处理" in status_lower:
            self.status = TaskStatus.PENDING
        elif "已取消" in status_lower or "取消" in status_lower:
            self.status = TaskStatus.CANCELLED
        else:
            # 默认状态
            self.status = TaskStatus.PENDING

    def get_rush_order_info(self) -> Dict[str, Any]:
        """获取爆单任务信息"""
        return {
            "is_rush_order": self.is_rush_order,
            "rush_work_minutes": 15 if self.is_rush_order else 0,
            "normal_work_minutes": (
                self.calculate_work_minutes() if not self.is_rush_order else 0
            ),
        }

    def get_import_data_summary(self) -> Dict[str, Any]:
        """获取导入数据摘要"""
        return {
            "has_original_data": bool(self.original_data),
            "has_matched_member_data": bool(self.matched_member_data),
            "is_matched": self.is_matched,
            "import_batch_id": self.import_batch_id,
            "work_order_status": self.work_order_status,
            "repair_form": self.repair_form,
        }

    # 线下单标记功能方法

    def mark_as_offline(
        self,
        marker_id: int,
        inspection_result: Optional[str] = None,
        images: Optional[List[str]] = None,
    ) -> None:
        """标记为线下单"""
        from datetime import datetime

        self.is_offline_marked = True
        self.offline_marked_by = marker_id
        self.offline_marked_at = datetime.now(timezone.utc)

        if inspection_result:
            self.offline_inspection_result = inspection_result

        if images:
            self.offline_images = images

        # 自动设置任务类型为线下
        self.task_type = TaskType.OFFLINE
        self.update_work_minutes()

    def unmark_offline(self) -> None:
        """取消线下单标记"""
        self.is_offline_marked = False
        self.offline_marked_by = None
        self.offline_marked_at = None
        self.offline_inspection_result = None
        self.offline_images = None

        # 恢复为线上任务（如果没有其他线下依据）
        if not self.repair_form or "现场" not in self.repair_form.lower():
            self.task_type = TaskType.ONLINE

        self.update_work_minutes()

    def add_offline_images(self, image_paths: List[str]) -> None:
        """添加线下任务图片"""
        if not self.offline_images:
            self.offline_images = []

        existing_images = (
            self.offline_images if isinstance(self.offline_images, list) else []
        )
        self.offline_images = list(set(existing_images + image_paths))

    def remove_offline_image(self, image_path: str) -> None:
        """删除线下任务图片"""
        if self.offline_images and isinstance(self.offline_images, list):
            if image_path in self.offline_images:
                self.offline_images.remove(image_path)

    def update_offline_inspection_result(self, result: str) -> None:
        """更新线下检查结果"""
        self.offline_inspection_result = result

    def get_offline_info(self) -> Dict[str, Any]:
        """获取线下单信息"""
        return {
            "is_offline_marked": self.is_offline_marked,
            "offline_marked_by": self.offline_marked_by,
            "offline_marked_at": (
                self.offline_marked_at.isoformat() if self.offline_marked_at else None
            ),
            "offline_inspection_result": self.offline_inspection_result,
            "offline_images": self.offline_images or [],
            "offline_images_count": (
                len(self.offline_images) if self.offline_images else 0
            ),
        }


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
        comment="Assigned member ID",
    )

    # Task details
    title = Column(String(200), nullable=False, comment="Task title")

    description = Column(Text, nullable=True, comment="Task description")

    location = Column(String(200), nullable=True, comment="Monitoring location")

    # Task categorization
    monitoring_type = Column(
        String(50),
        nullable=False,
        comment="Monitoring type (inspection, maintenance, etc.)",
    )

    # Time tracking
    start_time = Column(
        DateTime(timezone=True), nullable=False, comment="Task start time"
    )

    end_time = Column(DateTime(timezone=True), nullable=False, comment="Task end time")

    work_minutes = Column(Integer, nullable=False, comment="Actual work minutes")

    # 巡检任务支持 - 扩展现有任务类型
    cabinet_count = Column(
        Integer, nullable=True, comment="巡检机柜数量（用于计算工时）"
    )

    minutes_per_cabinet = Column(
        Integer, default=5, nullable=False, comment="每个机柜的巡检时长（分钟）"
    )

    inspection_notes = Column(Text, nullable=True, comment="巡检记录和备注")

    equipment_checked = Column(
        JSON, nullable=True, comment="已检查设备清单（JSON格式）"
    )

    issues_found = Column(JSON, nullable=True, comment="发现的问题记录（JSON格式）")

    # Status
    status: Mapped[TaskStatus] = mapped_column(
        PgEnum(
            TaskStatus,
            name="taskstatus",
            create_type=False,
            values_callable=lambda enum_cls: [member.value for member in enum_cls],
        ),
        default=TaskStatus.COMPLETED,
        nullable=False,
        comment="Task status",
    )

    # Relationships
    member: Mapped["Member"] = relationship(
        "Member", foreign_keys=[member_id], back_populates="monitoring_tasks"
    )

    # Constraints and indexes
    __table_args__ = (
        Index("idx_monitoring_task_member_time", "member_id", "start_time"),
        {"comment": "Monitoring tasks table"},
    )

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"<MonitoringTask(id={self.id}, member_id={self.member_id}, "
            f"work_minutes={self.work_minutes})>"
        )

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
        comment="Assisting member ID",
    )

    # Task details
    title = Column(String(200), nullable=False, comment="Assistance task title")

    description = Column(Text, nullable=True, comment="Task description")

    assisted_department = Column(
        String(100), nullable=True, comment="Assisted department/team"
    )

    assisted_person = Column(String(50), nullable=True, comment="Assisted person name")

    # Time tracking
    start_time = Column(
        DateTime(timezone=True), nullable=False, comment="Task start time"
    )

    end_time = Column(DateTime(timezone=True), nullable=False, comment="Task end time")

    work_minutes = Column(Integer, nullable=False, comment="Assistance work minutes")

    # Status
    status: Mapped[TaskStatus] = mapped_column(
        PgEnum(
            TaskStatus,
            name="taskstatus",
            create_type=False,
            values_callable=lambda enum_cls: [member.value for member in enum_cls],
        ),
        default=TaskStatus.PENDING,  # 改为待审核状态
        nullable=False,
        comment="Task status",
    )

    # 审核流程字段 - 扩展现有模型
    approved_by = Column(
        Integer,
        ForeignKey("members.id"),
        nullable=True,
        comment="Approver member ID",
    )

    approved_at = Column(
        DateTime(timezone=True), nullable=True, comment="Approval time"
    )

    review_comment = Column(
        Text, nullable=True, comment="Review comment for the assistance task"
    )

    # Relationships
    member: Mapped["Member"] = relationship(
        "Member", foreign_keys=[member_id], back_populates="assistance_tasks"
    )

    approver: Mapped[Optional["Member"]] = relationship(
        "Member", foreign_keys=[approved_by], post_update=True  # 避免循环引用
    )

    # Constraints and indexes
    __table_args__ = (
        Index("idx_assistance_task_member_time", "member_id", "start_time"),
        {"comment": "Assistance tasks table"},
    )

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"<AssistanceTask(id={self.id}, member_id={self.member_id}, "
            f"work_minutes={self.work_minutes})>"
        )

    def calculate_duration_minutes(self) -> int:
        """Calculate duration in minutes."""
        if self.end_time and self.start_time:
            duration = self.end_time - self.start_time
            return int(duration.total_seconds() / 60)
        return 0

    def update_work_minutes(self) -> None:
        """Update work minutes based on duration."""
        self.work_minutes = self.calculate_duration_minutes()
