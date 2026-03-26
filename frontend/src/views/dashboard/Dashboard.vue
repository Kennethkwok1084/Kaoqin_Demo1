<template>
  <div class="dashboard">
    <!-- 页面标题 -->
    <div class="dashboard-header">
      <div class="header-content">
        <h1 class="page-title">仪表板</h1>
        <p class="page-subtitle">考勤管理系统数据概览</p>
      </div>
      <div class="header-actions">
        <el-button
          type="primary"
          :icon="Refresh"
          @click="refreshData"
          :loading="isRefreshing"
        >
          刷新数据
        </el-button>
      </div>
    </div>

    <!-- 快速统计卡片 -->
    <div class="stats-section">
      <el-row :gutter="20">
        <el-col
          :xs="24"
          :sm="12"
          :md="6"
          v-for="stat in statsCards"
          :key="stat.key"
        >
          <div class="stat-card" :class="stat.className">
            <div class="stat-icon">
              <el-icon :size="32" :color="stat.iconColor">
                <component :is="stat.icon" />
              </el-icon>
            </div>
            <div class="stat-content">
              <div class="stat-value">
                {{ formatNumber(dashboardStats[stat.key]) }}
              </div>
              <div class="stat-label">{{ stat.label }}</div>
              <div
                class="stat-change"
                v-if="stat.change"
                :class="stat.change > 0 ? 'positive' : 'negative'"
              >
                <el-icon :size="12">
                  <component :is="stat.change > 0 ? ArrowUp : ArrowDown" />
                </el-icon>
                {{ Math.abs(stat.change) }}%
              </div>
            </div>
          </div>
        </el-col>
      </el-row>
    </div>

    <!-- 主要内容区域 -->
    <el-row :gutter="20" class="main-content">
      <!-- 左侧图表区域 -->
      <el-col :xs="24" :lg="16">
        <!-- 工时趋势图表 -->
        <el-card class="chart-card" shadow="hover">
          <template #header>
            <div class="card-header">
              <span class="card-title">工时趋势</span>
              <div class="card-actions">
                <el-radio-group
                  v-model="trendPeriod"
                  size="small"
                  @change="loadWorkHoursTrend"
                >
                  <el-radio-button label="7">7天</el-radio-button>
                  <el-radio-button label="30">30天</el-radio-button>
                  <el-radio-button label="90">90天</el-radio-button>
                </el-radio-group>
              </div>
            </div>
          </template>
          <div
            ref="workHoursChart"
            class="chart-container"
            v-loading="chartsLoading"
          ></div>
        </el-card>

        <!-- 任务分布饼图 -->
        <el-card class="chart-card" shadow="hover">
          <template #header>
            <span class="card-title">任务类型分布</span>
          </template>
          <div
            ref="taskDistributionChart"
            class="chart-container"
            v-loading="chartsLoading"
          ></div>
        </el-card>
      </el-col>

      <!-- 右侧信息区域 -->
      <el-col :xs="24" :lg="8">
        <!-- 系统警告 -->
        <el-card class="info-card" shadow="hover" v-if="alerts.length > 0">
          <template #header>
            <div class="card-header">
              <span class="card-title">系统警告</span>
              <el-badge :value="alerts.length" :max="99" class="alert-badge" />
            </div>
          </template>
          <div class="alerts-list">
            <div
              class="alert-item"
              v-for="alert in alerts.slice(0, 5)"
              :key="alert.id"
              :class="`alert-${alert.level}`"
            >
              <div class="alert-icon">
                <el-icon>
                  <component :is="getAlertIcon(alert.level)" />
                </el-icon>
              </div>
              <div class="alert-content">
                <div class="alert-title">{{ alert.title }}</div>
                <div class="alert-time">{{ formatTime(alert.timestamp) }}</div>
              </div>
              <el-button
                type="text"
                size="small"
                @click="resolveAlert(alert.id)"
                v-if="!alert.resolved"
              >
                处理
              </el-button>
            </div>
          </div>
          <div class="card-footer" v-if="alerts.length > 5">
            <el-button type="text" size="small" @click="viewAllAlerts">
              查看全部警告 ({{ alerts.length }})
            </el-button>
          </div>
        </el-card>

        <!-- 最近活动 -->
        <el-card class="info-card" shadow="hover">
          <template #header>
            <span class="card-title">最近活动</span>
          </template>
          <div class="activities-list">
            <div
              class="activity-item"
              v-for="activity in recentActivities.slice(0, 6)"
              :key="activity.id"
            >
              <div class="activity-icon">
                <el-icon :color="getActivityColor(activity.type)">
                  <component :is="getActivityIcon(activity.type)" />
                </el-icon>
              </div>
              <div class="activity-content">
                <div class="activity-title">{{ activity.title }}</div>
                <div class="activity-desc">{{ activity.description }}</div>
                <div class="activity-time">
                  {{ formatTime(activity.timestamp) }}
                </div>
              </div>
            </div>
          </div>
        </el-card>

        <!-- 快速操作 -->
        <el-card class="info-card" shadow="hover">
          <template #header>
            <span class="card-title">快速操作</span>
          </template>
          <div class="quick-actions">
            <el-button
              v-for="action in quickActions"
              :key="action.id"
              :type="action.color"
              :icon="action.icon"
              class="quick-action-btn"
              @click="navigateToAction(action.route)"
            >
              {{ action.title }}
            </el-button>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 成员绩效表格 -->
    <el-card class="performance-card" shadow="hover">
      <template #header>
        <div class="card-header">
          <span class="card-title">团队成员绩效</span>
          <el-button type="text" @click="viewAllMembers">查看详情</el-button>
        </div>
      </template>
      <el-table
        :data="memberPerformance"
        style="width: 100%"
        v-loading="tableLoading"
        empty-text="暂无数据"
      >
        <el-table-column prop="memberName" label="成员姓名" width="120" />
        <el-table-column
          prop="completedTasks"
          label="完成任务"
          width="100"
          align="center"
        />
        <el-table-column
          prop="workHours"
          label="工作时长"
          width="100"
          align="center"
        >
          <template #default="scope"> {{ scope.row.workHours }}h </template>
        </el-table-column>
        <el-table-column
          prop="attendanceRate"
          label="出勤率"
          width="100"
          align="center"
        >
          <template #default="scope">
            <el-tag
              :type="getAttendanceTagType(scope.row.attendanceRate) as any"
            >
              {{ (scope.row.attendanceRate * 100).toFixed(1) }}%
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column
          prop="efficiency"
          label="工作效率"
          width="120"
          align="center"
        >
          <template #default="scope">
            <el-progress
              :percentage="scope.row.efficiency"
              :color="getEfficiencyColor(scope.row.efficiency)"
              :show-text="true"
              :format="percentage => `${percentage}%`"
            />
          </template>
        </el-table-column>
        <el-table-column label="操作" align="center">
          <template #default="scope">
            <el-button
              type="text"
              size="small"
              @click="viewMemberDetail(scope.row.memberId)"
            >
              详情
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, onUnmounted, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import {
  Refresh,
  ArrowUp,
  ArrowDown,
  Document,
  User,
  Clock,
  DataLine,
  Warning,
  CircleCheck,
  InfoFilled,
  WarningFilled,
  Plus
} from '@element-plus/icons-vue'
import * as echarts from 'echarts'
import { statisticsApi } from '@/api/statistics'
import { dashboardApi } from '@/api/dashboard'
import dayjs from 'dayjs'
import type {
  DashboardStats,
  TaskDistribution,
  WorkHoursTrend,
  MemberPerformance,
  RecentActivity,
  AlertItem
} from '@/types/dashboard'

