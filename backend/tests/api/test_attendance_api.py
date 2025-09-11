"""
工时管理API测试用例
测试所有工时管理相关的API端点
"""

from datetime import date, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.models.member import Member, UserRole
from app.models.task import (
    AssistanceTask,
    MonitoringTask,
    RepairTask,
    TaskStatus,
    TaskType,
)


class TestAttendanceAPIBasic:
    """测试工时管理API基础功能"""

    @pytest.fixture
    async def client(self):
        """创建测试客户端"""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
            yield ac

    @pytest.fixture
    def regular_user(self):
        """创建普通用户"""
        return Member(
            id=1,
            username="regular_user",
            student_id="20210001",
            name="普通用户",
            email="regular@test.com",
            role=UserRole.MEMBER,
            is_active=True,
        )

    @pytest.fixture
    def admin_user(self):
        """创建管理员用户"""
        return Member(
            id=2,
            username="admin_user",
            student_id="20210002",
            name="管理员",
            email="admin@test.com",
            role=UserRole.ADMIN,
            is_active=True,
        )

    @pytest.fixture
    def test_user(self):
        """创建测试用户"""
        return Member(
            id=3,
            username="test_user",
            student_id="20210003",
            name="测试用户",
            email="test@test.com",
            role=UserRole.MEMBER,
            is_active=True,
        )

    @pytest.fixture
    def sample_repair_task(self, test_user):
        """创建示例报修任务"""
        return RepairTask(
            id=1,
            task_id="T001",
            title="网络故障维修",
            description="教学楼网络连接问题",
            work_minutes=120,
            completion_time=datetime(2024, 12, 15, 14, 30),
            member_id=test_user.id,
            status=TaskStatus.COMPLETED,
            task_type=TaskType.ONLINE,
            rating=5,
        )


class TestWorkHoursRecordsAPI(TestAttendanceAPIBasic):
    """测试工时记录API"""

    @pytest.mark.asyncio
    async def test_get_work_hours_records_basic(
        self, client, regular_user, sample_repair_task
    ):
        """测试获取工时记录基础功能"""
        from app.api.deps import get_current_user, get_db
        from app.main import app

        # Mock database session
        mock_db = AsyncMock()

        # Mock查询结果
        mock_record = MagicMock()
        mock_record.id = sample_repair_task.id
        mock_record.title = sample_repair_task.title
        mock_record.work_date = sample_repair_task.completion_time
        mock_record.work_minutes = sample_repair_task.work_minutes
        mock_record.task_type = sample_repair_task.task_type
        mock_record.rating = sample_repair_task.rating
        mock_record.member_id = sample_repair_task.member_id
        mock_record.member_name = regular_user.name

        mock_result = MagicMock()
        mock_result.fetchall.return_value = [mock_record]
        mock_db.execute.return_value = mock_result

        # Override dependencies
        def override_get_db():
            return mock_db

        def override_get_current_user():
            return regular_user

        app.dependency_overrides[get_db] = override_get_db
        app.dependency_overrides[get_current_user] = override_get_current_user

        try:
            response = await client.get("/api/v1/attendance/records")

            assert response.status_code == 200
            data = response.json()
            assert len(data) == 1
            assert data[0]["id"] == sample_repair_task.id
            assert data[0]["title"] == sample_repair_task.title
            assert data[0]["task_type"] == "维修任务"
            assert data[0]["work_hours"] == 2.0  # 120 minutes / 60
        finally:
            # Clean up overrides
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_get_work_hours_records_with_filters(
        self, client, regular_user, test_user
    ):
        """测试带过滤条件的工时记录查询"""
        with (
            patch("app.api.deps.get_db") as mock_get_db,
            patch("app.api.deps.get_current_user") as mock_get_user,
        ):

            mock_db = AsyncMock()
            mock_get_db.return_value = mock_db
            mock_get_user.return_value = regular_user

            mock_result = MagicMock()
            mock_result.fetchall.return_value = []
            mock_db.execute.return_value = mock_result

            response = await client.get(
                "/api/v1/attendance/records?date_from=2024-12-01&date_to=2024-12-31&page=1&size=20",
                headers={"Authorization": "Bearer test_token"},
            )

            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, list)

    @pytest.mark.asyncio
    async def test_get_work_hours_records_admin_view_others(
        self, client, admin_user, test_user
    ):
        """测试管理员查看其他人的工时记录"""
        with (
            patch("app.api.deps.get_db") as mock_get_db,
            patch("app.api.deps.get_current_user") as mock_get_user,
        ):

            mock_db = AsyncMock()
            mock_get_db.return_value = mock_db
            mock_get_user.return_value = admin_user

            mock_result = MagicMock()
            mock_result.fetchall.return_value = []
            mock_db.execute.return_value = mock_result

            response = await client.get(
                f"/api/v1/attendance/records?member_id={test_user.id}",
                headers={"Authorization": "Bearer admin_token"},
            )

            assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_get_work_hours_records_permission_denied(self, client, regular_user):
        """测试普通用户查看其他人记录权限拒绝"""
        with patch("app.api.deps.get_current_user") as mock_get_user:
            mock_get_user.return_value = regular_user

            response = await client.get(
                "/api/v1/attendance/records?member_id=2",  # 查看其他人的记录
                headers={"Authorization": "Bearer user_token"},
            )

            assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_get_work_hours_records_pagination(
        self, client, regular_user, test_user
    ):
        """测试工时记录分页功能"""
        with (
            patch("app.api.deps.get_db") as mock_get_db,
            patch("app.api.deps.get_current_user") as mock_get_user,
        ):

            mock_db = AsyncMock()
            mock_get_db.return_value = mock_db
            mock_get_user.return_value = regular_user

            # Mock大量记录
            mock_records = []
            for i in range(50):
                mock_record = MagicMock()
                mock_record.id = i + 1
                mock_record.title = f"任务{i+1}"
                mock_record.work_date = datetime.now()
                mock_record.work_minutes = 60
                mock_record.task_type = TaskType.ONLINE
                mock_record.rating = 4
                mock_record.member_id = test_user.id
                mock_record.member_name = "用户"
                mock_records.append(mock_record)

            mock_result = MagicMock()
            mock_result.fetchall.return_value = mock_records
            mock_db.execute.return_value = mock_result

            response = await client.get(
                "/api/v1/attendance/records?page=2&size=10",
                headers={"Authorization": "Bearer test_token"},
            )

            assert response.status_code == 200
            data = response.json()
            assert len(data) == 10  # 第二页应该有10条记录

    @pytest.mark.asyncio
    async def test_get_work_hours_records_database_error(self, client, regular_user):
        """测试数据库查询错误处理"""
        with (
            patch("app.api.deps.get_db") as mock_get_db,
            patch("app.api.deps.get_current_user") as mock_get_user,
        ):

            mock_db = AsyncMock()
            mock_get_db.return_value = mock_db
            mock_get_user.return_value = regular_user

            # Mock数据库错误
            mock_db.execute.side_effect = Exception("Database connection error")

            response = await client.get(
                "/api/v1/attendance/records",
                headers={"Authorization": "Bearer test_token"},
            )

            assert response.status_code == 500


