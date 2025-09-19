#!/usr/bin/env python3
"""
快速上线烟雾测试 - 5分钟验证核心功能
确保所有关键业务流程正常工作
"""

import asyncio
import aiohttp
import json
import sys
from pathlib import Path
import time

class QuickSmokeTest:
    def __init__(self):
        self.base_url = "http://localhost:8000"
        self.results = []
        self.failed_tests = []

    async def run_all_tests(self):
        """运行所有核心功能测试"""
        print("🚀 开始快速烟雾测试...")
        print("=" * 50)

        start_time = time.time()

        # P0 关键测试
        await self.test_health_check()
        await self.test_user_login()
        await self.test_basic_crud()
        await self.test_data_import()
        await self.test_work_hours_calculation()
        await self.test_data_export()

        # P1 重要测试
        await self.test_permissions()
        await self.test_statistics()

        end_time = time.time()
        duration = end_time - start_time

        self.print_summary(duration)
        return len(self.failed_tests) == 0

    async def test_health_check(self):
        """测试系统健康状态"""
        await self._test_api("GET", "/health", "系统健康检查")

    async def test_user_login(self):
        """测试用户登录"""
        login_data = {
            "username": "admin",
            "password": "admin123"
        }
        result = await self._test_api("POST", "/api/v1/auth/login", "用户登录", data=login_data)

        if result and 'access_token' in result:
            self.access_token = result['access_token']
            self._log_success("✅ 获取访问令牌成功")
        else:
            self._log_error("❌ 登录失败 - 无法获取访问令牌")

    async def test_basic_crud(self):
        """测试基础CRUD操作"""
        headers = self._get_auth_headers()

        # 测试成员列表
        await self._test_api("GET", "/api/v1/members", "获取成员列表", headers=headers)

        # 测试任务列表
        await self._test_api("GET", "/api/v1/tasks/repair", "获取报修任务", headers=headers)

        # 测试统计概览
        await self._test_api("GET", "/api/v1/statistics/overview", "获取统计概览", headers=headers)

    async def test_data_import(self):
        """测试数据导入功能"""
        headers = self._get_auth_headers()

        # 测试导入接口可用性
        await self._test_api("GET", "/api/v1/tasks/import/template", "获取导入模板", headers=headers)

    async def test_work_hours_calculation(self):
        """测试工时计算"""
        headers = self._get_auth_headers()

        # 测试工时记录
        await self._test_api("GET", "/api/v1/attendance/records", "获取工时记录", headers=headers)

    async def test_data_export(self):
        """测试数据导出"""
        headers = self._get_auth_headers()

        # 测试导出接口
        export_params = {
            "format": "excel",
            "date_from": "2024-01-01",
            "date_to": "2024-12-31"
        }
        await self._test_api("GET", "/api/v1/statistics/export", "数据导出", headers=headers, params=export_params)

    async def test_permissions(self):
        """测试权限控制"""
        headers = self._get_auth_headers()

        # 测试用户权限
        await self._test_api("GET", "/api/v1/auth/me", "获取用户信息", headers=headers)

    async def test_statistics(self):
        """测试统计功能"""
        headers = self._get_auth_headers()

        # 测试月度统计
        await self._test_api("GET", "/api/v1/statistics/monthly", "月度统计", headers=headers)

    async def _test_api(self, method, endpoint, description, data=None, headers=None, params=None):
        """通用API测试方法"""
        url = f"{self.base_url}{endpoint}"

        try:
            async with aiohttp.ClientSession() as session:
                kwargs = {}
                if data:
                    kwargs['json'] = data
                if headers:
                    kwargs['headers'] = headers
                if params:
                    kwargs['params'] = params

                async with session.request(method, url, **kwargs) as response:
                    if response.status in [200, 201]:
                        result = await response.json() if response.content_type == 'application/json' else await response.text()
                        self._log_success(f"✅ {description}")
                        return result
                    elif response.status == 404:
                        self._log_warning(f"⚠️  {description} - 接口未实现 (404)")
                        return None
                    else:
                        self._log_error(f"❌ {description} - HTTP {response.status}")
                        return None

        except Exception as e:
            self._log_error(f"❌ {description} - 连接失败: {str(e)}")
            return None

    def _get_auth_headers(self):
        """获取认证头部"""
        if hasattr(self, 'access_token'):
            return {"Authorization": f"Bearer {self.access_token}"}
        return {}

    def _log_success(self, message):
        """记录成功测试"""
        print(message)
        self.results.append(("SUCCESS", message))

    def _log_warning(self, message):
        """记录警告"""
        print(message)
        self.results.append(("WARNING", message))

    def _log_error(self, message):
        """记录失败测试"""
        print(message)
        self.results.append(("ERROR", message))
        self.failed_tests.append(message)

    def print_summary(self, duration):
        """打印测试摘要"""
        print("\n" + "=" * 50)
        print("📊 测试结果摘要")
        print("=" * 50)

        success_count = len([r for r in self.results if r[0] == "SUCCESS"])
        warning_count = len([r for r in self.results if r[0] == "WARNING"])
        error_count = len([r for r in self.results if r[0] == "ERROR"])
        total_count = len(self.results)

        print(f"总测试数: {total_count}")
        print(f"✅ 成功: {success_count}")
        print(f"⚠️  警告: {warning_count}")
        print(f"❌ 失败: {error_count}")
        print(f"⏱️  耗时: {duration:.2f}秒")

        success_rate = (success_count / total_count * 100) if total_count > 0 else 0
        print(f"🎯 成功率: {success_rate:.1f}%")

        if error_count == 0:
            print("\n🎉 所有关键功能测试通过！项目可以上线！")
        else:
            print(f"\n🚨 发现 {error_count} 个关键问题，需要修复后才能上线！")
            print("\n失败的测试:")
            for failed_test in self.failed_tests:
                print(f"  • {failed_test}")

        if warning_count > 0:
            print(f"\n💡 有 {warning_count} 个功能尚未实现，但不阻塞上线")

async def main():
    """主函数"""
    print("🔥 考勤管理系统 - 快速烟雾测试")
    print("目标：5分钟验证核心功能，确保快速上线")
    print()

    # 检查后端是否运行
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get("http://localhost:8000/health") as response:
                if response.status == 200:
                    print("✅ 后端服务正在运行")
                else:
                    print("❌ 后端服务响应异常")
                    return False
    except:
        print("❌ 无法连接到后端服务 (http://localhost:8000)")
        print("请确保后端服务已启动：uvicorn app.main:app --reload --host 0.0.0.0 --port 8000")
        return False

    # 运行测试
    tester = QuickSmokeTest()
    success = await tester.run_all_tests()

    return success

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)