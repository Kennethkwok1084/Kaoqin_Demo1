// 完美的任务相关类型定义
import type { BaseEntity, PaginatedResponse, PaginationParams } from './common'

// 主要的Task接口，支持双重格式以解决测试兼容性
export interface Task extends BaseEntity {
  title: string
  description: string

  // 支持双重命名格式
  task_type:
    | 'repair'
    | 'maintenance'
    | 'inspection'
    | 'monitoring'
    | 'assistance'
    | 'other'
  type?:
    | 'repair'
    | 'maintenance'
    | 'inspection'
    | 'monitoring'
    | 'assistance'
    | 'other'

  task_status: 'pending' | 'in_progress' | 'completed' | 'cancelled'
  status?: 'pending' | 'in_progress' | 'completed' | 'cancelled'

  priority: 'low' | 'medium' | 'high' | 'urgent'

  // 分配相关字段（支持双重格式）
  assignee_id?: number | null
  assigneeId?: number | null
  assignee_name?: string
  assigneeName?: string

  // 报告人相关字段
  reporter_id?: number
  reporterId?: number
  reporter_name: string
  reporterName?: string
  reporter_phone?: string
  reporter_contact?: string

  // 位置和时间
  location: string
  due_date?: string
  dueDate?: string

  // 工时相关
  estimated_hours?: number
  estimatedHours?: number
  actual_hours?: number | null
  actualHours?: number | null
  work_hours?: number

  // 时间戳
  started_at?: string | null
  startedAt?: string | null
  completed_at?: string | null
  completedAt?: string | null
  completion_notes?: string | null

  // 关联数据
  tags?: string[]
  attachments?: TaskAttachment[]
  comments?: TaskComment[]
  evaluation?: TaskEvaluation
  work_logs?: WorkHour[]
}

export interface WorkHour {
  id: number
  task_id: number
  member_id: number
  hours: number
  date: string
  description?: string
  created_at: string
}

export interface TaskAttachment extends BaseEntity {
  fileName: string
  fileUrl: string
  fileSize: number
  uploadedAt: string
  uploadedBy: number
}

export interface TaskComment extends BaseEntity {
  content: string
  authorId: number
  authorName: string
}

export interface TaskEvaluation extends BaseEntity {
  task_id: number
  rating: number
  feedback?: string
  evaluator_id: number
}

// 请求和响应类型
export interface TaskCreateRequest {
  title: string
  description: string
  task_type: Task['task_type']
  priority: Task['priority']
  assignee_id?: number
  reporter_name: string
  reporter_phone?: string
  location: string
  due_date?: string
  estimated_hours?: number
}

export interface TaskUpdateRequest {
  title?: string
  description?: string
  type?: Task['task_type']
  task_type?: Task['task_type']
  task_status?: Task['task_status']
  priority?: Task['priority']
  assignee_id?: number
  location?: string
  contactInfo?: string
  estimatedHours?: number
  estimated_hours?: number
  actual_hours?: number
  dueDate?: string
  tags?: string[]
  completion_notes?: string
}

export interface TaskListParams extends PaginationParams {
  task_type?: string | string[]
  task_status?: string | string[]
  priority?: string | string[]
  assignee_id?: number
  reporter_name?: string
  location?: string
  due_date_from?: string
  due_date_to?: string
  created_date_from?: string
  created_date_to?: string
  date_from?: string
  date_to?: string
  // Support frontend filter format
  pageSize?: number
  sortBy?: string
  sortOrder?: 'asc' | 'desc'
  filters?: TaskFilters
}

export interface TaskListResponse extends PaginatedResponse<Task> {}

export interface TaskFilters {
  type?: string[]
  task_type?: string[]
  status?: string[]
  task_status?: string[]
  priority?: string[]
  assignee_id?: number
  assigneeId?: number
  date_from?: string
  date_to?: string
  search?: string
  dateRange?: [string, string]
}

export interface TaskStats {
  total: number
  pending: number
  in_progress: number
  completed: number
  cancelled: number
  overdue: number
  total_work_hours: number
  avg_work_hours: number
  // Add compatibility properties
  inProgress?: number
}

// Export aliases for compatibility
export type CreateTaskRequest = TaskCreateRequest
export type UpdateTaskRequest = TaskUpdateRequest

// Task work log interface
export interface TaskWorkLog extends BaseEntity {
  task_id: number
  member_id: number
  member_name: string
  description: string
  hours: number
  date: string
}

// Task configuration constants for UI components
export const TASK_TYPE_CONFIG = {
  repair: {
    label: '维修任务',
    color: 'danger',
    icon: 'Tools',
    description: '设备故障维修'
  },
  maintenance: {
    label: '维护任务',
    color: 'warning',
    icon: 'Setting',
    description: '定期设备维护'
  },
  inspection: {
    label: '巡检任务',
    color: 'primary',
    icon: 'View',
    description: '例行安全巡检'
  },
  monitoring: {
    label: '监控任务',
    color: 'info',
    icon: 'Monitor',
    description: '系统监控'
  },
  assistance: {
    label: '协助任务',
    color: 'success',
    icon: 'UserFilled',
    description: '协助其他任务'
  },
  online: {
    label: '线上任务',
    color: 'info',
    icon: 'Monitor',
    description: '远程处理任务'
  },
  offline: {
    label: '线下任务',
    color: 'warning',
    icon: 'Tools',
    description: '现场处理任务'
  },
  other: {
    label: '其他任务',
    color: 'info',
    icon: 'Document',
    description: '其他类型任务'
  }
} as const

export const TASK_STATUS_CONFIG = {
  pending: { label: '待处理', color: 'info', icon: 'Clock' },
  in_progress: { label: '进行中', color: 'warning', icon: 'Loading' },
  completed: { label: '已完成', color: 'success', icon: 'Select' },
  cancelled: { label: '已取消', color: 'danger', icon: 'Close' }
} as const

export const TASK_PRIORITY_CONFIG = {
  low: { label: '低', color: 'info', icon: 'ArrowDown' },
  medium: { label: '中', color: 'warning', icon: 'Minus' },
  high: { label: '高', color: 'danger', icon: 'ArrowUp' },
  urgent: { label: '紧急', color: 'danger', icon: 'Warning' }
} as const
