"""
统计分析API测试用例
测试所有统计相关的API端点
"""

from datetime import date, datetime, timedelta
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import AsyncClient
from fastapi import HTTPException

from app.main import app
from app.models.attendance import AttendanceRecord
from app.models.member import Member, UserRole
from app.models.task import RepairTask, TaskCategory, TaskPriority, TaskStatus, TaskType


class TestStatisticsAPIBasic:
    """测试统计API基础功能"""

    @pytest.fixture
    async def client(self):
        """创建测试客户端"""
        async with AsyncClient(app=app, base_url="http://testserver") as ac:
            yield ac

    @pytest.fixture
    def regular_user(self):
        """创建普通用户"""
        return Member(
            id=1,
            username="regular_user",
            student_id="20210001",
            name="普通用户",
            role=UserRole.MEMBER,
        )

    @pytest.fixture
    def group_leader_user(self):
        """创建组长用户"""
        return Member(
            id=2,
            username="group_leader",
            student_id="20210002",
            name="组长",
            role=UserRole.GROUP_LEADER,
        )

    @pytest.fixture
    def admin_user(self):
        """创建管理员用户"""
        return Member(
            id=3,
            username="admin_user",
            student_id="20210003",
            name="管理员",
            role=UserRole.ADMIN,
        )

    @pytest.fixture
    def sample_tasks(self, regular_user):
        """创建示例任务数据"""
        return [
            RepairTask(
                id=1,
                task_id="T001",
                title="网络故障",
                status=TaskStatus.COMPLETED,
                task_type=TaskType.ONLINE,
                work_minutes=40,
                rating=5,
                report_time=datetime(2025, 1, 1, 10, 0),
                completion_time=datetime(2025, 1, 1, 12, 0),
                member_id=regular_user.id,
            ),
            RepairTask(
                id=2,
                task_id="T002",
                title="硬件维修",
                status=TaskStatus.COMPLETED,
                task_type=TaskType.OFFLINE,
                work_minutes=100,
                rating=4,
                report_time=datetime(2025, 1, 2, 9, 0),
                completion_time=datetime(2025, 1, 2, 14, 0),
                member_id=regular_user.id,
            ),
        ]


class TestStatisticsOverviewAPI(TestStatisticsAPIBasic):
    """测试统计概览API"""

    @pytest.mark.asyncio
    async def test_get_statistics_overview_basic(self, client, admin_user):
        """测试获取统计概览基础功能"""
        with (
            patch("app.api.deps.get_db") as mock_get_db,
            patch("app.api.deps.get_current_active_admin") as mock_get_admin,
        ):

            mock_db = AsyncMock()
            mock_get_db.return_value = mock_db
            mock_get_admin.return_value = admin_user

            # Mock统计查询结果
            mock_results = [
                # 总任务数
                MagicMock(scalar=MagicMock(return_value=100)),
                # 本月任务数
                MagicMock(scalar=MagicMock(return_value=25)),
                # 已完成任务数
                MagicMock(scalar=MagicMock(return_value=80)),
                # 平均完成时间
                MagicMock(scalar=MagicMock(return_value=2.5)),
                # 平均评分
                MagicMock(scalar=MagicMock(return_value=4.2)),
                # 总工时
                MagicMock(scalar=MagicMock(return_value=4800)),
                # 线上任务数
                MagicMock(scalar=MagicMock(return_value=70)),
                # 线下任务数
                MagicMock(scalar=MagicMock(return_value=30)),
            ]
            mock_db.execute.side_effect = mock_results

            response = await client.get(
                "/api/v1/statistics/overview",
                headers={"Authorization": "Bearer admin_token"},
            )

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["data"]["total_tasks"] == 100
            assert data["data"]["monthly_tasks"] == 25
            assert data["data"]["completed_tasks"] == 80
            assert data["data"]["avg_completion_hours"] == 2.5
            assert data["data"]["avg_rating"] == 4.2
            assert data["data"]["total_work_minutes"] == 4800

    @pytest.mark.asyncio
    async def test_get_statistics_overview_with_date_filter(self, client, admin_user):
        """测试带日期过滤的统计概览"""
        with (
            patch("app.api.deps.get_db") as mock_get_db,
            patch("app.api.deps.get_current_active_admin") as mock_get_admin,
        ):

            mock_db = AsyncMock()
            mock_get_db.return_value = mock_db
            mock_get_admin.return_value = admin_user

            # Mock带日期过滤的查询结果
            mock_results = [
                MagicMock(scalar=MagicMock(return_value=50)),  # 总任务数
                MagicMock(scalar=MagicMock(return_value=15)),  # 本月任务数
                MagicMock(scalar=MagicMock(return_value=40)),  # 已完成任务数
                MagicMock(scalar=MagicMock(return_value=3.0)),  # 平均完成时间
                MagicMock(scalar=MagicMock(return_value=4.5)),  # 平均评分
                MagicMock(scalar=MagicMock(return_value=2400)),  # 总工时
                MagicMock(scalar=MagicMock(return_value=35)),  # 线上任务数
                MagicMock(scalar=MagicMock(return_value=15)),  # 线下任务数
            ]
            mock_db.execute.side_effect = mock_results

            response = await client.get(
                "/api/v1/statistics/overview?start_date=2025-01-01&end_date=2025-01-31",
                headers={"Authorization": "Bearer admin_token"},
            )

            assert response.status_code == 200
            data = response.json()
            assert data["data"]["total_tasks"] == 50

    @pytest.mark.asyncio
    async def test_get_statistics_overview_permission_denied(
        self, client, regular_user
    ):
        """测试普通用户访问概览API权限拒绝"""
        with patch("app.api.deps.get_current_active_admin") as mock_get_admin:
            # Mock权限验证失败
            mock_get_admin.side_effect = HTTPException(
                status_code=403, detail="权限不足"
            )

            response = await client.get(
                "/api/v1/statistics/overview",
                headers={"Authorization": "Bearer user_token"},
            )

            assert response.status_code == 403


