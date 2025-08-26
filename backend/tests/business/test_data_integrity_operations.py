"""
数据完整性和批量操作核心业务逻辑测试
验证高风险操作的数据一致性和约束检查
"""

from datetime import datetime, timedelta

import pytest
from sqlalchemy import and_, func, select, text
from sqlalchemy.exc import IntegrityError

from app.core.database_compatibility import SQLiteEnumValidator
from app.models.member import Member, UserRole
from app.models.task import RepairTask, TaskStatus, TaskType
from app.services.import_service import DataImportService


@pytest.mark.asyncio
class TestDataIntegrityConstraints:
    """数据完整性约束测试"""

    async def test_foreign_key_constraints(self, async_session):
        """测试外键约束完整性"""
        # 测试任务-成员外键约束
        invalid_task = RepairTask(
            task_id="FK_TEST_001",
            title="无效外键任务",
            task_type=TaskType.ONLINE,
            status=TaskStatus.PENDING,
            member_id=99999,  # 不存在的成员ID
            report_time=datetime.utcnow(),
        )

        async_session.add(invalid_task)

        # 应该抛出外键约束错误
        with pytest.raises(IntegrityError, match="foreign key constraint"):
            await async_session.commit()

        await async_session.rollback()

        # 测试有效外键
        valid_member = Member(
            username="valid_member",
            name="有效成员",
            student_id="VM001",
            class_name="测试班级",
            role=UserRole.MEMBER,
        )
        async_session.add(valid_member)
        await async_session.flush()

        valid_task = RepairTask(
            task_id="FK_TEST_002",
            title="有效外键任务",
            task_type=TaskType.ONLINE,
            status=TaskStatus.PENDING,
            member_id=valid_member.id,
            report_time=datetime.utcnow(),
        )

        async_session.add(valid_task)
        await async_session.commit()  # 应该成功

    async def test_unique_constraints(self, async_session):
        """测试唯一约束"""
        # 创建测试成员
        member = Member(
            username="unique_test_member",
            name="唯一约束测试成员",
            student_id="UT001",
            class_name="测试班级",
            role=UserRole.MEMBER,
        )
        async_session.add(member)
        await async_session.flush()

        # 创建第一个任务
        task1 = RepairTask(
            task_id="UNIQUE_TASK_001",
            title="第一个任务",
            task_type=TaskType.ONLINE,
            status=TaskStatus.PENDING,
            member_id=member.id,
            report_time=datetime.utcnow(),
        )
        async_session.add(task1)
        await async_session.commit()

        # 尝试创建相同task_id的任务
        task2 = RepairTask(
            task_id="UNIQUE_TASK_001",  # 相同的task_id
            title="第二个任务",
            task_type=TaskType.OFFLINE,
            status=TaskStatus.PENDING,
            member_id=member.id,
            report_time=datetime.utcnow(),
        )
        async_session.add(task2)

        # 应该抛出唯一约束错误
        with pytest.raises(IntegrityError, match="unique constraint|UNIQUE constraint"):
            await async_session.commit()

        await async_session.rollback()

    async def test_not_null_constraints(self, async_session):
        """测试非空约束"""
        # 测试缺少必需字段
        with pytest.raises((IntegrityError, TypeError, ValueError)):
            invalid_task = RepairTask(
                # task_id=None,  # 必需字段缺失
                title="缺少task_id的任务",
                task_type=TaskType.ONLINE,
                status=TaskStatus.PENDING,
                report_time=datetime.utcnow(),
            )
            async_session.add(invalid_task)
            await async_session.commit()

        await async_session.rollback()

        # 测试所有必需字段都提供
        member = Member(
            username="notnull_test_member",
            name="非空测试成员",
            student_id="NT001",
            class_name="测试班级",
            role=UserRole.MEMBER,
        )
        async_session.add(member)
        await async_session.flush()

        valid_task = RepairTask(
            task_id="VALID_TASK_001",
            title="有效任务",
            task_type=TaskType.ONLINE,
            status=TaskStatus.PENDING,
            member_id=member.id,
            report_time=datetime.utcnow(),
        )
        async_session.add(valid_task)
        await async_session.commit()  # 应该成功

    async def test_enum_constraints_postgresql(self, async_session):
        """测试PostgreSQL ENUM约束"""
        from app.core.database_compatibility import should_use_postgresql_tests

        if not should_use_postgresql_tests():
            pytest.skip("PostgreSQL-only test")

        member = Member(
            username="enum_test_member",
            name="枚举测试成员",
            student_id="ET001",
            class_name="测试班级",
            role=UserRole.MEMBER,
        )
        async_session.add(member)
        await async_session.flush()

        # 测试无效ENUM值（PostgreSQL会抛出错误）
        with pytest.raises(Exception):  # PostgreSQL ENUM约束错误
            await async_session.execute(
                text(
                    """
                    INSERT INTO repair_tasks (task_id, title, task_type, status, member_id, report_time)
                    VALUES ('ENUM_TEST_001', '无效枚举任务', 'INVALID_TYPE', 'PENDING', :member_id, :report_time)
                """
                ),
                {"member_id": member.id, "report_time": datetime.utcnow()},
            )
            await async_session.commit()

        await async_session.rollback()

    async def test_sqlite_enum_validation(self, async_session):
        """测试SQLite ENUM验证"""
        from app.core.database_compatibility import should_use_postgresql_tests

        if should_use_postgresql_tests():
            pytest.skip("SQLite-only test")

        # 使用SQLite ENUM验证器
        validator = SQLiteEnumValidator()

        # 测试有效值
        assert validator.validate_task_status("PENDING") is True
        assert validator.validate_task_type("ONLINE") is True
        assert validator.validate_user_role("MEMBER") is True

        # 测试无效值
        assert validator.validate_task_status("INVALID_STATUS") is False
        assert validator.validate_task_type("INVALID_TYPE") is False
        assert validator.validate_user_role("INVALID_ROLE") is False


