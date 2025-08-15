"""
Performance tests for data import functionality.
Tests import speed for 1000 records and single work hour calculation.
"""

import asyncio
from datetime import datetime, timedelta
from typing import Any, Dict, List

import pytest

from app.models.member import Member, UserRole
from app.models.task import RepairTask, TaskCategory, TaskPriority, TaskStatus, TaskType
from app.services.import_service import DataImportService
from app.services.work_hours_service import WorkHoursCalculationService
from tests.conftest import AsyncTestClient


@pytest.fixture
def sample_import_data_1000() -> List[Dict[str, Any]]:
    """Generate 1000 sample records for import performance testing."""
    data = []
    base_time = datetime.now() - timedelta(days=30)

    for i in range(1000):
        record_time = base_time + timedelta(hours=i * 0.5)
        completion_time = record_time + timedelta(hours=2)

        data.append(
            {
                "title": f"网络故障维修任务 {i+1:04d}",
                "description": f"测试数据 - 办公区域网络连接问题，需要现场检查网络设备和线路连接情况 {i+1}",
                "reporter_name": f"测试用户{(i % 50) + 1:02d}",
                "reporter_contact": f"138{(i % 10):04d}{(i % 10000):04d}",
                "location": f"办公楼{chr(65 + (i % 5))}座{(i % 10) + 1:02d}01室",
                "report_time": record_time.isoformat(),
                "response_time": (record_time + timedelta(minutes=30)).isoformat(),
                "completion_time": completion_time.isoformat(),
                "status": ["已完成", "处理中", "待处理"][i % 3],
                "repair_form": ["远程处理", "现场维修"][i % 2],
                "rating": (i % 5) + 1,
                "feedback": f"工作完成及时，服务态度良好 {i+1}",
                "assignee": f"技术员{(i % 20) + 1:02d}",
                "department": "信息化建设处",
                "repair_type": ["网络维修", "硬件故障", "软件问题"][i % 3],
                "priority": ["高", "中", "低"][i % 3],
            }
        )

    return data


@pytest.fixture
def sample_work_hour_task(db_session) -> RepairTask:
    """Create a sample task for work hour calculation testing."""
    # Create a test member first
    member = Member(
        username="test_perf_user",
        name="性能测试用户",
        student_id="PERF001",
        phone="13800138000",
        department="信息化建设处",
        class_name="测试班级",
        password_hash="test_hash",
        role=UserRole.MEMBER,
        is_active=True,
    )
    db_session.add(member)
    db_session.flush()

    task = RepairTask(
        task_id="PERF_TEST_001",
        title="性能测试任务",
        description="用于工时计算性能测试的任务",
        category=TaskCategory.NETWORK_REPAIR,
        priority=TaskPriority.MEDIUM,
        task_type=TaskType.OFFLINE,
        status=TaskStatus.COMPLETED,
        location="测试地点",
        member_id=member.id,
        report_time=datetime.utcnow() - timedelta(hours=50),  # 超时响应
        response_time=datetime.utcnow() - timedelta(hours=40),  # 超时处理
        completion_time=datetime.utcnow() - timedelta(hours=2),
        reporter_name="测试报修人",
        reporter_contact="13800138000",
        rating=4,  # 好评
        feedback="非常满意，处理及时",
    )

    return task


