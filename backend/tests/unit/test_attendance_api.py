"""Unit tests for attendance check-in/check-out API handlers."""

from __future__ import annotations

from datetime import date, datetime
from typing import Any, List

import pytest
from fastapi import HTTPException

from app.api.v1.attendance import check_in, check_out
from app.models.attendance import AttendanceRecord
from app.models.member import Member, UserRole


class _ScalarResult:
    def __init__(self, value: Any) -> None:
        self._value = value

    def scalar_one_or_none(self) -> Any:
        return self._value


class _FakeDB:
    def __init__(self, execute_results: List[_ScalarResult]) -> None:
        self._execute_results = execute_results
        self.added: List[Any] = []
        self.commit_count = 0
        self.rollback_count = 0
        self.refresh_count = 0

    async def execute(self, *_args: Any, **_kwargs: Any) -> _ScalarResult:
        if not self._execute_results:
            raise AssertionError("No mocked execute result available")
        return self._execute_results.pop(0)

    def add(self, obj: Any) -> None:
        self.added.append(obj)

    async def commit(self) -> None:
        self.commit_count += 1

    async def rollback(self) -> None:
        self.rollback_count += 1

    async def refresh(self, _obj: Any) -> None:
        self.refresh_count += 1


class TestAttendanceApi:
    @staticmethod
    def _build_user() -> Member:
        return Member(
            id=1,
            username="test_user",
            name="测试用户",
            student_id="TEST001",
            role=UserRole.MEMBER,
            is_active=True,
        )

    @pytest.mark.asyncio
    async def test_check_in_create_new_record(self) -> None:
        user = self._build_user()
        db = _FakeDB(execute_results=[_ScalarResult(None)])

        result = await check_in(
            request_data={
                "checkinTime": "2026-04-10T09:00:00",
                "location": "信息中心",
                "deviceInfo": "ios",
            },
            current_user=user,
            db=db,
        )

        assert result["success"] is True
        assert result["status_code"] == 200
        assert result["data"]["member_id"] == user.id
        assert result["data"]["status"] == "已签到"
        assert result["data"]["location"] == "信息中心"

        assert len(db.added) == 1
        created_record = db.added[0]
        assert isinstance(created_record, AttendanceRecord)
        assert created_record.member_id == user.id
        assert created_record.attendance_date == date(2026, 4, 10)
        assert db.commit_count == 1
        assert db.refresh_count == 1

    @pytest.mark.asyncio
    async def test_check_out_without_any_checkin_raises_400(self) -> None:
        user = self._build_user()
        db = _FakeDB(execute_results=[_ScalarResult(None), _ScalarResult(None)])

        with pytest.raises(HTTPException) as exc_info:
            await check_out(
                request_data={"checkoutTime": "2026-04-10T18:00:00"},
                current_user=user,
                db=db,
            )

        assert exc_info.value.status_code == 400
        assert "尚未签到" in str(exc_info.value.detail)
        assert db.commit_count == 0

    @pytest.mark.asyncio
    async def test_check_out_cross_day_fallback_works(self) -> None:
        user = self._build_user()
        record = AttendanceRecord(
            id=10,
            member_id=user.id,
            attendance_date=date(2026, 4, 9),
            checkin_time=datetime(2026, 4, 9, 23, 0, 0),
            status="已签到",
        )
        db = _FakeDB(execute_results=[_ScalarResult(None), _ScalarResult(record)])

        result = await check_out(
            request_data={
                "checkoutTime": "2026-04-10T01:00:00",
                "workSummary": "跨天处理完成",
            },
            current_user=user,
            db=db,
        )

        assert result["success"] is True
        assert result["data"]["status"] == "已签退"
        assert result["data"]["work_hours"] == 2.0
        assert record.work_hours == 2.0
        assert record.checkout_time == datetime(2026, 4, 10, 1, 0, 0)
        assert db.commit_count == 1

    @pytest.mark.asyncio
    async def test_check_out_earlier_than_checkin_raises_400(self) -> None:
        user = self._build_user()
        record = AttendanceRecord(
            id=11,
            member_id=user.id,
            attendance_date=date(2026, 4, 10),
            checkin_time=datetime(2026, 4, 10, 10, 0, 0),
            status="已签到",
        )
        db = _FakeDB(execute_results=[_ScalarResult(record)])

        with pytest.raises(HTTPException) as exc_info:
            await check_out(
                request_data={"checkoutTime": "2026-04-10T09:00:00"},
                current_user=user,
                db=db,
            )

        assert exc_info.value.status_code == 400
        assert "不能早于" in str(exc_info.value.detail)
        assert db.commit_count == 0