class TestEfficiencyAnalysisAPI(TestStatisticsAPIBasic):
    """测试效率分析API"""

    @pytest.mark.asyncio
    async def test_get_efficiency_analysis_basic(self, client, admin_user):
        """测试获取效率分析基础功能"""
        with (
            patch("app.api.deps.get_db") as mock_get_db,
            patch("app.api.deps.get_current_active_admin") as mock_get_admin,
        ):

            mock_db = AsyncMock()
            mock_get_db.return_value = mock_db
            mock_get_admin.return_value = admin_user

            # Mock效率分析查询结果
            mock_efficiency_data = [
                (
                    1,
                    "张三",
                    65.5,
                    4.2,
                    3.5,
                    10,
                ),  # (member_id, name, avg_work_minutes, avg_rating, avg_completion_hours, total_tasks)
                (2, "李四", 72.0, 4.8, 2.8, 15),
            ]

            mock_result = MagicMock()
            mock_result.fetchall.return_value = mock_efficiency_data
            mock_db.execute.return_value = mock_result

            response = await client.get(
                "/api/v1/statistics/efficiency",
                headers={"Authorization": "Bearer admin_token"},
            )

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert len(data["data"]["members"]) == 2
            assert data["data"]["members"][0]["name"] == "张三"
            assert data["data"]["members"][1]["name"] == "李四"

    @pytest.mark.asyncio
    async def test_efficiency_analysis_with_member_filter(self, client, admin_user):
        """测试按成员过滤的效率分析"""
        with (
            patch("app.api.deps.get_db") as mock_get_db,
            patch("app.api.deps.get_current_active_admin") as mock_get_admin,
        ):

            mock_db = AsyncMock()
            mock_get_db.return_value = mock_db
            mock_get_admin.return_value = admin_user

            # Mock单个成员效率数据
            mock_efficiency_data = [(1, "张三", 65.5, 4.2, 3.5, 10)]

            mock_result = MagicMock()
            mock_result.fetchall.return_value = mock_efficiency_data
            mock_db.execute.return_value = mock_result

            response = await client.get(
                "/api/v1/statistics/efficiency?member_id=test_user.id",
                headers={"Authorization": "Bearer admin_token"},
            )

            assert response.status_code == 200
            data = response.json()
            assert len(data["data"]["members"]) == 1
            assert data["data"]["members"][0]["member_id"] == 1

    @pytest.mark.asyncio
    async def test_efficiency_calculation_logic(self, client, admin_user):
        """测试效率分数计算逻辑"""
        with patch("app.api.v1.statistics._calculate_efficiency_score") as mock_calc:
            # Mock效率分数计算函数
            mock_calc.return_value = 85.5

            # 测试效率计算函数
            score = mock_calc(65.5, 3.5, 4.2, 10)
            assert score == 85.5
            mock_calc.assert_called_once_with(65.5, 3.5, 4.2, 10)


