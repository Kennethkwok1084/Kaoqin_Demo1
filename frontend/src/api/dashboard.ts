import { http } from './client'
import type {
  DashboardStats,
  TaskDistribution,
  WorkHoursTrend,
  MemberPerformance,
  RecentActivity,
  MonthlyReport,
  AlertItem
} from '@/types/dashboard'

/**
 * 仪表板相关API
 */
export const dashboardApi = {
  /**
   * 获取仪表板统计数据
   */
  async getStats(): Promise<DashboardStats> {
    const response = await http.get<DashboardStats>('/dashboard/stats')
    return response.data
  },

  /**
   * 获取任务分布数据
   */
  async getTaskDistribution(): Promise<TaskDistribution> {
    const response = await http.get<TaskDistribution>(
      '/dashboard/task-distribution'
    )
    return response.data
  },

  /**
   * 获取工时趋势数据
   * @param days 获取最近多少天的数据，默认30天
   */
  async getWorkHoursTrend(days: number = 30): Promise<WorkHoursTrend[]> {
    const response = await http.get<WorkHoursTrend[]>(
      `/dashboard/work-hours-trend?days=${days}`
    )
    return response.data
  },

  /**
   * 获取成员绩效数据
   * @param limit 返回前N名成员，默认10
   */
  async getMemberPerformance(limit: number = 10): Promise<MemberPerformance[]> {
    const response = await http.get<MemberPerformance[]>(
      `/dashboard/member-performance?limit=${limit}`
    )
    return response.data
  },

  /**
   * 获取最近活动
   * @param limit 返回最近N条活动，默认20
   */
  async getRecentActivities(limit: number = 20): Promise<RecentActivity[]> {
    const response = await http.get<RecentActivity[]>(
      `/dashboard/recent-activities?limit=${limit}`
    )
    return response.data
  },

  /**
   * 获取月度报告
   * @param months 获取最近几个月的数据，默认6个月
   */
  async getMonthlyReports(months: number = 6): Promise<MonthlyReport[]> {
    const response = await http.get<MonthlyReport[]>(
      `/dashboard/monthly-reports?months=${months}`
    )
    return response.data
  },

  /**
   * 获取系统警告和提醒
   * @param resolved 是否包含已解决的警告，默认false
   */
  async getAlerts(resolved: boolean = false): Promise<AlertItem[]> {
    const response = await http.get<AlertItem[]>(
      `/dashboard/alerts?resolved=${resolved}`
    )
    return response.data
  },

  /**
   * 标记警告为已解决
   */
  async resolveAlert(alertId: number): Promise<void> {
    await http.patch(`/dashboard/alerts/${alertId}/resolve`)
  },

  /**
   * 获取系统健康状态
   */
  async getSystemHealth(): Promise<{
    status: 'healthy' | 'warning' | 'critical'
    database: boolean
    api: boolean
    storage: boolean
    lastUpdate: string
  }> {
    const response = await http.get('/dashboard/system-health')
    return response.data
  }
}
