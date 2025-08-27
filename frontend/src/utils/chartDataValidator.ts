/**
 * 图表数据验证和处理工具
 * 确保图表数据格式正确，避免undefined错误
 */

export interface ChartDataset {
  label: string
  data: number[]
  backgroundColor?: string[]
  borderColor?: string
  [key: string]: any
}

export interface ChartData {
  labels: string[]
  datasets: ChartDataset[]
  [key: string]: any
}

/**
 * 验证并修复图表数据
 */
export function validateChartData(
  data: any,
  defaultConfig?: Partial<ChartData>
): ChartData {
  const defaultLabels = defaultConfig?.labels || ['数据1', '数据2', '数据3']
  const defaultDataset: ChartDataset = {
    label: '默认数据',
    data: [0, 0, 0],
    backgroundColor: ['#5470c6', '#91cc75', '#fac858'],
    borderColor: '#5470c6'
  }

  // 如果数据为空或未定义，返回默认配置
  if (!data || typeof data !== 'object') {
    return {
      labels: defaultLabels,
      datasets: [{ ...defaultDataset, ...defaultConfig?.datasets?.[0] }]
    }
  }

  // 验证和修复labels
  const labels = Array.isArray(data.labels) ? data.labels : defaultLabels

  // 验证和修复datasets
  let datasets: ChartDataset[] = []
  if (Array.isArray(data.datasets) && data.datasets.length > 0) {
    datasets = data.datasets.map((dataset: any, index: number) => ({
      label: dataset?.label || `数据集${index + 1}`,
      data: Array.isArray(dataset?.data) ? dataset.data : defaultDataset.data,
      backgroundColor:
        dataset?.backgroundColor || defaultDataset.backgroundColor,
      borderColor: dataset?.borderColor || defaultDataset.borderColor,
      ...dataset
    }))
  } else {
    datasets = [defaultDataset]
  }

  // 确保数据长度匹配
  datasets = datasets.map(dataset => ({
    ...dataset,
    data: labels.map((_: any, index: number) => dataset.data[index] ?? 0)
  }))

  return {
    labels,
    datasets,
    ...data
  }
}

/**
 * 为饼图数据生成默认配置
 */
export function getDefaultPieChartData(): ChartData {
  return validateChartData(null, {
    labels: ['维修任务', '监控任务', '协助任务'],
    datasets: [
      {
        label: '任务分布',
        data: [0, 0, 0],
        backgroundColor: ['#5470c6', '#91cc75', '#fac858']
      }
    ]
  })
}

/**
 * 为折线图数据生成默认配置
 */
export function getDefaultLineChartData(): ChartData {
  const dates = []
  for (let i = 6; i >= 0; i--) {
    const date = new Date()
    date.setDate(date.getDate() - i)
    dates.push(date.toLocaleDateString())
  }

  return validateChartData(null, {
    labels: dates,
    datasets: [
      {
        label: '任务完成趋势',
        data: new Array(7).fill(0),
        backgroundColor: ['rgba(84, 112, 198, 0.2)'],
        borderColor: '#5470c6'
      }
    ]
  })
}

/**
 * 为柱状图数据生成默认配置
 */
export function getDefaultBarChartData(): ChartData {
  return validateChartData(null, {
    labels: ['成员1', '成员2', '成员3', '成员4', '成员5'],
    datasets: [
      {
        label: '工作时长',
        data: [0, 0, 0, 0, 0],
        backgroundColor: ['#5470c6', '#91cc75', '#fac858', '#ee6666', '#73c0de']
      }
    ]
  })
}

/**
 * 为甜甜圈图数据生成默认配置
 */
export function getDefaultDoughnutChartData(): ChartData {
  return validateChartData(null, {
    labels: ['出勤', '缺勤', '请假'],
    datasets: [
      {
        label: '考勤分布',
        data: [0, 0, 0],
        backgroundColor: ['#91cc75', '#ee6666', '#fac858']
      }
    ]
  })
}

/**
 * 安全地获取嵌套对象属性
 */
export function safeGet<T>(obj: any, path: string, defaultValue: T): T {
  const keys = path.split('.')
  let current = obj

  for (const key of keys) {
    if (current == null || typeof current !== 'object') {
      return defaultValue
    }
    current = current[key]
  }

  return current !== undefined ? current : defaultValue
}

/**
 * 格式化API响应数据
 */
export function formatApiResponse(response: any): any {
  if (!response || typeof response !== 'object') {
    return {}
  }

  // 如果响应包含data字段，提取data
  if (response.data) {
    return response.data
  }

  return response
}
