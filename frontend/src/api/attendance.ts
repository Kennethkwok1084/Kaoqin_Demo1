// 工时管理API客户端

import { http } from './client'
import type {
  WorkHoursRecord,
  WorkHoursListParams,
  WorkHoursSummary,
  MonthlyWorkHoursReport,
  WorkHoursStats,
  WorkHoursChart,
  WorkHoursCycleRecord
} from '@/types/attendance'

export const attendanceApi = {
  // 获取考勤周期汇总（基于任务口径，全员）
  async getCycleSummary(params: {
    cycle_type?: 'monthly' | 'weekly' | 'custom'
    month?: string // YYYY-MM
    week_start?: string // YYYY-MM-DD
    date_from?: string // YYYY-MM-DD
    date_to?: string // YYYY-MM-DD
    page?: number
    size?: number
  }): Promise<{
    success: boolean
    message: string
    data: {
      period: { start_date: string; end_date: string; cycle_type: string; days: number }
      page: number
      size: number
      total_members: number
      records: WorkHoursCycleRecord[]
    }
    status_code: number
  }> {
    const response = await http.get('/attendance/cycle-summary', { params })
    return response.data
  },

  // 导出考勤周期汇总
  async exportCycleSummary(params: {
    cycle_type?: 'monthly' | 'weekly' | 'custom'
    month?: string
    week_start?: string
    date_from?: string
    date_to?: string
    format?: 'excel' | 'csv'
  }): Promise<{
    success: boolean
    message: string
    filename: string
    total_records: number
    download_url: string
    expires_at: number
  }> {
    const response = await http.get('/attendance/cycle-export', { params })
    return response.data
  },

  // 下载导出文件（可直接 window.open(download_url)）
  async downloadExport(filename: string): Promise<Blob> {
    const response = await http.get(`/attendance/download/${filename}`, {
      responseType: 'blob'
    })
    return response.data
  },
  // 获取工时记录列表
  async getWorkHoursRecords(
    params?: WorkHoursListParams
  ): Promise<WorkHoursRecord[]> {
    try {
      const response = await http.get<WorkHoursRecord[]>('/attendance/records', {
        params
      })
      return response.data || []
    } catch (error) {
      console.error('获取工时记录失败:', error)
      // 返回空数组而不是抛出错误，让页面继续正常运行
      return []
    }
  },

  // 获取指定成员的工时记录
  async getMemberWorkHoursRecords(
    memberId: number,
    params?: WorkHoursListParams
  ): Promise<WorkHoursRecord[]> {
    const response = await http.get<WorkHoursRecord[]>('/attendance/records', {
      params: { ...params, member_id: memberId }
    })
    return response.data
  },

  // 获取今日工时概览
  async getTodayWorkHoursSummary(): Promise<WorkHoursSummary> {
    try {
      const response = await http.get<WorkHoursSummary>(
        '/attendance/today-summary'
      )
      return response.data
    } catch (error) {
      console.error('获取今日工时概览失败:', error)
      // 返回默认的空概览数据
      return {
        totalHours: 0,
        completedTasks: 0,
        ongoingTasks: 0,
        efficiency: 0
      } as WorkHoursSummary
    }
  },

  // 获取月度工时汇总
  async getMonthlyWorkHoursSummary(
    month: string,
    memberId?: number
  ): Promise<MonthlyWorkHoursReport> {
    const params = memberId ? { member_id: memberId } : {}
    const response = await http.get<MonthlyWorkHoursReport>(
      `/attendance/summary/${month}`,
      { params }
    )
    return response.data
  },

  // 导出工时数据
  async exportWorkHoursData(params: {
    date_from: string
    date_to: string
    member_ids?: number[]
    format?: 'excel'
  }): Promise<{
    success: boolean
    message: string
    filename: string
    total_records: number
    total?: number
    download_url: string
    expires_at: number
  }> {
    const response = await http.get('/attendance/export', { params })
    const data = response.data
    return (data && typeof data === 'object' && 'data' in data ? (data as any).data : data)
  },

  // 获取工时统计
  async getWorkHoursStats(params: {
    memberId?: number
    startDate: string
    endDate: string
  }): Promise<WorkHoursStats> {
    const response = await http.get<WorkHoursStats>('/attendance/stats', {
      params
    })
    return response.data
  },

  // 获取工时图表数据
  async getWorkHoursChartData(params: {
    type: 'daily' | 'weekly' | 'monthly'
    startDate: string
    endDate: string
    memberId?: number
  }): Promise<WorkHoursChart> {
    const response = await http.get<WorkHoursChart>('/attendance/chart-data', {
      params
    })
    return response.data
  },

  // 健康检查
  async healthCheck(): Promise<{ status: string; timestamp: string }> {
    const response = await http.get<{ status: string; timestamp: string }>(
      '/attendance/health'
    )
    return response.data
  },
}
