"""
工时计算核心业务逻辑测试
补充测试覆盖率严重不足的关键算法
"""

from datetime import datetime, timedelta

import pytest

from app.models.member import Member, UserRole
from app.models.task import RepairTask, TaskStatus, TaskTag, TaskTagType, TaskType
from app.services.work_hours_service import WorkHoursCalculationService


@pytest.mark.asyncio
class TestWorkHourCalculationAlgorithm:
    """工时计算算法核心测试"""

    async def test_online_task_base_minutes(self, async_session):
        """测试线上任务基础工时：40分钟"""
        # 创建测试成员
        member = Member(
            username="test_user",
            name="测试用户",
            student_id="TEST001",
            class_name="测试班级",
            role=UserRole.MEMBER,
        )
        async_session.add(member)
        await async_session.flush()

        # 创建线上任务
        task = RepairTask(
            task_id="TEST_ONLINE_001",
            title="线上维修任务",
            description="测试线上任务工时计算",
            task_type=TaskType.ONLINE,
            status=TaskStatus.COMPLETED,
            member_id=member.id,
            report_time=datetime.utcnow(),
        )
        async_session.add(task)
        await async_session.commit()

        # 测试基础工时计算
        base_minutes = task.get_base_work_minutes()
        assert (
            base_minutes == 40
        ), f"Expected 40 minutes for online task, got {base_minutes}"

        # 测试总工时计算（无额外标签）
        total_minutes = task.calculate_work_minutes()
        assert total_minutes == 40, f"Expected 40 total minutes, got {total_minutes}"

    async def test_offline_task_base_minutes(self, async_session):
        """测试线下任务基础工时：100分钟"""
        # 创建测试成员
        member = Member(
            username="test_user_offline",
            name="测试用户线下",
            student_id="TEST002",
            class_name="测试班级",
            role=UserRole.MEMBER,
        )
        async_session.add(member)
        await async_session.flush()

        # 创建线下任务
        task = RepairTask(
            task_id="TEST_OFFLINE_001",
            title="线下维修任务",
            description="测试线下任务工时计算",
            task_type=TaskType.OFFLINE,
            status=TaskStatus.COMPLETED,
            member_id=member.id,
            report_time=datetime.utcnow(),
        )
        async_session.add(task)
        await async_session.commit()

        # 测试基础工时计算
        base_minutes = task.get_base_work_minutes()
        assert (
            base_minutes == 100
        ), f"Expected 100 minutes for offline task, got {base_minutes}"

        # 测试总工时计算（无额外标签）
        total_minutes = task.calculate_work_minutes()
        assert total_minutes == 100, f"Expected 100 total minutes, got {total_minutes}"

    async def test_rush_order_bonus_calculation(self, async_session):
        """测试爆单奖励：+15分钟"""
        # 创建测试成员
        member = Member(
            username="test_rush_user",
            name="爆单测试用户",
            student_id="TEST003",
            class_name="测试班级",
            role=UserRole.MEMBER,
        )
        async_session.add(member)
        await async_session.flush()

        # 创建爆单任务
        task = RepairTask(
            task_id="TEST_RUSH_001",
            title="爆单任务",
            description="测试爆单奖励计算",
            task_type=TaskType.ONLINE,
            status=TaskStatus.COMPLETED,
            member_id=member.id,
            report_time=datetime.utcnow(),
            is_rush_order=True,
        )

        # 创建爆单标签
        rush_tag = TaskTag(
            name="爆单任务",
            description="爆单任务标记，独立计算工时15分钟",
            work_minutes_modifier=15,
            tag_type=TaskTagType.RUSH_ORDER,
            is_active=True,
        )

        task.tags = [rush_tag]
        async_session.add_all([task, rush_tag])
        await async_session.commit()

        # 验证爆单标记
        assert task.is_rush_order is True

        # 测试工时计算：40基础 + 15爆单 = 55分钟
        total_minutes = task.calculate_work_minutes()
        assert total_minutes == 55, f"Expected 55 minutes (40+15), got {total_minutes}"

    async def test_penalty_calculation_late_response(self, async_session):
        """测试延迟响应惩罚：-30分钟"""
        # 创建测试成员
        member = Member(
            username="test_late_user",
            name="延迟响应测试用户",
            student_id="TEST004",
            class_name="测试班级",
            role=UserRole.MEMBER,
        )
        async_session.add(member)
        await async_session.flush()

        # 创建延迟响应任务
        report_time = datetime.utcnow() - timedelta(hours=25)  # 25小时前报告
        response_time = datetime.utcnow() - timedelta(hours=1)  # 1小时前响应（超时）

        task = RepairTask(
            task_id="TEST_LATE_001",
            title="延迟响应任务",
            description="测试延迟响应惩罚",
            task_type=TaskType.ONLINE,
            status=TaskStatus.COMPLETED,
            member_id=member.id,
            report_time=report_time,
            response_time=response_time,
        )

        # 创建延迟响应惩罚标签
        late_tag = TaskTag(
            name="延迟响应",
            description="响应超时，惩罚30分钟",
            work_minutes_modifier=-30,
            tag_type=TaskTagType.TIMEOUT_RESPONSE,
            is_active=True,
        )

        task.tags = [late_tag]
        async_session.add_all([task, late_tag])
        await async_session.commit()

        # 测试延迟检测
        assert task.is_overdue_response is True

        # 测试工时计算：40基础 - 30惩罚 = 10分钟
        total_minutes = task.calculate_work_minutes()
        assert total_minutes == 10, f"Expected 10 minutes (40-30), got {total_minutes}"

    async def test_penalty_calculation_late_completion(self, async_session):
        """测试延迟完成惩罚：-30分钟"""
        # 创建测试成员
        member = Member(
            username="test_late_complete_user",
            name="延迟完成测试用户",
            student_id="TEST005",
            class_name="测试班级",
            role=UserRole.MEMBER,
        )
        async_session.add(member)
        await async_session.flush()

        # 创建延迟完成任务
        response_time = datetime.utcnow() - timedelta(hours=50)  # 50小时前响应
        completion_time = datetime.utcnow()  # 刚完成（超时）

        task = RepairTask(
            task_id="TEST_LATE_COMPLETE_001",
            title="延迟完成任务",
            description="测试延迟完成惩罚",
            task_type=TaskType.OFFLINE,
            status=TaskStatus.COMPLETED,
            member_id=member.id,
            report_time=datetime.utcnow() - timedelta(hours=51),
            response_time=response_time,
            completion_time=completion_time,
        )

        # 创建延迟完成惩罚标签
        late_complete_tag = TaskTag(
            name="延迟完成",
            description="完成超时，惩罚30分钟",
            work_minutes_modifier=-30,
            tag_type=TaskTagType.TIMEOUT_PROCESSING,
            is_active=True,
        )

        task.tags = [late_complete_tag]
        async_session.add_all([task, late_complete_tag])
        await async_session.commit()

        # 测试延迟完成检测
        assert task.is_overdue_completion is True

        # 测试工时计算：100基础 - 30惩罚 = 70分钟
        total_minutes = task.calculate_work_minutes()
        assert total_minutes == 70, f"Expected 70 minutes (100-30), got {total_minutes}"

    async def test_rating_bonus_system(self, async_session):
        """测试评价奖励系统：非默认好评+30分钟"""
        # 创建测试成员
        member = Member(
            username="test_rating_user",
            name="评价奖励测试用户",
            student_id="TEST006",
            class_name="测试班级",
            role=UserRole.MEMBER,
        )
        async_session.add(member)
        await async_session.flush()

        # 创建高评价任务
        task = RepairTask(
            task_id="TEST_RATING_001",
            title="高评价任务",
            description="测试评价奖励计算",
            task_type=TaskType.ONLINE,
            status=TaskStatus.COMPLETED,
            member_id=member.id,
            report_time=datetime.utcnow(),
            rating=5,  # 5星好评
            feedback="非常满意的服务",
        )

        # 创建非默认好评奖励标签
        rating_tag = TaskTag(
            name="非默认好评",
            description="用户给出非默认好评，奖励30分钟",
            work_minutes_modifier=30,
            tag_type=TaskTagType.NON_DEFAULT_RATING,
            is_active=True,
        )

        task.tags = [rating_tag]
        async_session.add_all([task, rating_tag])
        await async_session.commit()

        # 测试好评检测
        assert task.is_positive_review is True
        assert task.rating == 5

        # 测试工时计算：40基础 + 30奖励 = 70分钟
        total_minutes = task.calculate_work_minutes()
        assert total_minutes == 70, f"Expected 70 minutes (40+30), got {total_minutes}"

    async def test_bad_rating_penalty(self, async_session):
        """测试差评惩罚：≤2星-60分钟"""
        # 创建测试成员
        member = Member(
            username="test_bad_rating_user",
            name="差评惩罚测试用户",
            student_id="TEST007",
            class_name="测试班级",
            role=UserRole.MEMBER,
        )
        async_session.add(member)
        await async_session.flush()

        # 创建差评任务
        task = RepairTask(
            task_id="TEST_BAD_RATING_001",
            title="差评任务",
            description="测试差评惩罚计算",
            task_type=TaskType.OFFLINE,
            status=TaskStatus.COMPLETED,
            member_id=member.id,
            report_time=datetime.utcnow(),
            rating=2,  # 2星差评
            feedback="服务不满意",
        )

        # 创建差评惩罚标签
        bad_rating_tag = TaskTag(
            name="差评",
            description="用户给出差评（≤2星），惩罚60分钟",
            work_minutes_modifier=-60,
            tag_type=TaskTagType.BAD_RATING,
            is_active=True,
        )

        task.tags = [bad_rating_tag]
        async_session.add_all([task, bad_rating_tag])
        await async_session.commit()

        # 测试差评检测
        assert task.rating == 2
        assert task.rating <= 2  # 差评条件

        # 测试工时计算：100基础 - 60惩罚 = 40分钟
        total_minutes = task.calculate_work_minutes()
        assert total_minutes == 40, f"Expected 40 minutes (100-60), got {total_minutes}"

    async def test_complex_work_hour_calculation(self, async_session):
        """测试复杂工时计算：多种标签组合"""
        # 创建测试成员
        member = Member(
            username="test_complex_user",
            name="复杂工时测试用户",
            student_id="TEST008",
            class_name="测试班级",
            role=UserRole.MEMBER,
        )
        async_session.add(member)
        await async_session.flush()

        # 创建复杂任务：爆单 + 延迟响应 + 好评
        task = RepairTask(
            task_id="TEST_COMPLEX_001",
            title="复杂工时任务",
            description="测试多标签工时计算",
            task_type=TaskType.ONLINE,  # 40基础分钟
            status=TaskStatus.COMPLETED,
            member_id=member.id,
            report_time=datetime.utcnow() - timedelta(hours=25),  # 延迟响应
            response_time=datetime.utcnow() - timedelta(hours=1),
            rating=5,
            is_rush_order=True,
        )

        # 创建多个标签
        rush_tag = TaskTag(
            name="爆单任务",
            work_minutes_modifier=15,
            tag_type=TaskTagType.RUSH_ORDER,
            is_active=True,
        )

        late_tag = TaskTag(
            name="延迟响应",
            work_minutes_modifier=-30,
            tag_type=TaskTagType.TIMEOUT_RESPONSE,
            is_active=True,
        )

        rating_tag = TaskTag(
            name="非默认好评",
            work_minutes_modifier=30,
            tag_type=TaskTagType.NON_DEFAULT_RATING,
            is_active=True,
        )

        task.tags = [rush_tag, late_tag, rating_tag]
        async_session.add_all([task, rush_tag, late_tag, rating_tag])
        await async_session.commit()

        # 测试复杂工时计算：40基础 + 15爆单 - 30延迟 + 30好评 = 55分钟
        total_minutes = task.calculate_work_minutes()
        expected = 40 + 15 - 30 + 30  # 55
        assert (
            total_minutes == expected
        ), f"Expected {expected} minutes, got {total_minutes}"

    async def test_work_hour_service_integration(self, async_session):
        """测试工时服务集成"""
        service = WorkHoursCalculationService(async_session)

        # 创建测试成员
        member = Member(
            username="test_service_user",
            name="服务测试用户",
            student_id="TEST009",
            class_name="测试班级",
            role=UserRole.MEMBER,
        )
        async_session.add(member)
        await async_session.flush()

        # 创建测试任务
        task = RepairTask(
            task_id="TEST_SERVICE_001",
            title="服务测试任务",
            task_type=TaskType.ONLINE,
            status=TaskStatus.COMPLETED,
            member_id=member.id,
            report_time=datetime.utcnow(),
        )
        async_session.add(task)
        await async_session.commit()

        # 测试工时计算服务
        result = await service.calculate_task_work_minutes(task)

        # 验证结果结构
        assert isinstance(result, dict)
        assert "base_minutes" in result
        assert "modifier_minutes" in result
        assert "total_minutes" in result

        # 验证基础计算
        assert result["base_minutes"] == 40  # 线上任务基础工时
        assert result["total_minutes"] >= 0  # 总工时不应为负

    async def test_edge_case_zero_work_minutes(self, async_session):
        """测试边界情况：工时为零或负数"""
        # 创建测试成员
        member = Member(
            username="test_zero_user",
            name="零工时测试用户",
            student_id="TEST010",
            class_name="测试班级",
            role=UserRole.MEMBER,
        )
        async_session.add(member)
        await async_session.flush()

        # 创建高惩罚任务
        task = RepairTask(
            task_id="TEST_ZERO_001",
            title="高惩罚任务",
            task_type=TaskType.ONLINE,  # 40基础
            status=TaskStatus.COMPLETED,
            member_id=member.id,
            report_time=datetime.utcnow(),
        )

        # 添加多个惩罚标签，总惩罚超过基础工时
        penalty_tags = [
            TaskTag(
                name="延迟响应",
                work_minutes_modifier=-30,
                tag_type=TaskTagType.TIMEOUT_RESPONSE,
                is_active=True,
            ),
            TaskTag(
                name="延迟完成",
                work_minutes_modifier=-30,
                tag_type=TaskTagType.TIMEOUT_PROCESSING,
                is_active=True,
            ),
            TaskTag(
                name="差评",
                work_minutes_modifier=-60,
                tag_type=TaskTagType.BAD_RATING,
                is_active=True,
            ),
        ]

        task.tags = penalty_tags
        async_session.add_all([task] + penalty_tags)
        await async_session.commit()

        # 测试工时计算：40 - 30 - 30 - 60 = -80，应该被限制为0
        total_minutes = task.calculate_work_minutes()
        assert (
            total_minutes >= 0
        ), f"Work minutes should not be negative, got {total_minutes}"
