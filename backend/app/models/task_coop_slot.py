"""Coop task slot model aligned with docs SQL baseline."""

from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    SmallInteger,
    String,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class TaskCoopSlot(BaseModel):
    """协助任务时间段表。"""

    __tablename__ = "task_coop_slot"

    coop_task_id: Mapped[int] = mapped_column(
        ForeignKey("task_coop.id", ondelete="CASCADE"),
        nullable=False,
        comment="协助任务ID",
    )
    slot_title: Mapped[str | None] = mapped_column(
        String(128),
        nullable=True,
        comment="时间段标题",
    )
    start_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        comment="开始时间",
    )
    end_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        comment="结束时间",
    )
    signup_limit: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
        server_default=text("1"),
        comment="报名上限",
    )
    sort_no: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
        server_default=text("1"),
        comment="排序号",
    )
    status: Mapped[int] = mapped_column(
        SmallInteger,
        nullable=False,
        default=1,
        server_default=text("1"),
        comment="状态",
    )

    __table_args__ = (
        CheckConstraint("end_time > start_time", name="ck_task_coop_slot_time"),
        CheckConstraint("status IN (0,1)", name="ck_task_coop_slot_status"),
        Index("idx_task_coop_slot_task", "coop_task_id", "start_time"),
    )
