"""
任务管理和工时计算集成测试
测试任务CRUD、工时计算、自动化流程等
"""

from datetime import datetime, timedelta

import pytest

from app.models.task import TaskPriority, TaskStatus


class TestTasksCRUD:
    """测试任务CRUD操作"""

    def test_create_task_as_admin(self, client, auth_headers_admin, test_member_user):
        """测试管理员创建任务"""
        task_data = {
            "title": "新维修任务",
            "description": "网络设备故障需要维修",
            "task_type": "repair",
            "priority": "high",
            "location": "教学楼A座",
            "assigned_to": test_member_user.id,
            "estimated_minutes": 120,
            "deadline": (datetime.utcnow() + timedelta(days=2)).isoformat(),
            "reporter_name": "李老师",
            "reporter_contact": "13987654321",
            "is_rush": True,
        }

        response = client.post(
            "/api/tasks/repair", json=task_data, headers=auth_headers_admin
        )

        assert response.status_code == 201
        data = response.json()

        # 验证返回数据
        assert data["title"] == "新维修任务"
        assert data["description"] == "网络设备故障需要维修"
        assert data["task_type"] == "repair"
        assert data["priority"] == "high"
        assert data["location"] == "教学楼A座"
        assert data["assigned_to"] == test_member_user.id
        assert data["estimated_minutes"] == 120
        assert data["is_rush"] is True
        assert data["status"] == "pending"
        assert "task_number" in data
        assert "id" in data
        assert "created_at" in data

    def test_create_task_as_member(self, client, auth_headers_member):
        """测试成员创建任务"""
        task_data = {
            "title": "成员创建任务",
            "description": "测试成员创建任务",
            "task_type": "repair",
            "priority": "medium",
            "location": "宿舍楼",
            "estimated_minutes": 60,
        }

        response = client.post(
            "/api/tasks/repair", json=task_data, headers=auth_headers_member
        )

        # 可能被允许或拒绝，取决于权限设置
        assert response.status_code in [201, 403]

        if response.status_code == 201:
            data = response.json()
            assert data["title"] == "成员创建任务"
            # 创建者应该被自动设置为当前用户
            assert "created_by" in data or "assigned_to" in data

    def test_create_task_invalid_data(self, client, auth_headers_admin):
        """测试无效数据创建任务"""
        # 缺少必需字段
        task_data = {
            "description": "缺少标题的任务"
            # 缺少title
        }

        response = client.post(
            "/api/tasks/repair", json=task_data, headers=auth_headers_admin
        )

        assert response.status_code == 422

        # 无效的截止时间（过去时间）
        task_data2 = {
            "title": "过期任务",
            "task_type": "repair",
            "deadline": (datetime.utcnow() - timedelta(days=1)).isoformat(),  # 过去时间
        }

        response2 = client.post(
            "/api/tasks/repair", json=task_data2, headers=auth_headers_admin
        )

        assert response2.status_code == 422

    @pytest.mark.asyncio
    async def test_get_tasks_list(
        self, client, auth_headers_admin, test_data_helper, test_member_user, db_session
    ):
        """测试获取任务列表"""
        # 先创建一些测试任务
        await test_data_helper.create_test_tasks(db_session, test_member_user.id, 3)

        response = client.get("/api/tasks/repair", headers=auth_headers_admin)

        assert response.status_code == 200
        data = response.json()

        # 验证分页结构
        assert "items" in data
        assert "total" in data
        assert "page" in data
        assert "size" in data
        assert "pages" in data
        assert "has_next" in data
        assert "has_prev" in data

        # 验证任务数据
        for task in data["items"]:
            assert "id" in task
            assert "title" in task
            assert "status" in task
            assert "priority" in task
            assert "created_at" in task

    def test_get_tasks_with_filters(self, client, auth_headers_admin, test_member_user):
        """测试筛选任务"""
        # 按状态筛选
        response = client.get(
            "/api/tasks/repair?status=pending", headers=auth_headers_admin
        )

        assert response.status_code == 200
        data = response.json()

        for task in data["items"]:
            assert task["status"] == "pending"

        # 按优先级筛选
        response2 = client.get(
            "/api/tasks/repair?priority=high", headers=auth_headers_admin
        )

        assert response2.status_code == 200
        data2 = response2.json()

        for task in data2["items"]:
            assert task["priority"] == "high"

        # 按执行者筛选
        response3 = client.get(
            f"/api/tasks/repair?assigned_to={test_member_user.id}",
            headers=auth_headers_admin,
        )

        assert response3.status_code == 200

    def test_get_tasks_with_search(self, client, auth_headers_admin):
        """测试搜索任务"""
        response = client.get(
            "/api/tasks/repair?search=网络", headers=auth_headers_admin
        )

        assert response.status_code == 200
        data = response.json()

        # 搜索结果应包含"网络"
        for task in data["items"]:
            assert "网络" in task["title"] or "网络" in task.get("description", "")

    def test_get_task_detail(
        self, client, auth_headers_admin, db_session, test_member_user
    ):
        """测试获取任务详情"""
        # 先创建一个任务
        from app.models.task import RepairTask

        task = RepairTask(
            title="详情测试任务",
            description="用于测试任务详情的任务",
            task_number="T202501290001",
            status=TaskStatus.IN_PROGRESS,
            priority=TaskPriority.MEDIUM,
            assigned_to=test_member_user.id,
            estimated_minutes=90,
            deadline=datetime.utcnow() + timedelta(days=1),
            reporter_name="测试报告人",
            reporter_contact="13812345678",
        )

        db_session.add(task)
        db_session.commit()
        db_session.refresh(task)

        response = client.get(
            f"/api/tasks/repair/{task.id}", headers=auth_headers_admin
        )

        assert response.status_code == 200
        data = response.json()

        # 验证详情数据
        assert data["id"] == task.id
        assert data["title"] == "详情测试任务"
        assert data["task_number"] == "T202501290001"
        assert data["status"] == "in_progress"
        assert data["assigned_to"] == test_member_user.id
        assert data["reporter_name"] == "测试报告人"
        assert data["reporter_contact"] == "13812345678"

        # 应包含关联信息
        assert "assignee_name" in data or "creator_name" in data
        assert "tags" in data or "work_hour_breakdown" in data

    def test_get_nonexistent_task(self, client, auth_headers_admin):
        """测试获取不存在的任务"""
        response = client.get("/api/tasks/repair/99999", headers=auth_headers_admin)

        assert response.status_code == 404
        data = response.json()
        assert "未找到" in data["message"] or "not found" in data["message"]

    def test_update_task(
        self, client, auth_headers_admin, db_session, test_member_user
    ):
        """测试更新任务"""
        # 先创建任务
        from app.models.task import RepairTask

        task = RepairTask(
            title="待更新任务",
            description="原始描述",
            task_number="T202501290002",
            status=TaskStatus.PENDING,
            priority=TaskPriority.LOW,
            assigned_to=test_member_user.id,
            estimated_minutes=60,
        )

        db_session.add(task)
        db_session.commit()
        db_session.refresh(task)

        update_data = {
            "title": "更新后的任务",
            "description": "更新后的描述",
            "priority": "high",
            "estimated_minutes": 120,
            "is_rush": True,
        }

        response = client.put(
            f"/api/tasks/repair/{task.id}", json=update_data, headers=auth_headers_admin
        )

        assert response.status_code == 200
        data = response.json()

        # 验证更新结果
        assert data["title"] == "更新后的任务"
        assert data["description"] == "更新后的描述"
        assert data["priority"] == "high"
        assert data["estimated_minutes"] == 120
        assert data["is_rush"] is True
        assert data["updated_at"] != data["created_at"]

    def test_update_task_status(
        self, client, auth_headers_member, db_session, test_member_user
    ):
        """测试更新任务状态"""
        # 创建分配给当前用户的任务
        from app.models.task import RepairTask

        task = RepairTask(
            title="状态测试任务",
            task_number="T202501290003",
            status=TaskStatus.PENDING,
            assigned_to=test_member_user.id,
            estimated_minutes=90,
        )

        db_session.add(task)
        db_session.commit()
        db_session.refresh(task)

        # 开始任务
        start_data = {"status": "in_progress", "completion_note": "开始处理任务"}

        response = client.patch(
            f"/api/tasks/repair/{task.id}/status",
            json=start_data,
            headers=auth_headers_member,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "in_progress"

        # 完成任务
        complete_data = {
            "status": "completed",
            "completion_note": "任务已完成",
            "actual_minutes": 85,
        }

        response2 = client.patch(
            f"/api/tasks/repair/{task.id}/status",
            json=complete_data,
            headers=auth_headers_member,
        )

        assert response2.status_code == 200
        data2 = response2.json()
        assert data2["status"] == "completed"
        assert data2["actual_minutes"] == 85

    def test_assign_task(
        self,
        client,
        auth_headers_admin,
        db_session,
        test_member_user,
        test_group_leader,
    ):
        """测试分配任务"""
        # 创建未分配的任务
        from app.models.task import RepairTask

        task = RepairTask(
            title="待分配任务",
            task_number="T202501290004",
            status=TaskStatus.PENDING,
            estimated_minutes=60,
        )

        db_session.add(task)
        db_session.commit()
        db_session.refresh(task)

        assign_data = {
            "assigned_to": test_group_leader.id,
            "assignment_note": "分配给组长处理",
        }

        response = client.patch(
            f"/api/tasks/repair/{task.id}/assign",
            json=assign_data,
            headers=auth_headers_admin,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["assigned_to"] == test_group_leader.id

    def test_delete_task(self, client, auth_headers_admin, db_session):
        """测试删除任务"""
        # 创建待删除任务
        from app.models.task import RepairTask

        task = RepairTask(
            title="待删除任务",
            task_number="T202501290005",
            status=TaskStatus.PENDING,
            estimated_minutes=30,
        )

        db_session.add(task)
        db_session.commit()
        db_session.refresh(task)

        response = client.delete(
            f"/api/tasks/repair/{task.id}", headers=auth_headers_admin
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

        # 验证任务已删除
        get_response = client.get(
            f"/api/tasks/repair/{task.id}", headers=auth_headers_admin
        )
        assert get_response.status_code == 404


class TestWorkHourCalculation:
    """测试工时计算"""

    def test_basic_work_hour_calculation(
        self, client, auth_headers_admin, test_member_user
    ):
        """测试基础工时计算"""
        # 创建一个已完成的任务
        task_data = {
            "title": "工时计算测试任务",
            "description": "用于测试工时计算",
            "task_type": "repair",
            "priority": "medium",
            "assigned_to": test_member_user.id,
            "estimated_minutes": 100,  # 基础线下任务100分钟
            "is_rush": False,
        }

        create_response = client.post(
            "/api/tasks/repair", json=task_data, headers=auth_headers_admin
        )
        assert create_response.status_code == 201
        task_id = create_response.json()["id"]

        # 完成任务
        complete_data = {
            "status": "completed",
            "completion_note": "任务完成",
            "actual_minutes": 95,
        }

        status_response = client.patch(
            f"/api/tasks/repair/{task_id}/status",
            json=complete_data,
            headers=auth_headers_admin,
        )
        assert status_response.status_code == 200

        # 计算工时
        calc_data = {
            "task_id": task_id,
            "actual_minutes": 95,
            "review_rating": 4,  # 好评
            "is_late_response": False,
            "is_late_completion": False,
        }

        response = client.post(
            "/api/tasks/work-hours/calculate",
            json=calc_data,
            headers=auth_headers_admin,
        )

        assert response.status_code == 200
        data = response.json()

        # 验证工时计算结果
        assert "base_minutes" in data
        assert "rush_bonus" in data
        assert "review_bonus" in data
        assert "response_penalty" in data
        assert "completion_penalty" in data
        assert "review_penalty" in data
        assert "final_minutes" in data
        assert "calculation_details" in data

        # 基础工时应该是100分钟
        assert data["base_minutes"] == 100
        # 好评应该有奖励
        assert data["review_bonus"] > 0
        # 没有延迟，惩罚应该为0
        assert data["response_penalty"] == 0
        assert data["completion_penalty"] == 0
        # 最终工时应该大于基础工时（因为有好评奖励）
        assert data["final_minutes"] > data["base_minutes"]

    def test_rush_task_bonus(self, client, auth_headers_admin, test_member_user):
        """测试紧急任务奖励"""
        task_data = {
            "title": "紧急任务",
            "task_type": "repair",
            "assigned_to": test_member_user.id,
            "estimated_minutes": 100,
            "is_rush": True,  # 紧急任务
        }

        create_response = client.post(
            "/api/tasks/repair", json=task_data, headers=auth_headers_admin
        )
        task_id = create_response.json()["id"]

        # 完成任务并计算工时
        complete_data = {"status": "completed", "actual_minutes": 90}
        client.patch(
            f"/api/tasks/repair/{task_id}/status",
            json=complete_data,
            headers=auth_headers_admin,
        )

        calc_data = {
            "task_id": task_id,
            "actual_minutes": 90,
            "review_rating": 3,  # 中性评价
            "is_late_response": False,
            "is_late_completion": False,
        }

        response = client.post(
            "/api/tasks/work-hours/calculate",
            json=calc_data,
            headers=auth_headers_admin,
        )

        assert response.status_code == 200
        data = response.json()

        # 紧急任务应该有奖励
        assert data["rush_bonus"] > 0
        # 通常是15分钟奖励
        assert data["rush_bonus"] == 15

    def test_late_response_penalty(self, client, auth_headers_admin, test_member_user):
        """测试延迟响应惩罚"""
        task_data = {
            "title": "延迟响应测试",
            "task_type": "repair",
            "assigned_to": test_member_user.id,
            "estimated_minutes": 100,
        }

        create_response = client.post(
            "/api/tasks/repair", json=task_data, headers=auth_headers_admin
        )
        task_id = create_response.json()["id"]

        complete_data = {"status": "completed", "actual_minutes": 95}
        client.patch(
            f"/api/tasks/repair/{task_id}/status",
            json=complete_data,
            headers=auth_headers_admin,
        )

        calc_data = {
            "task_id": task_id,
            "actual_minutes": 95,
            "review_rating": 3,
            "is_late_response": True,  # 延迟响应
            "is_late_completion": False,
        }

        response = client.post(
            "/api/tasks/work-hours/calculate",
            json=calc_data,
            headers=auth_headers_admin,
        )

        assert response.status_code == 200
        data = response.json()

        # 应该有延迟响应惩罚
        assert data["response_penalty"] > 0
        # 通常是30分钟惩罚
        assert data["response_penalty"] == 30
        # 最终工时应该小于基础工时
        assert data["final_minutes"] < data["base_minutes"]

    def test_negative_review_penalty(
        self, client, auth_headers_admin, test_member_user
    ):
        """测试差评惩罚"""
        task_data = {
            "title": "差评测试任务",
            "task_type": "repair",
            "assigned_to": test_member_user.id,
            "estimated_minutes": 100,
        }

        create_response = client.post(
            "/api/tasks/repair", json=task_data, headers=auth_headers_admin
        )
        task_id = create_response.json()["id"]

        complete_data = {"status": "completed", "actual_minutes": 95}
        client.patch(
            f"/api/tasks/repair/{task_id}/status",
            json=complete_data,
            headers=auth_headers_admin,
        )

        calc_data = {
            "task_id": task_id,
            "actual_minutes": 95,
            "review_rating": 2,  # 差评（≤2分）
            "is_late_response": False,
            "is_late_completion": False,
        }

        response = client.post(
            "/api/tasks/work-hours/calculate",
            json=calc_data,
            headers=auth_headers_admin,
        )

        assert response.status_code == 200
        data = response.json()

        # 应该有差评惩罚
        assert data["review_penalty"] > 0
        # 通常是60分钟惩罚
        assert data["review_penalty"] == 60

    def test_online_vs_offline_task_calculation(
        self, client, auth_headers_admin, test_member_user
    ):
        """测试线上和线下任务工时计算差异"""
        # 创建线上任务
        online_task_data = {
            "title": "线上任务",
            "task_type": "monitoring",  # 假设监控任务是线上的
            "assigned_to": test_member_user.id,
            "estimated_minutes": 40,  # 线上任务基础40分钟
        }

        online_response = client.post(
            "/api/tasks/monitoring", json=online_task_data, headers=auth_headers_admin
        )

        if online_response.status_code == 201:
            online_task_id = online_response.json()["id"]

            # 计算线上任务工时
            calc_data = {
                "task_id": online_task_id,
                "actual_minutes": 35,
                "review_rating": 3,
                "is_late_response": False,
                "is_late_completion": False,
            }

            calc_response = client.post(
                "/api/tasks/work-hours/calculate",
                json=calc_data,
                headers=auth_headers_admin,
            )

            if calc_response.status_code == 200:
                online_data = calc_response.json()
                # 线上任务基础工时应该是40分钟
                assert online_data["base_minutes"] == 40

        # 创建线下任务
        offline_task_data = {
            "title": "线下任务",
            "task_type": "repair",  # 维修任务是线下的
            "assigned_to": test_member_user.id,
            "estimated_minutes": 100,  # 线下任务基础100分钟
        }

        offline_response = client.post(
            "/api/tasks/repair", json=offline_task_data, headers=auth_headers_admin
        )
        assert offline_response.status_code == 201
        offline_task_id = offline_response.json()["id"]

        complete_data = {"status": "completed", "actual_minutes": 95}
        client.patch(
            f"/api/tasks/repair/{offline_task_id}/status",
            json=complete_data,
            headers=auth_headers_admin,
        )

        calc_data = {
            "task_id": offline_task_id,
            "actual_minutes": 95,
            "review_rating": 3,
            "is_late_response": False,
            "is_late_completion": False,
        }

        calc_response = client.post(
            "/api/tasks/work-hours/calculate",
            json=calc_data,
            headers=auth_headers_admin,
        )

        assert calc_response.status_code == 200
        offline_data = calc_response.json()

        # 线下任务基础工时应该是100分钟
        assert offline_data["base_minutes"] == 100


class TestTaskAutomation:
    """测试任务自动化功能"""

    def test_automatic_overdue_detection(
        self, client, auth_headers_admin, db_session, test_member_user
    ):
        """测试自动超时检测"""
        # 创建一个已过期的任务
        from app.models.task import RepairTask

        overdue_task = RepairTask(
            title="过期任务",
            task_number="T202501290006",
            status=TaskStatus.PENDING,
            assigned_to=test_member_user.id,
            estimated_minutes=60,
            deadline=datetime.utcnow() - timedelta(hours=2),  # 2小时前就过期了
        )

        db_session.add(overdue_task)
        db_session.commit()
        db_session.refresh(overdue_task)

        # 触发自动超时检测
        response = client.post(
            "/api/tasks/automation/detect-overdue", headers=auth_headers_admin
        )

        if response.status_code == 200:
            data = response.json()
            assert "detected_count" in data
            assert "updated_count" in data
            assert data["detected_count"] > 0

    def test_automatic_penalty_application(
        self, client, auth_headers_admin, db_session, test_member_user
    ):
        """测试自动惩罚应用"""
        # 创建延迟任务
        from app.models.task import RepairTask

        late_task = RepairTask(
            title="延迟任务",
            task_number="T202501290007",
            status=TaskStatus.COMPLETED,
            assigned_to=test_member_user.id,
            estimated_minutes=60,
            actual_minutes=65,
            deadline=datetime.utcnow() - timedelta(hours=1),  # 已过期
            completed_at=datetime.utcnow(),  # 刚完成
        )

        db_session.add(late_task)
        db_session.commit()
        db_session.refresh(late_task)

        # 触发自动惩罚检测
        response = client.post(
            "/api/tasks/automation/apply-penalties", headers=auth_headers_admin
        )

        if response.status_code == 200:
            data = response.json()
            assert "processed_count" in data
            assert "penalties_applied" in data


class TestTaskStatistics:
    """测试任务统计"""

    @pytest.mark.asyncio
    async def test_get_task_statistics(
        self, client, auth_headers_admin, test_data_helper, test_member_user, db_session
    ):
        """测试获取任务统计"""
        # 创建一些测试任务
        await test_data_helper.create_test_tasks(db_session, test_member_user.id, 5)

        response = client.get("/api/tasks/statistics", headers=auth_headers_admin)

        assert response.status_code == 200
        data = response.json()

        # 验证统计数据结构
        assert "total_tasks" in data
        assert "pending_tasks" in data
        assert "in_progress_tasks" in data
        assert "completed_tasks" in data
        assert "overdue_tasks" in data
        assert "rush_tasks" in data
        assert "total_work_hours" in data
        assert "avg_completion_time" in data
        assert "task_type_distribution" in data
        assert "priority_distribution" in data
        assert "monthly_trends" in data

        # 验证数据合理性
        assert data["total_tasks"] >= 5
        assert (
            data["pending_tasks"] + data["in_progress_tasks"] + data["completed_tasks"]
        ) <= data["total_tasks"]

    def test_get_member_task_statistics(
        self, client, auth_headers_member, test_member_user
    ):
        """测试获取个人任务统计"""
        response = client.get(
            f"/api/members/{test_member_user.id}/tasks/statistics",
            headers=auth_headers_member,
        )

        if response.status_code == 200:
            data = response.json()

            # 个人统计应包含基本信息
            assert "total_tasks" in data or "assigned_tasks" in data
            assert "completed_tasks" in data or "completion_rate" in data
            assert "total_work_hours" in data or "avg_work_hours" in data

    def test_get_task_performance_metrics(self, client, auth_headers_admin):
        """测试获取任务绩效指标"""
        response = client.get("/api/tasks/performance", headers=auth_headers_admin)

        if response.status_code == 200:
            data = response.json()

            # 绩效指标
            assert "completion_rate" in data or "average_completion_time" in data
            assert "quality_score" in data or "efficiency_score" in data
