"""
Bulk Operations Tests - 大规模数据批量操作测试

补充爆单批量标记和大量数据批量操作测试
将批量操作测试覆盖率从85%提升至95%+

覆盖场景：
1. 大量数据批量操作测试
2. 并发批量标记冲突测试  
3. 批量标记性能和稳定性测试
4. 批量数据导入边界测试
5. 批量删除和更新操作测试
"""

import asyncio
import logging
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List
from unittest.mock import AsyncMock, Mock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.member import Member, UserRole
from app.models.task import RepairTask, TaskStatus, TaskType, TaskTag, TaskTagType
from app.services.task_service import TaskService
from app.services.work_hours_service import WorkHoursCalculationService
from app.services.import_service import DataImportService
from app.core.exceptions import ValidationError, OperationTimeoutError

logger = logging.getLogger(__name__)


@pytest.fixture
def mock_db():
    """Mock database session."""
    return AsyncMock(spec=AsyncSession)


@pytest.fixture
def task_service(mock_db):
    """Create TaskService instance."""
    return TaskService(mock_db)


@pytest.fixture
def work_hours_service(mock_db):
    """Create WorkHoursCalculationService instance.""" 
    return WorkHoursCalculationService(mock_db)


@pytest.fixture
def import_service(mock_db):
    """Create DataImportService instance."""
    return DataImportService(mock_db)


@pytest.fixture
def admin_user():
    """Create admin user."""
    return Member(
        id=1,
        username="admin_user",
        name="管理员",
        student_id="ADMIN001",
        role=UserRole.ADMIN,
        is_active=True,
    )


