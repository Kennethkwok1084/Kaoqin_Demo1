#!/usr/bin/env python3
"""
测试覆盖率优化执行脚本
运行重构后的真实功能测试，验证覆盖率提升效果
"""

import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path


def print_header(title):
    """打印格式化标题"""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)


def print_section(title):
    """打印小节标题"""
    print(f"\n🔹 {title}")
    print("-" * 40)


def run_command(cmd, description=""):
    """运行命令并返回结果"""
    if description:
        print(f"执行: {description}")
        print(f"命令: {cmd}")

    try:
        result = subprocess.run(
            cmd, shell=True, capture_output=True, text=True, timeout=600
        )
        return result.returncode == 0, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return False, "", "命令执行超时"


def get_coverage_data():
    """获取当前覆盖率数据"""
    if os.path.exists("coverage.json"):
        with open("coverage.json", "r") as f:
            return json.load(f)
    return None


def analyze_coverage_change(before_data, after_data):
    """分析覆盖率变化"""
    if not before_data or not after_data:
        return None

    before_pct = before_data["totals"]["percent_covered"]
    after_pct = after_data["totals"]["percent_covered"]

    before_lines = before_data["totals"]["num_statements"]
    after_lines = after_data["totals"]["num_statements"]

    before_covered = before_data["totals"]["covered_lines"]
    after_covered = after_data["totals"]["covered_lines"]

    return {
        "before_percent": before_pct,
        "after_percent": after_pct,
        "percent_change": after_pct - before_pct,
        "before_lines": before_lines,
        "after_lines": after_lines,
        "before_covered": before_covered,
        "after_covered": after_covered,
        "additional_lines_covered": after_covered - before_covered,
    }


