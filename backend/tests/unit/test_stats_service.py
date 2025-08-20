"""
Unit tests for Statistics Service.
Tests statistical analysis, performance metrics, and caching functionality.
"""

from datetime import date, datetime, timedelta
from unittest.mock import AsyncMock, Mock, patch

import pytest

from app.core.cache import cache
from app.models.member import Member, UserRole
from app.models.task import RepairTask, TaskStatus, TaskType
from app.services.stats_service import StatisticsService


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
    async def test_get_overview_statistics_basic(self, stats_service, mock_db):
        """Test basic overview statistics."""
        # Mock all the private cached methods
        with (
            patch.object(
                stats_service,
                "_get_member_statistics_cached",
                return_value={"active_count": 5},
            ),
            patch.object(
                stats_service,
                "_get_task_statistics_cached",
                return_value={"completed_count": 10},
            ),
            patch.object(
                stats_service,
                "_get_work_hour_statistics_cached",
                return_value={"total_hours": 50},
            ),
            patch.object(
                stats_service,
                "_get_performance_statistics_cached",
                return_value={"overall_rating": 4.5},
            ),
            patch.object(
                stats_service,
                "_get_attendance_statistics_cached",
                return_value={"overall_rate": 95},
            ),
        ):
            result = await stats_service.get_overview_statistics()

            assert "summary" in result
            assert result["summary"]["total_active_members"] == 5
            assert result["summary"]["total_tasks_completed"] == 10

    @pytest.mark.asyncio
    async def test_get_member_performance_report(
        self, stats_service, mock_db, sample_member
    ):
        """Test member performance report."""
        with (
            patch.object(
                stats_service,
                "_get_member_task_statistics",
                return_value={
                    "total_tasks": 2,
                    "completed_tasks": 2,
                    "completion_rate": 100.0,
                },
            ),
            patch.object(
                stats_service,
                "_get_member_work_hour_statistics",
                return_value={"total_hours": 2.33},
            ),
            patch.object(
                stats_service,
                "_get_member_quality_statistics",
                return_value={"avg_rating": 4.5},
            ),
            patch.object(
                stats_service, "_get_member_ranking", return_value={"work_hour_rank": 1}
            ),
            patch.object(
                stats_service,
                "_get_member_trend_analysis",
                return_value={"change_rate": 10.0},
            ),
        ):
            # Mock member query
            mock_member = Mock()
            mock_member.id = sample_member.id
            mock_member.name = sample_member.name
            mock_member.student_id = sample_member.student_id
            mock_member.department = "IT"
            mock_member.role = sample_member.role

            mock_result = Mock()
            mock_result.scalar_one_or_none.return_value = mock_member
            mock_db.execute.return_value = mock_result

            result = await stats_service.get_member_performance_report(
                member_id=sample_member.id, year=2024, month=1
            )

            assert result["member"]["id"] == sample_member.id
            assert result["tasks"]["total_tasks"] == 2
            assert result["tasks"]["completed_tasks"] == 2

    @pytest.mark.asyncio
    async def test_get_member_performance_report_no_member(
        self, stats_service, mock_db
    ):
        """Test member performance report with non-existent member."""
        # Mock empty member query result
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        with pytest.raises(ValueError, match="成员不存在"):
            await stats_service.get_member_performance_report(
                member_id=999, year=2024, month=1
            )

    @pytest.mark.asyncio
    async def test_get_team_comparison_report(self, stats_service, mock_db):
        """Test team comparison report."""
        # Mock member query
        mock_member = Mock()
        mock_member.id = 1
        mock_member.name = "Test User"
        mock_member.student_id = "TEST001"
        mock_member.department = "IT"
        mock_member.role = Mock()
        mock_member.role.value = "member"

        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = [mock_member]
        mock_db.execute.return_value = mock_result

        with (
            patch.object(
                stats_service,
                "_get_member_comparison_stats",
                return_value={
                    "work_hours": {"total_hours": 40},
                    "tasks": {"total_tasks": 10},
                    "quality": {"avg_rating": 4.5},
                },
            ),
            patch.object(
                stats_service,
                "_calculate_team_summary",
                return_value={"total_members": 1, "total_hours": 40},
            ),
        ):
            result = await stats_service.get_team_comparison_report()

            assert "team_summary" in result
            assert "member_rankings" in result

    @pytest.mark.asyncio
    async def test_get_monthly_trends(self, stats_service, mock_db):
        """Test monthly trends functionality."""
        with patch.object(
            stats_service,
            "_get_monthly_statistics",
            return_value={
                "total_tasks": 20,
                "completed_tasks": 18,
                "total_work_hours": 40.5,
                "completion_rate": 90.0,
            },
        ):
            result = await stats_service.get_monthly_trends(months=3)

            assert "monthly_data" in result
            assert "trend_analysis" in result
            assert result["analysis_months"] == 3

    @pytest.mark.asyncio
    async def test_export_statistics_data(self, stats_service, mock_db):
        """Test statistics data export functionality."""
        with patch.object(
            stats_service,
            "_export_summary_data",
            return_value={"export_type": "summary", "data": {}},
        ):
            result = await stats_service.export_statistics_data(
                "summary", datetime(2024, 1, 1), datetime(2024, 1, 31)
            )

            assert result["export_type"] == "summary"
            assert "data" in result

    @pytest.mark.asyncio
    async def test_export_invalid_type(self, stats_service):
        """Test export with invalid type raises error."""
        with pytest.raises(ValueError, match="不支持的导出类型"):
            await stats_service.export_statistics_data(
                "invalid_type", datetime(2024, 1, 1), datetime(2024, 1, 31)
            )

    @pytest.mark.asyncio
    async def test_overview_with_date_range(self, stats_service, mock_db):
        """Test overview statistics with custom date range."""
        date_from = datetime(2024, 1, 1)
        date_to = datetime(2024, 1, 31)

        with (
            patch.object(
                stats_service,
                "_get_member_statistics_cached",
                return_value={"active_count": 3},
            ),
            patch.object(
                stats_service,
                "_get_task_statistics_cached",
                return_value={"completed_count": 15},
            ),
            patch.object(
                stats_service,
                "_get_work_hour_statistics_cached",
                return_value={"total_hours": 75},
            ),
            patch.object(
                stats_service,
                "_get_performance_statistics_cached",
                return_value={"overall_rating": 4.2},
            ),
            patch.object(
                stats_service,
                "_get_attendance_statistics_cached",
                return_value={"overall_rate": 88},
            ),
        ):
            result = await stats_service.get_overview_statistics(
                date_from=date_from, date_to=date_to
            )

            assert result["period"]["from"] == date_from.isoformat()
            assert result["period"]["to"] == date_to.isoformat()
            assert result["summary"]["total_active_members"] == 3

    @pytest.mark.asyncio
    async def test_cache_disabled_functionality(self, mock_db):
        """Test statistics service with caching disabled."""
        stats_service = StatisticsService(mock_db)
        stats_service.cache_enabled = False

        with (
            patch.object(
                stats_service,
                "_get_member_statistics_cached",
                return_value={"active_count": 2},
            ),
            patch.object(
                stats_service,
                "_get_task_statistics_cached",
                return_value={"completed_count": 5},
            ),
            patch.object(
                stats_service,
                "_get_work_hour_statistics_cached",
                return_value={"total_hours": 25},
            ),
            patch.object(
                stats_service,
                "_get_performance_statistics_cached",
                return_value={"overall_rating": 4.0},
            ),
            patch.object(
                stats_service,
                "_get_attendance_statistics_cached",
                return_value={"overall_rate": 80},
            ),
        ):
            result = await stats_service.get_overview_statistics()

            assert "summary" in result
            assert result["summary"]["total_active_members"] == 2
