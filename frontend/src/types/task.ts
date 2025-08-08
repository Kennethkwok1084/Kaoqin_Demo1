// 任务相关类型定义

export interface Task {
  id: number
  title: string
  description: string
  type: 'repair' | 'monitoring' | 'assistance'
  priority: 'low' | 'medium' | 'high' | 'urgent'
  status: 'pending' | 'in_progress' | 'completed' | 'cancelled'
  assigneeId: number | null
  assigneeName?: string
  reporterId: number
  reporterName: string
  location: string
  contactInfo: string
  estimatedHours: number
  actualHours: number | null
  startedAt: string | null
  completedAt: string | null
  dueDate: string
  createdAt: string
  updatedAt: string
  tags: string[]
  attachments: TaskAttachment[]
  comments: TaskComment[]
  evaluation?: TaskEvaluation
}

export interface TaskAttachment {
  id: number
  fileName: string
  fileUrl: string
  fileSize: number
  uploadedAt: string
  uploadedBy: number
}

export interface TaskComment {
  id: number
  content: string
  authorId: number
  authorName: string
  createdAt: string
  updatedAt: string
}

export interface TaskEvaluation {
  id: number
  rating: 1 | 2 | 3 | 4 | 5
  comment: string
  evaluatedBy: number
  evaluatedAt: string
}

export interface CreateTaskRequest {
  title: string
  description: string
  type: 'repair' | 'monitoring' | 'assistance'
  priority: 'low' | 'medium' | 'high' | 'urgent'
  assigneeId?: number
  location: string
  contactInfo: string
  estimatedHours: number
  dueDate: string
  tags?: string[]
  attachments?: File[]
}

export interface UpdateTaskRequest {
  title?: string
  description?: string
  type?: 'repair' | 'monitoring' | 'assistance'
  priority?: 'low' | 'medium' | 'high' | 'urgent'
  status?: 'pending' | 'in_progress' | 'completed' | 'cancelled'
  assigneeId?: number
  location?: string
  contactInfo?: string
  estimatedHours?: number
  actualHours?: number
  dueDate?: string
  tags?: string[]
}

export interface TaskFilters {
  status?: ('pending' | 'in_progress' | 'completed' | 'cancelled')[]
  type?: ('repair' | 'monitoring' | 'assistance')[]
  priority?: ('low' | 'medium' | 'high' | 'urgent')[]
  assigneeId?: number
  reporterId?: number
  dateRange?: [string, string]
  search?: string
  tags?: string[]
}

export interface TaskListParams {
  page?: number
  pageSize?: number
  sortBy?: string
  sortOrder?: 'asc' | 'desc'
  filters?: TaskFilters
}

export interface TaskListResponse {
  items: Task[]
  total: number
  page: number
  pageSize: number
  totalPages: number
}

export interface TaskStats {
  total: number
  pending: number
  inProgress: number
  completed: number
  cancelled: number
  overdue: number
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
}

export interface TaskWorkLog {
  id: number
  taskId: number
  description: string
  hours: number
  loggedBy: number
  loggedByName: string
  loggedAt: string
}

export interface TaskTransition {
  fromStatus: string
  toStatus: string
  allowedRoles: string[]
  requireComment: boolean
}

// 任务状态流转配置
export const TASK_STATUS_TRANSITIONS: TaskTransition[] = [
  { fromStatus: 'pending', toStatus: 'in_progress', allowedRoles: ['user', 'admin'], requireComment: false },
  { fromStatus: 'in_progress', toStatus: 'completed', allowedRoles: ['user', 'admin'], requireComment: false },
  { fromStatus: 'in_progress', toStatus: 'cancelled', allowedRoles: ['admin'], requireComment: true },
  { fromStatus: 'pending', toStatus: 'cancelled', allowedRoles: ['admin'], requireComment: true },
  { fromStatus: 'completed', toStatus: 'in_progress', allowedRoles: ['admin'], requireComment: true }
]

// 任务类型配置
export const TASK_TYPE_CONFIG = {
  repair: {
    label: '维修任务',
    color: '#409EFF',
    icon: 'Tools',
    description: '设备维修和故障处理'
  },
  monitoring: {
    label: '监控任务', 
    color: '#67C23A',
    icon: 'Monitor',
    description: '系统监控和巡检'
  },
  assistance: {
    label: '协助任务',
    color: '#E6A23C', 
    icon: 'Connection',
    description: '技术支持和协助'
  }
}

// 优先级配置
export const TASK_PRIORITY_CONFIG = {
  low: {
    label: '低',
    color: '#909399',
    level: 1
  },
  medium: {
    label: '中',
    color: '#E6A23C',
    level: 2
  },
  high: {
    label: '高',
    color: '#F56C6C',
    level: 3
  },
  urgent: {
    label: '紧急',
    color: '#F56C6C',
    level: 4
  }
}

// 状态配置
export const TASK_STATUS_CONFIG = {
  pending: {
    label: '待处理',
    color: '#909399',
    bgColor: '#f4f4f5'
  },
  in_progress: {
    label: '进行中',
    color: '#409EFF',
    bgColor: '#ecf5ff'
  },
  completed: {
    label: '已完成',
    color: '#67C23A',
    bgColor: '#f0f9ff'
  },
  cancelled: {
    label: '已取消',
    color: '#F56C6C',
    bgColor: '#fef0f0'
  }
}