@pytest.mark.asyncio
class TestBulkOperationIntegrity:
    """批量操作完整性测试"""

    async def test_bulk_import_data_validation(self, async_session):
        """测试批量导入数据验证"""
        import_service = DataImportService(async_session)

        # 准备测试数据 - 包含有效和无效记录
        import_data = [
            {
                # 有效记录1
                "task_id": "BULK_VALID_001",
                "title": "有效任务1",
                "task_type": "ONLINE",
                "status": "PENDING",
                "reporter_name": "测试用户1",
                "reporter_contact": "13800138001",
                "report_time": datetime.utcnow().isoformat(),
            },
            {
                # 有效记录2
                "task_id": "BULK_VALID_002",
                "title": "有效任务2",
                "task_type": "OFFLINE",
                "status": "PENDING",
                "reporter_name": "测试用户2",
                "reporter_contact": "13800138002",
                "report_time": datetime.utcnow().isoformat(),
            },
            {
                # 无效记录 - 缺少必需字段
                "task_id": "BULK_INVALID_001",
                # "title": 缺失
                "task_type": "ONLINE",
                "status": "PENDING",
            },
            {
                # 无效记录 - ENUM值无效
                "task_id": "BULK_INVALID_002",
                "title": "无效任务2",
                "task_type": "INVALID_TYPE",  # 无效类型
                "status": "INVALID_STATUS",  # 无效状态
            },
        ]

        # 执行批量导入
        result = await import_service.bulk_import_repair_tasks(import_data)

        # 验证导入结果
        assert result["total"] == 4
        assert result["success"] >= 2  # 至少2条有效记录成功
        assert result["failed"] >= 2  # 至少2条无效记录失败
        assert len(result["errors"]) >= 2  # 错误信息

        # 验证成功导入的记录
        successful_tasks = await async_session.execute(
            select(RepairTask).where(
                RepairTask.task_id.in_(["BULK_VALID_001", "BULK_VALID_002"])
            )
        )
        tasks = successful_tasks.scalars().all()
        assert len(tasks) >= 2

        # 验证失败记录未被导入
        failed_tasks = await async_session.execute(
            select(RepairTask).where(
                RepairTask.task_id.in_(["BULK_INVALID_001", "BULK_INVALID_002"])
            )
        )
        failed_results = failed_tasks.scalars().all()
        assert len(failed_results) == 0  # 无效记录不应该被导入

    async def test_bulk_update_transaction_integrity(self, async_session):
        """测试批量更新事务完整性"""
        # 创建测试成员
        member = Member(
            username="bulk_update_member",
            name="批量更新测试成员",
            student_id="BU001",
            class_name="测试班级",
            role=UserRole.MEMBER,
        )
        async_session.add(member)
        await async_session.flush()

        # 创建多个测试任务
        tasks = []
        for i in range(5):
            task = RepairTask(
                task_id=f"BULK_UPDATE_{i:03d}",
                title=f"批量更新任务{i}",
                task_type=TaskType.ONLINE,
                status=TaskStatus.PENDING,
                member_id=member.id,
                report_time=datetime.utcnow(),
            )
            tasks.append(task)

        async_session.add_all(tasks)
        await async_session.commit()

        # 执行批量状态更新
        task_ids = [task.id for task in tasks]

        try:
            # 开始事务
            for task_id in task_ids[:3]:  # 前3个成功
                await async_session.execute(
                    text(
                        "UPDATE repair_tasks SET status = 'IN_PROGRESS' WHERE id = :task_id"
                    ),
                    {"task_id": task_id},
                )

            # 第4个制造失败（假设约束检查）
            # 这里我们模拟一个会失败的操作
            if len(task_ids) > 3:
                # 尝试设置无效状态（如果是PostgreSQL会失败）
                try:
                    await async_session.execute(
                        text(
                            "UPDATE repair_tasks SET status = 'INVALID_STATUS' WHERE id = :task_id"
                        ),
                        {"task_id": task_ids[3]},
                    )
                except Exception:
                    # 预期的失败，回滚事务
                    await async_session.rollback()

                    # 验证事务完整性 - 所有更新都应该被回滚
                    for task in tasks:
                        await async_session.refresh(task)
                        assert (
                            task.status == TaskStatus.PENDING
                        )  # 所有任务状态应该保持原始状态

                    return  # 测试完成

            await async_session.commit()

        except Exception as e:
            await async_session.rollback()
            # 验证回滚后的状态
            for task in tasks:
                await async_session.refresh(task)
                assert task.status == TaskStatus.PENDING

    async def test_concurrent_operation_integrity(self, async_session):
        """测试并发操作完整性"""
        import asyncio

        # 创建测试成员
        member = Member(
            username="concurrent_member",
            name="并发测试成员",
            student_id="CO001",
            class_name="测试班级",
            role=UserRole.MEMBER,
        )
        async_session.add(member)
        await async_session.flush()

        # 创建测试任务
        task = RepairTask(
            task_id="CONCURRENT_001",
            title="并发测试任务",
            task_type=TaskType.ONLINE,
            status=TaskStatus.PENDING,
            member_id=member.id,
            report_time=datetime.utcnow(),
        )
        async_session.add(task)
        await async_session.commit()

        # 模拟并发更新操作
        async def update_task_status(task_id: int, new_status: TaskStatus):
            """模拟并发状态更新"""
            try:
                await async_session.execute(
                    text(
                        "UPDATE repair_tasks SET status = :status WHERE id = :task_id"
                    ),
                    {"status": new_status.value, "task_id": task_id},
                )
                await async_session.commit()
                return True
            except Exception as e:
                await async_session.rollback()
                return False

        # 并发执行多个更新
        results = await asyncio.gather(
            update_task_status(task.id, TaskStatus.IN_PROGRESS),
            update_task_status(task.id, TaskStatus.COMPLETED),
            update_task_status(task.id, TaskStatus.CANCELLED),
            return_exceptions=True,
        )

        # 验证最终状态一致性
        await async_session.refresh(task)
        final_status = task.status

        # 最终状态应该是其中一个有效状态
        valid_statuses = [
            TaskStatus.IN_PROGRESS,
            TaskStatus.COMPLETED,
            TaskStatus.CANCELLED,
        ]
        assert final_status in valid_statuses

        # 至少一个操作应该成功
        success_count = sum(1 for result in results if result is True)
        assert success_count >= 1

    async def test_data_consistency_after_rollback(self, async_session):
        """测试回滚后数据一致性"""
        # 记录初始状态
        initial_task_count = await async_session.scalar(
            select(func.count(RepairTask.id))
        )
        initial_member_count = await async_session.scalar(select(func.count(Member.id)))

        try:
            # 开始复杂操作
            member = Member(
                username="rollback_test_member",
                name="回滚测试成员",
                student_id="RT001",
                class_name="测试班级",
                role=UserRole.MEMBER,
            )
            async_session.add(member)
            await async_session.flush()

            # 添加多个任务
            tasks = []
            for i in range(3):
                task = RepairTask(
                    task_id=f"ROLLBACK_TASK_{i:03d}",
                    title=f"回滚测试任务{i}",
                    task_type=TaskType.ONLINE,
                    status=TaskStatus.PENDING,
                    member_id=member.id,
                    report_time=datetime.utcnow(),
                )
                tasks.append(task)

            async_session.add_all(tasks)
            await async_session.flush()

            # 制造一个会导致回滚的错误
            # 尝试插入重复的task_id
            duplicate_task = RepairTask(
                task_id="ROLLBACK_TASK_000",  # 重复ID
                title="重复任务",
                task_type=TaskType.ONLINE,
                status=TaskStatus.PENDING,
                member_id=member.id,
                report_time=datetime.utcnow(),
            )
            async_session.add(duplicate_task)

            # 这应该失败并触发回滚
            await async_session.commit()

        except IntegrityError:
            # 预期的错误，执行回滚
            await async_session.rollback()

            # 验证数据一致性 - 所有数据都应该被回滚
            final_task_count = await async_session.scalar(
                select(func.count(RepairTask.id))
            )
            final_member_count = await async_session.scalar(
                select(func.count(Member.id))
            )

            assert final_task_count == initial_task_count
            assert final_member_count == initial_member_count

            # 验证没有部分数据残留
            rollback_tasks = await async_session.execute(
                select(RepairTask).where(RepairTask.task_id.like("ROLLBACK_TASK_%"))
            )
            assert len(rollback_tasks.scalars().all()) == 0

            rollback_members = await async_session.execute(
                select(Member).where(Member.username == "rollback_test_member")
            )
            assert len(rollback_members.scalars().all()) == 0


