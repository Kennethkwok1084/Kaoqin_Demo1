<template>
  <div class="statistics-report">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-left">
        <h1 class="page-title">统计报表</h1>
        <p class="page-description">数据分析、图表展示和报表生成</p>
      </div>
      <div class="header-actions">
        <el-button type="primary" :icon="Plus" @click="showReportDialog = true">
          生成报表
        </el-button>
        <el-button :icon="Download" @click="handleExport"> 导出数据 </el-button>
        <el-button :icon="Refresh" @click="refreshData" :loading="refreshing">
          刷新
        </el-button>
      </div>
    </div>

    <!-- 统计概览 -->
    <div class="overview-section">
      <el-row :gutter="20">
        <el-col :span="6">
          <el-card class="overview-card">
            <div class="metric-item">
              <div class="metric-icon primary">
                <el-icon><Document /></el-icon>
              </div>
              <div class="metric-content">
                <div class="metric-value">{{ overview.totalTasks }}</div>
                <div class="metric-label">总任务数</div>
                <div
                  class="metric-trend"
                  :class="getTrendClass(overview.monthlyGrowth)"
                >
                  <el-icon
                    ><CaretTop v-if="overview.monthlyGrowth > 0" /><CaretBottom
                      v-else
                  /></el-icon>
                  {{ Math.abs(overview.monthlyGrowth) }}%
                </div>
              </div>
            </div>
          </el-card>
        </el-col>

        <el-col :span="6">
          <el-card class="overview-card">
            <div class="metric-item">
              <div class="metric-icon success">
                <el-icon><User /></el-icon>
              </div>
              <div class="metric-content">
                <div class="metric-value">{{ overview.totalMembers }}</div>
                <div class="metric-label">团队成员</div>
                <div class="metric-trend positive">
                  <el-icon><TrendCharts /></el-icon>
                  {{ overview.attendanceRate }}% 出勤率
                </div>
              </div>
            </div>
          </el-card>
        </el-col>

        <el-col :span="6">
          <el-card class="overview-card">
            <div class="metric-item">
              <div class="metric-icon warning">
                <el-icon><Timer /></el-icon>
              </div>
              <div class="metric-content">
                <div class="metric-value">{{ overview.totalWorkHours }}</div>
                <div class="metric-label">总工时</div>
                <div class="metric-trend positive">
                  <el-icon><CaretTop /></el-icon>
                  {{ overview.completionRate }}% 完成率
                </div>
              </div>
            </div>
          </el-card>
        </el-col>

        <el-col :span="6">
          <el-card class="overview-card">
            <div class="metric-item">
              <div class="metric-icon info">
                <el-icon><TrendCharts /></el-icon>
              </div>
              <div class="metric-content">
                <div class="metric-value">{{ overview.efficiencyScore }}</div>
                <div class="metric-label">效率评分</div>
                <div class="metric-trend positive">
                  <el-icon><Star /></el-icon>
                  优秀
                </div>
              </div>
            </div>
          </el-card>
        </el-col>
      </el-row>
    </div>

    <!-- 筛选器 -->
    <div class="filters-section">
      <el-card class="filter-card">
        <div class="filters-row">
          <div class="filter-item">
            <label>时间范围：</label>
            <el-date-picker
              v-model="dateRange"
              type="daterange"
              range-separator="至"
              start-placeholder="开始日期"
              end-placeholder="结束日期"
              format="YYYY-MM-DD"
              value-format="YYYY-MM-DD"
              @change="handleFilterChange"
              style="width: 300px"
            />
          </div>

          <!-- 部门选择已移除，专注于单一团队管理 -->

          <div class="filter-item">
            <label>成员：</label>
            <el-select
              v-model="filters.members"
              multiple
              placeholder="选择成员"
              clearable
              filterable
              @change="handleFilterChange"
              style="width: 200px"
            >
              <el-option
                v-for="member in memberOptions"
                :key="member.id"
                :label="member.name"
                :value="member.id"
              />
            </el-select>
          </div>

          <div class="filter-item">
            <label>快捷选择：</label>
            <el-radio-group v-model="quickFilter" @change="handleQuickFilter">
              <el-radio-button label="today">今日</el-radio-button>
              <el-radio-button label="week">本周</el-radio-button>
              <el-radio-button label="month">本月</el-radio-button>
              <el-radio-button label="quarter">本季度</el-radio-button>
            </el-radio-group>
          </div>
        </div>
      </el-card>
    </div>

    <!-- 图表展示区域 -->
    <div class="charts-section">
      <el-row :gutter="20">
        <!-- 任务完成趋势 -->
        <el-col :span="12">
          <el-card class="chart-card">
            <template #header>
              <div class="card-header">
                <span>任务完成趋势</span>
                <el-dropdown @command="handleChartAction">
                  <el-button type="primary" link>
                    <el-icon><MoreFilled /></el-icon>
                  </el-button>
                  <template #dropdown>
                    <el-dropdown-menu>
                      <el-dropdown-item command="export-chart-1"
                        >导出图表</el-dropdown-item
                      >
                      <el-dropdown-item command="fullscreen-1"
                        >全屏查看</el-dropdown-item
                      >
                      <el-dropdown-item command="refresh-1"
                        >刷新数据</el-dropdown-item
                      >
                    </el-dropdown-menu>
                  </template>
                </el-dropdown>
              </div>
            </template>
            <div
              class="chart-container"
              ref="taskTrendChartRef"
              style="height: 300px"
            ></div>
          </el-card>
        </el-col>

        <!-- 任务类型分布 -->
        <el-col :span="12">
          <el-card class="chart-card">
            <template #header>
              <div class="card-header">
                <span>任务类型分布</span>
                <el-dropdown @command="handleChartAction">
                  <el-button type="primary" link>
                    <el-icon><MoreFilled /></el-icon>
                  </el-button>
                  <template #dropdown>
                    <el-dropdown-menu>
                      <el-dropdown-item command="export-chart-2"
                        >导出图表</el-dropdown-item
                      >
                      <el-dropdown-item command="fullscreen-2"
                        >全屏查看</el-dropdown-item
                      >
                      <el-dropdown-item command="refresh-2"
                        >刷新数据</el-dropdown-item
                      >
                    </el-dropdown-menu>
                  </template>
                </el-dropdown>
              </div>
            </template>
            <div
              class="chart-container"
              ref="taskTypeChartRef"
              style="height: 300px"
            ></div>
          </el-card>
        </el-col>
      </el-row>

      <el-row :gutter="20" style="margin-top: 20px">
        <!-- 考勤统计 -->
        <el-col :span="8">
          <el-card class="chart-card">
            <template #header>
              <div class="card-header">
                <span>考勤统计</span>
                <el-dropdown @command="handleChartAction">
                  <el-button type="primary" link>
                    <el-icon><MoreFilled /></el-icon>
                  </el-button>
                  <template #dropdown>
                    <el-dropdown-menu>
                      <el-dropdown-item command="export-chart-3"
                        >导出图表</el-dropdown-item
                      >
                      <el-dropdown-item command="fullscreen-3"
                        >全屏查看</el-dropdown-item
                      >
                      <el-dropdown-item command="refresh-3"
                        >刷新数据</el-dropdown-item
                      >
                    </el-dropdown-menu>
                  </template>
                </el-dropdown>
              </div>
            </template>
            <div
              class="chart-container"
              ref="attendanceChartRef"
              style="height: 250px"
            ></div>
          </el-card>
        </el-col>

        <!-- 工时分布 -->
        <el-col :span="8">
          <el-card class="chart-card">
            <template #header>
              <div class="card-header">
                <span>工时分布</span>
                <el-dropdown @command="handleChartAction">
                  <el-button type="primary" link>
                    <el-icon><MoreFilled /></el-icon>
                  </el-button>
                  <template #dropdown>
                    <el-dropdown-menu>
                      <el-dropdown-item command="export-chart-4"
                        >导出图表</el-dropdown-item
                      >
                      <el-dropdown-item command="fullscreen-4"
                        >全屏查看</el-dropdown-item
                      >
                      <el-dropdown-item command="refresh-4"
                        >刷新数据</el-dropdown-item
                      >
                    </el-dropdown-menu>
                  </template>
                </el-dropdown>
              </div>
            </template>
            <div
              class="chart-container"
              ref="workHoursChartRef"
              style="height: 250px"
            ></div>
          </el-card>
        </el-col>

        <!-- 部门对比图表已移除，专注于单一团队管理 -->
      </el-row>
    </div>

    <!-- 排行榜和数据表格 -->
    <div class="data-section">
      <el-row :gutter="20">
        <!-- 成员排行榜 -->
        <el-col :span="12">
          <el-card class="data-card">
            <template #header>
              <div class="card-header">
                <span>成员排行榜</span>
                <el-button type="primary" link @click="viewAllRankings">
                  查看全部
                </el-button>
              </div>
            </template>
            <div class="ranking-list">
              <div
                v-for="(member, index) in memberRanking"
                :key="member.memberId"
                class="ranking-item"
                :class="{ 'top-three': index < 3 }"
              >
                <div class="rank-number" :class="`rank-${index + 1}`">
                  {{ index + 1 }}
                </div>
                <el-avatar
                  :src="member.avatar"
                  :size="40"
                  :style="{
                    backgroundColor: getAvatarColor(member.memberName)
                  }"
                >
                  {{ member.memberName?.charAt(0) }}
                </el-avatar>
                <div class="member-info">
                  <div class="member-name">{{ member.memberName }}</div>
                  <!-- 部门信息已移除 -->
                </div>
                <div class="member-stats">
                  <div class="stat-item">
                    <span class="stat-value">{{ member.completedTasks }}</span>
                    <span class="stat-label">完成任务</span>
                  </div>
                  <div class="stat-item">
                    <span class="stat-value">{{ member.workHours }}h</span>
                    <span class="stat-label">工作时长</span>
                  </div>
                  <div class="stat-item">
                    <span class="stat-value">{{ member.efficiency }}%</span>
                    <span class="stat-label">效率</span>
                  </div>
                </div>
                <div
                  class="rank-change"
                  :class="getRankChangeClass(member.change)"
                >
                  <el-icon>
                    <CaretTop v-if="member.change > 0" />
                    <CaretBottom v-else-if="member.change < 0" />
                    <Minus v-else />
                  </el-icon>
                  {{ Math.abs(member.change) }}
                </div>
              </div>
            </div>
          </el-card>
        </el-col>

        <!-- 团队汇总统计 -->
        <el-col :span="12">
          <el-card class="data-card">
            <template #header>
              <div class="card-header">
                <span>团队汇总</span>
                <el-button type="primary" link @click="viewTeamDetails">
                  详细分析
                </el-button>
              </div>
            </template>
            <div class="team-summary">
              <div class="summary-item">
                <span class="summary-label">团队人数：</span>
                <span class="summary-value">{{ overview.totalMembers }}人</span>
              </div>
              <div class="summary-item">
                <span class="summary-label">总完成任务：</span>
                <span class="summary-value">{{ overview.totalTasks }}个</span>
              </div>
              <div class="summary-item">
                <span class="summary-label">总工作时长：</span>
                <span class="summary-value"
                  >{{ overview.totalWorkHours }}h</span
                >
              </div>
              <div class="summary-item">
                <span class="summary-label">团队效率评分：</span>
                <span class="summary-value"
                  >{{ overview.efficiencyScore }}分</span
                >
              </div>
            </div>
          </el-card>
        </el-col>
      </el-row>
    </div>

    <!-- 对话框 -->
    <ReportGenerateDialog
      :visible="showReportDialog"
      @update:visible="showReportDialog = $event"
      @success="handleReportSuccess"
    />

    <ChartFullScreenDialog
      :visible="showFullScreenDialog"
      :chart-config="fullScreenChartConfig"
      :chart-title="fullScreenChartConfig?.title || '图表'"
      @update:visible="showFullScreenDialog = $event"
    />

    <ExportDataDialog
      :visible="showExportDialog"
      @update:visible="showExportDialog = $event"
      @success="handleExportSuccess"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, nextTick, onUnmounted } from 'vue'
