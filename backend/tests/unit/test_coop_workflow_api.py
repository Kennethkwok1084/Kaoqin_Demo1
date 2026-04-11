"""Unit tests for migrated coop workflow APIs."""

from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest
from fastapi import HTTPException

from app.api.v1.coop import admin_review_task_signup, task_sign_repair_request
from app.models.task_coop_attendance import TaskCoopAttendance
from app.models.task_coop_signup import TaskCoopSignup


def _result_scalar_one_or_none(value):
    result = Mock()
    result.scalar_one_or_none.return_value = value
    return result


def _result_scalars_first(value):
    result = Mock()
    scalars = Mock()
    scalars.first.return_value = value
    result.scalars.return_value = scalars
    return result


@pytest.mark.asyncio
async def test_admin_review_task_signup_approve_success():
    db = AsyncMock()
    admin_user = SimpleNamespace(id=9001)

    signup = TaskCoopSignup(coop_task_id=1, coop_slot_id=2, user_id=3, status=0)
    signup.id = 101

    db.execute.return_value = _result_scalar_one_or_none(signup)

    resp = await admin_review_task_signup(
        task_id=1,
        signup_id=101,
        payload={"approve": True},
        db=db,
        current_user=admin_user,
    )

    assert resp["success"] is True
    assert resp["data"]["id"] == 101
    assert resp["data"]["status"] == 1
    assert signup.reviewed_by == 9001
    assert signup.cancel_reason is None
    db.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_admin_review_task_signup_not_found():
    db = AsyncMock()
    admin_user = SimpleNamespace(id=9001)

    db.execute.return_value = _result_scalar_one_or_none(None)

    with pytest.raises(HTTPException) as exc:
        await admin_review_task_signup(
            task_id=1,
            signup_id=999,
            payload={"approve": True},
            db=db,
            current_user=admin_user,
        )

    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_task_sign_repair_request_with_attendance_creates_todo():
    db = AsyncMock()
    current_user = SimpleNamespace(id=7)

    attendance = TaskCoopAttendance(coop_signup_id=11)
    attendance.id = 301
    attendance.review_status = 0

    db.execute.side_effect = [
        _result_scalar_one_or_none(attendance),  # attendance with join validation
        _result_scalars_first(None),  # pending todo not exists
    ]

    resp = await task_sign_repair_request(
        task_id=1,
        payload={"attendance_id": 301, "reason": "漏签"},
        db=db,
        current_user=current_user,
    )

    assert resp["success"] is True
    assert resp["data"]["attendance_id"] == 301
    assert attendance.remark == "漏签"
    assert db.add.call_count == 1  # created one todo item
    db.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_task_sign_repair_request_without_attendance_uses_signup_and_creates_attendance():
    db = AsyncMock()
    current_user = SimpleNamespace(id=7)

    signup = TaskCoopSignup(coop_task_id=1, coop_slot_id=2, user_id=7, status=1)
    signup.id = 88

    db.execute.side_effect = [
        _result_scalars_first(signup),  # lookup signup
        _result_scalar_one_or_none(None),  # attendance not found
        _result_scalars_first(None),  # pending todo not exists
    ]

    resp = await task_sign_repair_request(
        task_id=1,
        payload={"reason": "未生成签到记录"},
        db=db,
        current_user=current_user,
    )

    assert resp["success"] is True
    assert resp["data"]["attendance_id"] is not None
    assert db.flush.await_count == 1
    assert db.add.call_count == 2  # created attendance + todo
    db.commit.assert_awaited_once()
