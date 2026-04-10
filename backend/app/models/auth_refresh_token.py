"""Refresh token persistence model."""

from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class AuthRefreshToken(BaseModel):
    """Stores refresh token lifecycle for revoke and trace operations."""

    __tablename__ = "auth_refresh_token"

    user_id: Mapped[int] = mapped_column(
        ForeignKey("app_user.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="User id",
    )

    refresh_token: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
        comment="Refresh token",
    )

    device_id: Mapped[Optional[str]] = mapped_column(
        String(128),
        nullable=True,
        comment="Device identifier",
    )

    device_name: Mapped[Optional[str]] = mapped_column(
        String(128),
        nullable=True,
        comment="Device name",
    )

    platform_code: Mapped[Optional[str]] = mapped_column(
        String(32),
        nullable=True,
        comment="Platform code",
    )

    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
        comment="Refresh token expiration time",
    )

    revoked_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Revoke time",
    )