import { ElMessage } from 'element-plus'
import {
  Plus,
  Download,
  Refresh,
  Document,
  User,
  Timer,
  TrendCharts,
  Star,
  CaretTop,
  CaretBottom,
  Minus,
  MoreFilled
} from '@element-plus/icons-vue'
import * as echarts from 'echarts'
import { statisticsApi } from '@/api/statistics'
import {
  validateChartData,
  getDefaultPieChartData,
  getDefaultLineChartData,
  formatApiResponse
} from '@/utils/chartDataValidator'
import type {
  StatisticsOverview,
  StatisticsFilters,
  MemberRankingItem,
  DepartmentStatsItem
} from '@/types/statistics'
import { getMonthRange, getWeekRange, getQuarterRange } from '@/utils/date'
import ReportGenerateDialog from '@/components/statistics/ReportGenerateDialog.vue'
import ChartFullScreenDialog from '@/components/statistics/ChartFullScreenDialog.vue'
import ExportDataDialog from '@/components/statistics/ExportDataDialog.vue'

// 响应式数据
const refreshing = ref(false)
const showReportDialog = ref(false)
const showFullScreenDialog = ref(false)
const showExportDialog = ref(false)
const fullScreenChartConfig = ref<any>({
  title: '',
  data: null,
  type: 'line'
})

