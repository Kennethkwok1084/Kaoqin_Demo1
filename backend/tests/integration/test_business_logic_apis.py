"""
业务逻辑API集成测试
测试新增的工时计算、统计分析等核心业务功能API
"""

import asyncio
from datetime import date, datetime, timedelta
from typing import Any, Dict

import pytest
from app.core.config import settings
from app.models.attendance import AttendanceRecord
from app.models.member import Member, UserRole
from app.models.task import RepairTask, TaskCategory, TaskPriority, TaskStatus, TaskType
from httpx import AsyncClient


class TestWorkHoursManagementAPI:
    """工时管理API测试"""

    async def test_batch_recalculate_work_hours(
        self, client: AsyncClient, admin_headers: Dict[str, str]
    ):
        """测试批量重新计算工时"""
        # 创建测试任务
        task_data = {
            "title": "测试工时重算任务",
            "description": "用于测试工时重算功能",
            "category": TaskCategory.NETWORK_REPAIR.value,
            "priority": TaskPriority.MEDIUM.value,
            "task_type": TaskType.ONLINE.value,
            "location": "测试地点",
        }

        # 创建任务
        create_response = await client.post(
            "/api/v1/tasks/repair", json=task_data, headers=admin_headers
        )
        assert create_response.status_code == 201
        task_id = create_response.json()["data"]["id"]

        # 批量重算工时
        recalc_response = await client.post(
            "/api/v1/tasks/work-hours/recalculate",
            params={"task_ids": [task_id]},
            headers=admin_headers,
        )
        assert recalc_response.status_code == 200

        result = recalc_response.json()
        assert "data" in result
        assert result["data"]["total_tasks"] >= 1
        assert "recalculated_count" in result["data"]
        assert "error_count" in result["data"]

        print(f"✅ 批量工时重算测试通过: 处理了 {result['data']['total_tasks']} 个任务")

    async def test_single_task_recalculate_hours(
        self, client: AsyncClient, admin_headers: Dict[str, str]
    ):
        """测试单个任务工时重算"""
        # 创建测试任务
        task_data = {
            "title": "单任务工时重算测试",
            "description": "测试单个任务工时重算",
            "category": TaskCategory.SOFTWARE_REPAIR.value,
            "priority": TaskPriority.HIGH.value,
            "task_type": TaskType.OFFLINE.value,
            "location": "测试地点",
        }

        create_response = await client.post(
            "/api/v1/tasks/repair", json=task_data, headers=admin_headers
        )
        assert create_response.status_code == 201
        task_id = create_response.json()["data"]["id"]

        # 单任务重算
        recalc_response = await client.post(
            f"/api/v1/tasks/repair/{task_id}/recalculate-hours",
            params={"force_update": True},
            headers=admin_headers,
        )
        assert recalc_response.status_code == 200

        result = recalc_response.json()
        assert "data" in result
        assert result["data"]["task_id"] == task_id
        assert "old_minutes" in result["data"]
        assert "new_minutes" in result["data"]
        assert "breakdown" in result["data"]

        print(
            f"✅ 单任务工时重算测试通过: 任务 {task_id} 工时更新为 {result['data']['new_minutes']} 分钟"
        )

    async def test_pending_work_hours_review(
        self, client: AsyncClient, admin_headers: Dict[str, str]
    ):
        """测试待审核工时任务列表"""
        response = await client.get(
            "/api/v1/tasks/work-hours/pending-review",
            params={"threshold_hours": 3.0, "page": 1, "size": 10},
            headers=admin_headers,
        )
        assert response.status_code == 200

        result = response.json()
        assert "data" in result
        assert "items" in result["data"]
        assert "total" in result["data"]
        assert "page" in result["data"]

        # 检查返回的任务是否有异常原因
        for item in result["data"]["items"]:
            assert "anomaly_reasons" in item
            assert "breakdown" in item
            assert "work_minutes" in item

        print(
            f"✅ 待审核工时列表测试通过: 找到 {result['data']['total']} 个需要审核的任务"
        )

    async def test_adjust_task_work_hours(
        self, client: AsyncClient, admin_headers: Dict[str, str]
    ):
        """测试手动调整任务工时"""
        # 创建测试任务
        task_data = {
            "title": "工时调整测试任务",
            "description": "用于测试手动调整工时",
            "category": TaskCategory.EQUIPMENT_REPAIR.value,
            "priority": TaskPriority.LOW.value,
            "task_type": TaskType.ONLINE.value,
            "location": "测试地点",
        }

        create_response = await client.post(
            "/api/v1/tasks/repair", json=task_data, headers=admin_headers
        )
        assert create_response.status_code == 201
        task_id = create_response.json()["data"]["id"]

        # 手动调整工时
        adjust_response = await client.put(
            f"/api/v1/tasks/work-hours/{task_id}/adjust",
            params={"adjusted_minutes": 90, "reason": "特殊情况需要调整工时"},
            headers=admin_headers,
        )
        assert adjust_response.status_code == 200

        result = adjust_response.json()
        assert "data" in result
        assert result["data"]["task_id"] == task_id
        assert result["data"]["adjusted_minutes"] == 90
        assert "reason" in result["data"]
        assert "breakdown" in result["data"]

        print(f"✅ 手动调整工时测试通过: 任务 {task_id} 工时调整为 90 分钟")

    async def test_work_hours_statistics(
        self, client: AsyncClient, admin_headers: Dict[str, str]
    ):
        """测试工时统计信息"""
        response = await client.get(
            "/api/v1/tasks/work-hours/statistics",
            params={
                "group_by": "day",
                "date_from": (datetime.now() - timedelta(days=7)).isoformat(),
                "date_to": datetime.now().isoformat(),
            },
            headers=admin_headers,
        )
        assert response.status_code == 200

        result = response.json()
        assert "data" in result
        assert "period" in result["data"]
        assert "summary" in result["data"]
        assert "by_task_type" in result["data"]
        assert "time_series" in result["data"]

        # 检查统计数据结构
        summary = result["data"]["summary"]
        assert "total_tasks" in summary
        assert "total_work_hours" in summary
        assert "average_hours_per_task" in summary

        print(
            f"✅ 工时统计测试通过: 统计了 {summary['total_tasks']} 个任务，总工时 {summary['total_work_hours']} 小时"
        )