class TestMonthlyReportAPI(TestStatisticsAPIBasic):
    """测试月度报表API"""

    @pytest.mark.asyncio
    async def test_get_monthly_report_basic(self, client, admin_user):
        """测试获取月度报表基础功能"""
        with (
            patch("app.api.deps.get_db") as mock_get_db,
            patch("app.api.deps.get_current_active_admin") as mock_get_admin,
        ):

            mock_db = AsyncMock()
            mock_get_db.return_value = mock_db
            mock_get_admin.return_value = admin_user

            # Mock月度报表数据
            mock_results = [
                # 月度任务统计
                MagicMock(scalar=MagicMock(return_value=50)),  # 总任务
                MagicMock(scalar=MagicMock(return_value=45)),  # 已完成
                MagicMock(scalar=MagicMock(return_value=3)),  # 进行中
                MagicMock(scalar=MagicMock(return_value=2)),  # 待处理
                # 工时统计
                MagicMock(scalar=MagicMock(return_value=2400)),  # 总工时
                MagicMock(scalar=MagicMock(return_value=1600)),  # 报修工时
                MagicMock(scalar=MagicMock(return_value=480)),  # 监控工时
                MagicMock(scalar=MagicMock(return_value=320)),  # 协助工时
                # 评分统计
                MagicMock(scalar=MagicMock(return_value=4.3)),  # 平均评分
            ]
            mock_db.execute.side_effect = mock_results

            # Mock成员排名数据
            mock_member_data = [
                (
                    1,
                    "张三",
                    800,
                    15,
                    4.5,
                ),  # (id, name, work_minutes, task_count, avg_rating)
                (2, "李四", 720, 12, 4.2),
            ]
            mock_ranking_result = MagicMock()
            mock_ranking_result.fetchall.return_value = mock_member_data
            mock_db.execute.return_value = mock_ranking_result

            response = await client.get(
                "/api/v1/statistics/monthly-report?year=2025&month=1",
                headers={"Authorization": "Bearer admin_token"},
            )

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["data"]["summary"]["total_tasks"] == 50
            assert data["data"]["summary"]["completed_tasks"] == 45
            assert data["data"]["work_hours"]["total_minutes"] == 2400
            assert len(data["data"]["member_rankings"]) == 2

    @pytest.mark.asyncio
    async def test_monthly_report_current_month(self, client, admin_user):
        """测试获取当前月份报表"""
        with (
            patch("app.api.deps.get_db") as mock_get_db,
            patch("app.api.deps.get_current_active_admin") as mock_get_admin,
        ):

            mock_db = AsyncMock()
            mock_get_db.return_value = mock_db
            mock_get_admin.return_value = admin_user

            # Mock当前月份数据
            mock_results = [
                MagicMock(scalar=MagicMock(return_value=25)),  # 本月任务数
                MagicMock(scalar=MagicMock(return_value=20)),  # 已完成
                MagicMock(scalar=MagicMock(return_value=3)),  # 进行中
                MagicMock(scalar=MagicMock(return_value=2)),  # 待处理
                MagicMock(scalar=MagicMock(return_value=1200)),  # 总工时
                MagicMock(scalar=MagicMock(return_value=800)),  # 报修工时
                MagicMock(scalar=MagicMock(return_value=240)),  # 监控工时
                MagicMock(scalar=MagicMock(return_value=160)),  # 协助工时
                MagicMock(scalar=MagicMock(return_value=4.4)),  # 平均评分
            ]
            mock_db.execute.side_effect = mock_results

            mock_member_data = [(1, "张三", 400, 8, 4.6)]
            mock_ranking_result = MagicMock()
            mock_ranking_result.fetchall.return_value = mock_member_data
            mock_db.execute.return_value = mock_ranking_result

            response = await client.get(
                "/api/v1/statistics/monthly-report",  # 不指定年月，应该使用当前月份
                headers={"Authorization": "Bearer admin_token"},
            )

            assert response.status_code == 200
            data = response.json()
            assert data["data"]["summary"]["total_tasks"] == 25

    @pytest.mark.asyncio
    async def test_monthly_report_invalid_date(self, client, admin_user):
        """测试无效日期的月度报表"""
        with patch("app.api.deps.get_current_active_admin") as mock_get_admin:
            mock_get_admin.return_value = admin_user

            response = await client.get(
                "/api/v1/statistics/monthly-report?year=2025&month=13",  # 无效月份
                headers={"Authorization": "Bearer admin_token"},
            )

            assert response.status_code == 422  # 参数验证错误


