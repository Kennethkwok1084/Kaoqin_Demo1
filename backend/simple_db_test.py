#!/usr/bin/env python3
"""
简单数据库连接测试
"""
import os
import sys

# 设置默认环境变量（如果未设置）
# 检查是否在CI环境中
if os.getenv("CI") or os.getenv("GITHUB_ACTIONS"):
    # CI环境：使用本地PostgreSQL服务
    # 注意：这里不覆盖已经设置的环境变量
    if "DATABASE_URL" not in os.environ:
        os.environ["DATABASE_URL"] = (
            "postgresql+asyncpg://postgres:postgres@localhost:5432/test_attendence"
        )
    if "DATABASE_URL_SYNC" not in os.environ:
        os.environ["DATABASE_URL_SYNC"] = (
            "postgresql://postgres:postgres@localhost:5432/test_attendence"
        )
    # 确保CI环境标记
    os.environ["CI"] = "true"
    os.environ["GITHUB_ACTIONS"] = "true"
else:
    # 本地开发环境：使用外部数据库
    if "DATABASE_URL" not in os.environ:
        os.environ["DATABASE_URL"] = (
            "postgresql+asyncpg://kwok:Onjuju1084@192.168.31.124:5432/attendence_dev"
        )
    if "DATABASE_URL_SYNC" not in os.environ:
        os.environ["DATABASE_URL_SYNC"] = (
            "postgresql://kwok:Onjuju1084@192.168.31.124:5432/attendence_dev"
        )

os.environ["TESTING"] = "true"


def test_psycopg2_connection():
    """测试psycopg2连接"""
    try:
        from urllib.parse import urlparse

        import psycopg2

        print("尝试使用psycopg2连接数据库...")

        # 检查环境信息
        print(f"CI环境变量: {os.getenv('CI')}")
        print(f"GITHUB_ACTIONS环境变量: {os.getenv('GITHUB_ACTIONS')}")

        # 从环境变量解析数据库连接信息
        db_url = os.environ.get("DATABASE_URL_SYNC")
        if not db_url:
            raise ValueError("DATABASE_URL_SYNC环境变量未设置")

        print(f"使用数据库URL: {db_url}")
        parsed = urlparse(db_url)

        print(f"连接到数据库: {parsed.hostname}:{parsed.port}/{parsed.path[1:]}")
        print(f"用户名: {parsed.username}")

        conn = psycopg2.connect(
            host=parsed.hostname,
            port=parsed.port or 5432,
            user=parsed.username,
            password=parsed.password,
            database=parsed.path[1:],  # 移除开头的 '/'
            connect_timeout=10,
        )

        cursor = conn.cursor()
        cursor.execute("SELECT version()")
        version = cursor.fetchone()
        print(f"PostgreSQL版本: {version[0]}")

        cursor.execute("SELECT current_database()")
        db_name = cursor.fetchone()
        print(f"当前数据库: {db_name[0]}")

        cursor.close()
        conn.close()

        print("[OK] psycopg2连接成功")
        return True

    except Exception as e:
        print(f"[FAIL] psycopg2连接失败: {e}")
        print(f"错误类型: {type(e).__name__}")
        import traceback

        traceback.print_exc()
        return False


def test_basic_config():
    """测试基础配置"""
    try:
        # 添加路径
        sys.path.insert(0, ".")

        from app.core.config import settings

        print(f"数据库URL: {settings.DATABASE_URL}")
        print(f"测试模式: {settings.TESTING}")
        print("[OK] 配置加载成功")
        return True
    except Exception as e:
        print(f"[FAIL] 配置加载失败: {e}")
        return False


if __name__ == "__main__":
    print("=== 简单数据库连接测试 ===")

    # 测试配置加载
    config_ok = test_basic_config()

    # 测试数据库连接
    db_ok = test_psycopg2_connection()

    if config_ok and db_ok:
        print("\n[SUCCESS] 基础连接测试通过")
        sys.exit(0)
    else:
        print("\n[ERROR] 基础连接测试失败")
        sys.exit(1)
