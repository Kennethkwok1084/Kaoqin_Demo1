"""
Tasks API 简化功能测试
专注于核心API端点的基础覆盖率提升
"""

from datetime import datetime, timedelta

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_password_hash
from app.models.member import Member, UserRole
from app.models.task import RepairTask, TaskCategory, TaskPriority, TaskStatus, TaskType


class TestTasksAPISimple:
    """Tasks API 简化测试套件"""

    @pytest.fixture
    async def admin_user(self, async_session: AsyncSession) -> Member:
        """创建管理员用户"""
        admin = Member(
            username="admin_simple",
            name="Admin User",
            student_id="ADMIN_SIMPLE_001",
            password_hash=get_password_hash("AdminPass123!"),
            role=UserRole.ADMIN,
            is_active=True,
            phone="13900000101",
            email="admin@test.com",
            class_name="管理员班级",
        )
        async_session.add(admin)
        await async_session.commit()
        await async_session.refresh(admin)
        return admin

    @pytest.fixture
    async def sample_task(
        self, async_session: AsyncSession, admin_user: Member
    ) -> RepairTask:
        """创建示例任务"""
        task = RepairTask(
            title="测试维修任务",
            description="这是一个测试任务",
            category=TaskCategory.NETWORK_REPAIR,
            priority=TaskPriority.MEDIUM,
            status=TaskStatus.PENDING,
            task_type=TaskType.REPAIR,
            reporter_name="张三",
            reporter_phone="13800138001",
            location="测试地点",
            created_by_id=admin_user.id,
        )
        async_session.add(task)
        await async_session.commit()
        await async_session.refresh(task)
        return task

    async def get_auth_headers(
        self, async_client: AsyncClient, student_id: str, password: str
    ):
        """获取认证头"""
        login_data = {"student_id": student_id, "password": password}
        response = await async_client.post("/api/v1/auth/login", json=login_data)
        assert response.status_code == 200
        token_data = response.json()["data"]
        return {"Authorization": f"Bearer {token_data['access_token']}"}

    async def test_tasks_status_overview(
        self, async_client: AsyncClient, sample_task, admin_user: Member
    ):
        """测试任务状态概览"""
        headers = await self.get_auth_headers(
            async_client, "ADMIN_SIMPLE_001", "AdminPass123!"
        )

        response = await async_client.get("/api/v1/tasks/status", headers=headers)
        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True
        assert "data" in data

    async def test_get_repair_list(
        self, async_client: AsyncClient, sample_task, admin_user: Member
    ):
        """测试获取维修任务列表"""
        headers = await self.get_auth_headers(
            async_client, "ADMIN_SIMPLE_001", "AdminPass123!"
        )

        response = await async_client.get("/api/v1/tasks/repair-list", headers=headers)
        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True

    async def test_create_repair_task(
        self, async_client: AsyncClient, admin_user: Member
    ):
        """测试创建维修任务"""
        headers = await self.get_auth_headers(
            async_client, "ADMIN_SIMPLE_001", "AdminPass123!"
        )

        task_data = {
            "title": "新建测试任务",
            "description": "任务描述",
            "category": "NETWORK_REPAIR",
            "priority": "HIGH",
            "reporter_name": "测试用户",
            "reporter_phone": "13800138999",
            "location": "测试位置",
        }

        response = await async_client.post(
            "/api/v1/tasks/repair", json=task_data, headers=headers
        )
        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True

    async def test_get_task_detail(
        self, async_client: AsyncClient, sample_task, admin_user: Member
    ):
        """测试获取任务详情"""
        headers = await self.get_auth_headers(
            async_client, "ADMIN_SIMPLE_001", "AdminPass123!"
        )

        response = await async_client.get(
            f"/api/v1/tasks/repair/{sample_task.id}", headers=headers
        )
        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True
        assert data["data"]["id"] == sample_task.id

    async def test_update_task_status(
        self, async_client: AsyncClient, sample_task, admin_user: Member
    ):
        """测试更新任务状态"""
        headers = await self.get_auth_headers(
            async_client, "ADMIN_SIMPLE_001", "AdminPass123!"
        )

        status_data = {"status": "IN_PROGRESS", "notes": "开始处理任务"}

        response = await async_client.put(
            f"/api/v1/tasks/repair/{sample_task.id}/status",
            json=status_data,
            headers=headers,
        )
        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True

    async def test_task_statistics(
        self, async_client: AsyncClient, sample_task, admin_user: Member
    ):
        """测试任务统计"""
        headers = await self.get_auth_headers(
            async_client, "ADMIN_SIMPLE_001", "AdminPass123!"
        )

        response = await async_client.get("/api/v1/tasks/stats", headers=headers)
        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True

    async def test_work_hours_calculation(
        self, async_client: AsyncClient, sample_task, admin_user: Member
    ):
        """测试工时计算"""
        headers = await self.get_auth_headers(
            async_client, "ADMIN_SIMPLE_001", "AdminPass123!"
        )

        calc_data = {"actual_hours": 2.0, "completion_quality": "GOOD"}

        response = await async_client.post(
            f"/api/v1/tasks/repair/{sample_task.id}/calculate-hours",
            json=calc_data,
            headers=headers,
        )
        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True

    async def test_export_comprehensive(
        self, async_client: AsyncClient, sample_task, admin_user: Member
    ):
        """测试综合导出"""
        headers = await self.get_auth_headers(
            async_client, "ADMIN_SIMPLE_001", "AdminPass123!"
        )

        export_params = {
            "start_date": (datetime.now() - timedelta(days=7)).date().isoformat(),
            "end_date": datetime.now().date().isoformat(),
        }

        response = await async_client.get(
            "/api/v1/tasks/export/comprehensive", params=export_params, headers=headers
        )
        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True

    async def test_health_check(self, async_client: AsyncClient):
        """测试健康检查"""
        response = await async_client.get("/api/v1/tasks/health")
        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True

    async def test_my_tasks(self, async_client: AsyncClient, admin_user: Member):
        """测试我的任务列表"""
        headers = await self.get_auth_headers(
            async_client, "ADMIN_SIMPLE_001", "AdminPass123!"
        )

        response = await async_client.get("/api/v1/tasks/my", headers=headers)
        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True

    async def test_task_tags_list(self, async_client: AsyncClient, admin_user: Member):
        """测试任务标签列表"""
        headers = await self.get_auth_headers(
            async_client, "ADMIN_SIMPLE_001", "AdminPass123!"
        )

        response = await async_client.get("/api/v1/tasks/tags", headers=headers)
        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True

    async def test_work_hours_statistics(
        self, async_client: AsyncClient, admin_user: Member
    ):
        """测试工时统计"""
        headers = await self.get_auth_headers(
            async_client, "ADMIN_SIMPLE_001", "AdminPass123!"
        )

        response = await async_client.get(
            "/api/v1/tasks/work-hours/statistics", headers=headers
        )
        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True