// 图表引用
const taskTrendChartRef = ref<HTMLElement>()
const taskTypeChartRef = ref<HTMLElement>()
const attendanceChartRef = ref<HTMLElement>()
const workHoursChartRef = ref<HTMLElement>()
const departmentChartRef = ref<HTMLElement>()

// 图表实例
let taskTrendChart: echarts.ECharts | null = null
let taskTypeChart: echarts.ECharts | null = null
let attendanceChart: echarts.ECharts | null = null
let workHoursChart: echarts.ECharts | null = null
let departmentChart: echarts.ECharts | null = null

// 数据
const overview = reactive<StatisticsOverview>({
  totalMembers: 0,
  totalTasks: 0,
  totalAttendance: 0,
  totalWorkHours: 0,
  completionRate: 0,
  attendanceRate: 0,
  efficiencyScore: 0,
  monthlyGrowth: 0
})

const memberRanking = ref<MemberRankingItem[]>([])
const departmentStats = ref<DepartmentStatsItem[]>([])

// 筛选器
const dateRange = ref<[string, string]>(getMonthRange())
const quickFilter = ref('month')
const filters = reactive<StatisticsFilters>({
  departments: [],
  members: []
})

const memberOptions = ref<{ id: number; name: string }[]>([])

// 方法
const loadOverviewData = async () => {
  try {
    const data = await statisticsApi.getOverview({
      dateRange: dateRange.value,
      ...filters
    })
    Object.assign(overview, data)
  } catch (error) {
    console.error('加载概览数据失败:', error)
    ElMessage.error('加载概览数据失败')
  }
}

