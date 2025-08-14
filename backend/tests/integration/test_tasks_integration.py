"""
Integration tests for Tasks API endpoints.
Tests the complete API flow with database interactions.
"""

from datetime import datetime, timedelta

import pytest
from app.models.member import Member, UserRole
from app.models.task import (RepairTask, TaskCategory, TaskPriority,
                             TaskStatus, TaskTag, TaskTagType, TaskType)
from httpx import AsyncClient
from tests.conftest import AsyncTestClient


class TestTasksIntegration:
    """Integration tests for Tasks API endpoints."""

    @pytest.mark.asyncio
    async def test_get_work_time_detail_integration(
        self,
        async_client: AsyncClient,
        db_session,
        sample_member,
        auth_token_for_member,
    ):
        """Test work time detail endpoint with real database."""
        # Create a task with work time data
        task = RepairTask(
            task_id="INTEG_TEST_001",
            title="集成测试任务",
            description="用于测试工时详情的集成测试",
            category=TaskCategory.NETWORK_REPAIR,
            priority=TaskPriority.MEDIUM,
            task_type=TaskType.OFFLINE,
            status=TaskStatus.COMPLETED,
            location="测试地点",
            member_id=sample_member.id,
            report_time=datetime.utcnow() - timedelta(hours=50),
            response_time=datetime.utcnow() - timedelta(hours=40),
            completion_time=datetime.utcnow() - timedelta(hours=2),
            reporter_name="测试报修人",
            reporter_contact="13800138000",
            rating=4,
            feedback="服务很好",
            work_minutes=100,  # Offline task base minutes
        )
        db_session.add(task)
        await db_session.flush()

        # Add some penalty tags to test complex calculation
        penalty_tag = TaskTag.create_timeout_response_tag()
        db_session.add(penalty_tag)
        await db_session.flush()

        task.tags.append(penalty_tag)
        await db_session.commit()

        # Make API request
        headers = {"Authorization": f"Bearer {auth_token_for_member}"}
        response = await async_client.get(
            f"/api/v1/tasks/work-time-detail/{task.id}", headers=headers
        )

        # Verify response
        assert response.status_code == 200
        data = response.json()

        assert data["success"] is True
        assert "data" in data
        assert "task" in data["data"]
        assert "work_time_detail" in data["data"]

        # Check task details
        task_data = data["data"]["task"]
        assert task_data["id"] == task.id
        assert task_data["task_id"] == "INTEG_TEST_001"
        assert task_data["title"] == "集成测试任务"

        # Check work time details
        work_time = data["data"]["work_time_detail"]
        assert "total_minutes" in work_time
        assert "base_minutes" in work_time
        assert "penalty_minutes" in work_time
        assert "breakdown" in work_time

        # Verify penalty was applied (timeout response = -30 minutes)
        assert work_time["penalty_minutes"] > 0
        assert work_time["total_minutes"] < work_time["base_minutes"]

    @pytest.mark.asyncio
    async def test_get_repair_tasks_integration(
        self,
        async_client: AsyncClient,
        db_session,
        sample_member,
        auth_token_for_member,
    ):
        """Test repair tasks list endpoint with real database."""
        # Create multiple tasks
        tasks = []
        for i in range(3):
            task = RepairTask(
                task_id=f"REPAIR_TEST_{i:03d}",
                title=f"报修任务{i+1}",
                description=f"集成测试报修任务{i+1}",
                category=TaskCategory.NETWORK_REPAIR,
                priority=TaskPriority.MEDIUM,
                task_type=TaskType.ONLINE if i % 2 == 0 else TaskType.OFFLINE,
                status=TaskStatus.COMPLETED,
                location=f"测试地点{i+1}",
                member_id=sample_member.id,
                report_time=datetime.utcnow() - timedelta(hours=i + 1),
                response_time=datetime.utcnow() - timedelta(hours=i),
                completion_time=datetime.utcnow(),
                reporter_name=f"报修人{i+1}",
                reporter_contact=f"138000{i:05d}",
                rating=4 + i % 2,
                work_minutes=40 if i % 2 == 0 else 100,
            )
            tasks.append(task)
            db_session.add(task)

        await db_session.commit()

        # Make API request
        headers = {"Authorization": f"Bearer {auth_token_for_member}"}
        response = await async_client.get(
            "/api/v1/tasks/repair", headers=headers, params={"skip": 0, "limit": 10}
        )

        # Verify response
        assert response.status_code == 200
        data = response.json()

        assert data["success"] is True
        assert "data" in data
        assert "tasks" in data["data"]
        assert "total_count" in data["data"]

        # Check task list
        task_list = data["data"]["tasks"]
        assert len(task_list) == 3
        assert data["data"]["total_count"] == 3

        # Verify task details
        for i, task_data in enumerate(task_list):
            assert "id" in task_data
            assert "task_id" in task_data
            assert "title" in task_data
            assert "work_minutes" in task_data

    @pytest.mark.asyncio
    async def test_work_time_detail_permission_denied(
        self, async_client: AsyncClient, db_session, sample_member
    ):
        """Test work time detail endpoint - permission denied for other user's task."""
        # Create another member
        other_member = Member(
            username="other_test_user",
            name="其他测试用户",
            student_id="OTHER001",
            phone="13800138999",
            department="信息化建设处",
            class_name="测试班级2",
            password_hash="test_hash",
            role=UserRole.MEMBER,
            is_active=True,
        )
        db_session.add(other_member)
        await db_session.flush()

        # Create task for other member
        task = RepairTask(
            task_id="OTHER_TASK_001",
            title="其他人的任务",
            description="其他成员的任务",
            category=TaskCategory.NETWORK_REPAIR,
            priority=TaskPriority.MEDIUM,
            task_type=TaskType.OFFLINE,
            status=TaskStatus.COMPLETED,
            location="其他地点",
            member_id=other_member.id,  # Different member
            report_time=datetime.utcnow() - timedelta(hours=2),
            response_time=datetime.utcnow() - timedelta(hours=1),
            completion_time=datetime.utcnow(),
            reporter_name="其他报修人",
            reporter_contact="13800138888",
            work_minutes=100,
        )
        db_session.add(task)
        await db_session.commit()

        # Create token for sample_member
        from app.core.security import create_access_token

        token = create_access_token({"sub": sample_member.username})

        # Try to access other member's task
        headers = {"Authorization": f"Bearer {token}"}
        response = await async_client.get(
            f"/api/v1/tasks/work-time-detail/{task.id}", headers=headers
        )

        # Should be forbidden
        assert response.status_code == 403
        data = response.json()
        assert "权限不足" in data["detail"]

    @pytest.mark.asyncio
    async def test_work_time_detail_admin_access(
        self, async_client: AsyncClient, db_session, sample_member
    ):
        """Test admin can access any task's work time detail."""
        # Create admin user
        admin_member = Member(
            username="admin_test_user",
            name="管理员测试用户",
            student_id="ADMIN001",
            phone="13800138777",
            department="信息化建设处",
            class_name="管理员",
            password_hash="admin_hash",
            role=UserRole.ADMIN,
            is_active=True,
        )
        db_session.add(admin_member)
        await db_session.flush()

        # Create task for sample_member
        task = RepairTask(
            task_id="ADMIN_ACCESS_TEST",
            title="管理员权限测试",
            description="测试管理员访问权限",
            category=TaskCategory.NETWORK_REPAIR,
            priority=TaskPriority.HIGH,
            task_type=TaskType.OFFLINE,
            status=TaskStatus.COMPLETED,
            location="权限测试地点",
            member_id=sample_member.id,  # Different from admin
            report_time=datetime.utcnow() - timedelta(hours=2),
            response_time=datetime.utcnow() - timedelta(hours=1),
            completion_time=datetime.utcnow(),
            reporter_name="权限测试报修人",
            reporter_contact="13800138666",
            work_minutes=100,
        )
        db_session.add(task)
        await db_session.commit()

        # Create admin token
        from app.core.security import create_access_token

        admin_token = create_access_token({"sub": admin_member.username})

        # Admin should be able to access any task
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = await async_client.get(
            f"/api/v1/tasks/work-time-detail/{task.id}", headers=headers
        )

        # Should succeed
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["task"]["id"] == task.id

    @pytest.mark.asyncio
    async def test_tasks_pagination(
        self,
        async_client: AsyncClient,
        db_session,
        sample_member,
        auth_token_for_member,
    ):
        """Test tasks endpoint pagination."""
        # Create many tasks for pagination testing
        tasks = []
        for i in range(25):  # More than typical page size
            task = RepairTask(
                task_id=f"PAGE_TEST_{i:03d}",
                title=f"分页测试任务{i+1}",
                description=f"用于分页测试的任务{i+1}",
                category=TaskCategory.NETWORK_REPAIR,
                priority=TaskPriority.MEDIUM,
                task_type=TaskType.ONLINE,
                status=TaskStatus.COMPLETED,
                location=f"分页测试地点{i+1}",
                member_id=sample_member.id,
                report_time=datetime.utcnow() - timedelta(hours=i + 1),
                response_time=datetime.utcnow() - timedelta(hours=i),
                completion_time=datetime.utcnow(),
                reporter_name=f"分页测试报修人{i+1}",
                reporter_contact=f"138{i:08d}",
                work_minutes=40,
            )
            tasks.append(task)
            db_session.add(task)

        await db_session.commit()

        # Test first page
        headers = {"Authorization": f"Bearer {auth_token_for_member}"}
        response = await async_client.get(
            "/api/v1/tasks/repair", headers=headers, params={"skip": 0, "limit": 10}
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]["tasks"]) == 10
        assert data["data"]["total_count"] == 25

        # Test second page
        response = await async_client.get(
            "/api/v1/tasks/repair", headers=headers, params={"skip": 10, "limit": 10}
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]["tasks"]) == 10

        # Test last page
        response = await async_client.get(
            "/api/v1/tasks/repair", headers=headers, params={"skip": 20, "limit": 10}
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]["tasks"]) == 5  # Remaining tasks


@pytest.fixture
async def sample_member(db_session) -> Member:
    """Create a sample member for testing."""
    member = Member(
        username="integration_test_user",
        name="集成测试用户",
        student_id="INTEG001",
        phone="13800138001",
        department="信息化建设处",
        class_name="集成测试班",
        password_hash="integration_test_hash",
        role=UserRole.MEMBER,
        is_active=True,
    )
    db_session.add(member)
    await db_session.flush()
    return member


@pytest.fixture
def auth_token_for_member(sample_member) -> str:
    """Create authentication token for sample member."""
    from app.core.security import create_access_token

    return create_access_token({"sub": sample_member.username})
