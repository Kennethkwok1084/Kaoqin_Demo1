"""
Performance test configuration and fixtures.
"""

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.main import app


@pytest_asyncio.fixture
async def async_client():
    """Create an async HTTP client for testing."""
    from httpx import ASGITransport

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


@pytest_asyncio.fixture
async def db_session():
    """Create a database session for performance testing."""
    # Use the same database URL as tests
    engine = create_async_engine(
        "postgresql+asyncpg://kwok:Onjuju1084@192.168.31.124:5432/attendence_dev",
        echo=False,
        future=True,
    )

    async_session_maker = async_sessionmaker(
        bind=engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session_maker() as session:
        yield session

    await engine.dispose()


@pytest.fixture(scope="function")
def benchmark_config():
    """Configuration for performance benchmarks."""
    return {
        "max_time": 0.1,  # 100ms max for single operations
        "min_rounds": 5,
        "warmup": True,
        "warmup_iterations": 2,
    }
