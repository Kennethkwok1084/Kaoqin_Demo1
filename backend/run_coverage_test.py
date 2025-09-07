#!/usr/bin/env python3
"""
覆盖率测试运行器
提供不同级别的代码覆盖率测试和报告生成
"""

import argparse
import os
import subprocess
import sys
from pathlib import Path


def run_command(command, description):
    """运行命令并显示进度"""
    print(f"\n{'='*60}")
    print(f"正在执行: {description}")
    print(f"命令: {command}")
    print(f"{'='*60}")
    
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"❌ 错误: {description} 失败")
        print(f"错误输出: {result.stderr}")
        return False
    else:
        print(f"✅ 成功: {description} 完成")
        if result.stdout:
            print(f"输出: {result.stdout}")
        return True


def generate_coverage_report(test_level="basic", output_formats=None, exclude_files=None):
    """
    生成覆盖率报告
    
    Args:
        test_level: 测试级别 ("basic", "unit", "integration", "all")
        output_formats: 输出格式列表 (["html", "xml", "json", "term"])
        exclude_files: 排除的文件列表
    """
    if output_formats is None:
        output_formats = ["html", "term-missing", "json"]
    
    if exclude_files is None:
        exclude_files = [
            "tests/unit/test_coverage_improvement_strategy.py",
            "tests/e2e/test_repair_task_lifecycle.py"
        ]
    
    # 构建pytest命令
    base_cmd = "python -m pytest --cov=app"
    
    # 添加覆盖率报告格式
    for fmt in output_formats:
        base_cmd += f" --cov-report={fmt}"
    
    # 添加排除文件
    for exclude_file in exclude_files:
        base_cmd += f" --ignore={exclude_file}"
    
    # 根据测试级别选择测试路径
    test_paths = {
        "basic": ["tests/unit/test_simple_coverage.py"],
        "unit": ["tests/unit/"],
        "integration": ["tests/integration/"],
        "all": ["tests/"]
    }
    
    test_path = " ".join(test_paths.get(test_level, ["tests/"]))
    full_cmd = f"{base_cmd} {test_path} -v"
    
    return run_command(full_cmd, f"运行 {test_level} 级别的覆盖率测试")


def open_html_report():
    """打开HTML覆盖率报告"""
    html_report = Path("htmlcov/index.html")
    if html_report.exists():
        print(f"\n📊 HTML覆盖率报告已生成: {html_report.absolute()}")
        print("你可以用浏览器打开这个文件查看详细的覆盖率报告")
        
        # 尝试自动打开浏览器
        try:
            import webbrowser
            webbrowser.open(f"file://{html_report.absolute()}")
            print("✅ 已在浏览器中打开报告")
        except Exception as e:
            print(f"⚠️  无法自动打开浏览器: {e}")
    else:
        print("❌ HTML报告未找到")


def show_coverage_summary():
    """显示覆盖率摘要"""
    coverage_file = Path("coverage.json")
    if coverage_file.exists():
        try:
            import json
            with open(coverage_file, 'r') as f:
                coverage_data = json.load(f)
            
            print(f"\n📈 覆盖率摘要:")
            print(f"总覆盖率: {coverage_data['totals']['percent_covered']:.2f}%")
            print(f"测试的语句数: {coverage_data['totals']['covered_lines']}")
            print(f"总语句数: {coverage_data['totals']['num_statements']}")
            print(f"缺失语句数: {coverage_data['totals']['missing_lines']}")
            
        except Exception as e:
            print(f"❌ 读取覆盖率数据失败: {e}")


def main():
    parser = argparse.ArgumentParser(description="运行代码覆盖率测试")
    parser.add_argument(
        "--level", 
        choices=["basic", "unit", "integration", "all"], 
        default="basic",
        help="测试级别 (默认: basic)"
    )
    parser.add_argument(
        "--format", 
        nargs="+", 
        choices=["html", "xml", "json", "term", "term-missing"],
        default=["html", "term-missing", "json"],
        help="输出格式 (默认: html term-missing json)"
    )
    parser.add_argument(
        "--open", 
        action="store_true",
        help="完成后自动打开HTML报告"
    )
    parser.add_argument(
        "--summary", 
        action="store_true",
        help="显示覆盖率摘要"
    )
    
    args = parser.parse_args()
    
    print(f"🚀 开始运行 {args.level} 级别的覆盖率测试...")
    
    # 切换到项目目录
    os.chdir(Path(__file__).parent)
    
    # 运行覆盖率测试
    success = generate_coverage_report(
        test_level=args.level,
        output_formats=args.format
    )
    
    if success:
        print(f"\n✅ 覆盖率测试完成!")
        
        if args.summary:
            show_coverage_summary()
        
        if args.open:
            open_html_report()
        
        print(f"\n📁 生成的报告文件:")
        report_files = [
            ("HTML报告", "htmlcov/index.html"),
            ("JSON报告", "coverage.json"),
            ("XML报告", "coverage.xml")
        ]
        
        for name, path in report_files:
            if Path(path).exists():
                print(f"  - {name}: {path}")
    else:
        print(f"\n❌ 覆盖率测试失败!")
        sys.exit(1)


if __name__ == "__main__":
    main()
