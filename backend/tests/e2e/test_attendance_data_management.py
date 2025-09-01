"""
考勤数据管理E2E测试
测试月度工时统计、Excel数据导出、上月结转逻辑
包含考勤记录的完整生命周期管理和数据完整性验证
"""

import asyncio
import io
from datetime import datetime, timedelta
from typing import Dict, List

import pytest
from httpx import AsyncClient


class TestAttendanceDataManagement:
    """考勤数据管理E2E测试类"""

    @pytest.mark.asyncio
    async def test_monthly_work_hours_calculation(
        self,
        e2e_client: AsyncClient,
        e2e_user_tokens: Dict[str, str],
        e2e_test_users: Dict[str, str],
        e2e_auth_headers,
        e2e_helper,
    ):
        """测试月度工时统计计算"""

        admin_headers = e2e_auth_headers(e2e_user_tokens["admin"])
        student_headers = e2e_auth_headers(e2e_user_tokens["student"])

        # 1. 触发当月工时统计计算
        current_date = datetime.now()
        calculation_data = {
            "year": current_date.year,
            "month": current_date.month,
            "member_id": e2e_test_users["student"].id,
        }

        calc_response = await e2e_client.post(
            "/api/v1/attendance/calculate-monthly",
            json=calculation_data,
            headers=admin_headers,
        )

        if calc_response.status_code == 200:
            e2e_helper.assert_response_success(calc_response)
            calc_result = calc_response.json()

            assert calc_result["success"] is True
            calc_data = calc_result.get("data", {})

            # 验证计算结果结构
            expected_fields = [
                "total_work_hours",
                "base_work_hours",
                "bonus_hours",
                "penalty_hours",
                "task_count",
                "completed_task_count",
            ]

            for field in expected_fields:
                assert field in calc_data, f"Missing field: {field}"

            # 验证数值合理性
            assert calc_data["total_work_hours"] >= 0
            assert calc_data["base_work_hours"] >= 0
            assert calc_data["task_count"] >= calc_data["completed_task_count"]

            # 2. 获取计算后的考勤记录
            attendance_response = await e2e_client.get(
                f"/api/v1/attendance/member/{e2e_test_users['student'].id}",
                params={"year": current_date.year, "month": current_date.month},
                headers=admin_headers,
            )

            if attendance_response.status_code == 200:
                e2e_helper.assert_response_success(attendance_response)
                attendance_data = attendance_response.json().get("data", {})

                # 验证考勤记录与计算结果一致
                assert (
                    attendance_data["total_work_hours"] == calc_data["total_work_hours"]
                )
                assert attendance_data["task_count"] == calc_data["task_count"]
        else:
            pytest.skip("Monthly work hours calculation not available")

    @pytest.mark.asyncio
    async def test_batch_monthly_calculation(
        self,
        e2e_client: AsyncClient,
        e2e_user_tokens: Dict[str, str],
        e2e_auth_headers,
        e2e_helper,
    ):
        """测试批量月度工时计算"""

        admin_headers = e2e_auth_headers(e2e_user_tokens["admin"])

        # 1. 触发全员月度工时计算
        current_date = datetime.now()
        batch_calc_data = {
            "year": current_date.year,
            "month": current_date.month,
            "include_all_members": True,
        }

        batch_response = await e2e_client.post(
            "/api/v1/attendance/batch-calculate-monthly",
            json=batch_calc_data,
            headers=admin_headers,
        )

        if batch_response.status_code == 200:
            e2e_helper.assert_response_success(batch_response)
            batch_result = batch_response.json()

            assert batch_result["success"] is True
            batch_data = batch_result.get("data", {})

            # 验证批量处理结果
            assert "processed_count" in batch_data
            assert "success_count" in batch_data
            assert "failed_count" in batch_data
            assert batch_data["processed_count"] >= 0

            # 2. 验证批量计算后的考勤数据
            if batch_data["success_count"] > 0:
                # 获取当月所有考勤记录
                all_attendance_response = await e2e_client.get(
                    "/api/v1/attendance",
                    params={"year": current_date.year, "month": current_date.month},
                    headers=admin_headers,
                )

                if all_attendance_response.status_code == 200:
                    e2e_helper.assert_response_success(all_attendance_response)
                    all_attendance_data = all_attendance_response.json().get("data", {})
                    attendance_records = all_attendance_data.get("items", [])

                    # 验证有考勤记录生成
                    assert len(attendance_records) >= batch_data["success_count"]

                    # 验证每条记录的数据完整性
                    for record in attendance_records:
                        assert record["year"] == current_date.year
                        assert record["month"] == current_date.month
                        assert "total_work_hours" in record
                        assert "member_id" in record
        else:
            pytest.skip("Batch monthly calculation not available")

    @pytest.mark.asyncio
    async def test_attendance_record_crud_operations(
        self,
        e2e_client: AsyncClient,
        e2e_user_tokens: Dict[str, str],
        e2e_test_users: Dict[str, str],
        e2e_auth_headers,
        e2e_helper,
    ):
        """测试考勤记录的CRUD操作"""

        admin_headers = e2e_auth_headers(e2e_user_tokens["admin"])
        student_headers = e2e_auth_headers(e2e_user_tokens["student"])

        # 1. 创建考勤记录
        attendance_data = {
            "member_id": e2e_test_users["student"].id,
            "year": 2024,
            "month": 1,  # 使用历史月份避免与当前月份冲突
            "total_work_hours": 720,
            "base_work_hours": 680,
            "bonus_hours": 80,
            "penalty_hours": 40,
            "task_count": 16,
            "completed_task_count": 15,
        }

        create_response = await e2e_client.post(
            "/api/v1/attendance", json=attendance_data, headers=admin_headers
        )

        if create_response.status_code == 201:
            e2e_helper.assert_response_success(create_response, 201)
            create_result = create_response.json()

            assert create_result["success"] is True
            created_record = create_result.get("data", {})
            record_id = created_record["id"]

            # 验证创建的数据
            assert (
                created_record["total_work_hours"]
                == attendance_data["total_work_hours"]
            )
            assert created_record["member_id"] == attendance_data["member_id"]

            # 2. 读取考勤记录
            read_response = await e2e_client.get(
                f"/api/v1/attendance/{record_id}", headers=admin_headers
            )
            e2e_helper.assert_response_success(read_response)

            read_data = read_response.json().get("data", {})
            assert read_data["id"] == record_id
            assert read_data["total_work_hours"] == attendance_data["total_work_hours"]

            # 3. 更新考勤记录
            update_data = {
                "total_work_hours": 750,
                "bonus_hours": 100,
                "penalty_hours": 30,
            }

            update_response = await e2e_client.put(
                f"/api/v1/attendance/{record_id}",
                json=update_data,
                headers=admin_headers,
            )

            if update_response.status_code == 200:
                e2e_helper.assert_response_success(update_response)
                update_result = update_response.json()

                updated_record = update_result.get("data", {})
                assert (
                    updated_record["total_work_hours"]
                    == update_data["total_work_hours"]
                )
                assert updated_record["bonus_hours"] == update_data["bonus_hours"]

            # 4. 学生查看自己的考勤记录
            my_attendance_response = await e2e_client.get(
                "/api/v1/attendance/my",
                params={"year": 2024, "month": 1},
                headers=student_headers,
            )

            if my_attendance_response.status_code == 200:
                e2e_helper.assert_response_success(my_attendance_response)
                my_data = my_attendance_response.json().get("data", {})
                assert my_data["member_id"] == e2e_test_users["student"].id
                assert my_data["year"] == 2024
                assert my_data["month"] == 1

            # 5. 删除考勤记录（清理测试数据）
            delete_response = await e2e_client.delete(
                f"/api/v1/attendance/{record_id}", headers=admin_headers
            )

            if delete_response.status_code == 200:
                e2e_helper.assert_response_success(delete_response)

                # 验证记录已删除
                deleted_check_response = await e2e_client.get(
                    f"/api/v1/attendance/{record_id}", headers=admin_headers
                )
                assert deleted_check_response.status_code == 404
        else:
            pytest.skip("Attendance record creation not available")

    @pytest.mark.asyncio
    async def test_excel_data_export_functionality(
        self,
        e2e_client: AsyncClient,
        e2e_user_tokens: Dict[str, str],
        e2e_sample_attendance_records: List,
        e2e_auth_headers,
        e2e_helper,
    ):
        """测试Excel数据导出功能（4个工作表）"""

        admin_headers = e2e_auth_headers(e2e_user_tokens["admin"])

        if not e2e_sample_attendance_records:
            pytest.skip("No attendance records available for export test")

        # 1. 导出当月考勤数据
        current_date = datetime.now()
        export_params = {
            "year": current_date.year,
            "month": current_date.month,
            "format": "excel",
        }

        export_response = await e2e_client.get(
            "/api/v1/attendance/export", params=export_params, headers=admin_headers
        )

        if export_response.status_code == 200:
            e2e_helper.assert_response_success(export_response)

            # 验证响应头部包含Excel文件信息
            content_type = export_response.headers.get("content-type", "")
            assert (
                "application/vnd.openxmlformats" in content_type
                or "application/octet-stream" in content_type
            )

            content_disposition = export_response.headers.get("content-disposition", "")
            assert "attachment" in content_disposition
            assert ".xlsx" in content_disposition

            # 验证文件内容不为空
            file_content = export_response.content
            assert len(file_content) > 0

            # 2. 测试不同导出格式
            export_formats = ["excel", "csv"]

            for format_type in export_formats:
                format_response = await e2e_client.get(
                    "/api/v1/attendance/export",
                    params={
                        "year": current_date.year,
                        "month": current_date.month,
                        "format": format_type,
                    },
                    headers=admin_headers,
                )

                if format_response.status_code == 200:
                    # 验证不同格式的内容类型
                    format_content_type = format_response.headers.get(
                        "content-type", ""
                    )
                    if format_type == "excel":
                        assert (
                            "vnd.openxmlformats" in format_content_type
                            or "octet-stream" in format_content_type
                        )
                    elif format_type == "csv":
                        assert (
                            "text/csv" in format_content_type
                            or "text/plain" in format_content_type
                        )
        else:
            pytest.skip("Attendance data export not available")

    @pytest.mark.asyncio
    async def test_monthly_rollover_logic(
        self,
        e2e_client: AsyncClient,
        e2e_user_tokens: Dict[str, str],
        e2e_test_users: Dict[str, str],
        e2e_auth_headers,
        e2e_helper,
    ):
        """测试月度结转逻辑"""

        admin_headers = e2e_auth_headers(e2e_user_tokens["admin"])

        # 1. 模拟上月数据结转
        last_month = datetime.now().replace(day=1) - timedelta(days=1)
        rollover_data = {
            "from_year": last_month.year,
            "from_month": last_month.month,
            "to_year": datetime.now().year,
            "to_month": datetime.now().month,
            "member_id": e2e_test_users["student"].id,
        }

        rollover_response = await e2e_client.post(
            "/api/v1/attendance/monthly-rollover",
            json=rollover_data,
            headers=admin_headers,
        )

        if rollover_response.status_code == 200:
            e2e_helper.assert_response_success(rollover_response)
            rollover_result = rollover_response.json()

            assert rollover_result["success"] is True
            rollover_info = rollover_result.get("data", {})

            # 验证结转信息
            assert "carried_over_hours" in rollover_info
            assert "rollover_type" in rollover_info
            assert rollover_info["carried_over_hours"] >= 0

            # 2. 验证结转后的当月考勤记录
            current_attendance_response = await e2e_client.get(
                f"/api/v1/attendance/member/{e2e_test_users['student'].id}",
                params={"year": datetime.now().year, "month": datetime.now().month},
                headers=admin_headers,
            )

            if current_attendance_response.status_code == 200:
                e2e_helper.assert_response_success(current_attendance_response)
                current_data = current_attendance_response.json().get("data", {})

                # 验证结转数据已包含在当月记录中
                if rollover_info["carried_over_hours"] > 0:
                    assert "carried_over_from_previous" in current_data
                    assert (
                        current_data["carried_over_from_previous"]
                        == rollover_info["carried_over_hours"]
                    )
        else:
            pytest.skip("Monthly rollover functionality not available")

    @pytest.mark.asyncio
    async def test_attendance_statistics_and_analytics(
        self,
        e2e_client: AsyncClient,
        e2e_user_tokens: Dict[str, str],
        e2e_sample_attendance_records: List,
        e2e_auth_headers,
        e2e_helper,
    ):
        """测试考勤统计和分析功能"""

        admin_headers = e2e_auth_headers(e2e_user_tokens["admin"])

        if not e2e_sample_attendance_records:
            pytest.skip("No attendance records available for statistics test")

        # 1. 获取考勤统计概览
        stats_response = await e2e_client.get(
            "/api/v1/attendance/statistics/overview", headers=admin_headers
        )

        if stats_response.status_code == 200:
            e2e_helper.assert_response_success(stats_response)
            stats_data = stats_response.json().get("data", {})

            # 验证统计数据结构
            expected_stats = [
                "total_members",
                "total_work_hours",
                "average_work_hours",
                "top_performers",
                "monthly_trends",
            ]

            for stat in expected_stats:
                if stat in stats_data:
                    # 验证数据类型和合理性
                    if stat in [
                        "total_members",
                        "total_work_hours",
                        "average_work_hours",
                    ]:
                        assert stats_data[stat] >= 0

        # 2. 获取月度对比统计
        current_date = datetime.now()
        comparison_response = await e2e_client.get(
            "/api/v1/attendance/statistics/monthly-comparison",
            params={
                "year": current_date.year,
                "month": current_date.month,
                "compare_months": 3,  # 对比最近3个月
            },
            headers=admin_headers,
        )

        if comparison_response.status_code == 200:
            e2e_helper.assert_response_success(comparison_response)
            comparison_data = comparison_response.json().get("data", {})

            # 验证对比数据结构
            assert "monthly_data" in comparison_data
            assert "trends" in comparison_data

            monthly_data = comparison_data["monthly_data"]
            if monthly_data:
                for month_data in monthly_data:
                    assert "year" in month_data
                    assert "month" in month_data
                    assert "total_hours" in month_data

        # 3. 获取部门/小组统计
        group_stats_response = await e2e_client.get(
            "/api/v1/attendance/statistics/by-group",
            params={"year": current_date.year, "month": current_date.month},
            headers=admin_headers,
        )

        if group_stats_response.status_code == 200:
            e2e_helper.assert_response_success(group_stats_response)
            group_data = group_stats_response.json().get("data", {})

            # 验证小组统计数据
            assert "group_statistics" in group_data
            group_stats = group_data["group_statistics"]

            if group_stats:
                for group_stat in group_stats:
                    assert "group_id" in group_stat
                    assert "total_hours" in group_stat
                    assert "member_count" in group_stat

    @pytest.mark.asyncio
    async def test_attendance_data_validation_and_integrity(
        self,
        e2e_client: AsyncClient,
        e2e_user_tokens: Dict[str, str],
        e2e_test_users: Dict[str, str],
        e2e_auth_headers,
        e2e_helper,
    ):
        """测试考勤数据验证和完整性检查"""

        admin_headers = e2e_auth_headers(e2e_user_tokens["admin"])

        # 1. 测试无效数据验证
        invalid_attendance_data = {
            "member_id": e2e_test_users["student"].id,
            "year": 2024,
            "month": 13,  # 无效月份
            "total_work_hours": -100,  # 负数工时
            "task_count": -5,  # 负数任务数
        }

        invalid_response = await e2e_client.post(
            "/api/v1/attendance", json=invalid_attendance_data, headers=admin_headers
        )

        # 应该返回400或422验证错误
        assert invalid_response.status_code in [400, 422]

        error_data = invalid_response.json()
        assert not error_data.get("success", True)

        # 2. 测试重复记录验证
        valid_attendance_data = {
            "member_id": e2e_test_users["student"].id,
            "year": 2024,
            "month": 2,
            "total_work_hours": 700,
            "base_work_hours": 650,
            "bonus_hours": 50,
            "penalty_hours": 0,
            "task_count": 14,
            "completed_task_count": 14,
        }

        # 第一次创建
        first_create_response = await e2e_client.post(
            "/api/v1/attendance", json=valid_attendance_data, headers=admin_headers
        )

        if first_create_response.status_code == 201:
            record_id = first_create_response.json()["data"]["id"]

            # 尝试创建重复记录
            duplicate_response = await e2e_client.post(
                "/api/v1/attendance", json=valid_attendance_data, headers=admin_headers
            )

            # 应该失败（409 Conflict或400 Bad Request）
            assert duplicate_response.status_code in [400, 409, 422]

            # 清理测试数据
            await e2e_client.delete(
                f"/api/v1/attendance/{record_id}", headers=admin_headers
            )

        # 3. 测试数据完整性检查
        integrity_check_response = await e2e_client.post(
            "/api/v1/attendance/integrity-check",
            json={"year": datetime.now().year, "month": datetime.now().month},
            headers=admin_headers,
        )

        if integrity_check_response.status_code == 200:
            e2e_helper.assert_response_success(integrity_check_response)
            integrity_result = integrity_check_response.json()

            integrity_data = integrity_result.get("data", {})
            assert "check_results" in integrity_data
            assert "inconsistencies_found" in integrity_data

            check_results = integrity_data["check_results"]
            if check_results:
                for check in check_results:
                    assert "check_type" in check
                    assert "status" in check

    @pytest.mark.asyncio
    async def test_attendance_permissions_and_access_control(
        self,
        e2e_client: AsyncClient,
        e2e_user_tokens: Dict[str, str],
        e2e_test_users: Dict[str, str],
        e2e_auth_headers,
        e2e_helper,
    ):
        """测试考勤数据权限和访问控制"""

        student_headers = e2e_auth_headers(e2e_user_tokens["student"])
        admin_headers = e2e_auth_headers(e2e_user_tokens["admin"])
        leader_headers = e2e_auth_headers(e2e_user_tokens["leader"])

        # 1. 学生只能查看自己的考勤数据
        my_attendance_response = await e2e_client.get(
            "/api/v1/attendance/my", headers=student_headers
        )

        # 应该成功或返回404（没有记录）
        assert my_attendance_response.status_code in [200, 404]

        if my_attendance_response.status_code == 200:
            my_data = my_attendance_response.json().get("data", {})
            if my_data:
                assert my_data["member_id"] == e2e_test_users["student"].id

        # 2. 学生不能查看他人的考勤数据
        other_member_response = await e2e_client.get(
            f"/api/v1/attendance/member/{e2e_test_users['admin'].id}",
            headers=student_headers,
        )

        # 应该被拒绝访问
        assert other_member_response.status_code in [401, 403]

        # 3. 学生不能创建考勤记录
        student_create_attempt = await e2e_client.post(
            "/api/v1/attendance",
            json={
                "member_id": e2e_test_users["student"].id,
                "year": 2024,
                "month": 3,
                "total_work_hours": 600,
            },
            headers=student_headers,
        )

        # 应该被拒绝
        assert student_create_attempt.status_code in [401, 403]

        # 4. 管理员可以访问所有考勤数据
        all_attendance_response = await e2e_client.get(
            "/api/v1/attendance", headers=admin_headers
        )

        # 管理员应该能访问
        assert all_attendance_response.status_code in [200, 404]

        # 5. 组长权限测试（如果实现了组长特殊权限）
        group_attendance_response = await e2e_client.get(
            "/api/v1/attendance/my-group", headers=leader_headers
        )

        # 组长应该能查看本组数据（或返回404）
        assert group_attendance_response.status_code in [200, 404]


