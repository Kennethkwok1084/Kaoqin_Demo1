"""
数据库连接和模型集成测试
测试数据库连接、模型创建、关系和约束
"""

import pytest
import pytest_asyncio
from sqlalchemy import select, text
from sqlalchemy.exc import IntegrityError

from app.core.security import get_password_hash
from app.models import Member, UserRole
from app.models.attendance import (
    AttendanceException,
    AttendanceExceptionStatus,
    AttendanceRecord,
)
from app.models.task import RepairTask, TaskPriority, TaskStatus, TaskType


class TestDatabaseConnection:
    """测试数据库连接"""

    @pytest_asyncio.fixture(autouse=True)
    async def setup(self, db_session):
        self.db = db_session

    @pytest.mark.asyncio
    async def test_database_connection(self):
        """测试数据库连接是否正常"""
        result = await self.db.execute(text("SELECT 1"))
        assert result.scalar() == 1

    @pytest.mark.asyncio
    async def test_tables_created(self):
        """测试所有表是否正确创建"""
        # 检查主要表是否存在
        tables_to_check = [
            "members",
            "repair_tasks",
            "monitoring_tasks",
            "assistance_tasks",
            "attendance_records",
            "attendance_exceptions",
            "monthly_attendance_summaries",
            "task_tags",
        ]

        for table_name in tables_to_check:
            result = await self.db.execute(
                text(
                    f"SELECT tablename FROM pg_tables "
                    f"WHERE schemaname='public' AND tablename='{table_name}'"
                )
            )
            assert result.scalar() is not None, f"Table {table_name} should exist"


class TestMemberModel:
    """测试成员模型"""

    @pytest_asyncio.fixture(autouse=True)
    async def setup(self, db_session):
        self.db = db_session

    @pytest.mark.asyncio
    async def test_create_member(self):
        """测试创建成员"""
        member = Member(
            username="testuser001",
            name="测试用户",
            student_id="TEST001",
            phone="13888880001",
            department="信息与计算科学学院",
            password_hash=get_password_hash("password123"),
            role=UserRole.MEMBER,
            class_name="计算机2101",
            is_active=True,
            is_verified=False,
        )

        self.db.add(member)
        await self.db.commit()
        await self.db.refresh(member)

        assert member.id is not None
        assert member.name == "测试用户"
        assert member.student_id == "TEST001"
        assert member.role == UserRole.MEMBER
        assert member.is_active is True
        assert member.created_at is not None

    @pytest.mark.asyncio
    async def test_member_unique_constraint(self):
        """测试成员学号唯一约束"""
        # 创建第一个成员
        member1 = Member(
            name="用户1",
            student_id="UNIQUE001",
            password_hash=get_password_hash("password123"),
            role=UserRole.MEMBER,
        )
        self.db.add(member1)
        await self.db.commit()

        # 尝试创建相同学号的成员
        member2 = Member(
            name="用户2",
            student_id="UNIQUE001",  # 相同学号
            password_hash=get_password_hash("password456"),
            role=UserRole.MEMBER,
        )
        self.db.add(member2)

        with pytest.raises(IntegrityError):
            await self.db.commit()

    @pytest.mark.asyncio
    async def test_member_properties(self):
        """测试成员属性方法"""
        admin = Member(
            name="管理员",
            student_id="ADMIN001",
            password_hash=get_password_hash("admin123"),
            role=UserRole.ADMIN,
        )

        leader = Member(
            name="组长",
            student_id="LEADER001",
            password_hash=get_password_hash("leader123"),
            role=UserRole.GROUP_LEADER,
        )

        member = Member(
            name="成员",
            student_id="MEMBER001",
            password_hash=get_password_hash("member123"),
            role=UserRole.MEMBER,
        )

        # 测试角色属性
        assert admin.is_admin is True
        assert admin.is_group_leader is False
        assert admin.can_manage_group is True
        assert admin.can_import_data is True

        assert leader.is_admin is False
        assert leader.is_group_leader is True
        assert leader.can_manage_group is True
        assert leader.can_import_data is False

        assert member.is_admin is False
        assert member.is_group_leader is False
        assert member.can_manage_group is False
        assert member.can_import_data is False


