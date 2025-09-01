/**
 * 图表数据验证工具
 * Chart Data Validator Utilities
 */

export interface ChartDataset {
  label: string
  data: number[]
  backgroundColor?: string | string[]
  borderColor?: string
  borderWidth?: number
}

export interface ChartData {
  labels: string[]
  datasets: ChartDataset[]
}

/**
 * 验证图表数据结构是否有效
 */
export function validateChartData(data: unknown): data is ChartData {
  if (!data || typeof data !== 'object') {
    return false
  }

  const chartData = data as Partial<ChartData>

  // 检查 labels
  if (!Array.isArray(chartData.labels)) {
    return false
  }

  // 检查 datasets
  if (!Array.isArray(chartData.datasets)) {
    return false
  }

  // 检查每个 dataset
  return chartData.datasets.every(
    dataset =>
      typeof dataset === 'object' &&
      typeof dataset.label === 'string' &&
      Array.isArray(dataset.data)
  )
}

/**
 * 清洗图表数据，确保格式正确
 */
export function sanitizeChartData(data: unknown): ChartData {
  if (!validateChartData(data)) {
    return {
      labels: [],
      datasets: []
    }
  }

  return data
}

/**
 * 为图表数据生成默认颜色
 */
export function generateColors(count: number): string[] {
  const colors = [
    '#409EFF',
    '#67C23A',
    '#E6A23C',
    '#F56C6C',
    '#909399',
    '#303133',
    '#606266',
    '#1890ff',
    '#52c41a',
    '#faad14',
    '#f5222d',
    '#722ed1'
  ]

  const result: string[] = []
  for (let i = 0; i < count; i++) {
    result.push(colors[i % colors.length])
  }

  return result
}

/**
 * 创建默认的空图表数据
 */
export function createEmptyChartData(): ChartData {
  return {
    labels: [],
    datasets: []
  }
}

/**
 * 获取默认的线性图表数据
 */
export function getDefaultLineChartData(): ChartData {
  return {
    labels: ['1月', '2月', '3月', '4月', '5月', '6月'],
    datasets: [
      {
        label: '任务数量',
        data: [0, 0, 0, 0, 0, 0],
        borderColor: '#409EFF',
        backgroundColor: 'rgba(64, 158, 255, 0.1)'
      }
    ]
  }
}

/**
 * 获取默认的饼状图表数据
 */
export function getDefaultPieChartData(): ChartData {
  return {
    labels: ['暂无数据'],
    datasets: [
      {
        label: '数据分布',
        data: [0],
        backgroundColor: ['#DCDFE6']
      }
    ]
  }
}

/**
 * 格式化API响应数据为图表数据格式
 */
export function formatApiResponse(apiResponse: any): ChartData {
  if (!apiResponse) {
    return createEmptyChartData()
  }

  // 如果已经是正确格式，直接返回
  if (validateChartData(apiResponse)) {
    return apiResponse
  }

  // 尝试从常见的API响应格式中提取数据
  if (apiResponse.data && validateChartData(apiResponse.data)) {
    return apiResponse.data
  }

  // 如果是数组格式，尝试转换
  if (Array.isArray(apiResponse)) {
    return {
      labels: apiResponse.map(
        (item: any, index: number) => item.name || `项目${index + 1}`
      ),
      datasets: [
        {
          label: '数据',
          data: apiResponse.map((item: any) => item.value || item.count || 0),
          backgroundColor: generateColors(apiResponse.length)
        }
      ]
    }
  }

  return createEmptyChartData()
}
