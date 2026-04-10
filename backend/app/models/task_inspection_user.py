"""Inspection task member model aligned with docs SQL baseline."""

from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Integer, SmallInteger, String, UniqueConstraint, func, text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class TaskInspectionUser(Base):
    """巡检任务参与人员表。"""

    __tablename__ = "task_inspection_user"

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
    status: Mapped[int] = mapped_column(
        SmallInteger,
        nullable=False,
        default=1,
        server_default=text("1"),
        comment="状态",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="Record creation timestamp",
    )

    __table_args__ = (
        UniqueConstraint(
            "inspection_task_id",
            "user_id",
            name="uq_task_inspection_user_task_user",
        ),
        CheckConstraint(
            "role_in_task IN ('leader','executor')",
            name="ck_task_inspection_user_role",
        ),
        CheckConstraint("status IN (0,1)", name="ck_task_inspection_user_status"),
    )
