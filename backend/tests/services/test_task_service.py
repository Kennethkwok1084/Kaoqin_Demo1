"""
任务管理服务测试用例
测试核心业务逻辑：任务创建、状态管理、标签处理、工时计算等
"""

from datetime import date, datetime, timedelta
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.core.exceptions import PermissionDeniedError
from app.models.member import Member, UserRole
from app.models.task import (
    AssistanceTask,
    MonitoringTask,
    RepairTask,
    TaskCategory,
    TaskPriority,
    TaskStatus,
    TaskTag,
    TaskTagType,
    TaskType,
)
from app.services.task_service import TaskService


class TestTaskServiceInit:
    """测试任务服务初始化"""

    def test_init_with_valid_db_session(self):
        """测试有效数据库会话初始化"""
        mock_db = AsyncMock()
        service = TaskService(mock_db)

        assert service.db is mock_db
        assert service.work_hours_service is not None
        assert service.rush_task_service is not None

    def test_init_with_none_db_session(self):
        """测试空数据库会话初始化失败"""
        with pytest.raises(ValueError, match="Database session is required"):
            TaskService(None)


class TestTaskServiceBasic:
    """测试任务服务基础功能"""

    @pytest.fixture
    def mock_db(self):
        """创建模拟数据库会话"""
        return AsyncMock()

    @pytest.fixture
    def service(self, mock_db):
        """创建任务服务实例"""
        return TaskService(mock_db)

    @pytest.fixture
    def sample_member(self):
        """创建示例成员"""
        return Member(
            id=1,
            username="test_user",
            student_id="20210001",
            name="测试用户",
            role=UserRole.MEMBER,
        )

    @pytest.fixture
    def admin_member(self):
        """创建管理员成员"""
        return Member(
            id=2,
            username="admin_user",
            student_id="20210002",
            name="管理员",
            role=UserRole.ADMIN,
        )

    @pytest.fixture
    def sample_repair_task(self, sample_member):
        """创建示例报修任务"""
        task = RepairTask(
            id=1,
            task_id="T001",
            title="测试报修任务",
            description="测试描述",
            task_type=TaskType.ONLINE,
            status=TaskStatus.PENDING,
            category=TaskCategory.NETWORK_REPAIR,
            priority=TaskPriority.MEDIUM,
            report_time=datetime.utcnow(),
            member_id=sample_member.id,
            reporter_name="报修用户",
            reporter_contact="user@test.com",
        )
        task.tags = []
        task.is_rush_order = False
        return task


class TestCreateRepairTask(TestTaskServiceBasic):
    """测试创建报修任务功能"""

    @pytest.mark.asyncio
    async def test_create_repair_task_basic(self, service, mock_db):
        """测试基础报修任务创建"""
        task_data = {
            "title": "网络故障报修",
            "description": "教学楼网络无法连接",
            "category": TaskCategory.NETWORK_REPAIR.value,
            "priority": TaskPriority.HIGH.value,
            "reporter_name": "张三",
            "reporter_contact": "zhangsan@university.edu",
        }

        # Mock数据库操作
        mock_db.add = MagicMock()
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()

        # Mock生成任务ID
        with patch("app.services.task_service.datetime") as mock_datetime:
            mock_datetime.now.return_value.strftime.return_value = "20250906"
            mock_db.execute.return_value.scalar.return_value = 1  # 当日任务计数

            result = await service.create_repair_task(task_data, creator_id=1)

            # 验证数据库操作
            mock_db.add.assert_called_once()
            mock_db.commit.assert_called_once()
            mock_db.refresh.assert_called_once()

            # 验证任务数据
            assert "T20250906" in result.task_id
            assert result.title == "网络故障报修"
            assert result.category == TaskCategory.NETWORK_REPAIR
            assert result.priority == TaskPriority.HIGH

    @pytest.mark.asyncio
    async def test_create_repair_task_with_minimal_data(self, service, mock_db):
        """测试使用最少数据创建报修任务"""
        task_data = {"title": "简单报修"}

        mock_db.add = MagicMock()
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()

        with patch("app.services.task_service.datetime") as mock_datetime:
            mock_datetime.now.return_value.strftime.return_value = "20250906"
            mock_db.execute.return_value.scalar.return_value = 1

            result = await service.create_repair_task(task_data)

            # 验证默认值
            assert result.title == "简单报修"
            assert result.category == TaskCategory.NETWORK_REPAIR  # 默认分类
            assert result.priority == TaskPriority.MEDIUM  # 默认优先级
            assert result.task_type == TaskType.ONLINE  # 默认类型

    @pytest.mark.asyncio
    async def test_create_repair_task_with_auto_assignment(
        self, service, mock_db, sample_member
    ):
        """测试自动分配报修任务"""
        task_data = {"title": "自动分配任务", "auto_assign": True}

        # Mock查询结果
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_member
        mock_db.execute.return_value = mock_result
        mock_db.add = MagicMock()
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()

        with patch("app.services.task_service.datetime") as mock_datetime:
            mock_datetime.now.return_value.strftime.return_value = "20250906"

            result = await service.create_repair_task(task_data)

            # 验证自动分配
            assert result.member_id == sample_member.id
            assert result.assigned_at is not None

    @pytest.mark.asyncio
    async def test_create_repair_task_database_error(self, service, mock_db):
        """测试数据库错误处理"""
        task_data = {"title": "错误测试任务"}

        # Mock数据库提交失败
        mock_db.commit.side_effect = Exception("Database error")
        mock_db.rollback = AsyncMock()

        with pytest.raises(Exception, match="Database error"):
            await service.create_repair_task(task_data)

        mock_db.rollback.assert_called_once()


