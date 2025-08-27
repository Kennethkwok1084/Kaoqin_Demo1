// 任务相关类型定义

export interface Task {
  id: number
  title: string
  description: string
  type:
    | 'network_repair'
    | 'hardware_repair'
    | 'software_support'
    | 'monitoring'
    | 'assistance'
    | 'other' // 修复：使用后端TaskCategory枚举值
  priority: 'low' | 'medium' | 'high' | 'urgent'
  status: 'pending' | 'in_progress' | 'completed' | 'cancelled'
  assigneeId: number | null
  assigneeName?: string
  reporterId: number
  reporterName: string
  location: string
  reporter_contact: string // 修复：使用reporter_contact与后端保持一致
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
  type:
    | 'network_repair'
    | 'hardware_repair'
    | 'software_support'
    | 'monitoring'
    | 'assistance'
    | 'other' // 修复：使用后端TaskCategory枚举值
  priority: 'low' | 'medium' | 'high' | 'urgent'
  assigneeId?: number
  location: string
  reporter_contact: string // 修复：使用reporter_contact与后端保持一致
  estimatedHours: number
  dueDate: string
  tags?: string[]
  attachments?: File[]
}

export interface UpdateTaskRequest {
  title?: string
  description?: string
  type?:
    | 'network_repair'
    | 'hardware_repair'
    | 'software_support'
    | 'monitoring'
    | 'assistance'
    | 'other'
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
  type?: (
    | 'network_repair'
    | 'hardware_repair'
    | 'software_support'
    | 'monitoring'
    | 'assistance'
    | 'other'
  )[]
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
    network_repair: number
    hardware_repair: number
    software_support: number
    monitoring: number
    assistance: number
    other: number
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
  {
    fromStatus: 'pending',
    toStatus: 'in_progress',
    allowedRoles: ['user', 'admin'],
    requireComment: false
  },
  {
    fromStatus: 'in_progress',
    toStatus: 'completed',
    allowedRoles: ['user', 'admin'],
    requireComment: false
  },
  {
    fromStatus: 'in_progress',
    toStatus: 'cancelled',
    allowedRoles: ['admin'],
    requireComment: true
  },
  {
    fromStatus: 'pending',
    toStatus: 'cancelled',
    allowedRoles: ['admin'],
    requireComment: true
  },
  {
    fromStatus: 'completed',
    toStatus: 'in_progress',
    allowedRoles: ['admin'],
    requireComment: true
  }
]

// 任务类型配置 - 修复：匹配后端TaskCategory枚举
export const TASK_TYPE_CONFIG = {
  network_repair: {
    label: '网络维修',
    color: '#409EFF',
    icon: 'Tools',
    description: '网络设备维修和故障处理'
  },
  hardware_repair: {
    label: '硬件维修',
    color: '#F56C6C',
    icon: 'Tools',
    description: '硬件设备维修和更换'
  },
  software_support: {
    label: '软件支持',
    color: '#909399',
    icon: 'Computer',
    description: '软件安装配置和技术支持'
  },
  monitoring: {
    label: '日常监控',
    color: '#67C23A',
    icon: 'Monitor',
    description: '系统监控和巡检'
  },
  assistance: {
    label: '协助任务',
    color: '#E6A23C',
    icon: 'Connection',
    description: '技术支持和协助'
  },
  other: {
    label: '其他任务',
    color: '#606266',
    icon: 'More',
    description: '其他类型任务'
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
