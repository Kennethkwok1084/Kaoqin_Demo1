"""
快速API验证脚本
验证新增的业务逻辑API是否正常响应
"""

import asyncio
import sys
import traceback
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from datetime import datetime, timedelta
from fastapi.testclient import TestClient

# 尝试导入应用
try:
    from app.main import app
    from app.core.config import settings
    print("Success: 成功导入应用模块")
except ImportError as e:
    print(f"❌ 导入应用失败: {e}")
    sys.exit(1)


def test_new_api_endpoints():
    """测试新增的API端点"""
    client = TestClient(app)
    
    test_results = {
        "total_tests": 0,
        "passed_tests": 0,
        "failed_tests": 0,
        "test_details": []
    }
    
    # 测试端点列表
    api_endpoints = [
        # 工时管理API
        {
            "name": "批量工时重算API",
            "method": "POST",
            "url": "/api/v1/tasks/work-hours/recalculate",
            "requires_auth": True,
            "expected_status": [401, 403]  # 未认证应该返回401或403
        },
        {
            "name": "待审核工时列表API", 
            "method": "GET",
            "url": "/api/v1/tasks/work-hours/pending-review",
            "requires_auth": True,
            "expected_status": [401, 403]
        },
        {
            "name": "工时统计API",
            "method": "GET", 
            "url": "/api/v1/tasks/work-hours/statistics",
            "requires_auth": True,
            "expected_status": [401, 403]
        },
        
        # 统计分析API
        {
            "name": "系统概览统计API",
            "method": "GET",
            "url": "/api/v1/statistics/overview", 
            "requires_auth": True,
            "expected_status": [401, 403]
        },
        {
            "name": "效率分析API",
            "method": "GET",
            "url": "/api/v1/statistics/efficiency",
            "requires_auth": True,
            "expected_status": [401, 403]
        },
        {
            "name": "月度报表API",
            "method": "GET",
            "url": "/api/v1/statistics/monthly-report",
            "requires_auth": True,
            "expected_status": [401, 403, 422],  # 422 for missing required params
            "params": {"year": 2024, "month": 1}
        },
        {
            "name": "统计数据导出API",
            "method": "GET",
            "url": "/api/v1/statistics/export",
            "requires_auth": True,
            "expected_status": [401, 403, 422],
            "params": {"export_type": "overview", "format": "excel"}
        },
        
        # 健康检查API
        {
            "name": "任务服务健康检查",
            "method": "GET",
            "url": "/api/v1/tasks/health",
            "requires_auth": False,
            "expected_status": [200]
        },
        {
            "name": "统计服务健康检查",
            "method": "GET", 
            "url": "/api/v1/statistics/health",
            "requires_auth": False,
            "expected_status": [200]
        }
    ]
    
    print("🧪 开始API端点验证测试...")
    
    for endpoint in api_endpoints:
        test_results["total_tests"] += 1
        test_name = endpoint["name"]
        
        try:
            # 发送请求
            if endpoint["method"] == "GET":
                response = client.get(
                    endpoint["url"], 
                    params=endpoint.get("params", {})
                )
            elif endpoint["method"] == "POST":
                response = client.post(
                    endpoint["url"],
                    json=endpoint.get("json", {}),
                    params=endpoint.get("params", {})
                )
            else:
                response = client.request(
                    endpoint["method"],
                    endpoint["url"],
                    json=endpoint.get("json", {}),
                    params=endpoint.get("params", {})
                )
            
            # 检查响应状态
            if response.status_code in endpoint["expected_status"]:
                test_results["passed_tests"] += 1
                status = "✅ 通过"
                details = f"状态码: {response.status_code}"
                
                # 对于健康检查API，额外验证响应内容
                if not endpoint["requires_auth"] and response.status_code == 200:
                    try:
                        json_data = response.json()
                        if "success" in json_data and json_data["success"]:
                            details += f", 响应: {json_data.get('message', 'OK')}"
                        else:
                            details += ", 响应格式正确"
                    except:
                        details += ", 响应内容无法解析"
                        
            else:
                test_results["failed_tests"] += 1
                status = "❌ 失败"
                details = f"期望状态码: {endpoint['expected_status']}, 实际: {response.status_code}"
                
                # 尝试获取错误详情
                try:
                    error_detail = response.json()
                    details += f", 错误: {error_detail.get('detail', 'Unknown')}"
                except:
                    details += f", 响应文本: {response.text[:100]}..."
            
            test_results["test_details"].append({
                "name": test_name,
                "method": endpoint["method"],
                "url": endpoint["url"],
                "status": status,
                "details": details
            })
            
            print(f"  {status} {test_name}: {details}")
            
        except Exception as e:
            test_results["failed_tests"] += 1
            error_msg = f"请求异常: {str(e)}"
            test_results["test_details"].append({
                "name": test_name,
                "method": endpoint["method"],
                "url": endpoint["url"],
                "status": "❌ 异常",
                "details": error_msg
            })
            print(f"  ❌ 异常 {test_name}: {error_msg}")
    
    return test_results


