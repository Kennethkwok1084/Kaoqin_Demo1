"""
Exception handling tests for WorkHoursCalculationService.
Tests input validation and error handling for core service methods.
"""

from datetime import date, datetime, timedelta
from unittest.mock import AsyncMock, Mock

import pytest
from app.models.member import Member, UserRole
from app.models.task import RepairTask, TaskStatus, TaskType
from app.services.work_hours_service import (
    RushTaskMarkingService,
    WorkHoursCalculationService,
)


class TestWorkHoursServiceExceptions:
    """Test exception handling in WorkHoursCalculationService."""

    @pytest.fixture
    def work_hours_service(self):
        """Create WorkHoursCalculationService with mocked database."""
        mock_db = AsyncMock()
        return WorkHoursCalculationService(mock_db)

    @pytest.fixture
    def rush_service(self):
        """Create RushTaskMarkingService with mocked database."""
        mock_db = AsyncMock()
        return RushTaskMarkingService(mock_db)

    # Test calculate_task_work_minutes validation

    @pytest.mark.asyncio
    async def test_calculate_task_work_minutes_none_task(self, work_hours_service):
        """Test calculate_task_work_minutes with None task."""
        with pytest.raises(ValueError, match="任务对象不能为空"):
            await work_hours_service.calculate_task_work_minutes(None)

    @pytest.mark.asyncio
    async def test_calculate_task_work_minutes_invalid_task_id(
        self, work_hours_service
    ):
        """Test calculate_task_work_minutes with invalid task ID."""
        mock_task = Mock()
        mock_task.id = None

        with pytest.raises(ValueError, match="任务ID无效"):
            await work_hours_service.calculate_task_work_minutes(mock_task)

    @pytest.mark.asyncio
    async def test_calculate_task_work_minutes_invalid_task_type(
        self, work_hours_service
    ):
        """Test calculate_task_work_minutes with invalid task type."""
        mock_task = Mock()
        mock_task.id = 1
        mock_task.task_type = None

        with pytest.raises(ValueError, match="任务类型无效"):
            await work_hours_service.calculate_task_work_minutes(mock_task)

    @pytest.mark.asyncio
    async def test_calculate_task_work_minutes_invalid_report_time(
        self, work_hours_service
    ):
        """Test calculate_task_work_minutes with invalid report time."""
        mock_task = Mock()
        mock_task.id = 1
        mock_task.task_type = TaskType.ONLINE
        mock_task.report_time = None

        with pytest.raises(ValueError, match="报修时间无效"):
            await work_hours_service.calculate_task_work_minutes(mock_task)

    @pytest.mark.asyncio
    async def test_calculate_task_work_minutes_missing_tags(self, work_hours_service):
        """Test calculate_task_work_minutes with missing tags attribute."""
        mock_task = Mock()
        mock_task.id = 1
        mock_task.task_type = TaskType.ONLINE
        mock_task.report_time = datetime.utcnow()
        # No tags attribute - should trigger refresh attempt
        del mock_task.tags

        # Mock database refresh failure
        work_hours_service.db.refresh.side_effect = Exception("Refresh failed")

        with pytest.raises(RuntimeError, match="无法加载任务 1 的标签信息"):
            await work_hours_service.calculate_task_work_minutes(mock_task)

    # Test calculate_monthly_work_hours validation

    @pytest.mark.asyncio
    async def test_calculate_monthly_work_hours_invalid_member_id(
        self, work_hours_service
    ):
        """Test calculate_monthly_work_hours with invalid member ID."""
        with pytest.raises(ValueError, match="成员ID必须为正整数"):
            await work_hours_service.calculate_monthly_work_hours(0, 2024, 1)

        with pytest.raises(ValueError, match="成员ID必须为正整数"):
            await work_hours_service.calculate_monthly_work_hours(-1, 2024, 1)

        with pytest.raises(ValueError, match="成员ID必须为正整数"):
            await work_hours_service.calculate_monthly_work_hours("invalid", 2024, 1)

    @pytest.mark.asyncio
    async def test_calculate_monthly_work_hours_invalid_year(self, work_hours_service):
        """Test calculate_monthly_work_hours with invalid year."""
        with pytest.raises(ValueError, match="年份必须在2020-2050范围内"):
            await work_hours_service.calculate_monthly_work_hours(1, 2019, 1)

        with pytest.raises(ValueError, match="年份必须在2020-2050范围内"):
            await work_hours_service.calculate_monthly_work_hours(1, 2051, 1)

        with pytest.raises(ValueError, match="年份必须在2020-2050范围内"):
            await work_hours_service.calculate_monthly_work_hours(1, "2024", 1)

    @pytest.mark.asyncio
    async def test_calculate_monthly_work_hours_invalid_month(self, work_hours_service):
        """Test calculate_monthly_work_hours with invalid month."""
        with pytest.raises(ValueError, match="月份必须在1-12范围内"):
            await work_hours_service.calculate_monthly_work_hours(1, 2024, 0)

        with pytest.raises(ValueError, match="月份必须在1-12范围内"):
            await work_hours_service.calculate_monthly_work_hours(1, 2024, 13)

        with pytest.raises(ValueError, match="月份必须在1-12范围内"):
            await work_hours_service.calculate_monthly_work_hours(1, 2024, "1")

    @pytest.mark.asyncio
    async def test_calculate_monthly_work_hours_member_not_found(
        self, work_hours_service
    ):
        """Test calculate_monthly_work_hours with non-existent member."""
        # Mock database query returning None
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = None
        work_hours_service.db.execute.return_value = mock_result

        with pytest.raises(ValueError, match="成员 999 不存在"):
            await work_hours_service.calculate_monthly_work_hours(999, 2024, 1)

    # Test update_monthly_summary validation

    @pytest.mark.asyncio
    async def test_update_monthly_summary_invalid_params(self, work_hours_service):
        """Test update_monthly_summary with invalid parameters."""
        with pytest.raises(ValueError, match="成员ID必须为正整数"):
            await work_hours_service.update_monthly_summary(-1, 2024, 1)

        with pytest.raises(ValueError, match="年份必须在2020-2050范围内"):
            await work_hours_service.update_monthly_summary(1, 2019, 1)

        with pytest.raises(ValueError, match="月份必须在1-12范围内"):
            await work_hours_service.update_monthly_summary(1, 2024, 13)

    # Test batch_update_monthly_summaries validation

    @pytest.mark.asyncio
    async def test_batch_update_monthly_summaries_invalid_year(
        self, work_hours_service
    ):
        """Test batch_update_monthly_summaries with invalid year."""
        with pytest.raises(ValueError, match="年份必须在2020-2050范围内"):
            await work_hours_service.batch_update_monthly_summaries(2019, 1)

    @pytest.mark.asyncio
    async def test_batch_update_monthly_summaries_invalid_member_ids(
        self, work_hours_service
    ):
        """Test batch_update_monthly_summaries with invalid member IDs."""
        with pytest.raises(ValueError, match="成员ID列表必须为列表类型"):
            await work_hours_service.batch_update_monthly_summaries(
                2024, 1, "not_a_list"
            )

        with pytest.raises(ValueError, match="成员ID必须为正整数"):
            await work_hours_service.batch_update_monthly_summaries(2024, 1, [1, -1, 3])

        with pytest.raises(ValueError, match="成员ID必须为正整数"):
            await work_hours_service.batch_update_monthly_summaries(
                2024, 1, [1, "invalid", 3]
            )

    # Test apply_group_penalties validation

    @pytest.mark.asyncio
    async def test_apply_group_penalties_none_task(self, work_hours_service):
        """Test apply_group_penalties with None task."""
        with pytest.raises(ValueError, match="任务对象不能为空"):
            await work_hours_service.apply_group_penalties(None, "late_response")

    @pytest.mark.asyncio
    async def test_apply_group_penalties_invalid_task_id(self, work_hours_service):
        """Test apply_group_penalties with invalid task ID."""
        mock_task = Mock()
        mock_task.id = None

        with pytest.raises(ValueError, match="任务ID无效"):
            await work_hours_service.apply_group_penalties(mock_task, "late_response")

    @pytest.mark.asyncio
    async def test_apply_group_penalties_no_member(self, work_hours_service):
        """Test apply_group_penalties with task having no member."""
        mock_task = Mock()
        mock_task.id = 1
        mock_task.member = None

        with pytest.raises(ValueError, match="任务 1 没有关联的成员"):
            await work_hours_service.apply_group_penalties(mock_task, "late_response")

    @pytest.mark.asyncio
    async def test_apply_group_penalties_invalid_penalty_type(self, work_hours_service):
        """Test apply_group_penalties with invalid penalty type."""
        mock_task = Mock()
        mock_task.id = 1
        mock_task.member = Mock()

        with pytest.raises(ValueError, match="惩罚类型无效"):
            await work_hours_service.apply_group_penalties(mock_task, "invalid_penalty")

        with pytest.raises(ValueError, match="惩罚类型无效"):
            await work_hours_service.apply_group_penalties(mock_task, 123)


