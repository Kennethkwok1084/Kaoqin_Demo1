"""Align docs baseline phase2 governance and workhour core tables

Revision ID: d5e6f7a8b9c0
Revises: c4d5e6f7a8b9
Create Date: 2026-04-09 23:30:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "d5e6f7a8b9c0"
down_revision: Union[str, None] = "c4d5e6f7a8b9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade database schema."""

    op.create_table(
        "workhour_rule",
        sa.Column("rule_code", sa.String(length=64), nullable=False, comment="规则编码"),
        sa.Column("rule_name", sa.String(length=128), nullable=False, comment="规则名称"),
        sa.Column("biz_type", sa.String(length=32), nullable=False, comment="业务类型"),
        sa.Column("formula_desc", sa.Text(), nullable=False, comment="公式说明"),
        sa.Column(
            "formula_json",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
            comment="公式结构化定义",
        ),
        sa.Column(
            "is_enabled",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("true"),
            comment="是否启用",
        ),
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False, comment="Primary key"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
            comment="Record creation timestamp",
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
            comment="Record last update timestamp",
        ),
        sa.CheckConstraint(
            "biz_type IN ('coop','inspection','sampling','repair')",
            name="ck_workhour_rule_biz",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("rule_code", name="uq_workhour_rule_code"),
    )
    op.create_index(op.f("ix_workhour_rule_id"), "workhour_rule", ["id"], unique=False)

    op.create_table(
        "workhour_tag",
        sa.Column("tag_code", sa.String(length=64), nullable=False, comment="标签编码"),
        sa.Column("tag_name", sa.String(length=128), nullable=False, comment="标签名称"),
        sa.Column("tag_type", sa.String(length=32), nullable=False, comment="标签类型"),
        sa.Column(
            "bonus_mode",
            sa.String(length=16),
            nullable=False,
            server_default=sa.text("'add'"),
            comment="加成模式",
        ),
        sa.Column(
            "bonus_value",
            sa.Numeric(precision=10, scale=2),
            nullable=False,
            server_default=sa.text("0"),
            comment="加成值",
        ),
        sa.Column(
            "is_enabled",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("true"),
            comment="是否启用",
        ),
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False, comment="Primary key"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
            comment="Record creation timestamp",
        ),
        sa.CheckConstraint(
            "tag_type IN ('good_review','burst_order','custom')",
            name="ck_workhour_tag_type",
        ),
        sa.CheckConstraint(
            "bonus_mode IN ('add','multiply')",
            name="ck_workhour_tag_bonus_mode",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tag_code", name="uq_workhour_tag_code"),
    )
    op.create_index(op.f("ix_workhour_tag_id"), "workhour_tag", ["id"], unique=False)

    op.create_table(
        "review_log",
        sa.Column("biz_type", sa.String(length=32), nullable=False, comment="业务类型"),
        sa.Column("biz_id", sa.BigInteger(), nullable=False, comment="业务ID"),
        sa.Column("review_type", sa.String(length=32), nullable=False, comment="审核类型"),
        sa.Column("reviewer_id", sa.Integer(), nullable=False, comment="审核人"),
        sa.Column("action_code", sa.String(length=32), nullable=False, comment="动作编码"),
        sa.Column("review_note", sa.Text(), nullable=True, comment="审核备注"),
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False, comment="Primary key"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
            comment="Record creation timestamp",
        ),
        sa.ForeignKeyConstraint(["reviewer_id"], ["app_user.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_review_log_id"), "review_log", ["id"], unique=False)
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_review_log_biz ON review_log(biz_type, biz_id, created_at DESC)"
    )

    op.create_table(
        "todo_item",
        sa.Column("todo_type", sa.String(length=32), nullable=False, comment="待办类型"),
        sa.Column("source_biz_type", sa.String(length=32), nullable=False, comment="来源业务类型"),
        sa.Column("source_biz_id", sa.BigInteger(), nullable=False, comment="来源业务ID"),
        sa.Column("title", sa.String(length=255), nullable=False, comment="标题"),
        sa.Column("content", sa.Text(), nullable=True, comment="内容"),
        sa.Column("assignee_user_id", sa.Integer(), nullable=True, comment="处理人"),
        sa.Column(
            "priority_level",
            sa.SmallInteger(),
            nullable=False,
            server_default=sa.text("2"),
            comment="优先级 1-4",
        ),
        sa.Column(
            "status",
            sa.SmallInteger(),
            nullable=False,
            server_default=sa.text("0"),
            comment="状态",
        ),
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False, comment="Primary key"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
            comment="Record creation timestamp",
        ),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True, comment="解决时间"),
        sa.CheckConstraint("priority_level IN (1,2,3,4)", name="ck_todo_item_priority"),
        sa.CheckConstraint("status IN (0,1,2)", name="ck_todo_item_status"),
        sa.ForeignKeyConstraint(["assignee_user_id"], ["app_user.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_todo_item_id"), "todo_item", ["id"], unique=False)
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_todo_item_assignee_status ON todo_item(assignee_user_id, status, created_at DESC)"
    )

    op.create_table(
        "biz_operation_log",
        sa.Column("biz_type", sa.String(length=32), nullable=False, comment="业务类型"),
        sa.Column("biz_id", sa.BigInteger(), nullable=True, comment="业务ID"),
        sa.Column("operation_type", sa.String(length=32), nullable=False, comment="操作类型"),
        sa.Column("operator_user_id", sa.Integer(), nullable=True, comment="操作人"),
        sa.Column("request_id", sa.String(length=64), nullable=True, comment="请求链路ID"),
        sa.Column(
            "payload_before",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
            comment="变更前快照",
        ),
        sa.Column(
            "payload_after",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
            comment="变更后快照",
        ),
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False, comment="Primary key"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
            comment="Record creation timestamp",
        ),
        sa.ForeignKeyConstraint(["operator_user_id"], ["app_user.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_biz_operation_log_id"), "biz_operation_log", ["id"], unique=False)


def downgrade() -> None:
    """Downgrade database schema."""
    op.drop_index(op.f("ix_biz_operation_log_id"), table_name="biz_operation_log")
    op.drop_table("biz_operation_log")

    op.execute("DROP INDEX IF EXISTS idx_todo_item_assignee_status")
    op.drop_index(op.f("ix_todo_item_id"), table_name="todo_item")
    op.drop_table("todo_item")

    op.execute("DROP INDEX IF EXISTS idx_review_log_biz")
    op.drop_index(op.f("ix_review_log_id"), table_name="review_log")
    op.drop_table("review_log")

    op.drop_index(op.f("ix_workhour_tag_id"), table_name="workhour_tag")
    op.drop_table("workhour_tag")

    op.drop_index(op.f("ix_workhour_rule_id"), table_name="workhour_rule")
    op.drop_table("workhour_rule")
