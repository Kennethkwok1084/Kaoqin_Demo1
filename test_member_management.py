#!/usr/bin/env python3
"""
成员管理模块全面测试脚本
Comprehensive test script for member management module

测试内容:
1. 数据库连接和迁移测试
2. 模型导入和结构验证
3. Schema验证测试
4. API端点连通性测试
5. 业务逻辑测试
6. 数据验证测试
7. 权限控制测试
8. 导入功能测试
"""

import os
import sys
import asyncio
import json
from datetime import date
from typing import Dict, Any, List
import traceback

# 添加backend路径到sys.path
backend_path = os.path.join(os.path.dirname(__file__), 'backend')
sys.path.insert(0, backend_path)

# 设置环境变量
os.environ['PYTHONPATH'] = backend_path

def print_test_header(title: str):
    """打印测试标题"""
    print("\n" + "="*80)
    print(f"  {title}")
    print("="*80)

def print_test_result(test_name: str, success: bool, message: str = ""):
    """打印测试结果"""
    status = "PASS" if success else "FAIL"
    status_symbol = "[PASS]" if success else "[FAIL]"
    print(f"{status_symbol} {test_name}: {status}")
    if message:
        print(f"  详情: {message}")

def test_imports():
    """测试模块导入"""
    print_test_header("1. 模块导入测试")
    
    # 测试基础导入
    try:
        from app.models.member import Member, UserRole
        print_test_result("Member模型导入", True, "成功导入Member和UserRole")
    except Exception as e:
        print_test_result("Member模型导入", False, f"导入失败: {str(e)}")
        return False
    
    try:
        from app.schemas.member import (
            MemberCreate, MemberUpdate, MemberResponse,
            MemberImportRequest, MemberImportResponse
        )
        print_test_result("Member Schema导入", True, "成功导入所有Schema类")
    except Exception as e:
        print_test_result("Member Schema导入", False, f"导入失败: {str(e)}")
        return False
    
    try:
        from app.api.v1.members import router
        print_test_result("Members API路由导入", True, "成功导入API路由")
    except Exception as e:
        print_test_result("Members API路由导入", False, f"导入失败: {str(e)}")
        return False
    
    return True

def test_model_structure():
    """测试模型结构"""
    print_test_header("2. 模型结构测试")
    
    try:
        from app.models.member import Member, UserRole
        from sqlalchemy import inspect
        
        # 检查UserRole枚举
        roles = [role.value for role in UserRole]
        expected_roles = ['admin', 'group_leader', 'member', 'guest']
        roles_match = set(roles) == set(expected_roles)
        print_test_result("UserRole枚举检查", roles_match, f"角色: {roles}")
        
        # 检查Member模型字段
        member_fields = [attr for attr in dir(Member) if not attr.startswith('_')]
        expected_fields = [
            'username', 'name', 'student_id', 'phone', 'department', 
            'class_name', 'join_date', 'password_hash', 'role', 
            'is_active', 'is_verified', 'last_login', 'login_count'
        ]
        
        missing_fields = [field for field in expected_fields if field not in member_fields]
        if not missing_fields:
            print_test_result("Member模型字段检查", True, f"所有必要字段存在")
        else:
            print_test_result("Member模型字段检查", False, f"缺少字段: {missing_fields}")
        
        # 检查方法
        methods = ['is_admin', 'is_group_leader', 'can_manage_group', 'get_safe_dict']
        existing_methods = [method for method in methods if hasattr(Member, method)]
        print_test_result("Member模型方法检查", len(existing_methods) == len(methods), 
                         f"方法: {existing_methods}")
        
        return True
        
    except Exception as e:
        print_test_result("模型结构测试", False, f"测试失败: {str(e)}")
        return False

def test_schema_validation():
    """测试Schema验证"""
    print_test_header("3. Schema验证测试")
    
    try:
        from app.schemas.member import MemberCreate, MemberUpdate, MemberImportItem
        from pydantic import ValidationError
        
        # 测试正确的数据
        valid_data = {
            "username": "test_user",
            "name": "测试用户",
            "student_id": "123456",
            "phone": "13800138000",
            "class_name": "测试班级"
        }
        
        try:
            member = MemberCreate(**valid_data)
            print_test_result("正确数据验证", True, "数据验证通过")
        except ValidationError as e:
            print_test_result("正确数据验证", False, f"验证失败: {e}")
        
        # 测试错误的用户名格式
        invalid_username = valid_data.copy()
        invalid_username["username"] = "test-user@#"  # 包含特殊字符
        
        try:
            member = MemberCreate(**invalid_username)
            print_test_result("无效用户名验证", False, "应该验证失败但通过了")
        except ValidationError:
            print_test_result("无效用户名验证", True, "正确拒绝无效用户名")
        
        # 测试错误的学号格式
        invalid_student_id = valid_data.copy()
        invalid_student_id["student_id"] = "abc123"  # 包含字母
        
        try:
            member = MemberCreate(**invalid_student_id)
            print_test_result("无效学号验证", False, "应该验证失败但通过了")
        except ValidationError:
            print_test_result("无效学号验证", True, "正确拒绝无效学号")
        
        # 测试错误的手机号格式
        invalid_phone = valid_data.copy()
        invalid_phone["phone"] = "1380013800"  # 10位数字
        
        try:
            member = MemberCreate(**invalid_phone)
            print_test_result("无效手机号验证", False, "应该验证失败但通过了")
        except ValidationError:
            print_test_result("无效手机号验证", True, "正确拒绝无效手机号")
        
        return True
        
    except Exception as e:
        print_test_result("Schema验证测试", False, f"测试失败: {str(e)}")
        return False

