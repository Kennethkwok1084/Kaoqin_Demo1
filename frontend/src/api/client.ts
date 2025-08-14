// HTTP 客户端配置

import axios, {
  type AxiosInstance,
  type AxiosResponse,
  type AxiosError
} from 'axios'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getToken, removeToken } from '@/utils/auth'
import router from '@/router'

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
    return Promise.reject(error)
  }
)

// 响应拦截器
http.interceptors.response.use(
  (response: AxiosResponse) => {
    // 成功响应直接返回
    return response
  },
  (error: AxiosError) => {
    console.error('响应拦截器错误:', error)

    // 处理网络错误
    if (!error.response) {
      ElMessage.error('网络连接失败，请检查网络设置')
      return Promise.reject(error)
    }

    const { status, data } = error.response
    const message = (data as any)?.message || '请求失败'

    switch (status) {
      case 400:
        ElMessage.error(`请求错误: ${message}`)
        break

      case 401:
        ElMessage.error('登录已过期，请重新登录')
        removeToken()
        router.replace('/login')
        break

      case 403:
        ElMessage.error('权限不足，无法访问')
        router.replace('/403')
        break

      case 404:
        ElMessage.error('请求的资源不存在')
        break

      case 422:
        // 表单验证错误
        if ((data as any)?.errors) {
          const errors = (data as any).errors
          const errorMessages = Object.values(errors).flat().join('; ')
          ElMessage.error(`表单验证失败: ${errorMessages}`)
        } else {
          ElMessage.error(`验证失败: ${message}`)
        }
        break

      case 429:
        ElMessage.error('请求过于频繁，请稍后再试')
        break

      case 500:
        ElMessage.error('服务器内部错误')
        break

      case 502:
        ElMessage.error('网关错误')
        break

      case 503:
        ElMessage.error('服务暂时不可用')
        break

      case 504:
        ElMessage.error('网关超时')
        break

      default:
        ElMessage.error(`请求失败 (${status}): ${message}`)
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

  delete: <T = any>(url: string, config?: any) => http.delete<T>(url, config)
}

export default http
