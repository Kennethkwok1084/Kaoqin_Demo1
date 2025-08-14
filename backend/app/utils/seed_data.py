"""
Database seeding utilities.
Creates initial data for development and testing.
"""

import asyncio
import logging
from typing import List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from app.core.security import get_password_hash
from app.models.member import Member, UserRole
from app.models.task import TaskTag

logger = logging.getLogger(__name__)


async def create_default_users(db: AsyncSession) -> List[Member]:
    """Create default users for development and testing."""
    logger.info("Creating default users...")

    users_data = [
        {
            "name": "系统管理员",
            "student_id": "admin",
            "group_id": 0,
            "class_name": "管理员",
            "email": "admin@kaoqin.local",
            "password": "Admin123!",
            "role": UserRole.ADMIN,
            "is_active": True,
            "is_verified": True,
        },
        {
            "name": "组长张三",
            "student_id": "2021000001",
            "group_id": 1,
            "class_name": "计算机科学与技术2101",
            "email": "zhangsan@kaoqin.local",
            "password": "Leader123!",
            "role": UserRole.GROUP_LEADER,
            "is_active": True,
            "is_verified": True,
        },
        {
            "name": "成员李四",
            "student_id": "2021000002",
            "group_id": 1,
            "class_name": "计算机科学与技术2101",
            "email": "lisi@kaoqin.local",
            "password": "Member123!",
            "role": UserRole.MEMBER,
            "is_active": True,
            "is_verified": True,
        },
        {
            "name": "成员王五",
            "student_id": "2021000003",
            "group_id": 2,
            "class_name": "软件工程2101",
            "email": "wangwu@kaoqin.local",
            "password": "Member123!",
            "role": UserRole.MEMBER,
            "is_active": True,
            "is_verified": True,
        },
        {
            "name": "成员赵六",
            "student_id": "2021000004",
            "group_id": 2,
            "class_name": "网络工程2101",
            "email": "zhaoliu@kaoqin.local",
            "password": "Member123!",
            "role": UserRole.MEMBER,
            "is_active": True,
            "is_verified": False,  # Unverified user for testing
        },
        {
            "name": "停用用户",
            "student_id": "2021000999",
            "group_id": 1,
            "class_name": "测试班级",
            "email": "disabled@kaoqin.local",
            "password": "Disabled123!",
            "role": UserRole.MEMBER,
            "is_active": False,  # Inactive user for testing
            "is_verified": True,
        },
    ]

    created_users = []

    for user_data in users_data:
        # Check if user already exists
        result = await db.execute(
            select(Member).where(Member.student_id == user_data["student_id"])
        )
        existing_user = result.scalar_one_or_none()

        if existing_user:
            logger.info(f"User {user_data['student_id']} already exists, skipping...")
            created_users.append(existing_user)
            continue

        # Create new user
        password_hash = get_password_hash(user_data.pop("password"))
        user = Member(**user_data, password_hash=password_hash)

        db.add(user)
        created_users.append(user)
        logger.info(f"Created user: {user.name} ({user.student_id})")

    await db.commit()

    # Refresh all users to get their IDs
    for user in created_users:
        await db.refresh(user)

    logger.info(f"Created {len(created_users)} users")
    return created_users


