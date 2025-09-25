"""
任务API测试用例
测试所有任务相关的API端点
"""

from datetime import date, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import AsyncClient

from app.main import app
from app.models.member import Member, UserRole
from app.models.task import (
    AssistanceTask,
    MonitoringTask,
    RepairTask,
    TaskCategory,
    TaskPriority,
    TaskStatus,
    TaskType,
)


class TestTasksAPIBasic:
    """测试任务API基础功能"""

    @pytest.fixture
    async def client(self):
        """创建测试客户端"""
        async with AsyncClient(app=app, base_url="http://testserver") as ac:
            yield ac

    @pytest.fixture
    def sample_user(self):
        """创建示例用户"""
        return Member(
            id=1,
            username="test_user",
            student_id="20210001",
            name="测试用户",
            role=UserRole.MEMBER,
        )

    @pytest.fixture
    def admin_user(self):
        """创建管理员用户"""
        return Member(
            id=2,
            username="admin_user",
            student_id="20210002",
            name="管理员",
            role=UserRole.ADMIN,
        )

    @pytest.fixture
    def sample_repair_task(self, sample_user):
        """创建示例报修任务"""
        return RepairTask(
            id=1,
            task_id="T001",
            title="网络故障",
            description="教学楼网络无法连接",
            task_type=TaskType.ONLINE,
            status=TaskStatus.PENDING,
            category=TaskCategory.NETWORK_REPAIR,
            priority=TaskPriority.HIGH,
            report_time=datetime.utcnow(),
            member_id=sample_user.id,
            reporter_name="张三",
            reporter_contact="user@test.com",
            work_minutes=40,
        )


class TestStatusCheck(TestTasksAPIBasic):
    """测试状态检查API"""

    @pytest.mark.asyncio
    async def test_status_check_success(self, client):
        """测试状态检查成功"""
        response = await client.get("/api/v1/tasks/status")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert "service" in data


class TestMonitoringTasksAPI(TestTasksAPIBasic):
    """测试监控任务API"""

    @pytest.mark.asyncio
    async def test_get_monitoring_tasks_basic(self, client):
        """测试获取监控任务基础功能"""
        # Mock数据库查询结果
        with (
            patch("app.api.deps.get_db") as mock_get_db,
            patch("app.api.deps.get_current_user") as mock_get_user,
        ):

            mock_db = AsyncMock()
            mock_get_db.return_value = mock_db
            mock_get_user.return_value = self.sample_user()

            # Mock查询结果
            mock_tasks = [
                MagicMock(
                    id=1,
                    title="机房巡检",
                    monitoring_type="inspection",
                    start_time=datetime.utcnow(),
                    end_time=datetime.utcnow(),
                    work_minutes=120,
                    status=TaskStatus.COMPLETED,
                )
            ]

            mock_result = MagicMock()
            mock_result.scalars.return_value.all.return_value = mock_tasks
            mock_db.execute.return_value = mock_result

            response = await client.get(
                "/api/v1/tasks/monitoring",
                headers={"Authorization": "Bearer test_token"},
            )

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert len(data["data"]["tasks"]) == 1

    @pytest.mark.asyncio
    async def test_get_monitoring_tasks_with_filters(self, client):
        """测试带过滤条件的监控任务查询"""
        with (
            patch("app.api.deps.get_db") as mock_get_db,
            patch("app.api.deps.get_current_user") as mock_get_user,
        ):

            mock_db = AsyncMock()
            mock_get_db.return_value = mock_db
            mock_get_user.return_value = self.sample_user()

            mock_result = MagicMock()
            mock_result.scalars.return_value.all.return_value = []
            mock_db.execute.return_value = mock_result

            response = await client.get(
                "/api/v1/tasks/monitoring?monitoring_type=inspection&status=completed",
                headers={"Authorization": "Bearer test_token"},
            )

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True

    @pytest.mark.asyncio
    async def test_get_monitoring_tasks_unauthorized(self, client):
        """测试未授权访问监控任务"""
        response = await client.get("/api/v1/tasks/monitoring")

        # 根据实际的认证机制，可能返回401或其他状态码
        assert response.status_code in [401, 403, 422]


