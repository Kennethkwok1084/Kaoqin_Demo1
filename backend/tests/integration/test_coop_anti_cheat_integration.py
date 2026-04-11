"""Integration tests for coop sign anti-cheat workflow (DEV-004)."""

from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import pytest
from sqlalchemy import select

from app.api.deps import get_current_user, get_db
from app.main import app as fastapi_app
from app.models.app_user import AppUser, AppUserStatus
from app.models.building import Building
from app.models.member import UserRole
from app.models.task_coop import TaskCoop
from app.models.task_coop_attendance import TaskCoopAttendance
from app.models.task_coop_signup import TaskCoopSignup
from app.models.task_coop_slot import TaskCoopSlot
from app.models.todo_item import TodoItem


pytestmark = pytest.mark.asyncio(loop_scope="session")


async def _seed_coop_context(async_session):
    user = AppUser(
        student_no="COOP-INT-001",
        password_hash="x",
        real_name="Coop Tester",
        role_code="user",
        status=int(AppUserStatus.ENABLED),
    )
    async_session.add(user)
    await async_session.flush()

    building = Building(
        building_code="B-COOP-1",
        building_name="Coop Building",
        campus_name="Main",
        area_name="A",
        longitude=113.000001,
        latitude=23.000001,
        status=1,
    )
    async_session.add(building)
    await async_session.flush()

    task = TaskCoop(
        task_code="COOP-INT-TASK-001",
        title="Coop Task",
        description="integration",
        location_text="A1",
        building_id=building.id,
        signup_need_review=False,
        sign_in_mode_mask=0,
        status=1,
        created_by=user.id,
    )
    async_session.add(task)
    await async_session.flush()

    slot = TaskCoopSlot(
        coop_task_id=task.id,
        slot_title="Morning",
        start_time=datetime.now(timezone.utc) - timedelta(hours=1),
        end_time=datetime.now(timezone.utc) + timedelta(hours=1),
        signup_limit=5,
        sort_no=1,
        status=1,
    )
    async_session.add(slot)
    await async_session.flush()

    signup = TaskCoopSignup(
        coop_task_id=task.id,
        coop_slot_id=slot.id,
        user_id=user.id,
        signup_source="self",
        status=1,
    )
    async_session.add(signup)
    await async_session.commit()
    await async_session.refresh(signup)

    return user.id, task.id, slot.id, signup.id


async def test_sign_in_invalid_qr_creates_abnormal_todo(async_client, async_session):
    user_id, task_id, slot_id, signup_id = await _seed_coop_context(async_session)
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
            f"/api/v1/tasks/{task_id}/sign-in",
            headers={"Host": "localhost"},
            json={
                "slot_id": slot_id,
                "sign_in_type": "qr",
                "qr_token": "bad-token",
            },
        )
    finally:
        fastapi_app.dependency_overrides.clear()
        fastapi_app.dependency_overrides.update(original_overrides)

    assert response.status_code == 400, response.text

    todo = (
        await async_session.execute(
            select(TodoItem).where(
                TodoItem.todo_type == "coop_sign_abnormal",
                TodoItem.source_biz_type == "task_coop_signup",
                TodoItem.source_biz_id == signup_id,
            )
        )
    ).scalar_one_or_none()
    assert todo is not None
    assert "二维码验签" in (todo.content or "")


async def test_sign_out_device_mismatch_creates_abnormal_todo(async_client, async_session):
    user_id, task_id, slot_id, signup_id = await _seed_coop_context(async_session)

    attendance = TaskCoopAttendance(
        coop_signup_id=signup_id,
        sign_in_at=datetime.now(timezone.utc) - timedelta(minutes=20),
        sign_in_type="manual",
        remark='{"anti_cheat_device_id":"device-A"}',
    )
    async_session.add(attendance)
    await async_session.commit()
    await async_session.refresh(attendance)

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
            f"/api/v1/tasks/{task_id}/sign-out",
            headers={"Host": "localhost"},
            json={
                "slot_id": slot_id,
                "sign_out_type": "manual",
                "device_id": "device-B",
            },
        )
    finally:
        fastapi_app.dependency_overrides.clear()
        fastapi_app.dependency_overrides.update(original_overrides)

    assert response.status_code == 400, response.text

    todo = (
        await async_session.execute(
            select(TodoItem).where(
                TodoItem.todo_type == "coop_sign_abnormal",
                TodoItem.source_biz_type == "task_coop_attendance",
                TodoItem.source_biz_id == attendance.id,
            )
        )
    ).scalar_one_or_none()
    assert todo is not None
    assert "设备指纹不一致" in (todo.content or "")
