"""Business operation log model aligned with docs SQL baseline."""

from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class BizOperationLog(Base):
    """Unified operation audit log across business domains."""

    __tablename__ = "biz_operation_log"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
        autoincrement=True,
        comment="Primary key",
    )
    biz_type: Mapped[str] = mapped_column(String(32), nullable=False, comment="业务类型")
    biz_id: Mapped[int | None] = mapped_column(
        BigInteger, nullable=True, comment="业务ID"
    )
    operation_type: Mapped[str] = mapped_column(
        String(32), nullable=False, comment="操作类型"
    )
    operator_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("app_user.id", ondelete="SET NULL"),
        nullable=True,
        comment="操作人",
    )
    request_id: Mapped[str | None] = mapped_column(
        String(64), nullable=True, comment="请求链路ID"
    )
    payload_before: Mapped[dict | None] = mapped_column(
        JSONB, nullable=True, comment="变更前快照"
    )
    payload_after: Mapped[dict | None] = mapped_column(
        JSONB, nullable=True, comment="变更后快照"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="Record creation timestamp",
    )
