"""Unit tests for migrated repair order and media APIs."""

from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest
from fastapi import HTTPException

from app.api.v1.media import get_media
from app.api.v1.repair_orders import (
    create_repair_order,
    repair_order_ocr,
    repair_order_ocr_correct,
    repair_match_candidates,
    update_repair_order,
)
from app.models.member import UserRole
from app.models.repair_ticket import RepairTicket


def _result_scalar_one_or_none(value):
    result = Mock()
    result.scalar_one_or_none.return_value = value
    return result


@pytest.mark.asyncio
async def test_create_repair_order_success() -> None:
    db = AsyncMock()

    async def _refresh(obj):
        obj.id = 321

    db.refresh.side_effect = _refresh

    payload = {
        "title": "宿舍网络故障",
        "issue_content": "无法上网",
        "issue_category": "network",
    }

    resp = await create_repair_order(
        payload=payload,
        db=db,
        current_user=SimpleNamespace(id=9),
    )

    assert resp["success"] is True
    assert resp["data"]["id"] == 321
    db.add.assert_called_once()
    added = db.add.call_args[0][0]
    assert isinstance(added, RepairTicket)
    assert added.created_by == 9
    db.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_get_media_not_found() -> None:
    db = AsyncMock()
    db.execute.return_value = _result_scalar_one_or_none(None)

    with pytest.raises(HTTPException) as exc:
        await get_media(
            media_id=123,
            db=db,
            _=SimpleNamespace(id=1),
        )

    assert exc.value.status_code == 404
    assert exc.value.detail == "媒体不存在"


@pytest.mark.asyncio
async def test_get_media_forbidden_for_non_owner() -> None:
    db = AsyncMock()
    row = SimpleNamespace(
        id=123,
        uploaded_by=8,
        biz_type="repair",
        biz_id=77,
        file_type="image",
        file_name="x.jpg",
        storage_path="/tmp/x.jpg",
        file_size=100,
        watermark_payload=None,
    )
    db.execute.return_value = _result_scalar_one_or_none(row)

    with pytest.raises(HTTPException) as exc:
        await get_media(
            media_id=123,
            db=db,
            current_user=SimpleNamespace(id=1, role=UserRole.MEMBER),
        )

    assert exc.value.status_code == 403


@pytest.mark.asyncio
async def test_update_repair_order_forbidden_for_non_owner() -> None:
    db = AsyncMock()
    ticket = SimpleNamespace(id=66, created_by=9)
    db.execute.return_value = _result_scalar_one_or_none(ticket)

    with pytest.raises(HTTPException) as exc:
        await update_repair_order(
            ticket_id=66,
            payload={"title": "new"},
            db=db,
            current_user=SimpleNamespace(id=2, role=UserRole.MEMBER),
        )

    assert exc.value.status_code == 403


@pytest.mark.asyncio
async def test_repair_match_candidates_empty_when_no_repair_no() -> None:
    db = AsyncMock()
    ticket = SimpleNamespace(id=10, created_by=9, repair_no=None)
    db.execute.return_value = _result_scalar_one_or_none(ticket)

    resp = await repair_match_candidates(
        ticket_id=10,
        db=db,
        current_user=SimpleNamespace(id=9, role=UserRole.MEMBER),
    )

    assert resp["success"] is True
    assert resp["data"]["total"] == 0


@pytest.mark.asyncio
async def test_repair_order_ocr_structures_and_applies_fields() -> None:
    db = AsyncMock()

    ticket = SimpleNamespace(
        id=10,
        created_by=9,
        repair_no=None,
        report_user_name=None,
        report_phone=None,
        issue_content=None,
        issue_category=None,
        ocr_payload=None,
    )
    db.execute.return_value = _result_scalar_one_or_none(ticket)

    resp = await repair_order_ocr(
        ticket_id=10,
        payload={
            "raw_text": "报修人: 张三 联系电话: 13812345678 无法上网，WIFI掉线",
            "apply_to_ticket": True,
        },
        db=db,
        current_user=SimpleNamespace(id=9, role=UserRole.MEMBER),
    )

    assert resp["success"] is True
    assert resp["data"]["id"] == 10
    assert resp["data"]["structured_data"]["report_phone"] == "13812345678"
    assert ticket.report_phone == "13812345678"
    assert ticket.issue_category == "network"
    assert isinstance(ticket.ocr_payload, dict)
    assert ticket.ocr_payload.get("version") == "v2"
    db.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_repair_order_ocr_correct_updates_structured_and_ticket() -> None:
    db = AsyncMock()

    ticket = SimpleNamespace(
        id=11,
        created_by=9,
        repair_no=None,
        report_user_name="张三",
        report_phone="13800000000",
        issue_content="旧内容",
        issue_category="other",
        ocr_payload={
            "version": "v2",
            "structured_data": {
                "report_user_name": "张三",
                "report_phone": "13800000000",
                "issue_content": "旧内容",
                "issue_category": "other",
            },
            "manual_correction": {},
            "corrected_fields": [],
            "applied_fields": [],
        },
    )
    db.execute.return_value = _result_scalar_one_or_none(ticket)

    resp = await repair_order_ocr_correct(
        ticket_id=11,
        payload={
            "manual_correction": {
                "report_phone": "13912345678",
                "issue_category": "network",
            },
            "force_overwrite": True,
        },
        db=db,
        current_user=SimpleNamespace(id=9, role=UserRole.MEMBER),
    )

    assert resp["success"] is True
    assert ticket.report_phone == "13912345678"
    assert ticket.issue_category == "network"
    assert "report_phone" in resp["data"]["corrected_fields"]
    assert isinstance(ticket.ocr_payload, dict)
    assert ticket.ocr_payload.get("manual_correction", {}).get("report_phone") == "13912345678"
    db.commit.assert_awaited_once()
