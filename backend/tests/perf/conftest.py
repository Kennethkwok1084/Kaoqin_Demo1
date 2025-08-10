"""
Performance test configuration and fixtures.
"""

import pytest
import pytest_asyncio
from httpx import AsyncClient

from app.main import app


@pytest_asyncio.fixture
async def async_client():
    """Create an async HTTP client for testing."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client


@pytest.fixture(scope="function")
def benchmark_config():
    """Configuration for performance benchmarks."""
    return {
        "max_time": 0.1,  # 100ms max for single operations
        "min_rounds": 5,
        "warmup": True,
        "warmup_iterations": 2
    }