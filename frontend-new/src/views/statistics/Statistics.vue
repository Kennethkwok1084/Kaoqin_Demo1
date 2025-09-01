<template>
  <div class="desktop-statistics">
    <div class="page-header">
      <div class="header-content">
        <div class="header-text">
          <h1>统计报表</h1>
          <p>查看团队工作数据分析和统计报表</p>
        </div>
        <div class="header-actions">
          <a-button type="primary" :icon="h(DownloadOutlined)" @click="exportReport">
            导出报表
          </a-button>
          <a-button :icon="h(BarChartOutlined)" @click="$router.push('/statistics/report')">
            详细报表
          </a-button>
          <a-button :icon="h(ReloadOutlined)" @click="refreshStatistics" :loading="loading">
            刷新
          </a-button>
        </div>
      </div>
    </div>
    
    <!-- 统计卡片 -->
    <div class="statistics-cards">
      <div class="stats-row">
        <a-card class="stats-card primary">
          <a-statistic
            title="总任务数"
            :value="statistics.totalTasks"
            :value-style="{ color: '#1890ff', fontSize: '32px', fontWeight: '600' }"
          >
            <template #prefix>
              <AppstoreOutlined style="color: #1890ff" />
            </template>
          </a-statistic>
          <div class="stats-trend">
            <span class="trend-text">较上月</span>
            <span :class="`trend-value ${statistics.tasksTrend.direction}`">
              {{ statistics.tasksTrend.direction === 'up' ? '+' : '' }}{{ statistics.tasksTrend.value }}%
            </span>
          </div>
        </a-card>

        <a-card class="stats-card success">
          <a-statistic
            title="已完成"
            :value="statistics.completedTasks"
            :value-style="{ color: '#52c41a', fontSize: '32px', fontWeight: '600' }"
          >
            <template #prefix>
              <CheckCircleOutlined style="color: #52c41a" />
            </template>
          </a-statistic>
          <div class="stats-trend">
            <span class="trend-text">完成率</span>
            <span class="trend-value up">{{ statistics.completionRate }}%</span>
          </div>
        </a-card>

        <a-card class="stats-card warning">
          <a-statistic
            title="总工时"
            :value="statistics.totalWorkHours"
            suffix="小时"
            :value-style="{ color: '#fa8c16', fontSize: '32px', fontWeight: '600' }"
          >
            <template #prefix>
              <ClockCircleOutlined style="color: #fa8c16" />
            </template>
          </a-statistic>
          <div class="stats-trend">
            <span class="trend-text">平均工时</span>
            <span class="trend-value">{{ statistics.averageWorkHours }}小时</span>
          </div>
        </a-card>

        <a-card class="stats-card info">
          <a-statistic
            title="活跃成员"
            :value="statistics.activeMembers"
            :value-style="{ color: '#722ed1', fontSize: '32px', fontWeight: '600' }"
          >
            <template #prefix>
              <TeamOutlined style="color: #722ed1" />
            </template>
          </a-statistic>
          <div class="stats-trend">
            <span class="trend-text">参与率</span>
            <span class="trend-value">{{ statistics.participationRate }}%</span>
          </div>
        </a-card>
      </div>
    </div>

    <!-- 图表面板 -->
    <div class="charts-panel">
      <div class="charts-row">
        <!-- 任务完成趋势图 -->
        <a-card title="任务完成趋势" class="chart-card">
          <div class="chart-container">
            <div ref="taskTrendChart" class="chart"></div>
          </div>
        </a-card>

        <!-- 工时分布图 -->
        <a-card title="工时分布" class="chart-card">
          <div class="chart-container">
            <div ref="workHoursChart" class="chart"></div>
          </div>
        </a-card>
      </div>

      <div class="charts-row">
        <!-- 成员效率排名 -->
        <a-card title="成员效率排名" class="chart-card">
          <div class="chart-container">
            <div ref="memberRankingChart" class="chart"></div>
          </div>
        </a-card>

        <!-- 任务类型分布 -->
        <a-card title="任务类型分布" class="chart-card">
          <div class="chart-container">
            <div ref="taskTypeChart" class="chart"></div>
          </div>
        </a-card>
      </div>
    </div>

    <!-- 数据表格 -->
    <div class="data-tables">
      <a-card title="近期表现统计" class="table-card">
        <div class="table-filters">
          <a-select
            v-model:value="periodFilter"
            style="width: 120px"
            @change="handlePeriodChange"
          >
            <a-select-option value="week">本周</a-select-option>
            <a-select-option value="month">本月</a-select-option>
            <a-select-option value="quarter">本季度</a-select-option>
          </a-select>
          
          <a-select
            v-model:value="sortBy"
            style="width: 140px"
            @change="handleSortChange"
          >
            <a-select-option value="efficiency">按效率排序</a-select-option>
            <a-select-option value="tasks">按任务数排序</a-select-option>
            <a-select-option value="hours">按工时排序</a-select-option>
          </a-select>
        </div>

        <a-table
          :columns="performanceColumns"
          :data-source="performanceData"
          :loading="tableLoading"
          :pagination="{ pageSize: 10 }"
          row-key="id"
        >
          <template #efficiency="{ text }">
            <div class="efficiency-cell">
              <a-progress
                :percent="text"
                size="small"
                :stroke-color="getEfficiencyColor(text)"
              />
              <span class="efficiency-text">{{ text }}%</span>
            </div>
          </template>

          <template #trend="{ record }">
            <a-tag :color="record.trend === 'up' ? 'green' : record.trend === 'down' ? 'red' : 'blue'">
              {{ record.trend === 'up' ? '上升' : record.trend === 'down' ? '下降' : '持平' }}
            </a-tag>
          </template>
        </a-table>
      </a-card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, nextTick, h } from 'vue'
