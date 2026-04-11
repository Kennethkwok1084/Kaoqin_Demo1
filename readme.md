# 考勤管理系统

[![CI/CD](https://github.com/KangJianLin/Kaoqin_Demo/actions/workflows/ci.yml/badge.svg)](https://github.com/KangJianLin/Kaoqin_Demo/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/KangJianLin/Kaoqin_Demo/branch/main/graph/badge.svg)](https://codecov.io/gh/KangJianLin/Kaoqin_Demo)
[![Python 3.13+](https://img.shields.io/badge/python-3.13+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.116+-green.svg)](https://fastapi.tiangolo.com/)
[![Vue 3](https://img.shields.io/badge/Vue-3.0+-brightgreen.svg)](https://vuejs.org/)

## 项目简介

这是一个现代化的考勤管理系统，专为高校网络维护团队设计。系统提供完整的任务管理、工时统计和考勤分析功能，支持报修任务、监控任务和协助任务的全生命周期管理。

**技术架构**：采用前后端分离架构，后端使用 **Python + FastAPI + PostgreSQL**，前端使用 **Vue 3 + Capacitor** 构建跨平台应用，后期将混搭 **Flutter** 实现更丰富的移动端体验。

## V2口径基线声明

对外评审与联调时，统一以下两份文档为唯一外部基线：

- `docs/校园网部门综合运维工时平台_PostgreSQL建表SQL_V2.sql`
- `docs/校园网部门综合运维工时平台_接口返回规范_V2.docx`

以下资料中若存在 Flask/MySQL 或其他历史描述，均视为历史参考，不作为当前实现依据：

- `docs/old/` 下全部历史文档
- `docs/校园网部门综合运维工时平台_数据库表结构设计_接口清单_V2.docx` 中与当前代码不一致的历史段落

当前运行时口径以 FastAPI + PostgreSQL 实际代码为准。

## 协助任务二维码机制（task_qrcode）

- 管理端生成：`POST /api/v1/admin/tasks/{task_id}/qrcode/generate`
- 用户端获取当前：`GET /api/v1/tasks/{task_id}/qrcode/current`
- 签到校验入口：`POST /api/v1/tasks/{task_id}/sign-in`（`sign_in_type=qr/hybrid`）

生命周期与兼容策略：

1. 二维码令牌按时间桶动态生成，过期时间由系统配置 `checkin_qrcode_refresh_seconds`（兼容键：`task_qrcode_refresh_seconds`、`qrcode_refresh_seconds`）控制。
2. 服务端同时返回签名令牌 `qr_token` 与兼容令牌 `qr_token_legacy`，用于平滑迁移。
3. 校验窗口为“当前时间桶 + 上一时间桶”，降低客户端时钟与网络抖动带来的误拒。
4. 默认不落独立 task_qrcode 实体，采用无状态动态令牌；签到成功后仅在签到记录中保存实际使用令牌。

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
├── backend/docker-compose.yml  # 后端容器编排
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

## 📋 详细考勤管理制度

### 一、日常工作流程

#### （1）报修系统无线网络处理
负责处理报修系统无线网络报修单，进行诊断和解决，确保师生可以正常使用网络资源。

**时间要求**：
- 报修单需要24小时内响应
- 48小时内完成给出处理结果

**① 爆单处理流程**：
短时间内同类型异常报修单数量快速增加 → 上报 → 制定处理方案 → 根据处理方案解决报修单
- 仅做引导工作，反馈或协助报修人进行网络异常反馈
- 爆单按照15分钟/单计算

**② 线上报修单处理流程**：
接单 → 电话/微信联系 → 留言（三次）→ 线上处理 → 闭单
- 线上单按照40分钟/单计算
- 联系话术模板：
  - 第一次：【同学你好，这边通过电话/微信未能联系上，请你看到这则留言通过好友申请/回拨电话13XXXXXXXXX。】
  - 第二次：【同学你好，这边通过电话/微信未能联系上，请你看到这则留言通过好友申请/回拨电话13XXXXXXXXX。这边先做结单处理】

**③ 线下现场网络检测**：
线上无法处理 → 约定现场处理 → 现场检测并完成检测记录 → 闭单
- 线下单按照100分钟/单计算

**工时奖惩规则**：
- 非默认好评单加30分钟/单
- 超时响应单扣除组内30分钟/单/人
- 差评单扣除组内60分钟/单/人
- 超时处理单扣除处理人30分钟/人

#### （2）设备管理与维护
负责对园区的网络设备、机柜进行管理以及定期维护检查，形成设备清单和巡检记录，确保信息的准确性和可追溯性。
- 按照实际派发工作时长计算

#### （3）日常监控保障
负责日常监控保障网络，及时响应群内网络监控任务，确保网络的稳定性和安全性。
- 原则上组内必须有成员24小时值班以便及时响应紧急事件

### 二、协助任务

#### ① 推文更新
负责收集学生网管伙伴工作经验、技巧、技能以及知识，形成公开科普文章/内部白皮书；撰写记录部门活动通讯稿。

**工时计算**：每篇审核通过的文章可获得4小时协助时长

**工作流程**：选题 → 内容 → 素材 → 编辑 → 审核 → 发表

#### ② 流动服务摊位组
负责组织策划网络信息主题的流动服务方案，监督执行摊位活动事项，形成活动纪要。

**服务内容**：
- 协助教职员工或学生进行网络使用培训，提高他们的网络技能和意识
- 提供技术支持，帮助师生解决与网络相关的问题，比如网络连接、账号密码重置等

**协助时长**：按照派发工作任务时长或实际工作时间计算

#### ③ 其他协助任务
按照派发工作时长或实际工作时间计算

### 三、工作总结要求
按时保质处理报修单，定时定点完成机柜巡检。养成日常监控网络习惯，积极参与协助任务。

### 四、评优标准
学年工作满勤的前提下，通过【申请 → 初审 → 竞演 → 评分】得出。优秀者可获得部门"优秀学生助理"证书。

### 五、满勤时长
**30小时/月**，每月考勤需要本人签名。特殊情况无法及时签名，需要提前说明。

### 六、数据导入与自动识别逻辑

#### 导入表格说明
系统支持导入两类表格：

| 表格类型 | 说明 |
|----------|------|
| A表：报修单数据 | 原始报修记录，包含报修人、联系方式、时间、地点等 |
| B表：校园网维护记录 | 实际处理登记，包括检修形式、检修内容、负责人等 |

#### 匹配流程说明
1. 系统以【报修人姓名 + 联系方式】为**关键字段**，对 A、B 表进行一对一匹配
2. 匹配成功后，系统自动：
   - 读取 B 表中的 `检修形式` 字段 → 判断线上/线下任务
   - 读取相关字段 → 作为检修说明，自动写入任务描述
   - 标记任务属性（线上/线下），参与考勤计算
3. 无法匹配的数据标记为"未匹配记录"，反馈给管理员，A表中的报修单如果在B表中匹配不到，则默认为线上单

> ⚠️ 建议字段内容一致性需高，例如联系人名建议采用中文全名，避免同名冲突。

### 七、爆单任务标记机制
爆单任务需要由管理员在系统后台手动标记，当前支持：

| 标记方式 | 说明 |
|----------|------|
| 按日期批量选择 | 选择具体日期区间，勾选目标报修任务 |
| 按字段筛选 | 如字段包含"多个地点"、工单密集等特征 |
| 后续拓展（规划中） | 支持从 Excel 导入批量标记、或通过模型辅助识别爆单工单 |

> 管理员标记后任务自动加上"爆单"标签，计入考勤。

### 八、工时字段定义与存储结构
最终每条任务将根据标签打分，写入以下考勤字段：

| 字段名 | 含义 |
|--------|------|
| `repair_task_hours` | 本月报修任务累计时长（小时） |
| `monitoring_hours` | 本月监控任务累计时长（小时） |
| `assistance_hours` | 本月协助任务累计时长（小时） |
| `carried_hours` | 上月结转的剩余时长（小时） |
| `total_hours` | 实际总工时（小时） |
| `remaining_hours` | 扣除后可结转至下月的剩余工时 |

### 九、安全校验与权限要求
- 任务登记需用户登录，并具备操作权限
- 导入操作受限于管理员角色
- 系统自动记录每次导入和修改操作，生成审计日志

### 十、开发建议
- 所有任务应支持打标签机制，可并存多个标签
- 推荐建立任务标签枚举表，用于 UI 与后端同步
- 工时计算逻辑建议封装为统一服务接口，便于测试与复用
- 所有导入流程需进行字段匹配与校验，确保数据完整性

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

### 前后端独立部署（推荐）

- 详细文档：`docs/deployment/independent-deploy.md`
- 支持两种独立部署方式：
  - Docker：前后端分离编排（`deploy/docker/docker-compose.backend.yml`、`deploy/docker/docker-compose.frontend.yml`）
  - systemctl：后端 `kaoqin-backend.service` + 前端 `nginx.service`

快速命令（Docker）：

```bash
# 后端独立部署
docker compose --env-file deploy/docker/.env.backend -f deploy/docker/docker-compose.backend.yml up -d --build

# 前端独立部署
docker compose --env-file deploy/docker/.env.frontend -f deploy/docker/docker-compose.frontend.yml up -d --build
```

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
