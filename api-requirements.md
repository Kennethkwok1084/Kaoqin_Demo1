# 前端适配缺失API需求清单

基于需求文档分析，前端（frontend-new）需要以下缺失的API接口：

## 1. 协助任务审核API（优先级：P0 - 立即实现）

**需求来源**: 需求2.3 - "学生网管登记的协助任务需经管理员或超级管理员审核通过后，方可计入工时"

### 1.1 协助任务审核接口

```typescript
// 需要在后端实现
POST /api/v1/tasks/assistance/{task_id}/approve
PUT  /api/v1/tasks/assistance/{task_id}/reject
GET  /api/v1/tasks/assistance/pending  // 获取待审核任务
POST /api/v1/tasks/assistance/batch-approve  // 批量审核
```

### 1.2 前端API方法（已在AssistanceTaskReview.vue中使用）

```typescript
// frontend-new/src/api/client.ts 需要添加
async approveAssistanceTask(taskId: number, comment?: string) {
  const response = await apiClient.post(`/api/v1/tasks/assistance/${taskId}/approve`, { comment })
  return response.data
}

async rejectAssistanceTask(taskId: number, comment: string) {
  const response = await apiClient.put(`/api/v1/tasks/assistance/${taskId}/reject`, { comment })
  return response.data
}

async getPendingAssistanceTasks(params?: FilterParams) {
  const response = await apiClient.get('/api/v1/tasks/assistance/pending', { params })
  return response.data
}

async batchApproveAssistanceTasks(taskIds: number[], comment?: string) {
  const response = await apiClient.post('/api/v1/tasks/assistance/batch-approve', { task_ids: taskIds, comment })
  return response.data
}
```

## 2. 工时规则配置API（优先级：P1 - 近期实现）

**需求来源**: 需求2.2 - "超级管理员可在'系统设置'页面自定义所有工时和扣时规则的数值"

### 2.1 工时规则管理接口

```typescript
GET  /api/v1/system/work-rules        // 获取当前工时规则
PUT  /api/v1/system/work-rules        // 更新工时规则
POST /api/v1/system/work-rules/reset  // 重置为默认值
```

### 2.2 数据结构

```typescript
interface WorkRules {
  online_task_minutes: number                    // 线上任务工时（分钟/单）
  offline_task_minutes: number                   // 线下任务工时（分钟/单）  
  urgent_task_bonus_minutes: number              // 爆单任务加时（分钟/单）
  good_review_bonus_minutes: number              // 非默认好评加时（分钟/单）
  late_response_penalty_minutes: number          // 超时响应扣时（分钟/单）
  late_processing_penalty_minutes: number        // 超时处理扣时（分钟/人）
  bad_review_penalty_minutes: number             // 差评扣时（分钟/单）
  monthly_carry_over_threshold_hours: number     // 月度结转阈值（小时）
}
```

## 3. 考勤数据导出API（优先级：P1 - 近期实现）

**需求来源**: 需求2.5 - "支持将考勤数据导出为Excel文件"

### 3.1 数据导出接口

```typescript
POST /api/v1/attendance/export        // 导出考勤数据
GET  /api/v1/attendance/export/{task_id}/status  // 查询导出状态
GET  /api/v1/attendance/export/{task_id}/download // 下载导出文件
```

### 3.2 导出参数

```typescript
interface ExportRequest {
  month: string              // "YYYY-MM" 格式
  scope: 'all' | 'active' | 'group'  // 导出范围
  group_ids?: number[]       // 当scope='group'时指定分组ID
  include_summary?: boolean   // 是否包含汇总表
  include_repair_tasks?: boolean      // 是否包含报修单工作时长表
  include_assistance_tasks?: boolean  // 是否包含协助任务表  
  include_parameters?: boolean        // 是否包含参数信息表
}
```

### 3.3 Excel文件结构（严格按需求2.5）

**工作表1（汇总）**: 序号, 班级, 姓名, 上月结转时长, 报修单协助时长, 日常监控协助时长, 协助任务协助时长, 工作总时长, 签名

**工作表2（报修单工作时长-x月）**: 序号, 班级, 姓名, 报修单总数, 响应超时单数, 处理超时单数, 超时扣除时间数, 好评单数, 好评折算时间数, 汇总时间数, 签名

