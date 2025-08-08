import { http } from './http'
import type { 
  LoginRequest, 
  LoginResponse, 
  RefreshTokenResponse, 
  UserInfo,
  PasswordChangeRequest,
  ResetPasswordRequest,
  ConfirmResetPasswordRequest,
  ApiResponse
} from '@/types/auth'

/**
 * 认证相关API
 */
export const authApi = {
  /**
   * 用户登录
   */
  async login(credentials: LoginRequest): Promise<LoginResponse> {
    const response = await http.post<LoginResponse>('/auth/login', {
      student_id: credentials.username,
      password: credentials.password
    })
    return response.data
  },

  /**
   * 用户登出
   */
  async logout(): Promise<void> {
    await http.post('/auth/logout')
  },

  /**
   * 刷新访问令牌
   */
  async refreshToken(): Promise<RefreshTokenResponse> {
    const response = await http.post<RefreshTokenResponse>('/auth/refresh')
    return response.data
  },

  /**
   * 获取当前用户信息
   */
  async getUserInfo(): Promise<UserInfo> {
    const response = await http.get<ApiResponse<UserInfo>>('/auth/me')
    return response.data.data
  },

  /**
   * 修改密码
   */
  async changePassword(data: PasswordChangeRequest): Promise<{ message: string }> {
    const response = await http.post<{ message: string }>('/auth/change-password', data)
    return response.data
  },

  /**
   * 请求重置密码
   */
  async requestResetPassword(data: ResetPasswordRequest): Promise<{ message: string }> {
    const response = await http.post<{ message: string }>('/auth/reset-password', data)
    return response.data
  },

  /**
   * 确认重置密码
   */
  async confirmResetPassword(data: ConfirmResetPasswordRequest): Promise<{ message: string }> {
    const response = await http.post<{ message: string }>('/auth/reset-password/confirm', data)
    return response.data
  },

  /**
   * 验证token有效性
   */
  async validateToken(): Promise<{ valid: boolean }> {
    const response = await http.get<{ valid: boolean }>('/auth/validate')
    return response.data
  },

  /**
   * 获取用户权限列表
   */
  async getUserPermissions(): Promise<{ permissions: string[] }> {
    const response = await http.get<{ permissions: string[] }>('/auth/permissions')
    return response.data
  }
}