const loadTaskTrendChart = async () => {
  if (!taskTrendChartRef.value) return

  try {
    const apiResponse = await statisticsApi.getChartData({
      type: 'line',
      metric: 'task_completion_trend',
      filters: { dateRange: dateRange.value, ...filters }
    })

    const data = validateChartData(
      formatApiResponse(apiResponse),
      getDefaultLineChartData()
    )

    if (!taskTrendChart) {
      taskTrendChart = echarts.init(taskTrendChartRef.value)
    }

    const option = {
      title: {
        show: false
      },
      tooltip: {
        trigger: 'axis',
        axisPointer: {
          type: 'cross'
        }
      },
      legend: {
        data: data.datasets.map(d => d.label)
      },
      grid: {
        left: '3%',
        right: '4%',
        bottom: '3%',
        containLabel: true
      },
      xAxis: {
        type: 'category',
        boundaryGap: false,
        data: data.labels
      },
      yAxis: {
        type: 'value'
      },
      series: data.datasets.map(dataset => ({
        name: dataset.label,
        type: 'line',
        data: dataset.data,
        smooth: true,
        lineStyle: {
          color: dataset.borderColor || '#5470c6'
        },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: (dataset.borderColor || '#5470c6') + '40' },
            { offset: 1, color: (dataset.borderColor || '#5470c6') + '00' }
          ])
        }
      }))
    }

    taskTrendChart.setOption(option)
  } catch (error) {
    console.error('加载任务趋势图失败:', error)
    // 加载失败时显示默认数据
    const defaultData = getDefaultLineChartData()
    if (taskTrendChart) {
      const defaultOption = {
        title: { show: false },
        tooltip: { trigger: 'axis' },
        legend: { data: defaultData.datasets.map(d => d.label) },
        xAxis: { type: 'category', data: defaultData.labels },
        yAxis: { type: 'value' },
        series: defaultData.datasets.map(dataset => ({
          name: dataset.label,
          type: 'line',
          data: dataset.data,
          smooth: true
        }))
      }
      taskTrendChart.setOption(defaultOption)
    }
  }
}