def main():
    """主执行函数"""
    print_header("测试覆盖率优化执行脚本")
    print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # 记录开始前的覆盖率
    print_section("获取基线覆盖率数据")
    success, stdout, stderr = run_command(
        "python3 -m pytest --cov=app --cov-report=json --cov-report=term-missing tests/test_basic.py -q",
        "运行基础测试获取基线覆盖率",
    )

    if not success:
        print(f"❌ 基线测试失败: {stderr}")
        sys.exit(1)

    baseline_coverage = get_coverage_data()
    if baseline_coverage:
        baseline_pct = baseline_coverage["totals"]["percent_covered"]
        print(f"✅ 基线覆盖率: {baseline_pct:.2f}%")
    else:
        print("⚠️ 无法获取基线覆盖率数据")
        baseline_pct = 0

    # 第一阶段：运行重构的认证API测试
    print_section("第一阶段：运行重构的认证API测试")
    success, stdout, stderr = run_command(
        "python3 -m pytest tests/refactored_examples/test_auth_api_real_coverage.py "
        "--cov=app --cov-append --cov-report=json --cov-report=term-missing -v",
        "执行认证API真实功能测试",
    )

    if success:
        print("✅ 认证API测试执行成功")
        # 显示测试结果摘要
        lines = stdout.split("\n")
        for line in lines:
            if "passed" in line or "failed" in line or "TOTAL" in line:
                print(f"  {line}")
    else:
        print(f"❌ 认证API测试失败:")
        print(stderr)

    # 获取第一阶段后的覆盖率
    phase1_coverage = get_coverage_data()
    if phase1_coverage:
        phase1_pct = phase1_coverage["totals"]["percent_covered"]
        improvement1 = phase1_pct - baseline_pct
        print(f"📊 第一阶段后覆盖率: {phase1_pct:.2f}% (+{improvement1:.2f}%)")

    # 第二阶段：运行任务API测试（最大的覆盖率提升点）
    print_section("第二阶段：运行任务API真实功能测试")
    success, stdout, stderr = run_command(
        "python3 -m pytest tests/refactored_examples/test_tasks_api_real_coverage.py "
        "--cov=app --cov-append --cov-report=json --cov-report=term-missing -v",
        "执行任务API真实功能测试",
    )

    if success:
        print("✅ 任务API测试执行成功")
        # 显示关键测试结果
        lines = stdout.split("\n")
        for line in lines:
            if any(
                keyword in line for keyword in ["passed", "failed", "ERROR", "test_"]
            ):
                if "test_" in line and ("PASSED" in line or "FAILED" in line):
                    print(f"  {line}")
    else:
        print(f"❌ 任务API测试失败:")
        print(stderr[:1000])  # 只显示前1000个字符

    # 获取第二阶段后的覆盖率
    phase2_coverage = get_coverage_data()
    if phase2_coverage:
        phase2_pct = phase2_coverage["totals"]["percent_covered"]
        improvement2 = phase2_pct - (phase1_pct if phase1_coverage else baseline_pct)
        print(f"📊 第二阶段后覆盖率: {phase2_pct:.2f}% (+{improvement2:.2f}%)")

    # 第三阶段：运行统计API测试
    print_section("第三阶段：运行统计API真实功能测试")
    success, stdout, stderr = run_command(
        "python3 -m pytest tests/refactored_examples/test_statistics_api_real_coverage.py "
        "--cov=app --cov-append --cov-report=json --cov-report=html -v",
        "执行统计API真实功能测试",
    )

    if success:
        print("✅ 统计API测试执行成功")
    else:
        print(f"❌ 统计API测试执行结果:")
        print(stderr[:1000])

    # 获取最终覆盖率
    final_coverage = get_coverage_data()

    # 生成最终报告
    print_section("最终覆盖率优化报告")

    if final_coverage and baseline_coverage:
        change_analysis = analyze_coverage_change(baseline_coverage, final_coverage)

        if change_analysis:
            print(f"📊 基线覆盖率:     {change_analysis['before_percent']:.2f}%")
            print(f"📊 优化后覆盖率:   {change_analysis['after_percent']:.2f}%")
            print(f"📊 覆盖率提升:     +{change_analysis['percent_change']:.2f}%")
            print(
                f"📊 新增覆盖行数:   +{change_analysis['additional_lines_covered']} lines"
            )

            # 评估优化效果
            if change_analysis["percent_change"] >= 15:
                print("🎉 优化效果：优秀！覆盖率大幅提升")
            elif change_analysis["percent_change"] >= 8:
                print("✅ 优化效果：良好，覆盖率显著提升")
            elif change_analysis["percent_change"] >= 3:
                print("📈 优化效果：一般，有一定提升")
            else:
                print("⚠️ 优化效果：有限，需要进一步改进")

            # 计算距离目标还有多远
            target_coverage = 75.0
            if change_analysis["after_percent"] >= target_coverage:
                print(f"🎯 已达成目标！当前覆盖率超过{target_coverage}%")
            else:
                remaining = target_coverage - change_analysis["after_percent"]
                print(f"🎯 距离{target_coverage}%目标还需提升{remaining:.2f}%")

    else:
        print("⚠️ 无法生成覆盖率对比分析")

    # 检查生成的报告
    if os.path.exists("htmlcov/index.html"):
        print(f"📄 详细HTML报告已生成: htmlcov/index.html")

    if os.path.exists("coverage.json"):
        print(f"📄 JSON数据文件已生成: coverage.json")

    print_section("检测假测试")
    # 检测剩余的假测试
    success, stdout, stderr = run_command(
        "grep -r 'assert True.*覆盖率' tests/ | wc -l", "统计剩余假测试数量"
    )

    if success and stdout.strip().isdigit():
        fake_test_count = int(stdout.strip())
        if fake_test_count == 0:
            print("✅ 未发现假测试模式")
        else:
            print(f"⚠️ 仍有 {fake_test_count} 个假测试需要重构")

    # 下一步建议
    print_section("下一步建议")

    if final_coverage:
        final_pct = final_coverage["totals"]["percent_covered"]

        if final_pct < 45:
            print("🔧 建议重点关注:")
            print("   1. 继续重构更多假测试")
            print("   2. 补充API层基础功能测试")
            print("   3. 检查测试是否正确执行业务逻辑")

        elif final_pct < 60:
            print("🚀 建议进一步优化:")
            print("   1. 补强服务层业务逻辑测试")
            print("   2. 增加边界条件和异常情况测试")
            print("   3. 添加集成测试覆盖完整工作流")

        elif final_pct < 75:
            print("🎯 接近目标，建议:")
            print("   1. 完善剩余API端点测试")
            print("   2. 增加复杂业务场景测试")
            print("   3. 添加性能和压力测试")

        else:
            print("🎉 恭喜！已达成75%+覆盖率目标")
            print("💡 建议保持质量:")
            print("   1. 建立覆盖率监控机制")
            print("   2. 设置覆盖率质量门禁")
            print("   3. 定期重构和优化测试代码")

    print_header("优化执行完成")
    print(f"结束时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == "__main__":
    main()
