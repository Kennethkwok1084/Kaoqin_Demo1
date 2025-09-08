"""
统计API真正功能测试
针对app/api/v1/statistics.py (当前仅6.19%覆盖率)，提供真正的功能测试
预期覆盖率提升至50%+
"""

from datetime import datetime, timedelta

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_password_hash
from app.models.attendance import AttendanceExceptionStatus, AttendanceRecord
from app.models.member import Member, UserRole
from app.models.task import RepairTask, TaskCategory, TaskStatus, TaskType


@pytest.mark.asyncio
class TestStatisticsAPIRealCoverage:
    """真正的统计API功能测试 - 覆盖统计分析业务逻辑"""

    async def test_get_overview_statistics(
        self, async_client: AsyncClient, async_session: AsyncSession
    ):
        """测试获取概览统计 - 覆盖系统总体统计逻辑"""
        # 创建管理员用户
        admin = Member(
            username="admin_overview",
            name="概览统计管理员",
            student_id="2024000001",
            group_id=1,
            class_name="管理员",
            email="adminoverview@example.com",
            password_hash=get_password_hash("AdminPassword123!"),
            role=UserRole.ADMIN,
            is_active=True,
            is_verified=True,
        )

        # 创建普通成员
        members = []
        for i in range(5):
            member = Member(
                username=f"member_{i}",
                name=f"成员{i}",
                student_id=f"202400100{i}",
                group_id=1,
                class_name="计算机科学2024",
                email=f"member{i}@example.com",
                password_hash=get_password_hash("MemberPassword123!"),
                role=UserRole.MEMBER,
                is_active=True,
                is_verified=True,
            )
            async_session.add(member)
            members.append(member)

        async_session.add(admin)
        await async_session.commit()

        for member in members:
            await async_session.refresh(member)

        # 创建不同状态的任务
        now = datetime.now()
        tasks = []
        for i, member in enumerate(members):
            for j in range(3):  # 每个成员3个任务
                task = RepairTask(
                    title=f"统计测试任务{i}_{j}",
                    description=f"用于统计的任务{i}_{j}",
                    category=TaskCategory.REPAIR,
                    task_type=TaskType.ONLINE if (i + j) % 2 == 0 else TaskType.OFFLINE,
                    status=[
                        TaskStatus.PENDING,
                        TaskStatus.IN_PROGRESS,
                        TaskStatus.COMPLETED,
                    ][j],
                    assignee_id=member.id,
                    reporter_name=f"报告人{i}_{j}",
                    reporter_contact=f"1380013800{i}",
                    location=f"位置{i}_{j}",
                    problem_description=f"问题{i}_{j}",
                    created_at=now - timedelta(days=i + j),
                    completed_at=now - timedelta(hours=j) if j == 2 else None,
                    expected_completion_time=now + timedelta(hours=24),
                    actual_work_hours=2.0 if j == 2 else None,
                )
                async_session.add(task)
                tasks.append(task)

        await async_session.commit()

        # 创建考勤记录
        for i, member in enumerate(members):
            for days_ago in range(7):  # 每个成员7天的考勤记录
                attendance = AttendanceRecord(
                    member_id=member.id,
                    date=(now - timedelta(days=days_ago)).date(),
                    status=(
                        AttendanceStatus.PRESENT
                        if days_ago < 5
                        else AttendanceStatus.ABSENT
                    ),
                    check_in_time=(
                        now - timedelta(days=days_ago, hours=16)
                        if days_ago < 5
                        else None
                    ),
                    check_out_time=(
                        now - timedelta(days=days_ago, hours=8)
                        if days_ago < 5
                        else None
                    ),
                    work_hours=8.0 if days_ago < 5 else 0.0,
                    notes=f"考勤记录{i}_{days_ago}",
                )
                async_session.add(attendance)

        await async_session.commit()

        # 管理员登录
        login_response = await async_client.post(
            "/api/v1/auth/login",
            json={"username": "admin_overview", "password": "AdminPassword123!"},
        )
        token = login_response.json()["data"]["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # 获取概览统计
        response = await async_client.get(
            "/api/v1/statistics/overview", headers=headers
        )

        # 验证统计查询逻辑执行
        assert (
            response.status_code == 200
        ), f"Overview statistics failed: {response.text}"
        data = response.json()
        assert data["success"] is True

        overview = data["data"]

        # 验证基础统计数据
        assert "total_members" in overview
        assert "active_members" in overview
        assert "total_tasks" in overview
        assert "completed_tasks" in overview
        assert "pending_tasks" in overview
        assert "in_progress_tasks" in overview

        # 验证数据正确性
        assert overview["total_members"] == 6  # 5个成员 + 1个管理员
        assert overview["active_members"] == 6
        assert overview["total_tasks"] == 15  # 5个成员 × 3个任务
        assert overview["completed_tasks"] == 5  # 每个成员1个完成任务
        assert overview["pending_tasks"] == 5  # 每个成员1个待处理任务
        assert overview["in_progress_tasks"] == 5  # 每个成员1个进行中任务

        # 验证工时统计
        assert "total_work_hours" in overview
        assert "average_work_hours" in overview
        assert overview["total_work_hours"] == 10.0  # 5个完成任务 × 2小时

        # 验证考勤统计
        assert "attendance_rate" in overview
        assert "total_attendance_records" in overview

    async def test_get_member_performance_statistics(
        self, async_client: AsyncClient, async_session: AsyncSession
    ):
        """测试获取成员绩效统计 - 覆盖成员维度统计分析逻辑"""
        # 创建管理员和测试成员
        admin = Member(
            username="admin_performance",
            name="绩效统计管理员",
            student_id="2024000002",
            group_id=1,
            class_name="管理员",
            email="adminperformance@example.com",
            password_hash=get_password_hash("AdminPassword123!"),
            role=UserRole.ADMIN,
            is_active=True,
            is_verified=True,
        )

        test_member = Member(
            username="member_performance",
            name="绩效测试成员",
            student_id="2024001001",
            group_id=1,
            class_name="计算机科学2024",
            email="memberperf@example.com",
            password_hash=get_password_hash("MemberPassword123!"),
            role=UserRole.MEMBER,
            is_active=True,
            is_verified=True,
        )

        async_session.add_all([admin, test_member])
        await async_session.commit()
        await async_session.refresh(test_member)

        # 创建不同绩效水平的任务
        now = datetime.now()
        performance_tasks = [
            # 高质量完成任务
            RepairTask(
                title="高质量任务1",
                description="高质量完成的任务",
                category=TaskCategory.REPAIR,
                task_type=TaskType.ONLINE,
                status=TaskStatus.COMPLETED,
                assignee_id=test_member.id,
                reporter_name="高质量报告人",
                reporter_contact="13800138001",
                location="高质量位置",
                problem_description="高质量问题处理",
                created_at=now - timedelta(days=5),
                started_at=now - timedelta(days=5),
                completed_at=now - timedelta(days=4),
                expected_completion_time=now - timedelta(days=3),
                actual_work_hours=3.5,
                quality_rating=5,  # 优秀评级
                efficiency_score=95.0,
            ),
            # 延期完成任务
            RepairTask(
                title="延期任务1",
                description="延期完成的任务",
                category=TaskCategory.REPAIR,
                task_type=TaskType.OFFLINE,
                status=TaskStatus.COMPLETED,
                assignee_id=test_member.id,
                reporter_name="延期报告人",
                reporter_contact="13800138002",
                location="延期位置",
                problem_description="延期问题处理",
                created_at=now - timedelta(days=7),
                started_at=now - timedelta(days=6),
                completed_at=now - timedelta(days=2),
                expected_completion_time=now - timedelta(days=4),
                actual_work_hours=5.0,
                quality_rating=3,  # 一般评级
                efficiency_score=70.0,
            ),
            # 进行中任务
            RepairTask(
                title="进行中任务1",
                description="正在进行的任务",
                category=TaskCategory.REPAIR,
                task_type=TaskType.ONLINE,
                status=TaskStatus.IN_PROGRESS,
                assignee_id=test_member.id,
                reporter_name="进行中报告人",
                reporter_contact="13800138003",
                location="进行中位置",
                problem_description="进行中问题处理",
                created_at=now - timedelta(days=2),
                started_at=now - timedelta(days=1),
                expected_completion_time=now + timedelta(days=1),
                actual_work_hours=None,
            ),
        ]

        async_session.add_all(performance_tasks)
        await async_session.commit()

        # 管理员登录
        login_response = await async_client.post(
            "/api/v1/auth/login",
            json={"username": "admin_performance", "password": "AdminPassword123!"},
        )
        token = login_response.json()["data"]["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # 获取成员绩效统计
        response = await async_client.get(
            f"/api/v1/statistics/members/{test_member.id}/performance", headers=headers
        )

        # 验证绩效统计逻辑执行
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

        performance = data["data"]

        # 验证绩效指标
        assert "member_info" in performance
        assert "task_statistics" in performance
        assert "quality_metrics" in performance
        assert "efficiency_metrics" in performance
        assert "time_analysis" in performance

        # 验证任务统计
        task_stats = performance["task_statistics"]
        assert task_stats["total_tasks"] == 3
        assert task_stats["completed_tasks"] == 2
        assert task_stats["in_progress_tasks"] == 1
        assert task_stats["completion_rate"] >= 66.0  # 2/3 = 66.67%

        # 验证质量指标
        quality = performance["quality_metrics"]
        assert "average_rating" in quality
        assert "quality_distribution" in quality
        assert quality["average_rating"] == 4.0  # (5+3)/2 = 4.0

        # 验证效率指标
        efficiency = performance["efficiency_metrics"]
        assert "average_efficiency_score" in efficiency
        assert "on_time_completion_rate" in efficiency
        assert efficiency["average_efficiency_score"] == 82.5  # (95+70)/2 = 82.5

        # 验证时间分析
        time_analysis = performance["time_analysis"]
        assert "total_work_hours" in time_analysis
        assert "average_work_hours_per_task" in time_analysis
        assert time_analysis["total_work_hours"] == 8.5  # 3.5 + 5.0

    async def test_get_time_series_statistics(
        self, async_client: AsyncClient, async_session: AsyncSession
    ):
        """测试获取时间序列统计 - 覆盖趋势分析逻辑"""
        # 创建管理员
        admin = Member(
            username="admin_timeseries",
            name="时间序列管理员",
            student_id="2024000003",
            group_id=1,
            class_name="管理员",
            email="admintimeseries@example.com",
            password_hash=get_password_hash("AdminPassword123!"),
            role=UserRole.ADMIN,
            is_active=True,
            is_verified=True,
        )
        async_session.add(admin)
        await async_session.commit()

        # 创建时间序列数据 - 模拟30天的任务完成趋势
        now = datetime.now()
        for day in range(30):
            date = now - timedelta(days=day)
            # 模拟工作日更多任务，周末较少
            is_weekend = date.weekday() >= 5
            task_count = 2 if is_weekend else 5

            for i in range(task_count):
                task = RepairTask(
                    title=f"时序任务{day}_{i}",
                    description=f"第{day}天的任务{i}",
                    category=TaskCategory.REPAIR,
                    task_type=TaskType.ONLINE if i % 2 == 0 else TaskType.OFFLINE,
                    status=TaskStatus.COMPLETED,
                    assignee_id=admin.id,
                    reporter_name=f"时序报告人{day}_{i}",
                    reporter_contact=f"1380013800{day % 10}",
                    location=f"时序位置{day}_{i}",
                    problem_description=f"时序问题{day}_{i}",
                    created_at=date,
                    completed_at=date + timedelta(hours=2),
                    expected_completion_time=date + timedelta(hours=24),
                    actual_work_hours=1.5 + (day % 3) * 0.5,  # 变化的工时
                )
                async_session.add(task)

        await async_session.commit()

        # 管理员登录
        login_response = await async_client.post(
            "/api/v1/auth/login",
            json={"username": "admin_timeseries", "password": "AdminPassword123!"},
        )
        token = login_response.json()["data"]["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # 获取时间序列统计 - 按天聚合
        params = {
            "date_from": (now - timedelta(days=29)).date().isoformat(),
            "date_to": now.date().isoformat(),
            "granularity": "daily",
            "metrics": "task_count,work_hours,completion_rate",
        }
        response = await async_client.get(
            "/api/v1/statistics/time-series", params=params, headers=headers
        )

        # 验证时间序列分析逻辑执行
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

        time_series = data["data"]

        # 验证时间序列结构
        assert "series_data" in time_series
        assert "summary" in time_series
        assert "date_range" in time_series

        series_data = time_series["series_data"]
        assert len(series_data) == 30  # 30天的数据

        # 验证每日数据结构
        for daily_data in series_data:
            assert "date" in daily_data
            assert "task_count" in daily_data
            assert "work_hours" in daily_data
            assert "completion_rate" in daily_data

        # 验证汇总统计
        summary = time_series["summary"]
        assert "total_tasks" in summary
        assert "total_work_hours" in summary
        assert "average_daily_tasks" in summary
        assert "average_daily_work_hours" in summary

        # 验证工作日vs周末的统计差异
        weekday_tasks = [
            d["task_count"]
            for d in series_data
            if datetime.fromisoformat(d["date"]).weekday() < 5
        ]
        weekend_tasks = [
            d["task_count"]
            for d in series_data
            if datetime.fromisoformat(d["date"]).weekday() >= 5
        ]

        if weekday_tasks and weekend_tasks:
            avg_weekday = sum(weekday_tasks) / len(weekday_tasks)
            avg_weekend = sum(weekend_tasks) / len(weekend_tasks)
            assert avg_weekday > avg_weekend  # 工作日任务更多

        # 测试按周聚合
        weekly_params = {
            "date_from": (now - timedelta(days=27)).date().isoformat(),  # 4周
            "date_to": now.date().isoformat(),
            "granularity": "weekly",
            "metrics": "task_count,work_hours",
        }
        weekly_response = await async_client.get(
            "/api/v1/statistics/time-series", params=weekly_params, headers=headers
        )

        assert weekly_response.status_code == 200
        weekly_data = weekly_response.json()["data"]
        assert len(weekly_data["series_data"]) == 4  # 4周的数据

    async def test_get_workload_distribution_statistics(
        self, async_client: AsyncClient, async_session: AsyncSession
    ):
        """测试获取工作负载分布统计 - 覆盖工作负载分析逻辑"""
        # 创建管理员和多个成员
        admin = Member(
            username="admin_workload",
            name="工作负载管理员",
            student_id="2024000004",
            group_id=1,
            class_name="管理员",
            email="adminworkload@example.com",
            password_hash=get_password_hash("AdminPassword123!"),
            role=UserRole.ADMIN,
            is_active=True,
            is_verified=True,
        )

        members = []
        for i in range(4):
            member = Member(
                username=f"workload_member_{i}",
                name=f"负载成员{i}",
                student_id=f"202400200{i}",
                group_id=1,
                class_name="计算机科学2024",
                email=f"workload{i}@example.com",
                password_hash=get_password_hash("MemberPassword123!"),
                role=UserRole.MEMBER,
                is_active=True,
                is_verified=True,
            )
            async_session.add(member)
            members.append(member)

        async_session.add(admin)
        await async_session.commit()

        for member in members:
            await async_session.refresh(member)

        # 创建不同工作负载的任务分布
        now = datetime.now()
        workload_distribution = [10, 15, 8, 12]  # 每个成员的任务数量

        for member_idx, task_count in enumerate(workload_distribution):
            for task_idx in range(task_count):
                # 创建不同复杂度和工时的任务
                complexity = ["simple", "medium", "complex"][task_idx % 3]
                base_hours = {"simple": 1, "medium": 2, "complex": 4}[complexity]

                task = RepairTask(
                    title=f"负载任务{member_idx}_{task_idx}",
                    description=f"成员{member_idx}的{complexity}任务{task_idx}",
                    category=TaskCategory.REPAIR,
                    task_type=(
                        TaskType.ONLINE if task_idx % 2 == 0 else TaskType.OFFLINE
                    ),
                    status=(
                        TaskStatus.COMPLETED
                        if task_idx < task_count - 2
                        else TaskStatus.IN_PROGRESS
                    ),
                    assignee_id=members[member_idx].id,
                    reporter_name=f"负载报告人{member_idx}_{task_idx}",
                    reporter_contact=f"1380013810{member_idx}",
                    location=f"负载位置{member_idx}_{task_idx}",
                    problem_description=f"负载问题{member_idx}_{task_idx}",
                    created_at=now - timedelta(days=task_idx),
                    completed_at=(
                        now - timedelta(hours=task_idx)
                        if task_idx < task_count - 2
                        else None
                    ),
                    expected_completion_time=now + timedelta(hours=24),
                    actual_work_hours=base_hours + (task_idx % 2) * 0.5,
                    complexity_level=complexity,
                    priority=["low", "medium", "high"][task_idx % 3],
                )
                async_session.add(task)

        await async_session.commit()

        # 管理员登录
        login_response = await async_client.post(
            "/api/v1/auth/login",
            json={"username": "admin_workload", "password": "AdminPassword123!"},
        )
        token = login_response.json()["data"]["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # 获取工作负载分布统计
        response = await async_client.get(
            "/api/v1/statistics/workload-distribution", headers=headers
        )

        # 验证工作负载分析逻辑执行
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

        workload = data["data"]

        # 验证工作负载分布结构
        assert "member_workloads" in workload
        assert "distribution_analysis" in workload
        assert "balance_metrics" in workload
        assert "recommendations" in workload

        # 验证成员工作负载数据
        member_workloads = workload["member_workloads"]
        assert len(member_workloads) == 4  # 4个成员

        for member_data in member_workloads:
            assert "member_id" in member_data
            assert "member_name" in member_data
            assert "total_tasks" in member_data
            assert "completed_tasks" in member_data
            assert "in_progress_tasks" in member_data
            assert "total_work_hours" in member_data
            assert "average_task_complexity" in member_data

        # 验证分布分析
        distribution = workload["distribution_analysis"]
        assert "max_tasks_per_member" in distribution
        assert "min_tasks_per_member" in distribution
        assert "average_tasks_per_member" in distribution
        assert "workload_variance" in distribution

        # 验证平衡指标
        balance = workload["balance_metrics"]
        assert "workload_balance_score" in balance  # 0-100分
        assert "is_balanced" in balance
        assert "imbalance_threshold" in balance

        # 验证数据正确性
        total_tasks = sum(m["total_tasks"] for m in member_workloads)
        assert total_tasks == sum(workload_distribution)  # 45个任务

        expected_avg = sum(workload_distribution) / len(workload_distribution)
        assert abs(distribution["average_tasks_per_member"] - expected_avg) < 0.1

    async def test_export_statistical_report(
        self, async_client: AsyncClient, async_session: AsyncSession
    ):
        """测试导出统计报告 - 覆盖报告生成和导出逻辑"""
        # 创建管理员
        admin = Member(
            username="admin_export_stats",
            name="统计导出管理员",
            student_id="2024000005",
            group_id=1,
            class_name="管理员",
            email="adminexportstats@example.com",
            password_hash=get_password_hash("AdminPassword123!"),
            role=UserRole.ADMIN,
            is_active=True,
            is_verified=True,
        )
        async_session.add(admin)
        await async_session.commit()
        await async_session.refresh(admin)

        # 创建综合统计数据
        now = datetime.now()
        for i in range(20):
            # 创建任务
            task = RepairTask(
                title=f"统计导出任务{i}",
                description=f"用于统计导出的任务{i}",
                category=TaskCategory.REPAIR,
                task_type=TaskType.ONLINE if i % 2 == 0 else TaskType.OFFLINE,
                status=TaskStatus.COMPLETED if i < 15 else TaskStatus.IN_PROGRESS,
                assignee_id=admin.id,
                reporter_name=f"导出报告人{i}",
                reporter_contact=f"1380013820{i % 10}",
                location=f"导出位置{i}",
                problem_description=f"导出问题{i}",
                created_at=now - timedelta(days=i),
                completed_at=now - timedelta(hours=i) if i < 15 else None,
                expected_completion_time=now + timedelta(hours=24),
                actual_work_hours=1.5 + (i % 4) * 0.5,
                quality_rating=3 + (i % 3),  # 3-5星评级
                efficiency_score=70 + (i % 30),  # 70-99分效率
            )
            async_session.add(task)

            # 创建考勤记录
            if i < 14:  # 14天的考勤记录
                attendance = AttendanceRecord(
                    member_id=admin.id,
                    date=(now - timedelta(days=i)).date(),
                    status=(
                        AttendanceStatus.PRESENT
                        if i % 7 != 6
                        else AttendanceStatus.ABSENT
                    ),
                    check_in_time=(
                        now - timedelta(days=i, hours=16) if i % 7 != 6 else None
                    ),
                    check_out_time=(
                        now - timedelta(days=i, hours=8) if i % 7 != 6 else None
                    ),
                    work_hours=8.0 if i % 7 != 6 else 0.0,
                    notes=f"导出考勤{i}",
                )
                async_session.add(attendance)

        await async_session.commit()

        # 管理员登录
        login_response = await async_client.post(
            "/api/v1/auth/login",
            json={"username": "admin_export_stats", "password": "AdminPassword123!"},
        )
        token = login_response.json()["data"]["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # 测试导出Excel格式报告
        export_params = {
            "report_type": "comprehensive",
            "format": "excel",
            "date_from": (now - timedelta(days=30)).date().isoformat(),
            "date_to": now.date().isoformat(),
            "include_charts": "true",
            "include_details": "true",
        }

        response = await async_client.get(
            "/api/v1/statistics/export", params=export_params, headers=headers
        )

        # 验证报告导出逻辑执行
        assert response.status_code == 200

        # 验证响应是Excel文件
        content_type = response.headers.get("content-type", "")
        assert (
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            in content_type
            or "application/octet-stream" in content_type
        )

        # 验证文件名设置
        content_disposition = response.headers.get("content-disposition", "")
        assert "attachment" in content_disposition
        assert "statistics" in content_disposition or ".xlsx" in content_disposition

        # 验证文件不为空
        assert len(response.content) > 1000  # Excel文件应该有一定大小

        # 测试导出PDF格式报告
        pdf_params = {
            "report_type": "summary",
            "format": "pdf",
            "date_from": (now - timedelta(days=7)).date().isoformat(),
            "date_to": now.date().isoformat(),
            "include_charts": "true",
        }

        pdf_response = await async_client.get(
            "/api/v1/statistics/export", params=pdf_params, headers=headers
        )

        # 验证PDF导出
        assert pdf_response.status_code == 200

        pdf_content_type = pdf_response.headers.get("content-type", "")
        assert (
            "application/pdf" in pdf_content_type
            or "application/octet-stream" in pdf_content_type
        )

        pdf_disposition = pdf_response.headers.get("content-disposition", "")
        assert "attachment" in pdf_disposition
        assert ".pdf" in pdf_disposition

        # 测试导出JSON格式数据
        json_params = {
            "report_type": "raw_data",
            "format": "json",
            "date_from": (now - timedelta(days=7)).date().isoformat(),
            "date_to": now.date().isoformat(),
        }

        json_response = await async_client.get(
            "/api/v1/statistics/export", params=json_params, headers=headers
        )

        # 验证JSON数据导出
        assert json_response.status_code == 200
        json_data = json_response.json()
        assert json_data["success"] is True

        export_data = json_data["data"]
        assert "export_info" in export_data
        assert "statistics_data" in export_data
        assert "metadata" in export_data

        # 验证统计数据结构
        stats_data = export_data["statistics_data"]
        assert "tasks" in stats_data
        assert "attendance" in stats_data
        assert "summary" in stats_data

        # 验证元数据
        metadata = export_data["metadata"]
        assert "export_date" in metadata
        assert "date_range" in metadata
        assert "record_count" in metadata

    async def test_get_efficiency_trend_analysis(
        self, async_client: AsyncClient, async_session: AsyncSession
    ):
        """测试获取效率趋势分析 - 覆盖效率分析算法逻辑"""
        # 创建管理员
        admin = Member(
            username="admin_efficiency",
            name="效率分析管理员",
            student_id="2024000006",
            group_id=1,
            class_name="管理员",
            email="adminefficiency@example.com",
            password_hash=get_password_hash("AdminPassword123!"),
            role=UserRole.ADMIN,
            is_active=True,
            is_verified=True,
        )
        async_session.add(admin)
        await async_session.commit()
        await async_session.refresh(admin)

        # 创建效率趋势数据 - 模拟效率逐步提升的场景
        now = datetime.now()
        base_efficiency = 60  # 起始效率

        for week in range(8):  # 8周的数据
            week_start = now - timedelta(weeks=week)
            # 模拟效率提升趋势
            week_efficiency = base_efficiency + week * 5  # 每周提升5%

            for day in range(5):  # 每周5个工作日
                for task_num in range(3):  # 每天3个任务
                    task_date = week_start - timedelta(days=day)

                    # 添加一些随机波动
                    daily_efficiency = week_efficiency + ((task_num + day) % 7 - 3) * 2
                    daily_efficiency = max(
                        50, min(100, daily_efficiency)
                    )  # 限制在50-100范围

                    task = RepairTask(
                        title=f"效率分析任务W{week}D{day}T{task_num}",
                        description=f"第{week}周第{day}天任务{task_num}",
                        category=TaskCategory.REPAIR,
                        task_type=(
                            TaskType.ONLINE if task_num % 2 == 0 else TaskType.OFFLINE
                        ),
                        status=TaskStatus.COMPLETED,
                        assignee_id=admin.id,
                        reporter_name=f"效率报告人{week}_{day}",
                        reporter_contact=f"1380013830{week}",
                        location=f"效率位置{week}_{day}",
                        problem_description=f"效率问题{week}_{day}_{task_num}",
                        created_at=task_date,
                        started_at=task_date + timedelta(minutes=30),
                        completed_at=task_date + timedelta(hours=2),
                        expected_completion_time=task_date + timedelta(hours=3),
                        actual_work_hours=1.5 + (task_num * 0.25),
                        efficiency_score=daily_efficiency,
                        quality_rating=4 if daily_efficiency > 80 else 3,
                        on_time_completion=daily_efficiency > 75,
                    )
                    async_session.add(task)

        await async_session.commit()

        # 管理员登录
        login_response = await async_client.post(
            "/api/v1/auth/login",
            json={"username": "admin_efficiency", "password": "AdminPassword123!"},
        )
        token = login_response.json()["data"]["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # 获取效率趋势分析
        params = {
            "analysis_type": "trend",
            "date_from": (now - timedelta(weeks=7)).date().isoformat(),
            "date_to": now.date().isoformat(),
            "grouping": "weekly",
            "include_projections": "true",
        }

        response = await async_client.get(
            "/api/v1/statistics/efficiency-analysis", params=params, headers=headers
        )

        # 验证效率分析逻辑执行
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

        efficiency_analysis = data["data"]

        # 验证分析结果结构
        assert "trend_data" in efficiency_analysis
        assert "performance_metrics" in efficiency_analysis
        assert "improvement_analysis" in efficiency_analysis
        assert "projections" in efficiency_analysis

        # 验证趋势数据
        trend_data = efficiency_analysis["trend_data"]
        assert len(trend_data) == 8  # 8周的数据

        for week_data in trend_data:
            assert "period" in week_data
            assert "average_efficiency" in week_data
            assert "task_count" in week_data
            assert "completion_rate" in week_data
            assert "quality_score" in week_data

        # 验证效率提升趋势
        efficiencies = [w["average_efficiency"] for w in trend_data]
        # 由于数据是倒序的（最新的在前），反转后检查趋势
        efficiencies.reverse()

        # 检查总体是上升趋势（允许一些波动）
        first_quarter = sum(efficiencies[:2]) / 2
        last_quarter = sum(efficiencies[-2:]) / 2
        assert last_quarter > first_quarter, "效率应该呈现上升趋势"

        # 验证性能指标
        metrics = efficiency_analysis["performance_metrics"]
        assert "current_efficiency" in metrics
        assert "efficiency_change" in metrics
        assert "best_week" in metrics
        assert "improvement_rate" in metrics

        # 验证改进分析
        improvement = efficiency_analysis["improvement_analysis"]
        assert "trend_direction" in improvement
        assert "improvement_factors" in improvement
        assert "areas_for_improvement" in improvement

        # 验证预测数据
        projections = efficiency_analysis["projections"]
        assert "next_period_projection" in projections
        assert "confidence_level" in projections
        assert "recommendation" in projections
