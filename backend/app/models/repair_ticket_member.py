"""Repair ticket member model aligned with docs SQL baseline."""

from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Integer, String, UniqueConstraint, func, text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class RepairTicketMember(Base):
    """报修单参与人表。"""

    __tablename__ = "repair_ticket_member"

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
    user_id: Mapped[int] = mapped_column(
        ForeignKey("app_user.id", ondelete="RESTRICT"),
        nullable=False,
        comment="用户ID",
    )
    member_role: Mapped[str] = mapped_column(
        String(16),
        nullable=False,
        default="assist",
        server_default=text("'assist'"),
        comment="参与角色",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        comment="Record creation timestamp",
    )

    __table_args__ = (
        UniqueConstraint(
            "repair_ticket_id",
            "user_id",
            name="uq_repair_ticket_member_ticket_user",
        ),
        CheckConstraint(
            "member_role IN ('primary','assist')",
            name="ck_repair_ticket_member_role",
        ),
    )
