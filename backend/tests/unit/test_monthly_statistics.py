"""
Monthly Statistics Tests - 月度统计测试

测试月度工时汇总计算、考勤统计、绩效评估等核心业务逻辑
覆盖场景：
1. 月度工时汇总计算
2. 月度考勤统计
3. 绩效评估计算
4. 边界条件测试
"""

import logging
from calendar import monthrange
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Any, Dict, List
from unittest.mock import AsyncMock, Mock, patch

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.attendance import AttendanceRecord, MonthlyAttendanceSummary
from app.models.member import Member, UserRole
from app.models.task import (
    AssistanceTask,
    MonitoringTask,
    RepairTask,
    TaskStatus,
    TaskType,
)
from app.services.stats_service import StatisticsService
from app.services.work_hours_service import WorkHoursCalculationService

logger = logging.getLogger(__name__)


@pytest.fixture
def mock_db():
    """Mock database session."""
    return AsyncMock(spec=AsyncSession)


@pytest.fixture
def stats_service(mock_db):
    """Create StatisticsService instance."""
    return StatisticsService(mock_db)


@pytest.fixture
def work_hours_service(mock_db):
    """Create WorkHoursCalculationService instance."""
    return WorkHoursCalculationService(mock_db)


@pytest.fixture
def sample_members():
    """创建测试成员数据"""
    return [
        Member(
            id=1,
            username="test_user1",
            name="张三",
            student_id="TEST001",
            role=UserRole.MEMBER,
            is_active=True,
            department="信息化建设处",
            class_name="测试班级A",
        ),
        Member(
            id=2,
            username="test_user2",
            name="李四",
            student_id="TEST002",
            role=UserRole.GROUP_LEADER,
            is_active=True,
            department="信息化建设处",
            class_name="测试班级B",
        ),
        Member(
            id=3,
            username="test_user3",
            name="王五",
            student_id="TEST003",
            role=UserRole.MEMBER,
            is_active=True,
            department="网络中心",
            class_name="测试班级C",
        ),
    ]


@pytest.fixture
def sample_repair_tasks():
    """创建测试维修任务数据"""
    base_date = datetime(2024, 3, 1)
    return [
        # 张三的任务 - 正常完成，好评
        RepairTask(
            id=1,
            task_id="TASK_001",
            title="测试任务1",
            member_id=1,
            work_minutes=40,
            task_type=TaskType.ONLINE,
            status=TaskStatus.COMPLETED,
            completion_time=base_date + timedelta(hours=2),
            report_time=base_date,
            rating=5,
        ),
        # 张三的任务 - 爆单任务，迟到响应
        RepairTask(
            id=2,
            task_id="TASK_002",
            title="测试任务2",
            member_id=1,
            work_minutes=40,
            task_type=TaskType.ONLINE,
            status=TaskStatus.COMPLETED,
            completion_time=base_date + timedelta(days=1, hours=3),
            report_time=base_date + timedelta(days=1),
            rating=4,
        ),
        # 李四的任务 - 线下任务，评分差
        RepairTask(
            id=3,
            task_id="TASK_003",
            title="测试任务3",
            member_id=2,
            work_minutes=100,
            task_type=TaskType.OFFLINE,
            status=TaskStatus.COMPLETED,
            completion_time=base_date + timedelta(days=2, hours=5),
            report_time=base_date + timedelta(days=2),
            rating=2,
        ),
        # 王五的任务 - 进行中
        RepairTask(
            id=4,
            task_id="TASK_004",
            title="测试任务4",
            member_id=3,
            work_minutes=0,
            task_type=TaskType.ONLINE,
            status=TaskStatus.IN_PROGRESS,
            completion_time=None,
            report_time=base_date + timedelta(days=3),
            rating=None,
        ),
    ]


