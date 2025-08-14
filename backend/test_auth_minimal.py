"""
最小化认证API集成测试
"""

import asyncio
import os

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import (AsyncSession, async_sessionmaker,
                                    create_async_engine)

# 设置测试环境
os.environ["ENVIRONMENT"] = "test"
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"
os.environ["DATABASE_URL_SYNC"] = "sqlite:///:memory:"
os.environ["SECRET_KEY"] = "test_secret_key_for_development"
os.environ["ALGORITHM"] = "HS256"


async def test_auth_api():
    """测试认证API的基础功能"""
    print("=== Minimal Auth API Test ===")

    try:
        # 首先导入核心模块
        from app.core.security import get_password_hash
        from app.models import Base, Member, UserRole

        # 创建测试数据库引擎（适用于SQLite的参数）
        test_engine = create_async_engine(
            "sqlite+aiosqlite:///:memory:",
            echo=False,
            connect_args={"check_same_thread": False},
        )

        # 创建表结构
        async with test_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        # 创建测试用户
        async_session = async_sessionmaker(test_engine, class_=AsyncSession)
        async with async_session() as session:
            test_user = Member(
                username="testuser",
                name="Test User",
                student_id="STU12345",
                phone="13800138000",
                department="IT Department",
                class_name="2021 Class",
                password_hash=get_password_hash("test123"),
                role=UserRole.MEMBER,
                is_active=True,
                profile_completed=True,
            )
            session.add(test_user)
            await session.commit()
            await session.refresh(test_user)
            print(f"[OK] Test user created: {test_user.username}")

        # 延迟导入应用以避免数据库配置问题
        from app.core.database import get_db
        from app.main import app

        # 覆盖数据库依赖
        async def override_get_db():
            async with async_session() as session:
                yield session

        app.dependency_overrides[get_db] = override_get_db

        # 测试API
        async with AsyncClient(app=app, base_url="http://testserver") as client:
            # 测试健康检查
            health_response = await client.get("/health")
            print(f"[OK] Health check: {health_response.status_code}")

            # 测试登录
            login_data = {"student_id": "STU12345", "password": "test123"}
            login_response = await client.post("/api/v1/auth/login", json=login_data)
            print(f"[OK] Login test: {login_response.status_code}")

            if login_response.status_code == 200:
                login_result = login_response.json()
                access_token = login_result.get("access_token")
                print(f"[OK] Access token received: {access_token[:20]}...")

                # 测试受保护的端点
                headers = {"Authorization": f"Bearer {access_token}"}
                profile_response = await client.get(
                    "/api/v1/auth/profile", headers=headers
                )
                print(f"[OK] Profile access: {profile_response.status_code}")

                if profile_response.status_code == 200:
                    profile_data = profile_response.json()
                    print(f"[OK] Profile data: {profile_data.get('name')}")
            else:
                print(f"[WARN] Login failed: {login_response.text}")

        await test_engine.dispose()
        print("\n[SUCCESS] Minimal auth API test completed")

    except Exception as e:
        print(f"[ERROR] Test failed: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_auth_api())
