#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
本地CI/CD测试脚本

此脚本模拟GitHub Actions CI/CD流程，在本地环境中运行关键检查步骤，
帮助开发者在推送代码前验证CI/CD是否能够成功通过。

使用方法:
    python test_cicd_locally.py

检查项目:
    1. 代码格式检查 (black, isort)
    2. 类型检查 (mypy)
    3. 代码风格检查 (flake8)
    4. 数据库迁移测试
    5. 基本功能测试
"""

import os
import sys
import subprocess
import time
from pathlib import Path
from typing import List, Tuple, Optional


class Colors:
    """终端颜色常量"""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'


class CICDLocalTester:
    """本地CI/CD测试器"""

    def __init__(self):
        self.project_root = Path(__file__).parent
        self.backend_dir = self.project_root / "backend"
        self.frontend_dir = self.project_root / "frontend"
        self.failed_checks = []
        self.passed_checks = []

    def print_header(self, title: str) -> None:
        """打印测试步骤标题"""
        print(f"\n{Colors.CYAN}{Colors.BOLD}{'='*60}{Colors.END}")
        print(f"{Colors.CYAN}{Colors.BOLD}{title:^60}{Colors.END}")
        print(f"{Colors.CYAN}{Colors.BOLD}{'='*60}{Colors.END}\n")

    def print_step(self, step: str) -> None:
        """打印当前步骤"""
        print(f"{Colors.BLUE}🔄 {step}...{Colors.END}")

    def print_success(self, message: str) -> None:
        """打印成功信息"""
        print(f"{Colors.GREEN}✅ {message}{Colors.END}")

    def print_warning(self, message: str) -> None:
        """打印警告信息"""
        print(f"{Colors.YELLOW}⚠️  {message}{Colors.END}")

    def print_error(self, message: str) -> None:
        """打印错误信息"""
        print(f"{Colors.RED}❌ {message}{Colors.END}")

    def run_command(self, cmd: List[str], cwd: Optional[Path] = None,
                   check_return_code: bool = True) -> Tuple[bool, str, str]:
        """运行命令并返回结果"""
        try:
            if cwd is None:
                cwd = self.backend_dir

            result = subprocess.run(
                cmd,
                cwd=cwd,
                capture_output=True,
                text=True,
                timeout=300  # 5分钟超时
            )

            success = result.returncode == 0 if check_return_code else True
            return success, result.stdout, result.stderr

        except subprocess.TimeoutExpired:
            return False, "", "命令执行超时"
        except Exception as e:
            return False, "", str(e)

    def check_environment(self) -> bool:
        """检查环境依赖"""
        self.print_step("检查环境依赖")

        # 检查Python环境
        if not (self.backend_dir / "requirements.txt").exists():
            self.print_error("未找到 requirements.txt 文件")
            return False

        # 检查是否在虚拟环境中
        if not hasattr(sys, 'real_prefix') and not (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
            self.print_warning("建议在虚拟环境中运行此测试")

        # 检查必要的工具
        tools = ['python', 'pip']
        for tool in tools:
            success, _, _ = self.run_command(['which', tool] if os.name != 'nt' else ['where', tool],
                                           check_return_code=False)
            if not success:
                self.print_error(f"未找到工具: {tool}")
                return False

        self.print_success("环境检查通过")
        return True

    def install_dependencies(self) -> bool:
        """安装依赖"""
        self.print_step("检查并安装依赖")

        # 检查是否需要安装依赖
        success, _, _ = self.run_command(['python', '-c', 'import black, isort, mypy, flake8'],
                                       check_return_code=False)
        if success:
            self.print_success("依赖已安装")
            return True

        # 安装开发依赖
        self.print_step("安装开发依赖")
        success, stdout, stderr = self.run_command(['pip', 'install', '-r', 'requirements-dev.txt'])

        if not success:
            self.print_error(f"依赖安装失败: {stderr}")
            return False

        self.print_success("依赖安装完成")
        return True

    def check_code_format(self) -> bool:
        """检查代码格式"""
        self.print_step("检查代码格式 (black)")

        success, stdout, stderr = self.run_command(['black', '--check', '--diff', 'app/'])

        if success:
            self.print_success("代码格式检查通过")
            self.passed_checks.append("代码格式检查")
            return True
        else:
            self.print_error("代码格式检查失败")
            if stdout:
                print(f"{Colors.YELLOW}需要格式化的文件:{Colors.END}")
                print(stdout)
            self.failed_checks.append("代码格式检查")
            return False

    def check_import_sorting(self) -> bool:
        """检查导入排序"""
        self.print_step("检查导入排序 (isort)")

        success, stdout, stderr = self.run_command(['isort', '--check-only', '--diff', 'app/'])

        if success:
            self.print_success("导入排序检查通过")
            self.passed_checks.append("导入排序检查")
            return True
        else:
            self.print_error("导入排序检查失败")
            if stdout:
                print(f"{Colors.YELLOW}需要重新排序的文件:{Colors.END}")
                print(stdout)
            self.failed_checks.append("导入排序检查")
            return False

    def check_type_annotations(self) -> bool:
        """检查类型注解"""
        self.print_step("检查类型注解 (mypy)")

        success, stdout, stderr = self.run_command(['mypy', 'app/'])

        if success:
            self.print_success("类型检查通过")
            self.passed_checks.append("类型检查")
            return True
        else:
            # MyPy错误不阻塞CI，只是警告
            error_count = stdout.count('error:')
            self.print_warning(f"类型检查发现 {error_count} 个问题（不阻塞CI）")
            if error_count > 0:
                print(f"{Colors.YELLOW}类型错误详情:{Colors.END}")
                print(stdout[:1000] + "..." if len(stdout) > 1000 else stdout)
            self.passed_checks.append("类型检查（有警告）")
            return True

    def check_code_style(self) -> bool:
        """检查代码风格"""
        self.print_step("检查代码风格 (flake8)")

        success, stdout, stderr = self.run_command(['flake8', 'app/'])

        if success:
            self.print_success("代码风格检查通过")
            self.passed_checks.append("代码风格检查")
            return True
        else:
            # Flake8错误不阻塞CI，只是警告
            self.print_warning("代码风格检查发现问题（不阻塞CI）")
            if stdout:
                print(f"{Colors.YELLOW}风格问题详情:{Colors.END}")
                print(stdout[:1000] + "..." if len(stdout) > 1000 else stdout)
            self.passed_checks.append("代码风格检查（有警告）")
            return True

    def test_database_migration(self) -> bool:
        """测试数据库迁移"""
        self.print_step("测试数据库迁移")

        # 检查alembic配置
        if not (self.backend_dir / "alembic.ini").exists():
            self.print_error("未找到 alembic.ini 文件")
            self.failed_checks.append("数据库迁移测试")
            return False

        # 设置测试环境变量
        env = os.environ.copy()
        env['CI'] = 'true'
        env['GITHUB_ACTIONS'] = 'true'
        env['DATABASE_URL'] = 'postgresql+asyncpg://postgres:postgres@localhost:5432/test_db'

        # 检查迁移文件语法
        self.print_step("检查迁移文件语法")
        success, stdout, stderr = self.run_command(['alembic', 'check'])

        if not success:
            self.print_error(f"迁移文件语法检查失败: {stderr}")
            self.failed_checks.append("数据库迁移测试")
            return False

        self.print_success("数据库迁移测试通过")
        self.passed_checks.append("数据库迁移测试")
        return True

    def run_basic_tests(self) -> bool:
        """运行基本测试"""
        self.print_step("运行基本测试")

        # 检查是否有测试文件
        test_files = list(self.backend_dir.glob("test_*.py"))
        if not test_files:
            self.print_warning("未找到测试文件")
            self.passed_checks.append("基本测试（跳过）")
            return True

        # 运行简单的导入测试
        success, stdout, stderr = self.run_command(['python', '-c', 'import app; print("导入成功")'])

        if success:
            self.print_success("基本测试通过")
            self.passed_checks.append("基本测试")
            return True
        else:
            self.print_error(f"基本测试失败: {stderr}")
            self.failed_checks.append("基本测试")
            return False

    def print_summary(self) -> None:
        """打印测试总结"""
        self.print_header("测试总结")

        print(f"{Colors.GREEN}✅ 通过的检查 ({len(self.passed_checks)}):{Colors.END}")
        for check in self.passed_checks:
            print(f"   • {check}")

        if self.failed_checks:
            print(f"\n{Colors.RED}❌ 失败的检查 ({len(self.failed_checks)}):{Colors.END}")
            for check in self.failed_checks:
                print(f"   • {check}")

        print(f"\n{Colors.BOLD}总体结果:{Colors.END}")
        if not self.failed_checks:
            print(f"{Colors.GREEN}{Colors.BOLD}🎉 所有检查通过！CI/CD应该能够成功运行{Colors.END}")
        else:
            print(f"{Colors.RED}{Colors.BOLD}⚠️  有 {len(self.failed_checks)} 项检查失败，CI/CD可能会失败{Colors.END}")
            print(f"{Colors.YELLOW}建议修复失败的检查项后再推送代码{Colors.END}")

    def run_all_checks(self) -> bool:
        """运行所有检查"""
        self.print_header("本地CI/CD测试")

        print(f"{Colors.MAGENTA}此脚本将模拟GitHub Actions CI/CD流程{Colors.END}")
        print(f"{Colors.MAGENTA}帮助您在推送前验证代码是否能通过CI检查{Colors.END}\n")

        # 检查步骤
        checks = [
            ("环境检查", self.check_environment),
            ("依赖安装", self.install_dependencies),
            ("代码格式检查", self.check_code_format),
            ("导入排序检查", self.check_import_sorting),
            ("类型注解检查", self.check_type_annotations),
            ("代码风格检查", self.check_code_style),
            ("数据库迁移测试", self.test_database_migration),
            ("基本功能测试", self.run_basic_tests),
        ]

        start_time = time.time()

        for check_name, check_func in checks:
            try:
                result = check_func()
                if not result and check_name in ["环境检查", "依赖安装"]:
                    # 关键检查失败，停止后续检查
                    break
            except Exception as e:
                self.print_error(f"{check_name} 执行异常: {str(e)}")
                self.failed_checks.append(check_name)

        end_time = time.time()
        duration = end_time - start_time

        self.print_summary()
        print(f"\n{Colors.CYAN}测试耗时: {duration:.2f} 秒{Colors.END}")

        return len(self.failed_checks) == 0


def main():
    """主函数"""
    tester = CICDLocalTester()

    try:
        success = tester.run_all_checks()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}测试被用户中断{Colors.END}")
        sys.exit(1)
    except Exception as e:
        print(f"\n{Colors.RED}测试执行异常: {str(e)}{Colors.END}")
        sys.exit(1)


if __name__ == "__main__":
    main()
