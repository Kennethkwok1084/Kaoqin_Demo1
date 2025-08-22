"""
远程数据库初始化脚本 - 单连接优化
"""

import asyncio
import os

import asyncpg  # type: ignore[import-untyped]

# 设置环境变量
os.environ["ENVIRONMENT"] = "production"
os.environ["DATABASE_URL"] = (
    "postgresql+asyncpg://kwok:Onjuju1084@8.138.233.54:5432/attendence_dev"
)


async def test_basic_connection() -> bool:
    """测试基础连接 - 使用asyncpg直连"""
    print("=== Testing Basic Connection (asyncpg) ===")

    try:
        conn = await asyncpg.connect(
            host="8.138.233.54",
            port=5432,
            user="kwok",
            password="Onjuju1084",
            database="attendence_dev",
            server_settings={
                "application_name": "kaoqin_init_script",
            },
        )

        # 检查数据库版本
        version = await conn.fetchval("SELECT version()")
        print(f"[OK] Database version: {version.split(',')[0]}")

        # 检查现有表
        tables = await conn.fetch(
            """
            SELECT table_name FROM information_schema.tables
            WHERE table_schema = 'public'
            ORDER BY table_name
        """
        )
        print(f"[OK] Found {len(tables)} existing tables")

        # 检查members表是否存在
        members_exists = await conn.fetchval(
            """
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_schema = 'public'
                AND table_name = 'members'
            )
        """
        )
        print(f"[INFO] Members table exists: {members_exists}")

        await conn.close()
        return True

    except Exception as e:
        print(f"[ERROR] Connection failed: {e}")
        return False


async def create_members_table_minimal() -> bool:
    """创建最小化的members表结构"""
    print("=== Creating Minimal Members Table ===")

    try:
        conn = await asyncpg.connect(
            host="8.138.233.54",
            port=5432,
            user="kwok",
            password="Onjuju1084",
            database="attendence_dev",
        )

        # 删除现有的members表（如果存在）
        await conn.execute("DROP TABLE IF EXISTS members CASCADE")
        print("[OK] Dropped existing members table")

        # 创建新的members表
        await conn.execute(
            """
            CREATE TABLE members (
                id SERIAL PRIMARY KEY,
                username VARCHAR(50) UNIQUE NOT NULL,
                name VARCHAR(50) NOT NULL,
                student_id VARCHAR(20) UNIQUE,
                phone VARCHAR(20),
                department VARCHAR(100),
                class_name VARCHAR(50),
                password_hash VARCHAR(255) NOT NULL,
                role VARCHAR(20) DEFAULT 'MEMBER',
                is_active BOOLEAN DEFAULT true,
                profile_completed BOOLEAN DEFAULT false,
                is_verified BOOLEAN DEFAULT false,
                last_login TIMESTAMP,
                login_count INTEGER DEFAULT 0,
                join_date DATE DEFAULT CURRENT_DATE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """
        )
        print("[OK] Created members table")

        # 创建索引
        await conn.execute("CREATE INDEX idx_members_username ON members(username)")
        await conn.execute("CREATE INDEX idx_members_student_id ON members(student_id)")
        print("[OK] Created indexes")

        # 插入测试用户
        await conn.execute(
            """
            INSERT INTO members (username, name, student_id, phone, department, class_name, password_hash, role, is_active, profile_completed)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
        """,
            "testuser",
            "Test User",
            "STU12345",
            "13800138000",
            "IT Department",
            "2021 Class",
            "$2b$12$7DKis8BX0BY8vqjtylV46./D2LlSwWdV0XADOPWeyWkZPIlewARyS",
            "member",
            True,
            True,
        )
        print("[OK] Inserted test user")

        # 验证数据
        user = await conn.fetchrow(
            "SELECT username, name, student_id FROM members WHERE student_id = $1",
            "STU12345",
        )
        print(f"[OK] Test user: {user['username']} - {user['name']}")

        await conn.close()
        return True

    except Exception as e:
        print(f"[ERROR] Table creation failed: {e}")
        return False


async def main() -> bool:
    """主函数"""
    print("=== Remote Database Initialization ===")

    # 测试连接
    if not await test_basic_connection():
        return False

    # 创建表结构
    if not await create_members_table_minimal():
        return False

    print("\n[SUCCESS] Remote database initialization completed!")
    return True


if __name__ == "__main__":
    asyncio.run(main())