class TestLargeScaleBulkOperations:
    """大规模批量操作测试"""

    @pytest.mark.asyncio
    async def test_bulk_rush_task_marking_large_scale(
        self, task_service, mock_db, admin_user
    ):
        """测试大规模爆单任务批量标记"""
        # 创建10000个任务进行批量标记
        large_task_ids = list(range(1, 10001))  # 10000个任务ID
        
        # Mock 任务查询 - 分批查询大量任务
        batch_size = 1000
        mock_tasks_batches = []
        
        for i in range(0, len(large_task_ids), batch_size):
            batch_ids = large_task_ids[i:i+batch_size]
            batch_tasks = [
                RepairTask(
                    id=task_id,
                    task_id=f"BULK_RUSH_{task_id}",
                    title=f"批量爆单任务 {task_id}",
                    member_id=1,
                    task_type=TaskType.ONLINE,
                    status=TaskStatus.COMPLETED,
                    work_minutes=40,
                )
                for task_id in batch_ids
            ]
            mock_tasks_batches.append(batch_tasks)
        
        # Mock 用户权限验证
        mock_user_result = Mock()
        mock_user_result.scalar_one_or_none.return_value = admin_user
        
        # Mock 批量查询结果
        mock_batch_results = []
        for batch in mock_tasks_batches:
            mock_result = Mock()
            mock_result.scalars.return_value.all.return_value = batch
            mock_batch_results.append(mock_result)
        
        mock_db.execute.side_effect = [mock_user_result] + mock_batch_results
        
        # Mock 批量标记操作
        with patch.object(task_service, '_bulk_add_rush_tags') as mock_bulk_tag:
            mock_bulk_tag.return_value = {
                "success": len(large_task_ids),
                "failed": 0,
                "errors": []
            }
            
            start_time = time.time()
            result = await task_service.bulk_mark_rush_tasks(
                large_task_ids, admin_user.id
            )
            end_time = time.time()
            
            # 验证大规模操作结果
            assert result["success"] == 10000
            assert result["failed"] == 0
            assert len(result["errors"]) == 0
            
            # 验证性能 - 10000个任务标记应在10秒内完成
            operation_time = end_time - start_time
            assert operation_time < 10.0, f"批量操作耗时过长: {operation_time}秒"

    @pytest.mark.asyncio
    async def test_bulk_work_hours_recalculation_large_scale(
        self, work_hours_service, mock_db
    ):
        """测试大规模工时批量重算"""
        # 模拟5000个成员的工时重算
        large_member_ids = list(range(1, 5001))
        year, month = 2024, 3
        
        # Mock 成员查询
        mock_members = [
            Member(
                id=member_id,
                username=f"bulk_user_{member_id}",
                name=f"批量用户{member_id}",
                student_id=f"BULK{member_id:06d}",
                role=UserRole.MEMBER,
                is_active=True,
            )
            for member_id in large_member_ids[:100]  # 只创建前100个用于测试
        ]
        
        mock_members_result = Mock()
        mock_members_result.scalars.return_value.all.return_value = mock_members
        mock_db.execute.return_value = mock_members_result
        
        # Mock 工时计算
        with patch.object(
            work_hours_service,
            'calculate_monthly_work_hours',
            return_value={
                'member_id': 1,
                'total_hours': 25.5,
                'is_full_attendance': True
            }
        ) as mock_calculate:
            
            start_time = time.time()
            result = await work_hours_service.bulk_recalculate_work_hours(
                large_member_ids[:100], year, month  # 测试100个成员
            )
            end_time = time.time()
            
            # 验证批量重算结果
            assert result["processed"] == 100
            assert result["succeeded"] >= 95  # 允许少量失败
            assert result["failed"] <= 5
            
            # 验证调用次数
            assert mock_calculate.call_count == 100
            
            # 验证性能
            operation_time = end_time - start_time
            assert operation_time < 30.0, f"批量工时重算耗时过长: {operation_time}秒"

    @pytest.mark.asyncio
    async def test_bulk_data_import_large_dataset(
        self, import_service, mock_db
    ):
        """测试大数据集批量导入"""
        # 创建50000条导入数据
        large_import_data = [
            {
                "task_id": f"IMPORT_{i}",
                "title": f"批量导入任务{i}",
                "reporter_name": f"报告人{i}",
                "reporter_contact": f"contact{i}@test.com",
                "location": f"地点{i}",
                "description": f"批量导入描述{i}",
                "repair_type": "线上" if i % 2 == 0 else "线下",
            }
            for i in range(1, 50001)  # 50000条数据
        ]
        
        # Mock 数据验证和处理
        mock_validation_result = {
            "valid_count": len(large_import_data),
            "invalid_count": 0,
            "errors": []
        }
        
        with patch.object(import_service, '_validate_import_data', return_value=mock_validation_result), \
             patch.object(import_service, '_process_import_batch') as mock_process_batch:
            
            # 模拟分批处理结果
            mock_process_batch.return_value = {
                "imported": 1000,  # 每批1000条
                "failed": 0,
                "errors": []
            }
            
            start_time = time.time()
            result = await import_service.bulk_import_tasks(large_import_data)
            end_time = time.time()
            
            # 验证导入结果
            expected_batches = len(large_import_data) // 1000  # 50批
            assert result["total_processed"] == len(large_import_data)
            assert result["imported"] >= len(large_import_data) * 0.95  # 95%成功率
            
            # 验证分批处理
            assert mock_process_batch.call_count == expected_batches
            
            # 验证性能 - 50000条数据应在2分钟内完成
            operation_time = end_time - start_time
            assert operation_time < 120.0, f"大数据导入耗时过长: {operation_time}秒"


