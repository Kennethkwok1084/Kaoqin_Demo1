#!/usr/bin/env python3

"""
调试pytest测试发现问题的脚本
"""

import os
import sys
import subprocess
import traceback
from pathlib import Path

def main():
    print("调试pytest测试发现问题")
    print("=" * 50)
    
    # 1. 检查基本环境
    print("1. 基本环境检查:")
    print(f"   当前目录: {os.getcwd()}")
    print(f"   Python版本: {sys.version}")
    
    # 2. 检查文件结构
    print("\n2. 检查测试文件结构:")
    tests_dir = Path("tests")
    if tests_dir.exists():
        print(f"   ✅ tests/ 目录存在")
        
        # 检查integration目录
        integration_dir = tests_dir / "integration"
        if integration_dir.exists():
            print(f"   OK tests/integration/ 目录存在")
            
            # 列出所有测试文件
            test_files = list(integration_dir.glob("test_*.py"))
            print(f"   找到 {len(test_files)} 个测试文件:")
            for f in test_files:
                print(f"      - {f.name}")
        else:
            print(f"   ERROR tests/integration/ 目录不存在")
    else:
        print(f"   ❌ tests/ 目录不存在")
    
    # 3. 检查pytest配置
    print("\n3. 检查pytest配置:")
    pytest_ini = Path("pytest.ini")
    if pytest_ini.exists():
        print(f"   ✅ pytest.ini 存在")
        try:
            with open(pytest_ini, 'r', encoding='utf-8') as f:
                content = f.read()
                if "[pytest]" in content:
                    print(f"   ✅ pytest.ini 格式正确")
                else:
                    print(f"   ❌ pytest.ini 缺少 [pytest] 节")
        except Exception as e:
            print(f"   ❌ 读取pytest.ini失败: {e}")
    else:
        print(f"   ⚠️  pytest.ini 不存在")
    
    # 4. 检查应用导入
    print("\n4. 检查应用导入:")
    try:
        # 添加当前目录到Python路径
        current_dir = Path.cwd()
        if str(current_dir) not in sys.path:
            sys.path.insert(0, str(current_dir))
        
        import app.main
        print("   ✅ app.main 导入成功")
        
        import app.models
        print("   ✅ app.models 导入成功")
        
        import app.core.database
        print("   ✅ app.core.database 导入成功")
        
    except ImportError as e:
        print(f"   ❌ 导入失败: {e}")
        traceback.print_exc()
    
    # 5. 检查pytest导入
    print("\n5. 检查测试依赖:")
    try:
        import pytest
        print(f"   ✅ pytest 导入成功, 版本: {pytest.__version__}")
        
        import pytest_asyncio
        print(f"   ✅ pytest_asyncio 导入成功")
        
    except ImportError as e:
        print(f"   ❌ 测试依赖导入失败: {e}")
    
    # 6. 尝试pytest collect
    print("\n6. 测试pytest收集:")
    try:
        # 使用subprocess避免导入问题
        result = subprocess.run(
            [sys.executable, "-m", "pytest", "--collect-only", "-q", "tests/integration/"],
            capture_output=True,
            text=True,
            cwd=Path.cwd(),
            timeout=30
        )
        
        print(f"   退出码: {result.returncode}")
        
        if result.stdout:
            print("   标准输出:")
            for line in result.stdout.split('\n')[:10]:  # 只显示前10行
                if line.strip():
                    print(f"      {line}")
        
        if result.stderr:
            print("   错误输出:")
            for line in result.stderr.split('\n')[:10]:  # 只显示前10行
                if line.strip():
                    print(f"      {line}")
                    
        # 解释退出码
        if result.returncode == 0:
            print("   ✅ 测试收集成功")
        elif result.returncode == 4:
            print("   ❌ 配置错误或使用错误")
        elif result.returncode == 5:
            print("   ⚠️  没有找到测试")
        else:
            print(f"   ❌ 其他错误 (代码 {result.returncode})")
            
    except subprocess.TimeoutExpired:
        print("   ⏰ pytest收集超时")
    except Exception as e:
        print(f"   ❌ pytest收集异常: {e}")
    
    # 7. 尝试运行单个测试文件
    print("\n7. 尝试单个测试文件:")
    test_file = Path("tests/integration/test_database.py")
    if test_file.exists():
        try:
            result = subprocess.run(
                [sys.executable, "-m", "pytest", str(test_file), "--collect-only", "-v"],
                capture_output=True,
                text=True,
                timeout=20
            )
            print(f"   单文件收集退出码: {result.returncode}")
            
            if result.returncode == 0:
                print("   ✅ 单个文件测试收集成功")
            else:
                print("   ❌ 单个文件测试收集失败")
                if result.stderr:
                    print("   错误信息:")
                    for line in result.stderr.split('\n')[:5]:
                        if line.strip():
                            print(f"      {line}")
        except Exception as e:
            print(f"   ❌ 单文件测试异常: {e}")
    else:
        print(f"   ❌ 测试文件不存在: {test_file}")
    
    print("\n" + "=" * 50)
    print("🎯 调试完成")

if __name__ == "__main__":
    main()