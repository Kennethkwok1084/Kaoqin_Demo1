"""
简化的本地测试脚本
"""

import asyncio
import os

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

# 设置测试环境
os.environ["ENVIRONMENT"] = "test"


async def simple_test() -> None:
    """Simple test with minimal setup"""
    print("=== Simple Test ===")

    # 创建内存数据库引擎
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)

    try:
        # 测试基础连接
        async with engine.begin() as conn:
            result = await conn.execute(text("SELECT 1 as test"))
            test_value = result.fetchone()
            if test_value:
                print(f"[OK] Database connection test: {test_value[0]}")

            # 手动创建简单表
            await conn.execute(
                text(
                    """
                CREATE TABLE test_members (
                    id INTEGER PRIMARY KEY,
                    username TEXT NOT NULL,
                    name TEXT NOT NULL,
                    student_id TEXT UNIQUE
                )
            """
                )
            )
            print("[OK] Test table created")

            # 插入测试数据
            await conn.execute(
                text(
                    """
                INSERT INTO test_members (username, name, student_id)
                VALUES ('test_user', 'Test User', 'STU12345')
            """
                )
            )
            print("[OK] Test data inserted")

            # 查询测试数据
            result = await conn.execute(text("SELECT * FROM test_members"))
            user = result.fetchone()
            if user:
                print(f"[OK] Test data retrieved: {user[1]} - {user[2]}")

    except Exception as e:
        print(f"[ERROR] Test failed: {e}")
    finally:
        await engine.dispose()

    print("[SUCCESS] Simple test completed")


if __name__ == "__main__":
    asyncio.run(simple_test())
