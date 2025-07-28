# 考勤管理系统

## 项目简介

这是一个现代化的考勤管理系统，专为高校网络维护团队设计。系统提供完整的任务管理、工时统计和考勤分析功能，支持报修任务、监控任务和协助任务的全生命周期管理。

**技术架构**：采用前后端分离架构，后端使用 **Python + FastAPI + PostgreSQL**，前端使用 **Vue 3 + Capacitor** 构建跨平台应用，后期将混搭 **Flutter** 实现更丰富的移动端体验。

## 核心功能

### 📋 任务管理
- **报修任务**：支持线上/线下任务分类，自动工时计算
- **监控任务**：日常巡检和网络监控任务管理
- **协助任务**：跨部门协助工作记录和统计
- **爆单标记**：管理员可标记高峰期任务，享受额外工时奖励

### ⏱️ 智能工时计算
- **基础工时**：线上任务40分钟/单，线下任务100分钟/单
- **奖励机制**：爆单任务+15分钟，非默认好评+30分钟
- **异常扣时**：超时响应(-30分钟)、超时处理(-30分钟)、差评(-60分钟)
- **多标签累计**：单个任务可拥有多个标签，工时累计计算

### 📊 数据分析
- **实时统计**：月度工时汇总、任务完成率分析
- **可视化图表**：工时趋势、任务分布、成员绩效对比
- **导出功能**：支持Excel格式的详细报表导出

### 🔒 安全保障
- **JWT双令牌认证**：Access Token + Refresh Token机制
- **AES-256-GCM加密**：敏感数据端到端加密
- **HTTPS/TLS**：传输层安全保护
- **权限控制**：基于角色的访问控制(RBAC)

## 技术栈

### 后端技术
- **语言**：Python 3.11+
- **框架**：FastAPI (高性能异步Web框架)
- **数据库**：PostgreSQL 14+
  - 生产环境：`attendence` (用户: kwok, 密码: Onjuju1084)
  - 开发环境：`attendence_dev` (用户: kwok, 密码: Onjuju1084)
- **ORM**：SQLAlchemy 2.0 (现代化数据库操作)
- **认证**：JWT + Passlib (密码哈希)
- **API文档**：Swagger/OpenAPI 自动生成
- **测试**：Pytest + FastAPI TestClient

### 前端技术
- **框架**：Vue 3 (Composition API)
- **跨平台**：Capacitor (iOS/Android/Web统一开发)
- **UI组件库**：Element Plus / Ant Design Vue
- **状态管理**：Pinia (Vue 3官方推荐)
- **图表库**：ECharts / Chart.js
- **构建工具**：Vite (快速构建和热重载)
- **移动端增强**：后期集成Flutter组件

### 开发工具
- **容器化**：Docker + Docker Compose
- **代码质量**：ESLint + Prettier + Black
- **版本控制**：Git + GitFlow
- **CI/CD**：GitHub Actions / GitLab CI

## 项目结构

```
attendance-system/
├── backend/                 # FastAPI后端
│   ├── app/
│   │   ├── api/            # API路由
│   │   ├── core/           # 核心配置
│   │   ├── models/         # 数据模型
│   │   ├── schemas/        # Pydantic模式
│   │   ├── services/       # 业务逻辑
│   │   └── utils/          # 工具函数
│   ├── tests/              # 测试文件
│   ├── alembic/            # 数据库迁移
│   ├── requirements.txt    # Python依赖
│   └── Dockerfile          # 后端容器配置
├── frontend/               # Vue 3前端
│   ├── src/
│   │   ├── components/     # Vue组件
│   │   ├── views/          # 页面视图
│   │   ├── stores/         # Pinia状态管理
│   │   ├── utils/          # 工具函数
│   │   └── assets/         # 静态资源
│   ├── capacitor.config.ts # Capacitor配置
│   ├── package.json        # 前端依赖
│   └── Dockerfile          # 前端容器配置
├── mobile/                 # Flutter移动端(后期)
├── docs/                   # 项目文档
├── docker-compose.yml      # 容器编排
└── README.md              # 项目说明
```

## 业务规则

### 工时计算规则

| 任务类型 | 基础工时 | 说明 |
|---------|---------|------|
| 线上任务 | 40分钟/单 | 远程处理的报修任务 |
| 线下任务 | 100分钟/单 | 需要现场处理的报修任务 |
| 爆单任务 | +15分钟/单 | 管理员标记的高峰期任务 |
| 非默认好评 | +30分钟/单 | 用户主动给出的好评 |

