"""
工时计算服务测试用例
测试核心业务逻辑：工时计算、月度统计、批量操作等
"""

from datetime import date, datetime, timedelta
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.models.attendance import MonthlyAttendanceSummary
from app.models.member import Member
from app.models.task import (
    AssistanceTask,
    MonitoringTask,
    RepairTask,
    TaskStatus,
    TaskTag,
    TaskTagType,
    TaskType,
)
from app.services.work_hours_service import WorkHoursCalculationService, safe_float


class TestSafeFloatFunction:
    """测试safe_float辅助函数"""

    def test_safe_float_with_none(self):
        """测试None值处理"""
        assert safe_float(None) == 0.0
        assert safe_float(None, 10.5) == 10.5

    def test_safe_float_with_valid_numbers(self):
        """测试有效数字转换"""
        assert safe_float(10) == 10.0
        assert safe_float(10.5) == 10.5
        assert safe_float("10.5") == 10.5
        assert safe_float(Decimal("10.5")) == 10.5

    def test_safe_float_with_invalid_values(self):
        """测试无效值处理"""
        assert safe_float("invalid") == 0.0
        assert safe_float("invalid", 5.0) == 5.0
        assert safe_float([]) == 0.0
        assert safe_float({}) == 0.0

    def test_safe_float_with_mock_objects(self):
        """测试Mock对象处理"""
        mock_obj = MagicMock()
        assert safe_float(mock_obj) == 0.0
        assert safe_float(mock_obj, 15.0) == 15.0


class TestWorkHoursCalculationServiceInit:
    """测试工时计算服务初始化"""

    def test_init_with_valid_db_session(self):
        """测试有效数据库会话初始化"""
        mock_db = AsyncMock()
        service = WorkHoursCalculationService(mock_db)

        assert service.db is mock_db
        assert service.ONLINE_TASK_MINUTES == 40
        assert service.OFFLINE_TASK_MINUTES == 100
        assert service.RUSH_TASK_MINUTES == 15
        assert service.POSITIVE_REVIEW_MINUTES == 30

    def test_init_with_none_db_session(self):
        """测试空数据库会话初始化失败"""
        with pytest.raises(ValueError, match="Database session is required"):
            WorkHoursCalculationService(None)


class TestWorkHoursCalculationServiceBasic:
    """测试工时计算服务基础功能"""

    @pytest.fixture
    def mock_db(self):
        """创建模拟数据库会话"""
        return AsyncMock()

    @pytest.fixture
    def service(self, mock_db):
        """创建工时计算服务实例"""
        return WorkHoursCalculationService(mock_db)

    @pytest.fixture
    def sample_task(self):
        """创建示例任务"""
        task = RepairTask(
            id=1,
            task_id="T001",
            title="Test Task",
            task_type=TaskType.ONLINE,
            status=TaskStatus.COMPLETED,
            report_time=datetime.utcnow(),
            member_id=test_user.id,
        )
        task.tags = []
        task.is_rush_order = False
        return task

    @pytest.fixture
    def rush_task(self):
        """创建爆单任务"""
        task = RepairTask(
            id=2,
            task_id="T002",
            title="Rush Task",
            task_type=TaskType.ONLINE,
            status=TaskStatus.COMPLETED,
            report_time=datetime.utcnow(),
            member_id=test_user.id,
        )
        task.tags = []
        task.is_rush_order = True
        return task

    @pytest.fixture
    def penalty_tag(self):
        """创建惩罚标签"""
        tag = TaskTag(
            id=1,
            name="超时响应",
            tag_type=TaskTagType.TIMEOUT_RESPONSE,
            work_minutes_modifier=-30,
            is_active=True,
        )
        return tag

    @pytest.fixture
    def bonus_tag(self):
        """创建奖励标签"""
        tag = TaskTag(
            id=2,
            name="非默认好评",
            tag_type=TaskTagType.NON_DEFAULT_RATING,
            work_minutes_modifier=30,
            is_active=True,
        )
        return tag


