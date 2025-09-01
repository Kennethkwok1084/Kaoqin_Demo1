<template>
  <div class="desktop-advanced-analytics">
    <div class="page-header">
      <div class="header-content">
        <div class="header-text">
          <h1>高级数据分析</h1>
          <p>深度分析报修数据，发现问题规律和趋势</p>
        </div>
        <div class="header-actions">
          <a-date-picker
            v-model:value="dateRange"
            type="month"
            placeholder="选择分析月份"
            @change="handleDateChange"
          />
          <a-button :icon="h(ReloadOutlined)" @click="refreshAnalytics" :loading="loading">
            刷新
          </a-button>
        </div>
      </div>
    </div>

    <div class="analytics-content">
      <!-- 第一行：区域分析 -->
      <div class="analytics-row">
        <a-col :xs="24" :lg="12">
          <a-card title="区域问题热力图" class="analytics-card">
            <div class="chart-container">
              <div ref="regionHeatmapChart" class="chart"></div>
            </div>
            <div class="chart-summary">
              <a-row :gutter="16">
                <a-col :span="8">
                  <a-statistic title="问题最多区域" :value="hotspotAnalysis.topRegion" />
                </a-col>
                <a-col :span="8">
                  <a-statistic title="问题数量" :value="hotspotAnalysis.topCount" />
                </a-col>
                <a-col :span="8">
                  <a-statistic title="占比" :value="hotspotAnalysis.percentage" suffix="%" />
                </a-col>
              </a-row>
            </div>
          </a-card>
        </a-col>

        <a-col :xs="24" :lg="12">
          <a-card title="楼栋分布统计" class="analytics-card">
            <div class="chart-container">
              <div ref="buildingChart" class="chart"></div>
            </div>
            <div class="building-ranking">
              <h4>问题频发楼栋 TOP5</h4>
              <div class="ranking-list">
                <div 
                  v-for="(item, index) in buildingRanking" 
                  :key="item.building"
                  class="ranking-item"
                >
                  <div class="ranking-badge" :class="`rank-${index + 1}`">
                    {{ index + 1 }}
                  </div>
                  <div class="ranking-content">
                    <div class="building-name">{{ item.building }}</div>
                    <div class="building-count">{{ item.count }} 个问题</div>
                  </div>
                  <div class="ranking-trend">
                    <a-tag :color="item.trend === 'up' ? 'red' : item.trend === 'down' ? 'green' : 'blue'">
                      {{ getTrendText(item.trend) }}
                    </a-tag>
                  </div>
                </div>
              </div>
            </div>
          </a-card>
        </a-col>
      </div>

      <!-- 第二行：问题类型分析 -->
      <div class="analytics-row">
        <a-col :xs="24" :lg="16">
          <a-card title="问题类型词云分析" class="analytics-card">
            <div class="chart-container large">
              <div ref="wordCloudChart" class="chart"></div>
            </div>
            <div class="wordcloud-legend">
              <h4>高频问题关键词</h4>
              <div class="keyword-tags">
                <a-tag 
                  v-for="keyword in topKeywords" 
                  :key="keyword.word"
                  :color="getKeywordColor(keyword.frequency)"
                  size="large"
                >
                  {{ keyword.word }} ({{ keyword.frequency }})
                </a-tag>
              </div>
            </div>
          </a-card>
        </a-col>

        <a-col :xs="24" :lg="8">
          <a-card title="故障类型分析" class="analytics-card">
            <div class="chart-container">
              <div ref="faultTypeChart" class="chart"></div>
            </div>
            <div class="fault-stats">
              <div class="stat-item">
                <span class="stat-label">最常见故障:</span>
                <span class="stat-value">{{ faultAnalysis.topFault }}</span>
              </div>
              <div class="stat-item">
                <span class="stat-label">占比:</span>
                <span class="stat-value">{{ faultAnalysis.topPercentage }}%</span>
              </div>
              <div class="stat-item">
                <span class="stat-label">解决率:</span>
                <span class="stat-value">{{ faultAnalysis.resolveRate }}%</span>
              </div>
            </div>
          </a-card>
        </a-col>
      </div>

      <!-- 第三行：时间趋势分析 -->
      <div class="analytics-row">
        <a-col :xs="24">
          <a-card title="时间维度分析" class="analytics-card">
            <div class="time-analysis-tabs">
              <a-tabs v-model:activeKey="timeAnalysisTab" @change="handleTimeTabChange">
                <a-tab-pane key="hourly" tab="小时分布">
                  <div class="chart-container medium">
                    <div ref="hourlyChart" class="chart"></div>
                  </div>
                </a-tab-pane>
                <a-tab-pane key="weekly" tab="星期分布">
                  <div class="chart-container medium">
                    <div ref="weeklyChart" class="chart"></div>
                  </div>
                </a-tab-pane>
                <a-tab-pane key="monthly" tab="月度趋势">
                  <div class="chart-container medium">
                    <div ref="monthlyTrendChart" class="chart"></div>
                  </div>
                </a-tab-pane>
              </a-tabs>
            </div>
          </a-card>
        </a-col>
      </div>

      <!-- 第四行：效率分析 -->
      <div class="analytics-row">
        <a-col :xs="24" :lg="14">
          <a-card title="响应时间分析" class="analytics-card">
            <div class="response-analysis">
              <div class="analysis-metrics">
                <a-row :gutter="24}>
                  <a-col :span="6">
                    <a-statistic 
                      title="平均响应时间" 
                      :value="responseAnalysis.avgResponse" 
                      suffix="分钟"
                      :value-style="{ color: '#1890ff' }"
                    />
                  </a-col>
                  <a-col :span="6">
                    <a-statistic 
                      title="平均处理时间" 
                      :value="responseAnalysis.avgProcess" 
                      suffix="小时"
                      :value-style="{ color: '#52c41a' }"
                    />
                  </a-col>
                  <a-col :span="6">
                    <a-statistic 
                      title="超时率" 
                      :value="responseAnalysis.timeoutRate" 
                      suffix="%"
                      :value-style="{ color: responseAnalysis.timeoutRate > 10 ? '#ff4d4f' : '#52c41a' }"
                    />
                  </a-col>
                  <a-col :span="6">
                    <a-statistic 
                      title="一次解决率" 
                      :value="responseAnalysis.firstTimeResolve" 
                      suffix="%"
                      :value-style="{ color: '#722ed1' }"
                    />
                  </a-col>
                </a-row>
              </div>
              <div class="chart-container medium">
                <div ref="responseTimeChart" class="chart"></div>
              </div>
            </div>
          </a-card>
        </a-col>

        <a-col :xs="24" :lg="10">
          <a-card title="满意度分析" class="analytics-card">
            <div class="satisfaction-analysis">
              <div class="satisfaction-overview">
                <div class="satisfaction-score">
                  <div class="score-circle">
                    <div class="score-text">
                      <span class="score-number">{{ satisfactionAnalysis.overallScore }}</span>
                      <span class="score-label">总体满意度</span>
                    </div>
                  </div>
                </div>
                <div class="satisfaction-breakdown">
                  <div class="breakdown-item">
                    <a-progress 
                      :percent="satisfactionAnalysis.excellent" 
                      stroke-color="#52c41a"
                      :show-info="false"
                    />
                    <span class="breakdown-label">优秀 ({{ satisfactionAnalysis.excellent }}%)</span>
                  </div>
                  <div class="breakdown-item">
                    <a-progress 
                      :percent="satisfactionAnalysis.good" 
                      stroke-color="#1890ff"
                      :show-info="false"
                    />
                    <span class="breakdown-label">良好 ({{ satisfactionAnalysis.good }}%)</span>
                  </div>
                  <div class="breakdown-item">
                    <a-progress 
                      :percent="satisfactionAnalysis.fair" 
                      stroke-color="#fa8c16"
                      :show-info="false"
                    />
                    <span class="breakdown-label">一般 ({{ satisfactionAnalysis.fair }}%)</span>
                  </div>
                  <div class="breakdown-item">
                    <a-progress 
                      :percent="satisfactionAnalysis.poor" 
                      stroke-color="#ff4d4f"
                      :show-info="false"
                    />
                    <span class="breakdown-label">差评 ({{ satisfactionAnalysis.poor }}%)</span>
                  </div>
                </div>
              </div>
            </div>
          </a-card>
        </a-col>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, nextTick, h } from 'vue'
