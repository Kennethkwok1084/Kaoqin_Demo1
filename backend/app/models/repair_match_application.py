"""Repair match application model aligned with docs SQL baseline."""

from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Integer, SmallInteger, Text, UniqueConstraint, func, text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class RepairMatchApplication(Base):
    """用户提交的报修匹配申请。"""

    __tablename__ = "repair_match_application"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
        autoincrement=True,
        comment="Primary key",
    )
    repair_ticket_id: Mapped[int] = mapped_column(
        ForeignKey("repair_ticket.id", ondelete="CASCADE"),
        nullable=False,
        comment="报修单ID",
    )
    import_repair_row_id: Mapped[int] = mapped_column(
        ForeignKey("import_repair_row.id", ondelete="CASCADE"),
        nullable=False,
        comment="导入明细ID",
    )
    applied_by: Mapped[int] = mapped_column(
        ForeignKey("app_user.id", ondelete="RESTRICT"),
        nullable=False,
        comment="申请人",
    )
    apply_note: Mapped[str | None] = mapped_column(Text, nullable=True, comment="申请备注")
    status: Mapped[int] = mapped_column(
        SmallInteger,
        nullable=False,
        default=0,
        server_default=text("0"),
        comment="状态",
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
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        comment="Record creation timestamp",
    )

    __table_args__ = (
        UniqueConstraint("repair_ticket_id", name="uq_repair_match_application_ticket"),
        CheckConstraint(
            "status IN (0,1,2)",
            name="ck_repair_match_application_status",
        ),
    )
