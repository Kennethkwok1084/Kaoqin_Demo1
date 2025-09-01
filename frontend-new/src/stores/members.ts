// 成员管理状态
import { defineStore } from 'pinia'
import { ref, computed, readonly } from 'vue'
import type { Member } from '@/api/client'
import { api } from '@/api/client'

export interface MemberFilters {
  page?: number
  pageSize?: number
  search?: string
  role?: string
  isActive?: boolean
  department?: string
  className?: string
}

export const useMembersStore = defineStore('members', () => {
  // 状态
  const members = ref<Member[]>([])
  const total = ref(0)
  const loading = ref(false)
  const error = ref<string | null>(null)
  
  // 当前筛选条件
  const filters = ref<MemberFilters>({
    page: 1,
    pageSize: 20
  })

  // 计算属性
  const totalPages = computed(() => Math.ceil(total.value / (filters.value.pageSize || 20)))
  const activeMembers = computed(() => members.value.filter(member => member.isActive))
  const inactiveMembers = computed(() => members.value.filter(member => !member.isActive))
  const adminMembers = computed(() => members.value.filter(member => member.role === 'admin'))
  const regularMembers = computed(() => members.value.filter(member => member.role === 'member'))

  // 角色统计
  const roleStats = computed(() => {
    const stats = {
      admin: 0,
      group_leader: 0,
      member: 0,
      guest: 0
    }
    
    members.value.forEach(member => {
      if (member.role in stats) {
        stats[member.role as keyof typeof stats]++
      }
    })
    
    return stats
  })

  // 部门统计
  const departmentStats = computed(() => {
    const stats: Record<string, number> = {}
    
    members.value.forEach(member => {
      stats[member.department] = (stats[member.department] || 0) + 1
    })
    
    return stats
  })

  // 动作
  async function fetchMembers(newFilters?: Partial<MemberFilters>) {
    if (newFilters) {
      filters.value = { ...filters.value, ...newFilters }
    }

    loading.value = true
    error.value = null

    try {
      const response = await api.getMembers(filters.value)
      
      if (response.success && response.data) {
        members.value = response.data.items
        total.value = response.data.total
      } else {
        throw new Error(response.message || '获取成员列表失败')
      }
    } catch (err: any) {
      error.value = err.message
      console.error('Fetch members error:', err)
    } finally {
      loading.value = false
    }
  }

  async function createMember(memberData: {
    username: string
    name: string
    studentId: string
    password: string
    phone: string
    department: string
    className: string
    role: string
    isActive: boolean
    joinDate: string
  }) {
    loading.value = true
    error.value = null

    try {
      const response = await api.createMember(memberData)
      
      if (response.success && response.data) {
        // 重新加载成员列表
        await fetchMembers()
        return { success: true, message: response.message, data: response.data }
      } else {
        throw new Error(response.message || '创建成员失败')
      }
    } catch (err: any) {
      error.value = err.message
      return { success: false, message: error.value }
    } finally {
      loading.value = false
    }
  }

  async function importMembers(membersData: {
    skipDuplicates: boolean
    members: any[]
  }) {
    loading.value = true
    error.value = null

    try {
      const response = await api.importMembers(membersData)
      
      if (response.success) {
        // 重新加载成员列表
        await fetchMembers()
        return { 
          success: true, 
          message: response.message,
          data: response.data
        }
      } else {
        throw new Error(response.message || '批量导入失败')
      }
    } catch (err: any) {
      error.value = err.message
      return { success: false, message: error.value }
    } finally {
      loading.value = false
    }
  }

  // 搜索成员
  async function searchMembers(searchTerm: string) {
    await fetchMembers({ ...filters.value, search: searchTerm, page: 1 })
  }

  // 按角色筛选
  async function filterByRole(role: string) {
    await fetchMembers({ ...filters.value, role, page: 1 })
  }

  // 按状态筛选
  async function filterByStatus(isActive: boolean) {
    await fetchMembers({ ...filters.value, isActive, page: 1 })
  }

  // 按部门筛选
  async function filterByDepartment(department: string) {
    await fetchMembers({ ...filters.value, department, page: 1 })
  }

  // 按班级筛选
  async function filterByClass(className: string) {
    await fetchMembers({ ...filters.value, className, page: 1 })
  }

  // 重置筛选条件
  function resetFilters() {
    filters.value = {
      page: 1,
      pageSize: 20
    }
  }

  // 设置筛选条件
  function setFilters(newFilters: Partial<MemberFilters>) {
    filters.value = { ...filters.value, ...newFilters }
  }

  // 清除错误
  function clearError() {
    error.value = null
  }

  // 根据ID获取成员
  function getMemberById(memberId: number): Member | undefined {
    return members.value.find(member => member.id === memberId)
  }

  // 根据学号获取成员
  function getMemberByStudentId(studentId: string): Member | undefined {
    return members.value.find(member => member.studentId === studentId)
  }

  // 获取所有活跃成员选项（用于下拉选择）
  function getActiveMemberOptions() {
    return activeMembers.value.map(member => ({
      label: `${member.name} (${member.studentId})`,
      value: member.id,
      member
    }))
  }

  // 获取部门列表
  function getDepartments(): string[] {
    const departments = new Set(members.value.map(member => member.department))
    return Array.from(departments).sort()
  }

  // 获取班级列表
  function getClasses(): string[] {
    const classes = new Set(members.value.map(member => member.className))
    return Array.from(classes).sort()
  }

  // 验证成员数据
  function validateMemberData(memberData: any) {
    const errors: Record<string, string> = {}

    if (!memberData.username?.trim()) {
      errors.username = '用户名不能为空'
    }

    if (!memberData.name?.trim()) {
      errors.name = '姓名不能为空'
    }

    if (!memberData.studentId?.trim()) {
      errors.studentId = '学号不能为空'
    }

    if (!memberData.phone?.trim()) {
      errors.phone = '电话号码不能为空'
    } else if (!/^1[3-9]\d{9}$/.test(memberData.phone)) {
      errors.phone = '电话号码格式不正确'
    }

    if (!memberData.department?.trim()) {
      errors.department = '部门不能为空'
    }

    if (!memberData.className?.trim()) {
      errors.className = '班级不能为空'
    }

    return {
      isValid: Object.keys(errors).length === 0,
      errors
    }
  }

  return {
    // 状态
    members: readonly(members),
    total: readonly(total),
    loading: readonly(loading),
    error: readonly(error),
    filters: readonly(filters),
    
    // 计算属性
    totalPages,
    activeMembers,
    inactiveMembers,
    adminMembers,
    regularMembers,
    roleStats,
    departmentStats,
    
    // 动作
    fetchMembers,
    createMember,
    importMembers,
    searchMembers,
    filterByRole,
    filterByStatus,
    filterByDepartment,
    filterByClass,
    resetFilters,
    setFilters,
    clearError,
    getMemberById,
    getMemberByStudentId,
    getActiveMemberOptions,
    getDepartments,
    getClasses,
    validateMemberData
  }
})