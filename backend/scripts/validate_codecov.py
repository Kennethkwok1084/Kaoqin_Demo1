#!/usr/bin/env python3
"""
Codecov配置验证脚本
用于验证Codecov集成是否正确配置
"""

import json
import os
import subprocess
import sys
from pathlib import Path

import yaml


def validate_codecov_config():
    """验证Codecov配置文件"""
    print("🔍 验证Codecov配置...")

    # 检查codecov.yml文件
    codecov_yml = Path(__file__).parent.parent.parent / "codecov.yml"
    if not codecov_yml.exists():
        print("❌ codecov.yml文件不存在")
        return False

    # 解析YAML配置
    try:
        with open(codecov_yml, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
        print("✅ codecov.yml文件格式正确")
    except yaml.YAMLError as e:
        print(f"❌ codecov.yml格式错误: {e}")
        return False

    # 检查token配置
    if "codecov" in config and "token" in config["codecov"]:
        token = config["codecov"]["token"]
        print(f"✅ Codecov token已配置: {token[:8]}...{token[-8:]}")
    else:
        print("❌ 未找到Codecov token")
        return False

    # 检查覆盖率配置
    if "coverage" in config:
        coverage_config = config["coverage"]
        if "status" in coverage_config:
            project_target = coverage_config["status"]["project"]["default"]["target"]
            patch_target = coverage_config["status"]["patch"]["default"]["target"]
            print(f"✅ 覆盖率目标配置: 项目={project_target}, 补丁={patch_target}")
        else:
            print("❌ 未找到覆盖率状态配置")
            return False
    else:
        print("❌ 未找到覆盖率配置")
        return False

    return True


def check_coverage_files():
    """检查覆盖率文件是否存在"""
    print("\n🔍 检查覆盖率文件...")

    backend_dir = Path(__file__).parent.parent
    coverage_files = {
        "coverage.xml": backend_dir / "coverage.xml",
        "coverage.json": backend_dir / "coverage.json",
        "htmlcov": backend_dir / "htmlcov",
    }

    all_exists = True
    for name, path in coverage_files.items():
        if path.exists():
            if path.is_file():
                size = path.stat().st_size
                print(f"✅ {name} 存在 ({size:,} bytes)")
            else:
                print(f"✅ {name} 目录存在")
        else:
            print(f"❌ {name} 不存在")
            all_exists = False

    return all_exists


def get_coverage_summary():
    """获取覆盖率摘要"""
    print("\n📊 覆盖率摘要:")

    backend_dir = Path(__file__).parent.parent
    coverage_json = backend_dir / "coverage.json"

    if not coverage_json.exists():
        print("❌ coverage.json文件不存在")
        return False

    try:
        with open(coverage_json, "r") as f:
            data = json.load(f)

        totals = data["totals"]
        print(f"  总体覆盖率: {totals['percent_covered']:.2f}%")
        print(f"  总代码行数: {totals['num_statements']:,}")
        print(f"  已覆盖行数: {totals['covered_lines']:,}")
        print(f"  未覆盖行数: {totals['missing_lines']:,}")
        print(
            f"  分支覆盖率: {totals['covered_branches']}/{totals['num_branches']} ({totals['covered_branches']/totals['num_branches']*100:.1f}%)"
        )

        return True
    except Exception as e:
        print(f"❌ 读取coverage.json失败: {e}")
        return False


def simulate_codecov_upload():
    """模拟Codecov上传"""
    print("\n🚀 模拟Codecov上传...")

    backend_dir = Path(__file__).parent.parent
    coverage_xml = backend_dir / "coverage.xml"

    if not coverage_xml.exists():
        print("❌ coverage.xml文件不存在，无法模拟上传")
        return False

    # 检查是否安装了codecov
    try:
        result = subprocess.run(
            ["codecov", "--version"], capture_output=True, text=True, cwd=backend_dir
        )
        if result.returncode == 0:
            print("✅ codecov CLI已安装")
        else:
            print("ℹ️ codecov CLI未安装，但这在CI/CD中会自动处理")
    except FileNotFoundError:
        print("ℹ️ codecov CLI未安装，但这在CI/CD中会自动处理")

    # 模拟上传命令
    upload_command = f"codecov -f {coverage_xml}"
    print(f"📤 上传命令: {upload_command}")
    print("ℹ️ 在CI/CD管道中，这个命令会自动执行并上传覆盖率数据到Codecov")

    return True


def main():
    """主函数"""
    print("🎯 Codecov集成验证")
    print("=" * 50)

    success = True

    # 验证配置文件
    if not validate_codecov_config():
        success = False

    # 检查覆盖率文件
    if not check_coverage_files():
        success = False

    # 获取覆盖率摘要
    if not get_coverage_summary():
        success = False

    # 模拟上传
    if not simulate_codecov_upload():
        success = False

    print("\n" + "=" * 50)
    if success:
        print("🎉 Codecov集成验证成功！")
        print("\n下一步:")
        print("1. 将代码推送到GitHub")
        print("2. 在GitHub repository的Settings > Secrets中添加CODECOV_TOKEN")
        print("3. CI/CD管道会自动运行测试并上传覆盖率到Codecov")
        print("4. 在Codecov.io查看覆盖率报告")
        return True
    else:
        print("❌ Codecov集成验证失败，请检查上述错误")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