import { message } from 'ant-design-vue'
import * as echarts from 'echarts'
import 'echarts-wordcloud'
import dayjs, { type Dayjs } from 'dayjs'
import {
  ReloadOutlined
} from '@ant-design/icons-vue'

// 响应式数据
const loading = ref(false)
const dateRange = ref<Dayjs>(dayjs())
const timeAnalysisTab = ref('hourly')

// 图表实例引用
const regionHeatmapChart = ref()
const buildingChart = ref()
const wordCloudChart = ref()
const faultTypeChart = ref()
const hourlyChart = ref()
const weeklyChart = ref()
const monthlyTrendChart = ref()
const responseTimeChart = ref()

// 分析数据
const hotspotAnalysis = reactive({
  topRegion: '学生宿舍A区',
  topCount: 45,
  percentage: 28.5
})

const buildingRanking = ref([
  { building: 'A1栋', count: 45, trend: 'up' },
  { building: 'B2栋', count: 38, trend: 'down' },
  { building: 'C3栋', count: 32, trend: 'stable' },
  { building: 'D1栋', count: 28, trend: 'up' },
  { building: 'E2栋', count: 24, trend: 'down' }
])

const topKeywords = ref([
  { word: '网络断开', frequency: 89 },
  { word: '无法上网', frequency: 76 },
  { word: '网速慢', frequency: 64 },
  { word: '连接超时', frequency: 52 },
  { word: 'WiFi异常', frequency: 43 },
  { word: '设备故障', frequency: 38 },
  { word: '端口故障', frequency: 31 },
  { word: '系统错误', frequency: 25 }
])