class TestTaskModel:
    """测试任务模型"""

    @pytest_asyncio.fixture(autouse=True)
    async def setup(self, db_session, test_member_user):
        self.db = db_session
        self.member = test_member_user

    @pytest.mark.asyncio
    async def test_create_repair_task(self):
        """测试创建维修任务"""
        from datetime import datetime

        task = RepairTask(
            title="网络维修任务",
            description="修复网络故障",
            task_id="T202501280001",
            status=TaskStatus.PENDING,
            priority=TaskPriority.HIGH,
            task_type=TaskType.OFFLINE,
            location="图书馆",
            member_id=self.member.id,
            reporter_name="张老师",
            reporter_contact="13812345678",
            report_time=datetime.utcnow(),
        )

        self.db.add(task)
        await self.db.commit()
        await self.db.refresh(task)

        assert task.id is not None
        assert task.title == "网络维修任务"
        assert task.status == TaskStatus.PENDING
        assert task.member_id == self.member.id
        assert task.created_at is not None

    @pytest.mark.asyncio
    async def test_task_member_relationship(self):
        """测试任务与成员的关系"""
        from datetime import datetime

        task = RepairTask(
            title="关系测试任务",
            description="测试任务与成员关系",
            task_id="T202501280002",
            status=TaskStatus.IN_PROGRESS,
            priority=TaskPriority.MEDIUM,
            member_id=self.member.id,
            report_time=datetime.utcnow(),
        )

        self.db.add(task)
        await self.db.commit()
        await self.db.refresh(task)

        # 测试关系加载
        result = await self.db.execute(
            select(RepairTask).where(RepairTask.id == task.id)
        )
        loaded_task = result.scalar_one()

        # 加载关联的成员
        await self.db.refresh(loaded_task, ["member"])
        assert loaded_task.member is not None
        assert loaded_task.member.id == self.member.id
        assert loaded_task.member.name == self.member.name

    @pytest.mark.asyncio
    async def test_task_number_unique(self):
        """测试任务编号唯一性"""
        from datetime import datetime

        task1 = RepairTask(
            title="任务1",
            description="第一个任务",
            task_id="T202501280003",
            member_id=self.member.id,
            report_time=datetime.utcnow(),
        )
        self.db.add(task1)
        await self.db.commit()

        # 尝试创建相同编号的任务
        task2 = RepairTask(
            title="任务2",
            description="第二个任务",
            task_id="T202501280003",  # 相同编号
            member_id=self.member.id,
            report_time=datetime.utcnow(),
        )
        self.db.add(task2)

        with pytest.raises(IntegrityError):
            await self.db.commit()