class TestRepairTasksAPI(TestTasksAPIBasic):
    """测试报修任务API"""

    @pytest.mark.asyncio
    async def test_get_fix_tasks_basic(self, client, sample_repair_task):
        """测试获取报修任务基础功能"""
        with (
            patch("app.api.deps.get_db") as mock_get_db,
            patch("app.api.deps.get_current_user") as mock_get_user,
        ):

            mock_db = AsyncMock()
            mock_get_db.return_value = mock_db
            mock_get_user.return_value = self.sample_user()

            mock_result = MagicMock()
            mock_result.scalars.return_value.all.return_value = [sample_repair_task]
            mock_db.execute.return_value = mock_result

            response = await client.get(
                "/api/v1/tasks/fixes", headers={"Authorization": "Bearer test_token"}
            )

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert len(data["data"]["tasks"]) == 1

    @pytest.mark.asyncio
    async def test_get_repair_list_with_pagination(self, client):
        """测试带分页的报修任务列表"""
        with (
            patch("app.api.deps.get_db") as mock_get_db,
            patch("app.api.deps.get_current_user") as mock_get_user,
        ):

            mock_db = AsyncMock()
            mock_get_db.return_value = mock_db
            mock_get_user.return_value = self.sample_user()

            # Mock分页查询结果
            mock_result = MagicMock()
            mock_result.scalars.return_value.all.return_value = []
            mock_db.execute.return_value = mock_result

            # Mock计数查询
            mock_count_result = MagicMock()
            mock_count_result.scalar.return_value = 0

            response = await client.get(
                "/api/v1/tasks/repair-list?page=1&per_page=10",
                headers={"Authorization": "Bearer test_token"},
            )

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "pagination" in data["data"]


class TestAssistanceTasksAPI(TestTasksAPIBasic):
    """测试协助任务API"""

    @pytest.mark.asyncio
    async def test_get_assistance_tasks_basic(self, client):
        """测试获取协助任务基础功能"""
        with (
            patch("app.api.deps.get_db") as mock_get_db,
            patch("app.api.deps.get_current_user") as mock_get_user,
        ):

            mock_db = AsyncMock()
            mock_get_db.return_value = mock_db
            mock_get_user.return_value = self.sample_user()

            mock_assistance_task = MagicMock(
                id=1,
                title="协助教务处",
                assisted_department="教务处",
                start_time=datetime.utcnow(),
                end_time=datetime.utcnow(),
                work_minutes=180,
                status=TaskStatus.PENDING,
            )

            mock_result = MagicMock()
            mock_result.scalars.return_value.all.return_value = [mock_assistance_task]
            mock_db.execute.return_value = mock_result

            response = await client.get(
                "/api/v1/tasks/assistance",
                headers={"Authorization": "Bearer test_token"},
            )

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert len(data["data"]["tasks"]) == 1

    @pytest.mark.asyncio
    async def test_get_assistance_tasks_with_status_filter(self, client):
        """测试按状态过滤协助任务"""
        with (
            patch("app.api.deps.get_db") as mock_get_db,
            patch("app.api.deps.get_current_user") as mock_get_user,
        ):

            mock_db = AsyncMock()
            mock_get_db.return_value = mock_db
            mock_get_user.return_value = self.sample_user()

            mock_result = MagicMock()
            mock_result.scalars.return_value.all.return_value = []
            mock_db.execute.return_value = mock_result

            response = await client.get(
                "/api/v1/tasks/assistance?status=pending",
                headers={"Authorization": "Bearer test_token"},
            )

            assert response.status_code == 200


