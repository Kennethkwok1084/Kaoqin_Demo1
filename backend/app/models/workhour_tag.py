"""Workhour tag model aligned with docs SQL baseline."""

from datetime import datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    Integer,
    Numeric,
    String,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class WorkhourTag(Base):
    """Tag-based modifiers for workhour entries."""

    __tablename__ = "workhour_tag"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
        autoincrement=True,
        comment="Primary key",
    )
    tag_code: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        unique=True,
        comment="标签编码",
    )
    tag_name: Mapped[str] = mapped_column(
        String(128),
        nullable=False,
        comment="标签名称",
    )
    tag_type: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        comment="标签类型",
    )
    bonus_mode: Mapped[str] = mapped_column(
        String(16),
        nullable=False,
        default="add",
        server_default=text("'add'"),
        comment="加成模式",
    )
    bonus_value: Mapped[float] = mapped_column(
        Numeric(10, 2),
        nullable=False,
        default=0,
        server_default=text("0"),
        comment="加成值",
    )
    is_enabled: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default=text("true"),
        comment="是否启用",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="Record creation timestamp",
    )

    __table_args__ = (
        CheckConstraint(
            "tag_type IN ('good_review','burst_order','custom')",
            name="ck_workhour_tag_type",
        ),
        CheckConstraint(
            "bonus_mode IN ('add','multiply')",
            name="ck_workhour_tag_bonus_mode",
        ),
    )
