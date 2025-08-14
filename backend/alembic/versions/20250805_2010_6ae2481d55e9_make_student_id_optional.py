"""make_student_id_optional

Revision ID: 6ae2481d55e9
Revises: 2fc5b4d5d552
Create Date: 2025-08-05 20:10:01.113146

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "6ae2481d55e9"
down_revision: Union[str, None] = "2fc5b4d5d552"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Make student_id nullable."""
    # Make student_id nullable
    op.alter_column(
        "members", "student_id", existing_type=sa.VARCHAR(length=20), nullable=True
    )


def downgrade() -> None:
    """Make student_id not nullable again."""
    # Make student_id not nullable again
    op.alter_column(
        "members", "student_id", existing_type=sa.VARCHAR(length=20), nullable=False
    )