class TestWorkTimeDetailAPI(TestTasksAPIBasic):
    """测试工时详情API"""

    @pytest.mark.asyncio
    async def test_get_work_time_detail_basic(self, client, sample_repair_task):
        """测试获取工时详情基础功能"""
        with (
            patch("app.api.deps.get_db") as mock_get_db,
            patch("app.api.deps.get_current_user") as mock_get_user,
        ):

            mock_db = AsyncMock()
            mock_get_db.return_value = mock_db
            mock_get_user.return_value = self.sample_user()

            # Mock任务查询结果
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = sample_repair_task
            mock_db.execute.return_value = mock_result

            response = await client.get(
                "/api/v1/tasks/work-time-detail/1",
                headers={"Authorization": "Bearer test_token"},
            )

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["data"]["task_id"] == sample_repair_task.task_id
            assert data["data"]["work_minutes"] == sample_repair_task.work_minutes

    @pytest.mark.asyncio
    async def test_get_work_time_detail_not_found(self, client):
        """测试获取不存在任务的工时详情"""
        with (
            patch("app.api.deps.get_db") as mock_get_db,
            patch("app.api.deps.get_current_user") as mock_get_user,
        ):

            mock_db = AsyncMock()
            mock_get_db.return_value = mock_db
            mock_get_user.return_value = self.sample_user()

            # Mock任务不存在
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = None
            mock_db.execute.return_value = mock_result

            response = await client.get(
                "/api/v1/tasks/work-time-detail/999",
                headers={"Authorization": "Bearer test_token"},
            )

            assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_get_work_time_detail_with_calculation(
        self, client, sample_repair_task
    ):
        """测试带工时计算的详情API"""
        with (
            patch("app.api.deps.get_db") as mock_get_db,
            patch("app.api.deps.get_current_user") as mock_get_user,
            patch(
                "app.services.work_hours_service.WorkHoursCalculationService"
            ) as mock_service,
        ):

            mock_db = AsyncMock()
            mock_get_db.return_value = mock_db
            mock_get_user.return_value = self.sample_user()

            # Mock任务查询结果
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = sample_repair_task
            mock_db.execute.return_value = mock_result

            # Mock工时计算服务
            mock_calc_service = AsyncMock()
            mock_calc_service.calculate_task_work_minutes.return_value = {
                "base_minutes": 40,
                "bonus_minutes": 0,
                "penalty_minutes": 0,
                "total_minutes": 40,
            }
            mock_service.return_value = mock_calc_service

            response = await client.get(
                "/api/v1/tasks/work-time-detail/1?recalculate=true",
                headers={"Authorization": "Bearer test_token"},
            )

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "calculation_details" in data["data"]


class TestTasksStatsAPI(TestTasksAPIBasic):
    """测试任务统计API"""

    @pytest.mark.asyncio
    async def test_get_tasks_stats_basic(self, client):
        """测试获取任务统计基础功能"""
        with (
            patch("app.api.deps.get_db") as mock_get_db,
            patch("app.api.deps.get_current_user") as mock_get_user,
        ):

            mock_db = AsyncMock()
            mock_get_db.return_value = mock_db
            mock_get_user.return_value = self.admin_user()

            # Mock统计查询结果
            mock_results = [
                MagicMock(scalar=MagicMock(return_value=50)),  # 总任务数
                MagicMock(scalar=MagicMock(return_value=30)),  # 已完成
                MagicMock(scalar=MagicMock(return_value=15)),  # 进行中
                MagicMock(scalar=MagicMock(return_value=5)),  # 待处理
                MagicMock(scalar=MagicMock(return_value=2400)),  # 总工时
            ]
            mock_db.execute.side_effect = mock_results

            response = await client.get(
                "/api/v1/tasks/stats", headers={"Authorization": "Bearer admin_token"}
            )

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["data"]["total_tasks"] == 50
            assert data["data"]["completed_tasks"] == 30
            assert data["data"]["in_progress_tasks"] == 15
            assert data["data"]["pending_tasks"] == 5
            assert data["data"]["total_work_minutes"] == 2400

    @pytest.mark.asyncio
    async def test_get_tasks_stats_with_date_range(self, client):
        """测试带日期范围的任务统计"""
        with (
            patch("app.api.deps.get_db") as mock_get_db,
            patch("app.api.deps.get_current_user") as mock_get_user,
        ):

            mock_db = AsyncMock()
            mock_get_db.return_value = mock_db
            mock_get_user.return_value = self.admin_user()

            mock_results = [
                MagicMock(scalar=MagicMock(return_value=10)),
                MagicMock(scalar=MagicMock(return_value=8)),
                MagicMock(scalar=MagicMock(return_value=2)),
                MagicMock(scalar=MagicMock(return_value=0)),
                MagicMock(scalar=MagicMock(return_value=480)),
            ]
            mock_db.execute.side_effect = mock_results

            response = await client.get(
                "/api/v1/tasks/stats?start_date=2025-01-01&end_date=2025-01-31",
                headers={"Authorization": "Bearer admin_token"},
            )

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["data"]["total_tasks"] == 10

    @pytest.mark.asyncio
    async def test_get_tasks_stats_permission_denied(self, client):
        """测试非管理员访问统计API"""
        with patch("app.api.deps.get_current_user") as mock_get_user:
            mock_get_user.return_value = self.sample_user()  # 普通用户

            response = await client.get(
                "/api/v1/tasks/stats", headers={"Authorization": "Bearer test_token"}
            )

            # 根据实际权限控制，可能返回403或其他状态码
            assert response.status_code in [403, 422]


