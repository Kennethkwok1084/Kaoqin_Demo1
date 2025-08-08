import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { LoginRequest, LoginResponse, UserInfo } from '@/types/auth'
import { authApi } from '@/api/auth'
import { removeToken, setToken, getToken, setRefreshToken } from '@/utils/auth'
import router from '@/router'

export const useAuthStore = defineStore('auth', () => {
  // 状态
  const token = ref<string | null>(getToken())
  const userInfo = ref<UserInfo | null>(null)
  const isLoading = ref(false)

  // 计算属性
  const isAuthenticated = computed(() => !!token.value && !!userInfo.value)
  const isAdmin = computed(() => userInfo.value?.role === 'admin')
  const isGroupLeader = computed(() => userInfo.value?.role === 'group_leader')
  const hasPermission = computed(() => (permission: string) => {
    if (!userInfo.value) return false
    return userInfo.value.permissions?.includes(permission) || false
  })

  // 登录
  const login = async (credentials: LoginRequest): Promise<void> => {
    try {
      isLoading.value = true
      const response = await authApi.login(credentials)
      
      // 保存token和用户信息
      token.value = response.data.access_token
      userInfo.value = response.data.user
      setToken(response.data.access_token)
      setRefreshToken(response.data.refresh_token)
      
      // 检查是否需要完善信息
      if (response.data.user.needs_profile_completion) {
        await router.push('/auth/complete-profile')
      } else {
        // 跳转到首页或目标页面
        const redirect = router.currentRoute.value.query.redirect as string
        await router.push(redirect || '/')
      }
    } catch (error) {
      console.error('登录失败:', error)
      throw error
    } finally {
      isLoading.value = false
    }
  }

  // 登出
  const logout = async (): Promise<void> => {
    try {
      isLoading.value = true
      
      // 调用后端登出接口
      if (token.value) {
        await authApi.logout()
      }
    } catch (error) {
      console.error('登出请求失败:', error)
      // 即使后端请求失败，也要清除本地状态
    } finally {
      // 清除本地状态
      token.value = null
      userInfo.value = null
      removeToken()
      isLoading.value = false
      
      // 跳转到登录页
      await router.push('/login')
    }
  }

  // 获取用户信息
  const fetchUserInfo = async (): Promise<void> => {
    try {
      if (!token.value) {
        throw new Error('未找到认证token')
      }
      
      const response = await authApi.getUserInfo()
      userInfo.value = response
    } catch (error) {
      console.error('获取用户信息失败:', error)
      // 如果获取用户信息失败，可能是token过期，执行登出
      logout()
      throw error
    }
  }

  // 刷新token
  const refreshToken = async (): Promise<void> => {
    try {
      const response = await authApi.refreshToken()
      token.value = response.access_token
      setToken(response.access_token)
    } catch (error) {
      console.error('刷新token失败:', error)
      // token刷新失败，执行登出
      logout()
      throw error
    }
  }

  // 初始化认证状态
  const initAuth = async (): Promise<void> => {
    if (token.value) {
      try {
        await fetchUserInfo()
      } catch (error) {
        // 如果获取用户信息失败，清除token
        logout()
      }
    }
  }

  // 检查权限
  const checkPermission = (permission: string): boolean => {
    return hasPermission.value(permission)
  }

  // 检查是否需要完善信息
  const needsProfileCompletion = computed((): boolean => {
    return userInfo.value?.needs_profile_completion ?? false
  })

  // 刷新用户信息（用于信息完善后）
  const refreshUserInfo = async (): Promise<void> => {
    await fetchUserInfo()
  }

  // 检查角色
  const hasRole = (role: string): boolean => {
    return userInfo.value?.role === role
  }

  // 更新用户信息
  const updateUser = (updatedInfo: Partial<UserInfo>): void => {
    if (userInfo.value) {
      userInfo.value = { ...userInfo.value, ...updatedInfo }
    }
  }

  return {
    // 状态
    token,
    userInfo,
    isLoading,
    
    // 计算属性
    isAuthenticated,
    isAdmin,
    isGroupLeader,
    hasPermission,
    needsProfileCompletion,
    
    // 方法
    login,
    logout,
    fetchUserInfo,
    refreshUserInfo,
    refreshToken,
    initAuth,
    checkPermission,
    hasRole,
    updateUser
  }
})