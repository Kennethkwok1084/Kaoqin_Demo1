"""
数据库兼容性测试
验证SQLite vs PostgreSQL环境差异修复
"""

import pytest
from sqlalchemy import text

from app.core.database_compatibility import (
    DatabaseCompatibilityChecker,
    DatabaseType,
    SQLiteEnumValidator,
    should_use_postgresql_tests,
)
from tests.database_config import postgresql_only, sqlite_only


@pytest.mark.asyncio
class TestDatabaseCompatibilityChecker:
    """数据库兼容性检查器测试"""

    async def test_database_type_detection(self, async_session):
        """测试数据库类型检测"""
        checker = DatabaseCompatibilityChecker(async_session)
        assert checker.db_type in [DatabaseType.SQLITE, DatabaseType.POSTGRESQL]

    async def test_compatibility_report(self, async_session):
        """测试兼容性报告生成"""
        checker = DatabaseCompatibilityChecker(async_session)
        report = await checker.get_compatibility_report()

        # 验证报告结构
        assert "database_type" in report
        assert "enum_support" in report
        assert "concurrent_transactions" in report
        assert "constraint_validation" in report

        # 验证数据类型
        assert isinstance(report["enum_support"], bool)
        assert isinstance(report["concurrent_transactions"], bool)
        assert isinstance(report["constraint_validation"], bool)

    @postgresql_only
    async def test_postgresql_enum_support(self, async_session):
        """测试PostgreSQL ENUM支持"""
        checker = DatabaseCompatibilityChecker(async_session)

        # PostgreSQL应该支持ENUM
        enum_support = await checker.check_enum_support()
        assert enum_support is True

        # 检查具体的ENUM类型
        result = await async_session.execute(
            text("SELECT typname FROM pg_type WHERE typtype = 'e'")
        )
        enum_types = result.scalars().all()

        expected_enums = [
            "userrole",
            "taskstatus",
            "taskcategory",
            "taskpriority",
            "tasktype",
            "tasktagtype",
            "attendanceexceptionstatus",
        ]

        for enum_type in expected_enums:
            assert enum_type in enum_types, f"Missing ENUM type: {enum_type}"

    @postgresql_only
    async def test_postgresql_concurrent_transactions(self, async_session):
        """测试PostgreSQL并发事务支持"""
        checker = DatabaseCompatibilityChecker(async_session)

        # PostgreSQL应该支持并发事务
        concurrent_support = await checker.check_concurrent_transactions()
        assert concurrent_support is True

        # 验证隔离级别
        result = await async_session.execute(
            text("SELECT current_setting('transaction_isolation')")
        )
        isolation_level = result.scalar()
        assert isolation_level is not None

    @sqlite_only
    async def test_sqlite_limitations(self, async_session):
        """测试SQLite限制性"""
        checker = DatabaseCompatibilityChecker(async_session)

        # SQLite不支持原生ENUM
        enum_support = await checker.check_enum_support()
        assert enum_support is False

        # SQLite并发事务支持有限
        concurrent_support = await checker.check_concurrent_transactions()
        assert concurrent_support is False


