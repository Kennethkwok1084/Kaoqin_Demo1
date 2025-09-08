"""
服务层业务逻辑真实功能测试
针对低覆盖率的服务层模块，提供真正的业务逻辑测试
重点覆盖：
- task_service.py (35.6% -> 目标70%)
- work_hours_service.py (37.7% -> 目标70%)
- attendance_service.py (11.5% -> 目标60%)
"""

from datetime import datetime, timedelta

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_password_hash
from app.models.attendance import AttendanceExceptionStatus, AttendanceRecord
from app.models.member import Member, UserRole
from app.models.task import RepairTask, TaskCategory, TaskStatus, TaskType
from app.services.attendance_service import AttendanceService
from app.services.task_service import TaskService
from app.services.work_hours_service import WorkHoursCalculationService


@pytest.mark.asyncio
class TestTaskServiceRealCoverage:
    """任务服务真正功能测试 - 覆盖核心业务逻辑"""

    async def test_create_task_with_validation(self, async_session: AsyncSession):
        """测试创建任务及验证逻辑"""
        # 创建测试用户
        user = Member(
            username="task_creator",
            name="任务创建者",
            student_id="2024001001",
            group_id=1,
            class_name="计算机科学2024",
            email="taskcreator@example.com",
            password_hash=get_password_hash("UserPassword123!"),
            role=UserRole.MEMBER,
            is_active=True,
            is_verified=True,
        )
        async_session.add(user)
        await async_session.commit()
        await async_session.refresh(user)

        # 初始化服务
        task_service = TaskService(async_session)

        # 测试有效的任务创建
        valid_task_data = {
            "title": "服务层测试任务",
            "description": "通过服务层创建的测试任务",
            "category": TaskCategory.REPAIR,
            "task_type": TaskType.ONLINE,
            "priority": "high",
            "reporter_name": "测试报告人",
            "reporter_contact": "13800138000",
            "location": "实验室A101",
            "problem_description": "系统故障需要修复",
            "expected_completion_time": datetime.now() + timedelta(hours=24),
            "assignee_id": user.id,
        }

        # 执行任务创建
        created_task = await task_service.create_repair_task(valid_task_data)

        # 验证创建结果
        assert created_task is not None
        assert created_task.title == "服务层测试任务"
        assert created_task.status == TaskStatus.PENDING
        assert created_task.assignee_id == user.id
        assert created_task.category == TaskCategory.REPAIR

        # 验证任务编号生成逻辑
        assert created_task.task_number is not None
        assert created_task.task_number.startswith("TASK")

        # 测试无效数据验证
        invalid_task_data = {
            "title": "",  # 空标题
            "description": "无效任务测试",
            "category": TaskCategory.REPAIR,
            "task_type": TaskType.ONLINE,
            "reporter_name": "",  # 空报告人
            "reporter_contact": "invalid_phone",  # 无效电话
            "location": "测试位置",
            "problem_description": "问题描述",
        }

        # 验证创建失败并抛出适当异常
        with pytest.raises(
            ValueError, match="标题不能为空|报告人不能为空|联系方式格式错误"
        ):
            await task_service.create_repair_task(invalid_task_data)

    async def test_task_status_workflow(self, async_session: AsyncSession):
        """测试任务状态工作流逻辑"""
        # 创建用户和任务
        user = Member(
            username="workflow_user",
            name="工作流用户",
            student_id="2024001002",
            group_id=1,
            class_name="计算机科学2024",
            email="workflow@example.com",
            password_hash=get_password_hash("UserPassword123!"),
            role=UserRole.MEMBER,
            is_active=True,
            is_verified=True,
        )
        async_session.add(user)
        await async_session.commit()
        await async_session.refresh(user)

        task = RepairTask(
            title="工作流测试任务",
            description="测试状态工作流的任务",
            category=TaskCategory.REPAIR,
            task_type=TaskType.ONLINE,
            status=TaskStatus.PENDING,
            assignee_id=user.id,
            reporter_name="工作流报告人",
            reporter_contact="13800138001",
            location="工作流位置",
            problem_description="工作流问题",
            expected_completion_time=datetime.now() + timedelta(hours=24),
        )
        async_session.add(task)
        await async_session.commit()
        await async_session.refresh(task)

        task_service = TaskService(async_session)

        # 测试状态转换：PENDING -> ASSIGNED
        await task_service.assign_task(task.id, user.id, "分配任务给技术人员")
        updated_task = await task_service.get_task_by_id(task.id)
        assert updated_task.status == TaskStatus.ASSIGNED

        # 测试状态转换：ASSIGNED -> IN_PROGRESS
        await task_service.start_task(task.id, "开始处理任务")
        updated_task = await task_service.get_task_by_id(task.id)
        assert updated_task.status == TaskStatus.IN_PROGRESS
        assert updated_task.started_at is not None

        # 测试状态转换：IN_PROGRESS -> COMPLETED
        completion_data = {
            "completion_notes": "任务已成功完成",
            "solution_description": "更换了故障硬件",
            "actual_work_hours": 2.5,
            "materials_used": ["硬盘", "内存条"],
        }
        await task_service.complete_task(task.id, completion_data)

        updated_task = await task_service.get_task_by_id(task.id)
        assert updated_task.status == TaskStatus.COMPLETED
        assert updated_task.completed_at is not None
        assert updated_task.actual_work_hours == 2.5

        # 测试无效状态转换
        with pytest.raises(ValueError, match="无效的状态转换|任务已完成"):
            await task_service.start_task(task.id, "尝试重新开始已完成的任务")

    async def test_task_search_and_filter(self, async_session: AsyncSession):
        """测试任务搜索和过滤逻辑"""
        # 创建测试用户
        user = Member(
            username="search_user",
            name="搜索用户",
            student_id="2024001003",
            group_id=1,
            class_name="计算机科学2024",
            email="search@example.com",
            password_hash=get_password_hash("UserPassword123!"),
            role=UserRole.MEMBER,
            is_active=True,
            is_verified=True,
        )
        async_session.add(user)
        await async_session.commit()
        await async_session.refresh(user)

        # 创建多种类型的任务用于搜索测试
        test_tasks = [
            {
                "title": "网络连接故障修复",
                "description": "实验室网络无法连接互联网",
                "category": TaskCategory.REPAIR,
                "task_type": TaskType.ONLINE,
                "status": TaskStatus.PENDING,
                "location": "实验室A101",
                "problem_description": "网络设备故障",
            },
            {
                "title": "打印机维修",
                "description": "办公室打印机卡纸",
                "category": TaskCategory.REPAIR,
                "task_type": TaskType.OFFLINE,
                "status": TaskStatus.IN_PROGRESS,
                "location": "办公室B201",
                "problem_description": "硬件机械故障",
            },
            {
                "title": "系统安全检查",
                "description": "定期系统安全扫描",
                "category": TaskCategory.MONITORING,
                "task_type": TaskType.ONLINE,
                "status": TaskStatus.COMPLETED,
                "location": "服务器机房",
                "problem_description": "安全检查任务",
            },
        ]

        created_tasks = []
        for task_data in test_tasks:
            task = RepairTask(
                assignee_id=user.id,
                reporter_name="搜索测试报告人",
                reporter_contact="13800138002",
                expected_completion_time=datetime.now() + timedelta(hours=24),
                **task_data,
            )
            async_session.add(task)
            created_tasks.append(task)

        await async_session.commit()

        task_service = TaskService(async_session)

        # 测试关键词搜索
        search_results = await task_service.search_tasks(
            keyword="网络", assignee_id=user.id
        )
        assert len(search_results) >= 1
        assert any(
            "网络" in task.title or "网络" in task.description
            for task in search_results
        )

        # 测试状态过滤
        pending_tasks = await task_service.get_tasks_by_status(
            TaskStatus.PENDING, user.id
        )
        assert len(pending_tasks) >= 1
        assert all(task.status == TaskStatus.PENDING for task in pending_tasks)

        # 测试类型过滤
        online_tasks = await task_service.get_tasks_by_type(TaskType.ONLINE, user.id)
        assert len(online_tasks) >= 2
        assert all(task.task_type == TaskType.ONLINE for task in online_tasks)

        # 测试位置搜索
        lab_tasks = await task_service.search_tasks(
            keyword="实验室", assignee_id=user.id
        )
        assert len(lab_tasks) >= 1
        assert any("实验室" in task.location for task in lab_tasks)

        # 测试复合条件搜索
        complex_results = await task_service.search_tasks(
            keyword="故障",
            status=TaskStatus.PENDING,
            task_type=TaskType.ONLINE,
            assignee_id=user.id,
        )
        assert all(
            task.status == TaskStatus.PENDING
            and task.task_type == TaskType.ONLINE
            and ("故障" in task.title or "故障" in task.problem_description)
            for task in complex_results
        )