class TestMonthlySummaryAPI(TestAttendanceAPIBasic):
    """测试月度工时汇总API"""

    @pytest.mark.asyncio
    async def test_get_monthly_summary_basic(self, client, regular_user):
        """测试获取月度工时汇总基础功能"""
        with (
            patch("app.api.deps.get_db") as mock_get_db,
            patch("app.api.deps.get_current_user") as mock_get_user,
        ):

            mock_db = AsyncMock()
            mock_get_db.return_value = mock_db
            mock_get_user.return_value = regular_user

            # Mock成员查询结果
            mock_member_result = MagicMock()
            mock_member_result.scalar_one_or_none.return_value = regular_user

            # Mock统计查询结果
            mock_repair_stats = MagicMock()
            mock_repair_stats.total_minutes = 480  # 8小时
            mock_repair_stats.task_count = 4
            mock_repair_stats.avg_rating = 4.5

            mock_monitoring_stats = MagicMock()
            mock_monitoring_stats.total_minutes = 240  # 4小时
            mock_monitoring_stats.task_count = 2

            mock_assistance_stats = MagicMock()
            mock_assistance_stats.total_minutes = 180  # 3小时
            mock_assistance_stats.task_count = 1

            # 按查询顺序设置返回值
            mock_db.execute.side_effect = [
                mock_member_result,  # 成员查询
                MagicMock(
                    fetchone=MagicMock(return_value=mock_repair_stats)
                ),  # 报修统计
                MagicMock(
                    fetchone=MagicMock(return_value=mock_monitoring_stats)
                ),  # 监控统计
                MagicMock(
                    fetchone=MagicMock(return_value=mock_assistance_stats)
                ),  # 协助统计
            ]

            response = await client.get(
                "/api/v1/attendance/summary/2024-12",
                headers={"Authorization": "Bearer test_token"},
            )

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["data"]["member_id"] == regular_user.id
            assert data["data"]["member_name"] == regular_user.name
            assert data["data"]["year"] == 2024
            assert data["data"]["month"] == 12
            assert data["data"]["repair_tasks"]["hours"] == 8.0
            assert data["data"]["monitoring_tasks"]["hours"] == 4.0
            assert data["data"]["assistance_tasks"]["hours"] == 3.0
            assert data["data"]["total"]["hours"] == 15.0

    @pytest.mark.asyncio
    async def test_get_monthly_summary_invalid_month_format(self, client, regular_user):
        """测试无效月份格式"""
        with patch("app.api.deps.get_current_user") as mock_get_user:
            mock_get_user.return_value = regular_user

            response = await client.get(
                "/api/v1/attendance/summary/invalid-month",
                headers={"Authorization": "Bearer test_token"},
            )

            assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_get_monthly_summary_admin_view_others(
        self, client, admin_user, regular_user, test_user
    ):
        """测试管理员查看其他人的月度汇总"""
        with (
            patch("app.api.deps.get_db") as mock_get_db,
            patch("app.api.deps.get_current_user") as mock_get_user,
        ):

            mock_db = AsyncMock()
            mock_get_db.return_value = mock_db
            mock_get_user.return_value = admin_user

            # Mock成员查询结果
            mock_member_result = MagicMock()
            mock_member_result.scalar_one_or_none.return_value = regular_user

            # Mock统计结果为空
            mock_db.execute.side_effect = [
                mock_member_result,
                MagicMock(fetchone=MagicMock(return_value=None)),
                MagicMock(fetchone=MagicMock(return_value=None)),
                MagicMock(fetchone=MagicMock(return_value=None)),
            ]

            response = await client.get(
                f"/api/v1/attendance/summary/2024-12?member_id={test_user.id}",
                headers={"Authorization": "Bearer admin_token"},
            )

            assert response.status_code == 200
            data = response.json()
            assert data["data"]["member_id"] == 1
            assert data["data"]["total"]["hours"] == 0.0

    @pytest.mark.asyncio
    async def test_get_monthly_summary_member_not_found(self, client, admin_user):
        """测试成员不存在的情况"""
        with (
            patch("app.api.deps.get_db") as mock_get_db,
            patch("app.api.deps.get_current_user") as mock_get_user,
        ):

            mock_db = AsyncMock()
            mock_get_db.return_value = mock_db
            mock_get_user.return_value = admin_user

            # Mock成员不存在
            mock_member_result = MagicMock()
            mock_member_result.scalar_one_or_none.return_value = None
            mock_db.execute.return_value = mock_member_result

            response = await client.get(
                "/api/v1/attendance/summary/2024-12?member_id=999",
                headers={"Authorization": "Bearer admin_token"},
            )

            assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_get_monthly_summary_null_stats_handling(self, client, regular_user):
        """测试空统计数据处理"""
        with (
            patch("app.api.deps.get_db") as mock_get_db,
            patch("app.api.deps.get_current_user") as mock_get_user,
        ):

            mock_db = AsyncMock()
            mock_get_db.return_value = mock_db
            mock_get_user.return_value = regular_user

            # Mock成员存在但统计为空
            mock_member_result = MagicMock()
            mock_member_result.scalar_one_or_none.return_value = regular_user

            mock_db.execute.side_effect = [
                mock_member_result,
                MagicMock(fetchone=MagicMock(return_value=None)),  # 空统计
                MagicMock(fetchone=MagicMock(return_value=None)),
                MagicMock(fetchone=MagicMock(return_value=None)),
            ]

            response = await client.get(
                "/api/v1/attendance/summary/2024-12",
                headers={"Authorization": "Bearer test_token"},
            )

            assert response.status_code == 200
            data = response.json()
            assert data["data"]["total"]["hours"] == 0.0
            assert data["data"]["total"]["task_count"] == 0


