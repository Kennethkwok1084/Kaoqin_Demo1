"""Unit tests for repair-workhour orchestration service."""

from datetime import datetime, timezone
from unittest.mock import AsyncMock

import pytest

from app.models.repair_match_application import RepairMatchApplication
from app.models.repair_ticket import RepairTicket
from app.models.todo_item import TodoItem
from app.models.workhour_entry import WorkhourEntry
from app.schemas.repair_workhour import (
    RepairReviewActionRequest,
    RepairReviewSubmitRequest,
)
from app.services.repair_workhour_service import RepairWorkhourService


class _ScalarResult:
    def __init__(self, value):
        self.value = value

    def scalar_one_or_none(self):
        return self.value


class _RowsResult:
    def __init__(self, rows):
        self._rows = rows

    def all(self):
        return self._rows


class _ScalarsWrapper:
    def __init__(self, rows):
        self._rows = rows

    def all(self):
        return self._rows


class _TodoResult:
    def __init__(self, rows):
        self._rows = rows

    def scalars(self):
        return _ScalarsWrapper(self._rows)


@pytest.mark.asyncio
class TestRepairWorkhourService:
    async def test_review_application_rejects_invalid_action(self):
        db = AsyncMock()
        service = RepairWorkhourService(db)

        with pytest.raises(ValueError, match="approve/reject"):
            await service.review_application(
                ticket_id=1,
                reviewer_id=1,
                payload=RepairReviewActionRequest(action="invalid", note="x"),
            )

    async def test_submit_review_returns_already_pending(self):
        db = AsyncMock()
        db.commit = AsyncMock()
        db.rollback = AsyncMock()

        ticket = RepairTicket(
            id=1,
            ticket_source="online",
            title="T1",
            created_by=1,
        )
        ticket.matched_import_row_id = 99

        pending_app = RepairMatchApplication(
            id=10,
            repair_ticket_id=1,
            import_repair_row_id=99,
            applied_by=1,
            status=0,
        )

        db.execute = AsyncMock(
            side_effect=[
                _ScalarResult(ticket),
                _ScalarResult(pending_app),
            ]
        )

        service = RepairWorkhourService(db)
        result = await service.submit_review(
            ticket_id=1,
            operator_id=1,
            payload=RepairReviewSubmitRequest(note="重复提交"),
        )

        assert result["already_pending"] is True
        db.commit.assert_not_called()

    async def test_review_application_approve_updates_status_and_entry(self):
        db = AsyncMock()
        db.commit = AsyncMock()
        db.rollback = AsyncMock()
        db.flush = AsyncMock()
        db.add = AsyncMock()

        application = RepairMatchApplication(
            id=20,
            repair_ticket_id=2,
            import_repair_row_id=12,
            applied_by=3,
            status=0,
        )
        ticket = RepairTicket(
            id=2,
            ticket_source="offline",
            title="repair-2",
            created_by=3,
        )
        todo = TodoItem(
            id=8,
            todo_type="repair_match_review",
            source_biz_type="repair_match_application",
            source_biz_id=20,
            title="todo",
            status=0,
        )
        entry = WorkhourEntry(
            id=100,
            biz_type="repair",
            biz_id=2,
            user_id=3,
            base_minutes=100,
            final_minutes=100,
            review_status=1,
        )

        db.execute = AsyncMock(
            side_effect=[
                _ScalarResult(application),
                _ScalarResult(ticket),
                _TodoResult([todo]),
            ]
        )

        service = RepairWorkhourService(db)
        service._upsert_workhour_entry = AsyncMock(return_value=(entry, True))

        result = await service.review_application(
            ticket_id=2,
            reviewer_id=1,
            payload=RepairReviewActionRequest(action="approve", note="通过"),
        )

        assert result["action"] == "approve"
        assert result["workhour_entry_created"] is True
        assert result["workhour_entry_id"] == 100
        assert application.status == 1
        assert ticket.match_status == 2
        assert todo.status == 2
        assert todo.resolved_at is not None
        db.commit.assert_called_once()

    async def test_run_monthly_settlement_dry_run_rolls_back(self):
        db = AsyncMock()
        db.execute = AsyncMock()
        db.add = AsyncMock()
        db.commit = AsyncMock()
        db.rollback = AsyncMock()

        application = RepairMatchApplication(
            id=31,
            repair_ticket_id=4,
            import_repair_row_id=16,
            applied_by=2,
            status=1,
            reviewed_at=datetime.now(timezone.utc),
        )
        ticket = RepairTicket(
            id=4,
            ticket_source="online",
            title="ticket-4",
            created_by=2,
        )
        entry = WorkhourEntry(
            id=101,
            biz_type="repair",
            biz_id=4,
            user_id=2,
            base_minutes=40,
            final_minutes=40,
            review_status=1,
        )

        db.execute.return_value = _RowsResult([(application, ticket)])

        service = RepairWorkhourService(db)
        service._upsert_workhour_entry = AsyncMock(return_value=(entry, True))

        result = await service.run_monthly_settlement(
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
