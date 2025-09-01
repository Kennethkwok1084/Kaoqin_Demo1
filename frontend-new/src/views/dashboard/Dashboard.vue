<template>
  <div class="desktop-dashboard">
    <!-- 页面标题和用户欢迎区 -->
    <div class="dashboard-header">
      <div class="welcome-section">
        <div class="welcome-text">
          <h1>数据仪表板</h1>
          <p>欢迎回来，<strong>{{ user?.name || '管理员' }}</strong> | {{ getCurrentTime() }}</p>
        </div>
        <div class="quick-actions">
          <a-button type="primary" :icon="h(PlusOutlined)" @click="router.push('/tasks/create')">>
            新建任务
          </a-button>
          <a-button :icon="h(ReloadOutlined)" @click="refreshData" :loading="loading">
            刷新数据
          </a-button>
        </div>
      </div>
    </div>

    <!-- 核心指标卡片 -->
    <div class="metrics-grid">
      <div class="metric-card primary">
        <div class="metric-icon">
          <ProjectOutlined />
        </div>
        <div class="metric-content">
          <div class="metric-value">{{ loading ? '--' : (dashboardOverview?.metrics?.totalTasks || stats?.overview?.total || 0) }}</div>
          <div class="metric-label">总任务数</div>
          <div class="metric-trend" v-if="!loading && dashboardOverview?.trends?.totalTasksTrend" :class="getTrendClass(dashboardOverview.trends.totalTasksTrend.direction)">
            <CaretUpOutlined v-if="dashboardOverview.trends.totalTasksTrend.direction === 'up'" />
            <CaretDownOutlined v-else-if="dashboardOverview.trends.totalTasksTrend.direction === 'down'" />
            <span>{{ formatTrend(dashboardOverview.trends.totalTasksTrend.value, dashboardOverview.trends.totalTasksTrend.direction) }}</span>
          </div>
        </div>
      </div>

      <div class="metric-card success">
        <div class="metric-icon">
          <CheckCircleOutlined />
        </div>
        <div class="metric-content">
          <div class="metric-value">{{ loading ? '--' : (dashboardOverview?.metrics?.inProgress || stats?.overview?.inProgress || 0) }}</div>
          <div class="metric-label">进行中任务</div>
          <div class="metric-trend" v-if="!loading && dashboardOverview?.trends?.inProgressTrend" :class="getTrendClass(dashboardOverview.trends.inProgressTrend.direction)">
            <CaretUpOutlined v-if="dashboardOverview.trends.inProgressTrend.direction === 'up'" />
            <CaretDownOutlined v-else-if="dashboardOverview.trends.inProgressTrend.direction === 'down'" />
            <span>{{ formatTrend(dashboardOverview.trends.inProgressTrend.value, dashboardOverview.trends.inProgressTrend.direction) }}</span>
          </div>
        </div>
      </div>

      <div class="metric-card warning">
        <div class="metric-icon">
          <ClockCircleOutlined />
        </div>
        <div class="metric-content">
          <div class="metric-value">{{ loading ? '--' : (dashboardOverview?.metrics?.pending || stats?.overview?.pending || 0) }}</div>
          <div class="metric-label">待处理任务</div>
          <div class="metric-trend" v-if="!loading && dashboardOverview?.trends?.pendingTrend" :class="getTrendClass(dashboardOverview.trends.pendingTrend.direction)">
            <CaretUpOutlined v-if="dashboardOverview.trends.pendingTrend.direction === 'up'" />
            <CaretDownOutlined v-else-if="dashboardOverview.trends.pendingTrend.direction === 'down'" />
            <span>{{ formatTrend(dashboardOverview.trends.pendingTrend.value, dashboardOverview.trends.pendingTrend.direction) }}</span>
          </div>
        </div>
      </div>

      <div class="metric-card info">
        <div class="metric-icon">
          <TrophyOutlined />
        </div>
        <div class="metric-content">
          <div class="metric-value">{{ loading ? '--' : (dashboardOverview?.metrics?.completedThisMonth || stats?.overview?.completed || 0) }}</div>
          <div class="metric-label">本月完成</div>
          <div class="metric-trend" v-if="!loading && dashboardOverview?.trends?.completedTrend" :class="getTrendClass(dashboardOverview.trends.completedTrend.direction)">
            <CaretUpOutlined v-if="dashboardOverview.trends.completedTrend.direction === 'up'" />
            <CaretDownOutlined v-else-if="dashboardOverview.trends.completedTrend.direction === 'down'" />
            <span>{{ formatTrend(dashboardOverview.trends.completedTrend.value, dashboardOverview.trends.completedTrend.direction) }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- 主要内容区域 -->
    <div class="dashboard-content">
      <!-- 左侧内容列 -->
      <div class="content-left">
        <!-- 我的任务面板 -->
        <div class="dashboard-panel">
          <div class="panel-header">
            <div class="panel-title">
              <UserOutlined />
              <span>我的任务</span>
            </div>
            <div class="panel-actions">
              <router-link to="/tasks">
                <a-button type="text" size="small">查看全部</a-button>
              </router-link>
            </div>
          </div>
          
          <div class="panel-content">
            <div v-if="loading" class="loading-state">
              <a-spin size="large" />
              <p>正在加载任务数据...</p>
            </div>
            <div v-else-if="myTasks.length === 0" class="empty-state">
              <a-empty description="暂无分配给您的任务">
                <a-button type="primary" @click="$router.push('/tasks/create')">
                  创建第一个任务
                </a-button>
              </a-empty>
            </div>
            <div v-else class="task-list">
              <div
                v-for="task in myTasks.slice(0, 5)"
                :key="task.id"
                class="task-item-enhanced"
              >
                <div class="task-priority" :class="getPriorityClass('medium')"></div>
                <div class="task-details">
                  <div class="task-title">{{ task.title }}</div>
                  <div class="task-meta">
                    <span class="task-location">
                      <EnvironmentOutlined />
                      {{ task.location }}
                    </span>
                    <span class="task-time">
                      <ClockCircleOutlined />
                      {{ formatTime(task.createdAt) }}
                    </span>
                  </div>
                </div>
                <div class="task-status">
                  <a-tag :color="getStatusColor(task.status)" class="status-tag">
                    {{ getStatusText(task.status) }}
                  </a-tag>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- 系统状态面板 -->
        <div class="dashboard-panel">
          <div class="panel-header">
            <div class="panel-title">
              <MonitorOutlined />
              <span>系统状态</span>
            </div>
          </div>
          
          <div class="panel-content">
            <div class="system-stats">
              <div class="system-stat-item">
                <div class="stat-icon" :class="getSystemStatusClass(systemInfo?.systemStatus)">
                  <CheckCircleOutlined v-if="systemInfo?.systemStatus === 'healthy'" />
                  <CloseCircleOutlined v-else />
                </div>
                <div class="stat-info">
                  <div class="stat-label">系统状态</div>
                  <div class="stat-value" :class="getSystemStatusClass(systemInfo?.systemStatus)">
                    {{ loading ? '--' : getSystemStatusText(systemInfo?.systemStatus) }}
                  </div>
                </div>
              </div>
              
              <div class="system-stat-item">
                <div class="stat-icon">
                  <TeamOutlined />
                </div>
                <div class="stat-info">
                  <div class="stat-label">在线用户</div>
                  <div class="stat-value">{{ loading ? '--' : `${systemInfo?.onlineUsers || 0} 人` }}</div>
                </div>
              </div>
              
              <div class="system-stat-item">
                <div class="stat-icon">
                  <DatabaseOutlined />
                </div>
                <div class="stat-info">
                  <div class="stat-label">数据同步</div>
                  <div class="stat-value">{{ loading ? '--' : formatSyncTime(systemInfo?.lastDataSync) }}</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 右侧内容列 -->
      <div class="content-right">
        <!-- 最近活动面板 -->
        <div class="dashboard-panel">
          <div class="panel-header">
            <div class="panel-title">
              <BellOutlined />
              <span>最近活动</span>
            </div>
            <div class="panel-actions">
              <a-button type="text" size="small">查看全部</a-button>
            </div>
          </div>
          
          <div class="panel-content">
            <div v-if="loading" class="loading-state">
              <a-spin size="large" />
              <p>正在加载活动数据...</p>
            </div>
            <div v-else-if="recentActivities.length === 0" class="empty-state">
              <a-empty description="暂无最近活动">
                <span>等待系统活动数据...</span>
              </a-empty>
            </div>
            <div v-else class="activity-timeline">
              <div
                v-for="activity in recentActivities"
                :key="activity.id"
                class="activity-item"
              >
                <div class="activity-dot" :class="activity.priority"></div>
                <div class="activity-content">
                  <div class="activity-title">{{ activity.title }}</div>
                  <div class="activity-desc">{{ activity.description }}</div>
                  <div class="activity-time">{{ formatTime(activity.createdAt) }}</div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- 快速操作面板 -->
        <div class="dashboard-panel">
          <div class="panel-header">
            <div class="panel-title">
              <ThunderboltOutlined />
              <span>快速操作</span>
            </div>
          </div>
          
          <div class="panel-content">
            <div class="quick-actions-grid">
              <div class="quick-action-item" @click="$router.push('/tasks/create')">
                <div class="action-icon primary">
                  <PlusOutlined />
                </div>
                <div class="action-text">新建任务</div>
              </div>
              
              <div class="quick-action-item" @click="$router.push('/members/import')">
                <div class="action-icon success">
                  <ImportOutlined />
                </div>
                <div class="action-text">导入数据</div>
              </div>
              
              <div class="quick-action-item" @click="$router.push('/statistics/report')">
                <div class="action-icon warning">
                  <FileTextOutlined />
                </div>
                <div class="action-text">生成报表</div>
              </div>
              
              <div class="quick-action-item" @click="$router.push('/settings')">
                <div class="action-icon info">
                  <SettingOutlined />
                </div>
                <div class="action-text">系统设置</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, h } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useTasksStore } from '@/stores/tasks'