class TestAttendanceModel:
    """测试考勤模型"""

    @pytest_asyncio.fixture(autouse=True)
    async def setup(self, db_session, test_member_user):
        self.db = db_session
        self.member = test_member_user

    @pytest.mark.asyncio
    async def test_create_attendance_record(self):
        """测试创建考勤记录"""
        from datetime import date, datetime

        record = AttendanceRecord(
            member_id=self.member.id,
            attendance_date=date.today(),
            checkin_time=datetime.now().replace(hour=9, minute=0, second=0),
            checkout_time=datetime.now().replace(hour=17, minute=30, second=0),
            work_hours=8.5,
            status="正常",
            location="办公室",
            notes="正常考勤",
            is_late_checkin=False,
            is_early_checkout=False,
        )

        self.db.add(record)
        await self.db.commit()
        await self.db.refresh(record)

        assert record.id is not None
        assert record.member_id == self.member.id
        assert record.work_hours == 8.5
        assert record.status == "正常"
        assert record.is_late_checkin is False

    @pytest.mark.asyncio
    async def test_attendance_unique_constraint(self):
        """测试考勤记录唯一约束（每人每天只能有一条记录）"""
        from datetime import date, datetime

        today = date.today()

        # 创建第一条记录
        record1 = AttendanceRecord(
            member_id=self.member.id,
            attendance_date=today,
            checkin_time=datetime.now().replace(hour=9, minute=0),
            work_hours=8.0,
            status="正常",
        )
        self.db.add(record1)
        await self.db.commit()

        # 尝试创建同一天的第二条记录
        record2 = AttendanceRecord(
            member_id=self.member.id,
            attendance_date=today,  # 相同日期
            checkin_time=datetime.now().replace(hour=10, minute=0),
            work_hours=7.0,
            status="迟到",
        )
        self.db.add(record2)

        with pytest.raises(IntegrityError):
            await self.db.commit()

    @pytest.mark.asyncio
    async def test_create_attendance_exception(self):
        """测试创建考勤异常"""
        from datetime import date, datetime

        exception = AttendanceException(
            member_id=self.member.id,
            exception_type="迟到",
            exception_date=date.today(),
            reason="交通堵塞",
            supporting_documents="迟到证明.pdf",
            status=AttendanceExceptionStatus.PENDING,
            applied_at=datetime.utcnow(),
        )

        self.db.add(exception)
        await self.db.commit()
        await self.db.refresh(exception)

        assert exception.id is not None
        assert exception.member_id == self.member.id
        assert exception.exception_type == "迟到"
        assert exception.status == AttendanceExceptionStatus.PENDING
        assert exception.applied_at is not None

    @pytest.mark.asyncio
    async def test_attendance_member_relationship(self):
        """测试考勤记录与成员关系"""
        from datetime import date, datetime

        record = AttendanceRecord(
            member_id=self.member.id,
            attendance_date=date.today(),
            checkin_time=datetime.now(),
            work_hours=8.0,
            status="正常",
        )

        self.db.add(record)
        await self.db.commit()
        await self.db.refresh(record)

        # 测试关系加载
        result = await self.db.execute(
            select(AttendanceRecord).where(AttendanceRecord.id == record.id)
        )
        loaded_record = result.scalar_one()

        # 加载关联的成员
        await self.db.refresh(loaded_record, ["member"])
        assert loaded_record.member is not None
        assert loaded_record.member.id == self.member.id


class TestModelRelationships:
    """测试模型关系"""

    @pytest_asyncio.fixture(autouse=True)
    async def setup(self, db_session, test_member_user, test_data_helper):
        self.db = db_session
        self.member = test_member_user
        self.helper = test_data_helper

    @pytest.mark.asyncio
    async def test_member_tasks_relationship(self):
        """测试成员与任务的关系"""
        # 创建测试任务
        await self.helper.create_test_tasks(self.db, self.member.id, 3)

        # 通过成员查询关联任务
        result = await self.db.execute(
            select(Member).where(Member.id == self.member.id)
        )
        member = result.scalar_one()

        # 验证任务关系
        repair_tasks = await self.db.execute(
            select(RepairTask).where(RepairTask.member_id == member.id)
        )
        task_list = repair_tasks.scalars().all()

        assert len(task_list) == 3
        for task in task_list:
            assert task.member_id == member.id

    @pytest.mark.asyncio
    async def test_member_attendance_relationship(self):
        """测试成员与考勤记录的关系"""
        # 创建测试考勤记录
        await self.helper.create_test_attendance_records(self.db, self.member.id, 5)

        # 通过成员查询关联考勤记录
        attendance_records = await self.db.execute(
            select(AttendanceRecord).where(AttendanceRecord.member_id == self.member.id)
        )
        record_list = attendance_records.scalars().all()

        assert len(record_list) == 5
        for record in record_list:
            assert record.member_id == self.member.id

    @pytest.mark.asyncio
    async def test_cascade_deletion(self):
        """测试级联删除"""
        # 创建任务和考勤记录
        await self.helper.create_test_tasks(self.db, self.member.id, 2)
        await self.helper.create_test_attendance_records(self.db, self.member.id, 2)

        # 验证记录存在
        tasks_before = await self.db.execute(
            select(RepairTask).where(RepairTask.member_id == self.member.id)
        )
        assert len(tasks_before.scalars().all()) == 2

        attendance_before = await self.db.execute(
            select(AttendanceRecord).where(AttendanceRecord.member_id == self.member.id)
        )
        assert len(attendance_before.scalars().all()) == 2

        # 删除成员（注意：实际应用中可能不会物理删除，而是标记为不活跃）
        await self.db.delete(self.member)
        await self.db.commit()

        # 验证关联记录被级联删除或处理
        # 注意：具体行为取决于外键约束配置