const loadTaskTypeChart = async () => {
  if (!taskTypeChartRef.value) return

  try {
    const apiResponse = await statisticsApi.getChartData({
      type: 'pie',
      metric: 'task_type_distribution',
      filters: { dateRange: dateRange.value, ...filters }
    })

    const data = validateChartData(
      formatApiResponse(apiResponse),
      getDefaultPieChartData()
    )

    if (!taskTypeChart) {
      taskTypeChart = echarts.init(taskTypeChartRef.value)
    }

    const option = {
      tooltip: {
        trigger: 'item',
        formatter: '{a} <br/>{b}: {c} ({d}%)'
      },
      legend: {
        orient: 'vertical',
        left: 'left',
        data: data.labels
      },
      series: [
        {
          name: '任务类型',
          type: 'pie',
          radius: ['50%', '70%'],
          center: ['60%', '50%'],
          avoidLabelOverlap: false,
          label: {
            show: false,
            position: 'center'
          },
          emphasis: {
            label: {
              show: true,
              fontSize: '18',
              fontWeight: 'bold'
            }
          },
          labelLine: {
            show: false
          },
          data: data.labels.map((label, index) => ({
            value: data.datasets[0].data[index],
            name: label,
            itemStyle: {
              color: data.datasets[0].backgroundColor?.[index]
            }
          }))
        }
      ]
    }

    taskTypeChart.setOption(option)
  } catch (error) {
    console.error('加载任务类型图失败:', error)
  }
}

const loadAttendanceChart = async () => {
  if (!attendanceChartRef.value) return

  try {
    const data = await statisticsApi.getChartData({
      type: 'doughnut',
      metric: 'attendance_distribution',
      filters: { dateRange: dateRange.value, ...filters }
    })

    if (!attendanceChart) {
      attendanceChart = echarts.init(attendanceChartRef.value)
    }

    const option = {
      tooltip: {
        trigger: 'item'
      },
      series: [
        {
          name: '考勤统计',
          type: 'pie',
          radius: ['40%', '70%'],
          center: ['50%', '50%'],
          data: data.labels.map((label, index) => ({
            value: data.datasets[0].data[index],
            name: label,
            itemStyle: {
              color: data.datasets[0].backgroundColor?.[index]
            }
          }))
        }
      ]
    }

    attendanceChart.setOption(option)
  } catch (error) {
    console.error('加载考勤图失败:', error)
  }
}