const faultAnalysis = reactive({
  topFault: '网络连接问题',
  topPercentage: 42.3,
  resolveRate: 94.2
})

const responseAnalysis = reactive({
  avgResponse: 18.5,
  avgProcess: 2.3,
  timeoutRate: 8.2,
  firstTimeResolve: 87.6
})

const satisfactionAnalysis = reactive({
  overallScore: 4.2,
  excellent: 68,
  good: 22,
  fair: 8,
  poor: 2
})

// 图表实例
let charts: Record<string, any> = {}

// 模拟数据
const generateMockData = () => {
  return {
    regionHeatmap: [
      ['A1栋', '1楼', 12], ['A1栋', '2楼', 8], ['A1栋', '3楼', 15],
      ['A2栋', '1楼', 6], ['A2栋', '2楼', 9], ['A2栋', '3楼', 11],
      ['B1栋', '1楼', 18], ['B1栋', '2楼', 14], ['B1栋', '3楼', 7],
      ['B2栋', '1楼', 22], ['B2栋', '2楼', 16], ['B2栋', '3楼', 19]
    ],
    buildingData: [
      { name: 'A1栋', value: 45, itemStyle: { color: '#ff6b6b' } },
      { name: 'B2栋', value: 38, itemStyle: { color: '#4ecdc4' } },
      { name: 'C3栋', value: 32, itemStyle: { color: '#45b7d1' } },
      { name: 'D1栋', value: 28, itemStyle: { color: '#96ceb4' } },
      { name: 'E2栋', value: 24, itemStyle: { color: '#feca57' } }
    ],
    wordCloudData: topKeywords.value.map(item => ({
      name: item.word,
      value: item.frequency
    })),
    faultTypes: [
      { name: '网络连接', value: 42.3 },
      { name: '硬件故障', value: 23.1 },
      { name: '软件问题', value: 18.7 },
      { name: '配置错误', value: 10.2 },
      { name: '其他', value: 5.7 }
    ],
    hourlyDistribution: {
      hours: Array.from({length: 24}, (_, i) => i + 'h'),
      counts: [2, 1, 0, 1, 3, 8, 15, 25, 32, 28, 35, 42, 38, 45, 41, 39, 36, 33, 28, 22, 18, 12, 8, 5]
    },
    weeklyDistribution: {
      days: ['周一', '周二', '周三', '周四', '周五', '周六', '周日'],
      counts: [45, 52, 48, 61, 38, 23, 18]
    },
    monthlyTrend: {
      months: ['1月', '2月', '3月', '4月', '5月', '6月'],
      reported: [89, 95, 108, 125, 142, 156],
      resolved: [86, 91, 102, 118, 134, 148]
    },
    responseTime: {
      categories: ['<15分钟', '15-30分钟', '30-60分钟', '1-2小时', '2-4小时', '>4小时'],
      values: [125, 89, 64, 32, 18, 8]
    }
  }
}

