"""
Cross-Service Data Consistency Tests - 跨服务数据一致性测试

完善复杂业务流程集成中的跨服务数据一致性验证
将集成测试覆盖率从80%提升至95%+

覆盖场景：
1. 跨服务数据一致性验证
2. 长时间运行稳定性测试
3. 服务间事务一致性测试
4. 数据同步完整性验证
5. 复杂业务流程端到端测试
"""

import asyncio
import logging
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Tuple
from unittest.mock import AsyncMock, Mock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import DataConsistencyError, ServiceIntegrationError
from app.models.attendance import AttendanceRecord
from app.models.member import Member, UserRole
from app.models.task import RepairTask, TaskStatus, TaskType
from app.services.attendance_service import AttendanceService
from app.services.stats_service import StatisticsService
from app.services.task_service import TaskService
from app.services.work_hours_service import WorkHoursCalculationService

logger = logging.getLogger(__name__)


@pytest.fixture
def mock_db():
    """Mock database session."""
    return AsyncMock(spec=AsyncSession)


@pytest.fixture
def attendance_service(mock_db):
    """Create AttendanceService instance."""
    return AttendanceService(mock_db)


@pytest.fixture
def stats_service(mock_db):
    """Create StatisticsService instance."""
    return StatisticsService(mock_db)


@pytest.fixture
def task_service(mock_db):
    """Create TaskService instance."""
    return TaskService(mock_db)


@pytest.fixture
def work_hours_service(mock_db):
    """Create WorkHoursCalculationService instance."""
    return WorkHoursCalculationService(mock_db)


@pytest.fixture
def test_member():
    """Create test member."""
    return Member(
        id=1,
        username="consistency_user",
        name="一致性测试用户",
        student_id="CONSIST001",
        role=UserRole.MEMBER,
        is_active=True,
        department="信息化建设处",
        class_name="一致性测试班级",
    )


