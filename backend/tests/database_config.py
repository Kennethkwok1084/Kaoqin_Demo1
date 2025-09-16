"""
测试数据库配置
实现SQLite/PostgreSQL双数据库测试策略
"""

import asyncio

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

import app.models  # noqa: F401

# Import all models to ensure they are registered with Base metadata
# Import in correct order to avoid forward reference issues
import app.models.base  # noqa: F401
import app.models.member  # noqa: F401
import app.models.task  # noqa: F401
from app.core.database_compatibility import (
    DatabaseCompatibilityChecker,
    get_test_database_url,
)
from app.models.base import Base


class DatabaseTestConfig:
    """数据库测试配置管理器"""

    def __init__(self):
        self.test_database_url = get_test_database_url()

    async def create_test_engine(self):
        """创建测试数据库引擎（PostgreSQL）"""
        engine = create_async_engine(
            self.test_database_url,
            echo=False,
            pool_pre_ping=True,
            pool_recycle=300,  # 5分钟回收连接
            pool_size=5,  # 较小的连接池
            max_overflow=0,  # 不允许溢出连接
            pool_timeout=30,  # 连接超时
            connect_args={
                "server_settings": {
                    "application_name": "attendence_test",
                }
            },
        )
        return engine

    async def setup_test_database(self, engine):
        """设置测试数据库"""
        async with engine.begin() as conn:
            # 删除所有表
            await conn.run_sync(Base.metadata.drop_all)

            # 删除可能存在的ENUM类型
            enum_types = [
                "userrole",
                "taskstatus",
                "taskcategory",
                "taskpriority",
                "tasktype",
                "tasktagtype",
            ]
            for enum_type in enum_types:
                await conn.execute(text(f"DROP TYPE IF EXISTS {enum_type} CASCADE"))

            # 创建所需的ENUM类型
            await conn.execute(
                text(
                    "CREATE TYPE userrole AS ENUM ('admin','group_leader','member','guest')"
                )
            )
            await conn.execute(
                text(
                    "CREATE TYPE taskstatus AS ENUM ('pending','in_progress','completed','cancelled','on_hold')"
                )
            )
            await conn.execute(
                text(
                    "CREATE TYPE taskcategory AS ENUM ('network_repair','hardware_repair','software_support','software_issue','monitoring','assistance','other')"
                )
            )
            await conn.execute(
                text(
                    "CREATE TYPE taskpriority AS ENUM ('low','medium','high','urgent')"
                )
            )
            await conn.execute(
                text("CREATE TYPE tasktype AS ENUM ('online','offline','repair')")
            )
            await conn.execute(
                text(
                    "CREATE TYPE tasktagtype AS ENUM ('rush_order','non_default_rating','timeout_response','timeout_processing','bad_rating','bonus','penalty','category')"
                )
            )
            await conn.execute(
                text(
                    "CREATE TYPE attendanceexceptionstatus AS ENUM ('pending','approved','rejected')"
                )
            )

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