// 方法
const getTrendText = (trend: string) => {
  const textMap: Record<string, string> = {
    up: '上升',
    down: '下降',
    stable: '稳定'
  }
  return textMap[trend] || '未知'
}

const getKeywordColor = (frequency: number) => {
  if (frequency > 80) return 'red'
  if (frequency > 60) return 'orange'
  if (frequency > 40) return 'blue'
  if (frequency > 20) return 'green'
  return 'default'
}

const initCharts = () => {
  const mockData = generateMockData()
  
  nextTick(() => {
    initRegionHeatmapChart(mockData.regionHeatmap)
    initBuildingChart(mockData.buildingData)
    initWordCloudChart(mockData.wordCloudData)
    initFaultTypeChart(mockData.faultTypes)
    initHourlyChart(mockData.hourlyDistribution)
    initWeeklyChart(mockData.weeklyDistribution)
    initMonthlyTrendChart(mockData.monthlyTrend)
    initResponseTimeChart(mockData.responseTime)
  })
}

const initRegionHeatmapChart = (data: any[]) => {
  if (!regionHeatmapChart.value) return
  
  const chart = echarts.init(regionHeatmapChart.value)
  charts.regionHeatmap = chart
  
  const buildings = [...new Set(data.map(item => item[0]))]
  const floors = [...new Set(data.map(item => item[1]))]
  
  const option = {
    tooltip: {
      position: 'top',
      formatter: (params: any) => {
        const [building, floor, count] = params.data
        return `${building} ${floor}<br/>问题数量: ${count}`
      }
    },
    grid: {
      height: '50%',
      top: '10%'
    },
    xAxis: {
      type: 'category',
      data: buildings,
      splitArea: {
        show: true
      }
    },
    yAxis: {
      type: 'category',
      data: floors,
      splitArea: {
        show: true
      }
    },
    visualMap: {
      min: 0,
      max: 25,
      calculable: true,
      orient: 'horizontal',
      left: 'center',
      bottom: '15%',
      inRange: {
        color: ['#e6f7ff', '#1890ff', '#0050b3']
      }
    },
    series: [{
      name: '问题数量',
      type: 'heatmap',
      data: data.map(item => [
        buildings.indexOf(item[0]),
        floors.indexOf(item[1]),
        item[2]
      ]),
      label: {
        show: true
      },
      emphasis: {
        itemStyle: {
          shadowBlur: 10,
          shadowColor: 'rgba(0, 0, 0, 0.5)'
        }
      }
    }]
  }
  
  chart.setOption(option)
}

const initBuildingChart = (data: any[]) => {
  if (!buildingChart.value) return
  
  const chart = echarts.init(buildingChart.value)
  charts.building = chart
  
  const option = {
    tooltip: {
      trigger: 'item',
      formatter: '{a} <br/>{b}: {c} ({d}%)'
    },
    series: [{
      name: '楼栋分布',
      type: 'pie',
      radius: ['40%', '70%'],
      center: ['50%', '50%'],
      data: data,
      emphasis: {
        itemStyle: {
          shadowBlur: 10,
          shadowOffsetX: 0,
          shadowColor: 'rgba(0, 0, 0, 0.5)'
        }
      }
    }]
  }
  
  chart.setOption(option)
}

const initWordCloudChart = (data: any[]) => {
  if (!wordCloudChart.value) return
  
  const chart = echarts.init(wordCloudChart.value)
  charts.wordCloud = chart
  
  const option = {
    series: [{
      type: 'wordCloud',
      gridSize: 2,
      sizeRange: [12, 50],
      rotationRange: [-90, 90],
      shape: 'pentagon',
      width: '100%',
      height: '100%',
      drawOutOfBound: true,
      textStyle: {
        fontFamily: 'sans-serif',
        fontWeight: 'bold',
        color: () => {
          const colors = ['#ff6b6b', '#4ecdc4', '#45b7d1', '#96ceb4', '#feca57', '#ff9ff3', '#54a0ff']
          return colors[Math.floor(Math.random() * colors.length)]
        }
      },
      emphasis: {
        textStyle: {
          shadowBlur: 10,
          shadowColor: '#333'
        }
      },
      data: data
    }]
  }
  
  chart.setOption(option)
}