@pytest.fixture
def sample_monitoring_tasks():
    """创建测试监控任务数据"""
    base_date = datetime(2024, 3, 1)
    return [
        MonitoringTask(
            id=1,
            member_id=1,
            work_minutes=60,
            start_time=base_date,
            end_time=base_date + timedelta(hours=1),
            location="机房A",
            description="网络监控",
        ),
        MonitoringTask(
            id=2,
            member_id=2,
            work_minutes=120,
            start_time=base_date + timedelta(days=1),
            end_time=base_date + timedelta(days=1, hours=2),
            location="机房B",
            description="服务器维护",
        ),
    ]


@pytest.fixture
def sample_assistance_tasks():
    """创建测试协助任务数据"""
    base_date = datetime(2024, 3, 1)
    return [
        AssistanceTask(
            id=1,
            member_id=1,
            work_minutes=30,
            start_time=base_date,
            end_time=base_date + timedelta(minutes=30),
            assisted_member_id=3,
            description="协助处理网络故障",
        ),
        AssistanceTask(
            id=2,
            member_id=2,
            work_minutes=45,
            start_time=base_date + timedelta(days=1),
            end_time=base_date + timedelta(days=1, minutes=45),
            assisted_member_id=1,
            description="协助系统升级",
        ),
    ]


@pytest.fixture
def sample_attendance_records():
    """创建测试考勤记录数据"""
    base_date = date(2024, 3, 1)
    return [
        # 张三 - 正常出勤
        AttendanceRecord(
            id=1,
            member_id=1,
            attendance_date=base_date,
            checkin_time=datetime.combine(base_date, datetime.min.time().replace(hour=8)),
            checkout_time=datetime.combine(base_date, datetime.min.time().replace(hour=17)),
            work_hours=8.0,
            is_late_checkin=False,
            is_early_checkout=False,
        ),
        # 张三 - 迟到
        AttendanceRecord(
            id=2,
            member_id=1,
            attendance_date=base_date + timedelta(days=1),
            checkin_time=datetime.combine(base_date + timedelta(days=1), datetime.min.time().replace(hour=8, minute=30)),
            checkout_time=datetime.combine(base_date + timedelta(days=1), datetime.min.time().replace(hour=17)),
            work_hours=7.5,
            is_late_checkin=True,
            is_early_checkout=False,
        ),
        # 李四 - 早退
        AttendanceRecord(
            id=3,
            member_id=2,
            attendance_date=base_date,
            checkin_time=datetime.combine(base_date, datetime.min.time().replace(hour=8)),
            checkout_time=datetime.combine(base_date, datetime.min.time().replace(hour=16, minute=30)),
            work_hours=7.5,
            is_late_checkin=False,
            is_early_checkout=True,
        ),
    ]


