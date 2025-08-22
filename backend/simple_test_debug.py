#!/usr/bin/env python3

"""
简单的pytest测试发现调试脚本
"""

import os
import subprocess
import sys
from pathlib import Path


def main():
    print("pytest测试发现问题调试")
    print("=" * 40)

    # 检查基本信息
    print(f"当前目录: {os.getcwd()}")
    print(f"Python版本: {sys.version_info[:2]}")

    # 检查测试文件
    tests_dir = Path("tests/integration")
    if tests_dir.exists():
        test_files = list(tests_dir.glob("test_*.py"))
        print(f"发现 {len(test_files)} 个测试文件")
        for f in test_files[:3]:  # 只显示前3个
            print(f"  - {f.name}")
    else:
        print("tests/integration目录不存在")

    # 检查pytest配置
    pytest_ini = Path("pytest.ini")
    if pytest_ini.exists():
        print("pytest.ini存在")
    else:
        print("pytest.ini不存在")

    # 尝试导入关键模块
    print("\n导入测试:")
    try:
        sys.path.insert(0, str(Path.cwd()))

        print("  app.main: OK")
    except Exception as e:
        print(f"  app.main: ERROR - {e}")

    try:
        import pytest

        print(f"  pytest: OK - 版本 {pytest.__version__}")
    except Exception as e:
        print(f"  pytest: ERROR - {e}")

    # 测试pytest收集
    print("\npytest收集测试:")
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pytest", "--collect-only", "-q"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        print(f"退出码: {result.returncode}")

        if result.returncode == 4:
            print("ERROR: pytest配置错误")
        elif result.returncode == 5:
            print("WARNING: 没有找到测试")
        elif result.returncode == 0:
            print("SUCCESS: 测试收集成功")

        # 显示错误信息（如果有）
        if result.stderr:
            print("错误输出:")
            for line in result.stderr.split("\n")[:5]:
                if line.strip():
                    print(f"  {line}")
    except Exception as e:
        print(f"pytest运行失败: {e}")


if __name__ == "__main__":
    main()
