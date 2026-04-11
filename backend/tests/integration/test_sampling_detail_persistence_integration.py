"""Integration tests for sampling detail persistence (DEV-003)."""

from datetime import datetime, timezone
from types import SimpleNamespace

import pytest
from sqlalchemy import select

from app.api.deps import get_current_user, get_db
from app.main import app as fastapi_app
from app.models.app_user import AppUser, AppUserStatus
from app.models.building import Building, DormRoom
from app.models.member import UserRole
from app.models.sampling_record import SamplingRecord
from app.models.sampling_scan_detail import SamplingScanDetail
from app.models.sampling_test_detail import SamplingTestDetail
from app.models.task_sampling import TaskSampling
from app.models.task_sampling_room import TaskSamplingRoom
from app.models.task_sampling_user import TaskSamplingUser


pytestmark = pytest.mark.asyncio(loop_scope="session")


async def _seed_sampling_context(async_session):
    user = AppUser(
        student_no="SAMP-INT-001",
        password_hash="x",
        real_name="Sampling Tester",
        role_code="user",
        status=int(AppUserStatus.ENABLED),
    )
    async_session.add(user)
    await async_session.flush()

    building = Building(
        building_code="B-SAMP-1",
        building_name="Sampling Building",
        campus_name="Main",
        area_name="A",
        status=1,
    )
    async_session.add(building)
    await async_session.flush()

    room = DormRoom(
        building_id=building.id,
        room_no="101",
        target_ssid="CampusNet",
        target_bssid="00:11:22:33:44:55",
        active_repair_weight=5,
        status=1,
    )
    async_session.add(room)
    await async_session.flush()

    task = TaskSampling(
        task_code="SAMP-INT-TASK-001",
        title="Sampling Task",
        description="integration",
        building_id=building.id,
        target_room_count=1,
        sample_strategy="weighted_random",
        exclude_days=30,
        assigned_by=user.id,
        status=1,
    )
    async_session.add(task)
    await async_session.flush()

    task_user = TaskSamplingUser(
        sampling_task_id=task.id,
        user_id=user.id,
        role_in_task="executor",
    )
    task_room = TaskSamplingRoom(
        sampling_task_id=task.id,
        dorm_room_id=room.id,
        generated_weight=5,
        is_completed=False,
    )
    async_session.add(task_user)
    async_session.add(task_room)
    await async_session.commit()

    return user.id, task.id, task_room.id, room.id


async def test_network_test_submit_persists_master_and_two_detail_tables(async_client, async_session):
    user_id, task_id, task_room_id, room_id = await _seed_sampling_context(async_session)

    record = SamplingRecord(
        sampling_task_id=task_id,
        sampling_task_room_id=task_room_id,
        dorm_room_id=room_id,
        user_id=user_id,
        detect_mode="full",
        started_at=datetime.now(timezone.utc),
    )
    async_session.add(record)
    await async_session.commit()
    await async_session.refresh(record)

    current_user = SimpleNamespace(id=user_id, role=UserRole.MEMBER)

    async def override_get_db():
        yield async_session

    async def override_get_current_user():
        return current_user

    original_overrides = fastapi_app.dependency_overrides.copy()
    fastapi_app.dependency_overrides[get_db] = override_get_db
    fastapi_app.dependency_overrides[get_current_user] = override_get_current_user

    try:
        response = await async_client.post(
            f"/api/v1/network-tests/{record.id}/submit",
            headers={"Host": "localhost"},
            json={
                "loss_rate_pct": 1.2,
                "scan_details": [
                    {
                        "ssid": "CampusNet",
                        "bssid": "00:11:22:33:44:55",
                        "channel_no": 6,
                        "signal_strength_dbm": -60,
                        "is_same_channel": True,
                    },
                    {
                        "ssid": "CampusNet-Guest",
                        "bssid": "66:77:88:99:AA:BB",
                        "channel_no": 11,
                        "signal_strength_dbm": -73,
                        "is_adjacent_channel": True,
                    },
                ],
                "test_details": [
                    {
                        "item_code": "ping_internet",
                        "target_host": "8.8.8.8",
                        "result_payload": {"latency_ms": 22.4},
                    },
                    {
                        "item_code": "speedtest_down",
                        "target_host": "speed.example",
                        "result_payload": {"mbps": 98.6},
                    },
                ],
            },
        )
    finally:
        fastapi_app.dependency_overrides.clear()
        fastapi_app.dependency_overrides.update(original_overrides)

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["success"] is True
    assert body["data"]["id"] == record.id
    assert body["data"]["scan_detail_count"] == 2
    assert body["data"]["test_detail_count"] == 2

    refreshed_record = (
        await async_session.execute(select(SamplingRecord).where(SamplingRecord.id == record.id))
    ).scalar_one()
    assert refreshed_record.finished_at is not None

    scan_rows = (
        await async_session.execute(
            select(SamplingScanDetail).where(SamplingScanDetail.sampling_record_id == record.id)
        )
    ).scalars().all()
    test_rows = (
        await async_session.execute(
            select(SamplingTestDetail).where(SamplingTestDetail.sampling_record_id == record.id)
        )
    ).scalars().all()

    assert len(scan_rows) == 2
    assert len(test_rows) == 2


async def test_network_test_single_item_persists_master_and_two_detail_tables(async_client, async_session):
    user_id, task_id, task_room_id, room_id = await _seed_sampling_context(async_session)
    current_user = SimpleNamespace(id=user_id, role=UserRole.MEMBER)

    async def override_get_db():
        yield async_session

    async def override_get_current_user():
        return current_user

    original_overrides = fastapi_app.dependency_overrides.copy()
    fastapi_app.dependency_overrides[get_db] = override_get_db
    fastapi_app.dependency_overrides[get_current_user] = override_get_current_user

    try:
        response = await async_client.post(
            "/api/v1/network-tests/single-item",
            headers={"Host": "localhost"},
            json={
                "sampling_task_id": task_id,
                "sampling_task_room_id": task_room_id,
                "dorm_room_id": room_id,
                "item": "single-item-check",
                "scan_details": [
                    {
                        "ssid": "CampusNet",
                        "bssid": "00:11:22:33:44:55",
                        "channel_no": 6,
                    }
                ],
                "test_details": [
                    {
                        "item_code": "dns_resolve",
                        "target_host": "dns.example",
                        "result_payload": {"ok": True},
                    }
                ],
            },
        )
    finally:
        fastapi_app.dependency_overrides.clear()
        fastapi_app.dependency_overrides.update(original_overrides)

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["success"] is True
    record_id = body["data"]["id"]
    assert body["data"]["scan_detail_count"] == 1
    assert body["data"]["test_detail_count"] == 1

    record = (
        await async_session.execute(select(SamplingRecord).where(SamplingRecord.id == record_id))
    ).scalar_one()
    assert record.detect_mode == "single_item"

    scan_rows = (
        await async_session.execute(
            select(SamplingScanDetail).where(SamplingScanDetail.sampling_record_id == record_id)
        )
    ).scalars().all()
    test_rows = (
        await async_session.execute(
            select(SamplingTestDetail).where(SamplingTestDetail.sampling_record_id == record_id)
        )
    ).scalars().all()

    assert len(scan_rows) == 1
    assert len(test_rows) == 1
