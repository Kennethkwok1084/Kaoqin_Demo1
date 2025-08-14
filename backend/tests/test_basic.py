"""
基础测试文件，用于验证pytest基本功能
"""

import pytest


class TestBasic:
    """基础测试类"""

    def test_basic_math(self):
        """测试基本数学运算"""
        assert 1 + 1 == 2
        assert 2 * 3 == 6

    def test_string_operations(self):
        """测试字符串操作"""
        text = "hello world"
        assert text.upper() == "HELLO WORLD"
        assert len(text) == 11

    def test_list_operations(self):
        """测试列表操作"""
        data = [1, 2, 3, 4, 5]
        assert len(data) == 5
        assert sum(data) == 15
        assert max(data) == 5


@pytest.mark.asyncio
async def test_basic_async():
    """测试异步函数"""
    import asyncio

    async def async_add(a, b):
        await asyncio.sleep(0.001)  # 微小延迟
        return a + b

    result = await async_add(2, 3)
    assert result == 5


def test_imports():
    """测试关键模块导入"""
    # 测试标准库
    import json

    # 测试第三方库
    # 测试基本功能
    data = {"test": True}
    json_str = json.dumps(data)
    parsed = json.loads(json_str)
    assert parsed["test"] is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
