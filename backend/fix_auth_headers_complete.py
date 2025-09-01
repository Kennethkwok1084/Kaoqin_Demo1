#!/usr/bin/env python3
"""
彻底修复所有测试文件中的auth_headers使用问题
"""

import os
import re
from pathlib import Path


def fix_file_completely(filepath: str):
    """完全修复单个文件"""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            lines = f.readlines()

        # 跳过有自定义auth_headers fixture的文件
        content = "".join(lines)
        if "async def auth_headers(" in content:
            print(f"Skipping {filepath} - has custom auth_headers fixture")
            return

        new_lines = []
        for line in lines:
            # 修复async def行，添加token参数
            if re.match(
                r"    async def test_\w+\(self, async_client: AsyncClient, auth_headers\):",
                line,
            ):
                line = line.replace("auth_headers)", "auth_headers, token):")
            elif re.match(
                r"    async def test_\w+\(self, async_client: AsyncClient, auth_headers, token\):",
                line,
            ):
                pass  # 已经有token了

            # 修复headers = await auth_headers()
            if "headers = await auth_headers()" in line:
                line = line.replace(
                    "headers = await auth_headers()", "headers = auth_headers(token)"
                )
            elif "headers=await auth_headers()" in line:
                line = line.replace(
                    "headers=await auth_headers()", "headers=auth_headers(token)"
                )

            new_lines.append(line)

        with open(filepath, "w", encoding="utf-8") as f:
            f.writelines(new_lines)

        print(f"Fixed: {filepath}")

    except Exception as e:
        print(f"Error fixing {filepath}: {e}")


def main():
    """修复所有comprehensive测试文件"""
    test_dir = Path("tests/comprehensive")

    if not test_dir.exists():
        print(f"Directory {test_dir} not found")
        return

    for test_file in test_dir.glob("*.py"):
        if test_file.name.startswith("test_"):
            print(f"Processing: {test_file}")
            fix_file_completely(str(test_file))

    print("Complete auth headers fix done!")


if __name__ == "__main__":
    main()
