#!/usr/bin/env python3
"""
Codecov integration test script
测试 Codecov 集成是否正常工作
"""

import json
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
            print(result.stdout.strip()[:500])  # 限制输出长度
        return True
    except subprocess.CalledProcessError as e:
        print(f"⚠️ {description} 失败: {e}")
        if e.stdout:
            print(f"stdout: {e.stdout.strip()[:300]}")
        if e.stderr:
            print(f"stderr: {e.stderr.strip()[:300]}")
        return False


def check_coverage_files():
    """检查覆盖率文件是否存在且有效"""
    print("\n========== 检查覆盖率文件 ==========")

    files_to_check = [
        ("coverage.xml", "XML覆盖率报告（Codecov推荐）"),
        ("coverage.json", "JSON覆盖率报告"),
        ("htmlcov/index.html", "HTML覆盖率报告"),
        (".coverage", "Coverage数据文件"),
    ]

    all_good = True
    for file_path, description in files_to_check:
        path = Path(file_path)
        if path.exists():
            size = path.stat().st_size
            print(f"✅ {description}: {file_path} (大小: {size:,} 字节)")

            # 对JSON文件进行额外验证
            if file_path.endswith(".json") and size > 0:
                try:
                    with open(path, "r") as f:
                        data = json.load(f)
                    print(
                        f"   📊 JSON文件有效，包含 {len(data.get('files', {}))} 个文件的覆盖率数据"
                    )
                except Exception as e:
                    print(f"   ⚠️ JSON文件格式错误: {e}")
        else:
            print(f"❌ {description}: {file_path} 不存在")
            all_good = False

    return all_good


def show_coverage_summary():
    """显示覆盖率摘要"""
    print("\n========== 覆盖率摘要 ==========")

    # 显示总体覆盖率
    result = run_command("coverage report --format=total", "获取总覆盖率")

    # 显示详细摘要（最后10行）
    run_command("coverage report | tail -10", "覆盖率详细摘要")

    return result


def validate_codecov_config():
    """验证Codecov配置"""
    print("\n========== 验证Codecov配置 ==========")

    # 检查codecov.yml是否存在
    codecov_config = Path("../codecov.yml")
    if codecov_config.exists():
        print("✅ codecov.yml 配置文件存在")
        with open(codecov_config, "r") as f:
            content = f.read()
            if "backend" in content:
                print("✅ 配置中包含backend标志")
            else:
                print("⚠️ 配置中缺少backend标志")
    else:
        print("❌ codecov.yml 配置文件不存在")

    # 检查.coveragerc配置
    coverage_config = Path(".coveragerc")
    if coverage_config.exists():
        print("✅ .coveragerc 配置文件存在")
    else:
        print("⚠️ .coveragerc 配置文件不存在")


def simulate_codecov_upload():
    """模拟Codecov上传过程"""
    print("\n========== 模拟Codecov上传 ==========")
    print("📝 在实际CI环境中，会执行以下步骤:")
    print("1. codecov/codecov-action@v4 会上传 coverage.xml")
    print("2. Codecov会处理覆盖率数据并生成报告")
    print("3. GitHub PR会显示覆盖率变化")
    print("4. Codecov网站会提供详细的覆盖率分析")

    # 检查是否可以使用codecov CLI（如果安装了的话）
    try:
        result = subprocess.run(
            "which codecov", shell=True, capture_output=True, text=True
        )
        if result.returncode == 0:
            print("✅ Codecov CLI 可用")
            # 注意：不要在没有token的情况下实际上传
            print("💡 可以使用 'codecov -f coverage.xml' 命令上传（需要token）")
        else:
            print("ℹ️ Codecov CLI 未安装（这在CI环境中是正常的）")
    except:
        print("ℹ️ 无法检查Codecov CLI状态")


def main():
    """主函数"""
    print("🎯 开始Codecov集成测试...")

    # 确保在backend目录
    backend_dir = Path(__file__).parent.parent
    os.chdir(backend_dir)
    print(f"📁 当前目录: {os.getcwd()}")

    # 1. 运行测试并生成覆盖率
    print("\n🧪 第一步：运行测试并生成覆盖率数据...")
    test_success = run_command(
        "python -m pytest tests/unit/test_simple_coverage.py -v --cov=app --cov-report=xml --cov-report=json --cov-report=html",
        "运行测试并生成覆盖率",
    )

    if not test_success:
        print("❌ 测试失败，尝试简化版本...")
        test_success = run_command(
            "python -m pytest tests/unit/ --maxfail=5 --cov=app --cov-report=xml --cov-report=json",
            "运行简化测试",
        )

    # 2. 检查覆盖率文件
    files_ok = check_coverage_files()

    # 3. 显示覆盖率摘要
    show_coverage_summary()

    # 4. 验证Codecov配置
    validate_codecov_config()

    # 5. 模拟上传过程
    simulate_codecov_upload()

    # 总结
    print("\n" + "=" * 60)
    print("🎯 Codecov集成测试总结")
    print("=" * 60)

    if test_success and files_ok:
        print("✅ 所有检查通过！Codecov集成已就绪")
        print("📊 覆盖率报告已生成")
        print("🔧 配置文件已就位")
        print("🚀 CI/CD流水线中的Codecov上传应该能够正常工作")
        print("\n📋 后续步骤:")
        print("1. 确保GitHub仓库中设置了CODECOV_TOKEN secret")
        print("2. 推送代码到GitHub触发CI/CD")
        print("3. 查看Codecov.io网站上的覆盖率报告")
        return 0
    else:
        print("⚠️ 部分检查未通过，请检查上述错误信息")
        return 1


if __name__ == "__main__":
    sys.exit(main())
