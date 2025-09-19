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
    return response.data
  }
}
