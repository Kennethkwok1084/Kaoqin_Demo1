"""Align docs baseline phase5 sampling tables

Revision ID: 08b9c0d1e2f3
Revises: f7a8b9c0d1e2
Create Date: 2026-04-10 03:30:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "08b9c0d1e2f3"
down_revision: Union[str, None] = "f7a8b9c0d1e2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade database schema."""

    op.create_table(
        "task_sampling",
        sa.Column("task_code", sa.String(length=64), nullable=False, comment="任务编码"),
        sa.Column("title", sa.String(length=255), nullable=False, comment="标题"),
        sa.Column("description", sa.Text(), nullable=True, comment="描述"),
        sa.Column("building_id", sa.Integer(), nullable=False, comment="楼栋ID"),
        sa.Column("target_room_count", sa.Integer(), nullable=False, comment="目标宿舍数量"),
        sa.Column(
            "sample_strategy",
            sa.String(length=32),
            nullable=False,
            server_default=sa.text("'weighted_random'"),
            comment="抽样策略",
        ),
        sa.Column(
            "exclude_days",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("30"),
            comment="排除天数",
        ),
        sa.Column("assigned_by", sa.Integer(), nullable=False, comment="指派人"),
        sa.Column("planned_start_at", sa.DateTime(timezone=True), nullable=True, comment="计划开始时间"),
        sa.Column("planned_end_at", sa.DateTime(timezone=True), nullable=True, comment="计划结束时间"),
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
        sa.CheckConstraint(
            "sample_strategy IN ('weighted_random')",
            name="ck_task_sampling_strategy",
        ),
        sa.CheckConstraint("status IN (0,1,2,3,4,5)", name="ck_task_sampling_status"),
        sa.ForeignKeyConstraint(["assigned_by"], ["app_user.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["building_id"], ["building.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("task_code", name="uq_task_sampling_code"),
    )
    op.create_index(op.f("ix_task_sampling_id"), "task_sampling", ["id"], unique=False)

    op.create_table(
        "task_sampling_user",
        sa.Column("sampling_task_id", sa.Integer(), nullable=False, comment="抽检任务ID"),
        sa.Column("user_id", sa.Integer(), nullable=False, comment="用户ID"),
        sa.Column(
            "role_in_task",
            sa.String(length=16),
            nullable=False,
            server_default=sa.text("'executor'"),
            comment="任务角色",
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
            "role_in_task IN ('leader','executor')",
            name="ck_task_sampling_user_role",
        ),
        sa.ForeignKeyConstraint(["sampling_task_id"], ["task_sampling.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["app_user.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("sampling_task_id", "user_id", name="uq_task_sampling_user_task_user"),
    )
    op.create_index(op.f("ix_task_sampling_user_id"), "task_sampling_user", ["id"], unique=False)

    op.create_table(
        "task_sampling_room",
        sa.Column("sampling_task_id", sa.Integer(), nullable=False, comment="抽检任务ID"),
        sa.Column("dorm_room_id", sa.Integer(), nullable=False, comment="宿舍ID"),
        sa.Column(
            "generated_weight",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("0"),
            comment="生成权重",
        ),
        sa.Column(
            "is_completed",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
            comment="是否完成",
        ),
        sa.Column("completed_by", sa.Integer(), nullable=True, comment="完成人"),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True, comment="完成时间"),
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False, comment="Primary key"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
            comment="Record creation timestamp",
        ),
        sa.ForeignKeyConstraint(["completed_by"], ["app_user.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["dorm_room_id"], ["dorm_room.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["sampling_task_id"], ["task_sampling.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("sampling_task_id", "dorm_room_id", name="uq_task_sampling_room_task_room"),
    )
    op.create_index(op.f("ix_task_sampling_room_id"), "task_sampling_room", ["id"], unique=False)
    op.create_index(
        "idx_task_sampling_room_task",
        "task_sampling_room",
        ["sampling_task_id", "is_completed"],
        unique=False,
    )

    op.create_table(
        "sampling_record",
        sa.Column("sampling_task_id", sa.Integer(), nullable=False, comment="抽检任务ID"),
        sa.Column("sampling_task_room_id", sa.Integer(), nullable=False, comment="抽检任务宿舍ID"),
        sa.Column("dorm_room_id", sa.Integer(), nullable=False, comment="宿舍ID"),
        sa.Column("user_id", sa.Integer(), nullable=False, comment="执行人"),
        sa.Column(
            "detect_mode",
            sa.String(length=16),
            nullable=False,
            server_default=sa.text("'full'"),
            comment="检测模式",
        ),
        sa.Column("current_ssid", sa.String(length=64), nullable=True),
        sa.Column("current_bssid", sa.String(length=64), nullable=True),
        sa.Column("bssid_match", sa.Boolean(), nullable=True),
        sa.Column("ipv4_addr", sa.String(length=64), nullable=True),
        sa.Column("gateway_addr", sa.String(length=64), nullable=True),
        sa.Column("dns_list", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("operator_name", sa.String(length=64), nullable=True),
        sa.Column("channel_no", sa.Integer(), nullable=True),
        sa.Column("negotiated_rate_mbps", sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column("signal_strength_dbm", sa.Integer(), nullable=True),
        sa.Column("loss_rate_pct", sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column("intranet_ping_ms", sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column("internet_ping_ms", sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column("udp_jitter_ms", sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column("udp_loss_rate_pct", sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column("tcp_rtt_ms", sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column("down_speed_mbps", sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column("up_speed_mbps", sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column("interference_score", sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column(
            "exception_auto",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
        sa.Column(
            "exception_manual",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
        sa.Column("manual_exception_note", sa.Text(), nullable=True),
        sa.Column(
            "review_status",
            sa.SmallInteger(),
            nullable=False,
            server_default=sa.text("0"),
        ),
        sa.Column("reviewed_by", sa.Integer(), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
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
        sa.CheckConstraint("detect_mode IN ('full','single_item')", name="ck_sampling_record_mode"),
        sa.CheckConstraint("review_status IN (0,1,2)", name="ck_sampling_record_review"),
        sa.ForeignKeyConstraint(["dorm_room_id"], ["dorm_room.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["reviewed_by"], ["app_user.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["sampling_task_id"], ["task_sampling.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["sampling_task_room_id"], ["task_sampling_room.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["app_user.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_sampling_record_id"), "sampling_record", ["id"], unique=False)
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_sampling_record_task_user ON sampling_record(sampling_task_id, user_id, created_at DESC)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_sampling_record_room ON sampling_record(dorm_room_id, created_at DESC)"
    )

    op.create_table(
        "sampling_scan_detail",
        sa.Column("sampling_record_id", sa.Integer(), nullable=False, comment="抽检结果ID"),
        sa.Column("ssid", sa.String(length=128), nullable=True),
        sa.Column("bssid", sa.String(length=64), nullable=True),
        sa.Column("channel_no", sa.Integer(), nullable=True),
        sa.Column("signal_strength_dbm", sa.Integer(), nullable=True),
        sa.Column(
            "is_same_channel",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
        sa.Column(
            "is_adjacent_channel",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False, comment="Primary key"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
            comment="Record creation timestamp",
        ),
        sa.ForeignKeyConstraint(["sampling_record_id"], ["sampling_record.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_sampling_scan_detail_id"), "sampling_scan_detail", ["id"], unique=False)
    op.create_index(
        "idx_sampling_scan_detail_record",
        "sampling_scan_detail",
        ["sampling_record_id"],
        unique=False,
    )

    op.create_table(
        "sampling_test_detail",
        sa.Column("sampling_record_id", sa.Integer(), nullable=False, comment="抽检结果ID"),
        sa.Column("item_code", sa.String(length=32), nullable=False, comment="项目编码"),
        sa.Column("target_host", sa.String(length=255), nullable=True, comment="目标主机"),
        sa.Column(
            "result_payload",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
            comment="结果载荷",
        ),
        sa.Column(
            "save_to_record",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("true"),
            comment="是否回填主记录",
        ),
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False, comment="Primary key"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
            comment="Record creation timestamp",
        ),
        sa.ForeignKeyConstraint(["sampling_record_id"], ["sampling_record.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_sampling_test_detail_id"), "sampling_test_detail", ["id"], unique=False)


def downgrade() -> None:
    """Downgrade database schema."""

    op.drop_index(op.f("ix_sampling_test_detail_id"), table_name="sampling_test_detail")
    op.drop_table("sampling_test_detail")

    op.drop_index("idx_sampling_scan_detail_record", table_name="sampling_scan_detail")
    op.drop_index(op.f("ix_sampling_scan_detail_id"), table_name="sampling_scan_detail")
    op.drop_table("sampling_scan_detail")

    op.execute("DROP INDEX IF EXISTS idx_sampling_record_room")
    op.execute("DROP INDEX IF EXISTS idx_sampling_record_task_user")
    op.drop_index(op.f("ix_sampling_record_id"), table_name="sampling_record")
    op.drop_table("sampling_record")

    op.drop_index("idx_task_sampling_room_task", table_name="task_sampling_room")
    op.drop_index(op.f("ix_task_sampling_room_id"), table_name="task_sampling_room")
    op.drop_table("task_sampling_room")

    op.drop_index(op.f("ix_task_sampling_user_id"), table_name="task_sampling_user")
    op.drop_table("task_sampling_user")

    op.drop_index(op.f("ix_task_sampling_id"), table_name="task_sampling")
    op.drop_table("task_sampling")
