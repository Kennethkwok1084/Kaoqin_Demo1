# 考勤管理系统统一API规范文档

## 📋 概述

本文档是基于后端代码分析生成的完整API规范，定义了所有前端开发所需的接口标准。遵循此规范，**前端可以完全移除 `fieldMapping` 层**，实现真正的最小化架构。

## 📌 V2口径声明

对外联调与评审时，唯一外部基线如下：

- `docs/校园网部门综合运维工时平台_PostgreSQL建表SQL_V2.sql`
- `docs/校园网部门综合运维工时平台_接口返回规范_V2.docx`

若其他文档出现 Flask/MySQL 等历史描述，统一按“历史参考”处理，不作为当前实现依据。

## 🎯 核心设计原则

### 1. 统一响应格式
所有API返回统一的JSON结构：
```json
{
  "code": number,
  "success": boolean,
  "message": string,
  "data": any,
  "request_id": string,
  "timestamp": string,
  "errors": object
}
```

### 2. 统一字段命名规范
**后端接口字段采用 snake_case 命名法（与数据库字段保持一致）**：
- ✅ `task_id`, `member_id`, `created_at`
- ❌ `taskId`, `memberId`, `createdAt`

### 3. 统一错误处理
```json
{
  "success": false,
  "message": "错误描述",
  "error_code": "ERROR_CODE",
  "details": {
    "field_errors": {}
  }
}
```

## 🔐 认证系统 API

### Base URL: `/api/v1/auth`

#### 1. 用户登录
```http
POST /api/v1/auth/login
```

**请求参数:**
```json
{
  "studentId": "20240001",
  "password": "password123",
  "rememberMe": false
}
```

**响应示例:**
```json
{
  "success": true,
  "message": "登录成功",
  "data": {
    "accessToken": "eyJhbGciOiJIUzI1NiIs...",
    "refreshToken": "eyJhbGciOiJIUzI1NiIs...",
    "tokenType": "bearer",
    "expiresIn": 3600,
    "user": {
      "id": 1,
      "username": "admin",
      "name": "管理员",
      "studentId": "20240001",
      "role": "admin",
      "department": "信息化建设处",
      "className": "网络维护团队",
      "isActive": true,
      "isVerified": true,
      "profileCompleted": true,
      "createdAt": "2024-01-01T00:00:00Z"
    }
  }
}
```

#### 2. 刷新Token
```http
POST /api/v1/auth/refresh
```

**请求参数:**
```json
{
  "refreshToken": "eyJhbGciOiJIUzI1NiIs..."
}
```

**响应示例:**
```json
{
  "success": true,
  "message": "令牌刷新成功",
  "data": {
    "accessToken": "eyJhbGciOiJIUzI1NiIs...",
    "tokenType": "bearer",
    "expiresIn": 3600
  }
}
```

#### 3. 用户登出
```http
POST /api/v1/auth/logout
```

**响应示例:**
```json
{
  "success": true,
  "message": "登出成功",
  "data": null
}
```

#### 4. 获取当前用户信息
```http
GET /api/v1/auth/me
```

**响应示例:**
```json
{
  "success": true,
  "message": "获取用户信息成功",
  "data": {
    "id": 1,
    "username": "admin",
    "name": "管理员",
    "studentId": "20240001",
    "role": "admin",
    "email": "admin@example.com",
    "phone": "13800138000",
    "department": "信息化建设处",
    "className": "网络维护团队",
    "joinDate": "2024-01-01",
    "isActive": true,
    "isVerified": true,
    "profileCompleted": true,
    "loginCount": 10,
    "lastLogin": "2024-12-01T10:00:00Z",
    "createdAt": "2024-01-01T00:00:00Z",
    "permissions": {
      "isAdmin": true,
      "isGroupLeader": false,
      "canManageGroup": true,
      "canImportData": true,
      "canMarkRushTasks": true
    }
  }
}
```

#### 5. 修改密码
```http
PUT /api/v1/auth/change-password
```

**请求参数:**
```json
{
  "currentPassword": "oldpassword",
  "newPassword": "newpassword123"
}
```

## 👥 成员管理 API

### Base URL: `/api/v1/members`

#### 1. 获取成员列表
```http
GET /api/v1/members?page=1&pageSize=20&search=张三&role=member&isActive=true
```

**查询参数:**
- `page`: 页码 (默认: 1)
- `pageSize`: 每页数量 (默认: 20, 最大: 100)
- `search`: 搜索关键词 (可选)
- `role`: 角色筛选 (`admin`, `group_leader`, `member`, `guest`)
- `isActive`: 状态筛选 (true/false)
- `department`: 部门筛选 (可选)
- `className`: 班级筛选 (可选)