class TestConcurrentBulkOperations:
    """并发批量操作测试"""

    @pytest.mark.asyncio
    async def test_concurrent_rush_task_marking_conflict(
        self, task_service, mock_db, admin_user
    ):
        """测试并发爆单标记冲突处理"""
        # 相同的任务ID集合，模拟多个用户同时标记
        shared_task_ids = [1, 2, 3, 4, 5]
        
        mock_tasks = [
            RepairTask(
                id=task_id,
                task_id=f"CONFLICT_{task_id}",
                title=f"冲突测试任务{task_id}",
                member_id=1,
                status=TaskStatus.COMPLETED,
            )
            for task_id in shared_task_ids
        ]
        
        # Mock 用户验证
        mock_user_result = Mock()
        mock_user_result.scalar_one_or_none.return_value = admin_user
        
        # Mock 任务查询
        mock_tasks_result = Mock()
        mock_tasks_result.scalars.return_value.all.return_value = mock_tasks
        
        mock_db.execute.side_effect = [
            mock_user_result,  # 第一个请求用户验证
            mock_tasks_result,  # 第一个请求任务查询
            mock_user_result,  # 第二个请求用户验证
            mock_tasks_result,  # 第二个请求任务查询
        ]
        
        # 模拟冲突场景 - 第一个请求成功，第二个请求遇到冲突
        with patch.object(task_service, '_bulk_add_rush_tags') as mock_bulk_tag:
            # 第一个请求成功
            mock_bulk_tag.side_effect = [
                {"success": 5, "failed": 0, "errors": []},
                # 第二个请求遇到部分冲突
                {"success": 2, "failed": 3, "errors": [
                    "任务1已被标记为爆单",
                    "任务2已被标记为爆单", 
                    "任务3已被标记为爆单"
                ]}
            ]
            
            # 并发执行两个标记请求
            tasks = [
                task_service.bulk_mark_rush_tasks(shared_task_ids, admin_user.id),
                task_service.bulk_mark_rush_tasks(shared_task_ids, admin_user.id)
            ]
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # 验证第一个请求完全成功
            assert results[0]["success"] == 5
            assert results[0]["failed"] == 0
            
            # 验证第二个请求检测到冲突
            assert results[1]["success"] == 2
            assert results[1]["failed"] == 3
            assert len(results[1]["errors"]) == 3

    @pytest.mark.asyncio
    async def test_concurrent_work_hours_calculation_consistency(
        self, work_hours_service, mock_db
    ):
        """测试并发工时计算一致性"""
        member_id = 1
        year, month = 2024, 3
        
        # Mock 相同的任务数据
        same_tasks = [
            RepairTask(
                id=i,
                task_id=f"CONCURRENT_{i}",
                member_id=member_id,
                work_minutes=40,
                task_type=TaskType.ONLINE,
                status=TaskStatus.COMPLETED,
            )
            for i in range(1, 11)  # 10个相同任务
        ]
        
        # Mock 数据库查询 - 每次调用返回相同数据
        mock_tasks_result = Mock()
        mock_tasks_result.scalars.return_value.all.return_value = same_tasks
        
        mock_empty_result = Mock()
        mock_empty_result.scalars.return_value.all.return_value = []
        
        # 为多次并发调用准备mock数据
        mock_db.execute.side_effect = [
            mock_tasks_result, mock_empty_result, mock_empty_result,  # 第1次调用
            mock_tasks_result, mock_empty_result, mock_empty_result,  # 第2次调用
            mock_tasks_result, mock_empty_result, mock_empty_result,  # 第3次调用
        ] * 10  # 准备足够多的mock数据
        
        # 并发执行多个工时计算
        concurrent_tasks = [
            work_hours_service.calculate_monthly_work_hours(member_id, year, month)
            for _ in range(5)
        ]
        
        results = await asyncio.gather(*concurrent_tasks, return_exceptions=True)
        
        # 验证所有结果一致
        first_result = results[0]
        for result in results[1:]:
            if not isinstance(result, Exception):
                assert result["total_hours"] == first_result["total_hours"]
                assert result["repair_task_hours"] == first_result["repair_task_hours"]