class TestTaskCreationAPI(TestTasksAPIBasic):
    """测试任务创建API"""

    @pytest.mark.asyncio
    async def test_create_repair_task_basic(self, client):
        """测试创建报修任务基础功能"""
        task_data = {
            "title": "网络故障报修",
            "description": "教学楼1楼网络无法连接",
            "category": "network_repair",
            "priority": "high",
            "reporter_name": "张三",
            "reporter_contact": "zhangsan@university.edu",
        }

        with (
            patch("app.api.deps.get_db") as mock_get_db,
            patch("app.api.deps.get_current_user") as mock_get_user,
            patch("app.services.task_service.TaskService") as mock_service,
        ):

            mock_db = AsyncMock()
            mock_get_db.return_value = mock_db
            mock_get_user.return_value = self.sample_user()

            # Mock任务服务
            mock_task_service = AsyncMock()
            mock_task_service.create_repair_task.return_value = RepairTask(
                id=1, task_id="T001", title="网络故障报修", status=TaskStatus.PENDING
            )
            mock_service.return_value = mock_task_service

            response = await client.post(
                "/api/v1/tasks/repair",
                json=task_data,
                headers={"Authorization": "Bearer test_token"},
            )

            assert response.status_code == 201
            data = response.json()
            assert data["success"] is True
            assert data["data"]["title"] == "网络故障报修"

    @pytest.mark.asyncio
    async def test_create_repair_task_validation_error(self, client):
        """测试创建报修任务数据验证错误"""
        invalid_task_data = {
            "title": "",  # 空标题
            "category": "invalid_category",  # 无效分类
            "priority": "invalid_priority",  # 无效优先级
        }

        response = await client.post(
            "/api/v1/tasks/repair",
            json=invalid_task_data,
            headers={"Authorization": "Bearer test_token"},
        )

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_create_monitoring_task_basic(self, client):
        """测试创建监控任务基础功能"""
        task_data = {
            "title": "机房日常巡检",
            "description": "例行检查A栋机房设备状态",
            "location": "A栋机房",
            "monitoring_type": "inspection",
            "start_time": "2025-01-01T09:00:00",
            "end_time": "2025-01-01T11:00:00",
            "cabinet_count": 15,
        }

        with (
            patch("app.api.deps.get_db") as mock_get_db,
            patch("app.api.deps.get_current_user") as mock_get_user,
            patch("app.services.task_service.TaskService") as mock_service,
        ):

            mock_db = AsyncMock()
            mock_get_db.return_value = mock_db
            mock_get_user.return_value = self.sample_user()

            mock_task_service = AsyncMock()
            mock_task_service.create_monitoring_task.return_value = MonitoringTask(
                id=1,
                title="机房日常巡检",
                monitoring_type="inspection",
                work_minutes=120,
            )
            mock_service.return_value = mock_task_service

            response = await client.post(
                "/api/v1/tasks/monitoring",
                json=task_data,
                headers={"Authorization": "Bearer test_token"},
            )

            assert response.status_code == 201
            data = response.json()
            assert data["success"] is True
            assert data["data"]["title"] == "机房日常巡检"

    @pytest.mark.asyncio
    async def test_create_assistance_task_basic(self, client):
        """测试创建协助任务基础功能"""
        task_data = {
            "title": "协助教务处系统维护",
            "description": "协助更新教务管理系统",
            "assisted_department": "教务处",
            "assisted_person": "李老师",
            "start_time": "2025-01-01T14:00:00",
            "end_time": "2025-01-01T17:00:00",
        }

        with (
            patch("app.api.deps.get_db") as mock_get_db,
            patch("app.api.deps.get_current_user") as mock_get_user,
            patch("app.services.task_service.TaskService") as mock_service,
        ):

            mock_db = AsyncMock()
            mock_get_db.return_value = mock_db
            mock_get_user.return_value = self.sample_user()

            mock_task_service = AsyncMock()
            mock_task_service.create_assistance_task.return_value = AssistanceTask(
                id=1,
                title="协助教务处系统维护",
                assisted_department="教务处",
                work_minutes=180,
            )
            mock_service.return_value = mock_task_service

            response = await client.post(
                "/api/v1/tasks/assistance",
                json=task_data,
                headers={"Authorization": "Bearer test_token"},
            )

            assert response.status_code == 201
            data = response.json()
            assert data["success"] is True
            assert data["data"]["title"] == "协助教务处系统维护"


