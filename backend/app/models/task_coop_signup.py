"""Coop task signup model aligned with docs SQL baseline."""

from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    SmallInteger,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class TaskCoopSignup(BaseModel):
    """协助任务报名表。"""

    __tablename__ = "task_coop_signup"

    coop_task_id: Mapped[int] = mapped_column(
        ForeignKey("task_coop.id", ondelete="CASCADE"),
        nullable=False,
        comment="协助任务ID",
    )
    coop_slot_id: Mapped[int] = mapped_column(
        ForeignKey("task_coop_slot.id", ondelete="CASCADE"),
        nullable=False,
        comment="协助任务时间段ID",
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("app_user.id", ondelete="RESTRICT"),
        nullable=False,
        comment="报名用户ID",
    )
    signup_source: Mapped[str] = mapped_column(
        String(16),
        nullable=False,
        default="self",
        server_default=text("'self'"),
        comment="报名来源",
    )
    status: Mapped[int] = mapped_column(
        SmallInteger,
        nullable=False,
        default=1,
        server_default=text("1"),
        comment="状态",
    )
    reviewed_by: Mapped[int | None] = mapped_column(
        ForeignKey("app_user.id", ondelete="SET NULL"),
        nullable=True,
        comment="审核人",
    )
    reviewed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="审核时间",
    )
    cancel_reason: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="取消原因",
    )

    __table_args__ = (
        UniqueConstraint("coop_slot_id", "user_id", name="uq_task_coop_signup_slot_user"),
        CheckConstraint(
            "signup_source IN ('self','assign')",
            name="ck_task_coop_signup_source",
        ),
        CheckConstraint(
            "status IN (0,1,2,3,4)",
            name="ck_task_coop_signup_status",
        ),
        Index("idx_task_coop_signup_user", "user_id", "status"),
    )
