import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import {
  MembersApi,
  type Member,
  type MemberCreateRequest,
  type MemberUpdateRequest,
  type MemberListParams,
  type MemberImportRequest,
  type MemberStats
} from '@/api/members'

export const useMembersStore = defineStore('members', () => {
  // 核心状态
  const members = ref<Member[]>([])
  const currentMember = ref<Member | null>(null)
  const loading = ref(false)
  const error = ref<string | null>(null)
  const stats = ref<MemberStats | null>(null)

  // 分页状态
  const pagination = ref({
    page: 1,
    page_size: 20,
    total: 0,
    total_pages: 0
  })

  // 筛选状态
  const searchQuery = ref('')
  const filters = ref<Partial<MemberListParams>>({})

  // 计算属性
  const activeMembers = computed(() =>
    members.value.filter(member => member.is_active)
  )

  const inactiveMembers = computed(() =>
    members.value.filter(member => !member.is_active)
  )

  const totalMembers = computed(() => pagination.value.total)
  const hasNextPage = computed(
    () => pagination.value.page < pagination.value.total_pages
  )
  const hasPrevPage = computed(() => pagination.value.page > 1)

  // Actions
  const fetchMembers = async (params: MemberListParams = {}) => {
    try {
      loading.value = true
      error.value = null

      const queryParams: MemberListParams = {
        ...params,
        page: params.page || pagination.value.page,
        page_size: params.page_size || pagination.value.page_size,
        ...(searchQuery.value && { search: searchQuery.value }),
        ...filters.value
      }

      // 清理空值参数
      Object.keys(queryParams).forEach(key => {
        const value = queryParams[key as keyof typeof queryParams]
        if (value === '' || value === null || value === undefined) {
          delete queryParams[key as keyof typeof queryParams]
        }
      })

      const response = await MembersApi.getMembers(queryParams)

      // 更新状态
      members.value = response.items || []
      pagination.value = {
        page: response.page || 1,
        page_size: response.page_size || 20,
        total: response.total || 0,
        total_pages: response.total_pages || 0
      }

      return response
    } catch (err: any) {
      error.value =
        err instanceof Error ? err.message : 'Failed to fetch members'
      console.error('fetchMembers error:', err)
      return { items: [], total: 0, page: 1, page_size: 20, total_pages: 0 }
    } finally {
      loading.value = false
    }
  }

  const fetchMemberDetail = async (id: number) => {
    try {
      loading.value = true
      error.value = null
      const member = await MembersApi.getMember(id)
      currentMember.value = member
      return member
    } catch (err: any) {
      error.value = err instanceof Error ? err.message : 'Member not found'
      console.error('fetchMemberDetail error:', err)
      return null
    } finally {
      loading.value = false
    }
  }

  const createMember = async (memberData: MemberCreateRequest) => {
    try {
      loading.value = true
      error.value = null

      const newMember = await MembersApi.createMember(memberData)

      // 更新本地状态
      members.value.unshift(newMember)
      pagination.value.total += 1

      // 刷新列表以确保一致性
      await fetchMembers()

      return newMember
    } catch (err: any) {
      error.value = err instanceof Error ? err.message : 'Validation failed'
      console.error('createMember error:', err)
      return null
    } finally {
      loading.value = false
    }
  }

  const updateMember = async (id: number, memberData: MemberUpdateRequest) => {
    try {
      loading.value = true
      error.value = null

      const updatedMember = await MembersApi.updateMember(id, memberData)

      // 更新本地状态
      const index = members.value.findIndex(member => member.id === id)
      if (index !== -1) {
        members.value[index] = { ...members.value[index], ...updatedMember }
      }

      // 更新当前成员
      if (currentMember.value?.id === id) {
        currentMember.value = { ...currentMember.value, ...updatedMember }
      }

      return updatedMember
    } catch (err: any) {
      error.value = err instanceof Error ? err.message : 'Update failed'
      console.error('updateMember error:', err)
      return null
    } finally {
      loading.value = false
    }
  }

  const deleteMember = async (id: number) => {
    try {
      loading.value = true
      error.value = null

      await MembersApi.deleteMember(id)

      // 更新本地状态
      members.value = members.value.filter(member => member.id !== id)
      pagination.value.total = Math.max(0, pagination.value.total - 1)

      // 清除当前成员
      if (currentMember.value?.id === id) {
        currentMember.value = null
      }

      return true
    } catch (err: any) {
      error.value = err instanceof Error ? err.message : 'Delete failed'
      console.error('deleteMember error:', err)
      return false
    } finally {
      loading.value = false
    }
  }

  const importMembers = async (importData: MemberImportRequest) => {
    try {
      loading.value = true
      error.value = null

      const result = await MembersApi.importMembers(importData)

      // 刷新列表
      await fetchMembers()

      return result
    } catch (err: any) {
      error.value = err instanceof Error ? err.message : 'Import failed'
      console.error('importMembers error:', err)
      return null
    } finally {
      loading.value = false
    }
  }

  const exportMembers = async (format: 'csv' | 'excel' = 'excel') => {
    try {
      loading.value = true
      error.value = null

      const blob = await MembersApi.exportMembers(format)

      // 创建下载链接
      const url = window.URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = `members.${format === 'csv' ? 'csv' : 'xlsx'}`
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      window.URL.revokeObjectURL(url)

      return true
    } catch (err: any) {
      error.value = err instanceof Error ? err.message : 'Export failed'
      console.error('exportMembers error:', err)
      return false
    } finally {
      loading.value = false
    }
  }

  const fetchStats = async () => {
    try {
      loading.value = true
      error.value = null

      const statsData = await MembersApi.getMemberStats()
      stats.value = statsData

      return statsData
    } catch (err: any) {
      error.value = err instanceof Error ? err.message : 'Failed to fetch stats'
      console.error('fetchStats error:', err)
      return null
    } finally {
      loading.value = false
    }
  }

  // 搜索和筛选
  const setSearchQuery = async (query: string) => {
    searchQuery.value = query
    pagination.value.page = 1
    await fetchMembers()
  }

  const setFilters = async (newFilters: Partial<MemberListParams>) => {
    filters.value = { ...filters.value, ...newFilters }
    pagination.value.page = 1
    await fetchMembers()
  }

  const clearFilters = async () => {
    filters.value = {}
    searchQuery.value = ''
    pagination.value.page = 1
    await fetchMembers()
  }

  // 分页
  const setPage = async (newPage: number) => {
    pagination.value.page = newPage
    await fetchMembers({ page: newPage, page_size: pagination.value.page_size })
  }

  const setPageSize = async (size: number) => {
    pagination.value.page_size = size
    pagination.value.page = 1
    await fetchMembers({ page: 1, page_size: size })
  }

  // 批量操作
  const batchUpdateStatus = async (memberIds: number[], isActive: boolean) => {
    try {
      loading.value = true
      error.value = null

      const promises = memberIds.map(id =>
        MembersApi.updateMember(id, { is_active: isActive })
      )
      const results = await Promise.allSettled(promises)

      // 更新本地状态
      members.value = members.value.map(member =>
        memberIds.includes(member.id)
          ? { ...member, is_active: isActive }
          : member
      )

      const successful = results.filter(r => r.status === 'fulfilled').length
      return successful === memberIds.length
    } catch (err: any) {
      error.value = err instanceof Error ? err.message : '批量更新失败'
      console.error('batchUpdateStatus error:', err)
      return false
    } finally {
      loading.value = false
    }
  }

  const batchDeleteMembers = async (memberIds: number[]) => {
    try {
      loading.value = true
      error.value = null

      const promises = memberIds.map(id => MembersApi.deleteMember(id))
      const results = await Promise.allSettled(promises)

      // 更新本地状态 - 只移除成功删除的
      const successful = results.filter(r => r.status === 'fulfilled')
      const successfulIds = memberIds.filter(
        (_, index) => results[index].status === 'fulfilled'
      )

      members.value = members.value.filter(
        member => !successfulIds.includes(member.id)
      )
      pagination.value.total -= successful.length

      return successful.length === memberIds.length
    } catch (err: any) {
      error.value = err instanceof Error ? err.message : '批量删除失败'
      console.error('batchDeleteMembers error:', err)
      return false
    } finally {
      loading.value = false
    }
  }

  // 状态管理
  const resetState = () => {
    members.value = []
    currentMember.value = null
    loading.value = false
    error.value = null
    stats.value = null
    pagination.value = { page: 1, page_size: 20, total: 0, total_pages: 0 }
    filters.value = {}
    searchQuery.value = ''
  }

  const clearError = () => {
    error.value = null
  }

  return {
    // 状态
    members,
    currentMember,
    loading,
    error,
    stats,
    pagination,
    searchQuery,
    filters,

    // 计算属性
    activeMembers,
    inactiveMembers,
    totalMembers,
    hasNextPage,
    hasPrevPage,

    // 核心Actions
    fetchMembers,
    fetchMemberDetail,
    createMember,
    updateMember,
    deleteMember,
    importMembers,
    exportMembers,
    fetchStats,

    // 搜索和筛选
    setSearchQuery,
    setFilters,
    clearFilters,

    // 分页管理
    setPage,
    setPageSize,

    // 批量操作
    batchUpdateStatus,
    batchDeleteMembers,

    // 状态管理
    resetState,
    clearError,

    // 兼容性别名
    getMembers: fetchMembers,
    getMemberDetail: fetchMemberDetail
  }
})
