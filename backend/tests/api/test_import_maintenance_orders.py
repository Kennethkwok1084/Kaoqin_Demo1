import logging
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.api.v1.repair import import_maintenance_orders
from app.models.member import Member, UserRole


@pytest.mark.asyncio
async def test_import_orders_chinese_assignee(monkeypatch):
    current_user = Member(
        id=1,
        username="leader",
        student_id="1001",
        name="组长",
        role=UserRole.GROUP_LEADER,
    )
    matched_member = Member(
        id=2,
        username="zhangsan",
        student_id="1002",
        name="张三",
        role=UserRole.MEMBER,
    )

    existing_task_result = MagicMock()
    existing_task_result.scalar_one_or_none.return_value = None

    member_result = MagicMock()
    member_result.scalar_one_or_none.return_value = matched_member

    db = AsyncMock()
    db.execute.side_effect = [existing_task_result, member_result]

    create_task_mock = AsyncMock(return_value=MagicMock(task_id="T001"))

    class DummyTaskService:
        def __init__(self, db):
            self.create_repair_task = create_task_mock

    monkeypatch.setattr("app.services.task_service.TaskService", DummyTaskService)

    import_data = {"maintenance_orders": [{"title": "task", "负责人": "张三"}]}

    result = await import_maintenance_orders(
        import_data, current_user=current_user, db=db
    )

    assert result["data"]["matched_assignees"] == 1
    create_task_mock.assert_awaited_once()
    assert create_task_mock.await_args.args[0]["assigned_to"] == matched_member.id


@pytest.mark.asyncio
async def test_import_orders_missing_assignee_logs_warning(monkeypatch, caplog):
    current_user = Member(
        id=1,
        username="leader",
        student_id="1001",
        name="组长",
        role=UserRole.GROUP_LEADER,
    )

    existing_task_result = MagicMock()
    existing_task_result.scalar_one_or_none.return_value = None

    db = AsyncMock()
    db.execute.return_value = existing_task_result

    create_task_mock = AsyncMock(return_value=MagicMock(task_id="T001"))

    class DummyTaskService:
        def __init__(self, db):
            self.create_repair_task = create_task_mock

    monkeypatch.setattr("app.services.task_service.TaskService", DummyTaskService)

    import_data = {"maintenance_orders": [{"title": "task"}]}

    caplog.set_level(logging.WARNING)
    await import_maintenance_orders(import_data, current_user=current_user, db=db)

    assert any(
        "缺少处理人" in record.message or "Missing assignee" in record.message
        for record in caplog.records
    )
