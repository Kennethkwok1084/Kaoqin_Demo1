#!/usr/bin/env python3
"""
端到端冒烟测试脚本
一键启动后端并执行端到端冒烟测试

使用方法:
    python scripts/e2e_smoke.py --help
    python scripts/e2e_smoke.py --environment development
    python scripts/e2e_smoke.py --environment production --no-start-services
"""

import argparse
import asyncio
import json
import logging
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import aiohttp
import asyncpg
import pytest

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(), logging.FileHandler("e2e_smoke_test.log")],
)
logger = logging.getLogger(__name__)


class SmokeTestConfig:
    """冒烟测试配置"""

    def __init__(self, environment: str = "development"):
        self.environment = environment
        self.project_root = Path(__file__).parent.parent

        # 环境配置
        if environment == "production":
            self.base_url = "https://attendance.yourdomain.com"
            self.api_base_url = "https://api.attendance.yourdomain.com"
            self.db_host = "your-prod-db-host"
            self.db_port = 5432
        else:
            self.base_url = "http://localhost"
            self.api_base_url = "http://localhost:8000"
            self.db_host = "localhost"
            self.db_port = 5432

        # 测试配置
        self.timeout = 30
        self.retry_count = 3
        self.retry_delay = 5

        # 测试数据
        self.test_user = {
            "username": "test_smoke_user",
            "password": "TestSmokePass123!",
            "name": "冒烟测试用户",
            "student_id": "SMOKE001",
            "phone": "13800138000",
            "department": "信息化建设处",
            "class_name": "测试班",
        }


class ServiceManager:
    """服务管理器"""

    def __init__(self, config: SmokeTestConfig):
        self.config = config
        self.processes = []

    async def start_services(self) -> bool:
        """启动服务"""
        logger.info("启动后端服务...")

        try:
            if self.config.environment == "development":
                # 启动开发环境
                cmd = ["docker-compose", "up", "-d", "postgres", "redis", "backend"]
            else:
                # 启动生产环境
                cmd = ["docker-compose", "-f", "docker-compose.prod.yml", "up", "-d"]

            process = subprocess.Popen(
                cmd,
                cwd=self.config.project_root,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )

            stdout, stderr = process.communicate()

            if process.returncode != 0:
                logger.error(f"启动服务失败: {stderr.decode()}")
                return False

            logger.info("服务启动完成，等待服务就绪...")
            await self._wait_for_services()

            return True

        except Exception as e:
            logger.error(f"启动服务时发生异常: {str(e)}")
            return False

    async def stop_services(self):
        """停止服务"""
        logger.info("停止服务...")

        try:
            if self.config.environment == "development":
                cmd = ["docker-compose", "down"]
            else:
                cmd = ["docker-compose", "-f", "docker-compose.prod.yml", "down"]

            subprocess.run(cmd, cwd=self.config.project_root, check=True)
            logger.info("服务已停止")

        except Exception as e:
            logger.error(f"停止服务时发生异常: {str(e)}")

    async def _wait_for_services(self):
        """等待服务就绪"""
        max_attempts = 30
        attempt = 0

        while attempt < max_attempts:
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(
                        f"{self.config.api_base_url}/health",
                        timeout=aiohttp.ClientTimeout(total=5),
                    ) as response:
                        if response.status == 200:
                            logger.info("后端服务已就绪")
                            return

            except Exception:
                pass

            attempt += 1
            logger.info(f"等待服务就绪... ({attempt}/{max_attempts})")
            await asyncio.sleep(2)

        raise Exception("服务启动超时")


class DatabaseSmokeTest:
    """数据库冒烟测试"""

    def __init__(self, config: SmokeTestConfig):
        self.config = config

    async def test_database_connection(self) -> bool:
        """测试数据库连接"""
        logger.info("测试数据库连接...")

        try:
            # 从环境变量或配置文件获取数据库连接信息
            db_config = self._get_db_config()

            conn = await asyncpg.connect(
                host=db_config["host"],
                port=db_config["port"],
                user=db_config["user"],
                password=db_config["password"],
                database=db_config["database"],
            )

            # 执行简单查询
            result = await conn.fetchval("SELECT 1")
            assert result == 1

            # 检查关键表是否存在
            tables = await conn.fetch(
                """
                SELECT tablename FROM pg_tables
                WHERE schemaname = 'public'
                AND tablename IN ('members', 'repair_tasks', 'attendance_records')
            """
            )

            table_names = [row["tablename"] for row in tables]
            expected_tables = ["members", "repair_tasks", "attendance_records"]

            for table in expected_tables:
                if table not in table_names:
                    logger.error(f"关键表 {table} 不存在")
                    return False

            await conn.close()
            logger.info("数据库连接测试通过")
            return True

        except Exception as e:
            logger.error(f"数据库连接测试失败: {str(e)}")
            return False

    def _get_db_config(self) -> Dict[str, str]:
        """获取数据库配置"""
        if self.config.environment == "production":
            return {
                "host": os.getenv("DB_HOST", self.config.db_host),
                "port": int(os.getenv("DB_PORT", self.config.db_port)),
                "user": os.getenv("DB_USER", "kwok"),
                "password": os.getenv("DB_PASSWORD", "password"),
                "database": os.getenv("DB_NAME", "attendence_prod"),
            }
        else:
            return {
                "host": self.config.db_host,
                "port": self.config.db_port,
                "user": "kwok",
                "password": "Onjuju1084",
                "database": "attendence_dev",
            }


