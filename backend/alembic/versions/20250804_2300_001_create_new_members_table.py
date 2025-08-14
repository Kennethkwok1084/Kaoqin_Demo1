"""Create new members table with restructured fields

Revision ID: 20250804_2300_001
Revises: 20250801_0007_2fc5b4d5d552
Create Date: 2025-08-04 23:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "20250804_2300_001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create new restructured members table."""

    # Drop the old members table if it exists
    op.execute("DROP TABLE IF EXISTS members CASCADE")

    # Drop the old enum type if it exists
    op.execute("DROP TYPE IF EXISTS userrole CASCADE")

    # Create new members table with restructured fields
    op.create_table(
        "members",
        sa.Column(
            "id",
            sa.Integer(),
            autoincrement=True,
            nullable=False,
            comment="Primary key",
        ),
        sa.Column(
            "username",
            sa.String(length=50),
            nullable=False,
            comment="登录用户名（不含特殊字符和中文，可修改）",
        ),
        sa.Column(
            "name",
            sa.String(length=50),
            nullable=False,
            comment="真实姓名（可含中文和·符号）",
        ),
        sa.Column(
            "student_id",
            sa.String(length=20),
            nullable=False,
            comment="学号/员工号（纯数字，必填）",
        ),
        sa.Column(
            "phone",
            sa.String(length=11),
            nullable=True,
            comment="手机号（纯数字，可选）",
        ),
        sa.Column(
            "department",
            sa.String(length=100),
            nullable=False,
            comment="部门（默认信息化建设处）",
        ),
        sa.Column(
            "class_name", sa.String(length=50), nullable=False, comment="班级（必填）"
        ),
        sa.Column(
            "join_date", sa.Date(), nullable=False, comment="入职日期（默认导入时间）"
        ),
        sa.Column(
            "password_hash",
            sa.String(length=255),
            nullable=False,
            comment="密码哈希（初始密码123456）",
        ),
        sa.Column(
            "role",
            sa.Enum("ADMIN", "GROUP_LEADER", "MEMBER", "GUEST", name="userrole"),
            nullable=False,
            comment="用户角色",
        ),
        sa.Column(
            "is_active",
            sa.Boolean(),
            nullable=False,
            comment="在职状态（True=在职，False=离职）",
        ),
        sa.Column("is_verified", sa.Boolean(), nullable=False, comment="邮箱验证状态"),
        sa.Column("last_login", sa.DateTime(), nullable=True, comment="最后登录时间"),
        sa.Column("login_count", sa.Integer(), nullable=False, comment="登录次数"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
            comment="记录创建时间",
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
            comment="记录更新时间",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_members"),
        sa.UniqueConstraint("username", name="uq_member_username"),
        sa.UniqueConstraint("student_id", name="uq_member_student_id"),
        comment="成员信息表（重构版）",
    )

    # Create indexes
    op.create_index(op.f("ix_members_id"), "members", ["id"], unique=False)
    op.create_index(op.f("ix_members_username"), "members", ["username"], unique=False)
    op.create_index(op.f("ix_members_name"), "members", ["name"], unique=False)
    op.create_index(
        op.f("ix_members_student_id"), "members", ["student_id"], unique=False
    )

    # Insert default admin user
    op.execute(
        """
        INSERT INTO members (
            username, name, student_id, phone, department, class_name, 
            join_date, password_hash, role, is_active, is_verified, login_count
        ) VALUES (
            'admin', 
            '系统管理员', 
            'admin', 
            NULL,
            '信息化建设处', 
            '管理员',
            CURRENT_DATE,
            '$2b$12$Ke3Lf5m5nKCTb8LUADjzJu3CqgGk8zvFfW3CQvn5f4eKdfgY5G4YS',  -- password: admin123
            'ADMIN',
            true,
            true,
            0
        )
    """
    )


def downgrade() -> None:
    """Drop the restructured members table."""

    # Drop indexes
    op.drop_index(op.f("ix_members_student_id"), table_name="members")
    op.drop_index(op.f("ix_members_name"), table_name="members")
    op.drop_index(op.f("ix_members_username"), table_name="members")
    op.drop_index(op.f("ix_members_id"), table_name="members")

    # Drop table
    op.drop_table("members")

    # Drop enum type if it exists
    op.execute("DROP TYPE IF EXISTS userrole")
