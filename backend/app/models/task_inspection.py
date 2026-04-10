"""Inspection task model aligned with docs SQL baseline."""

from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, SmallInteger, String, Text, text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class TaskInspection(BaseModel):
    """巡检任务主表。"""

    __tablename__ = "task_inspection"

    task_code: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        unique=True,
        comment="任务编码",
    )
    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="标题",
    )
    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="描述",
    )
    building_id: Mapped[int | None] = mapped_column(
        ForeignKey("building.id", ondelete="SET NULL"),
        nullable=True,
        comment="楼栋ID",
    )
    planned_start_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="计划开始时间",
    )
    planned_end_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="计划结束时间",
    )
    assigned_by: Mapped[int] = mapped_column(
        ForeignKey("app_user.id", ondelete="RESTRICT"),
        nullable=False,
        comment="指派人",
    )
    status: Mapped[int] = mapped_column(
        SmallInteger,
        nullable=False,
        default=1,
        server_default=text("1"),
        comment="状态",
    )

    __table_args__ = (
        CheckConstraint("status IN (0,1,2,3,4,5)", name="ck_task_inspection_status"),
    )
