"""
集成测试运行器和报告生成器
运行完整的集成测试套件并生成详细的测试报告
"""

import pytest
import pytest_asyncio
import sys
import os
import json
import time
import asyncio
from datetime import datetime
from pathlib import Path
import subprocess
from typing import Dict, List, Any

import pytest_html
from pytest_html import extras


class IntegrationTestRunner:
    """集成测试运行器"""
    
    def __init__(self, test_directory: str = None):
        self.test_directory = test_directory or os.path.dirname(__file__)
        self.results = {}
        self.start_time = None
        self.end_time = None
        
    def run_test_suite(self, generate_html_report: bool = True, 
                      generate_json_report: bool = True,
                      coverage_report: bool = True) -> Dict[str, Any]:
        """运行完整的集成测试套件"""
        self.start_time = datetime.now()
        
        # 构建pytest命令
        test_files = [
            "test_database.py",
            "test_auth_flow.py", 
            "test_members_api.py",
            "test_tasks_workhours.py",
            "test_attendance_system.py",
            "test_data_import_cache.py"
        ]
        
        pytest_args = [
            "-v",  # 详细输出
            "--tb=short",  # 简短的错误追踪
            "--strict-markers",  # 严格标记模式
            "--disable-warnings",  # 禁用警告
        ]
        
        # 添加覆盖率报告
        if coverage_report:
            pytest_args.extend([
                "--cov=app",
                "--cov-report=html:htmlcov",
                "--cov-report=json:coverage.json",
                "--cov-report=term-missing",
                "--cov-branch"
            ])
        
        # 添加HTML报告
        if generate_html_report:
            html_report_path = Path(self.test_directory).parent / "reports" / "integration_test_report.html"
            html_report_path.parent.mkdir(exist_ok=True)
            pytest_args.extend([
                f"--html={html_report_path}",
                "--self-contained-html"
            ])
        
        # 添加JSON报告
        if generate_json_report:
            json_report_path = Path(self.test_directory).parent / "reports" / "integration_test_results.json"
            json_report_path.parent.mkdir(exist_ok=True)
            pytest_args.extend([
                f"--json-report",
                f"--json-report-file={json_report_path}"
            ])
        
        # 添加测试文件路径
        for test_file in test_files:
            test_path = Path(self.test_directory) / test_file
            if test_path.exists():
                pytest_args.append(str(test_path))
        
        # 运行pytest
        print(f"开始运行集成测试套件...")
        print(f"测试文件: {', '.join(test_files)}")
        print(f"pytest参数: {' '.join(pytest_args)}")
        
        try:
            # 使用subprocess运行pytest以获取更好的控制
            result = subprocess.run(
                [sys.executable, "-m", "pytest"] + pytest_args,
                capture_output=True,
                text=True,
                cwd=Path(self.test_directory).parent.parent,  # backend目录
                timeout=1800  # 30分钟超时
            )
            
        except subprocess.TimeoutExpired:
            print("测试运行超时（30分钟）")
            return {"error": "Test execution timeout"}
        except Exception as e:
            print(f"测试运行出错: {e}")
            return {"error": str(e)}
        
        self.end_time = datetime.now()
        
        # 解析结果
        test_results = self._parse_test_results(result)
        
        # 生成综合报告
        comprehensive_report = self._generate_comprehensive_report(test_results)
        
        return comprehensive_report
    
    def _parse_test_results(self, result: subprocess.CompletedProcess) -> Dict[str, Any]:
        """解析pytest运行结果"""
        stdout_lines = result.stdout.split('\n')
        stderr_lines = result.stderr.split('\n')
        
        # 提取测试统计信息
        stats = self._extract_test_statistics(stdout_lines)
        
        # 提取失败的测试
        failures = self._extract_failures(stdout_lines)
        
        # 提取警告信息
        warnings = self._extract_warnings(stdout_lines + stderr_lines)
        
        return {
            "return_code": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "statistics": stats,
            "failures": failures,
            "warnings": warnings,
            "duration": (self.end_time - self.start_time).total_seconds()
        }
    
    def _extract_test_statistics(self, lines: List[str]) -> Dict[str, Any]:
        """从pytest输出中提取测试统计信息"""
        stats = {
            "total_tests": 0,
            "passed": 0,
            "failed": 0,
            "skipped": 0,
            "errors": 0,
            "warnings": 0
        }
        
        # 查找统计行，通常在最后几行
        for line in reversed(lines[-20:]):
            if "passed" in line or "failed" in line or "error" in line:
                # 解析类似 "25 passed, 2 failed, 1 skipped in 45.23s" 的行
                parts = line.strip().split()
                for i, part in enumerate(parts):
                    if part.isdigit():
                        count = int(part)
                        if i + 1 < len(parts):
                            status = parts[i + 1].rstrip(',')
                            if status in stats:
                                stats[status] = count
                            elif status == "passed":
                                stats["passed"] = count
                            elif status == "failed":
                                stats["failed"] = count
                            elif status == "skipped":
                                stats["skipped"] = count
                            elif status == "error" or status == "errors":
                                stats["errors"] = count
                break
        
        # 计算总数
        stats["total_tests"] = stats["passed"] + stats["failed"] + stats["skipped"] + stats["errors"]
        
        return stats
    
    def _extract_failures(self, lines: List[str]) -> List[Dict[str, str]]:
        """提取失败的测试详情"""
        failures = []
        current_failure = None
        in_failure_section = False
        
        for line in lines:
            # 检测失败部分开始
            if "FAILURES" in line or "ERRORS" in line:
                in_failure_section = True
                continue
            
            if in_failure_section:
                # 检测新的失败用例
                if line.startswith("_" * 20) and "::" in line:
                    if current_failure:
                        failures.append(current_failure)
                    
                    # 提取测试名称
                    test_name = line.split("::")[-1].strip("_ ")
                    current_failure = {
                        "test_name": test_name,
                        "full_name": line.strip("_ "),
                        "error_message": "",
                        "traceback": []
                    }
                
                elif current_failure and line.strip():
                    # 收集错误信息和堆栈跟踪
                    if "AssertionError" in line or "Exception" in line or "Error:" in line:
                        current_failure["error_message"] = line.strip()
                    else:
                        current_failure["traceback"].append(line)
        
        # 添加最后一个失败
        if current_failure:
            failures.append(current_failure)
        
        return failures
    
    def _extract_warnings(self, lines: List[str]) -> List[str]:
        """提取警告信息"""
        warnings = []
        
        for line in lines:
            if "warning" in line.lower() or "deprecated" in line.lower():
                warnings.append(line.strip())
        
        return warnings
    
    def _generate_comprehensive_report(self, test_results: Dict[str, Any]) -> Dict[str, Any]:
        """生成综合测试报告"""
        stats = test_results["statistics"]
        
        # 计算成功率
        total_tests = stats["total_tests"]
        passed_tests = stats["passed"]
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        # 生成报告
        report = {
            "test_run_info": {
                "start_time": self.start_time.isoformat(),
                "end_time": self.end_time.isoformat(),
                "duration_seconds": test_results["duration"],
                "duration_formatted": self._format_duration(test_results["duration"]),
                "pytest_return_code": test_results["return_code"],
                "success": test_results["return_code"] == 0
            },
            "test_statistics": {
                **stats,
                "success_rate": round(success_rate, 2),
                "failure_rate": round((stats["failed"] / total_tests * 100) if total_tests > 0 else 0, 2)
            },
            "test_results_by_module": self._analyze_results_by_module(test_results),
            "failures": test_results["failures"],
            "warnings": test_results["warnings"],
            "recommendations": self._generate_recommendations(test_results),
            "system_info": self._get_system_info(),
            "coverage_info": self._get_coverage_info()
        }
        
        # 保存报告到文件
        self._save_report_to_file(report)
        
        return report
    
    def _analyze_results_by_module(self, test_results: Dict[str, Any]) -> Dict[str, Any]:
        """按测试模块分析结果"""
        modules = {
            "database": {"passed": 0, "failed": 0, "total": 0},
            "auth_flow": {"passed": 0, "failed": 0, "total": 0},
            "members_api": {"passed": 0, "failed": 0, "total": 0},
            "tasks_workhours": {"passed": 0, "failed": 0, "total": 0},
            "attendance_system": {"passed": 0, "failed": 0, "total": 0},
            "data_import_cache": {"passed": 0, "failed": 0, "total": 0}
        }
        
        # 从stdout解析每个模块的结果
        lines = test_results["stdout"].split('\n')
        current_module = None
        
        for line in lines:
            # 检测测试文件
            for module_name in modules.keys():
                if f"test_{module_name}.py" in line:
                    current_module = module_name
                    break
            
            # 统计测试结果
            if current_module and ("::" in line and ("PASSED" in line or "FAILED" in line)):
                modules[current_module]["total"] += 1
                if "PASSED" in line:
                    modules[current_module]["passed"] += 1
                elif "FAILED" in line:
                    modules[current_module]["failed"] += 1
        
        # 计算每个模块的成功率
        for module_name, module_stats in modules.items():
            total = module_stats["total"]
            if total > 0:
                module_stats["success_rate"] = round(module_stats["passed"] / total * 100, 2)
            else:
                module_stats["success_rate"] = 0
        
        return modules
    
    def _generate_recommendations(self, test_results: Dict[str, Any]) -> List[str]:
        """根据测试结果生成改进建议"""
        recommendations = []
        stats = test_results["statistics"]
        
        # 基于失败率的建议
        if stats["failed"] > 0:
            recommendations.append(f"发现 {stats['failed']} 个失败的测试用例，建议优先修复")
        
        # 基于跳过测试的建议
        if stats["skipped"] > 0:
            recommendations.append(f"有 {stats['skipped']} 个测试被跳过，建议检查跳过的原因")
        
        # 基于错误的建议
        if stats["errors"] > 0:
            recommendations.append(f"有 {stats['errors']} 个测试出现错误，建议检查测试环境配置")
        
        # 基于警告的建议
        if len(test_results["warnings"]) > 0:
            recommendations.append(f"有 {len(test_results['warnings'])} 个警告，建议检查代码质量")
        
        # 基于成功率的建议
        success_rate = (stats["passed"] / stats["total_tests"] * 100) if stats["total_tests"] > 0 else 0
        if success_rate < 90:
            recommendations.append("测试成功率低于90%，建议加强代码质量管控")
        elif success_rate < 95:
            recommendations.append("测试成功率可以进一步提升，建议优化测试覆盖")
        else:
            recommendations.append("测试成功率良好，建议保持现有的开发质量")
        
        # 基于具体失败模块的建议
        module_results = self._analyze_results_by_module(test_results)
        for module_name, module_stats in module_results.items():
            if module_stats["failed"] > 0:
                recommendations.append(f"{module_name} 模块有失败测试，建议重点关注")
        
        return recommendations
    
    def _get_system_info(self) -> Dict[str, str]:
        """获取系统信息"""
        import platform
        import sys
        
        return {
            "python_version": sys.version,
            "platform": platform.platform(),
            "architecture": platform.architecture()[0],
            "processor": platform.processor(),
            "pytest_version": pytest.__version__
        }
    
    def _get_coverage_info(self) -> Dict[str, Any]:
        """获取代码覆盖率信息"""
        coverage_file = Path(self.test_directory).parent.parent / "coverage.json"
        
        if coverage_file.exists():
            try:
                with open(coverage_file, 'r', encoding='utf-8') as f:
                    coverage_data = json.load(f)
                
                return {
                    "total_coverage": coverage_data.get("totals", {}).get("percent_covered", 0),
                    "files_covered": len(coverage_data.get("files", {})),
                    "missing_lines": coverage_data.get("totals", {}).get("missing_lines", 0),
                    "covered_lines": coverage_data.get("totals", {}).get("covered_lines", 0)
                }
            except Exception as e:
                return {"error": f"无法读取覆盖率数据: {e}"}
        else:
            return {"error": "覆盖率数据文件不存在"}
    
    def _format_duration(self, seconds: float) -> str:
        """格式化持续时间"""
        minutes = int(seconds // 60)
        seconds = seconds % 60
        return f"{minutes}分{seconds:.2f}秒"
    
    def _save_report_to_file(self, report: Dict[str, Any]) -> None:
        """保存报告到文件"""
        reports_dir = Path(self.test_directory).parent / "reports"
        reports_dir.mkdir(exist_ok=True)
        
        # 保存JSON格式报告
        json_file = reports_dir / "comprehensive_test_report.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2, default=str)
        
        # 保存Markdown格式报告
        markdown_file = reports_dir / "test_report.md"
        self._generate_markdown_report(report, markdown_file)
        
        print(f"报告已保存到:")
        print(f"  JSON格式: {json_file}")
        print(f"  Markdown格式: {markdown_file}")
    
    def _generate_markdown_report(self, report: Dict[str, Any], output_file: Path) -> None:
        """生成Markdown格式的测试报告"""
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("# 后端系统集成测试报告\n\n")
            
            # 测试运行信息
            f.write("## 测试运行信息\n\n")
            run_info = report["test_run_info"]
            f.write(f"- **开始时间**: {run_info['start_time']}\n")
            f.write(f"- **结束时间**: {run_info['end_time']}\n")
            f.write(f"- **运行时长**: {run_info['duration_formatted']}\n")
            f.write(f"- **运行状态**: {'✅ 成功' if run_info['success'] else '❌ 失败'}\n\n")
            
            # 测试统计
            f.write("## 测试统计\n\n")
            stats = report["test_statistics"]
            f.write(f"- **总测试数**: {stats['total_tests']}\n")
            f.write(f"- **通过**: {stats['passed']} ({stats['success_rate']}%)\n")
            f.write(f"- **失败**: {stats['failed']} ({stats['failure_rate']}%)\n")
            f.write(f"- **跳过**: {stats['skipped']}\n")
            f.write(f"- **错误**: {stats['errors']}\n\n")
            
            # 模块测试结果
            f.write("## 各模块测试结果\n\n")
            f.write("| 模块 | 总数 | 通过 | 失败 | 成功率 |\n")
            f.write("|------|------|------|------|--------|\n")
            
            for module_name, module_stats in report["test_results_by_module"].items():
                f.write(f"| {module_name} | {module_stats['total']} | "
                       f"{module_stats['passed']} | {module_stats['failed']} | "
                       f"{module_stats['success_rate']}% |\n")
            f.write("\n")
            
            # 失败的测试
            if report["failures"]:
                f.write("## 失败的测试\n\n")
                for i, failure in enumerate(report["failures"], 1):
                    f.write(f"### {i}. {failure['test_name']}\n\n")
                    f.write(f"**完整名称**: `{failure['full_name']}`\n\n")
                    if failure["error_message"]:
                        f.write(f"**错误信息**: {failure['error_message']}\n\n")
                    if failure["traceback"]:
                        f.write("**堆栈跟踪**:\n```\n")
                        f.write('\n'.join(failure["traceback"][:10]))  # 只显示前10行
                        f.write("\n```\n\n")
            
            # 改进建议
            f.write("## 改进建议\n\n")
            for i, recommendation in enumerate(report["recommendations"], 1):
                f.write(f"{i}. {recommendation}\n")
            f.write("\n")
            
            # 代码覆盖率
            coverage_info = report["coverage_info"]
            if "error" not in coverage_info:
                f.write("## 代码覆盖率\n\n")
                f.write(f"- **总覆盖率**: {coverage_info['total_coverage']:.2f}%\n")
                f.write(f"- **覆盖文件数**: {coverage_info['files_covered']}\n")
                f.write(f"- **覆盖行数**: {coverage_info['covered_lines']}\n")
                f.write(f"- **未覆盖行数**: {coverage_info['missing_lines']}\n\n")
            
            # 系统信息
            f.write("## 系统信息\n\n")
            sys_info = report["system_info"]
            f.write(f"- **Python版本**: {sys_info['python_version']}\n")
            f.write(f"- **操作系统**: {sys_info['platform']}\n")
            f.write(f"- **架构**: {sys_info['architecture']}\n")
            f.write(f"- **pytest版本**: {sys_info['pytest_version']}\n\n")


def main():
    """主函数：运行集成测试套件"""
    print("=" * 60)
    print("后端系统集成测试套件")
    print("=" * 60)
    
    # 创建测试运行器
    runner = IntegrationTestRunner()
    
    # 运行测试套件
    try:
        results = runner.run_test_suite(
            generate_html_report=True,
            generate_json_report=True,
            coverage_report=True
        )
        
        if "error" in results:
            print(f"❌ 测试运行失败: {results['error']}")
            return 1
        
        # 显示摘要
        print("\n" + "=" * 60)
        print("测试运行摘要")
        print("=" * 60)
        
        run_info = results["test_run_info"]
        stats = results["test_statistics"]
        
        print(f"运行时长: {run_info['duration_formatted']}")
        print(f"总测试数: {stats['total_tests']}")
        print(f"通过: {stats['passed']} ({stats['success_rate']}%)")
        print(f"失败: {stats['failed']} ({stats['failure_rate']}%)")
        print(f"跳过: {stats['skipped']}")
        print(f"错误: {stats['errors']}")
        
        # 显示模块结果
        print("\n各模块结果:")
        for module_name, module_stats in results["test_results_by_module"].items():
            status = "✅" if module_stats["failed"] == 0 else "❌"
            print(f"  {status} {module_name}: {module_stats['passed']}/{module_stats['total']} ({module_stats['success_rate']}%)")
        
        # 显示建议
        if results["recommendations"]:
            print("\n改进建议:")
            for i, rec in enumerate(results["recommendations"], 1):
                print(f"  {i}. {rec}")
        
        # 返回适当的退出代码
        return 0 if run_info["success"] else 1
        
    except KeyboardInterrupt:
        print("\n测试被用户中断")
        return 130
    except Exception as e:
        print(f"❌ 运行测试时出现意外错误: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())