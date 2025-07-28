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

### 🔥 High Priority Tasks (Phase 1)

#### Backend Core Implementation
- ✅ **API Routes & Endpoints** - Authentication API complete (`/api/v1/auth`)
- ✅ **Pydantic Schemas** - All complete: Auth ✅, Member ✅, Task ✅, Attendance ✅
- [ ] **Members Management API** - CRUD operations, role management (`/api/v1/members`)
- [ ] **Tasks Management API** - Repair/monitoring tasks API (`/api/v1/tasks`)
- [ ] **Business Logic Services** - Implement `task_service`, `stats_service`, `import_service`
- ✅ **Authentication System** - Complete JWT token generation/validation, password hashing, permissions
- [ ] **Work Hours Engine** - Implement calculation engine with tag system and business rules

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

#### 2025-01-28 (当前进程)
- ✅ 完成认证系统API实现 (`app/api/v1/auth.py`)
- ✅ 完成依赖注入系统 (`app/api/deps.py`)
- ✅ 完成JWT安全模块增强 (`app/core/security.py`)
- ✅ 完成认证相关Pydantic schemas (`app/schemas/auth.py`)
- ✅ 完成成员管理Pydantic schemas (`app/schemas/member.py`)
- ✅ 完成任务管理Pydantic schemas (`app/schemas/task.py`)
- ✅ 完成考勤统计Pydantic schemas (`app/schemas/attendance.py`)
- ✅ 完成数据库种子脚本 (`app/utils/seed_data.py`)
- ✅ 完成测试基础架构和30+认证测试用例 (`tests/test_auth.py`, `tests/conftest.py`)
- ✅ 完成测试文档和运行脚本 (`backend/TESTING.md`, `backend/run_tests.py`)
- ✅ 完成模块验证脚本 (`backend/module_verification.py`)
- ✅ **已完成**: 所有Pydantic schemas层实现完毕（auth, member, task, attendance）
- 📋 **下一步**: 实现成员管理API路由 (`app/api/v1/members.py`)

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