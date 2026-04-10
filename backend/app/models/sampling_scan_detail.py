"""Sampling scan detail model aligned with docs SQL baseline."""

from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Integer, String, func, text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class SamplingScanDetail(Base):
    """周边SSID/BSSID扫描明细表。"""

    __tablename__ = "sampling_scan_detail"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
        autoincrement=True,
        comment="Primary key",
    )
    sampling_record_id: Mapped[int] = mapped_column(
        ForeignKey("sampling_record.id", ondelete="CASCADE"),
        nullable=False,
        comment="抽检结果ID",
    )
    ssid: Mapped[str | None] = mapped_column(String(128), nullable=True)
    bssid: Mapped[str | None] = mapped_column(String(64), nullable=True)
    channel_no: Mapped[int | None] = mapped_column(Integer, nullable=True)
    signal_strength_dbm: Mapped[int | None] = mapped_column(Integer, nullable=True)
    is_same_channel: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default=text("false"),
    )
    is_adjacent_channel: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default=text("false"),
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="Record creation timestamp",
    )

    __table_args__ = (
        Index("idx_sampling_scan_detail_record", "sampling_record_id"),
    )
