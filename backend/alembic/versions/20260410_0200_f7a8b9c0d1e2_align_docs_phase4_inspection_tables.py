"""Align docs baseline phase4 inspection tables

Revision ID: f7a8b9c0d1e2
Revises: e6f7a8b9c0d1
Create Date: 2026-04-10 02:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "f7a8b9c0d1e2"
down_revision: Union[str, None] = "e6f7a8b9c0d1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade database schema."""

    op.create_table(
        "task_inspection",
        sa.Column("task_code", sa.String(length=64), nullable=False, comment="任务编码"),
        sa.Column("title", sa.String(length=255), nullable=False, comment="标题"),
        sa.Column("description", sa.Text(), nullable=True, comment="描述"),
        sa.Column("building_id", sa.Integer(), nullable=True, comment="楼栋ID"),
        sa.Column("planned_start_at", sa.DateTime(timezone=True), nullable=True, comment="计划开始时间"),
        sa.Column("planned_end_at", sa.DateTime(timezone=True), nullable=True, comment="计划结束时间"),
        sa.Column("assigned_by", sa.Integer(), nullable=False, comment="指派人"),
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
        sa.CheckConstraint("status IN (0,1,2,3,4,5)", name="ck_task_inspection_status"),
        sa.ForeignKeyConstraint(["assigned_by"], ["app_user.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["building_id"], ["building.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("task_code", name="uq_task_inspection_code"),
    )
    op.create_index(op.f("ix_task_inspection_id"), "task_inspection", ["id"], unique=False)

    op.create_table(
        "task_inspection_user",
        sa.Column("inspection_task_id", sa.Integer(), nullable=False, comment="巡检任务ID"),
        sa.Column("user_id", sa.Integer(), nullable=False, comment="用户ID"),
        sa.Column(
            "role_in_task",
            sa.String(length=16),
            nullable=False,
            server_default=sa.text("'executor'"),
            comment="任务角色",
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
        sa.CheckConstraint(
            "role_in_task IN ('leader','executor')",
            name="ck_task_inspection_user_role",
        ),
        sa.CheckConstraint("status IN (0,1)", name="ck_task_inspection_user_status"),
        sa.ForeignKeyConstraint(["inspection_task_id"], ["task_inspection.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["app_user.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("inspection_task_id", "user_id", name="uq_task_inspection_user_task_user"),
    )
    op.create_index(op.f("ix_task_inspection_user_id"), "task_inspection_user", ["id"], unique=False)

    op.create_table(
        "task_inspection_point",
        sa.Column("inspection_task_id", sa.Integer(), nullable=False, comment="巡检任务ID"),
        sa.Column("cabinet_name", sa.String(length=128), nullable=False, comment="机柜名称"),
        sa.Column("cabinet_location", sa.String(length=255), nullable=True, comment="机柜位置"),
        sa.Column(
            "sort_no",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("1"),
            comment="排序号",
        ),
        sa.Column(
            "is_mandatory_photo",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("true"),
            comment="是否必须拍照",
        ),
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False, comment="Primary key"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
            comment="Record creation timestamp",
        ),
        sa.ForeignKeyConstraint(["inspection_task_id"], ["task_inspection.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_task_inspection_point_id"), "task_inspection_point", ["id"], unique=False)
    op.create_index(
        "idx_task_inspection_point_task",
        "task_inspection_point",
        ["inspection_task_id", "sort_no"],
        unique=False,
    )

    op.create_table(
        "inspection_record",
        sa.Column("inspection_task_id", sa.Integer(), nullable=False, comment="巡检任务ID"),
        sa.Column("inspection_point_id", sa.Integer(), nullable=False, comment="巡检点位ID"),
        sa.Column("user_id", sa.Integer(), nullable=False, comment="提交人"),
        sa.Column(
            "result_status",
            sa.SmallInteger(),
            nullable=False,
            server_default=sa.text("1"),
            comment="结果状态",
        ),
        sa.Column("exception_type", sa.String(length=64), nullable=True, comment="异常类型"),
        sa.Column("exception_desc", sa.Text(), nullable=True, comment="异常描述"),
        sa.Column("handled_desc", sa.Text(), nullable=True, comment="处理说明"),
        sa.Column("media_image_id", sa.Integer(), nullable=True, comment="图片媒体ID"),
        sa.Column("media_video_id", sa.Integer(), nullable=True, comment="视频媒体ID"),
        sa.Column(
            "submitted_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
            comment="提交时间",
        ),
        sa.Column("reviewed_by", sa.Integer(), nullable=True, comment="审核人"),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True, comment="审核时间"),
        sa.Column(
            "review_status",
            sa.SmallInteger(),
            nullable=False,
            server_default=sa.text("0"),
            comment="审核状态",
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
        sa.CheckConstraint("result_status IN (1,2,3)", name="ck_inspection_record_result"),
        sa.CheckConstraint("review_status IN (0,1,2)", name="ck_inspection_record_review"),
        sa.ForeignKeyConstraint(["inspection_point_id"], ["task_inspection_point.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["inspection_task_id"], ["task_inspection.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["media_image_id"], ["media_file.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["media_video_id"], ["media_file.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["reviewed_by"], ["app_user.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["user_id"], ["app_user.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "inspection_task_id",
            "inspection_point_id",
            "user_id",
            name="uq_inspection_record_task_point_user",
        ),
    )
    op.create_index(op.f("ix_inspection_record_id"), "inspection_record", ["id"], unique=False)


def downgrade() -> None:
    """Downgrade database schema."""

    op.drop_index(op.f("ix_inspection_record_id"), table_name="inspection_record")
    op.drop_table("inspection_record")

    op.drop_index("idx_task_inspection_point_task", table_name="task_inspection_point")
    op.drop_index(op.f("ix_task_inspection_point_id"), table_name="task_inspection_point")
    op.drop_table("task_inspection_point")

    op.drop_index(op.f("ix_task_inspection_user_id"), table_name="task_inspection_user")
    op.drop_table("task_inspection_user")

    op.drop_index(op.f("ix_task_inspection_id"), table_name="task_inspection")
    op.drop_table("task_inspection")
