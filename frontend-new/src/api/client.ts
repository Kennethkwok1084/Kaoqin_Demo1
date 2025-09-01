// API客户端配置
import axios, { type AxiosResponse } from 'axios'
import type { paths, components } from '@/types/api'

// 从生成的API类型中提取标准响应类型
type StandardResponse<T = any> = {
  success: boolean
  message: string
  data?: T
}

// 仪表板相关类型定义
export type DashboardOverview = {
  metrics: {
    totalTasks: number
    inProgress: number
    pending: number
    completedThisMonth: number
    systemStatus: string
  }
  trends: {
    totalTasksTrend: {
      value: number
      direction: 'up' | 'down' | 'stable'
    }
    inProgressTrend: {
      value: number
      direction: 'up' | 'down' | 'stable'
    }
    pendingTrend: {
      value: number
      direction: 'up' | 'down' | 'stable'
    }
    completedTrend: {
      value: number
      direction: 'up' | 'down' | 'stable'
    }
  }
  systemInfo: {
    onlineUsers: number
    lastDataSync: string
    systemUptime: string
  }
}

export type DashboardTask = {
  id: number
  title: string
  status: string
  priority: string
  location: string
  createdAt?: string
  dueDate?: string
}

export type DashboardTasksResponse = {
  tasks: DashboardTask[]
  summary: {
    totalAssigned: number
    pending: number
    inProgress: number
    completed: number
  }
}

export type DashboardActivity = {
  id: number
  type: string
  title: string
  description: string
  actorName: string
  actorId: string
  targetId?: number
  targetType?: string
  createdAt: string
  priority: string
}

export type DashboardActivitiesResponse = {
  activities: DashboardActivity[]
  summary: {
    total: number
    todayCount: number
  }
}

// 常用的数据类型 - 临时定义，后续可根据实际API响应优化
export type User = {
  id: number
  username: string
  name: string
  studentId: string
  role: components['schemas']['UserRole']
  department: string
  className: string
  phone?: string
  isActive: boolean
  permissions?: any
}

export type Task = {
  id: number
  title: string
  description: string
  location: string
  status: components['schemas']['TaskStatus']
  assigneeId?: number
  assigneeName?: string
  reporterName: string
  contactInfo: string
  createdAt: string
  startedAt?: string
  completedAt?: string
  dueDate?: string
  actualHours?: number
}

export type Member = {
  id: number
  username: string
  name: string
  studentId: string
  role: components['schemas']['UserRole']
  department: string
  className: string
  phone: string
  isActive: boolean
}

// 创建axios实例
const apiClient = axios.create({
  baseURL: 'http://localhost:8000',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// 请求拦截器 - 添加认证头
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('accessToken')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error)
)

// 响应拦截器 - 处理全局错误
apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const errorMessage = error.response?.data?.message || error.message || '未知错误'
    const errorStatus = error.response?.status || 'N/A'
    
    // 详细的错误日志
    console.error(`[API Error] Status: ${errorStatus}, Message: ${errorMessage}`, {
      url: error.config?.url,
      method: error.config?.method,
      data: error.config?.data
    })
    
    // 处理401错误 - token过期
    if (error.response?.status === 401) {
      // 清除token并跳转登录页
      tokenManager.clearTokens()
      if (window.location.pathname !== '/login') {
        window.location.href = '/login'
      }
    }
    
    // 处理429错误 - 限流
    if (error.response?.status === 429) {
      console.warn('请求频率过高，请稍后再试')
    }
    
    // 处理500错误 - 服务器错误
    if (error.response?.status >= 500) {
      console.error('服务器内部错误，请稍后重试')
    }
    
    return Promise.reject(error)
  }
)

export default apiClient