class TestCreateMonitoringTask(TestTaskServiceBasic):
    """测试创建监控任务功能"""

    @pytest.mark.asyncio
    async def test_create_monitoring_task_basic(self, service, mock_db, sample_member):
        """测试基础监控任务创建"""
        task_data = {
            "title": "机房巡检",
            "description": "每日例行机房巡检",
            "location": "A栋机房",
            "monitoring_type": "inspection",
            "start_time": datetime.utcnow(),
            "end_time": datetime.utcnow() + timedelta(hours=2),
            "member_id": sample_member.id,
        }

        mock_db.add = MagicMock()
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()

        result = await service.create_monitoring_task(task_data)

        # 验证任务创建
        assert result.title == "机房巡检"
        assert result.monitoring_type == "inspection"
        assert result.member_id == sample_member.id
        assert result.work_minutes > 0  # 应该自动计算工时

    @pytest.mark.asyncio
    async def test_create_monitoring_task_with_cabinet_count(
        self, service, mock_db, sample_member
    ):
        """测试带机柜数量的监控任务创建"""
        task_data = {
            "title": "机柜巡检",
            "cabinet_count": 20,
            "member_id": sample_member.id,
            "start_time": datetime.utcnow(),
            "end_time": datetime.utcnow() + timedelta(hours=2),
        }

        mock_db.add = MagicMock()
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()

        result = await service.create_monitoring_task(task_data)

        # 验证机柜巡检相关字段
        assert result.cabinet_count == 20
        assert result.work_minutes == 100  # 20个机柜 * 5分钟/机柜


class TestCreateAssistanceTask(TestTaskServiceBasic):
    """测试创建协助任务功能"""

    @pytest.mark.asyncio
    async def test_create_assistance_task_basic(self, service, mock_db, sample_member):
        """测试基础协助任务创建"""
        task_data = {
            "title": "协助其他部门",
            "description": "协助教务处系统维护",
            "assisted_department": "教务处",
            "assisted_person": "李老师",
            "member_id": sample_member.id,
            "start_time": datetime.utcnow(),
            "end_time": datetime.utcnow() + timedelta(hours=3),
        }

        mock_db.add = MagicMock()
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()

        result = await service.create_assistance_task(task_data)

        # 验证任务创建
        assert result.title == "协助其他部门"
        assert result.assisted_department == "教务处"
        assert result.assisted_person == "李老师"
        assert result.status == TaskStatus.PENDING  # 默认待审核状态
        assert result.work_minutes == 180  # 3小时 = 180分钟

    @pytest.mark.asyncio
    async def test_create_assistance_task_invalid_time_range(
        self, service, mock_db, sample_member
    ):
        """测试无效时间范围的协助任务"""
        task_data = {
            "title": "无效时间任务",
            "member_id": sample_member.id,
            "start_time": datetime.utcnow(),
            "end_time": datetime.utcnow() - timedelta(hours=1),  # 结束时间早于开始时间
        }

        with pytest.raises(ValueError, match="结束时间不能早于开始时间"):
            await service.create_assistance_task(task_data)


