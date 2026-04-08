"""Add auth refresh token persistence table

Revision ID: a1f2c3d4e5f6
Revises: d1402934c1fc
Create Date: 2026-04-08 12:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "a1f2c3d4e5f6"
down_revision: Union[str, None] = "d1402934c1fc"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade database schema."""
    op.create_table(
        "auth_refresh_token",
        sa.Column("user_id", sa.Integer(), nullable=False, comment="User id"),
        sa.Column("refresh_token", sa.String(length=255), nullable=False, comment="Refresh token"),
        sa.Column("device_id", sa.String(length=128), nullable=True, comment="Device identifier"),
        sa.Column("device_name", sa.String(length=128), nullable=True, comment="Device name"),
        sa.Column("platform_code", sa.String(length=32), nullable=True, comment="Platform code"),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False, comment="Refresh token expiration time"),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True, comment="Revoke time"),
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
        sa.ForeignKeyConstraint(["user_id"], ["members.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(op.f("ix_auth_refresh_token_id"), "auth_refresh_token", ["id"], unique=False)
    op.create_index(
        op.f("ix_auth_refresh_token_refresh_token"),
        "auth_refresh_token",
        ["refresh_token"],
        unique=True,
    )
    op.create_index(
        op.f("ix_auth_refresh_token_user_id"),
        "auth_refresh_token",
        ["user_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_auth_refresh_token_expires_at"),
        "auth_refresh_token",
        ["expires_at"],
        unique=False,
    )


def downgrade() -> None:
    """Downgrade database schema."""
    op.drop_index(op.f("ix_auth_refresh_token_expires_at"), table_name="auth_refresh_token")
    op.drop_index(op.f("ix_auth_refresh_token_user_id"), table_name="auth_refresh_token")
    op.drop_index(op.f("ix_auth_refresh_token_refresh_token"), table_name="auth_refresh_token")
    op.drop_index(op.f("ix_auth_refresh_token_id"), table_name="auth_refresh_token")
    op.drop_table("auth_refresh_token")