@pytest.mark.asyncio
class TestDataIntegrityEdgeCases:
    """数据完整性边界情况测试"""

    async def test_cascade_delete_integrity(self, async_session):
        """测试级联删除完整性"""
        # 创建成员和关联任务
        member = Member(
            username="cascade_test_member",
            name="级联测试成员",
            student_id="CT001",
            class_name="测试班级",
            role=UserRole.MEMBER,
        )
        async_session.add(member)
        await async_session.flush()

        # 创建关联的任务
        task = RepairTask(
            task_id="CASCADE_TASK_001",
            title="级联测试任务",
            task_type=TaskType.ONLINE,
            status=TaskStatus.PENDING,
            member_id=member.id,
            report_time=datetime.utcnow(),
        )
        async_session.add(task)
        await async_session.commit()

        # 尝试删除成员（应该根据外键设置处理）
        await async_session.delete(member)

        try:
            await async_session.commit()

            # 如果删除成功，验证关联数据的处理
            remaining_task = await async_session.get(RepairTask, task.id)
            if remaining_task:
                # 如果任务仍存在，外键应该被设置为NULL或其他处理方式
                assert (
                    remaining_task.member_id is None
                    or remaining_task.member_id != member.id
                )

        except IntegrityError:
            # 如果有外键约束阻止删除，这也是正确的行为
            await async_session.rollback()

            # 验证原始数据仍然完整
            existing_member = await async_session.get(Member, member.id)
            existing_task = await async_session.get(RepairTask, task.id)

            assert existing_member is not None
            assert existing_task is not None
            assert existing_task.member_id == member.id

    async def test_large_data_batch_integrity(self, async_session):
        """测试大批量数据完整性"""
        # 创建基础成员
        member = Member(
            username="large_batch_member",
            name="大批量测试成员",
            student_id="LB001",
            class_name="测试班级",
            role=UserRole.MEMBER,
        )
        async_session.add(member)
        await async_session.flush()

        # 创建大量任务数据
        batch_size = 100
        tasks = []

        for i in range(batch_size):
            task = RepairTask(
                task_id=f"LARGE_BATCH_{i:05d}",
                title=f"大批量任务{i}",
                task_type=TaskType.ONLINE if i % 2 == 0 else TaskType.OFFLINE,
                status=TaskStatus.PENDING,
                member_id=member.id,
                report_time=datetime.utcnow() - timedelta(minutes=i),
            )
            tasks.append(task)

        # 分批插入以避免内存问题
        batch_insert_size = 20
        for i in range(0, len(tasks), batch_insert_size):
            batch = tasks[i : i + batch_insert_size]
            async_session.add_all(batch)

        await async_session.commit()

        # 验证数据完整性
        total_tasks = await async_session.scalar(
            select(func.count(RepairTask.id)).where(RepairTask.member_id == member.id)
        )
        assert total_tasks == batch_size

        # 验证数据一致性 - 所有任务都有有效的外键引用
        invalid_references = await async_session.scalar(
            select(func.count(RepairTask.id)).where(
                and_(
                    RepairTask.task_id.like("LARGE_BATCH_%"),
                    RepairTask.member_id.is_(None),
                )
            )
        )
        assert invalid_references == 0
