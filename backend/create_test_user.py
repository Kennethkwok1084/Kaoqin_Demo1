#!/usr/bin/env python3
"""
创建测试用户脚本
"""

import asyncio
import asyncpg
from passlib.context import CryptContext

# 密码加密上下文
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

async def create_test_user():
    """创建测试用户"""
    print("=== 创建测试用户 ===")

    try:
        # 连接到本地数据库
        conn = await asyncpg.connect(
            host="192.168.31.124",
            port=5432,
            user="kwok",
            password="Onjuju1084",
            database="attendence_dev",
        )

        # 检查表是否存在
        tables_exist = await conn.fetchval("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_schema = 'public'
                AND table_name = 'members'
            )
        """)

        if not tables_exist:
            print("Members表不存在，创建基础表结构...")

            # 创建用户角色枚举
            await conn.execute("""
                DO $$ BEGIN
                    CREATE TYPE user_role AS ENUM ('ADMIN', 'GROUP_LEADER', 'MEMBER');
                EXCEPTION
                    WHEN duplicate_object THEN null;
                END $$;
            """)

            # 创建members表
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS members (
                    id SERIAL PRIMARY KEY,
                    username VARCHAR(50) UNIQUE NOT NULL,
                    name VARCHAR(50) NOT NULL,
                    student_id VARCHAR(20) UNIQUE NOT NULL,
                    phone VARCHAR(20),
                    email VARCHAR(100),
                    department VARCHAR(100),
                    class_name VARCHAR(50),
                    password_hash VARCHAR(255) NOT NULL,
                    role user_role DEFAULT 'MEMBER',
                    group_id INTEGER,
                    is_active BOOLEAN DEFAULT true,
                    profile_completed BOOLEAN DEFAULT false,
                    is_verified BOOLEAN DEFAULT false,
                    last_login TIMESTAMP,
                    login_count INTEGER DEFAULT 0,
                    join_date DATE DEFAULT CURRENT_DATE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            print("✅ Members表创建成功")

        # 创建测试用户
        users_to_create = [
            {
                'username': 'admin',
                'name': '系统管理员',
                'student_id': 'ADMIN001',
                'password': 'admin123',
                'role': 'ADMIN',
                'phone': '13800138000',
                'email': 'admin@test.com'
            },
            {
                'username': 'testuser',
                'name': '测试用户',
                'student_id': 'STU001',
                'password': 'test123',
                'role': 'MEMBER',
                'phone': '13900139000',
                'email': 'test@test.com'
            },
            {
                'username': 'leader',
                'name': '组长',
                'student_id': 'LEADER001',
                'password': 'leader123',
                'role': 'GROUP_LEADER',
                'phone': '13700137000',
                'email': 'leader@test.com'
            }
        ]

        for user_data in users_to_create:
            # 检查用户是否已存在
            existing = await conn.fetchval(
                "SELECT id FROM members WHERE student_id = $1",
                user_data['student_id']
            )

            if existing:
                print(f"用户 {user_data['name']} ({user_data['student_id']}) 已存在，跳过")
                continue

            # 加密密码
            hashed_password = pwd_context.hash(user_data['password'])

            # 插入用户
            await conn.execute("""
                INSERT INTO members (
                    username, name, student_id, phone, email, password_hash,
                    role, is_active, profile_completed, is_verified
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
            """,
                user_data['username'],
                user_data['name'],
                user_data['student_id'],
                user_data['phone'],
                user_data['email'],
                hashed_password,
                user_data['role'],
                True,
                True,
                True
            )

            print(f"✅ 创建用户: {user_data['name']} ({user_data['student_id']}) - 密码: {user_data['password']}")

        # 验证创建的用户
        users = await conn.fetch("SELECT student_id, name, role FROM members ORDER BY id")
        print(f"\n📋 当前用户列表 ({len(users)}个):")
        for user in users:
            print(f"  - {user['student_id']}: {user['name']} ({user['role']})")

        await conn.close()
        print("\n🎉 测试用户创建完成！")

        print("\n🔑 登录信息:")
        print("管理员: student_id=ADMIN001, password=admin123")
        print("测试用户: student_id=STU001, password=test123")
        print("组长: student_id=LEADER001, password=leader123")

        return True

    except Exception as e:
        print(f"❌ 创建用户失败: {e}")
        return False

if __name__ == "__main__":
    asyncio.run(create_test_user())