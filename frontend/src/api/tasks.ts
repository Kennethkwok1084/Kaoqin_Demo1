import { http } from './client'
import type { 
  Task,
  CreateTaskRequest,
  UpdateTaskRequest,
  TaskListParams,
  TaskListResponse,
  TaskStats,
  TaskWorkLog,
  TaskComment,
  TaskEvaluation
} from '@/types/task'

/**
 * 任务管理相关API
 */
export const tasksApi = {
  /**
   * 获取任务列表
   */
  async getTasks(params?: TaskListParams): Promise<TaskListResponse> {
    // 将复杂的 filters 参数转换为简单的查询参数
    const queryParams: Record<string, any> = {
      page: params?.page || 1,
      pageSize: params?.pageSize || 20,
      sortBy: params?.sortBy || 'createdAt',
      sortOrder: params?.sortOrder || 'desc'
    }
    
    // 处理筛选条件
    if (params?.filters) {
      if (params.filters.search) {
        queryParams.search = params.filters.search
      }
      if (params.filters.type && params.filters.type.length > 0) {
        queryParams.type = params.filters.type[0] // 取第一个类型
      }
      if (params.filters.status && params.filters.status.length > 0) {
        queryParams.task_status = params.filters.status[0] // 取第一个状态
      }
      if (params.filters.assigneeId) {
        queryParams.assigned_to = params.filters.assigneeId
      }
    }
    
    const response = await http.get('/tasks', { params: queryParams })
    return response.data.data || { items: [], total: 0, page: 1, pageSize: 20 }
  },

  /**
   * 获取任务详情
   */
  async getTask(id: number): Promise<Task> {
    const response = await http.get(`/tasks/${id}`)
    return response.data.data
  },

  /**
   * 创建任务
   */
  async createTask(data: CreateTaskRequest): Promise<Task> {
    const formData = new FormData()
    
    // 处理文件上传
    if (data.attachments) {
      data.attachments.forEach((file, index) => {
        formData.append(`attachments[${index}]`, file)
      })
      delete data.attachments
    }
    
    Object.entries(data).forEach(([key, value]) => {
      if (value !== undefined && value !== null) {
        if (Array.isArray(value)) {
          formData.append(key, JSON.stringify(value))
        } else {
          formData.append(key, value.toString())
        }
      }
    })

    const response = await http.post<Task>('/tasks', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
    return response.data
  },

  /**
   * 更新任务
   */
  async updateTask(id: number, data: UpdateTaskRequest): Promise<Task> {
    const response = await http.put<Task>(`/tasks/${id}`, data)
    return response.data
  },

  /**
   * 删除任务
   */
  async deleteTask(id: number): Promise<void> {
    await http.delete(`/tasks/${id}`)
  },

  /**
   * 批量删除任务
   */
  async batchDeleteTasks(ids: number[]): Promise<void> {
    await http.post('/tasks/batch-delete', { ids })
  },

  /**
   * 分配任务
   */
  async assignTask(id: number, assigneeId: number): Promise<Task> {
    const response = await http.post<Task>(`/tasks/${id}/assign`, { assigneeId })
    return response.data
  },

  /**
   * 开始任务
   */
  async startTask(id: number): Promise<Task> {
    const response = await http.post<Task>(`/tasks/${id}/start`)
    return response.data
  },

  /**
   * 完成任务
   */
  async completeTask(id: number, actualHours?: number): Promise<Task> {
    const response = await http.post<Task>(`/tasks/${id}/complete`, { actualHours })
    return response.data
  },

  /**
   * 取消任务
   */
  async cancelTask(id: number, reason: string): Promise<Task> {
    const response = await http.post<Task>(`/tasks/${id}/cancel`, { reason })
    return response.data
  },

  /**
   * 重新打开任务
   */
  async reopenTask(id: number, reason: string): Promise<Task> {
    const response = await http.post<Task>(`/tasks/${id}/reopen`, { reason })
    return response.data
  },

  /**
   * 获取任务统计
   */
  async getTaskStats(filters?: any): Promise<TaskStats> {
    const response = await http.get('/tasks/stats', { params: filters })
    return response.data.data || {}
  },

  /**
   * 获取我的任务
   */
  async getMyTasks(params?: TaskListParams): Promise<TaskListResponse> {
    const response = await http.get('/tasks/my', { params })
    return response.data.data || { items: [], total: 0, page: 1, pageSize: 20 }
  },

  /**
   * 获取我创建的任务
   */
  async getCreatedTasks(params?: TaskListParams): Promise<TaskListResponse> {
    const response = await http.get('/tasks/created', { params })
    return response.data.data || { items: [], total: 0, page: 1, pageSize: 20 }
  },

  /**
   * 添加任务评论
   */
  async addComment(taskId: number, content: string): Promise<TaskComment> {
    const response = await http.post<TaskComment>(`/tasks/${taskId}/comments`, { content })
    return response.data
  },

  /**
   * 删除任务评论
   */
  async deleteComment(taskId: number, commentId: number): Promise<void> {
    await http.delete(`/tasks/${taskId}/comments/${commentId}`)
  },

  /**
   * 获取任务评论列表
   */
  async getComments(taskId: number): Promise<TaskComment[]> {
    const response = await http.get<TaskComment[]>(`/tasks/${taskId}/comments`)
    return response.data
  },

  /**
   * 评价任务
   */
  async evaluateTask(taskId: number, rating: number, comment: string): Promise<TaskEvaluation> {
    const response = await http.post<TaskEvaluation>(`/tasks/${taskId}/evaluate`, { rating, comment })
    return response.data
  },

  /**
   * 获取任务工时记录
   */
  async getWorkLogs(taskId: number): Promise<TaskWorkLog[]> {
    const response = await http.get<TaskWorkLog[]>(`/tasks/${taskId}/work-logs`)
    return response.data
  },

  /**
   * 添加工时记录
   */
  async addWorkLog(taskId: number, description: string, hours: number): Promise<TaskWorkLog> {
    const response = await http.post<TaskWorkLog>(`/tasks/${taskId}/work-logs`, { description, hours })
    return response.data
  },

  /**
   * 删除工时记录
   */
  async deleteWorkLog(taskId: number, logId: number): Promise<void> {
    await http.delete(`/tasks/${taskId}/work-logs/${logId}`)
  },

  /**
   * 上传任务附件
   */
  async uploadAttachment(taskId: number, file: File): Promise<{ id: number, fileName: string, fileUrl: string }> {
    const formData = new FormData()
    formData.append('file', file)
    
    const response = await http.post(`/tasks/${taskId}/attachments`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
    return response.data
  },

  /**
   * 删除任务附件
   */
  async deleteAttachment(taskId: number, attachmentId: number): Promise<void> {
    await http.delete(`/tasks/${taskId}/attachments/${attachmentId}`)
  },

  /**
   * 下载任务附件
   */
  async downloadAttachment(taskId: number, attachmentId: number, fileName: string): Promise<void> {
    await http.download(`/tasks/${taskId}/attachments/${attachmentId}/download`, fileName)
  },

  /**
   * 导出任务列表
   */
  async exportTasks(filters?: any, format: 'excel' | 'csv' = 'excel'): Promise<void> {
    await http.download('/tasks/export', `tasks_export.${format}`, { params: { ...filters, format } })
  },

  /**
   * 批量导入任务
   */
  async importTasks(file: File): Promise<{ success: number, failed: number, errors: string[] }> {
    const formData = new FormData()
    formData.append('file', file)
    
    const response = await http.post('/tasks/import', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
    return response.data.data || { success: 0, failed: 0, errors: [] }
  },

  /**
   * 导入维护工单（A-B表匹配）
   */
  async importMaintenanceOrders(data: {
    matched_data: any[],
    import_type: 'ab_matched' | 'online_only' | 'a_table' | 'b_table',
    auto_match?: boolean
  }): Promise<{ success: number, failed: number, matched: number, partial: number, errors: string[] }> {
    // 转换数据格式以匹配后端期望
    const backendData = {
      maintenance_orders: data.matched_data,
      auto_match: data.auto_match !== false,
      import_type: data.import_type
    }
    const response = await http.post('/tasks/maintenance-orders/import', backendData)
    return response.data.data || { success: 0, failed: 0, matched: 0, partial: 0, errors: [] }
  },

  /**
   * 获取任务标签列表
   */
  async getTags(): Promise<string[]> {
    const response = await http.get<string[]>('/tasks/tags')
    return response.data
  },

  /**
   * 搜索任务
   */
  async searchTasks(query: string, filters?: any): Promise<Task[]> {
    const response = await http.get<Task[]>('/tasks/search', { 
      params: { q: query, ...filters } 
    })
    return response.data
  },

  /**
   * 获取任务历史记录
   */
  async getTaskHistory(taskId: number): Promise<any[]> {
    const response = await http.get<any[]>(`/tasks/${taskId}/history`)
    return response.data
  },

  /**
   * 获取维护工单导入模板
   */
  async downloadMaintenanceTemplate(type: 'a-table' | 'b-table'): Promise<void> {
    await http.download(`/tasks/maintenance-orders/template/${type}`, `${type === 'a-table' ? 'A表' : 'B表'}_维护工单模板.xlsx`)
  },

  /**
   * 验证维护工单数据
   */
  async validateMaintenanceData(data: any[], type: 'a-table' | 'b-table'): Promise<{ valid: boolean, errors: string[] }> {
    const response = await http.post('/tasks/maintenance-orders/validate', { data, type })
    return response.data.data || { valid: false, errors: [] }
  }
}