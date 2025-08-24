"""
测试数据库配置
实现SQLite/PostgreSQL双数据库测试策略
"""

import asyncio

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.pool import StaticPool
from sqlalchemy import text

import app.models  # noqa: F401
import app.models.attendance  # noqa: F401

# Import all models to ensure they are registered with Base metadata
# Import in correct order to avoid forward reference issues
import app.models.base  # noqa: F401
import app.models.member  # noqa: F401
import app.models.task  # noqa: F401
from app.core.database_compatibility import (
    DatabaseCompatibilityChecker,
    DatabaseType,
    get_test_database_url,
    should_use_postgresql_tests,
)
from app.models.base import Base


class DatabaseTestConfig:
    """数据库测试配置管理器"""

    def __init__(self):
        self.test_database_url = get_test_database_url()
        self.use_postgresql = should_use_postgresql_tests()

    async def create_test_engine(self):
        """创建测试数据库引擎"""
        if self.use_postgresql:
            # PostgreSQL配置
            engine = create_async_engine(
                self.test_database_url,
                echo=False,
                pool_pre_ping=True,
                pool_recycle=3600,
            )
        else:
            # SQLite配置
            engine = create_async_engine(
                self.test_database_url,
                echo=False,
                connect_args={
                    "check_same_thread": False,
                },
                poolclass=StaticPool,
            )
        return engine

    async def setup_test_database(self, engine):
        """设置测试数据库"""
        async with engine.begin() as conn:
            # 删除所有表
            await conn.run_sync(Base.metadata.drop_all)
            # 创建所有表
            await conn.run_sync(Base.metadata.create_all)



# 全局测试配置
test_config = DatabaseTestConfig()


@pytest.fixture(scope="session")
def event_loop():
    """创建事件循环"""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def test_engine():
    """测试数据库引擎fixture"""
    engine = await test_config.create_test_engine()
    yield engine
    await engine.dispose()


@pytest.fixture(scope="session")
async def setup_database(test_engine):
    """设置测试数据库fixture"""
    await test_config.setup_test_database(test_engine)
    yield
    # 测试结束后清理
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def db_session(test_engine, setup_database):
    """数据库会话fixture"""
    async with AsyncSession(test_engine) as session:
        try:
            yield session
        finally:
            await session.rollback()


@pytest.fixture
async def db_compatibility_checker(db_session):
    """数据库兼容性检查器fixture"""
    return DatabaseCompatibilityChecker(db_session)


# PostgreSQL专属测试标记
postgresql_only = pytest.mark.skipif(
    not should_use_postgresql_tests(), reason="PostgreSQL-specific test"
)

# SQLite专属测试标记
sqlite_only = pytest.mark.skipif(
    should_use_postgresql_tests(), reason="SQLite-specific test"
)

# 数据库无关测试标记
database_agnostic = pytest.mark.parametrize(
    "db_type", [DatabaseType.SQLITE, DatabaseType.POSTGRESQL], indirect=True
)
