#!/usr/bin/env python3
"""
生成集成测试汇总报告
汇总所有测试结果，生成项目级别的测试状态报告
"""

import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any

def load_test_results() -> Dict[str, Any]:
    """加载测试结果数据"""
    backend_dir = Path(__file__).parent
    reports_dir = backend_dir / "tests" / "reports"
    
    # 查找最新的测试报告
    json_report = reports_dir / "comprehensive_test_report.json"
    
    if not json_report.exists():
        print("❌ 未找到测试报告文件，请先运行集成测试")
        print("   运行命令: python run_integration_tests.py")
        return None
    
    try:
        with open(json_report, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"❌ 读取测试报告失败: {e}")
        return None

def generate_summary_report(test_data: Dict[str, Any]) -> str:
    """生成汇总报告"""
    if not test_data:
        return "无法生成报告：测试数据为空"
    
    # 提取关键信息
    run_info = test_data.get("test_run_info", {})
    stats = test_data.get("test_statistics", {})
    modules = test_data.get("test_results_by_module", {})
    recommendations = test_data.get("recommendations", [])
    coverage = test_data.get("coverage_info", {})
    
    # 生成报告内容
    report_lines = []
    
    # 标题和基本信息
    report_lines.extend([
        "# 后端系统集成测试汇总报告",
        "",
        f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"**测试运行时间**: {run_info.get('start_time', 'N/A')} 至 {run_info.get('end_time', 'N/A')}",
        f"**总耗时**: {run_info.get('duration_formatted', 'N/A')}",
        ""
    ])
    
    # 总体状态
    success = run_info.get("success", False)
    status_icon = "✅" if success else "❌"
    status_text = "通过" if success else "失败"
    
    report_lines.extend([
        "## 🎯 总体测试状态",
        "",
        f"**{status_icon} 测试状态**: {status_text}",
        f"**📊 成功率**: {stats.get('success_rate', 0):.1f}%",
        f"**🧪 总测试数**: {stats.get('total_tests', 0)}",
        ""
    ])
    
    # 详细统计
    report_lines.extend([
        "## 📈 详细测试统计",
        "",
        "| 状态 | 数量 | 百分比 |",
        "|------|------|--------|",
        f"| ✅ 通过 | {stats.get('passed', 0)} | {stats.get('success_rate', 0):.1f}% |",
        f"| ❌ 失败 | {stats.get('failed', 0)} | {stats.get('failure_rate', 0):.1f}% |",
        f"| ⏭️ 跳过 | {stats.get('skipped', 0)} | {(stats.get('skipped', 0) / max(stats.get('total_tests', 1), 1) * 100):.1f}% |",
        f"| 🚫 错误 | {stats.get('errors', 0)} | {(stats.get('errors', 0) / max(stats.get('total_tests', 1), 1) * 100):.1f}% |",
        ""
    ])
    
    # 各模块测试结果
    report_lines.extend([
        "## 🏗️ 各模块测试结果",
        ""
    ])
    
    module_names = {
        "database": "数据库连接和模型",
        "auth_flow": "认证系统端到端流程", 
        "members_api": "成员管理API",
        "tasks_workhours": "任务管理和工时计算",
        "attendance_system": "考勤管理系统",
        "data_import_cache": "数据导入和缓存系统"
    }
    
    for module_key, module_stats in modules.items():
        module_name = module_names.get(module_key, module_key)
        total = module_stats.get("total", 0)
        passed = module_stats.get("passed", 0)
        failed = module_stats.get("failed", 0)
        success_rate = module_stats.get("success_rate", 0)
        
        status_icon = "✅" if failed == 0 and total > 0 else "❌" if failed > 0 else "⚠️"
        
        report_lines.extend([
            f"### {status_icon} {module_name}",
            "",
            f"- **总测试数**: {total}",
            f"- **通过**: {passed}",
            f"- **失败**: {failed}",
            f"- **成功率**: {success_rate:.1f}%",
            ""
        ])
    
    # 代码覆盖率
    if coverage and "error" not in coverage:
        report_lines.extend([
            "## 📊 代码覆盖率",
            "",
            f"- **总覆盖率**: {coverage.get('total_coverage', 0):.1f}%",
            f"- **覆盖文件数**: {coverage.get('files_covered', 0)}",
            f"- **覆盖行数**: {coverage.get('covered_lines', 0)}",
            f"- **未覆盖行数**: {coverage.get('missing_lines', 0)}",
            ""
        ])
    
    # 质量评估
    quality_score = calculate_quality_score(stats, coverage)
    quality_level, quality_color = get_quality_level(quality_score)
    
    report_lines.extend([
        "## 🎖️ 质量评估",
        "",
        f"**整体质量评分**: {quality_color} {quality_score:.1f}/100 ({quality_level})",
        "",
        "评分依据:",
        f"- 测试通过率: {stats.get('success_rate', 0):.1f}%",
        f"- 代码覆盖率: {coverage.get('total_coverage', 0) if coverage and 'error' not in coverage else 0:.1f}%",
        f"- 测试完整性: {min(100, len(modules) * 20):.0f}%",
        ""
    ])
    
    # 改进建议
    if recommendations:
        report_lines.extend([
            "## 💡 改进建议",
            ""
        ])
        
        for i, rec in enumerate(recommendations, 1):
            report_lines.append(f"{i}. {rec}")
        
        report_lines.append("")
    
    # 趋势分析（如果有历史数据）
    trend_data = analyze_trends()
    if trend_data:
        report_lines.extend([
            "## 📊 趋势分析",
            "",
            trend_data,
            ""
        ])
    
    # 下一步行动
    next_actions = generate_next_actions(stats, modules, recommendations)
    if next_actions:
        report_lines.extend([
            "## 🎯 下一步行动",
            "",
            *next_actions,
            ""
        ])
    
    # 附录信息
    report_lines.extend([
        "## 📎 附录信息",
        "",
        f"- **测试框架**: pytest + pytest-asyncio",
        f"- **测试环境**: {test_data.get('system_info', {}).get('platform', 'Unknown')}",
        f"- **Python版本**: {test_data.get('system_info', {}).get('python_version', 'Unknown').split()[0]}",
        f"- **报告文件**: tests/reports/",
        "",
        "---",
        "",
        f"*报告生成于 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*"
    ])
    
    return "\n".join(report_lines)