const router = useRouter()

// 响应式数据
const isRefreshing = ref(false)
const chartsLoading = ref(false)
const tableLoading = ref(false)
const trendPeriod = ref('30')

const dashboardStats = reactive<DashboardStats>({
  totalTasks: 0,
  completedTasks: 0,
  pendingTasks: 0,
  overdueTasks: 0,
  totalMembers: 0,
  activeMembers: 0,
  totalWorkHours: 0,
  monthlyWorkHours: 0,
  attendanceRate: 0,
  completionRate: 0
})

const taskDistribution = ref<TaskDistribution>({
  repair: 0,
  monitoring: 0,
  assistance: 0
})
const workHoursTrend = ref<WorkHoursTrend[]>([])
const memberPerformance = ref<MemberPerformance[]>([])
const recentActivities = ref<RecentActivity[]>([])
const alerts = ref<AlertItem[]>([])

// 图表实例
const workHoursChart = ref<HTMLElement>()
const taskDistributionChart = ref<HTMLElement>()
let workHoursChartInstance: echarts.ECharts | null = null
let taskDistributionChartInstance: echarts.ECharts | null = null

// 统计卡片配置
const statsCards = [
  {
    key: 'totalTasks' as keyof DashboardStats,
    label: '总任务数',
    icon: Document,
    iconColor: '#409EFF',
    className: 'stat-primary'
  },
  {
    key: 'completedTasks' as keyof DashboardStats,
    label: '已完成',
    icon: CircleCheck,
    iconColor: '#67C23A',
    className: 'stat-success'
  },
  {
    key: 'activeMembers' as keyof DashboardStats,
    label: '活跃成员',
    icon: User,
    iconColor: '#E6A23C',
    className: 'stat-warning'
  },
  {
    key: 'monthlyWorkHours' as keyof DashboardStats,
    label: '本月工时',
    icon: Clock,
    iconColor: '#F56C6C',
    className: 'stat-danger'
  }
]

