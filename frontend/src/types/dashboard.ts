// 仪表板相关类型定义

export interface DashboardStats {
  totalTasks: number
  completedTasks: number
  pendingTasks: number
  overdueTasks: number
  totalMembers: number
  activeMembers: number
  totalWorkHours: number
  monthlyWorkHours: number
  attendanceRate: number
  completionRate: number
}

export interface TaskDistribution {
  repair: number
  monitoring: number
  assistance: number
}

export interface WorkHoursTrend {
  date: string
  hours: number
  target: number
}

export interface MemberPerformance {
  memberId: number
  memberName: string
  completedTasks: number
  workHours: number
  attendanceRate: number
  efficiency: number
}

export interface RecentActivity {
  id: number
  type: 'task_completed' | 'task_assigned' | 'member_joined' | 'attendance'
  title: string
  description: string
  timestamp: string
  userId?: number
  userName?: string
}

export interface MonthlyReport {
  month: string
  totalTasks: number
  completedTasks: number
  totalHours: number
  averageHours: number
  attendanceRate: number
}

export interface AlertItem {
  id: number
  type: 'overdue' | 'low_efficiency' | 'absence' | 'system'
  level: 'low' | 'medium' | 'high' | 'critical'
  title: string
  message: string
  timestamp: string
  resolved: boolean
  taskId?: number
  memberId?: number
}

export interface QuickAction {
  id: string
  title: string
  description: string
  icon: string
  color: string
  route: string
  permission?: string
}