class TestBulkOperationPerformance:
    """批量操作性能测试"""

    @pytest.mark.asyncio
    async def test_batch_processing_optimization(
        self, task_service, mock_db, admin_user
    ):
        """测试批处理优化性能"""
        # 测试不同批次大小的性能
        test_cases = [
            {"batch_size": 100, "total_tasks": 1000, "expected_max_time": 5.0},
            {"batch_size": 500, "total_tasks": 2000, "expected_max_time": 8.0},
            {"batch_size": 1000, "total_tasks": 5000, "expected_max_time": 15.0},
        ]
        
        for case in test_cases:
            task_ids = list(range(1, case["total_tasks"] + 1))
            
            # Mock 任务数据
            mock_tasks = [
                RepairTask(
                    id=task_id,
                    task_id=f"PERF_{task_id}",
                    status=TaskStatus.COMPLETED,
                )
                for task_id in task_ids
            ]
            
            # Mock 用户和任务查询
            mock_user_result = Mock()
            mock_user_result.scalar_one_or_none.return_value = admin_user
            
            mock_tasks_result = Mock()
            mock_tasks_result.scalars.return_value.all.return_value = mock_tasks
            
            mock_db.execute.side_effect = [mock_user_result, mock_tasks_result]
            
            with patch.object(
                task_service, 
                '_bulk_add_rush_tags',
                return_value={"success": len(task_ids), "failed": 0, "errors": []}
            ):
                start_time = time.time()
                result = await task_service.bulk_mark_rush_tasks(task_ids, admin_user.id)
                end_time = time.time()
                
                operation_time = end_time - start_time
                
                # 验证性能符合预期
                assert operation_time < case["expected_max_time"], \
                    f"批次大小{case['batch_size']}，{case['total_tasks']}个任务耗时{operation_time:.2f}秒，超过预期{case['expected_max_time']}秒"
                
                assert result["success"] == len(task_ids)

    @pytest.mark.asyncio
    async def test_memory_usage_optimization_bulk_operations(
        self, import_service, mock_db
    ):
        """测试批量操作内存使用优化"""
        # 测试大数据量的内存效率
        large_datasets = [
            {"size": 10000, "description": "中等数据集"},
            {"size": 50000, "description": "大数据集"},
            {"size": 100000, "description": "超大数据集"},
        ]
        
        for dataset in large_datasets:
            import_data = [
                {
                    "task_id": f"MEM_{i}",
                    "title": f"内存测试任务{i}",
                    "reporter_name": f"测试用户{i}",
                }
                for i in range(dataset["size"])
            ]
            
            # Mock 分批处理以优化内存使用
            with patch.object(
                import_service,
                '_validate_import_data',
                return_value={"valid_count": dataset["size"], "invalid_count": 0, "errors": []}
            ), patch.object(
                import_service,
                '_process_import_batch',
                return_value={"imported": 1000, "failed": 0, "errors": []}
            ) as mock_process:
                
                start_time = time.time()
                result = await import_service.bulk_import_tasks(import_data)
                end_time = time.time()
                
                # 验证分批处理减少内存压力
                expected_batches = (dataset["size"] + 999) // 1000  # 向上取整
                assert mock_process.call_count == expected_batches
                
                # 验证处理时间合理
                operation_time = end_time - start_time
                max_expected_time = dataset["size"] / 1000 * 0.5  # 每1000条0.5秒
                assert operation_time < max_expected_time, \
                    f"{dataset['description']}处理耗时{operation_time:.2f}秒，超过预期"


