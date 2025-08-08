// 工时管理相关类型定义

export interface WorkHoursRecord {
  id: number
  task_id: string
  title: string
  task_type: string
  work_date: string | Date
  work_hours: number
  work_minutes: number
  task_category: string
  rating: number
  member_id: number
  member_name: string
  source: 'repair_task' | 'monitoring_task' | 'assistance_task'
}

// 保持向后兼容的旧接口
export interface AttendanceRecord extends WorkHoursRecord {
  memberId: number
  memberName: string
  memberAvatar?: string
  employeeId?: string
  department?: string
  date: string
  checkInTime?: string | null
  checkOutTime?: string | null
  workHours: number
  status?: string
  lateMinutes?: number
  earlyLeaveMinutes?: number
  overtimeHours?: number
  location?: string
  ip?: string
  device?: string
  remark?: string
  createdAt?: string
  updatedAt?: string
}

export interface CheckInRequest {
  location?: string
  remark?: string
  photo?: string
}

export interface CheckOutRequest {
  location?: string
  remark?: string
  photo?: string
}

export interface LeaveApplication {
  id: number
  memberId: number
  memberName: string
  type: 'sick' | 'personal' | 'annual' | 'maternity' | 'other'
  startDate: string
  endDate: string
  startTime: string
  endTime: string
  days: number
  hours: number
  reason: string
  status: 'pending' | 'approved' | 'rejected'
  appliedAt: string
  reviewedAt?: string
  reviewedBy?: number
  reviewerName?: string
  reviewComment?: string
  attachments: LeaveAttachment[]
}

export interface LeaveAttachment {
  id: number
  fileName: string
  fileUrl: string
  fileSize: number
  uploadedAt: string
}

export interface CreateLeaveRequest {
  type: 'sick' | 'personal' | 'annual' | 'maternity' | 'other'
  startDate: string
  endDate: string
  startTime: string
  endTime: string
  reason: string
  attachments?: File[]
}

export interface AttendanceFilters {
  memberId?: number
  department?: string[]
  status?: ('normal' | 'late' | 'early_leave' | 'absent' | 'leave' | 'overtime')[]
  dateRange?: [string, string]
  search?: string
}

export interface AttendanceListParams {
  page?: number
  pageSize?: number
  sortBy?: string
  sortOrder?: 'asc' | 'desc'
  filters?: AttendanceFilters
}

export interface AttendanceListResponse {
  items: AttendanceRecord[]
  total: number
  page: number
  pageSize: number
  totalPages: number
}

export interface AttendanceStats {
  totalDays: number
  normalDays: number
  lateDays: number
  earlyLeaveDays: number
  absentDays: number
  leaveDays: number
  overtimeDays: number
  totalWorkHours: number
  averageWorkHours: number
  totalLateMinutes: number
  totalEarlyLeaveMinutes: number
  totalOvertimeHours: number
  attendanceRate: number
}

// 工时汇总相关类型
export interface WorkHoursSummary {
  date: string
  total_members: number
  active_members: number
  total_hours: number
  repair_hours: number
  monitoring_hours: number
  assistance_hours: number
  average_hours: number
  participation_rate: number
}

export interface WorkHoursListParams {
  page?: number
  size?: number
  date_from?: string
  date_to?: string
  member_id?: number
  member_ids?: number[]
  task_type?: string
  search?: string
}

export interface WorkHoursListResponse {
  items: WorkHoursRecord[]
  total: number
  page: number
  size: number
}

export interface WorkHoursStats {
  total_hours: number
  total_tasks: number
  average_hours_per_task: number
  repair_hours: number
  monitoring_hours: number
  assistance_hours: number
  member_stats: Array<{
    member_id: number
    member_name: string
    total_hours: number
    task_count: number
  }>
}

export interface WorkHoursChart {
  labels: string[]
  datasets: Array<{
    label: string
    data: number[]
    backgroundColor?: string
    borderColor?: string
  }>
}

export interface MonthlyWorkHoursReport {
  member_id: number
  member_name: string
  year: number
  month: number
  month_string: string
  repair_tasks: {
    hours: number
    minutes: number
    task_count: number
    average_rating: number
  }
  monitoring_tasks: {
    hours: number
    minutes: number
    task_count: number
  }
  assistance_tasks: {
    hours: number
    minutes: number
    task_count: number
  }
  total: {
    hours: number
    minutes: number
    task_count: number
  }
}

// 保持向后兼容
export interface AttendanceSummary extends WorkHoursSummary {
  totalMembers: number
  presentMembers: number
  absentMembers: number
  lateMembers: number
  leaveMembers: number
  attendanceRate: number
  records: AttendanceRecord[]
}