import { useRouter } from 'vue-router'
import { message } from 'ant-design-vue'
import * as echarts from 'echarts'
import * as XLSX from 'xlsx'
import dayjs from 'dayjs'
import {
  DownloadOutlined,
  BarChartOutlined,
  ReloadOutlined,
  AppstoreOutlined,
  CheckCircleOutlined,
  ClockCircleOutlined,
  TeamOutlined
} from '@ant-design/icons-vue'

const router = useRouter()

// 模拟API数据
const mockApi = {
  async getStatisticsOverview() {
    await new Promise(resolve => setTimeout(resolve, 500))
    
    return {
      success: true,
      data: {
        totalTasks: 156,
        completedTasks: 134,
        totalWorkHours: 392.5,
        activeMembers: 12,
        completionRate: 85.9,
        averageWorkHours: 2.5,
        participationRate: 92.3,
        tasksTrend: {
          value: 12.5,
          direction: 'up'
        }
      }
    }
  },

  async getChartData() {
    await new Promise(resolve => setTimeout(resolve, 300))
    
    return {
      success: true,
      data: {
        taskTrend: {
          dates: ['01-24', '01-25', '01-26', '01-27', '01-28', '01-29', '01-30'],
          completed: [8, 12, 15, 18, 14, 22, 25],
          total: [10, 15, 18, 20, 16, 25, 28]
        },
        workHours: {
          categories: ['维修任务', '监测任务', '协助任务', '其他'],
          values: [156.5, 128.3, 87.2, 20.5]
        },
        memberRanking: [
          { name: '张三', efficiency: 96.5, tasks: 28 },
          { name: '李四', efficiency: 94.2, tasks: 25 },
          { name: '王五', efficiency: 91.8, tasks: 22 },
          { name: '赵六', efficiency: 89.3, tasks: 19 },
          { name: '钱七', efficiency: 87.1, tasks: 18 }
        ],
        taskTypes: [
          { name: '维修任务', value: 68 },
          { name: '监测任务', value: 42 },
          { name: '协助任务', value: 35 },
          { name: '其他', value: 11 }
        ]
      }
    }
  },

  async getPerformanceData(params: any) {
    await new Promise(resolve => setTimeout(resolve, 400))
    
    const mockData = [
      { id: 1, memberName: '张三', tasksCompleted: 28, workHours: 72.5, efficiency: 96.5, trend: 'up' },
      { id: 2, memberName: '李四', tasksCompleted: 25, workHours: 65.2, efficiency: 94.2, trend: 'up' },
      { id: 3, memberName: '王五', tasksCompleted: 22, workHours: 58.8, efficiency: 91.8, trend: 'stable' },
      { id: 4, memberName: '赵六', tasksCompleted: 19, workHours: 52.1, efficiency: 89.3, trend: 'down' },
      { id: 5, memberName: '钱七', tasksCompleted: 18, workHours: 48.9, efficiency: 87.1, trend: 'up' },
      { id: 6, memberName: '孙八', tasksCompleted: 16, workHours: 44.3, efficiency: 85.4, trend: 'stable' },
      { id: 7, memberName: '周九', tasksCompleted: 14, workHours: 39.7, efficiency: 82.9, trend: 'down' },
      { id: 8, memberName: '吴十', tasksCompleted: 12, workHours: 35.2, efficiency: 80.1, trend: 'up' }
    ]
    
    return {
      success: true,
      data: mockData
    }
  }
}

