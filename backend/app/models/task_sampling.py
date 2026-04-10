"""Sampling task model aligned with docs SQL baseline."""

from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Integer, SmallInteger, String, Text, text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class TaskSampling(BaseModel):
    """网络抽检任务主表。"""

    __tablename__ = "task_sampling"

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
    building_id: Mapped[int] = mapped_column(
        ForeignKey("building.id", ondelete="RESTRICT"),
        nullable=False,
        comment="楼栋ID",
    )
    target_room_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="目标宿舍数量",
    )
    sample_strategy: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="weighted_random",
        server_default=text("'weighted_random'"),
        comment="抽样策略",
    )
    exclude_days: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=30,
        server_default=text("30"),
        comment="排除天数",
    )
    assigned_by: Mapped[int] = mapped_column(
        ForeignKey("app_user.id", ondelete="RESTRICT"),
        nullable=False,
        comment="指派人",
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
    status: Mapped[int] = mapped_column(
        SmallInteger,
        nullable=False,
        default=1,
        server_default=text("1"),
        comment="状态",
    )

    __table_args__ = (
        CheckConstraint(
            "sample_strategy IN ('weighted_random')",
            name="ck_task_sampling_strategy",
        ),
        CheckConstraint("status IN (0,1,2,3,4,5)", name="ck_task_sampling_status"),
    )
