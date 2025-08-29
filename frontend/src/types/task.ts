// 完美的任务相关类型定义
import type { BaseEntity, PaginatedResponse, PaginationParams } from './common'

// 主要的Task接口，支持双重格式以解决测试兼容性
export interface Task extends BaseEntity {
  title: string
  description: string
  
  // 支持双重命名格式
  task_type: 'repair' | 'maintenance' | 'inspection' | 'monitoring' | 'assistance' | 'other'
  type?: 'repair' | 'maintenance' | 'inspection' | 'monitoring' | 'assistance' | 'other'
  
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
  task_status?: Task['task_status'] 
  priority?: Task['priority']
  assignee_id?: number
  estimated_hours?: number
  actual_hours?: number
  completion_notes?: string
}

export interface TaskListParams extends PaginationParams {
  task_type?: string
  task_status?: string
  priority?: string
  assignee_id?: number
  reporter_name?: string
  location?: string
  due_date_from?: string
  due_date_to?: string
  created_date_from?: string
  created_date_to?: string
}

export interface TaskListResponse extends PaginatedResponse<Task> {}

export interface TaskFilters {
  task_type?: string[]
  task_status?: string[]
  priority?: string[]
  assignee_id?: number
  date_from?: string
  date_to?: string
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
}