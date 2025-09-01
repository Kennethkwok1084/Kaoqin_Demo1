#!/usr/bin/env python3
"""
修复测试文件中的auth_headers使用问题
"""

import os
import re
from pathlib import Path

def fix_auth_headers_in_file(filepath: str):
    """修复单个文件中的auth_headers使用"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 替换函数参数中的类型注解
        content = re.sub(
            r'auth_headers: Dict\[str, str\]',
            'auth_headers',
            content
        )
        
        # 替换直接使用auth_headers的地方
        content = re.sub(
            r'headers=auth_headers\)',
            'headers=await auth_headers())',
            content
        )
        
        # 处理更复杂的情况
        content = re.sub(
            r'headers=auth_headers,',
            'headers=await auth_headers(),',
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
        if test_file.name.startswith("test_"):
            print(f"Processing: {test_file}")
            fix_auth_headers_in_file(str(test_file))
    
    print("Auth headers fix completed!")

if __name__ == "__main__":
    main()
