"""Unit tests for inspection/sampling workhour orchestration service."""

from datetime import datetime, timezone
from unittest.mock import AsyncMock

import pytest

from app.models.inspection_record import InspectionRecord
from app.models.sampling_record import SamplingRecord
from app.models.todo_item import TodoItem
from app.models.workhour_entry import WorkhourEntry
from app.schemas.repair_workhour import BizReviewSubmitRequest, RepairReviewActionRequest
from app.services.inspection_sampling_workhour_service import (
    InspectionSamplingWorkhourService,
)


class _ScalarResult:
    def __init__(self, value):
        self.value = value

    def scalar_one_or_none(self):
        return self.value


class _ScalarsWrapper:
    def __init__(self, rows):
        self._rows = rows

    def all(self):
        return self._rows


class _ScalarsResult:
    def __init__(self, rows):
        self._rows = rows

    def scalars(self):
        return _ScalarsWrapper(self._rows)


class _RowsResult:
    def __init__(self, rows):
        self._rows = rows

    def scalars(self):
        return _ScalarsWrapper(self._rows)


@pytest.mark.asyncio
class TestInspectionSamplingWorkhourService:
    async def test_submit_review_inspection_already_pending(self):
        db = AsyncMock()
        db.commit = AsyncMock()
        db.rollback = AsyncMock()

        record = InspectionRecord(
            id=1,
            inspection_task_id=10,
            inspection_point_id=11,
            user_id=3,
            result_status=1,
            review_status=0,
        )
        db.execute = AsyncMock(return_value=_ScalarResult(record))

        service = InspectionSamplingWorkhourService(db)
        result = await service.submit_review(
            biz_type="inspection",
            record_id=1,
            operator_id=99,
            payload=BizReviewSubmitRequest(note="重复提交"),
        )

        assert result["already_pending"] is True
        db.commit.assert_not_called()

    async def test_review_application_sampling_approve(self):
        db = AsyncMock()
        db.commit = AsyncMock()
        db.rollback = AsyncMock()
        db.flush = AsyncMock()
        db.add = AsyncMock()

        record = SamplingRecord(
            id=2,
            sampling_task_id=21,
            sampling_task_room_id=22,
            dorm_room_id=23,
            user_id=4,
            detect_mode="full",
            review_status=0,
            exception_auto=False,
            exception_manual=False,
        )
        todo = TodoItem(
            id=8,
            todo_type="sampling_record_review",
            source_biz_type="sampling_record_review",
            source_biz_id=2,
            title="todo",
            status=0,
        )
        entry = WorkhourEntry(
            id=100,
            biz_type="sampling",
            biz_id=2,
            user_id=4,
            base_minutes=40,
            final_minutes=40,
            review_status=1,
        )

        db.execute = AsyncMock(side_effect=[_ScalarResult(record), _ScalarsResult([todo])])

        service = InspectionSamplingWorkhourService(db)
        service._upsert_workhour_entry = AsyncMock(return_value=(entry, True))

        result = await service.review_application(
            biz_type="sampling",
            record_id=2,
            reviewer_id=1,
            payload=RepairReviewActionRequest(action="approve", note="通过"),
        )

        assert result["action"] == "approve"
        assert result["workhour_entry_created"] is True
        assert result["workhour_entry_id"] == 100
        assert todo.status == 2
        assert todo.resolved_at is not None
        db.commit.assert_called_once()

    async def test_run_monthly_settlement_inspection_dry_run(self):
        db = AsyncMock()
        db.commit = AsyncMock()
        db.rollback = AsyncMock()
        db.add = AsyncMock()

        record = InspectionRecord(
            id=3,
            inspection_task_id=30,
            inspection_point_id=31,
            user_id=5,
            result_status=1,
            review_status=1,
            reviewed_at=datetime.now(timezone.utc),
        )
        entry = WorkhourEntry(
            id=101,
            biz_type="inspection",
            biz_id=3,
            user_id=5,
            base_minutes=20,
            final_minutes=20,
            review_status=1,
        )

        db.execute = AsyncMock(return_value=_RowsResult([record]))

        service = InspectionSamplingWorkhourService(db)
        service._upsert_workhour_entry = AsyncMock(return_value=(entry, True))

        result = await service.run_monthly_settlement(
            biz_type="inspection",
            year=2026,
            month=4,
            operator_id=1,
            dry_run=True,
        )

        assert result["processed"] == 1
        assert result["created"] == 1
        assert result["updated"] == 0
        assert result["dry_run"] is True
        db.rollback.assert_called_once()
        db.commit.assert_not_called()
