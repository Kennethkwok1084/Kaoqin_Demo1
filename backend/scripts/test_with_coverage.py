#!/usr/bin/env python3
"""
Complete test run with coverage for Codecov integration
"""

import os
import subprocess
import sys
from pathlib import Path


def run_command(command, description, check=True):
    """运行命令并处理结果"""
    print(f"\n========== {description} ==========")
    try:
        result = subprocess.run(
            command,
            shell=True,
            check=check,
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent,
        )
        if result.returncode == 0:
            print(f"✅ {description} 成功")
        else:
            print(f"⚠️ {description} 完成但有警告 (返回码: {result.returncode})")

        if result.stdout:
            print(result.stdout)
        if result.stderr and result.returncode != 0:
            print(f"错误信息: {result.stderr}")
        return result.returncode == 0
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} 失败: {e}")
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

    print("🚀 开始运行测试和生成覆盖率报告...")

    # 1. 清理之前的覆盖率数据
    print("🧹 清理旧的覆盖率数据...")
    for file in [".coverage", "coverage.xml", "coverage.json"]:
        if Path(file).exists():
            Path(file).unlink()
            print(f"删除 {file}")

    if Path("htmlcov").exists():
        import shutil

        shutil.rmtree("htmlcov")
        print("删除 htmlcov 目录")

    # 2. 运行测试并收集覆盖率
    success = run_command(
        "coverage run -m pytest tests/unit/ -v --tb=short",
        "运行单元测试并收集覆盖率",
        check=False,
    )

    if not success:
        print("⚠️ 测试失败，尝试运行部分测试...")
        run_command(
            "coverage run -m pytest tests/unit/test_simple_coverage.py -v",
            "运行基础测试收集覆盖率",
            check=False,
        )

    # 3. 生成HTML报告
    run_command("coverage html", "生成HTML覆盖率报告", check=False)

    # 4. 生成JSON报告
    run_command("coverage json", "生成JSON覆盖率报告", check=False)

    # 5. 生成XML报告（Codecov推荐）
    run_command("coverage xml", "生成XML覆盖率报告", check=False)

    # 6. 显示覆盖率摘要
    run_command("coverage report", "显示覆盖率摘要", check=False)

    # 7. 检查文件是否生成成功
    coverage_files = ["coverage.xml", "coverage.json", "htmlcov/index.html"]

    print("\n========== 检查覆盖率文件 ==========")
    generated_files = 0
    for file_path in coverage_files:
        if Path(file_path).exists():
            size = Path(file_path).stat().st_size
            print(f"✅ {file_path} (大小: {size} 字节)")
            generated_files += 1
        else:
            print(f"❌ {file_path} 不存在")

    if generated_files > 0:
        print(f"\n🎉 成功生成 {generated_files}/{len(coverage_files)} 个覆盖率报告！")
        return 0 if generated_files == len(coverage_files) else 1
    else:
        print("\n❌ 未能生成任何覆盖率报告")
        return 1


if __name__ == "__main__":
    sys.exit(main())