### 异常扣时规则

| 异常类型 | 影响范围 | 扣时规则 |
|---------|---------|----------|
| 超时响应 | 组内所有成员 | -30分钟/单/人 (响应>24h) |
| 超时处理 | 实际处理人 | -30分钟/人 (处理>48h) |
| 差评任务 | 组内所有成员 | -60分钟/单/人 |

### 监控任务规则
- **巡检任务**：现场设备检查，手动登记时长
- **日常监控**：网络状态监控，按实际工作时间计算
- **任务比例**：巡检与监控建议比例为4:6

## 快速开始

### 环境要求
- Python 3.12+ / 3.13+
- Node.js 18+
- PostgreSQL 15+
- uv (推荐) 或 pip
- Docker & Docker Compose (可选)

### 本地开发

#### 1. 克隆项目
```bash
git clone <repository-url>
cd attendance-system
```

#### 2. 后端设置

**使用uv (推荐)**
```bash
cd backend

# 安装uv (如果尚未安装)
# Linux/macOS: curl -LsSf https://astral.sh/uv/install.sh | sh
# Windows: powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# 创建虚拟环境并安装依赖
uv venv
uv sync

# 激活虚拟环境
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 配置环境变量
cp .env.example .env
# 编辑 .env 文件，配置数据库连接等

# 数据库迁移
uv run alembic upgrade head

# 启动开发服务器
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**使用传统pip方式**
```bash
cd backend

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
# 编辑 .env 文件，配置数据库连接等

# 数据库迁移
alembic upgrade head

# 启动开发服务器
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### 3. 前端设置
```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev

# 构建移动端应用
npm run build
npx cap add ios
npx cap add android
npx cap sync
```

#### 4. 数据库配置
```sql
-- 创建数据库
CREATE DATABASE attendence OWNER kwok;
CREATE DATABASE attendence_dev OWNER kwok;

-- 创建用户(如果不存在)
CREATE USER kwok WITH PASSWORD 'Onjuju1084';
GRANT ALL PRIVILEGES ON DATABASE attendence TO kwok;
GRANT ALL PRIVILEGES ON DATABASE attendence_dev TO kwok;
```

### Docker部署

```bash
# 构建并启动所有服务
docker-compose up -d

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f
```

## API文档

启动后端服务后，访问以下地址查看API文档：
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### 主要API端点

#### 认证相关
- `POST /api/auth/login` - 用户登录
- `POST /api/auth/refresh` - 刷新令牌
- `POST /api/auth/logout` - 用户登出

#### 任务管理
- `GET /api/tasks/repair` - 获取报修任务列表
- `POST /api/tasks/repair` - 创建报修任务
- `PUT /api/tasks/repair/{id}` - 更新报修任务
- `POST /api/tasks/repair/import` - 批量导入报修数据

#### 统计分析
- `GET /api/statistics/overview` - 获取总览统计
- `GET /api/statistics/member/{id}` - 获取成员统计
- `GET /api/statistics/export` - 导出统计报表

## 数据模型

### 核心实体

#### Member (成员)
```python
class Member(BaseModel):
    id: int
    name: str
    student_id: str
    group_id: int
    class_name: str
    dormitory: str
    phone: str  # 加密存储
    email: str
    role: UserRole
    is_active: bool
    created_at: datetime
    updated_at: datetime
```

#### RepairTask (报修任务)
```python
class RepairTask(BaseModel):
    id: int
    task_id: str
    member_id: int
    title: str
    description: str
    location: str
    category: TaskCategory
    priority: TaskPriority
    status: TaskStatus
    report_time: datetime
    response_time: Optional[datetime]
    completion_time: Optional[datetime]
    feedback: Optional[str]
    rating: Optional[int]
    work_minutes: int
    tags: List[TaskTag]
    created_at: datetime
    updated_at: datetime
```

#### AttendanceRecord (考勤记录)
```python
class AttendanceRecord(BaseModel):
    id: int
    member_id: int
    month: str  # YYYY-MM格式
    repair_task_hours: float
    monitoring_hours: float
    assistance_hours: float
    carried_hours: float
    total_hours: float
    remaining_hours: float
    created_at: datetime
    updated_at: datetime
```

## 安全实现

