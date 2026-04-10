"""System config model aligned with docs SQL baseline."""

from typing import Optional

from sqlalchemy import Boolean, CheckConstraint, String, Text, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class SysConfig(BaseModel):
    """System config table for threshold and runtime business configs."""

    __tablename__ = "sys_config"

    config_group: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        comment="配置分组",
    )
    config_key: Mapped[str] = mapped_column(
        String(128),
        nullable=False,
        comment="配置键",
    )
    config_value: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        server_default=text("'{}'::jsonb"),
        comment="配置值 JSON",
    )
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="配置说明",
    )
    is_enabled: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default=text("true"),
        comment="是否启用",
    )

    __table_args__ = (
        UniqueConstraint("config_group", "config_key", name="uq_sys_config_group_key"),
        CheckConstraint("char_length(config_group) > 0", name="ck_sys_config_group_non_empty"),
        CheckConstraint("char_length(config_key) > 0", name="ck_sys_config_key_non_empty"),
    )