class APISmokeTest:
    """API冒烟测试"""

    def __init__(self, config: SmokeTestConfig):
        self.config = config
        self.session = None
        self.auth_token = None

    async def __aenter__(self):
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=self.config.timeout)
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def test_health_check(self) -> bool:
        """测试健康检查接口"""
        logger.info("测试健康检查接口...")

        try:
            async with self.session.get(
                f"{self.config.api_base_url}/health"
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    logger.info(f"健康检查通过: {data}")
                    return True
                else:
                    logger.error(f"健康检查失败，状态码: {response.status}")
                    return False

        except Exception as e:
            logger.error(f"健康检查接口测试失败: {str(e)}")
            return False

    async def test_authentication_flow(self) -> bool:
        """测试认证流程"""
        logger.info("测试用户认证流程...")

        try:
            # 1. 测试用户注册 (如果用户不存在)
            await self._ensure_test_user_exists()

            # 2. 测试用户登录
            login_data = {
                "username": self.config.test_user["username"],
                "password": self.config.test_user["password"],
            }

            async with self.session.post(
                f"{self.config.api_base_url}/api/v1/auth/login", json=login_data
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    self.auth_token = data["access_token"]
                    logger.info("用户登录测试通过")

                    # 3. 测试token验证
                    headers = {"Authorization": f"Bearer {self.auth_token}"}
                    async with self.session.get(
                        f"{self.config.api_base_url}/api/v1/auth/me", headers=headers
                    ) as me_response:
                        if me_response.status == 200:
                            user_data = await me_response.json()
                            logger.info(f"Token验证通过: {user_data['username']}")
                            return True
                        else:
                            logger.error(f"Token验证失败，状态码: {me_response.status}")
                            return False
                else:
                    logger.error(f"用户登录失败，状态码: {response.status}")
                    text = await response.text()
                    logger.error(f"响应内容: {text}")
                    return False

        except Exception as e:
            logger.error(f"认证流程测试失败: {str(e)}")
            return False

    async def test_core_api_endpoints(self) -> bool:
        """测试核心API接口"""
        logger.info("测试核心API接口...")

        if not self.auth_token:
            logger.error("未获得认证token，跳过API测试")
            return False

        headers = {"Authorization": f"Bearer {self.auth_token}"}

        # 测试接口列表
        test_endpoints = [
            ("GET", "/api/v1/tasks/repair", "获取报修任务列表"),
            ("GET", "/api/v1/members", "获取成员列表"),
            ("GET", "/api/v1/attendance", "获取考勤记录"),
            ("GET", "/api/v1/statistics/overview", "获取统计概览"),
            ("GET", "/api/v1/import/field-mapping", "获取字段映射"),
        ]

        success_count = 0

        for method, endpoint, description in test_endpoints:
            try:
                url = f"{self.config.api_base_url}{endpoint}"

                if method == "GET":
                    async with self.session.get(url, headers=headers) as response:
                        if response.status in [200, 201]:
                            logger.info(f"✅ {description} - 成功 ({response.status})")
                            success_count += 1
                        else:
                            logger.warning(
                                f"⚠️  {description} - 失败 ({response.status})"
                            )

            except Exception as e:
                logger.error(f"❌ {description} - 异常: {str(e)}")

        success_rate = success_count / len(test_endpoints)
        logger.info(
            f"核心API测试完成，成功率: {success_rate:.1%} ({success_count}/{len(test_endpoints)})"
        )

        # 至少80%的接口要通过测试
        return success_rate >= 0.8

    async def _ensure_test_user_exists(self):
        """确保测试用户存在"""
        try:
            # 尝试创建测试用户（如果已存在会失败，但不影响测试）
            user_data = self.config.test_user.copy()
            user_data["email"] = f"{user_data['username']}@test.com"

            async with self.session.post(
                f"{self.config.api_base_url}/api/v1/auth/register", json=user_data
            ) as response:
                if response.status in [200, 201]:
                    logger.info("测试用户创建成功")
                elif response.status == 400:
                    logger.info("测试用户已存在")
                else:
                    logger.warning(f"创建测试用户响应码: {response.status}")

        except Exception as e:
            logger.warning(f"创建测试用户时发生异常: {str(e)}")


class FrontendSmokeTest:
    """前端冒烟测试"""

    def __init__(self, config: SmokeTestConfig):
        self.config = config

    async def test_frontend_accessibility(self) -> bool:
        """测试前端可访问性"""
        logger.info("测试前端页面可访问性...")

        try:
            async with aiohttp.ClientSession() as session:
                # 测试主页
                async with session.get(self.config.base_url) as response:
                    if response.status == 200:
                        content = await response.text()
                        if "考勤管理系统" in content or "Attendance" in content:
                            logger.info("前端主页访问测试通过")
                            return True
                        else:
                            logger.error("前端主页内容异常")
                            return False
                    else:
                        logger.error(f"前端主页访问失败，状态码: {response.status}")
                        return False

        except Exception as e:
            logger.error(f"前端可访问性测试失败: {str(e)}")
            return False


class SmokeTestRunner:
    """冒烟测试执行器"""

    def __init__(self, config: SmokeTestConfig, start_services: bool = True):
        self.config = config
        self.start_services = start_services
        self.service_manager = ServiceManager(config)
        self.results = {}

    async def run_all_tests(self) -> Dict[str, bool]:
        """执行所有冒烟测试"""
        logger.info("开始执行端到端冒烟测试...")
        logger.info(f"测试环境: {self.config.environment}")
        logger.info(f"API地址: {self.config.api_base_url}")

        start_time = datetime.now()

        try:
            # 启动服务
            if self.start_services:
                if not await self.service_manager.start_services():
                    logger.error("服务启动失败，终止测试")
                    return {"service_start": False}

            # 1. 数据库测试
            db_test = DatabaseSmokeTest(self.config)
            self.results["database"] = await db_test.test_database_connection()

            # 2. API测试
            async with APISmokeTest(self.config) as api_test:
                self.results["health_check"] = await api_test.test_health_check()
                self.results["authentication"] = (
                    await api_test.test_authentication_flow()
                )
                self.results["core_apis"] = await api_test.test_core_api_endpoints()

            # 3. 前端测试
            frontend_test = FrontendSmokeTest(self.config)
            self.results["frontend"] = await frontend_test.test_frontend_accessibility()

            # 计算总体结果
            passed_tests = sum(1 for result in self.results.values() if result)
            total_tests = len(self.results)
            success_rate = passed_tests / total_tests if total_tests > 0 else 0

            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()

            # 输出测试结果
            self._print_results(success_rate, duration)

            return self.results

        except Exception as e:
            logger.error(f"测试执行过程中发生异常: {str(e)}")
            return {"exception": False}

        finally:
            # 清理服务
            if self.start_services:
                await self.service_manager.stop_services()

    def _print_results(self, success_rate: float, duration: float):
        """打印测试结果"""
        print("\n" + "=" * 60)
        print("端到端冒烟测试结果")
        print("=" * 60)

        for test_name, result in self.results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{test_name:20} : {status}")

        print("-" * 60)
        print(f"总体结果: {'✅ PASS' if success_rate >= 0.8 else '❌ FAIL'}")
        print(f"成功率: {success_rate:.1%}")
        print(f"执行时间: {duration:.1f}秒")

        if success_rate >= 0.8:
            print("\n🎉 冒烟测试通过！系统基本功能正常。")
        else:
            print("\n⚠️ 冒烟测试失败！请检查失败的测试项目。")

        print("=" * 60)


async def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="考勤管理系统端到端冒烟测试")
    parser.add_argument(
        "--environment",
        choices=["development", "staging", "production"],
        default="development",
        help="测试环境 (默认: development)",
    )
    parser.add_argument(
        "--no-start-services", action="store_true", help="不启动服务，假设服务已在运行"
    )
    parser.add_argument("--verbose", action="store_true", help="详细日志输出")

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # 创建配置
    config = SmokeTestConfig(args.environment)

    # 运行测试
    runner = SmokeTestRunner(config, start_services=not args.no_start_services)
    results = await runner.run_all_tests()

    # 返回退出码
    success_count = sum(1 for result in results.values() if result)
    total_count = len(results)
    success_rate = success_count / total_count if total_count > 0 else 0

    sys.exit(0 if success_rate >= 0.8 else 1)


if __name__ == "__main__":
    asyncio.run(main())