// 快速操作配置
const quickActions: Array<{
  id: string
  title: string
  icon: any
  color:
    | 'default'
    | 'primary'
    | 'success'
    | 'warning'
    | 'info'
    | 'danger'
    | 'text'
  route: string
}> = [
  {
    id: 'new-task',
    title: '新建任务',
    icon: Plus,
    color: 'primary',
    route: '/tasks'
  },
  {
    id: 'view-members',
    title: '成员管理',
    icon: User,
    color: 'success',
    route: '/members'
  },
  {
    id: 'attendance',
    title: '考勤记录',
    icon: Clock,
    color: 'warning',
    route: '/attendance'
  },
  {
    id: 'reports',
    title: '报表统计',
    icon: DataLine,
    color: 'info',
    route: '/statistics'
  }
]

// 方法
const formatNumber = (num: number): string => {
  if (num >= 1000) {
    return (num / 1000).toFixed(1) + 'k'
  }
  return num.toString()
}

const formatTime = (timestamp: string): string => {
  if (!timestamp) return '未知时间'

  const normalizeForParse = (value: string) =>
    value.includes('T') ? value : value.replace(' ', 'T')

  let parsed = dayjs(timestamp)
  if (!parsed.isValid()) {
    parsed = dayjs(normalizeForParse(timestamp))
  }

  if (!parsed.isValid()) return '未知时间'

  const diff = dayjs().diff(parsed)

  if (diff < 60000) return '刚刚'
  if (diff < 3600000) return `${Math.floor(diff / 60000)}分钟前`
  if (diff < 86400000) return `${Math.floor(diff / 3600000)}小时前`
  return `${Math.floor(diff / 86400000)}天前`
}

const getAlertIcon = (level: string) => {
  switch (level) {
    case 'critical':
      return WarningFilled
    case 'high':
      return Warning
    case 'medium':
      return InfoFilled
    default:
      return InfoFilled
  }
}

const getActivityIcon = (type: string) => {
  switch (type) {
    case 'task_completed':
      return CircleCheck
    case 'task_assigned':
      return Document
    case 'member_joined':
      return User
    case 'attendance':
      return Clock
    default:
      return InfoFilled
  }
}

const getActivityColor = (type: string): string => {
  switch (type) {
    case 'task_completed':
      return '#67C23A'
    case 'task_assigned':
      return '#409EFF'
    case 'member_joined':
      return '#E6A23C'
    case 'attendance':
      return '#909399'
    default:
      return '#909399'
  }
}

const getAttendanceTagType = (rate: number): string => {
  if (rate >= 0.95) return 'success'
  if (rate >= 0.9) return 'warning'
  return 'danger'
}

