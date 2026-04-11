"""Unit tests for migrated inspection/sampling workflow APIs."""

from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch

import pytest
from fastapi import HTTPException

from app.api.v1.inspection_sampling import (
    admin_approve_inspection_record,
    create_inspection_record,
    network_test_detail,
    network_test_single_item,
    network_test_submit,
)
from app.models.sampling_scan_detail import SamplingScanDetail
from app.models.sampling_test_detail import SamplingTestDetail
from app.models.sampling_record import SamplingRecord
from app.models.member import UserRole


def _result_scalar_one_or_none(value):
    result = Mock()
    result.scalar_one_or_none.return_value = value
    return result


def _result_scalars_all(values):
    result = Mock()
    scalars = Mock()
    scalars.all.return_value = values
    result.scalars.return_value = scalars
    return result


@pytest.mark.asyncio
async def test_create_inspection_record_requires_point_id():
    db = AsyncMock()
    current_user = SimpleNamespace(id=11)

    with pytest.raises(HTTPException) as exc:
        await create_inspection_record(
            task_id=1,
            payload={"inspection_point_id": 0},
            db=db,
            current_user=current_user,
        )

    assert exc.value.status_code == 400


@pytest.mark.asyncio
async def test_create_inspection_record_requires_point_belongs_to_task():
    db = AsyncMock()
    current_user = SimpleNamespace(id=11)
    db.execute.side_effect = [
        _result_scalar_one_or_none(SimpleNamespace()),
        _result_scalar_one_or_none(None),
    ]

    with pytest.raises(HTTPException) as exc:
        await create_inspection_record(
            task_id=1,
            payload={"inspection_point_id": 9},
            db=db,
            current_user=current_user,
        )

    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_create_inspection_record_forbidden_when_not_assigned():
    db = AsyncMock()
    current_user = SimpleNamespace(id=11, role=UserRole.MEMBER)
    db.execute.return_value = _result_scalar_one_or_none(None)

    with pytest.raises(HTTPException) as exc:
        await create_inspection_record(
            task_id=1,
            payload={"inspection_point_id": 9},
            db=db,
            current_user=current_user,
        )

    assert exc.value.status_code == 403


@pytest.mark.asyncio
async def test_admin_approve_inspection_record_success():
    db = AsyncMock()
    admin_user = SimpleNamespace(id=9001)

    row = SimpleNamespace(id=8, review_status=0, reviewed_by=None, reviewed_at=None)
    db.execute.return_value = _result_scalar_one_or_none(row)

    resp = await admin_approve_inspection_record(
        record_id=8,
        payload={"approve": True},
        db=db,
        current_user=admin_user,
    )

    assert resp["success"] is True
    assert resp["data"]["id"] == 8
    assert resp["data"]["review_status"] == 1
    assert row.reviewed_by == 9001
    db.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_network_test_submit_auto_marks_exception():
    db = AsyncMock()
    current_user = SimpleNamespace(id=7, role=UserRole.MEMBER)

    row = SimpleNamespace(
        id=5,
        user_id=7,
        loss_rate_pct=10.0,
        tcp_rtt_ms=300.0,
        down_speed_mbps=10.0,
        up_speed_mbps=1.0,
        exception_auto=False,
        manual_exception_note=None,
        finished_at=None,
    )
    db.execute.return_value = _result_scalar_one_or_none(row)

    with patch(
        "app.api.v1.inspection_sampling._get_system_config_float",
        new_callable=AsyncMock,
    ) as mock_get_float:
        mock_get_float.side_effect = [5.0, 200.0, 20.0, 2.0]

        resp = await network_test_submit(
            record_id=5,
            payload={},
            db=db,
            current_user=current_user,
        )

    assert resp["success"] is True
    assert resp["data"]["id"] == 5
    assert row.exception_auto is True
    assert "阈值" in (row.manual_exception_note or "")
    db.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_network_test_submit_persists_sampling_details() -> None:
    db = AsyncMock()
    current_user = SimpleNamespace(id=7, role=UserRole.MEMBER)

    row = SimpleNamespace(
        id=5,
        user_id=7,
        loss_rate_pct=0.1,
        tcp_rtt_ms=20.0,
        down_speed_mbps=100.0,
        up_speed_mbps=20.0,
        exception_auto=False,
        manual_exception_note=None,
        finished_at=None,
    )
    db.execute.return_value = _result_scalar_one_or_none(row)

    with patch(
        "app.api.v1.inspection_sampling._get_system_config_float",
        new_callable=AsyncMock,
    ) as mock_get_float:
        mock_get_float.side_effect = [5.0, 200.0, 20.0, 2.0]

        resp = await network_test_submit(
            record_id=5,
            payload={
                "scan_details": [
                    {
                        "ssid": "CampusNet",
                        "bssid": "00:11:22:33:44:55",
                        "channel_no": 6,
                        "signal_strength_dbm": -58,
                        "is_same_channel": True,
                    }
                ],
                "test_details": [
                    {
                        "item_code": "ping_internet",
                        "target_host": "8.8.8.8",
                        "result_payload": {"latency_ms": 23.1},
                    }
                ],
            },
            db=db,
            current_user=current_user,
        )

    assert resp["success"] is True
    assert resp["data"]["scan_detail_count"] == 1
    assert resp["data"]["test_detail_count"] == 1

    added_entities = [call_args[0][0] for call_args in db.add.call_args_list]
    assert any(isinstance(item, SamplingScanDetail) for item in added_entities)
    assert any(isinstance(item, SamplingTestDetail) for item in added_entities)
    db.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_network_test_detail_returns_scan_and_test_details() -> None:
    db = AsyncMock()
    current_user = SimpleNamespace(id=7, role=UserRole.MEMBER)

    record = SimpleNamespace(
        id=5,
        user_id=7,
        sampling_task_id=12,
        dorm_room_id=1201,
        detect_mode="full",
        bssid_match=True,
        down_speed_mbps=98.2,
        up_speed_mbps=23.5,
        review_status=0,
        exception_auto=False,
        exception_manual=False,
    )
    scan_detail = SimpleNamespace(
        id=1,
        ssid="CampusNet",
        bssid="00:11:22:33:44:55",
        channel_no=6,
        signal_strength_dbm=-58,
        is_same_channel=True,
        is_adjacent_channel=False,
    )
    test_detail = SimpleNamespace(
        id=2,
        item_code="ping_internet",
        target_host="8.8.8.8",
        result_payload={"latency_ms": 23.1},
        save_to_record=True,
    )

    db.execute.side_effect = [
        _result_scalar_one_or_none(record),
        _result_scalars_all([scan_detail]),
        _result_scalars_all([test_detail]),
    ]

    resp = await network_test_detail(
        record_id=5,
        db=db,
        current_user=current_user,
    )

    assert resp["success"] is True
    assert len(resp["data"]["scan_details"]) == 1
    assert len(resp["data"]["test_details"]) == 1
    assert resp["data"]["scan_details"][0]["ssid"] == "CampusNet"
    assert resp["data"]["test_details"][0]["item_code"] == "ping_internet"


