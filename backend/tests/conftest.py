"""
Pytest configuration and fixtures for testing.
Provides database setup, test client, and common fixtures.
"""

import asyncio
import os
from typing import AsyncGenerator, Generator

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.database import Base, get_async_session
from app.core.security import get_password_hash
from app.main import app
from app.models.member import Member, UserRole


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

# Test database URL - use PostgreSQL for testing

TEST_DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://kwok:Onjuju1084@8.138.233.54:5432/attendence_dev",
)

# Create test async engine
test_async_engine = create_async_engine(
    TEST_DATABASE_URL,
    echo=False,
    pool_size=1,  # Single connection for remote database
    max_overflow=0,
    pool_pre_ping=True,
    connect_args={
        "statement_cache_size": 0,  # Disable prepared statements
        "prepared_statement_cache_size": 0,  # Additional safeguard
        "server_settings": {"application_name": "kaoqin_pytest"},
    },
)

# Test session factory
TestAsyncSessionLocal = async_sessionmaker(
    test_async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


@pytest_asyncio.fixture
async def async_session() -> AsyncGenerator[AsyncSession, None]:
    """Create async database session for testing."""
    # Create tables
    async with test_async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Create session
    async with TestAsyncSessionLocal() as session:
        yield session

    # Drop tables after test
    async with test_async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


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
    import os

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
