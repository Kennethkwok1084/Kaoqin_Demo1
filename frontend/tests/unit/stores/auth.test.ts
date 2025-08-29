import { describe, it, expect, beforeEach, vi } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useAuthStore } from '@/stores/auth'
import { authApi } from '@/api/auth'

// Auth API is already mocked in setup.ts - no need to mock again

describe('Auth Store', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
    localStorage.clear()
  })

  describe('initial state', () => {
    it('should have correct initial state', () => {
      const authStore = useAuthStore()

      expect(authStore.isAuthenticated).toBe(false)
      expect(authStore.userInfo).toBeNull()
      expect(authStore.token).toBeNull()
      expect(authStore.refreshToken).toBeNull()
    })
  })

  describe('login', () => {
    it('should login successfully', async () => {
      const mockLoginResponse = {
        success: true,
        message: 'Login successful',
        data: {
          access_token: 'test-access-token',
          refresh_token: 'test-refresh-token',
          token_type: 'Bearer',
          expires_in: 3600,
          user: {
            id: 1,
            username: 'testuser',
            full_name: '测试用户',
            email: 'test@example.com',
            role: 'user',
            is_active: true
          }
        }
      }

      vi.mocked(authApi.login).mockResolvedValue(mockLoginResponse)

      const authStore = useAuthStore()
      const result = await authStore.login('testuser', 'password')

      expect(result).toBe(true)
      expect(authStore.isAuthenticated).toBe(true)
      expect(authStore.token).toBe('test-access-token')
      expect(authStore.refreshToken).toBe('test-refresh-token')
      expect(authStore.userInfo).toEqual(mockLoginResponse.data.user)
      expect(localStorage.setItem).toHaveBeenCalledWith(
        'access_token',
        'test-access-token'
      )
      expect(localStorage.setItem).toHaveBeenCalledWith(
        'refresh_token',
        'test-refresh-token'
      )
    })

    it('should handle login failure', async () => {
      const mockError = new Error('Invalid credentials')
      vi.mocked(authApi.login).mockRejectedValue(mockError)

      const authStore = useAuthStore()
      const result = await authStore.login('testuser', 'wrongpassword')

      expect(result).toBe(false)
      expect(authStore.isAuthenticated).toBe(false)
      expect(authStore.token).toBeNull()
      expect(authStore.userInfo).toBeNull()
    })
  })

  describe('logout', () => {
    it('should logout successfully', async () => {
      vi.mocked(authApi.logout).mockResolvedValue()

      const authStore = useAuthStore()
      // 先设置登录状态
      authStore.token = 'test-token'
      authStore.userInfo = { id: 1, username: 'testuser' } as any

      await authStore.logout()

      expect(authStore.isAuthenticated).toBe(false)
      expect(authStore.token).toBeNull()
      expect(authStore.userInfo).toBeNull()
      expect(localStorage.removeItem).toHaveBeenCalledWith('access_token')
      expect(localStorage.removeItem).toHaveBeenCalledWith('refresh_token')
    })
  })

  describe('initializeAuth', () => {
    it('should initialize auth from localStorage', async () => {
      const mockUserInfo = {
        id: 1,
        username: 'testuser',
        full_name: '测试用户',
        email: 'test@example.com',
        role: 'user',
        is_active: true
      }

      localStorage.setItem('access_token', 'stored-token')
      localStorage.setItem('refresh_token', 'stored-refresh-token')
      vi.mocked(authApi.getCurrentUser).mockResolvedValue(mockUserInfo)

      const authStore = useAuthStore()
      await authStore.initializeAuth()

      expect(authStore.isAuthenticated).toBe(true)
      expect(authStore.token).toBe('stored-token')
      expect(authStore.refreshToken).toBe('stored-refresh-token')
      expect(authStore.userInfo).toEqual(mockUserInfo)
    })

    it('should clear auth if token is invalid', async () => {
      localStorage.setItem('access_token', 'invalid-token')
      vi.mocked(authApi.getCurrentUser).mockRejectedValue(
        new Error('Invalid token')
      )

      const authStore = useAuthStore()
      await authStore.initializeAuth()

      expect(authStore.isAuthenticated).toBe(false)
      expect(authStore.token).toBeNull()
      expect(localStorage.removeItem).toHaveBeenCalledWith('access_token')
      expect(localStorage.removeItem).toHaveBeenCalledWith('refresh_token')
    })
  })

  describe('refreshAuthToken', () => {
    it('should refresh token successfully', async () => {
      const mockRefreshResponse = {
        access_token: 'new-access-token',
        refresh_token: 'new-refresh-token',
        token_type: 'Bearer',
        expires_in: 3600
      }

      vi.mocked(authApi.refreshToken).mockResolvedValue(mockRefreshResponse)

      const authStore = useAuthStore()
      authStore.refreshToken = 'old-refresh-token'

      const result = await authStore.refreshAuthToken()

      expect(result).toBe(true)
      expect(authStore.token).toBe('new-access-token')
      expect(authStore.refreshToken).toBe('new-refresh-token')
    })

    it('should handle refresh token failure', async () => {
      vi.mocked(authApi.refreshToken).mockRejectedValue(
        new Error('Refresh token expired')
      )

      const authStore = useAuthStore()
      authStore.refreshToken = 'expired-refresh-token'

      const result = await authStore.refreshAuthToken()

      expect(result).toBe(false)
      expect(authStore.isAuthenticated).toBe(false)
      expect(authStore.token).toBeNull()
    })
  })

  describe('computed properties', () => {
    it('should correctly compute isAdmin', () => {
      const authStore = useAuthStore()

      // 非管理员用户
      authStore.userInfo = { role: 'user' } as any
      expect(authStore.isAdmin).toBe(false)

      // 管理员用户
      authStore.userInfo = { role: 'admin' } as any
      expect(authStore.isAdmin).toBe(true)

      // 组长用户
      authStore.userInfo = { role: 'team_leader' } as any
      expect(authStore.isAdmin).toBe(true)
    })

    it('should correctly compute userRole', () => {
      const authStore = useAuthStore()

      authStore.userInfo = { role: 'user' } as any
      expect(authStore.userRole).toBe('user')

      authStore.userInfo = null
      expect(authStore.userRole).toBe('')
    })
  })
})