class TestMonthlyWorkHoursSummary:
    """月度工时汇总计算测试"""

    @pytest.mark.asyncio
    async def test_calculate_monthly_work_hours_basic(
        self, 
        work_hours_service,
        mock_db,
        sample_members,
        sample_repair_tasks,
        sample_monitoring_tasks,
        sample_assistance_tasks
    ):
        """测试基本的月度工时计算"""
        member = sample_members[0]  # 张三
        year, month = 2024, 3

        # Mock 数据库查询结果
        mock_repair_result = Mock()
        mock_repair_result.scalars.return_value.all.return_value = [
            task for task in sample_repair_tasks if task.member_id == member.id
        ]

        mock_monitoring_result = Mock()
        mock_monitoring_result.scalars.return_value.all.return_value = [
            task for task in sample_monitoring_tasks if task.member_id == member.id
        ]

        mock_assistance_result = Mock()
        mock_assistance_result.scalars.return_value.all.return_value = [
            task for task in sample_assistance_tasks if task.member_id == member.id
        ]

        # 模拟数据库查询调用顺序
        mock_db.execute.side_effect = [
            mock_repair_result,
            mock_monitoring_result, 
            mock_assistance_result
        ]

        result = await work_hours_service.calculate_monthly_work_hours(
            member.id, year, month
        )

        # 验证计算结果
        assert result["member_id"] == member.id
        assert result["year"] == year
        assert result["month"] == month
        assert result["repair_task_hours"] == 1.33  # (40 + 40) / 60 = 1.33
        assert result["monitoring_hours"] == 1.0  # 60 / 60 = 1.0  
        assert result["assistance_hours"] == 0.5  # 30 / 60 = 0.5

        # 奖励工时：爆单任务 +15分钟 = 0.25小时
        expected_rush_hours = 0.25
        assert result["rush_task_hours"] == expected_rush_hours

        # 惩罚工时：迟到响应 -30分钟 = -0.5小时
        expected_penalty = -0.5
        assert result["penalty_hours"] == expected_penalty

    @pytest.mark.asyncio
    async def test_calculate_monthly_work_hours_empty_data(
        self, work_hours_service, mock_db, sample_members
    ):
        """测试空数据的月度工时计算"""
        member = sample_members[0]
        year, month = 2024, 3

        # Mock 空结果
        mock_empty_result = Mock()
        mock_empty_result.scalars.return_value.all.return_value = []
        mock_db.execute.return_value = mock_empty_result

        result = await work_hours_service.calculate_monthly_work_hours(
            member.id, year, month
        )

        # 验证空数据处理
        assert result["member_id"] == member.id
        assert result["repair_task_hours"] == 0.0
        assert result["monitoring_hours"] == 0.0
        assert result["assistance_hours"] == 0.0
        assert result["total_hours"] == 0.0
        assert result["is_full_attendance"] is False

    @pytest.mark.asyncio
    async def test_calculate_monthly_work_hours_full_attendance(
        self, work_hours_service, mock_db, sample_members
    ):
        """测试满勤判断逻辑"""
        member = sample_members[0]
        year, month = 2024, 3

        # 创建满足满勤条件的任务数据 (总计30小时)
        high_work_tasks = [
            RepairTask(
                id=10 + i,
                task_id=f"FULL_TASK_{10+i}",
                title=f"满勤测试任务{i+1}",
                member_id=member.id,
                work_minutes=360,  # 6小时
                task_type=TaskType.ONLINE,
                status=TaskStatus.COMPLETED,
                completion_time=datetime(2024, 3, i + 1),
                report_time=datetime(2024, 3, i + 1),
                rating=5,
            )
            for i in range(5)  # 5个任务，每个6小时，总计30小时
        ]

        mock_repair_result = Mock()
        mock_repair_result.scalars.return_value.all.return_value = high_work_tasks

        mock_empty_result = Mock()
        mock_empty_result.scalars.return_value.all.return_value = []

        mock_db.execute.side_effect = [
            mock_repair_result,
            mock_empty_result,  # monitoring tasks
            mock_empty_result,  # assistance tasks
        ]

        result = await work_hours_service.calculate_monthly_work_hours(
            member.id, year, month
        )

        # 验证满勤判断
        assert result["total_hours"] == 30.0
        assert result["is_full_attendance"] is True

    @pytest.mark.asyncio
    async def test_batch_update_monthly_summaries(
        self, work_hours_service, mock_db, sample_members
    ):
        """测试批量更新月度工时汇总"""
        year, month = 2024, 3

        # Mock 活跃成员查询
        mock_members_result = Mock()
        mock_members_result.scalars.return_value.all.return_value = sample_members

        # Mock 工时计算结果
        with patch.object(
            work_hours_service,
            'calculate_monthly_work_hours',
            return_value={
                'member_id': 1,
                'total_hours': 25.5,
                'repair_task_hours': 20.0,
                'monitoring_hours': 3.0,
                'assistance_hours': 2.5,
                'penalty_hours': 0.0,
                'rush_task_hours': 0.0,
                'positive_review_hours': 0.0,
                'is_full_attendance': False
            }
        ):
            # Mock 现有汇总查询（假设不存在）
            mock_existing_result = Mock()
            mock_existing_result.scalars.return_value.all.return_value = []

            mock_db.execute.side_effect = [
                mock_members_result,  # 活跃成员查询
                mock_existing_result,  # 现有汇总查询
            ]

            result = await work_hours_service.batch_update_monthly_summaries(
                year, month
            )

            # 验证批量更新结果
            assert result["year"] == year
            assert result["month"] == month
            assert result["updated"] == len(sample_members)
            assert result["failed"] == 0


