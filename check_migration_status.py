#!/usr/bin/env python3
"""
检查数据库迁移状态
"""

import asyncio
import os
import sys

from dotenv import load_dotenv

# 添加backend路径到sys.path
backend_path = os.path.join(os.path.dirname(__file__), "backend")
sys.path.insert(0, backend_path)
os.environ["PYTHONPATH"] = backend_path

# 加载环境变量
env_path = os.path.join(backend_path, ".env")
load_dotenv(env_path)


async def check_migration_status():
    """检查迁移状态"""
    try:
        from app.core.database import async_engine
        from sqlalchemy import text

        print("=== 检查Alembic迁移状态 ===")

        # 检查alembic_version表是否存在
        async with async_engine.begin() as conn:
            result = await conn.execute(
                text(
                    "SELECT table_name FROM information_schema.tables WHERE table_name = 'alembic_version'"
                )
            )
            alembic_exists = result.fetchone() is not None

        print(f"Alembic版本表存在: {alembic_exists}")

        if alembic_exists:
            # 获取当前版本
            async with async_engine.begin() as conn:
                result = await conn.execute(
                    text("SELECT version_num FROM alembic_version")
                )
                current_version = result.scalar()
            print(f"当前迁移版本: {current_version}")
        else:
            print("Alembic版本表不存在 - 需要初始化Alembic")

        # 检查迁移文件
        migrations_dir = os.path.join(backend_path, "alembic", "versions")
        if os.path.exists(migrations_dir):
            migration_files = [
                f for f in os.listdir(migrations_dir) if f.endswith(".py")
            ]
            print(f"\n可用的迁移文件数量: {len(migration_files)}")

            for migration_file in sorted(migration_files):
                print(f"- {migration_file}")

            # 检查我们新创建的迁移文件
            new_migration = "20250804_2300_001_create_new_members_table.py"
            new_migration_path = os.path.join(migrations_dir, new_migration)
            if os.path.exists(new_migration_path):
                print(f"\n新的members表迁移文件存在: {new_migration}")
            else:
                print(f"\n新的members表迁移文件不存在: {new_migration}")
        else:
            print("迁移目录不存在")

    except Exception as e:
        print(f"检查失败: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(check_migration_status())
