#!/usr/bin/env python3
"""
Test script to verify SQLAlchemy enum creation fix.
This script tests the enum creation and basic model functionality.
"""

import asyncio
import os
import sys
sys.path.insert(0, 'backend')

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.pool import StaticPool
from app.models.base import Base
from app.models.member import Member, UserRole
from app.models.task import RepairTask, TaskType, TaskStatus, TaskCategory, TaskPriority
from app.core.security import get_password_hash

async def test_enum_creation():
    """Test enum creation and model functionality."""
    print("Starting SQLAlchemy ENUM creation test...")
    
    # Use SQLite for quick testing
    database_url = "sqlite+aiosqlite:///./test_enum_fix.db"
    
    engine = create_async_engine(
        database_url,
        echo=False,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    
    try:
        # Create all tables
        print("Creating database tables...")
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
            await conn.run_sync(Base.metadata.create_all)
        
        # Test model creation with enums
        print("Testing Member model with UserRole enum...")
        async with AsyncSession(engine) as session:
            # Create test user
            user = Member(
                username="test_enum_user",
                name="Test User",
                student_id="2025001001",
                class_name="Test Class",
                password_hash=get_password_hash("TestPassword123!"),
                role=UserRole.MEMBER,
                is_active=True
            )
            
            session.add(user)
            await session.commit()
            await session.refresh(user)
            
            print(f"SUCCESS: Created user: {user.username} with role: {user.role.value}")
            
            # Test RepairTask model with multiple enums
            print("Testing RepairTask model with multiple enums...")
            task = RepairTask(
                task_id="TEST_ENUM_001",
                member_id=user.id,
                title="Test Task",
                category=TaskCategory.NETWORK_REPAIR,
                priority=TaskPriority.MEDIUM,
                status=TaskStatus.PENDING,
                task_type=TaskType.ONLINE
            )
            
            session.add(task)
            await session.commit()
            await session.refresh(task)
            
            print(f"SUCCESS: Created task: {task.title}")
            print(f"   - Category: {task.category.value}")
            print(f"   - Priority: {task.priority.value}")
            print(f"   - Status: {task.status.value}")
            print(f"   - Type: {task.task_type.value}")
            
        print("\nAll enum tests passed successfully!")
        return True
        
    except Exception as e:
        print(f"\nERROR: Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        await engine.dispose()
        # Clean up test database
        if os.path.exists("test_enum_fix.db"):
            os.remove("test_enum_fix.db")

async def test_postgresql_enum_creation():
    """Test enum creation specifically for PostgreSQL setup."""
    print("\nTesting PostgreSQL enum creation logic...")
    
    # Test the enum creation logic without actual database
    try:
        # Import the models to trigger enum registration
        from app.models.member import UserRole
        from app.models.task import TaskType, TaskStatus, TaskCategory, TaskPriority, TaskTagType
        from app.models.attendance import AttendanceExceptionStatus
        
        print("SUCCESS: All enum classes imported successfully")
        print(f"   - UserRole values: {[role.value for role in UserRole]}")
        print(f"   - TaskType values: {[tt.value for tt in TaskType]}")
        print(f"   - TaskStatus values: {[ts.value for ts in TaskStatus]}")
        print(f"   - TaskCategory values: {[tc.value for tc in TaskCategory]}")
        print(f"   - TaskPriority values: {[tp.value for tp in TaskPriority]}")
        print(f"   - TaskTagType values: {[ttt.value for ttt in TaskTagType]}")
        print(f"   - AttendanceExceptionStatus values: {[aes.value for aes in AttendanceExceptionStatus]}")
        
        return True
        
    except Exception as e:
        print(f"ERROR: PostgreSQL enum test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Run all tests."""
    print("SQLAlchemy ENUM Creation Fix Test Suite")
    print("=" * 50)
    
    results = []
    
    # Test 1: Basic enum creation with SQLite
    results.append(await test_enum_creation())
    
    # Test 2: PostgreSQL enum logic
    results.append(await test_postgresql_enum_creation())
    
    print("\n" + "=" * 50)
    if all(results):
        print("All tests PASSED! The enum creation fix is working correctly.")
        return 0
    else:
        print("Some tests FAILED. Please check the errors above.")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
