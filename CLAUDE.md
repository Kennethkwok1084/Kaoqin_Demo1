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
- 🚧 **Backend API**: Core structure ready, but routes and services need implementation
- 🚧 **Frontend**: Basic Vue 3 structure exists, components need development
- ❌ **Integration**: Frontend-backend integration pending
- ❌ **Testing**: Test suites need implementation
- ❌ **Deployment**: Docker and deployment configuration pending

### 🔥 High Priority Tasks (Phase 1)

#### Backend Core Implementation
- [ ] **API Routes & Endpoints** - Implement `/api/v1/auth`, `/api/v1/members`, `/api/v1/tasks`, `/api/v1/attendance`
- [ ] **Pydantic Schemas** - Create request/response validation schemas for all endpoints
- [ ] **Business Logic Services** - Implement `auth_service`, `task_service`, `stats_service`, `import_service`
- [ ] **Authentication System** - Complete JWT token generation/validation, password hashing, permissions
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
**Last Updated**: 2025-01-27

#### 2025-01-27
- ✅ Project structure analysis completed
- ✅ Comprehensive todo list created with 30 actionable items
- ✅ Progress tracking system established
- 📋 Next: Begin Phase 1 implementation starting with backend API routes

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