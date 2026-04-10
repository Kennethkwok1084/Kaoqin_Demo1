"""Align docs baseline phase3 coop tables

Revision ID: e6f7a8b9c0d1
Revises: d5e6f7a8b9c0
Create Date: 2026-04-10 00:10:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "e6f7a8b9c0d1"
down_revision: Union[str, None] = "d5e6f7a8b9c0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade database schema."""

    op.create_table(
        "task_coop",
        sa.Column("task_code", sa.String(length=64), nullable=False, comment="任务编码"),
        sa.Column("title", sa.String(length=255), nullable=False, comment="标题"),
        sa.Column("description", sa.Text(), nullable=True, comment="描述"),
        sa.Column("location_text", sa.String(length=255), nullable=True, comment="地点文本"),
        sa.Column("building_id", sa.Integer(), nullable=True, comment="楼栋ID"),
        sa.Column(
            "signup_need_review",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
            comment="报名是否需要审核",
        ),
        sa.Column(
            "sign_in_mode_mask",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("0"),
            comment="签到方式位掩码",
        ),
        sa.Column(
            "no_show_enabled",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("true"),
            comment="是否启用爽约",
        ),
        sa.Column(
            "status",
            sa.SmallInteger(),
            nullable=False,
            server_default=sa.text("0"),
            comment="状态",
        ),
        sa.Column("created_by", sa.Integer(), nullable=False, comment="创建人"),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True, comment="发布时间"),
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
        sa.CheckConstraint("status IN (0,1,2,3,4,5)", name="ck_task_coop_status"),
        sa.ForeignKeyConstraint(["building_id"], ["building.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["created_by"], ["app_user.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("task_code", name="uq_task_coop_code"),
    )
    op.create_index(op.f("ix_task_coop_id"), "task_coop", ["id"], unique=False)
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_task_coop_status_time ON task_coop(status, published_at DESC)"
    )

    op.create_table(
        "task_coop_slot",
        sa.Column("coop_task_id", sa.Integer(), nullable=False, comment="协助任务ID"),
        sa.Column("slot_title", sa.String(length=128), nullable=True, comment="时间段标题"),
        sa.Column("start_time", sa.DateTime(timezone=True), nullable=False, comment="开始时间"),
        sa.Column("end_time", sa.DateTime(timezone=True), nullable=False, comment="结束时间"),
        sa.Column(
            "signup_limit",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("1"),
            comment="报名上限",
        ),
        sa.Column(
            "sort_no",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("1"),
            comment="排序号",
        ),
        sa.Column(
            "status",
            sa.SmallInteger(),
            nullable=False,
            server_default=sa.text("1"),
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
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
            comment="Record last update timestamp",
        ),
        sa.CheckConstraint("end_time > start_time", name="ck_task_coop_slot_time"),
        sa.CheckConstraint("status IN (0,1)", name="ck_task_coop_slot_status"),
        sa.ForeignKeyConstraint(["coop_task_id"], ["task_coop.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_task_coop_slot_id"), "task_coop_slot", ["id"], unique=False)
    op.create_index("idx_task_coop_slot_task", "task_coop_slot", ["coop_task_id", "start_time"], unique=False)

    op.create_table(
        "task_coop_signup",
        sa.Column("coop_task_id", sa.Integer(), nullable=False, comment="协助任务ID"),
        sa.Column("coop_slot_id", sa.Integer(), nullable=False, comment="协助任务时间段ID"),
        sa.Column("user_id", sa.Integer(), nullable=False, comment="报名用户ID"),
        sa.Column(
            "signup_source",
            sa.String(length=16),
            nullable=False,
            server_default=sa.text("'self'"),
            comment="报名来源",
        ),
        sa.Column(
            "status",
            sa.SmallInteger(),
            nullable=False,
            server_default=sa.text("1"),
            comment="状态",
        ),
        sa.Column("reviewed_by", sa.Integer(), nullable=True, comment="审核人"),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True, comment="审核时间"),
        sa.Column("cancel_reason", sa.Text(), nullable=True, comment="取消原因"),
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
        sa.CheckConstraint("signup_source IN ('self','assign')", name="ck_task_coop_signup_source"),
        sa.CheckConstraint("status IN (0,1,2,3,4)", name="ck_task_coop_signup_status"),
        sa.ForeignKeyConstraint(["coop_task_id"], ["task_coop.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["coop_slot_id"], ["task_coop_slot.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["reviewed_by"], ["app_user.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["user_id"], ["app_user.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("coop_slot_id", "user_id", name="uq_task_coop_signup_slot_user"),
    )
    op.create_index(op.f("ix_task_coop_signup_id"), "task_coop_signup", ["id"], unique=False)
    op.create_index("idx_task_coop_signup_user", "task_coop_signup", ["user_id", "status"], unique=False)

    op.create_table(
        "task_coop_attendance",
        sa.Column("coop_signup_id", sa.Integer(), nullable=False, comment="协助任务报名ID"),
        sa.Column("sign_in_at", sa.DateTime(timezone=True), nullable=True, comment="签到时间"),
        sa.Column("sign_out_at", sa.DateTime(timezone=True), nullable=True, comment="签退时间"),
        sa.Column("sign_in_type", sa.String(length=16), nullable=True, comment="签到方式"),
        sa.Column("sign_out_type", sa.String(length=16), nullable=True, comment="签退方式"),
        sa.Column("sign_in_longitude", sa.Numeric(precision=10, scale=6), nullable=True, comment="签到经度"),
        sa.Column("sign_in_latitude", sa.Numeric(precision=10, scale=6), nullable=True, comment="签到纬度"),
        sa.Column(
            "sign_out_longitude",
            sa.Numeric(precision=10, scale=6),
            nullable=True,
            comment="签退经度",
        ),
        sa.Column("sign_out_latitude", sa.Numeric(precision=10, scale=6), nullable=True, comment="签退纬度"),
        sa.Column("qr_token", sa.String(length=128), nullable=True, comment="二维码令牌"),
        sa.Column("admin_confirmed_by", sa.Integer(), nullable=True, comment="管理员确认人"),
        sa.Column(
            "admin_confirmed_at",
            sa.DateTime(timezone=True),
            nullable=True,
            comment="管理员确认时间",
        ),
        sa.Column(
            "duration_minutes",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("0"),
            comment="时长(分钟)",
        ),
        sa.Column(
            "review_status",
            sa.SmallInteger(),
            nullable=False,
            server_default=sa.text("0"),
            comment="审核状态",
        ),
        sa.Column("remark", sa.Text(), nullable=True, comment="备注"),
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
            "sign_in_type IN ('gps','qr','manual','admin','hybrid') OR sign_in_type IS NULL",
            name="ck_task_coop_attendance_type",
        ),
        sa.CheckConstraint("review_status IN (0,1,2)", name="ck_task_coop_attendance_review"),
        sa.ForeignKeyConstraint(["admin_confirmed_by"], ["app_user.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["coop_signup_id"], ["task_coop_signup.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_task_coop_attendance_id"),
        "task_coop_attendance",
        ["id"],
        unique=False,
    )
    op.create_index(
        "idx_task_coop_attendance_signup",
        "task_coop_attendance",
        ["coop_signup_id"],
        unique=False,
    )


def downgrade() -> None:
    """Downgrade database schema."""

    op.drop_index("idx_task_coop_attendance_signup", table_name="task_coop_attendance")
    op.drop_index(op.f("ix_task_coop_attendance_id"), table_name="task_coop_attendance")
    op.drop_table("task_coop_attendance")

    op.drop_index("idx_task_coop_signup_user", table_name="task_coop_signup")
    op.drop_index(op.f("ix_task_coop_signup_id"), table_name="task_coop_signup")
    op.drop_table("task_coop_signup")

    op.drop_index("idx_task_coop_slot_task", table_name="task_coop_slot")
    op.drop_index(op.f("ix_task_coop_slot_id"), table_name="task_coop_slot")
    op.drop_table("task_coop_slot")

    op.execute("DROP INDEX IF EXISTS idx_task_coop_status_time")
    op.drop_index(op.f("ix_task_coop_id"), table_name="task_coop")
    op.drop_table("task_coop")
