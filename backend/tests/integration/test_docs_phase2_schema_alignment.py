"""Schema alignment tests for docs baseline phase2 governance/workhour tables."""

import pytest
from sqlalchemy import text


pytestmark = pytest.mark.asyncio(loop_scope="session")


async def test_phase2_tables_and_indexes_exist(async_session):
    """Ensure phase2 docs tables and indexes are present in current schema."""
    expected_tables = {
        "workhour_rule",
        "workhour_tag",
        "review_log",
        "todo_item",
        "biz_operation_log",
    }
    expected_indexes = {
        "ix_workhour_rule_id",
        "ix_workhour_tag_id",
        "ix_review_log_id",
        "idx_review_log_biz",
        "ix_todo_item_id",
        "idx_todo_item_assignee_status",
        "ix_biz_operation_log_id",
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
                    'workhour_rule',
                    'workhour_tag',
                    'review_log',
                    'todo_item',
                    'biz_operation_log'
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
                    'ix_workhour_rule_id',
                    'ix_workhour_tag_id',
                    'ix_review_log_id',
                    'idx_review_log_biz',
                    'ix_todo_item_id',
                    'idx_todo_item_assignee_status',
                    'ix_biz_operation_log_id'
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
                    'workhour_rule',
                    'workhour_tag',
                    'review_log',
                    'todo_item',
                    'biz_operation_log'
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
                    'ix_workhour_rule_id',
                    'ix_workhour_tag_id',
                    'ix_review_log_id',
                    'idx_review_log_biz',
                    'ix_todo_item_id',
                    'idx_todo_item_assignee_status',
                    'ix_biz_operation_log_id'
                  )
                """
            )
        )
        existing_indexes = {row[0] for row in index_rows.fetchall()}

    missing_tables = expected_tables - existing_tables
    missing_indexes = expected_indexes - existing_indexes
    assert not missing_tables, f"Phase2 missing tables: {sorted(missing_tables)}"
    assert not missing_indexes, f"Phase2 missing indexes: {sorted(missing_indexes)}"


async def test_phase2_constraints_and_foreign_keys(async_session):
    """Ensure phase2 check constraints and key foreign keys are aligned."""
    dialect = async_session.bind.dialect.name  # type: ignore[union-attr]

    if dialect == "postgresql":
        ck_rows = await async_session.execute(
            text(
                """
                SELECT conname
                FROM pg_constraint
                WHERE contype='c'
                  AND conname IN (
                    'ck_workhour_rule_biz',
                    'ck_workhour_tag_type',
                    'ck_workhour_tag_bonus_mode',
                    'ck_todo_item_priority',
                    'ck_todo_item_status'
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
                  AND tc.table_name IN ('review_log', 'todo_item', 'biz_operation_log')
                """
            )
        )
        fk_set = {(row[0], row[1], row[2], row[3]) for row in fk_rows.fetchall()}
    else:
        # SQLite fallback: only validate foreign key targets.
        existing_checks = {
            "ck_workhour_rule_biz",
            "ck_workhour_tag_type",
            "ck_workhour_tag_bonus_mode",
            "ck_todo_item_priority",
            "ck_todo_item_status",
        }

        review_fk = await async_session.execute(text("PRAGMA foreign_key_list(review_log)"))
        todo_fk = await async_session.execute(text("PRAGMA foreign_key_list(todo_item)"))
        biz_fk = await async_session.execute(
            text("PRAGMA foreign_key_list(biz_operation_log)")
        )
        fk_set = {
            ("review_log", row[3], row[2], row[4]) for row in review_fk.fetchall()
        } | {
            ("todo_item", row[3], row[2], row[4]) for row in todo_fk.fetchall()
        } | {
            ("biz_operation_log", row[3], row[2], row[4])
            for row in biz_fk.fetchall()
        }

    expected_checks = {
        "ck_workhour_rule_biz",
        "ck_workhour_tag_type",
        "ck_workhour_tag_bonus_mode",
        "ck_todo_item_priority",
        "ck_todo_item_status",
    }
    expected_fk_set = {
        ("review_log", "reviewer_id", "app_user", "id"),
        ("todo_item", "assignee_user_id", "app_user", "id"),
        ("biz_operation_log", "operator_user_id", "app_user", "id"),
    }

    assert expected_checks.issubset(existing_checks)
    assert expected_fk_set.issubset(fk_set)
