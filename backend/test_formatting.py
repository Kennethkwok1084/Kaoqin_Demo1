# 这是一个测试文件，用于验证 pre-commit hooks
import os
import sys
from typing import Dict, List


def test_function(param1: str, param2: int) -> Dict[str, int]:
    """测试函数，故意使用不规范的格式"""
    result = {"key1": param2, "key2": len(param1)}
    return result


class TestClass:
    def __init__(self, name: str):
        self.name = name

    def get_info(self) -> str:
        return f"Name: {self.name}"


if __name__ == "__main__":
    test_obj = TestClass("test")
    print(test_obj.get_info())