class TestSQLiteEnumValidator:
    """SQLite ENUM验证器测试"""

    def test_task_status_validation(self):
        """测试任务状态验证"""
        # 有效值
        assert SQLiteEnumValidator.validate_task_status("PENDING") is True
        assert SQLiteEnumValidator.validate_task_status("IN_PROGRESS") is True
        assert SQLiteEnumValidator.validate_task_status("COMPLETED") is True
        assert SQLiteEnumValidator.validate_task_status("CANCELLED") is True
        assert SQLiteEnumValidator.validate_task_status("ON_HOLD") is True

        # 大小写兼容
        assert SQLiteEnumValidator.validate_task_status("pending") is True
        assert SQLiteEnumValidator.validate_task_status(TaskStatus.IN_PROGRESS) is True

        # 无效值
        assert SQLiteEnumValidator.validate_task_status("INVALID") is False
        assert SQLiteEnumValidator.validate_task_status("") is False
        assert SQLiteEnumValidator.validate_task_status(None) is False

    def test_user_role_validation(self):
        """测试用户角色验证"""
        # 有效值
        assert SQLiteEnumValidator.validate_user_role("ADMIN") is True
        assert SQLiteEnumValidator.validate_user_role("GROUP_LEADER") is True
        assert SQLiteEnumValidator.validate_user_role("MEMBER") is True
        assert SQLiteEnumValidator.validate_user_role("GUEST") is True

        # 大小写兼容
        assert SQLiteEnumValidator.validate_user_role("admin") is True
        assert SQLiteEnumValidator.validate_user_role("member") is True

        # 无效值
        assert SQLiteEnumValidator.validate_user_role("INVALID") is False
        assert SQLiteEnumValidator.validate_user_role(None) is False

    def test_task_type_validation(self):
        """测试任务类型验证"""
        # 有效值
        assert SQLiteEnumValidator.validate_task_type("ONLINE") is True
        assert SQLiteEnumValidator.validate_task_type("OFFLINE") is True

        # 大小写兼容
        assert SQLiteEnumValidator.validate_task_type("online") is True
        assert SQLiteEnumValidator.validate_task_type("offline") is True

        # 无效值
        assert SQLiteEnumValidator.validate_task_type("INVALID") is False
        assert SQLiteEnumValidator.validate_task_type(None) is False

    def test_task_priority_validation(self):
        """测试任务优先级验证"""
        # 有效值
        assert SQLiteEnumValidator.validate_task_priority("LOW") is True
        assert SQLiteEnumValidator.validate_task_priority("MEDIUM") is True
        assert SQLiteEnumValidator.validate_task_priority("HIGH") is True
        assert SQLiteEnumValidator.validate_task_priority("URGENT") is True

        # 无效值
        assert SQLiteEnumValidator.validate_task_priority("INVALID") is False
        assert SQLiteEnumValidator.validate_task_priority(None) is False

    def test_task_tag_type_validation(self):
        """测试任务标签类型验证"""
        # 有效值
        valid_tag_types = [
            "rush_order",
            "non_default_rating",
            "timeout_response",
            "timeout_processing",
            "bad_rating",
            "bonus",
            "penalty",
            "category",
        ]

        for tag_type in valid_tag_types:
            assert SQLiteEnumValidator.validate_task_tag_type(tag_type) is True

        # 大小写兼容性测试
        assert (
            SQLiteEnumValidator.validate_task_tag_type("RUSH_ORDER") is True
        )  # 大小写不敏感
        assert (
            SQLiteEnumValidator.validate_task_tag_type("Rush_Order") is True
        )  # 混合大小写也可以

        # 无效值
        assert SQLiteEnumValidator.validate_task_tag_type("invalid") is False
        assert SQLiteEnumValidator.validate_task_tag_type(None) is False

    def test_get_all_validations(self):
        """测试获取所有验证规则"""
        validations = SQLiteEnumValidator.get_all_validations()

        # 验证结构
        expected_keys = [
            "task_status",
            "user_role",
            "task_type",
            "task_priority",
            "task_tag_type",
        ]

        for key in expected_keys:
            assert key in validations
            assert isinstance(validations[key], list)
            assert len(validations[key]) > 0


@pytest.mark.asyncio
class TestDatabaseEnvironmentIntegration:
    """数据库环境集成测试"""

    async def test_database_environment_setup(self, async_session):
        """测试数据库环境设置"""
        # 验证数据库连接
        result = await async_session.execute(text("SELECT 1"))
        assert result.scalar() == 1

        # 验证兼容性检查器
        checker = DatabaseCompatibilityChecker(async_session)
        report = await checker.get_compatibility_report()

        # 根据环境验证预期行为
        if should_use_postgresql_tests():
            assert report["database_type"] == "postgresql"
            assert report["enum_support"] is True
            assert report["concurrent_transactions"] is True
        else:
            assert report["database_type"] == "sqlite"
            assert report["enum_support"] is False
            assert report["concurrent_transactions"] is False

    async def test_enum_constraint_behavior(self, async_session):
        """测试ENUM约束行为"""
        from app.models.member import Member, UserRole

        # 创建测试用户
        test_member = Member(
            username="test_enum_user",
            name="测试ENUM用户",
            student_id="TEST001",
            class_name="测试班级",
            role=UserRole.MEMBER,
        )

        async_session.add(test_member)
        await async_session.commit()

        # 验证ENUM值正确保存
        result = await async_session.execute(
            text("SELECT role FROM members WHERE username = 'test_enum_user'")
        )
        role_value = result.scalar()

        # 不同数据库的ENUM处理方式
        if should_use_postgresql_tests():
            # PostgreSQL保存ENUM值
            assert role_value == "MEMBER"
        else:
            # SQLite可能保存为字符串
            assert role_value in ["MEMBER", "member"]
