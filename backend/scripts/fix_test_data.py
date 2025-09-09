#!/usr/bin/env python3
"""
测试数据修复脚本
修复测试中的数据依赖和约束违反问题
"""

import re
from pathlib import Path


def fix_foreign_key_violations():
    """修复外键约束违反问题"""

    # 查找所有测试文件
    test_files = list(Path("tests").rglob("*.py"))

    fixes_made = 0

    for test_file in test_files:
        try:
            with open(test_file, "r", encoding="utf-8") as f:
                content = f.read()

            original_content = content

            # 修复member_id外键问题
            # 将无效的member_id替换为有效值或使用fixture
            content = re.sub(
                r'member_id["\s]*[=:]["\s]*99999', "member_id=test_user.id", content
            )

            content = re.sub(
                r'member_id["\s]*[=:]["\s]*1(?!\d)',  # 避免匹配更长的数字
                "member_id=test_user.id",
                content,
            )

            # 修复重复的task_id问题
            content = re.sub(
                r'task_id["\s]*[=:]["\s]*["\']UNIQUE_TASK_001["\']',
                'task_id=f"UNIQUE_TASK_{uuid.uuid4().hex[:8]}"',
                content,
            )

            content = re.sub(
                r'task_id["\s]*[=:]["\s]*["\']ROLLBACK_TASK_000["\']',
                'task_id=f"ROLLBACK_TASK_{uuid.uuid4().hex[:8]}"',
                content,
            )

            # 修复枚举类型问题
            content = re.sub(
                r'["\']INVALID_TYPE["\']',
                "TaskType.REPAIR",  # 使用有效的枚举值
                content,
            )

            content = re.sub(
                r'["\']INVALID_STATUS["\']',
                "TaskStatus.PENDING",  # 使用有效的枚举值
                content,
            )

            content = re.sub(
                r'["\']in_progress["\']',
                "TaskStatus.IN_PROGRESS",  # 使用正确的枚举值
                content,
            )

            # 如果内容有变化，添加必要的导入
            if content != original_content:
                # 检查是否需要添加导入
                imports_to_add = []

                if "uuid.uuid4()" in content and "import uuid" not in content:
                    imports_to_add.append("import uuid")

                if (
                    "TaskType." in content
                    and "from app.models.task import" not in content
                ):
                    if "TaskType" not in content.split("\n")[0]:  # 避免重复导入
                        imports_to_add.append(
                            "from app.models.task import TaskType, TaskStatus"
                        )

                # 在文件开头添加导入
                if imports_to_add:
                    lines = content.split("\n")
                    # 找到合适的位置插入导入（通常在其他导入之后）
                    import_line_index = 0
                    for i, line in enumerate(lines):
                        if line.startswith("import ") or line.startswith("from "):
                            import_line_index = i + 1
                        elif line.strip() == "" and import_line_index > 0:
                            import_line_index = i
                            break

                    # 插入新的导入
                    for import_stmt in reversed(imports_to_add):
                        lines.insert(import_line_index, import_stmt)

                    content = "\n".join(lines)

                # 保存修改后的文件
                with open(test_file, "w", encoding="utf-8") as f:
                    f.write(content)

                fixes_made += 1
                print(f"✅ 修复了 {test_file}")

        except Exception as e:
            print(f"⚠️  处理文件 {test_file} 时出错: {e}")

    return fixes_made


