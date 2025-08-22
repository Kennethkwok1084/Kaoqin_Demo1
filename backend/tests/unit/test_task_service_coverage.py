"""
Comprehensive tests for TaskService
Generated to improve test coverage to 90%+
"""

from datetime import datetime, timedelta
from unittest.mock import AsyncMock, Mock, patch

import pytest

from app.models.member import Member, UserRole
from app.models.task import (
    RepairTask,
    TaskCategory,
    TaskPriority,
    TaskStatus,
    TaskType,
)
from app.services.task_service import TaskService


@pytest.mark.asyncio
class TestTaskService:
    """Comprehensive TaskService tests for improved coverage"""

    async def test_service_initialization(self, async_session):
        """Test TaskService initialization"""
        service = TaskService(async_session)
        assert service is not None
        assert service.db == async_session
        assert service.work_hours_service is not None
        assert service.rush_task_service is not None

    async def test_create_repair_task_basic(self, async_session, sample_member):
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
                "assigned_to": sample_member.id,
                "reporter_name": "Test User",
                "reporter_contact": "test@example.com",
            }

            # Mock flush and add methods
            async_session.add = Mock()
            async_session.flush = AsyncMock()

            task = await service.create_repair_task(task_data, creator_id=1)

            assert task.title == "Network repair test"
            assert task.task_id == "T202501270001"
            assert task.category == TaskCategory.NETWORK_REPAIR
            assert task.priority == TaskPriority.HIGH
            assert task.task_type == TaskType.ONLINE
            assert task.member_id == sample_member.id
            assert async_session.add.called
            async_session.flush.assert_called_once()

    async def test_create_repair_task_with_tags(self, async_session, sample_member):
        """Test repair task creation with tags"""
        service = TaskService(async_session)

        with (
            patch.object(service, "_generate_task_id", return_value="T202501270002"),
            patch.object(
                service, "_add_tags_to_task", return_value=None
            ) as mock_add_tags,
        ):

            task_data = {
                "title": "Tagged task",
                "assigned_to": sample_member.id,
                "tag_ids": [1, 2, 3],
            }

            async_session.add = Mock()
            async_session.flush = AsyncMock()

            await service.create_repair_task(task_data, creator_id=1)

            mock_add_tags.assert_called_once()

    async def test_create_repair_task_rush_order(self, async_session, sample_member):
        """Test rush order task creation"""
        service = TaskService(async_session)

        with (
            patch.object(service, "_generate_task_id", return_value="T202501270003"),
            patch.object(service, "_add_rush_tag", return_value=None) as mock_rush_tag,
        ):

            task_data = {
                "title": "Rush task",
                "assigned_to": sample_member.id,
                "is_rush_order": True,
            }

            async_session.add = Mock()
            async_session.flush = AsyncMock()

            await service.create_repair_task(task_data, creator_id=1)

            mock_rush_tag.assert_called_once()

    async def test_get_repair_task_existing(self, async_session):
        """Test getting existing repair task"""
        service = TaskService(async_session)

        # Mock database query
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = RepairTask(
            id=1, task_id="T001", title="Test Task"
        )

        with patch.object(async_session, "execute", return_value=mock_result):
            task = await service.get_repair_task(task_id=1)

            assert task is not None
            assert task.id == 1
            assert task.task_id == "T001"

    async def test_get_repair_task_not_found(self, async_session):
        """Test getting non-existent repair task"""
        service = TaskService(async_session)

        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = None

        with patch.object(async_session, "execute", return_value=mock_result):
            task = await service.get_repair_task(task_id=999)

            assert task is None

    async def test_update_task_status_to_in_progress(self, async_session):
        """Test updating task status to in progress"""
        service = TaskService(async_session)

        # Create a mock task
        task = RepairTask(
            id=1, task_id="T001", title="Test Task", status=TaskStatus.PENDING
        )

        with patch.object(service, "get_repair_task", return_value=task):
            async_session.commit = AsyncMock()

            updated_task = await service.update_task_status(
                task_id=1, status=TaskStatus.IN_PROGRESS, member_id=1
            )

            assert updated_task.status == TaskStatus.IN_PROGRESS
            assert updated_task.response_time is not None
            await async_session.commit.assert_called_once()

    async def test_update_task_status_to_completed(self, async_session):
        """Test updating task status to completed"""
        service = TaskService(async_session)

        task = RepairTask(
            id=1, task_id="T001", title="Test Task", status=TaskStatus.IN_PROGRESS
        )

        with (
            patch.object(service, "get_repair_task", return_value=task),
            patch.object(service, "recalculate_task_work_hours", return_value=None),
        ):
            async_session.commit = AsyncMock()

            updated_task = await service.update_task_status(
                task_id=1, status=TaskStatus.COMPLETED, member_id=1
            )

            assert updated_task.status == TaskStatus.COMPLETED
            assert updated_task.completion_time is not None
            await async_session.commit.assert_called_once()

    async def test_get_tasks_by_member(self, async_session):
        """Test getting tasks by member"""
        service = TaskService(async_session)

        mock_tasks = [
            RepairTask(id=1, task_id="T001", title="Task 1", member_id=1),
            RepairTask(id=2, task_id="T002", title="Task 2", member_id=1),
        ]

        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = mock_tasks

        with patch.object(async_session, "execute", return_value=mock_result):
            tasks = await service.get_tasks_by_member(member_id=1)

            assert len(tasks) == 2
            assert all(task.member_id == 1 for task in tasks)

    async def test_get_tasks_by_status(self, async_session):
        """Test getting tasks by status"""
        service = TaskService(async_session)

        mock_tasks = [
            RepairTask(id=1, task_id="T001", title="Task 1", status=TaskStatus.PENDING),
            RepairTask(id=2, task_id="T002", title="Task 2", status=TaskStatus.PENDING),
        ]

        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = mock_tasks

        with patch.object(async_session, "execute", return_value=mock_result):
            tasks = await service.get_tasks_by_status(status=TaskStatus.PENDING)

            assert len(tasks) == 2
            assert all(task.status == TaskStatus.PENDING for task in tasks)

    async def test_assign_task_to_member(self, async_session, sample_member):
        """Test assigning task to member"""
        service = TaskService(async_session)

        task = RepairTask(id=1, task_id="T001", title="Test Task", member_id=None)

        with patch.object(service, "get_repair_task", return_value=task):
            async_session.commit = AsyncMock()

            updated_task = await service.assign_task(
                task_id=1, member_id=sample_member.id, assigner_id=1
            )

            assert updated_task.member_id == sample_member.id
            await async_session.commit.assert_called_once()

    async def test_add_task_rating_positive(self, async_session):
        """Test adding positive rating to task"""
        service = TaskService(async_session)

        task = RepairTask(
            id=1,
            task_id="T001",
            title="Test Task",
            status=TaskStatus.COMPLETED,
            rating=None,
        )

        with (
            patch.object(service, "get_repair_task", return_value=task),
            patch.object(service, "recalculate_task_work_hours", return_value=None),
        ):
            async_session.commit = AsyncMock()

            updated_task = await service.add_task_rating(
                task_id=1, rating=5, feedback="Great service!"
            )

            assert updated_task.rating == 5
            assert updated_task.feedback == "Great service!"
            await async_session.commit.assert_called_once()

    async def test_add_task_rating_negative(self, async_session):
        """Test adding negative rating to task"""
        service = TaskService(async_session)

        task = RepairTask(
            id=1,
            task_id="T001",
            title="Test Task",
            status=TaskStatus.COMPLETED,
            rating=None,
        )

        with (
            patch.object(service, "get_repair_task", return_value=task),
            patch.object(service, "recalculate_task_work_hours", return_value=None),
        ):
            async_session.commit = AsyncMock()

            updated_task = await service.add_task_rating(
                task_id=1, rating=2, feedback="Poor service"
            )

            assert updated_task.rating == 2
            assert updated_task.feedback == "Poor service"
            await async_session.commit.assert_called_once()

    async def test_get_overdue_tasks(self, async_session):
        """Test getting overdue tasks"""
        service = TaskService(async_session)

        # Create overdue tasks (older than 24 hours for response, 48 hours for
        # completion)
        old_time = datetime.utcnow() - timedelta(hours=25)
        mock_tasks = [
            RepairTask(
                id=1,
                task_id="T001",
                title="Overdue Task 1",
                status=TaskStatus.PENDING,
                report_time=old_time,
            ),
            RepairTask(
                id=2,
                task_id="T002",
                title="Overdue Task 2",
                status=TaskStatus.IN_PROGRESS,
                response_time=old_time,
            ),
        ]

        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = mock_tasks

        with patch.object(async_session, "execute", return_value=mock_result):
            tasks = await service.get_overdue_tasks()

            assert len(tasks) == 2

    async def test_delete_task(self, async_session):
        """Test deleting a task"""
        service = TaskService(async_session)

        task = RepairTask(id=1, task_id="T001", title="Test Task")

        with patch.object(service, "get_repair_task", return_value=task):
            async_session.delete = Mock()
            async_session.commit = AsyncMock()

            result = await service.delete_task(task_id=1)

            assert result is True
            async_session.delete.assert_called_once_with(task)
            await async_session.commit.assert_called_once()

    async def test_delete_task_not_found(self, async_session):
        """Test deleting non-existent task"""
        service = TaskService(async_session)

        with patch.object(service, "get_repair_task", return_value=None):
            result = await service.delete_task(task_id=999)

            assert result is False

    async def test_generate_task_id(self, async_session):
        """Test task ID generation"""
        service = TaskService(async_session)

        # Mock the database query for counting tasks
        mock_result = Mock()
        mock_result.scalar.return_value = 5  # 5 existing tasks

        with patch.object(async_session, "execute", return_value=mock_result):
            task_id = await service._generate_task_id()

            # Should generate format: T{YYYYMMDD}{NNNN}
            assert task_id.startswith("T")
            assert len(task_id) == 13  # T + 8 digits date + 4 digits counter
            assert task_id[1:9] == datetime.now().strftime("%Y%m%d")
            assert task_id[9:] == "0006"  # Next counter after 5 existing

    @pytest.mark.parametrize(
        "task_type,expected_minutes", [(TaskType.ONLINE, 40), (TaskType.OFFLINE, 100)]
    )
    async def test_base_work_minutes_calculation(
        self, async_session, task_type, expected_minutes
    ):
        """Test base work minutes calculation for different task types"""
        service = TaskService(async_session)

        task_data = {"title": "Test task", "task_type": task_type}

        with patch.object(service, "_generate_task_id", return_value="T202501270001"):
            async_session.add = Mock()
            async_session.flush = AsyncMock()

            task = await service.create_repair_task(task_data, creator_id=1)

            assert task.base_work_minutes == expected_minutes

    async def test_error_handling_invalid_task_data(self, async_session):
        """Test error handling for invalid task data"""
        service = TaskService(async_session)

        # Missing required title field
        invalid_task_data = {"description": "No title provided"}

        with pytest.raises(Exception):  # Should raise some validation error
            await service.create_repair_task(invalid_task_data, creator_id=1)

    async def test_bulk_task_operations(self, async_session):
        """Test bulk operations on multiple tasks"""
        service = TaskService(async_session)

        mock_tasks = [
            RepairTask(id=1, task_id="T001", title="Task 1", status=TaskStatus.PENDING),
            RepairTask(id=2, task_id="T002", title="Task 2", status=TaskStatus.PENDING),
            RepairTask(id=3, task_id="T003", title="Task 3", status=TaskStatus.PENDING),
        ]

        with patch.object(service, "get_tasks_by_status", return_value=mock_tasks):
            async_session.commit = AsyncMock()

            # Mock bulk status update
            result = await service.bulk_update_status(
                task_ids=[1, 2, 3], new_status=TaskStatus.IN_PROGRESS
            )

            assert len(result) == 3
            assert all(task.status == TaskStatus.IN_PROGRESS for task in result)


@pytest.fixture
async def sample_member(async_session):
    """Create a sample member for testing"""
    member = Member(
        id=1,
        username="testmember",
        student_id="202501001",
        name="Test Member",
        role=UserRole.MEMBER,
        is_active=True,
    )
    return member
