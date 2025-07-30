"""
集成测试配置文件
提供测试数据库、测试客户端和测试数据的fixture
"""

import asyncio
import os
import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

# Set testing environment before importing app
os.environ["TESTING"] = "1"
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./test_integration.db"
os.environ["DATABASE_URL_SYNC"] = "sqlite:///./test_integration.db"
os.environ["REDIS_URL"] = "redis://localhost:6379/1"

from app.main import app
from app.core.config import settings

# Override settings for testing
settings.TESTING = True
settings.DATABASE_URL = "sqlite+aiosqlite:///./test_integration.db"
settings.DATABASE_URL_SYNC = "sqlite:///./test_integration.db"
from app.core.database import get_async_session, get_sync_session
from app.models import Base, Member, UserRole
from app.core.security import get_password_hash


# 测试数据库配置
TEST_DATABASE_URL = "sqlite+aiosqlite:///./test_integration.db"
TEST_DATABASE_URL_SYNC = "sqlite:///./test_integration.db"

# 创建测试引擎
test_async_engine = create_async_engine(
    TEST_DATABASE_URL, 
    echo=False,
    future=True
)

test_sync_engine = create_engine(
    TEST_DATABASE_URL_SYNC,
    echo=False
)

TestingSessionLocal = sessionmaker(
    test_sync_engine, 
    expire_on_commit=False
)

TestingAsyncSessionLocal = sessionmaker(
    test_async_engine, 
    class_=AsyncSession, 
    expire_on_commit=False
)