class TestTodayWorkHoursSummaryAPI(TestAttendanceAPIBasic):
    """测试今日工时统计API"""

    @pytest.mark.asyncio
    async def test_get_today_summary_basic(self, client, regular_user):
        """测试获取今日工时统计基础功能"""
        with (
            patch("app.api.deps.get_db") as mock_get_db,
            patch("app.api.deps.get_current_user") as mock_get_user,
        ):

            mock_db = AsyncMock()
            mock_get_db.return_value = mock_db
            mock_get_user.return_value = regular_user

            # Mock各项统计查询结果
            mock_results = [
                MagicMock(scalar=MagicMock(return_value=240)),  # 维修任务4小时
                MagicMock(scalar=MagicMock(return_value=120)),  # 监控任务2小时
                MagicMock(scalar=MagicMock(return_value=60)),  # 协助任务1小时
                MagicMock(scalar=MagicMock(return_value=5)),  # 活跃成员数
                MagicMock(scalar=MagicMock(return_value=20)),  # 总成员数
            ]
            mock_db.execute.side_effect = mock_results

            response = await client.get(
                "/api/v1/attendance/today-summary",
                headers={"Authorization": "Bearer test_token"},
            )

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["data"]["total_hours"] == 7.0  # (240+120+60)/60
            assert data["data"]["repair_hours"] == 4.0
            assert data["data"]["monitoring_hours"] == 2.0
            assert data["data"]["assistance_hours"] == 1.0
            assert data["data"]["active_members"] == 5
            assert data["data"]["total_members"] == 20
            assert data["data"]["participation_rate"] == 25.0  # 5/20*100

    @pytest.mark.asyncio
    async def test_get_today_summary_today_alias(self, client, regular_user):
        """测试今日工时统计别名端点"""
        with (
            patch("app.api.deps.get_db") as mock_get_db,
            patch("app.api.deps.get_current_user") as mock_get_user,
        ):

            mock_db = AsyncMock()
            mock_get_db.return_value = mock_db
            mock_get_user.return_value = regular_user

            # Mock返回空结果
            mock_results = [
                MagicMock(scalar=MagicMock(return_value=0)),
                MagicMock(scalar=MagicMock(return_value=0)),
                MagicMock(scalar=MagicMock(return_value=0)),
                MagicMock(scalar=MagicMock(return_value=0)),
                MagicMock(scalar=MagicMock(return_value=10)),
            ]
            mock_db.execute.side_effect = mock_results

            response = await client.get(
                "/api/v1/attendance/today",
                headers={"Authorization": "Bearer test_token"},
            )

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["data"]["total_hours"] == 0.0
            assert data["data"]["average_hours"] == 0  # 没有活跃成员时为0
            assert data["data"]["participation_rate"] == 0.0

    @pytest.mark.asyncio
    async def test_get_today_summary_database_error(self, client, regular_user):
        """测试今日统计数据库错误处理"""
        with (
            patch("app.api.deps.get_db") as mock_get_db,
            patch("app.api.deps.get_current_user") as mock_get_user,
        ):

            mock_db = AsyncMock()
            mock_get_db.return_value = mock_db
            mock_get_user.return_value = regular_user

            # Mock数据库错误
            mock_db.execute.side_effect = Exception("Database error")

            response = await client.get(
                "/api/v1/attendance/today-summary",
                headers={"Authorization": "Bearer test_token"},
            )

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is False
            assert "error" in data["details"]

    @pytest.mark.asyncio
    async def test_get_today_summary_zero_division_handling(self, client, regular_user):
        """测试零除法处理"""
        with (
            patch("app.api.deps.get_db") as mock_get_db,
            patch("app.api.deps.get_current_user") as mock_get_user,
        ):

            mock_db = AsyncMock()
            mock_get_db.return_value = mock_db
            mock_get_user.return_value = regular_user

            # Mock零活跃成员和零总成员的情况
            mock_results = [
                MagicMock(scalar=MagicMock(return_value=60)),  # 有工时
                MagicMock(scalar=MagicMock(return_value=0)),
                MagicMock(scalar=MagicMock(return_value=0)),
                MagicMock(scalar=MagicMock(return_value=0)),  # 零活跃成员
                MagicMock(scalar=MagicMock(return_value=0)),  # 零总成员
            ]
            mock_db.execute.side_effect = mock_results

            response = await client.get(
                "/api/v1/attendance/today-summary",
                headers={"Authorization": "Bearer test_token"},
            )

            assert response.status_code == 200
            data = response.json()
            assert data["data"]["average_hours"] == 0  # 应该处理零除法
            assert data["data"]["participation_rate"] == 0.0