class TestUpdateTaskStatus(TestTaskServiceBasic):
    """测试更新任务状态功能"""

    @pytest.mark.asyncio
    async def test_update_task_status_basic(
        self, service, mock_db, sample_repair_task, sample_member
    ):
        """测试基础状态更新"""
        # Mock查询结果
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_repair_task
        mock_db.execute.return_value = mock_result
        mock_db.commit = AsyncMock()

        result = await service.update_task_status(
            task_id=1, new_status=TaskStatus.IN_PROGRESS, operator_id=sample_member.id
        )

        # 验证状态更新
        assert sample_repair_task.status == TaskStatus.IN_PROGRESS
        assert sample_repair_task.response_time is not None  # 应该设置响应时间
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_task_status_to_completed(
        self, service, mock_db, sample_repair_task, sample_member
    ):
        """测试更新为完成状态"""
        sample_repair_task.status = TaskStatus.IN_PROGRESS
        sample_repair_task.response_time = datetime.utcnow()

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_repair_task
        mock_db.execute.return_value = mock_result
        mock_db.commit = AsyncMock()

        # Mock工时重算
        with patch.object(
            service.work_hours_service, "calculate_task_work_minutes"
        ) as mock_calc:
            mock_calc.return_value = {"total_minutes": 45}

            result = await service.update_task_status(
                task_id=1, new_status=TaskStatus.COMPLETED, operator_id=sample_member.id
            )

        # 验证完成状态设置
        assert sample_repair_task.status == TaskStatus.COMPLETED
        assert sample_repair_task.completion_time is not None
        assert sample_repair_task.work_minutes == 45  # 工时已更新
        mock_calc.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_task_status_permission_denied(self, service, mock_db):
        """测试权限不足的状态更新"""
        # Mock任务不存在或无权限
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        with pytest.raises(PermissionDeniedError, match="无权限操作该任务"):
            await service.update_task_status(
                task_id=999, new_status=TaskStatus.COMPLETED, operator_id=1
            )


class TestAssignTask(TestTaskServiceBasic):
    """测试任务分配功能"""

    @pytest.mark.asyncio
    async def test_assign_task_basic(
        self, service, mock_db, sample_repair_task, sample_member, admin_member
    ):
        """测试基础任务分配"""
        # Mock查询结果
        task_result = MagicMock()
        task_result.scalar_one_or_none.return_value = sample_repair_task

        member_result = MagicMock()
        member_result.scalar_one_or_none.return_value = sample_member

        mock_db.execute.side_effect = [task_result, member_result]
        mock_db.commit = AsyncMock()

        result = await service.assign_task(
            task_id=1, assignee_id=sample_member.id, operator_id=admin_member.id
        )

        # 验证分配结果
        assert sample_repair_task.member_id == sample_member.id
        assert sample_repair_task.assigned_at is not None
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_assign_task_member_not_found(
        self, service, mock_db, sample_repair_task, admin_member
    ):
        """测试分配不存在的成员"""
        task_result = MagicMock()
        task_result.scalar_one_or_none.return_value = sample_repair_task

        member_result = MagicMock()
        member_result.scalar_one_or_none.return_value = None  # 成员不存在

        mock_db.execute.side_effect = [task_result, member_result]

        with pytest.raises(ValueError, match="指定的成员不存在"):
            await service.assign_task(
                task_id=1, assignee_id=999, operator_id=admin_member.id
            )


