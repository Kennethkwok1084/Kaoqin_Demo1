"""Unit tests for rule-based workhour recalculation API."""

from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest

from app.api.v1 import config_workhour
from app.api.v1.config_workhour import recalculate_workhours
from app.models.review_log import ReviewLog


def _result_scalar_one_or_none(value):
    result = Mock()
    result.scalar_one_or_none.return_value = value
    return result


def _result_scalars_all(values):
    scalars = Mock()
    scalars.all.return_value = values
    result = Mock()
    result.scalars.return_value = scalars
    return result


@pytest.mark.asyncio
async def test_recalculate_workhours_apply_rule_and_record_replay(monkeypatch) -> None:
    db = AsyncMock()
    entry = SimpleNamespace(
        id=101,
        biz_type="repair",
        biz_id=88,
        user_id=9,
        base_minutes=40,
        final_minutes=40,
        review_status=0,
        source_rule_id=None,
    )
    db.execute.return_value = _result_scalar_one_or_none(entry)

    rule = SimpleNamespace(
        id=12,
        formula_json={
            "mode": "base",
            "base_multiplier": 1,
            "add_minutes": 5,
            "conditions": [
                {
                    "field": "biz_id",
                    "op": "eq",
                    "value": 88,
                    "then_add": 10,
                    "reason": "repair bonus",
                }
            ],
            "min_minutes": 0,
            "max_minutes": 200,
        },
    )
    monkeypatch.setattr(
        config_workhour,
        "_resolve_recalc_rule",
        AsyncMock(return_value=rule),
    )

    resp = await recalculate_workhours(
        payload={"entry_id": 101, "reason": "rule_changed", "include_details": True},
        db=db,
        current_user=SimpleNamespace(id=1),
    )

    assert resp["success"] is True
    assert resp["data"]["updated"] == 1
    assert resp["data"]["changed"] == 1
    assert entry.final_minutes == 55
    assert entry.source_rule_id == 12
    assert resp["data"]["details"][0]["rule_id"] == 12
    assert len(resp["data"]["details"][0]["matched_conditions"]) == 1

    added_logs = [call.args[0] for call in db.add.call_args_list]
    assert len(added_logs) == 1
    assert isinstance(added_logs[0], ReviewLog)
    assert added_logs[0].action_code == "recalculate"
    assert "rule_changed" in (added_logs[0].review_note or "")
    db.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_recalculate_workhours_fallback_to_base_when_rule_missing(monkeypatch) -> None:
    db = AsyncMock()
    entry = SimpleNamespace(
        id=102,
        biz_type="inspection",
        biz_id=66,
        user_id=20,
        base_minutes=35,
        final_minutes=90,
        review_status=0,
        source_rule_id=None,
    )
    db.execute.return_value = _result_scalars_all([entry])

    monkeypatch.setattr(
        config_workhour,
        "_resolve_recalc_rule",
        AsyncMock(return_value=None),
    )

    resp = await recalculate_workhours(
        payload={"include_details": True},
        db=db,
        current_user=SimpleNamespace(id=2),
    )

    assert resp["success"] is True
    assert resp["data"]["updated"] == 1
    assert resp["data"]["changed"] == 1
    assert entry.final_minutes == 35
    assert resp["data"]["details"][0]["rule_id"] is None

    added_logs = [call.args[0] for call in db.add.call_args_list]
    assert len(added_logs) == 1
    assert isinstance(added_logs[0], ReviewLog)
    db.commit.assert_awaited_once()