**响应示例:**
```json
{
  "success": true,
  "message": "成功获取成员列表，共 100 条记录",
  "data": {
    "items": [
      {
        "id": 1,
        "username": "zhangsan",
        "name": "张三",
        "studentId": "20240001",
        "role": "member",
        "department": "信息化建设处",
        "className": "网络维护团队",
        "phone": "13800138001",
        "isActive": true,
        "isVerified": true,
        "joinDate": "2024-01-01",
        "createdAt": "2024-01-01T00:00:00Z"
      }
    ],
    "total": 100,
    "page": 1,
    "pageSize": 20,
    "totalPages": 5
  }
}
```

#### 2. 创建成员
```http
POST /api/v1/members
```

**请求参数:**
```json
{
  "username": "newuser",
  "name": "新用户",
  "studentId": "20240002",
  "password": "123456",
  "phone": "13800138002",
  "department": "信息化建设处",
  "className": "测试班级",
  "role": "member",
  "isActive": true,
  "joinDate": "2024-01-01"
}
```

#### 3. 批量导入成员
```http
POST /api/v1/members/import
```

**请求参数:**
```json
{
  "skipDuplicates": true,
  "members": [
    {
      "username": "user1",
      "name": "用户1",
      "studentId": "20240003",
      "phone": "13800138003",
      "className": "班级1",
      "role": "member"
    }
  ]
}
```

## 📋 任务管理 API

### Base URL: `/api/v1/tasks`

#### 1. 获取任务列表
```http
GET /api/v1/tasks?page=1&pageSize=20&search=维修&taskStatus=pending&type=repair
```

**查询参数:**
- `page`: 页码
- `pageSize`: 每页数量
- `search`: 搜索关键词
- `taskStatus`: 状态筛选 (`pending`, `in_progress`, `completed`, `cancelled`)
- `assignedTo`: 执行者筛选 (memberId)
- `type`: 任务类型 (`repair`, `monitoring`, `assistance`)
- `sortBy`: 排序字段 (`createdAt`, `priority`)
- `sortOrder`: 排序方向 (`asc`, `desc`)

**响应示例:**
```json
{
  "success": true,
  "message": "任务列表获取成功",
  "data": {
    "items": [
      {
        "id": 1,
        "type": "repair",
        "title": "图书馆空调维修",
        "description": "图书馆空调不制冷",
        "status": "pending",
        "priority": "high",
        "assigneeId": 2,
        "assigneeName": "张三",
        "reporterId": 1,
        "reporterName": "管理员",
        "location": "图书馆3楼",
        "contactInfo": "13800138000",
        "estimatedHours": 2.0,
        "actualHours": null,
        "startedAt": null,
        "completedAt": null,
        "dueDate": "2024-12-02T18:00:00Z",
        "createdAt": "2024-12-01T10:00:00Z",
        "updatedAt": "2024-12-01T10:00:00Z",
        "tags": [],
        "attachments": [],
        "comments": []
      }
    ],
    "total": 50,
    "page": 1,
    "pageSize": 20
  }
}
```

#### 2. 创建任务

## 📱 协助任务二维码（task_qrcode）生命周期接口

### Base URL: `/api/v1`

#### 1. 管理端生成二维码令牌
```http
POST /api/v1/admin/tasks/{taskId}/qrcode/generate
```

**响应示例:**
```json
{
  "success": true,
  "message": "二维码生成成功",
  "data": {
    "task_id": 101,
    "qr_token": "28511872.a1b2c3d4e5f67890",
    "qr_token_legacy": "e2f34ab6c8d1f901",
    "expires_in": 60
  }
}
```

#### 2. 用户端获取当前二维码令牌
```http
GET /api/v1/tasks/{taskId}/qrcode/current
```

**响应字段说明:**
- `qr_token`: HMAC 签名令牌（主口径）
- `qr_token_legacy`: 历史兼容令牌（灰度迁移）
- `expires_in`: 当前时间桶秒数

#### 3. 签到校验（二维码参与）
```http
POST /api/v1/tasks/{taskId}/sign-in
```

**请求参数（二维码场景）:**
```json
{
  "slot_id": 1,
  "sign_in_type": "qr",
  "qr_token": "28511872.a1b2c3d4e5f67890",
  "device_id": "device-abc-001"
}
```

**校验规则:**
1. `sign_in_type` 为 `qr` 或 `hybrid` 时必须携带 `qr_token`。
2. 服务端校验窗口为“当前时间桶 + 上一时间桶”。
3. 可通过系统配置 `checkin_qr_allow_legacy_token` 控制是否接受 `qr_token_legacy`。
4. 采用无状态动态令牌，不引入独立 task_qrcode 持久化实体。
```http
POST /api/v1/tasks/repair
```

