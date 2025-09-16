import pytest
from httpx import AsyncClient
from sqlalchemy import select, desc

from app.main import app
from app.core.security import create_access_token
from app.models.member import Member, UserRole
from app.models.task import RepairTask


@pytest.mark.asyncio
async def test_import_maintenance_orders_assignee_name_with_department_suffix(db_session):
    """
    确认“处理人”字段为“姓名+(信息处)”格式时，能正确匹配到成员并分配。
    场景：处理人 = "郑泰跃+(信息处)" -> 匹配到 name == "郑泰跃" 的成员。
    """
    # 准备成员数据：导入者（组长）与被分配处理的成员
    current_user = Member(
        username="group_leader",
        name="组长甲",
        class_name="一组",
        password_hash="hash",
        role=UserRole.GROUP_LEADER,
        is_active=True,
    )
    assignee = Member(
        username="zhengty",
        name="郑泰跃",
        class_name="一组",
        password_hash="hash",
        role=UserRole.MEMBER,
        is_active=True,
    )

    db_session.add_all([current_user, assignee])
    await db_session.commit()
    await db_session.refresh(current_user)
    await db_session.refresh(assignee)

    # 生成认证Token（组长权限）
    token = create_access_token(str(current_user.id))

    # 构造导入数据：处理人为“郑泰跃+(信息处)”
    payload = {
        "maintenance_orders": [
            {
                "title": "网络故障测试单",
                "reporter_name": "王五",
                "reporter_contact": "13800138000",
                "处理人": "郑泰跃+(信息处)",
            }
        ]
    }

    headers = {"Authorization": f"Bearer {token}"}

    async with AsyncClient(app=app, base_url="http://test") as ac:
        resp = await ac.post("/api/v1/tasks/maintenance-orders/import", json=payload, headers=headers)

    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body.get("success") is True

    data = body.get("data") or {}
    # 确认匹配到了处理人
    assert data.get("matched_assignees", 0) >= 1
    matches = data.get("assignee_matches", [])
    assert any("郑泰跃" in str(m) for m in matches)

    # 验证创建的任务已分配给目标成员
    result = await db_session.execute(
        select(RepairTask).order_by(desc(RepairTask.id))
    )
    created_task = result.scalars().first()
    assert created_task is not None
    assert created_task.member_id == assignee.id


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "field_key,assignee_value",
    [
        ("处理人", "郑泰跃＋（信息处）"),        # 全角加号 + 全角括号
        ("处理人", "郑泰跃/(信息处)"),        # 斜杠 + 半角括号
        ("负责人", "郑泰跃 |(信息处)"),       # 竖线 + 半角括号
        ("负责人", "郑泰跃｜（信息处）"),     # 全角竖线 + 全角括号
    ],
)
async def test_import_maintenance_orders_assignee_various_separators(db_session, field_key, assignee_value):
    """
    处理人/负责人字段中存在多种分隔符与括号时，确保清洗后仍能匹配成员。
    """
    # 准备成员数据：导入者（组长）与被分配处理的成员
    current_user = Member(
        username="group_leader2",
        name="组长乙",
        class_name="一组",
        password_hash="hash",
        role=UserRole.GROUP_LEADER,
        is_active=True,
    )
    assignee = Member(
        username="zhengty2",
        name="郑泰跃",
        class_name="一组",
        password_hash="hash",
        role=UserRole.MEMBER,
        is_active=True,
    )

    db_session.add_all([current_user, assignee])
    await db_session.commit()
    await db_session.refresh(current_user)
    await db_session.refresh(assignee)

    token = create_access_token(str(current_user.id))

    payload = {
        "maintenance_orders": [
            {
                "title": "网络故障测试单-分隔符",
                "reporter_name": "李四",
                "reporter_contact": "13800138001",
                field_key: assignee_value,
            }
        ]
    }

    headers = {"Authorization": f"Bearer {token}"}

    async with AsyncClient(app=app, base_url="http://test") as ac:
        resp = await ac.post("/api/v1/tasks/maintenance-orders/import", json=payload, headers=headers)

    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body.get("success") is True

    data = body.get("data") or {}
    assert data.get("matched_assignees", 0) >= 1
    matches = data.get("assignee_matches", [])
    assert any("郑泰跃" in str(m) for m in matches)

    # 验证创建的任务已分配给目标成员
    result = await db_session.execute(
        select(RepairTask).order_by(desc(RepairTask.id))
    )
    created_task = result.scalars().first()
    assert created_task is not None
    assert created_task.member_id == assignee.id