class TestRushTaskMarkingServiceExceptions:
    """Test exception handling in RushTaskMarkingService."""

    @pytest.fixture
    def rush_service(self):
        """Create RushTaskMarkingService with mocked database."""
        mock_db = AsyncMock()
        return RushTaskMarkingService(mock_db)

    # Test mark_rush_tasks_by_date validation

    @pytest.mark.asyncio
    async def test_mark_rush_tasks_invalid_date_types(self, rush_service):
        """Test mark_rush_tasks_by_date with invalid date types."""
        with pytest.raises(ValueError, match="开始日期必须为date对象"):
            await rush_service.mark_rush_tasks_by_date("2024-01-01", date(2024, 1, 31))

        with pytest.raises(ValueError, match="结束日期必须为date对象"):
            await rush_service.mark_rush_tasks_by_date(date(2024, 1, 1), "2024-01-31")

    @pytest.mark.asyncio
    async def test_mark_rush_tasks_invalid_date_range(self, rush_service):
        """Test mark_rush_tasks_by_date with invalid date range."""
        date_from = date(2024, 1, 31)
        date_to = date(2024, 1, 1)  # Earlier than date_from

        with pytest.raises(ValueError, match="开始日期不能晚于结束日期"):
            await rush_service.mark_rush_tasks_by_date(date_from, date_to)

    @pytest.mark.asyncio
    async def test_mark_rush_tasks_invalid_task_ids(self, rush_service):
        """Test mark_rush_tasks_by_date with invalid task IDs."""
        date_from = date(2024, 1, 1)
        date_to = date(2024, 1, 31)

        with pytest.raises(ValueError, match="任务ID列表必须为列表类型"):
            await rush_service.mark_rush_tasks_by_date(date_from, date_to, "not_a_list")

        with pytest.raises(ValueError, match="任务ID必须为正整数"):
            await rush_service.mark_rush_tasks_by_date(date_from, date_to, [1, -1, 3])

        with pytest.raises(ValueError, match="任务ID必须为正整数"):
            await rush_service.mark_rush_tasks_by_date(
                date_from, date_to, [1, "invalid", 3]
            )

    @pytest.mark.asyncio
    async def test_mark_rush_tasks_invalid_marked_by(self, rush_service):
        """Test mark_rush_tasks_by_date with invalid marked_by."""
        date_from = date(2024, 1, 1)
        date_to = date(2024, 1, 31)

        with pytest.raises(ValueError, match="标记人ID必须为正整数"):
            await rush_service.mark_rush_tasks_by_date(date_from, date_to, marked_by=-1)

        with pytest.raises(ValueError, match="标记人ID必须为正整数"):
            await rush_service.mark_rush_tasks_by_date(
                date_from, date_to, marked_by="invalid"
            )

    # Test batch_recalculate_work_hours validation

    @pytest.mark.asyncio
    async def test_batch_recalculate_invalid_date_types(self, rush_service):
        """Test batch_recalculate_work_hours with invalid date types."""
        with pytest.raises(ValueError, match="开始日期必须为date对象"):
            await rush_service.batch_recalculate_work_hours(
                "2024-01-01", date(2024, 1, 31)
            )

        with pytest.raises(ValueError, match="结束日期必须为date对象"):
            await rush_service.batch_recalculate_work_hours(
                date(2024, 1, 1), "2024-01-31"
            )

    @pytest.mark.asyncio
    async def test_batch_recalculate_invalid_date_range(self, rush_service):
        """Test batch_recalculate_work_hours with invalid date range."""
        date_from = date(2024, 1, 31)
        date_to = date(2024, 1, 1)  # Earlier than date_from

        with pytest.raises(ValueError, match="开始日期不能晚于结束日期"):
            await rush_service.batch_recalculate_work_hours(date_from, date_to)

    @pytest.mark.asyncio
    async def test_batch_recalculate_invalid_member_ids(self, rush_service):
        """Test batch_recalculate_work_hours with invalid member IDs."""
        date_from = date(2024, 1, 1)
        date_to = date(2024, 1, 31)

        with pytest.raises(ValueError, match="成员ID列表必须为列表类型"):
            await rush_service.batch_recalculate_work_hours(
                date_from, date_to, "not_a_list"
            )

        with pytest.raises(ValueError, match="成员ID必须为正整数"):
            await rush_service.batch_recalculate_work_hours(
                date_from, date_to, [1, -1, 3]
            )

        with pytest.raises(ValueError, match="成员ID必须为正整数"):
            await rush_service.batch_recalculate_work_hours(
                date_from, date_to, [1, "invalid", 3]
            )