// 响应式数据
const loading = ref(false)
const tableLoading = ref(false)
const periodFilter = ref('month')
const sortBy = ref('efficiency')

// 统计数据
const statistics = reactive({
  totalTasks: 0,
  completedTasks: 0,
  totalWorkHours: 0,
  activeMembers: 0,
  completionRate: 0,
  averageWorkHours: 0,
  participationRate: 0,
  tasksTrend: {
    value: 0,
    direction: 'up'
  }
})

// 图表数据
const chartData = ref<any>({})
const performanceData = ref<any[]>([])

// 图表实例
const taskTrendChart = ref()
const workHoursChart = ref()
const memberRankingChart = ref()
const taskTypeChart = ref()

let taskTrendChartInstance: any = null
let workHoursChartInstance: any = null
let memberRankingChartInstance: any = null
let taskTypeChartInstance: any = null

// 表格列定义
const performanceColumns = [
  {
    title: '成员姓名',
    dataIndex: 'memberName',
    key: 'memberName',
    width: 120,
    fixed: 'left'
  },
  {
    title: '完成任务',
    dataIndex: 'tasksCompleted',
    key: 'tasksCompleted',
    width: 100,
    sorter: (a: any, b: any) => a.tasksCompleted - b.tasksCompleted
  },
  {
    title: '工作时长',
    dataIndex: 'workHours',
    key: 'workHours',
    width: 100,
    customRender: ({ text }: any) => `${text} 小时`,
    sorter: (a: any, b: any) => a.workHours - b.workHours
  },
  {
    title: '工作效率',
    dataIndex: 'efficiency',
    key: 'efficiency',
    width: 180,
    slots: { customRender: 'efficiency' },
    sorter: (a: any, b: any) => a.efficiency - b.efficiency
  },
  {
    title: '趋势',
    key: 'trend',
    width: 80,
    slots: { customRender: 'trend' }
  }
]

// 方法
const getEfficiencyColor = (efficiency: number) => {
  if (efficiency >= 90) return '#52c41a'
  if (efficiency >= 80) return '#faad14'
  if (efficiency >= 70) return '#fa8c16'
  return '#ff4d4f'
}

// API 调用方法
const fetchStatisticsOverview = async () => {
  try {
    loading.value = true
    const response = await mockApi.getStatisticsOverview()
    
    if (response.success && response.data) {
      Object.assign(statistics, response.data)
    }
  } catch (error: any) {
    console.error('Fetch statistics overview error:', error)
    message.error('获取统计数据失败')
  } finally {
    loading.value = false
  }
}

const fetchChartData = async () => {
  try {
    const response = await mockApi.getChartData()
    
    if (response.success && response.data) {
      chartData.value = response.data
      await nextTick()
      initCharts()
    }
  } catch (error: any) {
    console.error('Fetch chart data error:', error)
    message.error('获取图表数据失败')
  }
}

const fetchPerformanceData = async () => {
  try {
    tableLoading.value = true
    const response = await mockApi.getPerformanceData({
      period: periodFilter.value,
      sortBy: sortBy.value
    })
    
    if (response.success && response.data) {
      performanceData.value = response.data
    }
  } catch (error: any) {
    console.error('Fetch performance data error:', error)
    message.error('获取表现数据失败')
  } finally {
    tableLoading.value = false
  }
}

// 图表初始化方法
const initCharts = () => {
  initTaskTrendChart()
  initWorkHoursChart()
  initMemberRankingChart()
  initTaskTypeChart()
}

const initTaskTrendChart = () => {
  if (!taskTrendChart.value || !chartData.value.taskTrend) return
  
  taskTrendChartInstance = echarts.init(taskTrendChart.value)
  
  const option = {
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'cross'
      }
    },
    legend: {
      data: ['已完成', '总任务']
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      data: chartData.value.taskTrend.dates
    },
    yAxis: {
      type: 'value'
    },
    series: [
      {
        name: '已完成',
        type: 'line',
        data: chartData.value.taskTrend.completed,
        smooth: true,
        itemStyle: {
          color: '#52c41a'
        },
        areaStyle: {
          opacity: 0.3
        }
      },
      {
        name: '总任务',
        type: 'line',
        data: chartData.value.taskTrend.total,
        smooth: true,
        itemStyle: {
          color: '#1890ff'
        }
      }
    ]
  }
  
  taskTrendChartInstance.setOption(option)
}

