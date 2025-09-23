#!/usr/bin/env python3
"""
直接通过后端API创建用户
"""

import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from passlib.context import CryptContext

# Import models
from app.models.member import Member, UserRole
from app.core.config import settings

# Password context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

async def create_users():
    """直接创建用户"""
    print("=== 直接创建用户 ===")

    # Use the same database URL as the application
    DATABASE_URL = "postgresql+asyncpg://kwok:Onjuju1084@192.168.31.124:5432/attendence_dev"

    engine = create_async_engine(DATABASE_URL, echo=True)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    try:
        async with async_session() as session:
            # 创建测试用户
            users_to_create = [
                {
                    'username': 'admin',
                    'name': '系统管理员',
                    'student_id': 'ADMIN001',
                    'password': 'admin123',
                    'role': UserRole.ADMIN,
                    'phone': '13800138000',
                    'email': 'admin@test.com'
                },
                {
                    'username': 'testuser',
                    'name': '测试用户',
                    'student_id': 'STU001',
                    'password': 'test123',
                    'role': UserRole.MEMBER,
                    'phone': '13900139000',
                    'email': 'test@test.com'
                }
            ]

            for user_data in users_to_create:
                # 检查用户是否已存在
                from sqlalchemy import select
                existing = await session.execute(
                    select(Member).where(Member.student_id == user_data['student_id'])
                )
                if existing.scalars().first():
                    print(f"用户 {user_data['name']} ({user_data['student_id']}) 已存在，跳过")
                    continue

                # 创建新用户
                hashed_password = pwd_context.hash(user_data['password'])

                new_user = Member(
                    username=user_data['username'],
                    name=user_data['name'],
                    student_id=user_data['student_id'],
                    phone=user_data['phone'],
                    email=user_data['email'],
                    password_hash=hashed_password,
                    role=user_data['role'],
                    is_active=True,
                    profile_completed=True,
                    is_verified=True
                )

                session.add(new_user)
                print(f"✅ 创建用户: {user_data['name']} ({user_data['student_id']}) - 密码: {user_data['password']}")

            await session.commit()

            # 验证创建的用户
            result = await session.execute(select(Member))
            users = result.scalars().all()

            print(f"\n📋 当前用户列表 ({len(users)}个):")
            for user in users:
                print(f"  - {user.student_id}: {user.name} ({user.role.value})")

        print("\n🎉 用户创建完成！")
        print("\n🔑 登录信息:")
        print("管理员: student_id=ADMIN001, password=admin123")
        print("测试用户: student_id=STU001, password=test123")

    except Exception as e:
        print(f"❌ 创建用户失败: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await engine.dispose()

if __name__ == "__main__":
    asyncio.run(create_users())