#!/bin/bash
# 测试数据库设置脚本

set -e

echo "🔧 设置测试数据库环境..."

# 等待PostgreSQL启动
until pg_isready -h localhost -p 5432 -U postgres; do
  echo "等待PostgreSQL启动..."
  sleep 2
done

# 创建测试数据库
echo "创建测试数据库..."
psql -h localhost -U postgres -c "DROP DATABASE IF EXISTS attendence_test;"
psql -h localhost -U postgres -c "CREATE DATABASE attendence_test OWNER postgres;"
psql -h localhost -U postgres -c "GRANT ALL PRIVILEGES ON DATABASE attendence_test TO postgres;"

echo "✅ 测试数据库设置完成"
