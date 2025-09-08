#!/usr/bin/env python3
"""
覆盖率报告分析器
分析并展示项目的代码覆盖率情况
"""

import json
import os
import subprocess
import sys
from pathlib import Path


def generate_coverage_report():
    """生成最新的覆盖率报告"""
    print("🔄 正在生成最新的覆盖率报告...")

    try:
        # 运行覆盖率测试，生成JSON和HTML报告
        cmd = [
            sys.executable,
            "-m",
            "pytest",
            "--cov=app",
            "--cov-report=json:coverage.json",
            "--cov-report=html:htmlcov",
            "--cov-report=term-missing",
            "tests/core/",
            "tests/unit/",
            "tests/services/",
            "tests/api/",
            "-v",
            "--tb=short",
            "--maxfail=10",  # 限制失败数量以加速测试
        ]

        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)

        if result.returncode == 0 or Path("coverage.json").exists():
            print("✅ 覆盖率报告生成完成")
            return True
        else:
            print(f"⚠️  测试运行中有一些失败，但覆盖率报告已生成")
            print(f"错误信息: {result.stderr[:500]}...")
            return Path("coverage.json").exists()

    except subprocess.TimeoutExpired:
        print("⚠️  测试运行超时，尝试读取已有的覆盖率数据")
        return Path("coverage.json").exists()
    except Exception as e:
        print(f"❌ 生成覆盖率报告时出错: {e}")
        return False


def analyze_coverage(auto_generate=True):
    """分析覆盖率数据并生成报告"""

    coverage_file = Path("coverage.json")

    # 如果文件不存在或需要自动生成，先生成报告
    if auto_generate and (not coverage_file.exists() or should_regenerate_coverage()):
        if not generate_coverage_report():
            print("❌ 无法生成或找到覆盖率数据文件")
            return

    if not coverage_file.exists():
        print("❌ 覆盖率数据文件不存在，请先运行覆盖率测试")
        return


