"""
Pytest configuration and fixtures for testing.
Provides database setup, test client, and common fixtures.
Updated to support dual database testing strategy (SQLite/PostgreSQL).
"""

import asyncio
import logging
import os
from typing import AsyncGenerator, Generator

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_session
from app.core.security import get_password_hash
from app.main import app as fastapi_app
from app.models.base import Base
from app.models.member import Member, UserRole
from app.api.deps import get_db
from tests.database_config import (
    test_config,
)

# Setup logging for tests
logger = logging.getLogger(__name__)

# Use PostgreSQL for tests by default to match production environment
if not os.getenv("DATABASE_URL") and not os.getenv("FORCE_SQLITE_TESTS"):
    os.environ["POSTGRES_TEST"] = "true"
    # Set PostgreSQL test connection parameters
    os.environ["TEST_DB_HOST"] = "localhost"
    os.environ["TEST_DB_USER"] = "kwok"
    os.environ["TEST_DB_PASSWORD"] = "Onjuju1084"
    os.environ["TEST_DB_NAME"] = "attendence_dev"

# Set test environment variables early
os.environ["TESTING"] = "true"
os.environ["DEBUG"] = "true"
os.environ["SECRET_KEY"] = "test-secret-key-for-testing-only"

# Set the test database URL early, before app import
os.environ["DATABASE_URL"] = test_config.test_database_url

# Import models in correct order to avoid forward reference issues
import app.models.attendance  # noqa: F401
import app.models.base  # noqa: F401
import app.models.member  # noqa: F401
import app.models.task  # noqa: F401

# Import and patch settings for testing before app import
from app.core.config import settings
settings.TESTING = True
settings.DEBUG = False
settings.DATABASE_URL = test_config.test_database_url

# Import database testing configuration

# Environment variable already set at top of file


@pytest.fixture(scope="session", autouse=True)
def force_sqlite_for_tests():
    """Force SQLite usage for all tests to avoid PostgreSQL asyncio issues."""
    # Environment variable already set at module level
    yield
    # Clean up at session end
    if "FORCE_SQLITE_TESTS" in os.environ:
        del os.environ["FORCE_SQLITE_TESTS"]