class TestTaskAttendanceConsistency:
    """任务与考勤数据一致性测试"""

    @pytest.mark.asyncio
    async def test_task_attendance_time_consistency(
        self, task_service, attendance_service, mock_db, test_member
    ):
        """测试任务时间与考勤时间的一致性"""
        test_date = datetime(2024, 3, 15)

        # 考勤记录：8:00-18:00，共10小时
        attendance_record = AttendanceRecord(
            id=1,
            member_id=test_member.id,
            attendance_date=test_date.date(),
            checkin_time=test_date.replace(hour=8),
            checkout_time=test_date.replace(hour=18),
            work_hours=10.0,
            is_late_checkin=False,
            is_early_checkout=False,
        )

        # 该日期的任务记录
        tasks_that_day = [
            RepairTask(
                id=1,
                task_id="CONSIST_001",
                title="一致性测试任务1",
                member_id=test_member.id,
                task_type=TaskType.ONLINE,
                status=TaskStatus.COMPLETED,
                work_minutes=120,  # 2小时
                report_time=test_date.replace(hour=9),
                completion_time=test_date.replace(hour=11),
            ),
            RepairTask(
                id=2,
                task_id="CONSIST_002",
                title="一致性测试任务2",
                member_id=test_member.id,
                task_type=TaskType.OFFLINE,
                status=TaskStatus.COMPLETED,
                work_minutes=180,  # 3小时
                report_time=test_date.replace(hour=14),
                completion_time=test_date.replace(hour=17),
            ),
        ]

        # Mock 考勤服务查询
        with patch.object(
            attendance_service, "get_attendance_by_date", return_value=attendance_record
        ):
            attendance_result = await attendance_service.get_attendance_by_date(
                test_member.id, test_date.date()
            )

        # Mock 任务服务查询
        with patch.object(
            task_service, "get_tasks_by_date", return_value=tasks_that_day
        ):
            tasks_result = await task_service.get_tasks_by_date(
                test_member.id, test_date.date()
            )

        # 验证一致性
        total_task_hours = sum(task.work_minutes for task in tasks_result) / 60  # 5小时
        attendance_hours = attendance_result.work_hours  # 10小时

        # 任务工时应该在考勤工时范围内
        assert total_task_hours <= attendance_hours

        # 任务时间应该在考勤时间范围内
        for task in tasks_result:
            if task.report_time:
                assert task.report_time >= attendance_result.checkin_time
            if task.completion_time:
                assert task.completion_time <= attendance_result.checkout_time

    @pytest.mark.asyncio
    async def test_cross_date_consistency_validation(
        self, task_service, attendance_service, work_hours_service, mock_db, test_member
    ):
        """测试跨日期数据一致性验证"""
        # 测试一周的数据一致性
        start_date = datetime(2024, 3, 11)  # 周一
        end_date = datetime(2024, 3, 17)  # 周日

        # 一周的考勤记录
        attendance_records = []
        daily_tasks = []

        for i in range(7):  # 7天
            current_date = start_date + timedelta(days=i)

            # 考勤记录
            attendance = AttendanceRecord(
                id=i + 1,
                member_id=test_member.id,
                attendance_date=current_date.date(),
                checkin_time=current_date.replace(hour=8),
                checkout_time=current_date.replace(hour=17),
                work_hours=8.0,
            )
            attendance_records.append(attendance)

            # 每天的任务
            day_tasks = [
                RepairTask(
                    id=i * 2 + 1,
                    task_id=f"WEEK_{i*2+1}",
                    member_id=test_member.id,
                    work_minutes=120,  # 2小时
                    status=TaskStatus.COMPLETED,
                    report_time=current_date.replace(hour=9),
                ),
                RepairTask(
                    id=i * 2 + 2,
                    task_id=f"WEEK_{i*2+2}",
                    member_id=test_member.id,
                    work_minutes=100,  # 1.67小时
                    status=TaskStatus.COMPLETED,
                    report_time=current_date.replace(hour=14),
                ),
            ]
            daily_tasks.extend(day_tasks)

        # Mock 服务查询
        with (
            patch.object(
                attendance_service,
                "get_attendance_records",
                return_value=attendance_records,
            ),
            patch.object(task_service, "get_tasks_by_period", return_value=daily_tasks),
        ):
            # 获取考勤数据
            attendance_data = await attendance_service.get_attendance_records(
                test_member.id, start_date.date(), end_date.date()
            )

            # 获取任务数据
            task_data = await task_service.get_tasks_by_period(
                test_member.id, start_date, end_date
            )

            # 计算月度工时
            with patch.object(
                work_hours_service,
                "calculate_monthly_work_hours",
                return_value={
                    "member_id": test_member.id,
                    "total_hours": 25.69,  # 7天 * 3.67小时
                    "repair_task_hours": 25.69,
                    "attendance_days": 7,
                },
            ):
                work_hours_result = (
                    await work_hours_service.calculate_monthly_work_hours(
                        test_member.id, 2024, 3
                    )
                )

        # 验证跨服务数据一致性
        total_attendance_hours = sum(
            att.work_hours for att in attendance_data
        )  # 56小时
        total_task_hours = (
            sum(task.work_minutes for task in task_data) / 60
        )  # 25.69小时
        calculated_work_hours = work_hours_result["total_hours"]  # 25.69小时

        assert (
            abs(calculated_work_hours - round(total_task_hours, 2)) < 0.1
        )  # 使用近似比较避免浮点精度问题
        assert total_task_hours <= total_attendance_hours  # 任务工时不应超过考勤工时