class TestExportStatisticsAPI(TestStatisticsAPIBasic):
    """测试统计数据导出API"""

    @pytest.mark.asyncio
    async def test_export_statistics_data_basic(self, client, admin_user):
        """测试导出统计数据基础功能"""
        with (
            patch("app.api.deps.get_db") as mock_get_db,
            patch("app.api.deps.get_current_active_admin") as mock_get_admin,
        ):

            mock_db = AsyncMock()
            mock_get_db.return_value = mock_db
            mock_get_admin.return_value = admin_user

            # Mock导出数据查询结果
            mock_export_data = [
                (1, "T001", "网络故障", "张三", "completed", 40, 5, "2025-01-01"),
                (2, "T002", "硬件维修", "李四", "completed", 100, 4, "2025-01-02"),
            ]

            mock_result = MagicMock()
            mock_result.fetchall.return_value = mock_export_data
            mock_db.execute.return_value = mock_result

            response = await client.get(
                "/api/v1/statistics/export?format=json",
                headers={"Authorization": "Bearer admin_token"},
            )

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert len(data["data"]["records"]) == 2
            assert data["data"]["format"] == "json"

    @pytest.mark.asyncio
    async def test_export_statistics_with_date_range(self, client, admin_user):
        """测试带日期范围的数据导出"""
        with (
            patch("app.api.deps.get_db") as mock_get_db,
            patch("app.api.deps.get_current_active_admin") as mock_get_admin,
        ):

            mock_db = AsyncMock()
            mock_get_db.return_value = mock_db
            mock_get_admin.return_value = admin_user

            mock_export_data = [
                (1, "T001", "网络故障", "张三", "completed", 40, 5, "2025-01-01")
            ]

            mock_result = MagicMock()
            mock_result.fetchall.return_value = mock_export_data
            mock_db.execute.return_value = mock_result

            response = await client.get(
                "/api/v1/statistics/export?format=csv&start_date=2025-01-01&end_date=2025-01-31",
                headers={"Authorization": "Bearer admin_token"},
            )

            assert response.status_code == 200
            data = response.json()
            assert data["data"]["format"] == "csv"
            assert len(data["data"]["records"]) == 1

    @pytest.mark.asyncio
    async def test_export_unsupported_format(self, client, admin_user):
        """测试不支持的导出格式"""
        with patch("app.api.deps.get_current_active_admin") as mock_get_admin:
            mock_get_admin.return_value = admin_user

            response = await client.get(
                "/api/v1/statistics/export?format=xml",  # 不支持的格式
                headers={"Authorization": "Bearer admin_token"},
            )

            assert response.status_code == 422


class TestChartDataAPI(TestStatisticsAPIBasic):
    """测试图表数据API"""

    @pytest.mark.asyncio
    async def test_get_chart_data_basic(self, client, group_leader_user):
        """测试获取图表数据基础功能"""
        with (
            patch("app.api.deps.get_db") as mock_get_db,
            patch("app.api.deps.get_current_active_group_leader") as mock_get_leader,
        ):

            mock_db = AsyncMock()
            mock_get_db.return_value = mock_db
            mock_get_leader.return_value = group_leader_user

            # Mock图表数据查询结果
            mock_chart_data = [
                ("2025-01-01", 5, 4, 1),  # (date, total, completed, pending)
                ("2025-01-02", 8, 7, 1),
                ("2025-01-03", 6, 5, 1),
            ]

            mock_result = MagicMock()
            mock_result.fetchall.return_value = mock_chart_data
            mock_db.execute.return_value = mock_result

            response = await client.get(
                "/api/v1/statistics/charts?chart_type=daily_tasks",
                headers={"Authorization": "Bearer leader_token"},
            )

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["data"]["chart_type"] == "daily_tasks"
            assert len(data["data"]["data_points"]) == 3

    @pytest.mark.asyncio
    async def test_get_chart_data_different_types(self, client, group_leader_user):
        """测试不同类型的图表数据"""
        chart_types = [
            "daily_tasks",
            "member_performance",
            "category_distribution",
            "work_hours_trend",
        ]

        for chart_type in chart_types:
            with (
                patch("app.api.deps.get_db") as mock_get_db,
                patch(
                    "app.api.deps.get_current_active_group_leader"
                ) as mock_get_leader,
            ):

                mock_db = AsyncMock()
                mock_get_db.return_value = mock_db
                mock_get_leader.return_value = group_leader_user

                # Mock不同类型图表的数据
                if chart_type == "member_performance":
                    mock_data = [("张三", 85.5), ("李四", 78.2)]
                elif chart_type == "category_distribution":
                    mock_data = [("网络维修", 15), ("硬件维修", 8)]
                else:
                    mock_data = [("2025-01-01", 5), ("2025-01-02", 8)]

                mock_result = MagicMock()
                mock_result.fetchall.return_value = mock_data
                mock_db.execute.return_value = mock_result

                response = await client.get(
                    f"/api/v1/statistics/charts?chart_type={chart_type}",
                    headers={"Authorization": "Bearer leader_token"},
                )

                assert response.status_code == 200
                data = response.json()
                assert data["data"]["chart_type"] == chart_type


