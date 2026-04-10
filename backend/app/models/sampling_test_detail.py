"""Sampling test detail model aligned with docs SQL baseline."""

from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, func, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class SamplingTestDetail(Base):
    """单项目检测明细表。"""

    __tablename__ = "sampling_test_detail"

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
    item_code: Mapped[str] = mapped_column(String(32), nullable=False, comment="项目编码")
    target_host: Mapped[str | None] = mapped_column(String(255), nullable=True, comment="目标主机")
    result_payload: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        server_default=text("'{}'::jsonb"),
        comment="结果载荷",
    )
    save_to_record: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default=text("true"),
        comment="是否回填主记录",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="Record creation timestamp",
    )
