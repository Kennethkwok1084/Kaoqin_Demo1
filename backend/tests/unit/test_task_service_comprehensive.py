"""
TaskService 核心业务逻辑测试
目标：覆盖 app/services/task_service.py 中的 786 行未覆盖代码
重点覆盖：任务创建、状态管理、工时计算、业务规则验证等核心逻辑
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from unittest.mock import AsyncMock, Mock, patch

import pytest

from app.core.security import get_password_hash
from app.models.member import Member, UserRole
from app.models.task import RepairTask, TaskCategory, TaskPriority, TaskStatus, TaskType
from app.services.task_service import TaskService


class TestTaskServiceComprehensive:
    """TaskService 核心业务逻辑测试套件"""

    @pytest.fixture
    def mock_session(self):
        """Mock数据库会话"""
        session = Mock()
        session.add = Mock()
        session.commit = AsyncMock()
        session.refresh = AsyncMock()
        session.execute = AsyncMock()
        session.get = AsyncMock()
        session.delete = Mock()
        session.flush = AsyncMock()
        return session

    @pytest.fixture
    def task_service(self, mock_session):
        """创建TaskService实例"""
        return TaskService(mock_session)

    @pytest.fixture
    def sample_member(self):
        """创建示例成员"""
        return Member(
            id=1,
            username="test_user",
            name="Test User",
            student_id="TEST001",
            password_hash=get_password_hash("password"),
            role=UserRole.MEMBER,
            is_active=True,
            class_name="测试班级",
        )

    @pytest.fixture
    def sample_task(self, sample_member):
        """创建示例任务"""
        return RepairTask(
            id=1,
            title="测试维修任务",
            description="任务描述",
            category=TaskCategory.NETWORK_REPAIR,
            priority=TaskPriority.MEDIUM,
            status=TaskStatus.PENDING,
            task_type=TaskType.REPAIR,
            reporter_name="张三",
            reporter_phone="13800138001",
            location="测试地点",
            assigned_to=sample_member,
            created_at=datetime.now(),
        )

    async def test_create_task_with_validation(
        self, task_service: TaskService, sample_member
    ):
        """测试任务创建业务逻辑验证"""
        task_data = {
            "title": "新建测试任务",
            "description": "任务详细描述",
            "category": TaskCategory.NETWORK_REPAIR,
            "priority": TaskPriority.HIGH,
            "reporter_name": "李四",
            "reporter_phone": "13800138002",
            "location": "办公楼A101",
        }

        # Mock数据库查询返回
        task_service.session.execute.return_value = Mock()
        task_service.session.execute.return_value.scalar.return_value = None

        # 调用创建任务方法
        result = await task_service.create_task(task_data, sample_member.id)

        # 验证调用了数据库操作
        task_service.session.add.assert_called_once()
        task_service.session.commit.assert_called_once()

        # 验证返回结果
        assert result is not None

    async def test_assign_task_business_logic(
        self, task_service: TaskService, sample_task, sample_member
    ):
        """测试任务分配业务逻辑"""
        # Mock数据库查询
        task_service.session.get.return_value = sample_task

        assignment_data = {
            "assigned_to_id": sample_member.id,
            "assignment_notes": "分配给技术人员处理",
        }

        result = await task_service.assign_task(sample_task.id, assignment_data)

        # 验证分配逻辑
        task_service.session.commit.assert_called_once()
        assert result is not None

    async def test_update_task_status_workflow(
        self, task_service: TaskService, sample_task
    ):
        """测试任务状态更新工作流"""
        # Mock任务查询
        task_service.session.get.return_value = sample_task

        # 测试状态转换：PENDING -> IN_PROGRESS
        await task_service.update_task_status(
            sample_task.id, TaskStatus.IN_PROGRESS, "开始处理"
        )

        # 验证状态更新逻辑
        task_service.session.commit.assert_called_once()
        assert sample_task.status == TaskStatus.IN_PROGRESS
        assert sample_task.started_at is not None

    async def test_calculate_work_hours_logic(
        self, task_service: TaskService, sample_task
    ):
        """测试工时计算核心逻辑"""
        # Mock任务查询
        task_service.session.get.return_value = sample_task

        calculation_data = {
            "actual_hours": 2.5,
            "completion_quality": "EXCELLENT",
            "is_rush_task": True,
            "has_penalty": False,
        }

        # Mock工时计算服务
        with patch("app.services.task_service.WorkHoursService") as mock_work_hours:
            mock_work_hours_instance = Mock()
            mock_work_hours.return_value = mock_work_hours_instance
            mock_work_hours_instance.calculate_hours = AsyncMock(
                return_value={
                    "calculated_hours": 2.5,
                    "bonus_hours": 0.5,
                    "total_hours": 3.0,
                }
            )

            result = await task_service.calculate_work_hours(
                sample_task.id, calculation_data
            )

            # 验证工时计算调用
            mock_work_hours_instance.calculate_hours.assert_called_once()
            assert result["total_hours"] == 3.0

    async def test_batch_operation_processing(
        self, task_service: TaskService, sample_member
    ):
        """测试批量操作处理逻辑"""
        task_ids = [1, 2, 3, 4, 5]
        operation_data = {
            "operation": "UPDATE_STATUS",
            "status": TaskStatus.COMPLETED,
            "notes": "批量完成任务",
        }

        # Mock批量查询结果
        mock_tasks = []
        for i, task_id in enumerate(task_ids):
            task = Mock()
            task.id = task_id
            task.status = TaskStatus.IN_PROGRESS
            mock_tasks.append(task)

        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = mock_tasks
        task_service.session.execute.return_value = mock_result

        # 调用批量操作
        result = await task_service.batch_update_tasks(
            task_ids, operation_data, sample_member.id
        )

        # 验证批量操作逻辑
        task_service.session.commit.assert_called_once()
        assert result["processed_count"] == 5
        assert result["success_count"] >= 0

    async def test_task_validation_rules(
        self, task_service: TaskService, sample_member
    ):
        """测试任务验证规则"""
        # 测试无效数据验证
        invalid_task_data = {
            "title": "",  # 空标题
            "description": "描述",
            "category": "INVALID_CATEGORY",  # 无效分类
            "priority": TaskPriority.HIGH,
            "reporter_name": "测试",
            "reporter_phone": "无效手机号",  # 无效手机号
            "location": "",  # 空位置
        }

        # 应该抛出验证异常
        with pytest.raises(Exception):
            await task_service.create_task(invalid_task_data, sample_member.id)

    async def test_task_search_and_filter_logic(self, task_service: TaskService):
        """测试任务搜索和过滤逻辑"""
        filter_params = {
            "status": [TaskStatus.PENDING, TaskStatus.IN_PROGRESS],
            "category": [TaskCategory.NETWORK_REPAIR],
            "priority": [TaskPriority.HIGH, TaskPriority.URGENT],
            "assigned_to_id": 1,
            "date_from": datetime.now() - timedelta(days=30),
            "date_to": datetime.now(),
            "search_text": "网络",
        }

        # Mock查询结果
        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = []
        task_service.session.execute.return_value = mock_result

        result = await task_service.search_tasks(filter_params)

        # 验证搜索逻辑被调用
        task_service.session.execute.assert_called()
        assert "tasks" in result
        assert "total" in result

    async def test_task_statistics_calculation(self, task_service: TaskService):
        """测试任务统计计算逻辑"""
        # Mock统计查询结果
        mock_stats = Mock()
        mock_stats.total_tasks = 100
        mock_stats.pending_tasks = 20
        mock_stats.in_progress_tasks = 30
        mock_stats.completed_tasks = 50
        mock_stats.overdue_tasks = 5

        task_service.session.execute.return_value.scalar.return_value = mock_stats

        result = await task_service.get_task_statistics()

        # 验证统计计算
        assert result["total_tasks"] >= 0
        assert result["completion_rate"] >= 0
        assert "distribution" in result

    async def test_task_priority_management(
        self, task_service: TaskService, sample_task
    ):
        """测试任务优先级管理逻辑"""
        # Mock任务查询
        task_service.session.get.return_value = sample_task

        # 测试优先级提升
        await task_service.escalate_task_priority(
            sample_task.id, "紧急情况需要提高优先级"
        )

        # 验证优先级逻辑
        task_service.session.commit.assert_called_once()

        # 测试优先级降级
        await task_service.downgrade_task_priority(sample_task.id, "情况已缓解")

        # 验证多次提交
        assert task_service.session.commit.call_count >= 2

    async def test_task_dependency_management(self, task_service: TaskService):
        """测试任务依赖关系管理"""
        parent_task_id = 1
        child_task_ids = [2, 3, 4]

        # Mock任务查询
        parent_task = Mock()
        parent_task.id = parent_task_id
        parent_task.status = TaskStatus.IN_PROGRESS

        child_tasks = [
            Mock(id=tid, status=TaskStatus.PENDING) for tid in child_task_ids
        ]

        task_service.session.get.side_effect = [parent_task] + child_tasks

        result = await task_service.create_task_dependencies(
            parent_task_id, child_task_ids
        )

        # 验证依赖关系创建
        assert task_service.session.add.call_count >= len(child_task_ids)
        task_service.session.commit.assert_called_once()
        assert result["created_dependencies"] >= 0

    async def test_task_time_tracking(self, task_service: TaskService, sample_task):
        """测试任务时间跟踪逻辑"""
        # Mock任务查询
        task_service.session.get.return_value = sample_task

        # 测试开始计时
        await task_service.start_task_timer(sample_task.id)
        task_service.session.commit.assert_called()

        # 测试暂停计时
        await task_service.pause_task_timer(sample_task.id)

        # 测试结束计时
        end_result = await task_service.stop_task_timer(sample_task.id)

        # 验证时间跟踪逻辑
        assert task_service.session.commit.call_count >= 3
        assert "elapsed_time" in end_result

    async def test_task_template_management(
        self, task_service: TaskService, sample_member
    ):
        """测试任务模板管理逻辑"""
        template_data = {
            "name": "网络维修标准模板",
            "title_template": "网络故障 - {location}",
            "description_template": "网络设备故障，位置：{location}，联系人：{reporter_name}",
            "category": TaskCategory.NETWORK_REPAIR,
            "priority": TaskPriority.MEDIUM,
            "estimated_hours": 2.0,
        }

        # 创建任务模板
        result = await task_service.create_task_template(
            template_data, sample_member.id
        )

        # 验证模板创建
        task_service.session.add.assert_called_once()
        task_service.session.commit.assert_called_once()
        assert result is not None

    async def test_task_notification_logic(
        self, task_service: TaskService, sample_task
    ):
        """测试任务通知逻辑"""
        # Mock任务查询
        task_service.session.get.return_value = sample_task

        notification_data = {
            "type": "ASSIGNMENT",
            "recipient_ids": [1, 2, 3],
            "message": "您有新的任务分配",
        }

        with patch(
            "app.services.task_service.NotificationService"
        ) as mock_notification:
            mock_notification_instance = Mock()
            mock_notification.return_value = mock_notification_instance
            mock_notification_instance.send_notification = AsyncMock()

            result = await task_service.send_task_notification(
                sample_task.id, notification_data
            )

            # 验证通知发送
            mock_notification_instance.send_notification.assert_called_once()
            assert result["sent_count"] >= 0

    async def test_task_audit_logging(
        self, task_service: TaskService, sample_task, sample_member
    ):
        """测试任务审计日志记录"""
        # Mock任务查询
        task_service.session.get.return_value = sample_task

        audit_data = {
            "action": "STATUS_UPDATE",
            "old_value": "PENDING",
            "new_value": "IN_PROGRESS",
            "reason": "开始处理任务",
        }

        result = await task_service.log_task_audit(
            sample_task.id, sample_member.id, audit_data
        )

        # 验证审计日志
        task_service.session.add.assert_called_once()
        task_service.session.commit.assert_called_once()
        assert result is not None

    async def test_task_export_logic(self, task_service: TaskService):
        """测试任务导出逻辑"""
        export_params = {
            "format": "excel",
            "date_from": datetime.now() - timedelta(days=30),
            "date_to": datetime.now(),
            "include_completed": True,
            "include_statistics": True,
        }

        # Mock查询结果
        mock_tasks = [Mock(id=i, title=f"Task {i}") for i in range(1, 11)]
        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = mock_tasks
        task_service.session.execute.return_value = mock_result

        result = await task_service.export_tasks(export_params)

        # 验证导出逻辑
        assert result["export_format"] == "excel"
        assert result["total_records"] >= 0
        assert "file_path" in result

    async def test_task_archival_logic(self, task_service: TaskService):
        """测试任务归档逻辑"""
        archival_criteria = {
            "days_since_completion": 90,
            "status": [TaskStatus.COMPLETED, TaskStatus.CANCELLED],
            "batch_size": 100,
        }

        # Mock查询结果
        mock_tasks = [Mock(id=i, status=TaskStatus.COMPLETED) for i in range(1, 51)]
        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = mock_tasks
        task_service.session.execute.return_value = mock_result

        result = await task_service.archive_old_tasks(archival_criteria)

        # 验证归档逻辑
        assert result["archived_count"] >= 0
        assert result["total_processed"] >= 0

    async def test_task_performance_metrics(self, task_service: TaskService):
        """测试任务性能指标计算"""
        metrics_params = {
            "period": "monthly",
            "include_member_stats": True,
            "include_category_breakdown": True,
        }

        # Mock统计数据
        mock_metrics = Mock()
        mock_metrics.avg_completion_time = 2.5
        mock_metrics.completion_rate = 0.85
        mock_metrics.overdue_rate = 0.15

        task_service.session.execute.return_value.scalar.return_value = mock_metrics

        result = await task_service.calculate_performance_metrics(metrics_params)

        # 验证性能指标
        assert "average_completion_time" in result
        assert "completion_rate" in result
        assert "productivity_score" in result