class TestMonthlyAttendanceStatistics:
    """月度考勤统计测试"""

    @pytest.mark.asyncio
    async def test_get_attendance_statistics_cached(
        self, stats_service, mock_db, sample_attendance_records
    ):
        """测试考勤统计计算（缓存版本）"""
        date_from = datetime(2024, 3, 1)
        date_to = datetime(2024, 3, 31)

        # Mock 考勤记录查询
        mock_result = Mock()
        mock_result.first.return_value = Mock(
            total_records=len(sample_attendance_records),
            checkin_count=len(sample_attendance_records),
            checkout_count=len(sample_attendance_records),
            late_count=1,  # 张三有一次迟到
            early_count=1,  # 李四有一次早退
            avg_work_hours=7.67,  # (8.0 + 7.5 + 7.5) / 3
            total_work_hours=23.0,  # 8.0 + 7.5 + 7.5
        )
        mock_db.execute.return_value = mock_result

        result = await stats_service._get_attendance_statistics_cached(
            date_from, date_to
        )

        # 验证考勤统计结果
        assert result["total_records"] == len(sample_attendance_records)
        assert result["checkin_count"] == len(sample_attendance_records)
        assert result["late_count"] == 1
        assert result["early_count"] == 1
        assert result["late_rate"] == 33.33  # 1/3 * 100 = 33.33%
        assert result["early_checkout_rate"] == 33.33  # 1/3 * 100 = 33.33%
        assert result["avg_work_hours"] == 7.67
        assert result["total_work_hours"] == 23.0

    @pytest.mark.asyncio
    async def test_get_attendance_statistics_no_data(
        self, stats_service, mock_db
    ):
        """测试无考勤数据的情况"""
        date_from = datetime(2024, 3, 1)
        date_to = datetime(2024, 3, 31)

        # Mock 空结果
        mock_result = Mock()
        mock_result.first.return_value = None
        mock_db.execute.return_value = mock_result

        result = await stats_service._get_attendance_statistics_cached(
            date_from, date_to
        )

        # 验证默认值处理
        assert result["total_records"] == 0
        assert result["checkin_count"] == 0
        assert result["overall_rate"] == 0
        assert result["late_rate"] == 0
        assert result["avg_work_hours"] == 0
        assert result["total_work_hours"] == 0

    @pytest.mark.asyncio
    async def test_get_attendance_statistics_with_exception(
        self, stats_service, mock_db
    ):
        """测试考勤统计异常处理"""
        date_from = datetime(2024, 3, 1)
        date_to = datetime(2024, 3, 31)

        # Mock 数据库异常
        mock_db.execute.side_effect = Exception("Database connection failed")

        result = await stats_service._get_attendance_statistics_cached(
            date_from, date_to
        )

        # 验证异常处理，返回默认值
        assert result["total_records"] == 0
        assert result["checkin_count"] == 0
        assert result["overall_rate"] == 0
        assert result["late_rate"] == 0
        assert result["avg_work_hours"] == 0
        assert result["total_work_hours"] == 0


