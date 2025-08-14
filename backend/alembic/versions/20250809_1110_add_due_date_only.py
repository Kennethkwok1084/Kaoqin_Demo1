"""Add due_date field only

Revision ID: 20250809_1110
Revises: 20250808_0001
Create Date: 2025-08-09 11:10:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "20250809_1110"
down_revision: Union[str, None] = "20250808_0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add due_date field to repair_tasks table."""
    op.add_column(
        "repair_tasks",
        sa.Column(
            "due_date",
            sa.DateTime(timezone=True),
            nullable=True,
            comment="Task due date (usually equals completion_time from import data)",
        ),
    )


def downgrade() -> None:
    """Remove due_date field from repair_tasks table."""
    op.drop_column("repair_tasks", "due_date")
