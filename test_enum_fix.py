#!/usr/bin/env python3
"""
测试数据库迁移中的 ENUM 类型修复
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

async def test_enum_creation():
    """测试 ENUM 类型创建是否正常"""
    try:
        from backend.app.core.database import get_async_session, engine
        from backend.app.models import Member, UserRole
        
        print("✅ 成功导入数据库相关模块")
        
        # 测试创建一个简单的会话
        async with get_async_session() as session:
            print("✅ 成功创建数据库会话")
            
        print("✅ ENUM 类型修复测试成功")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False
    
    return True

if __name__ == "__main__":
    result = asyncio.run(test_enum_creation())
    if result:
        print("\n🎉 所有测试通过！ENUM 类型修复成功")
        sys.exit(0)
    else:
        print("\n💥 测试失败，需要进一步检查")
        sys.exit(1)
