"""Debug test for database session isolation."""

import asyncio

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.pool import StaticPool

from app.core.security import get_password_hash
from app.models.base import Base
from app.models.member import Member, UserRole


async def debug_user_creation():
    """Debug user creation and retrieval."""
    # Create test engine
    engine = create_async_engine(
        "sqlite+aiosqlite:///./debug_test.db",
        echo=True,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    # Create and commit user
    async with AsyncSession(engine, expire_on_commit=False) as session:
        user = Member(
            username="test_user",
            name="测试用户",
            student_id="2021001001",
            group_id=1,
            class_name="计算机科学与技术2101",
            email="test@example.com",
            password_hash=get_password_hash("TestPassword123!"),
            role=UserRole.MEMBER,
            is_active=True,
            is_verified=True,
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
        print(f"Created user: {user.id}, {user.student_id}, {user.name}")

    # Try to find user in new session
    async with AsyncSession(engine, expire_on_commit=False) as new_session:
        found_user = await new_session.get(Member, user.id)
        if found_user:
            print(
                f"Found user by ID: {found_user.id}, {found_user.student_id}, {found_user.name}"
            )
        else:
            print("User not found by ID")

        # Try finding by student_id
        from sqlalchemy import select

        result = await new_session.execute(
            select(Member).where(Member.student_id == "2021001001")
        )
        found_by_student_id = result.scalar_one_or_none()
        if found_by_student_id:
            print(
                f"Found user by student_id: {found_by_student_id.id}, {found_by_student_id.student_id}, {found_by_student_id.name}"
            )
        else:
            print("User not found by student_id")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(debug_user_creation())