class TestWorkHoursExportAPI(TestAttendanceAPIBasic):
    """测试工时数据导出API"""

    @pytest.mark.asyncio
    async def test_export_work_hours_basic(self, client, admin_user, test_user):
        """测试导出工时数据基础功能"""
        with (
            patch("app.api.deps.get_db") as mock_get_db,
            patch("app.api.deps.get_current_user") as mock_get_user,
            patch("pandas.DataFrame") as mock_df,
            patch("tempfile.NamedTemporaryFile"),
        ):

            mock_db = AsyncMock()
            mock_get_db.return_value = mock_db
            mock_get_user.return_value = admin_user

            # Mock数据查询结果
            mock_record = MagicMock()
            mock_record.task_id = "T001"
            mock_record.title = "网络维修"
            mock_record.completion_time = datetime.now()
            mock_record.work_minutes = 120
            mock_record.task_type = TaskType.ONLINE
            mock_record.rating = 5
            mock_record.member_id = test_user.id
            mock_record.member_name = "测试用户"

            mock_result = MagicMock()
            mock_result.fetchall.return_value = [mock_record]
            mock_db.execute.return_value = mock_result

            # Mock DataFrame
            mock_df_instance = MagicMock()
            mock_df.return_value = mock_df_instance

            response = await client.get(
                "/api/v1/attendance/export?date_from=2024-12-01&date_to=2024-12-31&format=excel",
                headers={"Authorization": "Bearer admin_token"},
            )

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "filename" in data
            assert data["total_records"] == 1

    @pytest.mark.asyncio
    async def test_export_work_hours_csv_format(self, client, admin_user):
        """测试CSV格式导出"""
        with (
            patch("app.api.deps.get_db") as mock_get_db,
            patch("app.api.deps.get_current_user") as mock_get_user,
            patch("pandas.DataFrame") as mock_df,
            patch("tempfile.NamedTemporaryFile"),
        ):

            mock_db = AsyncMock()
            mock_get_db.return_value = mock_db
            mock_get_user.return_value = admin_user

            mock_result = MagicMock()
            mock_result.fetchall.return_value = []
            mock_db.execute.return_value = mock_result

            mock_df_instance = MagicMock()
            mock_df.return_value = mock_df_instance

            response = await client.get(
                "/api/v1/attendance/export?date_from=2024-12-01&date_to=2024-12-31&format=csv",
                headers={"Authorization": "Bearer admin_token"},
            )

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["total_records"] == 0

    @pytest.mark.asyncio
    async def test_export_work_hours_permission_denied(self, client, regular_user):
        """测试普通用户导出权限拒绝"""
        with patch("app.api.deps.get_current_user") as mock_get_user:
            mock_get_user.return_value = regular_user

            response = await client.get(
                "/api/v1/attendance/export?date_from=2024-12-01&date_to=2024-12-31",
                headers={"Authorization": "Bearer user_token"},
            )

            assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_export_work_hours_with_member_filter(self, client, admin_user):
        """测试按成员过滤导出"""
        with (
            patch("app.api.deps.get_db") as mock_get_db,
            patch("app.api.deps.get_current_user") as mock_get_user,
            patch("pandas.DataFrame") as mock_df,
            patch("tempfile.NamedTemporaryFile"),
        ):

            mock_db = AsyncMock()
            mock_get_db.return_value = mock_db
            mock_get_user.return_value = admin_user

            mock_result = MagicMock()
            mock_result.fetchall.return_value = []
            mock_db.execute.return_value = mock_result

            mock_df_instance = MagicMock()
            mock_df.return_value = mock_df_instance

            response = await client.get(
                "/api/v1/attendance/export?date_from=2024-12-01&date_to=2024-12-31&member_ids=1&member_ids=2",
                headers={"Authorization": "Bearer admin_token"},
            )

            assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_export_work_hours_no_data(self, client, admin_user):
        """测试无数据导出"""
        with (
            patch("app.api.deps.get_db") as mock_get_db,
            patch("app.api.deps.get_current_user") as mock_get_user,
        ):

            mock_db = AsyncMock()
            mock_get_db.return_value = mock_db
            mock_get_user.return_value = admin_user

            # Mock无数据结果
            mock_result = MagicMock()
            mock_result.fetchall.return_value = []
            mock_db.execute.return_value = mock_result

            response = await client.get(
                "/api/v1/attendance/export?date_from=2024-12-01&date_to=2024-12-31",
                headers={"Authorization": "Bearer admin_token"},
            )

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["total_records"] == 0