async def create_default_task_tags(db: AsyncSession) -> List[TaskTag]:
    """Create default task tags for work hour calculation."""
    logger.info("Creating default task tags...")

    tags_data = [
        {
            "name": "爆单任务",
            "description": "管理员标记的高峰期任务，额外获得15分钟工时",
            "work_minutes_modifier": 15,
            "tag_type": "bonus",
            "is_active": True,
        },
        {
            "name": "非默认好评",
            "description": "用户主动给出的好评，额外获得30分钟工时",
            "work_minutes_modifier": 30,
            "tag_type": "bonus",
            "is_active": True,
        },
        {
            "name": "超时响应",
            "description": "响应时间超过24小时，扣除30分钟工时",
            "work_minutes_modifier": -30,
            "tag_type": "penalty",
            "is_active": True,
        },
        {
            "name": "超时处理",
            "description": "处理时间超过48小时，扣除30分钟工时",
            "work_minutes_modifier": -30,
            "tag_type": "penalty",
            "is_active": True,
        },
        {
            "name": "差评任务",
            "description": "用户给出差评，扣除60分钟工时",
            "work_minutes_modifier": -60,
            "tag_type": "penalty",
            "is_active": True,
        },
        {
            "name": "紧急任务",
            "description": "紧急任务标记，额外获得20分钟工时",
            "work_minutes_modifier": 20,
            "tag_type": "bonus",
            "is_active": True,
        },
        {
            "name": "远程协助",
            "description": "远程协助任务，获得额外10分钟工时",
            "work_minutes_modifier": 10,
            "tag_type": "category",
            "is_active": True,
        },
        {
            "name": "重复问题",
            "description": "重复出现的问题，减少5分钟工时",
            "work_minutes_modifier": -5,
            "tag_type": "penalty",
            "is_active": True,
        },
        {
            "name": "复杂问题",
            "description": "技术复杂度高的问题，额外获得25分钟工时",
            "work_minutes_modifier": 25,
            "tag_type": "bonus",
            "is_active": True,
        },
        {
            "name": "培训任务",
            "description": "新手培训相关任务，正常工时无修正",
            "work_minutes_modifier": 0,
            "tag_type": "category",
            "is_active": True,
        },
    ]

    created_tags = []

    for tag_data in tags_data:
        # Check if tag already exists
        result = await db.execute(
            select(TaskTag).where(TaskTag.name == tag_data["name"])
        )
        existing_tag = result.scalar_one_or_none()

        if existing_tag:
            logger.info(f"Tag '{tag_data['name']}' already exists, skipping...")
            created_tags.append(existing_tag)
            continue

        # Create new tag
        tag = TaskTag(**tag_data)
        db.add(tag)
        created_tags.append(tag)
        logger.info(f"Created tag: {tag.name} ({tag.work_minutes_modifier:+d} minutes)")

    await db.commit()

    # Refresh all tags to get their IDs
    for tag in created_tags:
        await db.refresh(tag)

    logger.info(f"Created {len(created_tags)} task tags")
    return created_tags


async def seed_database():
    """Main function to seed the database with initial data."""
    logger.info("Starting database seeding...")

    try:
        async with AsyncSessionLocal() as db:
            # Create default users
            users = await create_default_users(db)
            logger.info(f"✓ Created {len(users)} users")

            # Create default task tags
            tags = await create_default_task_tags(db)
            logger.info(f"✓ Created {len(tags)} task tags")

            logger.info("Database seeding completed successfully!")

            # Print summary
            print("\n" + "=" * 50)
            print("DATABASE SEEDING SUMMARY")
            print("=" * 50)
            print("\nDefault Users Created:")
            for user in users:
                print(f"  • {user.name} ({user.student_id}) - {user.role.value}")
                if user.student_id == "admin":
                    print(f"    Password: Admin123!")
                elif user.role == UserRole.GROUP_LEADER:
                    print(f"    Password: Leader123!")
                else:
                    print(f"    Password: Member123!")

            print(f"\nTask Tags Created: {len(tags)} tags")
            print("\nYou can now start the server and test the authentication API!")
            print("Try logging in with admin/Admin123! or any other user.")
            print("=" * 50)

    except Exception as e:
        logger.error(f"Database seeding failed: {str(e)}")
        raise


async def clear_database():
    """Clear all data from database (use with caution!)."""
    logger.warning("Clearing database...")

    try:
        async with AsyncSessionLocal() as db:
            # Delete all data (in reverse order of dependencies)
            await db.execute("DELETE FROM task_tag_associations")
            await db.execute("DELETE FROM attendance_records")
            await db.execute("DELETE FROM assistance_tasks")
            await db.execute("DELETE FROM monitoring_tasks")
            await db.execute("DELETE FROM repair_tasks")
            await db.execute("DELETE FROM task_tags")
            await db.execute("DELETE FROM members")
            await db.commit()

            logger.info("Database cleared successfully!")

    except Exception as e:
        logger.error(f"Database clearing failed: {str(e)}")
        raise


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "clear":
        asyncio.run(clear_database())
    else:
        asyncio.run(seed_database())