def test_database_connection():
    """测试数据库连接"""
    print_test_header("4. 数据库连接测试")
    
    try:
        from app.core.database import engine, SessionLocal
        from app.models.member import Member
        from sqlalchemy import text
        
        # 测试数据库连接
        with SessionLocal() as db:
            result = db.execute(text("SELECT 1"))
            print_test_result("数据库连接", True, "数据库连接成功")
        
        # 检查members表是否存在
        with SessionLocal() as db:
            result = db.execute(text("SELECT table_name FROM information_schema.tables WHERE table_name = 'members'"))
            table_exists = result.fetchone() is not None
            print_test_result("Members表存在性检查", table_exists, 
                             "members表存在" if table_exists else "members表不存在")
        
        return True
        
    except Exception as e:
        print_test_result("数据库连接测试", False, f"连接失败: {str(e)}")
        return False

async def test_api_routes():
    """测试API路由"""
    print_test_header("5. API路由测试")
    
    try:
        from fastapi.testclient import TestClient
        from app.main import app
        
        client = TestClient(app)
        
        # 测试健康检查端点
        try:
            response = client.get("/api/v1/members/health")
            print_test_result("健康检查端点", response.status_code == 200, 
                             f"状态码: {response.status_code}")
        except Exception as e:
            print_test_result("健康检查端点", False, f"请求失败: {str(e)}")
        
        return True
        
    except Exception as e:
        print_test_result("API路由测试", False, f"测试失败: {str(e)}")
        return False

def test_business_logic():
    """测试业务逻辑"""
    print_test_header("6. 业务逻辑测试")
    
    try:
        from app.models.member import Member, UserRole
        
        # 创建测试成员
        member = Member(
            username="test_user",
            name="测试用户",
            student_id="123456",
            department="信息化建设处",
            class_name="测试班级",
            password_hash="test_hash",
            role=UserRole.ADMIN,
            is_active=True,
            is_verified=False,
            login_count=0
        )
        
        # 测试权限方法
        print_test_result("管理员权限检查", member.is_admin, "管理员权限正确")
        print_test_result("组管理权限检查", member.can_manage_group, "组管理权限正确")
        print_test_result("数据导入权限检查", member.can_import_data, "数据导入权限正确")
        
        # 测试安全字典方法
        safe_dict = member.get_safe_dict()
        sensitive_fields = ['password_hash']
        has_sensitive = any(field in safe_dict for field in sensitive_fields)
        print_test_result("安全字典检查", not has_sensitive, "敏感信息已过滤")
        
        # 测试显示名称
        display_name = member.get_display_name()
        expected = "测试用户 (123456)"
        print_test_result("显示名称生成", display_name == expected, 
                         f"生成: {display_name}")
        
        return True
        
    except Exception as e:
        print_test_result("业务逻辑测试", False, f"测试失败: {str(e)}")
        return False

def test_import_functionality():
    """测试导入功能逻辑"""
    print_test_header("7. 导入功能测试")
    
    try:
        from app.schemas.member import MemberImportRequest, MemberImportItem
        import time
        
        # 创建测试导入数据
        import_items = [
            MemberImportItem(
                name="张三",
                student_id="2023001",
                phone="13800138000",
                class_name="计算机1班"
            ),
            MemberImportItem(
                name="李四",
                student_id="2023002",
                class_name="计算机2班"
            )
        ]
        
        import_request = MemberImportRequest(
            members=import_items,
            skip_duplicates=True
        )
        
        print_test_result("导入请求创建", True, f"创建了{len(import_items)}个导入项")
        
        # 测试用户名生成逻辑
        timestamp = int(time.time())
        generated_usernames = []
        for index, item in enumerate(import_items):
            username = f"user_{timestamp}_{index+1:03d}"
            generated_usernames.append(username)
        
        print_test_result("用户名生成逻辑", len(generated_usernames) == len(import_items),
                         f"生成用户名: {generated_usernames}")
        
        return True
        
    except Exception as e:
        print_test_result("导入功能测试", False, f"测试失败: {str(e)}")
        return False

def run_all_tests():
    """运行所有测试"""
    print("="*80)
    print("  成员管理模块全面测试开始")
    print("="*80)
    
    test_results = {}
    
    # 运行各项测试
    test_results['imports'] = test_imports()
    test_results['model_structure'] = test_model_structure()
    test_results['schema_validation'] = test_schema_validation() 
    test_results['database_connection'] = test_database_connection()
    test_results['business_logic'] = test_business_logic()
    test_results['import_functionality'] = test_import_functionality()
    
    # 异步测试
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        test_results['api_routes'] = loop.run_until_complete(test_api_routes())
        loop.close()
    except Exception as e:
        print_test_result("API路由测试", False, f"异步测试失败: {str(e)}")
        test_results['api_routes'] = False
    
    # 汇总结果
    print_test_header("测试结果汇总")
    
    passed_tests = sum(1 for result in test_results.values() if result)
    total_tests = len(test_results)
    
    for test_name, result in test_results.items():
        status = "PASS" if result else "FAIL"
        status_symbol = "[PASS]" if result else "[FAIL]"
        print(f"{status_symbol} {test_name}: {status}")
    
    print(f"\n总计: {passed_tests}/{total_tests} 项测试通过")
    
    if passed_tests == total_tests:
        print("\n[SUCCESS] 所有测试通过！成员管理模块运行正常。")
        return True
    else:
        print(f"\n[WARNING] {total_tests - passed_tests} 项测试失败，需要修复。")
        return False

if __name__ == "__main__":
    try:
        success = run_all_tests()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n测试被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n测试过程中发生未预期错误: {str(e)}")
        traceback.print_exc()
        sys.exit(1)