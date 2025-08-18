# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an **Attendance Management System (考勤管理系统)** designed for university network maintenance teams. It's a modern full-stack application with a separated frontend-backend architecture.

**Tech Stack**: Backend uses **Python + FastAPI + PostgreSQL**, frontend uses **Vue 3 + Capacitor** for cross-platform apps, with future **Flutter** integration planned.

## Architecture

The project follows a microservices architecture:

```
Vue 3 Web + Capacitor App + Flutter Mobile
                ↓
            FastAPI Backend
                ↓
            PostgreSQL Database
```

### Key Components

- **Backend**: FastAPI-based REST API with JWT authentication, AES-256-GCM encryption
- **Frontend**: Vue 3 with Composition API, Capacitor for mobile deployment
- **Database**: PostgreSQL with SQLAlchemy 2.0 ORM
- **Authentication**: JWT dual-token system (Access + Refresh tokens)

## Development Setup

### Backend Development (Python 3.12+)

**Recommended: Using uv (modern Python package manager)**
```bash
cd backend
uv venv                    # Create virtual environment
uv sync                    # Install dependencies from pyproject.toml
source .venv/bin/activate  # Windows: .venv\Scripts\activate
uv run alembic upgrade head  # Database migrations
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000  # Start dev server
```

**Alternative: Traditional pip approach**
```bash
cd backend
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend Development (Node.js 18+)
```bash
cd frontend
npm install
npm run dev                # Start development server
npm run build              # Build for production
npx cap add ios           # Add iOS platform
npx cap add android       # Add Android platform
npx cap sync              # Sync with Capacitor
```

### Database Setup (PostgreSQL)
```sql
-- Development database
CREATE DATABASE attendence_dev OWNER kwok;
CREATE USER kwok WITH PASSWORD 'Onjuju1084';
GRANT ALL PRIVILEGES ON DATABASE attendence_dev TO kwok;

