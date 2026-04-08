from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.api.v1.repair import get_tasks_stats
from app.api.v1.statistics import get_statistics_overview
from app.models.member import UserRole


def _scalar_result(value):
    result = MagicMock()
    result.scalar.return_value = value
    return result


def _first_result(value):
    result = MagicMock()
    result.first.return_value = value
    return result


def _fetchall_result(value):
    result = MagicMock()
    result.fetchall.return_value = value
    return result


@pytest.mark.asyncio
async def test_get_tasks_stats_monitoring_uses_end_time():
    mock_db = AsyncMock()
    mock_db.execute.side_effect = [
        _scalar_result(12),  # total_tasks
        _scalar_result(3),   # pending_tasks
        _scalar_result(2),   # in_progress_tasks
        _scalar_result(7),   # completed_tasks
        _scalar_result(1),   # today_created
        _scalar_result(4),   # today_completed
        _scalar_result(360),  # total_work_minutes
    ]

    current_user = SimpleNamespace(
        id=1,
        role=UserRole.ADMIN,
        student_id="ADMIN001",
    )

    response = await get_tasks_stats(
        task_type="monitoring",
        current_user=current_user,
        db=mock_db,
    )

    assert response["success"] is True
    assert response["data"]["overview"]["total"] == 12
    assert response["data"]["today"]["completed"] == 4
    assert response["data"]["overview"]["total_work_hours"] == 6.0
    assert response["data"]["overview"]["overdue_response_count"] == 0
    assert response["data"]["overview"]["overdue_completion_count"] == 0


@pytest.mark.asyncio
async def test_get_tasks_stats_repair_includes_overdue_and_work_hour_fields():
    mock_db = AsyncMock()
    mock_db.execute.side_effect = [
        _scalar_result(20),   # total_tasks
        _scalar_result(5),    # pending_tasks
        _scalar_result(7),    # in_progress_tasks
        _scalar_result(8),    # completed_tasks
        _scalar_result(2),    # today_created
        _scalar_result(3),    # today_completed
        _scalar_result(750),  # total_work_minutes
        _scalar_result(4),    # overdue_response_count
        _scalar_result(6),    # overdue_completion_count
        _scalar_result(9),    # overdue_tasks
    ]

    current_user = SimpleNamespace(
        id=1,
        role=UserRole.ADMIN,
        student_id="ADMIN001",
    )

    response = await get_tasks_stats(
        task_type="repair",
        current_user=current_user,
        db=mock_db,
    )

    assert response["success"] is True
    assert response["data"]["overview"]["overdue_response"] == 4
    assert response["data"]["overview"]["overdue_response_count"] == 4
    assert response["data"]["overview"]["overdue_completion"] == 6
    assert response["data"]["overview"]["overdue_completion_count"] == 6
    assert response["data"]["overview"]["total_work_hours"] == 12.5
    assert response["data"]["overview"]["total_hours"] == 12.5
    assert response["data"]["overdue_response"] == 4
    assert response["data"]["overdue_completion"] == 6
    assert response["data"]["total_work_hours"] == 12.5
    assert response["data"]["total_hours"] == 12.5


@pytest.mark.asyncio
async def test_statistics_overview_without_date_filter_uses_full_repair_scope():
    mock_db = AsyncMock()
    mock_db.execute.side_effect = [
        _first_result(
            SimpleNamespace(
                total_tasks=7,
                completed_tasks=4,
                in_progress_tasks=2,
                pending_tasks=1,
                total_work_minutes=420,
                avg_work_minutes=60,
                online_tasks=5,
                offline_tasks=2,
            )
        ),
        _first_result(
            SimpleNamespace(
                total_members=10,
                active_members=9,
                admin_count=1,
                leader_count=2,
                member_count=7,
            )
        ),
        _first_result(
            SimpleNamespace(
                min_report_time=datetime(2024, 1, 1, tzinfo=timezone.utc),
                max_report_time=datetime(2025, 4, 1, tzinfo=timezone.utc),
            )
        ),
        _scalar_result(0),
        _scalar_result(0),
        _scalar_result(0),
        _fetchall_result([]),
        _fetchall_result([]),
    ]

    current_user = SimpleNamespace(
        id=1,
        role=UserRole.ADMIN,
        student_id="ADMIN001",
    )

    response = await get_statistics_overview(
        date_from=None,
        date_to=None,
        current_user=current_user,
        db=mock_db,
    )

    first_query = str(mock_db.execute.call_args_list[0].args[0])

    assert response["success"] is True
    assert response["data"]["tasks"]["total"] == 7
    assert response["data"]["period"]["from"] == "2024-01-01T00:00:00+00:00"
    assert response["data"]["period"]["to"] == "2025-04-01T00:00:00+00:00"
    assert "WHERE" not in first_query


@pytest.mark.asyncio
async def test_statistics_overview_with_date_filter_uses_report_time():
    mock_db = AsyncMock()
    mock_db.execute.side_effect = [
        _first_result(
            SimpleNamespace(
                total_tasks=2,
                completed_tasks=1,
                in_progress_tasks=1,
                pending_tasks=0,
                total_work_minutes=120,
                avg_work_minutes=60,
                online_tasks=2,
                offline_tasks=0,
            )
        ),
        _first_result(
            SimpleNamespace(
                total_members=10,
                active_members=9,
                admin_count=1,
                leader_count=2,
                member_count=7,
            )
        ),
        _first_result(
            SimpleNamespace(
                min_report_time=datetime(2025, 1, 1, tzinfo=timezone.utc),
                max_report_time=datetime(2025, 1, 31, tzinfo=timezone.utc),
            )
        ),
        _scalar_result(0),
        _scalar_result(0),
        _scalar_result(0),
        _fetchall_result([]),
        _fetchall_result([]),
    ]

    current_user = SimpleNamespace(
        id=1,
        role=UserRole.ADMIN,
        student_id="ADMIN001",
    )

    response = await get_statistics_overview(
        date_from=datetime(2025, 1, 1, tzinfo=timezone.utc),
        date_to=datetime(2025, 1, 31, tzinfo=timezone.utc),
        current_user=current_user,
        db=mock_db,
    )

    first_query = str(mock_db.execute.call_args_list[0].args[0])

    assert response["success"] is True
    assert response["data"]["tasks"]["total"] == 2
    assert "report_time" in first_query
    assert "created_at" not in first_query
