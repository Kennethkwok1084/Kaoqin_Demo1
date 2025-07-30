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

**Current Implementation Status**: 
- ✅ **Database Schema**: Complete with migrations ready
- ✅ **Models & Structure**: Backend models and project structure implemented  
- ✅ **Documentation**: Comprehensive technical documentation complete
- ✅ **Authentication System**: Complete JWT authentication with security features implemented
- ✅ **Testing Infrastructure**: Comprehensive test suite with 30+ test cases for authentication
- 🚧 **Backend API**: Authentication API complete, member/task APIs in progress
- ✅ **Pydantic Schemas**: All schemas complete - Auth ✅, Member ✅, Task ✅, Attendance ✅
- 🚧 **Frontend**: Basic Vue 3 structure exists, components need development
- ❌ **Integration**: Frontend-backend integration pending
- ❌ **Deployment**: Docker and deployment configuration pending

## 🚨 未完善的核心业务功能分析

### 1. 工时计算引擎的具体缺失

#### 1.1 自动化工时计算机制缺失 🔥
- **延迟检测自动化**: 缺乏定时任务自动检测超时并添加惩罚标签
- **评价自动处理**: 缺乏评价提交后自动计算奖励/惩罚的触发机制  
- **批量工时重算**: 当规则变更时，缺乏批量重新计算历史任务工时的功能

#### 1.2 复杂工时规则引擎缺失 📋
- **规则配置管理**: 无法动态配置工时计算规则
- **条件组合逻辑**: 缺乏复杂条件判断（特定时间段、特定类型任务的不同计算方式）
- **工时审核机制**: 缺乏管理员手动调整和审核工时的功能

### 2. 数据导入功能的具体问题

#### 2.1 Excel数据导入服务完全缺失 🔥
- **文件处理服务**: 完全没有实现Excel文件读取和解析
- **A/B表匹配算法**: 基于"报告人姓名+联系方式"的自动匹配逻辑缺失
- **数据验证清洗**: 缺乏导入数据的格式验证和清洗机制

#### 2.2 批量数据处理缺失 📋  
- **模糊匹配算法**: 处理姓名和联系方式的细微差异
- **重复数据检测**: 避免重复导入相同任务
- **匹配结果预览**: 在正式导入前展示匹配结果供确认

### 3. 统计分析服务的缺失

#### 3.1 高级统计算法缺失 📋
- **效率趋势分析**: 缺乏个人和团队效率变化趋势计算
- **工作量分布分析**: 缺乏按时间、地点、类型的工作量分布统计
- **完成模式分析**: 缺乏任务完成时间模式和预测算法

#### 3.2 实时统计数据缓存缺失 🔥
- **Redis缓存层**: 每次查询都实时计算，性能较差
- **增量更新机制**: 任务状态变更时缺乏增量更新统计
- **定时刷新**: 缺乏定期刷新统计缓存的机制

### 4. 考勤相关API的缺失

#### 4.1 考勤记录管理API完全缺失 🔥
- **签到签退接口**: `/api/v1/attendance/checkin`, `/checkout` 等完全缺失
- **考勤记录查询**: 缺乏个人和管理员查询考勤记录的接口
- **考勤异常处理**: 缺乏请假、迟到、早退的申请和审批接口

#### 4.2 考勤报表API缺失 📋
- **月度报表生成**: 缺乏个人和团队月度考勤报表接口
- **异常统计分析**: 缺乏各类考勤异常的统计接口
- **出勤率计算**: 缺乏出勤率和工时达成率的计算接口

### 5. 业务流程自动化的缺失

#### 5.1 任务生命周期自动化缺失 📋
- **智能任务分配**: 缺乏基于工作量和能力的自动分配算法
- **超时提醒机制**: 缺乏任务临近截止时间的自动提醒
- **紧急任务升级**: 缺乏紧急任务的自动升级和通知机制

#### 5.2 通知系统完全缺失 🔥  
- **任务分配通知**: 新任务分配时缺乏通知执行者的机制
- **状态变更通知**: 任务状态变更时缺乏通知相关人员
- **异常报警系统**: 系统异常和数据异常缺乏报警机制

### 🎯 优先级实现建议

#### 🔥 高优先级 (立即实现 - 2周内)
1. **数据导入服务实现**
   - 实现Excel文件处理和A/B表匹配
   - 技术栈：Pandas + openpyxl
   
2. **考勤记录API实现**  
   - 实现基础的签到签退和记录管理接口
   - 文件：`app/api/v1/attendance.py` (需创建)

3. **工时计算自动化机制**
   - 实现基于Celery的定时任务进行延迟检测和自动计算
   - 技术栈：Celery + Redis

#### 📋 中优先级 (1个月内)
4. **通知系统实现**
   - WebSocket实时通知 + 邮件通知
   - 技术栈：FastAPI WebSocket + 邮件服务

5. **统计分析增强**
   - Redis缓存 + 高级统计算法
   - 实现实时统计数据缓存和增量更新

6. **异常处理流程**
   - 考勤异常申请审批流程
   - 任务异常处理标准化流程

#### ⚡ 低优先级 (后期优化)
7. **工作流引擎**
8. **高级分析算法**  
9. **数据归档机制**

### 🔧 推荐技术实现方案

```python
# 需要新增的技术栈
dependencies = [
    "celery>=5.3.0",           # 异步任务和定时任务
    "redis>=5.0.0",            # 缓存和消息队列
    "pandas>=2.1.0",           # Excel数据处理
    "openpyxl>=3.1.0",         # Excel文件读写
    "websockets>=12.0",        # 实时通知
    "APScheduler>=3.10.0",     # 定时任务调度
]
```

