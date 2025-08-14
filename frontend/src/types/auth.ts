// 认证相关类型定义

export interface LoginRequest {
  student_id: string  // 修复：使用student_id与后端保持一致
  password: string
  remember_me?: boolean
}

// 标准API响应格式
export interface ApiResponse<T = any> {
  success: boolean
  message: string
  data: T
}

export interface LoginData {
  access_token: string
  refresh_token: string
  token_type: string
  expires_in: number
  user: UserInfo
}

export interface LoginResponse extends ApiResponse<LoginData> {}

export interface RefreshTokenResponse {
  access_token: string
  token_type: string
  expires_in: number
}

export interface UserInfo {
  id: number
  username: string
  name: string // 真实姓名
  student_id?: string
  email?: string
  phone?: string
  department?: string
  class_name?: string
  role: 'admin' | 'group_leader' | 'member' | 'guest'
  is_active: boolean
  is_verified?: boolean
  profile_completed?: boolean
  permissions?: string[]
  avatar?: string
  last_login?: string
  login_count?: number
  created_at: string
  updated_at?: string
  needs_profile_completion?: boolean // 是否需要完善信息
  // 为了兼容性，保留full_name作为name的别名
  full_name?: string
}

export interface AuthState {
  token: string | null
  user: UserInfo | null
  isLoading: boolean
}

export interface PasswordChangeRequest {
  current_password: string
  new_password: string
  confirm_password: string
}

export interface ResetPasswordRequest {
  email: string
}

export interface ConfirmResetPasswordRequest {
  token: string
  new_password: string
  confirm_password: string
}
