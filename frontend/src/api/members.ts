/**
 * 全新的成员管理API
 * 完全重构后的前端数据交互
 */

import { http } from './client'

// 类型定义
export interface Member {
  id: number
  username: string
  name: string
  student_id?: string
  phone?: string
  department: string
  class_name: string
  join_date?: string
  role: string
  is_active: boolean
  status_display: string
  is_verified: boolean
  profile_completed?: boolean
  last_login?: string
  login_count: number
  created_at: string
  updated_at: string
}

export interface MemberListResponse {
  items: Member[]
  total: number
  page: number
  page_size: number
  total_pages: number
}

export interface MemberCreateRequest {
  username: string
  name: string
  student_id?: string
  phone?: string
  department?: string
  class_name: string
  join_date?: string
  role?: string
  is_active?: boolean
  password?: string
}

export interface MemberUpdateRequest {
  username?: string
  name?: string
  phone?: string
  department?: string
  class_name?: string
  role?: string
  is_active?: boolean
}

export interface MemberImportItem {
  username?: string
  name: string
  student_id?: string
  phone?: string
  department?: string
  class_name: string
  role?: string
}

export interface MemberImportRequest {
  members: MemberImportItem[]
  skip_duplicates?: boolean
}

export interface MemberImportResponse {
  total_processed: number
  successful_imports: number
  failed_imports: number
  skipped_duplicates: number
  errors: string[]
}

export interface PasswordChangeRequest {
  old_password: string
  new_password: string
}

export interface MemberStats {
  total_members: number
  active_members: number
  inactive_members: number
  role_stats: Record<string, number>
  department_stats: Record<string, number>
}

export interface MemberListParams {
  page?: number
  page_size?: number
  search?: string
  role?: string
  is_active?: boolean
  department?: string
  class_name?: string
}

/**
 * 成员管理API类
 */
export class MembersApi {
  /**
   * 获取成员列表
   */
  static async getMembers(
    params: MemberListParams = {}
  ): Promise<MemberListResponse> {
    const response = await http.get('/members/', { params })
    return response.data.data
  }

  /**
   * 获取单个成员详情
   */
  static async getMember(id: number): Promise<Member> {
    const response = await http.get(`/members/${id}`)
    return response.data.data
  }

  /**
   * 创建新成员
   */
  static async createMember(data: MemberCreateRequest): Promise<Member> {
    const response = await http.post('/members/', data)
    return response.data.data
  }

  /**
   * 更新成员信息
   */
  static async updateMember(
    id: number,
    data: MemberUpdateRequest
  ): Promise<Member> {
    const response = await http.put(`/members/${id}`, data)
    return response.data.data
  }

  /**
   * 删除成员
   */
  static async deleteMember(id: number): Promise<void> {
    await http.delete(`/members/${id}`)
  }

  /**
   * 批量导入成员
   */
  static async importMembers(
    data: MemberImportRequest
  ): Promise<MemberImportResponse> {
    const response = await http.post('/members/import', data)
    return response.data.data
  }

  /**
   * 修改密码
   */
  static async changePassword(
    id: number,
    data: PasswordChangeRequest
  ): Promise<void> {
    await http.post(`/members/${id}/change-password`, data)
  }

  /**
   * 获取成员统计信息
   */
  static async getMemberStats(): Promise<MemberStats> {
    const response = await http.get('/members/stats/overview')
    return response.data.data
  }

  /**
   * 健康检查
   */
  static async healthCheck(): Promise<any> {
    const response = await http.get('/members/health')
    return response.data.data
  }

  /**
   * 完善个人信息
   */
  static async completeProfile(
    memberId: number,
    data: MemberUpdateRequest
  ): Promise<any> {
    const response = await http.post(
      `/members/${memberId}/complete-profile`,
      data
    )
    return response.data.data
  }
}

// 导出便捷方法
export const {
  getMembers,
  getMember,
  createMember,
  updateMember,
  deleteMember,
  importMembers,
  changePassword,
  getMemberStats,
  healthCheck
} = MembersApi

// 默认导出
export default MembersApi
