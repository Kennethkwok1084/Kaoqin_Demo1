#!/usr/bin/env python3
"""
简化的测试运行器，用于快速验证集成测试框架
"""

import subprocess
import sys
from pathlib import Path
import json
from datetime import datetime

def run_simple_tests():
    """运行简化的测试"""
    backend_dir = Path(__file__).parent
    
    # 简单的测试命令，避免复杂的导入
    test_commands = [
        # 基本导入测试
        ["python", "-c", "import pytest; print('pytest导入成功')"],
        ["python", "-c", "import pytest_asyncio; print('pytest-asyncio导入成功')"],
        ["python", "-c", "import sqlalchemy; print('SQLAlchemy导入成功')"],
        ["python", "-c", "import fastapi; print('FastAPI导入成功')"],
        ["python", "-c", "import pandas; print('Pandas导入成功')"],
    ]
    
    print("开始运行简化测试验证...")
    print("=" * 50)
    
    results = []
    
    for i, cmd in enumerate(test_commands, 1):
        print(f"\n[{i}/{len(test_commands)}] 执行: {' '.join(cmd)}")
        
        try:
            result = subprocess.run(
                cmd,
                cwd=backend_dir,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                print(f"成功: {result.stdout.strip()}")
                results.append({"command": " ".join(cmd), "status": "success", "output": result.stdout.strip()})
            else:
                print(f"失败: {result.stderr.strip()}")
                results.append({"command": " ".join(cmd), "status": "failed", "error": result.stderr.strip()})
                
        except subprocess.TimeoutExpired:
            print(f"超时")
            results.append({"command": " ".join(cmd), "status": "timeout"})
        except Exception as e:
            print(f"错误: {e}")
            results.append({"command": " ".join(cmd), "status": "error", "error": str(e)})
    
    # 尝试运行一个简单的pytest测试
    print(f"\n[{len(test_commands)+1}] 尝试运行pytest...")
    
    try:
        # 创建一个简单的测试文件
        simple_test_content = '''
import pytest

def test_basic_math():
    """基础数学测试"""
    assert 1 + 1 == 2
    assert 2 * 3 == 6

def test_string_operations():
    """字符串操作测试"""
    assert "hello".upper() == "HELLO"
    assert len("test") == 4

@pytest.mark.asyncio
async def test_async_function():
    """异步函数测试"""
    async def async_add(a, b):
        return a + b
    
    result = await async_add(2, 3)
    assert result == 5
'''
        
        test_file = backend_dir / "temp_test.py"
        with open(test_file, 'w', encoding='utf-8') as f:
            f.write(simple_test_content)
        
        # 运行简单测试
        pytest_cmd = ["python", "-m", "pytest", str(test_file), "-v"]
        result = subprocess.run(
            pytest_cmd,
            cwd=backend_dir,
            capture_output=True,
            text=True,
            timeout=60
        )
        
        if result.returncode == 0:
            print("pytest基础测试通过")
            results.append({"command": " ".join(pytest_cmd), "status": "success", "output": "基础测试通过"})
        else:
            print(f"pytest测试失败: {result.stderr}")
            results.append({"command": " ".join(pytest_cmd), "status": "failed", "error": result.stderr})
        
        # 清理临时文件
        if test_file.exists():
            test_file.unlink()
            
    except Exception as e:
        print(f"pytest测试出错: {e}")
        results.append({"command": "pytest简单测试", "status": "error", "error": str(e)})
    
    # 生成报告
    print("\n" + "=" * 50)
    print("测试验证结果汇总")
    print("=" * 50)
    
    success_count = sum(1 for r in results if r["status"] == "success")
    total_count = len(results)
    success_rate = (success_count / total_count * 100) if total_count > 0 else 0
    
    print(f"成功: {success_count}")
    print(f"失败: {total_count - success_count}")
    print(f"成功率: {success_rate:.1f}%")
    
    # 保存结果
    report = {
        "timestamp": datetime.now().isoformat(),
        "total_tests": total_count,
        "successful_tests": success_count,
        "success_rate": success_rate,
        "results": results
    }
    
    reports_dir = backend_dir / "tests" / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    
    report_file = reports_dir / "simple_test_verification.json"
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    print(f"\n详细报告已保存到: {report_file}")
    
    return success_rate >= 80  # 80%以上认为验证成功

if __name__ == "__main__":
    success = run_simple_tests()
    sys.exit(0 if success else 1)