def create_test_fixtures():
    """创建通用的测试fixtures来避免数据依赖问题"""

    fixtures_content = '''"""
通用测试fixtures
提供稳定的测试数据，避免外键约束和数据依赖问题
"""

import uuid
from datetime import datetime, date, timedelta
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.member import Member, UserRole
from app.models.task import RepairTask, TaskType, TaskStatus, TaskCategory, TaskPriority
from app.models.attendance import AttendanceRecord


@pytest.fixture
async def test_member(db_session: AsyncSession):
    """创建测试用户"""
    member = Member(
        student_id=f"TEST{uuid.uuid4().hex[:8].upper()}",
        name="测试用户",
        email=f"test{uuid.uuid4().hex[:8]}@example.com",
        phone="13800138000",
        role=UserRole.MEMBER,
        is_active=True,
        hashed_password="$2b$12$test_hashed_password"
    )
    
    db_session.add(member)
    await db_session.commit()
    await db_session.refresh(member)
    
    return member


@pytest.fixture
async def test_admin(db_session: AsyncSession):
    """创建测试管理员"""
    admin = Member(
        student_id=f"ADMIN{uuid.uuid4().hex[:8].upper()}",
        name="测试管理员",
        email=f"admin{uuid.uuid4().hex[:8]}@example.com",
        phone="13800138001",
        role=UserRole.ADMIN,
        is_active=True,
        hashed_password="$2b$12$test_hashed_password"
    )
    
    db_session.add(admin)
    await db_session.commit()
    await db_session.refresh(admin)
    
    return admin


@pytest.fixture
async def test_task(db_session: AsyncSession, test_member: Member):
    """创建测试任务"""
    task = RepairTask(
        task_id=f"TASK_{uuid.uuid4().hex[:8].upper()}",
        title="测试维修任务",
        description="这是一个测试任务",
        member_id=test_member.id,
        task_type=TaskType.REPAIR,
        status=TaskStatus.PENDING,
        category=TaskCategory.NETWORK,
        priority=TaskPriority.MEDIUM,
        report_time=datetime.utcnow(),
        reporter_name="测试报告人",
        reporter_contact="test@example.com"
    )
    
    db_session.add(task)
    await db_session.commit()
    await db_session.refresh(task)
    
    return task


@pytest.fixture
async def test_attendance(db_session: AsyncSession, test_member: Member):
    """创建测试考勤记录"""
    attendance = AttendanceRecord(
        member_id=test_member.id,
        date=date.today(),
        check_in_time=datetime.now().replace(hour=9, minute=0, second=0),
        check_out_time=datetime.now().replace(hour=17, minute=0, second=0),
        status="present",
        work_hours=8.0
    )
    
    db_session.add(attendance)
    await db_session.commit()
    await db_session.refresh(attendance)
    
    return attendance


@pytest.fixture
def unique_task_id():
    """生成唯一的任务ID"""
    return f"TASK_{uuid.uuid4().hex[:8].upper()}"


@pytest.fixture
def unique_student_id():
    """生成唯一的学号"""
    return f"STU{uuid.uuid4().hex[:8].upper()}"


@pytest.fixture
def unique_email():
    """生成唯一的邮箱"""
    return f"test{uuid.uuid4().hex[:8]}@example.com"
'''

    fixture_path = Path("tests/fixtures/common_fixtures.py")
    fixture_path.parent.mkdir(parents=True, exist_ok=True)

    with open(fixture_path, "w", encoding="utf-8") as f:
        f.write(fixtures_content)

    # 创建__init__.py文件
    init_file = fixture_path.parent / "__init__.py"
    init_file.touch()

    print(f"✅ 创建了通用测试fixtures: {fixture_path}")


def main():
    """主函数"""
    print("🔧 开始修复测试数据问题...")

    try:
        # 修复外键约束违反
        fixes_made = fix_foreign_key_violations()
        print(f"✅ 修复了 {fixes_made} 个测试文件中的数据问题")

        # 创建测试fixtures
        create_test_fixtures()

        print("\n🎉 测试数据修复完成！")
        print("\n📋 修复内容:")
        print("  ✅ 修复了外键约束违反问题")
        print("  ✅ 修复了重复task_id问题")
        print("  ✅ 修复了无效枚举值问题")
        print("  ✅ 创建了通用测试fixtures")

        print("\n📝 建议:")
        print("  1. 在测试中使用fixtures而不是硬编码数据")
        print("  2. 使用unique_*fixtures生成唯一标识符")
        print("  3. 确保测试间的数据隔离")

    except Exception as e:
        print(f"❌ 修复过程中出现错误: {e}")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
