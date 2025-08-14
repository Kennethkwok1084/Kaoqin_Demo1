// 统计报表API客户端

import { http } from './client'
import type {
  StatisticsOverview,
  TaskStatistics,
  AttendanceStatistics,
  WorkHoursStatistics,
  StatisticsFilters,
  ChartData,
  ReportTemplate,
  GeneratedReport,
  ExportOptions,
  PerformanceMetrics,
  ComparisonData,
  DashboardWidget
} from '@/types/statistics'

export const statisticsApi = {
  // 获取统计概览
  async getOverview(filters?: StatisticsFilters): Promise<StatisticsOverview> {
    const response = await http.get('/statistics/overview', { params: filters })
    return response.data.data || {}
  },

  // 获取任务统计
  async getTaskStatistics(
    filters?: StatisticsFilters
  ): Promise<TaskStatistics> {
    const response = await http.get('/statistics/tasks', { params: filters })
    return response.data.data || {}
  },

  // 获取考勤统计
  async getAttendanceStatistics(params: {
    start_date: string
    end_date: string
    [key: string]: any
  }): Promise<AttendanceStatistics> {
    const response = await http.get('/statistics/attendance', { params })
    return response.data.data || {}
  },

  // 获取工时统计
  async getWorkHoursStatistics(
    filters?: StatisticsFilters
  ): Promise<WorkHoursStatistics> {
    const response = await http.get('/statistics/work-hours', {
      params: filters
    })
    return response.data.data || {}
  },

  // 获取绩效指标
  async getPerformanceMetrics(
    filters?: StatisticsFilters
  ): Promise<PerformanceMetrics> {
    const response = await http.get('/statistics/performance', {
      params: filters
    })
    return response.data.data || {}
  },

  // 获取对比数据
  async getComparisonData(params: {
    metric: string
    currentPeriod: [string, string]
    previousPeriod: [string, string]
    filters?: StatisticsFilters
  }): Promise<ComparisonData> {
    const response = await http.get('/statistics/comparison', { params })
    return response.data.data || {}
  },

  // 获取图表数据
  async getChartData(params: {
    type: string
    metric: string
    filters?: StatisticsFilters
  }): Promise<ChartData> {
    const response = await http.get('/statistics/charts', { params })
    // 后端使用 create_response() 包装，实际数据在 data.data 中
    return response.data.data || { labels: [], datasets: [] }
  },

  // 获取实时数据
  async getRealTimeData(metrics: string[]): Promise<{ [key: string]: any }> {
    const response = await http.get('/statistics/realtime', {
      params: { metrics: metrics.join(',') }
    })
    return response.data.data || {}
  },

  // 获取趋势分析
  async getTrendAnalysis(params: {
    metric: string
    period: 'daily' | 'weekly' | 'monthly'
    range: [string, string]
    filters?: StatisticsFilters
  }): Promise<{
    trend: 'up' | 'down' | 'stable'
    change: number
    forecast: number[]
    data: { date: string; value: number }[]
  }> {
    const response = await http.get('/statistics/trends', { params })
    return (
      response.data.data || {
        trend: 'stable',
        change: 0,
        forecast: [],
        data: []
      }
    )
  },

  // 获取排行榜数据
  async getRankingData(params: {
    type: 'members' | 'departments' | 'tasks'
    metric: string
    period_start: string
    period_end: string
    limit?: number
  }): Promise<any[]> {
    const response = await http.get('/statistics/rankings', { params })
    return response.data.data || []
  },

  // 获取分布数据
  async getDistributionData(params: {
    metric: string
    dimension: string
    filters?: StatisticsFilters
  }): Promise<{ [key: string]: number }> {
    const response = await http.get('/statistics/distribution', { params })
    return response.data.data || {}
  },

  // === 报表管理 ===

  // 获取报表模板列表
  async getReportTemplates(): Promise<ReportTemplate[]> {
    const response = await http.get<ReportTemplate[]>(
      '/statistics/report-templates'
    )
    return response.data
  },

  // 获取报表模板详情
  async getReportTemplate(id: string): Promise<ReportTemplate> {
    const response = await http.get<ReportTemplate>(
      `/statistics/report-templates/${id}`
    )
    return response.data
  },

  // 创建报表模板
  async createReportTemplate(
    template: Omit<ReportTemplate, 'id'>
  ): Promise<ReportTemplate> {
    const response = await http.post<ReportTemplate>(
      '/statistics/report-templates',
      template
    )
    return response.data
  },

  // 更新报表模板
  async updateReportTemplate(
    id: string,
    template: Partial<ReportTemplate>
  ): Promise<ReportTemplate> {
    const response = await http.put<ReportTemplate>(
      `/statistics/report-templates/${id}`,
      template
    )
    return response.data
  },

  // 删除报表模板
  async deleteReportTemplate(id: string): Promise<void> {
    await http.delete(`/statistics/report-templates/${id}`)
  },

  // 生成报表
  async generateReport(params: {
    templateId: string
    period: [string, string]
    filters?: StatisticsFilters
    options?: ExportOptions
  }): Promise<GeneratedReport> {
    const response = await http.post<GeneratedReport>(
      '/statistics/reports/generate',
      params
    )
    return response.data
  },

  // 获取生成的报表列表
  async getGeneratedReports(params?: {
    page?: number
    pageSize?: number
    templateId?: string
    status?: string
    dateRange?: [string, string]
  }): Promise<{
    items: GeneratedReport[]
    total: number
    page: number
    pageSize: number
  }> {
    const response = await http.get('/statistics/reports', { params })
    return response.data
  },

  // 获取报表详情
  async getGeneratedReport(id: string): Promise<GeneratedReport> {
    const response = await http.get<GeneratedReport>(
      `/statistics/reports/${id}`
    )
    return response.data
  },

  // 下载报表
  async downloadReport(id: string): Promise<Blob> {
    const response = await http.get(`/statistics/reports/${id}/download`, {
      responseType: 'blob'
    })
    return response.data
  },

  // 删除报表
  async deleteReport(id: string): Promise<void> {
    await http.delete(`/statistics/reports/${id}`)
  },

  // === 数据导出 ===

  // 导出统计数据
  async exportStatistics(options: ExportOptions): Promise<Blob> {
    const response = await http.post('/statistics/export', options, {
      responseType: 'blob'
    })
    return response.data
  },

  // 导出图表
  async exportChart(params: {
    type: string
    metric: string
    format: 'png' | 'jpeg' | 'pdf' | 'svg'
    width?: number
    height?: number
    filters?: StatisticsFilters
  }): Promise<Blob> {
    const response = await http.post('/statistics/charts/export', params, {
      responseType: 'blob'
    })
    return response.data
  },

  // 批量导出
  async batchExport(params: {
    items: Array<{
      type: 'chart' | 'data' | 'report'
      id: string
      options?: any
    }>
    format: 'zip' | 'pdf'
  }): Promise<Blob> {
    const response = await http.post('/statistics/batch-export', params, {
      responseType: 'blob'
    })
    return response.data
  },

  // === 仪表板管理 ===

  // 获取仪表板配置
  async getDashboardConfig(userId?: number): Promise<DashboardWidget[]> {
    const response = await http.get<DashboardWidget[]>(
      '/statistics/dashboard',
      {
        params: { userId }
      }
    )
    return response.data
  },

  // 更新仪表板配置
  async updateDashboardConfig(widgets: DashboardWidget[]): Promise<void> {
    await http.put('/statistics/dashboard', { widgets })
  },

  // 获取仪表板数据
  async getDashboardData(widgetIds: string[]): Promise<{ [key: string]: any }> {
    const response = await http.post('/statistics/dashboard/data', {
      widgetIds
    })
    return response.data
  },

  // === 预设查询 ===

  // 今日数据
  async getTodayData(): Promise<{
    tasks: { total: number; completed: number; pending: number }
    attendance: { present: number; total: number; rate: number }
    workHours: { total: number; average: number }
  }> {
    const response = await http.get('/statistics/today')
    return response.data
  },

  // 本周数据
  async getWeekData(): Promise<{
    tasks: TaskStatistics
    attendance: AttendanceStatistics
    trends: { [key: string]: number[] }
  }> {
    const response = await http.get('/statistics/week')
    return response.data
  },

  // 本月数据
  async getMonthData(): Promise<{
    overview: StatisticsOverview
    comparison: ComparisonData
    rankings: any[]
  }> {
    const response = await http.get('/statistics/month')
    return response.data
  },

  // 年度数据
  async getYearData(): Promise<{
    overview: StatisticsOverview
    monthlyTrends: any[]
    achievements: any[]
  }> {
    const response = await http.get('/statistics/year')
    return response.data
  },

  // === 分析工具 ===

  // 异常检测
  async detectAnomalies(params: {
    metric: string
    period: [string, string]
    sensitivity?: 'low' | 'medium' | 'high'
  }): Promise<{
    anomalies: Array<{
      date: string
      value: number
      expected: number
      severity: 'low' | 'medium' | 'high'
      reason?: string
    }>
    summary: {
      total: number
      byType: { [key: string]: number }
    }
  }> {
    const response = await http.post('/statistics/anomalies', params)
    return response.data
  },

  // 相关性分析
  async getCorrelationAnalysis(params: {
    metrics: string[]
    period: [string, string]
    filters?: StatisticsFilters
  }): Promise<{
    correlations: { [key: string]: { [key: string]: number } }
    insights: string[]
  }> {
    const response = await http.post('/statistics/correlation', params)
    return response.data
  },

  // 预测分析
  async getForecast(params: {
    metric: string
    period: [string, string]
    forecastDays: number
    model?: 'linear' | 'polynomial' | 'seasonal'
  }): Promise<{
    historical: { date: string; value: number }[]
    forecast: { date: string; value: number; confidence: number }[]
    accuracy: number
  }> {
    const response = await http.post('/statistics/forecast', params)
    return response.data
  },

  // 健康检查
  async healthCheck(): Promise<{ status: string; timestamp: string }> {
    const response = await http.get<{ status: string; timestamp: string }>(
      '/statistics/health'
    )
    return response.data
  }
}