@pytest.mark.asyncio
class TestWorkHoursServiceRealCoverage:
    """工时服务真正功能测试 - 覆盖工时计算核心逻辑"""

    async def test_calculate_basic_work_hours(self, async_session: AsyncSession):
        """测试基础工时计算逻辑"""
        # 创建测试任务
        user = Member(
            username="workhours_user",
            name="工时用户",
            student_id="2024001004",
            group_id=1,
            class_name="计算机科学2024",
            email="workhours@example.com",
            password_hash=get_password_hash("UserPassword123!"),
            role=UserRole.MEMBER,
            is_active=True,
            is_verified=True,
        )
        async_session.add(user)
        await async_session.commit()
        await async_session.refresh(user)

        work_hours_service = WorkHoursCalculationService(async_session)

        # 测试在线任务工时计算
        online_task = RepairTask(
            title="在线工时测试任务",
            description="测试在线任务工时计算",
            category=TaskCategory.REPAIR,
            task_type=TaskType.ONLINE,
            status=TaskStatus.COMPLETED,
            assignee_id=user.id,
            reporter_name="工时报告人",
            reporter_contact="13800138003",
            location="在线位置",
            problem_description="在线问题",
            created_at=datetime.now() - timedelta(hours=3),
            started_at=datetime.now() - timedelta(hours=2),
            completed_at=datetime.now() - timedelta(hours=1),
            expected_completion_time=datetime.now() + timedelta(hours=1),
            actual_work_hours=1.5,
        )
        async_session.add(online_task)
        await async_session.commit()
        await async_session.refresh(online_task)

        # 计算基础工时
        base_hours = await work_hours_service.calculate_base_work_hours(online_task.id)
        assert base_hours == 40 / 60  # 在线任务基础40分钟 = 0.67小时

        # 测试离线任务工时计算
        offline_task = RepairTask(
            title="离线工时测试任务",
            description="测试离线任务工时计算",
            category=TaskCategory.REPAIR,
            task_type=TaskType.OFFLINE,
            status=TaskStatus.COMPLETED,
            assignee_id=user.id,
            reporter_name="离线报告人",
            reporter_contact="13800138004",
            location="离线位置",
            problem_description="离线问题",
            created_at=datetime.now() - timedelta(hours=5),
            started_at=datetime.now() - timedelta(hours=4),
            completed_at=datetime.now() - timedelta(hours=2),
            expected_completion_time=datetime.now(),
            actual_work_hours=2.5,
        )
        async_session.add(offline_task)
        await async_session.commit()
        await async_session.refresh(offline_task)

        base_hours_offline = await work_hours_service.calculate_base_work_hours(
            offline_task.id
        )
        assert base_hours_offline == 100 / 60  # 离线任务基础100分钟 = 1.67小时

    async def test_calculate_work_hours_with_bonuses_penalties(
        self, async_session: AsyncSession
    ):
        """测试工时奖励和惩罚计算逻辑"""
        # 创建测试用户
        user = Member(
            username="bonus_user",
            name="奖惩用户",
            student_id="2024001005",
            group_id=1,
            class_name="计算机科学2024",
            email="bonus@example.com",
            password_hash=get_password_hash("UserPassword123!"),
            role=UserRole.MEMBER,
            is_active=True,
            is_verified=True,
        )
        async_session.add(user)
        await async_session.commit()
        await async_session.refresh(user)

        work_hours_service = WorkHoursCalculationService(async_session)

        # 测试高质量完成任务（奖励）
        high_quality_task = RepairTask(
            title="高质量任务",
            description="获得好评的高质量任务",
            category=TaskCategory.REPAIR,
            task_type=TaskType.ONLINE,
            status=TaskStatus.COMPLETED,
            assignee_id=user.id,
            reporter_name="满意报告人",
            reporter_contact="13800138005",
            location="高质量位置",
            problem_description="复杂问题完美解决",
            created_at=datetime.now() - timedelta(hours=4),
            started_at=datetime.now() - timedelta(hours=3),
            completed_at=datetime.now() - timedelta(hours=1),
            expected_completion_time=datetime.now() + timedelta(hours=2),
            actual_work_hours=2.0,
            quality_rating=5,  # 优秀评级
            is_rush_task=True,  # 紧急任务
            has_positive_feedback=True,  # 正面反馈
            completion_ahead_of_schedule=True,  # 提前完成
        )
        async_session.add(high_quality_task)
        await async_session.commit()
        await async_session.refresh(high_quality_task)

        # 计算包含奖励的工时
        total_hours_with_bonus = await work_hours_service.calculate_final_work_hours(
            high_quality_task.id
        )
        base_hours = 40 / 60  # 基础40分钟

        # 验证奖励逻辑
        expected_bonus_minutes = 15 + 30  # 紧急任务奖励15分钟 + 正面反馈奖励30分钟
        expected_total = base_hours + expected_bonus_minutes / 60
        assert abs(total_hours_with_bonus - expected_total) < 0.01

        # 测试延迟完成任务（惩罚）
        delayed_task = RepairTask(
            title="延迟任务",
            description="延迟完成的任务",
            category=TaskCategory.REPAIR,
            task_type=TaskType.OFFLINE,
            status=TaskStatus.COMPLETED,
            assignee_id=user.id,
            reporter_name="不满意报告人",
            reporter_contact="13800138006",
            location="延迟位置",
            problem_description="处理缓慢",
            created_at=datetime.now() - timedelta(hours=10),
            started_at=datetime.now() - timedelta(hours=8),  # 延迟开始
            completed_at=datetime.now() - timedelta(hours=1),
            expected_completion_time=datetime.now() - timedelta(hours=3),  # 已超期
            actual_work_hours=3.0,
            quality_rating=2,  # 差评
            has_negative_feedback=True,  # 负面反馈
            late_start=True,  # 延迟开始
            late_completion=True,  # 延迟完成
        )
        async_session.add(delayed_task)
        await async_session.commit()
        await async_session.refresh(delayed_task)

        # 计算包含惩罚的工时
        total_hours_with_penalty = await work_hours_service.calculate_final_work_hours(
            delayed_task.id
        )
        base_hours_offline = 100 / 60  # 基础100分钟

        # 验证惩罚逻辑
        expected_penalty_minutes = (
            30 + 30 + 60
        )  # 延迟开始30分钟 + 延迟完成30分钟 + 负面反馈60分钟
        expected_total_with_penalty = max(
            0, base_hours_offline - expected_penalty_minutes / 60
        )
        assert abs(total_hours_with_penalty - expected_total_with_penalty) < 0.01

    async def test_batch_recalculate_work_hours(self, async_session: AsyncSession):
        """测试批量重算工时逻辑"""
        # 创建多个用户和任务
        users = []
        for i in range(3):
            user = Member(
                username=f"batch_user_{i}",
                name=f"批量用户{i}",
                student_id=f"202400100{i+6}",
                group_id=1,
                class_name="计算机科学2024",
                email=f"batch{i}@example.com",
                password_hash=get_password_hash("UserPassword123!"),
                role=UserRole.MEMBER,
                is_active=True,
                is_verified=True,
            )
            async_session.add(user)
            users.append(user)

        await async_session.commit()
        for user in users:
            await async_session.refresh(user)

        # 创建多个需要重算的任务
        tasks_to_recalculate = []
        for user_idx, user in enumerate(users):
            for task_idx in range(2):
                task = RepairTask(
                    title=f"批量重算任务{user_idx}_{task_idx}",
                    description=f"需要重新计算工时的任务{user_idx}_{task_idx}",
                    category=TaskCategory.REPAIR,
                    task_type=(
                        TaskType.ONLINE if task_idx % 2 == 0 else TaskType.OFFLINE
                    ),
                    status=TaskStatus.COMPLETED,
                    assignee_id=user.id,
                    reporter_name=f"批量报告人{user_idx}_{task_idx}",
                    reporter_contact=f"1380013800{user_idx + 7}",
                    location=f"批量位置{user_idx}_{task_idx}",
                    problem_description=f"批量问题{user_idx}_{task_idx}",
                    created_at=datetime.now() - timedelta(days=task_idx + 1),
                    completed_at=datetime.now() - timedelta(hours=task_idx + 1),
                    expected_completion_time=datetime.now() + timedelta(hours=24),
                    actual_work_hours=(task_idx + 1) * 1.5,
                    # 设置一些初始的错误工时值
                    calculated_work_hours=(task_idx + 1) * 0.5,  # 故意设置错误值
                    needs_recalculation=True,
                )
                async_session.add(task)
                tasks_to_recalculate.append(task)

        await async_session.commit()

        work_hours_service = WorkHoursCalculationService(async_session)

        # 执行批量重算
        task_ids = [task.id for task in tasks_to_recalculate]
        recalculation_result = await work_hours_service.batch_recalculate_work_hours(
            task_ids=task_ids, recalculation_reason="测试批量重算功能"
        )

        # 验证重算结果
        assert recalculation_result["total_tasks"] == len(task_ids)
        assert recalculation_result["successful_recalculations"] == len(task_ids)
        assert recalculation_result["failed_recalculations"] == 0

        # 验证每个任务的工时都被正确重算
        for task in tasks_to_recalculate:
            await async_session.refresh(task)
            # 验证工时已更新且不再需要重算
            assert task.needs_recalculation is False
            assert task.calculated_work_hours != (
                task.actual_work_hours * 0.5
            )  # 不再是错误值

            # 验证工时计算符合规则
            if task.task_type == TaskType.ONLINE:
                assert task.calculated_work_hours >= 40 / 60  # 至少基础工时
            else:
                assert task.calculated_work_hours >= 100 / 60  # 至少基础工时