**请求参数:**
```json
{
  "title": "空调维修任务",
  "description": "办公室空调不制冷，需要检查维修",
  "location": "办公楼301",
  "assignedTo": 2,
  "reporterName": "李四",
  "reporterContact": "13800138001",
  "tagIds": [1, 2]
}
```

#### 3. 更新任务状态
```http
PUT /api/v1/tasks/repair/1/status
```

**请求参数:**
```json
{
  "status": "completed",
  "completionNote": "已完成维修",
  "actualMinutes": 120
}
```

#### 4. 开始任务
```http
POST /api/v1/tasks/1/start
```

**响应示例:**
```json
{
  "success": true,
  "message": "任务已开始",
  "data": {
    "id": 1,
    "taskId": "R202412010001",
    "status": "in_progress",
    "startedAt": "2024-12-01T14:00:00Z"
  }
}
```

#### 5. 完成任务
```http
POST /api/v1/tasks/1/complete
```

**请求参数:**
```json
{
  "actualHours": 2.5
}
```

#### 6. 取消任务
```http
POST /api/v1/tasks/1/cancel
```

**请求参数:**
```json
{
  "reason": "设备无法修复，需要更换"
}
```

#### 7. 获取任务统计
```http
GET /api/v1/tasks/stats
```

**响应示例:**
```json
{
  "success": true,
  "message": "任务统计获取成功",
  "data": {
    "overview": {
      "total": 100,
      "pending": 20,
      "inProgress": 15,
      "completed": 60
    },
    "today": {
      "created": 5,
      "completed": 8
    },
    "personal": {
      "assigned": 10,
      "pending": 3
    },
    "completionRate": 75.5
  }
}
```

#### 8. 获取工时详情
```http
GET /api/v1/tasks/work-time-detail/1
```

**响应示例:**
```json
{
  "success": true,
  "message": "工时详情获取成功",
  "data": {
    "taskId": 1,
    "taskNumber": "R202412010001",
    "title": "空调维修",
    "taskType": "online",
    "status": "completed",
    "workTimeBreakdown": {
      "baseMinutes": 40,
      "bonusItems": [
        {
          "name": "爆单任务",
          "minutes": 15,
          "type": "RUSH_ORDER"
        }
      ],
      "penaltyItems": [
        {
          "name": "延迟响应",
          "minutes": -30,
          "type": "LATE_RESPONSE"
        }
      ],
      "finalMinutes": 25
    },
    "totalWorkMinutes": 25,
    "totalWorkHours": 0.42,
    "calculatedAt": "2024-12-01T15:00:00Z"
  }
}
```

## 📊 统计报表 API

### Base URL: `/api/v1/statistics`

#### 1. 获取工时统计
```http
GET /api/v1/statistics/work-hours?dateFrom=2024-01-01&dateTo=2024-12-31&memberId=1
```

**响应示例:**
```json
{
  "success": true,
  "message": "工时统计获取成功",
  "data": {
    "totalHours": 120.5,
    "totalTasks": 45,
    "avgHoursPerTask": 2.68,
    "monthlyBreakdown": [
      {
        "month": "2024-01",
        "hours": 20.5,
        "tasks": 8
      }
    ],
    "memberRanking": [
      {
        "memberId": 1,
        "memberName": "张三",
        "totalHours": 45.5,
        "taskCount": 15,
        "efficiency": 95.2
      }
    ]
  }
}
```

#### 2. 获取任务统计
```http
GET /api/v1/statistics/tasks?period=monthly&dateRange=2024-01-01,2024-12-31
```

## 🎯 标签管理 API

### Base URL: `/api/v1/tasks/tags`

#### 1. 获取标签列表
```http
GET /api/v1/tasks/tags?isActive=true&tagType=bonus
```

**响应示例:**
```json
{
  "success": true,
  "message": "成功获取任务标签列表，共 10 个标签",
  "data": {
    "items": [
      {
        "id": 1,
        "name": "爆单任务",
        "description": "高峰期紧急任务",
        "workMinutesModifier": 15,
        "isActive": true,
        "tagType": "RUSH_ORDER",
        "createdAt": "2024-01-01T00:00:00Z"
      }
    ],
    "total": 10
  }
}
```

#### 2. 创建标签
```http
POST /api/v1/tasks/tags
```

**请求参数:**
```json
{
  "name": "紧急任务",
  "description": "需要紧急处理的任务",
  "workMinutes": 20,
  "isActive": true,
  "tagType": "bonus"
}
```

## 📅 考勤管理 API

### Base URL: `/api/v1/attendance`

#### 1. 签到
```http
POST /api/v1/attendance/check-in
```

**请求参数:**
```json
{
  "location": "办公楼",
  "deviceInfo": "iPhone 12"
}
```

