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

export const systemApi = {
  async getSystemInfo(): Promise<SystemInfo> {
    const response = await http.get<SystemInfo>('/system/info')
    // 后端统一返回 { success, message, data }，这里取出真实数据
    return (response.data as any)?.data ?? (response.data as unknown as SystemInfo)
  }
}