class TestTaskUpdateAPI(TestTasksAPIBasic):
    """测试任务更新API"""

    @pytest.mark.asyncio
    async def test_update_task_status_basic(self, client, sample_repair_task):
        """测试更新任务状态基础功能"""
        update_data = {"status": TaskStatus.IN_PROGRESS, "note": "开始处理网络故障"}

        with (
            patch("app.api.deps.get_db") as mock_get_db,
            patch("app.api.deps.get_current_user") as mock_get_user,
            patch("app.services.task_service.TaskService") as mock_service,
        ):

            mock_db = AsyncMock()
            mock_get_db.return_value = mock_db
            mock_get_user.return_value = self.sample_user()

            mock_task_service = AsyncMock()
            mock_task_service.update_task_status.return_value = True
            mock_service.return_value = mock_task_service

            response = await client.patch(
                "/api/v1/tasks/1/status",
                json=update_data,
                headers={"Authorization": "Bearer test_token"},
            )

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True

    @pytest.mark.asyncio
    async def test_add_task_feedback_basic(self, client):
        """测试添加任务反馈基础功能"""
        feedback_data = {"feedback": "维修及时，服务态度很好", "rating": 5}

        with (
            patch("app.api.deps.get_db") as mock_get_db,
            patch("app.api.deps.get_current_user") as mock_get_user,
            patch("app.services.task_service.TaskService") as mock_service,
        ):

            mock_db = AsyncMock()
            mock_get_db.return_value = mock_db
            mock_get_user.return_value = self.sample_user()

            mock_task_service = AsyncMock()
            mock_task_service.add_task_rating.return_value = True
            mock_service.return_value = mock_task_service

            response = await client.post(
                "/api/v1/tasks/1/feedback",
                json=feedback_data,
                headers={"Authorization": "Bearer test_token"},
            )

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True


class TestErrorHandling(TestTasksAPIBasic):
    """测试API错误处理"""

    @pytest.mark.asyncio
    async def test_database_connection_error(self, client):
        """测试数据库连接错误"""
        with patch("app.api.deps.get_db") as mock_get_db:
            mock_get_db.side_effect = Exception("Database connection failed")

            response = await client.get("/api/v1/tasks/status")

            # 根据实际错误处理机制，可能返回500或其他状态码
            assert response.status_code in [500, 503]

    @pytest.mark.asyncio
    async def test_invalid_task_id_parameter(self, client):
        """测试无效任务ID参数"""
        with patch("app.api.deps.get_current_user") as mock_get_user:
            mock_get_user.return_value = self.sample_user()

            response = await client.get(
                "/api/v1/tasks/work-time-detail/invalid_id",
                headers={"Authorization": "Bearer test_token"},
            )

            assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_service_layer_exception(self, client):
        """测试服务层异常处理"""
        with (
            patch("app.api.deps.get_db") as mock_get_db,
            patch("app.api.deps.get_current_user") as mock_get_user,
            patch("app.services.task_service.TaskService") as mock_service,
        ):

            mock_db = AsyncMock()
            mock_get_db.return_value = mock_db
            mock_get_user.return_value = self.sample_user()

            # Mock服务层抛出异常
            mock_task_service = AsyncMock()
            mock_task_service.create_repair_task.side_effect = Exception(
                "Service error"
            )
            mock_service.return_value = mock_task_service

            task_data = {
                "title": "测试任务",
                "category": "network_repair",
                "priority": "medium",
            }

            response = await client.post(
                "/api/v1/tasks/repair",
                json=task_data,
                headers={"Authorization": "Bearer test_token"},
            )

            assert response.status_code == 500