class TestWorkHoursStatsAPI(TestAttendanceAPIBasic):
    """测试工时统计API"""

    @pytest.mark.asyncio
    async def test_get_work_hours_stats_basic(self, client, regular_user):
        """测试获取工时统计基础功能"""
        with (
            patch("app.api.deps.get_db") as mock_get_db,
            patch("app.api.deps.get_current_user") as mock_get_user,
        ):

            mock_db = AsyncMock()
            mock_get_db.return_value = mock_db
            mock_get_user.return_value = regular_user

            # Mock统计查询结果
            mock_stats = MagicMock()
            mock_stats.total_minutes = 480  # 8小时
            mock_stats.task_count = 4
            mock_stats.avg_rating = 4.5
            mock_stats.min_minutes = 60
            mock_stats.max_minutes = 180

            # Mock成员查询结果
            mock_member_result = MagicMock()
            mock_member_result.scalar_one_or_none.return_value = regular_user

            mock_db.execute.side_effect = [
                MagicMock(fetchone=MagicMock(return_value=mock_stats)),
                mock_member_result,
            ]

            response = await client.get(
                "/api/v1/attendance/stats?startDate=2024-12-01&endDate=2024-12-31",
                headers={"Authorization": "Bearer test_token"},
            )

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["data"]["total_hours"] == 8.0
            assert data["data"]["task_count"] == 4
            assert data["data"]["average_rating"] == 4.5
            assert data["data"]["average_hours_per_task"] == 2.0  # 8/4

    @pytest.mark.asyncio
    async def test_get_work_hours_stats_invalid_date_format(self, client, regular_user):
        """测试无效日期格式"""
        with patch("app.api.deps.get_current_user") as mock_get_user:
            mock_get_user.return_value = regular_user

            response = await client.get(
                "/api/v1/attendance/stats?startDate=invalid&endDate=2024-12-31",
                headers={"Authorization": "Bearer test_token"},
            )

            assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_get_work_hours_stats_admin_view_others(
        self, client, admin_user, regular_user
    ):
        """测试管理员查看其他人统计"""
        with (
            patch("app.api.deps.get_db") as mock_get_db,
            patch("app.api.deps.get_current_user") as mock_get_user,
        ):

            mock_db = AsyncMock()
            mock_get_db.return_value = mock_db
            mock_get_user.return_value = admin_user

            # Mock空统计结果
            mock_member_result = MagicMock()
            mock_member_result.scalar_one_or_none.return_value = regular_user

            mock_db.execute.side_effect = [
                MagicMock(fetchone=MagicMock(return_value=None)),
                mock_member_result,
            ]

            response = await client.get(
                "/api/v1/attendance/stats?memberId=1&startDate=2024-12-01&endDate=2024-12-31",
                headers={"Authorization": "Bearer admin_token"},
            )

            assert response.status_code == 200
            data = response.json()
            assert data["data"]["total_hours"] == 0.0

    @pytest.mark.asyncio
    async def test_get_work_hours_stats_permission_denied(self, client, regular_user):
        """测试普通用户查看其他人统计权限拒绝"""
        with patch("app.api.deps.get_current_user") as mock_get_user:
            mock_get_user.return_value = regular_user

            response = await client.get(
                "/api/v1/attendance/stats?memberId=2&startDate=2024-12-01&endDate=2024-12-31",
                headers={"Authorization": "Bearer user_token"},
            )

            assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_get_work_hours_stats_member_not_found(self, client, admin_user):
        """测试成员不存在"""
        with (
            patch("app.api.deps.get_db") as mock_get_db,
            patch("app.api.deps.get_current_user") as mock_get_user,
        ):

            mock_db = AsyncMock()
            mock_get_db.return_value = mock_db
            mock_get_user.return_value = admin_user

            # Mock成员不存在
            mock_member_result = MagicMock()
            mock_member_result.scalar_one_or_none.return_value = None

            mock_db.execute.side_effect = [
                MagicMock(fetchone=MagicMock(return_value=None)),
                mock_member_result,
            ]

            response = await client.get(
                "/api/v1/attendance/stats?memberId=999&startDate=2024-12-01&endDate=2024-12-31",
                headers={"Authorization": "Bearer admin_token"},
            )

            assert response.status_code == 404


