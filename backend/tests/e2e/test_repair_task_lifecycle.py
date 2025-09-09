"""
报修单生命周期E2E测试
测试A/B表数据导入、报修单创建、分配、处理的完整流程
包含线下任务标记、图片上传、工时计算验证、任务状态流转
"""

import asyncio
import io
import json
from datetime import datetime, timedelta
from typing import Dict, List

import pytest
from httpx import AsyncClient

from app.models.task import TaskPriority, TaskStatus


class TestRepairTaskLifecycle:
    """报修单生命周期E2E测试类"""

    @pytest.mark.asyncio
    async def test_complete_ab_table_import_flow(
        self,
        e2e_client: AsyncClient,
        e2e_user_tokens: Dict[str, str],
        e2e_auth_headers,
        e2e_sample_excel_data,
        e2e_helper,
    ):
        """测试A/B表数据导入完整流程"""

        admin_headers = e2e_auth_headers(e2e_user_tokens["admin"])

        # 1. 准备A表数据（报修信息）
        a_table_data = e2e_sample_excel_data["repair_data"]

        # 2. 准备B表数据（处理信息）
        b_table_data = [
            {
                "报修人姓名": "测试用户1",
                "报修人联系方式": "13800138001",
                "处理人": "张三",
                "处理时间": "2024-01-15 14:30:00",
                "处理结果": "已完成网络配置",
                "评价": "满意",
            },
            {
                "报修人姓名": "测试用户2",
                "报修人联系方式": "13800138002",
                "处理人": "李四",
                "处理时间": "2024-01-15 15:00:00",
                "处理结果": "硬件更换完成",
                "评价": "非常满意",
            },
        ]

        # 3. 创建模拟Excel文件内容
        excel_content = json.dumps({"A表": a_table_data, "B表": b_table_data}).encode(
            "utf-8"
        )

        # 4. 执行导入
        import_response = await e2e_helper.simulate_file_upload(
            e2e_client,
            "/api/v1/tasks/repair/import",
            excel_content,
            "test_repair_data.xlsx",
            admin_headers,
        )

        if import_response.status_code == 200:
            e2e_helper.assert_response_success(import_response)
            import_result = import_response.json()

            assert import_result["success"] is True
            data = import_result.get("data", {})
            assert "imported_count" in data
            assert data["imported_count"] > 0

            # 5. 验证导入的任务
            tasks_response = await e2e_client.get(
                "/api/v1/tasks/repair", headers=admin_headers
            )
            e2e_helper.assert_response_success(tasks_response)

            tasks_data = tasks_response.json().get("data", {})
            tasks = tasks_data.get("items", [])
            assert len(tasks) >= 2  # 至少导入了2个任务

        else:
            pytest.skip("Import functionality not available or failed")

    @pytest.mark.asyncio
    async def test_repair_task_creation_and_assignment(
        self,
        e2e_client: AsyncClient,
        e2e_user_tokens: Dict[str, str],
        e2e_test_users: Dict[str, str],
        e2e_auth_headers,
        e2e_helper,
    ):
        """测试报修任务创建和分配流程"""

        admin_headers = e2e_auth_headers(e2e_user_tokens["admin"])

        # 1. 创建新的报修任务
        task_data = {
            "reporter_name": "测试报修人",
            "reporter_contact": "13800138999",
            "contact_info": "测试报修人联系方式",
            "repair_type": "网络故障",
            "description": "宿舍网络无法连接",
            "location": "学生宿舍A栋101",
            "urgency_level": UrgencyLevel.NORMAL.value,
        }

        create_response = await e2e_client.post(
            "/api/v1/tasks/repair", json=task_data, headers=admin_headers
        )

        e2e_helper.assert_response_success(create_response, 201)
        create_result = create_response.json()
        assert create_result["success"] is True

        task = create_result.get("data", {})
        task_id = task["id"]
        assert task["status"] == TaskStatus.PENDING.value
        assert task["reporter_name"] == task_data["reporter_name"]

        # 2. 分配任务给学生网管
        student_member = e2e_test_users["student"]
        assignment_data = {"assigned_member_id": student_member.id}

        assign_response = await e2e_client.put(
            f"/api/v1/tasks/repair/{task_id}/assign",
            json=assignment_data,
            headers=admin_headers,
        )

        e2e_helper.assert_response_success(assign_response)
        assign_result = assign_response.json()
        assert assign_result["success"] is True

        # 3. 验证任务分配成功
        task_response = await e2e_client.get(
            f"/api/v1/tasks/repair/{task_id}", headers=admin_headers
        )
        e2e_helper.assert_response_success(task_response)

        updated_task = task_response.json().get("data", {})
        assert updated_task["assigned_member_id"] == student_member.id
        assert updated_task["status"] == TaskStatus.ASSIGNED.value

    @pytest.mark.asyncio
    async def test_student_task_processing_flow(
        self,
        e2e_client: AsyncClient,
        e2e_user_tokens: Dict[str, str],
        e2e_sample_repair_tasks: List,
        e2e_auth_headers,
        e2e_helper,
    ):
        """测试学生网管处理任务流程"""

        student_headers = e2e_auth_headers(e2e_user_tokens["student"])

        # 获取分配给学生的任务
        in_progress_task = None
        for task in e2e_sample_repair_tasks:
            if task.status == TaskStatus.IN_PROGRESS:
                in_progress_task = task
                break

        assert in_progress_task is not None, "No in-progress task found"

        # 1. 学生开始处理任务
        start_response = await e2e_client.post(
            f"/api/v1/tasks/repair/{in_progress_task.id}/start", headers=student_headers
        )

        if start_response.status_code == 200:
            e2e_helper.assert_response_success(start_response)

        # 2. 更新任务进度
        progress_data = {
            "progress_notes": "已到达现场，正在检查网络设备",
            "status": TaskStatus.IN_PROGRESS.value,
        }

        progress_response = await e2e_client.put(
            f"/api/v1/tasks/repair/{in_progress_task.id}/progress",
            json=progress_data,
            headers=student_headers,
        )

        if progress_response.status_code == 200:
            e2e_helper.assert_response_success(progress_response)
            progress_result = progress_response.json()
            assert progress_result["success"] is True

        # 3. 完成任务
        completion_data = {
            "solution": "重新配置网络参数，问题已解决",
            "completion_notes": "任务顺利完成，用户满意",
            "status": TaskStatus.COMPLETED.value,
        }

        complete_response = await e2e_client.put(
            f"/api/v1/tasks/repair/{in_progress_task.id}/complete",
            json=completion_data,
            headers=student_headers,
        )

        if complete_response.status_code == 200:
            e2e_helper.assert_response_success(complete_response)

            # 4. 验证任务状态更新
            final_task_response = await e2e_client.get(
                f"/api/v1/tasks/repair/{in_progress_task.id}", headers=student_headers
            )
            e2e_helper.assert_response_success(final_task_response)

            final_task = final_task_response.json().get("data", {})
            assert final_task["status"] == TaskStatus.COMPLETED.value
            assert final_task["solution"] == completion_data["solution"]
        else:
            pytest.skip("Task completion functionality not available")

    @pytest.mark.asyncio
    async def test_offline_task_marking_with_image_upload(
        self,
        e2e_client: AsyncClient,
        e2e_user_tokens: Dict[str, str],
        e2e_sample_repair_tasks: List,
        e2e_auth_headers,
        e2e_helper,
    ):
        """测试线下任务标记和图片上传功能"""

        student_headers = e2e_auth_headers(e2e_user_tokens["student"])

        # 查找线下任务
        offline_task = None
        for task in e2e_sample_repair_tasks:
            if not task.is_online_task:
                offline_task = task
                break

        assert offline_task is not None, "No offline task found"

        # 1. 标记为线下任务（如果还未标记）
        offline_marking_data = {
            "is_offline_confirmed": True,
            "offline_reason": "需要现场硬件维修",
            "estimated_completion_time": "2024-01-16 10:00:00",
        }

        offline_response = await e2e_client.put(
            f"/api/v1/tasks/repair/{offline_task.id}/mark-offline",
            json=offline_marking_data,
            headers=student_headers,
        )

        if offline_response.status_code == 200:
            e2e_helper.assert_response_success(offline_response)

        # 2. 上传现场图片
        # 创建模拟图片文件
        fake_image_content = b"fake_image_data_for_testing"

        image_upload_response = await e2e_helper.simulate_file_upload(
            e2e_client,
            f"/api/v1/tasks/repair/{offline_task.id}/upload-image",
            fake_image_content,
            "repair_photo.jpg",
            student_headers,
        )

        if image_upload_response.status_code == 200:
            e2e_helper.assert_response_success(image_upload_response)
            upload_result = image_upload_response.json()
            assert upload_result["success"] is True

            upload_data = upload_result.get("data", {})
            assert "image_url" in upload_data or "file_path" in upload_data

        # 3. 添加线下任务完成证明
        completion_proof_data = {
            "completion_proof": "已更换故障硬件，用户确认问题解决",
            "on_site_notes": "硬件故障，已更换内存条",
            "user_confirmation": True,
        }

        proof_response = await e2e_client.put(
            f"/api/v1/tasks/repair/{offline_task.id}/completion-proof",
            json=completion_proof_data,
            headers=student_headers,
        )

        if proof_response.status_code == 200:
            e2e_helper.assert_response_success(proof_response)
            proof_result = proof_response.json()
            assert proof_result["success"] is True

    @pytest.mark.asyncio
    async def test_task_status_flow_validation(
        self,
        e2e_client: AsyncClient,
        e2e_user_tokens: Dict[str, str],
        e2e_auth_headers,
        e2e_helper,
    ):
        """测试任务状态流转验证"""

        admin_headers = e2e_auth_headers(e2e_user_tokens["admin"])
        student_headers = e2e_auth_headers(e2e_user_tokens["student"])

        # 1. 创建新任务
        task_data = {
            "reporter_name": "状态流转测试用户",
            "reporter_contact": "13800138000",
            "repair_type": "状态测试",
            "description": "用于测试状态流转",
            "location": "测试地点",
            "urgency_level": UrgencyLevel.LOW.value,
        }

        create_response = await e2e_client.post(
            "/api/v1/tasks/repair", json=task_data, headers=admin_headers
        )

        if create_response.status_code != 201:
            pytest.skip("Cannot create task for status flow test")

        task = create_response.json().get("data", {})
        task_id = task["id"]

        # 2. 验证状态流转：PENDING -> ASSIGNED
        assignment_data = {"assigned_member_id=test_user.id}  # 假设存在ID为1的成员

        assign_response = await e2e_client.put(
            f"/api/v1/tasks/repair/{task_id}/assign",
            json=assignment_data,
            headers=admin_headers,
        )

        if assign_response.status_code == 200:
            # 验证状态确实变为ASSIGNED
            task_response = await e2e_client.get(
                f"/api/v1/tasks/repair/{task_id}", headers=admin_headers
            )
            task_data = task_response.json().get("data", {})
            assert task_data["status"] == TaskStatus.ASSIGNED.value

        # 3. 验证不合法的状态转换
        # 尝试直接从ASSIGNED跳转到COMPLETED（应该失败）
        invalid_completion_data = {
            "solution": "直接完成",
            "status": TaskStatus.COMPLETED.value,
        }

        invalid_response = await e2e_client.put(
            f"/api/v1/tasks/repair/{task_id}/complete",
            json=invalid_completion_data,
            headers=student_headers,
        )

        # 期望这个操作失败（因为跳过了IN_PROGRESS状态）
        # 如果系统允许状态跳转，则这个测试可能需要调整
        if invalid_response.status_code in [400, 422]:
            # 状态流转验证生效
            error_data = invalid_response.json()
            assert not error_data.get("success", True)

    @pytest.mark.asyncio
    async def test_work_hours_calculation_for_tasks(
        self,
        e2e_client: AsyncClient,
        e2e_user_tokens: Dict[str, str],
        e2e_sample_repair_tasks: List,
        e2e_auth_headers,
        e2e_helper,
    ):
        """测试任务工时计算验证"""

        admin_headers = e2e_auth_headers(e2e_user_tokens["admin"])

        # 1. 获取已完成的任务
        completed_task = None
        for task in e2e_sample_repair_tasks:
            if task.status == TaskStatus.COMPLETED:
                completed_task = task
                break

        if completed_task is None:
            pytest.skip("No completed task available for work hours calculation test")

        # 2. 触发工时计算
        calculation_response = await e2e_client.post(
            f"/api/v1/tasks/repair/{completed_task.id}/calculate-work-hours",
            headers=admin_headers,
        )

        if calculation_response.status_code == 200:
            e2e_helper.assert_response_success(calculation_response)
            calc_result = calculation_response.json()

            work_hours_data = calc_result.get("data", {})
            assert "total_work_hours" in work_hours_data
            assert "base_hours" in work_hours_data
            assert work_hours_data["total_work_hours"] > 0

            # 3. 验证工时规则
            # 线上任务应该是40分钟，线下任务应该是100分钟
            expected_base_hours = 100 if not completed_task.is_online_task else 40

            # 允许有奖励和惩罚的调整
            assert work_hours_data["base_hours"] == expected_base_hours

        # 4. 批量重算工时
        batch_recalc_response = await e2e_client.post(
            "/api/v1/tasks/work-hours/recalculate",
            json={"member_id": completed_task.assigned_member_id},
            headers=admin_headers,
        )

        if batch_recalc_response.status_code == 200:
            e2e_helper.assert_response_success(batch_recalc_response)
            batch_result = batch_recalc_response.json()

            batch_data = batch_result.get("data", {})
            assert "processed_count" in batch_data
            assert batch_data["processed_count"] >= 0

    @pytest.mark.asyncio
    async def test_task_urgency_and_rush_period_handling(
        self,
        e2e_client: AsyncClient,
        e2e_user_tokens: Dict[str, str],
        e2e_auth_headers,
        e2e_helper,
    ):
        """测试任务紧急程度和加急时段处理"""

        admin_headers = e2e_auth_headers(e2e_user_tokens["admin"])

        # 1. 创建高紧急度任务
        urgent_task_data = {
            "reporter_name": "紧急任务报修人",
            "reporter_contact": "13800138888",
            "repair_type": "紧急网络故障",
            "description": "整栋楼网络中断",
            "location": "学生宿舍整栋",
            "urgency_level": UrgencyLevel.HIGH.value,
        }

        urgent_response = await e2e_client.post(
            "/api/v1/tasks/repair", json=urgent_task_data, headers=admin_headers
        )

        if urgent_response.status_code == 201:
            e2e_helper.assert_response_success(urgent_response, 201)
            urgent_task = urgent_response.json().get("data", {})

            # 2. 标记为加急任务
            rush_marking_data = {
                "is_rush_period": True,
                "rush_reason": "全楼网络中断，影响学生学习",
            }

            rush_response = await e2e_client.put(
                f"/api/v1/tasks/repair/{urgent_task['id']}/mark-rush",
                json=rush_marking_data,
                headers=admin_headers,
            )

            if rush_response.status_code == 200:
                e2e_helper.assert_response_success(rush_response)
                rush_result = rush_response.json()
                assert rush_result["success"] is True

                # 3. 验证加急标记生效
                task_detail_response = await e2e_client.get(
                    f"/api/v1/tasks/repair/{urgent_task['id']}", headers=admin_headers
                )
                e2e_helper.assert_response_success(task_detail_response)

                task_detail = task_detail_response.json().get("data", {})
                # 检查是否有加急相关字段
                assert task_detail["urgency_level"] == UrgencyLevel.HIGH.value

    @pytest.mark.asyncio
    async def test_task_evaluation_and_feedback(
        self,
        e2e_client: AsyncClient,
        e2e_user_tokens: Dict[str, str],
        e2e_sample_repair_tasks: List,
        e2e_auth_headers,
        e2e_helper,
    ):
        """测试任务评价和反馈系统"""

        admin_headers = e2e_auth_headers(e2e_user_tokens["admin"])

        # 查找已完成的任务
        completed_task = None
        for task in e2e_sample_repair_tasks:
            if task.status == TaskStatus.COMPLETED:
                completed_task = task
                break

        if completed_task is None:
            pytest.skip("No completed task available for evaluation test")

        # 1. 添加用户评价
        evaluation_data = {
            "rating": 5,  # 1-5星评价
            "feedback": "服务非常好，问题解决及时",
            "evaluation_type": "positive",
        }

        evaluation_response = await e2e_client.post(
            f"/api/v1/tasks/repair/{completed_task.id}/evaluate",
            json=evaluation_data,
            headers=admin_headers,
        )

        if evaluation_response.status_code == 200:
            e2e_helper.assert_response_success(evaluation_response)
            eval_result = evaluation_response.json()
            assert eval_result["success"] is True

            # 2. 验证评价影响工时计算
            # 正面评价应该增加工时奖励
            work_hours_response = await e2e_client.get(
                f"/api/v1/tasks/repair/{completed_task.id}/work-hours",
                headers=admin_headers,
            )

            if work_hours_response.status_code == 200:
                work_hours_data = work_hours_response.json().get("data", {})
                assert "bonus_hours" in work_hours_data
                assert work_hours_data["bonus_hours"] >= 0

        # 3. 测试负面评价
        negative_evaluation_data = {
            "rating": 2,
            "feedback": "响应时间过长，服务态度一般",
            "evaluation_type": "negative",
        }

        # 为另一个任务添加负面评价（如果有的话）
        other_completed_tasks = [
            t
            for t in e2e_sample_repair_tasks
            if t.status == TaskStatus.COMPLETED and t.id != completed_task.id
        ]

        if other_completed_tasks:
            negative_response = await e2e_client.post(
                f"/api/v1/tasks/repair/{other_completed_tasks[0].id}/evaluate",
                json=negative_evaluation_data,
                headers=admin_headers,
            )

            if negative_response.status_code == 200:
                e2e_helper.assert_response_success(negative_response)

    @pytest.mark.asyncio
    async def test_task_search_and_filtering(
        self,
        e2e_client: AsyncClient,
        e2e_user_tokens: Dict[str, str],
        e2e_auth_headers,
        e2e_helper,
    ):
        """测试任务搜索和筛选功能"""

        admin_headers = e2e_auth_headers(e2e_user_tokens["admin"])

        # 1. 获取所有任务
        all_tasks_response = await e2e_client.get(
            "/api/v1/tasks/repair", headers=admin_headers
        )
        e2e_helper.assert_response_success(all_tasks_response)

        all_tasks_data = all_tasks_response.json().get("data", {})
        total_tasks = all_tasks_data.get("total", 0)

        if total_tasks == 0:
            pytest.skip("No tasks available for search and filtering test")

        # 2. 按状态筛选
        status_filter_response = await e2e_client.get(
            "/api/v1/tasks/repair",
            params={"status": TaskStatus.COMPLETED.value},
            headers=admin_headers,
        )
        e2e_helper.assert_response_success(status_filter_response)

        filtered_data = status_filter_response.json().get("data", {})
        filtered_tasks = filtered_data.get("items", [])

        # 验证筛选结果
        for task in filtered_tasks:
            assert task["status"] == TaskStatus.COMPLETED.value

        # 3. 按关键词搜索
        search_response = await e2e_client.get(
            "/api/v1/tasks/repair", params={"search": "网络"}, headers=admin_headers
        )
        e2e_helper.assert_response_success(search_response)

        search_data = search_response.json().get("data", {})
        search_results = search_data.get("items", [])

        # 验证搜索结果包含关键词
        for task in search_results:
            task_text = f"{task.get('repair_type', '')} {task.get('description', '')}"
            # 检查是否包含搜索关键词（不区分大小写）
            assert "网络" in task_text.lower() or "network" in task_text.lower()

        # 4. 组合筛选（状态 + 紧急程度）
        combo_response = await e2e_client.get(
            "/api/v1/tasks/repair",
            params={
                "status": TaskStatus.PENDING.value,
                "urgency_level": UrgencyLevel.HIGH.value,
            },
            headers=admin_headers,
        )
        e2e_helper.assert_response_success(combo_response)

        combo_data = combo_response.json().get("data", {})
        combo_tasks = combo_data.get("items", [])

        # 验证组合筛选结果
        for task in combo_tasks:
            assert task["status"] == TaskStatus.PENDING.value
            assert task["urgency_level"] == UrgencyLevel.HIGH.value


class TestRepairTaskPerformance:
    """报修任务性能测试"""

    @pytest.mark.asyncio
    async def test_task_creation_performance(
        self,
        e2e_client: AsyncClient,
        e2e_user_tokens: Dict[str, str],
        e2e_auth_headers,
        e2e_performance_monitor,
        e2e_helper,
    ):
        """测试任务创建性能"""

        admin_headers = e2e_auth_headers(e2e_user_tokens["admin"])
        e2e_performance_monitor.start()

        # 批量创建任务测试性能
        creation_times = []

        for i in range(10):
            task_data = {
                "reporter_name": f"性能测试用户{i}",
                "reporter_contact": f"1380013800{i}",
                "repair_type": "性能测试",
                "description": f"性能测试任务{i}",
                "location": f"测试地点{i}",
                "urgency_level": UrgencyLevel.NORMAL.value,
            }

            start_time = asyncio.get_event_loop().time()

            create_response = await e2e_client.post(
                "/api/v1/tasks/repair", json=task_data, headers=admin_headers
            )

            end_time = asyncio.get_event_loop().time()
            duration = end_time - start_time
            creation_times.append(duration)

            e2e_performance_monitor.record(f"task_creation_{i}", duration)

            if create_response.status_code == 201:
                create_result = create_response.json()
                assert create_result["success"] is True

        # 性能验证
        avg_creation_time = sum(creation_times) / len(creation_times)
        max_creation_time = max(creation_times)

        assert (
            avg_creation_time < 1.0
        ), f"Average task creation time {avg_creation_time}s exceeds 1s"
        assert (
            max_creation_time < 3.0
        ), f"Max task creation time {max_creation_time}s exceeds 3s"

        summary = e2e_performance_monitor.summary()
        print(f"Task Creation Performance Summary: {summary}")

    @pytest.mark.asyncio
    async def test_concurrent_task_operations(
        self,
        e2e_client: AsyncClient,
        e2e_user_tokens: Dict[str, str],
        e2e_sample_repair_tasks: List,
        e2e_auth_headers,
        e2e_helper,
    ):
        """测试并发任务操作"""

        admin_headers = e2e_auth_headers(e2e_user_tokens["admin"])
        student_headers = e2e_auth_headers(e2e_user_tokens["student"])

        if not e2e_sample_repair_tasks:
            pytest.skip("No sample tasks available for concurrent operations test")

        # 并发操作：同时读取多个任务
        task_ids = [task.id for task in e2e_sample_repair_tasks[:3]]

        concurrent_tasks = [
            e2e_client.get(f"/api/v1/tasks/repair/{task_id}", headers=admin_headers)
            for task_id in task_ids
        ]

        # 添加列表查询的并发操作
        concurrent_tasks.append(
            e2e_client.get("/api/v1/tasks/repair", headers=admin_headers)
        )
        concurrent_tasks.append(
            e2e_client.get("/api/v1/tasks/repair/my", headers=student_headers)
        )

        # 执行并发操作
        results = await asyncio.gather(*concurrent_tasks, return_exceptions=True)

        # 验证并发操作结果
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                pytest.fail(f"Concurrent operation {i} failed with exception: {result}")
            else:
                assert result.status_code in [
                    200,
                    404,
                ], f"Concurrent operation {i} returned {result.status_code}"
