#!/usr/bin/env python3
"""
集成测试运行脚本
提供便捷的测试运行接口和配置选项
"""

import argparse
import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from tests.integration.test_runner import IntegrationTestRunner


def parse_arguments():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        description="运行后端系统集成测试套件",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法:
  python run_integration_tests.py                    # 运行所有测试
  python run_integration_tests.py --no-html         # 不生成HTML报告
  python run_integration_tests.py --no-coverage     # 不生成覆盖率报告
  python run_integration_tests.py --quick           # 快速模式（无报告）
        """
    )
    
    parser.add_argument(
        "--html",
        action="store_true",
        default=True,
        help="生成HTML测试报告（默认启用）"
    )
    
    parser.add_argument(
        "--no-html", 
        action="store_false",
        dest="html",
        help="不生成HTML测试报告"
    )
    
    parser.add_argument(
        "--json",
        action="store_true", 
        default=True,
        help="生成JSON测试报告（默认启用）"
    )
    
    parser.add_argument(
        "--no-json",
        action="store_false",
        dest="json", 
        help="不生成JSON测试报告"
    )
    
    parser.add_argument(
        "--coverage",
        action="store_true",
        default=True,
        help="生成代码覆盖率报告（默认启用）"
    )
    
    parser.add_argument(
        "--no-coverage",
        action="store_false",
        dest="coverage",
        help="不生成代码覆盖率报告"
    )
    
    parser.add_argument(
        "--quick",
        action="store_true",
        help="快速模式：只运行测试，不生成任何报告"
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="详细输出模式"
    )
    
    parser.add_argument(
        "--test-dir",
        type=str,
        default=None,
        help="指定测试目录（默认使用tests/integration）"
    )
    
    return parser.parse_args()


def setup_environment():
    """设置测试环境"""
    # 设置环境变量
    os.environ["ENVIRONMENT"] = "test"
    os.environ["TESTING"] = "1"
    
    # 确保必要的目录存在
    reports_dir = project_root / "tests" / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    
    # 检查依赖
    try:
        import pytest
        import pytest_asyncio
        import sqlalchemy
        import fastapi
    except ImportError as e:
        print(f"❌ 缺少必要的依赖: {e}")
        print("请运行: pip install -r requirements-test.txt")
        return False
    
    return True


def print_header():
    """打印程序头部信息"""
    print("=" * 70)
    print("后端系统集成测试套件 - 考勤管理系统")
    print("=" * 70)
    print()
    print("此测试套件将验证以下功能模块:")
    print("  📊 数据库连接和模型")
    print("  🔐 认证系统端到端流程")
    print("  👥 成员管理API完整流程")
    print("  📋 任务管理和工时计算")
    print("  📅 考勤管理系统")
    print("  📥 数据导入和缓存系统")
    print()


def print_footer(success: bool, duration: str = None):
    """打印结果汇总"""
    print()
    print("=" * 70)
    if success:
        print("✅ 集成测试运行完成")
        if duration:
            print(f"⏱️  总用时: {duration}")
        print("📊 详细报告已生成，请查看 tests/reports/ 目录")
    else:
        print("❌ 集成测试运行失败")
        print("🔍 请查看上述错误信息和测试报告")
    print("=" * 70)


def main():
    """主函数"""
    args = parse_arguments()
    
    # 打印头部信息
    if args.verbose:
        print_header()
    
    # 设置环境
    if not setup_environment():
        return 1
    
    # 快速模式设置
    if args.quick:
        args.html = False
        args.json = False  
        args.coverage = False
        if args.verbose:
            print("🚀 快速模式：只运行测试，不生成报告")
            print()
    
    # 创建测试运行器
    test_dir = args.test_dir if args.test_dir else None
    runner = IntegrationTestRunner(test_directory=test_dir)
    
    # 运行测试
    try:
        if args.verbose:
            print("🏃 开始运行集成测试...")
            print()
        
        results = runner.run_test_suite(
            generate_html_report=args.html,
            generate_json_report=args.json,
            coverage_report=args.coverage
        )
        
        if "error" in results:
            print(f"❌ 测试运行出错: {results['error']}")
            return 1
        
        # 显示结果摘要
        run_info = results["test_run_info"]
        stats = results["test_statistics"]
        success = run_info["success"]
        
        if args.verbose:
            print()
            print("📊 测试结果摘要:")
            print(f"   总测试数: {stats['total_tests']}")
            print(f"   ✅ 通过: {stats['passed']} ({stats['success_rate']:.1f}%)")
            print(f"   ❌ 失败: {stats['failed']} ({stats['failure_rate']:.1f}%)")
            print(f"   ⏭️  跳过: {stats['skipped']}")
            print(f"   🚫 错误: {stats['errors']}")
            print()
            
            # 显示各模块结果
            print("📋 各模块测试结果:")
            for module_name, module_stats in results["test_results_by_module"].items():
                status_icon = "✅" if module_stats["failed"] == 0 else "❌"
                module_display_name = module_name.replace("_", " ").title()
                print(f"   {status_icon} {module_display_name}: "
                      f"{module_stats['passed']}/{module_stats['total']} "
                      f"({module_stats['success_rate']:.1f}%)")
            print()
            
            # 显示改进建议
            if results["recommendations"]:
                print("💡 改进建议:")
                for i, rec in enumerate(results["recommendations"], 1):
                    print(f"   {i}. {rec}")
                print()
            
            # 显示报告文件位置
            if args.html or args.json or args.coverage:
                print("📁 生成的报告文件:")
                reports_dir = project_root / "tests" / "reports"
                
                if args.html:
                    html_file = reports_dir / "integration_test_report.html"
                    if html_file.exists():
                        print(f"   🌐 HTML报告: {html_file}")
                
                if args.json:
                    json_file = reports_dir / "comprehensive_test_report.json"
                    if json_file.exists():
                        print(f"   📄 JSON报告: {json_file}")
                
                markdown_file = reports_dir / "test_report.md"
                if markdown_file.exists():
                    print(f"   📝 Markdown报告: {markdown_file}")
                
                if args.coverage:
                    coverage_dir = project_root / "htmlcov"
                    if coverage_dir.exists():
                        print(f"   📊 覆盖率报告: {coverage_dir / 'index.html'}")
                print()
        else:
            # 简洁模式输出
            if success:
                print(f"✅ 测试通过: {stats['passed']}/{stats['total_tests']} "
                      f"({stats['success_rate']:.1f}%)")
            else:
                print(f"❌ 测试失败: {stats['failed']}/{stats['total_tests']} 失败")
        
        # 打印footer
        if args.verbose:
            print_footer(success, run_info['duration_formatted'])
        
        return 0 if success else 1
        
    except KeyboardInterrupt:
        print("\n⚠️  测试被用户中断")
        return 130
    except Exception as e:
        print(f"❌ 运行测试时出现意外错误: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)