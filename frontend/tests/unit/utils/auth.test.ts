import { describe, it, expect, beforeEach } from 'vitest'
import {
  getToken,
  setToken,
  removeToken,
  getRefreshToken,
  setRefreshToken,
  removeRefreshToken,
  isTokenExpired,
  parseJWT,
  clearAuthData
} from '@/utils/auth'

describe('Auth Utils', () => {
  beforeEach(() => {
    localStorage.clear()
    sessionStorage.clear()
  })

  describe('token management', () => {
    it('should get and set access token', () => {
      expect(getToken()).toBeNull()

      setToken('test-token')
      expect(getToken()).toBe('test-token')
      expect(localStorage.getItem('access_token')).toBe('test-token')
    })

    it('should remove access token', () => {
      setToken('test-token')
      expect(getToken()).toBe('test-token')

      removeToken()
      expect(getToken()).toBeNull()
      expect(localStorage.getItem('access_token')).toBeNull()
    })

    it('should get and set refresh token', () => {
      expect(getRefreshToken()).toBeNull()

      setRefreshToken('test-refresh-token')
      expect(getRefreshToken()).toBe('test-refresh-token')
      expect(localStorage.getItem('refresh_token')).toBe('test-refresh-token')
    })

    it('should remove refresh token', () => {
      setRefreshToken('test-refresh-token')
      expect(getRefreshToken()).toBe('test-refresh-token')

      removeRefreshToken()
      expect(getRefreshToken()).toBeNull()
      expect(localStorage.getItem('refresh_token')).toBeNull()
    })

    it('should clear all auth data', () => {
      setToken('test-token')
      setRefreshToken('test-refresh-token')

      clearAuthData()

      expect(getToken()).toBeNull()
      expect(getRefreshToken()).toBeNull()
    })
  })

  describe('JWT parsing', () => {
    it('should parse valid JWT token', () => {
      // 创建一个测试用的JWT token (header.payload.signature)
      const payload = {
        sub: '123',
        name: 'Test User',
        iat: Math.floor(Date.now() / 1000),
        exp: Math.floor(Date.now() / 1000) + 3600
      }

      const encodedPayload = btoa(JSON.stringify(payload))
      const mockToken = `header.${encodedPayload}.signature`

      const decoded = parseJWT(mockToken)
      expect(decoded).toEqual(payload)
    })

    it('should return null for invalid JWT token', () => {
      expect(parseJWT('invalid-token')).toBeNull()
      expect(parseJWT('')).toBeNull()
      expect(parseJWT('header.invalid-payload.signature')).toBeNull()
    })

    it('should handle malformed JWT token', () => {
      expect(parseJWT('header.payload')).toBeNull()
      expect(parseJWT('header')).toBeNull()
    })
  })

  describe('token expiration', () => {
    it('should detect expired token', () => {
      const expiredPayload = {
        exp: Math.floor(Date.now() / 1000) - 3600 // 1小时前过期
      }
      const encodedPayload = btoa(JSON.stringify(expiredPayload))
      const expiredToken = `header.${encodedPayload}.signature`

      expect(isTokenExpired(expiredToken)).toBe(true)
    })

    it('should detect valid token', () => {
      const validPayload = {
        exp: Math.floor(Date.now() / 1000) + 3600 // 1小时后过期
      }
      const encodedPayload = btoa(JSON.stringify(validPayload))
      const validToken = `header.${encodedPayload}.signature`

      expect(isTokenExpired(validToken)).toBe(false)
    })

    it('should handle token without exp claim', () => {
      const payloadWithoutExp = {
        sub: '123',
        name: 'Test User'
      }
      const encodedPayload = btoa(JSON.stringify(payloadWithoutExp))
      const tokenWithoutExp = `header.${encodedPayload}.signature`

      expect(isTokenExpired(tokenWithoutExp)).toBe(true)
    })

    it('should handle invalid token in expiration check', () => {
      expect(isTokenExpired('invalid-token')).toBe(true)
      expect(isTokenExpired('')).toBe(true)
      expect(isTokenExpired(null as any)).toBe(true)
    })
  })

  describe('edge cases', () => {
    it('should handle localStorage not available', () => {
      // Mock localStorage to throw error
      const originalLocalStorage = global.localStorage
      delete (global as any).localStorage

      expect(() => getToken()).not.toThrow()
      expect(() => setToken('test')).not.toThrow()

      // Restore localStorage
      global.localStorage = originalLocalStorage
    })

    it('should handle JSON parse errors gracefully', () => {
      // 创建一个包含无效JSON的伪JWT
      const invalidPayload = btoa('invalid json {')
      const invalidToken = `header.${invalidPayload}.signature`

      expect(parseJWT(invalidToken)).toBeNull()
    })
  })
})