const getEfficiencyColor = (efficiency: number): string => {
  if (efficiency >= 80) return '#67C23A'
  if (efficiency >= 60) return '#E6A23C'
  return '#F56C6C'
}

// 加载数据的方法
const loadDashboardStats = async () => {
  try {
    // 调用API获取仪表板统计数据
    const statsData = await dashboardApi.getStats()

    // 更新仪表板统计数据
    Object.assign(dashboardStats, statsData)
  } catch (error) {
    console.error('加载统计数据失败:', error)
    ElMessage.error('加载仪表板数据失败')
  }
}

const loadTaskDistribution = async () => {
  try {
    // 获取任务分布数据
    const distributionData = await dashboardApi.getTaskDistribution()

    // 更新任务分布数据
    taskDistribution.value = distributionData

    await nextTick()
    initTaskDistributionChart()
  } catch (error) {
    console.error('加载任务分布失败:', error)
    ElMessage.error('加载任务分布数据失败')
  }
}

const loadWorkHoursTrend = async () => {
  try {
    chartsLoading.value = true
    // 调用API获取工时趋势数据
    const data = await dashboardApi.getWorkHoursTrend(parseInt(trendPeriod.value))
    workHoursTrend.value = data || []
    await nextTick()
    initWorkHoursChart()
  } catch (error) {
    console.error('加载工时趋势失败:', error)
    ElMessage.error('加载工时趋势数据失败')
    workHoursTrend.value = []
  } finally {
    chartsLoading.value = false
  }
}

const loadMemberPerformance = async () => {
  try {
    tableLoading.value = true
    // 调用API获取成员绩效数据
    const data = await dashboardApi.getMemberPerformance()
    memberPerformance.value = data || []
  } catch (error) {
    console.error('加载成员绩效失败:', error)
    ElMessage.error('加载成员绩效数据失败')
    memberPerformance.value = []
  } finally {
    tableLoading.value = false
  }
}

const loadRecentActivities = async () => {
  try {
    // 调用API获取最近活动数据
    const data = await dashboardApi.getRecentActivities(10)
    recentActivities.value = Array.isArray(data)
      ? data
      : Array.isArray((data as any)?.items)
        ? (data as any).items
        : []
  } catch (error) {
    console.error('加载最近活动失败:', error)
    ElMessage.error('加载最近活动数据失败')
    recentActivities.value = []
  }
}

const loadAlerts = async () => {
  try {
    // 调用API获取系统警告数据
    const data = await dashboardApi.getAlerts(false)
    alerts.value = data || []
  } catch (error) {
    console.error('加载警告信息失败:', error)
    ElMessage.error('加载系统警告数据失败')
    alerts.value = []
  }
}

// 图表初始化
const initWorkHoursChart = () => {
  if (!workHoursChart.value) return

  if (workHoursChartInstance) {
    workHoursChartInstance.dispose()
  }

  workHoursChartInstance = echarts.init(workHoursChart.value)

  const option = {
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'cross'
      }
    },
    legend: {
      data: ['实际工时', '目标工时']
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      data: workHoursTrend.value.map(item => item.date)
    },
    yAxis: {
      type: 'value',
      name: '工时(小时)'
    },
    series: [
      {
        name: '实际工时',
        type: 'line',
        data: workHoursTrend.value.map(item => item.hours),
        itemStyle: { color: '#409EFF' },
        smooth: true
      },
      {
        name: '目标工时',
        type: 'line',
        data: workHoursTrend.value.map(item => item.target),
        itemStyle: { color: '#67C23A' },
        lineStyle: { type: 'dashed' },
        smooth: true
      }
    ]
  }

  workHoursChartInstance.setOption(option)
}

