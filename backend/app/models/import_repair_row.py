"""Import repair row model aligned with docs SQL baseline."""

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, Text, func, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class ImportRepairRow(Base):
    """报修总表导入明细。"""

    __tablename__ = "import_repair_row"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
        autoincrement=True,
        comment="Primary key",
    )
    import_batch_id: Mapped[int] = mapped_column(
        ForeignKey("import_batch.id", ondelete="CASCADE"),
        nullable=False,
        comment="导入批次ID",
    )
    repair_no: Mapped[str | None] = mapped_column(String(64), nullable=True, comment="报修编号")
    report_user_name: Mapped[str | None] = mapped_column(
        String(64), nullable=True, comment="报修人"
    )
    report_phone: Mapped[str | None] = mapped_column(
        String(32), nullable=True, comment="联系电话"
    )
    building_name: Mapped[str | None] = mapped_column(
        String(128), nullable=True, comment="楼栋名"
    )
    room_no: Mapped[str | None] = mapped_column(String(32), nullable=True, comment="房间号")
    issue_content: Mapped[str | None] = mapped_column(Text, nullable=True, comment="问题描述")
    raw_payload: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        server_default=text("'{}'::jsonb"),
        comment="原始载荷",
    )
    matched_ticket_id: Mapped[int | None] = mapped_column(
        ForeignKey("repair_ticket.id", ondelete="SET NULL"),
        nullable=True,
        comment="匹配报修单ID",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        comment="Record creation timestamp",
    )

    __table_args__ = (
        Index("idx_import_repair_row_no", "repair_no"),
        Index("idx_import_repair_row_match", "matched_ticket_id"),
    )
