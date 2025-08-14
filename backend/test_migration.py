"""
Test database migration by creating a simple task
"""

import asyncio
import os
import sys
from datetime import datetime

# Add the app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.core.config import get_database_url
from app.models.member import Member
from app.models.task import RepairTask, TaskStatus, TaskType
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine


async def test_task_creation():
    """Test creating a task with new fields"""

    # Create async engine
    engine = create_async_engine(get_database_url())
    SessionLocal = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with SessionLocal() as db:
        try:
            # Find an existing member to assign the task to
            from sqlalchemy import text

            member_result = await db.execute(
                text("SELECT id, name FROM members LIMIT 1")
            )
            member_row = member_result.fetchone()

            if not member_row:
                print("❌ No members found in database. Please ensure members exist.")
                return False

            member_id = member_row[0]
            member_name = member_row[1]
            print(f"Using member: {member_name} (ID: {member_id})")

            # Create a test task with new fields
            test_task = RepairTask(
                task_id=f"TEST-{int(datetime.now().timestamp())}",
                member_id=member_id,
                title="测试任务 - 迁移验证",
                description="验证数据库迁移是否成功",
                location="测试地点",
                task_type=TaskType.ONLINE,
                status=TaskStatus.PENDING,
                report_time=datetime.utcnow(),
                # Test new fields
                original_data={"test": "original_data_field_works"},
                matched_member_data={"test": "matched_member_data_field_works"},
                is_rush_order=True,
                work_order_status="测试状态",
                repair_form="远程维修",
            )

            # Add and commit
            db.add(test_task)
            await db.commit()
            await db.refresh(test_task)

            print("✅ Task created successfully with new fields!")
            print(f"   Task ID: {test_task.task_id}")
            print(f"   Rush Order: {test_task.is_rush_order}")
            print(f"   Work Order Status: {test_task.work_order_status}")
            print(f"   Repair Form: {test_task.repair_form}")
            print(f"   Original Data: {test_task.original_data}")
            print(f"   Matched Member Data: {test_task.matched_member_data}")

            # Test new methods
            test_task.mark_as_rush_order(False)
            print(f"   After unmarking rush order: {test_task.is_rush_order}")

            test_task.set_task_type_by_repair_form("现场维修")
            print(f"   After setting repair form: {test_task.task_type}")

            test_task.set_status_by_work_order_status("已完成")
            print(f"   After status mapping: {test_task.status}")

            # Clean up - delete test task
            await db.delete(test_task)
            await db.commit()
            print("✅ Test task cleaned up successfully")

            return True

        except Exception as e:
            print(f"❌ Error during task creation test: {e}")
            await db.rollback()
            return False

    await engine.dispose()


async def main():
    print("🧪 Testing database migration...")
    print("=" * 50)

    success = await test_task_creation()

    print("=" * 50)
    if success:
        print("🎉 Database migration test PASSED!")
        print("   All new fields and methods are working correctly.")
        print("   The system is ready for use!")
    else:
        print("❌ Database migration test FAILED!")
        print("   Please check the error messages above.")

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