const loadWorkHoursChart = async () => {
  if (!workHoursChartRef.value) return

  try {
    const data = await statisticsApi.getChartData({
      type: 'bar',
      metric: 'work_hours_distribution',
      filters: { dateRange: dateRange.value, ...filters }
    })

    if (!workHoursChart) {
      workHoursChart = echarts.init(workHoursChartRef.value)
    }

    const option = {
      tooltip: {
        trigger: 'axis'
      },
      xAxis: {
        type: 'category',
        data: data.labels
      },
      yAxis: {
        type: 'value'
      },
      series: data.datasets.map(dataset => ({
        name: dataset.label,
        type: 'bar',
        data: dataset.data,
        itemStyle: {
          color: dataset.backgroundColor
        }
      }))
    }

    workHoursChart.setOption(option)
  } catch (error) {
    console.error('加载工时图失败:', error)
  }
}

const loadDepartmentChart = async () => {
  if (!departmentChartRef.value) return

  try {
    const data = await statisticsApi.getChartData({
      type: 'radar',
      metric: 'department_comparison',
      filters: { dateRange: dateRange.value, ...filters }
    })

    if (!departmentChart) {
      departmentChart = echarts.init(departmentChartRef.value)
    }

    const option = {
      tooltip: {},
      radar: {
        indicator: data.labels.map(label => ({ name: label, max: 100 }))
      },
      series: [
        {
          name: '部门对比',
          type: 'radar',
          data: data.datasets.map(dataset => ({
            value: dataset.data,
            name: dataset.label,
            areaStyle: {
              color: dataset.backgroundColor + '40'
            }
          }))
        }
      ]
    }

    departmentChart.setOption(option)
  } catch (error) {
    console.error('加载部门对比图失败:', error)
  }
}

const loadRankingData = async () => {
  try {
    const data = await statisticsApi.getRankingData({
      type: 'members',
      metric: 'comprehensive_score',
      period_start: dateRange.value[0],
      period_end: dateRange.value[1],
      limit: 10
    })
    memberRanking.value = data
  } catch (error) {
    console.error('加载排行榜数据失败:', error)
  }
}

const loadDepartmentStats = async () => {
  try {
    const stats = await statisticsApi.getAttendanceStatistics({
      start_date: dateRange.value[0],
      end_date: dateRange.value[1],
      ...filters
    })
    departmentStats.value = stats.departmentStats
  } catch (error) {
    console.error('加载部门统计失败:', error)
  }
}

const refreshData = async () => {
  refreshing.value = true
  try {
    await Promise.all([
      loadOverviewData(),
      loadTaskTrendChart(),
      loadTaskTypeChart(),
      loadAttendanceChart(),
      loadWorkHoursChart(),
      loadDepartmentChart(),
      loadRankingData(),
      loadDepartmentStats()
    ])
    ElMessage.success('数据刷新成功')
  } catch (error) {
    console.error('刷新数据失败:', error)
    ElMessage.error('刷新数据失败')
  } finally {
    refreshing.value = false
  }
}

const handleFilterChange = () => {
  nextTick(() => {
    refreshData()
  })
}

const viewTeamDetails = () => {
  ElMessage.info('团队详细分析功能开发中')
}

const handleQuickFilter = (value: string | number | boolean | undefined) => {
  if (typeof value !== 'string') return
  switch (value) {
    case 'today': {
      const today = new Date().toISOString().split('T')[0]
      dateRange.value = [today, today]
      break
    }
    case 'week':
      dateRange.value = getWeekRange()
      break
    case 'month':
      dateRange.value = getMonthRange()
      break
    case 'quarter':
      dateRange.value = getQuarterRange()
      break
  }
  handleFilterChange()
}

const handleChartAction = (command: string) => {
  const [action, chartId] = command.split('-')

  switch (action) {
    case 'export':
      handleExportChart(chartId)
      break
    case 'fullscreen':
      handleFullScreen(chartId)
      break
    case 'refresh':
      handleRefreshChart(chartId)
      break
  }
}