const initTaskDistributionChart = () => {
  if (!taskDistributionChart.value) return

  if (taskDistributionChartInstance) {
    taskDistributionChartInstance.dispose()
  }

  taskDistributionChartInstance = echarts.init(taskDistributionChart.value)

  const option = {
    tooltip: {
      trigger: 'item',
      formatter: '{a} <br/>{b}: {c} ({d}%)'
    },
    legend: {
      orient: 'vertical',
      left: 10,
      data: ['维修任务', '监控任务', '协助任务']
    },
    series: [
      {
        name: '任务分布',
        type: 'pie',
        radius: ['40%', '70%'],
        center: ['60%', '50%'],
        data: [
          {
            value: taskDistribution.value.repair,
            name: '维修任务',
            itemStyle: { color: '#409EFF' }
          },
          {
            value: taskDistribution.value.monitoring,
            name: '监控任务',
            itemStyle: { color: '#67C23A' }
          },
          {
            value: taskDistribution.value.assistance,
            name: '协助任务',
            itemStyle: { color: '#E6A23C' }
          }
        ],
        emphasis: {
          itemStyle: {
            shadowBlur: 10,
            shadowOffsetX: 0,
            shadowColor: 'rgba(0, 0, 0, 0.5)'
          }
        }
      }
    ]
  }

  taskDistributionChartInstance.setOption(option)
}

// 事件处理
const refreshData = async () => {
  isRefreshing.value = true
  try {
    await Promise.all([
      loadDashboardStats(),
      loadTaskDistribution(),
      loadWorkHoursTrend(),
      loadMemberPerformance(),
      loadRecentActivities(),
      loadAlerts()
    ])
    ElMessage.success('数据刷新成功')
  } catch (error) {
    ElMessage.error('数据刷新失败')
  } finally {
    isRefreshing.value = false
  }
}

const resolveAlert = async (alertId: number) => {
  void alertId
  ElMessage.warning('告警处理接口暂未接入，当前仅支持查看告警信息')
}

const navigateToAction = (route: string) => {
  router.push(route)
}

const viewAllAlerts = () => {
  ElMessage.warning('告警详情页暂未配置路由')
}

const viewAllMembers = () => {
  router.push('/members')
}

const viewMemberDetail = (memberId: number) => {
  router.push(`/members/${memberId}`)
}

const handleWindowResize = () => {
  workHoursChartInstance?.resize()
  taskDistributionChartInstance?.resize()
}

// 生命周期
onMounted(async () => {
  await refreshData()
  window.addEventListener('resize', handleWindowResize)
})

onUnmounted(() => {
  window.removeEventListener('resize', handleWindowResize)
  workHoursChartInstance?.dispose()
  taskDistributionChartInstance?.dispose()
  workHoursChartInstance = null
  taskDistributionChartInstance = null
})
</script>

<style scoped lang="scss">
@use '@/styles/variables.scss' as *;
@use '@/styles/mixins.scss' as *;
@use 'sass:color';

.dashboard {
  padding: $spacing-base;
  background: $background-color-base;
  min-height: calc(100vh - #{$header-height});
  position: relative;
  z-index: 1;
}

.dashboard-header {
  @include flex-between;
  margin-bottom: $spacing-large;
  padding: $spacing-base;
  background: $background-color-white;
  border-radius: $border-radius-base;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);

  .header-content {
    .page-title {
      margin: 0 0 $spacing-extra-small 0;
      font-size: $font-size-extra-large;
      font-weight: 600;
      color: $text-color-primary;
    }

    .page-subtitle {
      margin: 0;
      font-size: $font-size-small;
      color: $text-color-secondary;
    }
  }
}

.stats-section {
  margin-bottom: $spacing-large;
}

.stat-card {
  @include flex-start;
  padding: $spacing-base;
  background: $background-color-white;
  border-radius: $border-radius-base;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
  transition: all $transition-base;
  margin-bottom: $spacing-small; // 防止垂直重叠
  position: relative;

  &:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
  }

  .stat-icon {
    @include flex-center;
    width: 60px;
    height: 60px;
    border-radius: 50%;
    margin-right: $spacing-base;
  }

  .stat-content {
    flex: 1;

    .stat-value {
      font-size: $font-size-title;
      font-weight: 700;
      color: $text-color-primary;
      line-height: 1.2;
    }

    .stat-label {
      font-size: $font-size-small;
      color: $text-color-secondary;
      margin: $spacing-extra-small 0;
    }

    .stat-change {
      @include flex-start;
      font-size: $font-size-extra-small;
      gap: 2px;

      &.positive {
        color: $success-color;
      }

      &.negative {
        color: $danger-color;
      }
    }
  }

  &.stat-primary .stat-icon {
    background: color.adjust($primary-color, $lightness: 45%);
  }

  &.stat-success .stat-icon {
    background: color.adjust($success-color, $lightness: 45%);
  }

  &.stat-warning .stat-icon {
    background: color.adjust($warning-color, $lightness: 45%);
  }

  &.stat-danger .stat-icon {
    background: color.adjust($danger-color, $lightness: 45%);
  }
}