@pytest.fixture(scope="session")
def event_loop():
    """创建事件循环"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session")
async def setup_test_database():
    """设置测试数据库"""
    # 创建所有表
    async with test_async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield
    
    # 清理测试数据库
    async with test_async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def db_session(setup_test_database):
    """获取异步数据库会话"""
    async with TestingAsyncSessionLocal() as session:
        yield session


@pytest.fixture
def sync_db_session(setup_test_database):
    """获取同步数据库会话"""
    with TestingSessionLocal() as session:
        yield session


async def override_get_async_session():
    """重写数据库会话依赖"""
    async with TestingAsyncSessionLocal() as session:
        yield session


def override_get_sync_session():
    """重写同步数据库会话依赖"""
    with TestingSessionLocal() as session:
        yield session


@pytest.fixture
def client(setup_test_database):
    """测试客户端"""
    # 重写依赖
    app.dependency_overrides[get_async_session] = override_get_async_session
    app.dependency_overrides[get_sync_session] = override_get_sync_session
    
    with TestClient(app) as test_client:
        yield test_client
    
    # 清理依赖重写
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def test_admin_user(db_session):
    """创建测试管理员用户"""
    import uuid
    unique_id = str(uuid.uuid4())[:8]
    
    admin_user = Member(
        name=f"测试管理员{unique_id}",
        student_id=f"admin{unique_id}",
        email=f"admin{unique_id}@test.com",
        password_hash=get_password_hash("admin123456"),
        role=UserRole.ADMIN,
        is_active=True,
        is_verified=True
    )
    
    db_session.add(admin_user)
    await db_session.commit()
    await db_session.refresh(admin_user)
    return admin_user


@pytest_asyncio.fixture
async def test_member_user(db_session):
    """创建测试普通成员"""
    import uuid
    unique_id = str(uuid.uuid4())[:8]
    
    member_user = Member(
        name=f"测试成员{unique_id}",
        student_id=f"member{unique_id}",
        email=f"member{unique_id}@test.com",
        password_hash=get_password_hash("member123456"),
        role=UserRole.MEMBER,
        group_id=1,
        class_name="计算机科学与技术2101",
        is_active=True,
        is_verified=True
    )
    
    db_session.add(member_user)
    await db_session.commit()
    await db_session.refresh(member_user)
    return member_user


@pytest_asyncio.fixture
async def test_group_leader(db_session):
    """创建测试组长"""
    import uuid
    unique_id = str(uuid.uuid4())[:8]
    
    leader_user = Member(
        name=f"测试组长{unique_id}",
        student_id=f"leader{unique_id}",
        email=f"leader{unique_id}@test.com",
        password_hash=get_password_hash("leader123456"),
        role=UserRole.GROUP_LEADER,
        group_id=1,
        class_name="计算机科学与技术2101",
        is_active=True,
        is_verified=True
    )
    
    db_session.add(leader_user)
    await db_session.commit()
    await db_session.refresh(leader_user)
    return leader_user


@pytest.fixture
def auth_headers_admin(client, test_admin_user):
    """获取管理员认证头"""
    login_data = {
        "student_id": test_admin_user.student_id,
        "password": "admin123456"
    }
    response = client.post("/api/v1/auth/login", json=login_data)
    assert response.status_code == 200
    
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def auth_headers_member(client, test_member_user):
    """获取成员认证头"""
    login_data = {
        "student_id": test_member_user.student_id,
        "password": "member123456"
    }
    response = client.post("/api/v1/auth/login", json=login_data)
    assert response.status_code == 200
    
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def auth_headers_leader(client, test_group_leader):
    """获取组长认证头"""
    login_data = {
        "student_id": test_group_leader.student_id,
        "password": "leader123456"
    }
    response = client.post("/api/v1/auth/login", json=login_data)
    assert response.status_code == 200
    
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def sample_task_data():
    """示例任务数据"""
    return {
        "title": "图书馆网络故障维修",
        "description": "图书馆3楼网络设备无法正常连接，需要检查交换机状态",
        "task_type": "repair",
        "priority": "high",
        "location": "图书馆3楼",
        "estimated_minutes": 120,
        "reporter_name": "张老师",
        "reporter_contact": "13812345678",
        "is_rush": True
    }


@pytest.fixture
def sample_member_data():
    """示例成员数据"""
    import uuid
    unique_id = str(uuid.uuid4())[:8]
    
    return {
        "name": f"新测试成员{unique_id}",
        "student_id": f"new{unique_id}",
        "email": f"new{unique_id}@test.com",
        "password": "newpassword123",
        "role": "member",
        "group_id": 1,
        "class_name": "计算机科学与技术2103",
        "is_active": True,
        "is_verified": False
    }


class TestDataHelper:
    """测试数据帮助类"""
    
    @staticmethod
    async def create_test_tasks(db_session, member_id: int, count: int = 5):
        """创建测试任务"""
        from app.models.task import RepairTask, TaskStatus, TaskPriority
        from datetime import datetime, timedelta
        import uuid
        
        tasks = []
        for i in range(count):
            unique_suffix = str(uuid.uuid4())[:8]
            task = RepairTask(
                title=f"测试任务 {i+1}",
                description=f"这是第{i+1}个测试任务",
                task_id=f"T{unique_suffix}{i+1:04d}",
                status=TaskStatus.PENDING if i % 2 == 0 else TaskStatus.COMPLETED,
                priority=TaskPriority.MEDIUM,
                location=f"测试地点{i+1}",
                member_id=member_id,
                reporter_name=f"报告人{i+1}",
                reporter_contact=f"1381234567{i}",
                report_time=datetime.utcnow() - timedelta(days=i+1)
            )
            db_session.add(task)
            tasks.append(task)
        
        await db_session.commit()
        return tasks
    
    @staticmethod
    async def create_test_attendance_records(db_session, member_id: int, days: int = 7):
        """创建测试考勤记录"""
        from app.models.attendance import AttendanceRecord
        from datetime import datetime, date, timedelta
        
        records = []
        base_date = date.today() - timedelta(days=days)
        
        for i in range(days):
            current_date = base_date + timedelta(days=i)
            checkin_time = datetime.combine(current_date, datetime.min.time()) + timedelta(hours=9, minutes=i*5)
            checkout_time = checkin_time + timedelta(hours=8, minutes=30)
            
            record = AttendanceRecord(
                member_id=member_id,
                attendance_date=current_date,
                checkin_time=checkin_time,
                checkout_time=checkout_time,
                work_hours=8.5,
                status="正常",
                location="办公室",
                notes=f"第{i+1}天考勤",
                is_late_checkin=(i % 4 == 0),
                late_checkin_minutes=10 if i % 4 == 0 else 0,
                is_early_checkout=False,
                early_checkout_minutes=0
            )
            db_session.add(record)
            records.append(record)
        
        await db_session.commit()
        return records


@pytest.fixture
def test_data_helper():
    """测试数据帮助类fixture"""
    return TestDataHelper