class TestPerformanceEvaluation:
    """绩效评估计算测试"""

    @pytest.mark.asyncio
    async def test_get_performance_statistics_cached(
        self, stats_service, mock_db, sample_repair_tasks
    ):
        """测试绩效统计计算"""
        date_from = datetime(2024, 3, 1)
        date_to = datetime(2024, 3, 31)

        # 计算预期的统计值
        completed_tasks = [t for t in sample_repair_tasks if t.status == TaskStatus.COMPLETED]
        rated_tasks = [t for t in completed_tasks if t.rating is not None]
        avg_rating = sum(t.rating for t in rated_tasks) / len(rated_tasks)
        good_rating_count = len([t for t in rated_tasks if t.rating >= 4])
        poor_rating_count = len([t for t in rated_tasks if t.rating <= 2])

        # Mock 绩效查询结果
        mock_result = Mock()
        mock_result.first.return_value = Mock(
            overall_rating=avg_rating,
            rated_count=len(rated_tasks),
            total_tasks=len(completed_tasks),
            good_rating_count=good_rating_count,
            poor_rating_count=poor_rating_count,
        )
        mock_db.execute.return_value = mock_result

        result = await stats_service._get_performance_statistics_cached(
            date_from, date_to
        )

        # 验证绩效统计结果
        assert result["overall_rating"] == round(avg_rating, 2)
        assert result["rated_count"] == len(rated_tasks)
        assert result["rating_rate"] == round(len(rated_tasks) / len(completed_tasks) * 100, 2)
        assert result["good_rating_count"] == good_rating_count
        assert result["poor_rating_count"] == poor_rating_count
        assert result["good_rating_rate"] == round(good_rating_count / len(rated_tasks) * 100, 2)
        assert result["poor_rating_rate"] == round(poor_rating_count / len(rated_tasks) * 100, 2)

    @pytest.mark.asyncio
    async def test_member_quality_statistics(
        self, stats_service, mock_db, sample_repair_tasks, sample_members
    ):
        """测试成员质量统计"""
        member = sample_members[0]  # 张三
        start_date = datetime(2024, 3, 1)
        end_date = datetime(2024, 3, 31)

        # 张三的任务
        member_tasks = [t for t in sample_repair_tasks if t.member_id == member.id]

        # Mock 任务查询
        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = member_tasks
        mock_db.execute.return_value = mock_result

        result = await stats_service._get_member_quality_statistics(
            member.id, start_date, end_date
        )

        # 计算预期值
        rated_tasks = [t for t in member_tasks if t.rating is not None]
        avg_rating = sum(t.rating for t in rated_tasks) / len(rated_tasks)
        positive_reviews = len([t for t in rated_tasks if t.rating >= 4])
        positive_rate = positive_reviews / len(rated_tasks) * 100
        overdue_response = len([t for t in member_tasks if t.is_overdue_response])
        overdue_completion = len([t for t in member_tasks if t.is_overdue_completion])

        # 验证质量统计结果
        assert result["avg_rating"] == round(avg_rating, 2)
        assert result["total_rated_tasks"] == len(rated_tasks)
        assert result["positive_rate"] == round(positive_rate, 2)
        assert result["overdue_response"] == overdue_response
        assert result["overdue_completion"] == overdue_completion

    @pytest.mark.asyncio
    async def test_member_ranking_calculation(
        self, stats_service, mock_db, sample_members
    ):
        """测试成员排名计算"""
        member = sample_members[0]  # 张三
        start_date = datetime(2024, 3, 1)
        end_date = datetime(2024, 3, 31)

        # Mock 排名查询结果 (按工时降序)
        ranking_data = [
            (2, "李四", 3000),      # 李四第1名，50小时
            (1, "张三", 1800),      # 张三第2名，30小时  
            (3, "王五", 1200),      # 王五第3名，20小时
        ]

        mock_result = Mock()
        mock_result.fetchall.return_value = ranking_data
        mock_db.execute.return_value = mock_result

        result = await stats_service._get_member_ranking(
            member.id, start_date, end_date
        )

        # 验证排名结果
        assert result["work_hour_rank"] == 2  # 张三排第2名
        assert result["total_members"] == 3
        assert result["percentile"] == 66.7  # (1 - (2-1)/3) * 100 = 66.7%


