"""
Unit tests for Tasks API endpoints.
Tests the individual API endpoint behaviors with mocked dependencies.
"""

from datetime import datetime, timedelta
from unittest.mock import AsyncMock, Mock, patch

import pytest
from fastapi import HTTPException

from app.api.v1.tasks import (
    get_all_tasks,
    get_assistance_tasks,
    get_monitoring_tasks,
    get_repair_list,
    get_work_time_detail,
)
from app.models.member import Member, UserRole
from app.models.task import RepairTask, TaskCategory, TaskPriority, TaskStatus, TaskType


class TestTasksAPI:
    """Unit tests for Tasks API endpoints."""

    @pytest.mark.asyncio
    async def test_get_work_time_detail_success(self):
        """Test work time detail endpoint - success case."""
        # Mock dependencies
        mock_db = AsyncMock()
        mock_user = Member(
            username="test_user",
            name="测试用户",
            class_name="测试班级",
            role=UserRole.MEMBER,
            is_active=True,
        )

        # Mock task with work time details
        mock_task = RepairTask(
            id=1,
            task_id="TEST_001",
            title="测试任务",
            description="测试工时计算",
            category=TaskCategory.NETWORK_REPAIR,
            priority=TaskPriority.MEDIUM,
            task_type=TaskType.OFFLINE,
            status=TaskStatus.COMPLETED,
            location="测试地点",
            member_id=1,
            work_minutes=100,  # 添加work_minutes字段
            report_time=datetime.utcnow() - timedelta(hours=2),
            response_time=datetime.utcnow() - timedelta(hours=1),
            completion_time=datetime.utcnow(),
            reporter_name="测试报修人",
            reporter_contact="13800138000",
            rating=4,
            feedback="满意",
        )

        # Mock database query
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = mock_task
        mock_db.execute.return_value = mock_result

        # Call endpoint
        result = await get_work_time_detail(
            task_id=1, current_user=mock_user, db=mock_db
        )

        # Verify results
        assert result["success"] is True
        assert result["data"]["task_id"] == 1
        assert result["data"]["total_work_minutes"] == 100
        assert result["data"]["total_work_hours"] == round(100 / 60.0, 2)
        assert "work_time_breakdown" in result["data"]

    @pytest.mark.asyncio
    async def test_get_work_time_detail_task_not_found(self):
        """Test work time detail endpoint - task not found."""
        # Mock dependencies
        mock_db = AsyncMock()
        mock_user = Member(
            username="test_user",
            name="测试用户",
            class_name="测试班级",
            department="信息化建设处",
            role=UserRole.MEMBER,
            is_active=True,
        )

        # Mock empty database result
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        # Call endpoint and expect exception
        with pytest.raises(HTTPException) as exc_info:
            await get_work_time_detail(task_id=999, current_user=mock_user, db=mock_db)

        assert exc_info.value.status_code == 404
        assert "任务不存在" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_get_work_time_detail_no_permission(self):
        """Test work time detail endpoint - no permission to view task."""
        # Mock dependencies
        mock_db = AsyncMock()
        mock_user = Member(
            id=2, username="other_user", name="其他用户", class_name="测试班级", role=UserRole.MEMBER, is_active=True
        )

        # Mock task belonging to different user
        mock_task = RepairTask(
            id=1,
            member_id=1,  # Different from current_user.id
            status=TaskStatus.COMPLETED,
        )

        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = mock_task
        mock_db.execute.return_value = mock_result

        # Call endpoint and expect exception
        with pytest.raises(HTTPException) as exc_info:
            await get_work_time_detail(task_id=1, current_user=mock_user, db=mock_db)

        assert exc_info.value.status_code == 403
        assert "无权限查看" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_get_repair_list_success(self):
        """Test repair tasks list endpoint - success case."""
        # Call endpoint (get_repair_list doesn't take parameters in actual
        # implementation)
        result = await get_repair_list()

        # Verify results (based on actual implementation)
        assert result["success"] is True
        assert "data" in result
        assert "items" in result["data"]

    @pytest.mark.asyncio
    async def test_get_monitoring_tasks_success(self):
        """Test monitoring tasks endpoint - success case."""
        # Mock dependencies
        mock_db = AsyncMock()
        mock_user = Member(
            username="test_user",
            name="测试用户",
            class_name="测试班级",
            department="信息化建设处",
            role=UserRole.MEMBER,
            is_active=True,
        )

        # Mock empty result (placeholder implementation)
        mock_result = Mock()
        mock_scalars = Mock()
        mock_scalars.unique.return_value.all.return_value = []
        mock_result.scalars.return_value = mock_scalars

        # Mock count result
        mock_count_result = Mock()
        mock_count_result.scalar.return_value = 0

        # Configure db.execute to return different results for different calls
        mock_db.execute.side_effect = [mock_result, mock_count_result]

        # Call endpoint
        result = await get_monitoring_tasks(
            page=1, pageSize=10, current_user=mock_user, db=mock_db
        )

        # Verify results
        assert result["success"] is True
        assert result["data"]["items"] == []
        assert result["data"]["total"] == 0
        assert result["data"]["page"] == 1
        assert result["data"]["pageSize"] == 10

    @pytest.mark.asyncio
    async def test_get_assistance_tasks_success(self):
        """Test assistance tasks endpoint - success case."""
        # Mock dependencies
        mock_db = AsyncMock()
        mock_user = Member(
            username="test_user",
            name="测试用户",
            class_name="测试班级",
            department="信息化建设处",
            role=UserRole.MEMBER,
            is_active=True,
        )

        # Mock empty result (placeholder implementation)
        mock_result = Mock()
        mock_scalars = Mock()
        mock_scalars.unique.return_value.all.return_value = []
        mock_result.scalars.return_value = mock_scalars

        # Mock count result
        mock_count_result = Mock()
        mock_count_result.scalar.return_value = 0

        # Configure db.execute to return different results for different calls
        mock_db.execute.side_effect = [mock_result, mock_count_result]

        # Call endpoint
        result = await get_assistance_tasks(
            page=1, pageSize=10, current_user=mock_user, db=mock_db
        )

        # Verify results
        assert result["success"] is True
        assert result["data"]["items"] == []
        assert result["data"]["total"] == 0
        assert result["data"]["page"] == 1
        assert result["data"]["pageSize"] == 10

    @pytest.mark.asyncio
    async def test_get_all_tasks_admin_permission(self):
        """Test tasks list endpoint - admin can see all tasks."""
        # Mock dependencies
        mock_db = AsyncMock()
        mock_admin_user = Member(
            id=1, username="admin_user", name="管理员", class_name="管理员", role=UserRole.ADMIN, is_active=True
        )

        # Mock database result
        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute.return_value = mock_result

        # Call endpoint
        result = await get_all_tasks(
            page=1, pageSize=10, current_user=mock_admin_user, db=mock_db
        )

        # Verify admin endpoint works
        assert result["success"] is True
        assert "data" in result


@pytest.fixture
def mock_work_hours_service():
    """Mock work hours calculation service."""
    with patch("app.services.work_hours_service.WorkHoursCalculationService") as mock:
        service_instance = AsyncMock()
        mock.return_value = service_instance
        yield service_instance
