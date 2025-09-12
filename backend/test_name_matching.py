#!/usr/bin/env python3
"""测试名字匹配功能"""

import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.ab_table_matching_service import ABTableMatchingService


def test_name_cleaning():
    """测试名字清理功能"""
    service = ABTableMatchingService(None)
    
    test_cases = [
        ("郑泰跃(信息处)", "郑泰跃"),
        ("张三（财务部）", "张三"),
        ("李四", "李四"),
        ("王五 (技术部)", "王五"),
    ]
    
    print("测试名字清理功能：")
    for input_name, expected in test_cases:
        cleaned = service._clean_name(input_name)
        status = "✓" if cleaned == expected.lower() else "✗"
        print(f"  {status} 输入: '{input_name}' -> 清理后: '{cleaned}' (期望: '{expected.lower()}')")


def test_name_extraction():
    """测试从记录中提取名字"""
    service = ABTableMatchingService(None)
    
    test_records = [
        {"处理人": "郑泰跃(信息处)"},
        {"处理人员": "张三（财务部）"},
        {"维修人员": "李四"},
        {"姓名": "王五"},
        {"name": "赵六"},
    ]
    
    print("\n测试名字提取功能：")
    for record in test_records:
        extracted = service._extract_name(record)
        print(f"  记录: {record} -> 提取: '{extracted}'")


def test_name_similarity():
    """测试名字相似度计算"""
    service = ABTableMatchingService(None)
    
    test_pairs = [
        ("郑泰跃", "郑泰跃", 1.0),
        ("张三", "张三丰", 0.75),
        ("李四", "李五", 0.5),
        ("王", "王小明", 0.75),
    ]
    
    print("\n测试名字相似度计算：")
    for name1, name2, expected_min in test_pairs:
        clean1 = service._clean_name(name1)
        clean2 = service._clean_name(name2)
        score = service._name_similarity_score(clean1, clean2)
        status = "✓" if score >= expected_min else "✗"
        print(f"  {status} '{name1}' vs '{name2}': {score:.2f} (期望最小值: {expected_min})")


async def test_member_matching():
    """测试成员匹配（需要数据库连接）"""
    print("\n测试成员匹配功能：")
    print("  注意：此测试需要数据库连接，如果没有配置数据库将跳过")
    
    try:
        from app.core.database import get_db
        from sqlalchemy.ext.asyncio import AsyncSession
        
        # 这里需要实际的数据库连接
        # 由于是测试脚本，这部分可能需要根据实际情况调整
        print("  跳过数据库相关测试...")
    except Exception as e:
        print(f"  跳过数据库测试: {e}")


if __name__ == "__main__":
    print("=" * 60)
    print("名字匹配功能测试")
    print("=" * 60)
    
    test_name_cleaning()
    test_name_extraction()
    test_name_similarity()
    
    # 运行异步测试
    asyncio.run(test_member_matching())
    
    print("\n测试完成！")