const initFaultTypeChart = (data: any[]) => {
  if (!faultTypeChart.value) return
  
  const chart = echarts.init(faultTypeChart.value)
  charts.faultType = chart
  
  const option = {
    tooltip: {
      trigger: 'item'
    },
    series: [{
      type: 'pie',
      radius: '70%',
      data: data,
      emphasis: {
        itemStyle: {
          shadowBlur: 10,
          shadowOffsetX: 0,
          shadowColor: 'rgba(0, 0, 0, 0.5)'
        }
      },
      label: {
        fontSize: 12
      }
    }]
  }
  
  chart.setOption(option)
}

const initHourlyChart = (data: any) => {
  if (!hourlyChart.value) return
  
  const chart = echarts.init(hourlyChart.value)
  charts.hourly = chart
  
  const option = {
    tooltip: {
      trigger: 'axis'
    },
    xAxis: {
      type: 'category',
      data: data.hours
    },
    yAxis: {
      type: 'value'
    },
    series: [{
      type: 'bar',
      data: data.counts,
      itemStyle: {
        color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
          { offset: 0, color: '#87CEEB' },
          { offset: 1, color: '#1890ff' }
        ])
      }
    }]
  }
  
  chart.setOption(option)
}

const initWeeklyChart = (data: any) => {
  if (!weeklyChart.value) return
  
  const chart = echarts.init(weeklyChart.value)
  charts.weekly = chart
  
  const option = {
    tooltip: {
      trigger: 'axis'
    },
    xAxis: {
      type: 'category',
      data: data.days
    },
    yAxis: {
      type: 'value'
    },
    series: [{
      type: 'line',
      data: data.counts,
      smooth: true,
      areaStyle: {
        opacity: 0.3
      },
      itemStyle: {
        color: '#52c41a'
      }
    }]
  }
  
  chart.setOption(option)
}

const initMonthlyTrendChart = (data: any) => {
  if (!monthlyTrendChart.value) return
  
  const chart = echarts.init(monthlyTrendChart.value)
  charts.monthlyTrend = chart
  
  const option = {
    tooltip: {
      trigger: 'axis'
    },
    legend: {
      data: ['报修数量', '解决数量']
    },
    xAxis: {
      type: 'category',
      data: data.months
    },
    yAxis: {
      type: 'value'
    },
    series: [
      {
        name: '报修数量',
        type: 'line',
        data: data.reported,
        itemStyle: { color: '#ff4d4f' }
      },
      {
        name: '解决数量',
        type: 'line',
        data: data.resolved,
        itemStyle: { color: '#52c41a' }
      }
    ]
  }
  
  chart.setOption(option)
}

const initResponseTimeChart = (data: any) => {
  if (!responseTimeChart.value) return
  
  const chart = echarts.init(responseTimeChart.value)
  charts.responseTime = chart
  
  const option = {
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'shadow'
      }
    },
    xAxis: {
      type: 'category',
      data: data.categories
    },
    yAxis: {
      type: 'value'
    },
    series: [{
      type: 'bar',
      data: data.values,
      itemStyle: {
        color: (params: any) => {
          const colors = ['#52c41a', '#1890ff', '#faad14', '#fa8c16', '#ff4d4f', '#a0a0a0']
          return colors[params.dataIndex] || '#1890ff'
        }
      }
    }]
  }
  
  chart.setOption(option)
}

const handleDateChange = () => {
  refreshAnalytics()
}

const handleTimeTabChange = (activeKey: string) => {
  timeAnalysisTab.value = activeKey
  // 根据选中的tab重新渲染相应图表
  nextTick(() => {
    if (charts[activeKey]) {
      charts[activeKey].resize()
    }
  })
}

const refreshAnalytics = () => {
  loading.value = true
  // 模拟数据加载
  setTimeout(() => {
    loading.value = false
    message.success('数据刷新完成')
    initCharts()
  }, 1000)
}

const resizeAllCharts = () => {
  Object.values(charts).forEach(chart => {
    if (chart && chart.resize) {
      chart.resize()
    }
  })
}

// 生命周期
onMounted(() => {
  initCharts()
})

// 窗口大小变化监听
window.addEventListener('resize', resizeAllCharts)
</script>

<style scoped>
.desktop-advanced-analytics {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  gap: 24px;
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
  align-items: center;
}

.analytics-content {
  display: flex;
  flex-direction: column;
  gap: 24px;
  flex: 1;
}

