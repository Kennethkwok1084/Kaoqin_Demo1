"""Add app_user and user_profile tables with members backfill

Revision ID: b3c4d5e6f7a8
Revises: a1f2c3d4e5f6
Create Date: 2026-04-08 16:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "b3c4d5e6f7a8"
down_revision: Union[str, None] = "a1f2c3d4e5f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade database schema."""
    op.create_table(
        "app_user",
        sa.Column("student_no", sa.String(length=32), nullable=False, comment="学号/工号"),
        sa.Column("password_hash", sa.String(length=255), nullable=False, comment="密码哈希"),
        sa.Column("real_name", sa.String(length=64), nullable=False, comment="真实姓名"),
        sa.Column(
            "role_code",
            sa.String(length=16),
            nullable=False,
            server_default=sa.text("'user'"),
            comment="角色编码",
        ),
        sa.Column("phone", sa.String(length=32), nullable=True, comment="手机号"),
        sa.Column("email", sa.String(length=128), nullable=True, comment="邮箱"),
        sa.Column("avatar_url", sa.Text(), nullable=True, comment="头像地址"),
        sa.Column(
            "status",
            sa.SmallInteger(),
            nullable=False,
            server_default=sa.text("1"),
            comment="0禁用 1启用 2锁定",
        ),
        sa.Column(
            "last_login_at",
            sa.DateTime(timezone=True),
            nullable=True,
            comment="最近登录时间",
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
        sa.CheckConstraint("role_code IN ('admin','user')", name="ck_app_user_role_code"),
        sa.CheckConstraint("status IN (0,1,2)", name="ck_app_user_status"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(op.f("ix_app_user_id"), "app_user", ["id"], unique=False)
    op.create_index(
        op.f("ix_app_user_student_no"), "app_user", ["student_no"], unique=True
    )
    op.create_index(
        "idx_app_user_role_status", "app_user", ["role_code", "status"], unique=False
    )

    op.create_table(
        "user_profile",
        sa.Column("user_id", sa.Integer(), nullable=False, comment="用户ID"),
        sa.Column("nickname", sa.String(length=64), nullable=True, comment="昵称"),
        sa.Column("gender", sa.SmallInteger(), nullable=True, comment="性别 0未知 1男 2女"),
        sa.Column(
            "department_name", sa.String(length=128), nullable=True, comment="部门名称"
        ),
        sa.Column("grade_name", sa.String(length=64), nullable=True, comment="年级"),
        sa.Column("class_name", sa.String(length=64), nullable=True, comment="班级"),
        sa.Column("major_name", sa.String(length=128), nullable=True, comment="专业"),
        sa.Column(
            "id_card_mask", sa.String(length=32), nullable=True, comment="脱敏身份证号"
        ),
        sa.Column(
            "emergency_contact", sa.String(length=64), nullable=True, comment="紧急联系人"
        ),
        sa.Column(
            "emergency_phone", sa.String(length=32), nullable=True, comment="紧急联系电话"
        ),
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
            "gender IN (0,1,2) OR gender IS NULL", name="ck_user_profile_gender"
        ),
        sa.ForeignKeyConstraint(["user_id"], ["app_user.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("user_id"),
    )

    op.execute(
        """
        INSERT INTO app_user (
            id,
            student_no,
            password_hash,
            real_name,
            role_code,
            phone,
            email,
            status,
            last_login_at,
            remark,
            created_at,
            updated_at
        )
        SELECT
            m.id,
            COALESCE(NULLIF(m.student_id, ''), m.username) AS student_no,
            m.password_hash,
            m.name AS real_name,
            CASE WHEN m.role = 'admin' THEN 'admin' ELSE 'user' END AS role_code,
            m.phone,
            m.email,
            CASE WHEN m.is_active THEN 1 ELSE 0 END AS status,
            m.last_login,
            'backfill from members',
            m.created_at,
            m.updated_at
        FROM members m
        WHERE NOT EXISTS (
            SELECT 1
            FROM app_user au
            WHERE au.id = m.id
        )
        """
    )

    op.execute(
        """
        INSERT INTO user_profile (
            user_id,
            nickname,
            department_name,
            class_name,
            created_at,
            updated_at
        )
        SELECT
            m.id,
            m.name,
            m.department,
            m.class_name,
            m.created_at,
            m.updated_at
        FROM members m
        WHERE NOT EXISTS (
            SELECT 1
            FROM user_profile up
            WHERE up.user_id = m.id
        )
        """
    )

    op.execute(
        """
        SELECT setval(
            pg_get_serial_sequence('app_user', 'id'),
            COALESCE((SELECT MAX(id) FROM app_user), 1),
            true
        )
        """
    )


def downgrade() -> None:
    """Downgrade database schema."""
    op.drop_table("user_profile")
    op.drop_index("idx_app_user_role_status", table_name="app_user")
    op.drop_index(op.f("ix_app_user_student_no"), table_name="app_user")
    op.drop_index(op.f("ix_app_user_id"), table_name="app_user")
    op.drop_table("app_user")