import { api } from '@/api/client'
import type { Task, DashboardOverview, DashboardTasksResponse, DashboardActivitiesResponse } from '@/api/client'
import {
  PlusOutlined,
  ReloadOutlined,
  ProjectOutlined,
  CaretUpOutlined,
  CaretDownOutlined,
  ImportOutlined,
  UserOutlined,
  ClockCircleOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
  TrophyOutlined,
  EnvironmentOutlined,
  MonitorOutlined,
  TeamOutlined,
  DatabaseOutlined,
  BellOutlined,
  ThunderboltOutlined
} from '@ant-design/icons-vue'

const authStore = useAuthStore()
const tasksStore = useTasksStore()
const router = useRouter()

// 响应式数据
const dashboardOverview = ref<DashboardOverview | null>(null)
const myTasksData = ref<DashboardTasksResponse | null>(null)
const recentActivitiesData = ref<DashboardActivitiesResponse | null>(null)
const dashboardLoading = ref(false)

// 计算属性
const user = computed(() => authStore.user)
const stats = computed(() => tasksStore.stats)
const loading = computed(() => tasksStore.loading || dashboardLoading.value)

// 系统信息和活动数据 - 从 API 获取
const systemInfo = computed(() => {
  if (!dashboardOverview.value) {
    return {
      systemStatus: 'unknown',
      onlineUsers: 0,
      lastDataSync: null
    }
  }
  
  return {
    systemStatus: dashboardOverview.value.metrics.systemStatus,
    onlineUsers: dashboardOverview.value.systemInfo.onlineUsers,
    lastDataSync: dashboardOverview.value.systemInfo.lastDataSync
  }
})