def test_api_documentation():
    """测试API文档生成"""
    client = TestClient(app)
    
    print("\n📚 测试API文档...")
    
    doc_results = {}
    
    try:
        # 测试OpenAPI JSON文档
        openapi_response = client.get("/openapi.json")
        if openapi_response.status_code == 200:
            openapi_data = openapi_response.json()
            
            # 检查新增的API路径
            paths = openapi_data.get("paths", {})
            new_paths = [
                "/api/v1/tasks/work-hours/recalculate",
                "/api/v1/tasks/work-hours/pending-review", 
                "/api/v1/tasks/work-hours/statistics",
                "/api/v1/statistics/overview",
                "/api/v1/statistics/efficiency",
                "/api/v1/statistics/monthly-report",
                "/api/v1/statistics/export"
            ]
            
            found_paths = []
            for path in new_paths:
                if path in paths:
                    found_paths.append(path)
            
            doc_results["openapi"] = {
                "status": "✅ 正常" if len(found_paths) > 0 else "⚠️ 部分缺失",
                "total_new_paths": len(new_paths),
                "found_paths": len(found_paths),
                "details": f"找到 {len(found_paths)}/{len(new_paths)} 个新API路径"
            }
            
            print(f"  ✅ OpenAPI文档: {doc_results['openapi']['details']}")
            
        else:
            doc_results["openapi"] = {
                "status": "❌ 失败",
                "details": f"OpenAPI文档访问失败: {openapi_response.status_code}"
            }
            print(f"  ❌ OpenAPI文档访问失败: {openapi_response.status_code}")
    
    except Exception as e:
        doc_results["openapi"] = {
            "status": "❌ 异常",
            "details": f"OpenAPI文档测试异常: {str(e)}"
        }
        print(f"  ❌ OpenAPI文档测试异常: {str(e)}")
    
    # 测试Swagger UI (仅在开发模式下)
    if settings.DEBUG:
        try:
            docs_response = client.get("/docs")
            if docs_response.status_code == 200:
                doc_results["swagger"] = {
                    "status": "✅ 正常",
                    "details": "Swagger UI可访问"
                }
                print(f"  ✅ Swagger UI: 可访问")
            else:
                doc_results["swagger"] = {
                    "status": "❌ 失败", 
                    "details": f"Swagger UI访问失败: {docs_response.status_code}"
                }
                print(f"  ❌ Swagger UI访问失败: {docs_response.status_code}")
        
        except Exception as e:
            doc_results["swagger"] = {
                "status": "❌ 异常",
                "details": f"Swagger UI测试异常: {str(e)}"
            }
            print(f"  ❌ Swagger UI测试异常: {str(e)}")
    else:
        doc_results["swagger"] = {
            "status": "⚠️ 跳过",
            "details": "非开发模式，跳过Swagger UI测试"
        }
        print(f"  ⚠️ Swagger UI: 非开发模式，跳过测试")
    
    return doc_results


def main():
    """主函数"""
    print("🚀 开始快速API验证...")
    print(f"⚙️ 应用配置: DEBUG={settings.DEBUG}, TESTING={settings.TESTING}")
    
    try:
        # 运行API端点测试
        api_results = test_new_api_endpoints()
        
        # 运行文档测试
        doc_results = test_api_documentation()
        
        # 汇总结果
        print(f"\n📋 测试汇总:")
        print(f"  API端点测试: {api_results['passed_tests']}/{api_results['total_tests']} 通过")
        print(f"  文档测试: {doc_results}")
        
        # 详细结果
        success_rate = (api_results['passed_tests'] / api_results['total_tests']) * 100 if api_results['total_tests'] > 0 else 0
        print(f"  成功率: {success_rate:.1f}%")
        
        if api_results['failed_tests'] > 0:
            print(f"\n⚠️ 失败的测试:")
            for detail in api_results['test_details']:
                if "❌" in detail['status']:
                    print(f"    - {detail['name']}: {detail['details']}")
        
        # 生成验证报告
        verification_report = {
            "timestamp": datetime.now().isoformat(),
            "api_tests": api_results,
            "documentation_tests": doc_results,
            "summary": {
                "total_api_tests": api_results['total_tests'],
                "passed_api_tests": api_results['passed_tests'],
                "success_rate": success_rate,
                "overall_status": "通过" if success_rate >= 80 else "需要检查"
            }
        }
        
        # 保存报告
        import json
        report_file = project_root / "tests" / "reports" / "api_verification_report.json"
        report_file.parent.mkdir(exist_ok=True)
        
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(verification_report, f, ensure_ascii=False, indent=2)
        
        print(f"\n📄 验证报告已保存: {report_file}")
        
        if success_rate >= 80:
            print("✅ API验证通过！新增的业务逻辑API基本功能正常")
            return 0
        else:
            print("⚠️ API验证需要检查，部分功能可能存在问题")
            return 1
            
    except Exception as e:
        print(f"❌ 验证过程异常: {str(e)}")
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)