"""Sampling record model aligned with docs SQL baseline."""

from datetime import datetime

from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, Index, Integer, Numeric, SmallInteger, String, Text, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class SamplingRecord(BaseModel):
    """网络抽检结果主表。"""

    __tablename__ = "sampling_record"

    sampling_task_id: Mapped[int] = mapped_column(
        ForeignKey("task_sampling.id", ondelete="CASCADE"),
        nullable=False,
        comment="抽检任务ID",
    )
    sampling_task_room_id: Mapped[int] = mapped_column(
        ForeignKey("task_sampling_room.id", ondelete="CASCADE"),
        nullable=False,
        comment="抽检任务宿舍ID",
    )
    dorm_room_id: Mapped[int] = mapped_column(
        ForeignKey("dorm_room.id", ondelete="RESTRICT"),
        nullable=False,
        comment="宿舍ID",
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("app_user.id", ondelete="RESTRICT"),
        nullable=False,
        comment="执行人",
    )
    detect_mode: Mapped[str] = mapped_column(
        String(16),
        nullable=False,
        default="full",
        server_default=text("'full'"),
        comment="检测模式",
    )
    current_ssid: Mapped[str | None] = mapped_column(String(64), nullable=True)
    current_bssid: Mapped[str | None] = mapped_column(String(64), nullable=True)
    bssid_match: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    ipv4_addr: Mapped[str | None] = mapped_column(String(64), nullable=True)
    gateway_addr: Mapped[str | None] = mapped_column(String(64), nullable=True)
    dns_list: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    operator_name: Mapped[str | None] = mapped_column(String(64), nullable=True)
    channel_no: Mapped[int | None] = mapped_column(Integer, nullable=True)
    negotiated_rate_mbps: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)
    signal_strength_dbm: Mapped[int | None] = mapped_column(Integer, nullable=True)
    loss_rate_pct: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    intranet_ping_ms: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)
    internet_ping_ms: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)
    udp_jitter_ms: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)
    udp_loss_rate_pct: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    tcp_rtt_ms: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)
    down_speed_mbps: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)
    up_speed_mbps: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)
    interference_score: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)
    exception_auto: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default=text("false"),
    )
    exception_manual: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default=text("false"),
    )
    manual_exception_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    review_status: Mapped[int] = mapped_column(
        SmallInteger,
        nullable=False,
        default=0,
        server_default=text("0"),
    )
    reviewed_by: Mapped[int | None] = mapped_column(
        ForeignKey("app_user.id", ondelete="SET NULL"),
        nullable=True,
    )
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        CheckConstraint(
            "detect_mode IN ('full','single_item')",
            name="ck_sampling_record_mode",
        ),
        CheckConstraint("review_status IN (0,1,2)", name="ck_sampling_record_review"),
        Index(
            "idx_sampling_record_task_user",
            "sampling_task_id",
            "user_id",
            "created_at",
        ),
        Index("idx_sampling_record_room", "dorm_room_id", "created_at"),
    )
