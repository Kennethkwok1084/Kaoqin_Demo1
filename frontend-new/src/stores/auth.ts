// 认证状态管理
import { defineStore } from 'pinia'
import { ref, computed, readonly } from 'vue'
import type { User } from '@/api/client'
import { api, tokenManager } from '@/api/client'

export const useAuthStore = defineStore('auth', () => {
  // 状态
  const user = ref<User | null>(null)
  const loading = ref(false)
  const error = ref<string | null>(null)

  // 计算属性
  const isAuthenticated = computed(() => !!user.value && !!tokenManager.getAccessToken())
  const isAdmin = computed(() => user.value?.role === 'admin')
  const isGroupLeader = computed(() => user.value?.role === 'group_leader')
  const canManageMembers = computed(() => isAdmin.value || isGroupLeader.value)

  // 用户权限
  const permissions = computed(() => ({
    isAdmin: user.value?.permissions?.isAdmin ?? false,
    isGroupLeader: user.value?.permissions?.isGroupLeader ?? false,
    canManageGroup: user.value?.permissions?.canManageGroup ?? false,
    canImportData: user.value?.permissions?.canImportData ?? false,
    canMarkRushTasks: user.value?.permissions?.canMarkRushTasks ?? false
  }))

  // 动作
  async function login(credentials: { studentId: string; password: string; rememberMe?: boolean }) {
    loading.value = true
    error.value = null

    try {
      const response = await api.login(credentials)
      
      if (response.success && response.data) {
        // 保存tokens
        tokenManager.setTokens(response.data.accessToken, response.data.refreshToken)
        
        // 设置用户信息
        user.value = response.data.user
        
        return { success: true, message: response.message }
      } else {
        throw new Error(response.message || '登录失败')
      }
    } catch (err: any) {
      error.value = err.message || '登录失败，请检查网络连接'
      return { success: false, message: error.value }
    } finally {
      loading.value = false
    }
  }

  async function logout() {
    loading.value = true
    
    try {
      await api.logout()
    } catch (err) {
      console.error('Logout API call failed:', err)
    } finally {
      // 无论API调用是否成功，都清除本地状态
      user.value = null
      tokenManager.clearTokens()
      loading.value = false
    }
  }

  async function getCurrentUser() {
    if (!tokenManager.getAccessToken()) {
      return false
    }

    loading.value = true
    error.value = null

    try {
      const response = await api.getCurrentUser()
      
      if (response.success && response.data) {
        user.value = response.data
        return true
      } else {
        throw new Error('获取用户信息失败')
      }
    } catch (err: any) {
      error.value = err.message
      // Token可能已过期，尝试刷新
      const refreshed = await tokenManager.refreshTokenIfNeeded()
      if (refreshed) {
        return getCurrentUser() // 递归重试
      }
      
      // 刷新失败，清除认证状态
      await logout()
      return false
    } finally {
      loading.value = false
    }
  }

  async function changePassword(currentPassword: string, newPassword: string) {
    loading.value = true
    error.value = null

    try {
      // 这里需要添加修改密码的API调用
      // const response = await api.changePassword({ currentPassword, newPassword })
      // 临时模拟
      await new Promise(resolve => setTimeout(resolve, 1000))
      return { success: true, message: '密码修改成功' }
    } catch (err: any) {
      error.value = err.message || '密码修改失败'
      return { success: false, message: error.value }
    } finally {
      loading.value = false
    }
  }

  // 初始化认证状态
  async function initializeAuth() {
    const token = tokenManager.getAccessToken()
    if (token) {
      await getCurrentUser()
    }
  }

  // 检查权限
  function hasPermission(permission: string): boolean {
    if (!user.value) return false
    
    switch (permission) {
      case 'admin':
        return isAdmin.value
      case 'manage_members':
        return canManageMembers.value
      case 'import_data':
        return permissions.value.canImportData
      case 'mark_rush_tasks':
        return permissions.value.canMarkRushTasks
      default:
        return false
    }
  }

  // 清除错误
  function clearError() {
    error.value = null
  }

  return {
    // 状态
    user: readonly(user),
    loading: readonly(loading),
    error: readonly(error),
    
    // 计算属性
    isAuthenticated,
    isAdmin,
    isGroupLeader,
    canManageMembers,
    permissions,
    
    // 动作
    login,
    logout,
    getCurrentUser,
    changePassword,
    initializeAuth,
    hasPermission,
    clearError
  }
})