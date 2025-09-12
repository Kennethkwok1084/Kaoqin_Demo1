#!/usr/bin/env python
"""
生成管理员密码的哈希值，可用于数据库插入
"""
import sys
import os
from pathlib import Path

# 添加当前目录到系统路径
current_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(current_dir))

try:
    from app.core.security import get_password_hash

    def generate_password_hash(password: str) -> str:
        """生成密码哈希"""
        return get_password_hash(password)

    if __name__ == "__main__":
        # 如果提供了命令行参数，使用它作为密码
        if len(sys.argv) > 1:
            password = sys.argv[1]
        else:
            # 默认密码是 'admin123'
            password = "admin123"
        
        # 打印哈希值
        hash_value = generate_password_hash(password)
        print(f"\n密码 '{password}' 的哈希值是:\n\n{hash_value}\n")
        print("你可以将此哈希值用于数据库中的管理员密码。")
except ImportError as e:
    print(f"导入错误: {e}")
    print("确保你在backend目录下运行这个脚本，并且已激活虚拟环境。")
    sys.exit(1)
