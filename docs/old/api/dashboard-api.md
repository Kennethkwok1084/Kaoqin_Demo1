# 仪表板API规范文档

## 📋 概述

本文档定义了仪表板模块专用的API接口规范，提供仪表板所需的概览数据、任务摘要、活动时间线等功能。所有接口遵循项目统一的响应格式和字段命名规范。

## 🎯 设计原则

### 1. 统一响应格式
```json
{
  "success": boolean,
  "message": string,
  "data": any
}
```

### 2. 字段命名规范
采用 camelCase 命名法，与前端保持一致。

### 3. 数据聚合
仪表板API专注于数据聚合和统计，减少前端数据处理工作。

## 🏠 仪表板API

### Base URL: `/api/v1/dashboard`

---

#### 1. 获取仪表板概览数据
```http
GET /api/v1/dashboard/overview
```

**功能描述**: 获取仪表板首页的所有核心指标和趋势数据

**权限要求**: 需要认证

**请求参数**: 无

**响应示例**:
```json
{
  "success": true,
  "message": "仪表板数据获取成功",
  "data": {
    "metrics": {
      "totalTasks": 156,
      "inProgress": 23,
      "pending": 45,
      "completedThisMonth": 88,
      "systemStatus": "healthy"
    },
    "trends": {
      "totalTasksTrend": {
        "value": 12.5,
        "direction": "up"
      },
      "inProgressTrend": {
        "value": 8.3,
        "direction": "up"
      },
      "pendingTrend": {
        "value": 5.2,
        "direction": "down"
      },
      "completedTrend": {
        "value": 15.7,
        "direction": "up"
      }
    },
    "systemInfo": {
      "onlineUsers": 12,
      "lastDataSync": "2024-12-01T10:00:00Z",
      "systemUptime": "99.9%"
    }
  }
}
```

**字段说明**:
- `metrics.totalTasks`: 总任务数
- `metrics.inProgress`: 进行中的任务数
- `metrics.pending`: 待处理的任务数
- `metrics.completedThisMonth`: 本月完成的任务数
- `metrics.systemStatus`: 系统状态 (`healthy`|`warning`|`error`)
- `trends.*.value`: 相比上期的变化百分比
- `trends.*.direction`: 趋势方向 (`up`|`down`|`stable`)
- `systemInfo.onlineUsers`: 当前在线用户数
- `systemInfo.lastDataSync`: 最后数据同步时间(ISO 8601格式)
- `systemInfo.systemUptime`: 系统可用性百分比

---

#### 2. 获取我的任务摘要
```http
GET /api/v1/dashboard/my-tasks
```

**功能描述**: 获取当前用户相关的任务摘要，用于仪表板任务卡片展示

**权限要求**: 需要认证

**请求参数**:
| 参数 | 类型 | 默认值 | 说明 |
|-----|------|--------|------|
| limit | int | 5 | 返回任务数量限制 |

**响应示例**:
```json
{
  "success": true,
  "message": "我的任务获取成功",
  "data": {
    "tasks": [
      {
        "id": 1,
        "title": "图书馆空调维修",
        "status": "pending",
        "priority": "high",
        "location": "图书馆3楼",
        "createdAt": "2024-12-01T10:00:00Z",
        "dueDate": "2024-12-02T18:00:00Z"
      },
      {
        "id": 2,
        "title": "实验室网络检修",
        "status": "in_progress",
        "priority": "medium",
        "location": "实验楼B202",
        "createdAt": "2024-11-30T09:00:00Z",
        "dueDate": "2024-12-01T17:00:00Z"
      }
    ],
    "summary": {
      "totalAssigned": 10,
      "pending": 3,
      "inProgress": 2,
      "completed": 5
    }
  }
}
```

**字段说明**:
- `tasks`: 任务列表（按创建时间倒序，限制数量）
- `tasks[].status`: 任务状态 (`pending`|`in_progress`|`completed`)
- `tasks[].priority`: 优先级 (`high`|`medium`|`low`)
- `summary.totalAssigned`: 我被分配的任务总数
- `summary.pending`: 我的待处理任务数
- `summary.inProgress`: 我的进行中任务数
- `summary.completed`: 我的已完成任务数

---

#### 3. 获取最近活动
```http
GET /api/v1/dashboard/recent-activities
```

**功能描述**: 获取系统最近的活动记录，用于活动时间线展示

**权限要求**: 需要认证

**请求参数**:
| 参数 | 类型 | 默认值 | 说明 |
|-----|------|--------|------|
| limit | int | 10 | 返回活动数量限制 |

