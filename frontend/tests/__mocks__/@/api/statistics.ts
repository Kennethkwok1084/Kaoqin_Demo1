// Statistics API Mock
import { vi } from 'vitest'

const mockStatsData = {
  task_distribution: {
    repair: 45,
    monitoring: 35,
    assistance: 20
  },
  task_status_distribution: {
    pending: 15,
    in_progress: 25,
    completed: 55,
    cancelled: 5
  },
  work_hours_trend: [
    { date: '2023-11-01', hours: 280 },
    { date: '2023-11-02', hours: 320 },
    { date: '2023-11-03', hours: 290 },
    { date: '2023-11-04', hours: 350 },
    { date: '2023-11-05', hours: 310 }
  ],
  member_efficiency: [
    { name: '张三', completion_rate: 0.95, avg_time: 2.1 },
    { name: '李四', completion_rate: 0.88, avg_time: 2.8 },
    { name: '王五', completion_rate: 0.92, avg_time: 2.3 }
  ]
}

// 导出所有需要的 API 函数
export const getOverviewStats = vi.fn().mockResolvedValue(mockStatsData)
export const getTaskStats = vi
  .fn()
  .mockResolvedValue(mockStatsData.task_status_distribution)
export const getWorkHourTrend = vi
  .fn()
  .mockResolvedValue(mockStatsData.work_hours_trend)
export const getMemberEfficiency = vi
  .fn()
  .mockResolvedValue(mockStatsData.member_efficiency)

// 导出 statisticsApi 对象
export const statisticsApi = {
  getOverviewStats,
  getTaskStats,
  getWorkHourTrend,
  getMemberEfficiency
}

// 默认导出
export default statisticsApi
