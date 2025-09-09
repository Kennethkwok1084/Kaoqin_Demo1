#!/usr/bin/env python3
"""
CI问题修复脚本
修复GitHub Actions CI/CD中的常见问题
"""

import os
import yaml
from pathlib import Path


def fix_github_workflow():
    """修复GitHub Actions workflow配置"""

    workflow_path = Path("../.github/workflows/backend-ci.yml")
    if not workflow_path.exists():
        print("GitHub workflow文件不存在，跳过修复")
        return

    # 读取现有workflow
    with open(workflow_path, "r", encoding="utf-8") as f:
        workflow = yaml.safe_load(f)

    # 修复PostgreSQL服务配置
    services = (
        workflow.get("jobs", {})
        .get("backend-comprehensive-test", {})
        .get("services", {})
    )
    if "postgres" in services:
        postgres_config = services["postgres"]

        # 确保使用正确的用户配置
        postgres_config["env"] = {
            "POSTGRES_DB": "attendence_test",
            "POSTGRES_USER": "postgres",
            "POSTGRES_PASSWORD": "postgres",
            "POSTGRES_HOST_AUTH_METHOD": "trust",
        }

        # 确保健康检查正确
        postgres_config["options"] = (
            '--health-cmd="pg_isready -U postgres" '
            "--health-interval=10s "
            "--health-timeout=5s "
            "--health-retries=5"
        )

    # 修复测试环境变量
    test_job = workflow.get("jobs", {}).get("backend-comprehensive-test", {})
    if "env" not in test_job:
        test_job["env"] = {}

    test_job["env"].update(
        {
            "DATABASE_URL": "postgresql://postgres:postgres@localhost:5432/attendence_test",
            "POSTGRES_USER": "postgres",
            "POSTGRES_PASSWORD": "postgres",
            "TESTING": "true",
            "CI": "true",
        }
    )

    # 保存修复后的workflow
    with open(workflow_path, "w", encoding="utf-8") as f:
        yaml.dump(workflow, f, default_flow_style=False, allow_unicode=True)

    print("✅ GitHub workflow配置已修复")


def fix_pytest_config():
    """修复pytest配置"""

    # 创建/更新pytest.ini
    pytest_config = """[tool:pytest]
testpaths = tests
python_files = test_*.py *_test.py
python_classes = Test*
python_functions = test_*
addopts = 
    --strict-markers
    --strict-config
    --verbose
    --tb=short
    --maxfail=10
    --durations=10
    --import-mode=importlib
filterwarnings =
    ignore::DeprecationWarning
    ignore::PendingDeprecationWarning
    ignore::pytest.PytestUnraisableExceptionWarning
markers =
    slow: marks tests as slow (deselect with '-m "not slow"')
    integration: marks tests as integration tests
    unit: marks tests as unit tests
    api: marks tests as API tests
    benchmark: marks tests as benchmark tests (pytest-benchmark required)
asyncio_mode = auto
"""

    with open("pytest.ini", "w", encoding="utf-8") as f:
        f.write(pytest_config)

    print("✅ pytest配置已修复")


def create_test_database_setup():
    """创建测试数据库设置脚本"""

    setup_script = """#!/bin/bash
# 测试数据库设置脚本

set -e

echo "🔧 设置测试数据库环境..."

# 等待PostgreSQL启动
until pg_isready -h localhost -p 5432 -U postgres; do
  echo "等待PostgreSQL启动..."
  sleep 2
done

# 创建测试数据库
echo "创建测试数据库..."
psql -h localhost -U postgres -c "DROP DATABASE IF EXISTS attendence_test;"
psql -h localhost -U postgres -c "CREATE DATABASE attendence_test OWNER postgres;"
psql -h localhost -U postgres -c "GRANT ALL PRIVILEGES ON DATABASE attendence_test TO postgres;"

echo "✅ 测试数据库设置完成"
"""

    script_path = Path("scripts/setup_test_db.sh")
    script_path.parent.mkdir(exist_ok=True)

    with open(script_path, "w", encoding="utf-8") as f:
        f.write(setup_script)

    # 设置执行权限
    script_path.chmod(0o755)

    print(f"✅ 测试数据库设置脚本已创建: {script_path}")


