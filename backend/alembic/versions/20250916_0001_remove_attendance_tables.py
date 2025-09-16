"""
Remove attendance-related tables and enums (attendance_records, attendance_exceptions).

Revision ID: remove_attendance_tables_20250916
Revises: 20250915_1506_e47caaff7c57_add_assistance_task_type
Create Date: 2025-09-16 00:01:00
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "remove_attendance_tables_20250916"
down_revision: Union[str, None] = "20250915_1506_e47caaff7c57_add_assistance_task_type"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Drop FKs and tables if they exist. Use IF EXISTS guards via raw SQL for safety.
    conn = op.get_bind()

    # Drop indexes (ignore errors if not exist)
    try:
        op.drop_index("idx_attendance_date_member", table_name="attendance_records")
    except Exception:
        pass

    # Drop tables
    op.execute("DROP TABLE IF EXISTS attendance_exceptions CASCADE")
    op.execute("DROP TABLE IF EXISTS attendance_records CASCADE")

    # Drop enum types if exist (PostgreSQL)
    op.execute("DO $$ BEGIN IF EXISTS (SELECT 1 FROM pg_type WHERE typname = 'attendanceexceptionstatus') THEN DROP TYPE attendanceexceptionstatus; END IF; END $$;")


def downgrade() -> None:
    # Recreate ENUM
    op.execute("CREATE TYPE attendanceexceptionstatus AS ENUM ('pending','approved','rejected')")

    # Recreate tables with minimal structure matching previous models (subset sufficient for downgrade)
    op.create_table(
        "attendance_records",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("member_id", sa.Integer(), nullable=False),
        sa.Column("attendance_date", sa.Date(), nullable=False),
        sa.Column("checkin_time", sa.DateTime(), nullable=True),
        sa.Column("checkout_time", sa.DateTime(), nullable=True),
        sa.Column("work_hours", sa.Float(), nullable=True, server_default="0"),
    )
    op.create_index("idx_attendance_date_member", "attendance_records", ["attendance_date", "member_id"], unique=False)

    op.create_table(
        "attendance_exceptions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("member_id", sa.Integer(), nullable=False),
        sa.Column("exception_type", sa.String(50), nullable=False),
        sa.Column("exception_date", sa.Date(), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("status", sa.Enum(name="attendanceexceptionstatus", *["pending","approved","rejected"]), nullable=False),
    )

