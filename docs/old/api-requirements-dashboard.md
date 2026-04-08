# 仪表板API需求文档

## 问题说明
当前仪表板使用了静态数据，需要真实的API数据来替换。根据现有API文档分析，缺少以下仪表板专用的API接口。

## 需求的API接口

### 1. 仪表板概览数据 API
```http
GET /api/v1/dashboard/overview
```

**用途**: 获取仪表板首页的所有核心指标数据

**请求参数**: 无需参数（根据当前登录用户自动计算）

**需要的响应数据**:
```json
{
  "success": true,
  "message": "仪表板数据获取成功",
  "data": {
    "metrics": {
      "totalTasks": 156,           // 总任务数
      "inProgress": 23,            // 进行中任务数
      "pending": 45,               // 待处理任务数
      "completedThisMonth": 88,    // 本月完成任务数
      "systemStatus": "healthy"    // 系统状态: healthy/warning/error
    },
    "trends": {
      "totalTasksTrend": {
        "value": 12.5,             // 增长百分比
        "direction": "up"          // up/down/stable
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
      "onlineUsers": 12,           // 在线用户数
      "lastDataSync": "2024-12-01T10:00:00Z",  // 最后数据同步时间
      "systemUptime": "99.9%"      // 系统可用性
    }
  }
}
```

### 2. 我的任务列表 API (仪表板专用)
```http
GET /api/v1/dashboard/my-tasks?limit=5
```

**用途**: 获取当前用户分配的任务，仅显示最近的5条

**请求参数**:
- `limit`: 限制返回数量 (默认5条)

**需要的响应数据**:
```json
{
  "success": true,
  "message": "我的任务获取成功",
  "data": {
    "tasks": [
      {
        "id": 1,
        "title": "图书馆空调维修",
        "status": "pending",         // pending/in_progress/completed
        "priority": "high",          // high/medium/low
        "location": "图书馆3楼",
        "createdAt": "2024-12-01T10:00:00Z",
        "dueDate": "2024-12-02T18:00:00Z"
      }
    ],
    "totalAssigned": 10            // 我被分配的任务总数
  }
}
```

### 3. 最近活动API
```http
GET /api/v1/dashboard/recent-activities?limit=4
```

**用途**: 获取系统最近的活动记录，用于活动时间线展示

**请求参数**:
- `limit`: 限制返回数量 (默认4条)

**需要的响应数据**:
```json
{
  "success": true,
  "message": "最近活动获取成功",
  "data": {
    "activities": [
      {
        "id": 1,
        "type": "task_created",      // task_created/task_completed/task_status_changed/user_login
        "title": "创建了新任务",
        "description": "\"图书馆空调维修\" - 紧急任务",
        "actorName": "张三",         // 操作者姓名
        "createdAt": "2024-12-01T12:00:00Z",
        "priority": "primary"        // primary/success/warning/info (对应颜色)
      },
      {
        "id": 2,
        "type": "task_completed",
        "title": "完成了任务", 
        "description": "\"实验室网络检修\" - 已验收通过",
        "actorName": "李四",
        "createdAt": "2024-12-01T08:00:00Z",
        "priority": "success"
      },
      {
        "id": 3,
        "type": "task_status_changed",
        "title": "任务状态变更",
        "description": "\"宿舍网络优化\" - 等待审批",
        "actorName": "王五",
        "createdAt": "2024-12-01T06:00:00Z", 
        "priority": "warning"
      },
      {
        "id": 4,
        "type": "user_login",
        "title": "用户登录",
        "description": "张三 - 从 192.168.1.100 登录",
        "actorName": "张三",
        "createdAt": "2024-12-01T04:00:00Z",
        "priority": "info"
      }
    ]
  }
}
```

## 当前存在的API（可以使用的）
根据现有API文档，以下接口已存在，可以直接使用：

1. `GET /api/v1/tasks/stats` - 基础任务统计（但缺少趋势数据）
2. `GET /api/v1/tasks` - 任务列表（但需要根据当前用户过滤）
3. `GET /api/v1/auth/me` - 当前用户信息

## 前端实现计划

1. **删除所有静态数据**：移除模板中的硬编码数值
2. **加载状态处理**：显示加载中的状态，而不是静态fallback值
3. **错误处理**：当API返回错误时显示错误信息
4. **数据更新**：实现数据刷新功能

## 优先级
1. **高优先级**: 仪表板概览数据API - 核心指标展示
2. **中优先级**: 我的任务列表API - 个人任务展示  
3. **低优先级**: 最近活动API - 活动时间线展示（可以暂时隐藏这个模块）

如果部分API暂时无法提供，我可以：
- 先隐藏对应的UI模块
- 或显示"数据加载中"状态
- 或显示"暂无数据"提示

请确认这些API需求是否合理，以及你希望优先实现哪些接口。