const handleExportChart = async (chartId: string) => {
  try {
    const blob = await statisticsApi.exportChart({
      type: 'task_trend',
      metric: 'completion',
      format: 'png',
      width: 800,
      height: 400,
      filters: { dateRange: dateRange.value, ...filters }
    })

    // 创建下载链接
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `chart_${chartId}_${new Date().toISOString().split('T')[0]}.png`
    document.body.appendChild(a)
    a.click()
    window.URL.revokeObjectURL(url)
    document.body.removeChild(a)

    ElMessage.success('图表导出成功')
  } catch (error) {
    console.error('导出图表失败:', error)
    ElMessage.error('导出图表失败')
  }
}

// eslint-disable-next-line @typescript-eslint/no-unused-vars
const handleFullScreen = (_chartId: string) => {
  // TODO: 实现全屏查看
  ElMessage.info('全屏功能开发中...')
}

const handleRefreshChart = (chartId: string) => {
  // 根据图表ID刷新对应图表
  switch (chartId) {
    case '1':
      loadTaskTrendChart()
      break
    case '2':
      loadTaskTypeChart()
      break
    case '3':
      loadAttendanceChart()
      break
    case '4':
      loadWorkHoursChart()
      break
    case '5':
      loadDepartmentChart()
      break
  }
}

const handleExport = () => {
  showExportDialog.value = true
}

const handleReportSuccess = () => {
  ElMessage.success('报表生成成功')
}

const handleExportSuccess = () => {
  ElMessage.success('数据导出成功')
}

const viewAllRankings = () => {
  // TODO: 跳转到详细排行榜页面
  ElMessage.info('详细排行榜功能开发中...')
}

// 工具方法
const getTrendClass = (value: number) => {
  return value > 0 ? 'positive' : value < 0 ? 'negative' : 'neutral'
}

const getRankChangeClass = (change: number) => {
  return change > 0 ? 'rank-up' : change < 0 ? 'rank-down' : 'rank-same'
}

const getAvatarColor = (name: string) => {
  const colors = ['#409EFF', '#67C23A', '#E6A23C', '#F56C6C', '#909399']
  const hash =
    name?.split('').reduce((acc, char) => acc + char.charCodeAt(0), 0) || 0
  return colors[hash % colors.length]
}

// 处理窗口大小变化
const handleResize = () => {
  taskTrendChart?.resize()
  taskTypeChart?.resize()
  attendanceChart?.resize()
  workHoursChart?.resize()
  departmentChart?.resize()
}

// 生命周期
onMounted(() => {
  nextTick(() => {
    refreshData()
    window.addEventListener('resize', handleResize)
  })
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  taskTrendChart?.dispose()
  taskTypeChart?.dispose()
  attendanceChart?.dispose()
  workHoursChart?.dispose()
  departmentChart?.dispose()
})
</script>

<style scoped lang="scss">
@use '@/styles/variables.scss' as *;
@use '@/styles/mixins.scss' as *;