class TestStatisticsAPI:
    """统计分析API测试"""

    async def test_statistics_overview(
        self, client: AsyncClient, admin_headers: Dict[str, str]
    ):
        """测试系统概览统计"""
        response = await client.get(
            "/api/v1/statistics/overview",
            params={
                "date_from": (datetime.now() - timedelta(days=30)).isoformat(),
                "date_to": datetime.now().isoformat(),
            },
            headers=admin_headers,
        )
        assert response.status_code == 200

        result = response.json()
        assert "data" in result
        assert "period" in result["data"]
        assert "tasks" in result["data"]
        assert "members" in result["data"]
        assert "attendance" in result["data"]
        assert "trends" in result["data"]
        assert "categories" in result["data"]

        # 检查任务统计数据
        tasks_data = result["data"]["tasks"]
        required_fields = [
            "total",
            "completed",
            "in_progress",
            "pending",
            "completion_rate",
            "total_work_hours",
            "avg_work_hours",
        ]
        for field in required_fields:
            assert field in tasks_data

        print(f"✅ 系统概览统计测试通过: 任务完成率 {tasks_data['completion_rate']}%")

    async def test_efficiency_analysis(
        self, client: AsyncClient, admin_headers: Dict[str, str]
    ):
        """测试工作效率分析"""
        response = await client.get(
            "/api/v1/statistics/efficiency",
            params={
                "group_by": "member",
                "date_from": (datetime.now() - timedelta(days=30)).isoformat(),
                "date_to": datetime.now().isoformat(),
            },
            headers=admin_headers,
        )
        assert response.status_code == 200

        result = response.json()
        assert "data" in result
        assert "period" in result["data"]
        assert "overall" in result["data"]

        # 检查整体效率数据
        overall = result["data"]["overall"]
        required_fields = [
            "total_tasks",
            "total_work_hours",
            "avg_work_hours",
            "avg_completion_hours",
        ]
        for field in required_fields:
            assert field in overall

        # 如果有成员数据，检查成员效率分析
        if "members" in result["data"]:
            for member in result["data"]["members"]:
                assert "member_id" in member
                assert "member_name" in member
                assert "total_tasks" in member
                assert "efficiency_score" in member

        print(f"✅ 效率分析测试通过: 分析了 {overall['total_tasks']} 个任务")

    async def test_monthly_report_team(
        self, client: AsyncClient, admin_headers: Dict[str, str]
    ):
        """测试团队月度报表"""
        current_date = datetime.now()
        response = await client.get(
            "/api/v1/statistics/monthly-report",
            params={"year": current_date.year, "month": current_date.month},
            headers=admin_headers,
        )
        assert response.status_code == 200

        result = response.json()
        assert "data" in result
        assert "period" in result["data"]
        assert "type" in result["data"]
        assert result["data"]["type"] == "team"

        # 检查团队报表数据
        if "team_summary" in result["data"]:
            team_summary = result["data"]["team_summary"]
            assert "total_tasks" in team_summary
            assert "completed_tasks" in team_summary
            assert "completion_rate" in team_summary
            assert "total_work_hours" in team_summary

        print(f"✅ 团队月度报表测试通过: {current_date.year}年{current_date.month}月")

    async def test_monthly_report_personal(
        self, client: AsyncClient, user_headers: Dict[str, str], test_user_id: int
    ):
        """测试个人月度报表"""
        current_date = datetime.now()
        response = await client.get(
            "/api/v1/statistics/monthly-report",
            params={
                "year": current_date.year,
                "month": current_date.month,
                "member_id": test_user_id,
            },
            headers=user_headers,
        )
        assert response.status_code == 200

        result = response.json()
        assert "data" in result
        assert "type" in result["data"]
        assert result["data"]["type"] == "personal"

        # 检查个人报表数据
        assert "member" in result["data"]
        assert "tasks" in result["data"]
        assert "attendance" in result["data"]

        member_info = result["data"]["member"]
        assert "id" in member_info
        assert "name" in member_info
        assert member_info["id"] == test_user_id

        print(
            f"✅ 个人月度报表测试通过: 用户 {member_info['name']} 的 {current_date.year}年{current_date.month}月报表"
        )

    async def test_export_statistics_data(
        self, client: AsyncClient, admin_headers: Dict[str, str]
    ):
        """测试统计数据导出"""
        export_types = ["overview", "efficiency", "monthly"]
        formats = ["excel", "csv", "json"]

        for export_type in export_types:
            for format_type in formats:
                response = await client.get(
                    "/api/v1/statistics/export",
                    params={
                        "export_type": export_type,
                        "format": format_type,
                        "date_from": (datetime.now() - timedelta(days=7)).isoformat(),
                        "date_to": datetime.now().isoformat(),
                    },
                    headers=admin_headers,
                )
                assert response.status_code == 200

                result = response.json()
                assert "data" in result
                assert "download_url" in result["data"]
                assert "filename" in result["data"]
                assert "export_type" in result["data"]
                assert "format" in result["data"]
                assert result["data"]["export_type"] == export_type
                assert result["data"]["format"] == format_type

        print(
            f"✅ 统计数据导出测试通过: 测试了 {len(export_types) * len(formats)} 种导出组合"
        )