class TestWorkHoursChartDataAPI(TestAttendanceAPIBasic):
    """测试工时图表数据API"""

    @pytest.mark.asyncio
    async def test_get_chart_data_daily(self, client, regular_user):
        """测试按日获取图表数据"""
        with (
            patch("app.api.deps.get_db") as mock_get_db,
            patch("app.api.deps.get_current_user") as mock_get_user,
        ):

            mock_db = AsyncMock()
            mock_get_db.return_value = mock_db
            mock_get_user.return_value = regular_user

            # Mock每日数据
            mock_chart_data = [
                MagicMock(period=date(2024, 12, 1), total_minutes=120, task_count=2),
                MagicMock(period=date(2024, 12, 2), total_minutes=180, task_count=3),
            ]

            mock_result = MagicMock()
            mock_result.fetchall.return_value = mock_chart_data
            mock_db.execute.return_value = mock_result

            response = await client.get(
                "/api/v1/attendance/chart-data?type=daily&startDate=2024-12-01&endDate=2024-12-31",
                headers={"Authorization": "Bearer test_token"},
            )

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["data"]["type"] == "daily"
            assert len(data["data"]["chart"]["labels"]) == 2
            assert data["data"]["chart"]["datasets"][0]["data"] == [2.0, 3.0]  # hours
            assert data["data"]["chart"]["datasets"][1]["data"] == [2, 3]  # task counts

    @pytest.mark.asyncio
    async def test_get_chart_data_weekly(self, client, regular_user):
        """测试按周获取图表数据"""
        with (
            patch("app.api.deps.get_db") as mock_get_db,
            patch("app.api.deps.get_current_user") as mock_get_user,
        ):

            mock_db = AsyncMock()
            mock_get_db.return_value = mock_db
            mock_get_user.return_value = regular_user

            # Mock按周数据
            mock_chart_data = [
                MagicMock(period="2024-W48", total_minutes=480, task_count=8),
                MagicMock(period="2024-W49", total_minutes=360, task_count=6),
            ]

            mock_result = MagicMock()
            mock_result.fetchall.return_value = mock_chart_data
            mock_db.execute.return_value = mock_result

            response = await client.get(
                "/api/v1/attendance/chart-data?type=weekly&startDate=2024-12-01&endDate=2024-12-31",
                headers={"Authorization": "Bearer test_token"},
            )

            assert response.status_code == 200
            data = response.json()
            assert data["data"]["type"] == "weekly"
            assert len(data["data"]["chart"]["labels"]) == 2
            assert data["data"]["summary"]["total_hours"] == 14.0  # (480+360)/60

    @pytest.mark.asyncio
    async def test_get_chart_data_monthly(self, client, regular_user):
        """测试按月获取图表数据"""
        with (
            patch("app.api.deps.get_db") as mock_get_db,
            patch("app.api.deps.get_current_user") as mock_get_user,
        ):

            mock_db = AsyncMock()
            mock_get_db.return_value = mock_db
            mock_get_user.return_value = regular_user

            # Mock按月数据
            mock_chart_data = [
                MagicMock(period="2024-12", total_minutes=2400, task_count=40),
            ]

            mock_result = MagicMock()
            mock_result.fetchall.return_value = mock_chart_data
            mock_db.execute.return_value = mock_result

            response = await client.get(
                "/api/v1/attendance/chart-data?type=monthly&startDate=2024-12-01&endDate=2024-12-31",
                headers={"Authorization": "Bearer test_token"},
            )

            assert response.status_code == 200
            data = response.json()
            assert data["data"]["type"] == "monthly"
            assert data["data"]["summary"]["total_hours"] == 40.0

    @pytest.mark.asyncio
    async def test_get_chart_data_invalid_type(self, client, regular_user):
        """测试无效图表类型"""
        with patch("app.api.deps.get_current_user") as mock_get_user:
            mock_get_user.return_value = regular_user

            response = await client.get(
                "/api/v1/attendance/chart-data?type=invalid&startDate=2024-12-01&endDate=2024-12-31",
                headers={"Authorization": "Bearer test_token"},
            )

            assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_get_chart_data_invalid_date(self, client, regular_user):
        """测试无效日期格式"""
        with patch("app.api.deps.get_current_user") as mock_get_user:
            mock_get_user.return_value = regular_user

            response = await client.get(
                "/api/v1/attendance/chart-data?type=daily&startDate=invalid&endDate=2024-12-31",
                headers={"Authorization": "Bearer test_token"},
            )

            assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_get_chart_data_with_member_filter(self, client, admin_user):
        """测试按成员过滤图表数据"""
        with (
            patch("app.api.deps.get_db") as mock_get_db,
            patch("app.api.deps.get_current_user") as mock_get_user,
        ):

            mock_db = AsyncMock()
            mock_get_db.return_value = mock_db
            mock_get_user.return_value = admin_user

            mock_result = MagicMock()
            mock_result.fetchall.return_value = []
            mock_db.execute.return_value = mock_result

            response = await client.get(
                "/api/v1/attendance/chart-data?type=daily&startDate=2024-12-01&endDate=2024-12-31&memberId=1",
                headers={"Authorization": "Bearer admin_token"},
            )

            assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_get_chart_data_empty_result(self, client, regular_user):
        """测试空图表数据"""
        with (
            patch("app.api.deps.get_db") as mock_get_db,
            patch("app.api.deps.get_current_user") as mock_get_user,
        ):

            mock_db = AsyncMock()
            mock_get_db.return_value = mock_db
            mock_get_user.return_value = regular_user

            mock_result = MagicMock()
            mock_result.fetchall.return_value = []
            mock_db.execute.return_value = mock_result

            response = await client.get(
                "/api/v1/attendance/chart-data?type=daily&startDate=2024-12-01&endDate=2024-12-31",
                headers={"Authorization": "Bearer test_token"},
            )

            assert response.status_code == 200
            data = response.json()
            assert data["data"]["chart"]["labels"] == []
            assert data["data"]["summary"]["total_hours"] == 0


