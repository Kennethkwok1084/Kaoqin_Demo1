"""Align docs baseline phase1 foundation tables

Revision ID: c4d5e6f7a8b9
Revises: b3c4d5e6f7a8
Create Date: 2026-04-09 22:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "c4d5e6f7a8b9"
down_revision: Union[str, None] = "b3c4d5e6f7a8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade database schema."""
    # Fix refresh token FK target: members.id -> app_user.id
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1
                FROM pg_constraint
                WHERE conname = 'auth_refresh_token_user_id_fkey'
            ) THEN
                ALTER TABLE auth_refresh_token
                DROP CONSTRAINT auth_refresh_token_user_id_fkey;
            END IF;

            IF EXISTS (
                SELECT 1
                FROM pg_constraint
                WHERE conname = 'fk_auth_refresh_token_user_id_members'
            ) THEN
                ALTER TABLE auth_refresh_token
                DROP CONSTRAINT fk_auth_refresh_token_user_id_members;
            END IF;

            IF NOT EXISTS (
                SELECT 1
                FROM pg_constraint
                WHERE conname = 'fk_auth_refresh_token_user_id_app_user'
            ) THEN
                ALTER TABLE auth_refresh_token
                ADD CONSTRAINT fk_auth_refresh_token_user_id_app_user
                FOREIGN KEY (user_id)
                REFERENCES app_user(id)
                ON DELETE CASCADE;
            END IF;
        END
        $$;
        """
    )

    op.create_table(
        "sys_config",
        sa.Column("config_group", sa.String(length=64), nullable=False, comment="配置分组"),
        sa.Column("config_key", sa.String(length=128), nullable=False, comment="配置键"),
        sa.Column(
            "config_value",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
            comment="配置值 JSON",
        ),
        sa.Column("description", sa.Text(), nullable=True, comment="配置说明"),
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
        sa.CheckConstraint("char_length(config_group) > 0", name="ck_sys_config_group_non_empty"),
        sa.CheckConstraint("char_length(config_key) > 0", name="ck_sys_config_key_non_empty"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("config_group", "config_key", name="uq_sys_config_group_key"),
    )
    op.create_index(op.f("ix_sys_config_id"), "sys_config", ["id"], unique=False)

    op.create_table(
        "building",
        sa.Column("building_code", sa.String(length=32), nullable=False, comment="楼栋编码"),
        sa.Column("building_name", sa.String(length=128), nullable=False, comment="楼栋名称"),
        sa.Column("campus_name", sa.String(length=128), nullable=True, comment="校区名称"),
        sa.Column("area_name", sa.String(length=128), nullable=True, comment="区域名称"),
        sa.Column("longitude", sa.Numeric(precision=10, scale=6), nullable=True, comment="经度"),
        sa.Column("latitude", sa.Numeric(precision=10, scale=6), nullable=True, comment="纬度"),
        sa.Column(
            "status",
            sa.SmallInteger(),
            nullable=False,
            server_default=sa.text("1"),
            comment="0禁用 1启用",
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
        sa.CheckConstraint("status IN (0,1)", name="ck_building_status"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("building_code", name="uq_building_code"),
    )
    op.create_index(op.f("ix_building_id"), "building", ["id"], unique=False)

    op.create_table(
        "dorm_room",
        sa.Column("building_id", sa.Integer(), nullable=False, comment="楼栋ID"),
        sa.Column("room_no", sa.String(length=32), nullable=False, comment="房间号"),
        sa.Column("floor_no", sa.String(length=16), nullable=True, comment="楼层"),
        sa.Column(
            "target_ssid",
            sa.String(length=64),
            nullable=False,
            server_default=sa.text("'GCC'"),
            comment="目标SSID",
        ),
        sa.Column("target_bssid", sa.String(length=64), nullable=False, comment="目标BSSID"),
        sa.Column("dorm_label", sa.String(length=128), nullable=True, comment="宿舍标签"),
        sa.Column(
            "active_repair_weight",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("0"),
            comment="当期报修权重",
        ),
        sa.Column("last_sampled_at", sa.DateTime(timezone=True), nullable=True, comment="最近抽检时间"),
        sa.Column(
            "status",
            sa.SmallInteger(),
            nullable=False,
            server_default=sa.text("1"),
            comment="0禁用 1启用",
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
        sa.CheckConstraint("status IN (0,1)", name="ck_dorm_room_status"),
        sa.ForeignKeyConstraint(["building_id"], ["building.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("building_id", "room_no", name="uq_dorm_room_building_room"),
    )
    op.create_index(op.f("ix_dorm_room_id"), "dorm_room", ["id"], unique=False)
    op.create_index("idx_dorm_room_building_status", "dorm_room", ["building_id", "status"], unique=False)
    op.create_index("idx_dorm_room_last_sampled", "dorm_room", ["last_sampled_at"], unique=False)

    op.create_table(
        "media_file",
        sa.Column("biz_type", sa.String(length=32), nullable=False, comment="业务类型"),
        sa.Column("biz_id", sa.BigInteger(), nullable=False, comment="业务主键ID"),
        sa.Column("file_type", sa.String(length=16), nullable=False, comment="文件类型"),
        sa.Column("storage_path", sa.Text(), nullable=False, comment="存储路径"),
        sa.Column("file_name", sa.String(length=255), nullable=False, comment="原始文件名"),
        sa.Column("content_type", sa.String(length=128), nullable=True, comment="MIME类型"),
        sa.Column(
            "file_size",
            sa.BigInteger(),
            nullable=False,
            server_default=sa.text("0"),
            comment="文件大小(字节)",
        ),
        sa.Column("sha256_hex", sa.String(length=128), nullable=True, comment="SHA256摘要"),
        sa.Column(
            "watermark_payload",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
            comment="水印元数据",
        ),
        sa.Column("uploaded_by", sa.Integer(), nullable=False, comment="上传人"),
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False, comment="Primary key"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
            comment="Record creation timestamp",
        ),
        sa.CheckConstraint(
            "file_type IN ('image','video','audio','ocr_source','other')",
            name="ck_media_file_type",
        ),
        sa.ForeignKeyConstraint(["uploaded_by"], ["app_user.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_media_file_id"), "media_file", ["id"], unique=False)
    op.create_index("idx_media_file_biz", "media_file", ["biz_type", "biz_id"], unique=False)


def downgrade() -> None:
    """Downgrade database schema."""
    op.drop_index("idx_media_file_biz", table_name="media_file")
    op.drop_index(op.f("ix_media_file_id"), table_name="media_file")
    op.drop_table("media_file")

    op.drop_index("idx_dorm_room_last_sampled", table_name="dorm_room")
    op.drop_index("idx_dorm_room_building_status", table_name="dorm_room")
    op.drop_index(op.f("ix_dorm_room_id"), table_name="dorm_room")
    op.drop_table("dorm_room")

    op.drop_index(op.f("ix_building_id"), table_name="building")
    op.drop_table("building")

    op.drop_index(op.f("ix_sys_config_id"), table_name="sys_config")
    op.drop_table("sys_config")

    # Restore refresh token FK target: app_user.id -> members.id
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1
                FROM pg_constraint
                WHERE conname = 'fk_auth_refresh_token_user_id_app_user'
            ) THEN
                ALTER TABLE auth_refresh_token
                DROP CONSTRAINT fk_auth_refresh_token_user_id_app_user;
            END IF;

            IF NOT EXISTS (
                SELECT 1
                FROM pg_constraint
                WHERE conname = 'auth_refresh_token_user_id_fkey'
            ) THEN
                ALTER TABLE auth_refresh_token
                ADD CONSTRAINT auth_refresh_token_user_id_fkey
                FOREIGN KEY (user_id)
                REFERENCES members(id)
                ON DELETE CASCADE;
            END IF;
        END
        $$;
        """
    )