const recentActivities = computed(() => recentActivitiesData.value?.activities || [])

// 我的任务 - 优先使用 dashboard API，回退到 store 数据
const myTasks = computed(() => {
  if (myTasksData.value?.tasks) {
    return myTasksData.value.tasks
  }
  if (!user.value) return []
  return tasksStore.getMyTasks(user.value.id)
})

// 方法
const getStatusColor = (status: string) => {
  const colors: Record<string, string> = {
    pending: 'orange',
    in_progress: 'blue',
    completed: 'green',
    cancelled: 'red'
  }
  return colors[status] || 'default'
}

const getStatusText = (status: string) => {
  const texts: Record<string, string> = {
    pending: '待处理',
    in_progress: '进行中',
    completed: '已完成',
    cancelled: '已取消'
  }
  return texts[status] || status
}

const getPriorityClass = (priority: string) => {
  return priority || 'medium'
}

const formatTime = (dateStr?: string) => {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  return date.toLocaleDateString('zh-CN')
}

const getCurrentTime = () => {
  const now = new Date()
  return now.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit', 
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

const refreshData = async () => {
  // 刷新所有数据
  await Promise.all([
    loadDashboardData(),
    tasksStore.fetchTaskStats(),
    tasksStore.fetchTasks({ pageSize: 10 })
  ])
}

// 趋势显示辅助方法
const getTrendClass = (direction: string) => {
  return direction === 'up' ? 'positive' : direction === 'down' ? 'negative' : 'neutral'
}

const formatTrend = (value: number, direction: string) => {
  const prefix = direction === 'up' ? '+' : direction === 'down' ? '' : '±'
  return `${prefix}${Math.abs(value)}%`
}

// 系统状态辅助方法
const getSystemStatusClass = (status: string) => {
  return status === 'healthy' ? 'healthy' : status === 'warning' ? 'warning' : 'error'
}

const getSystemStatusText = (status: string) => {
  const statusMap: Record<string, string> = {
    healthy: '正常运行',
    warning: '运行异常',
    error: '系统故障'
  }
  return statusMap[status] || '状态未知'
}

const formatSyncTime = (timestamp: string | null) => {
  if (!timestamp) return '未知'
  const now = new Date()
  const syncTime = new Date(timestamp)
  const diffMs = now.getTime() - syncTime.getTime()
  const diffMinutes = Math.floor(diffMs / (1000 * 60))
  
  if (diffMinutes < 1) return '刚刚'
  if (diffMinutes < 60) return `${diffMinutes} 分钟前`
  
  const diffHours = Math.floor(diffMinutes / 60)
  if (diffHours < 24) return `${diffHours} 小时前`
  
  const diffDays = Math.floor(diffHours / 24)
  return `${diffDays} 天前`
}

// Dashboard API 数据加载
const loadDashboardData = async () => {
  try {
    dashboardLoading.value = true
    
    // 并行加载三个 dashboard API
    const [overviewResult, tasksResult, activitiesResult] = await Promise.allSettled([
      api.getDashboardOverview(),
      api.getDashboardMyTasks(),
      api.getDashboardRecentActivities()
    ])
    
    // 处理概览数据
    if (overviewResult.status === 'fulfilled' && overviewResult.value.data) {
      dashboardOverview.value = overviewResult.value.data
    } else if (overviewResult.status === 'rejected') {
      console.error('Failed to load dashboard overview:', overviewResult.reason)
    }
    
    // 处理我的任务数据
    if (tasksResult.status === 'fulfilled' && tasksResult.value.data) {
      myTasksData.value = tasksResult.value.data
    } else if (tasksResult.status === 'rejected') {
      console.error('Failed to load my tasks:', tasksResult.reason)
    }
    
    // 处理最近活动数据
    if (activitiesResult.status === 'fulfilled' && activitiesResult.value.data) {
      recentActivitiesData.value = activitiesResult.value.data
    } else if (activitiesResult.status === 'rejected') {
      console.error('Failed to load recent activities:', activitiesResult.reason)
    }
    
  } catch (error) {
    console.error('Error loading dashboard data:', error)
  } finally {
    dashboardLoading.value = false
  }
}

// 生命周期
onMounted(() => {
  // 加载仪表板数据
  loadDashboardData()
  tasksStore.fetchTaskStats()
  tasksStore.fetchTasks({ pageSize: 10 })
})
</script>

<style scoped>
/* 仪表板页头区域 */
.dashboard-header {
  margin-bottom: 32px;
  padding: 0;
}

.welcome-section {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: white;
  border-radius: 12px;
  padding: 32px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.04);
  border: 1px solid #e8e9ea;
}

