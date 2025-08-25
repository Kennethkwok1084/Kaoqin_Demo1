"""
任务分配和状态管理核心业务逻辑测试
补充任务生命周期管理的关键测试用例
"""

from datetime import datetime, timedelta

import pytest

from app.models.member import Member, UserRole
from app.models.task import RepairTask, TaskCategory, TaskPriority, TaskStatus, TaskType
from app.services.task_service import TaskService


@pytest.mark.asyncio
class TestTaskAssignmentWorkflow:
    """任务分配工作流测试"""

    async def test_task_creation_and_assignment(self, async_session):
        """测试任务创建和分配流程"""
        service = TaskService(async_session)

        # 创建测试成员
        admin = Member(
            username="admin_user",
            name="管理员",
            student_id="ADMIN001",
            class_name="管理",
            role=UserRole.ADMIN,
        )

        member = Member(
            username="worker_user",
            name="工作人员",
            student_id="WORKER001",
            class_name="技术部",
            role=UserRole.MEMBER,
        )

        async_session.add_all([admin, member])
        await async_session.flush()

        # 测试任务创建
        task_data = {
            "title": "网络故障修复",
            "description": "办公区域网络连接异常，需要检查交换机",
            "category": TaskCategory.NETWORK_REPAIR,
            "priority": TaskPriority.HIGH,
            "task_type": TaskType.OFFLINE,
            "location": "办公楼A座3层",
            "reporter_name": "张老师",
            "reporter_contact": "13800138000",
            "assigned_to": member.id,
        }

        task = await service.create_repair_task(**task_data)

        # 验证任务创建
        assert task.title == "网络故障修复"
        assert task.status == TaskStatus.PENDING  # 初始状态
        assert task.member_id == member.id
        assert task.category == TaskCategory.NETWORK_REPAIR
        assert task.priority == TaskPriority.HIGH
        assert task.task_type == TaskType.OFFLINE

        # 验证任务ID生成
        assert task.task_id is not None
        assert task.task_id.startswith("REPAIR_")

        return task, member, admin

    async def test_task_status_transitions(self, async_session):
        """测试任务状态转换流程"""
        # 创建初始任务
        task, member, admin = await self.test_task_creation_and_assignment(
            async_session
        )
        service = TaskService(async_session)

        # 1. PENDING -> IN_PROGRESS (开始处理)
        await service.update_task_status(
            task.id, TaskStatus.IN_PROGRESS, completion_note="开始处理任务"
        )

        await async_session.refresh(task)
        assert task.status == TaskStatus.IN_PROGRESS
        assert task.response_time is not None  # 响应时间应该被记录

        # 2. IN_PROGRESS -> COMPLETED (完成任务)
        completion_time = datetime.utcnow()
        await service.update_task_status(
            task.id, TaskStatus.COMPLETED, completion_note="任务已完成，网络恢复正常"
        )

        await async_session.refresh(task)
        assert task.status == TaskStatus.COMPLETED
        assert task.completion_time is not None

        # 3. 测试无效状态转换
        with pytest.raises(ValueError, match="Invalid status transition"):
            await service.update_task_status(
                task.id,
                TaskStatus.PENDING,  # 不能从COMPLETED回到PENDING
                completion_note="尝试无效转换",
            )

    async def test_task_assignment_permissions(self, async_session):
        """测试任务分配权限控制"""
        service = TaskService(async_session)

        # 创建不同角色的用户
        admin = Member(
            username="admin",
            name="管理员",
            student_id="A001",
            class_name="管理",
            role=UserRole.ADMIN,
        )
        leader = Member(
            username="leader",
            name="组长",
            student_id="L001",
            class_name="技术",
            role=UserRole.GROUP_LEADER,
        )
        member1 = Member(
            username="member1",
            name="成员1",
            student_id="M001",
            class_name="技术",
            role=UserRole.MEMBER,
        )
        member2 = Member(
            username="member2",
            name="成员2",
            student_id="M002",
            class_name="技术",
            role=UserRole.MEMBER,
        )
        guest = Member(
            username="guest",
            name="访客",
            student_id="G001",
            class_name="访客",
            role=UserRole.GUEST,
        )

        async_session.add_all([admin, leader, member1, member2, guest])
        await async_session.flush()

        # 创建未分配的任务
        task = RepairTask(
            task_id="ASSIGN_TEST_001",
            title="权限测试任务",
            task_type=TaskType.ONLINE,
            status=TaskStatus.PENDING,
            report_time=datetime.utcnow(),
        )
        async_session.add(task)
        await async_session.flush()

        # 测试管理员分配权限
        await service.assign_task(task.id, member1.id, assigned_by=admin.id)
        await async_session.refresh(task)
        assert task.member_id == member1.id

        # 测试组长分配权限
        await service.assign_task(task.id, member2.id, assigned_by=leader.id)
        await async_session.refresh(task)
        assert task.member_id == member2.id

        # 测试普通成员不能分配任务（应该抛出权限错误）
        with pytest.raises(PermissionError, match="Insufficient permissions"):
            await service.assign_task(task.id, member1.id, assigned_by=member2.id)

        # 测试访客不能分配任务
        with pytest.raises(PermissionError, match="Insufficient permissions"):
            await service.assign_task(task.id, member1.id, assigned_by=guest.id)

    async def test_task_priority_handling(self, async_session):
        """测试任务优先级处理"""
        service = TaskService(async_session)

        # 创建测试成员
        member = Member(
            username="priority_test_user",
            name="优先级测试用户",
            student_id="PRI001",
            class_name="测试",
            role=UserRole.MEMBER,
        )
        async_session.add(member)
        await async_session.flush()

        # 创建不同优先级的任务
        tasks = []
        priorities = [
            TaskPriority.LOW,
            TaskPriority.MEDIUM,
            TaskPriority.HIGH,
            TaskPriority.URGENT,
        ]

        for i, priority in enumerate(priorities):
            task = RepairTask(
                task_id=f"PRI_TEST_{i:03d}",
                title=f"{priority.value}优先级任务",
                task_type=TaskType.ONLINE,
                status=TaskStatus.PENDING,
                priority=priority,
                member_id=member.id,
                report_time=datetime.utcnow()
                - timedelta(minutes=i * 10),  # 不同报告时间
            )
            tasks.append(task)

        async_session.add_all(tasks)
        await async_session.commit()

        # 测试按优先级排序
        pending_tasks = await service.get_pending_tasks_by_priority()

        # 验证排序：URGENT > HIGH > MEDIUM > LOW
        priority_values = [task.priority for task in pending_tasks]
        expected_order = [
            TaskPriority.URGENT,
            TaskPriority.HIGH,
            TaskPriority.MEDIUM,
            TaskPriority.LOW,
        ]

        for expected in expected_order:
            assert expected in priority_values

        # 验证紧急任务在最前面
        assert pending_tasks[0].priority == TaskPriority.URGENT

    async def test_task_deadline_management(self, async_session):
        """测试任务截止时间管理"""
        service = TaskService(async_session)

        # 创建测试成员
        member = Member(
            username="deadline_test_user",
            name="截止时间测试用户",
            student_id="DL001",
            class_name="测试",
            role=UserRole.MEMBER,
        )
        async_session.add(member)
        await async_session.flush()

        # 创建带截止时间的任务
        future_deadline = datetime.utcnow() + timedelta(hours=24)
        past_deadline = datetime.utcnow() - timedelta(hours=1)

        # 正常任务
        normal_task = RepairTask(
            task_id="DL_NORMAL_001",
            title="正常截止任务",
            task_type=TaskType.ONLINE,
            status=TaskStatus.PENDING,
            member_id=member.id,
            due_date=future_deadline,
            report_time=datetime.utcnow(),
        )

        # 逾期任务
        overdue_task = RepairTask(
            task_id="DL_OVERDUE_001",
            title="逾期任务",
            task_type=TaskType.OFFLINE,
            status=TaskStatus.IN_PROGRESS,
            member_id=member.id,
            due_date=past_deadline,
            report_time=datetime.utcnow() - timedelta(hours=2),
        )

        async_session.add_all([normal_task, overdue_task])
        await async_session.commit()

        # 测试逾期任务检测
        overdue_tasks = await service.get_overdue_tasks()

        overdue_ids = [task.task_id for task in overdue_tasks]
        assert "DL_OVERDUE_001" in overdue_ids
        assert "DL_NORMAL_001" not in overdue_ids

        # 测试截止时间警告
        warning_tasks = await service.get_tasks_approaching_deadline(hours=48)

        warning_ids = [task.task_id for task in warning_tasks]
        assert "DL_NORMAL_001" in warning_ids  # 24小时内到期

    async def test_bulk_task_operations(self, async_session):
        """测试批量任务操作"""
        service = TaskService(async_session)

        # 创建测试成员
        members = []
        for i in range(3):
            member = Member(
                username=f"bulk_user_{i}",
                name=f"批量用户{i}",
                student_id=f"BULK{i:03d}",
                class_name="批量测试",
                role=UserRole.MEMBER,
            )
            members.append(member)

        async_session.add_all(members)
        await async_session.flush()

        # 创建批量任务
        tasks = []
        for i in range(10):
            task = RepairTask(
                task_id=f"BULK_TASK_{i:03d}",
                title=f"批量任务{i}",
                task_type=TaskType.ONLINE,
                status=TaskStatus.PENDING,
                member_id=members[i % 3].id,  # 轮流分配
                report_time=datetime.utcnow() - timedelta(minutes=i),
            )
            tasks.append(task)

        async_session.add_all(tasks)
        await async_session.commit()

        # 测试批量状态更新
        task_ids = [task.id for task in tasks[:5]]  # 前5个任务
        await service.bulk_update_task_status(task_ids, TaskStatus.IN_PROGRESS)

        # 验证批量更新结果
        for task in tasks[:5]:
            await async_session.refresh(task)
            assert task.status == TaskStatus.IN_PROGRESS

        for task in tasks[5:]:
            await async_session.refresh(task)
            assert task.status == TaskStatus.PENDING  # 未被更新

        # 测试批量分配
        new_assignee = members[0].id
        await service.bulk_assign_tasks(task_ids[2:], new_assignee)

        # 验证批量分配结果
        for task in tasks[2:5]:
            await async_session.refresh(task)
            assert task.member_id == new_assignee

    async def test_task_escalation_workflow(self, async_session):
        """测试任务升级流程"""
        service = TaskService(async_session)

        # 创建测试用户
        admin = Member(
            username="admin",
            name="管理员",
            student_id="A001",
            class_name="管理",
            role=UserRole.ADMIN,
        )
        leader = Member(
            username="leader",
            name="组长",
            student_id="L001",
            class_name="技术",
            role=UserRole.GROUP_LEADER,
        )
        member = Member(
            username="member",
            name="成员",
            student_id="M001",
            class_name="技术",
            role=UserRole.MEMBER,
        )

        async_session.add_all([admin, leader, member])
        await async_session.flush()

        # 创建长时间未处理的任务
        old_task = RepairTask(
            task_id="ESCALATE_001",
            title="需要升级的任务",
            task_type=TaskType.OFFLINE,
            priority=TaskPriority.HIGH,
            status=TaskStatus.PENDING,
            member_id=member.id,
            report_time=datetime.utcnow() - timedelta(hours=48),  # 48小时前
        )
        async_session.add(old_task)
        await async_session.commit()

        # 测试任务升级
        await service.escalate_overdue_tasks()

        await async_session.refresh(old_task)

        # 验证升级结果
        assert old_task.priority == TaskPriority.HIGH  # 优先级提升

        # 检查升级记录
        escalation_logs = await service.get_task_escalation_history(old_task.id)
        assert len(escalation_logs) > 0
        assert "escalated" in escalation_logs[0]["action"].lower()

    async def test_task_cancellation_workflow(self, async_session):
        """测试任务取消流程"""
        service = TaskService(async_session)

        # 创建测试用户和任务
        admin = Member(
            username="cancel_admin",
            name="管理员",
            student_id="CA001",
            class_name="管理",
            role=UserRole.ADMIN,
        )
        member = Member(
            username="cancel_member",
            name="成员",
            student_id="CM001",
            class_name="技术",
            role=UserRole.MEMBER,
        )

        async_session.add_all([admin, member])
        await async_session.flush()

        # 创建可取消的任务
        task = RepairTask(
            task_id="CANCEL_001",
            title="需要取消的任务",
            task_type=TaskType.ONLINE,
            status=TaskStatus.PENDING,
            member_id=member.id,
            report_time=datetime.utcnow(),
        )
        async_session.add(task)
        await async_session.flush()

        # 测试任务取消
        cancellation_reason = "设备已自行恢复，无需处理"
        await service.cancel_task(
            task.id, cancelled_by=admin.id, reason=cancellation_reason
        )

        await async_session.refresh(task)

        # 验证取消结果
        assert task.status == TaskStatus.CANCELLED
        assert task.completion_time is not None  # 取消时间被记录

        # 验证取消记录
        cancellation_log = await service.get_task_cancellation_info(task.id)
        assert cancellation_log is not None
        assert cancellation_log["reason"] == cancellation_reason
        assert cancellation_log["cancelled_by"] == admin.id

        # 测试已完成任务不能取消
        completed_task = RepairTask(
            task_id="COMPLETED_001",
            title="已完成任务",
            task_type=TaskType.ONLINE,
            status=TaskStatus.COMPLETED,
            member_id=member.id,
            report_time=datetime.utcnow(),
            completion_time=datetime.utcnow(),
        )
        async_session.add(completed_task)
        await async_session.flush()

        with pytest.raises(ValueError, match="Cannot cancel completed task"):
            await service.cancel_task(
                completed_task.id, cancelled_by=admin.id, reason="尝试取消已完成任务"
            )
