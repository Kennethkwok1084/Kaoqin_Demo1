#!/usr/bin/env python3
"""
E2E测试运行脚本
自动化执行完整的端到端测试套件
包含测试环境检查、数据准备、测试执行和结果报告
"""

import argparse
import asyncio
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import pytest


class E2ETestRunner:
    """E2E测试运行器"""
    
    def __init__(self):
        self.test_dir = Path(__file__).parent
        self.backend_dir = self.test_dir.parent.parent
        self.results_dir = self.test_dir / "results"
        self.results_dir.mkdir(exist_ok=True)
        
        self.test_modules = [
            "test_user_authentication_flow.py",
            "test_repair_task_lifecycle.py", 
            "test_assistance_task_management.py",
            "test_attendance_data_management.py",
            "test_system_settings_and_permissions.py",
            "test_statistics_and_reports.py"
        ]
    
    def check_environment(self) -> bool:
        """检查测试环境是否就绪"""
        print("🔍 检查E2E测试环境...")
        
        # 检查必要文件
        required_files = ["conftest.py"] + self.test_modules
        missing_files = []
        
        for file in required_files:
            if not (self.test_dir / file).exists():
                missing_files.append(file)
        
        if missing_files:
            print(f"❌ 缺少测试文件: {', '.join(missing_files)}")
            return False
        
        # 检查测试配置
        try:
            import pytest
            import httpx
            import asyncio
            print("✅ 测试依赖包检查通过")
        except ImportError as e:
            print(f"❌ 缺少测试依赖: {e}")
            return False
        
        # 检查数据库配置
        try:
            # 添加backend目录到sys.path以支持相对导入
            sys.path.insert(0, str(self.backend_dir))
            from tests.database_config import test_config
            print("✅ 测试数据库配置检查通过")
        except ImportError as e:
            print(f"❌ 测试数据库配置错误: {e}")
            return False
        finally:
            # 清理sys.path
            if str(self.backend_dir) in sys.path:
                sys.path.remove(str(self.backend_dir))
        
        print("✅ E2E测试环境检查完成")
        return True
    
    def run_single_module(self, module_name: str, verbose: bool = False) -> Dict:
        """运行单个测试模块"""
        print(f"🧪 运行测试模块: {module_name}")
        
        # 构建pytest命令
        xml_name = module_name.replace('.py', '_results.xml')
        json_name = module_name.replace('.py', '_results.json')
        
        pytest_args = [
            str(self.test_dir / module_name),
            "-v" if verbose else "-q",
            "--tb=short",
            "--disable-warnings",
            f"--junitxml={self.results_dir / xml_name}",
            f"--json-report-file={self.results_dir / json_name}",
            "--asyncio-mode=auto"
        ]
        
        # 执行测试
        start_time = time.time()
        exit_code = pytest.main(pytest_args)
        duration = time.time() - start_time
        
        # 解析结果
        result = {
            "module": module_name,
            "exit_code": exit_code,
            "duration": round(duration, 2),
            "status": "PASSED" if exit_code == 0 else "FAILED",
            "timestamp": datetime.now().isoformat()
        }
        
        # 尝试读取详细结果
        json_result_filename = module_name.replace(".py", "_results.json")
        json_result_file = self.results_dir / json_result_filename
        if json_result_file.exists():
            try:
                with open(json_result_file, 'r', encoding='utf-8') as f:
                    detailed_results = json.load(f)
                    result.update({
                        "tests_collected": detailed_results.get("summary", {}).get("total", 0),
                        "tests_passed": detailed_results.get("summary", {}).get("passed", 0),
                        "tests_failed": detailed_results.get("summary", {}).get("failed", 0),
                        "tests_skipped": detailed_results.get("summary", {}).get("skipped", 0),
                        "tests_error": detailed_results.get("summary", {}).get("error", 0)
                    })
            except Exception as e:
                print(f"⚠️  无法解析测试结果文件: {e}")
        
        return result
    
    def run_all_tests(self, 
                     modules: Optional[List[str]] = None,
                     verbose: bool = False,
                     parallel: bool = False,
                     stop_on_failure: bool = False) -> Dict:
        """运行所有E2E测试"""
        
        if modules is None:
            modules = self.test_modules
        
        print(f"🚀 开始运行E2E测试套件 ({len(modules)} 个模块)")
        print(f"📁 测试目录: {self.test_dir}")
        print(f"📊 结果目录: {self.results_dir}")
        
        overall_start_time = time.time()
        results = {
            "start_time": datetime.now().isoformat(),
            "test_modules": [],
            "summary": {
                "total_modules": len(modules),
                "passed_modules": 0,
                "failed_modules": 0,
                "total_tests": 0,
                "passed_tests": 0,
                "failed_tests": 0,
                "skipped_tests": 0,
                "error_tests": 0
            }
        }
        
        # 运行测试模块
        for module in modules:
            if not (self.test_dir / module).exists():
                print(f"⚠️  跳过不存在的模块: {module}")
                continue
            
            module_result = self.run_single_module(module, verbose)
            results["test_modules"].append(module_result)
            
            # 更新汇总统计
            if module_result["status"] == "PASSED":
                results["summary"]["passed_modules"] += 1
            else:
                results["summary"]["failed_modules"] += 1
                
                if stop_on_failure:
                    print(f"❌ 模块 {module} 失败，停止测试执行")
                    break
            
            # 累加测试统计
            for key in ["tests_collected", "tests_passed", "tests_failed", "tests_skipped", "tests_error"]:
                if key in module_result:
                    results["summary"][key.replace("tests_", "")] = \
                        results["summary"].get(key.replace("tests_", ""), 0) + module_result[key]
            
            print(f"✅ {module}: {module_result['status']} ({module_result['duration']}s)")
        
        # 完成测试
        overall_duration = time.time() - overall_start_time
        results["end_time"] = datetime.now().isoformat()
        results["total_duration"] = round(overall_duration, 2)
        
        return results
    
    def generate_report(self, results: Dict) -> str:
        """生成测试报告"""
        
        report_lines = [
            "=" * 80,
            "🧪 E2E测试执行报告",
            "=" * 80,
            f"开始时间: {results['start_time']}",
            f"结束时间: {results['end_time']}",
            f"总耗时: {results['total_duration']}秒",
            "",
            "📊 测试统计:",
            f"  - 测试模块: {results['summary']['total_modules']}",
            f"  - 通过模块: {results['summary']['passed_modules']}",
            f"  - 失败模块: {results['summary']['failed_modules']}",
            f"  - 总测试数: {results['summary'].get('total', 0)}",
            f"  - 通过测试: {results['summary'].get('passed', 0)}",
            f"  - 失败测试: {results['summary'].get('failed', 0)}",
            f"  - 跳过测试: {results['summary'].get('skipped', 0)}",
            f"  - 错误测试: {results['summary'].get('error', 0)}",
            "",
            "📋 模块详情:",
        ]
        
        for module_result in results["test_modules"]:
            status_icon = "✅" if module_result["status"] == "PASSED" else "❌"
            report_lines.append(
                f"  {status_icon} {module_result['module']}: "
                f"{module_result['status']} ({module_result['duration']}s)"
            )
            
            if module_result.get("tests_collected", 0) > 0:
                report_lines.append(
                    f"      测试: {module_result.get('tests_passed', 0)}/{module_result.get('tests_collected', 0)} 通过"
                )
        
        report_lines.extend([
            "",
            "=" * 80
        ])
        
        return "\n".join(report_lines)
    
    def save_results(self, results: Dict) -> str:
        """保存测试结果"""
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 保存JSON结果
        json_file = self.results_dir / f"e2e_test_results_{timestamp}.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        # 保存文本报告
        report = self.generate_report(results)
        report_file = self.results_dir / f"e2e_test_report_{timestamp}.txt"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)
        
        print(f"📄 测试结果已保存:")
        print(f"  - JSON: {json_file}")
        print(f"  - 报告: {report_file}")
        
        return str(report_file)


