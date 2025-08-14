// 工时管理相关类型定义

export interface WorkHour {
  id: number
  taskId: number
  memberId: number
  memberName: string
  taskTitle: string
  taskType: 'repair' | 'monitoring' | 'assistance'
  baseHours: number
  bonusHours: number
  penaltyHours: number
  totalHours: number
  status: 'pending' | 'approved' | 'rejected'
  adjustmentReason?: string
  adminNotes?: string
  createdAt: string
  updatedAt: string
  approvedAt?: string
  approvedBy?: string
}

export interface WorkHourAdjustment {
  id: number
  workHourId: number
  originalHours: number
  adjustedHours: number
  adjustmentType: 'bonus' | 'penalty' | 'manual'
  reason: string
  adjustedBy: string
  adjustedAt: string
}

export interface WorkHourStatistics {
  totalMembers: number
  totalHours: number
  totalTasks: number
  avgHoursPerTask: number
  avgHoursPerMember: number
  pendingReviews: number
  approvedHours: number
  rejectedHours: number
  efficiency: number
}

export interface WorkHourFilters {
  memberId?: number
  taskType?: string
  status?: string
  dateRange?: [Date, Date]
  department?: string
}

export interface WorkHourRule {
  id: number
  name: string
  taskType: string
  baseHours: number
  bonusConditions: BonusCondition[]
  penaltyConditions: PenaltyCondition[]
  isActive: boolean
  createdAt: string
  updatedAt: string
}

export interface BonusCondition {
  type: 'rush_period' | 'positive_review' | 'early_completion' | 'quality_bonus'
  value: number
  description: string
}

export interface PenaltyCondition {
  type:
    | 'late_response'
    | 'late_completion'
    | 'negative_review'
    | 'quality_issue'
  value: number
  description: string
}

export interface WorkHourCalculationRequest {
  taskIds: number[]
  recalculateAll?: boolean
  applyNewRules?: boolean
}

export interface WorkHourCalculationResult {
  taskId: number
  originalHours: number
  calculatedHours: number
  adjustments: {
    type: string
    value: number
    reason: string
  }[]
  success: boolean
  message?: string
}

export interface WorkHourReview {
  id: number
  workHourId: number
  reviewType: 'approve' | 'reject' | 'adjust'
  adjustedHours?: number
  reviewNotes: string
  reviewedBy: string
  reviewedAt: string
}

export interface PaginatedWorkHours {
  data: WorkHour[]
  total: number
  page: number
  pageSize: number
  totalPages: number
}

export interface WorkHourSummary {
  period: string
  totalHours: number
  baseHours: number
  bonusHours: number
  penaltyHours: number
  avgEfficiency: number
  taskCount: number
}

export interface MemberWorkHourSummary {
  memberId: number
  memberName: string
  department: string
  totalHours: number
  completedTasks: number
  avgHoursPerTask: number
  efficiency: number
  ranking: number
}

export interface WorkHourTrend {
  date: string
  totalHours: number
  baseHours: number
  bonusHours: number
  penaltyHours: number
  taskCount: number
}

export interface WorkHourExportConfig {
  format: 'xlsx' | 'csv' | 'pdf'
  dateRange: [Date, Date]
  includeDetails: boolean
  includeSummary: boolean
  includeCharts: boolean
  filters: WorkHourFilters
}
