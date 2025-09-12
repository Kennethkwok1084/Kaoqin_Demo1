#!/usr/bin/env python3
"""
生成管理员密码哈希的简单脚本。
"""
from passlib.context import CryptContext

# 使用与应用相同的加密配置
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password: str) -> str:
    """生成密码哈希值"""
    return pwd_context.hash(password)

def main():
    """主函数"""
    password = "Admin@123456"
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

if __name__ == "__main__":
    main()
