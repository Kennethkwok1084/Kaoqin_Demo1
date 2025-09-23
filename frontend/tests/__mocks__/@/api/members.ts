// Members API Mock
import { vi } from 'vitest'

const mockMembersData = {
  items: [
    {
      id: 1,
      username: 'test1',
      name: '测试用户1',
      student_id: '2021001',
      phone: '13800138001',
      department: '网络维护部',
      class_name: '计算机1班',
      group_id: 1,
      group_name: '第1组',
      role: 'member',
      is_active: true,
      status_display: '在职',
      join_date: '2023-01-01',
      last_login: '2023-12-01T10:00:00'
    },
    {
      id: 2,
      username: 'test2',
      name: '测试用户2',
      student_id: '2021002',
      phone: '13800138002',
      department: '网络维护部',
      class_name: '计算机2班',
      group_id: null,
      group_name: null,
      role: 'group_leader',
      is_active: true,
      status_display: '在职',
      join_date: '2023-01-01',
      last_login: null
    }
  ],
  total: 2,
  total_pages: 1
}

// 导出所有需要的 API 函数
export const getMembers = vi.fn().mockResolvedValue(mockMembersData)
export const getMemberDetail = vi
  .fn()
  .mockResolvedValue(mockMembersData.items[0])
export const createMember = vi
  .fn()
  .mockResolvedValue({ id: 3, ...mockMembersData.items[0] })
export const updateMember = vi.fn().mockResolvedValue(mockMembersData.items[0])
export const deleteMember = vi.fn().mockResolvedValue(undefined)
export const importMembers = vi
  .fn()
  .mockResolvedValue({
    total_processed: 10,
    successful_imports: 10,
    failed_imports: 0,
    skipped_duplicates: 0,
    errors: []
  })

// 导出 membersApi 对象
export const membersApi = {
  getMembers,
  getMemberDetail,
  createMember,
  updateMember,
  deleteMember,
  importMembers
}

// 默认导出
export default membersApi