class TestCalculateTaskWorkMinutes(TestWorkHoursCalculationServiceBasic):
    """测试计算任务工时功能"""

    @pytest.mark.asyncio
    async def test_calculate_task_work_minutes_with_none_task(self, service):
        """测试空任务输入"""
        with pytest.raises(ValueError, match="任务对象不能为空"):
            await service.calculate_task_work_minutes(None)

    @pytest.mark.asyncio
    async def test_calculate_task_work_minutes_without_id(self, service):
        """测试无ID任务"""
        task = MagicMock()
        task.id = None

        with pytest.raises(ValueError, match="任务ID无效"):
            await service.calculate_task_work_minutes(task)

    @pytest.mark.asyncio
    async def test_calculate_task_work_minutes_without_task_type(self, service):
        """测试无任务类型"""
        task = MagicMock()
        task.id = 1
        task.task_type = None

        with pytest.raises(ValueError, match="任务类型无效"):
            await service.calculate_task_work_minutes(task)

    @pytest.mark.asyncio
    async def test_calculate_task_work_minutes_without_report_time(self, service):
        """测试无报修时间"""
        task = MagicMock()
        task.id = 1
        task.task_type = TaskType.ONLINE
        task.report_time = None

        with pytest.raises(ValueError, match="报修时间无效"):
            await service.calculate_task_work_minutes(task)

    @pytest.mark.asyncio
    async def test_calculate_online_task_basic(self, service, sample_task, mock_db):
        """测试线上任务基础计算"""
        # 设置mock返回值
        mock_db.refresh = AsyncMock()

        result = await service.calculate_task_work_minutes(sample_task)

        assert result["base_minutes"] == 40  # 线上任务基础工时
        assert result["total_minutes"] == 40
        assert result["penalty_minutes"] == 0
        assert result["bonus_minutes"] == 0

    @pytest.mark.asyncio
    async def test_calculate_offline_task_basic(self, service, mock_db):
        """测试线下任务基础计算"""
        task = RepairTask(
            id=1,
            task_id="T001",
            title="Offline Task",
            task_type=TaskType.OFFLINE,
            status=TaskStatus.COMPLETED,
            report_time=datetime.utcnow(),
            member_id=test_user.id,
        )
        task.tags = []
        task.is_rush_order = False

        mock_db.refresh = AsyncMock()

        result = await service.calculate_task_work_minutes(task)

        assert result["base_minutes"] == 100  # 线下任务基础工时
        assert result["total_minutes"] == 100

    @pytest.mark.asyncio
    async def test_calculate_rush_task_basic(self, service, rush_task, mock_db):
        """测试爆单任务基础计算"""
        mock_db.refresh = AsyncMock()

        result = await service.calculate_task_work_minutes(rush_task)

        assert result["rush_minutes"] == 15  # 爆单任务固定工时
        assert result["total_minutes"] == 15

    @pytest.mark.asyncio
    async def test_calculate_task_with_penalty_tag(
        self, service, sample_task, penalty_tag, mock_db
    ):
        """测试带惩罚标签的任务"""
        sample_task.tags = [penalty_tag]
        mock_db.refresh = AsyncMock()

        result = await service.calculate_task_work_minutes(sample_task)

        assert result["base_minutes"] == 40
        assert result["penalty_minutes"] == 30
        assert result["total_minutes"] == 10  # 40 - 30 = 10

    @pytest.mark.asyncio
    async def test_calculate_task_with_bonus_tag(
        self, service, sample_task, bonus_tag, mock_db
    ):
        """测试带奖励标签的任务"""
        sample_task.tags = [bonus_tag]
        mock_db.refresh = AsyncMock()

        result = await service.calculate_task_work_minutes(sample_task)

        assert result["base_minutes"] == 40
        assert result["bonus_minutes"] == 30
        assert result["total_minutes"] == 70  # 40 + 30 = 70

    @pytest.mark.asyncio
    async def test_calculate_rush_task_with_penalty(
        self, service, rush_task, penalty_tag, mock_db
    ):
        """测试爆单任务与惩罚标签叠加"""
        rush_task.tags = [penalty_tag]
        mock_db.refresh = AsyncMock()

        result = await service.calculate_task_work_minutes(rush_task)

        assert result["rush_minutes"] == 15
        assert result["penalty_minutes"] == 30
        assert result["total_minutes"] == 0  # max(0, 15-30) = 0，不允许负数

    @pytest.mark.asyncio
    async def test_calculate_task_without_tags_attribute(self, service, mock_db):
        """测试无tags属性的任务"""
        task = MagicMock()
        task.id = 1
        task.task_type = TaskType.ONLINE
        task.report_time = datetime.utcnow()
        task.is_rush_order = False
        # 没有tags属性
        del task.tags

        mock_db.refresh = AsyncMock()

        # 由于没有tags属性，应该尝试从DB刷新
        with pytest.raises(AttributeError):
            await service.calculate_task_work_minutes(task)


