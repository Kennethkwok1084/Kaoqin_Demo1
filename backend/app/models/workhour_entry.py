"""Workhour entry model aligned with docs SQL baseline."""

from datetime import datetime

from sqlalchemy import BigInteger, CheckConstraint, DateTime, ForeignKey, Index, Integer, SmallInteger, String, Text, text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class WorkhourEntry(BaseModel):
    """工时明细表。"""

    __tablename__ = "workhour_entry"

    biz_type: Mapped[str] = mapped_column(String(32), nullable=False, comment="业务类型")
    biz_id: Mapped[int] = mapped_column(BigInteger, nullable=False, comment="业务ID")
    user_id: Mapped[int] = mapped_column(
        ForeignKey("app_user.id", ondelete="RESTRICT"),
        nullable=False,
        comment="用户ID",
    )
    source_rule_id: Mapped[int | None] = mapped_column(
        ForeignKey("workhour_rule.id", ondelete="SET NULL"),
        nullable=True,
        comment="来源规则ID",
    )
    base_minutes: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default=text("0"),
        comment="基础工时(分钟)",
    )
    final_minutes: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default=text("0"),
        comment="最终工时(分钟)",
    )
    review_status: Mapped[int] = mapped_column(
        SmallInteger,
        nullable=False,
        default=0,
        server_default=text("0"),
        comment="审核状态",
    )
    reviewed_by: Mapped[int | None] = mapped_column(
        ForeignKey("app_user.id", ondelete="SET NULL"),
        nullable=True,
        comment="审核人",
    )
    reviewed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="审核时间",
    )
    review_note: Mapped[str | None] = mapped_column(Text, nullable=True, comment="审核备注")

    __table_args__ = (
        CheckConstraint(
            "biz_type IN ('coop','inspection','sampling','repair')",
            name="ck_workhour_entry_biz",
        ),
        CheckConstraint("review_status IN (0,1,2)", name="ck_workhour_entry_review"),
        Index("idx_workhour_entry_user_time", "user_id", "created_at"),
        Index("idx_workhour_entry_biz", "biz_type", "biz_id"),
    )
