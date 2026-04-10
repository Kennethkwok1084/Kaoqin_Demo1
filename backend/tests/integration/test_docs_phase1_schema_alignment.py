"""Schema alignment tests for docs baseline phase 1 foundation tables."""

import pytest
from sqlalchemy import text


pytestmark = pytest.mark.asyncio(loop_scope="session")


async def test_phase1_foundation_tables_exist(async_session):
    """Ensure docs phase1 foundation tables are present in current schema."""
    target_tables = {
        "sys_config",
        "building",
        "dorm_room",
        "media_file",
        "auth_refresh_token",
    }

    dialect = async_session.bind.dialect.name  # type: ignore[union-attr]
    if dialect == "postgresql":
        result = await async_session.execute(
            text(
                """
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public'
                  AND table_name IN ('sys_config', 'building', 'dorm_room', 'media_file', 'auth_refresh_token')
                """
            )
        )
        existing_tables = {row[0] for row in result.fetchall()}
    else:
        result = await async_session.execute(
            text(
                """
                SELECT name
                FROM sqlite_master
                WHERE type = 'table'
                  AND name IN ('sys_config', 'building', 'dorm_room', 'media_file', 'auth_refresh_token')
                """
            )
        )
        existing_tables = {row[0] for row in result.fetchall()}

    missing = target_tables - existing_tables
    assert not missing, f"Missing phase1 tables: {sorted(missing)}"


async def test_auth_refresh_token_fk_targets_app_user(async_session):
    """Ensure refresh token foreign key points to app_user instead of legacy members."""
    dialect = async_session.bind.dialect.name  # type: ignore[union-attr]

    if dialect == "postgresql":
        result = await async_session.execute(
            text(
                """
                SELECT ccu.table_name
                FROM information_schema.table_constraints tc
                JOIN information_schema.key_column_usage kcu
                  ON tc.constraint_name = kcu.constraint_name
                 AND tc.table_schema = kcu.table_schema
                JOIN information_schema.constraint_column_usage ccu
                  ON ccu.constraint_name = tc.constraint_name
                 AND ccu.table_schema = tc.table_schema
                WHERE tc.constraint_type = 'FOREIGN KEY'
                  AND tc.table_name = 'auth_refresh_token'
                  AND kcu.column_name = 'user_id'
                """
            )
        )
        referenced_tables = {row[0] for row in result.fetchall()}
    else:
        result = await async_session.execute(text("PRAGMA foreign_key_list(auth_refresh_token)"))
        referenced_tables = {row[2] for row in result.fetchall()}

    assert "app_user" in referenced_tables
