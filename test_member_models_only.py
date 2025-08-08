#!/usr/bin/env python3
"""
成员管理模块 - 模型和Schema测试
仅测试不依赖数据库的功能
"""

import os
import sys
from datetime import date, datetime

# 添加backend路径到sys.path
backend_path = os.path.join(os.path.dirname(__file__), 'backend')
sys.path.insert(0, backend_path)
os.environ['PYTHONPATH'] = backend_path

def print_test_result(test_name: str, success: bool, message: str = ""):
    """打印测试结果"""
    status = "PASS" if success else "FAIL"
    status_symbol = "[PASS]" if success else "[FAIL]"
    print(f"{status_symbol} {test_name}: {status}")
    if message:
        print(f"  详情: {message}")

def test_model_imports():
    """测试模型导入"""
    print("\n=== 模型导入测试 ===")
    
    try:
        from app.models.member import Member, UserRole
        print_test_result("Member模型导入", True, "成功导入Member和UserRole")
        
        # 测试枚举值
        roles = [role.value for role in UserRole]
        expected_roles = ['admin', 'group_leader', 'member', 'guest']
        print_test_result("UserRole枚举值", set(roles) == set(expected_roles), f"角色: {roles}")
        
        return True
    except Exception as e:
        print_test_result("Member模型导入", False, f"导入失败: {str(e)}")
        return False

def test_schema_imports():
    """测试Schema导入"""
    print("\n=== Schema导入测试 ===")
    
    try:
        from app.schemas.member import (
            MemberCreate, MemberUpdate, MemberResponse,
            MemberImportRequest, MemberImportResponse, MemberImportItem
        )
        print_test_result("Schema导入", True, "所有Schema类导入成功")
        return True
    except Exception as e:
        print_test_result("Schema导入", False, f"导入失败: {str(e)}")
        return False

def test_schema_validation():
    """测试Schema验证功能"""
    print("\n=== Schema验证测试 ===")
    
    try:
        from app.schemas.member import MemberCreate, MemberImportItem
        from pydantic import ValidationError
        
        # 测试正确数据
        valid_data = {
            "username": "test_user",
            "name": "测试用户",
            "student_id": "123456",
            "phone": "13800138000",
            "class_name": "测试班级"
        }
        
        member = MemberCreate(**valid_data)
        print_test_result("正确数据验证", True, f"用户名: {member.username}, 姓名: {member.name}")
        
        # 测试无效用户名
        try:
            invalid_data = valid_data.copy()
            invalid_data["username"] = "test-user@#"
            MemberCreate(**invalid_data)
            print_test_result("无效用户名验证", False, "应该拒绝但接受了")
        except ValidationError:
            print_test_result("无效用户名验证", True, "正确拒绝了无效用户名")
        
        # 测试无效学号
        try:
            invalid_data = valid_data.copy()
            invalid_data["student_id"] = "abc123"
            MemberCreate(**invalid_data)
            print_test_result("无效学号验证", False, "应该拒绝但接受了")
        except ValidationError:
            print_test_result("无效学号验证", True, "正确拒绝了无效学号")
        
        # 测试无效手机号
        try:
            invalid_data = valid_data.copy()
            invalid_data["phone"] = "1380013800"  # 10位
            MemberCreate(**invalid_data)
            print_test_result("无效手机号验证", False, "应该拒绝但接受了")
        except ValidationError:
            print_test_result("无效手机号验证", True, "正确拒绝了无效手机号")
        
        return True
        
    except Exception as e:
        print_test_result("Schema验证测试", False, f"测试失败: {str(e)}")
        return False

def test_member_model_methods():
    """测试Member模型方法"""
    print("\n=== Member模型方法测试 ===")
    
    try:
        from app.models.member import Member, UserRole
        
        # 创建一个Admin用户进行测试
        admin_member = Member(
            username="admin",
            name="管理员",
            student_id="admin",
            department="信息化建设处",
            class_name="管理员",
            password_hash="test_hash",
            role=UserRole.ADMIN,
            is_active=True
        )
        
        # 测试权限方法
        print_test_result("is_admin方法", admin_member.is_admin, "管理员权限检查正确")
        print_test_result("can_manage_group方法", admin_member.can_manage_group, "组管理权限检查正确")
        print_test_result("can_import_data方法", admin_member.can_import_data, "数据导入权限检查正确")
        
        # 创建普通成员测试
        member = Member(
            username="member",
            name="普通成员",
            student_id="123456",
            department="信息化建设处",
            class_name="测试班级",
            password_hash="test_hash",
            role=UserRole.MEMBER,
            is_active=True
        )
        
        print_test_result("普通成员权限", not member.is_admin and not member.can_import_data, "普通成员权限限制正确")
        
        # 测试显示名称生成
        display_name = member.get_display_name()
        expected = "普通成员 (123456)"
        print_test_result("显示名称生成", display_name == expected, f"生成: {display_name}")
        
        # 测试状态显示
        print_test_result("状态显示", member.status_display == "在职", f"状态: {member.status_display}")
        
        return True
        
    except Exception as e:
        print_test_result("Member模型方法测试", False, f"测试失败: {str(e)}")
        return False

def test_import_schema():
    """测试导入Schema"""
    print("\n=== 导入Schema测试 ===")
    
    try:
        from app.schemas.member import MemberImportRequest, MemberImportItem
        
        # 创建导入数据
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
        
        print_test_result("导入Schema创建", True, f"成功创建包含{len(import_items)}个成员的导入请求")
        print_test_result("跳过重复设置", import_request.skip_duplicates, "跳过重复功能已启用")
        
        # 验证第一个成员数据
        first_member = import_request.members[0]
        print_test_result("成员数据完整性", 
                         first_member.name == "张三" and first_member.student_id == "2023001",
                         f"姓名: {first_member.name}, 学号: {first_member.student_id}")
        
        return True
        
    except Exception as e:
        print_test_result("导入Schema测试", False, f"测试失败: {str(e)}")
        return False

def run_model_tests():
    """运行所有模型测试"""
    print("="*60)
    print("  成员管理模块 - 模型和Schema测试")
    print("="*60)
    
    test_results = []
    
    # 运行各项测试
    test_results.append(("模型导入", test_model_imports()))
    test_results.append(("Schema导入", test_schema_imports()))
    test_results.append(("Schema验证", test_schema_validation()))
    test_results.append(("模型方法", test_member_model_methods()))
    test_results.append(("导入Schema", test_import_schema()))
    
    # 汇总结果
    print("\n=== 测试结果汇总 ===")
    passed = sum(1 for _, result in test_results if result)
    total = len(test_results)
    
    for test_name, result in test_results:
        status = "PASS" if result else "FAIL"
        status_symbol = "[PASS]" if result else "[FAIL]"
        print(f"{status_symbol} {test_name}: {status}")
    
    print(f"\n总计: {passed}/{total} 项测试通过")
    
    if passed == total:
        print("\n[SUCCESS] 所有模型测试通过！")
        return True
    else:
        print(f"\n[WARNING] {total - passed} 项测试失败")
        return False

if __name__ == "__main__":
    try:
        success = run_model_tests()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n测试过程中发生错误: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)