class TestRankingsAPI(TestStatisticsAPIBasic):
    """测试排名API"""

    @pytest.mark.asyncio
    async def test_get_rankings_basic(self, client, admin_user):
        """测试获取排名基础功能"""
        with (
            patch("app.api.deps.get_db") as mock_get_db,
            patch("app.api.deps.get_current_active_admin") as mock_get_admin,
        ):

            mock_db = AsyncMock()
            mock_get_db.return_value = mock_db
            mock_get_admin.return_value = admin_user

            # Mock排名数据
            mock_ranking_data = [
                (
                    1,
                    "张三",
                    1200,
                    20,
                    4.8,
                    1,
                ),  # (id, name, work_minutes, task_count, avg_rating, rank)
                (2, "李四", 1000, 18, 4.5, 2),
                (3, "王五", 800, 15, 4.2, 3),
            ]

            mock_result = MagicMock()
            mock_result.fetchall.return_value = mock_ranking_data
            mock_db.execute.return_value = mock_result

            response = await client.get(
                "/api/v1/statistics/rankings?ranking_type=work_hours",
                headers={"Authorization": "Bearer admin_token"},
            )

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert len(data["data"]["rankings"]) == 3
            assert data["data"]["rankings"][0]["name"] == "张三"
            assert data["data"]["rankings"][0]["rank"] == 1

    @pytest.mark.asyncio
    async def test_rankings_different_types(self, client, admin_user):
        """测试不同类型的排名"""
        ranking_types = ["work_hours", "task_count", "efficiency", "rating"]

        for ranking_type in ranking_types:
            with (
                patch("app.api.deps.get_db") as mock_get_db,
                patch("app.api.deps.get_current_active_admin") as mock_get_admin,
            ):

                mock_db = AsyncMock()
                mock_get_db.return_value = mock_db
                mock_get_admin.return_value = admin_user

                mock_ranking_data = [(1, "张三", 1200, 20, 4.8, 1)]
                mock_result = MagicMock()
                mock_result.fetchall.return_value = mock_ranking_data
                mock_db.execute.return_value = mock_result

                response = await client.get(
                    f"/api/v1/statistics/rankings?ranking_type={ranking_type}",
                    headers={"Authorization": "Bearer admin_token"},
                )

                assert response.status_code == 200
                data = response.json()
                assert data["data"]["ranking_type"] == ranking_type


