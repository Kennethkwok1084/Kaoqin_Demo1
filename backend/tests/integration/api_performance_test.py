"""
API性能测试脚本
测试新增业务逻辑API的性能和响应时间
"""

import asyncio
import time
import statistics
import sys
from pathlib import Path
from typing import List, Dict, Any

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

try:
    from fastapi.testclient import TestClient
    from app.main import app
    print("Successfully imported test dependencies")
except ImportError as e:
    print(f"Failed to import dependencies: {e}")
    sys.exit(1)


class APIPerformanceTester:
    """API性能测试器"""
    
    def __init__(self):
        self.client = TestClient(app)
        self.results = {
            "test_summary": {},
            "endpoint_results": {},
            "performance_metrics": {}
        }
    
    def measure_response_time(self, method: str, url: str, **kwargs) -> Dict[str, Any]:
        """测量API响应时间"""
        start_time = time.time()
        
        try:
            if method.upper() == "GET":
                response = self.client.get(url, **kwargs)
            elif method.upper() == "POST":
                response = self.client.post(url, **kwargs)
            elif method.upper() == "PUT":
                response = self.client.put(url, **kwargs)
            else:
                response = self.client.request(method, url, **kwargs)
            
            end_time = time.time()
            response_time = (end_time - start_time) * 1000  # 转换为毫秒
            
            return {
                "success": True,
                "status_code": response.status_code,
                "response_time_ms": response_time,
                "content_length": len(response.content) if hasattr(response, 'content') else 0
            }
            
        except Exception as e:
            end_time = time.time()
            response_time = (end_time - start_time) * 1000
            
            return {
                "success": False,
                "error": str(e),
                "response_time_ms": response_time,
                "content_length": 0
            }
    
    def run_endpoint_performance_test(self, endpoint_config: Dict[str, Any], iterations: int = 10) -> Dict[str, Any]:
        """运行单个端点的性能测试"""
        endpoint_name = endpoint_config["name"]
        method = endpoint_config["method"]
        url = endpoint_config["url"]
        params = endpoint_config.get("params", {})
        
        print(f"Testing {endpoint_name}...")
        
        response_times = []
        success_count = 0
        status_codes = []
        content_lengths = []
        
        for i in range(iterations):
            result = self.measure_response_time(
                method=method,
                url=url,
                params=params
            )
            
            response_times.append(result["response_time_ms"])
            content_lengths.append(result["content_length"])
            
            if result["success"]:
                success_count += 1
                status_codes.append(result["status_code"])
            
            # 避免过于频繁的请求
            time.sleep(0.1)
        
        # 计算统计指标
        avg_response_time = statistics.mean(response_times)
        min_response_time = min(response_times)
        max_response_time = max(response_times)
        median_response_time = statistics.median(response_times)
        
        # 计算成功率
        success_rate = (success_count / iterations) * 100
        
        # 性能评级
        performance_grade = self._calculate_performance_grade(avg_response_time)
        
        endpoint_result = {
            "endpoint_name": endpoint_name,
            "method": method,
            "url": url,
            "iterations": iterations,
            "success_count": success_count,
            "success_rate": success_rate,
            "response_times": {
                "average_ms": round(avg_response_time, 2),
                "min_ms": round(min_response_time, 2),
                "max_ms": round(max_response_time, 2),
                "median_ms": round(median_response_time, 2)
            },
            "content_length": {
                "average_bytes": round(statistics.mean(content_lengths), 2) if content_lengths else 0
            },
            "performance_grade": performance_grade,
            "status_codes": list(set(status_codes))
        }
        
        self.results["endpoint_results"][endpoint_name] = endpoint_result
        
        print(f"  - Average response time: {avg_response_time:.2f}ms")
        print(f"  - Success rate: {success_rate:.1f}%")
        print(f"  - Performance grade: {performance_grade}")
        
        return endpoint_result
    
    def _calculate_performance_grade(self, avg_response_time: float) -> str:
        """计算性能等级"""
        if avg_response_time < 100:
            return "Excellent"
        elif avg_response_time < 300:
            return "Good"
        elif avg_response_time < 1000:
            return "Fair"
        elif avg_response_time < 3000:
            return "Poor"
        else:
            return "Very Poor"
    
    def run_load_test(self, endpoint_config: Dict[str, Any], concurrent_requests: int = 5) -> Dict[str, Any]:
        """运行负载测试（模拟并发请求）"""
        endpoint_name = endpoint_config["name"]
        method = endpoint_config["method"]
        url = endpoint_config["url"]
        params = endpoint_config.get("params", {})
        
        print(f"Load testing {endpoint_name} with {concurrent_requests} concurrent requests...")
        
        start_time = time.time()
        results = []
        
        # 模拟并发请求（由于TestClient的限制，这里使用快速连续请求模拟）
        for i in range(concurrent_requests):
            result = self.measure_response_time(
                method=method,
                url=url,
                params=params
            )
            results.append(result)
        
        end_time = time.time()
        total_time = (end_time - start_time) * 1000  # 毫秒
        
        # 分析结果
        response_times = [r["response_time_ms"] for r in results]
        success_count = sum(1 for r in results if r["success"])
        
        load_test_result = {
            "endpoint_name": endpoint_name,
            "concurrent_requests": concurrent_requests,
            "total_time_ms": round(total_time, 2),
            "success_count": success_count,
            "success_rate": (success_count / concurrent_requests) * 100,
            "average_response_time_ms": round(statistics.mean(response_times), 2),
            "max_response_time_ms": round(max(response_times), 2),
            "requests_per_second": round(concurrent_requests / (total_time / 1000), 2)
        }
        
        print(f"  - Total time: {total_time:.2f}ms")
        print(f"  - Requests per second: {load_test_result['requests_per_second']:.2f}")
        print(f"  - Success rate: {load_test_result['success_rate']:.1f}%")
        
        return load_test_result
    
    def run_comprehensive_performance_test(self):
        """运行综合性能测试"""
        print("Starting comprehensive API performance testing...")
        
        # 定义测试端点
        test_endpoints = [
            # 健康检查API（无需认证）
            {
                "name": "Root Health Check",
                "method": "GET",
                "url": "/",
                "params": {}
            },
            {
                "name": "System Health Check",
                "method": "GET", 
                "url": "/health",
                "params": {}
            },
            {
                "name": "Tasks Health Check",
                "method": "GET",
                "url": "/api/v1/tasks/health",
                "params": {}
            },
            {
                "name": "Statistics Health Check",
                "method": "GET",
                "url": "/api/v1/statistics/health",
                "params": {}
            },
            
            # 需要认证的API（预期返回401/403）
            {
                "name": "Work Hours Recalculate",
                "method": "POST",
                "url": "/api/v1/tasks/work-hours/recalculate",
                "params": {}
            },
            {
                "name": "Pending Review List",
                "method": "GET",
                "url": "/api/v1/tasks/work-hours/pending-review",
                "params": {"page": 1, "size": 10}
            },
            {
                "name": "Work Hours Statistics",
                "method": "GET",
                "url": "/api/v1/tasks/work-hours/statistics",
                "params": {"group_by": "day"}
            },
            {
                "name": "Statistics Overview",
                "method": "GET",
                "url": "/api/v1/statistics/overview",
                "params": {}
            },
            {
                "name": "Efficiency Analysis",
                "method": "GET",
                "url": "/api/v1/statistics/efficiency",
                "params": {"group_by": "member"}
            },
            {
                "name": "Monthly Report",
                "method": "GET",
                "url": "/api/v1/statistics/monthly-report",
                "params": {"year": 2024, "month": 1}
            }
        ]
        
        # 运行性能测试
        print("\n1. Running response time tests...")
        all_response_times = []
        
        for endpoint in test_endpoints:
            result = self.run_endpoint_performance_test(endpoint, iterations=5)
            all_response_times.append(result["response_times"]["average_ms"])
        
        # 运行负载测试（仅对健康检查端点）
        print("\n2. Running load tests...")
        load_test_results = []
        
        health_check_endpoints = [ep for ep in test_endpoints if "health" in ep["name"].lower()]
        for endpoint in health_check_endpoints[:2]:  # 只测试前2个健康检查端点
            load_result = self.run_load_test(endpoint, concurrent_requests=10)
            load_test_results.append(load_result)
        
        # 计算总体性能指标
        self.results["performance_metrics"] = {
            "average_response_time_ms": round(statistics.mean(all_response_times), 2),
            "fastest_endpoint_ms": round(min(all_response_times), 2),
            "slowest_endpoint_ms": round(max(all_response_times), 2),
            "total_endpoints_tested": len(test_endpoints),
            "load_test_results": load_test_results
        }
        
        # 性能总结
        avg_time = self.results["performance_metrics"]["average_response_time_ms"]
        overall_grade = self._calculate_performance_grade(avg_time)
        
        self.results["test_summary"] = {
            "overall_performance_grade": overall_grade,
            "average_response_time_ms": avg_time,
            "recommendations": self._generate_performance_recommendations(avg_time)
        }
        
        return self.results
    
    def _generate_performance_recommendations(self, avg_response_time: float) -> List[str]:
        """生成性能优化建议"""
        recommendations = []
        
        if avg_response_time > 1000:
            recommendations.extend([
                "Consider implementing Redis caching for frequently accessed data",
                "Optimize database queries and add appropriate indexes",
                "Review and optimize business logic algorithms"
            ])
        elif avg_response_time > 300:
            recommendations.extend([
                "Consider adding caching for statistical calculations",
                "Review database connection pooling configuration",
                "Monitor and optimize slow database queries"
            ])
        else:
            recommendations.extend([
                "Performance is good, consider load balancing for production",
                "Monitor performance under real-world load conditions",
                "Consider implementing API rate limiting"
            ])
        
        return recommendations
    
    def generate_performance_report(self) -> str:
        """生成性能测试报告"""
        if not self.results.get("test_summary"):
            return "No test results available. Run tests first."
        
        report = []
        report.append("=== API Performance Test Report ===")
        report.append("")
        
        # 总体性能
        summary = self.results["test_summary"]
        metrics = self.results["performance_metrics"]
        
        report.append("Overall Performance:")
        report.append(f"  - Performance Grade: {summary['overall_performance_grade']}")
        report.append(f"  - Average Response Time: {summary['average_response_time_ms']:.2f}ms")
        report.append(f"  - Fastest Endpoint: {metrics['fastest_endpoint_ms']:.2f}ms")
        report.append(f"  - Slowest Endpoint: {metrics['slowest_endpoint_ms']:.2f}ms")
        report.append(f"  - Total Endpoints Tested: {metrics['total_endpoints_tested']}")
        report.append("")
        
        # 端点详情
        report.append("Endpoint Performance Details:")
        for name, result in self.results["endpoint_results"].items():
            report.append(f"  - {name}:")
            report.append(f"    * Average: {result['response_times']['average_ms']:.2f}ms")
            report.append(f"    * Success Rate: {result['success_rate']:.1f}%")
            report.append(f"    * Grade: {result['performance_grade']}")
        
        report.append("")
        
        # 负载测试结果
        if metrics.get("load_test_results"):
            report.append("Load Test Results:")
            for load_result in metrics["load_test_results"]:
                report.append(f"  - {load_result['endpoint_name']}:")
                report.append(f"    * Requests per second: {load_result['requests_per_second']:.2f}")
                report.append(f"    * Success rate: {load_result['success_rate']:.1f}%")
        
        report.append("")
        
        # 优化建议
        report.append("Performance Recommendations:")
        for rec in summary["recommendations"]:
            report.append(f"  - {rec}")
        
        return "\n".join(report)


def main():
    """主函数"""
    print("Starting API Performance Testing...")
    
    tester = APIPerformanceTester()
    
    try:
        # 运行综合性能测试
        results = tester.run_comprehensive_performance_test()
        
        # 生成报告
        report = tester.generate_performance_report()
        print(f"\n{report}")
        
        # 保存报告到文件
        report_file = project_root / "tests" / "reports" / "api_performance_report.txt"
        report_file.parent.mkdir(exist_ok=True)
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)
        
        print(f"\nPerformance report saved to: {report_file}")
        
        # 保存详细结果为JSON
        import json
        json_file = project_root / "tests" / "reports" / "api_performance_results.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        print(f"Detailed results saved to: {json_file}")
        
        # 根据性能等级返回退出码
        overall_grade = results["test_summary"]["overall_performance_grade"]
        if overall_grade in ["Excellent", "Good"]:
            print("\nAPI Performance Test: PASSED")
            return 0
        elif overall_grade == "Fair":
            print("\nAPI Performance Test: WARNING - Performance could be improved")
            return 1
        else:
            print("\nAPI Performance Test: FAILED - Performance needs attention")
            return 2
            
    except Exception as e:
        print(f"Performance testing failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)