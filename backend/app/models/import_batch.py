"""Import batch model aligned with docs SQL baseline."""

from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Integer, SmallInteger, String, Text, func, text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class ImportBatch(Base):
    """导入批次表。"""

    __tablename__ = "import_batch"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
        autoincrement=True,
        comment="Primary key",
    )
    batch_type: Mapped[str] = mapped_column(String(32), nullable=False, comment="批次类型")
    file_name: Mapped[str] = mapped_column(String(255), nullable=False, comment="文件名")
    file_storage_path: Mapped[str | None] = mapped_column(
        Text, nullable=True, comment="文件存储路径"
    )
    imported_by: Mapped[int] = mapped_column(
        ForeignKey("app_user.id", ondelete="RESTRICT"),
        nullable=False,
        comment="导入人",
    )
    total_rows: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default=text("0"),
        comment="总行数",
    )
    success_rows: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default=text("0"),
        comment="成功行数",
    )
    failed_rows: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default=text("0"),
        comment="失败行数",
    )
    status: Mapped[int] = mapped_column(
        SmallInteger,
        nullable=False,
        default=0,
        server_default=text("0"),
        comment="批次状态",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        comment="Record creation timestamp",
    )
    finished_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="完成时间",
    )

    __table_args__ = (
        CheckConstraint(
            "batch_type IN ('repair_total','repair_legacy','other')",
            name="ck_import_batch_type",
        ),
        CheckConstraint("status IN (0,1,2,3)", name="ck_import_batch_status"),
    )
