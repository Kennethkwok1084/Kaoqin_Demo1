"""
修复的100%覆盖率验证脚本
修复数据不一致问题，准确计算覆盖率
"""

import json
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Set


def analyze_coverage_accurately():
    """准确分析覆盖率"""
    backend_path = Path("/home/kwok/Coder/Kaoqin_Demo/backend")

    # 读取之前的报告
    report_file = backend_path / "coverage_100_percent_report.json"

    if not report_file.exists():
        print("❌ 报告文件不存在")
        return

    with open(report_file, "r", encoding="utf-8") as f:
        report = json.load(f)

    uncovered = set(report.get("uncovered_endpoints", []))
    covered = set(report.get("covered_endpoints", []))

    print("🔍 准确覆盖率分析结果:")
    print(f"📊 总API端点数: {report['analysis_summary']['total_api_endpoints']}")
    print(f"📊 已覆盖端点数: {len(covered)}")
    print(f"📊 未覆盖端点数: {len(uncovered)}")

    # 重新计算覆盖率
    total_endpoints = len(covered) + len(uncovered)
    actual_coverage = (
        (len(covered) / total_endpoints) * 100 if total_endpoints > 0 else 0
    )

    print(f"📊 实际总端点数: {total_endpoints}")
    print(f"📊 实际覆盖率: {actual_coverage:.2f}%")

    print(f"\n⚠️ 未覆盖的端点列表 ({len(uncovered)} 个):")
    for i, endpoint in enumerate(sorted(uncovered)):
        if i < 20:  # 显示前20个
            print(f"  {i+1}. {endpoint}")
        elif i == 20:
            print(f"  ... 还有 {len(uncovered) - 20} 个未显示")
            break

    # 分析未覆盖端点的类型
    print(f"\n📋 未覆盖端点分类:")
    delete_endpoints = [e for e in uncovered if e.startswith("DELETE")]
    get_endpoints = [e for e in uncovered if e.startswith("GET")]
    post_endpoints = [e for e in uncovered if e.startswith("POST")]
    put_endpoints = [e for e in uncovered if e.startswith("PUT")]

    print(f"  - DELETE 操作: {len(delete_endpoints)} 个")
    print(f"  - GET 操作: {len(get_endpoints)} 个")
    print(f"  - POST 操作: {len(post_endpoints)} 个")
    print(f"  - PUT 操作: {len(put_endpoints)} 个")

    return uncovered


if __name__ == "__main__":
    uncovered_endpoints = analyze_coverage_accurately()