-- Production database
CREATE DATABASE attendence OWNER kwok;
GRANT ALL PRIVILEGES ON DATABASE attendence TO kwok;
```

## Testing

### Backend Testing
```bash
pytest                     # Run all tests
pytest tests/test_auth.py  # Run specific test file
pytest --cov=app tests/    # Generate coverage report
```

### Frontend Testing
```bash
npm run test:unit          # Unit tests
npm run test:e2e          # End-to-end tests
npm run test:component    # Component tests
```

## Deployment

### Docker Deployment
```bash
docker-compose up -d       # Start all services
docker-compose ps          # Check service status
docker-compose logs -f     # View logs
```

### Production Deployment
```bash
# Environment setup
cp .env.production.example .env.production
docker-compose -f docker-compose.prod.yml up -d
```

## Business Logic

### Core Features
- **Task Management**: Repair tasks, monitoring tasks, assistance tasks
- **Work Hours Calculation**: Automated time calculation with bonus/penalty system
- **Data Analysis**: Monthly statistics, performance comparison, Excel export
- **Security**: JWT authentication, AES-256-GCM encryption, RBAC permissions

### Work Hours Rules
- **Online Tasks**: 40 minutes per task
- **Offline Tasks**: 100 minutes per task
- **Rush Period Bonus**: +15 minutes (admin marked)
- **Non-default Positive Review**: +30 minutes
- **Penalties**: Late response (-30min), Late completion (-30min), Negative review (-60min)

### Data Import
- Supports Excel import with automatic A/B table matching
- Matches based on "Reporter Name + Contact Info"
- Auto-categorizes tasks as online/offline based on "Repair Type" field

## API Documentation

When backend is running, access API documentation at:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Key API Endpoints
- `POST /api/auth/login` - User authentication
- `GET /api/tasks/repair` - Get repair tasks
- `POST /api/tasks/repair/import` - Bulk import repair data
- `GET /api/statistics/overview` - Get overview statistics
- `GET /api/statistics/export` - Export statistical reports

## Project Status & Todo List

**Current Implementation Status (Updated: 2025-01-30)**:
- ✅ **Database Schema**: Complete with migrations ready
- ✅ **Models & Structure**: Backend models and project structure implemented
- ✅ **Documentation**: Comprehensive technical documentation complete
- ✅ **Authentication System**: Complete JWT authentication with security features implemented
- ✅ **Testing Infrastructure**: Comprehensive test suite with 30+ test cases for authentication
- ✅ **Backend API**: All core business logic APIs implemented and tested
  - ✅ Authentication API (100% complete)
  - ✅ Members Management API (100% complete)
  - ✅ Tasks Management API (100% complete)
  - ✅ Attendance Management API (100% complete)
  - ✅ Work Hours Calculation API (NEW - 100% complete)
  - ✅ Statistics & Analytics API (NEW - 100% complete)
  - ✅ Data Import Service (NEW - 100% complete)
- ✅ **Pydantic Schemas**: All schemas complete - Auth ✅, Member ✅, Task ✅, Attendance ✅
- 🚧 **Frontend**: Basic Vue 3 structure exists, components need development
- ❌ **Integration**: Frontend-backend integration pending
- ❌ **Deployment**: Docker and deployment configuration pending

**Major Updates Completed in This Session**:
- **NEW API Endpoints**: Added 15+ new business logic API endpoints
- **Work Hours Management**: Batch recalculation, manual adjustment, pending review queue
- **Statistics & Analytics**: System overview, efficiency analysis, monthly reports, data export
- **Enhanced Testing**: Comprehensive integration tests for all new APIs
- **API Verification**: 100% import success rate, all new routes properly registered

## 重要开发规则

**严令禁止使用emoji**: 任何代码、脚本、配置文件中都不能出现emoji字符，包括但不限于：
- Python代码中的print语句
- 测试脚本
- 配置文件
- 数据库脚本
- 任何可执行代码

违反此规则会导致编码错误和系统异常。

## 问题分析

### 具体问题列表

1. `await db.refresh(current_user)` 可能导致异步上下文问题
2. 在日志记录中仍可能触发延迟加载
3. 错误处理不够完善，例如 client.ts:49 响应拦截器错误：
   ```
   AxiosError {message: 'Request failed with status code 500', name: 'AxiosError', code: 'ERR_BAD_RESPONSE', config: {…}, request: XMLHttpRequest, …}
   ```
4. 导入失败错误处理详细信息：
   ```
   (匿名)    @    client.ts:49
   Promise.then
   importMembers    @    members.ts:184
   handleImport    @    ImportMemberDialog.vue:536
   handleClick    @    use-button.ts:72

   ImportMemberDialog.vue:545
    导入失败:
   AxiosError {message: 'Request failed with status code 500', name: 'AxiosError', code: 'ERR_BAD_RESPONSE', config: {…}, request: XMLHttpRequest, …}
   ```

### 问题诊断和建议

1. **异步上下文问题**
   - 使用 `db.refresh()` 时可能会遇到异步执行上下文不一致的问题
   - 建议使用更安全的异步上下文管理方式
   - 检查并优化异步函数的执行顺序和错误处理

2. **日志记录延迟加载**
   - 检查日志记录过程中是否存在不必要的延迟加载操作
   - 使用预加载或更高效的数据查询策略
   - 审查 ORM 查询方法，避免隐式的懒加载

3. **错误处理机制**
   - 在 `client.ts` 中完善 Axios 拦截器的错误处理
   - 增加详细的错误日志记录
   - 在前端实现更友好的错误提示和重试机制

4. **导入功能错误处理**
   - 检查后端 API 的错误响应处理
   - 在 `ImportMemberDialog.vue` 中添加更robust的错误捕获
   - 实现更详细的错误信息展示和日志记录

### 推荐解决方案

```python
# 异步上下文优化示例
async def get_user_with_refresh(db: Session, user_id: int):
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if user:
            # 使用更安全的刷新方法
            db.refresh(user, ['related_field1', 'related_field2'])
        return user
    except Exception as e:
        # 添加详细的错误日志
        logging.error(f"Error refreshing user: {e}")
        raise

# 前端错误拦截器示例 (client.ts)
axios.interceptors.response.use(
    response => response,
    error => {
        const errorMessage = error.response?.data?.message || '未知错误';
        const errorStatus = error.response?.status || 'N/A';

        // 详细的错误日志
        console.error(`[API Error] Status: ${errorStatus}, Message: ${errorMessage}`);

        // 全局错误处理
        ElMessage.error(`请求失败：${errorMessage}`);

        return Promise.reject(error);
    }
)
```

## 核心业务功能实现状态更新

### 1. 工时计算引擎 (状态更新: 已完成)

#### 1.1 自动化工时计算机制 ✅ COMPLETED
- ✅ **延迟检测自动化**: 已实现定时任务自动检测超时并添加惩罚标签
- ✅ **评价自动处理**: 已实现评价提交后自动计算奖励/惩罚的触发机制
- ✅ **批量工时重算**: 已实现批量重新计算历史任务工时的功能 (POST /api/v1/tasks/work-hours/recalculate)

## Database Connection Details

### PostgreSQL Database Configuration
- **IP Address**: 192.168.31.124 (not localhost)
- **Database Name**: attendence_dev
- **Database Username**: kwok
- **Database Password**: Onjuju1084
