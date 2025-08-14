import { describe, it, expect, beforeEach, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { createRouter, createWebHistory } from 'vue-router'
import Dashboard from '@/views/dashboard/Dashboard.vue'
import * as dashboardApi from '@/api/dashboard'
import * as statisticsApi from '@/api/statistics'

// Mock APIs
vi.mock('@/api/dashboard', () => ({
  getDashboardOverview: vi.fn(),
  getRecentTasks: vi.fn(),
  getRecentAttendance: vi.fn()
}))

vi.mock('@/api/statistics', () => ({
  getOverviewStats: vi.fn(),
  getTaskStats: vi.fn(),
  getWorkHourStats: vi.fn()
}))

// Mock ECharts
vi.mock('vue-echarts', () => ({
  default: {
    name: 'VChart',
    template: '<div class="mock-chart"></div>',
    props: ['option', 'autoresize']
  }
}))

// Mock router
const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/dashboard', component: Dashboard },
    { path: '/tasks', component: { template: '<div>Tasks</div>' } },
    { path: '/members', component: { template: '<div>Members</div>' } },
    { path: '/work-hours', component: { template: '<div>Work Hours</div>' } }
  ]
})

describe('Dashboard', () => {
  let wrapper: any

  const mockDashboardData = {
    overview: {
      total_tasks: 156,
      pending_tasks: 23,
      in_progress_tasks: 45,
      completed_tasks: 88,
      total_members: 42,
      active_members: 38,
      total_work_hours: 3240,
      avg_completion_time: 2.5
    },
    recent_tasks: [
      {
        id: 1,
        title: '图书馆网络故障',
        task_type: 'repair',
        task_status: 'pending',
        priority: 'high',
        created_at: '2023-12-01T10:00:00',
        assignee_name: '张三'
      },
      {
        id: 2,
        title: '宿舍楼监控检查',
        task_type: 'monitoring',
        task_status: 'in_progress',
        priority: 'medium',
        created_at: '2023-12-01T09:30:00',
        assignee_name: '李四'
      }
    ],
    recent_attendance: [
      {
        id: 1,
        member_name: '张三',
        check_in_time: '2023-12-01T08:30:00',
        check_out_time: '2023-12-01T17:30:00',
        work_hours: 8.5,
        status: 'normal'
      },
      {
        id: 2,
        member_name: '李四',
        check_in_time: '2023-12-01T08:45:00',
        check_out_time: null,
        work_hours: 0,
        status: 'working'
      }
    ]
  }

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

  beforeEach(async () => {
    setActivePinia(createPinia())

    // Mock API responses
    vi.mocked(dashboardApi.getDashboardOverview).mockResolvedValue(
      mockDashboardData.overview
    )
    vi.mocked(dashboardApi.getRecentTasks).mockResolvedValue(
      mockDashboardData.recent_tasks
    )
    vi.mocked(dashboardApi.getRecentAttendance).mockResolvedValue(
      mockDashboardData.recent_attendance
    )
    vi.mocked(statisticsApi.getOverviewStats).mockResolvedValue(
      mockStatsData.task_distribution
    )
    vi.mocked(statisticsApi.getTaskStats).mockResolvedValue(
      mockStatsData.task_status_distribution
    )
    vi.mocked(statisticsApi.getWorkHourStats).mockResolvedValue(
      mockStatsData.work_hours_trend
    )

    wrapper = mount(Dashboard, {
      global: {
        plugins: [router]
      }
    })

    await wrapper.vm.$nextTick()
  })

  afterEach(() => {
    wrapper?.unmount()
    vi.clearAllMocks()
  })

  describe('组件渲染', () => {
    it('应该正确渲染仪表板组件', () => {
      expect(wrapper.find('.dashboard-container').exists()).toBe(true)
      expect(wrapper.find('.dashboard-header').exists()).toBe(true)
      expect(wrapper.find('.overview-cards').exists()).toBe(true)
      expect(wrapper.find('.dashboard-charts').exists()).toBe(true)
      expect(wrapper.find('.recent-activities').exists()).toBe(true)
    })

    it('应该渲染页面标题和时间', () => {
      expect(wrapper.find('.dashboard-title').text()).toContain('数据概览')
      expect(wrapper.find('.dashboard-time').exists()).toBe(true)
    })

    it('应该渲染刷新按钮', () => {
      expect(wrapper.find('.refresh-btn').exists()).toBe(true)
    })
  })

  describe('数据加载', () => {
    it('应该在组件挂载时加载所有数据', async () => {
      expect(dashboardApi.getDashboardOverview).toHaveBeenCalled()
      expect(dashboardApi.getRecentTasks).toHaveBeenCalled()
      expect(dashboardApi.getRecentAttendance).toHaveBeenCalled()
      expect(statisticsApi.getOverviewStats).toHaveBeenCalled()
    })

    it('应该正确显示加载状态', async () => {
      // 模拟加载状态
      vi.mocked(dashboardApi.getDashboardOverview).mockImplementation(
        () =>
          new Promise(resolve =>
            setTimeout(() => resolve(mockDashboardData.overview), 100)
          )
      )

      const newWrapper = mount(Dashboard, {
        global: {
          plugins: [router]
        }
      })

      expect(newWrapper.vm.loading).toBe(true)

      await new Promise(resolve => setTimeout(resolve, 150))

      expect(newWrapper.vm.loading).toBe(false)
      newWrapper.unmount()
    })

    it('应该处理数据加载错误', async () => {
      vi.mocked(dashboardApi.getDashboardOverview).mockRejectedValue(
        new Error('API Error')
      )

      const newWrapper = mount(Dashboard, {
        global: {
          plugins: [router]
        }
      })

      await new Promise(resolve => setTimeout(resolve, 50))

      expect(newWrapper.vm.error).toBeTruthy()
      newWrapper.unmount()
    })
  })

  describe('概览卡片', () => {
    beforeEach(() => {
      wrapper.vm.overview = mockDashboardData.overview
    })

    it('应该显示任务统计卡片', async () => {
      await wrapper.vm.$nextTick()

      const taskCards = wrapper.findAll('.overview-card')
      expect(taskCards.length).toBeGreaterThan(0)

      // 验证总任务数
      expect(wrapper.text()).toContain('156')
      expect(wrapper.text()).toContain('总任务数')

      // 验证待处理任务数
      expect(wrapper.text()).toContain('23')
      expect(wrapper.text()).toContain('待处理')

      // 验证进行中任务数
      expect(wrapper.text()).toContain('45')
      expect(wrapper.text()).toContain('进行中')

      // 验证已完成任务数
      expect(wrapper.text()).toContain('88')
      expect(wrapper.text()).toContain('已完成')
    })

    it('应该显示成员统计卡片', async () => {
      await wrapper.vm.$nextTick()

      expect(wrapper.text()).toContain('42')
      expect(wrapper.text()).toContain('总成员数')

      expect(wrapper.text()).toContain('38')
      expect(wrapper.text()).toContain('活跃成员')
    })

    it('应该显示工时统计卡片', async () => {
      await wrapper.vm.$nextTick()

      expect(wrapper.text()).toContain('3240')
      expect(wrapper.text()).toContain('总工时')

      expect(wrapper.text()).toContain('2.5')
      expect(wrapper.text()).toContain('平均完成时间')
    })

    it('应该正确计算完成率', () => {
      const completionRate = wrapper.vm.getCompletionRate()
      const expected = ((88 / 156) * 100).toFixed(1)
      expect(completionRate).toBe(expected)
    })
  })

  describe('图表渲染', () => {
    beforeEach(() => {
      wrapper.vm.taskStats = mockStatsData.task_status_distribution
      wrapper.vm.workHourTrend = mockStatsData.work_hours_trend
    })

    it('应该渲染任务状态分布图表', async () => {
      await wrapper.vm.$nextTick()

      const taskChart = wrapper.find('[data-testid="task-status-chart"]')
      expect(taskChart.exists()).toBe(true)

      // 验证图表配置
      const chartOption = wrapper.vm.getTaskStatusChartOption()
      expect(chartOption.series[0].data).toHaveLength(4)
      expect(chartOption.series[0].data[0].value).toBe(15)
      expect(chartOption.series[0].data[0].name).toBe('待处理')
    })

    it('应该渲染工时趋势图表', async () => {
      await wrapper.vm.$nextTick()

      const trendChart = wrapper.find('[data-testid="work-hour-trend-chart"]')
      expect(trendChart.exists()).toBe(true)

      // 验证图表配置
      const chartOption = wrapper.vm.getWorkHourTrendChartOption()
      expect(chartOption.series[0].data).toHaveLength(5)
      expect(chartOption.xAxis.data).toEqual([
        '2023-11-01',
        '2023-11-02',
        '2023-11-03',
        '2023-11-04',
        '2023-11-05'
      ])
    })

    it('应该在数据为空时显示空状态', async () => {
      wrapper.vm.taskStats = {}
      wrapper.vm.workHourTrend = []
      await wrapper.vm.$nextTick()

      expect(wrapper.find('.empty-chart-state').exists()).toBe(true)
    })
  })

  describe('最近活动', () => {
    beforeEach(() => {
      wrapper.vm.recentTasks = mockDashboardData.recent_tasks
      wrapper.vm.recentAttendance = mockDashboardData.recent_attendance
    })

    it('应该显示最近任务列表', async () => {
      await wrapper.vm.$nextTick()

      const taskList = wrapper.find('.recent-tasks')
      expect(taskList.exists()).toBe(true)

      expect(wrapper.text()).toContain('图书馆网络故障')
      expect(wrapper.text()).toContain('宿舍楼监控检查')
      expect(wrapper.text()).toContain('张三')
      expect(wrapper.text()).toContain('李四')
    })

    it('应该显示任务优先级标签', async () => {
      await wrapper.vm.$nextTick()

      expect(wrapper.find('.priority-high').exists()).toBe(true)
      expect(wrapper.find('.priority-medium').exists()).toBe(true)
    })

    it('应该显示任务状态标签', async () => {
      await wrapper.vm.$nextTick()

      expect(wrapper.find('.status-pending').exists()).toBe(true)
      expect(wrapper.find('.status-in-progress').exists()).toBe(true)
    })

    it('应该显示最近考勤记录', async () => {
      await wrapper.vm.$nextTick()

      const attendanceList = wrapper.find('.recent-attendance')
      expect(attendanceList.exists()).toBe(true)

      expect(wrapper.text()).toContain('张三')
      expect(wrapper.text()).toContain('8.5')
      expect(wrapper.text()).toContain('李四')
      expect(wrapper.text()).toContain('工作中')
    })
  })

  describe('操作功能', () => {
    it('应该处理刷新操作', async () => {
      vi.clearAllMocks()

      await wrapper.find('.refresh-btn').trigger('click')

      expect(dashboardApi.getDashboardOverview).toHaveBeenCalled()
      expect(dashboardApi.getRecentTasks).toHaveBeenCalled()
      expect(dashboardApi.getRecentAttendance).toHaveBeenCalled()
    })

    it('应该处理快速导航', async () => {
      const routerPushSpy = vi.spyOn(router, 'push')

      await wrapper.find('.nav-to-tasks').trigger('click')
      expect(routerPushSpy).toHaveBeenCalledWith('/tasks')

      await wrapper.find('.nav-to-members').trigger('click')
      expect(routerPushSpy).toHaveBeenCalledWith('/members')

      await wrapper.find('.nav-to-work-hours').trigger('click')
      expect(routerPushSpy).toHaveBeenCalledWith('/work-hours')
    })

    it('应该处理任务详情查看', async () => {
      wrapper.vm.recentTasks = mockDashboardData.recent_tasks
      await wrapper.vm.$nextTick()

      const taskItem = wrapper.find('.task-item').first()
      await taskItem.trigger('click')

      expect(wrapper.vm.taskDetailVisible).toBe(true)
      expect(wrapper.vm.selectedTask).toEqual(mockDashboardData.recent_tasks[0])
    })

    it('应该处理考勤详情查看', async () => {
      wrapper.vm.recentAttendance = mockDashboardData.recent_attendance
      await wrapper.vm.$nextTick()

      const attendanceItem = wrapper.find('.attendance-item').first()
      await attendanceItem.trigger('click')

      expect(wrapper.vm.attendanceDetailVisible).toBe(true)
      expect(wrapper.vm.selectedAttendance).toEqual(
        mockDashboardData.recent_attendance[0]
      )
    })
  })

  describe('实时更新', () => {
    it('应该支持自动刷新', async () => {
      vi.useFakeTimers()

      wrapper.vm.enableAutoRefresh = true
      wrapper.vm.autoRefreshInterval = 30000

      vi.clearAllMocks()
      wrapper.vm.startAutoRefresh()

      // 快进30秒
      vi.advanceTimersByTime(30000)

      expect(dashboardApi.getDashboardOverview).toHaveBeenCalled()

      wrapper.vm.stopAutoRefresh()
      vi.useRealTimers()
    })

    it('应该在组件销毁时停止自动刷新', async () => {
      const stopSpy = vi.spyOn(wrapper.vm, 'stopAutoRefresh')

      wrapper.unmount()

      expect(stopSpy).toHaveBeenCalled()
    })
  })

  describe('响应式设计', () => {
    it('应该在移动设备上调整布局', async () => {
      // 模拟移动设备
      Object.defineProperty(window, 'innerWidth', {
        writable: true,
        configurable: true,
        value: 600
      })

      window.dispatchEvent(new Event('resize'))
      await wrapper.vm.$nextTick()

      expect(wrapper.vm.isMobile).toBe(true)
      expect(wrapper.find('.dashboard-container').classes()).toContain(
        'mobile-layout'
      )
    })

    it('应该在平板设备上调整图表大小', async () => {
      Object.defineProperty(window, 'innerWidth', {
        writable: true,
        configurable: true,
        value: 768
      })

      window.dispatchEvent(new Event('resize'))
      await wrapper.vm.$nextTick()

      expect(wrapper.vm.isTablet).toBe(true)
    })
  })

  describe('无障碍访问', () => {
    it('应该有正确的ARIA标签', () => {
      expect(wrapper.find('[role="main"]').exists()).toBe(true)
      expect(wrapper.find('[aria-label="数据概览"]').exists()).toBe(true)
    })

    it('应该支持键盘导航', async () => {
      const focusableElements = wrapper.findAll('[tabindex="0"]')
      expect(focusableElements.length).toBeGreaterThan(0)

      // 测试Tab键导航
      await wrapper.trigger('keydown.tab')
      expect(document.activeElement?.tagName).toBeDefined()
    })
  })

  describe('错误状态处理', () => {
    it('应该显示网络错误提示', async () => {
      wrapper.vm.error = '网络连接失败'
      await wrapper.vm.$nextTick()

      expect(wrapper.find('.error-message').exists()).toBe(true)
      expect(wrapper.text()).toContain('网络连接失败')
    })

    it('应该提供重试功能', async () => {
      wrapper.vm.error = '加载失败'
      await wrapper.vm.$nextTick()

      const retryBtn = wrapper.find('.retry-btn')
      expect(retryBtn.exists()).toBe(true)

      vi.clearAllMocks()
      await retryBtn.trigger('click')

      expect(dashboardApi.getDashboardOverview).toHaveBeenCalled()
      expect(wrapper.vm.error).toBe(null)
    })
  })

  describe('性能优化', () => {
    it('应该对大量数据进行分页处理', async () => {
      const largeTasks = Array.from({ length: 100 }, (_, i) => ({
        id: i + 1,
        title: `任务${i + 1}`,
        task_type: 'repair',
        task_status: 'pending',
        priority: 'medium',
        created_at: new Date().toISOString(),
        assignee_name: `用户${i + 1}`
      }))

      wrapper.vm.recentTasks = largeTasks
      await wrapper.vm.$nextTick()

      // 验证只显示前10条
      const taskItems = wrapper.findAll('.task-item')
      expect(taskItems.length).toBeLessThanOrEqual(10)
    })

    it('应该使用虚拟滚动处理大量数据', () => {
      const virtualScrollConfig = wrapper.vm.getVirtualScrollConfig()
      expect(virtualScrollConfig.itemHeight).toBeDefined()
      expect(virtualScrollConfig.visibleCount).toBeDefined()
    })
  })
})
