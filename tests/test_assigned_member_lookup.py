import pytest

from app.models.member import Member
from app.services.import_service import DataImportService


@pytest.mark.asyncio
async def test_assigned_to_name_matches_member(db_session):
    member = Member(
        username="tech1",
        name="张三",
        class_name="一班",
        password_hash="hash",
        phone="13800001111",
    )
    db_session.add(member)
    await db_session.commit()
    await db_session.refresh(member)

    service = DataImportService(db_session)
    import_data = {
        "title": "测试任务",
        "assigned_to": "张三(信息处)",
    }

    task = await service._create_repair_task_from_import_data(import_data, 1)

    assert task.member_id == member.id


@pytest.mark.asyncio
async def test_assigned_to_unknown_defaults(db_session):
    service = DataImportService(db_session)
    import_data = {
        "title": "未知处理人任务",
        "assigned_to": "不存在的成员(信息处)",
    }

    task = await service._create_repair_task_from_import_data(import_data, 1)
    default_member = await service._get_or_create_default_member()

    assert task.member_id == default_member.id
