// 统计报表相关类型定义

export interface StatisticsOverview {
  totalMembers: number
  totalTasks: number
  totalAttendance: number
  totalWorkHours: number
  completionRate: number
  attendanceRate: number
  efficiencyScore: number
  monthlyGrowth: number
}

export interface TaskStatistics {
  totalTasks: number
  completedTasks: number
  pendingTasks: number
  overdueTasks: number
  avgCompletionTime: number
  byType: {
    repair: number
    monitoring: number
    assistance: number
  }
  byPriority: {
    low: number
    medium: number
    high: number
    urgent: number
  }
  byStatus: {
    pending: number
    in_progress: number
    completed: number
    cancelled: number
  }
  monthlyTrend: MonthlyTrendData[]
  memberRanking: MemberRankingItem[]
}

export interface AttendanceStatistics {
  totalDays: number
  workDays: number
  presentDays: number
  absentDays: number
  lateDays: number
  leaveDays: number
  overtimeDays: number
  avgWorkHours: number
  attendanceRate: number
  punctualityRate: number
  overtimeRate: number
  monthlyTrend: MonthlyTrendData[]
  departmentStats: DepartmentStatsItem[]
}

export interface WorkHoursStatistics {
  totalHours: number
  regularHours: number
  overtimeHours: number
  avgDailyHours: number
  avgWeeklyHours: number
  efficiency: number
  productivity: number
  utilization: number
  distribution: WorkHoursDistribution
  trends: WorkHoursTrend[]
  comparisons: WorkHoursComparison[]
}

export interface MonthlyTrendData {
  month: string
  value: number
  growth?: number
  target?: number
}

export interface MemberRankingItem {
  memberId: number
  memberName: string
  avatar?: string
  department: string
  score: number
  completedTasks: number
  workHours: number
  efficiency: number
  rank: number
  change: number // 排名变化
}

export interface DepartmentStatsItem {
  department: string
  memberCount: number
  totalTasks: number
  completedTasks: number
  totalHours: number
  attendanceRate: number
  efficiency: number
  ranking: number
}

export interface WorkHoursDistribution {
  morning: number // 上午工时
  afternoon: number // 下午工时
  evening: number // 晚上工时
  weekend: number // 周末工时
  byDay: { [key: string]: number } // 按星期分布
  byHour: { [key: string]: number } // 按小时分布
}

export interface WorkHoursTrend {
  date: string
  regularHours: number
  overtimeHours: number
  efficiency: number
}

export interface WorkHoursComparison {
  period: string
  current: number
  previous: number
  change: number
  changePercent: number
}

export interface ChartData {
  labels: string[]
  datasets: ChartDataset[]
}

export interface ChartDataset {
  label: string
  data: number[]
  backgroundColor?: string | string[]
  borderColor?: string | string[]
  borderWidth?: number
  fill?: boolean
  tension?: number
  type?: 'line' | 'bar' | 'pie' | 'doughnut' | 'radar'
}

export interface ChartOptions {
  responsive: boolean
  maintainAspectRatio: boolean
  plugins?: {
    title?: {
      display: boolean
      text: string
    }
    legend?: {
      display: boolean
      position?: 'top' | 'bottom' | 'left' | 'right'
    }
    tooltip?: {
      enabled: boolean
    }
  }
  scales?: {
    x?: {
      display: boolean
      title?: {
        display: boolean
        text: string
      }
    }
    y?: {
      display: boolean
      title?: {
        display: boolean
        text: string
      }
      beginAtZero?: boolean
    }
  }
}

export interface ReportTemplate {
  id: string
  name: string
  description: string
  type: 'daily' | 'weekly' | 'monthly' | 'quarterly' | 'yearly'
  categories: string[]
  metrics: string[]
  charts: string[]
  format: 'pdf' | 'excel' | 'word'
  schedule?: ReportSchedule
}

export interface ReportSchedule {
  enabled: boolean
  frequency: 'daily' | 'weekly' | 'monthly'
  time: string
  recipients: string[]
  nextRun?: string
}

export interface GeneratedReport {
  id: string
  templateId: string
  templateName: string
  type: string
  period: string
  createdAt: string
  createdBy: number
  creatorName: string
  status: 'generating' | 'completed' | 'failed'
  fileUrl?: string
  fileSize?: number
  downloadCount: number
}

export interface StatisticsFilters {
  dateRange?: [string, string]
  departments?: string[]
  members?: number[]
  taskTypes?: string[]
  includeWeekends?: boolean
  includeHolidays?: boolean
}

export interface ExportOptions {
  format: 'excel' | 'pdf' | 'csv'
  template?: string
  includeCharts: boolean
  includeRawData: boolean
  dateRange: [string, string]
  categories: string[]
}

export interface DashboardWidget {
  id: string
  type: 'chart' | 'metric' | 'table' | 'progress'
  title: string
  size: 'small' | 'medium' | 'large'
  position: { x: number; y: number; w: number; h: number }
  config: any
  data?: any
  loading?: boolean
  error?: string
}