.statistics-report {
  padding: 24px;

  .page-header {
    @include flex-between;
    margin-bottom: 24px;

    .header-left {
      .page-title {
        font-size: $font-size-title;
        font-weight: 600;
        margin: 0 0 8px 0;
        color: $text-color-primary;
      }

      .page-description {
        color: $text-color-regular;
        margin: 0;
      }
    }

    .header-actions {
      display: flex;
      gap: 12px;
    }
  }

  .overview-section {
    margin-bottom: 24px;

    .overview-card {
      height: 120px;

      .metric-item {
        @include flex-start;
        gap: 16px;
        height: 100%;

        .metric-icon {
          width: 60px;
          height: 60px;
          border-radius: 12px;
          @include flex-center;
          color: white;

          &.primary {
            background: linear-gradient(135deg, $primary-color, #66b2ff);
          }
          &.success {
            background: linear-gradient(135deg, $success-color, #85ce61);
          }
          &.warning {
            background: linear-gradient(135deg, $warning-color, #eebe77);
          }
          &.info {
            background: linear-gradient(135deg, $info-color, #a6a9ad);
          }
        }

        .metric-content {
          flex: 1;

          .metric-value {
            font-size: 28px;
            font-weight: bold;
            color: $text-color-primary;
            margin-bottom: 4px;
          }

          .metric-label {
            color: $text-color-regular;
            font-size: 14px;
            margin-bottom: 8px;
          }

          .metric-trend {
            display: flex;
            align-items: center;
            gap: 4px;
            font-size: 12px;

            &.positive {
              color: $success-color;
            }
            &.negative {
              color: $danger-color;
            }
            &.neutral {
              color: $text-color-secondary;
            }
          }
        }
      }
    }
  }

  .filters-section {
    margin-bottom: 24px;

    .filter-card {
      .filters-row {
        display: flex;
        align-items: center;
        gap: 24px;
        flex-wrap: wrap;

        .filter-item {
          display: flex;
          align-items: center;
          gap: 8px;

          label {
            font-size: 14px;
            color: $text-color-regular;
            white-space: nowrap;
          }
        }
      }
    }
  }

  .charts-section {
    margin-bottom: 24px;

    .chart-card {
      .card-header {
        @include flex-between;
        align-items: center;
      }

      .chart-container {
        width: 100%;
      }
    }
  }

  .data-section {
    .data-card {
      .card-header {
        @include flex-between;
        align-items: center;
        margin-bottom: 16px;
      }

      .ranking-list {
        .ranking-item {
          @include flex-start;
          gap: 16px;
          padding: 16px 0;
          border-bottom: 1px solid $border-color-lighter;

          &:last-child {
            border-bottom: none;
          }

          &.top-three {
            background: linear-gradient(90deg, #fff7e6, transparent);
            margin: 0 -16px;
            padding: 16px;
            border-radius: 8px;
          }

          .rank-number {
            width: 30px;
            height: 30px;
            border-radius: 50%;
            @include flex-center;
            font-weight: bold;
            color: white;

            &.rank-1 {
              background: linear-gradient(135deg, #ffd700, #ffa500);
            }
            &.rank-2 {
              background: linear-gradient(135deg, #c0c0c0, #a0a0a0);
            }
            &.rank-3 {
              background: linear-gradient(135deg, #cd7f32, #b8860b);
            }
          }

          .member-info {
            flex: 1;

            .member-name {
              font-weight: 500;
              color: $text-color-primary;
              margin-bottom: 4px;
            }

            .member-dept {
              font-size: 12px;
              color: $text-color-secondary;
            }
          }

          .member-stats {
            display: flex;
            gap: 16px;

            .stat-item {
              text-align: center;

              .stat-value {
                display: block;
                font-weight: 600;
                color: $primary-color;
                margin-bottom: 2px;
              }

              .stat-label {
                font-size: 11px;
                color: $text-color-secondary;
              }
            }
          }

          .rank-change {
            display: flex;
            align-items: center;
            gap: 4px;
            font-size: 12px;

            &.rank-up {
              color: $success-color;
            }
            &.rank-down {
              color: $danger-color;
            }
            &.rank-same {
              color: $text-color-secondary;
            }
          }
        }
      }

      .progress-text {
        font-size: 12px;
        color: $text-color-secondary;
        margin-left: 8px;
      }
    }
  }

  @include respond-to(sm) {
    padding: 16px;

    .overview-section {
      .overview-card {
        height: auto;

        .metric-item {
          flex-direction: column;
          text-align: center;
          gap: 12px;
        }
      }
    }

    .filters-section {
      .filter-card {
        .filters-row {
          flex-direction: column;
          align-items: stretch;
          gap: 16px;

          .filter-item {
            flex-direction: column;
            align-items: flex-start;
            gap: 8px;
          }
        }
      }
    }

    .data-section {
      .ranking-list {
        .ranking-item {
          .member-stats {
            flex-direction: column;
            gap: 8px;
          }
        }
      }
    }
  }
}
</style>