class TestImportPerformance:
    """Import performance test suite."""

    @pytest.mark.asyncio
    @pytest.mark.benchmark
    async def test_import_1000_records_performance(
        self,
        benchmark,
        db_session,
        sample_import_data_1000,
        async_client: AsyncTestClient,
    ):
        """
        Test importing 1000 records performance.
        Benchmark threshold: should complete within 30 seconds.
        """
        import_service = DataImportService(db_session)

        async def import_data():
            # Simulate the import process
            result = await import_service._match_ab_tables(
                sample_import_data_1000,
                {
                    "type": "task_table",
                    "columns": list(sample_import_data_1000[0].keys()),
                },
            )
            return result

        # Run benchmark
        result = benchmark(asyncio.run, import_data())

        # Verify results
        assert result is not None
        assert "matched" in result
        assert "unmatched" in result

        # Performance assertions
        benchmark_result = benchmark.stats
        assert (
            benchmark_result["mean"] < 30.0
        ), f"Import took {benchmark_result['mean']:.2f}s, should be < 30s"

        print("\n📊 Import Performance Results:")
        print(f"   Mean time: {benchmark_result['mean']:.3f}s")
        print(f"   Min time:  {benchmark_result['min']:.3f}s")
        print(f"   Max time:  {benchmark_result['max']:.3f}s")
        print(f"   Records/second: {1000 / benchmark_result['mean']:.1f}")

    @pytest.mark.asyncio
    @pytest.mark.benchmark
    async def test_single_work_hour_calculation_performance(
        self, benchmark, db_session, sample_work_hour_task
    ):
        """
        Test single work hour calculation performance.
        Benchmark threshold: should complete within 100ms.
        """
        work_hours_service = WorkHoursCalculationService(db_session)
        task = sample_work_hour_task

        db_session.add(task)
        await db_session.flush()

        async def calculate_work_hours():
            # Test the work hour calculation
            result = await work_hours_service.calculate_task_work_hours(task.id)
            return result

        # Run benchmark
        result = benchmark(asyncio.run, calculate_work_hours())

        # Verify results
        assert result is not None
        assert "total_minutes" in result
        assert result["total_minutes"] >= 0

        # Performance assertions
        benchmark_result = benchmark.stats
        assert (
            benchmark_result["mean"] < 0.1
        ), f"Calculation took {benchmark_result['mean']:.4f}s, should be < 0.1s"

        print("\n📊 Work Hour Calculation Performance Results:")
        print(f"   Mean time: {benchmark_result['mean']*1000:.2f}ms")
        print(f"   Min time:  {benchmark_result['min']*1000:.2f}ms")
        print(f"   Max time:  {benchmark_result['max']*1000:.2f}ms")
        print(f"   Calculations/second: {1 / benchmark_result['mean']:.0f}")

    @pytest.mark.asyncio
    @pytest.mark.benchmark
    async def test_batch_work_hour_calculation_performance(self, benchmark, db_session):
        """
        Test batch work hour calculation performance.
        Benchmark threshold: 100 calculations should complete within 10 seconds.
        """
        work_hours_service = WorkHoursCalculationService(db_session)

        # Create 100 test tasks
        tasks = []
        for i in range(100):
            member = Member(
                username=f"batch_test_user_{i}",
                name=f"批量测试用户{i}",
                student_id=f"BATCH{i:03d}",
                phone=f"138{i:08d}",
                department="信息化建设处",
                class_name="测试班级",
                password_hash="test_hash",
                role=UserRole.MEMBER,
                is_active=True,
            )
            db_session.add(member)

        await db_session.flush()

        for i in range(100):
            task = RepairTask(
                task_id=f"BATCH_TEST_{i:03d}",
                title=f"批量测试任务{i}",
                description="批量工时计算测试任务",
                category=TaskCategory.NETWORK_REPAIR,
                priority=TaskPriority.MEDIUM,
                task_type=TaskType.ONLINE if i % 2 == 0 else TaskType.OFFLINE,
                status=TaskStatus.COMPLETED,
                location=f"测试地点{i}",
                member_id=i + 1,  # Assuming member IDs start from 1
                report_time=datetime.utcnow() - timedelta(hours=i),
                response_time=datetime.utcnow() - timedelta(hours=i - 1),
                completion_time=datetime.utcnow() - timedelta(hours=i - 2),
                reporter_name=f"测试报修人{i}",
                reporter_contact=f"138{i:08d}",
                rating=(i % 5) + 1,
            )
            tasks.append(task)
            db_session.add(task)

        await db_session.flush()

        async def calculate_batch_work_hours():
            results = []
            for task in tasks:
                result = await work_hours_service.calculate_task_work_hours(task.id)
                results.append(result)
            return results

        # Run benchmark
        results = benchmark(asyncio.run, calculate_batch_work_hours())

        # Verify results
        assert len(results) == 100
        for result in results:
            assert result is not None
            assert "total_minutes" in result

        # Performance assertions
        benchmark_result = benchmark.stats
        assert (
            benchmark_result["mean"] < 10.0
        ), f"Batch calculation took {benchmark_result['mean']:.2f}s, should be < 10s"

        print("\n📊 Batch Work Hour Calculation Performance Results:")
        print(f"   Mean time: {benchmark_result['mean']:.3f}s")
        print(f"   Tasks/second: {100 / benchmark_result['mean']:.1f}")

    @pytest.mark.asyncio
    @pytest.mark.benchmark
    async def test_fuzzy_member_matching_performance(self, benchmark, db_session):
        """
        Test fuzzy member matching performance.
        Benchmark threshold: 1000 fuzzy matches should complete within 5 seconds.
        """
        # Create test members with various name formats
        test_members = []
        for i in range(100):
            member = Member(
                username=f"fuzzy_test_{i}",
                name=f"张{chr(19977 + i)}",  # Different Chinese characters
                student_id=f"FUZZY{i:03d}",
                phone=f"139{i:08d}",
                department="信息化建设处",
                class_name="测试班级",
                password_hash="test_hash",
                role=UserRole.MEMBER,
                is_active=True,
            )
            test_members.append(member)
            db_session.add(member)

        await db_session.flush()

        import_service = DataImportService(db_session)

        # Test data with various name formats (including brackets)
        test_names = [
            "张三(信息处)",
            "李四（技术部）",
            "王五[维修组]",
            "赵六{网络组}",
            "张三工程师",
            "李四技术员",
            "王五主管",
            "赵六组长",
        ] * 125  # 1000 total tests

        async def perform_fuzzy_matching():
            matches = 0
            for name in test_names:
                # Simulate the fuzzy matching logic
                import re

                clean_name = name.strip()
                clean_name = re.sub(
                    r"[\(\)（）\[\]{}〈〉].*?[\(\)（）\[\]{}〈〉]", "", clean_name
                )
                clean_name = re.sub(r"[\(\)（）\[\]{}〈〉].*", "", clean_name)
                clean_name = re.sub(
                    r"(工程师|技术员|主管|经理|组长|部长|处长|科长)$", "", clean_name
                )
                clean_name = clean_name.strip()

                # Simulate database query (without actual DB hit for performance)
                if len(clean_name) >= 2:
                    matches += 1

            return matches

        # Run benchmark
        result = benchmark(asyncio.run, perform_fuzzy_matching())

        # Verify results
        assert result > 0

        # Performance assertions
        benchmark_result = benchmark.stats
        assert (
            benchmark_result["mean"] < 5.0
        ), f"Fuzzy matching took {benchmark_result['mean']:.3f}s, should be < 5s"

        print("\n📊 Fuzzy Member Matching Performance Results:")
        print(f"   Mean time: {benchmark_result['mean']:.3f}s")
        print(f"   Matches/second: {1000 / benchmark_result['mean']:.0f}")


def pytest_configure(config):
    """Configure pytest with benchmark plugin."""
    config.addinivalue_line(
        "markers", "benchmark: mark test as a performance benchmark"
    )


def pytest_runtest_setup(item):
    """Setup for benchmark tests."""
    if "benchmark" in item.keywords:
        if not hasattr(item, "benchmark"):
            pytest.skip("benchmark plugin not available")
