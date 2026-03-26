import { http } from './client'

export interface SystemInfo {
  version: string
  buildTime: string
  pythonVersion: string
  databaseVersion: string
  uptime: string
  activeUsers: number
  totalTasks: number
  completedTasks: number
}

export interface SystemSettingsPayload {
  workHours: {
    onlineTaskMinutes: number
    offlineTaskMinutes: number
    rushBonusMinutes: number
    positiveReviewBonusMinutes?: number
    positiveRatingBonus?: number
    lateResponsePenaltyMinutes?: number
    lateResponsePenalty?: number
    lateCompletionPenaltyMinutes?: number
    lateCompletionPenalty?: number
    negativeReviewPenaltyMinutes?: number
    negativeRatingPenalty?: number
  }
  notifications: {
    enableEmailNotifications?: boolean
    emailEnabled?: boolean
    smtpServer?: string
    smtpPort?: number
    senderEmail?: string
    enableSmsNotifications?: boolean
    enablePushNotifications?: boolean
    systemNotificationEnabled?: boolean
    taskAssignmentNotification?: boolean
    taskCompletionNotification?: boolean
    workHoursNotification?: boolean
  }
  thresholds?: Record<string, unknown>
  penalties?: Record<string, unknown>
}

export const systemApi = {
  async getSystemInfo(): Promise<SystemInfo> {
    const response = await http.get<SystemInfo>('/system/info')
    // 后端统一返回 { success, message, data }，这里取出真实数据
    return (response.data as any)?.data ?? (response.data as unknown as SystemInfo)
  },

  async getSystemSettings(): Promise<SystemSettingsPayload> {
    const response = await http.get<SystemSettingsPayload>('/system/settings')
    return (response.data as any)?.data ?? (response.data as SystemSettingsPayload)
  },

  async updateSystemSettings(
    payload: Partial<SystemSettingsPayload>
  ): Promise<{ updatedCount?: number; failedCount?: number; updatedKeys?: string[] }> {
    const response = await http.put('/system/settings', payload)
    return (response.data as any)?.data ?? response.data
  }
}