@pytest.mark.asyncio
async def test_network_test_single_item_rejects_mismatched_target_room() -> None:
    db = AsyncMock()
    current_user = SimpleNamespace(id=7, role=UserRole.MEMBER)

    db.execute.side_effect = [
        _result_scalar_one_or_none(SimpleNamespace()),
        _result_scalar_one_or_none(SimpleNamespace(id=88, dorm_room_id=2001)),
    ]

    with pytest.raises(HTTPException) as exc:
        await network_test_single_item(
            payload={
                "sampling_task_id": 1,
                "sampling_task_room_id": 88,
                "dorm_room_id": 3001,
            },
            db=db,
            current_user=current_user,
        )

    assert exc.value.status_code == 400


@pytest.mark.asyncio
async def test_network_test_single_item_persists_sampling_details() -> None:
    db = AsyncMock()
    current_user = SimpleNamespace(id=7, role=UserRole.MEMBER)

    db.execute.side_effect = [
        _result_scalar_one_or_none(SimpleNamespace()),
        _result_scalar_one_or_none(SimpleNamespace(id=88, dorm_room_id=2001)),
        _result_scalar_one_or_none(None),
        _result_scalar_one_or_none(None),
    ]

    async def _refresh(row):
        row.id = 901

    db.refresh.side_effect = _refresh

    resp = await network_test_single_item(
        payload={
            "sampling_task_id": 1,
            "sampling_task_room_id": 88,
            "dorm_room_id": 2001,
            "scan_details": [{"ssid": "CampusNet"}],
            "test_details": [{"item_code": "dns_resolve", "result_payload": {"ok": True}}],
        },
        db=db,
        current_user=current_user,
    )

    assert resp["success"] is True
    assert resp["data"]["id"] == 901
    assert resp["data"]["scan_detail_count"] == 1
    assert resp["data"]["test_detail_count"] == 1

    added_entities = [call_args[0][0] for call_args in db.add.call_args_list]
    assert any(isinstance(item, SamplingRecord) for item in added_entities)
    assert any(isinstance(item, SamplingScanDetail) for item in added_entities)
    assert any(isinstance(item, SamplingTestDetail) for item in added_entities)
