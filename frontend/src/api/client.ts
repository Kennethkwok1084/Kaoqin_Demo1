// HTTP 客户端配置 - 统一消息管理

import axios, {
  type AxiosInstance,
  type AxiosResponse,
  type AxiosError
} from 'axios'
import { ElMessage } from 'element-plus'
import { getToken, removeToken } from '@/utils/auth'
import router from '@/router'
import { MessageManager, MESSAGES } from '@/constants/messages'

// 创建axios实例
export const http: AxiosInstance = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api/v1',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// 请求拦截器
http.interceptors.request.use(
  config => {
    // 添加认证令牌
    const token = getToken()
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }

    // 添加请求时间戳（防止IE缓存）
    if (config.method === 'get') {
      config.params = {
        ...config.params,
        _t: Date.now()
      }
    }

    return config
  },
  error => {
    console.error('请求拦截器错误:', error)
    ElMessage.error(MESSAGES.NETWORK_ERROR_CONNECTION)
    return Promise.reject(error)
  }
)

// 响应拦截器
http.interceptors.response.use(
  (response: AxiosResponse) => {
    // 统一处理API响应格式
    const { data } = response

    // 如果是标准API响应格式，直接返回
    if (
      data &&
      typeof data === 'object' &&
      'success' in data &&
      'message' in data &&
      'data' in data
    ) {
      return response
    }

    // 如果不是标准格式，包装成标准格式
    response.data = {
      success: true,
      message: 'Success',
      data: data
    }

    return response
  },
  (error: AxiosError) => {
    console.error('响应拦截器错误:', error)

    // 处理网络错误
    if (!error.response) {
      ElMessage.error(MESSAGES.NETWORK_ERROR_CONNECTION)
      return Promise.reject(error)
    }

    const { status, data } = error.response
    const serverMessage = (data as any)?.message

    // 优先使用服务器返回的消息，否则使用统一消息管理
    let displayMessage: string

    if (serverMessage) {
      // 如果服务器有返回消息，直接使用
      displayMessage = serverMessage
    } else {
      // 使用统一的HTTP错误消息
      displayMessage = MessageManager.getHttpErrorMessage(status)
    }

    switch (status) {
      case 400:
        ElMessage.error(displayMessage)
        break

      case 401:
        ElMessage.error(displayMessage)
        removeToken()
        router.replace('/login')
        break

      case 403:
        ElMessage.error(displayMessage)
        router.replace('/403')
        break

      case 404:
        ElMessage.error(displayMessage)
        break

      case 422:
        // 表单验证错误
        if ((data as any)?.details?.field_errors) {
          const errors = (data as any).details.field_errors
          const errorMessages = Object.values(errors).flat().join('; ')
          ElMessage.error(`${MESSAGES.HTTP_ERROR_422}: ${errorMessages}`)
        } else {
          ElMessage.error(displayMessage)
        }
        break

      case 429:
        ElMessage.error(displayMessage)
        break

      case 500:
        ElMessage.error(displayMessage)
        break

      case 502:
        ElMessage.error(displayMessage)
        break

      case 503:
        ElMessage.error(displayMessage)
        break

      case 504:
        ElMessage.error(displayMessage)
        break

      default:
        ElMessage.error(displayMessage)
    }

    return Promise.reject(error)
  }
)

// 导出便捷方法
export const api = {
  get: <T = any>(url: string, config?: any) => http.get<T>(url, config),

  post: <T = any>(url: string, data?: any, config?: any) =>
    http.post<T>(url, data, config),

  put: <T = any>(url: string, data?: any, config?: any) =>
    http.put<T>(url, data, config),

  patch: <T = any>(url: string, data?: any, config?: any) =>
    http.patch<T>(url, data, config),

  delete: <T = any>(url: string, config?: any) => http.delete<T>(url, config),

  // 文件下载方法
  download: async (url: string, filename?: string, config?: any) => {
    try {
      const response = await http.get(url, {
        ...config,
        responseType: 'blob'
      })
      
      // 创建下载链接
      const blob = new Blob([response.data])
      const downloadUrl = window.URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = downloadUrl
      link.download = filename || 'download'
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      window.URL.revokeObjectURL(downloadUrl)
    } catch (error) {
      console.error('文件下载失败:', error)
      ElMessage.error('文件下载失败')
      throw error
    }
  }
}

// 扩展http实例，添加download方法
Object.assign(http, {
  download: api.download
})

export default http
