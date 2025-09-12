#!/bin/bash

# PostgreSQL安装和配置脚本 - Ubuntu 22.04
# 创建数据库: attendance_dev
# 创建用户: kwok, 密码: Onjuju1084

set -e  # 遇到错误时停止执行

echo "开始安装和配置PostgreSQL..."

# 更新系统包
echo "更新系统包..."
sudo apt update

# 安装PostgreSQL和相关工具
echo "安装PostgreSQL..."
sudo apt install -y postgresql postgresql-contrib

# 启动PostgreSQL服务
echo "启动PostgreSQL服务..."
sudo systemctl start postgresql
sudo systemctl enable postgresql

# 检查PostgreSQL服务状态
echo "检查PostgreSQL服务状态..."
sudo systemctl status postgresql --no-pager

# 等待PostgreSQL完全启动
sleep 5

echo "配置PostgreSQL数据库和用户..."

# 切换到postgres用户并执行数据库操作
sudo -u postgres psql << EOF
-- 创建用户kwok
CREATE USER kwok WITH PASSWORD 'Onjuju1084';

-- 创建数据库attendance_dev
CREATE DATABASE attendance_dev OWNER kwok;

-- 授予用户kwok对数据库的所有权限
GRANT ALL PRIVILEGES ON DATABASE attendance_dev TO kwok;

-- 授予用户kwok创建数据库的权限
ALTER USER kwok CREATEDB;

-- 显示创建的用户和数据库
\du
\l

-- 退出psql
\q
EOF

echo "配置PostgreSQL允许本地连接..."

# 备份原始配置文件
sudo cp /etc/postgresql/14/main/pg_hba.conf /etc/postgresql/14/main/pg_hba.conf.backup

# 修改pg_hba.conf以允许密码验证
sudo sed -i "s/local   all             all                                     peer/local   all             all                                     md5/" /etc/postgresql/14/main/pg_hba.conf

# 重启PostgreSQL服务以应用配置更改
echo "重启PostgreSQL服务..."
sudo systemctl restart postgresql

# 测试连接
echo "测试数据库连接..."
export PGPASSWORD='Onjuju1084'
if psql -h localhost -U kwok -d attendance_dev -c "SELECT version();" > /dev/null 2>&1; then
    echo "✓ 数据库连接测试成功！"
else
    echo "✗ 数据库连接测试失败，请检查配置"
    exit 1
fi

echo "PostgreSQL安装和配置完成！"
echo ""
echo "数据库信息："
echo "  主机: localhost"
echo "  端口: 5432"
echo "  数据库: attendance_dev"
echo "  用户: kwok"
echo "  密码: Onjuju1084"
echo ""
echo "连接命令示例："
echo "  psql -h localhost -U kwok -d attendance_dev"
echo ""
echo "如果您需要从其他主机连接，请编辑以下文件："
echo "  sudo nano /etc/postgresql/14/main/postgresql.conf"
echo "  sudo nano /etc/postgresql/14/main/pg_hba.conf"
