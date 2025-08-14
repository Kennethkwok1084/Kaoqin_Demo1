#!/usr/bin/env python3
"""
数据库基础连接测试
测试数据库迁移和基本连接功能
"""

import asyncio
import os
import sys
from datetime import date, datetime

# 添加backend路径到sys.path
backend_path = os.path.join(os.path.dirname(__file__), "backend")
sys.path.insert(0, backend_path)
os.environ["PYTHONPATH"] = backend_path


def print_test_result(test_name: str, success: bool, message: str = ""):
    """打印测试结果"""
    status = "PASS" if success else "FAIL"
    status_symbol = "[PASS]" if success else "[FAIL]"
    print(f"{status_symbol} {test_name}: {status}")
    if message:
        print(f"  详情: {message}")


def test_env_loading():
    """测试环境变量加载"""
    print("\n=== 环境变量测试 ===")

    try:
        from dotenv import load_dotenv

        # 显式加载.env文件
        env_path = os.path.join(backend_path, ".env")
        if os.path.exists(env_path):
            load_dotenv(env_path)
            print_test_result("环境文件存在", True, f"找到环境文件: {env_path}")
        else:
            print_test_result("环境文件存在", False, f"未找到环境文件: {env_path}")
            return False

        # 检查关键环境变量
        db_url = os.getenv("DATABASE_URL")
        db_url_sync = os.getenv("DATABASE_URL_SYNC")

        print_test_result("DATABASE_URL", db_url is not None, f"DATABASE_URL: {db_url}")
        print_test_result(
            "DATABASE_URL_SYNC",
            db_url_sync is not None,
            f"DATABASE_URL_SYNC: {db_url_sync}",
        )

        return db_url is not None and db_url_sync is not None

    except Exception as e:
        print_test_result("环境变量测试", False, f"测试失败: {str(e)}")
        return False


def test_settings_loading():
    """测试配置加载"""
    print("\n=== 配置加载测试 ===")

    try:
        # 先加载环境变量
        from dotenv import load_dotenv

        env_path = os.path.join(backend_path, ".env")
        load_dotenv(env_path)

        from app.core.config import Settings

        # 创建设置实例
        settings = Settings()

        print_test_result("配置对象创建", True, "Settings对象创建成功")

        # 检查数据库URL
        has_db_url = hasattr(settings, "DATABASE_URL") and settings.DATABASE_URL
        has_db_url_sync = (
            hasattr(settings, "DATABASE_URL_SYNC") and settings.DATABASE_URL_SYNC
        )

        print_test_result(
            "数据库URL配置",
            has_db_url,
            f"DATABASE_URL: {getattr(settings, 'DATABASE_URL', 'None')}",
        )
        print_test_result(
            "同步数据库URL配置",
            has_db_url_sync,
            f"DATABASE_URL_SYNC: {getattr(settings, 'DATABASE_URL_SYNC', 'None')}",
        )

        return has_db_url and has_db_url_sync

    except Exception as e:
        print_test_result("配置加载测试", False, f"测试失败: {str(e)}")
        return False


def test_database_engine():
    """测试数据库引擎创建"""
    print("\n=== 数据库引擎测试 ===")

    try:
        # 先加载环境变量
        from dotenv import load_dotenv

        env_path = os.path.join(backend_path, ".env")
        load_dotenv(env_path)

        from app.core.database import (
            AsyncSessionLocal,
            SessionLocal,
            async_engine,
            sync_engine,
        )

        print_test_result(
            "异步数据库引擎创建", async_engine is not None, "异步数据库引擎对象创建成功"
        )
        print_test_result(
            "同步数据库引擎创建", sync_engine is not None, "同步数据库引擎对象创建成功"
        )
        print_test_result(
            "异步会话工厂创建",
            AsyncSessionLocal is not None,
            "异步数据库会话工厂创建成功",
        )
        print_test_result(
            "同步会话工厂创建", SessionLocal is not None, "同步数据库会话工厂创建成功"
        )

        return True

    except Exception as e:
        print_test_result("数据库引擎测试", False, f"测试失败: {str(e)}")
        return False


