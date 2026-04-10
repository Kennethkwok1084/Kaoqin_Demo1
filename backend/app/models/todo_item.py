"""Todo item model aligned with docs SQL baseline."""

from datetime import datetime

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    SmallInteger,
    String,
    Text,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class TodoItem(Base):
    """Admin todo pool for pending review and exception workflows."""

    __tablename__ = "todo_item"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
        autoincrement=True,
        comment="Primary key",
    )
    todo_type: Mapped[str] = mapped_column(String(32), nullable=False, comment="待办类型")
    source_biz_type: Mapped[str] = mapped_column(
        String(32), nullable=False, comment="来源业务类型"
    )
    source_biz_id: Mapped[int] = mapped_column(
        BigInteger, nullable=False, comment="来源业务ID"
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False, comment="标题")
    content: Mapped[str | None] = mapped_column(Text, nullable=True, comment="内容")
    assignee_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("app_user.id", ondelete="SET NULL"),
        nullable=True,
        comment="处理人",
    )
    priority_level: Mapped[int] = mapped_column(
        SmallInteger,
        nullable=False,
        default=2,
        server_default=text("2"),
        comment="优先级 1-4",
    )
    status: Mapped[int] = mapped_column(
        SmallInteger,
        nullable=False,
        default=0,
        server_default=text("0"),
        comment="状态 0待处理 1处理中 2已完成",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="Record creation timestamp",
    )
    resolved_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="解决时间",
    )

    __table_args__ = (
        CheckConstraint("priority_level IN (1,2,3,4)", name="ck_todo_item_priority"),
        CheckConstraint("status IN (0,1,2)", name="ck_todo_item_status"),
        Index("idx_todo_item_assignee_status", "assignee_user_id", "status", "created_at"),
    )
