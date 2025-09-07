"""
E2E Test Configuration and Fixtures
提供端到端测试的配置、数据库设置和通用夹具
包含完整的测试环境准备和清理逻辑
"""

import asyncio
import os
import tempfile
from datetime import datetime, timedelta
from typing import AsyncGenerator, Dict, List, Optional

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from httpx import AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_session
from app.core.security import get_password_hash
from app.main import app as fastapi_app
from app.models.attendance import AttendanceRecord, AttendanceException, MonthlyAttendanceSummary
from app.models.member import Member, UserRole
from app.models.task import RepairTask, TaskStatus
from tests.database_config import test_config


# E2E测试环境配置
@pytest.fixture(scope="session", autouse=True)
def setup_e2e_environment():
    """设置E2E测试环境变量"""
    os.environ["TESTING"] = "true"
    os.environ["E2E_TESTING"] = "true"
    os.environ["DEBUG"] = "true"
    os.environ["SECRET_KEY"] = "e2e-test-secret-key-for-testing-only"
    os.environ["FORCE_SQLITE_TESTS"] = "true"
    yield
    # 测试结束后清理环境变量
    for key in ["E2E_TESTING", "TESTING", "DEBUG", "SECRET_KEY", "FORCE_SQLITE_TESTS"]:
        if key in os.environ:
            del os.environ[key]


# E2E测试数据库引擎和会话
@pytest_asyncio.fixture(scope="function")
async def e2e_test_engine():
    """为E2E测试创建独立的数据库引擎"""
    engine = await test_config.create_test_engine()
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def e2e_setup_database(e2e_test_engine):
    """设置E2E测试数据库"""
    await test_config.setup_test_database(e2e_test_engine)
    yield
    # 测试后清理
    try:
        async with e2e_test_engine.begin() as conn:
            # 清理测试数据
            await conn.execute(text("DELETE FROM attendance"))
            await conn.execute(text("DELETE FROM repair_tasks"))
            await conn.execute(text("DELETE FROM members"))
    except Exception:
        pass  # 忽略清理错误


@pytest_asyncio.fixture
async def e2e_session(
    e2e_test_engine, e2e_setup_database
) -> AsyncGenerator[AsyncSession, None]:
    """E2E测试专用数据库会话"""
    async with AsyncSession(
        e2e_test_engine,
        expire_on_commit=False,
        autoflush=False,
    ) as session:
        try:
            yield session
            if session.in_transaction():
                await session.commit()
        except Exception:
            if session.in_transaction():
                await session.rollback()
            raise
        finally:
            await session.close()


