#!/usr/bin/env python3
"""
完整的迁移测试脚本
测试数据库迁移是否可以正常工作，不会出现表已存在的冲突
"""

import asyncio
import os
import sys
from pathlib import Path

# 添加backend目录到Python路径
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from sqlalchemy import text
from app.core.database import async_engine
from app.models.base import Base


async def test_clean_migration():
    """测试清理后的迁移是否工作正常"""
    print("=== 完整迁移测试 ===")
    print(f"数据库引擎: {async_engine.url}")
    
    try:
        # 1. 清空数据库（除了PostgreSQL系统表）
        print("\n[步骤1] 清空现有数据库...")
        async with async_engine.begin() as conn:
            # 删除 alembic_version 表
            await conn.execute(text('DROP TABLE IF EXISTS alembic_version CASCADE'))
            
            # 删除所有用户表
            tables_to_drop = [
                'task_tag_associations',
                'monthly_attendance_summaries', 
                'attendance_exceptions',
                'attendance_records',
                'assistance_tasks',
                'monitoring_tasks', 
                'repair_tasks',
                'task_tags',
                'members'
            ]
            
            for table in tables_to_drop:
                await conn.execute(text(f'DROP TABLE IF EXISTS {table} CASCADE'))
                print(f"  - 删除表: {table}")
            
            # 删除枚举类型
            enum_types = [
                'userrole',
                'taskstatus', 
                'taskcategory',
                'taskpriority',
                'tasktype',
                'tasktagtype',
                'attendanceexceptionstatus'
            ]
            
            for enum_type in enum_types:
                await conn.execute(text(f'DROP TYPE IF EXISTS {enum_type} CASCADE'))
                print(f"  - 删除枚举: {enum_type}")
                
        print("[OK] 数据库已清空")
        
        # 2. 运行Alembic迁移
        print("\n[步骤2] 运行Alembic迁移...")
        import subprocess
        result = subprocess.run([
            sys.executable, "-m", "alembic", "upgrade", "head"
        ], cwd=backend_dir, capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"[ERROR] Alembic迁移失败: {result.stderr}")
            return False
        else:
            print("[OK] Alembic迁移成功")
        
        # 3. 验证表是否创建成功
        print("\n[步骤3] 验证表结构...")
        async with async_engine.begin() as conn:
            # 检查所有必要的表是否存在
            result = await conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_type = 'BASE TABLE'
                ORDER BY table_name
            """))
            
            tables = [row[0] for row in result]
            print(f"  发现表: {tables}")
            
            expected_tables = {
                'members', 'task_tags', 'repair_tasks', 'monitoring_tasks',
                'assistance_tasks', 'attendance_records', 'attendance_exceptions',
                'monthly_attendance_summaries', 'task_tag_associations', 'alembic_version'
            }
            
            missing_tables = expected_tables - set(tables)
            if missing_tables:
                print(f"[ERROR] 缺少表: {missing_tables}")
                return False
            else:
                print("[OK] 所有必要的表都已创建")
            
            # 检查枚举类型
            result = await conn.execute(text("""
                SELECT typname 
                FROM pg_type 
                WHERE typname IN ('userrole', 'taskstatus', 'taskcategory', 'taskpriority', 'tasktype', 'tasktagtype', 'attendanceexceptionstatus')
                ORDER BY typname
            """))
            
            enums = [row[0] for row in result]
            print(f"  发现枚举: {enums}")
            
            expected_enums = {
                'userrole', 'taskstatus', 'taskcategory', 
                'taskpriority', 'tasktype', 'tasktagtype', 'attendanceexceptionstatus'
            }
            
            missing_enums = expected_enums - set(enums)
            if missing_enums:
                print(f"[ERROR] 缺少枚举: {missing_enums}")
                return False
            else:
                print("[OK] 所有枚举类型都已创建")
        
        # 4. 测试重复运行迁移（应该不报错）
        print("\n[步骤4] 测试重复运行迁移...")
        result2 = subprocess.run([
            sys.executable, "-m", "alembic", "upgrade", "head"
        ], cwd=backend_dir, capture_output=True, text=True)
        
        if result2.returncode == 0:
            print("[OK] 重复运行迁移成功（无冲突）")
        else:
            print(f"[ERROR] 重复运行迁移失败: {result2.stderr}")
            return False
        
        # 5. 测试基本数据操作
        print("\n[步骤5] 测试基本数据操作...")
        async with async_engine.begin() as conn:
            # 插入测试数据
            await conn.execute(text("""
                INSERT INTO members (username, name, class_name, password_hash, role, department, join_date, is_active, profile_completed, is_verified, login_count) 
                VALUES ('test_user', '测试用户', '测试班级', 'test_hash', 'MEMBER', '信息化建设处', CURRENT_DATE, true, false, false, 0)
                ON CONFLICT (username) DO NOTHING
            """))
            
            # 查询数据
            result = await conn.execute(text("""
                SELECT username, name FROM members WHERE username = 'test_user'
            """))
            
            row = result.fetchone()
            if row:
                print(f"[OK] 数据操作成功: {row[0]} - {row[1]}")
            else:
                print("[ERROR] 数据操作失败")
                return False
        
        print("\n[SUCCESS] 完整迁移测试通过！")
        print("数据库迁移工作正常，无表冲突")
        print("所有表和枚举都已正确创建")  
        print("可以重复运行迁移而不出错")
        print("基本数据操作正常")
        
        return True
        
    except Exception as e:
        print(f"\n[ERROR] 迁移测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(test_clean_migration())
    sys.exit(0 if success else 1)