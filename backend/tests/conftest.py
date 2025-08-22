"""
Pytest configuration and fixtures for testing.
Provides database setup, test client, and common fixtures.
Updated to support dual database testing strategy (SQLite/PostgreSQL).
"""

# Force SQLite usage for tests to avoid asyncpg event loop issues
# Set BEFORE imports to ensure it's available during database config loading
from tests.database_config import (
    test_config,
)
from app.models.member import Member, UserRole
from app.models.base import Base
from app.main import app
from app.core.security import get_password_hash
from app.core.database import get_async_session
from sqlalchemy.ext.asyncio import AsyncSession
from httpx import AsyncClient
from fastapi.testclient import TestClient
import pytest_asyncio
import pytest
from typing import AsyncGenerator, Generator
import asyncio
import os

os.environ["FORCE_SQLITE_TESTS"] = "true"


import app.models.attendance  # noqa: F401

# Import models in correct order to avoid forward reference issues
import app.models.base  # noqa: F401
import app.models.member  # noqa: F401
import app.models.task  # noqa: F401

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

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        yield client


# Export AsyncClient as AsyncTestClient for backward compatibility
AsyncTestClient = AsyncClient


# Use new database testing configuration
@pytest_asyncio.fixture(scope="session")
async def test_engine():
    """Create test database engine using new configuration."""
    engine = await test_config.create_test_engine()
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture(scope="session")
async def setup_database(test_engine):
    """Setup test database using new configuration."""
    await test_config.setup_test_database(test_engine)
    yield
    # Cleanup after all tests
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def async_session(
    test_engine, setup_database
) -> AsyncGenerator[AsyncSession, None]:
    """Create async database session for testing."""
    async with AsyncSession(test_engine) as session:
        try:
            yield session
        finally:
            await session.rollback()


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    """Create test client."""
    with TestClient(app) as test_client:
        yield test_client


@pytest_asyncio.fixture
async def client_with_db(
    async_session: AsyncSession,
) -> AsyncGenerator[TestClient, None]:
    """Create test client with database session override."""

    async def override_get_async_session():
        yield async_session

    app.dependency_overrides[get_async_session] = override_get_async_session

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def test_user(async_session: AsyncSession) -> Member:
    """Create a test user."""
    user = Member(
        username="test_user",  # 添加username字段
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

    return user


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


# Event loop configuration for async tests
@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# Test configuration
@pytest.fixture(autouse=True)
def setup_test_environment():
    """Setup test environment variables."""
    os.environ["TESTING"] = "true"
    os.environ["DEBUG"] = "true"
    os.environ["SECRET_KEY"] = "test-secret-key-for-testing-only"
    yield
    # Cleanup is automatic when test ends


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
