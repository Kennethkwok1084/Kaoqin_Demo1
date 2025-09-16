import pytest
from datetime import datetime, timedelta, timezone

from app.core.security import create_access_token
from app.models.member import Member, UserRole
from app.models.task import RepairTask, TaskStatus, TaskType, TaskCategory, TaskPriority


@pytest.mark.asyncio
async def test_attendance_records_join_with_explicit_onclause(client_with_db, async_session):
    """
    验证 GET /api/v1/attendance/records 在存在多外键的情况下，
    通过显式 onclause 关联 Member 后能正常返回数据（不再 500）。
    """
    # 1) 创建成员（普通成员即可）
    user = Member(
        username="att_join_user",
        name="联调用户",
        class_name="测试组",
        password_hash="hash",
        role=UserRole.MEMBER,
        is_active=True,
    )
    async_session.add(user)
    await async_session.commit()
    await async_session.refresh(user)

    # 2) 为该成员创建一条已完成的维修任务（用于生成工时记录）
    completed_at = datetime.now(timezone.utc) - timedelta(days=1)
    task = RepairTask(
        task_id=f"UT_ATT_JOIN_{user.id}",
        title="联调-维修任务",
        member_id=user.id,
        status=TaskStatus.COMPLETED,
        task_type=TaskType.ONLINE,
        category=TaskCategory.NETWORK_REPAIR,
        priority=TaskPriority.MEDIUM,
        completion_time=completed_at,
    )
    task.work_minutes = 120  # 2 小时
    async_session.add(task)
    await async_session.commit()

    # 3) 生成访问令牌并请求接口
    token = create_access_token(str(user.id))
    headers = {"Authorization": f"Bearer {token}"}

    resp = client_with_db.get("/api/v1/attendance/records", headers=headers)
    assert resp.status_code == 200, resp.text

    data = resp.json()
    assert isinstance(data, list)
    assert any(r.get("work_minutes") == 120 for r in data)
    # 返回中包含成员姓名，证明 join Member 成功
    assert any(r.get("member_name") == user.name for r in data)

