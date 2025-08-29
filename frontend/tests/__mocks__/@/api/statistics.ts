// Mock for @/api/statistics
import { vi } from 'vitest'

export const statisticsApi = {
  getOverview: vi.fn().mockResolvedValue({
    totalMembers: 50,
    activeMembers: 45,
    totalTasks: 120,
    completedTasks: 100,
    pendingTasks: 20,
    totalWorkHours: 2400,
    avgWorkHours: 48,
    efficiency: 85.5,
    categories: {
      repair: 30,
      maintenance: 45,
      cleaning: 25
    }
  }),
  
  getTaskStatistics: vi.fn().mockResolvedValue({
    byType: { repair: 30, maintenance: 45 },
    byStatus: { pending: 20, completed: 100 },
    trend: []
  }),
  
  getAttendanceStatistics: vi.fn().mockResolvedValue({
    totalDays: 30,
    presentDays: 28,
    absentDays: 2
  }),
  
  getWorkHoursStatistics: vi.fn().mockResolvedValue({
    thisMonth: 480,
    lastMonth: 450,
    growth: 6.7,
    daily: []
  }),

  // 其他可能需要的方法
  getDashboardChartData: vi.fn().mockResolvedValue({
    data: []
  }),
  
  getPerformanceMetrics: vi.fn().mockResolvedValue({
    data: {}
  }),
  
  generateReport: vi.fn().mockResolvedValue({
    data: {}
  }),
  
  exportData: vi.fn().mockResolvedValue({
    data: {}
  }),

  // Dashboard specific methods
  getOverviewStats: vi.fn().mockResolvedValue({
    repair: 45,
    monitoring: 35,
    assistance: 20
  }),

  getTaskStats: vi.fn().mockResolvedValue({
    pending: 15,
    in_progress: 25,
    completed: 55,
    cancelled: 5
  }),

  getWorkHourStats: vi.fn().mockResolvedValue([
    { date: '2023-11-01', hours: 280 },
    { date: '2023-11-02', hours: 320 },
    { date: '2023-11-03', hours: 290 },
    { date: '2023-11-04', hours: 350 },
    { date: '2023-11-05', hours: 310 }
  ])
}