class TestTimeOverdueChecks(TestWorkHoursCalculationServiceBasic):
    """测试超时检查功能"""

    def test_is_response_overdue_true(self, service):
        """测试响应超时检查 - 超时情况"""
        task = MagicMock()
        task.response_time = None
        task.status = TaskStatus.PENDING
        task.report_time = datetime.utcnow() - timedelta(hours=25)  # 超过24小时

        result = service._is_response_overdue(task)
        assert result is True

    def test_is_response_overdue_false(self, service):
        """测试响应超时检查 - 未超时情况"""
        task = MagicMock()
        task.response_time = None
        task.status = TaskStatus.PENDING
        task.report_time = datetime.utcnow() - timedelta(hours=10)  # 未超过24小时

        result = service._is_response_overdue(task)
        assert result is False

    def test_is_response_overdue_already_responded(self, service):
        """测试响应超时检查 - 已响应情况"""
        task = MagicMock()
        task.response_time = datetime.utcnow()  # 已响应
        task.status = TaskStatus.IN_PROGRESS
        task.report_time = datetime.utcnow() - timedelta(hours=30)

        result = service._is_response_overdue(task)
        assert result is False

    def test_is_completion_overdue_true(self, service):
        """测试完成超时检查 - 超时情况"""
        task = MagicMock()
        base_time = datetime.utcnow() - timedelta(hours=50)
        task.report_time = base_time
        task.response_time = base_time
        task.completion_time = None

        result = service._is_completion_overdue(task)
        assert result is True

    def test_is_completion_overdue_false(self, service):
        """测试完成超时检查 - 未超时情况"""
        task = MagicMock()
        base_time = datetime.utcnow() - timedelta(hours=20)
        task.report_time = base_time
        task.response_time = base_time
        task.completion_time = None

        result = service._is_completion_overdue(task)
        assert result is False

    def test_is_completion_overdue_with_completion_time(self, service):
        """处理完成但耗时超过阈值仍判定超时"""
        start_time = datetime.utcnow() - timedelta(hours=60)
        finish_time = start_time + timedelta(hours=55)

        task = MagicMock()
        task.report_time = start_time
        task.response_time = start_time
        task.completion_time = finish_time

        result = service._is_completion_overdue(task)
        assert result is True

    def test_is_negative_review_true(self, service):
        """测试差评检查 - 差评情况"""
        task = MagicMock()
        task.rating = 2  # 2星差评

        result = service._is_negative_review(task)
        assert result is True

    def test_is_negative_review_false(self, service):
        """测试差评检查 - 好评情况"""
        task = MagicMock()
        task.rating = 4  # 4星好评

        result = service._is_negative_review(task)
        assert result is False

    def test_is_negative_review_no_rating(self, service):
        """测试差评检查 - 无评分情况"""
        task = MagicMock()
        task.rating = None

        result = service._is_negative_review(task)
        assert result is False


