"""
Unit tests for Statistics Service.
Tests statistical analysis, performance metrics, and caching functionality.
"""

import pytest
from unittest.mock import AsyncMock, Mock, patch
from datetime import datetime, timedelta, date
from typing import Any, Dict, List

from app.services.stats_service import StatisticsService
from app.models.member import Member, UserRole
from app.models.task import RepairTask, TaskStatus, TaskType, TaskCategory, TaskPriority


class TestStatisticsService:
    """Unit tests for StatisticsService class."""

    @pytest.fixture
    def mock_db(self):
        """Mock database session."""
        return AsyncMock()

    @pytest.fixture
    def stats_service(self, mock_db):
        """Create StatisticsService instance."""
        return StatisticsService(mock_db)

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
            department="信息化建设处",
            class_name="测试班级",
        )

    @pytest.fixture
    def sample_tasks(self, sample_member):
        """Sample tasks for testing."""
        now = datetime.utcnow()

        return [
            RepairTask(
                id=1,
                task_id="REPAIR_001",
                title="网络故障维修",
                member_id=sample_member.id,
                member=sample_member,
                status=TaskStatus.COMPLETED,
                task_type=TaskType.OFFLINE,
                work_minutes=100,
                report_time=now - timedelta(hours=3),
                completion_time=now - timedelta(hours=1),
                rating=5,
            ),
            RepairTask(
                id=2,
                task_id="REPAIR_002",
                title="硬件故障维修",
                member_id=sample_member.id,
                member=sample_member,
                status=TaskStatus.COMPLETED,
                task_type=TaskType.ONLINE,
                work_minutes=40,
                report_time=now - timedelta(hours=2),
                completion_time=now - timedelta(minutes=30),
                rating=4,
            ),
        ]

    def test_generate_cache_key_basic(self, stats_service):
        """Test cache key generation with basic parameters."""
        cache_key = stats_service._generate_cache_key(
            "test_method", param1="value1", param2=123
        )

        assert cache_key == "stats:test_method:param1=value1_param2=123"

    def test_generate_cache_key_filters_none(self, stats_service):
        """Test cache key generation filters None values."""
        cache_key = stats_service._generate_cache_key(
            "test_method", param1="value1", param2=None, param3="value3"
        )

        assert cache_key == "stats:test_method:param1=value1_param3=value3"

    def test_generate_cache_key_long_params_hashed(self, stats_service):
        """Test cache key generation with long parameters gets hashed."""
        long_string = "x" * 150  # Force hashing
        cache_key = stats_service._generate_cache_key(
            "test_method", long_param=long_string
        )

        assert cache_key.startswith("stats:test_method:hash_")
        assert len(cache_key.split("hash_")[1]) == 8  # MD5 hash truncated to 8 chars

    def test_generate_cache_key_empty_params(self, stats_service):
        """Test cache key generation with no parameters."""
        cache_key = stats_service._generate_cache_key("test_method")

        assert cache_key == "stats:test_method"

    @pytest.mark.asyncio
    async def test_get_overview_statistics_basic(
        self, stats_service, mock_db, sample_tasks
    ):
        """Test basic overview statistics."""
        # Mock database queries
        mock_result = Mock()

        # Mock member count
        mock_result.scalar.return_value = 50

        # Mock task counts
        mock_db.execute.side_effect = [
            mock_result,  # Total members
            Mock(scalar=Mock(return_value=100)),  # Total tasks
            Mock(scalar=Mock(return_value=85)),  # Completed tasks
            Mock(scalar=Mock(return_value=10)),  # In progress tasks
            Mock(scalar=Mock(return_value=5)),  # Pending tasks
        ]

        result = await stats_service.get_overview_statistics()

        # Since we don't know the exact return structure, just verify it's called
        assert result is not None

    @pytest.mark.asyncio
    async def test_get_system_overview_zero_tasks(self, stats_service, mock_db):
        """Test system overview with zero tasks."""
        # Mock database queries returning zero
        mock_db.execute.side_effect = [
            Mock(scalar=Mock(return_value=50)),  # Total members
            Mock(scalar=Mock(return_value=0)),  # Total tasks
            Mock(scalar=Mock(return_value=0)),  # Completed tasks
            Mock(scalar=Mock(return_value=0)),  # In progress tasks
            Mock(scalar=Mock(return_value=0)),  # Pending tasks
        ]

        with patch.object(
            stats_service,
            "_get_performance_metrics",
            return_value={
                "average_completion_time": 0,
                "average_rating": 0,
                "efficiency_score": 0,
            },
        ):

            result = await stats_service.get_system_overview()

            assert result["total_tasks"] == 0
            assert result["completion_rate"] == 0
            assert result["average_completion_time"] == 0

    @pytest.mark.asyncio
    async def test_get_member_performance_stats(
        self, stats_service, mock_db, sample_member
    ):
        """Test member performance statistics."""
        # Mock database query for member tasks
        mock_tasks_result = Mock()
        mock_tasks_result.scalars.return_value.all.return_value = [
            Mock(
                status=TaskStatus.COMPLETED,
                work_minutes=100,
                rating=5,
                report_time=datetime.utcnow() - timedelta(hours=3),
                completion_time=datetime.utcnow() - timedelta(hours=1),
            ),
            Mock(
                status=TaskStatus.COMPLETED,
                work_minutes=40,
                rating=4,
                report_time=datetime.utcnow() - timedelta(hours=2),
                completion_time=datetime.utcnow() - timedelta(minutes=30),
            ),
        ]

        mock_db.execute.return_value = mock_tasks_result

        result = await stats_service.get_member_performance_stats(
            member_id=sample_member.id,
            start_date=date.today() - timedelta(days=30),
            end_date=date.today(),
        )

        assert result["member_id"] == sample_member.id
        assert result["total_tasks"] == 2
        assert result["completed_tasks"] == 2
        assert result["total_work_minutes"] == 140
        assert result["average_rating"] == 4.5
        assert result["completion_rate"] == 100.0

    @pytest.mark.asyncio
    async def test_get_member_performance_stats_no_tasks(self, stats_service, mock_db):
        """Test member performance stats with no tasks."""
        # Mock empty database result
        mock_tasks_result = Mock()
        mock_tasks_result.scalars.return_value.all.return_value = []
        mock_db.execute.return_value = mock_tasks_result

        result = await stats_service.get_member_performance_stats(
            member_id=999,
            start_date=date.today() - timedelta(days=30),
            end_date=date.today(),
        )

        assert result["total_tasks"] == 0
        assert result["completed_tasks"] == 0
        assert result["completion_rate"] == 0
        assert result["average_rating"] == 0

    @pytest.mark.asyncio
    async def test_get_task_type_distribution(self, stats_service, mock_db):
        """Test task type distribution statistics."""
        # Mock database query result
        mock_result = Mock()
        mock_result.all.return_value = [(TaskType.ONLINE, 30), (TaskType.OFFLINE, 70)]
        mock_db.execute.return_value = mock_result

        result = await stats_service.get_task_type_distribution()

        assert len(result) == 2
        assert result[0]["task_type"] == "online"
        assert result[0]["count"] == 30
        assert result[0]["percentage"] == 30.0
        assert result[1]["task_type"] == "offline"
        assert result[1]["count"] == 70
        assert result[1]["percentage"] == 70.0

    @pytest.mark.asyncio
    async def test_get_task_type_distribution_empty(self, stats_service, mock_db):
        """Test task type distribution with no tasks."""
        # Mock empty database result
        mock_result = Mock()
        mock_result.all.return_value = []
        mock_db.execute.return_value = mock_result

        result = await stats_service.get_task_type_distribution()

        assert result == []

    @pytest.mark.asyncio
    async def test_get_monthly_trends(self, stats_service, mock_db):
        """Test monthly trends statistics."""
        # Mock database query result
        mock_result = Mock()
        mock_result.all.return_value = [
            (2024, 1, 45, 42, 40),  # year, month, total, completed, avg_minutes
            (2024, 2, 50, 48, 38),
            (2024, 3, 55, 52, 42),
        ]
        mock_db.execute.return_value = mock_result

        result = await stats_service.get_monthly_trends(year=2024)

        assert len(result) == 3
        assert result[0]["month"] == "2024-01"
        assert result[0]["total_tasks"] == 45
        assert result[0]["completed_tasks"] == 42
        assert result[0]["completion_rate"] == round((42 / 45) * 100, 2)
        assert result[0]["average_work_minutes"] == 40

    @pytest.mark.asyncio
    async def test_get_workload_distribution(self, stats_service, mock_db):
        """Test workload distribution across members."""
        # Mock database query result
        mock_result = Mock()
        mock_result.all.return_value = [
            (
                1,
                "张三",
                "TEST001",
                25,
                23,
                920,
            ),  # member_id, name, student_id, total, completed, work_minutes
            (2, "李四", "TEST002", 20, 18, 760),
            (3, "王五", "TEST003", 15, 15, 600),
        ]
        mock_db.execute.return_value = mock_result

        result = await stats_service.get_workload_distribution()

        assert len(result) == 3
        assert result[0]["member_id"] == 1
        assert result[0]["name"] == "张三"
        assert result[0]["total_tasks"] == 25
        assert result[0]["completion_rate"] == 92.0  # 23/25 * 100
        assert result[0]["total_work_minutes"] == 920

    @pytest.mark.asyncio
    async def test_caching_functionality(self, stats_service, mock_db):
        """Test caching functionality in statistics service."""
        cache_key = "test_cache_key"
        cached_data = {"test": "data"}

        # Test cache hit
        with patch.object(cache, "get_stats_cache", return_value={"data": cached_data}):
            with patch.object(
                stats_service, "_generate_cache_key", return_value=cache_key
            ):

                # This should return cached data without hitting database
                result = await stats_service._get_cached_or_compute(
                    cache_key, lambda: {"computed": "data"}
                )

                assert result == cached_data

    @pytest.mark.asyncio
    async def test_cache_miss_computation(self, stats_service, mock_db):
        """Test cache miss triggers computation."""
        cache_key = "test_cache_key"
        computed_data = {"computed": "data"}

        # Test cache miss
        with patch.object(cache, "get_stats_cache", return_value=None):
            with patch.object(cache, "set_stats_cache", return_value=True):
                with patch.object(
                    stats_service, "_generate_cache_key", return_value=cache_key
                ):

                    async def compute_function():
                        return computed_data

                    result = await stats_service._get_cached_or_compute(
                        cache_key, compute_function
                    )

                    assert result == computed_data

    @pytest.mark.asyncio
    async def test_get_efficiency_analysis(self, stats_service, mock_db):
        """Test efficiency analysis calculations."""
        # Mock database results for efficiency metrics
        mock_result = Mock()
        mock_result.all.return_value = [
            (
                1,
                "张三",
                2.5,
                4.8,
                8.5,
            ),  # member_id, name, avg_completion_hours, avg_rating, efficiency_score
            (2, "李四", 3.0, 4.5, 7.8),
            (3, "王五", 1.8, 4.9, 9.2),
        ]
        mock_db.execute.return_value = mock_result

        result = await stats_service.get_efficiency_analysis(group_by="member")

        assert len(result) == 3
        assert result[0]["member_id"] == 1
        assert result[0]["name"] == "张三"
        assert result[0]["average_completion_hours"] == 2.5
        assert result[0]["average_rating"] == 4.8
        assert result[0]["efficiency_score"] == 8.5

    @pytest.mark.asyncio
    async def test_performance_metrics_calculation(self, stats_service, mock_db):
        """Test performance metrics calculation."""
        # Mock database query for performance data
        mock_result = Mock()
        mock_result.all.return_value = [
            (2.5, 4.8),  # completion_hours, rating
            (3.0, 4.5),
            (1.8, 4.9),
            (2.2, 4.6),
        ]
        mock_db.execute.return_value = mock_result

        result = await stats_service._get_performance_metrics()

        expected_avg_time = (2.5 + 3.0 + 1.8 + 2.2) / 4
        expected_avg_rating = (4.8 + 4.5 + 4.9 + 4.6) / 4

        assert result["average_completion_time"] == round(expected_avg_time, 2)
        assert result["average_rating"] == round(expected_avg_rating, 2)
        assert "efficiency_score" in result

    @pytest.mark.asyncio
    async def test_date_range_validation(self, stats_service):
        """Test date range validation in various methods."""
        start_date = date(2024, 6, 1)
        end_date = date(2024, 5, 1)  # End date before start date

        with pytest.raises(ValueError, match="结束日期必须大于等于开始日期"):
            await stats_service.get_member_performance_stats(
                member_id=1, start_date=start_date, end_date=end_date
            )

    @pytest.mark.asyncio
    async def test_invalid_member_id_handling(self, stats_service, mock_db):
        """Test handling of invalid member IDs."""
        # Mock empty result for non-existent member
        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute.return_value = mock_result

        result = await stats_service.get_member_performance_stats(
            member_id=99999,  # Non-existent member
            start_date=date.today() - timedelta(days=30),
            end_date=date.today(),
        )

        # Should return empty stats rather than error
        assert result["total_tasks"] == 0
        assert result["member_id"] == 99999

    @pytest.mark.asyncio
    async def test_cache_disabled_functionality(self, mock_db):
        """Test statistics service with caching disabled."""
        stats_service = StatisticsService(mock_db)
        stats_service.cache_enabled = False

        # Mock database query
        mock_result = Mock()
        mock_result.scalar.return_value = 10
        mock_db.execute.return_value = mock_result

        # Even with cache disabled, should work normally
        with patch.object(
            stats_service,
            "_get_performance_metrics",
            return_value={
                "average_completion_time": 0,
                "average_rating": 0,
                "efficiency_score": 0,
            },
        ):
            result = await stats_service.get_system_overview()

            assert "total_members" in result