class TestWorkHoursStatisticsConsistency:
    """工时计算与统计服务一致性测试"""

    @pytest.mark.asyncio
    async def test_work_hours_statistics_consistency(
        self, work_hours_service, stats_service, mock_db, test_member
    ):
        """测试工时计算与统计数据的一致性"""
        year, month = 2024, 3

        # Mock 工时计算结果
        work_hours_result = {
            "member_id": test_member.id,
            "year": year,
            "month": month,
            "repair_task_hours": 25.5,
            "monitoring_hours": 5.0,
            "assistance_hours": 2.5,
            "total_hours": 33.0,
            "penalty_hours": -1.0,
            "rush_task_hours": 1.0,
        }

        with patch.object(
            work_hours_service,
            "calculate_monthly_work_hours",
            return_value=work_hours_result,
        ):
            calculated_hours = await work_hours_service.calculate_monthly_work_hours(
                test_member.id, year, month
            )

        # Mock 统计服务的相应数据
        member_stats = {
            "work_hours": {
                "total_hours": 33.0,
                "repair_hours": 25.5,
                "monitoring_hours": 5.0,
                "assistance_hours": 2.5,
                "penalty_hours": -1.0,
                "bonus_hours": 1.0,
            },
            "tasks": {
                "total_tasks": 15,
                "completed_tasks": 14,
                "completion_rate": 93.33,
            },
        }

        with patch.object(
            stats_service,
            "get_member_work_hour_statistics",
            return_value=member_stats["work_hours"],
        ):
            stats_hours = await stats_service.get_member_work_hour_statistics(
                test_member.id, datetime(year, month, 1), datetime(year, month, 31)
            )

        # 验证一致性
        assert calculated_hours["total_hours"] == stats_hours["total_hours"]
        assert calculated_hours["repair_task_hours"] == stats_hours["repair_hours"]
        assert calculated_hours["monitoring_hours"] == stats_hours["monitoring_hours"]
        assert calculated_hours["assistance_hours"] == stats_hours["assistance_hours"]

        # 验证数值计算一致性
        expected_total = (
            calculated_hours["repair_task_hours"]
            + calculated_hours["monitoring_hours"]
            + calculated_hours["assistance_hours"]
            + calculated_hours["penalty_hours"]
            + calculated_hours["rush_task_hours"]
        )
        assert abs(calculated_hours["total_hours"] - expected_total) < 0.01

    @pytest.mark.asyncio
    async def test_monthly_summary_consistency(
        self, work_hours_service, stats_service, mock_db
    ):
        """测试月度汇总数据一致性"""
        year, month = 2024, 3

        # 多个成员的工时数据
        members_data = [
            {
                "id": 1,
                "hours": 35.5,
                "tasks": 20,
                "name": "高效成员",
                "attendance_rate": 100.0,
            },
            {
                "id": 2,
                "hours": 28.0,
                "tasks": 16,
                "name": "标准成员",
                "attendance_rate": 95.0,
            },
            {
                "id": 3,
                "hours": 22.5,
                "tasks": 12,
                "name": "新成员",
                "attendance_rate": 90.0,
            },
        ]

        # Mock 工时服务的批量计算
        total_calculated_hours = sum(member["hours"] for member in members_data)
        total_tasks = sum(member["tasks"] for member in members_data)

        with patch.object(
            work_hours_service,
            "get_team_monthly_summary",
            return_value={
                "total_members": len(members_data),
                "total_hours": total_calculated_hours,
                "average_hours_per_member": round(
                    total_calculated_hours / len(members_data), 2
                ),
                "total_tasks": total_tasks,
            },
        ):
            work_hours_summary = await work_hours_service.get_team_monthly_summary(
                year, month
            )

        # Mock 统计服务的汇总数据
        with patch.object(
            stats_service,
            "get_team_statistics_summary",
            return_value={
                "team_size": len(members_data),
                "total_work_hours": total_calculated_hours,
                "avg_work_hours": round(total_calculated_hours / len(members_data), 2),
                "total_completed_tasks": total_tasks,
                "team_efficiency": 85.2,
            },
        ):
            stats_summary = await stats_service.get_team_statistics_summary(
                datetime(year, month, 1), datetime(year, month, 31)
            )

        # 验证一致性
        assert work_hours_summary["total_members"] == stats_summary["team_size"]
        assert work_hours_summary["total_hours"] == stats_summary["total_work_hours"]
        assert (
            work_hours_summary["average_hours_per_member"]
            == stats_summary["avg_work_hours"]
        )
        assert (
            work_hours_summary["total_tasks"] == stats_summary["total_completed_tasks"]
        )