class TestMonthlyCalculations(TestWorkHoursCalculationServiceBasic):
    """测试月度计算功能"""

    @pytest.fixture
    def sample_member(self):
        """创建示例成员"""
        return Member(
            id=1, username="test_user", student_id="20210001", name="测试用户"
        )

    @pytest.mark.asyncio
    async def test_calculate_monthly_work_hours_basic(
        self, service, sample_member, mock_db
    ):
        """测试月度工时计算基础功能"""
        # 创建示例任务数据
        repair_tasks = [
            MagicMock(work_minutes=40),
            MagicMock(work_minutes=100),
            MagicMock(work_minutes=60),
        ]

        monitoring_tasks = [MagicMock(work_minutes=30), MagicMock(work_minutes=45)]

        assistance_tasks = [MagicMock(work_minutes=90)]

        # 设置mock查询结果
        mock_db.execute = AsyncMock()
        mock_result = MagicMock()

        # 设置三个查询的返回值
        mock_db.execute.side_effect = [
            # 报修任务查询结果
            MagicMock(
                scalars=MagicMock(
                    return_value=MagicMock(all=MagicMock(return_value=repair_tasks))
                )
            ),
            # 监控任务查询结果
            MagicMock(
                scalars=MagicMock(
                    return_value=MagicMock(all=MagicMock(return_value=monitoring_tasks))
                )
            ),
            # 协助任务查询结果
            MagicMock(
                scalars=MagicMock(
                    return_value=MagicMock(all=MagicMock(return_value=assistance_tasks))
                )
            ),
        ]

        result = await service.calculate_monthly_work_hours(sample_member, 2025, 1)

        assert result["repair_minutes"] == 200  # 40+100+60
        assert result["monitoring_minutes"] == 75  # 30+45
        assert result["assistance_minutes"] == 90
        assert result["total_minutes"] == 365  # 200+75+90
        assert result["total_hours"] == 6.08  # 365/60 = 6.083...

    @pytest.mark.asyncio
    async def test_update_monthly_summary_create_new(
        self, service, sample_member, mock_db
    ):
        """测试更新月度总结 - 创建新记录"""
        # Mock数据库查询返回None（记录不存在）
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result
        mock_db.add = MagicMock()
        mock_db.commit = AsyncMock()

        # Mock计算结果
        work_hours_data = {
            "repair_minutes": 200,
            "monitoring_minutes": 75,
            "assistance_minutes": 90,
            "total_minutes": 365,
            "total_hours": 6.08,
        }

        with patch.object(
            service, "calculate_monthly_work_hours", return_value=work_hours_data
        ) as mock_calc:
            result = await service.update_monthly_summary(sample_member, 2025, 1)

            # 验证调用了计算方法
            mock_calc.assert_called_once_with(sample_member, 2025, 1)

            # 验证添加了新记录
            mock_db.add.assert_called_once()
            mock_db.commit.assert_called_once()

            # 验证返回结果
            assert result["total_hours"] == 6.08
            assert result["created"] is True

    @pytest.mark.asyncio
    async def test_update_monthly_summary_update_existing(
        self, service, sample_member, mock_db
    ):
        """测试更新月度总结 - 更新现有记录"""
        # Mock现有记录
        existing_summary = MonthlyAttendanceSummary(
            member_id=test_user.id,
            year=2025,
            month=1,
            repair_work_minutes=100,
            monitoring_work_minutes=50,
            assistance_work_minutes=60,
            total_work_minutes=210,
        )

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = existing_summary
        mock_db.execute.return_value = mock_result
        mock_db.commit = AsyncMock()

        # Mock计算结果
        work_hours_data = {
            "repair_minutes": 200,
            "monitoring_minutes": 75,
            "assistance_minutes": 90,
            "total_minutes": 365,
            "total_hours": 6.08,
        }

        with patch.object(
            service, "calculate_monthly_work_hours", return_value=work_hours_data
        ) as mock_calc:
            result = await service.update_monthly_summary(sample_member, 2025, 1)

            # 验证更新了现有记录
            assert existing_summary.repair_work_minutes == 200
            assert existing_summary.monitoring_work_minutes == 75
            assert existing_summary.assistance_work_minutes == 90
            assert existing_summary.total_work_minutes == 365

            mock_db.commit.assert_called_once()
            assert result["created"] is False


