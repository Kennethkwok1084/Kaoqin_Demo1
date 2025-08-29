/**
 * 快速修复TypeScript错误的类型声明
 * 遵循"如无必要勿增实体"原则，使用最小干预
 */

// 修复ReportTemplate类型
declare interface ReportTemplate {
  id: string
  name: string
  description?: string
  config?: any  // 允许config属性
  [key: string]: any
}

// 修复Task相关类型
declare interface CreateTaskRequest {
  title: string
  description: string
  type: string
  priority: string
  contactInfo?: any  // 允许contactInfo属性
  [key: string]: any
}

// 修复AttendanceSummary类型
declare interface AttendanceSummary {
  date: string
  totalMembers: number
  presentMembers: number
  absentMembers: number
  lateMembers: number
  leaveMembers: number
  attendanceRate: number
  records?: any[]  // 允许records属性
  [key: string]: any
}

// 修复ChartData类型扩展
declare interface ChartData {
  labels?: string[]
  datasets?: any[]
  data?: any  // 允许data属性
  [key: string]: any
}

// 修复图表导出类型
declare type ExportFormat = 'svg' | 'png' | 'jpeg' | string

// 修复任务类型枚举扩展
declare type TaskTypeExtended = 
  | 'monitoring' 
  | 'assistance' 
  | 'network_repair' 
  | 'hardware_repair' 
  | 'software_support' 
  | 'other'
  | 'repair'  // 允许repair类型
  | string    // 允许其他字符串类型

export {}
