// 工时管理API客户端

import { http } from './client'
import type {
  WorkHoursRecord,
  WorkHoursListParams,
  WorkHoursSummary,
  MonthlyWorkHoursReport,
  WorkHoursStats,
  WorkHoursChart
} from '@/types/attendance'

export const attendanceApi = {
  // 获取工时记录列表
  async getWorkHoursRecords(
    params?: WorkHoursListParams
  ): Promise<WorkHoursRecord[]> {
    const response = await http.get<WorkHoursRecord[]>('/attendance/records', {
      params
    })
    return response.data
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
    const response = await http.get<WorkHoursSummary>(
      '/attendance/today-summary'
    )
    return response.data
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
    format?: 'excel' | 'csv'
  }): Promise<{
    success: boolean
    message: string
    filename: string
    total_records: number
    download_url: string
    expires_at: number
  }> {
    const response = await http.get('/attendance/export', { params })
    return response.data
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

  // 考勤纠正 (占位符实现)
  async correctAttendance(params: {
    recordId: number
    type: string
    reason: string
  }): Promise<{ success: boolean; message: string }> {
    const response = await http.post('/attendance/correct', params)
    return response.data
  },

  // 获取签到地点 (占位符实现)
  async getCheckInLocations(): Promise<
    Array<{ id: number; name: string; address: string }>
  > {
    const response = await http.get('/attendance/check-in-locations')
    return response.data || []
  },

  // 签到 (占位符实现)
  async checkIn(params: {
    location: string
    latitude?: number
    longitude?: number
  }): Promise<{ success: boolean; message: string }> {
    const response = await http.post('/attendance/check-in', params)
    return response.data
  },

  // 签退 (占位符实现)
  async checkOut(params: {
    location: string
    workSummary?: string
  }): Promise<{ success: boolean; message: string }> {
    const response = await http.post('/attendance/check-out', params)
    return response.data
  },

  // 获取今日考勤状态 (占位符实现)
  async getTodayAttendanceStatus(): Promise<{
    hasCheckedIn: boolean
    hasCheckedOut: boolean
    checkInTime?: string
    checkOutTime?: string
  }> {
    const response = await http.get('/attendance/today-status')
    return response.data
  },

  // 创建请假申请 (占位符实现)
  async createLeaveApplication(params: {
    type: string
    startDate: string
    endDate: string
    reason: string
  }): Promise<{ success: boolean; message: string }> {
    const response = await http.post('/attendance/leave-application', params)
    return response.data
  },

  // 创建加班申请 (占位符实现)
  async createOvertimeApplication(params: {
    date: string
    startTime: string
    endTime: string
    reason: string
  }): Promise<{ success: boolean; message: string }> {
    const response = await http.post('/attendance/overtime-application', params)
    return response.data
  }
}
