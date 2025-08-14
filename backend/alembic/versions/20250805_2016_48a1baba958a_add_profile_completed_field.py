"""add_profile_completed_field

Revision ID: 48a1baba958a
Revises: 6ae2481d55e9
Create Date: 2025-08-05 20:16:01.438754

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "48a1baba958a"
down_revision: Union[str, None] = "6ae2481d55e9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add profile_completed field to members table."""
    # Add profile_completed column
    op.add_column(
        "members",
        sa.Column(
            "profile_completed", sa.Boolean(), nullable=False, server_default="false"
        ),
    )


def downgrade() -> None:
    """Remove profile_completed field from members table."""
    # Remove profile_completed column
    op.drop_column("members", "profile_completed")
