"""Coop task attendance model aligned with docs SQL baseline."""

from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    SmallInteger,
    String,
    Text,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class TaskCoopAttendance(BaseModel):
    """协助任务签到签退记录表。"""

    __tablename__ = "task_coop_attendance"

    coop_signup_id: Mapped[int] = mapped_column(
        ForeignKey("task_coop_signup.id", ondelete="CASCADE"),
        nullable=False,
        comment="协助任务报名ID",
    )
    sign_in_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="签到时间",
    )
    sign_out_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="签退时间",
    )
    sign_in_type: Mapped[str | None] = mapped_column(
        String(16),
        nullable=True,
        comment="签到方式",
    )
    sign_out_type: Mapped[str | None] = mapped_column(
        String(16),
        nullable=True,
        comment="签退方式",
    )
    sign_in_longitude: Mapped[float | None] = mapped_column(
        Numeric(10, 6),
        nullable=True,
        comment="签到经度",
    )
    sign_in_latitude: Mapped[float | None] = mapped_column(
        Numeric(10, 6),
        nullable=True,
        comment="签到纬度",
    )
    sign_out_longitude: Mapped[float | None] = mapped_column(
        Numeric(10, 6),
        nullable=True,
        comment="签退经度",
    )
    sign_out_latitude: Mapped[float | None] = mapped_column(
        Numeric(10, 6),
        nullable=True,
        comment="签退纬度",
    )
    qr_token: Mapped[str | None] = mapped_column(
        String(128),
        nullable=True,
        comment="二维码令牌",
    )
    admin_confirmed_by: Mapped[int | None] = mapped_column(
        ForeignKey("app_user.id", ondelete="SET NULL"),
        nullable=True,
        comment="管理员确认人",
    )
    admin_confirmed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="管理员确认时间",
    )
    duration_minutes: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default=text("0"),
        comment="时长(分钟)",
    )
    review_status: Mapped[int] = mapped_column(
        SmallInteger,
        nullable=False,
        default=0,
        server_default=text("0"),
        comment="审核状态",
    )
    remark: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="备注",
    )

    __table_args__ = (
        CheckConstraint(
            "sign_in_type IN ('gps','qr','manual','admin','hybrid') OR sign_in_type IS NULL",
            name="ck_task_coop_attendance_type",
        ),
        CheckConstraint(
            "review_status IN (0,1,2)",
            name="ck_task_coop_attendance_review",
        ),
        Index("idx_task_coop_attendance_signup", "coop_signup_id"),
    )
