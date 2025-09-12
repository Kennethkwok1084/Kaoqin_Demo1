#!/usr/bin/env python3
"""
生成管理员账户密码哈希

此脚本只生成密码哈希值，不直接操作数据库
您可以使用生成的SQL语句在PostgreSQL中手动创建管理员账户
"""
import sys
from pathlib import Path

# 添加项目根目录到Python路径
current_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(current_dir))

# 导入加密函数
try:
    from app.core.security import get_password_hash
except ImportError:
    print("[错误] 无法导入安全模块，请确保你在正确的目录中运行此脚本")
    sys.exit(1)


def generate_admin_password_hash(password: str = "Admin@123456"):
    """生成管理员密码哈希值"""
    try:
        # 生成密码哈希
        password_hash = get_password_hash(password)
        
        print("="*50)
        print(f"密码 '{password}' 的哈希值已生成!")
        print("="*50)
        print(f"\n哈希值: {password_hash}\n")
        
        # 生成SQL插入语句
        print("您可以使用以下SQL语句在PostgreSQL数据库中创建管理员账户:")
        print("\nINSERT INTO members (")
        print("    username, name, student_id, email, department, class_name,")
        print("    password_hash, role, is_active, profile_completed, is_verified,")
        print("    join_date, login_count)")
        print("VALUES (")
        print("    'admin', '系统管理员', 'admin001', 'admin@example.com',")
        print("    '系统管理部门', '管理员',")
        print(f"    '{password_hash}', 'ADMIN', true, true, true,")
        print("    CURRENT_DATE, 0);\n")
        
        return password_hash
    
    except Exception as e:
        print(f"[错误] 生成密码哈希失败: {e}")
        return None


def main():
    """主函数"""
    print("="*50)
    print("考勤系统 - 生成管理员密码哈希")
    print("="*50)
    
    # 生成默认密码的哈希值
    password = "Admin@123456"
    generate_admin_password_hash(password)
    
    print("\n提示: 执行上述SQL语句后，您可以使用以下凭据登录:")
    print(f"  用户名: admin")
    print(f"  密码: {password}")
    print("="*50)


if __name__ == "__main__":
    main()