.welcome-text h1 {
  margin: 0 0 8px;
  font-size: 32px;
  font-weight: 600;
  color: #1a1a1a;
}

.welcome-text p {
  margin: 0;
  font-size: 16px;
  color: #666666;
}

.quick-actions {
  display: flex;
  gap: 16px;
}

/* 核心指标卡片网格 */
.metrics-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 24px;
  margin-bottom: 32px;
}

.metric-card {
  background: white;
  border-radius: 12px;
  padding: 32px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.04);
  border: 1px solid #e8e9ea;
  display: flex;
  align-items: center;
  gap: 20px;
  transition: all 0.3s ease;
  position: relative;
  overflow: hidden;
}

.metric-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(0,0,0,0.08);
}

.metric-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  width: 4px;
  height: 100%;
}

.metric-card.primary::before {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.metric-card.success::before {
  background: linear-gradient(135deg, #52c41a 0%, #389e0d 100%);
}

.metric-card.warning::before {
  background: linear-gradient(135deg, #faad14 0%, #d48806 100%);
}

.metric-card.info::before {
  background: linear-gradient(135deg, #1890ff 0%, #096dd9 100%);
}

.metric-icon {
  width: 64px;
  height: 64px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 28px;
  color: white;
}

.metric-card.primary .metric-icon {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.metric-card.success .metric-icon {
  background: linear-gradient(135deg, #52c41a 0%, #389e0d 100%);
}

.metric-card.warning .metric-icon {
  background: linear-gradient(135deg, #faad14 0%, #d48806 100%);
}

.metric-card.info .metric-icon {
  background: linear-gradient(135deg, #1890ff 0%, #096dd9 100%);
}

.metric-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.metric-value {
  font-size: 36px;
  font-weight: 700;
  color: #1a1a1a;
  line-height: 1;
}

.metric-label {
  font-size: 16px;
  color: #666666;
  font-weight: 500;
}

.metric-trend {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 14px;
  font-weight: 600;
}

.metric-trend.positive {
  color: #52c41a;
}

.metric-trend.negative {
  color: #ff4d4f;
}

/* 主内容区域双列布局 */
.dashboard-content {
  display: grid;
  grid-template-columns: 1fr 400px;
  gap: 32px;
  align-items: start;
}

.content-left,
.content-right {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

/* 仪表板面板通用样式 */
.dashboard-panel {
  background: white;
  border-radius: 12px;
  border: 1px solid #e8e9ea;
  box-shadow: 0 2px 8px rgba(0,0,0,0.04);
  overflow: hidden;
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 24px 32px;
  border-bottom: 1px solid #e8e9ea;
  background: #fafbfc;
}

.panel-title {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 18px;
  font-weight: 600;
  color: #1a1a1a;
}

.panel-title .anticon {
  font-size: 20px;
  color: #667eea;
}

.panel-actions {
  display: flex;
  gap: 8px;
}

.panel-content {
  padding: 24px 32px;
}

/* 任务列表样式 */
.loading-state,
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
  text-align: center;
  color: #8c8c8c;
}

.loading-state p {
  margin-top: 16px;
  font-size: 16px;
}

.task-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.task-item-enhanced {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 20px;
  background: #fafbfc;
  border-radius: 8px;
  border: 1px solid #e8e9ea;
  transition: all 0.3s ease;
}

.task-item-enhanced:hover {
  background: #f0f2f5;
  border-color: #d9d9d9;
  transform: translateX(4px);
}

.task-priority {
  width: 4px;
  height: 48px;
  border-radius: 2px;
}

.task-priority.high {
  background: #ff4d4f;
}

.task-priority.medium {
  background: #faad14;
}

.task-priority.low {
  background: #52c41a;
}

.task-details {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.task-title {
  font-size: 16px;
  font-weight: 500;
  color: #1a1a1a;
  margin: 0;
}

.task-meta {
  display: flex;
  gap: 16px;
  font-size: 14px;
  color: #8c8c8c;
}

.task-meta span {
  display: flex;
  align-items: center;
  gap: 4px;
}

.task-status {
  display: flex;
  align-items: center;
}

.status-tag {
  border: none;
  font-weight: 500;
  border-radius: 6px;
}

/* 系统状态面板样式 */
.system-stats {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.system-stat-item {
  display: flex;
  align-items: center;
  gap: 16px;
}

.stat-icon {
  width: 48px;
  height: 48px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f0f2f5;
  color: #8c8c8c;
  font-size: 20px;
}

.stat-icon.healthy {
  background: #f6ffed;
  color: #52c41a;
}

.stat-info {
  flex: 1;
}

.stat-label {
  font-size: 14px;
  color: #8c8c8c;
  margin-bottom: 4px;
}

.stat-value {
  font-size: 16px;
  font-weight: 600;
  color: #1a1a1a;
}

.stat-value.healthy {
  color: #52c41a;
}

/* 活动时间线样式 */
.activity-timeline {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.activity-item {
  display: flex;
  gap: 16px;
  position: relative;
}

.activity-item:not(:last-child)::after {
  content: '';
  position: absolute;
  left: 8px;
  top: 32px;
  width: 2px;
  height: calc(100% + 8px);
  background: #e8e9ea;
}

.activity-dot {
  width: 16px;
  height: 16px;
  border-radius: 50%;
  margin-top: 4px;
  position: relative;
  z-index: 1;
}

.activity-dot.primary {
  background: #667eea;
}

.activity-dot.success {
  background: #52c41a;
}

.activity-dot.warning {
  background: #faad14;
}

.activity-dot.info {
  background: #1890ff;
}

.activity-content {
  flex: 1;
}

.activity-title {
  font-size: 15px;
  font-weight: 500;
  color: #1a1a1a;
  margin-bottom: 4px;
}

.activity-desc {
  font-size: 14px;
  color: #8c8c8c;
  margin-bottom: 6px;
  line-height: 1.5;
}

.activity-time {
  font-size: 13px;
  color: #bfbfbf;
}

/* 快速操作网格 */
.quick-actions-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16px;
}

.quick-action-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  padding: 24px 16px;
  background: #fafbfc;
  border: 1px solid #e8e9ea;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s ease;
  text-align: center;
}

.quick-action-item:hover {
  background: #f0f2f5;
  border-color: #d9d9d9;
  transform: translateY(-2px);
}

.action-icon {
  width: 48px;
  height: 48px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
  color: white;
}

.action-icon.primary {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.action-icon.success {
  background: linear-gradient(135deg, #52c41a 0%, #389e0d 100%);
}

.action-icon.warning {
  background: linear-gradient(135deg, #faad14 0%, #d48806 100%);
}

.action-icon.info {
  background: linear-gradient(135deg, #1890ff 0%, #096dd9 100%);
}

.action-text {
  font-size: 14px;
  font-weight: 500;
  color: #1a1a1a;
}

/* 响应式优化 */
@media (max-width: 1200px) {
  .dashboard-content {
    grid-template-columns: 1fr;
    gap: 24px;
  }
  
  .content-right {
    order: -1;
  }
  
  .metrics-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 768px) {
  .welcome-section {
    flex-direction: column;
    gap: 20px;
    text-align: center;
  }
  
  .metrics-grid {
    grid-template-columns: 1fr;
  }
  
  .panel-header {
    padding: 20px;
  }
  
  .panel-content {
    padding: 20px;
  }
}
</style>