"""Integration tests for sampling target generation strategy (DEV-002)."""

from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import pytest
from sqlalchemy import select

from app.api.deps import get_current_active_admin, get_db
from app.main import app as fastapi_app
from app.models.app_user import AppUser, AppUserStatus
from app.models.building import Building, DormRoom
from app.models.member import UserRole
from app.models.sampling_record import SamplingRecord
from app.models.task_sampling import TaskSampling
from app.models.task_sampling_room import TaskSamplingRoom


pytestmark = pytest.mark.asyncio(loop_scope="session")


async def _seed_sampling_target_context(async_session):
    admin = AppUser(
        student_no="SAMP-ADMIN-001",
        password_hash="x",
        real_name="Sampling Admin",
        role_code="admin",
        status=int(AppUserStatus.ENABLED),
    )
    async_session.add(admin)
    await async_session.flush()

    building = Building(
        building_code="B-SAMP-ST-1",
        building_name="Sampling Strategy Building",
        campus_name="Main",
        area_name="A",
        status=1,
    )
    async_session.add(building)
    await async_session.flush()

    room_recent = DormRoom(
        building_id=building.id,
        room_no="101",
        target_ssid="CampusNet",
        target_bssid="00:11:22:33:44:55",
        active_repair_weight=10,
        status=1,
    )
    room_old = DormRoom(
        building_id=building.id,
        room_no="102",
        target_ssid="CampusNet",
        target_bssid="00:11:22:33:44:66",
        active_repair_weight=2,
        status=1,
    )
    room_existing = DormRoom(
        building_id=building.id,
        room_no="103",
        target_ssid="CampusNet",
        target_bssid="00:11:22:33:44:77",
        active_repair_weight=5,
        status=1,
    )
    async_session.add_all([room_recent, room_old, room_existing])
    await async_session.flush()

    task = TaskSampling(
        task_code="SAMP-STRATEGY-001",
        title="Sampling Strategy Task",
        description="integration",
        building_id=building.id,
        target_room_count=2,
        sample_strategy="weighted_random",
        exclude_days=30,
        assigned_by=admin.id,
        status=1,
    )
    async_session.add(task)
    await async_session.flush()

    existing_target = TaskSamplingRoom(
        sampling_task_id=task.id,
        dorm_room_id=room_existing.id,
        generated_weight=room_existing.active_repair_weight,
        is_completed=False,
    )
    async_session.add(existing_target)
    await async_session.flush()

    recent_record = SamplingRecord(
        sampling_task_id=task.id,
        sampling_task_room_id=existing_target.id,
        dorm_room_id=room_recent.id,
        user_id=admin.id,
        detect_mode="full",
        started_at=datetime.now(timezone.utc),
        finished_at=datetime.now(timezone.utc),
    )
    old_record = SamplingRecord(
        sampling_task_id=task.id,
        sampling_task_room_id=existing_target.id,
        dorm_room_id=room_old.id,
        user_id=admin.id,
        detect_mode="full",
        started_at=datetime.now(timezone.utc) - timedelta(days=40),
        finished_at=datetime.now(timezone.utc) - timedelta(days=40),
    )
    async_session.add_all([recent_record, old_record])
    await async_session.flush()

    old_record.created_at = datetime.now(timezone.utc) - timedelta(days=40)

    await async_session.commit()

    return {
        "admin_id": admin.id,
        "task_id": task.id,
        "room_recent_id": room_recent.id,
        "room_old_id": room_old.id,
        "room_existing_id": room_existing.id,
    }


async def test_generate_sampling_targets_respects_exclude_days_and_idempotency(async_client, async_session):
    ctx = await _seed_sampling_target_context(async_session)

    current_admin = SimpleNamespace(id=ctx["admin_id"], role=UserRole.ADMIN)

    async def override_get_db():
        yield async_session

    async def override_get_current_admin():
        return current_admin

    original_overrides = fastapi_app.dependency_overrides.copy()
    fastapi_app.dependency_overrides[get_db] = override_get_db
    fastapi_app.dependency_overrides[get_current_active_admin] = override_get_current_admin

    try:
        resp_first = await async_client.post(
            f"/api/v1/admin/tasks/{ctx['task_id']}/sampling/generate-targets",
            headers={"Host": "localhost"},
            json={"target_room_count": 2, "exclude_days": 30},
        )
        assert resp_first.status_code == 200, resp_first.text
        body_first = resp_first.json()
        assert body_first["success"] is True
        assert body_first["data"]["created"] == 1

        resp_second = await async_client.post(
            f"/api/v1/admin/tasks/{ctx['task_id']}/sampling/generate-targets",
            headers={"Host": "localhost"},
            json={"target_room_count": 2, "exclude_days": 30},
        )
        assert resp_second.status_code == 200, resp_second.text
        body_second = resp_second.json()
        assert body_second["success"] is True
        assert body_second["data"]["created"] == 0

    finally:
        fastapi_app.dependency_overrides.clear()
        fastapi_app.dependency_overrides.update(original_overrides)

    rows = (
        await async_session.execute(
            select(TaskSamplingRoom).where(TaskSamplingRoom.sampling_task_id == ctx["task_id"])
        )
    ).scalars().all()
    target_room_ids = {row.dorm_room_id for row in rows}

    assert ctx["room_existing_id"] in target_room_ids
    assert ctx["room_old_id"] in target_room_ids
    assert ctx["room_recent_id"] not in target_room_ids
    assert len(target_room_ids) == 2
