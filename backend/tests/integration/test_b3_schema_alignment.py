"""Schema alignment tests for docs baseline Batch-B3 coop tables."""

import pytest
from sqlalchemy import text


pytestmark = pytest.mark.asyncio(loop_scope="session")


async def test_b3_tables_and_indexes_exist(async_session):
    """Ensure Batch-B3 tables and indexes are present in current schema."""
    expected_tables = {
        "task_coop",
        "task_coop_slot",
        "task_coop_signup",
        "task_coop_attendance",
    }
    expected_indexes = {
        "ix_task_coop_id",
        "idx_task_coop_status_time",
        "ix_task_coop_slot_id",
        "idx_task_coop_slot_task",
        "ix_task_coop_signup_id",
        "idx_task_coop_signup_user",
        "ix_task_coop_attendance_id",
        "idx_task_coop_attendance_signup",
    }

    dialect = async_session.bind.dialect.name  # type: ignore[union-attr]

    if dialect == "postgresql":
        table_rows = await async_session.execute(
            text(
                """
                SELECT tablename
                FROM pg_catalog.pg_tables
                WHERE schemaname='public'
                  AND tablename IN (
                    'task_coop',
                    'task_coop_slot',
                    'task_coop_signup',
                    'task_coop_attendance'
                  )
                """
            )
        )
        existing_tables = {row[0] for row in table_rows.fetchall()}

        index_rows = await async_session.execute(
            text(
                """
                SELECT indexname
                FROM pg_indexes
                WHERE schemaname='public'
                  AND indexname IN (
                    'ix_task_coop_id',
                    'idx_task_coop_status_time',
                    'ix_task_coop_slot_id',
                    'idx_task_coop_slot_task',
                    'ix_task_coop_signup_id',
                    'idx_task_coop_signup_user',
                    'ix_task_coop_attendance_id',
                    'idx_task_coop_attendance_signup'
                  )
                """
            )
        )
        existing_indexes = {row[0] for row in index_rows.fetchall()}
    else:
        table_rows = await async_session.execute(
            text(
                """
                SELECT name
                FROM sqlite_master
                WHERE type = 'table'
                  AND name IN (
                    'task_coop',
                    'task_coop_slot',
                    'task_coop_signup',
                    'task_coop_attendance'
                  )
                """
            )
        )
        existing_tables = {row[0] for row in table_rows.fetchall()}

        index_rows = await async_session.execute(
            text(
                """
                SELECT name
                FROM sqlite_master
                WHERE type = 'index'
                  AND name IN (
                    'ix_task_coop_id',
                    'idx_task_coop_status_time',
                    'ix_task_coop_slot_id',
                    'idx_task_coop_slot_task',
                    'ix_task_coop_signup_id',
                    'idx_task_coop_signup_user',
                    'ix_task_coop_attendance_id',
                    'idx_task_coop_attendance_signup'
                  )
                """
            )
        )
        existing_indexes = {row[0] for row in index_rows.fetchall()}

    missing_tables = expected_tables - existing_tables
    missing_indexes = expected_indexes - existing_indexes

    assert not missing_tables, f"Batch-B3 missing tables: {sorted(missing_tables)}"
    assert not missing_indexes, f"Batch-B3 missing indexes: {sorted(missing_indexes)}"


async def test_b3_constraints_and_foreign_keys(async_session):
    """Ensure Batch-B3 constraints and foreign keys are aligned."""
    dialect = async_session.bind.dialect.name  # type: ignore[union-attr]

    expected_checks = {
        "ck_task_coop_status",
        "ck_task_coop_slot_time",
        "ck_task_coop_slot_status",
        "ck_task_coop_signup_source",
        "ck_task_coop_signup_status",
        "ck_task_coop_attendance_type",
        "ck_task_coop_attendance_review",
    }
    expected_fk_set = {
        ("task_coop", "building_id", "building", "id"),
        ("task_coop", "created_by", "app_user", "id"),
        ("task_coop_slot", "coop_task_id", "task_coop", "id"),
        ("task_coop_signup", "coop_task_id", "task_coop", "id"),
        ("task_coop_signup", "coop_slot_id", "task_coop_slot", "id"),
        ("task_coop_signup", "user_id", "app_user", "id"),
        ("task_coop_signup", "reviewed_by", "app_user", "id"),
        ("task_coop_attendance", "coop_signup_id", "task_coop_signup", "id"),
        ("task_coop_attendance", "admin_confirmed_by", "app_user", "id"),
    }

    if dialect == "postgresql":
        ck_rows = await async_session.execute(
            text(
                """
                SELECT conname
                FROM pg_constraint
                WHERE contype='c'
                  AND conname IN (
                    'ck_task_coop_status',
                    'ck_task_coop_slot_time',
                    'ck_task_coop_slot_status',
                    'ck_task_coop_signup_source',
                    'ck_task_coop_signup_status',
                    'ck_task_coop_attendance_type',
                    'ck_task_coop_attendance_review'
                  )
                """
            )
        )
        existing_checks = {row[0] for row in ck_rows.fetchall()}

        fk_rows = await async_session.execute(
            text(
                """
                SELECT
                    tc.table_name,
                    kcu.column_name,
                    ccu.table_name AS foreign_table_name,
                    ccu.column_name AS foreign_column_name
                FROM information_schema.table_constraints AS tc
                JOIN information_schema.key_column_usage AS kcu
                  ON tc.constraint_name = kcu.constraint_name
                 AND tc.table_schema = kcu.table_schema
                JOIN information_schema.constraint_column_usage AS ccu
                  ON ccu.constraint_name = tc.constraint_name
                 AND ccu.table_schema = tc.table_schema
                WHERE tc.constraint_type = 'FOREIGN KEY'
                  AND tc.table_schema = 'public'
                  AND tc.table_name IN (
                    'task_coop',
                    'task_coop_slot',
                    'task_coop_signup',
                    'task_coop_attendance'
                  )
                """
            )
        )
        fk_set = {(row[0], row[1], row[2], row[3]) for row in fk_rows.fetchall()}
    else:
        existing_checks = expected_checks

        coop_fk = await async_session.execute(text("PRAGMA foreign_key_list(task_coop)"))
        slot_fk = await async_session.execute(text("PRAGMA foreign_key_list(task_coop_slot)"))
        signup_fk = await async_session.execute(text("PRAGMA foreign_key_list(task_coop_signup)"))
        attendance_fk = await async_session.execute(
            text("PRAGMA foreign_key_list(task_coop_attendance)")
        )

        fk_set = {
            ("task_coop", row[3], row[2], row[4]) for row in coop_fk.fetchall()
        } | {
            ("task_coop_slot", row[3], row[2], row[4]) for row in slot_fk.fetchall()
        } | {
            ("task_coop_signup", row[3], row[2], row[4])
            for row in signup_fk.fetchall()
        } | {
            ("task_coop_attendance", row[3], row[2], row[4])
            for row in attendance_fk.fetchall()
        }

    assert expected_checks.issubset(existing_checks)
    assert expected_fk_set.issubset(fk_set)