const initWorkHoursChart = () => {
  if (!workHoursChart.value || !chartData.value.workHours) return
  
  workHoursChartInstance = echarts.init(workHoursChart.value)
  
  const option = {
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'shadow'
      }
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      data: chartData.value.workHours.categories
    },
    yAxis: {
      type: 'value',
      name: '工时(小时)'
    },
    series: [
      {
        type: 'bar',
        data: chartData.value.workHours.values,
        itemStyle: {
          color: '#fa8c16'
        },
        barWidth: '60%'
      }
    ]
  }
  
  workHoursChartInstance.setOption(option)
}

const initMemberRankingChart = () => {
  if (!memberRankingChart.value || !chartData.value.memberRanking) return
  
  memberRankingChartInstance = echarts.init(memberRankingChart.value)
  
  const option = {
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'shadow'
      }
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      containLabel: true
    },
    xAxis: {
      type: 'value',
      name: '效率(%)'
    },
    yAxis: {
      type: 'category',
      data: chartData.value.memberRanking.map((item: any) => item.name)
    },
    series: [
      {
        type: 'bar',
        data: chartData.value.memberRanking.map((item: any) => item.efficiency),
        itemStyle: {
          color: '#722ed1'
        }
      }
    ]
  }
  
  memberRankingChartInstance.setOption(option)
}