class TestServiceRuntimeExceptions:
    """Test runtime exception handling in services."""

    @pytest.fixture
    def work_hours_service(self):
        """Create WorkHoursCalculationService with mocked database."""
        mock_db = AsyncMock()
        return WorkHoursCalculationService(mock_db)

    @pytest.mark.asyncio
    async def test_calculate_task_work_minutes_runtime_error(self, work_hours_service):
        """Test calculate_task_work_minutes runtime error handling."""
        mock_task = Mock()
        mock_task.id = 1
        mock_task.task_type = TaskType.ONLINE
        mock_task.report_time = datetime.utcnow()
        mock_task.tags = []

        # Mock database refresh to raise unexpected error
        work_hours_service.db.refresh.side_effect = Exception(
            "Database connection lost"
        )

        with pytest.raises(RuntimeError, match="工时计算过程发生未预期错误"):
            await work_hours_service.calculate_task_work_minutes(mock_task)

    @pytest.mark.asyncio
    async def test_update_monthly_summary_runtime_error(self, work_hours_service):
        """Test update_monthly_summary runtime error handling."""
        # Mock calculate_monthly_work_hours to succeed
        work_hours_service.calculate_monthly_work_hours = AsyncMock()
        work_hours_service.calculate_monthly_work_hours.return_value = {
            "total_hours": 30.0,
            "repair_task_hours": 25.0,
        }

        # Mock database operations to fail
        work_hours_service.db.execute.side_effect = Exception("Database error")

        with pytest.raises(RuntimeError, match="更新月度汇总时出错"):
            await work_hours_service.update_monthly_summary(1, 2024, 1)

    @pytest.mark.asyncio
    async def test_batch_update_runtime_error(self, work_hours_service):
        """Test batch_update_monthly_summaries runtime error handling."""
        # Mock database operations to fail
        work_hours_service.db.execute.side_effect = Exception("Connection timeout")

        with pytest.raises(RuntimeError, match="批量更新月度汇总时出错"):
            await work_hours_service.batch_update_monthly_summaries(2024, 1)

    @pytest.mark.asyncio
    async def test_apply_group_penalties_runtime_error(self, work_hours_service):
        """Test apply_group_penalties runtime error handling."""
        mock_task = Mock()
        mock_task.id = 1
        mock_task.member = Mock()
        mock_task.member.department = "IT"

        # Mock database operations to fail
        work_hours_service.db.execute.side_effect = Exception("Database error")

        with pytest.raises(RuntimeError, match="应用组内惩罚时出错"):
            await work_hours_service.apply_group_penalties(mock_task, "late_response")