export interface PerformanceMetrics {
  productivity: {
    score: number
    trend: number
    comparison: string
  }
  efficiency: {
    score: number
    trend: number
    comparison: string
  }
  quality: {
    score: number
    trend: number
    comparison: string
  }
  timeliness: {
    score: number
    trend: number
    comparison: string
  }
}

export interface ComparisonData {
  current: {
    period: string
    value: number
    label: string
  }
  previous: {
    period: string
    value: number
    label: string
  }
  change: {
    value: number
    percent: number
    trend: 'up' | 'down' | 'stable'
  }
}

// 图表类型配置
export const CHART_TYPES = {
  line: {
    name: '折线图',
    icon: 'TrendCharts',
    description: '显示数据随时间的变化趋势'
  },
  bar: {
    name: '柱状图',
    icon: 'DataAnalysis',
    description: '比较不同类别的数据'
  },
  pie: {
    name: '饼图',
    icon: 'PieChart',
    description: '显示数据的组成比例'
  },
  doughnut: {
    name: '环形图',
    icon: 'Connection',
    description: '饼图的变体，中间有空洞'
  },
  radar: {
    name: '雷达图',
    icon: 'Histogram',
    description: '多维度数据比较'
  },
  scatter: {
    name: '散点图',
    icon: 'ScaleToOriginal',
    description: '显示两个变量之间的关系'
  }
}

// 统计指标配置
export const METRICS_CONFIG = {
  tasks: {
    total: { name: '任务总数', unit: '个', icon: 'Document' },
    completed: { name: '已完成', unit: '个', icon: 'CircleCheck' },
    completion_rate: { name: '完成率', unit: '%', icon: 'TrendCharts' },
    avg_time: { name: '平均用时', unit: '小时', icon: 'Timer' }
  },
  attendance: {
    rate: { name: '出勤率', unit: '%', icon: 'User' },
    punctuality: { name: '准时率', unit: '%', icon: 'Clock' },
    overtime: { name: '加班时长', unit: '小时', icon: 'Timer' },
    leave_days: { name: '请假天数', unit: '天', icon: 'Calendar' }
  },
  performance: {
    efficiency: { name: '工作效率', unit: '分', icon: 'Lightning' },
    quality: { name: '工作质量', unit: '分', icon: 'Star' },
    productivity: { name: '生产力', unit: '分', icon: 'TrendCharts' },
    satisfaction: { name: '满意度', unit: '分', icon: 'Like' }
  }
}

// 报表模板配置
export const REPORT_TEMPLATES: ReportTemplate[] = [
  {
    id: 'daily_summary',
    name: '日报',
    description: '每日工作总结报告',
    type: 'daily',
    categories: ['tasks', 'attendance'],
    metrics: ['completion_rate', 'attendance_rate'],
    charts: ['task_completion', 'attendance_overview'],
    format: 'pdf'
  },
  {
    id: 'weekly_report',
    name: '周报',
    description: '每周工作分析报告',
    type: 'weekly',
    categories: ['tasks', 'attendance', 'performance'],
    metrics: ['total_tasks', 'work_hours', 'efficiency'],
    charts: ['weekly_trend', 'department_comparison'],
    format: 'excel'
  },
  {
    id: 'monthly_analysis',
    name: '月报',
    description: '月度综合分析报告',
    type: 'monthly',
    categories: ['tasks', 'attendance', 'performance', 'analysis'],
    metrics: ['all_metrics'],
    charts: ['monthly_trends', 'member_ranking', 'department_stats'],
    format: 'pdf'
  },
  {
    id: 'quarterly_review',
    name: '季报',
    description: '季度回顾和分析报告',
    type: 'quarterly',
    categories: ['strategic', 'performance', 'trends'],
    metrics: ['kpi_metrics'],
    charts: ['quarterly_trends', 'goal_achievement'],
    format: 'pdf'
  }
]

// 颜色主题配置
export const CHART_COLORS = {
  primary: ['#409EFF', '#67C23A', '#E6A23C', '#F56C6C', '#909399'],
  success: ['#67C23A', '#85CE61', '#A4D884', '#C2E2A7', '#E1F0CA'],
  warning: ['#E6A23C', '#EEBE77', '#F3D19E', '#F8E3C5', '#FCF6EC'],
  danger: ['#F56C6C', '#F78989', '#F9A6A6', '#FBC4C4', '#FDE2E2'],
  info: ['#909399', '#A6A9AD', '#BCBEC2', '#D3D4D6', '#E9E9EB'],
  gradient: {
    blue: ['#409EFF', '#66B2FF', '#8CC5FF', '#B3D8FF'],
    green: ['#67C23A', '#95D475', '#B6E3A0', '#D8F3CB'],
    orange: ['#E6A23C', '#F0C272', '#F5D49E', '#FAE6CA'],
    red: ['#F56C6C', '#F89898', '#FAB6B6', '#FDD4D4']
  }
}
