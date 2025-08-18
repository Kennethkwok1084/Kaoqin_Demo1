"""
远程数据库迁移工具 - 使用单连接配置
"""

import asyncio
import os

from sqlalchemy.ext.asyncio import create_async_engine

from app.models import Base

# 设置环境变量
os.environ["ENVIRONMENT"] = "production"
os.environ["DATABASE_URL"] = (
    "postgresql+asyncpg://kwok:Onjuju1084@8.138.233.54:5432/attendence_dev"
)


async def run_migration():
    """使用单连接运行数据库迁移"""
    print("=== Remote Database Migration ===")

    try:
        # 创建单连接引擎
        engine = create_async_engine(
            "postgresql+asyncpg://kwok:Onjuju1084@8.138.233.54:5432/attendence_dev",
            echo=True,
            pool_size=1,  # 单连接
            max_overflow=0,  # 无额外连接
            pool_pre_ping=True,
            connect_args={"server_settings": {"application_name": "kaoqin_migration"}},
        )

        print("[INFO] Creating database connection...")

        # 删除现有表并重新创建（全新开始）
        async with engine.begin() as conn:
            print("[INFO] Dropping all existing tables...")
            await conn.run_sync(Base.metadata.drop_all)
            print("[OK] All tables dropped")

            print("[INFO] Creating new tables from models...")
            await conn.run_sync(Base.metadata.create_all)
            print("[OK] All tables created")

            # 验证表创建
            from sqlalchemy import text

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
            print(f"[OK] Created {len(tables)} tables:")
            for table in tables:
                print(f"  - {table[0]}")

        # 插入必要的初始数据
        async with engine.begin() as conn:
            from datetime import date

            from app.core.security import get_password_hash

            print("[INFO] Inserting initial data...")
            await conn.execute(
                text(
                    """
                INSERT INTO members (username, name, student_id, phone, department, class_name, join_date, password_hash, role, is_active, profile_completed, is_verified, login_count)
                VALUES (:username, :name, :student_id, :phone, :department, :class_name, :join_date, :password_hash, :role, :is_active, :profile_completed, :is_verified, :login_count)
            """
                ),
                {
                    "username": "testuser",
                    "name": "Test User",
                    "student_id": "STU12345",
                    "phone": "13800138000",
                    "department": "IT Department",
                    "class_name": "2021 Class",
                    "join_date": date(2024, 1, 1),
                    "password_hash": get_password_hash("test123"),
                    "role": "MEMBER",
                    "is_active": True,
                    "profile_completed": True,
                    "is_verified": False,
                    "login_count": 0,
                },
            )
            print("[OK] Test user created")

            await conn.execute(
                text(
                    """
                INSERT INTO members (username, name, student_id, phone, department, class_name, join_date, password_hash, role, is_active, profile_completed, is_verified, login_count)
                VALUES (:username, :name, :student_id, :phone, :department, :class_name, :join_date, :password_hash, :role, :is_active, :profile_completed, :is_verified, :login_count)
            """
                ),
                {
                    "username": "admin",
                    "name": "System Admin",
                    "student_id": "ADMIN001",
                    "phone": "13900139000",
                    "department": "Administration",
                    "class_name": "Staff",
                    "join_date": date(2023, 1, 1),
                    "password_hash": get_password_hash("admin123"),
                    "role": "ADMIN",
                    "is_active": True,
                    "profile_completed": True,
                    "is_verified": True,
                    "login_count": 0,
                },
            )
            print("[OK] Admin user created")

        # 现在标记Alembic版本
        async with engine.begin() as conn:
            # 创建alembic_version表并设置为最新版本
            await conn.execute(
                text(
                    """
                CREATE TABLE IF NOT EXISTS alembic_version (
                    version_num VARCHAR(32) NOT NULL,
                    CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num)
                )
            """
                )
            )

            # 插入最新的迁移版本
            await conn.execute(text("DELETE FROM alembic_version"))
            await conn.execute(
                text(
                    "INSERT INTO alembic_version (version_num) VALUES ('20250809_1110')"
                )
            )
            print("[OK] Alembic version marked as 20250809_1110")

        await engine.dispose()
        print("\n[SUCCESS] Remote database migration completed!")
        return True

    except Exception as e:
        print(f"[ERROR] Migration failed: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(run_migration())
    if success:
        print("\n✅ Migration successful - database is ready for CI/CD!")
    else:
        print("\n❌ Migration failed - check errors above")