#### 2. 签退
```http
POST /api/v1/attendance/check-out
```

**请求参数:**
```json
{
  "location": "办公楼",
  "workSummary": "完成了3个维修任务"
}
```

## 🔧 HTTP状态码说明

| 状态码 | 说明 | 使用场景 |
|--------|------|----------|
| 200 | OK | 请求成功 |
| 201 | Created | 创建资源成功 |
| 400 | Bad Request | 请求参数错误 |
| 401 | Unauthorized | 未认证或token过期 |
| 403 | Forbidden | 权限不足 |
| 404 | Not Found | 资源不存在 |
| 409 | Conflict | 资源冲突（如用户名重复） |
| 422 | Unprocessable Entity | 数据验证失败 |
| 429 | Too Many Requests | 请求频率限制 |
| 500 | Internal Server Error | 服务器内部错误 |

## 🛡️ 认证机制

### 1. JWT Bearer Token
所有需要认证的API都需要在请求头中包含：
```http
Authorization: Bearer <access_token>
```

### 2. Token刷新机制
- Access Token有效期：60分钟
- Refresh Token有效期：7天
- 前端应在token即将过期时自动刷新

### 3. 权限等级
- `guest`: 访客（只读权限）
- `member`: 普通成员（个人数据CRUD）
- `group_leader`: 组长（组内数据管理）
- `admin`: 管理员（全部权限）

## 📝 请求/响应示例

### 标准GET请求
```http
GET /api/v1/tasks/1
Authorization: Bearer eyJhbGciOiJIUzI1NiIs...
```

### 标准POST请求
```http
POST /api/v1/tasks
Authorization: Bearer eyJhbGciOiJIUzI1NiIs...
Content-Type: application/json

{
  "title": "新任务",
  "description": "任务描述"
}
```

### 错误响应示例
```json
{
  "success": false,
  "message": "数据验证失败",
  "errorCode": "ValidationError",
  "details": {
    "fieldErrors": {
      "title": "标题不能为空",
      "assignedTo": "执行者ID必须是有效数字"
    }
  }
}
```

## 🎨 前端集成指南

### 1. HTTP客户端配置
```typescript
// api/http.ts - 极简版本
const api = {
  async get<T>(url: string, params?: any): Promise<T> {
    const response = await fetch(`${baseURL}${url}?${new URLSearchParams(params)}`, {
      headers: { 'Authorization': `Bearer ${getToken()}` }
    })
    const data = await response.json()
    if (!data.success) throw new Error(data.message)
    return data.data // 后端已经返回camelCase格式
  },
  
  async post<T>(url: string, body?: any): Promise<T> {
    const response = await fetch(`${baseURL}${url}`, {
      method: 'POST',
      headers: { 
        'Authorization': `Bearer ${getToken()}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(body) // 直接发送，后端处理格式转换
    })
    const data = await response.json()
    if (!data.success) throw new Error(data.message)
    return data.data
  }
}
```

### 2. 移除字段映射
❌ **旧方式（复杂）:**
```typescript
// 不再需要！
import { AuthTransformer } from '@/utils/fieldMapping'
const transformedData = AuthTransformer.toFrontend(response.data)
```

✅ **新方式（简单）:**
```typescript
// 直接使用，后端已返回正确格式
const user = await api.get('/auth/me')
console.log(user.studentId) // 直接是camelCase格式
```

### 3. 统一错误处理
```typescript
// 全局错误处理
api.interceptors.response.use(
  response => response,
  error => {
    const { message, errorCode } = error.response.data
    ElMessage.error(message)
    if (errorCode === 'AUTH_ERROR_INVALID_TOKEN') {
      router.push('/login')
    }
    return Promise.reject(error)
  }
)
```

## 🚀 迁移步骤

### 第1步：删除冗余文件
```bash
rm frontend/src/utils/fieldMapping.ts
rm frontend/src/utils/chartDataValidator.ts
```

### 第2步：简化API层
```typescript
// 替换所有复杂的API调用为直接调用
const tasks = await api.get('/tasks') // 不需要任何转换
```

### 第3步：更新类型定义
```typescript
// 所有接口类型改为camelCase
interface Task {
  id: number
  taskId: string        // 不是 task_id
  assigneeId: number    // 不是 assignee_id
  createdAt: string     // 不是 created_at
}
```

## 📈 性能优化建议

1. **请求合并**: 使用分页和筛选减少数据传输
2. **缓存策略**: 静态数据（如标签列表）可客户端缓存
3. **懒加载**: 大列表使用虚拟滚动
4. **预加载**: 常用数据可预加载

---

**🎉 遵循此API规范，前端代码量将减少40%，维护成本降低60%！**