def main():
    """主函数"""
    
    parser = argparse.ArgumentParser(description="运行考勤系统E2E测试")
    parser.add_argument("--modules", "-m", nargs="+", 
                       help="指定要运行的测试模块 (默认运行全部)")
    parser.add_argument("--verbose", "-v", action="store_true",
                       help="详细输出模式")
    parser.add_argument("--parallel", "-p", action="store_true",
                       help="并行执行测试 (实验性功能)")
    parser.add_argument("--stop-on-failure", "-s", action="store_true",
                       help="遇到失败时停止执行")
    parser.add_argument("--check-only", "-c", action="store_true",
                       help="仅检查环境，不执行测试")
    parser.add_argument("--list-modules", "-l", action="store_true",
                       help="列出所有可用的测试模块")
    
    args = parser.parse_args()
    
    # 创建测试运行器
    runner = E2ETestRunner()
    
    # 列出模块
    if args.list_modules:
        print("📋 可用的E2E测试模块:")
        for i, module in enumerate(runner.test_modules, 1):
            print(f"  {i}. {module}")
        return 0
    
    # 检查环境
    if not runner.check_environment():
        print("❌ 环境检查失败，无法执行测试")
        return 1
    
    if args.check_only:
        print("✅ 环境检查完成")
        return 0
    
    # 准备测试模块列表
    modules_to_run = args.modules if args.modules else runner.test_modules
    
    # 验证指定的模块存在
    if args.modules:
        invalid_modules = []
        for module in args.modules:
            if module not in runner.test_modules:
                invalid_modules.append(module)
        
        if invalid_modules:
            print(f"❌ 无效的测试模块: {', '.join(invalid_modules)}")
            print("💡 使用 --list-modules 查看所有可用模块")
            return 1
    
    # 运行测试
    try:
        results = runner.run_all_tests(
            modules=modules_to_run,
            verbose=args.verbose,
            parallel=args.parallel,
            stop_on_failure=args.stop_on_failure
        )
        
        # 显示报告
        report = runner.generate_report(results)
        print(report)
        
        # 保存结果
        runner.save_results(results)
        
        # 返回适当的退出码
        if results["summary"]["failed_modules"] > 0:
            print("❌ 部分测试失败")
            return 1
        else:
            print("✅ 所有测试通过")
            return 0
            
    except KeyboardInterrupt:
        print("\n⚠️  测试被用户中断")
        return 130
    except Exception as e:
        print(f"❌ 测试执行过程中出现错误: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())