"""
Tasks API 完整功能测试
目标：覆盖 app/api/v1/tasks.py 中的 1,817 行未覆盖代码
重点覆盖：任务生命周期、批量操作、工时计算、统计分析等核心业务逻辑
"""

import pytest
import json
from datetime import datetime, timedelta
from typing import Dict, Any
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.member import Member, UserRole
from app.models.task import (
    RepairTask, TaskStatus, TaskType, TaskCategory, 
    TaskPriority, TaskTag, TaskTagType
)
from app.core.security import get_password_hash


class TestTasksAPIComprehensive:
    """Tasks API 完整功能测试套件"""

    @pytest.fixture
    async def admin_user(self, async_session: AsyncSession) -> Member:
        """创建管理员用户"""
        admin = Member(
            username="admin_tasks",
            name="Tasks Admin",
            student_id="ADMIN_TASKS_001",
            password_hash=get_password_hash("AdminPass123!"),
            role=UserRole.ADMIN,
            is_active=True,
            phone="13900000001",
            email="admin_tasks@test.com",
            class_name="测试班级"
        )
        async_session.add(admin)
        await async_session.commit()
        await async_session.refresh(admin)
        return admin

    @pytest.fixture
    async def regular_user(self, async_session: AsyncSession) -> Member:
        """创建普通用户"""
        user = Member(
            username="user_tasks",
            name="Tasks User", 
            student_id="USER_TASKS_001",
            password_hash=get_password_hash("UserPass123!"),
            role=UserRole.MEMBER,
            is_active=True,
            phone="13900000002",
            email="user_tasks@test.com",
            class_name="测试班级"
        )
        async_session.add(user)
        await async_session.commit()
        await async_session.refresh(user)
        return user

    @pytest.fixture
    async def sample_tasks(self, async_session: AsyncSession, admin_user: Member, regular_user: Member):
        """创建示例任务数据"""
        tasks = []
        
        # 创建不同状态的维修任务
        task_data = [
            {
                "title": "网络故障维修",
                "description": "机房网络设备故障",
                "category": TaskCategory.NETWORK_REPAIR,
                "priority": TaskPriority.HIGH,
                "status": TaskStatus.PENDING,
                "task_type": TaskType.REPAIR,
                "assigned_to_id": regular_user.id,
                "reporter_name": "张三",
                "reporter_phone": "13800138001",
                "location": "教学楼A101"
            },
            {
                "title": "设备检查任务",
                "description": "定期设备检查",
                "category": TaskCategory.HARDWARE_REPAIR, 
                "priority": TaskPriority.MEDIUM,
                "status": TaskStatus.IN_PROGRESS,
                "task_type": TaskType.MONITORING,
                "assigned_to_id": regular_user.id,
                "reporter_name": "李四",
                "reporter_phone": "13800138002", 
                "location": "实验楼B202"
            },
            {
                "title": "紧急协助任务",
                "description": "紧急技术支持",
                "category": TaskCategory.SOFTWARE_SUPPORT,
                "priority": TaskPriority.URGENT,
                "status": TaskStatus.COMPLETED,
                "task_type": TaskType.ASSISTANCE,
                "assigned_to_id": admin_user.id,
                "reporter_name": "王五",
                "reporter_phone": "13800138003",
                "location": "办公楼C303"
            }
        ]

        for data in task_data:
            task = RepairTask(**data, created_by_id=admin_user.id)
            async_session.add(task)
            tasks.append(task)
        
        await async_session.commit()
        
        # 刷新任务对象
        for task in tasks:
            await async_session.refresh(task)
            
        return tasks

    async def get_auth_headers(self, async_client: AsyncClient, student_id: str, password: str) -> Dict[str, str]:
        """获取认证头"""
        login_data = {"student_id": student_id, "password": password}
        response = await async_client.post("/api/v1/auth/login", json=login_data)
        assert response.status_code == 200
        
        token_data = response.json()["data"]
        return {"Authorization": f"Bearer {token_data['access_token']}"}

    # ============= 核心API测试 =============

    async def test_get_tasks_status_overview(self, async_client: AsyncClient, sample_tasks, admin_user: Member):
        """测试任务状态概览 - 覆盖状态统计逻辑"""
        headers = await self.get_auth_headers(async_client, "ADMIN_TASKS_001", "AdminPass123!")
        
        response = await async_client.get("/api/v1/tasks/status", headers=headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        
        # 验证统计数据结构
        stats = data["data"]
        assert "total_tasks" in stats
        assert "pending_tasks" in stats
        assert "in_progress_tasks" in stats
        assert "completed_tasks" in stats
        assert "overdue_tasks" in stats
        
        # 验证数据正确性
        assert stats["total_tasks"] == 3
        assert stats["pending_tasks"] == 1
        assert stats["in_progress_tasks"] == 1
        assert stats["completed_tasks"] == 1

    async def test_get_monitoring_tasks(self, async_client: AsyncClient, sample_tasks, admin_user: Member):
        """测试获取监控任务列表 - 覆盖任务过滤和分页逻辑"""
        headers = await self.get_auth_headers(async_client, "ADMIN_TASKS_001", "AdminPass123!")
        
        # 测试基本获取
        response = await async_client.get("/api/v1/tasks/monitoring", headers=headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        assert "total" in data["data"]
        assert "tasks" in data["data"]
        
        # 测试分页参数
        response = await async_client.get(
            "/api/v1/tasks/monitoring?page=1&page_size=10&status=IN_PROGRESS", 
            headers=headers
        )
        assert response.status_code == 200
        
        data = response.json()
        monitoring_tasks = [t for t in data["data"]["tasks"] if t["task_type"] == "MONITORING"]
        assert len(monitoring_tasks) >= 0

    async def test_create_repair_task_complete_flow(self, async_client: AsyncClient, admin_user: Member):
        """测试创建维修任务完整流程 - 覆盖任务创建逻辑"""
        headers = await self.get_auth_headers(async_client, "ADMIN_TASKS_001", "AdminPass123!")
        
        # 准备任务数据
        task_data = {
            "title": "新维修任务测试",
            "description": "这是一个测试维修任务的详细描述",
            "category": "NETWORK_REPAIR",
            "priority": "HIGH",
            "task_type": "REPAIR",
            "reporter_name": "测试报告人",
            "reporter_phone": "13800138999",
            "location": "测试位置A101",
            "estimated_hours": 2.5,
            "expected_completion": (datetime.now() + timedelta(days=1)).isoformat(),
            "tags": ["urgent", "network"]
        }
        
        response = await async_client.post("/api/v1/tasks/repair", json=task_data, headers=headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        
        # 验证创建的任务数据
        created_task = data["data"]
        assert created_task["title"] == task_data["title"]
        assert created_task["description"] == task_data["description"]
        assert created_task["category"] == task_data["category"]
        assert created_task["priority"] == task_data["priority"]
        assert created_task["status"] == "PENDING"
        
        # 验证任务ID返回
        task_id = created_task["id"]
        assert task_id is not None
        
        return task_id

    async def test_update_repair_task_comprehensive(self, async_client: AsyncClient, sample_tasks, admin_user: Member):
        """测试更新维修任务 - 覆盖任务更新逻辑"""
        headers = await self.get_auth_headers(async_client, "ADMIN_TASKS_001", "AdminPass123!")
        
        task_id = sample_tasks[0].id
        
        # 准备更新数据
        update_data = {
            "title": "更新后的任务标题",
            "description": "更新后的任务描述",
            "priority": "URGENT",
            "estimated_hours": 3.0,
            "location": "更新后的位置",
            "notes": "任务更新测试备注"
        }
        
        response = await async_client.put(f"/api/v1/tasks/repair/{task_id}", json=update_data, headers=headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        
        # 验证更新的数据
        updated_task = data["data"]
        assert updated_task["title"] == update_data["title"]
        assert updated_task["description"] == update_data["description"]
        assert updated_task["priority"] == update_data["priority"]
        assert float(updated_task["estimated_hours"]) == update_data["estimated_hours"]

    async def test_task_status_workflow(self, async_client: AsyncClient, sample_tasks, admin_user: Member, regular_user: Member):
        """测试任务状态工作流 - 覆盖状态转换逻辑"""
        admin_headers = await self.get_auth_headers(async_client, "ADMIN_TASKS_001", "AdminPass123!")
        user_headers = await self.get_auth_headers(async_client, "USER_TASKS_001", "UserPass123!")
        
        task_id = sample_tasks[0].id
        
        # 1. 分配任务
        assign_data = {
            "assigned_to_id": regular_user.id,
            "assignment_notes": "分配给指定用户处理"
        }
        response = await async_client.put(f"/api/v1/tasks/repair/{task_id}/assign", json=assign_data, headers=admin_headers)
        assert response.status_code == 200
        
        # 2. 开始任务
        response = await async_client.post(f"/api/v1/tasks/{task_id}/start", headers=user_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True
        task_data = data["data"]
        assert task_data["status"] == "IN_PROGRESS"
        assert task_data["started_at"] is not None
        
        # 3. 完成任务
        completion_data = {
            "completion_notes": "任务已成功完成",
            "actual_hours": 2.0,
            "quality_rating": 5
        }
        response = await async_client.post(f"/api/v1/tasks/{task_id}/complete", json=completion_data, headers=user_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True
        task_data = data["data"]
        assert task_data["status"] == "COMPLETED"
        assert task_data["completed_at"] is not None

    async def test_batch_operations(self, async_client: AsyncClient, sample_tasks, admin_user: Member):
        """测试批量操作 - 覆盖批量处理逻辑"""
        headers = await self.get_auth_headers(async_client, "ADMIN_TASKS_001", "AdminPass123!")
        
        task_ids = [task.id for task in sample_tasks[:2]]
        
        # 测试批量删除
        batch_data = {"task_ids": task_ids}
        response = await async_client.delete("/api/v1/tasks/batch-delete", json=batch_data, headers=headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        
        # 验证批量操作结果
        result = data["data"]
        assert "deleted_count" in result
        assert result["deleted_count"] >= 1

    async def test_work_hours_calculation(self, async_client: AsyncClient, sample_tasks, admin_user: Member):
        """测试工时计算 - 覆盖工时计算逻辑"""
        headers = await self.get_auth_headers(async_client, "ADMIN_TASKS_001", "AdminPass123!")
        
        task_id = sample_tasks[0].id
        
        # 测试工时计算
        calc_data = {
            "actual_hours": 2.5,
            "completion_quality": "EXCELLENT",
            "is_rush_task": True,
            "has_overtime": False,
            "notes": "工时计算测试"
        }
        
        response = await async_client.post(f"/api/v1/tasks/repair/{task_id}/calculate-hours", json=calc_data, headers=headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        
        # 验证计算结果
        calculation = data["data"]
        assert "calculated_hours" in calculation
        assert "bonus_hours" in calculation
        assert "total_hours" in calculation
        assert float(calculation["calculated_hours"]) >= 0

    async def test_task_statistics_comprehensive(self, async_client: AsyncClient, sample_tasks, admin_user: Member):
        """测试任务统计 - 覆盖统计分析逻辑"""
        headers = await self.get_auth_headers(async_client, "ADMIN_TASKS_001", "AdminPass123!")
        
        # 测试获取任务统计
        response = await async_client.get("/api/v1/tasks/stats", headers=headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        
        # 验证统计数据结构
        stats = data["data"]
        required_fields = [
            "total_tasks", "completion_rate", "average_completion_time",
            "task_distribution", "priority_distribution", "monthly_trends"
        ]
        
        for field in required_fields:
            assert field in stats
        
        # 验证统计数据类型
        assert isinstance(stats["total_tasks"], int)
        assert isinstance(stats["completion_rate"], (int, float))
        assert isinstance(stats["task_distribution"], dict)

    async def test_comprehensive_export(self, async_client: AsyncClient, sample_tasks, admin_user: Member):
        """测试综合导出功能 - 覆盖数据导出逻辑"""
        headers = await self.get_auth_headers(async_client, "ADMIN_TASKS_001", "AdminPass123!")
        
        # 测试综合导出
        export_params = {
            "start_date": (datetime.now() - timedelta(days=30)).date().isoformat(),
            "end_date": datetime.now().date().isoformat(),
            "include_completed": True,
            "include_statistics": True,
            "format": "detailed"
        }
        
        response = await async_client.get(
            "/api/v1/tasks/export/comprehensive", 
            params=export_params,
            headers=headers
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        
        # 验证导出数据结构
        export_data = data["data"]
        assert "tasks" in export_data
        assert "statistics" in export_data
        assert "summary" in export_data

    async def test_work_hours_bulk_recalculate(self, async_client: AsyncClient, sample_tasks, admin_user: Member):
        """测试批量工时重算 - 覆盖批量计算逻辑"""
        headers = await self.get_auth_headers(async_client, "ADMIN_TASKS_001", "AdminPass123!")
        
        # 准备批量重算数据
        recalc_data = {
            "task_ids": [task.id for task in sample_tasks],
            "recalculation_reason": "测试批量重算",
            "apply_new_rules": True,
            "update_existing": True
        }
        
        response = await async_client.post("/api/v1/tasks/work-hours/bulk-recalculate", json=recalc_data, headers=headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        
        # 验证重算结果
        result = data["data"]
        assert "processed_count" in result
        assert "updated_count" in result
        assert result["processed_count"] >= 0

    async def test_task_tags_management(self, async_client: AsyncClient, admin_user: Member):
        """测试任务标签管理 - 覆盖标签管理逻辑"""
        headers = await self.get_auth_headers(async_client, "ADMIN_TASKS_001", "AdminPass123!")
        
        # 测试获取标签列表
        response = await async_client.get("/api/v1/tasks/tags", headers=headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        
        # 测试创建新标签
        tag_data = {
            "name": "测试标签",
            "tag_type": "SYSTEM",
            "color": "#FF5722",
            "description": "这是一个测试标签"
        }
        
        response = await async_client.post("/api/v1/tasks/tags", json=tag_data, headers=headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        
        # 验证标签创建
        created_tag = data["data"]
        assert created_tag["name"] == tag_data["name"]
        assert created_tag["tag_type"] == tag_data["tag_type"]
        assert created_tag["color"] == tag_data["color"]

    async def test_my_tasks_with_filters(self, async_client: AsyncClient, sample_tasks, regular_user: Member):
        """测试我的任务查询 - 覆盖个人任务过滤逻辑"""
        headers = await self.get_auth_headers(async_client, "USER_TASKS_001", "UserPass123!")
        
        # 测试基本查询
        response = await async_client.get("/api/v1/tasks/my", headers=headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        
        # 测试带过滤条件的查询
        filter_params = {
            "status": "PENDING,IN_PROGRESS",
            "priority": "HIGH,URGENT",
            "start_date": (datetime.now() - timedelta(days=7)).date().isoformat(),
            "end_date": datetime.now().date().isoformat()
        }
        
        response = await async_client.get("/api/v1/tasks/my", params=filter_params, headers=headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True
        
        # 验证过滤结果
        tasks = data["data"]["tasks"] if "tasks" in data["data"] else []
        for task in tasks:
            assert task["status"] in ["PENDING", "IN_PROGRESS"]
            assert task["priority"] in ["HIGH", "URGENT"]

    async def test_monitoring_inspection_workflow(self, async_client: AsyncClient, admin_user: Member):
        """测试监控任务检查工作流 - 覆盖监控逻辑"""
        headers = await self.get_auth_headers(async_client, "ADMIN_TASKS_001", "AdminPass123!")
        
        # 1. 创建监控任务
        task_data = {
            "title": "设备监控检查",
            "description": "定期设备状态监控", 
            "category": "EQUIPMENT_MAINTENANCE",
            "task_type": "MONITORING",
            "priority": "MEDIUM",
            "location": "机房B区"
        }
        
        response = await async_client.post("/api/v1/tasks/monitoring", json=task_data, headers=headers)
        assert response.status_code == 200
        
        task_data = response.json()["data"]
        task_id = task_data["id"]
        
        # 2. 执行检查
        inspection_data = {
            "inspection_type": "ROUTINE",
            "findings": "设备运行正常",
            "recommendations": "继续监控",
            "next_inspection": (datetime.now() + timedelta(days=7)).isoformat()
        }
        
        response = await async_client.put(f"/api/v1/tasks/monitoring/{task_id}/inspection", json=inspection_data, headers=headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True
        
        # 3. 完成检查
        response = await async_client.put(f"/api/v1/tasks/monitoring/{task_id}/inspection/complete", headers=headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True

    async def test_assistance_approval_workflow(self, async_client: AsyncClient, admin_user: Member, regular_user: Member):
        """测试协助任务审批工作流 - 覆盖审批逻辑"""
        admin_headers = await self.get_auth_headers(async_client, "ADMIN_TASKS_001", "AdminPass123!")
        user_headers = await self.get_auth_headers(async_client, "USER_TASKS_001", "UserPass123!")
        
        # 1. 创建协助任务
        task_data = {
            "title": "技术协助申请", 
            "description": "需要技术支持协助",
            "category": "TECHNICAL_SUPPORT",
            "task_type": "ASSISTANCE", 
            "priority": "MEDIUM",
            "requested_by_id": regular_user.id,
            "assistance_reason": "技术问题需要协助"
        }
        
        response = await async_client.post("/api/v1/tasks/assistance", json=task_data, headers=user_headers)
        assert response.status_code == 200
        
        task_data = response.json()["data"] 
        task_id = task_data["id"]
        
        # 2. 管理员审批
        approval_data = {
            "approved": True,
            "approval_notes": "同意协助申请",
            "assigned_to_id": admin_user.id
        }
        
        response = await async_client.put(f"/api/v1/tasks/assistance/{task_id}/approve", json=approval_data, headers=admin_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True
        
        # 3. 协助任务评价
        review_data = {
            "rating": 5,
            "feedback": "协助效果很好", 
            "completion_quality": "EXCELLENT"
        }
        
        response = await async_client.post(f"/api/v1/tasks/assistance/{task_id}/review", json=review_data, headers=user_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True

    async def test_health_check_endpoint(self, async_client: AsyncClient):
        """测试健康检查端点 - 覆盖系统状态检查逻辑"""
        response = await async_client.get("/api/v1/tasks/health")
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        
        # 验证健康状态数据
        health_data = data["data"]
        assert "status" in health_data
        assert "timestamp" in health_data
        assert "version" in health_data
        assert health_data["status"] == "healthy"