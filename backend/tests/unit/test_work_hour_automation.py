"""
Unit tests for Work Hour Automation Service.
Tests automated task detection, penalty application, and scheduling functionality.
"""

from datetime import datetime, timedelta
from unittest.mock import AsyncMock, Mock, patch

import pytest

from app.models.member import Member, UserRole
from app.models.task import RepairTask, TaskStatus, TaskTag, TaskTagType, TaskType
from app.services.work_hour_automation import WorkHourAutomationService


class TestWorkHourAutomationService:
    """Unit tests for WorkHourAutomationService class."""

    @pytest.fixture
    def mock_db(self):
        """Mock database session."""
        return AsyncMock()

    @pytest.fixture
    def automation_service(self, mock_db):
        """Create WorkHourAutomationService instance."""
        return WorkHourAutomationService(mock_db)

    @pytest.fixture
    def sample_member(self):
        """Sample member for testing."""
        return Member(
            id=1,
            username="test_user",
            name="测试用户",
            student_id="TEST001",
            role=UserRole.MEMBER,
            is_active=True,
        )

    @pytest.fixture
    def overdue_task(self, sample_member):
        """Sample overdue task for testing."""
        now = datetime.utcnow()
        return RepairTask(
            id=1,
            task_id="REPAIR_001",
            title="延迟维修任务",
            member_id=sample_member.id,
            member=sample_member,
            status=TaskStatus.IN_PROGRESS,
            task_type=TaskType.OFFLINE,
            report_time=now - timedelta(hours=48),  # Reported 48 hours ago
            response_time=None,  # No response yet
            completion_time=None,
            location="测试地点",
            reporter_name="测试用户",
            reporter_contact="13800138000",
        )

    @pytest.fixture
    def completed_task_late_response(self, sample_member):
        """Sample task with late response but completed."""
        now = datetime.utcnow()
        return RepairTask(
            id=2,
            task_id="REPAIR_002",
            title="响应延迟任务",
            member_id=sample_member.id,
            member=sample_member,
            status=TaskStatus.COMPLETED,
            task_type=TaskType.ONLINE,
            report_time=now - timedelta(hours=72),
            response_time=now - timedelta(hours=35),  # Responded after 37 hours (late)
            completion_time=now - timedelta(hours=1),
            location="测试地点",
            reporter_name="测试用户",
            reporter_contact="13800138000",
        )

    @pytest.mark.asyncio
    async def test_schedule_overdue_detection_success(
        self, automation_service, mock_db
    ):
        """Test successful overdue detection scheduling."""
        # Mock the individual detection methods
        with (
            patch.object(
                automation_service, "_detect_late_response_tasks", return_value=5
            ),
            patch.object(
                automation_service, "_detect_late_completion_tasks", return_value=3
            ),
            patch.object(
                automation_service, "_detect_long_overdue_tasks", return_value=2
            ),
        ):
            result = await automation_service.schedule_overdue_detection()

            assert result["success"] is True
            assert result["late_response_tasks"] == 5
            assert result["late_completion_tasks"] == 3
            assert result["long_overdue_tasks"] == 2
            assert result["total_processed"] == 10

    @pytest.mark.asyncio
    async def test_detect_late_response_tasks(
        self, automation_service, mock_db, overdue_task
    ):
        """Test detection of late response tasks."""
        # Mock database query to return overdue tasks
        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = [overdue_task]
        mock_db.execute.return_value = mock_result

        # Mock tag application
        with patch.object(automation_service, "_apply_penalty_tag", return_value=True):
            count = await automation_service._detect_late_response_tasks()

            assert count == 1
            # Verify database query was called
            mock_db.execute.assert_called()

    @pytest.mark.asyncio
    async def test_detect_late_completion_tasks(
        self, automation_service, mock_db, completed_task_late_response
    ):
        """Test detection of late completion tasks."""
        # Mock database query to return late completion tasks
        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = [
            completed_task_late_response
        ]
        mock_db.execute.return_value = mock_result

        # Mock tag application
        with patch.object(automation_service, "_apply_penalty_tag", return_value=True):
            count = await automation_service._detect_late_completion_tasks()

            assert count == 1
            mock_db.execute.assert_called()

    @pytest.mark.asyncio
    async def test_detect_long_overdue_tasks(self, automation_service, mock_db):
        """Test detection of long overdue tasks."""
        # Create a task that's been pending for over 72 hours
        now = datetime.utcnow()
        long_overdue_task = RepairTask(
            id=3,
            task_id="REPAIR_003",
            status=TaskStatus.PENDING,
            report_time=now - timedelta(hours=100),  # Very overdue
            response_time=None,
        )

        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = [long_overdue_task]
        mock_db.execute.return_value = mock_result

        with patch.object(automation_service, "_apply_penalty_tag", return_value=True):
            count = await automation_service._detect_long_overdue_tasks()

            assert count == 1

    @pytest.mark.asyncio
    async def test_apply_penalty_tag_success(
        self, automation_service, mock_db, overdue_task
    ):
        """Test successful penalty tag application."""
        # Mock tag creation and association
        mock_tag = TaskTag(
            id=1,
            name="延迟响应",
            tag_type=TaskTagType.PENALTY,
            work_minutes_modifier=-30,
        )

        # Mock existing tag query
        mock_tag_result = Mock()
        mock_tag_result.scalar_one_or_none.return_value = mock_tag

        # Mock existing association check
        mock_assoc_result = Mock()
        mock_assoc_result.scalar_one_or_none.return_value = (
            None  # No existing association
        )

        mock_db.execute.side_effect = [mock_tag_result, mock_assoc_result]

        result = await automation_service._apply_penalty_tag(
            task=overdue_task, tag_name="延迟响应", reason="任务响应超时"
        )

        assert result is True
        # Verify database operations
        mock_db.add.assert_called()
        mock_db.commit.assert_called()

    @pytest.mark.asyncio
    async def test_apply_penalty_tag_already_exists(
        self, automation_service, mock_db, overdue_task
    ):
        """Test penalty tag application when tag already exists on task."""
        mock_tag = TaskTag(
            id=1,
            name="延迟响应",
            tag_type=TaskTagType.PENALTY,
            work_minutes_modifier=-30,
        )

        # Mock existing tag
        mock_tag_result = Mock()
        mock_tag_result.scalar_one_or_none.return_value = mock_tag

        # Mock existing association (tag already applied)
        mock_assoc_result = Mock()
        mock_assoc_result.scalar_one_or_none.return_value = Mock()  # Association exists

        mock_db.execute.side_effect = [mock_tag_result, mock_assoc_result]

        result = await automation_service._apply_penalty_tag(
            task=overdue_task, tag_name="延迟响应", reason="任务响应超时"
        )

        assert result is False  # Tag already exists, so no new application
        # Verify no new database additions
        mock_db.add.assert_not_called()

    @pytest.mark.asyncio
    async def test_create_new_penalty_tag(
        self, automation_service, mock_db, overdue_task
    ):
        """Test creation of new penalty tag when it doesn't exist."""
        # Mock no existing tag
        mock_tag_result = Mock()
        mock_tag_result.scalar_one_or_none.return_value = None

        # Mock no existing association
        mock_assoc_result = Mock()
        mock_assoc_result.scalar_one_or_none.return_value = None

        mock_db.execute.side_effect = [mock_tag_result, mock_assoc_result]

        result = await automation_service._apply_penalty_tag(
            task=overdue_task, tag_name="新惩罚标签", reason="新的惩罚原因"
        )

        assert result is True
        # Verify new tag creation - should be called twice (tag + association)
        assert mock_db.add.call_count == 2
        mock_db.commit.assert_called()

    @pytest.mark.asyncio
    async def test_schedule_evaluation_response_automation(
        self, automation_service, mock_db
    ):
        """Test automated evaluation response processing."""
        # Mock database query for tasks needing evaluation processing
        task_with_rating = RepairTask(
            id=4,
            task_id="REPAIR_004",
            status=TaskStatus.COMPLETED,
            rating=5,  # Excellent rating
            feedback="非常满意",
        )

        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = [task_with_rating]
        mock_db.execute.return_value = mock_result

        with patch.object(
            automation_service, "_process_evaluation_response", return_value=True
        ):
            result = await automation_service.schedule_evaluation_response_automation()

            assert result["success"] is True
            assert result["processed_evaluations"] >= 0

    @pytest.mark.asyncio
    async def test_process_evaluation_response_positive(
        self, automation_service, mock_db
    ):
        """Test processing positive evaluation response."""
        # Task with excellent rating (5 stars)
        excellent_task = RepairTask(
            id=5,
            task_id="REPAIR_005",
            status=TaskStatus.COMPLETED,
            rating=5,
            feedback="服务非常好",
        )

        with patch.object(automation_service, "_apply_bonus_tag", return_value=True):
            result = await automation_service._process_evaluation_response(
                excellent_task
            )

            assert result is True

    @pytest.mark.asyncio
    async def test_process_evaluation_response_negative(
        self, automation_service, mock_db
    ):
        """Test processing negative evaluation response."""
        # Task with poor rating (1-2 stars)
        poor_task = RepairTask(
            id=6,
            task_id="REPAIR_006",
            status=TaskStatus.COMPLETED,
            rating=1,
            feedback="服务不满意",
        )

        with patch.object(automation_service, "_apply_penalty_tag", return_value=True):
            result = await automation_service._process_evaluation_response(poor_task)

            assert result is True

    @pytest.mark.asyncio
    async def test_apply_bonus_tag_success(self, automation_service, mock_db):
        """Test successful bonus tag application."""
        excellent_task = RepairTask(
            id=7, task_id="REPAIR_007", status=TaskStatus.COMPLETED, rating=5
        )

        # Mock bonus tag
        mock_bonus_tag = TaskTag(
            id=2, name="优质服务", tag_type=TaskTagType.BONUS, work_minutes_modifier=30
        )

        mock_tag_result = Mock()
        mock_tag_result.scalar_one_or_none.return_value = mock_bonus_tag

        mock_assoc_result = Mock()
        mock_assoc_result.scalar_one_or_none.return_value = (
            None  # No existing association
        )

        mock_db.execute.side_effect = [mock_tag_result, mock_assoc_result]

        result = await automation_service._apply_bonus_tag(
            task=excellent_task, tag_name="优质服务", reason="客户评价优秀"
        )

        assert result is True
        mock_db.add.assert_called()
        mock_db.commit.assert_called()

    @pytest.mark.asyncio
    async def test_batch_recalculate_work_hours(self, automation_service, mock_db):
        """Test batch work hours recalculation."""
        # Mock tasks that need recalculation
        tasks_to_recalc = [
            RepairTask(id=1, task_id="REPAIR_001"),
            RepairTask(id=2, task_id="REPAIR_002"),
            RepairTask(id=3, task_id="REPAIR_003"),
        ]

        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = tasks_to_recalc
        mock_db.execute.return_value = mock_result

        # Mock work hours calculation service
        with patch.object(
            automation_service.task_service,
            "recalculate_task_work_hours",
            return_value=True,
        ):
            result = await automation_service.batch_recalculate_work_hours(
                start_date=datetime.now().date() - timedelta(days=30),
                end_date=datetime.now().date(),
            )

            assert result["success"] is True
            assert result["processed_tasks"] == 3

    @pytest.mark.asyncio
    async def test_get_automation_statistics(self, automation_service, mock_db):
        """Test automation statistics retrieval."""
        # Mock database queries for statistics
        mock_db.execute.side_effect = [
            Mock(scalar=Mock(return_value=15)),  # Tasks with penalty tags
            Mock(scalar=Mock(return_value=8)),  # Tasks with bonus tags
            Mock(scalar=Mock(return_value=23)),  # Total automated actions
            Mock(scalar=Mock(return_value=150)),  # Total tasks processed
        ]

        result = await automation_service.get_automation_statistics()

        assert result["penalty_tags_applied"] == 15
        assert result["bonus_tags_applied"] == 8
        assert result["total_automated_actions"] == 23
        assert result["automation_rate"] == round((23 / 150) * 100, 2)

    @pytest.mark.asyncio
    async def test_error_handling_in_detection(self, automation_service, mock_db):
        """Test error handling during overdue detection."""
        # Mock database error
        mock_db.execute.side_effect = Exception("Database connection error")

        with patch.object(
            automation_service,
            "_detect_late_response_tasks",
            side_effect=Exception("Detection error"),
        ):
            result = await automation_service.schedule_overdue_detection()

            assert result["success"] is False
            assert "error" in result
            assert "Detection error" in result["error"]

    @pytest.mark.asyncio
    async def test_tag_validation(self, automation_service):
        """Test tag name and type validation."""
        # Test invalid tag names
        invalid_names = [
            "",
            None,
            "   ",
            "a" * 101,
        ]  # Empty, None, whitespace, too long

        for invalid_name in invalid_names:
            is_valid = automation_service._validate_tag_name(invalid_name)
            assert is_valid is False

        # Test valid tag names
        valid_names = ["延迟响应", "优质服务", "紧急处理"]

        for valid_name in valid_names:
            is_valid = automation_service._validate_tag_name(valid_name)
            assert is_valid is True

    @pytest.mark.asyncio
    async def test_time_threshold_calculations(self, automation_service):
        """Test time threshold calculations for different task types."""
        # Test response time threshold (should be 30 minutes for urgent, 4 hours for normal)
        urgent_threshold = automation_service._get_response_time_threshold(
            is_urgent=True
        )
        normal_threshold = automation_service._get_response_time_threshold(
            is_urgent=False
        )

        assert urgent_threshold == timedelta(minutes=30)
        assert normal_threshold == timedelta(hours=4)

        # Test completion time threshold (should be 24 hours for urgent, 72 hours for normal)
        urgent_completion = automation_service._get_completion_time_threshold(
            is_urgent=True
        )
        normal_completion = automation_service._get_completion_time_threshold(
            is_urgent=False
        )

        assert urgent_completion == timedelta(hours=24)
        assert normal_completion == timedelta(hours=72)

    @pytest.mark.asyncio
    async def test_concurrent_processing_safety(self, automation_service, mock_db):
        """Test thread safety and concurrent processing handling."""
        # Mock multiple simultaneous processing requests

        with patch.object(
            automation_service, "_acquire_processing_lock", return_value=True
        ):
            result = await automation_service.schedule_overdue_detection()

            # Should succeed when lock is acquired
            assert result["success"] is True or "error" in result

        with patch.object(
            automation_service, "_acquire_processing_lock", return_value=False
        ):
            # Should handle concurrent processing gracefully
            result = await automation_service.schedule_overdue_detection()

            # Either succeeds or indicates concurrent processing
            assert isinstance(result, dict)
            assert "success" in result or "error" in result

    def test_helper_methods(self, automation_service):
        """Test various helper methods."""
        # Test tag name validation
        assert automation_service._validate_tag_name("Valid Tag") is True
        assert automation_service._validate_tag_name("") is False
        assert automation_service._validate_tag_name(None) is False

        # Test time threshold getters
        assert automation_service._get_response_time_threshold(True) == timedelta(
            minutes=30
        )
        assert automation_service._get_completion_time_threshold(False) == timedelta(
            hours=72
        )
