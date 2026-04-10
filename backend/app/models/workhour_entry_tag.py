"""Workhour entry tag mapping model aligned with docs SQL baseline."""

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, UniqueConstraint, func, text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class WorkhourEntryTag(Base):
    """工时明细与标签关联表。"""

    __tablename__ = "workhour_entry_tag"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
        autoincrement=True,
        comment="Primary key",
    )
    workhour_entry_id: Mapped[int] = mapped_column(
        ForeignKey("workhour_entry.id", ondelete="CASCADE"),
        nullable=False,
        comment="工时明细ID",
    )
    workhour_tag_id: Mapped[int] = mapped_column(
        ForeignKey("workhour_tag.id", ondelete="RESTRICT"),
        nullable=False,
        comment="工时标签ID",
    )
    bonus_minutes: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default=text("0"),
        comment="标签加减工时",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        comment="Record creation timestamp",
    )

    __table_args__ = (
        UniqueConstraint(
            "workhour_entry_id",
            "workhour_tag_id",
            name="uq_workhour_entry_tag_entry_tag",
        ),
    )