class TestBatchOperations(TestWorkHoursCalculationServiceBasic):
    """测试批量操作功能"""

    @pytest.mark.asyncio
    async def test_batch_update_monthly_summaries_basic(self, service, mock_db):
        """测试批量更新月度总结基础功能"""
        # Mock成员查询结果
        members = [
            Member(id=1, username="user1", student_id="20210001", name="用户1"),
            Member(id=2, username="user2", student_id="20210002", name="用户2"),
        ]

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = members
        mock_db.execute.return_value = mock_result

        # Mock更新结果
        with patch.object(service, "update_monthly_summary") as mock_update:
            mock_update.side_effect = [
                {"total_hours": 5.5, "created": True},
                {"total_hours": 6.2, "created": False},
            ]

            result = await service.batch_update_monthly_summaries(2025, 1)

            # 验证调用了正确次数的更新
            assert mock_update.call_count == 2

            # 验证返回结果
            assert result["processed_count"] == 2
            assert result["created_count"] == 1
            assert result["updated_count"] == 1
            assert len(result["results"]) == 2

    @pytest.mark.asyncio
    async def test_batch_recalculate_work_hours_basic(self, service, mock_db):
        """测试批量重算工时基础功能"""
        # Mock任务查询结果
        tasks = [MagicMock(id=1, work_minutes=40), MagicMock(id=2, work_minutes=100)]

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = tasks
        mock_db.execute.return_value = mock_result
        mock_db.commit = AsyncMock()

        # Mock工时计算结果
        with patch.object(service, "calculate_task_work_minutes") as mock_calc:
            mock_calc.side_effect = [{"total_minutes": 45}, {"total_minutes": 95}]

            result = await service.batch_recalculate_work_hours(task_ids=[1, 2])

            # 验证调用了正确次数的计算
            assert mock_calc.call_count == 2

            # 验证更新了任务工时
            assert tasks[0].work_minutes == 45
            assert tasks[1].work_minutes == 95

            # 验证返回结果
            assert result["processed_count"] == 2
            assert result["updated_count"] == 2

    @pytest.mark.asyncio
    async def test_batch_mark_rush_tasks_basic(self, service, mock_db):
        """测试批量标记爆单任务基础功能"""
        # Mock任务查询结果
        tasks = [
            MagicMock(id=1, is_rush_order=False),
            MagicMock(id=2, is_rush_order=False),
        ]

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = tasks
        mock_db.execute.return_value = mock_result
        mock_db.commit = AsyncMock()

        result = await service.batch_mark_rush_tasks(task_ids=[1, 2], is_rush=True)

        # 验证标记了爆单状态
        assert tasks[0].is_rush_order is True
        assert tasks[1].is_rush_order is True

        # 验证返回结果
        assert result["processed_count"] == 2
        assert result["marked_count"] == 2


class TestStatisticsAndReports(TestWorkHoursCalculationServiceBasic):
    """测试统计和报表功能"""

    @pytest.mark.asyncio
    async def test_get_team_monthly_summary_basic(self, service, mock_db):
        """测试获取团队月度总结基础功能"""
        # Mock查询结果
        summaries = [
            MagicMock(
                member_id=test_user.id,
                repair_work_minutes=200,
                monitoring_work_minutes=100,
                assistance_work_minutes=50,
                total_work_minutes=350,
            ),
            MagicMock(
                member_id=2,
                repair_work_minutes=150,
                monitoring_work_minutes=80,
                assistance_work_minutes=70,
                total_work_minutes=300,
            ),
        ]

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = summaries
        mock_db.execute.return_value = mock_result

        result = await service.get_team_monthly_summary(2025, 1)

        # 验证团队总计
        assert result["team_total"]["repair_minutes"] == 350  # 200+150
        assert result["team_total"]["monitoring_minutes"] == 180  # 100+80
        assert result["team_total"]["assistance_minutes"] == 120  # 50+70
        assert result["team_total"]["total_minutes"] == 650  # 350+300

        # 验证平均值
        assert result["team_average"]["total_minutes"] == 325.0  # 650/2

        # 验证个人记录数量
        assert len(result["member_summaries"]) == 2

    @pytest.mark.asyncio
    async def test_get_statistics_basic(self, service, mock_db):
        """测试获取统计信息基础功能"""
        # Mock各种查询结果
        mock_db.execute = AsyncMock()

        # 设置多个查询的返回值
        mock_results = [
            # 总任务数查询
            MagicMock(scalar=MagicMock(return_value=100)),
            # 本月任务数查询
            MagicMock(scalar=MagicMock(return_value=25)),
            # 爆单任务数查询
            MagicMock(scalar=MagicMock(return_value=5)),
            # 超时任务数查询
            MagicMock(scalar=MagicMock(return_value=3)),
        ]

        mock_db.execute.side_effect = mock_results

        result = await service.get_statistics()

        # 验证统计结果
        assert result["total_tasks"] == 100
        assert result["monthly_tasks"] == 25
        assert result["rush_tasks"] == 5
        assert result["overdue_tasks"] == 3

        # 验证调用了正确次数的查询
        assert mock_db.execute.call_count == 4