**工作表3（协助任务-x月）**: 序号, 班级, 姓名, 协助任务名称, 协助任务地点, 协助任务日期, 协助任务时间段, 协助任务小时数, 签名

**工作表4（导出信息）**: 包含所有可自定义的参数信息，如好评加多少、超时扣多少等

## 4. 线下单标记API（优先级：P2 - 计划实现）

**需求来源**: 需求2.3 - "学生网管可自主将本月报修单标记为线下单"

### 4.1 线下单标记接口

```typescript
PUT /api/v1/repair-orders/{order_id}/mark-offline
GET /api/v1/repair-orders/user-markable  // 获取用户可标记的本月报修单
```

### 4.2 标记数据结构

```typescript
interface OfflineMarkRequest {
  inspection_result: string     // 检修结果（必填）
  inspection_content: string    // 检修内容（必填）
  inspection_images: string[]   // 检修图片URL列表
}
```

## 5. 人员分组管理API（优先级：P2 - 计划实现）

**需求来源**: 需求2.4 - "支持分组功能，管理员可为人员进行分组"

### 5.1 分组管理接口

```typescript
GET  /api/v1/members/groups           // 获取分组列表
POST /api/v1/members/groups           // 创建分组
PUT  /api/v1/members/groups/{id}      // 更新分组
DELETE /api/v1/members/groups/{id}    // 删除分组
PUT  /api/v1/members/{id}/group       // 设置成员分组
```

## 6. 巡检任务API（优先级：P3 - 后续实现）

**需求来源**: 需求2.2 - "巡检时长：按巡检机柜数量计算"

### 6.1 巡检任务管理

```typescript
GET  /api/v1/inspection/tasks         // 获取巡检任务
POST /api/v1/inspection/tasks         // 创建巡检任务  
PUT  /api/v1/inspection/tasks/{id}    // 更新巡检任务
GET  /api/v1/inspection/cabinets      // 获取机柜列表
```

## 7. 数据匹配优化API（优先级：P3 - 后续实现）

**需求来源**: 需求2.3 - "系统以【报修人姓名 + 联系方式】为关键字段进行匹配"

### 7.1 数据匹配接口

```typescript
GET  /api/v1/data-import/unmatched    // 获取未匹配记录
POST /api/v1/data-import/match        // 手动匹配数据
POST /api/v1/data-import/rematch      // 重新执行匹配
```

## 8. 统计分析API（优先级：P3 - 后续实现）

**需求来源**: 需求2.6 - 报表统计与展示

### 8.1 统计报表接口

```typescript
GET /api/v1/statistics/repair-trends      // 报修单趋势
GET /api/v1/statistics/area-issues        // 区域问题统计  
GET /api/v1/statistics/problem-wordcloud  // 问题类型词云
GET /api/v1/statistics/member-rankings    // 个人工时排名
```

## 9. 系统监控API（优先级：P3 - 后续实现）

**需求来源**: 需求2.1 - "显示系统运行状态，如在线用户数等"

### 9.1 系统状态接口

```typescript
GET /api/v1/system/status              // 系统运行状态
GET /api/v1/system/online-users        // 在线用户统计
GET /api/v1/system/health              // 系统健康检查
```

---

## 实现时间线建议

**第1周（P0）**: 协助任务审核API - 解决前端AssistanceTaskReview.vue功能需求

**第2-3周（P1）**: 工时规则配置API + 考勤数据导出API - 完善Settings.vue功能

**第4-6周（P2）**: 线下单标记API + 人员分组管理API - 核心业务功能补充

**第7-12周（P3）**: 其他增强功能API - 提升用户体验和系统完整性

---

## 技术债务说明

1. **协助任务审核流程**：前端已实现完整界面，后端缺失审核状态管理和批量操作API
2. **工时规则动态配置**：前端Settings.vue已支持参数配置，后端需实现规则存储和应用逻辑  
3. **Excel导出格式标准化**：需严格按照需求文档的4个工作表结构实现
4. **数据权限控制**：各API需根据用户角色（学生网管/管理员/超级管理员）实现权限验证
- `GET /api/v1/tasks/assistance` ✅
- `GET /api/v1/tasks/assistance/list` ✅

