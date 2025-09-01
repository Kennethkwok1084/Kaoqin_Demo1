#!/usr/bin/env python3
"""
修复测试文件中的auth_headers使用问题 - 使用token模式
"""

import os
import re
from pathlib import Path

def fix_auth_headers_in_file(filepath: str):
    """修复单个文件中的auth_headers使用"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 替换直接调用为使用token
        # 首先查找是否有自定义的auth_headers fixture
        if 'async def auth_headers(' in content:
            print(f"Skipping {filepath} - has custom auth_headers fixture")
            return
            
        # 添加token fixture并修复auth_headers使用
        content = re.sub(
            r'headers=await auth_headers\(\)',
            'headers=auth_headers(token)',
            content
        )
        
        # 添加token参数到测试方法
        content = re.sub(
            r'async def (test_\w+)\(self, async_client: AsyncClient, auth_headers\):',
            r'async def \1(self, async_client: AsyncClient, auth_headers, token):',
            content
        )
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        
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
        if test_file.name.startswith("test_") and test_file.name != "test_complete_api_coverage.py":
            print(f"Processing: {test_file}")
            fix_auth_headers_in_file(str(test_file))
    
    print("Auth headers token fix completed!")

if __name__ == "__main__":
    main()