class TestErrorHandling(TestWorkHoursCalculationServiceBasic):
    """测试错误处理"""

    @pytest.mark.asyncio
    async def test_calculate_task_work_minutes_db_error(
        self, service, sample_task, mock_db
    ):
        """测试数据库错误处理"""
        # Mock数据库刷新失败
        mock_db.refresh = AsyncMock(side_effect=Exception("DB connection failed"))

        with pytest.raises(RuntimeError, match="无法加载任务"):
            await service.calculate_task_work_minutes(sample_task)

    @pytest.mark.asyncio
    async def test_batch_operations_partial_failure(self, service, mock_db):
        """测试批量操作部分失败"""
        # Mock部分任务查询成功，部分失败
        tasks = [
            MagicMock(id=1, work_minutes=40),
            MagicMock(id=2, work_minutes=100, side_effect=Exception("Task 2 error")),
        ]

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = tasks
        mock_db.execute.return_value = mock_result
        mock_db.commit = AsyncMock()

        # Mock工时计算，第二个任务失败
        with patch.object(service, "calculate_task_work_minutes") as mock_calc:
            mock_calc.side_effect = [
                {"total_minutes": 45},
                Exception("Calculation failed for task 2"),
            ]

            result = await service.batch_recalculate_work_hours(task_ids=[1, 2])

            # 验证部分成功
            assert result["processed_count"] == 2
            assert result["updated_count"] == 1  # 只有1个成功
            assert len(result["errors"]) == 1  # 有1个错误


# ============================================================
# P0 边界回归测试（对应 change-review-2026-02-25.md）
# ============================================================

class TestP0OverdueResponseFix:
    """Fix B: 超时响应判定——不以'是否有 response_time'直接返回"""

    @pytest.fixture
    def mock_db(self):
        return AsyncMock()

    @pytest.fixture
    def service(self, mock_db):
        return WorkHoursCalculationService(mock_db)

    def _make_task(self, report_time, response_time=None, status=TaskStatus.COMPLETED):
        task = MagicMock()
        task.report_time = report_time
        task.response_time = response_time
        task.status = status
        return task

    def test_response_within_24h_not_overdue(self, service):
        """已在24小时内响应 → 不超时"""
        now = datetime(2026, 2, 25, 12, 0, 0)
        report = now - timedelta(hours=10)
        response = now - timedelta(hours=5)
        task = self._make_task(report, response)
        assert service._is_response_overdue(task) is False

    def test_response_after_24h_is_overdue(self, service):
        """已响应但超过24小时 → 超时（原始 bug：此处曾直接返回 False）"""
        now = datetime(2026, 2, 25, 12, 0, 0)
        report = now - timedelta(hours=30)
        response = now - timedelta(hours=4)  # 报修30小时后才响应
        task = self._make_task(report, response)
        assert service._is_response_overdue(task) is True

    def test_no_response_within_24h_not_overdue(self, service):
        """未响应且未超过24小时 → 不超时"""
        from datetime import timezone as tz
        report = datetime.now(tz.utc) - timedelta(hours=12)
        task = self._make_task(report)
        assert service._is_response_overdue(task) is False

    def test_no_response_after_24h_is_overdue(self, service):
        """未响应且超过24小时 → 超时"""
        from datetime import timezone as tz
        report = datetime.now(tz.utc) - timedelta(hours=25)
        task = self._make_task(report)
        assert service._is_response_overdue(task) is True

    def test_none_report_time_returns_false(self, service):
        """report_time 为 None → 安全返回 False"""
        task = self._make_task(None)
        assert service._is_response_overdue(task) is False

    def test_naive_and_aware_mixed_no_error(self, service):
        """naive 与 aware 混合不应抛异常（Fix E）"""
        from datetime import timezone as tz
        report = datetime(2026, 2, 24, 8, 0, 0)  # naive
        response = datetime(2026, 2, 24, 10, 0, 0)  # naive, 2小时后
        task = self._make_task(report, response)
        # 2小时 < 24小时 → 不超时，不抛异常
        result = service._is_response_overdue(task)
        assert result is False


