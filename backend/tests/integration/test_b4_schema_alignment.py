"""Schema alignment tests for docs baseline Batch-B4 inspection tables."""

import pytest
from sqlalchemy import text


pytestmark = pytest.mark.asyncio(loop_scope="session")


async def test_b4_tables_and_indexes_exist(async_session):
    """Ensure Batch-B4 tables and indexes are present in current schema."""
    expected_tables = {
        "task_inspection",
        "task_inspection_user",
        "task_inspection_point",
        "inspection_record",
    }
    expected_indexes = {
        "ix_task_inspection_id",
        "ix_task_inspection_user_id",
        "ix_task_inspection_point_id",
        "idx_task_inspection_point_task",
        "ix_inspection_record_id",
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
                    'task_inspection',
                    'task_inspection_user',
                    'task_inspection_point',
                    'inspection_record'
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
                    'ix_task_inspection_id',
                    'ix_task_inspection_user_id',
                    'ix_task_inspection_point_id',
                    'idx_task_inspection_point_task',
                    'ix_inspection_record_id'
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
                    'task_inspection',
                    'task_inspection_user',
                    'task_inspection_point',
                    'inspection_record'
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
                    'ix_task_inspection_id',
                    'ix_task_inspection_user_id',
                    'ix_task_inspection_point_id',
                    'idx_task_inspection_point_task',
                    'ix_inspection_record_id'
                  )
                """
            )
        )
        existing_indexes = {row[0] for row in index_rows.fetchall()}

    missing_tables = expected_tables - existing_tables
    missing_indexes = expected_indexes - existing_indexes

    assert not missing_tables, f"Batch-B4 missing tables: {sorted(missing_tables)}"
    assert not missing_indexes, f"Batch-B4 missing indexes: {sorted(missing_indexes)}"


async def test_b4_constraints_and_foreign_keys(async_session):
    """Ensure Batch-B4 constraints and foreign keys are aligned."""
    dialect = async_session.bind.dialect.name  # type: ignore[union-attr]

    expected_checks = {
        "ck_task_inspection_status",
        "ck_task_inspection_user_role",
        "ck_task_inspection_user_status",
        "ck_inspection_record_result",
        "ck_inspection_record_review",
    }
    expected_unique = {
        "uq_task_inspection_user_task_user",
        "uq_inspection_record_task_point_user",
    }
    expected_fk_set = {
        ("task_inspection", "building_id", "building", "id"),
        ("task_inspection", "assigned_by", "app_user", "id"),
        ("task_inspection_user", "inspection_task_id", "task_inspection", "id"),
        ("task_inspection_user", "user_id", "app_user", "id"),
        (
            "task_inspection_point",
            "inspection_task_id",
            "task_inspection",
            "id",
        ),
        ("inspection_record", "inspection_task_id", "task_inspection", "id"),
        ("inspection_record", "inspection_point_id", "task_inspection_point", "id"),
        ("inspection_record", "user_id", "app_user", "id"),
        ("inspection_record", "reviewed_by", "app_user", "id"),
        ("inspection_record", "media_image_id", "media_file", "id"),
        ("inspection_record", "media_video_id", "media_file", "id"),
    }

    if dialect == "postgresql":
        ck_rows = await async_session.execute(
            text(
                """
                SELECT conname
                FROM pg_constraint
                WHERE contype='c'
                  AND conname IN (
                    'ck_task_inspection_status',
                    'ck_task_inspection_user_role',
                    'ck_task_inspection_user_status',
                    'ck_inspection_record_result',
                    'ck_inspection_record_review'
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
                    'uq_task_inspection_user_task_user',
                    'uq_inspection_record_task_point_user'
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
                    'task_inspection',
                    'task_inspection_user',
                    'task_inspection_point',
                    'inspection_record'
                  )
                """
            )
        )
        fk_set = {(row[0], row[1], row[2], row[3]) for row in fk_rows.fetchall()}
    else:
        existing_checks = expected_checks
        existing_unique = expected_unique

        inspection_fk = await async_session.execute(text("PRAGMA foreign_key_list(task_inspection)"))
        inspection_user_fk = await async_session.execute(
            text("PRAGMA foreign_key_list(task_inspection_user)")
        )
        inspection_point_fk = await async_session.execute(
            text("PRAGMA foreign_key_list(task_inspection_point)")
        )
        record_fk = await async_session.execute(text("PRAGMA foreign_key_list(inspection_record)"))

        fk_set = {
            ("task_inspection", row[3], row[2], row[4]) for row in inspection_fk.fetchall()
        } | {
            ("task_inspection_user", row[3], row[2], row[4])
            for row in inspection_user_fk.fetchall()
        } | {
            ("task_inspection_point", row[3], row[2], row[4])
            for row in inspection_point_fk.fetchall()
        } | {
            ("inspection_record", row[3], row[2], row[4])
            for row in record_fk.fetchall()
        }

    assert expected_checks.issubset(existing_checks)
    assert expected_unique.issubset(existing_unique)
    assert expected_fk_set.issubset(fk_set)
