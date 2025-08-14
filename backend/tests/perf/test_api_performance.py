"""
API endpoint performance tests.
Tests response times for critical API endpoints.
"""

import asyncio

import pytest
import pytest_benchmark
from httpx import AsyncClient
from tests.conftest import AsyncTestClient


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
        response = benchmark(asyncio.run, get_tasks_list())

        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert "success" in data

        # Performance assertions
        benchmark_result = benchmark.stats
        assert (
            benchmark_result["mean"] < 0.5
        ), f"API took {benchmark_result['mean']:.3f}s, should be < 0.5s"

        print(f"\n📊 Tasks List API Performance:")
        print(f"   Mean time: {benchmark_result['mean']*1000:.1f}ms")
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
        response = benchmark(asyncio.run, get_work_time_detail())

        # Performance assertions
        benchmark_result = benchmark.stats
        assert (
            benchmark_result["mean"] < 0.2
        ), f"API took {benchmark_result['mean']:.3f}s, should be < 0.2s"

        print(f"\n📊 Work Time Detail API Performance:")
        print(f"   Mean time: {benchmark_result['mean']*1000:.1f}ms")
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
        response = benchmark(asyncio.run, get_field_mapping())

        # Performance assertions
        benchmark_result = benchmark.stats
        assert (
            benchmark_result["mean"] < 0.1
        ), f"API took {benchmark_result['mean']:.3f}s, should be < 0.1s"

        print(f"\n📊 Field Mapping API Performance:")
        print(f"   Mean time: {benchmark_result['mean']*1000:.1f}ms")
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
        responses = benchmark(asyncio.run, concurrent_requests())

        # Verify all responses
        assert len(responses) == 10
        for response in responses:
            assert response.status_code == 200

        # Performance assertions
        benchmark_result = benchmark.stats
        assert (
            benchmark_result["mean"] < 2.0
        ), f"Concurrent requests took {benchmark_result['mean']:.3f}s, should be < 2s"

        print(f"\n📊 Concurrent API Performance:")
        print(f"   Mean time: {benchmark_result['mean']:.3f}s")
        print(f"   Requests/second: {10 / benchmark_result['mean']:.1f}")


@pytest.fixture
def auth_headers():
    """Mock authentication headers for testing."""
    return {"Authorization": "Bearer test_token", "Content-Type": "application/json"}


@pytest.fixture
def sample_task_id():
    """Sample task ID for testing."""
    return 1
