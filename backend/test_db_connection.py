#!/usr/bin/env python3
"""
测试数据库连接和迁移脚本
用于验证CI/CD环境中的数据库配置
"""

import asyncio
import os
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def test_database_connection():
    """测试数据库连接配置"""
    print("=== 数据库连接测试 ===")

    try:
        from app.core.config import settings

        print(f"数据库URL: {settings.DATABASE_URL}")
        print(f"同步数据库URL: {settings.DATABASE_URL_SYNC}")
        print(f"测试模式: {settings.TESTING}")
        print(f"调试模式: {settings.DEBUG}")
        print("[OK] 配置加载成功")
        return True
    except Exception as e:
        print(f"[FAIL] 配置加载失败: {e}")
        return False


async def test_async_connection():
    """测试异步数据库连接"""
    print("\n=== 异步数据库连接测试 ===")

    try:
        from app.core.database import async_engine

        async with async_engine.begin() as conn:
            result = await conn.execute("SELECT 1 as test")
            row = result.fetchone()
            if row and row[0] == 1:
                print("[OK] 异步数据库连接成功")
                return True
            else:
                print("[FAIL] 异步数据库连接失败: 查询结果不正确")
                return False

    except Exception as e:
        print(f"[FAIL] 异步数据库连接失败: {e}")
        return False


def test_sync_connection():
    """测试同步数据库连接"""
    print("\n=== 同步数据库连接测试 ===")

    try:
        import psycopg2
        from app.core.config import settings

        # 解析数据库URL
        db_url = settings.DATABASE_URL_SYNC
        if db_url.startswith("postgresql://"):
            # 提取连接参数
            import urllib.parse

            parsed = urllib.parse.urlparse(db_url)

            conn = psycopg2.connect(
                host=parsed.hostname,
                port=parsed.port,
                user=parsed.username,
                password=parsed.password,
                database=parsed.path[1:],  # 去掉前面的 /
            )

            with conn.cursor() as cursor:
                cursor.execute("SELECT 1 as test")
                result = cursor.fetchone()
                if result and result[0] == 1:
                    print("[OK] 同步数据库连接成功")
                    conn.close()
                    return True
                else:
                    print("[FAIL] 同步数据库连接失败: 查询结果不正确")
                    conn.close()
                    return False

    except Exception as e:
        print(f"[FAIL] 同步数据库连接失败: {e}")
        return False


async def test_table_creation():
    """测试数据库表创建"""
    print("\n=== 数据库表创建测试 ===")

    try:
        from app.core.database import Base, async_engine

        async with async_engine.begin() as conn:
            # 创建所有表
            await conn.run_sync(Base.metadata.create_all)
            print("[OK] 数据库表创建成功")

            # 检查表是否存在
            result = await conn.execute(
                """
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_type = 'BASE TABLE'
            """
            )

            tables = [row[0] for row in result.fetchall()]
            print(f"[INFO] 创建的表: {', '.join(tables)}")

            # 检查关键表是否存在
            expected_tables = ["members", "repair_tasks", "attendance_records"]
            missing_tables = [t for t in expected_tables if t not in tables]

            if missing_tables:
                print(f"[WARN] 缺少关键表: {', '.join(missing_tables)}")
                return False
            else:
                print("[OK] 所有关键表都已创建")
                return True

    except Exception as e:
        print(f"[FAIL] 数据库表创建失败: {e}")
        return False


async def test_alembic_migration():
    """测试Alembic迁移"""
    print("\n=== Alembic迁移测试 ===")

    try:
        import subprocess

        # 检查Alembic配置
        alembic_ini = Path("alembic.ini")
        if not alembic_ini.exists():
            print("[FAIL] 未找到alembic.ini文件")
            return False

        print("[INFO] 找到alembic.ini配置文件")

        # 获取当前迁移状态
        try:
            result = subprocess.run(
                ["alembic", "current"], capture_output=True, text=True, timeout=30
            )
            print(f"[INFO] 当前迁移状态: {result.stdout.strip()}")
        except Exception as e:
            print(f"[WARN] 获取迁移状态失败: {e}")

        # 运行迁移
        try:
            result = subprocess.run(
                ["alembic", "upgrade", "head"],
                capture_output=True,
                text=True,
                timeout=60,
            )

            if result.returncode == 0:
                print("[OK] Alembic迁移执行成功")
                print(f"[INFO] 迁移输出: {result.stdout}")
                return True
            else:
                print(f"[FAIL] Alembic迁移失败: {result.stderr}")
                return False

        except Exception as e:
            print(f"[FAIL] Alembic迁移执行异常: {e}")
            return False

    except Exception as e:
        print(f"[FAIL] Alembic迁移测试失败: {e}")
        return False


async def main():
    """主函数"""
    print("[START] 开始数据库测试...")

    # 测试结果统计
    tests = []

    # 1. 配置加载测试
    tests.append(("配置加载", test_database_connection()))

    # 2. 异步连接测试
    tests.append(("异步连接", await test_async_connection()))

    # 3. 同步连接测试
    tests.append(("同步连接", test_sync_connection()))

    # 4. Alembic迁移测试
    tests.append(("Alembic迁移", await test_alembic_migration()))

    # 5. 表创建测试 (如果Alembic失败的话)
    if not tests[-1][1]:  # 如果Alembic迁移失败
        print("\n[WARN] Alembic迁移失败，尝试直接创建表...")
        tests.append(("表创建", await test_table_creation()))

    # 统计结果
    print("\n" + "=" * 50)
    print("[RESULT] 测试结果汇总")
    print("=" * 50)

    passed = 0
    total = len(tests)

    for test_name, result in tests:
        status = "[OK] 通过" if result else "[FAIL] 失败"
        print(f"{test_name}: {status}")
        if result:
            passed += 1

    print(f"\n[STATS] 总体结果: {passed}/{total} 测试通过")
    success_rate = (passed / total) * 100
    print(f"[RATE] 成功率: {success_rate:.1f}%")

    if success_rate >= 80:
        print("[SUCCESS] 数据库环境测试通过！")
        return 0
    else:
        print("[ERROR] 数据库环境测试失败，请检查配置")
        return 1


if __name__ == "__main__":
    # 设置环境变量
    os.environ.setdefault("TESTING", "true")
    os.environ.setdefault("DEBUG", "false")

    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n[STOP] 测试被用户中断")
        sys.exit(130)
    except Exception as e:
        print(f"\n[CRASH] 测试过程中发生未预期错误: {e}")
        sys.exit(1)