## 📋 协助任务审核工作流

### 2. 协助任务审核API
**需求**: 学生网管登记的协助任务需经管理员审核通过后计入工时

```typescript
// ❌ 缺失 - 协助任务审核相关API
export const api = {
  // 获取待审核协助任务
  async getPendingAssistanceTasks(params?: {
    page?: number
    pageSize?: number
    status?: 'pending' | 'approved' | 'rejected'
  }) {
    const response = await apiClient.get<StandardResponse>('/api/v1/tasks/assistance/pending-review', { params })
    return response.data
  },

  // 审核协助任务
  async approveAssistanceTask(taskId: number, data: {
    action: 'approve' | 'reject'
    comment?: string
  }) {
    const response = await apiClient.post<StandardResponse>(`/api/v1/tasks/assistance/${taskId}/review`, data)
    return response.data
  },

  // 批量审核协助任务
  async batchApproveAssistanceTasks(taskIds: number[], action: 'approve' | 'reject') {
    const response = await apiClient.post<StandardResponse>('/api/v1/tasks/assistance/batch-review', {
      task_ids: taskIds,
      action
    })
    return response.data
  }
}
```

**后端API状态**: ❌ 需要实现
- `GET /api/v1/tasks/assistance/pending-review` ❌
- `POST /api/v1/tasks/assistance/{id}/review` ❌
- `POST /api/v1/tasks/assistance/batch-review` ❌

## 🔧 报修单任务增强功能

### 3. 线下单标记API
**需求**: 学生网管可自主将报修单标记为线下单，填写检修结果、内容和图片

```typescript
// ❌ 缺失 - 线下单标记API
export const api = {
  // 标记为线下单
  async markTaskAsOffline(taskId: number, data: {
    inspection_result: string      // 检修结果
    inspection_content: string     // 检修内容
    inspection_images?: File[]     // 检修图片
  }) {
    const formData = new FormData()
    formData.append('inspection_result', data.inspection_result)
    formData.append('inspection_content', data.inspection_content)
    
    if (data.inspection_images) {
      data.inspection_images.forEach((file, index) => {
        formData.append(`inspection_image_${index}`, file)
      })
    }

    const response = await apiClient.post<StandardResponse>(`/api/v1/tasks/repair/${taskId}/mark-offline`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
    return response.data
  },

  // 手动创建线下单
  async createOfflineTask(data: {
    title: string
    location: string
    inspection_result: string
    inspection_content: string
    inspection_images?: File[]
    work_date: string
  }) {
    const formData = new FormData()
    Object.keys(data).forEach(key => {
      if (key !== 'inspection_images' && data[key]) {
        formData.append(key, data[key])
      }
    })

    if (data.inspection_images) {
      data.inspection_images.forEach((file, index) => {
        formData.append(`inspection_image_${index}`, file)
      })
    }

    const response = await apiClient.post<StandardResponse>('/api/v1/tasks/repair/offline', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
    return response.data
  }
}
```

**后端API状态**: ❌ 需要实现
- `POST /api/v1/tasks/repair/{id}/mark-offline` ❌
- `POST /api/v1/tasks/repair/offline` ❌

### 4. 爆单任务标记API
**需求**: 报修单可标记为"爆单"，增加工时计算

```typescript
// ❌ 缺失 - 爆单标记API
export const api = {
  // 批量标记爆单任务
  async markRushTasks(data: {
    task_ids: number[]
    date_from: string
    date_to: string
    reason?: string
  }) {
    const response = await apiClient.post<StandardResponse>('/api/v1/tasks/repair/mark-rush', data)
    return response.data
  },

  // 获取爆单任务列表
  async getRushTasks(params?: {
    page?: number
    pageSize?: number
    date_from?: string
    date_to?: string
  }) {
    const response = await apiClient.get<StandardResponse>('/api/v1/tasks/repair/rush', { params })
    return response.data
  }
}
```

**后端API状态**: ✅ 已实现
- `POST /api/v1/tasks/mark-rush` ✅
- 但需要适配为 `/api/v1/tasks/repair/mark-rush`