class TestTaskFeedbackAndRating(TestTaskServiceBasic):
    """测试任务反馈和评分功能"""

    @pytest.mark.asyncio
    async def test_add_task_feedback_basic(self, service, mock_db, sample_repair_task):
        """测试添加任务反馈"""
        feedback_text = "维修及时，服务态度很好"

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_repair_task
        mock_db.execute.return_value = mock_result
        mock_db.commit = AsyncMock()

        result = await service.add_task_feedback(task_id=1, feedback=feedback_text)

        # 验证反馈添加
        assert sample_repair_task.feedback == feedback_text
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_add_task_rating_with_positive_review(
        self, service, mock_db, sample_repair_task
    ):
        """测试添加正面评分"""
        rating = 5
        feedback = "非常满意的服务"

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_repair_task
        mock_db.execute.return_value = mock_result
        mock_db.commit = AsyncMock()

        # Mock工时重算
        with patch.object(
            service.work_hours_service, "calculate_task_work_minutes"
        ) as mock_calc:
            mock_calc.return_value = {"total_minutes": 70}  # 基础40 + 好评30

            result = await service.add_task_rating(
                task_id=1, rating=rating, feedback=feedback
            )

        # 验证评分设置
        assert sample_repair_task.rating == rating
        assert sample_repair_task.feedback == feedback
        assert sample_repair_task.work_minutes == 70  # 工时已重算
        mock_calc.assert_called_once()

    @pytest.mark.asyncio
    async def test_add_task_rating_with_negative_review(
        self, service, mock_db, sample_repair_task
    ):
        """测试添加负面评分"""
        rating = 2  # 差评
        feedback = "响应速度慢"

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_repair_task
        mock_db.execute.return_value = mock_result
        mock_db.commit = AsyncMock()

        # Mock工时重算
        with patch.object(
            service.work_hours_service, "calculate_task_work_minutes"
        ) as mock_calc:
            mock_calc.return_value = {
                "total_minutes": 0
            }  # 基础40 - 差评60 = 0 (不能为负)

            result = await service.add_task_rating(
                task_id=1, rating=rating, feedback=feedback
            )

        # 验证差评处理
        assert sample_repair_task.rating == rating
        assert sample_repair_task.work_minutes == 0
        mock_calc.assert_called_once()


class TestRushTaskManagement(TestTaskServiceBasic):
    """测试爆单任务管理功能"""

    @pytest.mark.asyncio
    async def test_batch_mark_rush_tasks_basic(
        self, service, mock_db, sample_repair_task
    ):
        """测试批量标记爆单任务"""
        # Mock查询结果
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [sample_repair_task]
        mock_db.execute.return_value = mock_result
        mock_db.commit = AsyncMock()

        # Mock爆单标记服务
        with patch.object(
            service.rush_task_service, "batch_mark_rush_tasks"
        ) as mock_rush:
            mock_rush.return_value = {
                "success": True,
                "marked_count": 1,
                "total_requested": 1,
            }

            result = await service.batch_mark_rush_tasks(
                task_ids=[1], is_rush=True, operator_id=1
            )

        # 验证爆单标记
        mock_rush.assert_called_once_with([1], True)
        assert result["marked_count"] == 1

    @pytest.mark.asyncio
    async def test_get_rush_tasks_list_basic(
        self, service, mock_db, sample_repair_task
    ):
        """测试获取爆单任务列表"""
        sample_repair_task.is_rush_order = True

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [sample_repair_task]
        mock_db.execute.return_value = mock_result

        result = await service.get_rush_tasks_list(page=1, per_page=10)

        # 验证查询结果
        assert len(result["items"]) == 1
        assert result["items"][0].is_rush_order is True
        assert result["page"] == 1
        assert result["per_page"] == 10

    @pytest.mark.asyncio
    async def test_get_rush_tasks_statistics_basic(self, service, mock_db):
        """测试获取爆单任务统计"""
        # Mock统计查询结果
        mock_results = [
            MagicMock(scalar=MagicMock(return_value=5)),  # 总数
            MagicMock(scalar=MagicMock(return_value=2)),  # 本月
            MagicMock(scalar=MagicMock(return_value=3)),  # 已完成
            MagicMock(scalar=MagicMock(return_value=1)),  # 待处理
        ]
        mock_db.execute.side_effect = mock_results

        result = await service.get_rush_tasks_statistics()

        # 验证统计结果
        assert result["total_rush_tasks"] == 5
        assert result["monthly_rush_tasks"] == 2
        assert result["completed_rush_tasks"] == 3
        assert result["pending_rush_tasks"] == 1


