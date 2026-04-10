"""Application user model aligned with docs SQL baseline."""

import enum
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import CheckConstraint, DateTime, SmallInteger, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.user_profile import UserProfile


class AppUserRole(enum.Enum):
    """Supported app user roles."""

    ADMIN = "admin"
    USER = "user"


class AppUserStatus(enum.IntEnum):
    """Status values aligned with docs SQL baseline."""

    DISABLED = 0
    ENABLED = 1
    LOCKED = 2


class AppUser(BaseModel):
    """Dual-write user table for staged migration from members."""

    __tablename__ = "app_user"

    student_no: Mapped[str] = mapped_column(
        String(32), nullable=False, unique=True, index=True, comment="学号/工号"
    )
    password_hash: Mapped[str] = mapped_column(
        String(255), nullable=False, comment="密码哈希"
    )
    real_name: Mapped[str] = mapped_column(String(64), nullable=False, comment="真实姓名")
    role_code: Mapped[str] = mapped_column(
        String(16), nullable=False, default=AppUserRole.USER.value, comment="角色编码"
    )
    phone: Mapped[Optional[str]] = mapped_column(
        String(32), nullable=True, comment="手机号"
    )
    email: Mapped[Optional[str]] = mapped_column(
        String(128), nullable=True, comment="邮箱"
    )
    avatar_url: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="头像地址"
    )
    status: Mapped[int] = mapped_column(
        SmallInteger,
        nullable=False,
        default=int(AppUserStatus.ENABLED),
        comment="0禁用 1启用 2锁定",
    )
    last_login_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True, comment="最近登录时间"
    )
    remark: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="备注")

    profile: Mapped[Optional["UserProfile"]] = relationship(
        "UserProfile",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    __table_args__ = (
        CheckConstraint("role_code IN ('admin','user')", name="ck_app_user_role_code"),
        CheckConstraint("status IN (0,1,2)", name="ck_app_user_status"),
    )

    def __repr__(self) -> str:
        """Readable model representation for logs."""
        return (
            f"<AppUser(id={self.id}, student_no='{self.student_no}', "
            f"role_code='{self.role_code}')>"
        )
