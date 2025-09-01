// 统计数据状态管理
import { defineStore } from 'pinia'
import { ref, computed, readonly } from 'vue'
// 临时类型定义
export interface WorkHoursStats {
  totalHours: number
  totalTasks: number
  avgHoursPerTask: number
  monthlyBreakdown: any[]
  memberRanking: any[]
}

export interface MemberRanking {
  memberId: number
  memberName: string
  totalHours: number
  taskCount: number
  efficiency: number
}
import { api } from '@/api/client'

export interface StatisticsFilters {
  dateFrom?: string
  dateTo?: string
  memberId?: number
  period?: 'daily' | 'weekly' | 'monthly' | 'yearly'
}

export const useStatisticsStore = defineStore('statistics', () => {
  // 状态
  const workHoursStats = ref<WorkHoursStats | null>(null)
  const taskStatistics = ref<any>(null)
  const loading = ref(false)
  const error = ref<string | null>(null)
  
  // 当前筛选条件
  const filters = ref<StatisticsFilters>({
    period: 'monthly'
  })

  // 计算属性
  const totalWorkHours = computed(() => workHoursStats.value?.totalHours || 0)
  const totalTasks = computed(() => workHoursStats.value?.totalTasks || 0)
  const avgHoursPerTask = computed(() => workHoursStats.value?.avgHoursPerTask || 0)
  
  const topPerformers = computed(() => {
    if (!workHoursStats.value?.memberRanking) return []
    return workHoursStats.value.memberRanking
      .sort((a, b) => b.totalHours - a.totalHours)
      .slice(0, 5)
  })

  const monthlyTrend = computed(() => {
    if (!workHoursStats.value?.monthlyBreakdown) return []
    return workHoursStats.value.monthlyBreakdown.map(item => ({
      month: item.month,
      hours: item.hours,
      tasks: item.tasks,
      avgHours: item.tasks > 0 ? Number((item.hours / item.tasks).toFixed(2)) : 0
    }))
  })

  // 动作
  async function fetchWorkHoursStats(newFilters?: Partial<StatisticsFilters>) {
    if (newFilters) {
      filters.value = { ...filters.value, ...newFilters }
    }

    loading.value = true
    error.value = null

    try {
      const response = await api.getWorkHoursStats({
        dateFrom: filters.value.dateFrom,
        dateTo: filters.value.dateTo,
        memberId: filters.value.memberId
      })
      
      if (response.success && response.data) {
        workHoursStats.value = response.data
      } else {
        throw new Error(response.message || '获取工时统计失败')
      }
    } catch (err: any) {
      error.value = err.message
      console.error('Fetch work hours stats error:', err)
    } finally {
      loading.value = false
    }
  }

  async function fetchTaskStatistics(newFilters?: Partial<StatisticsFilters>) {
    if (newFilters) {
      filters.value = { ...filters.value, ...newFilters }
    }

    loading.value = true
    error.value = null

    try {
      const response = await api.getTaskStatistics({
        period: filters.value.period,
        dateRange: filters.value.dateFrom && filters.value.dateTo 
          ? `${filters.value.dateFrom},${filters.value.dateTo}` 
          : undefined
      })
      
      if (response.success && response.data) {
        taskStatistics.value = response.data
      } else {
        throw new Error(response.message || '获取任务统计失败')
      }
    } catch (err: any) {
      error.value = err.message
      console.error('Fetch task statistics error:', err)
    } finally {
      loading.value = false
    }
  }

  // 获取指定时间范围的统计
  async function getStatsByDateRange(dateFrom: string, dateTo: string, memberId?: number) {
    await fetchWorkHoursStats({ dateFrom, dateTo, memberId })
    await fetchTaskStatistics({ dateFrom, dateTo })
  }

  // 获取当月统计
  async function getCurrentMonthStats() {
    const now = new Date()
    const firstDay = new Date(now.getFullYear(), now.getMonth(), 1)
    const lastDay = new Date(now.getFullYear(), now.getMonth() + 1, 0)
    
    await getStatsByDateRange(
      firstDay.toISOString().split('T')[0],
      lastDay.toISOString().split('T')[0]
    )
  }

  // 获取当年统计
  async function getCurrentYearStats() {
    const now = new Date()
    const firstDay = new Date(now.getFullYear(), 0, 1)
    const lastDay = new Date(now.getFullYear(), 11, 31)
    
    await getStatsByDateRange(
      firstDay.toISOString().split('T')[0],
      lastDay.toISOString().split('T')[0]
    )
  }

  // 获取个人统计
  async function getPersonalStats(memberId: number, dateFrom?: string, dateTo?: string) {
    await fetchWorkHoursStats({ memberId, dateFrom, dateTo })
  }

  // 生成图表数据
  function generateChartData(type: 'workHours' | 'taskCount' | 'efficiency') {
    if (!workHoursStats.value?.monthlyBreakdown) return []

    return workHoursStats.value.monthlyBreakdown.map(item => {
      switch (type) {
        case 'workHours':
          return { x: item.month, y: item.hours }
        case 'taskCount':
          return { x: item.month, y: item.tasks }
        case 'efficiency':
          return { x: item.month, y: item.tasks > 0 ? item.hours / item.tasks : 0 }
        default:
          return { x: item.month, y: 0 }
      }
    })
  }

  // 生成成员排名数据
  function generateRankingData(limit: number = 10) {
    if (!workHoursStats.value?.memberRanking) return []

    return workHoursStats.value.memberRanking
      .sort((a, b) => b.totalHours - a.totalHours)
      .slice(0, limit)
      .map((member, index) => ({
        rank: index + 1,
        ...member
      }))
  }

  // 计算效率指标
  function calculateEfficiencyMetrics() {
    if (!workHoursStats.value) return null

    const { memberRanking, monthlyBreakdown } = workHoursStats.value

    // 成员效率分析
    const memberEfficiency = memberRanking.map(member => ({
      ...member,
      avgHoursPerTask: member.taskCount > 0 ? member.totalHours / member.taskCount : 0,
      productivityScore: member.efficiency || 0
    }))

    // 月度趋势分析
    const monthlyTrends = monthlyBreakdown.map((item, index, array) => {
      const prevItem = array[index - 1]
      const growthRate = prevItem 
        ? ((item.hours - prevItem.hours) / prevItem.hours * 100)
        : 0

      return {
        ...item,
        avgHoursPerTask: item.tasks > 0 ? item.hours / item.tasks : 0,
        growthRate: Number(growthRate.toFixed(2))
      }
    })

    return {
      memberEfficiency,
      monthlyTrends,
      totalEfficiencyScore: memberEfficiency.length > 0 
        ? memberEfficiency.reduce((sum, m) => sum + m.productivityScore, 0) / memberEfficiency.length
        : 0
    }
  }

  // 重置筛选条件
  function resetFilters() {
    filters.value = {
      period: 'monthly'
    }
  }

  // 清除错误
  function clearError() {
    error.value = null
  }

  // 导出数据
  function exportStatsData() {
    if (!workHoursStats.value) return null

    return {
      summary: {
        totalHours: totalWorkHours.value,
        totalTasks: totalTasks.value,
        avgHoursPerTask: avgHoursPerTask.value
      },
      monthlyData: monthlyTrend.value,
      memberRanking: workHoursStats.value.memberRanking,
      exportedAt: new Date().toISOString()
    }
  }

  return {
    // 状态
    workHoursStats: readonly(workHoursStats),
    taskStatistics: readonly(taskStatistics),
    loading: readonly(loading),
    error: readonly(error),
    filters: readonly(filters),
    
    // 计算属性
    totalWorkHours,
    totalTasks,
    avgHoursPerTask,
    topPerformers,
    monthlyTrend,
    
    // 动作
    fetchWorkHoursStats,
    fetchTaskStatistics,
    getStatsByDateRange,
    getCurrentMonthStats,
    getCurrentYearStats,
    getPersonalStats,
    generateChartData,
    generateRankingData,
    calculateEfficiencyMetrics,
    resetFilters,
    clearError,
    exportStatsData
  }
})