### 认证机制
- **JWT双令牌系统**：短期访问令牌(1小时) + 长期刷新令牌(7天)
- **密码安全**：使用bcrypt进行密码哈希，支持密码强度验证
- **会话管理**：支持令牌撤销和会话过期处理

### 数据加密
- **传输加密**：全站HTTPS，TLS 1.2+
- **存储加密**：敏感字段使用AES-256-GCM加密
- **密钥管理**：环境变量管理，支持密钥轮换

### 权限控制
- **角色定义**：管理员、组长、普通成员
- **资源保护**：基于角色和资源的访问控制
- **操作审计**：关键操作日志记录

## 测试策略

### 后端测试
```bash
# 运行所有测试
pytest

# 运行特定测试
pytest tests/test_auth.py

# 生成覆盖率报告
pytest --cov=app tests/
```

### 前端测试
```bash
# 单元测试
npm run test:unit

# E2E测试
npm run test:e2e

# 组件测试
npm run test:component
```

### API测试
- **自动化测试**：Postman/Newman集成测试
- **性能测试**：使用Locust进行负载测试
- **安全测试**：OWASP ZAP安全扫描

## 部署指南

### 生产环境部署

#### 1. 服务器要求
- **CPU**: 4核心以上
- **内存**: 8GB以上
- **存储**: 100GB SSD
- **操作系统**: Ubuntu 20.04 LTS / CentOS 8

#### 2. 环境配置
```bash
# 安装Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# 安装Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# 配置防火墙
sudo ufw allow 80
sudo ufw allow 443
sudo ufw allow 22
sudo ufw enable
```

#### 3. SSL证书配置
```bash
# 使用Let's Encrypt
sudo apt install certbot
sudo certbot certonly --standalone -d your-domain.com
```

#### 4. 生产部署
```bash
# 克隆项目
git clone <repository-url>
cd attendance-system

# 配置生产环境变量
cp .env.production.example .env.production
# 编辑环境变量文件

# 启动生产服务
docker-compose -f docker-compose.prod.yml up -d

# 配置Nginx反向代理
sudo cp nginx.conf /etc/nginx/sites-available/attendance
sudo ln -s /etc/nginx/sites-available/attendance /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### 监控和维护

#### 日志管理
```bash
# 查看应用日志
docker-compose logs -f backend
docker-compose logs -f frontend

# 日志轮换配置
sudo logrotate -d /etc/logrotate.d/attendance
```

#### 数据备份
```bash
# 数据库备份脚本
#!/bin/bash
BACKUP_DIR="/backup/postgresql"
DATE=$(date +"%Y%m%d_%H%M%S")
pg_dump -h localhost -U kwok -d attendence > "$BACKUP_DIR/attendence_$DATE.sql"

# 定时备份(crontab)
0 2 * * * /path/to/backup-script.sh
```

## 开发计划

### 已完成功能 ✅
- [x] 数据库设计和模型定义
- [x] 后端API开发(FastAPI)
- [x] JWT认证系统
- [x] 工时计算逻辑
- [x] 数据导入功能
- [x] 基础测试覆盖

### 进行中功能 🚧
- [ ] Vue 3前端界面开发
- [ ] Capacitor移动端适配
- [ ] 数据可视化图表
- [ ] 用户权限管理

### 计划功能 📋
- [ ] Flutter组件集成
- [ ] 实时通知系统
- [ ] 高级数据分析
- [ ] 移动端离线支持
- [ ] 微信小程序版本

## 贡献指南

### 开发规范
- **代码风格**：遵循PEP 8(Python)和ESLint(JavaScript)
- **提交规范**：使用Conventional Commits格式
- **分支策略**：GitFlow工作流
- **代码审查**：所有PR需要至少一人审查

### 提交流程
1. Fork项目到个人仓库
2. 创建功能分支：`git checkout -b feature/new-feature`
3. 提交更改：`git commit -m 'feat: add new feature'`
4. 推送分支：`git push origin feature/new-feature`
5. 创建Pull Request

## 许可证

本项目采用 MIT 许可证，详情请参阅 [LICENSE](LICENSE) 文件。

## 联系方式

- **项目维护者**：开发团队
- **技术支持**：[技术支持邮箱]
- **问题反馈**：[GitHub Issues]

---

**最后更新**：2025-01-21  
**版本**：v2.0.0  
**文档版本**：v2.0.0

