import pytest
from datetime import date, datetime, timedelta

from app.core.security import create_access_token
from app.models.member import Member, UserRole
from app.models.task import RepairTask, TaskStatus, TaskType, TaskCategory, TaskPriority


@pytest.mark.asyncio
async def test_cycle_summary_monthly_admin(client_with_db, async_session):
    """组长/管理员可查看周期内全员考勤汇总。"""
    # 管理员
    admin = Member(
        username="leader1",
        name="组长甲",
        class_name="一组",
        password_hash="hash",
        role=UserRole.GROUP_LEADER,
        is_active=True,
    )
    m1 = Member(
        username="u1",
        name="张三",
        class_name="一组",
        password_hash="hash",
        role=UserRole.MEMBER,
        is_active=True,
    )
    m2 = Member(
        username="u2",
        name="李四",
        class_name="一组",
        password_hash="hash",
        role=UserRole.MEMBER,
        is_active=True,
    )
    async_session.add_all([admin, m1, m2])
    await async_session.commit()
    await async_session.refresh(admin)
    await async_session.refresh(m1)
    await async_session.refresh(m2)

    # 本月两天任务工时
    today = date.today()
    d1 = today.replace(day=1)
    d2 = d1 + timedelta(days=1)
    # 张三两天完成报修任务：120min + 60min
    t1 = RepairTask(
        task_id=f"R_{m1.id}_1",
        title="test",
        member_id=m1.id,
        status=TaskStatus.COMPLETED,
        task_type=TaskType.ONLINE,
        category=TaskCategory.NETWORK_REPAIR,
        priority=TaskPriority.MEDIUM,
        completion_time=datetime.combine(d1, datetime.min.time()),
    )
    t1.work_minutes = 120
    t2 = RepairTask(
        task_id=f"R_{m1.id}_2",
        title="test2",
        member_id=m1.id,
        status=TaskStatus.COMPLETED,
        task_type=TaskType.ONLINE,
        category=TaskCategory.NETWORK_REPAIR,
        priority=TaskPriority.MEDIUM,
        completion_time=datetime.combine(d2, datetime.min.time()),
    )
    t2.work_minutes = 60
    # 李四一天完成报修任务：210min
    t3 = RepairTask(
        task_id=f"R_{m2.id}_1",
        title="test3",
        member_id=m2.id,
        status=TaskStatus.COMPLETED,
        task_type=TaskType.ONLINE,
        category=TaskCategory.NETWORK_REPAIR,
        priority=TaskPriority.MEDIUM,
        completion_time=datetime.combine(d1, datetime.min.time()),
    )
    t3.work_minutes = 210

    async_session.add_all([t1, t2, t3])
    await async_session.commit()

    token = create_access_token(str(admin.id))
    headers = {"Authorization": f"Bearer {token}"}

    # 调用按月统计（cycle_type=monthly）
    month_str = f"{today.year}-{today.month:02d}"
    resp = client_with_db.get(
        f"/api/v1/attendance/cycle-summary?cycle_type=monthly&month={month_str}",
        headers=headers,
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body.get("success") is True

    data = body.get("data") or {}
    records = data.get("records") or []
    # 至少包含两名成员
    member_names = [r.get("member_name") for r in records]
    assert "张三" in member_names and "李四" in member_names

    # 张三累计 3.0 小时（180分钟）
    zhang = next(r for r in records if r.get("member_name") == "张三")
    assert zhang.get("total_work_hours") == 3.0
    assert "average_daily_hours" in zhang and "repair_minutes" in zhang
    # 李四累计 3.5 小时
    li = next(r for r in records if r.get("member_name") == "李四")
    assert li.get("total_work_hours") == 3.5


@pytest.mark.asyncio
async def test_cycle_export_and_download_csv(client_with_db, async_session, tmp_path):
    """导出周期汇总CSV并下载。"""
    # 组长
    leader = Member(
        username="leader2",
        name="组长乙",
        class_name="一组",
        password_hash="hash",
        role=UserRole.GROUP_LEADER,
        is_active=True,
    )
    member = Member(
        username="mexp",
        name="王五",
        class_name="一组",
        password_hash="hash",
        role=UserRole.MEMBER,
        is_active=True,
    )
    async_session.add_all([leader, member])
    await async_session.commit()
    await async_session.refresh(leader)
    await async_session.refresh(member)

    # 一条完成的报修任务（150分钟）
    t = RepairTask(
        task_id=f"R_EXP_{member.id}",
        title="exp",
        member_id=member.id,
        status=TaskStatus.COMPLETED,
        task_type=TaskType.ONLINE,
        category=TaskCategory.NETWORK_REPAIR,
        priority=TaskPriority.MEDIUM,
        completion_time=datetime.combine(date.today(), datetime.min.time()),
    )
    t.work_minutes = 150
    async_session.add(t)
    await async_session.commit()

    token = create_access_token(str(leader.id))
    headers = {"Authorization": f"Bearer {token}"}

    # 导出为CSV
    resp = client_with_db.get("/api/v1/attendance/cycle-export?format=csv", headers=headers)
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body.get("success") is True
    filename = body.get("filename")
    assert filename and filename.endswith(".csv")

    # 下载文件
    dl = client_with_db.get(f"/api/v1/attendance/download/{filename}", headers=headers)
    assert dl.status_code == 200
    assert dl.headers.get("content-type", "").startswith("text/csv")