def should_regenerate_coverage():
    """检查是否需要重新生成覆盖率报告"""
    coverage_file = Path("coverage.json")
    if not coverage_file.exists():
        return True

    # 检查覆盖率文件是否过时（超过10分钟）
    import time

    file_age = time.time() - coverage_file.stat().st_mtime
    return file_age > 600  # 10分钟

    try:
        with open(coverage_file, "r") as f:
            data = json.load(f)

        print("📊 项目代码覆盖率分析报告")
        print("=" * 60)

        # 总体覆盖率
        totals = data.get("totals", {})
        total_coverage = totals.get("percent_covered", 0)

        print(f"\n🎯 总体覆盖率: {total_coverage:.2f}%")
        print(f"📝 总代码行数: {totals.get('num_statements', 0)}")
        print(f"✅ 已测试行数: {totals.get('covered_lines', 0)}")
        print(f"❌ 未测试行数: {totals.get('missing_lines', 0)}")
        print(f"🌿 分支覆盖数: {totals.get('num_branches', 0)}")
        print(f"✅ 已覆盖分支: {totals.get('covered_branches', 0)}")

        # 覆盖率等级
        if total_coverage >= 90:
            grade = "🥇 优秀"
            color = "\033[92m"  # Green
        elif total_coverage >= 80:
            grade = "🥈 良好"
            color = "\033[93m"  # Yellow
        elif total_coverage >= 60:
            grade = "🥉 及格"
            color = "\033[94m"  # Blue
        else:
            grade = "❌ 不及格"
            color = "\033[91m"  # Red

        print(f"\n{color}📊 覆盖率等级: {grade}\033[0m")

        # 文件级别的覆盖率分析
        files = data.get("files", {})
        if files:
            print(f"\n📁 文件覆盖率详情 (共 {len(files)} 个文件):")
            print("-" * 80)

            # 按覆盖率排序
            sorted_files = sorted(
                files.items(),
                key=lambda x: x[1]["summary"]["percent_covered"],
                reverse=True,
            )

            # 分类统计
            excellent_files = []  # >= 90%
            good_files = []  # 80% - 89%
            fair_files = []  # 60% - 79%
            poor_files = []  # < 60%

            for file_path, file_data in sorted_files:
                coverage_percent = file_data["summary"]["percent_covered"]
                file_name = Path(file_path).name

                if coverage_percent >= 90:
                    excellent_files.append((file_name, coverage_percent))
                elif coverage_percent >= 80:
                    good_files.append((file_name, coverage_percent))
                elif coverage_percent >= 60:
                    fair_files.append((file_name, coverage_percent))
                else:
                    poor_files.append((file_name, coverage_percent))

            # 显示统计结果
            print(f"🥇 优秀 (>=90%): {len(excellent_files)} 个文件")
            if excellent_files[:5]:  # 显示前5个
                for name, coverage in excellent_files[:5]:
                    print(f"   {name:<40} {coverage:6.2f}%")

            print(f"\n🥈 良好 (80-89%): {len(good_files)} 个文件")
            if good_files[:5]:
                for name, coverage in good_files[:5]:
                    print(f"   {name:<40} {coverage:6.2f}%")

            print(f"\n🥉 及格 (60-79%): {len(fair_files)} 个文件")
            if fair_files[:5]:
                for name, coverage in fair_files[:5]:
                    print(f"   {name:<40} {coverage:6.2f}%")

            print(f"\n❌ 需改进 (<60%): {len(poor_files)} 个文件")
            if poor_files[:10]:  # 显示更多需要改进的文件
                for name, coverage in poor_files[:10]:
                    print(f"   {name:<40} {coverage:6.2f}%")

            # Priority 3 核心模块分析
            priority3_modules = {
                "deps.py": None,
                "security.py": None,
                "database.py": None,
            }

            # 查找Priority 3模块的覆盖率
            for file_path, file_data in files.items():
                file_name = Path(file_path).name
                if file_name in priority3_modules:
                    priority3_modules[file_name] = file_data["summary"][
                        "percent_covered"
                    ]

            # 显示Priority 3模块状态
            if any(v is not None for v in priority3_modules.values()):
                print(f"\n🎯 Priority 3 核心基础设施模块:")
                print("-" * 80)
                for module, coverage in priority3_modules.items():
                    if coverage is not None:
                        if coverage >= 90:
                            status = "🥇 优秀"
                            color = "\033[92m"
                        elif coverage >= 80:
                            status = "🥈 良好"
                            color = "\033[93m"
                        else:
                            status = "⚠️  需改进"
                            color = "\033[91m"
                        print(
                            f"   {color}{module:<20} {coverage:6.2f}% {status}\033[0m"
                        )

            # 改进建议
            print(f"\n💡 改进建议:")
            if poor_files:
                print(f"   • 优先为覆盖率低于60%的 {len(poor_files)} 个文件增加测试")
            if fair_files:
                print(f"   • 为覆盖率60-79%的 {len(fair_files)} 个文件补充边界测试")
            if total_coverage < 80:
                print(f"   • 目标是将总覆盖率提升到80%以上")
                missing_coverage = 80 - total_coverage
                print(f"   • 还需要提升 {missing_coverage:.1f}% 的覆盖率")
            else:
                print(f"   • 🎉 太棒了！总覆盖率已达到 {total_coverage:.2f}%")

        # HTML报告位置
        html_report = Path("htmlcov/index.html")
        if html_report.exists():
            print(f"\n📋 详细HTML报告: {html_report.absolute()}")
            print("   可在浏览器中打开查看详细的行级覆盖率信息")

    except Exception as e:
        print(f"❌ 分析覆盖率数据时出错: {e}")


if __name__ == "__main__":
    # 切换到backend目录
    backend_dir = Path(__file__).parent
    os.chdir(backend_dir)

    # 检查是否需要跳过自动生成
    auto_gen = True
    if len(sys.argv) > 1 and sys.argv[1] == "--no-generate":
        auto_gen = False
        print("📋 仅分析现有覆盖率数据，不生成新报告")

    analyze_coverage(auto_generate=auto_gen)
