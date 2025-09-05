#!/usr/bin/env python3
"""
测试覆盖率质量门禁系统
用于CI/CD流水线中的覆盖率质量检查和持续监控
"""

import json
import sys
import os
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple


class CoverageQualityGate:
    """覆盖率质量门禁"""
    
    def __init__(self, config_path: Optional[str] = None):
        self.config = self._load_config(config_path)
        self.results = {}
        
    def _load_config(self, config_path: Optional[str]) -> Dict:
        """加载配置"""
        default_config = {
            "thresholds": {
                "minimum_coverage": 30.0,  # 最低覆盖率要求
                "target_coverage": 75.0,   # 目标覆盖率
                "regression_threshold": -2.0,  # 覆盖率回退阈值
                "critical_files_threshold": 50.0  # 关键文件覆盖率要求
            },
            "critical_files": [
                "app/api/v1/tasks.py",
                "app/api/v1/statistics.py", 
                "app/api/v1/members.py",
                "app/api/v1/auth.py",
                "app/services/task_service.py",
                "app/services/work_hours_service.py",
                "app/core/security.py"
            ],
            "quality_checks": {
                "detect_fake_tests": True,
                "check_test_quality": True,
                "validate_critical_paths": True,
                "analyze_coverage_trends": True
            }
        }
        
        if config_path and os.path.exists(config_path):
            with open(config_path, 'r') as f:
                user_config = json.load(f)
                default_config.update(user_config)
                
        return default_config

    def run_coverage_analysis(self) -> bool:
        """运行覆盖率分析"""
        print("🔍 运行覆盖率分析...")
        
        # 运行测试并生成覆盖率报告
        cmd = "python3 -m pytest --cov=app --cov-report=json --cov-report=term-missing --cov-report=html -q"
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"❌ 测试执行失败: {result.stderr}")
            return False
            
        # 加载覆盖率数据
        if not os.path.exists('coverage.json'):
            print("❌ 覆盖率数据文件不存在")
            return False
            
        with open('coverage.json', 'r') as f:
            self.coverage_data = json.load(f)
            
        return True

    def check_minimum_coverage(self) -> Tuple[bool, str]:
        """检查最低覆盖率要求"""
        current_coverage = self.coverage_data['totals']['percent_covered']
        minimum_required = self.config['thresholds']['minimum_coverage']
        
        if current_coverage >= minimum_required:
            return True, f"✅ 覆盖率达标: {current_coverage:.2f}% >= {minimum_required}%"
        else:
            return False, f"❌ 覆盖率不达标: {current_coverage:.2f}% < {minimum_required}%"

    def check_coverage_regression(self) -> Tuple[bool, str]:
        """检查覆盖率回退"""
        history_file = 'coverage_history.json'
        
        if not os.path.exists(history_file):
            # 首次运行，创建历史记录
            self._save_coverage_history()
            return True, "✅ 首次运行，已建立覆盖率基线"
            
        with open(history_file, 'r') as f:
            history = json.load(f)
            
        if not history['records']:
            return True, "✅ 无历史记录，跳过回退检查"
            
        current_coverage = self.coverage_data['totals']['percent_covered']
        last_coverage = history['records'][-1]['coverage']
        regression_threshold = self.config['thresholds']['regression_threshold']
        
        coverage_change = current_coverage - last_coverage
        
        if coverage_change >= regression_threshold:
            self._save_coverage_history()
            return True, f"✅ 覆盖率变化正常: {coverage_change:+.2f}%"
        else:
            return False, f"❌ 覆盖率严重回退: {coverage_change:+.2f}% < {regression_threshold}%"

    def check_critical_files_coverage(self) -> Tuple[bool, str]:
        """检查关键文件覆盖率"""
        critical_files = self.config['critical_files']
        threshold = self.config['thresholds']['critical_files_threshold']
        
        failed_files = []
        results = []
        
        for file_path in critical_files:
            if file_path in self.coverage_data['files']:
                file_data = self.coverage_data['files'][file_path]
                covered_lines = len(file_data['executed_lines'])
                total_lines = covered_lines + len(file_data['missing_lines'])
                
                if total_lines > 0:
                    coverage_pct = (covered_lines / total_lines) * 100
                    
                    if coverage_pct >= threshold:
                        results.append(f"✅ {file_path}: {coverage_pct:.1f}%")
                    else:
                        results.append(f"❌ {file_path}: {coverage_pct:.1f}% < {threshold}%")
                        failed_files.append(file_path)
                else:
                    results.append(f"⚠️ {file_path}: 无可执行代码")
            else:
                results.append(f"⚠️ {file_path}: 未找到文件")
                
        success = len(failed_files) == 0
        message = f"关键文件覆盖率检查:\n" + "\n".join(results)
        
        return success, message

    def detect_fake_tests(self) -> Tuple[bool, str]:
        """检测假测试"""
        if not self.config['quality_checks']['detect_fake_tests']:
            return True, "⏭️ 跳过假测试检测"
            
        # 搜索假测试模式
        fake_test_patterns = [
            "assert True.*覆盖率",
            "assert True.*coverage", 
            "status_code in.*\\[.*401.*404.*405.*501.*\\].*assert True"
        ]
        
        fake_tests_found = []
        
        for pattern in fake_test_patterns:
            result = subprocess.run(
                f"grep -r -n '{pattern}' tests/",
                shell=True, capture_output=True, text=True
            )
            
            if result.returncode == 0 and result.stdout.strip():
                fake_tests_found.extend(result.stdout.strip().split('\n'))
                
        if fake_tests_found:
            message = f"❌ 发现 {len(fake_tests_found)} 个假测试:\n"
            message += "\n".join(fake_tests_found[:10])  # 只显示前10个
            if len(fake_tests_found) > 10:
                message += f"\n... 还有 {len(fake_tests_found) - 10} 个"
            return False, message
        else:
            return True, "✅ 未发现假测试模式"

    def analyze_test_quality(self) -> Tuple[bool, str]:
        """分析测试质量"""
        if not self.config['quality_checks']['check_test_quality']:
            return True, "⏭️ 跳过测试质量检查"
            
        quality_issues = []
        
        # 检查测试文件数量与应用文件数量比例
        test_files = len([f for f in Path('tests').rglob('test_*.py')])
        app_files = len([f for f in Path('app').rglob('*.py')])
        
        test_to_app_ratio = test_files / app_files if app_files > 0 else 0
        
        if test_to_app_ratio < 0.3:
            quality_issues.append(f"测试文件比例过低: {test_to_app_ratio:.2f} < 0.3")
            
        # 检查测试方法平均长度（过长可能是集成测试而非单元测试）
        result = subprocess.run(
            "find tests -name '*.py' -exec grep -c 'def test_' {} + | awk '{s+=$1; c++} END {print s/c}'",
            shell=True, capture_output=True, text=True
        )
        
        # 检查是否有足够的断言
        result = subprocess.run(
            "grep -r 'assert' tests/ | wc -l",
            shell=True, capture_output=True, text=True
        )
        
        if result.returncode == 0 and result.stdout.strip().isdigit():
            assert_count = int(result.stdout.strip())
            if assert_count < test_files * 5:  # 平均每个测试文件至少5个断言
                quality_issues.append(f"断言数量可能不足: {assert_count} assertions")
                
        if quality_issues:
            return False, "⚠️ 测试质量问题:\n" + "\n".join(quality_issues)
        else:
            return True, "✅ 测试质量检查通过"

    def generate_coverage_report(self) -> Dict:
        """生成覆盖率报告"""
        current_coverage = self.coverage_data['totals']['percent_covered']
        target_coverage = self.config['thresholds']['target_coverage']
        
        # 计算各模块覆盖率
        module_coverage = {}
        for file_path, file_data in self.coverage_data['files'].items():
            if file_path.startswith('app/'):
                module = file_path.split('/')[1] if '/' in file_path else 'root'
                if module not in module_coverage:
                    module_coverage[module] = {'covered': 0, 'total': 0, 'files': 0}
                    
                covered = len(file_data['executed_lines'])
                total = covered + len(file_data['missing_lines'])
                
                module_coverage[module]['covered'] += covered
                module_coverage[module]['total'] += total
                module_coverage[module]['files'] += 1
                
        # 计算模块覆盖率百分比
        for module in module_coverage:
            if module_coverage[module]['total'] > 0:
                module_coverage[module]['percentage'] = (
                    module_coverage[module]['covered'] / 
                    module_coverage[module]['total'] * 100
                )
            else:
                module_coverage[module]['percentage'] = 0
                
        return {
            'timestamp': datetime.now().isoformat(),
            'overall_coverage': current_coverage,
            'target_coverage': target_coverage,
            'coverage_gap': target_coverage - current_coverage,
            'module_coverage': module_coverage,
            'total_lines': self.coverage_data['totals']['num_statements'],
            'covered_lines': self.coverage_data['totals']['covered_lines'],
            'missing_lines': self.coverage_data['totals']['num_statements'] - self.coverage_data['totals']['covered_lines']
        }

    def _save_coverage_history(self):
        """保存覆盖率历史记录"""
        history_file = 'coverage_history.json'
        current_coverage = self.coverage_data['totals']['percent_covered']
        
        history = {'records': []}
        if os.path.exists(history_file):
            with open(history_file, 'r') as f:
                history = json.load(f)
                
        # 添加当前记录
        history['records'].append({
            'timestamp': datetime.now().isoformat(),
            'coverage': current_coverage,
            'commit_hash': os.getenv('GITHUB_SHA', 'unknown'),
            'branch': os.getenv('GITHUB_REF_NAME', 'unknown')
        })
        
        # 只保留最近30条记录
        history['records'] = history['records'][-30:]
        
        with open(history_file, 'w') as f:
            json.dump(history, f, indent=2)

    def run_quality_gate(self) -> bool:
        """运行完整的质量门禁检查"""
        print("🚪 运行覆盖率质量门禁检查...")
        print("=" * 60)
        
        # 运行覆盖率分析
        if not self.run_coverage_analysis():
            return False
            
        checks = [
            ("最低覆盖率检查", self.check_minimum_coverage),
            ("覆盖率回退检查", self.check_coverage_regression),
            ("关键文件覆盖率检查", self.check_critical_files_coverage),
            ("假测试检测", self.detect_fake_tests),
            ("测试质量分析", self.analyze_test_quality)
        ]
        
        all_passed = True
        results = []
        
        for check_name, check_func in checks:
            print(f"\n🔍 {check_name}...")
            try:
                passed, message = check_func()
                results.append({
                    'name': check_name,
                    'passed': passed,
                    'message': message
                })
                print(message)
                if not passed:
                    all_passed = False
            except Exception as e:
                error_msg = f"❌ 检查失败: {str(e)}"
                results.append({
                    'name': check_name,
                    'passed': False,
                    'message': error_msg
                })
                print(error_msg)
                all_passed = False
                
        # 生成总结报告
        print("\n" + "=" * 60)
        print("📊 覆盖率质量门禁总结")
        print("=" * 60)
        
        passed_checks = sum(1 for r in results if r['passed'])
        total_checks = len(results)
        
        print(f"检查通过: {passed_checks}/{total_checks}")
        
        if all_passed:
            print("🎉 恭喜！所有质量门禁检查通过")
        else:
            print("❌ 质量门禁检查失败，请修复以下问题:")
            for result in results:
                if not result['passed']:
                    print(f"   - {result['name']}")
                    
        # 生成详细报告
        report = self.generate_coverage_report()
        report['quality_gate_results'] = results
        report['overall_passed'] = all_passed
        
        with open('coverage_quality_report.json', 'w') as f:
            json.dump(report, f, indent=2)
            
        print(f"\n📄 详细报告已保存到: coverage_quality_report.json")
        
        return all_passed


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='覆盖率质量门禁检查')
    parser.add_argument('--config', help='配置文件路径')
    parser.add_argument('--ci', action='store_true', help='CI模式（失败时退出）')
    
    args = parser.parse_args()
    
    gate = CoverageQualityGate(args.config)
    success = gate.run_quality_gate()
    
    if args.ci and not success:
        print("\n💥 质量门禁失败，CI构建终止")
        sys.exit(1)
    elif success:
        print("\n✅ 质量门禁通过，可以继续部署")
        sys.exit(0)
    else:
        print("\n⚠️ 质量门禁失败，建议修复后再部署")
        sys.exit(1)


if __name__ == "__main__":
    main()