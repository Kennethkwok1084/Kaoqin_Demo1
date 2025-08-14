"""
远程数据库连接配置 - 针对低并发限制优化
"""

import logging
from typing import AsyncGenerator, Optional

from app.core.config import get_database_url, get_database_url_sync, settings
from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import Session, sessionmaker

logger = logging.getLogger(__name__)


def create_remote_optimized_engine(database_url: str, is_async: bool = True):
    """
    创建针对远程数据库优化的引擎
    - 低并发设置
    - 更长的超时时间
    - 连接重用优化
    """
    if is_async:
        return create_async_engine(
            database_url,
            echo=False,  # 关闭SQL日志减少输出
            future=True,
            pool_pre_ping=True,
            pool_size=2,  # 最小连接池 - 降低并发
            max_overflow=3,  # 最小溢出连接
            pool_recycle=1800,  # 30分钟回收连接
            connect_args={
                "server_settings": {
                    "application_name": "kaoqin_test",
                }
            },
        )
    else:
        return create_engine(
            database_url,
            echo=False,
            pool_pre_ping=True,
            pool_size=2,
            max_overflow=3,
            pool_recycle=1800,
        )


async def init_remote_database():
    """初始化远程数据库表结构"""
    print("=== Initializing Remote Database ===")

    try:
        from app.models.base import Base

        # 创建优化的引擎
        engine = create_remote_optimized_engine(get_database_url())

        # 创建所有表
        async with engine.begin() as conn:
            # 先检查数据库连接
            result = await conn.execute(text("SELECT version()"))
            version = result.fetchone()
            print(f"[OK] Connected to: {version[0]}")

            # 创建表结构
            await conn.run_sync(Base.metadata.create_all)
            print("[OK] Database tables created successfully")

            # 验证表是否存在
            result = await conn.execute(
                text(
                    """
                SELECT table_name FROM information_schema.tables 
                WHERE table_schema = 'public' 
                ORDER BY table_name
            """
                )
            )
            tables = result.fetchall()
            print(f"[OK] Found {len(tables)} tables:")
            for table in tables[:5]:  # 只显示前5个
                print(f"  - {table[0]}")

        await engine.dispose()
        print("[SUCCESS] Remote database initialization completed")
        return True

    except Exception as e:
        print(f"[ERROR] Database initialization failed: {e}")
        return False


async def test_single_connection():
    """测试单个数据库连接"""
    print("=== Testing Single Connection ===")

    try:
        # 使用最小连接参数
        engine = create_async_engine(
            get_database_url(),
            echo=False,
            pool_size=1,  # 仅使用单连接
            max_overflow=0,  # 无溢出连接
            pool_pre_ping=True,
        )

        async with engine.begin() as conn:
            # 测试基础查询
            result = await conn.execute(text("SELECT 1 as test, now() as time"))
            test_result = result.fetchone()
            print(f"[OK] Connection test: {test_result[0]}, Time: {test_result[1]}")

            # 检查members表是否存在
            result = await conn.execute(
                text(
                    """
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = 'members'
                )
            """
                )
            )
            table_exists = result.fetchone()[0]
            print(f"[OK] Members table exists: {table_exists}")

        await engine.dispose()
        return True

    except Exception as e:
        print(f"[ERROR] Connection test failed: {e}")
        return False


if __name__ == "__main__":
    import asyncio

    async def main():
        # 首先测试连接
        if await test_single_connection():
            # 然后初始化数据库
            await init_remote_database()

    asyncio.run(main())