class TestMemberTaskSummary(TestTaskServiceBasic):
    """测试成员任务汇总功能"""

    @pytest.mark.asyncio
    async def test_get_member_task_summary_basic(self, service, mock_db, sample_member):
        """测试获取成员任务汇总"""
        # Mock各类任务查询结果
        repair_result = MagicMock()
        repair_result.scalars.return_value.all.return_value = [
            MagicMock(work_minutes=40),
            MagicMock(work_minutes=100),
        ]

        monitoring_result = MagicMock()
        monitoring_result.scalars.return_value.all.return_value = [
            MagicMock(work_minutes=60)
        ]

        assistance_result = MagicMock()
        assistance_result.scalars.return_value.all.return_value = [
            MagicMock(work_minutes=90)
        ]

        mock_db.execute.side_effect = [
            repair_result,
            monitoring_result,
            assistance_result,
        ]

        result = await service.get_member_task_summary(
            member_id=sample_member.id, year=2025, month=1
        )

        # 验证汇总结果
        assert result["repair_tasks"] == 2
        assert result["repair_work_minutes"] == 140
        assert result["monitoring_tasks"] == 1
        assert result["monitoring_work_minutes"] == 60
        assert result["assistance_tasks"] == 1
        assert result["assistance_work_minutes"] == 90
        assert result["total_work_minutes"] == 290
        assert result["total_work_hours"] == 4.83  # 290/60 ≈ 4.83


class TestWorkHoursRecalculation(TestTaskServiceBasic):
    """测试工时重算功能"""

    @pytest.mark.asyncio
    async def test_recalculate_task_work_hours_basic(
        self, service, mock_db, sample_repair_task
    ):
        """测试单个任务工时重算"""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_repair_task
        mock_db.execute.return_value = mock_result
        mock_db.commit = AsyncMock()

        # Mock工时计算
        with patch.object(
            service.work_hours_service, "calculate_task_work_minutes"
        ) as mock_calc:
            mock_calc.return_value = {"total_minutes": 55}

            result = await service.recalculate_task_work_hours(task_id=1)

        # 验证工时重算
        assert result is True
        assert sample_repair_task.work_minutes == 55
        mock_calc.assert_called_once_with(sample_repair_task)
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_recalculate_task_work_hours_not_found(self, service, mock_db):
        """测试重算不存在的任务工时"""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        result = await service.recalculate_task_work_hours(task_id=999)

        # 验证返回失败
        assert result is False

    @pytest.mark.asyncio
    async def test_recalculate_task_work_hours_calculation_error(
        self, service, mock_db, sample_repair_task
    ):
        """测试工时计算失败的情况"""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_repair_task
        mock_db.execute.return_value = mock_result

        # Mock计算失败
        with patch.object(
            service.work_hours_service, "calculate_task_work_minutes"
        ) as mock_calc:
            mock_calc.side_effect = Exception("计算失败")

            result = await service.recalculate_task_work_hours(task_id=1)

        # 验证异常处理
        assert result is False


class TestErrorHandling(TestTaskServiceBasic):
    """测试错误处理"""

    @pytest.mark.asyncio
    async def test_create_task_invalid_data(self, service, mock_db):
        """测试创建任务时的数据验证错误"""
        invalid_task_data = {
            "title": "",  # 空标题
            "priority": "INVALID_PRIORITY",  # 无效优先级
        }

        with pytest.raises(ValueError):
            await service.create_repair_task(invalid_task_data)

    @pytest.mark.asyncio
    async def test_database_connection_error(self, service, mock_db):
        """测试数据库连接错误"""
        mock_db.execute.side_effect = Exception("Database connection lost")

        with pytest.raises(Exception, match="Database connection lost"):
            await service.get_member_task_summary(member_id=1, year=2025, month=1)

    @pytest.mark.asyncio
    async def test_concurrent_task_modification(
        self, service, mock_db, sample_repair_task
    ):
        """测试并发任务修改冲突"""
        # 模拟任务在查询后被其他进程修改
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_repair_task
        mock_db.execute.return_value = mock_result

        # 提交时出现并发冲突
        mock_db.commit.side_effect = Exception("Concurrent modification detected")
        mock_db.rollback = AsyncMock()

        with pytest.raises(Exception, match="Concurrent modification detected"):
            await service.update_task_status(
                task_id=1, new_status=TaskStatus.COMPLETED, operator_id=1
            )

        mock_db.rollback.assert_called_once()