def create_database_cleanup_fixture():
    """创建数据库清理fixture"""

    fixture_code = '''"""
数据库清理和设置fixtures
确保每次测试前数据库状态干净
"""

import pytest
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.core.database import async_engine, get_async_session
from app.models.base import Base


@pytest.fixture(scope="session", autouse=True)
async def setup_test_database():
    """设置测试数据库"""
    async with async_engine.begin() as conn:
        # 创建所有表
        await conn.run_sync(Base.metadata.create_all)
    
    yield
    
    # 清理
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture(autouse=True)
async def clean_database():
    """每个测试前清理数据库"""
    async with async_engine.begin() as conn:
        # 禁用外键约束
        await conn.execute(text("SET session_replication_role = replica;"))
        
        # 清理所有表数据
        for table in reversed(Base.metadata.sorted_tables):
            await conn.execute(text(f"TRUNCATE TABLE {table.name} RESTART IDENTITY CASCADE;"))
        
        # 重新启用外键约束
        await conn.execute(text("SET session_replication_role = DEFAULT;"))
        
        await conn.commit()


@pytest.fixture
async def db_session():
    """获取数据库会话"""
    async with get_async_session() as session:
        yield session


@pytest.fixture
async def clean_db_session():
    """获取干净的数据库会话（确保事务隔离）"""
    async with get_async_session() as session:
        # 开始事务
        transaction = await session.begin()
        try:
            yield session
        finally:
            # 回滚事务，确保测试不影响其他测试
            await transaction.rollback()
'''

    fixture_path = Path("tests/conftest_db.py")
    fixture_path.parent.mkdir(exist_ok=True)

    with open(fixture_path, "w", encoding="utf-8") as f:
        f.write(fixture_code)

    print(f"✅ 数据库清理fixture已创建: {fixture_path}")


def fix_test_imports():
    """修复测试中的导入问题"""

    # 创建测试专用的导入助手
    import_helper = '''"""
测试导入助手
统一管理测试中常用的导入，避免重复和遗漏
"""

# FastAPI相关
from fastapi import HTTPException, status
from fastapi.testclient import TestClient

# 测试相关
import pytest
from httpx import AsyncClient
from unittest.mock import AsyncMock, MagicMock, patch

# 业务异常
from app.core.exceptions import (
    ValidationError,
    NotFoundError,
    PermissionDeniedError,
    DatabaseError,
    AuthenticationError,
    BusinessLogicError,
    ExternalServiceError
)

# 数据模型
from app.models.member import Member, UserRole
from app.models.task import RepairTask, TaskStatus, TaskType, TaskCategory, TaskPriority
from app.models.attendance import AttendanceRecord

# 服务层
from app.services.attendance_service import AttendanceService
from app.services.stats_service import StatisticsService
from app.services.task_service import TaskService
from app.services.work_hours_service import WorkHoursService

# 应用
from app.main import app

__all__ = [
    # FastAPI
    'HTTPException', 'status', 'TestClient',
    
    # 测试工具
    'pytest', 'AsyncClient', 'AsyncMock', 'MagicMock', 'patch',
    
    # 异常
    'ValidationError', 'NotFoundError', 'PermissionDeniedError', 
    'DatabaseError', 'AuthenticationError', 'BusinessLogicError', 
    'ExternalServiceError',
    
    # 模型
    'Member', 'UserRole', 'RepairTask', 'TaskStatus', 'TaskType',
    'TaskCategory', 'TaskPriority', 'AttendanceRecord',
    
    # 服务
    'AttendanceService', 'StatisticsService', 'TaskService', 'WorkHoursService',
    
    # 应用
    'app'
]
'''

    helper_path = Path("tests/test_imports.py")
    with open(helper_path, "w", encoding="utf-8") as f:
        f.write(import_helper)

    print(f"✅ 测试导入助手已创建: {helper_path}")


def main():
    """主函数"""
    print("🔧 开始修复CI问题...")

    try:
        fix_pytest_config()
        create_test_database_setup()
        create_database_cleanup_fixture()
        fix_test_imports()
        fix_github_workflow()

        print("\n🎉 CI问题修复完成！")
        print("\n📋 修复内容:")
        print("  ✅ 修复了pytest配置")
        print("  ✅ 创建了数据库设置脚本")
        print("  ✅ 创建了数据库清理fixture")
        print("  ✅ 修复了测试导入问题")
        print("  ✅ 修复了GitHub workflow配置")

        print("\n📝 后续操作:")
        print("  1. 运行 chmod +x scripts/setup_test_db.sh")
        print("  2. 在测试中导入 tests.conftest_db 中的fixtures")
        print("  3. 更新GitHub workflow以使用新的数据库配置")
        print("  4. 重新运行CI测试")

    except Exception as e:
        print(f"❌ 修复过程中出现错误: {e}")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
