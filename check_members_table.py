#!/usr/bin/env python3
"""
检查members表结构
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


async def check_table_structure():
    """检查表结构"""
    try:
        from app.core.database import async_engine
        from sqlalchemy import text

        print("=== 检查Members表结构 ===")

        # 检查表是否存在
        async with async_engine.begin() as conn:
            result = await conn.execute(
                text(
                    "SELECT table_name FROM information_schema.tables WHERE table_name = 'members'"
                )
            )
            table_exists = result.fetchone() is not None

        print(f"Members表存在: {table_exists}")

        if table_exists:
            # 检查所有列
            async with async_engine.begin() as conn:
                result = await conn.execute(
                    text(
                        """
                    SELECT column_name, data_type, is_nullable, column_default
                    FROM information_schema.columns
                    WHERE table_name = 'members'
                    ORDER BY ordinal_position
                """
                    )
                )
                columns = result.fetchall()

            print("\n表结构:")
            print("列名".ljust(20) + "类型".ljust(15) + "可空".ljust(8) + "默认值")
            print("-" * 70)
            for col in columns:
                column_name, data_type, is_nullable, column_default = col
                default_display = str(column_default)[:30] if column_default else "NULL"
                print(
                    f"{column_name.ljust(20)}{data_type.ljust(15)}{is_nullable.ljust(8)}{default_display}"
                )

            # 检查索引
            async with async_engine.begin() as conn:
                result = await conn.execute(
                    text(
                        """
                    SELECT indexname, indexdef
                    FROM pg_indexes
                    WHERE tablename = 'members'
                """
                    )
                )
                indexes = result.fetchall()

            print("\n索引:")
            for idx in indexes:
                print(f"- {idx[0]}: {idx[1]}")

            # 检查约束
            async with async_engine.begin() as conn:
                result = await conn.execute(
                    text(
                        """
                    SELECT constraint_name, constraint_type
                    FROM information_schema.table_constraints
                    WHERE table_name = 'members'
                """
                    )
                )
                constraints = result.fetchall()

            print("\n约束:")
            for constraint in constraints:
                print(f"- {constraint[0]}: {constraint[1]}")

            # 检查数据
            async with async_engine.begin() as conn:
                result = await conn.execute(text("SELECT COUNT(*) FROM members"))
                count = result.scalar()

            print(f"\n数据行数: {count}")

            if count > 0:
                # 显示前几行数据（如果有列的话）
                try:
                    async with async_engine.begin() as conn:
                        result = await conn.execute(
                            text("SELECT * FROM members LIMIT 3")
                        )
                        rows = result.fetchall()

                    print("\n前3行数据:")
                    for i, row in enumerate(rows, 1):
                        print(f"行{i}: {dict(row._mapping)}")

                except Exception as e:
                    print(f"获取数据失败: {e}")

        else:
            print("Members表不存在")

            # 检查迁移状态
            async with async_engine.begin() as conn:
                result = await conn.execute(
                    text(
                        "SELECT table_name FROM information_schema.tables WHERE table_name = 'alembic_version'"
                    )
                )
                alembic_exists = result.fetchone() is not None

            print(f"Alembic版本表存在: {alembic_exists}")

            if alembic_exists:
                async with async_engine.begin() as conn:
                    result = await conn.execute(
                        text("SELECT version_num FROM alembic_version")
                    )
                    version = result.scalar()
                print(f"当前迁移版本: {version}")

    except Exception as e:
        print(f"检查失败: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(check_table_structure())
