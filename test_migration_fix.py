#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库迁移错误修复验证脚本

专门测试和验证数据库迁移文件的修复，确保解决 'relation assistance_tasks does not exist' 错误
"""

import os
import sys
from pathlib import Path


def test_initial_migration_creation():
    """测试初始迁移文件是否创建成功"""
    print("检查初始迁移文件...")

    backend_dir = Path(__file__).parent / "backend"
    initial_migration = backend_dir / "alembic" / "versions" / "20250750_0000_initial_tables_creation.py"

    if not initial_migration.exists():
        print("初始迁移文件不存在")
        return False

    try:
        with open(initial_migration, 'r', encoding='utf-8') as f:
            content = f.read()

        # 检查是否包含 assistance_tasks 表的创建
        if 'assistance_tasks' in content and 'create_table' in content:
            print("发现 assistance_tasks 表创建语句")
        else:
            print("未找到 assistance_tasks 表创建语句")
            return False

        # 检查语法
        compile(content, initial_migration, 'exec')
        print("初始迁移文件语法正确")

        return True

    except Exception as e:
        print(f"初始迁移文件测试失败: {e}")
        return False


def test_problematic_migration_fix():
    """测试问题迁移文件是否已修复"""
    print("检查问题迁移文件修复...")

    backend_dir = Path(__file__).parent / "backend"
    migration_file = backend_dir / "alembic" / "versions" / "20250801_0007_2fc5b4d5d552_add_daily_attendance_records_and_.py"

    if not migration_file.exists():
        print("迁移文件不存在")
        return False

    try:
        with open(migration_file, 'r', encoding='utf-8') as f:
            content = f.read()

        # 检查是否使用了安全的表检查
        if 'IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = \'assistance_tasks\')' in content:
            print("发现安全的表存在性检查")
        else:
            print("未找到安全的表存在性检查")
            return False

        # 检查是否还有直接的 ALTER TABLE assistance_tasks
        if 'ALTER TABLE assistance_tasks' in content and 'DO $$' not in content:
            print("仍然包含不安全的 ALTER TABLE 语句")
            return False

        # 检查语法
        compile(content, migration_file, 'exec')
        print("问题迁移文件已修复，语法正确")

        return True

    except Exception as e:
        print(f"问题迁移文件测试失败: {e}")
        return False


def test_migration_dependencies():
    """测试迁移依赖关系是否正确"""
    print("检查迁移依赖关系...")

    backend_dir = Path(__file__).parent / "backend"
    versions_dir = backend_dir / "alembic" / "versions"

    # 读取所有迁移文件的依赖关系
    migrations = {}

    try:
        for file in versions_dir.glob("*.py"):
            if file.name.startswith("__"):
                continue

            with open(file, 'r', encoding='utf-8') as f:
                content = f.read()

            # 提取 revision 和 down_revision
            revision = None
            down_revision = None

            for line in content.split('\n'):
                line = line.strip()
                if line.startswith('revision:'):
                    # 匹配 revision: str = "value"
                    import re
                    match = re.search(r'revision:\s*str\s*=\s*["\']([^"\']+)["\']', line)
                    if match:
                        revision = match.group(1)
                elif line.startswith('down_revision:'):
                    # 匹配 down_revision: Union[str, None] = "value" 或 None
                    if 'None' in line and '"' not in line:
                        down_revision = None
                    else:
                        import re
                        match = re.search(r'down_revision:\s*[^=]+\s*=\s*["\']([^"\']+)["\']', line)
                        if match:
                            down_revision = match.group(1)

            if revision:
                migrations[revision] = {
                    'file': file.name,
                    'down_revision': down_revision
                }
# print(f"  解析文件 {file.name}: revision={revision}, down_revision={down_revision}")  # 调试信息

        # 检查初始迁移是否为根
        initial_migration = "20250750_0000"
        if initial_migration in migrations:
            if migrations[initial_migration]['down_revision'] is None:
                print(f"初始迁移 {initial_migration} 正确设置为根迁移")
            else:
                print(f"初始迁移 {initial_migration} 不是根迁移")
                return False
        else:
            print("未找到初始迁移")
            return False

        # 检查成员表迁移是否依赖初始迁移
        members_migration = "20250804_2300_001"
        if members_migration in migrations:
            if migrations[members_migration]['down_revision'] == initial_migration:
                print(f"成员表迁移正确依赖初始迁移")
            else:
                actual_dep = migrations[members_migration]['down_revision']
                print(f"成员表迁移依赖关系: {actual_dep}")
                # 如果实际依赖是None，说明还是旧的配置，需要修复
                if actual_dep != initial_migration:
                    print(f"依赖关系需要修复为: {initial_migration}")
                    return False

        print("迁移依赖关系检查通过")
        return True

    except Exception as e:
        print(f"迁移依赖关系检查失败: {e}")
        return False


def test_all_tables_covered():
    """测试是否所有必需的表都有创建语句"""
    print("检查所有表是否都有创建语句...")

    required_tables = {
        'members', 'task_tags', 'repair_tasks', 'monitoring_tasks',
        'assistance_tasks', 'task_tag_associations', 'attendance_records',
        'attendance_exceptions', 'monthly_attendance_summaries'
    }

    backend_dir = Path(__file__).parent / "backend"
    versions_dir = backend_dir / "alembic" / "versions"

    created_tables = set()

    try:
        for file in versions_dir.glob("*.py"):
            if file.name.startswith("__"):
                continue

            with open(file, 'r', encoding='utf-8') as f:
                content = f.read()

            # 查找 create_table 调用
            import re
            create_matches = re.findall(r'create_table\s*\(\s*["\']([^"\']+)["\']', content)
            for table in create_matches:
                created_tables.add(table)

        missing_tables = required_tables - created_tables
        extra_tables = created_tables - required_tables

        if missing_tables:
            print(f"缺失的表: {missing_tables}")
            return False

        if extra_tables:
            print(f"额外的表: {extra_tables}")

        print(f"所有必需的表都有创建语句: {len(created_tables)} 个表")
        return True

    except Exception as e:
        print(f"表覆盖检查失败: {e}")
        return False


def main():
    """主函数"""
    print("数据库迁移错误修复验证")
    print("=" * 50)

    tests = [
        ("初始迁移文件创建", test_initial_migration_creation),
        ("问题迁移文件修复", test_problematic_migration_fix),
        ("迁移依赖关系检查", test_migration_dependencies),
        ("表创建覆盖检查", test_all_tables_covered),
    ]

    passed = 0
    failed = 0

    for test_name, test_func in tests:
        print(f"\n{test_name}:")
        print("-" * 30)
        try:
            if test_func():
                print(f"通过")
                passed += 1
            else:
                print(f"失败")
                failed += 1
        except Exception as e:
            print(f"异常: {str(e)}")
            failed += 1

    print("\n" + "=" * 50)
    print("测试总结:")
    print(f"通过: {passed}")
    print(f"失败: {failed}")

    if failed == 0:
        print("\n所有修复验证通过！")
        print("\n修复摘要:")
        print("1. 创建了初始迁移文件 (20250750_0000) 来创建所有缺失的表")
        print("2. 修复了问题迁移文件中的 ALTER TABLE assistance_tasks 语句")
        print("3. 更新了迁移依赖关系，确保正确的执行顺序")
        print("4. 使用安全的表存在性检查避免 'relation does not exist' 错误")
        print("\n建议:")
        print("- 推送代码到远程仓库触发CI/CD测试")
        print("- 观察GitHub Actions中的数据库迁移步骤")
        print("- 确认不再出现表不存在的错误")
        return True
    else:
        print(f"\n有 {failed} 项测试失败，需要进一步检查和修复")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