def calculate_quality_score(stats: Dict[str, Any], coverage: Dict[str, Any]) -> float:
    """计算质量评分（0-100分）"""
    score = 0.0
    
    # 测试通过率权重40%
    success_rate = stats.get("success_rate", 0)
    score += success_rate * 0.4
    
    # 代码覆盖率权重30%
    if coverage and "error" not in coverage:
        coverage_rate = coverage.get("total_coverage", 0)
        score += coverage_rate * 0.3
    
    # 测试完整性权重20%（基于测试模块数量）
    total_tests = stats.get("total_tests", 0)
    if total_tests > 0:
        completeness = min(100, total_tests * 2)  # 假设50个测试为满分
        score += completeness * 0.2
    
    # 错误率惩罚权重10%
    total_tests = max(stats.get("total_tests", 1), 1)
    error_rate = (stats.get("errors", 0) + stats.get("failed", 0)) / total_tests * 100
    error_penalty = max(0, 100 - error_rate * 2)  # 错误率每增加1%扣2分
    score += error_penalty * 0.1
    
    return min(100.0, max(0.0, score))

def get_quality_level(score: float) -> tuple:
    """根据评分获取质量等级"""
    if score >= 90:
        return "优秀", "🟢"
    elif score >= 80:
        return "良好", "🟡"
    elif score >= 70:
        return "一般", "🟠"
    elif score >= 60:
        return "需改进", "🔴"
    else:
        return "急需改进", "⚠️"

def analyze_trends() -> str:
    """分析测试趋势（需要历史数据）"""
    # 这里可以实现历史数据分析
    # 暂时返回空字符串
    return ""

def generate_next_actions(stats: Dict[str, Any], modules: Dict[str, Any], recommendations: List[str]) -> List[str]:
    """生成下一步行动建议"""
    actions = []
    
    # 基于失败测试的行动
    if stats.get("failed", 0) > 0:
        actions.append("🔧 **立即修复失败的测试用例**")
        
        # 找出失败最多的模块
        max_failures = 0
        critical_module = None
        for module_name, module_stats in modules.items():
            if module_stats.get("failed", 0) > max_failures:
                max_failures = module_stats.get("failed", 0)
                critical_module = module_name
        
        if critical_module:
            actions.append(f"   - 优先关注 {critical_module} 模块（{max_failures} 个失败测试）")
    
    # 基于成功率的行动
    success_rate = stats.get("success_rate", 0)
    if success_rate < 80:
        actions.append("📈 **提升测试成功率到80%以上**")
        actions.append("   - 分析失败原因，制定修复计划")
        actions.append("   - 加强代码质量控制流程")
    
    # 基于跳过测试的行动
    if stats.get("skipped", 0) > 0:
        actions.append("⏭️ **处理跳过的测试用例**")
        actions.append("   - 分析跳过原因，评估是否需要实现")
    
    # 基于错误的行动
    if stats.get("errors", 0) > 0:
        actions.append("🚫 **解决测试错误**")
        actions.append("   - 检查测试环境配置")
        actions.append("   - 验证依赖和数据库连接")
    
    # 基于建议的行动
    if len(recommendations) > 3:
        actions.append("💡 **按优先级实施改进建议**")
        actions.append("   - 每周处理1-2项建议")
        actions.append("   - 跟踪改进效果")
    
    return actions

def save_summary_report(content: str) -> None:
    """保存汇总报告"""
    backend_dir = Path(__file__).parent
    reports_dir = backend_dir / "tests" / "reports"
    reports_dir.mkdir(exist_ok=True)
    
    # 保存Markdown文件
    summary_file = reports_dir / "test_summary.md"
    with open(summary_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"📊 测试汇总报告已生成: {summary_file}")

def main():
    """主函数"""
    print("🔍 正在生成集成测试汇总报告...")
    
    # 加载测试结果
    test_data = load_test_results()
    if not test_data:
        return 1
    
    # 生成汇总报告
    summary_content = generate_summary_report(test_data)
    
    # 保存报告
    save_summary_report(summary_content)
    
    # 显示简要摘要
    stats = test_data.get("test_statistics", {})
    run_info = test_data.get("test_run_info", {})
    
    print("\n" + "="*50)
    print("📋 测试汇总")
    print("="*50)
    print(f"✅ 测试状态: {'通过' if run_info.get('success') else '失败'}")
    print(f"📊 成功率: {stats.get('success_rate', 0):.1f}%")
    print(f"🧪 总测试数: {stats.get('total_tests', 0)}")
    print(f"⏱️ 运行时长: {run_info.get('duration_formatted', 'N/A')}")
    
    # 显示质量评分
    coverage = test_data.get("coverage_info", {})
    quality_score = calculate_quality_score(stats, coverage)
    quality_level, quality_color = get_quality_level(quality_score)
    print(f"🎖️ 质量评分: {quality_color} {quality_score:.1f}/100 ({quality_level})")
    
    print("="*50)
    print(f"📄 详细报告: tests/reports/test_summary.md")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())