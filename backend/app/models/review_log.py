"""Review log model aligned with docs SQL baseline."""

from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, Index, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class ReviewLog(Base):
    """Review action history for business entities."""

    __tablename__ = "review_log"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
        autoincrement=True,
        comment="Primary key",
    )
    biz_type: Mapped[str] = mapped_column(String(32), nullable=False, comment="业务类型")
    biz_id: Mapped[int] = mapped_column(BigInteger, nullable=False, comment="业务ID")
    review_type: Mapped[str] = mapped_column(String(32), nullable=False, comment="审核类型")
    reviewer_id: Mapped[int] = mapped_column(
        ForeignKey("app_user.id", ondelete="RESTRICT"),
        nullable=False,
        comment="审核人",
    )
    action_code: Mapped[str] = mapped_column(String(32), nullable=False, comment="动作编码")
    review_note: Mapped[str | None] = mapped_column(Text, nullable=True, comment="审核备注")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="Record creation timestamp",
    )

    __table_args__ = (
        Index("idx_review_log_biz", "biz_type", "biz_id", "created_at"),
    )