// 导出便捷的API方法
export const api = {
  // 认证相关
  async login(credentials: { studentId: string; password: string; rememberMe?: boolean }) {
    // 按照API文档，后端已统一使用camelCase，无需字段映射
    const requestData = {
      studentId: credentials.studentId,
      password: credentials.password,
      rememberMe: credentials.rememberMe
    }
    const response = await apiClient.post<StandardResponse>('/api/v1/auth/login', requestData)
    return response.data
  },

  async logout() {
    const response = await apiClient.post<StandardResponse>('/api/v1/auth/logout')
    return response.data
  },

  async getCurrentUser() {
    const response = await apiClient.get<StandardResponse>('/api/v1/auth/me')
    return response.data
  },

  async refreshToken(refreshToken: string) {
    const response = await apiClient.post<StandardResponse>('/api/v1/auth/refresh', { refreshToken })
    return response.data
  },

  async changePassword(data: { currentPassword: string; newPassword: string }) {
    const response = await apiClient.put<StandardResponse>('/api/v1/auth/change-password', {
      current_password: data.currentPassword,
      new_password: data.newPassword
    })
    return response.data
  },

  // 任务相关
  async getTasks(params?: {
    page?: number
    pageSize?: number
    search?: string
    taskStatus?: string
    type?: string
    assignedTo?: number
    sortBy?: string
    sortOrder?: 'asc' | 'desc'
  }) {
    const response = await apiClient.get<StandardResponse>('/api/v1/tasks', { params })
    return response.data
  },

  async getRepairTasks(params?: {
    page?: number
    pageSize?: number
    search?: string
    taskStatus?: string
    assignedTo?: number
  }) {
    const response = await apiClient.get<StandardResponse>('/api/v1/tasks/repair-list', { params })
    return response.data
  },

  async getRepairTask(taskId: number) {
    const response = await apiClient.get<StandardResponse>(`/api/v1/tasks/repair/${taskId}`)
    return response.data
  },

  async createTask(taskData: {
    title: string
    description: string
    location: string
    assignedTo?: number
    reporterName: string
    reporterContact: string
    tagIds?: number[]
  }) {
    const response = await apiClient.post<StandardResponse>('/api/v1/tasks/repair', taskData)
    return response.data
  },

  async updateRepairTask(taskId: number, taskData: any) {
    const response = await apiClient.put<StandardResponse>(`/api/v1/tasks/repair/${taskId}`, taskData)
    return response.data
  },

  async deleteRepairTask(taskId: number) {
    const response = await apiClient.delete<StandardResponse>(`/api/v1/tasks/repair/${taskId}`)
    return response.data
  },

  async startTask(taskId: number) {
    const response = await apiClient.post<StandardResponse>(`/api/v1/tasks/${taskId}/start`)
    return response.data
  },

  async completeTask(taskId: number, actualHours: number) {
    const response = await apiClient.post<StandardResponse>(`/api/v1/tasks/${taskId}/complete`, { actualHours })
    return response.data
  },

  async getTaskStats() {
    const response = await apiClient.get<StandardResponse>('/api/v1/tasks/stats')
    return response.data
  },

  // 仪表板相关API
  async getDashboardOverview() {
    const response = await apiClient.get<StandardResponse<DashboardOverview>>('/api/v1/dashboard/overview')
    return response.data
  },

  async getDashboardMyTasks(limit: number = 5) {
    const response = await apiClient.get<StandardResponse<DashboardTasksResponse>>('/api/v1/dashboard/my-tasks', {
      params: { limit }
    })
    return response.data
  },

  async getDashboardRecentActivities(limit: number = 10) {
    const response = await apiClient.get<StandardResponse<DashboardActivitiesResponse>>('/api/v1/dashboard/recent-activities', {
      params: { limit }
    })
    return response.data
  },

  // 成员相关
  async getMembers(params?: {
    page?: number
    pageSize?: number
    search?: string
    role?: string
    isActive?: boolean
    department?: string
    className?: string
  }) {
    const response = await apiClient.get<StandardResponse>('/api/v1/members', { params })
    return response.data
  },

  async createMember(memberData: {
    username: string
    name: string
    studentId: string
    password: string
    phone: string
    department: string
    className: string
    role: string
    isActive: boolean
    joinDate: string
  }) {
    const response = await apiClient.post<StandardResponse>('/api/v1/members', memberData)
    return response.data
  },

  async importMembers(membersData: {
    skipDuplicates: boolean
    members: any[]
  }) {
    const response = await apiClient.post<StandardResponse>('/api/v1/members/import', membersData)
    return response.data
  },

  // 工时记录相关
  async getWorkHoursRecords(params?: {
    memberId?: number
    dateFrom?: string
    dateTo?: string
    page?: number
    size?: number
  }) {
    const response = await apiClient.get<StandardResponse>('/api/v1/attendance/records', { params })
    return response.data
  },

  // 统计相关
  async getWorkHoursStats(params?: {
    dateFrom?: string
    dateTo?: string
    memberId?: number
  }) {
    const response = await apiClient.get<StandardResponse>('/api/v1/statistics/work-hours', { params })
    return response.data
  },

  async getTaskStatistics(params?: {
    period?: string
    dateRange?: string
  }) {
    const response = await apiClient.get<StandardResponse>('/api/v1/statistics/tasks', { params })
    return response.data
  },

  // 标签相关
  async getTags(params?: {
    isActive?: boolean
    tagType?: string
  }) {
    const response = await apiClient.get<StandardResponse>('/api/v1/tasks/tags', { params })
    return response.data
  },

  async createTag(tagData: {
    name: string
    description: string
    workMinutes: number
    isActive: boolean
    tagType: string
  }) {
    const response = await apiClient.post<StandardResponse>('/api/v1/tasks/tags', tagData)
    return response.data
  },

  // 协助任务相关API
  async createAssistanceTask(taskData: {
    title: string
    assistedDepartment: string
    assistedPerson?: string
    location: string
    assistanceDate: string
    startTime?: string
    endTime?: string
    workHours?: number
    description: string
    remarks?: string
    attachments: string[]
    status: string
  }) {
    const response = await apiClient.post<StandardResponse>('/api/v1/tasks/assistance', taskData)
    return response.data
  },

  // 保存协助任务草稿
  async saveAssistanceTaskDraft(draftData: any) {
    const response = await apiClient.post<StandardResponse>('/api/v1/tasks/assistance/draft', draftData)
    return response.data
  },

  // 获取我的协助任务统计
  async getMyAssistanceTasksStats() {
    const response = await apiClient.get<StandardResponse>('/api/v1/tasks/assistance/my-stats')
    return response.data
  },

  async getAssistanceTasks(params?: {
    page?: number
    pageSize?: number
    memberId?: number
    dateFrom?: string
    dateTo?: string
  }) {
    // Convert camelCase to snake_case for backend
    const backendParams = {
      page: params?.page,
      pageSize: params?.pageSize,
      member_id: params?.memberId,
      date_from: params?.dateFrom,
      date_to: params?.dateTo
    }
    const response = await apiClient.get<StandardResponse>('/api/v1/tasks/assistance', { params: backendParams })
    return response.data
  },

  async getAssistanceTaskStats(params?: {
    memberId?: number
    dateFrom?: string
    dateTo?: string
  }) {
    // Convert camelCase to snake_case for backend
    const backendParams = {
      member_id: params?.memberId,
      date_from: params?.dateFrom,
      date_to: params?.dateTo
    }
    const response = await apiClient.get<StandardResponse>('/api/v1/tasks/assistance/stats', { params: backendParams })
    return response.data
  },

  // 协助任务审核API (待后端实现)
  async getPendingAssistanceTasks(params?: {
    page?: number
    pageSize?: number
    status?: string
    date_from?: string
    date_to?: string
  }) {
    // 暂时使用现有的getAssistanceTasks API
    return await this.getAssistanceTasks(params)
  },

  async approveAssistanceTask(taskId: number, data: {
    action: 'approve' | 'reject'
    comment?: string
  }) {
    const response = await apiClient.post<StandardResponse>(`/api/v1/tasks/assistance/${taskId}/review`, data)
    return response.data
  },

  async batchApproveAssistanceTasks(taskIds: number[], action: 'approve' | 'reject') {
    const response = await apiClient.post<StandardResponse>('/api/v1/tasks/assistance/batch-review', {
      task_ids: taskIds,
      action
    })
    return response.data
  },

  // 线下单标记API 
  async markTaskAsOffline(data: {
    taskId: number
    repairResult: string
    repairContent: string
    repairImages: string[]
    estimatedDuration: number
    remarks?: string
    isOffline: boolean
  }) {
    const response = await apiClient.post<StandardResponse>(`/api/v1/tasks/${data.taskId}/mark-offline`, {
      repairResult: data.repairResult,
      repairContent: data.repairContent,
      repairImages: data.repairImages,
      estimatedDuration: data.estimatedDuration,
      remarks: data.remarks,
      isOffline: data.isOffline
    })
    return response.data
  },

  // 报修单AB表导入API
  async importRepairTasks(data: {
    tasks: any[]
    options: {
      overwrite: boolean
      skipDuplicates: boolean
      autoAssign: boolean
    }
  }) {
    const response = await apiClient.post<StandardResponse>('/api/v1/tasks/import-repair-data', data)
    return response.data
  },

  // 数据导出API
  async exportAttendanceData(params: {
    month: string        // 格式: YYYY-MM
    includeCarryover?: boolean
    memberIds?: number[]
  }) {
    // Convert camelCase to snake_case for backend
    const backendParams = {
      month: params.month,
      include_carryover: params.includeCarryover,
      member_ids: params.memberIds
    }
    
    const response = await apiClient.post('/api/v1/attendance/export', backendParams, {
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

  // 系统设置API
  async getSystemSettings() {
    const response = await apiClient.get<StandardResponse>('/api/v1/system/settings')
    return response.data
  },

  async updateSystemSettings(settings: {
    workHourRules: any
    attendanceRules: any
    notificationSettings: any
  }) {
    const response = await apiClient.put<StandardResponse>('/api/v1/system/settings', settings)
    return response.data
  },

  async getSettingsModifyHistory() {
    const response = await apiClient.get<StandardResponse>('/api/v1/system/settings/history')
    return response.data
  },

  // 权限管理API
  async getRoles() {
    const response = await apiClient.get<StandardResponse>('/api/v1/roles')
    return response.data
  },

  async createRole(roleData: {
    name: string
    description: string
    level: number
    permissions: string[]
  }) {
    const response = await apiClient.post<StandardResponse>('/api/v1/roles', roleData)
    return response.data
  },

  async updateRole(roleId: number, roleData: {
    name: string
    description: string
    level: number
    permissions: string[]
  }) {
    const response = await apiClient.put<StandardResponse>(`/api/v1/roles/${roleId}`, roleData)
    return response.data
  },

  async deleteRole(roleId: number) {
    const response = await apiClient.delete<StandardResponse>(`/api/v1/roles/${roleId}`)
    return response.data
  },

  async updateRolePermissions(roleId: number, data: { permissions: string[] }) {
    const response = await apiClient.put<StandardResponse>(`/api/v1/roles/${roleId}/permissions`, data)
    return response.data
  },

  async getPermissions() {
    const response = await apiClient.get<StandardResponse>('/api/v1/permissions')
    return response.data
  }
}

// 错误处理工具
export class ApiError extends Error {
  constructor(
    message: string,
    public status?: number,
    public code?: string,
    public details?: any
  ) {
    super(message)
    this.name = 'ApiError'
  }
}

// Token管理工具
export const tokenManager = {
  getAccessToken(): string | null {
    return localStorage.getItem('accessToken')
  },

  getRefreshToken(): string | null {
    return localStorage.getItem('refreshToken')
  },

  setTokens(accessToken: string, refreshToken: string) {
    localStorage.setItem('accessToken', accessToken)
    localStorage.setItem('refreshToken', refreshToken)
  },

  clearTokens() {
    localStorage.removeItem('accessToken')
    localStorage.removeItem('refreshToken')
  },

  async refreshTokenIfNeeded() {
    const refreshToken = this.getRefreshToken()
    if (!refreshToken) return false

    try {
      const response = await api.refreshToken(refreshToken)
      if (response.success && response.data) {
        this.setTokens(response.data.accessToken, refreshToken)
        return true
      }
    } catch (error) {
      console.error('Token refresh failed:', error)
      this.clearTokens()
    }
    return false
  }
}