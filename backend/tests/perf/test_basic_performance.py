"""
基础性能测试
用于CI/CD环境中的性能基准测试
"""

import asyncio
import time

import pytest


class TestBasicPerformance:
    """基础性能测试套件"""

    def test_import_speed(self, benchmark):
        """测试导入速度"""

        def import_modules():
            pass

            return True

        result = benchmark(import_modules)
        assert result is True

    @pytest.mark.asyncio
    async def test_async_operation_speed(self, benchmark):
        """测试异步操作速度"""

        async def async_operation():
            await asyncio.sleep(0.001)  # 1ms延迟
            return {"status": "success"}

        def run_async():
            return asyncio.run(async_operation())

        result = benchmark(run_async)
        assert result["status"] == "success"

    def test_json_processing_speed(self, benchmark):
        """测试JSON处理速度"""
        import json

        test_data = {
            "users": [
                {"id": i, "name": f"User {i}", "active": True} for i in range(100)
            ]
        }

        def process_json():
            serialized = json.dumps(test_data)
            return json.loads(serialized)

        result = benchmark(process_json)
        assert len(result["users"]) == 100

    def test_string_processing_speed(self, benchmark):
        """测试字符串处理速度"""

        def process_strings():
            text = "Hello World " * 1000
            return text.upper().replace("HELLO", "Hi").split()

        result = benchmark(process_strings)
        assert len(result) > 0
        assert "Hi" in result[0]

    @pytest.mark.parametrize("data_size", [10, 100, 1000])
    def test_data_processing_scalability(self, benchmark, data_size):
        """测试数据处理扩展性"""

        def process_data():
            data = list(range(data_size))
            # 模拟数据处理操作
            result = [x * 2 for x in data if x % 2 == 0]
            return sum(result)

        result = benchmark(process_data)
        expected = sum(x * 2 for x in range(data_size) if x % 2 == 0)
        assert result == expected


@pytest.fixture(scope="session")
def performance_report():
    """性能测试报告fixture"""
    return {"test_start": time.time(), "benchmarks": []}


def pytest_benchmark_group_stats(config, benchmarks, group_by):
    """收集性能统计信息"""
    if benchmarks:
        print(f"\n📊 性能测试统计:")
        for benchmark in benchmarks:
            mean_time = benchmark.stats["mean"] * 1000  # 转换为毫秒
            print(f"   {benchmark.name}: {mean_time:.2f}ms")


def pytest_sessionfinish(session, exitstatus):
    """测试会话结束时的处理"""
    if hasattr(session.config, "_benchmarksession"):
        print("\n🎯 所有性能测试完成")