@pytest_asyncio.fixture
async def e2e_client(e2e_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """E2E测试客户端，带有数据库会话注入"""

    async def override_get_async_session():
        yield e2e_session

    # 注入测试数据库会话
    original_overrides = fastapi_app.dependency_overrides.copy()
    fastapi_app.dependency_overrides[get_async_session] = override_get_async_session

    from httpx import ASGITransport

    transport = ASGITransport(app=fastapi_app)

    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        yield client

    # 恢复原始依赖
    fastapi_app.dependency_overrides.clear()
    fastapi_app.dependency_overrides.update(original_overrides)


# 测试用户夹具
@pytest_asyncio.fixture
async def e2e_test_users(e2e_session: AsyncSession) -> Dict[str, Member]:
    """创建E2E测试用户集合"""
    users = {}

    # 学生网管
    student_member = Member(
        username="student_001",
        name="张三",
        student_id="2021001001",
        group_id=1,
        class_name="计算机科学与技术2101",
        email="student@example.com",
        password_hash=get_password_hash("StudentPass123!"),
        role=UserRole.MEMBER,
        is_active=True,
        is_verified=True,
    )

    # 组长
    group_leader = Member(
        username="leader_001",
        name="李四",
        student_id="2021000002",
        group_id=1,
        class_name="计算机科学与技术2101",
        email="leader@example.com",
        password_hash=get_password_hash("LeaderPass123!"),
        role=UserRole.GROUP_LEADER,
        is_active=True,
        is_verified=True,
    )

    # 管理员
    admin = Member(
        username="admin_001",
        name="王五",
        student_id="2021000001",
        group_id=1,
        class_name="管理员",
        email="admin@example.com",
        password_hash=get_password_hash("AdminPass123!"),
        role=UserRole.ADMIN,
        is_active=True,
        is_verified=True,
    )

    # 超级管理员
    super_admin = Member(
        username="super_admin",
        name="赵六",
        student_id="2021000000",
        group_id=1,
        class_name="超级管理员",
        email="superadmin@example.com",
        password_hash=get_password_hash("SuperPass123!"),
        role=UserRole.SUPER_ADMIN,
        is_active=True,
        is_verified=True,
    )

    # 批量添加用户
    test_users = [student_member, group_leader, admin, super_admin]
    for user in test_users:
        e2e_session.add(user)

    await e2e_session.commit()

    # 刷新用户数据
    for user in test_users:
        await e2e_session.refresh(user)

    users["student"] = student_member
    users["leader"] = group_leader
    users["admin"] = admin
    users["super_admin"] = super_admin

    return users


@pytest_asyncio.fixture
async def e2e_user_tokens(
    e2e_client: AsyncClient, e2e_test_users: Dict[str, Member]
) -> Dict[str, str]:
    """为E2E测试用户获取JWT令牌"""
    tokens = {}

    # 用户登录凭据映射
    login_credentials = {
        "student": {"username": "student_001", "password": "StudentPass123!"},
        "leader": {"username": "leader_001", "password": "LeaderPass123!"},
        "admin": {"username": "admin_001", "password": "AdminPass123!"},
        "super_admin": {"username": "super_admin", "password": "SuperPass123!"},
    }

    # 为每个用户获取token
    for role, credentials in login_credentials.items():
        login_response = await e2e_client.post("/api/v1/auth/login", json=credentials)

        if login_response.status_code == 200:
            data = login_response.json()
            token = data.get("data", {}).get("access_token")
            if token:
                tokens[role] = token
            else:
                # 如果登录失败，使用模拟token
                tokens[role] = f"mock_token_{role}"
        else:
            tokens[role] = f"mock_token_{role}"

    return tokens


@pytest.fixture
def e2e_auth_headers():
    """创建E2E测试的认证头部"""

    def _create_headers(token: str) -> Dict[str, str]:
        return {"Authorization": f"Bearer {token}"}

    return _create_headers


# 测试数据夹具
@pytest_asyncio.fixture
async def e2e_sample_repair_tasks(
    e2e_session: AsyncSession, e2e_test_users: Dict[str, Member]
) -> List[RepairTask]:
    """创建样本报修任务"""
    tasks = []

    # 线上报修任务
    online_task = RepairTask(
        reporter_name="用户A",
        reporter_contact="13800138001",
        contact_info="用户A联系方式",
        repair_type="网络故障",
        description="无法连接网络",
        location="宿舍A101",
        urgency_level="normal",
        is_online_task=True,
        assigned_member_id=e2e_test_users["student"].id,
        status=TaskStatus.IN_PROGRESS,
        created_at=datetime.now(),
    )

    # 线下报修任务
    offline_task = RepairTask(
        reporter_name="用户B",
        reporter_contact="13800138002",
        contact_info="用户B联系方式",
        repair_type="硬件维修",
        description="电脑无法开机",
        location="宿舍B202",
        urgency_level="high",
        is_online_task=False,
        assigned_member_id=e2e_test_users["student"].id,
        status=TaskStatus.PENDING,
        created_at=datetime.now() - timedelta(hours=2),
    )

    # 已完成任务
    completed_task = RepairTask(
        reporter_name="用户C",
        reporter_contact="13800138003",
        contact_info="用户C联系方式",
        repair_type="软件问题",
        description="系统异常",
        location="宿舍C303",
        urgency_level="low",
        is_online_task=True,
        assigned_member_id=e2e_test_users["student"].id,
        status=TaskStatus.COMPLETED,
        completed_at=datetime.now() - timedelta(hours=1),
        created_at=datetime.now() - timedelta(hours=3),
    )

    tasks = [online_task, offline_task, completed_task]

    for task in tasks:
        e2e_session.add(task)

    await e2e_session.commit()

    # 刷新任务数据
    for task in tasks:
        await e2e_session.refresh(task)

    return tasks


@pytest_asyncio.fixture
async def e2e_sample_attendance_records(
    e2e_session: AsyncSession, e2e_test_users: Dict[str, Member]
) -> List[MonthlyAttendanceSummary]:
    """创建样本考勤记录"""
    records = []

    # 当月考勤记录
    current_month_record = MonthlyAttendanceSummary(
        **{
            "member_id": e2e_test_users["student"].id,
            "year": datetime.now().year,
            "month": datetime.now().month,
            "total_hours": 800,
            "repair_task_hours": 720,
            "monitoring_hours": 50,
            "assistance_hours": 30,
            "task_completion_count": 18,
        }
    )
    current_month_record.created_at = datetime.now()
    current_month_record.updated_at = datetime.now()

    # 上月考勤记录
    last_month = datetime.now().replace(day=1) - timedelta(days=1)
    last_month_record = MonthlyAttendanceSummary(
        **{
            "member_id": e2e_test_users["student"].id,
            "year": last_month.year,
            "month": last_month.month,
            "total_hours": 750,
            "repair_task_hours": 700,
            "monitoring_hours": 25,
            "assistance_hours": 25,
            "task_completion_count": 15,
        }
    )
    last_month_record.created_at = last_month
    last_month_record.updated_at = last_month

    records = [current_month_record, last_month_record]

    for record in records:
        e2e_session.add(record)

    await e2e_session.commit()

    # 刷新记录数据
    for record in records:
        await e2e_session.refresh(record)

    return records


# 测试数据文件夹具
@pytest.fixture
def e2e_temp_upload_dir():
    """创建临时上传目录用于E2E测试"""
    with tempfile.TemporaryDirectory(prefix="e2e_uploads_") as temp_dir:
        yield temp_dir


@pytest.fixture
def e2e_sample_excel_data():
    """提供E2E测试的Excel样本数据"""
    return {
        "repair_data": [
            {
                "报修人姓名": "测试用户1",
                "报修人联系方式": "13800138001",
                "故障类型": "网络故障",
                "故障描述": "无法上网",
                "故障地点": "宿舍A101",
                "紧急程度": "一般",
                "报修时间": "2024-01-15 10:30:00",
            },
            {
                "报修人姓名": "测试用户2",
                "报修人联系方式": "13800138002",
                "故障类型": "硬件故障",
                "故障描述": "电脑死机",
                "故障地点": "宿舍B202",
                "紧急程度": "紧急",
                "报修时间": "2024-01-15 11:00:00",
            },
        ],
        "member_data": [
            {
                "姓名": "新学生1",
                "学号": "2024001001",
                "班级": "计算机科学与技术2401",
                "邮箱": "newstudent1@example.com",
                "小组": "第1组",
            },
            {
                "姓名": "新学生2",
                "学号": "2024001002",
                "班级": "计算机科学与技术2401",
                "邮箱": "newstudent2@example.com",
                "小组": "第1组",
            },
        ],
    }


# E2E测试辅助函数
class E2ETestHelper:
    """E2E测试辅助类"""

    @staticmethod
    async def wait_for_task_status(
        client: AsyncClient,
        task_id: int,
        expected_status: TaskStatus,
        timeout: int = 30,
        headers: Optional[Dict[str, str]] = None,
    ) -> bool:
        """等待任务状态变更"""
        start_time = asyncio.get_event_loop().time()

        while asyncio.get_event_loop().time() - start_time < timeout:
            response = await client.get(
                f"/api/v1/tasks/repair/{task_id}", headers=headers or {}
            )

            if response.status_code == 200:
                task_data = response.json().get("data", {})
                if task_data.get("status") == expected_status.value:
                    return True

            await asyncio.sleep(1)

        return False

    @staticmethod
    async def simulate_file_upload(
        client: AsyncClient,
        endpoint: str,
        file_content: bytes,
        filename: str,
        headers: Optional[Dict[str, str]] = None,
    ):
        """模拟文件上传"""
        files = {"file": (filename, file_content, "application/octet-stream")}
        return await client.post(endpoint, files=files, headers=headers or {})

    @staticmethod
    def assert_response_success(response, expected_status: int = 200):
        """断言响应成功"""
        assert (
            response.status_code == expected_status
        ), f"Expected status {expected_status}, got {response.status_code}. Response: {response.text}"

    @staticmethod
    def assert_response_data(response, expected_keys: List[str]):
        """断言响应数据包含期望的键"""
        data = response.json().get("data", {})
        for key in expected_keys:
            assert (
                key in data
            ), f"Expected key '{key}' not found in response data: {data}"


@pytest.fixture
def e2e_helper():
    """E2E测试辅助函数"""
    return E2ETestHelper


# 事件循环配置
@pytest.fixture(scope="function")
def event_loop():
    """为E2E测试创建新的事件循环"""
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()

    try:
        yield loop
    finally:
        try:
            # 取消所有待处理的任务
            pending = asyncio.all_tasks(loop)
            for task in pending:
                task.cancel()

            # 等待所有任务完成取消
            if pending:
                try:
                    loop.run_until_complete(
                        asyncio.gather(*pending, return_exceptions=True)
                    )
                except Exception:
                    pass
        except Exception:
            pass
        finally:
            loop.close()


# 性能监控夹具
@pytest_asyncio.fixture
async def e2e_performance_monitor():
    """E2E性能监控"""
    performance_data = {"start_time": None, "operations": []}

    def start_monitoring():
        performance_data["start_time"] = asyncio.get_event_loop().time()

    def record_operation(name: str, duration: float):
        performance_data["operations"].append({"name": name, "duration": duration})

    def get_summary():
        total_time = sum(op["duration"] for op in performance_data["operations"])
        return {
            "total_operations": len(performance_data["operations"]),
            "total_time": total_time,
            "average_time": (
                total_time / len(performance_data["operations"])
                if performance_data["operations"]
                else 0
            ),
            "operations": performance_data["operations"],
        }

    monitor = type(
        "PerformanceMonitor",
        (),
        {"start": start_monitoring, "record": record_operation, "summary": get_summary},
    )()

    yield monitor