## 📊 数据导出功能

### 5. 考勤数据导出API
**需求**: 4个工作表的Excel导出功能

```typescript
// ❌ 缺失 - 数据导出API
export const api = {
  // 导出考勤数据Excel
  async exportAttendanceData(params: {
    month: string        // 格式: YYYY-MM
    include_carryover?: boolean  // 是否包含结转时长
    member_ids?: number[]        // 指定成员，为空则全部
  }) {
    const response = await apiClient.post('/api/v1/attendance/export', params, {
      responseType: 'blob'
    })
    
    // 下载文件
    const blob = new Blob([response.data], { 
      type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' 
    })
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `考勤数据_${params.month}.xlsx`
    link.click()
    window.URL.revokeObjectURL(url)
  },

  // 获取导出预览数据
  async getExportPreview(params: {
    month: string
    member_ids?: number[]
  }) {
    const response = await apiClient.get<StandardResponse>('/api/v1/attendance/export-preview', { params })
    return response.data
  }
}
```

**后端API状态**: ❌ 需要实现
- `POST /api/v1/attendance/export` ❌
- `GET /api/v1/attendance/export-preview` ❌

## ⚙️ 系统设置API

### 6. 系统配置管理API
**需求**: 超级管理员可自定义工时规则参数

```typescript
// ❌ 缺失 - 系统配置API
export const api = {
  // 获取系统配置
  async getSystemConfig() {
    const response = await apiClient.get<StandardResponse>('/api/v1/system/config')
    return response.data
  },

  // 更新系统配置
  async updateSystemConfig(config: {
    online_task_minutes?: number         // 线上任务基础工时
    offline_task_minutes?: number        // 线下任务基础工时
    rush_bonus_minutes?: number          // 爆单加时
    positive_review_bonus_minutes?: number  // 好评加时
    negative_review_penalty_minutes?: number // 差评扣时
    response_timeout_hours?: number      // 响应超时阈值
    process_timeout_hours?: number       // 处理超时阈值
    timeout_penalty_minutes?: number    // 超时扣时
    monthly_carryover_hours?: number     // 月度结转阈值
  }) {
    const response = await apiClient.put<StandardResponse>('/api/v1/system/config', config)
    return response.data
  },

  // 重置为默认配置
  async resetSystemConfig() {
    const response = await apiClient.post<StandardResponse>('/api/v1/system/config/reset')
    return response.data
  }
}
```

**后端API状态**: ❌ 需要实现
- `GET /api/v1/system/config` ❌
- `PUT /api/v1/system/config` ❌
- `POST /api/v1/system/config/reset` ❌

## 📈 统计分析增强API

### 7. 报表统计API
**需求**: 趋势图表、区域统计、词云分析等

```typescript
// ❌ 缺失 - 统计分析API
export const api = {
  // 获取报修单趋势
  async getRepairTrends(params: {
    period: 'monthly' | 'weekly' | 'daily'
    start_date: string
    end_date: string
  }) {
    const response = await apiClient.get<StandardResponse>('/api/v1/statistics/repair-trends', { params })
    return response.data
  },

  // 获取区域问题统计
  async getLocationStats(params?: {
    start_date?: string
    end_date?: string
    top_n?: number  // 返回前N个问题区域
  }) {
    const response = await apiClient.get<StandardResponse>('/api/v1/statistics/location-stats', { params })
    return response.data
  },

  // 获取问题类型词云数据
  async getProblemWordCloud(params?: {
    start_date?: string
    end_date?: string
    max_words?: number
  }) {
    const response = await apiClient.get<StandardResponse>('/api/v1/statistics/problem-wordcloud', { params })
    return response.data
  },

  // 获取个人工时排名
  async getWorkHoursRanking(params: {
    month: string
    top_n?: number
  }) {
    const response = await apiClient.get<StandardResponse>('/api/v1/statistics/workhours-ranking', { params })
    return response.data
  }
}
```

**后端API状态**: ❌ 需要实现
- `GET /api/v1/statistics/repair-trends` ❌
- `GET /api/v1/statistics/location-stats` ❌
- `GET /api/v1/statistics/problem-wordcloud` ❌
- `GET /api/v1/statistics/workhours-ranking` ❌

