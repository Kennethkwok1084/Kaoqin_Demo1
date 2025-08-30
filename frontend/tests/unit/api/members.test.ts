import { describe, it, expect, beforeEach, vi } from 'vitest'
import {
  getMembers,
  getMemberDetail,
  createMember,
  updateMember,
  deleteMember,
  importMembers,
  exportMembers,
  getMemberStats
} from '@/api/members'
import { http } from '@/api/client'
import type {
  Member,
  MemberCreateRequest,
  MemberUpdateRequest,
  MemberListParams
} from '@/types/member'

// Mock http client
vi.mock('@/api/client', () => ({
  http: {
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
    delete: vi.fn()
  }
}))

describe('Members API', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('getMembers', () => {
    it('应该获取成员列表', async () => {
      const mockResponse = {
        data: {
          items: [
            {
              id: 1,
              username: 'test1',
              name: '测试用户1',
              role: 'member',
              is_active: true
            }
          ],
          total: 1,
          page: 1,
          page_size: 20,
          total_pages: 1
        }
      }

      vi.mocked(http.get).mockResolvedValue(mockResponse)

      const params: MemberListParams = {
        page: 1,
        page_size: 20,
        search: '测试'
      }

      const result = await getMembers(params)

      expect(http.get).toHaveBeenCalledWith('/members/', { params })
      expect(result).toEqual(mockResponse.data.data)
    })

    it('应该处理无参数的请求', async () => {
      const mockResponse = {
        data: {
          items: [],
          total: 0,
          page: 1,
          page_size: 20,
          total_pages: 0
        }
      }

      vi.mocked(http.get).mockResolvedValue(mockResponse)

      const result = await getMembers()

      expect(http.get).toHaveBeenCalledWith('/members/', { params: {} })
      expect(result).toEqual(mockResponse.data.data)
    })

    it('应该处理筛选参数', async () => {
      const mockResponse = {
        data: {
          items: [],
          total: 0,
          page: 1,
          page_size: 20,
          total_pages: 0
        }
      }

      vi.mocked(http.get).mockResolvedValue(mockResponse)

      const params: MemberListParams = {
        page: 1,
        page_size: 10,
        role: 'admin',
        is_active: true,
        department: '技术部',
        class_name: '计算机1班'
      }

      await getMembers(params)

      expect(http.get).toHaveBeenCalledWith('/members/', { params })
    })
  })

  describe('getMemberDetail', () => {
    it('应该获取成员详情', async () => {
      const mockMember: Member = {
        id: 1,
        username: 'test1',
        name: '测试用户',
        email: 'test@example.com',
        phone: '13800138001',
        student_id: '2021001',
        department: '技术部',
        class_name: '计算机1班',
        role: 'member',
        is_active: true,
        status_display: '在职',
        join_date: '2023-01-01',
        last_login: '2023-12-01T10:00:00',
        profile_completed: true,
        created_at: '2023-01-01T00:00:00',
        updated_at: '2023-12-01T10:00:00'
      }

      const mockResponse = { data: mockMember }
      vi.mocked(http.get).mockResolvedValue(mockResponse)

      const result = await getMemberDetail(1)

      expect(http.get).toHaveBeenCalledWith('/members/1')
      expect(result).toEqual(mockMember)
    })

    it('应该处理不存在的成员ID', async () => {
      vi.mocked(http.get).mockRejectedValue(new Error('Member not found'))

      await expect(getMemberDetail(999)).rejects.toThrow('Member not found')
      expect(http.get).toHaveBeenCalledWith('/members/999')
    })
  })

  describe('createMember', () => {
    it('应该创建新成员', async () => {
      const createData: MemberCreateRequest = {
        username: 'newuser',
        name: '新用户',
        email: 'newuser@example.com',
        phone: '13800138000',
        password: 'password123',
        student_id: '2024001',
        department: '技术部',
        class_name: '计算机1班',
        role: 'member'
      }

      const mockCreatedMember: Member = {
        id: 2,
        ...createData,
        is_active: true,
        status_display: '在职',
        join_date: '2023-12-01',
        last_login: null,
        profile_completed: false,
        created_at: '2023-12-01T10:00:00',
        updated_at: '2023-12-01T10:00:00'
      }

      const mockResponse = { data: mockCreatedMember }
      vi.mocked(http.post).mockResolvedValue(mockResponse)

      const result = await createMember(createData)

      expect(http.post).toHaveBeenCalledWith('/members/', createData)
      expect(result).toEqual(mockCreatedMember)
    })

    it('应该处理创建时的验证错误', async () => {
      const createData: MemberCreateRequest = {
        username: '',
        name: '新用户',
        email: 'invalid-email',
        phone: '138',
        password: '123',
        student_id: '',
        department: '',
        class_name: '',
        role: 'member'
      }

      vi.mocked(http.post).mockRejectedValue(new Error('Validation failed'))

      await expect(createMember(createData)).rejects.toThrow(
        'Validation failed'
      )
    })
  })

  describe('updateMember', () => {
    it('应该更新成员信息', async () => {
      const updateData: MemberUpdateRequest = {
        name: '更新的用户名',
        email: 'updated@example.com',
        phone: '13800138999',
        department: '新技术部',
        role: 'group_leader'
      }

      const mockUpdatedMember: Member = {
        id: 1,
        username: 'test1',
        ...updateData,
        student_id: '2021001',
        class_name: '计算机1班',
        is_active: true,
        status_display: '在职',
        join_date: '2023-01-01',
        last_login: '2023-12-01T10:00:00',
        profile_completed: true,
        created_at: '2023-01-01T00:00:00',
        updated_at: '2023-12-01T10:30:00'
      }

      const mockResponse = { data: mockUpdatedMember }
      vi.mocked(http.put).mockResolvedValue(mockResponse)

      const result = await updateMember(1, updateData)

      expect(http.put).toHaveBeenCalledWith('/members/1', updateData)
      expect(result).toEqual(mockUpdatedMember)
    })

    it('应该处理部分字段更新', async () => {
      const updateData: MemberUpdateRequest = {
        name: '只更新姓名'
      }

      const mockUpdatedMember: Member = {
        id: 1,
        username: 'test1',
        name: '只更新姓名',
        email: 'test@example.com',
        phone: '13800138001',
        student_id: '2021001',
        department: '技术部',
        class_name: '计算机1班',
        role: 'member',
        is_active: true,
        status_display: '在职',
        join_date: '2023-01-01',
        last_login: '2023-12-01T10:00:00',
        profile_completed: true,
        created_at: '2023-01-01T00:00:00',
        updated_at: '2023-12-01T10:30:00'
      }

      const mockResponse = { data: mockUpdatedMember }
      vi.mocked(http.put).mockResolvedValue(mockResponse)

      const result = await updateMember(1, updateData)

      expect(http.put).toHaveBeenCalledWith('/members/1', updateData)
      expect(result).toEqual(mockUpdatedMember)
    })
  })

  describe('deleteMember', () => {
    it('应该删除成员', async () => {
      const mockResponse = { data: { message: 'Member deleted successfully' } }
      vi.mocked(http.delete).mockResolvedValue(mockResponse)

      await deleteMember(1)

      expect(http.delete).toHaveBeenCalledWith('/members/1')
    })

    it('应该处理删除不存在的成员', async () => {
      vi.mocked(http.delete).mockRejectedValue(new Error('Member not found'))

      await expect(deleteMember(999)).rejects.toThrow('Member not found')
    })
  })

  describe('importMembers', () => {
    it('应该批量导入成员', async () => {
      const file = new File(
        ['name,username,email\n张三,zhangsan,zhang@test.com'],
        'members.csv',
        {
          type: 'text/csv'
        }
      )

      const mockImportResult = {
        success_count: 1,
        failed_count: 0,
        total_count: 1,
        failed_items: [],
        import_id: 'import_123'
      }

      const mockResponse = { data: mockImportResult }
      vi.mocked(http.post).mockResolvedValue(mockResponse)

      const result = await importMembers(file, { update_existing: true })

      expect(http.post).toHaveBeenCalledWith(
        '/members/import',
        expect.any(FormData),
        expect.objectContaining({
          headers: {
            'Content-Type': 'multipart/form-data'
          }
        })
      )
      expect(result).toEqual(mockImportResult)
    })

    it('应该处理导入文件格式错误', async () => {
      const file = new File(['invalid content'], 'invalid.txt', {
        type: 'text/plain'
      })

      vi.mocked(http.post).mockRejectedValue(new Error('Invalid file format'))

      await expect(importMembers(file)).rejects.toThrow('Invalid file format')
    })

    it('应该处理空文件导入', async () => {
      const file = new File([''], 'empty.csv', {
        type: 'text/csv'
      })

      vi.mocked(http.post).mockRejectedValue(new Error('Empty file'))

      await expect(importMembers(file)).rejects.toThrow('Empty file')
    })
  })

  describe('exportMembers', () => {
    it('应该导出成员数据', async () => {
      const mockExportData = new Blob(['exported data'], {
        type: 'application/vnd.ms-excel'
      })
      const mockResponse = { data: mockExportData }

      vi.mocked(http.get).mockResolvedValue(mockResponse)

      const params = {
        format: 'excel' as const,
        role: 'member',
        is_active: true
      }

      const result = await exportMembers(params)

      expect(http.get).toHaveBeenCalledWith('/members/export', {
        params,
        responseType: 'blob'
      })
      expect(result).toEqual(mockExportData)
    })

    it('应该支持CSV格式导出', async () => {
      const mockExportData = new Blob(['csv data'], { type: 'text/csv' })
      const mockResponse = { data: mockExportData }

      vi.mocked(http.get).mockResolvedValue(mockResponse)

      const params = {
        format: 'csv' as const,
        fields: ['name', 'username', 'email']
      }

      const result = await exportMembers(params)

      expect(http.get).toHaveBeenCalledWith('/members/export', {
        params,
        responseType: 'blob'
      })
      expect(result).toEqual(mockExportData)
    })

    it('应该处理导出权限错误', async () => {
      vi.mocked(http.get).mockRejectedValue(new Error('Permission denied'))

      const params = { format: 'excel' as const }

      await expect(exportMembers(params)).rejects.toThrow('Permission denied')
    })
  })

  describe('getMemberStats', () => {
    it('应该获取成员统计信息', async () => {
      const mockStats = {
        total_members: 100,
        active_members: 85,
        inactive_members: 15,
        role_distribution: {
          admin: 2,
          group_leader: 8,
          member: 88,
          guest: 2
        },
        department_distribution: {
          技术部: 45,
          运维部: 30,
          测试部: 25
        },
        recent_registrations: 12,
        recent_logins: 78
      }

      const mockResponse = { data: mockStats }
      vi.mocked(http.get).mockResolvedValue(mockResponse)

      const result = await getMemberStats()

      expect(http.get).toHaveBeenCalledWith('/members/stats/overview')
      expect(result).toEqual(mockStats)
    })

    it('应该支持时间范围查询统计', async () => {
      const mockStats = {
        total_members: 100,
        active_members: 85,
        inactive_members: 15,
        role_distribution: {},
        department_distribution: {},
        recent_registrations: 5,
        recent_logins: 40
      }

      const mockResponse = { data: mockStats }
      vi.mocked(http.get).mockResolvedValue(mockResponse)

      const params = {
        start_date: '2023-01-01',
        end_date: '2023-12-31'
      }

      const result = await getMemberStats(params)

      expect(http.get).toHaveBeenCalledWith('/members/stats/overview', {
        params
      })
      expect(result).toEqual(mockStats)
    })
  })

  describe('错误处理', () => {
    it('应该正确传递网络错误', async () => {
      const networkError = new Error('Network Error')
      vi.mocked(http.get).mockRejectedValue(networkError)

      await expect(getMembers()).rejects.toThrow('Network Error')
    })

    it('应该正确传递服务器错误', async () => {
      const serverError = new Error('Internal Server Error')
      vi.mocked(http.post).mockRejectedValue(serverError)

      const createData: MemberCreateRequest = {
        username: 'test',
        name: '测试',
        email: 'test@test.com',
        phone: '13800138000',
        password: 'password',
        student_id: '2024001',
        department: '技术部',
        class_name: '计算机1班',
        role: 'member'
      }

      await expect(createMember(createData)).rejects.toThrow(
        'Internal Server Error'
      )
    })

    it('应该正确传递验证错误', async () => {
      const validationError = new Error('Validation Error')
      vi.mocked(http.put).mockRejectedValue(validationError)

      const updateData: MemberUpdateRequest = {
        email: 'invalid-email'
      }

      await expect(updateMember(1, updateData)).rejects.toThrow(
        'Validation Error'
      )
    })
  })
})
