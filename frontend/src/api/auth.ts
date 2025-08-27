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
import {
  AuthTransformer,
  extractResponseData,
  transformEnum,
  UserRoleMapping
} from '@/utils/fieldMapping'

/**
 * 认证相关API
 */
export const authApi = {
  /**
   * 用户登录
   */
  async login(credentials: LoginRequest): Promise<LoginResponse> {
    // Transform frontend request to backend format
    const backendRequest = AuthTransformer.toBackend(credentials)

    const response = await http.post<ApiResponse<any>>(
      '/auth/login',
      backendRequest
    )

    // Extract and transform response data
    const responseData = extractResponseData(response.data)

    // Transform backend response to frontend format
    const transformedData = AuthTransformer.toFrontend(responseData)

    // Transform role enum values
    if (transformedData.user?.role) {
      transformedData.user.role = transformEnum(
        transformedData.user.role,
        UserRoleMapping.toFrontend
      )
    }

    return {
      success: response.data.success,
      message: response.data.message,
      data: transformedData
    }
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
    const response = await http.get<ApiResponse<any>>('/auth/me')

    // Extract and transform response data
    const responseData = extractResponseData(response.data)
    const transformedData = AuthTransformer.toFrontend(responseData)

    // Transform role enum values
    if (transformedData.role) {
      transformedData.role = transformEnum(
        transformedData.role,
        UserRoleMapping.toFrontend
      )
    }

    return transformedData
  },

  /**
   * 修改密码
   */
  async changePassword(
    data: PasswordChangeRequest
  ): Promise<{ message: string }> {
    const response = await http.post<{ message: string }>(
      '/auth/change-password',
      data
    )
    return response.data
  },

  /**
   * 请求重置密码
   */
  async requestResetPassword(
    data: ResetPasswordRequest
  ): Promise<{ message: string }> {
    const response = await http.post<{ message: string }>(
      '/auth/reset-password',
      data
    )
    return response.data
  },

  /**
   * 确认重置密码
   */
  async confirmResetPassword(
    data: ConfirmResetPasswordRequest
  ): Promise<{ message: string }> {
    const response = await http.post<{ message: string }>(
      '/auth/reset-password/confirm',
      data
    )
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
    const response = await http.get<{ permissions: string[] }>(
      '/auth/permissions'
    )
    return response.data
  }
}
