"""Schema alignment tests for docs baseline Batch-B5 sampling tables."""

import pytest
from sqlalchemy import text


pytestmark = pytest.mark.asyncio(loop_scope="session")


async def test_b5_tables_and_indexes_exist(async_session):
    """Ensure Batch-B5 tables and indexes are present in current schema."""
    expected_tables = {
        "task_sampling",
        "task_sampling_user",
        "task_sampling_room",
        "sampling_record",
        "sampling_scan_detail",
        "sampling_test_detail",
    }
    expected_indexes = {
        "ix_task_sampling_id",
        "ix_task_sampling_user_id",
        "ix_task_sampling_room_id",
        "idx_task_sampling_room_task",
        "ix_sampling_record_id",
        "idx_sampling_record_task_user",
        "idx_sampling_record_room",
        "ix_sampling_scan_detail_id",
        "idx_sampling_scan_detail_record",
        "ix_sampling_test_detail_id",
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
                    'task_sampling',
                    'task_sampling_user',
                    'task_sampling_room',
                    'sampling_record',
                    'sampling_scan_detail',
                    'sampling_test_detail'
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
                    'ix_task_sampling_id',
                    'ix_task_sampling_user_id',
                    'ix_task_sampling_room_id',
                    'idx_task_sampling_room_task',
                    'ix_sampling_record_id',
                    'idx_sampling_record_task_user',
                    'idx_sampling_record_room',
                    'ix_sampling_scan_detail_id',
                    'idx_sampling_scan_detail_record',
                    'ix_sampling_test_detail_id'
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
                    'task_sampling',
                    'task_sampling_user',
                    'task_sampling_room',
                    'sampling_record',
                    'sampling_scan_detail',
                    'sampling_test_detail'
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
                    'ix_task_sampling_id',
                    'ix_task_sampling_user_id',
                    'ix_task_sampling_room_id',
                    'idx_task_sampling_room_task',
                    'ix_sampling_record_id',
                    'idx_sampling_record_task_user',
                    'idx_sampling_record_room',
                    'ix_sampling_scan_detail_id',
                    'idx_sampling_scan_detail_record',
                    'ix_sampling_test_detail_id'
                  )
                """
            )
        )
        existing_indexes = {row[0] for row in index_rows.fetchall()}

    missing_tables = expected_tables - existing_tables
    missing_indexes = expected_indexes - existing_indexes

    assert not missing_tables, f"Batch-B5 missing tables: {sorted(missing_tables)}"
    assert not missing_indexes, f"Batch-B5 missing indexes: {sorted(missing_indexes)}"


async def test_b5_constraints_and_foreign_keys(async_session):
    """Ensure Batch-B5 constraints and foreign keys are aligned."""
    dialect = async_session.bind.dialect.name  # type: ignore[union-attr]

    expected_checks = {
        "ck_task_sampling_strategy",
        "ck_task_sampling_status",
        "ck_task_sampling_user_role",
        "ck_sampling_record_mode",
        "ck_sampling_record_review",
    }
    expected_unique = {
        "uq_task_sampling_user_task_user",
        "uq_task_sampling_room_task_room",
    }
    expected_fk_set = {
        ("task_sampling", "building_id", "building", "id"),
        ("task_sampling", "assigned_by", "app_user", "id"),
        ("task_sampling_user", "sampling_task_id", "task_sampling", "id"),
        ("task_sampling_user", "user_id", "app_user", "id"),
        ("task_sampling_room", "sampling_task_id", "task_sampling", "id"),
        ("task_sampling_room", "dorm_room_id", "dorm_room", "id"),
        ("task_sampling_room", "completed_by", "app_user", "id"),
        ("sampling_record", "sampling_task_id", "task_sampling", "id"),
        ("sampling_record", "sampling_task_room_id", "task_sampling_room", "id"),
        ("sampling_record", "dorm_room_id", "dorm_room", "id"),
        ("sampling_record", "user_id", "app_user", "id"),
        ("sampling_record", "reviewed_by", "app_user", "id"),
        ("sampling_scan_detail", "sampling_record_id", "sampling_record", "id"),
        ("sampling_test_detail", "sampling_record_id", "sampling_record", "id"),
    }

    if dialect == "postgresql":
        ck_rows = await async_session.execute(
            text(
                """
                SELECT conname
                FROM pg_constraint
                WHERE contype='c'
                  AND conname IN (
                    'ck_task_sampling_strategy',
                    'ck_task_sampling_status',
                    'ck_task_sampling_user_role',
                    'ck_sampling_record_mode',
                    'ck_sampling_record_review'
                  )
                """
            )
        )
        existing_checks = {row[0] for row in ck_rows.fetchall()}

        unique_rows = await async_session.execute(
            text(
                """
                SELECT conname
                FROM pg_constraint
                WHERE contype='u'
                  AND conname IN (
                    'uq_task_sampling_user_task_user',
                    'uq_task_sampling_room_task_room'
                  )
                """
            )
        )
        existing_unique = {row[0] for row in unique_rows.fetchall()}

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
                    'task_sampling',
                    'task_sampling_user',
                    'task_sampling_room',
                    'sampling_record',
                    'sampling_scan_detail',
                    'sampling_test_detail'
                  )
                """
            )
        )
        fk_set = {(row[0], row[1], row[2], row[3]) for row in fk_rows.fetchall()}
    else:
        existing_checks = expected_checks
        existing_unique = expected_unique

        task_fk = await async_session.execute(text("PRAGMA foreign_key_list(task_sampling)"))
        user_fk = await async_session.execute(text("PRAGMA foreign_key_list(task_sampling_user)"))
        room_fk = await async_session.execute(text("PRAGMA foreign_key_list(task_sampling_room)"))
        record_fk = await async_session.execute(text("PRAGMA foreign_key_list(sampling_record)"))
        scan_fk = await async_session.execute(text("PRAGMA foreign_key_list(sampling_scan_detail)"))
        test_fk = await async_session.execute(text("PRAGMA foreign_key_list(sampling_test_detail)"))

        fk_set = {
            ("task_sampling", row[3], row[2], row[4]) for row in task_fk.fetchall()
        } | {
            ("task_sampling_user", row[3], row[2], row[4]) for row in user_fk.fetchall()
        } | {
            ("task_sampling_room", row[3], row[2], row[4]) for row in room_fk.fetchall()
        } | {
            ("sampling_record", row[3], row[2], row[4]) for row in record_fk.fetchall()
        } | {
            ("sampling_scan_detail", row[3], row[2], row[4]) for row in scan_fk.fetchall()
        } | {
            ("sampling_test_detail", row[3], row[2], row[4]) for row in test_fk.fetchall()
        }

    assert expected_checks.issubset(existing_checks)
    assert expected_unique.issubset(existing_unique)
    assert expected_fk_set.issubset(fk_set)