async def test_database_connection():
    """测试数据库连接"""
    print("\n=== 数据库连接测试 ===")

    try:
        # 先加载环境变量
        from dotenv import load_dotenv

        env_path = os.path.join(backend_path, ".env")
        load_dotenv(env_path)

        from app.core.database import async_engine
        from sqlalchemy import text

        # 测试异步连接
        async with async_engine.begin() as conn:
            result = await conn.execute(text("SELECT 1 as test"))
            test_value = result.scalar()

        print_test_result("数据库连接", test_value == 1, "数据库连接成功")
        return True

    except Exception as e:
        print_test_result("数据库连接测试", False, f"连接失败: {str(e)}")
        return False


async def test_members_table():
    """测试members表"""
    print("\n=== Members表测试 ===")

    try:
        # 先加载环境变量
        from dotenv import load_dotenv

        env_path = os.path.join(backend_path, ".env")
        load_dotenv(env_path)

        from app.core.database import async_engine
        from sqlalchemy import text

        # 检查表是否存在
        async with async_engine.begin() as conn:
            result = await conn.execute(
                text(
                    "SELECT table_name FROM information_schema.tables WHERE table_name = 'members'"
                )
            )
            table_exists = result.fetchone() is not None

        print_test_result(
            "Members表存在",
            table_exists,
            "members表存在于数据库中" if table_exists else "members表不存在",
        )

        if table_exists:
            # 检查表结构
            async with async_engine.begin() as conn:
                result = await conn.execute(
                    text(
                        "SELECT column_name FROM information_schema.columns WHERE table_name = 'members'"
                    )
                )
                columns = [row[0] for row in result.fetchall()]

            expected_columns = [
                "id",
                "username",
                "name",
                "student_id",
                "phone",
                "department",
                "class_name",
                "role",
            ]
            has_key_columns = all(col in columns for col in expected_columns)

            print_test_result(
                "表结构检查", has_key_columns, f"关键字段存在: {has_key_columns}"
            )

            # 检查是否有默认admin用户
            async with async_engine.begin() as conn:
                result = await conn.execute(
                    text("SELECT COUNT(*) FROM members WHERE username = 'admin'")
                )
                admin_count = result.scalar()

            print_test_result(
                "默认admin用户", admin_count > 0, f"admin用户数量: {admin_count}"
            )

        return table_exists

    except Exception as e:
        print_test_result("Members表测试", False, f"测试失败: {str(e)}")
        return False


async def run_database_tests():
    """运行所有数据库测试"""
    print("=" * 60)
    print("  数据库基础连接测试")
    print("=" * 60)

    test_results = []

    # 同步测试
    test_results.append(("环境变量", test_env_loading()))
    test_results.append(("配置加载", test_settings_loading()))
    test_results.append(("数据库引擎", test_database_engine()))

    # 异步测试
    try:
        test_results.append(("数据库连接", await test_database_connection()))
        test_results.append(("Members表", await test_members_table()))
    except Exception as e:
        print_test_result("异步测试", False, f"异步测试失败: {str(e)}")
        test_results.append(("数据库连接", False))
        test_results.append(("Members表", False))

    # 汇总结果
    print("\n=== 测试结果汇总 ===")
    passed = sum(1 for _, result in test_results if result)
    total = len(test_results)

    for test_name, result in test_results:
        status = "PASS" if result else "FAIL"
        status_symbol = "[PASS]" if result else "[FAIL]"
        print(f"{status_symbol} {test_name}: {status}")

    print(f"\n总计: {passed}/{total} 项测试通过")

    if passed == total:
        print("\n[SUCCESS] 所有数据库测试通过！")
        return True
    else:
        print(f"\n[WARNING] {total - passed} 项测试失败")
        return False


if __name__ == "__main__":
    try:
        success = asyncio.run(run_database_tests())
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n测试过程中发生错误: {str(e)}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
