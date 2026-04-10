"""Coop task model aligned with docs SQL baseline."""

from datetime import datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    SmallInteger,
    String,
    Text,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class TaskCoop(BaseModel):
    """协助任务主表。"""

    __tablename__ = "task_coop"

    task_code: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        unique=True,
        comment="任务编码",
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False, comment="标题")
    description: Mapped[str | None] = mapped_column(Text, nullable=True, comment="描述")
    location_text: Mapped[str | None] = mapped_column(
        String(255), nullable=True, comment="地点文本"
    )
    building_id: Mapped[int | None] = mapped_column(
        ForeignKey("building.id", ondelete="SET NULL"),
        nullable=True,
        comment="楼栋ID",
    )
    signup_need_review: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default=text("false"),
        comment="报名是否需要审核",
    )
    sign_in_mode_mask: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default=text("0"),
        comment="签到方式位掩码",
    )
    no_show_enabled: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default=text("true"),
        comment="是否启用爽约",
    )
    status: Mapped[int] = mapped_column(
        SmallInteger,
        nullable=False,
        default=0,
        server_default=text("0"),
        comment="状态",
    )
    created_by: Mapped[int] = mapped_column(
        ForeignKey("app_user.id", ondelete="RESTRICT"),
        nullable=False,
        comment="创建人",
    )
    published_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="发布时间",
    )

    __table_args__ = (
        CheckConstraint("status IN (0,1,2,3,4,5)", name="ck_task_coop_status"),
        Index("idx_task_coop_status_time", "status", "published_at"),
    )
