import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest'
import axios from 'axios'
import { ElMessage } from 'element-plus'
import { client, setupInterceptors } from '@/api/client'
import { useAuthStore } from '@/stores/auth'
import { createPinia, setActivePinia } from 'pinia'

// Mock Element Plus
vi.mock('element-plus', () => ({
  ElMessage: {
    error: vi.fn(),
    success: vi.fn(),
    warning: vi.fn(),
  },
}))

// Mock axios
vi.mock('axios', () => ({
  default: {
    create: vi.fn(),
    interceptors: {
      request: {
        use: vi.fn(),
      },
      response: {
        use: vi.fn(),
      },
    },
  },
}))

// Mock router
const mockRouterPush = vi.fn()
vi.mock('vue-router', () => ({
  useRouter: () => ({
    push: mockRouterPush,
  }),
}))

describe('API Client', () => {
  let mockAxiosInstance: any
  let authStore: any

  beforeEach(() => {
    setActivePinia(createPinia())
    authStore = useAuthStore()
    
    // 创建模拟的axios实例
    mockAxiosInstance = {
      defaults: { headers: { common: {} } },
      interceptors: {
        request: { use: vi.fn() },
        response: { use: vi.fn() },
      },
      get: vi.fn(),
      post: vi.fn(),
      put: vi.fn(),
      delete: vi.fn(),
      patch: vi.fn(),
    }
    
    vi.mocked(axios.create).mockReturnValue(mockAxiosInstance)
    
    // 清除所有mock调用
    vi.clearAllMocks()
  })

  afterEach(() => {
    vi.resetAllMocks()
  })

  describe('客户端初始化', () => {
    it('应该使用正确的基础URL创建axios实例', () => {
      expect(axios.create).toHaveBeenCalledWith({
        baseURL: expect.stringMatching(/\/api$/),
        timeout: expect.any(Number),
        headers: {
          'Content-Type': 'application/json',
        },
      })
    })

    it('应该设置默认超时时间', () => {
      const createCall = vi.mocked(axios.create).mock.calls[0]
      expect(createCall[0].timeout).toBe(30000) // 30秒
    })

    it('应该设置默认Content-Type', () => {
      const createCall = vi.mocked(axios.create).mock.calls[0]
      expect(createCall[0].headers['Content-Type']).toBe('application/json')
    })
  })

  describe('请求拦截器', () => {
    let requestInterceptor: Function

    beforeEach(() => {
      setupInterceptors()
      // 获取注册的请求拦截器
      const requestUseCall = mockAxiosInstance.interceptors.request.use.mock.calls[0]
      requestInterceptor = requestUseCall[0]
    })

    it('应该在有token时添加Authorization头', () => {
      authStore.token = 'test-token'
      
      const config = { headers: {} }
      const result = requestInterceptor(config)
      
      expect(result.headers['Authorization']).toBe('Bearer test-token')
    })

    it('应该在没有token时不添加Authorization头', () => {
      authStore.token = null
      
      const config = { headers: {} }
      const result = requestInterceptor(config)
      
      expect(result.headers['Authorization']).toBeUndefined()
    })

    it('应该保留现有的请求头', () => {
      authStore.token = 'test-token'
      
      const config = {
        headers: {
          'Custom-Header': 'custom-value',
        },
      }
      const result = requestInterceptor(config)
      
      expect(result.headers['Custom-Header']).toBe('custom-value')
      expect(result.headers['Authorization']).toBe('Bearer test-token')
    })

    it('应该处理没有headers的配置', () => {
      authStore.token = 'test-token'
      
      const config = {}
      const result = requestInterceptor(config)
      
      expect(result.headers['Authorization']).toBe('Bearer test-token')
    })
  })

  describe('响应拦截器', () => {
    let responseInterceptor: Function
    let responseErrorHandler: Function

    beforeEach(() => {
      setupInterceptors()
      // 获取注册的响应拦截器
      const responseUseCall = mockAxiosInstance.interceptors.response.use.mock.calls[0]
      responseInterceptor = responseUseCall[0]
      responseErrorHandler = responseUseCall[1]
    })

    it('应该直接返回成功响应', () => {
      const response = { data: { message: 'success' }, status: 200 }
      const result = responseInterceptor(response)
      
      expect(result).toBe(response)
    })

    it('应该处理401未授权错误', async () => {
      const error = {
        response: {
          status: 401,
          data: { message: '未授权' }
        }
      }
      
      try {
        await responseErrorHandler(error)
      } catch (e) {
        // 预期会抛出错误
      }
      
      expect(ElMessage.error).toHaveBeenCalledWith('登录已过期，请重新登录')
      expect(mockRouterPush).toHaveBeenCalledWith('/login')
    })

    it('应该处理403权限不足错误', async () => {
      const error = {
        response: {
          status: 403,
          data: { message: '权限不足' }
        }
      }
      
      try {
        await responseErrorHandler(error)
      } catch (e) {
        // 预期会抛出错误
      }
      
      expect(ElMessage.error).toHaveBeenCalledWith('权限不足，无法访问该资源')
    })

    it('应该处理404未找到错误', async () => {
      const error = {
        response: {
          status: 404,
          data: { message: '资源未找到' }
        }
      }
      
      try {
        await responseErrorHandler(error)
      } catch (e) {
        // 预期会抛出错误
      }
      
      expect(ElMessage.error).toHaveBeenCalledWith('请求的资源不存在')
    })

    it('应该处理422数据验证错误', async () => {
      const error = {
        response: {
          status: 422,
          data: { 
            message: '数据验证失败',
            detail: [
              { field: 'username', message: '用户名不能为空' },
              { field: 'password', message: '密码长度不足' }
            ]
          }
        }
      }
      
      try {
        await responseErrorHandler(error)
      } catch (e) {
        // 预期会抛出错误
      }
      
      expect(ElMessage.error).toHaveBeenCalledWith('数据验证失败：用户名不能为空; 密码长度不足')
    })

    it('应该处理500服务器错误', async () => {
      const error = {
        response: {
          status: 500,
          data: { message: '服务器内部错误' }
        }
      }
      
      try {
        await responseErrorHandler(error)
      } catch (e) {
        // 预期会抛出错误
      }
      
      expect(ElMessage.error).toHaveBeenCalledWith('服务器错误，请稍后重试')
    })

    it('应该处理网络错误', async () => {
      const error = {
        request: {},
        message: 'Network Error'
      }
      
      try {
        await responseErrorHandler(error)
      } catch (e) {
        // 预期会抛出错误
      }
      
      expect(ElMessage.error).toHaveBeenCalledWith('网络连接失败，请检查网络设置')
    })

    it('应该处理请求超时错误', async () => {
      const error = {
        code: 'ECONNABORTED',
        message: 'timeout of 30000ms exceeded'
      }
      
      try {
        await responseErrorHandler(error)
      } catch (e) {
        // 预期会抛出错误
      }
      
      expect(ElMessage.error).toHaveBeenCalledWith('请求超时，请稍后重试')
    })

    it('应该处理取消的请求', async () => {
      const error = {
        message: 'Request canceled'
      }
      
      try {
        await responseErrorHandler(error)
      } catch (e) {
        // 预期会抛出错误
      }
      
      // 取消的请求不应该显示错误消息
      expect(ElMessage.error).not.toHaveBeenCalled()
    })

    it('应该处理未知错误', async () => {
      const error = {
        message: 'Unknown error'
      }
      
      try {
        await responseErrorHandler(error)
      } catch (e) {
        // 预期会抛出错误
      }
      
      expect(ElMessage.error).toHaveBeenCalledWith('请求失败，请稍后重试')
    })
  })

  describe('请求方法', () => {
    beforeEach(() => {
      setupInterceptors()
    })

    it('应该支持GET请求', async () => {
      mockAxiosInstance.get.mockResolvedValue({ data: { success: true } })
      
      await client.get('/test')
      
      expect(mockAxiosInstance.get).toHaveBeenCalledWith('/test')
    })

    it('应该支持POST请求', async () => {
      mockAxiosInstance.post.mockResolvedValue({ data: { success: true } })
      
      const data = { name: 'test' }
      await client.post('/test', data)
      
      expect(mockAxiosInstance.post).toHaveBeenCalledWith('/test', data)
    })

    it('应该支持PUT请求', async () => {
      mockAxiosInstance.put.mockResolvedValue({ data: { success: true } })
      
      const data = { name: 'updated' }
      await client.put('/test/1', data)
      
      expect(mockAxiosInstance.put).toHaveBeenCalledWith('/test/1', data)
    })

    it('应该支持DELETE请求', async () => {
      mockAxiosInstance.delete.mockResolvedValue({ data: { success: true } })
      
      await client.delete('/test/1')
      
      expect(mockAxiosInstance.delete).toHaveBeenCalledWith('/test/1')
    })

    it('应该支持PATCH请求', async () => {
      mockAxiosInstance.patch.mockResolvedValue({ data: { success: true } })
      
      const data = { name: 'patched' }
      await client.patch('/test/1', data)
      
      expect(mockAxiosInstance.patch).toHaveBeenCalledWith('/test/1', data)
    })
  })

  describe('自动重试机制', () => {
    it('应该在网络错误时重试', async () => {
      const networkError = new Error('Network Error')
      networkError.code = 'ENOTFOUND'
      
      mockAxiosInstance.get
        .mockRejectedValueOnce(networkError)
        .mockRejectedValueOnce(networkError)
        .mockResolvedValue({ data: { success: true } })
      
      const response = await client.get('/test')
      
      expect(mockAxiosInstance.get).toHaveBeenCalledTimes(3)
      expect(response.data.success).toBe(true)
    })

    it('应该在5xx错误时重试', async () => {
      const serverError = {
        response: { status: 500 },
        message: 'Server Error'
      }
      
      mockAxiosInstance.get
        .mockRejectedValueOnce(serverError)
        .mockRejectedValueOnce(serverError)
        .mockResolvedValue({ data: { success: true } })
      
      const response = await client.get('/test')
      
      expect(mockAxiosInstance.get).toHaveBeenCalledTimes(3)
      expect(response.data.success).toBe(true)
    })

    it('应该在达到最大重试次数后停止', async () => {
      const networkError = new Error('Network Error')
      networkError.code = 'ENOTFOUND'
      
      mockAxiosInstance.get.mockRejectedValue(networkError)
      
      try {
        await client.get('/test')
      } catch (error) {
        // 预期会抛出错误
      }
      
      expect(mockAxiosInstance.get).toHaveBeenCalledTimes(3) // 1次初始 + 2次重试
    })

    it('应该在4xx错误时不重试', async () => {
      const clientError = {
        response: { status: 400 },
        message: 'Bad Request'
      }
      
      mockAxiosInstance.get.mockRejectedValue(clientError)
      
      try {
        await client.get('/test')
      } catch (error) {
        // 预期会抛出错误
      }
      
      expect(mockAxiosInstance.get).toHaveBeenCalledTimes(1) // 只调用1次，不重试
    })
  })

  describe('请求取消', () => {
    it('应该支持取消请求', () => {
      const source = axios.CancelToken?.source()
      if (source) {
        mockAxiosInstance.get.mockImplementation(() => 
          Promise.reject({ message: 'Request canceled' })
        )
        
        client.get('/test', { cancelToken: source.token })
        source.cancel('Operation canceled by the user.')
        
        expect(mockAxiosInstance.get).toHaveBeenCalled()
      }
    })
  })
})