.main-content {
  margin-bottom: $spacing-large;
}

.chart-card,
.info-card,
.performance-card {
  margin-bottom: $spacing-base;

  .card-header {
    @include flex-between;

    .card-title {
      font-size: $font-size-medium;
      font-weight: 600;
      color: $text-color-primary;
    }
  }

  .chart-container {
    height: 300px;
    width: 100%;
  }
}

.alerts-list,
.activities-list {
  .alert-item,
  .activity-item {
    @include flex-start;
    padding: $spacing-small 0;
    border-bottom: 1px solid $border-color-extra-light;

    &:last-child {
      border-bottom: none;
    }

    .alert-icon,
    .activity-icon {
      @include flex-center;
      width: 32px;
      height: 32px;
      border-radius: 50%;
      margin-right: $spacing-small;
      flex-shrink: 0;
    }

    .alert-content,
    .activity-content {
      flex: 1;
      min-width: 0;

      .alert-title,
      .activity-title {
        font-size: $font-size-small;
        font-weight: 500;
        color: $text-color-primary;
        margin-bottom: 2px;
        @include text-ellipsis;
      }

      .activity-desc {
        font-size: $font-size-extra-small;
        color: $text-color-secondary;
        margin-bottom: 2px;
        @include text-ellipsis;
      }

      .alert-time,
      .activity-time {
        font-size: $font-size-extra-small;
        color: $text-color-placeholder;
      }
    }
  }

  .alert-item {
    &.alert-critical .alert-icon {
      background: color.adjust($danger-color, $lightness: 45%);
      color: $danger-color;
    }

    &.alert-high .alert-icon {
      background: color.adjust($warning-color, $lightness: 45%);
      color: $warning-color;
    }

    &.alert-medium .alert-icon {
      background: color.adjust($info-color, $lightness: 45%);
      color: $info-color;
    }
  }
}

.quick-actions {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: $spacing-small;

  .quick-action-btn {
    width: 100%;
    height: 40px;
  }
}

.card-footer {
  text-align: center;
  padding-top: $spacing-small;
  border-top: 1px solid $border-color-extra-light;
}

// 响应式设计
@include respond-to(md) {
  .dashboard {
    padding: $spacing-small;
    padding-bottom: calc(#{$spacing-small} + 60px); // 避免与底部导航重叠
  }

  .dashboard-header {
    flex-direction: column;
    gap: $spacing-base;
    align-items: stretch;

    .header-actions {
      align-self: flex-end;
    }
  }
}

@include respond-to(sm) {
  .dashboard {
    padding-bottom: calc(#{$spacing-small} + 80px); // 移动端底部导航更高
  }

  .stats-section {
    margin-bottom: $spacing-base;

    .el-col {
      margin-bottom: $spacing-small; // 卡片间距
    }
  }

  .main-content {
    .el-col {
      margin-bottom: $spacing-base; // 主要内容区间距
    }
  }

  .chart-card,
  .info-card {
    margin-bottom: $spacing-base;
    overflow: hidden; // 防止内容溢出
  }

  .quick-actions {
    grid-template-columns: 1fr;
    gap: $spacing-extra-small;
  }

  .chart-container {
    height: 250px;
    min-height: 200px; // 确保最小高度
  }

  .stat-card {
    padding: $spacing-small;
    margin-bottom: $spacing-small;

    .stat-icon {
      width: 48px;
      height: 48px;
    }

    .stat-content {
      .stat-value {
        font-size: $font-size-large;
      }
    }
  }
}
</style>
