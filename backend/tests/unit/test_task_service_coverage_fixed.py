"""
Comprehensive tests for TaskService (Fixed Version)
Improved test coverage targeting actual TaskService methods
"""

from datetime import datetime, timedelta
from unittest.mock import AsyncMock, Mock, patch

import pytest

from app.models.member import Member, UserRole
from app.models.task import (
    MonitoringTask,
    RepairTask,
    TaskCategory,
    TaskPriority,
    TaskStatus,
    TaskType,
)
from app.services.task_service import TaskService


@pytest.mark.asyncio
class TestTaskServiceFixed:
    """Fixed TaskService tests targeting real methods"""

    async def test_service_initialization(self, async_session):
        """Test TaskService initialization"""
        service = TaskService(async_session)
        assert service is not None
        assert service.db == async_session
        assert service.work_hours_service is not None
        assert service.rush_task_service is not None

    async def test_create_repair_task_basic(self, async_session):
        """Test basic repair task creation"""
        service = TaskService(async_session)

        # Mock the task ID generation
        with patch.object(service, "_generate_task_id", return_value="T202501270001"):
            task_data = {
                "title": "Network repair test",
                "description": "Test description",
                "category": TaskCategory.NETWORK_REPAIR,
                "priority": TaskPriority.HIGH,
                "task_type": TaskType.ONLINE,
                "assigned_to": 1,
                "reporter_name": "Test User",
                "reporter_contact": "test@example.com",
            }

            # Mock database operations
            async_session.add = Mock()
            async_session.flush = AsyncMock()
            async_session.commit = AsyncMock()
            async_session.refresh = AsyncMock()

            # Mock the private methods
            with (
                patch.object(service, "_add_tags_to_task", return_value=None),
                patch.object(service, "_add_rush_tag", return_value=None),
                patch.object(service, "_auto_add_penalty_tags", return_value=None),
                patch.object(service, "_auto_add_bonus_tags", return_value=None),
            ):

                task = await service.create_repair_task(task_data, creator_id=1)

                assert task.title == "Network repair test"
                assert task.task_id == "T202501270001"
                assert task.category == TaskCategory.NETWORK_REPAIR
                assert task.priority == TaskPriority.HIGH
                assert task.task_type == TaskType.ONLINE
                assert task.member_id == 1

                async_session.add.assert_called_once()
                async_session.flush.assert_called_once()
                async_session.commit.assert_called_once()
                async_session.refresh.assert_called_once()

    async def test_create_repair_task_with_tags(self, async_session):
        """Test repair task creation with tags"""
        service = TaskService(async_session)

        with (
            patch.object(service, "_generate_task_id", return_value="T202501270002"),
            patch.object(
                service, "_add_tags_to_task", return_value=None
            ) as mock_add_tags,
            patch.object(service, "_add_rush_tag", return_value=None),
            patch.object(service, "_auto_add_penalty_tags", return_value=None),
            patch.object(service, "_auto_add_bonus_tags", return_value=None),
        ):

            task_data = {"title": "Tagged task", "assigned_to": 1, "tag_ids": [1, 2, 3]}

            async_session.add = Mock()
            async_session.flush = AsyncMock()
            async_session.commit = AsyncMock()
            async_session.refresh = AsyncMock()

            await service.create_repair_task(task_data, creator_id=1)

            mock_add_tags.assert_called_once()
            async_session.add.assert_called_once()
            async_session.flush.assert_called_once()
            async_session.commit.assert_called_once()

    async def test_create_monitoring_task_success(self, async_session):
        """Test successful monitoring task creation"""
        service = TaskService(async_session)

        start_time = datetime.utcnow()
        end_time = start_time + timedelta(hours=2)

        task_data = {
            "title": "Network monitoring",
            "description": "Monitor network status",
            "location": "Server room",
            "monitoring_type": "网络监控",
            "start_time": start_time,
            "end_time": end_time,
            "member_id": 1,
        }

        # Mock database operations
        async_session.add = Mock()
        async_session.commit = AsyncMock()
        async_session.refresh = AsyncMock()

        # Mock work hours service
        with patch.object(
            service.work_hours_service, "update_monthly_summary", return_value=None
        ):
            task = await service.create_monitoring_task(task_data, creator_id=1)

            assert task.title == "Network monitoring"
            assert task.work_minutes == 120  # 2 hours
            assert task.status == TaskStatus.COMPLETED
            assert task.member_id == 1

            async_session.add.assert_called_once()
            async_session.commit.assert_called_once()
            async_session.refresh.assert_called_once()

    async def test_create_monitoring_task_invalid_time_range(self, async_session):
        """Test monitoring task with invalid time range"""
        service = TaskService(async_session)

        start_time = datetime.utcnow()
        end_time = start_time - timedelta(hours=1)  # End before start

        task_data = {
            "title": "Invalid monitoring",
            "start_time": start_time,
            "end_time": end_time,
            "member_id": 1,
        }

        async_session.rollback = AsyncMock()

        with pytest.raises(ValueError, match="结束时间必须晚于开始时间"):
            await service.create_monitoring_task(task_data, creator_id=1)

        await async_session.rollback.assert_called_once()

    async def test_create_assistance_task_success(self, async_session):
        """Test successful assistance task creation"""
        service = TaskService(async_session)

        start_time = datetime.utcnow()
        end_time = start_time + timedelta(hours=3)

        task_data = {
            "title": "Help IT department",
            "description": "Assist with server maintenance",
            "assisted_department": "IT部门",
            "assisted_person": "张工程师",
            "start_time": start_time,
            "end_time": end_time,
            "member_id": 1,
        }

        # Mock database operations
        async_session.add = Mock()
        async_session.commit = AsyncMock()
        async_session.refresh = AsyncMock()

        # Mock work hours service
        with patch.object(
            service.work_hours_service, "update_monthly_summary", return_value=None
        ):
            task = await service.create_assistance_task(task_data, creator_id=1)

            assert task.title == "Help IT department"
            assert task.work_minutes == 180  # 3 hours
            assert task.status == TaskStatus.COMPLETED
            assert task.assisted_department == "IT部门"
            assert task.member_id == 1

            async_session.add.assert_called_once()
            async_session.commit.assert_called_once()
            async_session.refresh.assert_called_once()

    async def test_update_task_status_success(self, async_session):
        """Test successful task status update"""
        service = TaskService(async_session)

        # Create a mock task
        mock_task = RepairTask(
            id=1,
            task_id="T001",
            title="Test Task",
            status=TaskStatus.PENDING,
            member_id=1,
        )

        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = mock_task

        with (
            patch.object(async_session, "execute", return_value=mock_result),
            patch.object(
                service, "_recalculate_work_hours_if_needed", return_value=None
            ),
        ):
            async_session.commit = AsyncMock()

            updated_task = await service.update_task_status(
                task_id=1,
                new_status=TaskStatus.IN_PROGRESS,
                operator_id=1,
                note="开始处理任务",
            )

            assert updated_task.status == TaskStatus.IN_PROGRESS
            async_session.commit.assert_called_once()

    async def test_update_task_status_not_found(self, async_session):
        """Test task status update when task not found"""
        service = TaskService(async_session)

        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = None

        with patch.object(async_session, "execute", return_value=mock_result):
            async_session.rollback = AsyncMock()

            with pytest.raises(ValueError, match="任务不存在"):
                await service.update_task_status(
                    task_id=999, new_status=TaskStatus.COMPLETED, operator_id=1
                )

            async_session.rollback.assert_called_once()

    async def test_assign_task_success(self, async_session):
        """Test successful task assignment"""
        service = TaskService(async_session)

        # Mock task lookup
        mock_task = RepairTask(id=1, task_id="T001", title="Test Task", member_id=None)
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = mock_task

        # Mock member lookup
        mock_member = Member(
            username="testuser", name="Test Member", class_name="测试班级"
        )
        mock_member_result = Mock()
        mock_member_result.scalar_one_or_none.return_value = mock_member

        with patch.object(
            async_session, "execute", side_effect=[mock_result, mock_member_result]
        ):
            async_session.commit = AsyncMock()

            result = await service.assign_task(task_id=1, member_id=2, operator_id=1)

            assert result.member_id == 2
            async_session.commit.assert_called_once()

    async def test_assign_task_member_not_found(self, async_session):
        """Test task assignment when member not found"""
        service = TaskService(async_session)

        # Mock task found but member not found
        mock_task = RepairTask(id=1, task_id="T001", title="Test Task")
        mock_task_result = Mock()
        mock_task_result.scalar_one_or_none.return_value = mock_task

        mock_member_result = Mock()
        mock_member_result.scalar_one_or_none.return_value = None

        with patch.object(
            async_session, "execute", side_effect=[mock_task_result, mock_member_result]
        ):
            async_session.rollback = AsyncMock()

            with pytest.raises(ValueError, match="成员不存在"):
                await service.assign_task(task_id=1, member_id=999, operator_id=1)

            async_session.rollback.assert_called_once()

    async def test_add_task_feedback_positive(self, async_session):
        """Test adding positive feedback to task"""
        service = TaskService(async_session)

        mock_task = RepairTask(
            id=1,
            task_id="T001",
            title="Test Task",
            status=TaskStatus.COMPLETED,
            rating=None,
        )
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = mock_task

        with (
            patch.object(async_session, "execute", return_value=mock_result),
            patch.object(service, "recalculate_task_work_hours", return_value=None),
        ):
            async_session.commit = AsyncMock()

            updated_task = await service.add_task_feedback(
                task_id=1, rating=5, feedback="Excellent service!", operator_id=1
            )

            assert updated_task.rating == 5
            assert updated_task.feedback == "Excellent service!"
            async_session.commit.assert_called_once()

    async def test_get_member_task_summary(self, async_session):
        """Test getting member task summary"""
        service = TaskService(async_session)

        member_id = 1
        year = 2025
        month = 1

        # Mock database query results
        mock_summary_data = {
            "total_tasks": 10,
            "completed_tasks": 8,
            "pending_tasks": 2,
            "total_work_hours": 15.5,
            "average_completion_time": 2.3,
        }

        with patch.object(
            service, "_calculate_member_summary", return_value=mock_summary_data
        ):
            summary = await service.get_member_task_summary(member_id, year, month)

            assert summary["total_tasks"] == 10
            assert summary["completed_tasks"] == 8
            assert summary["total_work_hours"] == 15.5

    async def test_batch_mark_rush_tasks(self, async_session):
        """Test batch marking tasks as rush orders"""
        service = TaskService(async_session)

        task_ids = [1, 2, 3]

        with patch.object(
            service.rush_task_service, "batch_mark_rush_tasks", return_value=3
        ) as mock_batch:
            result = await service.batch_mark_rush_tasks(task_ids, operator_id=1)

            assert result == 3
            mock_batch.assert_called_once_with(task_ids, operator_id=1)

    async def test_get_rush_tasks_list(self, async_session):
        """Test getting rush tasks list"""
        service = TaskService(async_session)

        # Mock rush tasks
        mock_tasks = [
            RepairTask(id=1, task_id="T001", title="Rush Task 1", is_rush_order=True),
            RepairTask(id=2, task_id="T002", title="Rush Task 2", is_rush_order=True),
        ]

        with patch.object(
            service.rush_task_service, "get_rush_tasks_list", return_value=mock_tasks
        ):
            tasks = await service.get_rush_tasks_list(status=TaskStatus.PENDING)

            assert len(tasks) == 2
            assert all(task.is_rush_order for task in tasks)

    async def test_get_rush_tasks_statistics(self, async_session):
        """Test getting rush tasks statistics"""
        service = TaskService(async_session)

        mock_stats = {
            "total_rush_tasks": 25,
            "pending_rush_tasks": 5,
            "completed_rush_tasks": 20,
            "average_completion_time": 1.5,
        }

        with patch.object(
            service.rush_task_service, "get_statistics", return_value=mock_stats
        ):
            stats = await service.get_rush_tasks_statistics(year=2025, month=1)

            assert stats["total_rush_tasks"] == 25
            assert stats["pending_rush_tasks"] == 5

    async def test_remove_rush_task_marking(self, async_session):
        """Test removing rush task marking"""
        service = TaskService(async_session)

        with patch.object(
            service.rush_task_service, "remove_rush_marking", return_value=True
        ) as mock_remove:
            result = await service.remove_rush_task_marking(task_id=1, operator_id=1)

            assert result is True
            mock_remove.assert_called_once_with(task_id=1, operator_id=1)

    @pytest.mark.parametrize(
        "task_type,expected_minutes", [(TaskType.ONLINE, 40), (TaskType.OFFLINE, 100)]
    )
    async def test_base_work_minutes_calculation(
        self, async_session, task_type, expected_minutes
    ):
        """Test base work minutes calculation for different task types"""
        service = TaskService(async_session)

        task_data = {"title": "Test task", "task_type": task_type}

        with (
            patch.object(service, "_generate_task_id", return_value="T202501270001"),
            patch.object(service, "_add_tags_to_task", return_value=None),
            patch.object(service, "_add_rush_tag", return_value=None),
            patch.object(service, "_auto_add_penalty_tags", return_value=None),
            patch.object(service, "_auto_add_bonus_tags", return_value=None),
        ):

            async_session.add = Mock()
            async_session.flush = AsyncMock()
            async_session.commit = AsyncMock()
            async_session.refresh = AsyncMock()

            task = await service.create_repair_task(task_data, creator_id=1)

            # The base work minutes should match task type default
            # This tests the get_base_work_minutes() method call
            assert task.base_work_minutes == expected_minutes

    async def test_error_handling_database_error(self, async_session):
        """Test error handling for database errors"""
        service = TaskService(async_session)

        task_data = {"title": "Test task"}

        # Mock database error during task creation
        async_session.add = Mock()
        async_session.flush = AsyncMock(
            side_effect=Exception("Database connection error")
        )
        async_session.rollback = AsyncMock()

        with patch.object(service, "_generate_task_id", return_value="T001"):
            with pytest.raises(Exception, match="Database connection error"):
                await service.create_repair_task(task_data, creator_id=1)

            async_session.rollback.assert_called_once()

    async def test_create_assistance_task_invalid_duration(self, async_session):
        """Test assistance task with zero duration"""
        service = TaskService(async_session)

        start_time = datetime.utcnow()
        end_time = start_time  # Same time = zero duration

        task_data = {
            "title": "Zero duration task",
            "start_time": start_time,
            "end_time": end_time,
            "member_id": 1,
        }

        async_session.rollback = AsyncMock()

        with pytest.raises(ValueError, match="结束时间必须晚于开始时间"):
            await service.create_assistance_task(task_data, creator_id=1)

        await async_session.rollback.assert_called_once()


@pytest.fixture
def sample_member():
    """Create a sample member for testing"""
    return Member(
        id=1,
        username="testuser",
        student_id="202501001",
        name="Test Member",
        role=UserRole.MEMBER,
        is_active=True,
    )


@pytest.fixture
def sample_repair_task():
    """Create a sample repair task for testing"""
    return RepairTask(
        id=1,
        task_id="T202501270001",
        title="Test Repair Task",
        description="Test description",
        category=TaskCategory.NETWORK_REPAIR,
        priority=TaskPriority.MEDIUM,
        task_type=TaskType.ONLINE,
        status=TaskStatus.PENDING,
        member_id=1,
        report_time=datetime.utcnow(),
        base_work_minutes=40,
        work_minutes=40,
    )


@pytest.fixture
def sample_monitoring_task():
    """Create a sample monitoring task for testing"""
    start_time = datetime.utcnow()
    end_time = start_time + timedelta(hours=2)

    return MonitoringTask(
        id=1,
        member_id=1,
        title="Network Monitoring",
        description="Monitor network status",
        location="Server room",
        monitoring_type="网络监控",
        start_time=start_time,
        end_time=end_time,
        work_minutes=120,
        status=TaskStatus.COMPLETED,
    )