class TestHealthCheckAPI(TestAttendanceAPIBasic):
    """测试健康检查API"""

    @pytest.mark.asyncio
    async def test_health_check(self, client):
        """测试健康检查端点"""
        response = await client.get("/api/v1/attendance/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "work_hours_management"
        assert "timestamp" in data
        assert "message" in data


class TestAttendanceAPIErrorHandling(TestAttendanceAPIBasic):
    """测试工时管理API错误处理"""

    @pytest.mark.asyncio
    async def test_unauthorized_access(self, client):
        """测试未授权访问"""
        response = await client.get("/api/v1/attendance/records")

        assert response.status_code in [401, 422]

    @pytest.mark.asyncio
    async def test_database_connection_error(self, client, regular_user):
        """测试数据库连接错误"""
        with (
            patch("app.api.deps.get_db") as mock_get_db,
            patch("app.api.deps.get_current_user") as mock_get_user,
        ):

            mock_get_user.return_value = regular_user
            mock_get_db.side_effect = Exception("Database connection failed")

            response = await client.get(
                "/api/v1/attendance/records",
                headers={"Authorization": "Bearer test_token"},
            )

            assert response.status_code == 500

    @pytest.mark.asyncio
    async def test_concurrent_requests_handling(self, client, regular_user):
        """测试并发请求处理"""
        with (
            patch("app.api.deps.get_db") as mock_get_db,
            patch("app.api.deps.get_current_user") as mock_get_user,
        ):

            mock_db = AsyncMock()
            mock_get_db.return_value = mock_db
            mock_get_user.return_value = regular_user

            # Mock延迟响应
            async def slow_execute(*args):
                import asyncio

                await asyncio.sleep(0.1)
                mock_result = MagicMock()
                mock_result.fetchall.return_value = []
                return mock_result

            mock_db.execute = slow_execute

            # 发送多个并发请求
            import asyncio

            tasks = []
            for _ in range(3):
                task = client.get(
                    "/api/v1/attendance/records",
                    headers={"Authorization": "Bearer test_token"},
                )
                tasks.append(task)

            responses = await asyncio.gather(*tasks)

            # 所有请求都应该成功
            for response in responses:
                assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_large_date_range_handling(self, client, regular_user):
        """测试大日期范围处理"""
        with (
            patch("app.api.deps.get_db") as mock_get_db,
            patch("app.api.deps.get_current_user") as mock_get_user,
        ):

            mock_db = AsyncMock()
            mock_get_db.return_value = mock_db
            mock_get_user.return_value = regular_user

            mock_result = MagicMock()
            mock_result.fetchall.return_value = []
            mock_db.execute.return_value = mock_result

            # 测试一年的日期范围
            response = await client.get(
                "/api/v1/attendance/records?date_from=2024-01-01&date_to=2024-12-31",
                headers={"Authorization": "Bearer test_token"},
            )

            assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_malformed_query_parameters(self, client, regular_user):
        """测试错误格式的查询参数"""
        with patch("app.api.deps.get_current_user") as mock_get_user:
            mock_get_user.return_value = regular_user

            # 测试无效的分页参数
            response = await client.get(
                "/api/v1/attendance/records?page=0&size=1001",
                headers={"Authorization": "Bearer test_token"},
            )

            # 应该返回验证错误
            assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_sql_injection_prevention(self, client, regular_user):
        """测试SQL注入防护"""
        with (
            patch("app.api.deps.get_db") as mock_get_db,
            patch("app.api.deps.get_current_user") as mock_get_user,
        ):

            mock_db = AsyncMock()
            mock_get_db.return_value = mock_db
            mock_get_user.return_value = regular_user

            mock_result = MagicMock()
            mock_result.fetchall.return_value = []
            mock_db.execute.return_value = mock_result

            # 尝试SQL注入
            response = await client.get(
                "/api/v1/attendance/records?date_from=2024-01-01'; DROP TABLE repair_tasks; --",
                headers={"Authorization": "Bearer test_token"},
            )

            # 应该正常处理，不会执行恶意SQL
            assert response.status_code in [200, 422]

    @pytest.mark.asyncio
    async def test_memory_usage_with_large_datasets(
        self, client, admin_user, test_user
    ):
        """测试大数据集内存使用"""
        with (
            patch("app.api.deps.get_db") as mock_get_db,
            patch("app.api.deps.get_current_user") as mock_get_user,
            patch("pandas.DataFrame") as mock_df,
            patch("tempfile.NamedTemporaryFile"),
        ):

            mock_db = AsyncMock()
            mock_get_db.return_value = mock_db
            mock_get_user.return_value = admin_user

            # Mock大量记录
            large_dataset = []
            for i in range(10000):
                mock_record = MagicMock()
                mock_record.task_id = f"T{i:05d}"
                mock_record.title = f"任务{i}"
                mock_record.completion_time = datetime.now()
                mock_record.work_minutes = 60
                mock_record.task_type = TaskType.ONLINE
                mock_record.rating = 4
                mock_record.member_id = test_user.id
                mock_record.member_name = "用户"
                large_dataset.append(mock_record)

            mock_result = MagicMock()
            mock_result.fetchall.return_value = large_dataset
            mock_db.execute.return_value = mock_result

            mock_df_instance = MagicMock()
            mock_df.return_value = mock_df_instance

            response = await client.get(
                "/api/v1/attendance/export?date_from=2024-01-01&date_to=2024-12-31",
                headers={"Authorization": "Bearer admin_token"},
            )

            # 应该能处理大数据集而不崩溃
            assert response.status_code == 200
            data = response.json()
            assert data["total_records"] == 10000
