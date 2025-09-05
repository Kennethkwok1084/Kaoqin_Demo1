#!/usr/bin/env python3
"""
Coverage report generation script for Codecov integration
"""

import os
import subprocess
import sys
from pathlib import Path


def run_command(command, description):
    """运行命令并处理结果"""
    print(f"\n========== {description} ==========")
    try:
        result = subprocess.run(
            command, shell=True, check=True, capture_output=True, text=True
        )
        print(f"✅ {description} 成功")
        if result.stdout:
            print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"⚠️ {description} 失败: {e}")
        if e.stdout:
            print(f"stdout: {e.stdout}")
        if e.stderr:
            print(f"stderr: {e.stderr}")
        return False


def main():
    """主函数"""
    # 确保在backend目录
    backend_dir = Path(__file__).parent
    os.chdir(backend_dir)

    print("🎯 开始生成覆盖率报告...")

    # 1. 生成HTML报告
    run_command("coverage html", "生成HTML覆盖率报告")

    # 2. 生成JSON报告
    run_command("coverage json", "生成JSON覆盖率报告")

    # 3. 生成XML报告（Codecov推荐）
    run_command("coverage xml", "生成XML覆盖率报告")

    # 4. 显示覆盖率摘要
    run_command("coverage report --show-missing", "显示覆盖率摘要")

    # 5. 检查文件是否生成成功
    coverage_files = ["coverage.xml", "coverage.json", "htmlcov/index.html"]

    print("\n========== 检查覆盖率文件 ==========")
    all_files_exist = True
    for file_path in coverage_files:
        if Path(file_path).exists():
            size = Path(file_path).stat().st_size
            print(f"✅ {file_path} (大小: {size} 字节)")
        else:
            print(f"❌ {file_path} 不存在")
            all_files_exist = False

    if all_files_exist:
        print("\n🎉 所有覆盖率报告生成成功！")
        return 0
    else:
        print("\n⚠️ 部分覆盖率报告生成失败")
        return 1


if __name__ == "__main__":
    sys.exit(main())
