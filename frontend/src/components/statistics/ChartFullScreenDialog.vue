<template>
  <el-dialog
    v-model="dialogVisible"
    :title="chartTitle"
    width="90%"
    fullscreen
    @close="handleClose"
  >
    <div class="chart-fullscreen-container">
      <div class="chart-header">
        <div class="chart-info">
          <h3>{{ chartTitle }}</h3>
          <p v-if="chartDescription" class="chart-description">
            {{ chartDescription }}
          </p>
        </div>
        <div class="chart-actions">
          <el-button-group>
            <el-button @click="refreshChart" :loading="loading">
              <el-icon><Refresh /></el-icon>
              刷新
            </el-button>
            <el-button @click="downloadChart('png')">
              <el-icon><Download /></el-icon>
              PNG
            </el-button>
            <el-button @click="downloadChart('jpg')">
              <el-icon><Download /></el-icon>
              JPG
            </el-button>
            <el-button @click="downloadChart('pdf')">
              <el-icon><Download /></el-icon>
              PDF
            </el-button>
            <el-button @click="downloadChart('svg')">
              <el-icon><Download /></el-icon>
              SVG
            </el-button>
          </el-button-group>
        </div>
      </div>

      <div class="chart-content">
        <div ref="chartRef" class="chart-container"></div>
      </div>

      <div class="chart-controls" v-if="showControls">
        <el-card>
          <template #header>
            <span>图表控制</span>
          </template>

          <div class="control-section">
            <el-row :gutter="20">
              <el-col :span="8">
                <el-form-item label="时间范围">
                  <el-date-picker
                    v-model="chartFilters.dateRange"
                    type="monthrange"
                    range-separator="至"
                    start-placeholder="开始月份"
                    end-placeholder="结束月份"
                    @change="updateChart"
                  />
                </el-form-item>
              </el-col>

              <el-col :span="8">
                <el-form-item label="数据维度">
                  <el-select
                    v-model="chartFilters.dimension"
                    @change="updateChart"
                  >
                    <el-option label="按日统计" value="day" />
                    <el-option label="按周统计" value="week" />
                    <el-option label="按月统计" value="month" />
                  </el-select>
                </el-form-item>
              </el-col>

              <el-col :span="8">
                <el-form-item label="图表类型">
                  <el-select v-model="chartType" @change="changeChartType">
                    <el-option label="柱状图" value="bar" />
                    <el-option label="折线图" value="line" />
                    <el-option label="面积图" value="area" />
                    <el-option label="饼图" value="pie" />
                    <el-option label="雷达图" value="radar" />
                  </el-select>
                </el-form-item>
              </el-col>
            </el-row>
          </div>
        </el-card>
      </div>

      <div class="chart-data" v-if="showDataTable">
        <el-card>
          <template #header>
            <div class="data-header">
              <span>数据详情</span>
              <el-button @click="exportData" type="primary" size="small">
                <el-icon><Download /></el-icon>
                导出数据
              </el-button>
            </div>
          </template>

          <el-table :data="chartData" stripe style="width: 100%">
            <el-table-column
              v-for="column in dataColumns"
              :key="column.prop"
              :prop="column.prop"
              :label="column.label"
              :formatter="column.formatter"
            />
          </el-table>
        </el-card>
      </div>
    </div>

    <template #footer>
      <div class="dialog-footer">
        <el-button @click="toggleControls">
          {{ showControls ? '隐藏控制面板' : '显示控制面板' }}
        </el-button>
        <el-button @click="toggleDataTable">
          {{ showDataTable ? '隐藏数据表格' : '显示数据表格' }}
        </el-button>
        <el-button type="primary" @click="handleClose">关闭</el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, reactive, watch, onMounted, onUnmounted, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import { Refresh, Download } from '@element-plus/icons-vue'
import * as echarts from 'echarts'
import type { ECharts } from 'echarts'
import { statisticsApi } from '@/api/statistics'
import type { ChartConfig, StatisticsFilters } from '@/types/statistics'

interface Props {
  visible: boolean
  chartConfig: ChartConfig | null
  chartTitle: string
  chartDescription?: string
}

