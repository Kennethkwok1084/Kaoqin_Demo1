#!/usr/bin/env python3
"""
简单数据库连接测试
"""
import os
import sys

# 设置环境变量
os.environ["DATABASE_URL"] = (
    "postgresql+asyncpg://kwok:Onjuju1084@8.138.233.54:5432/attendence_dev"
)
os.environ["DATABASE_URL_SYNC"] = (
    "postgresql://kwok:Onjuju1084@8.138.233.54:5432/attendence_dev"
)
os.environ["TESTING"] = "true"


def test_psycopg2_connection():
    """测试psycopg2连接"""
    try:
        import psycopg2

        print("尝试使用psycopg2连接数据库...")

        conn = psycopg2.connect(
            host="8.138.233.54",
            port=5432,
            user="kwok",
            password="Onjuju1084",
            database="attendence_dev",
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
