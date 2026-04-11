"""Integration tests for DEV-006 rule replay consistency."""

import json
from types import SimpleNamespace

import pytest
from sqlalchemy import select

from app.api.deps import get_current_active_admin, get_db
from app.main import app as fastapi_app
from app.models.app_user import AppUser, AppUserStatus
from app.models.review_log import ReviewLog
from app.models.workhour_entry import WorkhourEntry
from app.models.workhour_rule import WorkhourRule


pytestmark = pytest.mark.asyncio(loop_scope="session")


async def _seed_recalculate_context(async_session):
    admin = AppUser(
        student_no="WH-ADMIN-INT-001",
        password_hash="x",
        real_name="Workhour Admin",
        role_code="admin",
        status=int(AppUserStatus.ENABLED),
    )
    worker = AppUser(
        student_no="WH-USER-INT-001",
        password_hash="x",
        real_name="Workhour User",
        role_code="user",
        status=int(AppUserStatus.ENABLED),
    )
    async_session.add_all([admin, worker])
    await async_session.flush()

    rule = WorkhourRule(
        rule_code="repair_recalc_replay_int",
        rule_name="Repair Replay Rule",
        biz_type="repair",
        formula_desc="base + 10",
        formula_json={
            "mode": "base",
            "add_minutes": 10,
            "min_minutes": 0,
            "max_minutes": 200,
        },
        is_enabled=True,
    )
    async_session.add(rule)
    await async_session.flush()

    entry = WorkhourEntry(
        biz_type="repair",
        biz_id=9001,
        user_id=worker.id,
        source_rule_id=rule.id,
        base_minutes=40,
        final_minutes=40,
        review_status=0,
    )
    async_session.add(entry)
    await async_session.commit()
    await async_session.refresh(admin)
    await async_session.refresh(rule)
    await async_session.refresh(entry)

    return {
        "admin_id": admin.id,
        "rule_id": rule.id,
        "entry_id": entry.id,
    }


async def test_recalculate_replay_keeps_rule_snapshot_after_formula_switch(async_client, async_session):
    ctx = await _seed_recalculate_context(async_session)
    current_admin = SimpleNamespace(id=ctx["admin_id"])

    async def override_get_db():
        yield async_session

    async def override_get_current_admin():
        return current_admin

    original_overrides = fastapi_app.dependency_overrides.copy()
    fastapi_app.dependency_overrides[get_db] = override_get_db
    fastapi_app.dependency_overrides[get_current_active_admin] = override_get_current_admin

    try:
        resp_v1 = await async_client.post(
            "/api/v1/internal/workhours/recalculate",
            headers={"Host": "localhost"},
            json={"entry_id": ctx["entry_id"], "reason": "rule_v1", "include_details": True},
        )
        assert resp_v1.status_code == 200, resp_v1.text
        body_v1 = resp_v1.json()
        assert body_v1["success"] is True
        assert body_v1["data"]["updated"] == 1
        assert body_v1["data"]["changed"] == 1
        assert body_v1["data"]["details"][0]["before"] == 40
        assert body_v1["data"]["details"][0]["after"] == 50

        rule = (
            await async_session.execute(select(WorkhourRule).where(WorkhourRule.id == ctx["rule_id"]))
        ).scalar_one()
        rule.formula_desc = "base + 30"
        rule.formula_json = {
            "mode": "base",
            "add_minutes": 30,
            "min_minutes": 0,
            "max_minutes": 200,
        }
        await async_session.commit()

        resp_v2 = await async_client.post(
            "/api/v1/internal/workhours/recalculate",
            headers={"Host": "localhost"},
            json={"entry_id": ctx["entry_id"], "reason": "rule_v2", "include_details": True},
        )
        assert resp_v2.status_code == 200, resp_v2.text
        body_v2 = resp_v2.json()
        assert body_v2["success"] is True
        assert body_v2["data"]["updated"] == 1
        assert body_v2["data"]["changed"] == 1
        assert body_v2["data"]["details"][0]["before"] == 50
        assert body_v2["data"]["details"][0]["after"] == 70

    finally:
        fastapi_app.dependency_overrides.clear()
        fastapi_app.dependency_overrides.update(original_overrides)

    entry_after = (
        await async_session.execute(select(WorkhourEntry).where(WorkhourEntry.id == ctx["entry_id"]))
    ).scalar_one()
    assert entry_after.final_minutes == 70

    logs = (
        await async_session.execute(
            select(ReviewLog)
            .where(
                ReviewLog.biz_type == "workhour_entry",
                ReviewLog.biz_id == ctx["entry_id"],
                ReviewLog.review_type == "workhour_recalculate",
                ReviewLog.action_code == "recalculate",
            )
            .order_by(ReviewLog.id)
        )
    ).scalars().all()

    assert len(logs) == 2

    log_v1 = json.loads(logs[0].review_note or "{}")
    log_v2 = json.loads(logs[1].review_note or "{}")

    assert log_v1["reason"] == "rule_v1"
    assert log_v1["before"] == 40
    assert log_v1["after"] == 50
    assert log_v1["replay"]["formula"]["add_minutes"] == 10
    assert log_v1["replay"]["context"]["final_minutes"] == 40

    assert log_v2["reason"] == "rule_v2"
    assert log_v2["before"] == 50
    assert log_v2["after"] == 70
    assert log_v2["replay"]["formula"]["add_minutes"] == 30
    assert log_v2["replay"]["context"]["final_minutes"] == 50
