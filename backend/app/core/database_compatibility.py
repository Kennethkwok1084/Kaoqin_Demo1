"""
PostgreSQL数据库配置和工具
专用于PostgreSQL数据库的配置管理
"""

import logging
import os
from enum import Enum
from typing import Any, Dict, List, Optional

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class DatabaseType(Enum):
    """数据库类型枚举 - PostgreSQL专用"""
    
    POSTGRESQL = "postgresql"


class PostgreSQLChecker:
    """PostgreSQL数据库检查器"""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.db_type = DatabaseType.POSTGRESQL

    def _detect_database_type(self) -> DatabaseType:
        """检测数据库类型 - 始终返回PostgreSQL"""
        return DatabaseType.POSTGRESQL

    async def check_enum_support(self) -> bool:
        """检查ENUM支持 - PostgreSQL原生支持"""
        try:
            # PostgreSQL原生支持ENUM类型
            result = await self.session.execute(
                text("SELECT typname FROM pg_type WHERE typtype = 'e' LIMIT 1")
            )
            return result.scalar() is not None
        except Exception as e:
            logger.error(f"Failed to check ENUM support: {e}")
            return False

    async def check_concurrent_transactions(self) -> bool:
        """检查并发事务支持 - PostgreSQL完全支持MVCC"""
        try:
            # PostgreSQL支持真正的MVCC
            result = await self.session.execute(
                text("SELECT current_setting('transaction_isolation')")
            )
            isolation_level = result.scalar()
            return isolation_level is not None
        except Exception as e:
            logger.error(f"Failed to check concurrent transactions: {e}")
            return False

    async def validate_constraints(self) -> bool:
        """验证约束系统 - PostgreSQL完整支持"""
        try:
            # 检查约束系统
            result = await self.session.execute(
                text(
                    """
                    SELECT COUNT(*) FROM information_schema.check_constraints
                    WHERE constraint_schema = current_schema()
                """
                )
            )
            constraint_count = result.scalar()
            return constraint_count is not None
        except Exception as e:
            logger.error(f"Failed to validate constraints: {e}")
            return False

    async def get_compatibility_report(self) -> Dict[str, Any]:
        """获取PostgreSQL兼容性报告"""
        return {
            "database_type": self.db_type.value,
            "enum_support": await self.check_enum_support(),
            "concurrent_transactions": await self.check_concurrent_transactions(),
            "constraint_validation": await self.validate_constraints(),
        }


class PostgreSQLEnumValidator:
    """PostgreSQL ENUM值验证器"""

    # 定义ENUM值映射
    TASK_STATUS_VALUES = ["PENDING", "IN_PROGRESS", "COMPLETED", "CANCELLED", "ON_HOLD"]
    USER_ROLE_VALUES = ["ADMIN", "GROUP_LEADER", "MEMBER", "GUEST"]
    TASK_TYPE_VALUES = ["ONLINE", "OFFLINE"]
    TASK_PRIORITY_VALUES = ["LOW", "MEDIUM", "HIGH", "URGENT"]
    TASK_TAG_TYPE_VALUES = [
        "rush_order",
        "non_default_rating",
        "timeout_response",
        "timeout_processing",
        "bad_rating",
        "bonus",
        "penalty",
        "category",
    ]

    @classmethod
    def validate_task_status(cls, value: Optional[str]) -> bool:
        """验证任务状态"""
        if value is None:
            return False
        return value.upper() in cls.TASK_STATUS_VALUES

    @classmethod
    def validate_user_role(cls, value: Optional[str]) -> bool:
        """验证用户角色"""
        if value is None:
            return False
        return value.upper() in cls.USER_ROLE_VALUES

    @classmethod
    def validate_task_type(cls, value: Optional[str]) -> bool:
        """验证任务类型"""
        if value is None:
            return False
        return value.upper() in cls.TASK_TYPE_VALUES

    @classmethod
    def validate_task_priority(cls, value: Optional[str]) -> bool:
        """验证任务优先级"""
        if value is None:
            return False
        return value.upper() in cls.TASK_PRIORITY_VALUES

    @classmethod
    def validate_task_tag_type(cls, value: Optional[str]) -> bool:
        """验证任务标签类型"""
        if value is None:
            return False
        value_lower = value.lower()
        # Check direct match against lowercase values
        return value_lower in [tag.lower() for tag in cls.TASK_TAG_TYPE_VALUES]

    @classmethod
    def get_all_validations(cls) -> Dict[str, List[str]]:
        """获取所有验证规则"""
        return {
            "task_status": cls.TASK_STATUS_VALUES,
            "user_role": cls.USER_ROLE_VALUES,
            "task_type": cls.TASK_TYPE_VALUES,
            "task_priority": cls.TASK_PRIORITY_VALUES,
            "task_tag_type": cls.TASK_TAG_TYPE_VALUES,
        }


def get_test_database_url() -> str:
    """获取测试数据库URL - PostgreSQL专用"""
    # 首先检查是否有明确的DATABASE_URL环境变量
    explicit_url = os.getenv("DATABASE_URL")
    if explicit_url:
        return explicit_url

    # PostgreSQL配置基于环境
    if os.getenv("CI") == "true" or os.getenv("GITHUB_ACTIONS") == "true":
        # CI环境：使用PostgreSQL服务
        host = os.getenv("TEST_DB_HOST", "localhost")
        port = os.getenv("TEST_DB_PORT", "5432")
        user = os.getenv("TEST_DB_USER", "postgres")
        password = os.getenv("TEST_DB_PASSWORD", "postgres")
        database = os.getenv("TEST_DB_NAME", "test_attendence")
        return f"postgresql+asyncpg://{user}:{password}@{host}:{port}/{database}"
    elif os.getenv("INTEGRATION_TEST") == "true":
        # 集成测试使用PostgreSQL
        host = os.getenv("TEST_DB_HOST", "localhost")
        port = os.getenv("TEST_DB_PORT", "5432")
        user = os.getenv("TEST_DB_USER", "kwok")
        password = os.getenv("TEST_DB_PASSWORD", "Onjuju1084")
        database = os.getenv("TEST_DB_NAME", "attendence_dev")
        return f"postgresql+asyncpg://{user}:{password}@{host}:{port}/{database}"
    else:
        # 本地测试使用PostgreSQL
        host = os.getenv("TEST_DB_HOST", "localhost")
        port = os.getenv("TEST_DB_PORT", "5432")
        user = os.getenv("TEST_DB_USER", "kwok")
        password = os.getenv("TEST_DB_PASSWORD", "Onjuju1084")
        database = os.getenv("TEST_DB_NAME", "attendence_dev")
        return f"postgresql+asyncpg://{user}:{password}@{host}:{port}/{database}"


def should_use_postgresql_tests() -> bool:
    """判断是否应该使用PostgreSQL测试 - 始终返回True"""
    return True


# 向后兼容性别名
DatabaseCompatibilityChecker = PostgreSQLChecker
SQLiteEnumValidator = PostgreSQLEnumValidator