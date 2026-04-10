"""Inspection task point model aligned with docs SQL baseline."""

from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Integer, String, func, text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class TaskInspectionPoint(Base):
    """巡检点位/机柜表。"""

    __tablename__ = "task_inspection_point"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
        autoincrement=True,
        comment="Primary key",
    )
    inspection_task_id: Mapped[int] = mapped_column(
        ForeignKey("task_inspection.id", ondelete="CASCADE"),
        nullable=False,
        comment="巡检任务ID",
    )
    cabinet_name: Mapped[str] = mapped_column(
        String(128),
        nullable=False,
        comment="机柜名称",
    )
    cabinet_location: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        comment="机柜位置",
    )
    sort_no: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
        server_default=text("1"),
        comment="排序号",
    )
    is_mandatory_photo: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default=text("true"),
        comment="是否必须拍照",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="Record creation timestamp",
    )

    __table_args__ = (
        Index("idx_task_inspection_point_task", "inspection_task_id", "sort_no"),
    )
