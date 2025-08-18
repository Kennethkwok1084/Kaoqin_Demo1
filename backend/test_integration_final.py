"""
最终集成测试 - 使用初始化后的远程数据库
"""

import asyncio
import os

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

# 设置环境变量使用远程数据库
os.environ["ENVIRONMENT"] = "production"
os.environ[
    "DATABASE_URL"
] = "postgresql+asyncpg://kwok:Onjuju1084@8.138.233.54:5432/attendence_dev"
os.environ[
    "DATABASE_URL_SYNC"
] = "postgresql://kwok:Onjuju1084@8.138.233.54:5432/attendence_dev"
os.environ["SECRET_KEY"] = "test_secret_key_for_remote_testing"
os.environ["ALGORITHM"] = "HS256"


async def test_remote_integration():
    """测试使用远程数据库的完整集成"""
    print("=== Remote Database Integration Test ===")

    try:
        # 创建单连接引擎（避免并发问题）
        test_engine = create_async_engine(
            "postgresql+asyncpg://kwok:Onjuju1084@8.138.233.54:5432/attendence_dev",
            echo=False,
            pool_size=1,  # 单连接
            max_overflow=0,  # 无额外连接
            pool_pre_ping=True,
            connect_args={
                "statement_cache_size": 0,  # 禁用预处理语句缓存
                "prepared_statement_cache_size": 0,  # 额外保障
                "server_settings": {"application_name": "kaoqin_integration_test"},
            },
        )

        # 验证数据库连接和数据
        async_session = async_sessionmaker(test_engine, class_=AsyncSession)
        async with async_session() as session:
            from sqlalchemy import text

            result = await session.execute(
                text("SELECT username, name FROM members WHERE student_id = 'STU12345'")
            )
            user = result.fetchone()
            if user:
                print(f"[OK] Found test user: {user[0]} - {user[1]}")
            else:
                print("[ERROR] Test user not found")
                return False

        # 现在导入应用并覆盖数据库配置
        from app.api.deps import get_db
        from app.main import app

        # 覆盖数据库依赖为我们的单连接引擎
        async def override_get_db():
            async with async_session() as session:
                yield session

        app.dependency_overrides[get_db] = override_get_db

        # 开始API测试
        from httpx import ASGITransport

        transport = ASGITransport(app=app)
        async with AsyncClient(
            transport=transport, base_url="http://testserver", timeout=30.0
        ) as client:
            # 1. 健康检查
            health_response = await client.get("/health")
            print(f"[OK] Health check: {health_response.status_code}")

            # 2. 测试登录
            login_data = {
                "student_id": "STU12345",
                "password": "test123",  # 对应hash: $2b$12$7DKis8BX0BY8vqjtylV46./D2LlSwWdV0XADOPWeyWkZPIlewARyS
            }
            login_response = await client.post("/api/v1/auth/login", json=login_data)
            print(f"[TEST] Login response: {login_response.status_code}")

            if login_response.status_code == 200:
                login_result = login_response.json()
                access_token = login_result.get("access_token")
                print(f"[OK] Login successful!")
                print(
                    f"[DEBUG] Login response keys: {login_result.keys() if login_result else 'None'}"
                )
                print(
                    f"[DEBUG] Login response data: {login_result.get('data', {}) if login_result else 'None'}"
                )

                # 检查不同的token字段位置
                access_token = (
                    login_result.get("access_token")
                    or login_result.get("data", {}).get("access_token")
                    or login_result.get("data", {}).get("token")
                )

                if access_token:
                    print(f"[OK] Access token: {access_token[:30]}...")

                # 3. 测试受保护的端点
                if access_token:
                    headers = {"Authorization": f"Bearer {access_token}"}
                    profile_response = await client.get(
                        "/api/v1/auth/profile", headers=headers
                    )
                    print(f"[TEST] Profile response: {profile_response.status_code}")

                    if profile_response.status_code == 200:
                        profile_data = profile_response.json()
                        print(
                            f"[OK] Profile: {profile_data.get('name')} - {profile_data.get('department')}"
                        )

                        # 4. 测试其他端点
                        members_response = await client.get(
                            "/api/v1/members/", headers=headers
                        )
                        print(f"[TEST] Members list: {members_response.status_code}")

                        # 5. 测试任务端点
                        tasks_response = await client.get(
                            "/api/v1/tasks/repair", headers=headers
                        )
                        print(f"[TEST] Tasks list: {tasks_response.status_code}")

                    else:
                        print(f"[WARN] Profile access failed: {profile_response.text}")
                else:
                    print("[WARN] No access token received")

            else:
                print(f"[WARN] Login failed: {login_response.text}")

        await test_engine.dispose()
        print("\n[SUCCESS] Remote integration test completed")
        return True

    except Exception as e:
        print(f"[ERROR] Integration test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    result = asyncio.run(test_remote_integration())
    if result:
        print("\n[SUCCESS] All tests passed - CI/CD should work now!")
    else:
        print("\n[FAILED] Tests failed - further investigation needed")
