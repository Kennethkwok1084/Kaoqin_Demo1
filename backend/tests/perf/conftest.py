"""
Performance test configuration and fixtures.
OPTIMIZED VERSION FOR CI/CD PERFORMANCE
"""

import asyncio
import os
import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.main import app
from app.core.database_compatibility import get_test_database_url, should_use_postgresql_tests


def _is_ci_environment() -> bool:
    """Check if running in CI/CD environment."""
    return os.getenv("CI") == "true" or os.getenv("GITHUB_ACTIONS") == "true"


def _get_optimized_engine_config():
    """Get optimized engine configuration for performance tests."""
    if _is_ci_environment():
        return {
            "pool_size": 1,  # Minimal pool for CI
            "max_overflow": 2,
            "pool_recycle": 300,  # 5 minutes
            "pool_timeout": 5,  # Fast timeout
            "pool_pre_ping": True,
            "connect_args": {
                "command_timeout": 30,  # 30 seconds for CI
                "connect_timeout": 10,
                "server_settings": {
                    "application_name": "perf_test_ci",
                },
            }
        }
    else:
        return {
            "pool_size": 2,
            "max_overflow": 3,
            "pool_recycle": 600,  # 10 minutes
            "pool_timeout": 10,
            "pool_pre_ping": True,
            "connect_args": {
                "command_timeout": 60,  # 1 minute for local tests
                "connect_timeout": 5,
                "server_settings": {
                    "application_name": "perf_test_local",
                },
            }
        }


@pytest_asyncio.fixture(scope="session")
async def async_client() -> AsyncClient:
    """Create an async HTTP client for testing with proper lifecycle management."""
    from httpx import ASGITransport

    transport = ASGITransport(app=app)
    client = AsyncClient(transport=transport, base_url="http://testserver")
    
    try:
        yield client
    finally:
        await client.aclose()


@pytest_asyncio.fixture(scope="session")
async def test_engine():
    """Create optimized test database engine for performance testing."""
    # Use unified test database configuration
    db_url = get_test_database_url()
    
    if should_use_postgresql_tests():
        engine_config = _get_optimized_engine_config()
        # Create engine with optimized settings for PostgreSQL
        engine = create_async_engine(
            db_url,
            echo=False,  # Always disable echo in performance tests
            future=True,
            **engine_config
        )
    else:
        # SQLite configuration for performance tests
        engine = create_async_engine(
            db_url,
            echo=False,
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
            future=True,
        )
    
    try:
        yield engine
    finally:
        await engine.dispose()


@pytest_asyncio.fixture
async def db_session(test_engine):
    """Create optimized database session for performance testing."""
    async_session_maker = async_sessionmaker(
        bind=test_engine, 
        class_=AsyncSession, 
        expire_on_commit=False
    )

    async with async_session_maker() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


@pytest.fixture(scope="function")
def benchmark_config():
    """Configuration for performance benchmarks optimized by environment."""
    if _is_ci_environment():
        return {
            "max_time": 0.2,  # 200ms max for CI (more lenient)
            "min_rounds": 3,  # Fewer rounds in CI
            "warmup": False,  # Skip warmup in CI
            "warmup_iterations": 0,
            "timeout": 30,  # 30 second timeout for CI
        }
    else:
        return {
            "max_time": 0.1,  # 100ms max for local development
            "min_rounds": 5,
            "warmup": True,
            "warmup_iterations": 2,
            "timeout": 60,  # 60 second timeout for local
        }


@pytest_asyncio.fixture(autouse=True)
async def setup_performance_test():
    """Setup and teardown for each performance test."""
    # Setup
    original_event_loop = None
    try:
        original_event_loop = asyncio.get_running_loop()
    except RuntimeError:
        pass
    
    yield
    
    # Teardown - ensure event loop is properly managed
    try:
        if original_event_loop and not original_event_loop.is_closed():
            # Wait for any pending tasks
            pending = asyncio.all_tasks(original_event_loop)
            if pending:
                await asyncio.gather(*pending, return_exceptions=True)
    except Exception as e:
        # Log but don't fail the test due to cleanup issues
        print(f"Performance test cleanup warning: {e}")


# Performance monitoring utilities
class PerformanceMonitor:
    """Monitor performance metrics during tests."""
    
    def __init__(self):
        self.metrics = {}
    
    def record_metric(self, name: str, value: float, unit: str = "seconds"):
        """Record a performance metric."""
        if name not in self.metrics:
            self.metrics[name] = []
        self.metrics[name].append({"value": value, "unit": unit})
    
    def get_summary(self) -> dict:
        """Get performance summary."""
        summary = {}
        for name, values in self.metrics.items():
            numeric_values = [v["value"] for v in values]
            if numeric_values:
                summary[name] = {
                    "count": len(numeric_values),
                    "mean": sum(numeric_values) / len(numeric_values),
                    "min": min(numeric_values),
                    "max": max(numeric_values),
                    "unit": values[0]["unit"] if values else "unknown"
                }
        return summary


@pytest.fixture
def performance_monitor():
    """Provide a performance monitor for tests."""
    return PerformanceMonitor()


# Timeout decorator for performance tests
def timeout_test(seconds: int = 30):
    """Decorator to add timeout to performance tests."""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            try:
                return await asyncio.wait_for(func(*args, **kwargs), timeout=seconds)
            except asyncio.TimeoutError:
                pytest.fail(f"Performance test timed out after {seconds} seconds")
        return wrapper
    return decorator


# CI-specific test markers
ci_skip_slow = pytest.mark.skipif(
    _is_ci_environment(), 
    reason="Slow test skipped in CI environment"
)

ci_only = pytest.mark.skipif(
    not _is_ci_environment(), 
    reason="CI-specific test"
)

local_only = pytest.mark.skipif(
    _is_ci_environment(), 
    reason="Local development test only"
)