interface Emits {
  (e: 'update:visible', value: boolean): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

const dialogVisible = ref(false)
const loading = ref(false)
const chartRef = ref<HTMLDivElement>()
const chartInstance = ref<ECharts>()
const showControls = ref(false)
const showDataTable = ref(false)
const chartType = ref('bar')
const chartData = ref<any[]>([])
const dataColumns = ref<any[]>([])

const chartFilters = reactive<StatisticsFilters>({
  dateRange: [new Date(2024, 0, 1), new Date()],
  dimension: 'month'
})

watch(
  () => props.visible,
  visible => {
    dialogVisible.value = visible
    if (visible) {
      nextTick(() => {
        initChart()
      })
    }
  }
)

watch(dialogVisible, visible => {
  emit('update:visible', visible)
  if (!visible) {
    destroyChart()
  }
})

onMounted(() => {
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  destroyChart()
})

const initChart = async () => {
  if (!chartRef.value || !props.chartConfig) return

  try {
    loading.value = true

    // 初始化图表实例
    chartInstance.value = echarts.init(chartRef.value)

    // 加载图表数据
    await loadChartData()

    // 渲染图表
    renderChart()
  } catch (error) {
    console.error('初始化图表失败:', error)
    ElMessage.error('初始化图表失败')
  } finally {
    loading.value = false
  }
}

const loadChartData = async () => {
  if (!props.chartConfig) return

  try {
    const response = await statisticsApi.getChartData(
      props.chartConfig.id,
      chartFilters
    )
    chartData.value = response.data

    // 设置数据表格列
    if (chartData.value.length > 0) {
      const firstItem = chartData.value[0]
      dataColumns.value = Object.keys(firstItem).map(key => ({
        prop: key,
        label: getColumnLabel(key),
        formatter: getColumnFormatter(key)
      }))
    }
  } catch (error) {
    console.error('加载图表数据失败:', error)
    throw error
  }
}

const renderChart = () => {
  if (!chartInstance.value || !chartData.value.length) return

  const option = generateChartOption()
  chartInstance.value.setOption(option)
}

const generateChartOption = () => {
  const baseOption = {
    title: {
      text: props.chartTitle,
      left: 'center',
      textStyle: {
        fontSize: 18,
        fontWeight: 'bold'
      }
    },
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'shadow'
      }
    },
    legend: {
      top: 40,
      left: 'center'
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      containLabel: true
    }
  }

  switch (chartType.value) {
    case 'line':
      return {
        ...baseOption,
        xAxis: {
          type: 'category',
          data: chartData.value.map(item => item.name || item.label)
        },
        yAxis: {
          type: 'value'
        },
        series: [
          {
            type: 'line',
            data: chartData.value.map(item => item.value),
            smooth: true,
            areaStyle: {}
          }
        ]
      }

    case 'pie':
      return {
        ...baseOption,
        series: [
          {
            type: 'pie',
            radius: ['40%', '70%'],
            center: ['50%', '60%'],
            data: chartData.value.map(item => ({
              name: item.name || item.label,
              value: item.value
            })),
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

    case 'radar':
      return {
        ...baseOption,
        radar: {
          indicator: chartData.value.map(item => ({
            name: item.name || item.label,
            max: Math.max(...chartData.value.map(d => d.value)) * 1.2
          }))
        },
        series: [
          {
            type: 'radar',
            data: [
              {
                value: chartData.value.map(item => item.value),
                name: props.chartTitle
              }
            ]
          }
        ]
      }

    default: // bar
      return {
        ...baseOption,
        xAxis: {
          type: 'category',
          data: chartData.value.map(item => item.name || item.label)
        },
        yAxis: {
          type: 'value'
        },
        series: [
          {
            type: 'bar',
            data: chartData.value.map(item => item.value),
            itemStyle: {
              color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                { offset: 0, color: '#83bff6' },
                { offset: 0.5, color: '#188df0' },
                { offset: 1, color: '#188df0' }
              ])
            }
          }
        ]
      }
  }
}

const updateChart = async () => {
  await loadChartData()
  renderChart()
}

const changeChartType = () => {
  renderChart()
}

const refreshChart = async () => {
  await updateChart()
  ElMessage.success('图表已刷新')
}

const downloadChart = (format: string) => {
  if (!chartInstance.value) return

  try {
    const url = chartInstance.value.getDataURL({
      type: format === 'jpg' ? 'jpeg' : format,
      pixelRatio: 2,
      backgroundColor: '#fff'
    })

    const link = document.createElement('a')
    link.download = `${props.chartTitle}.${format}`
    link.href = url
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)

    ElMessage.success(`图表已导出为 ${format.toUpperCase()} 格式`)
  } catch (error) {
    console.error('导出图表失败:', error)
    ElMessage.error('导出图表失败')
  }
}

const exportData = () => {
  try {
    const csv = convertToCSV(chartData.value)
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' })
    const link = document.createElement('a')
    link.download = `${props.chartTitle}_数据.csv`
    link.href = URL.createObjectURL(blob)
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)

    ElMessage.success('数据已导出为 CSV 格式')
  } catch (error) {
    console.error('导出数据失败:', error)
    ElMessage.error('导出数据失败')
  }
}

const convertToCSV = (data: any[]): string => {
  if (!data.length) return ''

  const headers = Object.keys(data[0])
  const csvContent = [
    headers.join(','),
    ...data.map(row => headers.map(header => row[header]).join(','))
  ].join('\n')

  return csvContent
}

const getColumnLabel = (key: string): string => {
  const labelMap: Record<string, string> = {
    name: '名称',
    value: '数值',
    date: '日期',
    count: '数量',
    percentage: '百分比',
    department: '部门',
    member: '成员'
  }
  return labelMap[key] || key
}

const getColumnFormatter = (key: string) => {
  if (key === 'percentage') {
    return (row: any, column: any, cellValue: any) => `${cellValue}%`
  }
  return undefined
}

const toggleControls = () => {
  showControls.value = !showControls.value
}

const toggleDataTable = () => {
  showDataTable.value = !showDataTable.value
}

const handleResize = () => {
  if (chartInstance.value) {
    chartInstance.value.resize()
  }
}

const destroyChart = () => {
  if (chartInstance.value) {
    chartInstance.value.dispose()
    chartInstance.value = undefined
  }
}

const handleClose = () => {
  dialogVisible.value = false
}
</script>

<style lang="scss" scoped>
.chart-fullscreen-container {
  height: calc(100vh - 120px);
  display: flex;
  flex-direction: column;
}

.chart-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding-bottom: 15px;
  border-bottom: 1px solid var(--el-border-color);

  .chart-info {
    h3 {
      margin: 0 0 8px 0;
      font-size: 20px;
      font-weight: 600;
      color: var(--el-text-color-primary);
    }

    .chart-description {
      margin: 0;
      color: var(--el-text-color-regular);
      font-size: 14px;
    }
  }
}

.chart-content {
  flex: 1;
  min-height: 400px;
  margin-bottom: 20px;

  .chart-container {
    width: 100%;
    height: 100%;
    min-height: 400px;
  }
}

.chart-controls,
.chart-data {
  margin-bottom: 20px;

  .control-section {
    :deep(.el-form-item) {
      margin-bottom: 0;
    }
  }

  .data-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }
}

.dialog-footer {
  text-align: right;
}
</style>