.analytics-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 24px;
}

.analytics-row:nth-child(3),
.analytics-row:nth-child(4) {
  grid-template-columns: 1fr;
}

.analytics-card {
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.04);
  border: 1px solid #e8e9ea;
  height: fit-content;
}

.chart-container {
  width: 100%;
  height: 300px;
}

.chart-container.medium {
  height: 350px;
}

.chart-container.large {
  height: 400px;
}

.chart {
  width: 100%;
  height: 100%;
}

.chart-summary {
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px solid #e8e9ea;
}

.building-ranking {
  margin-top: 16px;
}

.building-ranking h4 {
  margin: 0 0 16px;
  font-size: 14px;
  color: #1a1a1a;
  font-weight: 600;
}

.ranking-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.ranking-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 8px;
  background: #f8f9fa;
  border-radius: 6px;
}

.ranking-badge {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 12px;
  font-weight: 600;
}

.ranking-badge.rank-1 { background: #gold; }
.ranking-badge.rank-2 { background: #silver; }
.ranking-badge.rank-3 { background: #cd7f32; }
.ranking-badge.rank-4 { background: #1890ff; }
.ranking-badge.rank-5 { background: #722ed1; }

.ranking-content {
  flex: 1;
}

.building-name {
  font-weight: 500;
  color: #1a1a1a;
}

.building-count {
  font-size: 12px;
  color: #8c8c8c;
}

.wordcloud-legend {
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px solid #e8e9ea;
}

.wordcloud-legend h4 {
  margin: 0 0 12px;
  font-size: 14px;
  color: #1a1a1a;
  font-weight: 600;
}

.keyword-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.fault-stats {
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px solid #e8e9ea;
}

.stat-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 0;
}

.stat-label {
  font-size: 13px;
  color: #8c8c8c;
}

.stat-value {
  font-size: 13px;
  font-weight: 500;
  color: #1a1a1a;
}

.time-analysis-tabs {
  margin-top: -24px;
}

.response-analysis {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.analysis-metrics {
  padding: 16px;
  background: #f8f9fa;
  border-radius: 8px;
}

.satisfaction-analysis {
  padding: 16px;
}

.satisfaction-overview {
  display: flex;
  gap: 24px;
  align-items: center;
}

.satisfaction-score {
  flex-shrink: 0;
}

.score-circle {
  width: 120px;
  height: 120px;
  border-radius: 50%;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
}

.score-text {
  text-align: center;
  line-height: 1.2;
}

.score-number {
  font-size: 32px;
  font-weight: 600;
  display: block;
}

.score-label {
  font-size: 12px;
  opacity: 0.9;
}

.satisfaction-breakdown {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.breakdown-item {
  display: flex;
  align-items: center;
  gap: 12px;
}

.breakdown-item :deep(.ant-progress) {
  flex: 1;
}

.breakdown-label {
  font-size: 12px;
  color: #666666;
  min-width: 80px;
  text-align: right;
}

/* 统计数值样式优化 */
:deep(.ant-statistic-title) {
  font-size: 12px;
  color: #8c8c8c;
  font-weight: 500;
}

:deep(.ant-statistic-content-value) {
  font-size: 18px;
  font-weight: 600;
  color: #1a1a1a;
}

:deep(.ant-card-head-title) {
  font-size: 16px;
  font-weight: 600;
  color: #1a1a1a;
}

:deep(.ant-tabs-tab) {
  font-weight: 500;
}

/* 响应式优化 */
@media (max-width: 1200px) {
  .header-content {
    flex-direction: column;
    gap: 20px;
    text-align: center;
  }
  
  .analytics-row {
    grid-template-columns: 1fr;
    gap: 16px;
  }
  
  .chart-container {
    height: 250px;
  }
  
  .satisfaction-overview {
    flex-direction: column;
    text-align: center;
  }
}

@media (max-width: 768px) {
  .page-header {
    padding: 20px;
  }
  
  .analytics-card {
    padding: 16px;
  }
  
  .chart-container {
    height: 200px;
  }
  
  .ranking-item {
    flex-direction: column;
    gap: 8px;
    text-align: center;
  }
  
  .keyword-tags {
    justify-content: center;
  }
  
  .score-circle {
    width: 100px;
    height: 100px;
  }
  
  .score-number {
    font-size: 24px;
  }
}
</style>