@pytest.mark.asyncio
class TestAttendanceServiceRealCoverage:
    """考勤服务真正功能测试 - 覆盖考勤管理核心逻辑"""

    async def test_create_attendance_record(self, async_session: AsyncSession):
        """测试创建考勤记录逻辑"""
        # 创建测试用户
        user = Member(
            username="attendance_user",
            name="考勤用户",
            student_id="2024001007",
            group_id=1,
            class_name="计算机科学2024",
            email="attendance@example.com",
            password_hash=get_password_hash("UserPassword123!"),
            role=UserRole.MEMBER,
            is_active=True,
            is_verified=True,
        )
        async_session.add(user)
        await async_session.commit()
        await async_session.refresh(user)

        attendance_service = AttendanceService(async_session)
        today = datetime.now().date()

        # 测试正常签到
        checkin_time = datetime.now().replace(hour=9, minute=0, second=0, microsecond=0)
        attendance_record = await attendance_service.check_in(
            member_id=user.id,
            check_in_time=checkin_time,
            location="办公室",
            device_info="测试设备",
        )

        assert attendance_record is not None
        assert attendance_record.member_id == user.id
        assert attendance_record.date == today
        assert attendance_record.status == AttendanceStatus.PRESENT
        assert attendance_record.check_in_time == checkin_time

        # 测试签退
        checkout_time = datetime.now().replace(
            hour=18, minute=0, second=0, microsecond=0
        )
        updated_record = await attendance_service.check_out(
            member_id=user.id, check_out_time=checkout_time, location="办公室"
        )

        assert updated_record.check_out_time == checkout_time
        # 验证工作时长计算
        expected_hours = (checkout_time - checkin_time).total_seconds() / 3600
        assert abs(updated_record.work_hours - expected_hours) < 0.01

        # 测试重复签到（应该失败）
        with pytest.raises(ValueError, match="今日已签到|重复签到"):
            await attendance_service.check_in(
                member_id=user.id, check_in_time=datetime.now(), location="办公室"
            )

    async def test_calculate_monthly_attendance_stats(
        self, async_session: AsyncSession
    ):
        """测试月度考勤统计计算逻辑"""
        # 创建测试用户
        user = Member(
            username="monthly_user",
            name="月度统计用户",
            student_id="2024001008",
            group_id=1,
            class_name="计算机科学2024",
            email="monthly@example.com",
            password_hash=get_password_hash("UserPassword123!"),
            role=UserRole.MEMBER,
            is_active=True,
            is_verified=True,
        )
        async_session.add(user)
        await async_session.commit()
        await async_session.refresh(user)

        # 创建一个月的考勤记录
        now = datetime.now()
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        attendance_records = []
        for day in range(1, 22):  # 21个工作日
            record_date = month_start.replace(day=day)

            # 模拟不同的考勤情况
            if day <= 18:  # 18天正常出勤
                status = AttendanceStatus.PRESENT
                check_in = record_date.replace(hour=9, minute=0)
                check_out = record_date.replace(hour=18, minute=0)
                work_hours = 8.0
            elif day == 19:  # 1天迟到
                status = AttendanceStatus.LATE
                check_in = record_date.replace(hour=9, minute=30)  # 迟到30分钟
                check_out = record_date.replace(hour=18, minute=0)
                work_hours = 7.5
            elif day == 20:  # 1天早退
                status = AttendanceStatus.EARLY_LEAVE
                check_in = record_date.replace(hour=9, minute=0)
                check_out = record_date.replace(hour=17, minute=0)  # 早退1小时
                work_hours = 7.0
            else:  # 1天请假
                status = AttendanceStatus.LEAVE
                check_in = None
                check_out = None
                work_hours = 0.0

            record = AttendanceRecord(
                member_id=user.id,
                date=record_date.date(),
                status=status,
                check_in_time=check_in,
                check_out_time=check_out,
                work_hours=work_hours,
                notes=f"第{day}天考勤",
            )
            async_session.add(record)
            attendance_records.append(record)

        await async_session.commit()

        attendance_service = AttendanceService(async_session)

        # 计算月度统计
        monthly_stats = await attendance_service.calculate_monthly_attendance_stats(
            member_id=user.id, year=now.year, month=now.month
        )

        # 验证统计结果
        assert monthly_stats is not None
        assert monthly_stats["member_id"] == user.id
        assert monthly_stats["total_work_days"] == 21
        assert monthly_stats["present_days"] == 18
        assert monthly_stats["late_days"] == 1
        assert monthly_stats["early_leave_days"] == 1
        assert monthly_stats["leave_days"] == 1
        assert monthly_stats["absent_days"] == 0

        # 验证出勤率计算
        expected_attendance_rate = (18 + 1 + 1) / 21 * 100  # 20/21 ≈ 95.24%
        assert abs(monthly_stats["attendance_rate"] - expected_attendance_rate) < 0.1

        # 验证总工作时长
        expected_total_hours = 18 * 8.0 + 7.5 + 7.0  # 158.5小时
        assert abs(monthly_stats["total_work_hours"] - expected_total_hours) < 0.1

        # 验证平均工作时长
        expected_avg_hours = expected_total_hours / 20  # 除以实际工作天数
        assert abs(monthly_stats["average_work_hours"] - expected_avg_hours) < 0.1

    async def test_detect_attendance_anomalies(self, async_session: AsyncSession):
        """测试考勤异常检测逻辑"""
        # 创建测试用户
        user = Member(
            username="anomaly_user",
            name="异常检测用户",
            student_id="2024001009",
            group_id=1,
            class_name="计算机科学2024",
            email="anomaly@example.com",
            password_hash=get_password_hash("UserPassword123!"),
            role=UserRole.MEMBER,
            is_active=True,
            is_verified=True,
        )
        async_session.add(user)
        await async_session.commit()
        await async_session.refresh(user)

        # 创建包含异常的考勤记录
        now = datetime.now()
        anomaly_records = [
            # 正常记录
            AttendanceRecord(
                member_id=user.id,
                date=(now - timedelta(days=5)).date(),
                status=AttendanceStatus.PRESENT,
                check_in_time=now - timedelta(days=5, hours=15),  # 9:00
                check_out_time=now - timedelta(days=5, hours=6),  # 18:00
                work_hours=8.0,
            ),
            # 异常：工作时间过长
            AttendanceRecord(
                member_id=user.id,
                date=(now - timedelta(days=4)).date(),
                status=AttendanceStatus.PRESENT,
                check_in_time=now - timedelta(days=4, hours=17),  # 7:00
                check_out_time=now - timedelta(days=4, hours=2),  # 22:00
                work_hours=15.0,  # 工作15小时
            ),
            # 异常：工作时间过短
            AttendanceRecord(
                member_id=user.id,
                date=(now - timedelta(days=3)).date(),
                status=AttendanceStatus.PRESENT,
                check_in_time=now - timedelta(days=3, hours=13),  # 11:00
                check_out_time=now - timedelta(days=3, hours=11),  # 13:00
                work_hours=2.0,  # 工作2小时
            ),
            # 异常：深夜签到
            AttendanceRecord(
                member_id=user.id,
                date=(now - timedelta(days=2)).date(),
                status=AttendanceStatus.PRESENT,
                check_in_time=now - timedelta(days=2, hours=1),  # 23:00
                check_out_time=now - timedelta(days=2, hours=0.5),  # 23:30
                work_hours=0.5,
            ),
            # 异常：签退时间早于签到时间
            AttendanceRecord(
                member_id=user.id,
                date=(now - timedelta(days=1)).date(),
                status=AttendanceStatus.PRESENT,
                check_in_time=now - timedelta(days=1, hours=6),  # 18:00
                check_out_time=now - timedelta(days=1, hours=15),  # 9:00 (第二天)
                work_hours=-9.0,  # 负数工时
            ),
        ]

        for record in anomaly_records:
            async_session.add(record)
        await async_session.commit()

        attendance_service = AttendanceService(async_session)

        # 执行异常检测
        anomalies = await attendance_service.detect_attendance_anomalies(
            member_id=user.id,
            start_date=(now - timedelta(days=7)).date(),
            end_date=now.date(),
        )

        # 验证检测到的异常
        assert len(anomalies) >= 4  # 至少检测到4个异常

        anomaly_types = [anomaly["type"] for anomaly in anomalies]

        # 验证不同类型的异常都被检测到
        assert "EXCESSIVE_WORK_HOURS" in anomaly_types  # 工作时间过长
        assert "INSUFFICIENT_WORK_HOURS" in anomaly_types  # 工作时间过短
        assert "UNUSUAL_TIME_PATTERN" in anomaly_types  # 异常时间模式
        assert "DATA_INCONSISTENCY" in anomaly_types  # 数据不一致

        # 验证异常详细信息
        excessive_work_anomaly = next(
            (a for a in anomalies if a["type"] == "EXCESSIVE_WORK_HOURS"), None
        )
        assert excessive_work_anomaly is not None
        assert excessive_work_anomaly["severity"] == "HIGH"
        assert "15.0" in str(excessive_work_anomaly["details"])  # 包含15小时的详情

        # 验证修复建议
        assert "recommendations" in excessive_work_anomaly
        assert len(excessive_work_anomaly["recommendations"]) > 0