## 👥 人员管理增强API

### 8. 人员分组管理API
**需求**: 支持人员分组功能，用于扣时规则计算

```typescript
// ❌ 缺失 - 人员分组API
export const api = {
  // 获取分组列表
  async getMemberGroups() {
    const response = await apiClient.get<StandardResponse>('/api/v1/members/groups')
    return response.data
  },

  // 创建分组
  async createMemberGroup(data: {
    name: string
    description?: string
    member_ids: number[]
  }) {
    const response = await apiClient.post<StandardResponse>('/api/v1/members/groups', data)
    return response.data
  },

  // 更新分组成员
  async updateGroupMembers(groupId: number, memberIds: number[]) {
    const response = await apiClient.put<StandardResponse>(`/api/v1/members/groups/${groupId}/members`, {
      member_ids: memberIds
    })
    return response.data
  },

  // 批量设置成员状态
  async batchUpdateMemberStatus(memberIds: number[], isActive: boolean) {
    const response = await apiClient.post<StandardResponse>('/api/v1/members/batch-status', {
      member_ids: memberIds,
      is_active: isActive
    })
    return response.data
  }
}
```

**后端API状态**: ❌ 需要实现
- `GET /api/v1/members/groups` ❌
- `POST /api/v1/members/groups` ❌
- `PUT /api/v1/members/groups/{id}/members` ❌
- `POST /api/v1/members/batch-status` ❌

## 🔍 数据导入增强API

### 9. A/B表匹配导入API
**需求**: 支持A表（报修单）和B表（维护记录）的匹配导入

```typescript
// ❌ 缺失 - A/B表导入API
export const api = {
  // 上传并验证A表数据
  async validateATableData(file: File) {
    const formData = new FormData()
    formData.append('file', file)
    
    const response = await apiClient.post<StandardResponse>('/api/v1/import/a-table/validate', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
    return response.data
  },

  // 上传并验证B表数据
  async validateBTableData(file: File) {
    const formData = new FormData()
    formData.append('file', file)
    
    const response = await apiClient.post<StandardResponse>('/api/v1/import/b-table/validate', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
    return response.data
  },

  // 执行A/B表匹配导入
  async importMatchedTables(data: {
    a_table_data: any[]
    b_table_data: any[]
    auto_match: boolean
    skip_unmatched: boolean
  }) {
    const response = await apiClient.post<StandardResponse>('/api/v1/import/ab-tables/match', data)
    return response.data
  },

  // 获取导入历史
  async getImportHistory(params?: {
    page?: number
    pageSize?: number
    import_type?: string
  }) {
    const response = await apiClient.get<StandardResponse>('/api/v1/import/history', { params })
    return response.data
  }
}
```

**后端API状态**: ✅ 部分已实现
- 导入功能存在，但需要适配前端调用方式
- `POST /api/v1/tasks/import-maintenance-orders` ✅

## 🎯 优先级和实施计划

### 🔥 P0 - 紧急修复（1天内）
1. **协助任务API断层修复** - 修复TaskCreate.vue调用错误
2. **基础API客户端方法** - createAssistanceTask, getAssistanceTasks

### ⚡ P1 - 核心功能（1周内）  
1. **协助任务审核工作流** - 审核界面和API
2. **线下单标记功能** - 图片上传和标记
3. **数据导出功能** - 4个工作表Excel导出

### 📊 P2 - 增强功能（2周内）
1. **系统配置管理** - 参数自定义界面
2. **统计分析增强** - 图表和排名功能
3. **人员分组管理** - 分组功能

### 🔧 P3 - 完善功能（3周内）
1. **A/B表导入优化** - 匹配预览和历史
2. **爆单任务管理** - 批量标记界面

## 📝 实施建议

1. **优先修复API断层** - 确保现有功能正常运行
2. **按需求优先级实施** - 核心考勤功能优先
3. **前后端并行开发** - 前端适配的同时后端补充API
4. **充分测试集成** - 确保API调用和数据格式匹配

---

**最后更新**: 2025-08-31  
**文档版本**: 1.0  
**状态**: 待实施