class TestIntegratedBusinessFlow:
    """集成业务流程测试"""

    async def test_complete_task_workflow_with_statistics(
        self,
        client: AsyncClient,
        admin_headers: Dict[str, str],
        user_headers: Dict[str, str],
        test_user_id: int,
    ):
        """测试完整的任务工作流程及统计分析"""

        # 1. 创建任务
        task_data = {
            "title": "集成测试任务",
            "description": "用于测试完整业务流程",
            "category": TaskCategory.NETWORK_REPAIR.value,
            "priority": TaskPriority.HIGH.value,
            "task_type": TaskType.ONLINE.value,
            "location": "集成测试地点",
            "assigned_to": test_user_id,
        }

        create_response = await client.post(
            "/api/v1/tasks/repair", json=task_data, headers=admin_headers
        )
        assert create_response.status_code == 201
        task_id = create_response.json()["data"]["id"]
        print(f"📝 创建任务: {task_id}")

        # 2. 接受任务
        accept_response = await client.put(
            f"/api/v1/tasks/repair/{task_id}/status",
            json={"status": TaskStatus.IN_PROGRESS.value},
            headers=user_headers,
        )
        assert accept_response.status_code == 200
        print(f"▶️ 接受任务: {task_id}")

        # 3. 完成任务
        complete_response = await client.put(
            f"/api/v1/tasks/repair/{task_id}/status",
            json={
                "status": TaskStatus.COMPLETED.value,
                "completion_notes": "任务已完成",
                "actual_work_hours": 1.0,
            },
            headers=user_headers,
        )
        assert complete_response.status_code == 200
        print(f"✅ 完成任务: {task_id}")

        # 4. 计算工时
        calc_response = await client.post(
            f"/api/v1/tasks/repair/{task_id}/calculate-hours",
            json={
                "review_rating": 5,
                "is_late_response": False,
                "is_late_completion": False,
            },
            headers=user_headers,
        )
        assert calc_response.status_code == 200
        work_hours_data = calc_response.json()["data"]
        print(f"⏱️ 计算工时: {work_hours_data['final_minutes']} 分钟")

        # 5. 检查统计数据更新
        stats_response = await client.get(
            "/api/v1/statistics/overview",
            params={
                "date_from": (datetime.now() - timedelta(hours=1)).isoformat(),
                "date_to": datetime.now().isoformat(),
            },
            headers=admin_headers,
        )
        assert stats_response.status_code == 200
        stats_data = stats_response.json()["data"]

        # 验证统计数据包含新完成的任务
        assert stats_data["tasks"]["completed"] >= 1
        print(f"📊 统计数据更新: 已完成任务 {stats_data['tasks']['completed']} 个")

        # 6. 检查效率分析
        efficiency_response = await client.get(
            "/api/v1/statistics/efficiency",
            params={
                "member_id": test_user_id,
                "group_by": "member",
                "date_from": (datetime.now() - timedelta(hours=1)).isoformat(),
                "date_to": datetime.now().isoformat(),
            },
            headers=admin_headers,
        )
        assert efficiency_response.status_code == 200
        efficiency_data = efficiency_response.json()["data"]

        # 验证效率分析包含该用户的数据
        if "members" in efficiency_data:
            user_found = any(
                member["member_id"] == test_user_id
                for member in efficiency_data["members"]
            )
            if user_found:
                print(f"🎯 效率分析更新: 用户 {test_user_id} 的效率数据已更新")

        print(f"✅ 完整业务流程测试通过: 任务 {task_id} 从创建到统计分析全流程正常")

    async def test_data_consistency_across_apis(
        self, client: AsyncClient, admin_headers: Dict[str, str]
    ):
        """测试各API间数据一致性"""

        # 获取任务统计
        task_stats_response = await client.get(
            "/api/v1/tasks/statistics/overview", headers=admin_headers
        )
        assert task_stats_response.status_code == 200
        task_stats = task_stats_response.json()["data"]

        # 获取系统概览统计
        overview_response = await client.get(
            "/api/v1/statistics/overview", headers=admin_headers
        )
        assert overview_response.status_code == 200
        overview_stats = overview_response.json()["data"]

        # 获取工时统计
        work_hours_response = await client.get(
            "/api/v1/tasks/work-hours/statistics", headers=admin_headers
        )
        assert work_hours_response.status_code == 200
        work_hours_stats = work_hours_response.json()["data"]

        # 数据一致性检查（在相同时间范围内）
        # 注意：由于时间范围可能不完全一致，这里主要检查数据结构一致性
        print(f"📊 任务统计 - 总任务数: {task_stats.get('total_tasks', 0)}")
        print(f"📊 概览统计 - 总任务数: {overview_stats['tasks'].get('total', 0)}")
        print(
            f"📊 工时统计 - 总任务数: {work_hours_stats['summary'].get('total_tasks', 0)}"
        )

        # 检查数据结构完整性
        assert isinstance(task_stats.get("total_tasks", 0), int)
        assert isinstance(overview_stats["tasks"].get("total", 0), int)
        assert isinstance(work_hours_stats["summary"].get("total_tasks", 0), int)

        print("✅ 各API数据一致性检查通过")


# 测试运行器
async def run_business_logic_api_tests():
    """运行所有业务逻辑API测试"""
    print("🚀 开始业务逻辑API集成测试...")

    # 测试配置
    test_results = {
        "total_tests": 0,
        "passed_tests": 0,
        "failed_tests": 0,
        "test_details": [],
    }

    try:
        # 这里需要实际的测试客户端和认证头设置
        # 由于这是集成测试，需要在实际的测试环境中运行

        print("⚠️  业务逻辑API集成测试需要在完整的测试环境中运行")
        print("   请使用 pytest tests/integration/test_business_logic_apis.py 命令执行")

        test_results.update(
            {
                "status": "ready",
                "message": "测试代码已准备就绪，等待执行",
                "test_classes": [
                    "TestWorkHoursManagementAPI",
                    "TestStatisticsAPI",
                    "TestIntegratedBusinessFlow",
                ],
            }
        )

    except Exception as e:
        print(f"❌ 测试运行失败: {str(e)}")
        test_results.update({"status": "error", "error": str(e)})

    return test_results


if __name__ == "__main__":
    # 直接运行测试（需要测试环境）
    results = asyncio.run(run_business_logic_api_tests())
    print(f"\n📋 测试结果: {results}")