**响应示例**:
```json
{
  "success": true,
  "message": "最近活动获取成功",
  "data": {
    "activities": [
      {
        "id": 1,
        "type": "task_created",
        "title": "创建了新任务",
        "description": "\"图书馆空调维修\" - 紧急任务",
        "actorName": "张三",
        "actorId": "20240001",
        "targetId": 1,
        "targetType": "task",
        "createdAt": "2024-12-01T12:00:00Z",
        "priority": "primary"
      },
      {
        "id": 2,
        "type": "task_completed",
        "title": "完成了任务",
        "description": "\"实验室网络检修\" - 已验收通过",
        "actorName": "李四",
        "actorId": "20240002",
        "targetId": 2,
        "targetType": "task",
        "createdAt": "2024-12-01T08:00:00Z",
        "priority": "success"
      },
      {
        "id": 3,
        "type": "task_status_changed",
        "title": "任务状态变更",
        "description": "\"宿舍网络优化\" - 等待审批",
        "actorName": "王五",
        "actorId": "20240003",
        "targetId": 3,
        "targetType": "task",
        "createdAt": "2024-12-01T06:00:00Z",
        "priority": "warning"
      },
      {
        "id": 4,
        "type": "user_login",
        "title": "用户登录",
        "description": "张三 - 从 192.168.1.100 登录",
        "actorName": "张三",
        "actorId": "20240001",
        "targetId": null,
        "targetType": null,
        "createdAt": "2024-12-01T04:00:00Z",
        "priority": "info"
      }
    ],
    "summary": {
      "total": 45,
      "todayCount": 8
    }
  }
}
```

**字段说明**:
- `activities`: 活动记录列表（按时间倒序）
- `activities[].type`: 活动类型 (`task_created`|`task_completed`|`task_status_changed`|`user_login`|`task_assigned`)
- `activities[].title`: 活动标题（用于显示）
- `activities[].description`: 活动详细描述
- `activities[].actorName`: 操作者姓名
- `activities[].actorId`: 操作者ID
- `activities[].targetId`: 目标对象ID（如任务ID）
- `activities[].targetType`: 目标对象类型 (`task`|`member`|null)
- `activities[].priority`: 显示优先级 (`primary`|`success`|`warning`|`info`) - 对应Ant Design颜色
- `summary.total`: 活动记录总数
- `summary.todayCount`: 今日活动数量

---

## 📊 数据统计说明

### 趋势计算逻辑
趋势数据通过对比相同时间段的历史数据计算：
- 对于月度数据：对比上个月同期
- 对于周度数据：对比上周同期
- 对于日度数据：对比昨天同期

### 系统状态判断
- `healthy`: 所有核心指标正常
- `warning`: 存在需要关注的问题（如任务积压）
- `error`: 存在严重问题（如系统异常）

### 活动类型定义
| 类型 | 说明 | 优先级 |
|-----|------|--------|
| `task_created` | 任务创建 | `primary` |
| `task_completed` | 任务完成 | `success` |
| `task_status_changed` | 任务状态变更 | `warning` |
| `task_assigned` | 任务分配 | `info` |
| `user_login` | 用户登录 | `info` |

## 🚫 错误响应

### 通用错误响应格式
```json
{
  "success": false,
  "message": "错误描述",
  "errorCode": "ERROR_CODE"
}
```

### 常见错误码
| 错误码 | 说明 |
|-------|------|
| `UNAUTHORIZED` | 未认证或token过期 |
| `FORBIDDEN` | 无权限访问 |
| `INVALID_PARAMETER` | 请求参数无效 |
| `INTERNAL_ERROR` | 服务器内部错误 |

## 🔄 使用建议

### 1. 数据刷新策略
- 仪表板概览数据：建议30秒自动刷新
- 我的任务：建议60秒自动刷新或手动刷新
- 最近活动：建议实时更新（WebSocket）或15秒轮询

### 2. 缓存策略
- 概览数据可缓存30秒
- 任务数据可缓存60秒
- 活动数据建议不缓存

### 3. 错误处理
- 网络错误：显示重试按钮
- 权限错误：跳转到登录页
- 数据为空：显示空状态提示

## 📝 实现优先级

1. **高优先级**: `GET /api/v1/dashboard/overview` - 核心指标展示
2. **中优先级**: `GET /api/v1/dashboard/my-tasks` - 个人任务展示
3. **低优先级**: `GET /api/v1/dashboard/recent-activities` - 活动时间线

如果暂时无法实现某些API，前端可以：
- 隐藏对应的UI模块
- 显示"数据加载中"状态
- 显示"暂无数据"提示