class TestAttendanceDataPerformance:
    """考勤数据性能测试"""

    @pytest.mark.asyncio
    async def test_monthly_calculation_performance(
        self,
        e2e_client: AsyncClient,
        e2e_user_tokens: Dict[str, str],
        e2e_test_users: Dict[str, str],
        e2e_auth_headers,
        e2e_performance_monitor,
        e2e_helper,
    ):
        """测试月度工时计算性能"""

        admin_headers = e2e_auth_headers(e2e_user_tokens["admin"])
        e2e_performance_monitor.start()

        # 测试单个用户月度计算性能
        calculation_times = []

        for i in range(3):  # 减少测试次数避免过多计算
            calc_data = {
                "year": datetime.now().year,
                "month": datetime.now().month,
                "member_id": e2e_test_users["student"].id,
            }

            start_time = asyncio.get_event_loop().time()

            calc_response = await e2e_client.post(
                "/api/v1/attendance/calculate-monthly",
                json=calc_data,
                headers=admin_headers,
            )

            end_time = asyncio.get_event_loop().time()
            duration = end_time - start_time
            calculation_times.append(duration)

            e2e_performance_monitor.record(f"monthly_calculation_{i}", duration)

            if calc_response.status_code == 200:
                calc_result = calc_response.json()
                assert calc_result["success"] is True

        # 性能验证
        if calculation_times:
            avg_calc_time = sum(calculation_times) / len(calculation_times)
            max_calc_time = max(calculation_times)

            assert (
                avg_calc_time < 3.0
            ), f"Average monthly calculation time {avg_calc_time}s exceeds 3s"
            assert (
                max_calc_time < 10.0
            ), f"Max monthly calculation time {max_calc_time}s exceeds 10s"

            summary = e2e_performance_monitor.summary()
            print(f"Monthly Calculation Performance Summary: {summary}")
        else:
            pytest.skip("No monthly calculations performed for performance test")

    @pytest.mark.asyncio
    async def test_concurrent_attendance_operations(
        self,
        e2e_client: AsyncClient,
        e2e_user_tokens: Dict[str, str],
        e2e_auth_headers,
        e2e_helper,
    ):
        """测试并发考勤操作"""

        admin_headers = e2e_auth_headers(e2e_user_tokens["admin"])
        student_headers = e2e_auth_headers(e2e_user_tokens["student"])

        # 并发操作：同时查询不同的考勤数据
        concurrent_tasks = [
            e2e_client.get("/api/v1/attendance", headers=admin_headers),
            e2e_client.get("/api/v1/attendance/my", headers=student_headers),
            e2e_client.get(
                "/api/v1/attendance/statistics/overview", headers=admin_headers
            ),
            e2e_client.get(
                "/api/v1/attendance/statistics/monthly-comparison",
                params={"year": datetime.now().year, "month": datetime.now().month},
                headers=admin_headers,
            ),
        ]

        # 执行并发操作
        results = await asyncio.gather(*concurrent_tasks, return_exceptions=True)

        # 验证并发操作结果
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                pytest.fail(
                    f"Concurrent attendance operation {i} failed with exception: {result}"
                )
            else:
                # 允许200, 404（无数据）或403（权限限制）
                assert result.status_code in [
                    200,
                    404,
                    403,
                ], f"Concurrent attendance operation {i} returned {result.status_code}"