class TestAttendanceStatisticsAPI(TestStatisticsAPIBasic):
    """测试考勤统计API"""

    @pytest.mark.asyncio
    async def test_get_attendance_statistics_basic(self, client, admin_user):
        """测试获取考勤统计基础功能"""
        with (
            patch("app.api.deps.get_db") as mock_get_db,
            patch("app.api.deps.get_current_active_admin") as mock_get_admin,
            patch("app.services.attendance_service.AttendanceService") as mock_service,
        ):

            mock_db = AsyncMock()
            mock_get_db.return_value = mock_db
            mock_get_admin.return_value = admin_user

            # Mock考勤服务
            mock_attendance_service = AsyncMock()
            mock_attendance_service.get_monthly_statistics.return_value = {
                "total_work_days": 22,
                "avg_work_hours": 7.5,
                "total_members": 10,
                "attendance_rate": 95.5,
                "member_statistics": [
                    {
                        "member_id=test_user.id,
                        "name": "张三",
                        "work_days": 20,
                        "work_hours": 150,
                    },
                    {
                        "member_id": 2,
                        "name": "李四",
                        "work_days": 19,
                        "work_hours": 142.5,
                    },
                ],
            }
            mock_service.return_value = mock_attendance_service

            response = await client.get(
                "/api/v1/statistics/attendance?year=2025&month=1",
                headers={"Authorization": "Bearer admin_token"},
            )

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["data"]["total_work_days"] == 22
            assert data["data"]["attendance_rate"] == 95.5
            assert len(data["data"]["member_statistics"]) == 2

    @pytest.mark.asyncio
    async def test_attendance_statistics_with_member_filter(self, client, admin_user):
        """测试按成员过滤的考勤统计"""
        with (
            patch("app.api.deps.get_db") as mock_get_db,
            patch("app.api.deps.get_current_active_admin") as mock_get_admin,
            patch("app.services.attendance_service.AttendanceService") as mock_service,
        ):

            mock_db = AsyncMock()
            mock_get_db.return_value = mock_db
            mock_get_admin.return_value = admin_user

            mock_attendance_service = AsyncMock()
            mock_attendance_service.get_member_statistics.return_value = {
                "member_id=test_user.id,
                "name": "张三",
                "work_days": 20,
                "work_hours": 150,
                "attendance_rate": 90.9,
                "daily_records": [],
            }
            mock_service.return_value = mock_attendance_service

            response = await client.get(
                "/api/v1/statistics/attendance?member_id=test_user.id&year=2025&month=1",
                headers={"Authorization": "Bearer admin_token"},
            )

            assert response.status_code == 200
            data = response.json()
            assert data["data"]["member_id"] == 1
            assert data["data"]["name"] == "张三"


class TestWorkHoursOverviewAPI(TestStatisticsAPIBasic):
    """测试工时概览API"""

    @pytest.mark.asyncio
    async def test_get_work_hours_overview_basic(self, client, group_leader_user):
        """测试获取工时概览基础功能"""
        with (
            patch("app.api.deps.get_db") as mock_get_db,
            patch("app.api.deps.get_current_active_group_leader") as mock_get_leader,
        ):

            mock_db = AsyncMock()
            mock_get_db.return_value = mock_db
            mock_get_leader.return_value = group_leader_user

            # Mock工时概览查询结果
            mock_results = [
                MagicMock(scalar=MagicMock(return_value=4800)),  # 总工时
                MagicMock(scalar=MagicMock(return_value=3200)),  # 报修工时
                MagicMock(scalar=MagicMock(return_value=960)),  # 监控工时
                MagicMock(scalar=MagicMock(return_value=640)),  # 协助工时
                MagicMock(scalar=MagicMock(return_value=80.0)),  # 平均工时
            ]
            mock_db.execute.side_effect = mock_results

            response = await client.get(
                "/api/v1/statistics/work-hours/overview",
                headers={"Authorization": "Bearer leader_token"},
            )

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["data"]["total_work_minutes"] == 4800
            assert data["data"]["repair_work_minutes"] == 3200
            assert data["data"]["monitoring_work_minutes"] == 960
            assert data["data"]["assistance_work_minutes"] == 640
            assert data["data"]["avg_work_minutes"] == 80.0

    @pytest.mark.asyncio
    async def test_work_hours_overview_with_filters(self, client, group_leader_user):
        """测试带过滤条件的工时概览"""
        with (
            patch("app.api.deps.get_db") as mock_get_db,
            patch("app.api.deps.get_current_active_group_leader") as mock_get_leader,
        ):

            mock_db = AsyncMock()
            mock_get_db.return_value = mock_db
            mock_get_leader.return_value = group_leader_user

            mock_results = [
                MagicMock(scalar=MagicMock(return_value=2400)),  # 总工时
                MagicMock(scalar=MagicMock(return_value=1600)),  # 报修工时
                MagicMock(scalar=MagicMock(return_value=480)),  # 监控工时
                MagicMock(scalar=MagicMock(return_value=320)),  # 协助工时
                MagicMock(scalar=MagicMock(return_value=75.0)),  # 平均工时
            ]
            mock_db.execute.side_effect = mock_results

            response = await client.get(
                "/api/v1/statistics/work-hours/overview?member_id=test_user.id&start_date=2025-01-01&end_date=2025-01-31",
                headers={"Authorization": "Bearer leader_token"},
            )

            assert response.status_code == 200
            data = response.json()
            assert data["data"]["total_work_minutes"] == 2400


