"""Workhour rule model aligned with docs SQL baseline."""

from sqlalchemy import Boolean, CheckConstraint, String, Text, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class WorkhourRule(BaseModel):
    """Rule configuration for workhour calculation by business type."""

    __tablename__ = "workhour_rule"

    rule_code: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        unique=True,
        comment="规则编码",
    )
    rule_name: Mapped[str] = mapped_column(
        String(128),
        nullable=False,
        comment="规则名称",
    )
    biz_type: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        comment="业务类型",
    )
    formula_desc: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="公式说明",
    )
    formula_json: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        server_default=text("'{}'::jsonb"),
        comment="公式结构化定义",
    )
    is_enabled: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default=text("true"),
        comment="是否启用",
    )

    __table_args__ = (
        CheckConstraint(
            "biz_type IN ('coop','inspection','sampling','repair')",
            name="ck_workhour_rule_biz",
        ),
    )
