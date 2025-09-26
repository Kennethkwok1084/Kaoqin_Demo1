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
    const typeFromFilters =
      params?.filters?.type?.[0] ||
      (Array.isArray(params?.task_type) ? params?.task_type[0] : params?.task_type) ||
      'repair'

    const endpointMap: Record<string, string> = {
      repair: '/tasks/fixes',
      monitoring: '/tasks/monitoring',
      assistance: '/tasks/assistance'
    }

    const endpoint = endpointMap[typeFromFilters] || endpointMap.repair

    const queryParams: Record<string, any> = {
      page: params?.page || 1,
      pageSize: params?.pageSize || 20,
      sortBy: params?.sortBy || 'createdAt',
      sortOrder: params?.sortOrder || 'desc'
    }
    queryParams.size = queryParams.pageSize

    if (params?.filters) {
      if (params.filters.search) {
        queryParams.search = params.filters.search
      }
      if (params.filters.status && params.filters.status.length > 0) {
        queryParams.status = params.filters.status[0]
        queryParams.task_status = params.filters.status[0]
      }
      if (params.filters.assigneeId) {
        queryParams.assigned_to = params.filters.assigneeId
      }
      if (params.filters.priority && params.filters.priority.length > 0) {
        queryParams.priority = params.filters.priority[0]
      }
      if (params.filters.dateRange && params.filters.dateRange.length === 2) {
        queryParams.start_date = params.filters.dateRange[0]
        queryParams.end_date = params.filters.dateRange[1]
      }
    }

    const response = await http.get(endpoint, { params: queryParams })
    return response.data.data || { items: [], total: 0, page: 1, pageSize: 20 }
  },

  /**
   * 获取任务详情
   */
  async getTask(id: number, options?: { type?: string }): Promise<Task> {
    const taskType = options?.type || 'repair'

    let endpoint = `/tasks/repair/${id}`
    if (taskType === 'assistance') {
      endpoint = `/tasks/assistance/${id}`
    }

    console.log('🌐 [TasksAPI] 调用任务详情接口', {
      id,
      taskType,
      endpoint,
      options
    })

    const response = await http.get(endpoint)

    console.log('📡 [TasksAPI] 任务详情API响应:', {
      status: response.status,
      data: response.data
    })

    return response.data.data
  },

  /**
   * 获取任务详情 (别名方法，用于测试兼容性)
   */
  async getTaskDetail(id: number, options?: { type?: string }): Promise<Task> {
    return this.getTask(id, options)
  },

  /**
   * 创建任务
   */
  async createTask(data: CreateTaskRequest): Promise<Task> {
    const taskType = (data as any).type || (data as any).task_type || 'repair'
    let endpoint = '/tasks/repair'

    if (taskType === 'assistance') {
      endpoint = '/tasks/assistance'
    } else if (taskType === 'monitoring') {
      endpoint = '/tasks/monitoring'
    }

    const taskTypeMap: Record<string, string> = {
      repair: 'repair',
      assistance: 'assistance',
      monitoring: 'offline',
      online: 'online',
      offline: 'offline',
      maintenance: 'offline',
      inspection: 'offline',
      other: 'offline'
    }

    const normalizedTaskType = taskTypeMap[taskType] || 'repair'

    const payload: Record<string, any> = {
      title: (data as any).title,
      description: (data as any).description,
      task_type: normalizedTaskType,
      priority: (data as any).priority || 'medium',
      location: (data as any).location,
      assigned_to:
        (data as any).assigneeId ?? (data as any).assignee_id ?? (data as any).assigned_to,
      reporter_name:
        (data as any).reporter_name ?? (data as any).contactInfo ?? '',
      reporter_contact:
        (data as any).contactInfo ?? (data as any).contact_info ?? '',
      tag_ids: ((data as any).tags ?? (data as any).tag_ids ?? []).map((tag: any) =>
        Number.isNaN(Number(tag)) ? undefined : Number(tag)
      ),
      is_rush: Boolean((data as any).is_rush)
    }

    payload.tag_ids = payload.tag_ids.filter((tag: any) => typeof tag === 'number')
    if (!payload.tag_ids.length) {
      delete payload.tag_ids
    }

    const deadlineValue = (data as any).dueDate || (data as any).deadline
    if (deadlineValue) {
      const deadlineDate = new Date(deadlineValue)
      if (!Number.isNaN(deadlineDate.getTime())) {
        payload.deadline = deadlineDate.toISOString()
      }
    }

    const estimatedMinutes =
      typeof (data as any).estimatedHours === 'number'
        ? Math.round((data as any).estimatedHours * 60)
        : (data as any).estimated_minutes

    if (
      typeof estimatedMinutes === 'number' &&
      estimatedMinutes >= 1 &&
      estimatedMinutes <= 999
    ) {
      payload.estimated_minutes = estimatedMinutes
    }

    // 移除undefined字段，避免422
    Object.keys(payload).forEach(key => {
      if (payload[key] === undefined || payload[key] === null || payload[key] === '') {
        delete payload[key]
      }
    })

    if (import.meta.env.DEV) {
      console.debug('[tasksApi] createTask payload', payload)
    }

    const response = await http.post<{
      success: boolean
      message: string
      data: Task
    }>(endpoint, payload)

    return response.data.data || (response.data as any)
  },

  /**
   * 更新任务
   */
  async updateTask(id: number, data: UpdateTaskRequest): Promise<Task> {
    const response = await http.put<{
      success: boolean
      message: string
      data: Task
    }>(`/tasks/repair/${id}`, data)
    return response.data.data || (response.data as any)
  },

  /**
   * 删除任务
   */
  async deleteTask(id: number): Promise<void> {
    await http.delete(`/tasks/repair/${id}`)
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
    const response = await http.put<{
      success: boolean
      message: string
      data: Task
    }>(`/tasks/repair/${id}/assign`, {
      member_id: assigneeId
    })
    return response.data.data || (response.data as any)
  },

  /**
   * 开始任务
   */
  async startTask(id: number): Promise<Task> {
    const response = await http.post<{
      success: boolean
      message: string
      data: Task
    }>(`/tasks/${id}/start`)
    return response.data.data || (response.data as any)
  },

  /**
   * 完成任务
   */
  async completeTask(id: number, actualHours?: number): Promise<Task> {
    const response = await http.post<{
      success: boolean
      message: string
      data: Task
    }>(`/tasks/${id}/complete`, {
      actualHours
    })
    return response.data.data || (response.data as any)
  },

  /**
   * 取消任务
   */
  async cancelTask(id: number, reason: string): Promise<Task> {
    const response = await http.post<{
      success: boolean
      message: string
      data: Task
    }>(`/tasks/${id}/cancel`, { reason })
    return response.data.data || (response.data as any)
  },

  /**
   * 重新打开任务
   */
  async reopenTask(id: number, reason: string): Promise<Task> {
    const response = await http.post<{
      success: boolean
      message: string
      data: Task
    }>(`/tasks/${id}/reopen`, { reason })
    return response.data.data || (response.data as any)
  },

  /**
   * 获取任务统计
   */
  async getTaskStats(filters?: any): Promise<TaskStats> {
    const queryParams: Record<string, any> = {}

    if (filters?.type && filters.type.length > 0) {
      queryParams.task_type = filters.type[0]
    }

    const response = await http.get('/tasks/stats', { params: queryParams })
    const data = response.data.data || {}
    const overview = data.overview || {}

    const toNumber = (value: unknown): number => {
      if (value === null || value === undefined) return 0
      const numeric = Number(value)
      return Number.isFinite(numeric) ? numeric : 0
    }

    const normalized = {
      total: toNumber(overview.total ?? data.total),
      pending: toNumber(overview.pending ?? data.pending),
      in_progress: toNumber(
        overview.in_progress ??
          overview.inProgress ??
          data.in_progress ??
          data.inProgress
      ),
      completed: toNumber(overview.completed ?? data.completed),
      cancelled: toNumber(overview.cancelled ?? data.cancelled),
      overdue: toNumber(overview.overdue ?? data.overdue),
      total_work_hours: toNumber(
        overview.total_work_hours ??
          overview.totalWorkHours ??
          data.total_work_hours ??
          data.totalWorkHours
      ),
      avg_work_hours: toNumber(
        overview.avg_work_hours ??
          overview.avgWorkHours ??
          data.avg_work_hours ??
          data.avgWorkHours
      ),
      inProgress: 0
    } satisfies TaskStats & {
      overview?: typeof overview
      today?: Record<string, number>
      personal?: Record<string, number>
      completion_rate?: number
    }

    normalized.inProgress = normalized.in_progress
    normalized.overview = overview
    normalized.today = (data.today || {}) as Record<string, number>
    normalized.personal = (data.personal || {}) as Record<string, number>
    normalized.completion_rate = toNumber(
      data.completion_rate ?? data.completionRate
    )

    return normalized
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
    try {
      const response = await http.post<{
        success: boolean
        message: string
        data: TaskComment
      }>(`/tasks/${taskId}/comments`, {
        content
      })
      return response.data.data || (response.data as any)
    } catch (error) {
      console.warn('Add comment API not implemented')
      throw new Error('添加评论功能暂未实现')
    }
  },

  /**
   * 删除任务评论
   */
  async deleteComment(taskId: number, commentId: number): Promise<void> {
    try {
      await http.delete(`/tasks/${taskId}/comments/${commentId}`)
    } catch (error) {
      console.warn('Delete comment API not implemented')
      throw new Error('删除评论功能暂未实现')
    }
  },

  /**
   * 获取任务评论列表
   */
  async getComments(taskId: number): Promise<TaskComment[]> {
    // API暂未实现，直接返回空数组
    console.warn('Comments API not implemented, returning empty array')
    return []
  },

  /**
   * 评价任务
   */
  async evaluateTask(
    taskId: number,
    rating: number,
    comment: string
  ): Promise<TaskEvaluation> {
    const response = await http.post<{
      success: boolean
      message: string
      data: TaskEvaluation
    }>(`/tasks/${taskId}/evaluate`, { rating, comment })
    return response.data.data || (response.data as any)
  },

  /**
   * 获取任务工时记录
   */
  async getWorkLogs(taskId: number): Promise<TaskWorkLog[]> {
    // API暂未实现，直接返回空数组
    console.warn('Work logs API not implemented, returning empty array')
    return []
  },

  /**
   * 添加工时记录
   */
  async addWorkLog(
    taskId: number,
    description: string,
    hours: number
  ): Promise<TaskWorkLog> {
    try {
      const response = await http.post<{
        success: boolean
        message: string
        data: TaskWorkLog
      }>(`/tasks/${taskId}/work-logs`, { description, hours })
      return response.data.data || (response.data as any)
    } catch (error) {
      console.warn('Add work log API not implemented')
      throw new Error('添加工时记录功能暂未实现')
    }
  },

  /**
   * 删除工时记录
   */
  async deleteWorkLog(taskId: number, logId: number): Promise<void> {
    try {
      await http.delete(`/tasks/${taskId}/work-logs/${logId}`)
    } catch (error) {
      console.warn('Delete work log API not implemented')
      throw new Error('删除工时记录功能暂未实现')
    }
  },

  /**
   * 上传任务附件
   */
  async uploadAttachment(
    taskId: number,
    file: File
  ): Promise<{ id: number; fileName: string; fileUrl: string }> {
    try {
      const formData = new FormData()
      formData.append('file', file)

      const response = await http.post<{
        success: boolean
        message: string
        data: { id: number; fileName: string; fileUrl: string }
      }>(`/tasks/${taskId}/attachments`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      })
      return response.data.data || (response.data as any)
    } catch (error) {
      console.warn('Upload attachment API not implemented')
      throw new Error('上传附件功能暂未实现')
    }
  },

  /**
   * 删除任务附件
   */
  async deleteAttachment(taskId: number, attachmentId: number): Promise<void> {
    try {
      await http.delete(`/tasks/${taskId}/attachments/${attachmentId}`)
    } catch (error) {
      console.warn('Delete attachment API not implemented')
      throw new Error('删除附件功能暂未实现')
    }
  },

  /**
   * 下载任务附件
   */
  async downloadAttachment(
    taskId: number,
    attachmentId: number,
    fileName: string
  ): Promise<void> {
    try {
      await (http as any).download(
        `/tasks/${taskId}/attachments/${attachmentId}/download`,
        fileName
      )
    } catch (error) {
      console.warn('Download attachment API not implemented')
      throw new Error('下载附件功能暂未实现')
    }
  },

  /**
   * 导出任务列表
   */
  async exportTasks(
    filters?: any,
    format: 'excel' | 'csv' = 'excel'
  ): Promise<void> {
    await (http as any).download('/tasks/export', `tasks_export.${format}`, {
      params: { ...filters, format }
    })
  },

  /**
   * 批量导入任务
   */
  async importTasks(
    file: File
  ): Promise<{ success: number; failed: number; errors: string[] }> {
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
    matched_data: any[]
    import_type: 'ab_matched' | 'online_only' | 'a_table' | 'b_table'
    auto_match?: boolean
  }): Promise<{
    success: number
    failed: number
    matched: number
    partial: number
    errors: string[]
  }> {
    // 转换数据格式以匹配后端期望
    const backendData = {
      maintenance_orders: data.matched_data,
      auto_match: data.auto_match !== false,
      import_type: data.import_type
    }
    const response = await http.post(
      '/tasks/maintenance-orders/import',
      backendData
    )
    return (
      response.data.data || {
        success: 0,
        failed: 0,
        matched: 0,
        partial: 0,
        errors: []
      }
    )
  },

  /**
   * 获取任务标签列表
   */
  async getTags(): Promise<string[]> {
    const response = await http.get<{
      success: boolean
      message: string
      data: string[]
    }>('/tasks/tags')
    return response.data.data || (response.data as any) || []
  },

  /**
   * 搜索任务
   */
  async searchTasks(query: string, filters?: any): Promise<Task[]> {
    const response = await http.get<{
      success: boolean
      message: string
      data: Task[]
    }>('/tasks/search', {
      params: { q: query, ...filters }
    })
    return response.data.data || (response.data as any) || []
  },

  /**
   * 获取任务历史记录
   */
  async getTaskHistory(taskId: number): Promise<any[]> {
    const response = await http.get<{
      success: boolean
      message: string
      data: any[]
    }>(`/tasks/${taskId}/history`)
    return response.data.data || (response.data as any) || []
  },

  /**
   * 获取维护工单导入模板
   */
  async downloadMaintenanceTemplate(
    type: 'a-table' | 'b-table'
  ): Promise<void> {
    await (http as any).download(
      `/tasks/maintenance-orders/template/${type}`,
      `${type === 'a-table' ? 'A表' : 'B表'}_维护工单模板.xlsx`
    )
  },

  /**
   * 验证维护工单数据
   */
  async validateMaintenanceData(
    data: any[],
    type: 'a-table' | 'b-table'
  ): Promise<{ valid: boolean; errors: string[] }> {
    const response = await http.post<{
      success: boolean
      message: string
      data: { valid: boolean; errors: string[] }
    }>('/tasks/maintenance-orders/validate', {
      data,
      type
    })
    return response.data.data || { valid: false, errors: [] }
  },

  /**
   * 获取工时详情（别名方法）
   */
  async getWorkTimeDetail(taskId: number): Promise<TaskWorkLog[]> {
    return this.getWorkLogs(taskId)
  },

  /**
   * 导入协助任务
   */
  async importAssistanceTasks(tasks: any[]): Promise<{
    success_count: number
    failed_count: number
    total_count: number
    errors: any[]
  }> {
    try {
      const response = await http.post('/tasks/assistance/import', {
        assistance_tasks: tasks
      })
      return response.data.data || {
        success_count: tasks.length,
        failed_count: 0,
        total_count: tasks.length,
        errors: []
      }
    } catch (error) {
      console.error('Import assistance tasks failed:', error)
      throw new Error('导入协助任务失败')
    }
  }
}

// Export individual functions for test compatibility and easier imports
export const getTasks = tasksApi.getTasks
export const getTask = tasksApi.getTask
export const getTaskDetail = tasksApi.getTaskDetail // Direct method for compatibility
export const createTask = tasksApi.createTask
export const updateTask = tasksApi.updateTask
export const deleteTask = tasksApi.deleteTask
export const getTaskStats = tasksApi.getTaskStats
export const getWorkTimeDetail = async (taskId: number) => {
  return await tasksApi.getWorkLogs(taskId)
}

// Also add the method directly to tasksApi
const originalTasksApi = tasksApi
export const tasksApiWithWorkTime = {
  ...originalTasksApi,
  getWorkTimeDetail: getWorkTimeDetail
}