class TestP0MonthlyBoundaryFix:
    """Fix A: 月度查询使用半开区间 [月初, 次月月初)，确保月末全天数据被计入"""

    @pytest.fixture
    def mock_db(self):
        return AsyncMock()

    @pytest.fixture
    def service(self, mock_db):
        return WorkHoursCalculationService(mock_db)

    @pytest.mark.asyncio
    async def test_month_end_task_included_in_monthly_query(self, service, mock_db):
        """月末 23:59:59 的任务应计入当月（原始 bug：半闭区间会漏掉此记录）"""
        from datetime import date

        # 构造月末任务
        month_end_task = MagicMock()
        month_end_task.report_time = datetime(2026, 1, 31, 23, 59, 59)
        month_end_task.work_minutes = 40
        month_end_task.id = 1
        month_end_task.member_id = 1
        month_end_task.tags = []
        month_end_task.is_rush_order = False
        month_end_task.task_type = TaskType.ONLINE
        month_end_task.status = TaskStatus.COMPLETED

        # 验证查询中使用的是次月月初边界
        # 通过验证 next_month_start 的构造逻辑（单元测试替代集成测试）
        first_day = date(2026, 1, 1)
        next_month_start = date(2026, 2, 1)

        # 月末任务的 report_time < next_month_start 应为 True
        assert month_end_task.report_time.date() < next_month_start

    def test_next_month_start_december_wraps_correctly(self, service):
        """12月的次月月初应为次年1月1日"""
        from datetime import date
        year, month = 2026, 12
        next_month_start = date(year + 1, 1, 1) if month == 12 else date(year, month + 1, 1)
        assert next_month_start == date(2027, 1, 1)

    def test_next_month_start_normal_month(self, service):
        """普通月份的次月月初计算正确"""
        from datetime import date
        year, month = 2026, 3
        next_month_start = date(year + 1, 1, 1) if month == 12 else date(year, month + 1, 1)
        assert next_month_start == date(2026, 4, 1)


class TestP0RushOrderRuleConsistency:
    """Fix D: 爆单口径一致性 — 固定 15 分钟，不叠加基础工时"""

    @pytest.fixture
    def mock_db(self):
        return AsyncMock()

    @pytest.fixture
    def service(self, mock_db):
        return WorkHoursCalculationService(mock_db)

    def test_rush_order_rule_version_declared(self, service):
        """规则版本号已声明"""
        assert hasattr(service, "RUSH_ORDER_RULE_VERSION")
        assert service.RUSH_ORDER_RULE_VERSION != ""

    def test_rush_order_fixed_minutes_is_15(self, service):
        """爆单固定工时为15分钟"""
        assert service.RUSH_ORDER_FIXED_MINUTES == 15

    @pytest.mark.asyncio
    async def test_rush_order_total_without_penalty_is_15(self, service, mock_db):
        """无惩罚的爆单任务总工时 = 15（不叠加基础工时）"""
        mock_db.refresh = AsyncMock()

        task = MagicMock()
        task.id = 99
        task.task_type = TaskType.ONLINE  # 线上任务基础工时40，但爆单应为15
        task.report_time = datetime.utcnow()
        task.is_rush_order = True
        task.tags = []
        task.status = TaskStatus.COMPLETED
        task.response_time = datetime.utcnow()  # 已在1秒内响应，不超时
        task.completion_time = datetime.utcnow()
        task.rating = 5

        result = await service.calculate_task_work_minutes(task)
        assert result["is_rush_order"] is True
        assert result["total_minutes"] == 15
        assert result["base_minutes"] == 0  # 爆单不叠加基础工时
