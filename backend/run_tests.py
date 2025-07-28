#!/usr/bin/env python3
"""
测试运行脚本
提供多种测试运行方式的便捷接口
"""

import subprocess
import sys
import os
import argparse
from pathlib import Path


def run_command(command, description):
    """运行命令并显示结果"""
    print(f"\n{'='*60}")
    print(f"🧪 {description}")
    print(f"{'='*60}")
    print(f"执行命令: {command}")
    print("-" * 60)
    
    try:
        result = subprocess.run(command, shell=True, check=True, 
                              capture_output=False, text=True)
        print(f"\n✅ {description} - 成功完成")
        return True
    except subprocess.CalledProcessError as e:
        print(f"\n❌ {description} - 执行失败")
        print(f"错误码: {e.returncode}")
        return False
    except Exception as e:
        print(f"\n💥 {description} - 意外错误: {e}")
        return False


def install_dependencies():
    """安装测试依赖"""
    commands = [
        ("pip install pytest pytest-asyncio pytest-cov httpx faker factory-boy", 
         "安装测试依赖包"),
        ("pip install pytest-xdist pytest-benchmark", 
         "安装高级测试工具")
    ]
    
    print("📦 安装测试依赖...")
    for command, desc in commands:
        run_command(command, desc)


def run_auth_tests():
    """运行认证模块测试"""
    return run_command(
        "pytest tests/test_auth.py -v --tb=short",
        "认证模块测试"
    )


def run_all_tests():
    """运行所有测试"""
    return run_command(
        "pytest tests/ -v",
        "所有模块测试"
    )


def run_coverage_tests():
    """运行带覆盖率的测试"""
    return run_command(
        "pytest --cov=app --cov-report=term-missing --cov-report=html tests/",
        "代码覆盖率测试"
    )


def run_fast_tests():
    """运行快速测试（失败时停止）"""
    return run_command(
        "pytest tests/ -x --tb=short",
        "快速测试（遇到失败即停止）"
    )


def run_parallel_tests():
    """并行运行测试"""
    return run_command(
        "pytest tests/ -n 4 -v",
        "并行测试执行"
    )


def run_benchmark_tests():
    """运行性能基准测试"""
    return run_command(
        "pytest tests/ --benchmark-only",
        "性能基准测试"
    )


def run_specific_test(test_path):
    """运行特定测试"""
    return run_command(
        f"pytest {test_path} -v --tb=short",
        f"特定测试: {test_path}"
    )


def check_environment():
    """检查测试环境"""
    print("🔍 检查测试环境...")
    
    # 检查Python版本
    python_version = sys.version_info
    if python_version < (3, 12):
        print(f"⚠️  推荐Python 3.12+，当前版本: {python_version.major}.{python_version.minor}")
    else:
        print(f"✅ Python版本: {python_version.major}.{python_version.minor}")
    
    # 检查必要文件
    required_files = [
        "tests/test_auth.py",
        "tests/conftest.py", 
        "app/main.py",
        ".env"
    ]
    
    missing_files = []
    for file_path in required_files:
        if not Path(file_path).exists():
            missing_files.append(file_path)
        else:
            print(f"✅ {file_path} 存在")
    
    if missing_files:
        print(f"❌ 缺失文件: {missing_files}")
        return False
    
    # 检查环境变量
    env_file = Path(".env")
    if env_file.exists():
        print("✅ .env 配置文件存在")
    else:
        print("⚠️  .env 配置文件不存在，将使用默认配置")
    
    return True


def generate_test_report():
    """生成测试报告"""
    commands = [
        ("pytest --cov=app --cov-report=html --cov-report=term tests/",
         "生成HTML覆盖率报告"),
        ("pytest --junitxml=test-results.xml tests/",
         "生成JUnit XML报告")
    ]
    
    for command, desc in commands:
        run_command(command, desc)
    
    print("\n📊 测试报告已生成:")
    print("- HTML覆盖率报告: htmlcov/index.html")
    print("- JUnit XML报告: test-results.xml")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="考勤管理系统测试运行器")
    parser.add_argument("action", nargs="?", default="menu", 
                       choices=["menu", "install", "auth", "all", "coverage", 
                               "fast", "parallel", "benchmark", "report", "check"],
                       help="要执行的操作")
    parser.add_argument("--test", "-t", help="运行特定测试文件或用例")
    
    args = parser.parse_args()
    
    print("🧪 考勤管理系统 - 测试运行器")
    print("=" * 50)
    
    # 切换到正确目录
    os.chdir(Path(__file__).parent)
    
    if args.action == "install":
        install_dependencies()
    elif args.action == "check":
        check_environment()
    elif args.action == "auth":
        if check_environment():
            run_auth_tests()
    elif args.action == "all":
        if check_environment():
            run_all_tests()
    elif args.action == "coverage":
        if check_environment():
            run_coverage_tests()
    elif args.action == "fast":
        if check_environment():
            run_fast_tests()
    elif args.action == "parallel":
        if check_environment():
            run_parallel_tests()
    elif args.action == "benchmark":
        if check_environment():
            run_benchmark_tests()
    elif args.action == "report":
        if check_environment():
            generate_test_report()
    elif args.test:
        if check_environment():
            run_specific_test(args.test)
    else:
        # 显示交互式菜单
        show_menu()


def show_menu():
    """显示交互式菜单"""
    while True:
        print("\n🎯 请选择要执行的操作:")
        print("1. 🔍 检查测试环境")
        print("2. 📦 安装测试依赖")
        print("3. 🔐 运行认证模块测试")
        print("4. 🧪 运行所有测试")
        print("5. 📊 运行覆盖率测试")
        print("6. ⚡ 运行快速测试")
        print("7. 🚀 运行并行测试")
        print("8. 📈 运行性能测试")
        print("9. 📋 生成测试报告")
        print("0. 🚪 退出")
        
        choice = input("\n请输入选择 (0-9): ").strip()
        
        if choice == "0":
            print("👋 再见！")
            break
        elif choice == "1":
            check_environment()
        elif choice == "2":
            install_dependencies()
        elif choice == "3":
            if check_environment():
                run_auth_tests()
        elif choice == "4":
            if check_environment():
                run_all_tests()
        elif choice == "5":
            if check_environment():
                run_coverage_tests()
        elif choice == "6":
            if check_environment():
                run_fast_tests()
        elif choice == "7":
            if check_environment():
                run_parallel_tests()
        elif choice == "8":
            if check_environment():
                run_benchmark_tests()
        elif choice == "9":
            if check_environment():
                generate_test_report()
        else:
            print("❌ 无效选择，请重新输入")


if __name__ == "__main__":
    main()