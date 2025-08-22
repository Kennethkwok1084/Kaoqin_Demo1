"""
本地SQLite测试脚本 - 验证代码逻辑
"""

import asyncio
import os

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.database import Base
from app.core.security import get_password_hash
from app.models import Member

# 设置测试环境
os.environ["ENVIRONMENT"] = "test"
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///test_local.db"
os.environ["DATABASE_URL_SYNC"] = "sqlite:///test_local.db"


async def test_local_setup():
    """Test local SQLite database setup and basic operations"""
    print("=== Local SQLite Database Test ===")

    # Create async engine
    engine = create_async_engine(
        "sqlite+aiosqlite:///test_local.db", echo=False  # Reduce verbose output
    )

    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    print("[OK] Database tables created successfully")

    # 创建会话
    async_session = async_sessionmaker(engine, class_=AsyncSession)

    # Test creating user
    async with async_session() as session:
        test_user = Member(
            username="test_user",
            name="Test User",
            student_id="STU12345",
            phone="13800138000",
            department="IT Department",
            class_name="2021 Class",
            password_hash=get_password_hash("test123"),
            role="member",
            is_active=True,
            profile_completed=True,
        )

        session.add(test_user)
        await session.commit()
        await session.refresh(test_user)

        print(
            f"[OK] User created successfully: {test_user.username} (ID: {test_user.id})"
        )

    # Test querying user
    async with async_session() as session:
        from sqlalchemy import select

        result = await session.execute(
            select(Member).where(Member.student_id == "STU12345")
        )
        user = result.scalar_one_or_none()

        if user:
            print(f"[OK] User query successful: {user.name} - {user.department}")
        else:
            print("[FAIL] User query failed")

    await engine.dispose()
    print("\n[SUCCESS] Local SQLite test completed")


if __name__ == "__main__":
    asyncio.run(test_local_setup())
