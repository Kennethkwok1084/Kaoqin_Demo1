"""Unified media file model aligned with docs SQL baseline."""

from datetime import datetime
from typing import Optional

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class MediaFile(Base):
    """Store image/video/audio and OCR source metadata in one table."""

    __tablename__ = "media_file"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
        comment="Primary key",
    )
    biz_type: Mapped[str] = mapped_column(String(32), nullable=False, comment="业务类型")
    biz_id: Mapped[int] = mapped_column(BigInteger, nullable=False, comment="业务主键ID")
    file_type: Mapped[str] = mapped_column(String(16), nullable=False, comment="文件类型")
    storage_path: Mapped[str] = mapped_column(Text, nullable=False, comment="存储路径")
    file_name: Mapped[str] = mapped_column(String(255), nullable=False, comment="原始文件名")
    content_type: Mapped[Optional[str]] = mapped_column(
        String(128), nullable=True, comment="MIME类型"
    )
    file_size: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
        default=0,
        comment="文件大小(字节)",
    )
    sha256_hex: Mapped[Optional[str]] = mapped_column(
        String(128), nullable=True, comment="SHA256摘要"
    )
    watermark_payload: Mapped[Optional[dict]] = mapped_column(
        JSONB, nullable=True, comment="水印元数据"
    )
    uploaded_by: Mapped[int] = mapped_column(
        ForeignKey("app_user.id", ondelete="RESTRICT"),
        nullable=False,
        comment="上传人",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="Record creation timestamp",
    )

    __table_args__ = (
        CheckConstraint(
            "file_type IN ('image','video','audio','ocr_source','other')",
            name="ck_media_file_type",
        ),
        Index("idx_media_file_biz", "biz_type", "biz_id"),
    )