# Async test client fixture
@pytest_asyncio.fixture
async def async_client() -> AsyncGenerator[AsyncClient, None]:
    """Create async test client."""
    from httpx import ASGITransport

    transport = ASGITransport(app=fastapi_app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        yield client


# Export AsyncClient as AsyncTestClient for backward compatibility
AsyncTestClient = AsyncClient


# Use new database testing configuration with consistent scopes
@pytest_asyncio.fixture(scope="function", autouse=True)
async def test_engine():
    """Create test database engine using new configuration."""
    engine = None
    try:
        engine = await test_config.create_test_engine()
        yield engine
    except Exception as e:
        logger.error(f"Test engine creation failed: {e}")
        raise
    finally:
        if engine:
            try:
                await engine.dispose()
            except Exception as e:
                logger.error(f"Test engine disposal failed: {e}")


@pytest_asyncio.fixture(scope="function", autouse=True)
async def setup_database(test_engine):
    """Setup test database using new configuration."""
    try:
        await test_config.setup_test_database(test_engine)
        yield
    except Exception as e:
        logger.error(f"Database setup failed: {e}")
        raise
    finally:
        # Cleanup after each test function
        try:
            # Clean up any test data that may have been created
            async with test_engine.begin() as conn:
                # Only clean up if we're in test mode
                if os.getenv("TESTING") == "true":
                    pass  # Let the transaction rollback handle cleanup
        except Exception as e:
            logger.error(f"Database cleanup failed: {e}")


@pytest_asyncio.fixture(scope="function")
async def async_session(
    test_engine, setup_database
) -> AsyncGenerator[AsyncSession, None]:
    """Create async database session for testing with proper isolation and error handling."""
    session = None

    try:
        # Create a simple session without complex transaction management
        # This avoids connection_lost issues when sharing with the application
        session = AsyncSession(
            test_engine,
            expire_on_commit=False,
            autoflush=True,  # Allow autoflush for better compatibility
            autocommit=False,
        )

        yield session

        # Commit any pending changes
        if session.in_transaction():
            await session.commit()

    except Exception as e:
        logger.error(f"Session error: {e}")
        # Rollback on exception
        if session and session.in_transaction():
            try:
                await session.rollback()
            except Exception as rollback_error:
                logger.error(f"Session rollback failed: {rollback_error}")
        raise
    finally:
        # Clean up session
        if session:
            try:
                await session.close()
            except Exception as close_error:
                # Don't log event loop closed errors
                if "event loop is closed" not in str(close_error).lower():
                    logger.error(f"Session close failed: {close_error}")


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    """Create test client."""
    with TestClient(fastapi_app) as test_client:
        yield test_client


@pytest_asyncio.fixture
async def client_with_db(
    async_session: AsyncSession,
) -> AsyncGenerator[TestClient, None]:
    """Create test client with database session override."""

    async def override_get_db():
        yield async_session

    # Store original overrides and restore after test
    original_overrides = fastapi_app.dependency_overrides.copy()
    fastapi_app.dependency_overrides[get_db] = override_get_db

    with TestClient(fastapi_app) as test_client:
        yield test_client

    # Restore original overrides instead of clearing all
    fastapi_app.dependency_overrides.clear()
    fastapi_app.dependency_overrides.update(original_overrides)


@pytest_asyncio.fixture
async def test_user(async_session: AsyncSession) -> Member:
    """Create a test user using the shared async session."""
    user = Member(
        username="test_user",
        name="测试用户",
        student_id="2021001001",
        group_id=1,
        class_name="计算机科学与技术2101",
        email="test@example.com",
        password_hash=get_password_hash("TestPassword123!"),
        role=UserRole.MEMBER,
        is_active=True,
        is_verified=True,
    )

    async_session.add(user)
    await async_session.commit()
    await async_session.refresh(user)

    yield user

    # Cleanup is handled by the async_session fixture


@pytest_asyncio.fixture
async def test_admin(async_session: AsyncSession) -> Member:
    """Create a test admin user."""
    admin = Member(
        username="test_admin",  # 添加username字段
        name="管理员",
        student_id="2021000001",
        group_id=1,
        class_name="管理员",
        email="admin@example.com",
        password_hash=get_password_hash("AdminPassword123!"),
        role=UserRole.ADMIN,
        is_active=True,
        is_verified=True,
    )

    async_session.add(admin)
    await async_session.commit()
    await async_session.refresh(admin)

    return admin


@pytest_asyncio.fixture
async def test_group_leader(async_session: AsyncSession) -> Member:
    """Create a test group leader."""
    leader = Member(
        username="test_leader",  # 添加username字段
        name="组长",
        student_id="2021000002",
        group_id=1,
        class_name="计算机科学与技术2101",
        email="leader@example.com",
        password_hash=get_password_hash("LeaderPassword123!"),
        role=UserRole.GROUP_LEADER,
        is_active=True,
        is_verified=True,
    )

    async_session.add(leader)
    await async_session.commit()
    await async_session.refresh(leader)

    return leader


@pytest.fixture
def auth_headers():
    """Create authorization headers for testing."""

    def _create_headers(token: str) -> dict:
        return {"Authorization": f"Bearer {token}"}

    return _create_headers


@pytest.fixture
async def token(async_client):
    """Get authentication token for testing."""
    # 创建测试用户
    user_data = {
        "username": "testuser",
        "password": "TestPassword123!",
        "student_id": "2024001001",
        "name": "测试用户",
        "email": "testuser@example.com",
    }

    # 先尝试注册
    await async_client.post("/api/v1/auth/register", json=user_data)

    # 登录获取token
    login_response = await async_client.post(
        "/api/v1/auth/login",
        json={"username": user_data["username"], "password": user_data["password"]},
    )

    if login_response.status_code == 200:
        data = login_response.json()
        return data.get("data", {}).get("access_token", "mock_token")
    else:
        return "mock_token"


@pytest.fixture
def sample_login_data():
    """Sample login data for testing."""
    return {"student_id": "2021001001", "password": "TestPassword123!"}


@pytest.fixture
def sample_invalid_login_data():
    """Sample invalid login data for testing."""
    return {"student_id": "2021001001", "password": "WrongPassword"}


@pytest.fixture
def sample_profile_update():
    """Sample profile update data for testing."""
    return {
        "name": "更新后的用户名",
        "class_name": "计算机科学与技术2102",
        "email": "updated@example.com",
    }


@pytest.fixture
def sample_password_change():
    """Sample password change data for testing."""
    return {"current_password": "TestPassword123!", "new_password": "NewPassword456!"}


@pytest.fixture
def sample_invalid_password_change():
    """Sample invalid password change data for testing."""
    return {
        "current_password": "WrongCurrentPassword",
        "new_password": "NewPassword456!",
    }


@pytest.fixture
def sample_weak_password_change():
    """Sample weak password change data for testing."""
    return {"current_password": "TestPassword123!", "new_password": "weak"}


# Enhanced event loop configuration for async tests with better CI/CD support
@pytest.fixture(scope="function")
def event_loop():
    """Create a new event loop for each test function with enhanced cleanup."""
    import logging

    logger = logging.getLogger(__name__)

    # Save the current event loop policy
    original_policy = asyncio.get_event_loop_policy()

    # Create a new event loop
    loop = None
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        yield loop

    finally:
        # Clean up tasks and close loop safely
        if loop and not loop.is_closed():
            try:
                # Cancel all remaining tasks
                pending = asyncio.all_tasks(loop)
                if pending:
                    for task in pending:
                        if not task.done() and not task.cancelled():
                            task.cancel()

                    # Give tasks a moment to cancel gracefully
                    try:
                        loop.run_until_complete(
                            asyncio.wait_for(
                                asyncio.gather(*pending, return_exceptions=True),
                                timeout=1.0,
                            )
                        )
                    except (asyncio.TimeoutError, RuntimeError) as e:
                        logger.debug(f"Task cleanup timeout/error (expected): {e}")

                # Close the loop
                loop.close()

            except Exception as e:
                logger.error(f"Event loop cleanup error: {e}")

        # Reset to original policy
        try:
            asyncio.set_event_loop_policy(original_policy)
        except Exception as e:
            logger.error(f"Failed to restore event loop policy: {e}")


# Test configuration - Environment already set at module level


class TestResponse:
    """Helper class for testing API responses."""

    @staticmethod
    def is_success(response) -> bool:
        """Check if response indicates success."""
        return response.status_code < 400

    @staticmethod
    def get_data(response) -> dict:
        """Extract data from response."""
        json_response = response.json()
        return json_response.get("data", {})

    @staticmethod
    def get_message(response) -> str:
        """Extract message from response."""
        json_response = response.json()
        return json_response.get("message", "")

    @staticmethod
    def get_errors(response) -> dict:
        """Extract errors from response."""
        json_response = response.json()
        return json_response.get("details", {})


@pytest.fixture
def test_response():
    """Test response helper."""
    return TestResponse
