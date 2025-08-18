#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试迁移修复脚本

专门测试我们修复的DROP TABLE IF EXISTS问题
"""

import os
import sys
from pathlib import Path


def test_migration_file_syntax():
    """测试迁移文件语法"""
    print("🔄 检查迁移文件语法...")
    
    backend_dir = Path(__file__).parent / "backend"
    migration_file = backend_dir / "alembic" / "versions" / "20250801_0007_2fc5b4d5d552_add_daily_attendance_records_and_.py"
    
    if not migration_file.exists():
        print("❌ 迁移文件不存在")
        return False
    
    # 读取文件内容
    try:
        with open(migration_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查是否包含修复后的语句
        if 'DROP TABLE IF EXISTS attendance_configurations' in content:
            print("✅ 发现修复后的 DROP TABLE IF EXISTS 语句")
        elif 'op.drop_table("attendance_configurations")' in content:
            print("❌ 仍然包含有问题的 op.drop_table 语句")
            return False
        else:
            print("⚠️  未找到相关的 DROP TABLE 语句")
        
        # 尝试编译Python语法
        compile(content, migration_file, 'exec')
        print("✅ 迁移文件Python语法正确")
        
        return True
        
    except SyntaxError as e:
        print(f"❌ 迁移文件语法错误: {e}")
        return False
    except Exception as e:
        print(f"❌ 读取迁移文件失败: {e}")
        return False


def test_config_ci_detection():
    """测试配置文件的CI环境检测"""
    print("🔄 测试CI环境检测...")
    
    # 设置CI环境变量
    original_ci = os.environ.get('CI')
    original_github = os.environ.get('GITHUB_ACTIONS')
    
    try:
        os.environ['CI'] = 'true'
        os.environ['GITHUB_ACTIONS'] = 'true'
        
        # 导入配置
        sys.path.insert(0, str(Path(__file__).parent / "backend"))
        from app.core.config import settings
        
        # 检查数据库URL是否使用了本地配置
        db_url = str(settings.DATABASE_URL)
        if 'localhost' in db_url and 'test_db' in db_url:
            print("✅ CI环境检测正常，使用本地数据库配置")
            print(f"   数据库URL: {db_url}")
            return True
        else:
            print(f"❌ CI环境检测失败，数据库URL: {db_url}")
            return False
            
    except Exception as e:
        print(f"❌ 配置测试失败: {e}")
        return False
    finally:
        # 恢复环境变量
        if original_ci is not None:
            os.environ['CI'] = original_ci
        elif 'CI' in os.environ:
            del os.environ['CI']
            
        if original_github is not None:
            os.environ['GITHUB_ACTIONS'] = original_github
        elif 'GITHUB_ACTIONS' in os.environ:
            del os.environ['GITHUB_ACTIONS']


def main():
    """主函数"""
    print("🚀 测试迁移修复\n")
    
    tests = [
        ("迁移文件语法检查", test_migration_file_syntax),
        ("CI环境检测测试", test_config_ci_detection),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ {test_name} 执行异常: {str(e)}")
            failed += 1
        print()
    
    print("📊 测试总结:")
    print(f"✅ 通过: {passed}")
    print(f"❌ 失败: {failed}")
    
    if failed == 0:
        print("\n🎉 所有修复验证通过！CI/CD中的数据库迁移问题应该已解决")
        print("\n💡 建议:")
        print("   1. 推送代码到远程仓库触发CI/CD")
        print("   2. 观察GitHub Actions中的数据库迁移步骤")
        print("   3. 确认不再出现 'table does not exist' 错误")
        return True
    else:
        print(f"\n⚠️  有 {failed} 项测试失败，需要进一步检查")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)