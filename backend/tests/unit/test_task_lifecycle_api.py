"""Unit tests for migrated task lifecycle APIs."""

from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch

import pytest
from fastapi import HTTPException

from app.api.v1.task_lifecycle import (
    _find_task_any,
    admin_approve_sign_record,
    admin_assign_task,
    task_sign_in,
    task_sign_out,
)
from app.models.todo_item import TodoItem
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
async def test_admin_approve_sign_record_success() -> None:
    db = AsyncMock()
    row = TaskCoopAttendance(coop_signup_id=11)
    row.id = 55
    row.review_status = 0
    db.execute.return_value = _result_scalar_one_or_none(row)

    resp = await admin_approve_sign_record(
        record_id=55,
        payload={"approve": True},
        db=db,
        _=SimpleNamespace(id=1),
    )

    assert resp["success"] is True
    assert resp["data"]["id"] == 55
    assert resp["data"]["review_status"] == 1
    db.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_task_sign_out_requires_existing_sign_in_record() -> None:
    db = AsyncMock()
    current_user = SimpleNamespace(id=7)

    signup = TaskCoopSignup(coop_task_id=1, coop_slot_id=2, user_id=7, status=1)
    signup.id = 99

    db.execute.side_effect = [
        _result_scalar_one_or_none(SimpleNamespace(id=1, building_id=None)),
        _result_scalars_first(signup),
        _result_scalar_one_or_none(None),
    ]

    with pytest.raises(HTTPException) as exc:
        await task_sign_out(
            task_id=1,
            payload={},
            db=db,
            current_user=current_user,
        )

    assert exc.value.status_code == 400
    assert exc.value.detail == "请先签到"


@pytest.mark.asyncio
async def test_admin_assign_task_invalid_user_id() -> None:
    db = AsyncMock()

    with pytest.raises(HTTPException) as exc:
        await admin_assign_task(
            task_id=1,
            payload={"user_id": 0},
            db=db,
            _=SimpleNamespace(id=1),
        )

    assert exc.value.status_code == 400
    assert "user_id" in str(exc.value.detail)


@pytest.mark.asyncio
async def test_find_task_any_raises_on_ambiguous_id() -> None:
    db = AsyncMock()
    coop_task = SimpleNamespace(id=1)
    inspection_task = SimpleNamespace(id=1)

    db.execute.side_effect = [
        _result_scalar_one_or_none(coop_task),
        _result_scalar_one_or_none(inspection_task),
        _result_scalar_one_or_none(None),
    ]

    with pytest.raises(HTTPException) as exc:
        await _find_task_any(db, task_id=1)

    assert exc.value.status_code == 409


@pytest.mark.asyncio
async def test_task_sign_in_rejects_invalid_qr_and_creates_todo() -> None:
    db = AsyncMock()
    current_user = SimpleNamespace(id=7)

    signup = TaskCoopSignup(coop_task_id=1, coop_slot_id=2, user_id=7, status=1)
    signup.id = 88

    db.execute.side_effect = [
        _result_scalar_one_or_none(SimpleNamespace(id=1, building_id=None)),
        _result_scalars_first(signup),
        _result_scalar_one_or_none(None),
    ]

    with patch(
        "app.api.v1.task_lifecycle._validate_qr_token",
        new_callable=AsyncMock,
    ) as mock_validate_qr:
        mock_validate_qr.return_value = False

        with pytest.raises(HTTPException) as exc:
            await task_sign_in(
                task_id=1,
                payload={"sign_in_type": "qr", "qr_token": "bad-token"},
                db=db,
                current_user=current_user,
            )

    assert exc.value.status_code == 400
    assert "二维码验签" in str(exc.value.detail)
    added_entities = [call_args[0][0] for call_args in db.add.call_args_list]
    assert any(isinstance(item, TodoItem) for item in added_entities)
    db.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_task_sign_out_rejects_device_mismatch_and_creates_todo() -> None:
    db = AsyncMock()
    current_user = SimpleNamespace(id=7)

    signup = TaskCoopSignup(coop_task_id=1, coop_slot_id=2, user_id=7, status=1)
    signup.id = 88

    attendance = TaskCoopAttendance(coop_signup_id=signup.id)
    attendance.id = 201
    attendance.sign_in_at = datetime.now(timezone.utc)
    attendance.sign_out_at = None
    attendance.remark = '{"anti_cheat_device_id":"device-A"}'

    db.execute.side_effect = [
        _result_scalar_one_or_none(SimpleNamespace(id=1, building_id=None)),
        _result_scalars_first(signup),
        _result_scalar_one_or_none(attendance),
        _result_scalar_one_or_none(None),
        _result_scalar_one_or_none(None),
    ]

    with pytest.raises(HTTPException) as exc:
        await task_sign_out(
            task_id=1,
            payload={"device_id": "device-B"},
            db=db,
            current_user=current_user,
        )

    assert exc.value.status_code == 400
    assert "设备指纹不一致" in str(exc.value.detail)
    added_entities = [call_args[0][0] for call_args in db.add.call_args_list]
    assert any(isinstance(item, TodoItem) for item in added_entities)
    db.commit.assert_awaited_once()
