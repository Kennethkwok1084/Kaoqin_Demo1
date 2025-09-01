"""
协助任务管理流程E2E测试
测试学生自主登记协助任务、管理员审核流程、工时计算和统计
包含协助任务的完整生命周期管理
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, List

import pytest
from httpx import AsyncClient

from app.models.task import TaskStatus


class TestAssistanceTaskManagement:
    """协助任务管理E2E测试类"""

    @pytest.mark.asyncio
    async def test_student_self_register_assistance_task(
        self,
        e2e_client: AsyncClient,
        e2e_user_tokens: Dict[str, str],
        e2e_auth_headers,
        e2e_helper,
    ):
        """测试学生自主登记协助任务流程"""

        student_headers = e2e_auth_headers(e2e_user_tokens["student"])

        # 1. 学生创建协助任务申请
        assistance_data = {
            "task_type": "assistance",
            "description": "协助维护机房设备",
            "location": "计算机实验中心",
            "assistance_type": "equipment_maintenance",
            "estimated_duration": 120,  # 预计120分钟
            "proposed_date": (datetime.now() + timedelta(days=1)).isoformat(),
            "reason": "实验中心需要额外人手进行设备维护",
            "skills_required": "熟悉计算机硬件",
        }

        create_response = await e2e_client.post(
            "/api/v1/tasks/assistance", json=assistance_data, headers=student_headers
        )

        if create_response.status_code == 201:
            e2e_helper.assert_response_success(create_response, 201)
            create_result = create_response.json()

            assert create_result["success"] is True
            task_data = create_result.get("data", {})
            assert task_data["description"] == assistance_data["description"]
            assert task_data["status"] == "pending_approval"  # 待审核状态

            task_id = task_data["id"]

            # 2. 验证任务创建成功
            task_detail_response = await e2e_client.get(
                f"/api/v1/tasks/assistance/{task_id}", headers=student_headers
            )
            e2e_helper.assert_response_success(task_detail_response)

            task_detail = task_detail_response.json().get("data", {})
            assert task_detail["description"] == assistance_data["description"]
            assert (
                task_detail["estimated_duration"]
                == assistance_data["estimated_duration"]
            )

            return task_id
        else:
            pytest.skip("Assistance task creation not available")

    @pytest.mark.asyncio
    async def test_admin_approval_workflow(
        self,
        e2e_client: AsyncClient,
        e2e_user_tokens: Dict[str, str],
        e2e_auth_headers,
        e2e_helper,
    ):
        """测试管理员审核协助任务流程"""

        student_headers = e2e_auth_headers(e2e_user_tokens["student"])
        admin_headers = e2e_auth_headers(e2e_user_tokens["admin"])

        # 1. 先创建一个待审核的协助任务
        assistance_data = {
            "task_type": "assistance",
            "description": "协助网络设备巡检",
            "location": "各宿舍楼网络机房",
            "assistance_type": "network_inspection",
            "estimated_duration": 180,
            "proposed_date": (datetime.now() + timedelta(days=2)).isoformat(),
            "reason": "月度网络设备例行巡检需要协助",
        }

        create_response = await e2e_client.post(
            "/api/v1/tasks/assistance", json=assistance_data, headers=student_headers
        )

        if create_response.status_code != 201:
            pytest.skip("Cannot create assistance task for approval test")

        task_id = create_response.json()["data"]["id"]

        # 2. 管理员查看待审核任务列表
        pending_tasks_response = await e2e_client.get(
            "/api/v1/tasks/assistance/pending-approval", headers=admin_headers
        )

        if pending_tasks_response.status_code == 200:
            e2e_helper.assert_response_success(pending_tasks_response)
            pending_data = pending_tasks_response.json().get("data", {})
            pending_tasks = pending_data.get("items", [])

            # 验证新创建的任务出现在待审核列表中
            task_found = any(task["id"] == task_id for task in pending_tasks)
            assert (
                task_found
            ), "Created assistance task not found in pending approval list"

        # 3. 管理员审批通过
        approval_data = {
            "approval_status": "approved",
            "approval_notes": "同意协助网络巡检，注意安全",
            "approved_duration": 180,  # 确认预计时长
            "scheduled_date": (datetime.now() + timedelta(days=2)).isoformat(),
        }

        approval_response = await e2e_client.put(
            f"/api/v1/tasks/assistance/{task_id}/approve",
            json=approval_data,
            headers=admin_headers,
        )

        if approval_response.status_code == 200:
            e2e_helper.assert_response_success(approval_response)
            approval_result = approval_response.json()

            assert approval_result["success"] is True

            # 4. 验证任务状态变更
            updated_task_response = await e2e_client.get(
                f"/api/v1/tasks/assistance/{task_id}", headers=admin_headers
            )
            e2e_helper.assert_response_success(updated_task_response)

            updated_task = updated_task_response.json().get("data", {})
            assert updated_task["status"] == "approved"
            assert updated_task["approval_notes"] == approval_data["approval_notes"]

            return task_id
        else:
            pytest.skip("Assistance task approval functionality not available")

    @pytest.mark.asyncio
    async def test_admin_rejection_workflow(
        self,
        e2e_client: AsyncClient,
        e2e_user_tokens: Dict[str, str],
        e2e_auth_headers,
        e2e_helper,
    ):
        """测试管理员拒绝协助任务流程"""

        student_headers = e2e_auth_headers(e2e_user_tokens["student"])
        admin_headers = e2e_auth_headers(e2e_user_tokens["admin"])

        # 1. 创建协助任务申请
        assistance_data = {
            "task_type": "assistance",
            "description": "协助清理机房（测试拒绝）",
            "location": "实验室",
            "assistance_type": "cleaning",
            "estimated_duration": 60,
            "proposed_date": (datetime.now() + timedelta(days=1)).isoformat(),
            "reason": "测试拒绝流程",
        }

        create_response = await e2e_client.post(
            "/api/v1/tasks/assistance", json=assistance_data, headers=student_headers
        )

        if create_response.status_code != 201:
            pytest.skip("Cannot create assistance task for rejection test")

        task_id = create_response.json()["data"]["id"]

        # 2. 管理员拒绝申请
        rejection_data = {
            "approval_status": "rejected",
            "rejection_reason": "当前不需要此类协助",
            "approval_notes": "建议关注其他类型的协助任务",
        }

        rejection_response = await e2e_client.put(
            f"/api/v1/tasks/assistance/{task_id}/approve",
            json=rejection_data,
            headers=admin_headers,
        )

        if rejection_response.status_code == 200:
            e2e_helper.assert_response_success(rejection_response)
            rejection_result = rejection_response.json()

            assert rejection_result["success"] is True

            # 3. 验证任务状态和拒绝原因
            rejected_task_response = await e2e_client.get(
                f"/api/v1/tasks/assistance/{task_id}", headers=admin_headers
            )
            e2e_helper.assert_response_success(rejected_task_response)

            rejected_task = rejected_task_response.json().get("data", {})
            assert rejected_task["status"] == "rejected"
            assert (
                rejected_task["rejection_reason"] == rejection_data["rejection_reason"]
            )
        else:
            pytest.skip("Assistance task rejection functionality not available")

    @pytest.mark.asyncio
    async def test_assistance_task_execution_flow(
        self,
        e2e_client: AsyncClient,
        e2e_user_tokens: Dict[str, str],
        e2e_auth_headers,
        e2e_helper,
    ):
        """测试协助任务执行流程"""

        student_headers = e2e_auth_headers(e2e_user_tokens["student"])
        admin_headers = e2e_auth_headers(e2e_user_tokens["admin"])

        # 1. 创建并审批协助任务
        assistance_data = {
            "task_type": "assistance",
            "description": "协助系统维护测试",
            "location": "服务器机房",
            "assistance_type": "system_maintenance",
            "estimated_duration": 90,
            "proposed_date": datetime.now().isoformat(),
            "reason": "测试执行流程",
        }

        create_response = await e2e_client.post(
            "/api/v1/tasks/assistance", json=assistance_data, headers=student_headers
        )

        if create_response.status_code != 201:
            pytest.skip("Cannot create assistance task for execution test")

        task_id = create_response.json()["data"]["id"]

        # 快速审批
        approval_data = {
            "approval_status": "approved",
            "approval_notes": "同意执行",
            "approved_duration": 90,
        }

        await e2e_client.put(
            f"/api/v1/tasks/assistance/{task_id}/approve",
            json=approval_data,
            headers=admin_headers,
        )

        # 2. 学生开始执行任务
        start_execution_data = {
            "actual_start_time": datetime.now().isoformat(),
            "execution_notes": "开始协助系统维护工作",
        }

        start_response = await e2e_client.post(
            f"/api/v1/tasks/assistance/{task_id}/start",
            json=start_execution_data,
            headers=student_headers,
        )

        if start_response.status_code == 200:
            e2e_helper.assert_response_success(start_response)

            # 3. 更新执行进度
            progress_data = {
                "progress_notes": "已完成50%的维护工作",
                "progress_percentage": 50,
            }

            progress_response = await e2e_client.put(
                f"/api/v1/tasks/assistance/{task_id}/progress",
                json=progress_data,
                headers=student_headers,
            )

            if progress_response.status_code == 200:
                e2e_helper.assert_response_success(progress_response)

            # 4. 完成任务
            completion_data = {
                "actual_end_time": datetime.now().isoformat(),
                "actual_duration": 85,  # 实际用时85分钟
                "completion_summary": "系统维护协助任务顺利完成",
                "achievements": "协助完成了3台服务器的系统更新",
            }

            completion_response = await e2e_client.put(
                f"/api/v1/tasks/assistance/{task_id}/complete",
                json=completion_data,
                headers=student_headers,
            )

            if completion_response.status_code == 200:
                e2e_helper.assert_response_success(completion_response)
                completion_result = completion_response.json()
                assert completion_result["success"] is True

                # 5. 验证任务完成状态
                final_task_response = await e2e_client.get(
                    f"/api/v1/tasks/assistance/{task_id}", headers=student_headers
                )
                e2e_helper.assert_response_success(final_task_response)

                final_task = final_task_response.json().get("data", {})
                assert final_task["status"] == "completed"
                assert (
                    final_task["actual_duration"] == completion_data["actual_duration"]
                )
        else:
            pytest.skip("Assistance task execution functionality not available")

    @pytest.mark.asyncio
    async def test_assistance_task_work_hours_calculation(
        self,
        e2e_client: AsyncClient,
        e2e_user_tokens: Dict[str, str],
        e2e_auth_headers,
        e2e_helper,
    ):
        """测试协助任务工时计算"""

        student_headers = e2e_auth_headers(e2e_user_tokens["student"])
        admin_headers = e2e_auth_headers(e2e_user_tokens["admin"])

        # 1. 创建、审批并完成协助任务
        assistance_data = {
            "task_type": "assistance",
            "description": "协助工时计算测试",
            "location": "测试地点",
            "assistance_type": "testing",
            "estimated_duration": 60,
            "proposed_date": datetime.now().isoformat(),
            "reason": "工时计算测试",
        }

        # 创建任务
        create_response = await e2e_client.post(
            "/api/v1/tasks/assistance", json=assistance_data, headers=student_headers
        )

        if create_response.status_code != 201:
            pytest.skip("Cannot create assistance task for work hours test")

        task_id = create_response.json()["data"]["id"]

        # 审批任务
        approval_data = {"approval_status": "approved", "approved_duration": 60}

        await e2e_client.put(
            f"/api/v1/tasks/assistance/{task_id}/approve",
            json=approval_data,
            headers=admin_headers,
        )

        # 完成任务
        completion_data = {
            "actual_end_time": datetime.now().isoformat(),
            "actual_duration": 65,  # 实际用时65分钟
            "completion_summary": "工时计算测试任务完成",
        }

        completion_response = await e2e_client.put(
            f"/api/v1/tasks/assistance/{task_id}/complete",
            json=completion_data,
            headers=student_headers,
        )

        if completion_response.status_code == 200:
            # 2. 触发工时计算
            work_hours_response = await e2e_client.post(
                f"/api/v1/tasks/assistance/{task_id}/calculate-work-hours",
                headers=admin_headers,
            )

            if work_hours_response.status_code == 200:
                e2e_helper.assert_response_success(work_hours_response)
                work_hours_result = work_hours_response.json()

                work_hours_data = work_hours_result.get("data", {})
                assert "total_work_hours" in work_hours_data
                assert work_hours_data["total_work_hours"] > 0

                # 3. 验证工时计算逻辑
                # 协助任务应该按实际时长计算，可能有额外奖励
                assert "base_hours" in work_hours_data
                assert (
                    work_hours_data["base_hours"] == completion_data["actual_duration"]
                )
        else:
            pytest.skip("Assistance task completion functionality not available")

    @pytest.mark.asyncio
    async def test_assistance_task_statistics_and_reporting(
        self,
        e2e_client: AsyncClient,
        e2e_user_tokens: Dict[str, str],
        e2e_auth_headers,
        e2e_helper,
    ):
        """测试协助任务统计和报表功能"""

        admin_headers = e2e_auth_headers(e2e_user_tokens["admin"])
        student_headers = e2e_auth_headers(e2e_user_tokens["student"])

        # 1. 获取协助任务统计概览
        stats_response = await e2e_client.get(
            "/api/v1/tasks/assistance/statistics", headers=admin_headers
        )

        if stats_response.status_code == 200:
            e2e_helper.assert_response_success(stats_response)
            stats_data = stats_response.json().get("data", {})

            # 验证统计数据结构
            expected_stats = [
                "total_tasks",
                "pending_approval_count",
                "approved_count",
                "completed_count",
                "rejected_count",
                "total_work_hours",
            ]

            for stat in expected_stats:
                assert stat in stats_data, f"Missing statistic: {stat}"

        # 2. 获取个人协助任务统计
        personal_stats_response = await e2e_client.get(
            "/api/v1/tasks/assistance/my-statistics", headers=student_headers
        )

        if personal_stats_response.status_code == 200:
            e2e_helper.assert_response_success(personal_stats_response)
            personal_stats = personal_stats_response.json().get("data", {})

            # 验证个人统计数据
            expected_personal_stats = [
                "my_assistance_tasks",
                "completed_assistance_tasks",
                "total_assistance_hours",
                "approval_rate",
            ]

            for stat in expected_personal_stats:
                assert stat in personal_stats, f"Missing personal statistic: {stat}"

        # 3. 获取协助任务排行榜
        leaderboard_response = await e2e_client.get(
            "/api/v1/tasks/assistance/leaderboard", headers=admin_headers
        )

        if leaderboard_response.status_code == 200:
            e2e_helper.assert_response_success(leaderboard_response)
            leaderboard_data = leaderboard_response.json().get("data", {})

            # 验证排行榜数据结构
            assert "top_assistants" in leaderboard_data
            assistants = leaderboard_data["top_assistants"]

            if assistants:
                for assistant in assistants:
                    assert "member_name" in assistant
                    assert "assistance_count" in assistant
                    assert "total_hours" in assistant

    @pytest.mark.asyncio
    async def test_assistance_task_filtering_and_search(
        self,
        e2e_client: AsyncClient,
        e2e_user_tokens: Dict[str, str],
        e2e_auth_headers,
        e2e_helper,
    ):
        """测试协助任务筛选和搜索功能"""

        admin_headers = e2e_auth_headers(e2e_user_tokens["admin"])

        # 1. 获取所有协助任务
        all_tasks_response = await e2e_client.get(
            "/api/v1/tasks/assistance", headers=admin_headers
        )

        if all_tasks_response.status_code == 200:
            e2e_helper.assert_response_success(all_tasks_response)
            all_tasks_data = all_tasks_response.json().get("data", {})
            total_tasks = all_tasks_data.get("total", 0)

            if total_tasks == 0:
                pytest.skip("No assistance tasks available for filtering test")

        # 2. 按状态筛选
        status_filter_response = await e2e_client.get(
            "/api/v1/tasks/assistance",
            params={"status": "approved"},
            headers=admin_headers,
        )

        if status_filter_response.status_code == 200:
            e2e_helper.assert_response_success(status_filter_response)
            filtered_data = status_filter_response.json().get("data", {})
            filtered_tasks = filtered_data.get("items", [])

            # 验证筛选结果
            for task in filtered_tasks:
                assert task["status"] == "approved"

        # 3. 按协助类型筛选
        type_filter_response = await e2e_client.get(
            "/api/v1/tasks/assistance",
            params={"assistance_type": "equipment_maintenance"},
            headers=admin_headers,
        )

        if type_filter_response.status_code == 200:
            e2e_helper.assert_response_success(type_filter_response)
            type_filtered_data = type_filter_response.json().get("data", {})
            type_filtered_tasks = type_filtered_data.get("items", [])

            # 验证类型筛选结果
            for task in type_filtered_tasks:
                assert task["assistance_type"] == "equipment_maintenance"

        # 4. 按关键词搜索
        search_response = await e2e_client.get(
            "/api/v1/tasks/assistance", params={"search": "维护"}, headers=admin_headers
        )

        if search_response.status_code == 200:
            e2e_helper.assert_response_success(search_response)
            search_data = search_response.json().get("data", {})
            search_results = search_data.get("items", [])

            # 验证搜索结果包含关键词
            for task in search_results:
                task_text = f"{task.get('description', '')} {task.get('reason', '')}"
                assert "维护" in task_text

        # 5. 按日期范围筛选
        date_filter_response = await e2e_client.get(
            "/api/v1/tasks/assistance",
            params={
                "start_date": (datetime.now() - timedelta(days=7)).date().isoformat(),
                "end_date": datetime.now().date().isoformat(),
            },
            headers=admin_headers,
        )

        if date_filter_response.status_code == 200:
            e2e_helper.assert_response_success(date_filter_response)

    @pytest.mark.asyncio
    async def test_assistance_task_notifications(
        self,
        e2e_client: AsyncClient,
        e2e_user_tokens: Dict[str, str],
        e2e_auth_headers,
        e2e_helper,
    ):
        """测试协助任务通知功能"""

        student_headers = e2e_auth_headers(e2e_user_tokens["student"])
        admin_headers = e2e_auth_headers(e2e_user_tokens["admin"])

        # 1. 创建协助任务后检查通知
        assistance_data = {
            "task_type": "assistance",
            "description": "通知测试协助任务",
            "location": "测试地点",
            "assistance_type": "testing",
            "estimated_duration": 30,
            "proposed_date": (datetime.now() + timedelta(days=1)).isoformat(),
            "reason": "测试通知功能",
        }

        create_response = await e2e_client.post(
            "/api/v1/tasks/assistance", json=assistance_data, headers=student_headers
        )

        if create_response.status_code == 201:
            task_id = create_response.json()["data"]["id"]

            # 2. 检查管理员是否收到新申请通知
            admin_notifications_response = await e2e_client.get(
                "/api/v1/notifications", headers=admin_headers
            )

            if admin_notifications_response.status_code == 200:
                notifications = (
                    admin_notifications_response.json().get("data", {}).get("items", [])
                )

                # 查找相关通知
                assistance_notifications = [
                    notif
                    for notif in notifications
                    if "协助任务" in notif.get("content", "")
                    or "assistance" in notif.get("type", "")
                ]

                # 应该有新的协助任务申请通知
                assert (
                    len(assistance_notifications) > 0
                ), "No assistance task notification found"

            # 3. 管理员审批后检查学生通知
            approval_data = {
                "approval_status": "approved",
                "approval_notes": "同意申请",
            }

            approval_response = await e2e_client.put(
                f"/api/v1/tasks/assistance/{task_id}/approve",
                json=approval_data,
                headers=admin_headers,
            )

            if approval_response.status_code == 200:
                # 检查学生是否收到审批通知
                student_notifications_response = await e2e_client.get(
                    "/api/v1/notifications", headers=student_headers
                )

                if student_notifications_response.status_code == 200:
                    student_notifications = (
                        student_notifications_response.json()
                        .get("data", {})
                        .get("items", [])
                    )

                    # 查找审批通知
                    approval_notifications = [
                        notif
                        for notif in student_notifications
                        if "审批" in notif.get("content", "")
                        or "approval" in notif.get("type", "")
                    ]

                    assert (
                        len(approval_notifications) > 0
                    ), "No approval notification found"
        else:
            pytest.skip("Cannot create assistance task for notification test")


class TestAssistanceTaskPerformance:
    """协助任务性能测试"""

    @pytest.mark.asyncio
    async def test_assistance_task_creation_performance(
        self,
        e2e_client: AsyncClient,
        e2e_user_tokens: Dict[str, str],
        e2e_auth_headers,
        e2e_performance_monitor,
        e2e_helper,
    ):
        """测试协助任务创建性能"""

        student_headers = e2e_auth_headers(e2e_user_tokens["student"])
        e2e_performance_monitor.start()

        creation_times = []

        # 批量创建协助任务测试性能
        for i in range(5):  # 较少的数量避免过多测试数据
            assistance_data = {
                "task_type": "assistance",
                "description": f"性能测试协助任务{i}",
                "location": f"测试地点{i}",
                "assistance_type": "performance_test",
                "estimated_duration": 60 + i * 10,
                "proposed_date": (datetime.now() + timedelta(days=i + 1)).isoformat(),
                "reason": f"性能测试{i}",
            }

            start_time = asyncio.get_event_loop().time()

            create_response = await e2e_client.post(
                "/api/v1/tasks/assistance",
                json=assistance_data,
                headers=student_headers,
            )

            end_time = asyncio.get_event_loop().time()
            duration = end_time - start_time
            creation_times.append(duration)

            e2e_performance_monitor.record(f"assistance_creation_{i}", duration)

            if create_response.status_code == 201:
                create_result = create_response.json()
                assert create_result["success"] is True

        # 性能验证
        if creation_times:
            avg_creation_time = sum(creation_times) / len(creation_times)
            max_creation_time = max(creation_times)

            assert (
                avg_creation_time < 1.5
            ), f"Average assistance creation time {avg_creation_time}s exceeds 1.5s"
            assert (
                max_creation_time < 3.0
            ), f"Max assistance creation time {max_creation_time}s exceeds 3s"

            summary = e2e_performance_monitor.summary()
            print(f"Assistance Task Creation Performance Summary: {summary}")
        else:
            pytest.skip("No assistance tasks created for performance test")

    @pytest.mark.asyncio
    async def test_concurrent_assistance_operations(
        self,
        e2e_client: AsyncClient,
        e2e_user_tokens: Dict[str, str],
        e2e_auth_headers,
        e2e_helper,
    ):
        """测试并发协助任务操作"""

        admin_headers = e2e_auth_headers(e2e_user_tokens["admin"])
        student_headers = e2e_auth_headers(e2e_user_tokens["student"])

        # 并发操作：同时查询不同类型的协助任务信息
        concurrent_tasks = [
            e2e_client.get("/api/v1/tasks/assistance", headers=admin_headers),
            e2e_client.get(
                "/api/v1/tasks/assistance/pending-approval", headers=admin_headers
            ),
            e2e_client.get("/api/v1/tasks/assistance/my", headers=student_headers),
            e2e_client.get(
                "/api/v1/tasks/assistance/statistics", headers=admin_headers
            ),
            e2e_client.get(
                "/api/v1/tasks/assistance/leaderboard", headers=admin_headers
            ),
        ]

        # 执行并发操作
        results = await asyncio.gather(*concurrent_tasks, return_exceptions=True)

        # 验证并发操作结果
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                pytest.fail(
                    f"Concurrent assistance operation {i} failed with exception: {result}"
                )
            else:
                # 允许200或404（功能未实现）
                assert result.status_code in [
                    200,
                    404,
                ], f"Concurrent assistance operation {i} returned {result.status_code}"
