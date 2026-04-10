"""Sampling task user model aligned with docs SQL baseline."""

from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Integer, String, UniqueConstraint, func, text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class TaskSamplingUser(Base):
    """抽检任务参与人员表。"""

    __tablename__ = "task_sampling_user"

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
    user_id: Mapped[int] = mapped_column(
        ForeignKey("app_user.id", ondelete="RESTRICT"),
        nullable=False,
        comment="用户ID",
    )
    role_in_task: Mapped[str] = mapped_column(
        String(16),
        nullable=False,
        default="executor",
        server_default=text("'executor'"),
        comment="任务角色",
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
            "user_id",
            name="uq_task_sampling_user_task_user",
        ),
        CheckConstraint(
            "role_in_task IN ('leader','executor')",
            name="ck_task_sampling_user_role",
        ),
    )
