"""
数据库清理和设置fixtures
确保每次测试前数据库状态干净
"""

import pytest
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.core.database import async_engine, get_async_session
from app.models.base import Base


@pytest.fixture(scope="session", autouse=True)
async def setup_test_database():
    """设置测试数据库"""
    async with async_engine.begin() as conn:
        # 创建所有表
        await conn.run_sync(Base.metadata.create_all)
    
    yield
    
    # 清理
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture(autouse=True)
async def clean_database():
    """每个测试前清理数据库"""
    async with async_engine.begin() as conn:
        # 禁用外键约束
        await conn.execute(text("SET session_replication_role = replica;"))
        
        # 清理所有表数据
        for table in reversed(Base.metadata.sorted_tables):
            await conn.execute(text(f"TRUNCATE TABLE {table.name} RESTART IDENTITY CASCADE;"))
        
        # 重新启用外键约束
        await conn.execute(text("SET session_replication_role = DEFAULT;"))
        
        await conn.commit()


@pytest.fixture
async def db_session():
    """获取数据库会话"""
    async with get_async_session() as session:
        yield session


@pytest.fixture
async def clean_db_session():
    """获取干净的数据库会话（确保事务隔离）"""
    async with get_async_session() as session:
        # 开始事务
        transaction = await session.begin()
        try:
            yield session
        finally:
            # 回滚事务，确保测试不影响其他测试
            await transaction.rollback()