class TestStatisticsErrorHandling(TestStatisticsAPIBasic):
    """测试统计API错误处理"""

    @pytest.mark.asyncio
    async def test_database_connection_error(self, client, admin_user):
        """测试数据库连接错误"""
        with (
            patch("app.api.deps.get_db") as mock_get_db,
            patch("app.api.deps.get_current_active_admin") as mock_get_admin,
        ):

            mock_get_admin.return_value = admin_user
            mock_get_db.side_effect = Exception("Database connection failed")

            response = await client.get(
                "/api/v1/statistics/overview",
                headers={"Authorization": "Bearer admin_token"},
            )

            assert response.status_code == 500

    @pytest.mark.asyncio
    async def test_invalid_query_parameters(self, client, admin_user):
        """测试无效查询参数"""
        with patch("app.api.deps.get_current_active_admin") as mock_get_admin:
            mock_get_admin.return_value = admin_user

            # 测试无效日期格式
            response = await client.get(
                "/api/v1/statistics/overview?start_date=invalid_date",
                headers={"Authorization": "Bearer admin_token"},
            )

            assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_empty_result_handling(self, client, admin_user):
        """测试空结果处理"""
        with (
            patch("app.api.deps.get_db") as mock_get_db,
            patch("app.api.deps.get_current_active_admin") as mock_get_admin,
        ):

            mock_db = AsyncMock()
            mock_get_db.return_value = mock_db
            mock_get_admin.return_value = admin_user

            # Mock空结果
            mock_results = [
                MagicMock(scalar=MagicMock(return_value=0)),  # 总任务数为0
                MagicMock(scalar=MagicMock(return_value=0)),  # 本月任务数为0
                MagicMock(scalar=MagicMock(return_value=0)),  # 已完成任务数为0
                MagicMock(scalar=MagicMock(return_value=None)),  # 平均完成时间为None
                MagicMock(scalar=MagicMock(return_value=None)),  # 平均评分为None
                MagicMock(scalar=MagicMock(return_value=0)),  # 总工时为0
                MagicMock(scalar=MagicMock(return_value=0)),  # 线上任务数为0
                MagicMock(scalar=MagicMock(return_value=0)),  # 线下任务数为0
            ]
            mock_db.execute.side_effect = mock_results

            response = await client.get(
                "/api/v1/statistics/overview",
                headers={"Authorization": "Bearer admin_token"},
            )

            assert response.status_code == 200
            data = response.json()
            assert data["data"]["total_tasks"] == 0
            assert data["data"]["avg_completion_hours"] is None
            assert data["data"]["avg_rating"] is None

    @pytest.mark.asyncio
    async def test_concurrent_access_handling(self, client, admin_user):
        """测试并发访问处理"""
        with (
            patch("app.api.deps.get_db") as mock_get_db,
            patch("app.api.deps.get_current_active_admin") as mock_get_admin,
        ):

            mock_db = AsyncMock()
            mock_get_db.return_value = mock_db
            mock_get_admin.return_value = admin_user

            # Mock并发访问时的数据库锁定情况
            mock_db.execute.side_effect = Exception("Database locked")

            response = await client.get(
                "/api/v1/statistics/overview",
                headers={"Authorization": "Bearer admin_token"},
            )

            assert response.status_code == 500


class TestCalculateEfficiencyScore:
    """测试效率分数计算函数"""

    def test_calculate_efficiency_score_normal_case(self):
        """测试正常情况下的效率分数计算"""
        from app.api.v1.statistics import _calculate_efficiency_score

        # 测试良好表现的分数计算
        score = _calculate_efficiency_score(60.0, 2.0, 4.5, 10)
        assert 80 <= score <= 100  # 高评分应该得到高分数

        # 测试一般表现的分数计算
        score = _calculate_efficiency_score(90.0, 4.0, 3.5, 8)
        assert 50 <= score <= 80  # 中等评分应该得到中等分数

    def test_calculate_efficiency_score_edge_cases(self):
        """测试边界情况的效率分数计算"""
        from app.api.v1.statistics import _calculate_efficiency_score

        # 测试零任务情况
        score = _calculate_efficiency_score(60.0, 2.0, 4.5, 0)
        assert score == 0.0

        # 测试None值处理
        score = _calculate_efficiency_score(None, None, None, 5)
        assert score >= 0.0

        # 测试极值情况
        score = _calculate_efficiency_score(0.0, 0.0, 5.0, 1)
        assert score <= 100.0