### 🔥 High Priority Tasks (Phase 1)

#### Backend Core Implementation  
- ✅ **API Routes & Endpoints** - Auth ✅, Members ✅, Tasks ✅
- ✅ **Pydantic Schemas** - All complete: Auth ✅, Member ✅, Task ✅, Attendance ✅
- ✅ **Members Management API** - CRUD operations, role management (`/api/v1/members`)
- ✅ **Tasks Management API** - Repair/monitoring tasks API (`/api/v1/tasks`)
- ✅ **Business Logic Services** - Implemented `task_service`, `stats_service`
- ✅ **Authentication System** - Complete JWT token generation/validation, password hashing, permissions
- 🔥 **Work Hours Engine** - 需要实现自动化计算引擎和规则配置系统
- 🔥 **Data Import Service** - 需要实现Excel导入和A/B表匹配服务
- 🔥 **Attendance API** - 需要创建考勤记录管理接口

#### Frontend Core Implementation  
- [ ] **Package Setup** - Configure package.json with Vue 3, Capacitor, Element Plus dependencies
- [ ] **Authentication UI** - Login/logout forms, token management, route guards
- [ ] **State Management** - Create Pinia stores for auth, tasks, members, attendance
- [ ] **API Client** - Build Axios client for backend communication and error handling
- [ ] **Router Setup** - Configure Vue Router with authentication guards

### 📋 Medium Priority Tasks (Phase 2)

#### Backend Features
- [ ] **Excel Data Import** - Build A/B table processing and matching service
- [ ] **AES Encryption** - Implement encryption utilities for sensitive data  
- [ ] **Dependencies** - Create dependency injection for database sessions
- [ ] **Environment Config** - Create .env.example and configuration files
- [ ] **Test Suite** - Write unit, integration, and API tests

#### Frontend Components
- [ ] **Task Management** - TaskList, TaskDetail, TaskForm, TaskImport components
- [ ] **Member Management** - MemberList, MemberDetail, MemberForm components  
- [ ] **Dashboard** - Statistics overview with ECharts data visualization
- [ ] **Attendance Views** - Statistics views with export functionality
- [ ] **Common Components** - Reusable UI components (BaseButton, BaseCard, BaseTable)
- [ ] **TypeScript Types** - Define types for API models and component props

#### Infrastructure
- [ ] **Database Seeds** - Create sample data for development and testing
- [ ] **Database Testing** - Test migrations and schema functionality
- [ ] **Docker Config** - Create development and production containerization
- [ ] **Security Implementation** - CORS, CSP, rate limiting, input validation

### 🔧 Low Priority Tasks (Phase 3)

- [ ] **Mobile Deployment** - Configure Capacitor for iOS/Android testing
- [ ] **Development Scripts** - Create setup automation tools
- [ ] **CI/CD Pipeline** - GitHub Actions for automated testing and deployment
- [ ] **Code Quality** - ESLint, Prettier, Black, mypy configuration
- [ ] **API Documentation** - Enhanced documentation with examples

## Progress Tracking

### Daily Progress Log
**Last Updated**: 2025-07-28

#### 2025-01-29 (最新进程)
- ✅ 完成认证系统API实现 (`app/api/v1/auth.py`)
- ✅ 完成成员管理API完整实现 (`app/api/v1/members.py` - 34.8KB)
- ✅ 完成任务管理API完整实现 (`app/api/v1/tasks.py` - 42.1KB)  
- ✅ 完成业务逻辑服务层 (`app/services/task_service.py`, `app/services/stats_service.py`)
- ✅ 完成SQLAlchemy 2.0兼容性修复 (Mapped类型注解)
- ✅ 完成主路由配置更新 (`app/main.py`)
- ✅ 完成核心功能验证测试 (75%测试通过率)
- ✅ **已完成**: 后端核心架构和API层实现完毕
- 📋 **当前状态**: 项目75%完成，后端就绪，前端缺失

#### 2025-01-27
- ✅ Project structure analysis completed
- ✅ Comprehensive todo list created with 30 actionable items
- ✅ Progress tracking system established

### Development Milestones

#### Milestone 1: Backend Foundation (Target: Week 1)
- Complete API routes implementation
- Implement authentication system
- Set up business logic services
- Deploy basic API with Swagger documentation

#### Milestone 2: Frontend Foundation (Target: Week 2)  
- Complete frontend package setup
- Implement authentication UI
- Create core components and routing
- Establish API integration

#### Milestone 3: Core Features (Target: Week 3-4)
- Work hours calculation engine
- Task and member management
- Data import functionality
- Basic testing coverage

#### Milestone 4: Polish & Deploy (Target: Week 5-6)
- Comprehensive testing
- Security implementation
- Docker deployment
- Documentation completion

## Implementation Notes

The project has excellent foundational work:
- **Database schema** is production-ready with proper indexes and constraints
- **Model definitions** follow best practices with proper relationships
- **Configuration system** is well-structured with environment-based settings
- **Project structure** follows FastAPI and Vue 3 conventions

**Key Implementation Focus**:
1. **Authentication First** - Secure the application before building features
2. **API-Driven Development** - Complete backend APIs before frontend integration  
3. **Test-Driven Approach** - Write tests alongside implementation
4. **Progressive Enhancement** - Start with core features, add complexity gradually
5. **Notice** - Always respose in Chinese/中文 ,Program display language is Chinese/中文.