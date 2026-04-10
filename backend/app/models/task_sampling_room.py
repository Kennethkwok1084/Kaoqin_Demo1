"""Sampling task room model aligned with docs SQL baseline."""

from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Integer, UniqueConstraint, func, text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class TaskSamplingRoom(Base):
    """抽检任务生成后的宿舍清单。"""

    __tablename__ = "task_sampling_room"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
        autoincrement=True,
        comment="Primary key",
    )
    sampling_task_id: Mapped[int] = mapped_column(
        ForeignKey("task_sampling.id", ondelete="CASCADE"),
        nullable=False,
        comment="抽检任务ID",
    )
    dorm_room_id: Mapped[int] = mapped_column(
        ForeignKey("dorm_room.id", ondelete="RESTRICT"),
        nullable=False,
        comment="宿舍ID",
    )
    generated_weight: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default=text("0"),
        comment="生成权重",
    )
    is_completed: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default=text("false"),
        comment="是否完成",
    )
    completed_by: Mapped[int | None] = mapped_column(
        ForeignKey("app_user.id", ondelete="SET NULL"),
        nullable=True,
        comment="完成人",
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="完成时间",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="Record creation timestamp",
    )

    __table_args__ = (
        UniqueConstraint(
            "sampling_task_id",
            "dorm_room_id",
            name="uq_task_sampling_room_task_room",
        ),
        Index(
            "idx_task_sampling_room_task",
            "sampling_task_id",
            "is_completed",
        ),
    )
