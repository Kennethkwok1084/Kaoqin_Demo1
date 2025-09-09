"""
通用测试fixtures
提供稳定的测试数据，避免外键约束和数据依赖问题
"""

import uuid
from datetime import datetime, date, timedelta
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.member import Member, UserRole
from app.models.task import RepairTask, TaskType, TaskStatus, TaskCategory, TaskPriority
from app.models.attendance import AttendanceRecord


@pytest.fixture
async def test_member(db_session: AsyncSession):
    """创建测试用户"""
    member = Member(
        student_id=f"TEST{uuid.uuid4().hex[:8].upper()}",
        name="测试用户",
        email=f"test{uuid.uuid4().hex[:8]}@example.com",
        phone="13800138000",
        role=UserRole.MEMBER,
        is_active=True,
        hashed_password="$2b$12$test_hashed_password",
    )

    db_session.add(member)
    await db_session.commit()
    await db_session.refresh(member)

    return member


@pytest.fixture
async def test_admin(db_session: AsyncSession):
    """创建测试管理员"""
    admin = Member(
        student_id=f"ADMIN{uuid.uuid4().hex[:8].upper()}",
        name="测试管理员",
        email=f"admin{uuid.uuid4().hex[:8]}@example.com",
        phone="13800138001",
        role=UserRole.ADMIN,
        is_active=True,
        hashed_password="$2b$12$test_hashed_password",
    )

    db_session.add(admin)
    await db_session.commit()
    await db_session.refresh(admin)

    return admin


@pytest.fixture
async def test_task(db_session: AsyncSession, test_member: Member):
    """创建测试任务"""
    task = RepairTask(
        task_id=f"TASK_{uuid.uuid4().hex[:8].upper()}",
        title="测试维修任务",
        description="这是一个测试任务",
        member_id=test_member.id,
        task_type=TaskType.REPAIR,
        status=TaskStatus.PENDING,
        category=TaskCategory.NETWORK,
        priority=TaskPriority.MEDIUM,
        report_time=datetime.utcnow(),
        reporter_name="测试报告人",
        reporter_contact="test@example.com",
    )

    db_session.add(task)
    await db_session.commit()
    await db_session.refresh(task)

    return task


@pytest.fixture
async def test_attendance(db_session: AsyncSession, test_member: Member):
    """创建测试考勤记录"""
    attendance = AttendanceRecord(
        member_id=test_member.id,
        date=date.today(),
        check_in_time=datetime.now().replace(hour=9, minute=0, second=0),
        check_out_time=datetime.now().replace(hour=17, minute=0, second=0),
        status="present",
        work_hours=8.0,
    )

    db_session.add(attendance)
    await db_session.commit()
    await db_session.refresh(attendance)

    return attendance


@pytest.fixture
def unique_task_id():
    """生成唯一的任务ID"""
    return f"TASK_{uuid.uuid4().hex[:8].upper()}"


@pytest.fixture
def unique_student_id():
    """生成唯一的学号"""
    return f"STU{uuid.uuid4().hex[:8].upper()}"


@pytest.fixture
def unique_email():
    """生成唯一的邮箱"""
    return f"test{uuid.uuid4().hex[:8]}@example.com"