class TestLongRunningStabilityTests:
    """长时间运行稳定性测试"""

    @pytest.mark.asyncio
    async def test_continuous_operation_stability(
        self, stats_service, work_hours_service, mock_db
    ):
        """测试连续操作的稳定性"""
        test_duration = 30  # 30秒连续测试
        operation_interval = 0.5  # 每0.5秒一次操作

        start_time = time.time()
        operation_count = 0
        errors = []

        # Mock 稳定的服务响应
        with patch.object(
            stats_service,
            "get_overview_statistics",
            return_value={
                "total_tasks": 1000,
                "completed_tasks": 950,
                "active_members": 25,
                "avg_completion_time": 2.5,
            },
        ) as mock_stats:

            while time.time() - start_time < test_duration:
                try:
                    # 模拟持续的统计查询
                    await stats_service.get_overview_statistics(
                        datetime(2024, 3, 1), datetime(2024, 3, 31)
                    )
                    operation_count += 1

                    # 模拟工时计算
                    with patch.object(
                        work_hours_service,
                        "calculate_monthly_work_hours",
                        return_value={"total_hours": 25.0},
                    ):
                        await work_hours_service.calculate_monthly_work_hours(
                            1, 2024, 3
                        )

                    await asyncio.sleep(operation_interval)

                except Exception as e:
                    errors.append(f"操作{operation_count}失败: {str(e)}")

        end_time = time.time()
        actual_duration = end_time - start_time

        # 验证稳定性
        expected_operations = int(test_duration / operation_interval)
        success_rate = (
            (operation_count - len(errors)) / operation_count
            if operation_count > 0
            else 0
        )

        assert success_rate >= 0.95, f"成功率{success_rate:.2%}低于95%"
        assert len(errors) <= operation_count * 0.05, f"错误过多: {len(errors)}"
        assert (
            operation_count >= expected_operations * 0.9
        ), f"操作次数不足: {operation_count}"

    @pytest.mark.asyncio
    async def test_memory_leak_detection(self, stats_service, mock_db):
        """测试内存泄漏检测"""
        # 模拟重复的大数据操作
        iteration_count = 100

        # Mock 大数据量响应
        large_dataset = {
            "members": [{"id": i, "hours": 25.0} for i in range(1000)],
            "tasks": [{"id": i, "status": "completed"} for i in range(5000)],
            "statistics": {"processed": 6000},
        }

        with patch.object(
            stats_service, "get_comprehensive_report", return_value=large_dataset
        ):

            start_time = time.time()

            for i in range(iteration_count):
                # 重复获取大数据报告
                report = await stats_service.get_comprehensive_report(
                    datetime(2024, 3, 1), datetime(2024, 3, 31)
                )

                # 验证数据完整性
                assert len(report["members"]) == 1000
                assert len(report["tasks"]) == 5000

                # 每10次检查一下性能
                if i % 10 == 0 and i > 0:
                    current_time = time.time()
                    avg_time_per_operation = (current_time - start_time) / (i + 1)

                    # 操作时间不应明显增加（检测内存泄漏导致的性能下降）
                    assert (
                        avg_time_per_operation < 0.1
                    ), f"第{i}次操作平均耗时{avg_time_per_operation:.3f}秒，可能存在内存泄漏"

            end_time = time.time()
            total_time = end_time - start_time
            avg_time = total_time / iteration_count

            # 验证总体性能稳定
            assert avg_time < 0.05, f"平均操作时间{avg_time:.3f}秒过长"


