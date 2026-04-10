"""Align docs baseline phase6 repair and workhour entry tables

Revision ID: 19c0d1e2f304
Revises: 08b9c0d1e2f3
Create Date: 2026-04-10 05:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "19c0d1e2f304"
down_revision: Union[str, None] = "08b9c0d1e2f3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade database schema."""

    op.create_table(
        "repair_ticket",
        sa.Column("repair_no", sa.String(length=64), nullable=True, comment="报修编号"),
        sa.Column("ticket_source", sa.String(length=16), nullable=False, comment="报修来源"),
        sa.Column("title", sa.String(length=255), nullable=True, comment="标题"),
        sa.Column("report_user_name", sa.String(length=64), nullable=True, comment="报修人"),
        sa.Column("report_phone", sa.String(length=32), nullable=True, comment="报修电话"),
        sa.Column("building_id", sa.Integer(), nullable=True, comment="楼栋ID"),
        sa.Column("dorm_room_id", sa.Integer(), nullable=True, comment="宿舍ID"),
        sa.Column("issue_content", sa.Text(), nullable=True, comment="问题描述"),
        sa.Column("issue_category", sa.String(length=64), nullable=True, comment="问题分类"),
        sa.Column("solution_desc", sa.Text(), nullable=True, comment="处理方案"),
        sa.Column(
            "solve_status",
            sa.SmallInteger(),
            nullable=False,
            server_default=sa.text("0"),
            comment="处理状态",
        ),
        sa.Column("source_screenshot_id", sa.Integer(), nullable=True, comment="来源截图ID"),
        sa.Column("doorplate_image_id", sa.Integer(), nullable=True, comment="门牌图片ID"),
        sa.Column(
            "ocr_payload",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
            comment="OCR数据",
        ),
        sa.Column(
            "match_status",
            sa.SmallInteger(),
            nullable=False,
            server_default=sa.text("0"),
            comment="匹配状态",
        ),
        sa.Column("matched_import_row_id", sa.Integer(), nullable=True, comment="匹配导入行ID"),
        sa.Column("created_by", sa.Integer(), nullable=False, comment="创建人"),
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
        sa.CheckConstraint("ticket_source IN ('online','offline')", name="ck_repair_ticket_source"),
        sa.CheckConstraint("solve_status IN (0,1,2)", name="ck_repair_ticket_solve_status"),
        sa.CheckConstraint("match_status IN (0,1,2,3)", name="ck_repair_ticket_match_status"),
        sa.ForeignKeyConstraint(["building_id"], ["building.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["created_by"], ["app_user.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["doorplate_image_id"], ["media_file.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["dorm_room_id"], ["dorm_room.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["source_screenshot_id"], ["media_file.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_repair_ticket_id"), "repair_ticket", ["id"], unique=False)
    op.create_index("idx_repair_ticket_no", "repair_ticket", ["repair_no"], unique=False)
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_repair_ticket_source_status ON repair_ticket(ticket_source, match_status, created_at DESC)"
    )

    op.create_table(
        "repair_ticket_member",
        sa.Column("repair_ticket_id", sa.Integer(), nullable=False, comment="报修单ID"),
        sa.Column("user_id", sa.Integer(), nullable=False, comment="用户ID"),
        sa.Column(
            "member_role",
            sa.String(length=16),
            nullable=False,
            server_default=sa.text("'assist'"),
            comment="参与角色",
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
            "member_role IN ('primary','assist')",
            name="ck_repair_ticket_member_role",
        ),
        sa.ForeignKeyConstraint(["repair_ticket_id"], ["repair_ticket.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["app_user.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("repair_ticket_id", "user_id", name="uq_repair_ticket_member_ticket_user"),
    )
    op.create_index(op.f("ix_repair_ticket_member_id"), "repair_ticket_member", ["id"], unique=False)

    op.create_table(
        "import_batch",
        sa.Column("batch_type", sa.String(length=32), nullable=False, comment="批次类型"),
        sa.Column("file_name", sa.String(length=255), nullable=False, comment="文件名"),
        sa.Column("file_storage_path", sa.Text(), nullable=True, comment="文件存储路径"),
        sa.Column("imported_by", sa.Integer(), nullable=False, comment="导入人"),
        sa.Column(
            "total_rows",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("0"),
            comment="总行数",
        ),
        sa.Column(
            "success_rows",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("0"),
            comment="成功行数",
        ),
        sa.Column(
            "failed_rows",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("0"),
            comment="失败行数",
        ),
        sa.Column(
            "status",
            sa.SmallInteger(),
            nullable=False,
            server_default=sa.text("0"),
            comment="批次状态",
        ),
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False, comment="Primary key"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
            comment="Record creation timestamp",
        ),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True, comment="完成时间"),
        sa.CheckConstraint(
            "batch_type IN ('repair_total','repair_legacy','other')",
            name="ck_import_batch_type",
        ),
        sa.CheckConstraint("status IN (0,1,2,3)", name="ck_import_batch_status"),
        sa.ForeignKeyConstraint(["imported_by"], ["app_user.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_import_batch_id"), "import_batch", ["id"], unique=False)

    op.create_table(
        "import_repair_row",
        sa.Column("import_batch_id", sa.Integer(), nullable=False, comment="导入批次ID"),
        sa.Column("repair_no", sa.String(length=64), nullable=True, comment="报修编号"),
        sa.Column("report_user_name", sa.String(length=64), nullable=True, comment="报修人"),
        sa.Column("report_phone", sa.String(length=32), nullable=True, comment="联系电话"),
        sa.Column("building_name", sa.String(length=128), nullable=True, comment="楼栋名"),
        sa.Column("room_no", sa.String(length=32), nullable=True, comment="房间号"),
        sa.Column("issue_content", sa.Text(), nullable=True, comment="问题描述"),
        sa.Column(
            "raw_payload",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
            comment="原始载荷",
        ),
        sa.Column("matched_ticket_id", sa.Integer(), nullable=True, comment="匹配报修单ID"),
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False, comment="Primary key"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
            comment="Record creation timestamp",
        ),
        sa.ForeignKeyConstraint(["import_batch_id"], ["import_batch.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["matched_ticket_id"], ["repair_ticket.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_import_repair_row_id"), "import_repair_row", ["id"], unique=False)
    op.create_index("idx_import_repair_row_no", "import_repair_row", ["repair_no"], unique=False)
    op.create_index(
        "idx_import_repair_row_match",
        "import_repair_row",
        ["matched_ticket_id"],
        unique=False,
    )

    op.create_table(
        "repair_match_application",
        sa.Column("repair_ticket_id", sa.Integer(), nullable=False, comment="报修单ID"),
        sa.Column("import_repair_row_id", sa.Integer(), nullable=False, comment="导入明细ID"),
        sa.Column("applied_by", sa.Integer(), nullable=False, comment="申请人"),
        sa.Column("apply_note", sa.Text(), nullable=True, comment="申请备注"),
        sa.Column(
            "status",
            sa.SmallInteger(),
            nullable=False,
            server_default=sa.text("0"),
            comment="状态",
        ),
        sa.Column("reviewed_by", sa.Integer(), nullable=True, comment="审核人"),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True, comment="审核时间"),
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False, comment="Primary key"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
            comment="Record creation timestamp",
        ),
        sa.CheckConstraint("status IN (0,1,2)", name="ck_repair_match_application_status"),
        sa.ForeignKeyConstraint(["applied_by"], ["app_user.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["import_repair_row_id"], ["import_repair_row.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["repair_ticket_id"], ["repair_ticket.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["reviewed_by"], ["app_user.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("repair_ticket_id", name="uq_repair_match_application_ticket"),
    )
    op.create_index(op.f("ix_repair_match_application_id"), "repair_match_application", ["id"], unique=False)

    op.create_table(
        "workhour_entry",
        sa.Column("biz_type", sa.String(length=32), nullable=False, comment="业务类型"),
        sa.Column("biz_id", sa.BigInteger(), nullable=False, comment="业务ID"),
        sa.Column("user_id", sa.Integer(), nullable=False, comment="用户ID"),
        sa.Column("source_rule_id", sa.Integer(), nullable=True, comment="来源规则ID"),
        sa.Column(
            "base_minutes",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("0"),
            comment="基础工时(分钟)",
        ),
        sa.Column(
            "final_minutes",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("0"),
            comment="最终工时(分钟)",
        ),
        sa.Column(
            "review_status",
            sa.SmallInteger(),
            nullable=False,
            server_default=sa.text("0"),
            comment="审核状态",
        ),
        sa.Column("reviewed_by", sa.Integer(), nullable=True, comment="审核人"),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True, comment="审核时间"),
        sa.Column("review_note", sa.Text(), nullable=True, comment="审核备注"),
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
            name="ck_workhour_entry_biz",
        ),
        sa.CheckConstraint("review_status IN (0,1,2)", name="ck_workhour_entry_review"),
        sa.ForeignKeyConstraint(["reviewed_by"], ["app_user.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["source_rule_id"], ["workhour_rule.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["user_id"], ["app_user.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_workhour_entry_id"), "workhour_entry", ["id"], unique=False)
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_workhour_entry_user_time ON workhour_entry(user_id, created_at DESC)"
    )
    op.create_index("idx_workhour_entry_biz", "workhour_entry", ["biz_type", "biz_id"], unique=False)

    op.create_table(
        "workhour_entry_tag",
        sa.Column("workhour_entry_id", sa.Integer(), nullable=False, comment="工时明细ID"),
        sa.Column("workhour_tag_id", sa.Integer(), nullable=False, comment="工时标签ID"),
        sa.Column(
            "bonus_minutes",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("0"),
            comment="标签加减工时",
        ),
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False, comment="Primary key"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
            comment="Record creation timestamp",
        ),
        sa.ForeignKeyConstraint(["workhour_entry_id"], ["workhour_entry.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["workhour_tag_id"], ["workhour_tag.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("workhour_entry_id", "workhour_tag_id", name="uq_workhour_entry_tag_entry_tag"),
    )
    op.create_index(op.f("ix_workhour_entry_tag_id"), "workhour_entry_tag", ["id"], unique=False)


def downgrade() -> None:
    """Downgrade database schema."""

    op.drop_index(op.f("ix_workhour_entry_tag_id"), table_name="workhour_entry_tag")
    op.drop_table("workhour_entry_tag")

    op.drop_index("idx_workhour_entry_biz", table_name="workhour_entry")
    op.execute("DROP INDEX IF EXISTS idx_workhour_entry_user_time")
    op.drop_index(op.f("ix_workhour_entry_id"), table_name="workhour_entry")
    op.drop_table("workhour_entry")

    op.drop_index(op.f("ix_repair_match_application_id"), table_name="repair_match_application")
    op.drop_table("repair_match_application")

    op.drop_index("idx_import_repair_row_match", table_name="import_repair_row")
    op.drop_index("idx_import_repair_row_no", table_name="import_repair_row")
    op.drop_index(op.f("ix_import_repair_row_id"), table_name="import_repair_row")
    op.drop_table("import_repair_row")

    op.drop_index(op.f("ix_import_batch_id"), table_name="import_batch")
    op.drop_table("import_batch")

    op.drop_index(op.f("ix_repair_ticket_member_id"), table_name="repair_ticket_member")
    op.drop_table("repair_ticket_member")

    op.execute("DROP INDEX IF EXISTS idx_repair_ticket_source_status")
    op.drop_index("idx_repair_ticket_no", table_name="repair_ticket")
    op.drop_index(op.f("ix_repair_ticket_id"), table_name="repair_ticket")
    op.drop_table("repair_ticket")