class TestBoundaryConditions:
    """边界条件和异常情况测试"""

    @pytest.mark.asyncio
    async def test_monthly_statistics_cross_year(
        self, work_hours_service, mock_db, sample_members
    ):
        """测试跨年份的月度统计"""
        member = sample_members[0]
        
        # 测试12月到1月的跨年情况
        year, month = 2024, 12
        
        # Mock 空结果（跨年边界情况通常数据较少）
        mock_empty_result = Mock()
        mock_empty_result.scalars.return_value.all.return_value = []
        mock_db.execute.return_value = mock_empty_result

        result = await work_hours_service.calculate_monthly_work_hours(
            member.id, year, month
        )

        # 验证跨年处理
        assert result["year"] == 2024
        assert result["month"] == 12
        assert result["total_hours"] == 0.0

    @pytest.mark.asyncio
    async def test_leap_year_february_calculation(
        self, work_hours_service, mock_db, sample_members
    ):
        """测试闰年2月的工时计算"""
        member = sample_members[0]
        year, month = 2024, 2  # 2024年是闰年

        # 验证2024年2月有29天
        assert monthrange(year, month)[1] == 29

        mock_empty_result = Mock()
        mock_empty_result.scalars.return_value.all.return_value = []
        mock_db.execute.return_value = mock_empty_result

        result = await work_hours_service.calculate_monthly_work_hours(
            member.id, year, month
        )

        # 验证闰年处理
        assert result["year"] == 2024
        assert result["month"] == 2
        
    @pytest.mark.asyncio
    async def test_extreme_work_hours_calculation(
        self, work_hours_service, mock_db, sample_members
    ):
        """测试极值工时计算（大量任务情况）"""
        member = sample_members[0]
        year, month = 2024, 3

        # 创建大量任务数据（模拟高工作量成员）
        extreme_tasks = [
            RepairTask(
                id=100 + i,
                task_id=f"EXTREME_TASK_{100+i}",
                title=f"极值测试任务{i+1}",
                member_id=member.id,
                work_minutes=240,  # 4小时每个任务
                task_type=TaskType.ONLINE,
                status=TaskStatus.COMPLETED,
                completion_time=datetime(2024, 3, (i % 30) + 1),
                report_time=datetime(2024, 3, (i % 30) + 1),
                rating=5,
            )
            for i in range(50)  # 50个任务，总计200小时
        ]

        mock_repair_result = Mock()
        mock_repair_result.scalars.return_value.all.return_value = extreme_tasks

        mock_empty_result = Mock()
        mock_empty_result.scalars.return_value.all.return_value = []

        mock_db.execute.side_effect = [
            mock_repair_result,
            mock_empty_result,  # monitoring
            mock_empty_result,  # assistance
        ]

        result = await work_hours_service.calculate_monthly_work_hours(
            member.id, year, month
        )

        # 验证极值处理
        expected_base_hours = 50 * 4  # 200小时基础工时
        expected_rush_bonus = 10 * 0.25  # 10个爆单任务，每个+0.25小时
        expected_total = expected_base_hours + expected_rush_bonus

        assert result["repair_task_hours"] == expected_base_hours
        assert result["rush_task_hours"] == expected_rush_bonus
        assert result["total_hours"] == expected_total
        assert result["is_full_attendance"] is True  # 远超满勤标准

    @pytest.mark.asyncio
    async def test_invalid_member_id(
        self, work_hours_service, mock_db
    ):
        """测试无效成员ID的处理"""
        invalid_member_id = 99999
        year, month = 2024, 3

        # Mock 空结果
        mock_empty_result = Mock()
        mock_empty_result.scalars.return_value.all.return_value = []
        mock_db.execute.return_value = mock_empty_result

        result = await work_hours_service.calculate_monthly_work_hours(
            invalid_member_id, year, month
        )

        # 验证无效ID处理
        assert result["member_id"] == invalid_member_id
        assert result["total_hours"] == 0.0
        assert result["is_full_attendance"] is False

    @pytest.mark.asyncio
    async def test_database_connection_error(
        self, work_hours_service, mock_db, sample_members
    ):
        """测试数据库连接错误的处理"""
        member = sample_members[0]
        year, month = 2024, 3

        # Mock 数据库异常
        mock_db.execute.side_effect = Exception("Database connection lost")

        with pytest.raises(Exception, match="Database connection lost"):
            await work_hours_service.calculate_monthly_work_hours(
                member.id, year, month
            )

    @pytest.mark.asyncio
    async def test_monthly_statistics_data_consistency(
        self, stats_service, mock_db, sample_members
    ):
        """测试月度统计数据一致性"""
        year, month = 2024, 3

        # Mock 月度统计查询
        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = [
            Mock(
                status=TaskStatus.COMPLETED,
                work_minutes=100,
            ),
            Mock(
                status=TaskStatus.COMPLETED,
                work_minutes=150,
            ),
            Mock(
                status=TaskStatus.PENDING,
                work_minutes=0,
            )
        ]
        mock_db.execute.return_value = mock_result

        start_date = datetime(year, month, 1)
        _, last_day = monthrange(year, month)
        end_date = datetime(year, month, last_day, 23, 59, 59)

        result = await stats_service._get_monthly_statistics(
            start_date, end_date
        )

        # 验证数据一致性
        assert result["total_tasks"] == 3
        assert result["completed_tasks"] == 2
        assert result["total_work_hours"] == round((100 + 150) / 60, 2)  # 4.17小时
        assert result["completion_rate"] == round(2 / 3 * 100, 2)  # 66.67%

    @pytest.mark.asyncio
    async def test_performance_metrics_boundary_values(
        self, stats_service, mock_db
    ):
        """测试绩效指标边界值处理"""
        date_from = datetime(2024, 3, 1)
        date_to = datetime(2024, 3, 31)

        # 测试极端评分情况
        test_cases = [
            # 全部最高分
            {
                "overall_rating": 5.0,
                "good_rating_count": 10,
                "poor_rating_count": 0,
                "rated_count": 10,
                "total_tasks": 10,
            },
            # 全部最低分
            {
                "overall_rating": 1.0,
                "good_rating_count": 0,
                "poor_rating_count": 10,
                "rated_count": 10,
                "total_tasks": 10,
            },
            # 无评分任务
            {
                "overall_rating": None,
                "good_rating_count": 0,
                "poor_rating_count": 0,
                "rated_count": 0,
                "total_tasks": 5,
            }
        ]

        for case in test_cases:
            mock_result = Mock()
            mock_result.first.return_value = Mock(**case)
            mock_db.execute.return_value = mock_result

            result = await stats_service._get_performance_statistics_cached(
                date_from, date_to
            )

            # 验证边界值处理
            if case["overall_rating"] is not None:
                assert result["overall_rating"] == case["overall_rating"]
                assert result["good_rating_rate"] <= 100.0
                assert result["poor_rating_rate"] <= 100.0
            else:
                assert result["overall_rating"] == 0.0
                assert result["good_rating_rate"] == 0.0
                assert result["poor_rating_rate"] == 0.0

            assert result["rating_rate"] >= 0.0
            assert result["rating_rate"] <= 100.0


