#!/usr/bin/env python3
"""
简化的导入匹配分析脚本
分析数据库成员的匹配键格式，帮助理解为什么Excel导入时名字匹配不上
"""

import asyncio
import os
import sys
from typing import Dict, List, Optional

# 添加项目路径
project_root = os.path.dirname(os.path.abspath(__file__))
backend_path = os.path.join(project_root, 'backend')
sys.path.insert(0, backend_path)

try:
    from app.core.database import get_db
    from app.models.member import Member
    from sqlalchemy import select
except ImportError as e:
    print(f"导入错误: {e}")
    print("请确保在项目根目录运行此脚本")
    sys.exit(1)


def create_match_key(name: str, contact: str) -> str:
    """创建用于匹配的键（与import_service.py中的逻辑完全一致）"""
    if not name or not contact:
        return ""
    
    # 标准化姓名（去除空格和特殊字符）
    clean_name = "".join(name.split())
    
    # 标准化联系方式（只保留数字）
    clean_contact = "".join(filter(str.isdigit, contact))
    
    return f"{clean_name}:{clean_contact}"


async def analyze_database_members():
    """分析数据库中成员的匹配键格式"""
    print("🔍 分析数据库成员匹配键格式")
    print("=" * 80)
    
    try:
        async for db in get_db():
            # 获取所有活跃成员
            member_query = select(Member).where(Member.is_active.is_(True))
            member_result = await db.execute(member_query)
            members = member_result.scalars().all()
            
            print(f"✅ 找到 {len(members)} 个活跃成员")
            print()
            
            # 分析匹配键格式
            match_keys = {}
            members_without_phone = []
            members_with_issues = []
            
            for member in members:
                if not member.name:
                    members_with_issues.append(f"成员ID {member.id}: 缺少姓名")
                    continue
                
                phone = getattr(member, 'phone', None)
                if not phone:
                    members_without_phone.append(f"{member.name} (ID: {member.id})")
                    continue
                
                match_key = create_match_key(member.name, phone)
                if match_key:
                    match_keys[match_key] = member
                else:
                    members_with_issues.append(f"{member.name} (ID: {member.id}): 无法生成匹配键")
            
            print(f"📊 统计信息:")
            print(f"  - 有效匹配键: {len(match_keys)} 个")
            print(f"  - 缺少电话号码: {len(members_without_phone)} 个")
            print(f"  - 其他问题: {len(members_with_issues)} 个")
            print()
            
            # 显示匹配键示例
            print("📋 匹配键示例 (姓名:电话号码):")
            for i, (key, member) in enumerate(list(match_keys.items())[:10]):
                print(f"  {i+1}. {key} -> {member.name} ({member.phone})")
            
            if len(match_keys) > 10:
                print(f"  ... 还有 {len(match_keys) - 10} 个")
            print()
            
            # 显示问题成员
            if members_without_phone:
                print("⚠️  缺少电话号码的成员:")
                for member_info in members_without_phone[:10]:
                    print(f"  - {member_info}")
                if len(members_without_phone) > 10:
                    print(f"  ... 还有 {len(members_without_phone) - 10} 个")
                print()
            
            if members_with_issues:
                print("❌ 有问题的成员:")
                for issue in members_with_issues[:10]:
                    print(f"  - {issue}")
                if len(members_with_issues) > 10:
                    print(f"  ... 还有 {len(members_with_issues) - 10} 个")
                print()
            
            # 分析电话号码格式
            print("📱 电话号码格式分析:")
            phone_patterns = {}
            for key, member in match_keys.items():
                _, clean_contact = key.split(":")
                length = len(clean_contact)
                phone_patterns[length] = phone_patterns.get(length, 0) + 1
            
            for length, count in sorted(phone_patterns.items()):
                print(f"  - {length} 位数字: {count} 个")
            print()
            
            # 提供Excel导入建议
            print("💡 Excel导入建议:")
            print("  1. 确保Excel文件中有包含以下关键词的列名:")
            print("     姓名列: '姓名', '报告人', '申请人', '报修人', '联系人'")
            print("     电话列: '联系方式', '电话', '手机', '联系电话', '手机号'")
            print()
            print("  2. 确保Excel中的姓名和电话号码格式与数据库一致:")
            print("     - 姓名应该完全匹配（不含多余空格）")
            print("     - 电话号码应该是纯数字格式")
            print()
            print("  3. 常见匹配失败原因:")
            print("     - Excel列名不包含识别关键词")
            print("     - 姓名中包含额外的空格或特殊字符")
            print("     - 电话号码格式不一致（如包含连字符、空格等）")
            print("     - 数据库中成员缺少电话号码")
            
            break
            
    except Exception as e:
        print(f"❌ 分析失败: {e}")
        import traceback
        traceback.print_exc()


def test_match_key_generation():
    """测试匹配键生成"""
    print("\n🧪 测试匹配键生成:")
    print("-" * 40)
    
    test_cases = [
        ("张三", "13812345678"),
        ("李 四", "138-1234-5678"),
        ("王五", "138 1234 5678"),
        ("赵六", "+86 13812345678"),
        ("钱七", "13812345678 "),
        ("  孙八  ", "  13812345678  "),
    ]
    
    for name, phone in test_cases:
        match_key = create_match_key(name, phone)
        print(f"  '{name}' + '{phone}' -> '{match_key}'")


async def main():
    """主函数"""
    await analyze_database_members()
    test_match_key_generation()
    
    print("\n" + "=" * 80)
    print("如果您有具体的Excel文件，请提供文件路径或文件内容示例，")
    print("我可以帮您分析具体的匹配失败原因。")


if __name__ == "__main__":
    asyncio.run(main())
