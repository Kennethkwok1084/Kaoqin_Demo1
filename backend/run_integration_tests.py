#!/usr/bin/env python3

"""
集成测试运行脚本
用于CI/CD环境中运行所有集成测试
"""

import argparse
import asyncio
import json
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Dict, List


class IntegrationTestRunner:
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.results: Dict[str, Any] = {
            "start_time": None,
            "end_time": None,
            "total_duration": 0,
            "tests": {},
            "summary": {
                "total": 0,
                "passed": 0,
                "failed": 0,
                "errors": 0,
                "success_rate": 0,
            },
        }

    def log(self, message: str, level: str = "INFO"):
        if self.verbose or level != "DEBUG":
            timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
            print(f"[{timestamp}] {level}: {message}")

    def run_pytest_tests(self) -> Dict[str, Any]:
        """运行pytest集成测试"""
        self.log("开始运行pytest集成测试")

        cmd = [sys.executable, "-m", "pytest", "tests/integration/", "-v", "--tb=short"]

        # 尝试添加JSON报告（如果可用）
        try:
            import pytest_json_report

            cmd.extend(["--json-report", "--json-report-file=test_results.json"])
        except ImportError:
            self.log("pytest-json-report未安装，跳过JSON报告", "WARNING")

        if self.verbose:
            cmd.append("--verbose")

        try:
            result = subprocess.run(
                cmd,
                cwd=Path.cwd(),
                capture_output=True,
                text=True,
                timeout=300,  # 5分钟超时
            )

            # 读取JSON报告
            json_report = {}
            json_report_path = Path("test_results.json")
            if json_report_path.exists():
                try:
                    with open(json_report_path, "r", encoding="utf-8") as f:
                        json_report = json.load(f)
                except Exception as e:
                    self.log(f"无法读取JSON报告: {e}", "WARNING")

            return {
                "return_code": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "json_report": json_report,
            }

        except subprocess.TimeoutExpired:
            self.log("测试超时 (5分钟)", "ERROR")
            return {
                "return_code": 124,  # Timeout
                "stdout": "",
                "stderr": "测试执行超时",
                "json_report": {},
            }
        except Exception as e:
            self.log(f"运行pytest时发生错误: {e}", "ERROR")
            return {"return_code": 1, "stdout": "", "stderr": str(e), "json_report": {}}

    def run_custom_tests(self) -> Dict[str, Any]:
        """运行自定义集成测试"""
        self.log("运行自定义集成测试")

        custom_tests = [
            "tests/integration/simple_api_check.py",
            "tests/integration/quick_api_verification.py",
        ]

        results = {}
        for test_file in custom_tests:
            test_path = Path(test_file)
            if not test_path.exists():
                self.log(f"测试文件不存在: {test_file}", "WARNING")
                continue

            self.log(f"运行 {test_file}")
            try:
                result = subprocess.run(
                    [sys.executable, test_file],
                    cwd=Path.cwd(),
                    capture_output=True,
                    text=True,
                    timeout=120,
                )

                results[test_file] = {
                    "return_code": result.returncode,
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                }

                if result.returncode == 0:
                    self.log(f"PASS {test_file} 通过")
                else:
                    self.log(f"FAIL {test_file} 失败 (退出码: {result.returncode})", "ERROR")

            except subprocess.TimeoutExpired:
                self.log(f"TIMEOUT {test_file} 超时", "WARNING")
                results[test_file] = {
                    "return_code": 124,
                    "stdout": "",
                    "stderr": "测试超时",
                }
            except Exception as e:
                self.log(f"ERROR {test_file} 执行错误: {e}", "ERROR")
                results[test_file] = {"return_code": 1, "stdout": "", "stderr": str(e)}

        return results

    def run_api_verification(self) -> Dict[str, Any]:
        """运行API验证测试"""
        self.log("运行API验证测试")

        # 尝试运行API验证脚本
        verification_script = Path("tests/integration/quick_api_verification.py")
        if verification_script.exists():
            try:
                result = subprocess.run(
                    [sys.executable, str(verification_script)],
                    cwd=Path.cwd(),
                    capture_output=True,
                    text=True,
                    timeout=60,
                )

                return {
                    "return_code": result.returncode,
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                }
            except Exception as e:
                self.log(f"API验证失败: {e}", "ERROR")
                return {"return_code": 1, "stdout": "", "stderr": str(e)}
        else:
            self.log("API验证脚本不存在，跳过", "WARNING")
            return {"return_code": 0, "stdout": "API验证脚本不存在，跳过", "stderr": ""}

    def generate_report(self) -> str:
        """生成测试报告"""
        report_lines = [
            "=" * 50,
            "集成测试报告",
            "=" * 50,
            f"开始时间: {self.results['start_time']}",
            f"结束时间: {self.results['end_time']}",
            f"总耗时: {self.results['total_duration']:.2f}秒",
            "",
            "测试概览:",
            f"  总测试数: {self.results['summary']['total']}",
            f"  通过: {self.results['summary']['passed']}",
            f"  失败: {self.results['summary']['failed']}",
            f"  错误: {self.results['summary']['errors']}",
            f"  成功率: {self.results['summary']['success_rate']:.1f}%",
            "",
        ]

        # 添加详细结果
        for test_name, test_result in self.results["tests"].items():
            status = "PASS 通过" if test_result.get("return_code", 1) == 0 else "FAIL 失败"
            report_lines.extend(
                [
                    f"{test_name}: {status}",
                    f"  退出码: {test_result.get('return_code', 'N/A')}",
                ]
            )

            if test_result.get("stderr"):
                report_lines.append(f"  错误: {test_result['stderr'][:200]}...")

            report_lines.append("")

        report_lines.append("=" * 50)
        return "\n".join(report_lines)

    def save_results(self):
        """保存测试结果到文件"""
        # 保存JSON格式结果
        results_file = Path("integration_test_results.json")
        with open(results_file, "w", encoding="utf-8") as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)

        # 保存文本报告
        report_file = Path("integration_test_report.txt")
        with open(report_file, "w", encoding="utf-8") as f:
            f.write(self.generate_report())

        self.log(f"测试结果已保存到: {results_file}")
        self.log(f"测试报告已保存到: {report_file}")

    def run(self) -> int:
        """运行所有集成测试"""
        self.results["start_time"] = time.strftime("%Y-%m-%d %H:%M:%S")
        start_time = time.time()

        self.log("开始运行集成测试套件")

        # 1. 运行pytest测试
        pytest_result = self.run_pytest_tests()
        self.results["tests"]["pytest_integration"] = pytest_result

        # 2. 运行自定义测试
        custom_results = self.run_custom_tests()
        self.results["tests"].update(custom_results)

        # 3. 运行API验证
        api_result = self.run_api_verification()
        self.results["tests"]["api_verification"] = api_result

        # 计算总体结果
        end_time = time.time()
        self.results["end_time"] = time.strftime("%Y-%m-%d %H:%M:%S")
        self.results["total_duration"] = end_time - start_time

        # 统计结果
        total_tests = len(self.results["tests"])
        passed_tests = sum(
            1
            for result in self.results["tests"].values()
            if result.get("return_code", 1) == 0
        )
        failed_tests = total_tests - passed_tests

        self.results["summary"] = {
            "total": total_tests,
            "passed": passed_tests,
            "failed": failed_tests,
            "errors": failed_tests,  # 简化：将失败视为错误
            "success_rate": (
                (passed_tests / total_tests * 100) if total_tests > 0 else 0
            ),
        }

        # 保存结果
        self.save_results()

        # 打印报告
        print(self.generate_report())

        # 返回适当的退出码
        if passed_tests == total_tests:
            self.log("SUCCESS 所有集成测试通过!")
            return 0
        else:
            self.log(f"FAILED {failed_tests}/{total_tests} 测试失败", "ERROR")
            return 1


def main():
    parser = argparse.ArgumentParser(description="运行集成测试")
    parser.add_argument("--verbose", "-v", action="store_true", help="启用详细输出")
    parser.add_argument(
        "--timeout", "-t", type=int, default=600, help="总超时时间（秒），默认600秒"
    )

    args = parser.parse_args()

    runner = IntegrationTestRunner(verbose=args.verbose)

    try:
        exit_code = runner.run()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n测试被用户中断")
        sys.exit(130)
    except Exception as e:
        print(f"运行测试时发生未预期的错误: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