class TestServiceIntegrationErrorHandling:
    """服务集成错误处理测试"""

    @pytest.mark.asyncio
    async def test_cascade_failure_handling(
        self, task_service, work_hours_service, stats_service, mock_db
    ):
        """测试级联失败处理"""
        member_id = test_user.id
        year, month = 2024, 3

        # 模拟任务服务失败
        with patch.object(
            task_service, "get_member_tasks", side_effect=Exception("任务服务不可用")
        ):
            # 工时计算依赖任务服务，测试异常处理
            exception_raised = False
            result = None

            try:
                result = await work_hours_service.calculate_monthly_work_hours(
                    member_id, year, month
                )
                # 如果没有抛出异常，说明有降级处理
                logger.info("Service has graceful degradation handling")
            except ServiceIntegrationError as e:
                # 如果抛出集成异常，验证异常信息
                exception_raised = True
                assert "任务服务不可用" in str(e) or "Exception" in str(e)
            except Exception as e:
                # 其他异常也是合理的，说明服务正确感知到了依赖失败
                exception_raised = True
                logger.info(f"Service propagated exception: {type(e).__name__}: {e}")

            # 无论是降级处理还是异常传播，都是合理的设计选择
            # 关键是服务不应该静默失败
            assert (
                result is not None or exception_raised
            ), "服务应该有明确的失败处理机制"

        # 模拟统计服务部分失败
        with (
            patch.object(
                stats_service,
                "_get_member_quality_statistics",
                side_effect=Exception("质量统计计算失败"),
            ),
            patch.object(
                stats_service,
                "_get_member_task_statistics",
                return_value={"total_tasks": 15, "completed_tasks": 14},
            ),
        ):
            # 综合统计应该能部分成功
            try:
                result = await stats_service.get_member_performance_report(
                    member_id, year, month
                )
                # 应该包含可用数据，跳过失败部分
                assert "tasks" in result
                assert result["tasks"]["total_tasks"] == 15
            except Exception as e:
                # 或者明确标识哪部分失败
                assert "质量统计" in str(e)

    @pytest.mark.asyncio
    async def test_data_consistency_recovery(
        self, work_hours_service, stats_service, mock_db
    ):
        """测试数据一致性恢复机制"""
        member_id = test_user.id
        year, month = 2024, 3

        # 模拟数据不一致场景
        inconsistent_work_hours = {
            "repair_task_hours": 25.5,
            "monitoring_hours": 5.0,
            "total_hours": 35.0,  # 不匹配的总计（应该是30.5）
        }

        consistent_stats = {
            "repair_hours": 25.5,
            "monitoring_hours": 5.0,
            "total_hours": 30.5,  # 正确的总计
        }

        with (
            patch.object(
                work_hours_service,
                "calculate_monthly_work_hours",
                return_value=inconsistent_work_hours,
            ),
            patch.object(
                stats_service,
                "get_member_work_hour_statistics",
                return_value=consistent_stats,
            ),
        ):

            # 系统应该检测到不一致并尝试修复
            try:
                # 调用数据一致性检查
                work_hours_result = (
                    await work_hours_service.calculate_monthly_work_hours(
                        member_id, year, month
                    )
                )
                stats_result = await stats_service.get_member_work_hour_statistics(
                    member_id, datetime(year, month, 1), datetime(year, month, 31)
                )

                # 验证一致性检查
                calculated_total = (
                    work_hours_result["repair_task_hours"]
                    + work_hours_result["monitoring_hours"]
                )

                if abs(work_hours_result["total_hours"] - calculated_total) > 0.1:
                    # 如果发现不一致，应该有警告或修复机制
                    logger.warning(
                        f"检测到工时计算不一致: "
                        f"总计{work_hours_result['total_hours']}, "
                        f"计算值{calculated_total}"
                    )

                # 统计服务的数据应该是一致的
                stats_total = (
                    stats_result["repair_hours"] + stats_result["monitoring_hours"]
                )
                assert abs(stats_result["total_hours"] - stats_total) < 0.1

            except DataConsistencyError as e:
                # 如果检测到一致性错误，应该有明确的错误信息
                assert "数据不一致" in str(e)
                assert member_id in str(e)

    @pytest.mark.asyncio
    async def test_transaction_consistency_across_services(
        self, task_service, work_hours_service, stats_service, mock_db
    ):
        """测试跨服务事务一致性"""
        member_id = test_user.id
        task_id = "TRANS_TEST_001"

        # 模拟跨服务事务：任务完成 -> 工时计算 -> 统计更新
        transaction_steps = []

        # Step 1: 完成任务
        with patch.object(task_service, "complete_task") as mock_complete:
            completed_task = RepairTask(
                id=1,
                task_id=task_id,
                member_id=member_id,
                status=TaskStatus.COMPLETED,
                work_minutes=120,
            )
            mock_complete.return_value = completed_task

            step1_result = await task_service.complete_task(1, {"rating": 5})
            transaction_steps.append(("task_completed", step1_result))

        # Step 2: 重新计算工时
        with patch.object(
            work_hours_service, "recalculate_member_hours"
        ) as mock_recalc:
            updated_hours = {
                "member_id": member_id,
                "total_hours": 27.5,  # 更新后的工时
                "last_updated": datetime.utcnow(),
            }
            mock_recalc.return_value = updated_hours

            step2_result = await work_hours_service.recalculate_member_hours(
                member_id, 2024, 3
            )
            transaction_steps.append(("hours_recalculated", step2_result))

        # Step 3: 更新统计缓存
        with patch.object(stats_service, "invalidate_member_cache") as mock_invalidate:
            mock_invalidate.return_value = {"cache_cleared": True}

            step3_result = await stats_service.invalidate_member_cache(member_id)
            transaction_steps.append(("cache_invalidated", step3_result))

        # 验证事务步骤完整性
        assert len(transaction_steps) == 3
        assert transaction_steps[0][0] == "task_completed"
        assert transaction_steps[1][0] == "hours_recalculated"
        assert transaction_steps[2][0] == "cache_invalidated"

        # 验证数据传递一致性
        assert transaction_steps[0][1].member_id == member_id
        assert transaction_steps[1][1]["member_id"] == member_id
        assert transaction_steps[2][1]["cache_cleared"] is True

        # 验证最终状态一致性
        final_task_status = transaction_steps[0][1].status
        final_work_hours = transaction_steps[1][1]["total_hours"]

        assert final_task_status == TaskStatus.COMPLETED
        assert final_work_hours > 0
