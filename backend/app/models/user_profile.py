"""User profile extension model aligned with docs SQL baseline."""

from typing import TYPE_CHECKING, Optional

from sqlalchemy import CheckConstraint, ForeignKey, Integer, SmallInteger, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.app_user import AppUser


class UserProfile(Base, TimestampMixin):
    """Extension profile table for app_user."""

    __tablename__ = "user_profile"

    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("app_user.id", ondelete="CASCADE"),
        primary_key=True,
        comment="用户ID",
    )
    nickname: Mapped[Optional[str]] = mapped_column(
        String(64), nullable=True, comment="昵称"
    )
    gender: Mapped[Optional[int]] = mapped_column(
        SmallInteger, nullable=True, comment="性别 0未知 1男 2女"
    )
    department_name: Mapped[Optional[str]] = mapped_column(
        String(128), nullable=True, comment="部门名称"
    )
    grade_name: Mapped[Optional[str]] = mapped_column(
        String(64), nullable=True, comment="年级"
    )
    class_name: Mapped[Optional[str]] = mapped_column(
        String(64), nullable=True, comment="班级"
    )
    major_name: Mapped[Optional[str]] = mapped_column(
        String(128), nullable=True, comment="专业"
    )
    id_card_mask: Mapped[Optional[str]] = mapped_column(
        String(32), nullable=True, comment="脱敏身份证号"
    )
    emergency_contact: Mapped[Optional[str]] = mapped_column(
        String(64), nullable=True, comment="紧急联系人"
    )
    emergency_phone: Mapped[Optional[str]] = mapped_column(
        String(32), nullable=True, comment="紧急联系电话"
    )

    user: Mapped["AppUser"] = relationship("AppUser", back_populates="profile")

    __table_args__ = (
        CheckConstraint(
            "gender IN (0,1,2) OR gender IS NULL", name="ck_user_profile_gender"
        ),
    )

    def __repr__(self) -> str:
        """Readable model representation for logs."""
        return f"<UserProfile(user_id={self.user_id})>"