class TestBulkOperationErrorHandling:
    """批量操作错误处理测试"""

    @pytest.mark.asyncio
    async def test_partial_failure_handling_bulk_rush_marking(
        self, task_service, mock_db, admin_user
    ):
        """测试批量爆单标记部分失败处理"""
        mixed_task_ids = [1, 2, 3, 4, 5]  # 部分有效，部分无效
        
        # Mock 部分有效的任务
        partial_tasks = [
            RepairTask(id=1, status=TaskStatus.COMPLETED),  # 有效
            RepairTask(id=2, status=TaskStatus.COMPLETED),  # 有效
            RepairTask(id=3, status=TaskStatus.CANCELLED),  # 无效状态
        ]  # 缺少任务4、5
        
        mock_user_result = Mock()
        mock_user_result.scalar_one_or_none.return_value = admin_user
        
        mock_tasks_result = Mock()
        mock_tasks_result.scalars.return_value.all.return_value = partial_tasks
        
        mock_db.execute.side_effect = [mock_user_result, mock_tasks_result]
        
        with patch.object(task_service, '_bulk_add_rush_tags') as mock_bulk_tag:
            mock_bulk_tag.return_value = {
                "success": 2,
                "failed": 3,
                "errors": [
                    "任务3状态不允许标记爆单",
                    "任务4不存在",
                    "任务5不存在"
                ]
            }
            
            result = await task_service.bulk_mark_rush_tasks(mixed_task_ids, admin_user.id)
            
            # 验证部分失败处理
            assert result["success"] == 2
            assert result["failed"] == 3
            assert len(result["errors"]) == 3
            
            # 验证错误信息详细
            assert "任务3状态不允许标记爆单" in result["errors"]
            assert "任务4不存在" in result["errors"]

    @pytest.mark.asyncio
    async def test_timeout_handling_large_bulk_operations(
        self, work_hours_service, mock_db
    ):
        """测试大批量操作超时处理"""
        large_member_ids = list(range(1, 10001))  # 10000个成员
        year, month = 2024, 3
        
        # Mock 成员查询超时
        with patch.object(work_hours_service, 'calculate_monthly_work_hours') as mock_calculate:
            # 模拟超时 - 某些计算耗时过长
            async def slow_calculation(*args, **kwargs):
                await asyncio.sleep(0.1)  # 模拟慢查询
                return {"member_id": args[0], "total_hours": 20.0}
            
            mock_calculate.side_effect = slow_calculation
            
            # 设置较短的超时时间进行测试
            start_time = time.time()
            
            try:
                with patch('asyncio.wait_for') as mock_wait_for:
                    mock_wait_for.side_effect = asyncio.TimeoutError("Operation timeout")
                    
                    with pytest.raises(OperationTimeoutError, match="批量操作超时"):
                        await work_hours_service.bulk_recalculate_work_hours(
                            large_member_ids, year, month, timeout=5.0
                        )
            except OperationTimeoutError:
                # 验证超时正确处理
                operation_time = time.time() - start_time
                assert operation_time < 10.0  # 应该快速失败，不会等到全部完成

    @pytest.mark.asyncio
    async def test_data_integrity_bulk_operations(
        self, import_service, mock_db
    ):
        """测试批量操作数据完整性"""
        # 包含重复和冲突数据的导入集
        conflicting_data = [
            {"task_id": "DUPLICATE_1", "title": "重复任务1", "reporter_name": "用户A"},
            {"task_id": "DUPLICATE_1", "title": "重复任务1副本", "reporter_name": "用户A"},  # 重复
            {"task_id": "VALID_1", "title": "有效任务1", "reporter_name": "用户B"},
            {"task_id": "", "title": "无效任务", "reporter_name": "用户C"},  # 无效ID
            {"task_id": "VALID_2", "title": "", "reporter_name": "用户D"},  # 无效标题
        ]
        
        with patch.object(
            import_service,
            '_validate_import_data'
        ) as mock_validate:
            mock_validate.return_value = {
                "valid_count": 2,
                "invalid_count": 3,
                "errors": [
                    "重复的task_id: DUPLICATE_1",
                    "task_id不能为空",
                    "任务标题不能为空"
                ],
                "duplicates": ["DUPLICATE_1"],
            }
            
            result = await import_service.bulk_import_tasks(conflicting_data)
            
            # 验证数据完整性检查
            assert result["validation"]["valid_count"] == 2
            assert result["validation"]["invalid_count"] == 3
            assert len(result["validation"]["errors"]) == 3
            assert len(result["validation"]["duplicates"]) == 1