const initTaskTypeChart = () => {
  if (!taskTypeChart.value || !chartData.value.taskTypes) return
  
  taskTypeChartInstance = echarts.init(taskTypeChart.value)
  
  const option = {
    tooltip: {
      trigger: 'item'
    },
    legend: {
      orient: 'vertical',
      left: 'left'
    },
    series: [
      {
        type: 'pie',
        radius: '50%',
        data: chartData.value.taskTypes,
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
  
  taskTypeChartInstance.setOption(option)
}

// 事件处理方法
const handlePeriodChange = () => {
  fetchPerformanceData()
}

const handleSortChange = () => {
  fetchPerformanceData()
}

const refreshStatistics = () => {
  fetchStatisticsOverview()
  fetchChartData()
  fetchPerformanceData()
}

const exportReport = () => {
  try {
    // 准备导出数据
    const exportData = [
      {
        '统计项目': '总任务数',
        '数值': statistics.totalTasks,
        '单位': '个',
        '备注': ''
      },
      {
        '统计项目': '已完成任务',
        '数值': statistics.completedTasks,
        '单位': '个',
        '备注': `完成率 ${statistics.completionRate}%`
      },
      {
        '统计项目': '总工时',
        '数值': statistics.totalWorkHours,
        '单位': '小时',
        '备注': `平均 ${statistics.averageWorkHours} 小时`
      },
      {
        '统计项目': '活跃成员',
        '数值': statistics.activeMembers,
        '单位': '人',
        '备注': `参与率 ${statistics.participationRate}%`
      }
    ]

    // 添加成员表现数据
    const memberPerformanceData = performanceData.value.map((item, index) => ({
      '排名': index + 1,
      '成员姓名': item.memberName,
      '完成任务': item.tasksCompleted,
      '工作时长': item.workHours,
      '工作效率': item.efficiency,
      '趋势': item.trend === 'up' ? '上升' : item.trend === 'down' ? '下降' : '持平'
    }))
    
    // 创建工作簿
    const wb = XLSX.utils.book_new()
    
    // 添加统计概览表
    const ws1 = XLSX.utils.json_to_sheet(exportData)
    XLSX.utils.book_append_sheet(wb, ws1, '统计概览')
    
    // 添加成员表现表
    const ws2 = XLSX.utils.json_to_sheet(memberPerformanceData)
    XLSX.utils.book_append_sheet(wb, ws2, '成员表现')
    
    // 生成文件名
    const fileName = `统计报表_${dayjs().format('YYYY-MM-DD')}.xlsx`
    
    // 下载文件
    XLSX.writeFile(wb, fileName)
    message.success('报表导出成功')
  } catch (error) {
    console.error('Export error:', error)
    message.error('报表导出失败')
  }
}

// 生命周期和窗口事件
onMounted(() => {
  fetchStatisticsOverview()
  fetchChartData()
  fetchPerformanceData()
})

// 窗口大小变化时重新调整图表
window.addEventListener('resize', () => {
  if (taskTrendChartInstance) taskTrendChartInstance.resize()
  if (workHoursChartInstance) workHoursChartInstance.resize()
  if (memberRankingChartInstance) memberRankingChartInstance.resize()
  if (taskTypeChartInstance) taskTypeChartInstance.resize()
})
</script>

<style scoped>
/* 桌面端统计报表界面样式 */
.desktop-statistics {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  gap: 24px;
  padding-bottom: 24px;
}

.page-header {
  background: white;
  border-radius: 12px;
  padding: 32px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.04);
  border: 1px solid #e8e9ea;
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-text h1 {
  margin: 0 0 8px;
  font-size: 28px;
  font-weight: 600;
  color: #1a1a1a;
}

.header-text p {
  margin: 0;
  font-size: 16px;
  color: #666666;
}

.header-actions {
  display: flex;
  gap: 12px;
}

/* 统计卡片样式 */
.statistics-cards {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.stats-row {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 24px;
}

.stats-card {
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.04);
  transition: transform 0.3s ease, box-shadow 0.3s ease;
  overflow: hidden;
  position: relative;
}

.stats-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 24px rgba(0,0,0,0.12);
}

.stats-card.primary {
  border-left: 4px solid #1890ff;
}

.stats-card.success {
  border-left: 4px solid #52c41a;
}

.stats-card.warning {
  border-left: 4px solid #fa8c16;
}

.stats-card.info {
  border-left: 4px solid #722ed1;
}

.stats-trend {
  margin-top: 16px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.trend-text {
  font-size: 14px;
  color: #8c8c8c;
}

.trend-value {
  font-weight: 500;
  font-size: 14px;
}

.trend-value.up {
  color: #52c41a;
}

.trend-value.down {
  color: #ff4d4f;
}

.trend-value.stable {
  color: #1890ff;
}

/* 图表面板样式 */
.charts-panel {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.charts-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 24px;
}

.chart-card {
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.04);
  border: 1px solid #e8e9ea;
}

.chart-card :deep(.ant-card-head-title) {
  font-size: 16px;
  font-weight: 600;
  color: #1a1a1a;
}

.chart-container {
  width: 100%;
  height: 320px;
  padding: 16px;
}

.chart {
  width: 100%;
  height: 100%;
}

/* 数据表格样式 */
.data-tables {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.table-card {
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.04);
  border: 1px solid #e8e9ea;
}

.table-filters {
  display: flex;
  gap: 16px;
  margin-bottom: 16px;
  padding: 16px 0;
}

.efficiency-cell {
  display: flex;
  align-items: center;
  gap: 12px;
}

.efficiency-text {
  font-weight: 500;
  min-width: 40px;
}

/* 表格样式优化 */
:deep(.ant-table-thead > tr > th) {
  background: #fafbfc;
  border-bottom: 2px solid #e8e9ea;
  font-weight: 600;
  color: #1a1a1a;
  font-size: 14px;
}

:deep(.ant-table-tbody > tr > td) {
  border-bottom: 1px solid #f0f0f0;
  padding: 16px;
}

:deep(.ant-table-tbody > tr:hover > td) {
  background: #f8f9fa;
}

/* 统计数值样式优化 */
:deep(.ant-statistic-title) {
  font-size: 16px;
  color: #8c8c8c;
  font-weight: 500;
  margin-bottom: 8px;
}

/* 标签样式优化 */
:deep(.ant-tag) {
  border: none;
  font-weight: 500;
  font-size: 12px;
  border-radius: 6px;
  padding: 2px 8px;
}

/* 响应式优化 */
@media (max-width: 1600px) {
  .stats-row {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 1200px) {
  .header-content {
    flex-direction: column;
    gap: 20px;
    text-align: center;
  }
  
  .charts-row {
    grid-template-columns: 1fr;
  }
  
  .stats-row {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 768px) {
  .page-header {
    padding: 20px;
  }
  
  .stats-row {
    grid-template-columns: 1fr;
  }
  
  .chart-container {
    height: 240px;
    padding: 8px;
  }
  
  .header-actions {
    flex-direction: column;
    width: 100%;
  }
  
  .table-filters {
    flex-direction: column;
    gap: 12px;
  }
}

@media (max-width: 480px) {
  .desktop-statistics {
    gap: 16px;
    padding-bottom: 16px;
  }
  
  .chart-container {
    height: 200px;
  }
}
</style>