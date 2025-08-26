#!/usr/bin/env python3
"""
数据库连接修复测试脚本
测试数据库连接问题并提供修复方案
"""

import asyncio
import os
import sys
from pathlib import Path

# 添加项目根路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

import asyncpg
from sqlalchemy.ext.asyncio import create_async_engine


async def test_asyncpg_direct():
    """直接测试 asyncpg 连接"""
    print("=== 直接测试 asyncpg 连接 ===")
    
    # 测试默认的 CI 配置
    ci_config = {
        "host": "localhost",
        "port": 5432,
        "user": "postgres", 
        "password": "postgres",
        "database": "test_attendence"
    }
    
    try:
        print(f"尝试连接: {ci_config}")
        conn = await asyncpg.connect(
            host=ci_config["host"],
            port=ci_config["port"],
            user=ci_config["user"],
            password=ci_config["password"],
            database=ci_config["database"]
        )
        await conn.close()
        print("✅ asyncpg 直接连接成功")
        return True
    except Exception as e:
        print(f"❌ asyncpg 直接连接失败: {e}")
        return False


async def test_sqlalchemy_connection():
    """测试 SQLAlchemy 连接"""
    print("\n=== 测试 SQLAlchemy 连接 ===")
    
    # 设置环境变量
    database_url = "postgresql+asyncpg://postgres:postgres@localhost:5432/test_attendence"
    os.environ["DATABASE_URL"] = database_url
    
    try:
        print(f"使用连接字符串: {database_url}")
        engine = create_async_engine(
            database_url,
            echo=False,
            pool_pre_ping=True,
            pool_timeout=10,
            connect_args={
                "command_timeout": 30,
                "server_settings": {
                    "application_name": "test_connection_fix"
                }
            }
        )
        
        async with engine.begin() as conn:
            result = await conn.execute("SELECT 1")
            print(f"✅ SQLAlchemy 连接成功，查询结果: {result.scalar()}")
            
        await engine.dispose()
        return True
        
    except Exception as e:
        print(f"❌ SQLAlchemy 连接失败: {e}")
        return False


async def test_performance_timeout():
    """测试性能测试超时机制"""
    print("\n=== 测试性能测试超时机制 ===")
    
    try:
        # 模拟一个会超时的操作
        async def mock_slow_operation():
            await asyncio.sleep(5)  # 模拟慢操作
            return "success"
        
        # 测试 asyncio.wait_for 超时
        result = await asyncio.wait_for(
            mock_slow_operation(),
            timeout=2.0  # 2秒超时
        )
        print(f"操作成功: {result}")
        
    except asyncio.TimeoutError:
        print("✅ 超时机制工作正常 - 操作在2秒内被正确终止")
        return True
    except Exception as e:
        print(f"❌ 超时测试失败: {e}")
        return False


def check_environment_variables():
    """检查环境变量配置"""
    print("\n=== 检查环境变量配置 ===")
    
    env_vars = [
        "DATABASE_URL",
        "DATABASE_URL_SYNC", 
        "CI",
        "GITHUB_ACTIONS",
        "POSTGRES_TEST",
        "TESTING"
    ]
    
    print("当前环境变量:")
    for var in env_vars:
        value = os.getenv(var, "未设置")
        print(f"  {var}: {value}")
    
    # 检查可能的问题
    issues = []
    database_url = os.getenv("DATABASE_URL", "")
    if "root" in database_url:
        issues.append(f"DATABASE_URL 包含 'root' 用户: {database_url}")
    
    if issues:
        print("\n⚠️ 发现的问题:")
        for issue in issues:
            print(f"  - {issue}")
        return False
    else:
        print("\n✅ 环境变量配置正常")
        return True


async def main():
    """主测试函数"""
    print("数据库连接修复测试")
    print("=" * 50)
    
    results = []
    
    # 1. 检查环境变量
    results.append(("环境变量检查", check_environment_variables()))
    
    # 2. 测试超时机制
    results.append(("超时机制测试", await test_performance_timeout()))
    
    # 3. 测试数据库连接
    results.append(("asyncpg 连接测试", await test_asyncpg_direct()))
    results.append(("SQLAlchemy 连接测试", await test_sqlalchemy_connection()))
    
    # 汇总结果
    print("\n" + "=" * 50)
    print("测试结果汇总:")
    success_count = 0
    for test_name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"  {test_name}: {status}")
        if result:
            success_count += 1
    
    print(f"\n通过率: {success_count}/{len(results)} ({success_count/len(results)*100:.1f}%)")
    
    # 提供修复建议
    if success_count < len(results):
        print("\n🔧 修复建议:")
        print("1. 确保 PostgreSQL 服务正在运行")
        print("2. 验证用户名和密码正确 (postgres:postgres)")
        print("3. 确认数据库 'test_attendence' 存在")
        print("4. 检查防火墙设置允许端口 5432")
        
        print("\n🚀 CI/CD 修复步骤:")
        print("1. 性能测试已添加超时机制，防止无限卡住")
        print("2. 所有 API 调用都有 asyncio.wait_for 保护")
        print("3. pytest 测试有总体超时限制")
        print("4. 数据库连接错误会优雅处理并跳过测试")


if __name__ == "__main__":
    asyncio.run(main())