export interface AttendanceSettings {
  workStartTime: string
  workEndTime: string
  lateThreshold: number // 迟到阈值（分钟）
  earlyLeaveThreshold: number // 早退阈值（分钟）
  overtimeThreshold: number // 加班阈值（分钟）
  enableLocationCheck: boolean
  allowedLocations: string[]
  requireCheckInPhoto: boolean
  requireCheckOutPhoto: boolean
  autoCheckOut: boolean
  autoCheckOutTime: string
}

export interface MonthlyReport {
  memberId: number
  memberName: string
  department: string
  year: number
  month: number
  workDays: number
  actualWorkDays: number
  totalWorkHours: number
  normalDays: number
  lateDays: number
  earlyLeaveDays: number
  absentDays: number
  leaveDays: number
  overtimeDays: number
  overtimeHours: number
  attendanceRate: number
  dailyRecords: DailyRecord[]
}

export interface DailyRecord {
  date: string
  checkInTime: string | null
  checkOutTime: string | null
  workHours: number
  status: string
  lateMinutes: number
  earlyLeaveMinutes: number
  overtimeHours: number
}

export interface AttendanceChart {
  labels: string[]
  datasets: {
    label: string
    data: number[]
    backgroundColor?: string
    borderColor?: string
    fill?: boolean
  }[]
}

export interface OvertimeApplication {
  id: number
  memberId: number
  memberName: string
  date: string
  startTime: string
  endTime: string
  hours: number
  reason: string
  status: 'pending' | 'approved' | 'rejected'
  appliedAt: string
  reviewedAt?: string
  reviewedBy?: number
  reviewerName?: string
  reviewComment?: string
}

export interface CreateOvertimeRequest {
  date: string
  startTime: string
  endTime: string
  reason: string
}

// 考勤状态配置
export const ATTENDANCE_STATUS_CONFIG = {
  normal: {
    label: '正常',
    color: '#67C23A',
    bgColor: '#f0f9ff',
    icon: 'CircleCheck'
  },
  late: {
    label: '迟到',
    color: '#E6A23C',
    bgColor: '#fdf6ec',
    icon: 'Clock'
  },
  early_leave: {
    label: '早退',
    color: '#F56C6C',
    bgColor: '#fef0f0',
    icon: 'ArrowLeft'
  },
  absent: {
    label: '缺勤',
    color: '#909399',
    bgColor: '#f4f4f5',
    icon: 'Close'
  },
  leave: {
    label: '请假',
    color: '#409EFF',
    bgColor: '#ecf5ff',
    icon: 'Document'
  },
  overtime: {
    label: '加班',
    color: '#9C27B0',
    bgColor: '#f3e5f5',
    icon: 'Timer'
  }
}

// 请假类型配置
export const LEAVE_TYPE_CONFIG = {
  sick: {
    label: '病假',
    color: '#F56C6C'
  },
  personal: {
    label: '事假',
    color: '#E6A23C'
  },
  annual: {
    label: '年假',
    color: '#67C23A'
  },
  maternity: {
    label: '产假',
    color: '#409EFF'
  },
  other: {
    label: '其他',
    color: '#909399'
  }
}

// 申请状态配置
export const APPLICATION_STATUS_CONFIG = {
  pending: {
    label: '待审批',
    color: '#E6A23C',
    bgColor: '#fdf6ec'
  },
  approved: {
    label: '已批准',
    color: '#67C23A',
    bgColor: '#f0f9ff'
  },
  rejected: {
    label: '已拒绝',
    color: '#F56C6C',
    bgColor: '#fef0f0'
  }
}

// 部门选项
export const DEPARTMENT_OPTIONS = [
  { value: 'IT', label: 'IT部门' },
  { value: 'Network', label: '网络维护部' },
  { value: 'Support', label: '技术支持部' },
  { value: 'Operations', label: '运维部' },
  { value: 'Security', label: '网络安全部' },
  { value: 'Management', label: '管理部门' }
]

// 默认考勤设置
export const DEFAULT_ATTENDANCE_SETTINGS: AttendanceSettings = {
  workStartTime: '09:00',
  workEndTime: '18:00',
  lateThreshold: 15,
  earlyLeaveThreshold: 15,
  overtimeThreshold: 30,
  enableLocationCheck: true,
  allowedLocations: ['公司', '客户现场', '远程办公'],
  requireCheckInPhoto: false,
  requireCheckOutPhoto: false,
  autoCheckOut: true,
  autoCheckOutTime: '22:00'
}