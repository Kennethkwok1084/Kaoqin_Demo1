"""
API endpoint performance tests.
Tests response times for critical API endpoints.
"""

import asyncio
from typing import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.main import app


class TestAPIPerformance:
    """API performance test suite."""

    @pytest.mark.asyncio
    @pytest.mark.benchmark
    async def test_tasks_list_performance(
        self, benchmark, async_client: AsyncClient, auth_headers
    ):
        """
        Test tasks list API performance.
        Benchmark threshold: should respond within 500ms.
        """

        async def get_tasks_list():
            response = await async_client.get("/api/v1/tasks/", headers=auth_headers)
            return response

        # Run benchmark
        response = await benchmark.pedantic(get_tasks_list, rounds=5)

        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert "success" in data

        # Performance assertions
        benchmark_result = benchmark.stats
        assert (
            benchmark_result["mean"] < 0.5
        ), f"API took {benchmark_result['mean']:.3f}s, should be < 0.5s"

        print("\n📊 Tasks List API Performance:")
        print(f"   Mean time: {benchmark_result['mean'] * 1000:.1f}ms")
        print(f"   Status: {response.status_code}")

    @pytest.mark.asyncio
    @pytest.mark.benchmark
    async def test_work_time_detail_performance(
        self,
        benchmark,
        async_client: AsyncClient,
        auth_headers,
        sample_task_id: int = 1,
    ):
        """
        Test work time detail API performance.
        Benchmark threshold: should respond within 200ms.
        """

        async def get_work_time_detail():
            response = await async_client.get(
                f"/api/v1/tasks/work-time-detail/{sample_task_id}", headers=auth_headers
            )
            return response

        # Run benchmark
        response = await benchmark.pedantic(get_work_time_detail, rounds=5)

        # Performance assertions
        benchmark_result = benchmark.stats
        assert (
            benchmark_result["mean"] < 0.2
        ), f"API took {benchmark_result['mean']:.3f}s, should be < 0.2s"

        print("\n📊 Work Time Detail API Performance:")
        print(f"   Mean time: {benchmark_result['mean'] * 1000:.1f}ms")
        print(f"   Status: {response.status_code}")

    @pytest.mark.asyncio
    @pytest.mark.benchmark
    async def test_field_mapping_performance(
        self, benchmark, async_client: AsyncClient, auth_headers
    ):
        """
        Test field mapping API performance.
        Benchmark threshold: should respond within 100ms.
        """

        async def get_field_mapping():
            response = await async_client.get(
                "/api/v1/import/field-mapping", headers=auth_headers
            )
            return response

        # Run benchmark
        response = await benchmark.pedantic(get_field_mapping, rounds=5)

        # Performance assertions
        benchmark_result = benchmark.stats
        assert (
            benchmark_result["mean"] < 0.1
        ), f"API took {benchmark_result['mean']:.3f}s, should be < 0.1s"

        print("\n📊 Field Mapping API Performance:")
        print(f"   Mean time: {benchmark_result['mean'] * 1000:.1f}ms")
        print(f"   Status: {response.status_code}")

    @pytest.mark.asyncio
    @pytest.mark.benchmark
    async def test_concurrent_api_performance(
        self, benchmark, async_client: AsyncClient, auth_headers
    ):
        """
        Test concurrent API requests performance.
        Benchmark threshold: 10 concurrent requests should complete within 2 seconds.
        """

        async def concurrent_requests():
            tasks = []
            for i in range(10):
                task = async_client.get("/api/v1/tasks/stats", headers=auth_headers)
                tasks.append(task)

            responses = await asyncio.gather(*tasks)
            return responses

        # Run benchmark
        responses = await benchmark.pedantic(concurrent_requests, rounds=3)

        # Verify all responses
        assert len(responses) == 10
        for response in responses:
            assert response.status_code == 200

        # Performance assertions
        benchmark_result = benchmark.stats
        assert (
            benchmark_result["mean"] < 2.0
        ), f"Concurrent requests took {benchmark_result['mean']:.3f}s, should be < 2s"

        print("\n📊 Concurrent API Performance:")
        print(f"   Mean time: {benchmark_result['mean']:.3f}s")
        print(f"   Requests/second: {10 / benchmark_result['mean']:.1f}")


@pytest_asyncio.fixture
async def async_client() -> AsyncGenerator[AsyncClient, None]:
    """Create async test client for performance testing."""
    from httpx import ASGITransport

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        yield client


@pytest.fixture
def auth_headers():
    """Create valid authentication headers for testing."""
    from app.core.security import create_access_token

    # Create a valid JWT token with a test user ID
    access_token = create_access_token(subject=1)
    return {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }


@pytest.fixture
def sample_task_id():
    """Sample task ID for testing."""
    return 1
