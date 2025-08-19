#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Database initialization script to create default admin user for testing
"""
import asyncio
import sys
from datetime import datetime
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select

from app.core.database import AsyncSessionLocal
from app.core.security import get_password_hash
from app.models.member import Member, UserRole


async def create_default_admin():
    """Create default admin user if it doesn't exist"""

    admin_data = {
        "student_id": "admin",
        "password": "admin123",
        "name": "Default Admin",
        "email": "admin@example.com",
        "role": UserRole.ADMIN,
        "group_id": 1,
        "class_name": "Admin Class",
        "is_active": True,
        "is_verified": True,
    }

    async with AsyncSessionLocal() as session:
        try:
            # Check if admin user already exists
            result = await session.execute(
                select(Member).where(Member.student_id == admin_data["student_id"])
            )
            existing_user = result.scalar_one_or_none()

            if existing_user:
                print(f"[INFO] Admin user '{admin_data['student_id']}' already exists")
                print(f"[INFO] User ID: {existing_user.id}, Name: {existing_user.name}")
                return existing_user

            # Create new admin user
            admin_user = Member(
                username=admin_data["student_id"],  # 添加username字段
                name=admin_data["name"],
                student_id=admin_data["student_id"],
                group_id=admin_data["group_id"],
                class_name=admin_data["class_name"],
                email=admin_data["email"],
                password_hash=get_password_hash(admin_data["password"]),
                role=admin_data["role"],
                is_active=admin_data["is_active"],
                is_verified=admin_data["is_verified"],
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )

            session.add(admin_user)
            await session.commit()
            await session.refresh(admin_user)

            print("[SUCCESS] Created admin user:")
            print(f"  Student ID: {admin_user.student_id}")
            print(f"  Name: {admin_user.name}")
            print(f"  Role: {admin_user.role.value}")
            print(f"  Email: {admin_user.email}")
            print(f"  Password: {admin_data['password']}")

            return admin_user

        except Exception as e:
            await session.rollback()
            print(f"[ERROR] Failed to create admin user: {e}")
            raise


async def create_test_users():
    """Create additional test users for integration testing"""

    test_users = [
        {
            "student_id": "test_admin_001",
            "password": "test_password_123",
            "name": "Test Admin",
            "email": "test_admin@example.com",
            "role": UserRole.ADMIN,
            "group_id": 1,
            "class_name": "Test Class",
            "is_active": True,
            "is_verified": True,
        },
        {
            "student_id": "test_user_001",
            "password": "test_password_123",
            "name": "Test User",
            "email": "test_user@example.com",
            "role": UserRole.MEMBER,
            "group_id": 1,
            "class_name": "Test Class",
            "is_active": True,
            "is_verified": True,
        },
    ]

    async with AsyncSessionLocal() as session:
        created_users = []

        for user_data in test_users:
            try:
                # Check if user already exists
                result = await session.execute(
                    select(Member).where(Member.student_id == user_data["student_id"])
                )
                existing_user = result.scalar_one_or_none()

                if existing_user:
                    print(
                        f"[INFO] Test user '{user_data['student_id']}' already exists"
                    )
                    created_users.append(existing_user)
                    continue

                # Create new test user
                test_user = Member(
                    username=user_data["student_id"],  # 添加username字段
                    name=user_data["name"],
                    student_id=user_data["student_id"],
                    group_id=user_data["group_id"],
                    class_name=user_data["class_name"],
                    email=user_data["email"],
                    password_hash=get_password_hash(user_data["password"]),
                    role=user_data["role"],
                    is_active=user_data["is_active"],
                    is_verified=user_data["is_verified"],
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow(),
                )

                session.add(test_user)
                await session.commit()
                await session.refresh(test_user)

                print(
                    f"[SUCCESS] Created test user: {test_user.student_id} ({test_user.name})"
                )
                created_users.append(test_user)

            except Exception as e:
                await session.rollback()
                print(
                    f"[ERROR] Failed to create test user {user_data['student_id']}: {e}"
                )
                continue

        return created_users


async def main():
    """Main function"""
    print("=" * 50)
    print("Database Initialization Script")
    print("=" * 50)

    try:
        # Create default admin user
        print("\n[STEP 1] Creating default admin user...")
        admin_user = await create_default_admin()

        # Create test users
        print("\n[STEP 2] Creating test users...")
        test_users = await create_test_users()

        print("\n" + "=" * 50)
        print("Database initialization completed successfully!")
        users_count = (1 if admin_user else 0) + len(test_users)
        print(f"Created/verified {users_count} users")
        print("=" * 50)

        # Display login credentials
        print("\n[LOGIN CREDENTIALS]")
        print("Default Admin:")
        print("  Student ID: admin")
        print("  Password: admin123")
        print("\nTest Admin:")
        print("  Student ID: test_admin_001")
        print("  Password: test_password_123")
        print("=" * 50)

    except Exception as e:
        print(f"\n[ERROR] Database initialization failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
