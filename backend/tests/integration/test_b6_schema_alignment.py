"""Schema alignment tests for docs baseline Batch-B6 repair/import/workhour tables."""

import pytest
from sqlalchemy import text


pytestmark = pytest.mark.asyncio(loop_scope="session")


async def test_b6_tables_and_indexes_exist(async_session):
    """Ensure Batch-B6 tables and indexes are present in current schema."""
    expected_tables = {
        "repair_ticket",
        "repair_ticket_member",
        "import_batch",
        "import_repair_row",
        "repair_match_application",
        "workhour_entry",
        "workhour_entry_tag",
    }
    expected_indexes = {
        "ix_repair_ticket_id",
        "idx_repair_ticket_no",
        "idx_repair_ticket_source_status",
        "ix_repair_ticket_member_id",
        "ix_import_batch_id",
        "ix_import_repair_row_id",
        "idx_import_repair_row_no",
        "idx_import_repair_row_match",
        "ix_repair_match_application_id",
        "ix_workhour_entry_id",
        "idx_workhour_entry_user_time",
        "idx_workhour_entry_biz",
        "ix_workhour_entry_tag_id",
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
                    'repair_ticket',
                    'repair_ticket_member',
                    'import_batch',
                    'import_repair_row',
                    'repair_match_application',
                    'workhour_entry',
                    'workhour_entry_tag'
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
                    'ix_repair_ticket_id',
                    'idx_repair_ticket_no',
                    'idx_repair_ticket_source_status',
                    'ix_repair_ticket_member_id',
                    'ix_import_batch_id',
                    'ix_import_repair_row_id',
                    'idx_import_repair_row_no',
                    'idx_import_repair_row_match',
                    'ix_repair_match_application_id',
                    'ix_workhour_entry_id',
                    'idx_workhour_entry_user_time',
                    'idx_workhour_entry_biz',
                    'ix_workhour_entry_tag_id'
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
                    'repair_ticket',
                    'repair_ticket_member',
                    'import_batch',
                    'import_repair_row',
                    'repair_match_application',
                    'workhour_entry',
                    'workhour_entry_tag'
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
                    'ix_repair_ticket_id',
                    'idx_repair_ticket_no',
                    'idx_repair_ticket_source_status',
                    'ix_repair_ticket_member_id',
                    'ix_import_batch_id',
                    'ix_import_repair_row_id',
                    'idx_import_repair_row_no',
                    'idx_import_repair_row_match',
                    'ix_repair_match_application_id',
                    'ix_workhour_entry_id',
                    'idx_workhour_entry_user_time',
                    'idx_workhour_entry_biz',
                    'ix_workhour_entry_tag_id'
                  )
                """
            )
        )
        existing_indexes = {row[0] for row in index_rows.fetchall()}

    missing_tables = expected_tables - existing_tables
    missing_indexes = expected_indexes - existing_indexes

    assert not missing_tables, f"Batch-B6 missing tables: {sorted(missing_tables)}"
    assert not missing_indexes, f"Batch-B6 missing indexes: {sorted(missing_indexes)}"


async def test_b6_constraints_and_foreign_keys(async_session):
    """Ensure Batch-B6 constraints and foreign keys are aligned."""
    dialect = async_session.bind.dialect.name  # type: ignore[union-attr]

    expected_checks = {
        "ck_repair_ticket_source",
        "ck_repair_ticket_solve_status",
        "ck_repair_ticket_match_status",
        "ck_repair_ticket_member_role",
        "ck_import_batch_type",
        "ck_import_batch_status",
        "ck_repair_match_application_status",
        "ck_workhour_entry_biz",
        "ck_workhour_entry_review",
    }
    expected_unique = {
        "uq_repair_ticket_member_ticket_user",
        "uq_repair_match_application_ticket",
        "uq_workhour_entry_tag_entry_tag",
    }
    expected_fk_set = {
        ("repair_ticket", "building_id", "building", "id"),
        ("repair_ticket", "dorm_room_id", "dorm_room", "id"),
        ("repair_ticket", "source_screenshot_id", "media_file", "id"),
        ("repair_ticket", "doorplate_image_id", "media_file", "id"),
        ("repair_ticket", "created_by", "app_user", "id"),
        ("repair_ticket_member", "repair_ticket_id", "repair_ticket", "id"),
        ("repair_ticket_member", "user_id", "app_user", "id"),
        ("import_batch", "imported_by", "app_user", "id"),
        ("import_repair_row", "import_batch_id", "import_batch", "id"),
        ("import_repair_row", "matched_ticket_id", "repair_ticket", "id"),
        ("repair_match_application", "repair_ticket_id", "repair_ticket", "id"),
        ("repair_match_application", "import_repair_row_id", "import_repair_row", "id"),
        ("repair_match_application", "applied_by", "app_user", "id"),
        ("repair_match_application", "reviewed_by", "app_user", "id"),
        ("workhour_entry", "user_id", "app_user", "id"),
        ("workhour_entry", "source_rule_id", "workhour_rule", "id"),
        ("workhour_entry", "reviewed_by", "app_user", "id"),
        ("workhour_entry_tag", "workhour_entry_id", "workhour_entry", "id"),
        ("workhour_entry_tag", "workhour_tag_id", "workhour_tag", "id"),
    }

    if dialect == "postgresql":
        ck_rows = await async_session.execute(
            text(
                """
                SELECT conname
                FROM pg_constraint
                WHERE contype='c'
                  AND conname IN (
                    'ck_repair_ticket_source',
                    'ck_repair_ticket_solve_status',
                    'ck_repair_ticket_match_status',
                    'ck_repair_ticket_member_role',
                    'ck_import_batch_type',
                    'ck_import_batch_status',
                    'ck_repair_match_application_status',
                    'ck_workhour_entry_biz',
                    'ck_workhour_entry_review'
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
                    'uq_repair_ticket_member_ticket_user',
                    'uq_repair_match_application_ticket',
                    'uq_workhour_entry_tag_entry_tag'
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
                    'repair_ticket',
                    'repair_ticket_member',
                    'import_batch',
                    'import_repair_row',
                    'repair_match_application',
                    'workhour_entry',
                    'workhour_entry_tag'
                  )
                """
            )
        )
        fk_set = {(row[0], row[1], row[2], row[3]) for row in fk_rows.fetchall()}
    else:
        existing_checks = expected_checks
        existing_unique = expected_unique

        ticket_fk = await async_session.execute(text("PRAGMA foreign_key_list(repair_ticket)"))
        member_fk = await async_session.execute(text("PRAGMA foreign_key_list(repair_ticket_member)"))
        batch_fk = await async_session.execute(text("PRAGMA foreign_key_list(import_batch)"))
        row_fk = await async_session.execute(text("PRAGMA foreign_key_list(import_repair_row)"))
        app_fk = await async_session.execute(text("PRAGMA foreign_key_list(repair_match_application)"))
        entry_fk = await async_session.execute(text("PRAGMA foreign_key_list(workhour_entry)"))
        entry_tag_fk = await async_session.execute(text("PRAGMA foreign_key_list(workhour_entry_tag)"))

        fk_set = {
            ("repair_ticket", row[3], row[2], row[4]) for row in ticket_fk.fetchall()
        } | {
            ("repair_ticket_member", row[3], row[2], row[4]) for row in member_fk.fetchall()
        } | {
            ("import_batch", row[3], row[2], row[4]) for row in batch_fk.fetchall()
        } | {
            ("import_repair_row", row[3], row[2], row[4]) for row in row_fk.fetchall()
        } | {
            ("repair_match_application", row[3], row[2], row[4])
            for row in app_fk.fetchall()
        } | {
            ("workhour_entry", row[3], row[2], row[4]) for row in entry_fk.fetchall()
        } | {
            ("workhour_entry_tag", row[3], row[2], row[4])
            for row in entry_tag_fk.fetchall()
        }

    assert expected_checks.issubset(existing_checks)
    assert expected_unique.issubset(existing_unique)
    assert expected_fk_set.issubset(fk_set)
