import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { LoginRequest, UserInfo } from '@/types/auth'
import { authApi } from '@/api/auth'
import { removeToken, setToken, getToken, setRefreshToken } from '@/utils/auth'
import router from '@/router'

export const useAuthStore = defineStore('auth', () => {
  // 状态
  const token = ref<string | null>(getToken())
  const refreshTokenRef = ref<string | null>(
    typeof localStorage !== 'undefined'
      ? localStorage.getItem('refresh_token')
      : null
  )
  const userInfo = ref<UserInfo | null>(null)
  const isLoading = ref(false)

  // 计算属性
  const isAuthenticated = computed(() => !!token.value && !!userInfo.value)
  const isAdmin = computed(() => {
    const role = userInfo.value?.role
    return role === 'admin' || role === 'group_leader'
  })
  const isGroupLeader = computed(() => userInfo.value?.role === 'group_leader')
  const hasPermission = computed(() => (permission: string) => {
    if (!userInfo.value) return false
    return userInfo.value.permissions?.includes(permission) || false
  })

  // 登录
  const login = async (
    usernameOrEmail: string | LoginRequest,
    password?: string
  ): Promise<boolean> => {
    let credentials: LoginRequest

    // 支持两种调用方式：login(credentials) 或 login(username, password)
    if (typeof usernameOrEmail === 'string' && password) {
      credentials = { student_id: usernameOrEmail, username: usernameOrEmail, password }
    } else {
      credentials = usernameOrEmail as LoginRequest
    }
    try {
      isLoading.value = true
      const response = await authApi.login(credentials)

      // 保存token和用户信息
      token.value = response.data.access_token
      refreshTokenRef.value = response.data.refresh_token
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

      return true
    } catch (error) {
      console.error('登录失败:', error)
      return false
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
      refreshTokenRef.value = null
      userInfo.value = null
      removeToken()
      if (typeof localStorage !== 'undefined') {
        localStorage.removeItem('refresh_token')
      }
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
      if (response.refresh_token) {
        refreshTokenRef.value = response.refresh_token
        setRefreshToken(response.refresh_token)
      }
    } catch (error) {
      console.error('刷新token失败:', error)
      // token刷新失败，执行登出
      logout()
      throw error
    }
  }

  // refreshAuthToken 方法 - 测试期望的返回 boolean
  const refreshAuthToken = async (): Promise<boolean> => {
    try {
      const response = await authApi.refreshToken()
      token.value = response.access_token
      setToken(response.access_token)
      if (response.refresh_token) {
        refreshTokenRef.value = response.refresh_token
        setRefreshToken(response.refresh_token)
      }
      return true
    } catch (error) {
      console.error('刷新token失败:', error)
      // token刷新失败，执行登出
      logout()
      return false
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

  // initializeAuth 方法 - 测试兼容性别名
  const initializeAuth = async (): Promise<void> => {
    const storedToken = getToken()
    const storedRefreshToken =
      typeof localStorage !== 'undefined'
        ? localStorage.getItem('refresh_token')
        : null

    if (storedToken) {
      token.value = storedToken
      if (storedRefreshToken) {
        // 设置refreshToken的ref值
        refreshTokenRef.value = storedRefreshToken
      }

      try {
        const userInfoData = await authApi.getCurrentUser()
        userInfo.value = userInfoData
      } catch (error) {
        // token无效，清除认证状态
        token.value = null
        refreshTokenRef.value = null
        userInfo.value = null
        removeToken()
        if (typeof localStorage !== 'undefined') {
          localStorage.removeItem('refresh_token')
        }
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
    refreshToken: refreshTokenRef,
    userInfo,
    isLoading,

    // 计算属性
    isAuthenticated,
    isAdmin,
    isGroupLeader,
    hasPermission,
    needsProfileCompletion,
    userRole: computed(() => userInfo.value?.role || ''), // 测试期望的计算属性

    // 方法
    login,
    logout,
    refreshTokenMethod: refreshAuthToken, // 重命名以避免冲突
    fetchUserInfo,
    refreshUserInfo,
    initAuth,
    initializeAuth, // 测试期望的别名
    checkPermission,
    hasRole,
    updateUser
  }
})