class TestIntegrationScenarios:
    """集成测试场景"""

    @pytest.mark.asyncio
    async def test_complete_monthly_report_generation(
        self, stats_service, mock_db, sample_members, sample_repair_tasks
    ):
        """测试完整的月度报表生成流程"""
        year, month = 2024, 3
        
        # Mock 综合统计服务调用
        with patch.object(
            stats_service,
            '_get_member_task_statistics',
            return_value={
                'total_tasks': 2,
                'completed_tasks': 2,
                'completion_rate': 100.0
            }
        ), patch.object(
            stats_service,
            '_get_member_work_hour_statistics', 
            return_value={
                'total_hours': 25.5,
                'repair_hours': 20.0,
                'monitoring_hours': 3.0,
                'assistance_hours': 2.5
            }
        ), patch.object(
            stats_service,
            '_get_member_quality_statistics',
            return_value={
                'avg_rating': 4.2,
                'positive_rate': 85.0,
                'overdue_response': 1,
                'overdue_completion': 0
            }
        ), patch.object(
            stats_service,
            '_get_member_ranking',
            return_value={
                'work_hour_rank': 2,
                'total_members': 3,
                'percentile': 66.7
            }
        ), patch.object(
            stats_service,
            '_get_member_trend_analysis',
            return_value={
                'change_rate': 15.5,
                'trend_direction': 'up'
            }
        ):
            # Mock 成员查询
            mock_result = Mock()
            mock_result.scalar_one_or_none.return_value = sample_members[0]
            mock_db.execute.return_value = mock_result

            result = await stats_service.get_member_performance_report(
                sample_members[0].id, year, month
            )

            # 验证完整报表结构
            assert "member" in result
            assert "period" in result
            assert "tasks" in result
            assert "work_hours" in result
            assert "quality" in result
            assert "ranking" in result
            assert "trends" in result

            # 验证关键指标
            assert result["tasks"]["completion_rate"] == 100.0
            assert result["work_hours"]["total_hours"] == 25.5
            assert result["quality"]["avg_rating"] == 4.2
            assert result["ranking"]["work_hour_rank"] == 2

    @pytest.mark.asyncio
    async def test_team_comparison_with_mixed_performance(
        self, stats_service, mock_db, sample_members
    ):
        """测试团队对比报告（混合绩效场景）"""
        
        # 模拟不同绩效水平的成员数据
        performance_data = [
            # 张三 - 高绩效
            {
                'work_hours': {'total_hours': 35.5},
                'tasks': {'total_tasks': 15, 'completed_tasks': 15},
                'quality': {'avg_rating': 4.8, 'positive_rate': 95.0}
            },
            # 李四 - 中等绩效  
            {
                'work_hours': {'total_hours': 28.2},
                'tasks': {'total_tasks': 12, 'completed_tasks': 11}, 
                'quality': {'avg_rating': 3.9, 'positive_rate': 75.0}
            },
            # 王五 - 较低绩效
            {
                'work_hours': {'total_hours': 18.7},
                'tasks': {'total_tasks': 8, 'completed_tasks': 6},
                'quality': {'avg_rating': 3.2, 'positive_rate': 60.0}
            }
        ]

        # Mock 成员查询
        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = sample_members
        mock_db.execute.return_value = mock_result

        with patch.object(
            stats_service,
            '_get_member_comparison_stats',
            side_effect=performance_data
        ), patch.object(
            stats_service,
            '_calculate_team_summary',
            return_value={
                'total_members': 3,
                'total_hours': 82.4,  # 35.5 + 28.2 + 18.7
                'total_tasks': 35,
                'total_completed': 32,
                'team_completion_rate': 91.43,
                'team_avg_rating': 3.97
            }
        ):
            result = await stats_service.get_team_comparison_report()

            # 验证团队对比结果
            assert result["team_summary"]["total_members"] == 3
            assert result["team_summary"]["total_hours"] == 82.4
            assert result["team_summary"]["team_completion_rate"] == 91.43
            
            # 验证成员排名（按工时排序）
            rankings = result["member_rankings"]
            assert len(rankings) == 3
            assert rankings[0]["work_hours"]["total_hours"] >= rankings[1]["work_hours"]["total_hours"]
            assert rankings[1]["work_hours"]["total_hours"] >= rankings[2]["work_hours"]["total_hours"]