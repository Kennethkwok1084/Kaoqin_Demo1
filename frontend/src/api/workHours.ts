import { http } from '@/api/http'
import type {
  WorkHour,
  WorkHourAdjustment,
  WorkHourStatistics,
  WorkHourFilters,
  WorkHourRule,
  WorkHourCalculationRequest,
  WorkHourCalculationResult,
  WorkHourReview,
  PaginatedWorkHours,
  WorkHourSummary,
  MemberWorkHourSummary,
  WorkHourTrend,
  WorkHourExportConfig
} from '@/types/workHours'

export const workHoursApi = {
  // 获取工时列表
  async getWorkHours(
    page: number = 1,
    pageSize: number = 20,
    filters?: WorkHourFilters
  ): Promise<PaginatedWorkHours> {
    const response = await http.get<PaginatedWorkHours>('/work-hours', {
      params: { page, page_size: pageSize, ...filters }
    })
    return response.data
  },

  // 获取工时详情
  async getWorkHour(id: number): Promise<WorkHour> {
    const response = await http.get<WorkHour>(`/work-hours/${id}`)
    return response.data
  },

  // 获取待审核工时列表
  async getPendingWorkHours(): Promise<WorkHour[]> {
    const response = await http.get<WorkHour[]>('/work-hours/pending-review')
    return response.data
  },

  // 批量重新计算工时
  async recalculateWorkHours(
    request: WorkHourCalculationRequest
  ): Promise<WorkHourCalculationResult[]> {
    const response = await http.post<WorkHourCalculationResult[]>(
      '/work-hours/recalculate',
      request
    )
    return response.data
  },

  // 单个任务工时重算
  async recalculateTaskWorkHours(
    taskId: number
  ): Promise<WorkHourCalculationResult> {
    const response = await http.post<WorkHourCalculationResult>(
      `/tasks/${taskId}/recalculate-hours`
    )
    return response.data
  },

  // 手动调整工时
  async adjustWorkHours(
    workHourId: number,
    adjustedHours: number,
    reason: string,
    notes?: string
  ): Promise<WorkHour> {
    const response = await http.put<WorkHour>(
      `/work-hours/${workHourId}/adjust`,
      {
        adjusted_hours: adjustedHours,
        reason,
        notes
      }
    )
    return response.data
  },

  // 审核工时
  async reviewWorkHour(
    workHourId: number,
    reviewType: 'approve' | 'reject' | 'adjust',
    reviewNotes: string,
    adjustedHours?: number
  ): Promise<WorkHour> {
    const response = await http.post<WorkHour>(
      `/work-hours/${workHourId}/review`,
      {
        review_type: reviewType,
        review_notes: reviewNotes,
        adjusted_hours: adjustedHours
      }
    )
    return response.data
  },

  // 批量审核工时
  async batchReviewWorkHours(
    workHourIds: number[],
    reviewType: 'approve' | 'reject',
    reviewNotes: string
  ): Promise<WorkHour[]> {
    const response = await http.post<WorkHour[]>('/work-hours/batch-review', {
      work_hour_ids: workHourIds,
      review_type: reviewType,
      review_notes: reviewNotes
    })
    return response.data
  },

  // 获取工时统计
  async getWorkHourStatistics(
    filters?: WorkHourFilters
  ): Promise<WorkHourStatistics> {
    const response = await http.get<WorkHourStatistics>(
      '/work-hours/statistics',
      {
        params: filters
      }
    )
    return response.data
  },

  // 获取工时汇总
  async getWorkHourSummary(
    period: 'daily' | 'weekly' | 'monthly',
    dateRange: [Date, Date]
  ): Promise<WorkHourSummary[]> {
    const response = await http.get<WorkHourSummary[]>('/work-hours/summary', {
      params: {
        period,
        start_date: dateRange[0].toISOString().split('T')[0],
        end_date: dateRange[1].toISOString().split('T')[0]
      }
    })
    return response.data
  },

  // 获取成员工时汇总
  async getMemberWorkHourSummary(
    dateRange: [Date, Date],
    department?: string
  ): Promise<MemberWorkHourSummary[]> {
    const response = await http.get<MemberWorkHourSummary[]>(
      '/work-hours/member-summary',
      {
        params: {
          start_date: dateRange[0].toISOString().split('T')[0],
          end_date: dateRange[1].toISOString().split('T')[0],
          department
        }
      }
    )
    return response.data
  },

  // 获取工时趋势
  async getWorkHourTrend(
    dateRange: [Date, Date],
    memberId?: number
  ): Promise<WorkHourTrend[]> {
    const response = await http.get<WorkHourTrend[]>('/work-hours/trend', {
      params: {
        start_date: dateRange[0].toISOString().split('T')[0],
        end_date: dateRange[1].toISOString().split('T')[0],
        member_id: memberId
      }
    })
    return response.data
  },

  // 获取工时调整记录
  async getWorkHourAdjustments(
    workHourId: number
  ): Promise<WorkHourAdjustment[]> {
    const response = await http.get<WorkHourAdjustment[]>(
      `/work-hours/${workHourId}/adjustments`
    )
    return response.data
  },

  // 获取工时审核记录
  async getWorkHourReviews(workHourId: number): Promise<WorkHourReview[]> {
    const response = await http.get<WorkHourReview[]>(
      `/work-hours/${workHourId}/reviews`
    )
    return response.data
  },

  // 获取工时规则列表
  async getWorkHourRules(): Promise<WorkHourRule[]> {
    const response = await http.get<WorkHourRule[]>('/work-hours/rules')
    return response.data
  },

  // 创建工时规则
  async createWorkHourRule(
    rule: Omit<WorkHourRule, 'id' | 'createdAt' | 'updatedAt'>
  ): Promise<WorkHourRule> {
    const response = await http.post<WorkHourRule>('/work-hours/rules', rule)
    return response.data
  },

  // 更新工时规则
  async updateWorkHourRule(
    id: number,
    rule: Partial<WorkHourRule>
  ): Promise<WorkHourRule> {
    const response = await http.put<WorkHourRule>(
      `/work-hours/rules/${id}`,
      rule
    )
    return response.data
  },

  // 删除工时规则
  async deleteWorkHourRule(id: number): Promise<void> {
    await http.delete(`/work-hours/rules/${id}`)
  },

  // 导出工时数据
  async exportWorkHours(config: WorkHourExportConfig): Promise<Blob> {
    const response = await http.post('/work-hours/export', config, {
      responseType: 'blob'
    })
    return response.data
  },

  // 获取工时模板
  async getWorkHourTemplate(): Promise<Blob> {
    const response = await http.get('/work-hours/template', {
      responseType: 'blob'
    })
    return response.data
  },

  // 导入工时数据
  async importWorkHours(file: File): Promise<{
    success: number
    failed: number
    errors: string[]
  }> {
    const formData = new FormData()
    formData.append('file', file)

    const response = await http.post('/work-hours/import', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
    return response.data
  },

  // 预览工时计算
  async previewWorkHourCalculation(
    taskId: number
  ): Promise<WorkHourCalculationResult> {
    const response = await http.get<WorkHourCalculationResult>(
      `/work-hours/preview/${taskId}`
    )
    return response.data
  },

  // 获取工时健康检查
  async getWorkHourHealthCheck(): Promise<{
    status: 'healthy' | 'warning' | 'error'
    pendingReviews: number
    overdueReviews: number
    inconsistentHours: number
    lastUpdated: string
  }> {
    const response = await http.get('/work-hours/health')
    return response.data
  }
}
