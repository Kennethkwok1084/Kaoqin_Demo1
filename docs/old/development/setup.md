# 🚀 项目设置指南

## 📋 环境要求

### 系统要求
- **操作系统**: Linux/macOS/Windows
- **Python**: 3.9+ (推荐 3.11)
- **Node.js**: 16+ (推荐 18)
- **数据库**: PostgreSQL 12+ 或 SQLite 3
- **缓存**: Redis 6+ (可选)

### 开发工具
- **代码编辑器**: VS Code (推荐)
- **包管理器**: uv (Python) / npm/yarn (Node.js)
- **版本控制**: Git
- **API测试**: Postman/Insomnia (可选)

## 🔧 快速开始

### 1. 克隆项目

```bash
git clone https://github.com/KangJianLin/Kaoqin_Demo.git
cd Kaoqin_Demo
```

### 2. 后端设置

```bash
# 进入后端目录
cd backend

# 使用uv管理Python环境 (推荐)
uv venv
source .venv/bin/activate  # Linux/macOS
# 或 .venv\Scripts\activate  # Windows

# 安装依赖
uv pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
# 编辑.env文件配置数据库连接等

# 初始化数据库
alembic upgrade head

# 启动开发服务器
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 3. 前端设置

```bash
# 进入前端目录
cd frontend

# 安装依赖
npm install

# 配置环境变量
cp .env.example .env.local
# 编辑.env.local文件配置API地址等

# 启动开发服务器
npm run dev
```

### 4. 验证安装

```bash
# 检查后端API健康状态
curl http://localhost:8000/health

# 访问API文档
# http://localhost:8000/docs

# 访问前端应用
# http://localhost:3000 (或其他端口)
```

## ⚙️ 详细配置

### 数据库配置

#### PostgreSQL (生产环境推荐)

```bash
# 安装PostgreSQL
sudo apt-get install postgresql postgresql-contrib  # Ubuntu/Debian
brew install postgresql                             # macOS

# 创建数据库
sudo -u postgres createdb attendance_db
sudo -u postgres createuser -s attendance_user

# 配置.env文件
DATABASE_URL=postgresql://attendance_user:password@localhost/attendance_db
```

#### SQLite (开发环境)

```bash
# SQLite无需额外安装，配置.env文件
DATABASE_URL=sqlite:///./attendance.db
```

### Redis配置 (可选)

```bash
# 安装Redis
sudo apt-get install redis-server  # Ubuntu/Debian
brew install redis                  # macOS

# 启动Redis
redis-server

# 配置.env文件
REDIS_URL=redis://localhost:6379/0
```

### 环境变量配置

创建并配置 `backend/.env` 文件：

```bash
# 应用配置
APP_NAME=考勤管理系统
APP_VERSION=1.0.0
DEBUG=true
SECRET_KEY=your-secret-key-here

# 数据库配置
DATABASE_URL=sqlite:///./attendance.db
# 或 PostgreSQL: postgresql://user:pass@localhost/db

# 缓存配置 (可选)
REDIS_URL=redis://localhost:6379/0

# JWT配置
JWT_SECRET_KEY=your-jwt-secret-key
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7

# CORS配置
CORS_ORIGINS=["http://localhost:3000", "http://127.0.0.1:3000"]

# 邮件配置 (可选)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
```

创建并配置 `frontend/.env.local` 文件：

```bash
# API配置
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
NEXT_PUBLIC_APP_NAME=考勤管理系统

# 环境标识
NODE_ENV=development
```

## 📦 依赖管理

### Python依赖 (后端)

使用 `uv` 管理Python环境和依赖：

```bash
# 创建虚拟环境
uv venv

# 激活环境
source .venv/bin/activate

# 安装依赖
uv pip install -r requirements.txt

# 添加新依赖
uv add fastapi sqlalchemy

# 更新requirements.txt
uv pip freeze > requirements.txt
```

### Node.js依赖 (前端)

```bash
# 安装依赖
npm install

# 添加新依赖
npm install axios @types/axios

# 更新依赖
npm update

# 检查安全漏洞
npm audit
```

## 🗄️ 数据库管理

### Alembic迁移

```bash
# 创建新迁移
alembic revision --autogenerate -m "描述变更"

# 执行迁移
alembic upgrade head

# 回滚迁移
alembic downgrade -1

# 查看迁移历史
alembic history

# 查看当前版本
alembic current
```

### 初始数据

```bash
# 创建管理员用户和示例数据
python -c "from app.core.init_db import init_db; init_db()"

# 或运行初始化脚本
python scripts/init_demo_data.py
```

## 🧪 开发和测试

### 后端测试

```bash
# 运行所有测试
pytest

# 运行特定测试
pytest tests/api/test_auth.py

# 生成覆盖率报告
pytest --cov=app --cov-report=html
```

### 前端测试

```bash
# 运行单元测试
npm test

# 运行E2E测试
npm run test:e2e

# 运行Linting
npm run lint

# 类型检查
npm run type-check
```

## 🛠️ 开发工具配置

### VS Code配置

推荐的VS Code扩展：

```json
{
  "recommendations": [
    "ms-python.python",
    "ms-python.flake8", 
    "ms-python.black-formatter",
    "bradlc.vscode-tailwindcss",
    "Vue.volar",
    "ms-vscode.vscode-typescript-next"
  ]
}
```

工作区配置 `.vscode/settings.json`：

```json
{
  "python.defaultInterpreterPath": "./backend/.venv/bin/python",
  "python.linting.enabled": true,
  "python.linting.flake8Enabled": true,
  "python.formatting.provider": "black",
  "editor.formatOnSave": true,
  "editor.codeActionsOnSave": {
    "source.organizeImports": true
  }
}
```

### Git配置

`.gitignore` 已配置忽略：

```
# Python
__pycache__/
*.pyc
.env
.venv/

# Node.js
node_modules/
.env.local
dist/

# Database
*.db
*.sqlite

# IDE
.vscode/
.idea/
```

## 🚨 常见问题

### Q: 启动时出现端口占用错误

```bash
# 查找占用端口的进程
lsof -i :8000  # 后端端口
lsof -i :3000  # 前端端口

# 终止进程
kill -9 <PID>
```

### Q: 数据库连接失败

```bash
# 检查数据库服务状态
sudo systemctl status postgresql  # Linux
brew services list | grep postgres  # macOS

# 检查连接字符串
echo $DATABASE_URL
```

### Q: Python包安装失败

```bash
# 更新pip
uv pip install --upgrade pip

# 清理缓存
uv cache clean

# 重新安装
uv pip install -r requirements.txt --force-reinstall
```

### Q: 前端构建失败

```bash
# 清理node_modules
rm -rf node_modules package-lock.json
npm install

# 更新Node.js
nvm install node  # 如果使用nvm
```

## 🎯 下一步

设置完成后，建议：

1. **阅读架构文档**: [architecture.md](architecture.md)
2. **查看API文档**: [../api/specification.md](../api/specification.md)
3. **配置自动化工具**: [../api/automation-readme.md](../api/automation-readme.md)
4. **了解贡献流程**: [contributing.md](contributing.md)

## 📞 获取帮助

- **技术问题**: 查看 [GitHub Issues](https://github.com/KangJianLin/Kaoqin_Demo/issues)
- **功能建议**: 提交 [GitHub Discussions](https://github.com/KangJianLin/Kaoqin_Demo/discussions)
- **文档问题**: 编辑相应文档并提交PR
