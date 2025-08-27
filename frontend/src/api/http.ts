import axios, {
  type AxiosInstance,
  type AxiosRequestConfig,
  type AxiosResponse
} from 'axios'
import { ElMessage } from 'element-plus'
import { getToken, removeToken, isTokenExpired } from '@/utils/auth'
import router from '@/router'

// 创建axios实例
const http: AxiosInstance = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api/v1',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// 请求拦截器
http.interceptors.request.use(
  config => {
    const token = getToken()

    // 添加认证头
    if (token) {
      // 检查token是否过期
      if (isTokenExpired(token)) {
        // Token已过期，清除本地token并跳转到登录页
        removeToken()
        router.push('/login')
        return Promise.reject(new Error('Token已过期'))
      }

      config.headers.Authorization = `Bearer ${token}`
    }

    // 添加请求时间戳，防止IE缓存
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
    // 处理文件下载响应
    if (
      response.headers['content-type']?.includes('application/octet-stream') ||
      response.headers['content-type']?.includes('application/vnd.ms-excel') ||
      response.headers['content-type']?.includes(
        'application/vnd.openxmlformats'
      )
    ) {
      return response
    }

    return response
  },
  async error => {
    const { response } = error

    // 网络错误
    if (!response) {
      ElMessage.error('网络连接失败，请检查网络设置')
      return Promise.reject(error)
    }

    const { status } = response

    switch (status) {
      case 401:
        // 未认证或token过期
        ElMessage.error('登录已过期，请重新登录')
        removeToken()

        // 避免在登录页面重复跳转
        if (router.currentRoute.value.path !== '/login') {
          router.push({
            path: '/login',
            query: { redirect: router.currentRoute.value.fullPath }
          })
        }
        break

      case 403:
        // 无权限
        ElMessage.error('权限不足，无法访问该资源')
        break

      case 404:
        // 资源不存在
        ElMessage.error('请求的资源不存在')
        break

      case 422: {
        // 验证错误
        const validationErrors = response.data?.detail
        if (Array.isArray(validationErrors)) {
          const errorMessage = validationErrors
            .map((err: any) => `${err.loc?.join('.')}: ${err.msg}`)
            .join('、')
          ElMessage.error(`输入验证失败: ${errorMessage}`)
        } else {
          ElMessage.error('输入数据格式不正确')
        }
        break
      }

      case 429:
        // 请求频率限制
        ElMessage.error('请求过于频繁，请稍后再试')
        break

      case 500:
        // 服务器错误
        ElMessage.error('服务器内部错误，请联系管理员')
        break

      case 502:
      case 503:
      case 504:
        // 服务不可用
        ElMessage.error('服务暂时不可用，请稍后再试')
        break

      default: {
        // 其他错误
        const errorMessage =
          response.data?.message || response.data?.detail || '请求失败'
        ElMessage.error(errorMessage)
        break
      }
    }

    return Promise.reject(error)
  }
)

// 封装常用HTTP方法
export const httpRequest = {
  get<T = any>(
    url: string,
    config?: AxiosRequestConfig
  ): Promise<AxiosResponse<T>> {
    return http.get(url, config)
  },

  post<T = any>(
    url: string,
    data?: any,
    config?: AxiosRequestConfig
  ): Promise<AxiosResponse<T>> {
    return http.post(url, data, config)
  },

  put<T = any>(
    url: string,
    data?: any,
    config?: AxiosRequestConfig
  ): Promise<AxiosResponse<T>> {
    return http.put(url, data, config)
  },

  patch<T = any>(
    url: string,
    data?: any,
    config?: AxiosRequestConfig
  ): Promise<AxiosResponse<T>> {
    return http.patch(url, data, config)
  },

  delete<T = any>(
    url: string,
    config?: AxiosRequestConfig
  ): Promise<AxiosResponse<T>> {
    return http.delete(url, config)
  },

  upload<T = any>(
    url: string,
    file: File,
    config?: AxiosRequestConfig
  ): Promise<AxiosResponse<T>> {
    const formData = new FormData()
    formData.append('file', file)

    return http.post(url, formData, {
      ...config,
      headers: {
        'Content-Type': 'multipart/form-data',
        ...config?.headers
      }
    })
  },

  download(
    url: string,
    filename?: string,
    config?: AxiosRequestConfig
  ): Promise<void> {
    return http
      .get(url, {
        ...config,
        responseType: 'blob'
      })
      .then(response => {
        const blob = new Blob([response.data])
        const downloadUrl = window.URL.createObjectURL(blob)
        const link = document.createElement('a')
        link.href = downloadUrl
        link.download = filename || 'download'
        document.body.appendChild(link)
        link.click()
        document.body.removeChild(link)
        window.URL.revokeObjectURL(downloadUrl)
      })
  }
}

export { http }
export default http
