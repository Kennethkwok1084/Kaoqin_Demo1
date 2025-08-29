// frontend/tests/setup.ts
import { vi } from 'vitest'
import { config } from '@vue/test-utils'

// =========================
// 1. 完整API Mock配置
// =========================
// 统计API使用手动Mock文件，在tests/__mocks__/@/api/statistics.ts中定义

vi.mock('@/api/auth', () => {
  const mockAuthApi = {
    login: vi.fn(() => Promise.resolve({
      success: true,
      message: 'Login successful',
      data: {
        access_token: 'mock_access_token',
        refresh_token: 'mock_refresh_token',
        token_type: 'Bearer',
        expires_in: 3600,
        user: {
          id: 1,
          name: '测试用户',
          email: 'test@example.com',
          role: 'user',
          permissions: ['read']
        }
      }
    })),
    logout: vi.fn(() => Promise.resolve()),
    refreshToken: vi.fn(() => Promise.resolve({
      access_token: 'new_mock_token',
      refresh_token: 'new_refresh_token'
    })),
    getUserInfo: vi.fn(() => Promise.resolve({
      id: 1,
      name: '测试用户',
      email: 'test@example.com',
      role: 'user',
      permissions: ['read']
    })),
    changePassword: vi.fn(() => Promise.resolve()),
    requestResetPassword: vi.fn(() => Promise.resolve()),
    confirmResetPassword: vi.fn(() => Promise.resolve()),
    validateToken: vi.fn(() => Promise.resolve({ valid: true })),
    getUserPermissions: vi.fn(() => Promise.resolve({ permissions: ['read'] }))
  }
  
  return {
    authApi: mockAuthApi
  }
})

vi.mock('@/api/tasks', () => {
  const mockTasks = vi.fn(() => Promise.resolve({ items: [], total: 0, page: 1, page_size: 20, total_pages: 0 }))
  const mockTask = vi.fn(() => Promise.resolve({}))
  const mockTaskCreate = vi.fn(() => Promise.resolve({}))
  const mockTaskUpdate = vi.fn(() => Promise.resolve({}))
  const mockTaskDelete = vi.fn(() => Promise.resolve())
  const mockTaskStats = vi.fn(() => Promise.resolve({}))
  const mockWorkTimeDetail = vi.fn(() => Promise.resolve({}))
  
  return {
    // Object-based API
    tasksApi: {
      getTasks: mockTasks,
      getTask: mockTask,
      createTask: mockTaskCreate,
      updateTask: mockTaskUpdate,
      deleteTask: mockTaskDelete,
      getTaskStats: mockTaskStats,
      getWorkTimeDetail: mockWorkTimeDetail
    },
    // Individual function exports for direct import compatibility
    getTasks: mockTasks,
    getTask: mockTask,
    getTaskDetail: mockTask, // Alias
    createTask: mockTaskCreate,
    updateTask: mockTaskUpdate,
    deleteTask: mockTaskDelete,
    getTaskStats: mockTaskStats,
    getWorkTimeDetail: mockWorkTimeDetail
  }
})

// 不mock members API，让测试使用真实的API，只mock底层的HTTP client

vi.mock('@/api/client', () => ({
  http: {
    get: vi.fn(() => Promise.resolve({ data: {}, status: 200 })),
    post: vi.fn(() => Promise.resolve({ data: {}, status: 200 })),
    put: vi.fn(() => Promise.resolve({ data: {}, status: 200 })),
    delete: vi.fn(() => Promise.resolve({ data: {}, status: 200 })),
    patch: vi.fn(() => Promise.resolve({ data: {}, status: 200 }))
  }
}))

// =========================
// 2. ECharts Canvas环境修复
// =========================
// 增强Canvas mock以完全支持ECharts
global.HTMLCanvasElement = class MockCanvas {
  constructor() {
    this.width = 800
    this.height = 600
    this.getContext = vi.fn(() => ({
      // 基础绘制方法
      clearRect: vi.fn(),
      fillRect: vi.fn(),
      strokeRect: vi.fn(),
      drawImage: vi.fn(),
      measureText: vi.fn(() => ({ width: 100, height: 12 })),
      fillText: vi.fn(),
      strokeText: vi.fn(),
      
      // 状态管理
      restore: vi.fn(),
      save: vi.fn(),
      
      // 变换方法
      scale: vi.fn(),
      translate: vi.fn(),
      rotate: vi.fn(),
      transform: vi.fn(),
      setTransform: vi.fn(),
      
      // 路径方法
      beginPath: vi.fn(),
      closePath: vi.fn(),
      stroke: vi.fn(),
      fill: vi.fn(),
      arc: vi.fn(),
      arcTo: vi.fn(),
      lineTo: vi.fn(),
      moveTo: vi.fn(),
      quadraticCurveTo: vi.fn(),
      bezierCurveTo: vi.fn(),
      rect: vi.fn(),
      clip: vi.fn(),
      
      // 渐变和样式
      createLinearGradient: vi.fn(() => ({
        addColorStop: vi.fn()
      })),
      createRadialGradient: vi.fn(() => ({
        addColorStop: vi.fn()
      })),
      createPattern: vi.fn(() => ({})),
      
      // ECharts特定属性
      canvas: { width: 800, height: 600 },
      globalAlpha: 1,
      globalCompositeOperation: 'source-over',
      font: '10px sans-serif',
      textAlign: 'start',
      textBaseline: 'alphabetic',
      direction: 'inherit',
      fillStyle: '#000000',
      strokeStyle: '#000000',
      lineWidth: 1,
      lineCap: 'butt',
      lineJoin: 'miter',
      miterLimit: 10,
      lineDashOffset: 0,
      shadowOffsetX: 0,
      shadowOffsetY: 0,
      shadowBlur: 0,
      shadowColor: 'rgba(0, 0, 0, 0)',
      
      // 其他ECharts需要的方法
      getImageData: vi.fn(() => ({ data: new Uint8ClampedArray(4) })),
      putImageData: vi.fn(),
      createImageData: vi.fn(),
      getLineDash: vi.fn(() => []),
      setLineDash: vi.fn(),
      isPointInPath: vi.fn(() => false),
      isPointInStroke: vi.fn(() => false)
    }))
  }
  width = 800
  height = 600
  toDataURL = vi.fn(() => 'data:image/png;base64,')
  toBlob = vi.fn()
}

Object.defineProperty(HTMLCanvasElement.prototype, 'getContext', {
  value: function(contextType) {
    if (contextType === '2d') {
      return new MockCanvas().getContext()
    }
    return null
  }
})

// DOM尺寸修复
Object.defineProperty(HTMLElement.prototype, 'clientWidth', {
  value: 800,
  configurable: true
})
Object.defineProperty(HTMLElement.prototype, 'clientHeight', {
  value: 600,
  configurable: true
})
Object.defineProperty(HTMLElement.prototype, 'offsetWidth', {
  value: 800,
  configurable: true
})
Object.defineProperty(HTMLElement.prototype, 'offsetHeight', {
  value: 600,
  configurable: true
})

// =========================
// 3. Element Plus组件全局Mock
// =========================
const elementPlusComponents = [
  'el-button', 'el-input', 'el-form', 'el-form-item', 'el-select',
  'el-option', 'el-dialog', 'el-table', 'el-table-column', 'el-pagination',
  'el-card', 'el-row', 'el-col', 'el-icon', 'el-steps', 'el-step',
  'el-upload', 'el-result', 'el-date-picker', 'el-time-picker',
  'el-switch', 'el-radio', 'el-radio-group', 'el-checkbox', 'el-checkbox-group',
  'el-menu', 'el-menu-item', 'el-sub-menu', 'el-breadcrumb', 'el-breadcrumb-item',
  'el-tooltip', 'el-popover', 'el-dropdown', 'el-dropdown-menu', 'el-dropdown-item',
  'el-tag', 'el-badge', 'el-progress', 'el-loading', 'el-empty', 'el-divider',
  'el-radio-button', 'el-checkbox-button', 'el-cascader', 'el-color-picker', 
  'el-slider', 'el-rate', 'el-transfer', 'el-tree', 'el-tree-select', 'el-autocomplete',
  'el-link'
]

config.global.stubs = elementPlusComponents.reduce((stubs, component) => {
  stubs[component] = true
  return stubs
}, {
  // Router components
  'router-link': true,
  'router-view': true
})

// 模拟Element Plus插件安装以消除插件警告
config.global.plugins = [
  {
    install(app) {
      // 模拟Element Plus组件注册
      elementPlusComponents.forEach(component => {
        app.component(component, { 
          template: `<div class="${component}-stub"><slot /></div>`,
          props: ['modelValue', 'value', 'disabled', 'placeholder', 'size', 'type']
        })
      })
    }
  }
]

// =========================
// 4. Vue Router Mock
// =========================
vi.mock('vue-router', () => ({
  createRouter: vi.fn(() => ({
    push: vi.fn(),
    replace: vi.fn(),
    go: vi.fn(),
    back: vi.fn(),
    forward: vi.fn(),
    beforeEach: vi.fn(),
    afterEach: vi.fn(),
    getRoutes: vi.fn(() => []),
    hasRoute: vi.fn(() => false),
    resolve: vi.fn(() => ({ name: 'Dashboard', path: '/', params: {}, query: {}, meta: {} }))
  })),
  createWebHistory: vi.fn(),
  useRouter: vi.fn(() => ({
    push: vi.fn(),
    replace: vi.fn(),
    go: vi.fn(),
    back: vi.fn(),
    forward: vi.fn(),
    beforeEach: vi.fn(),
    afterEach: vi.fn()
  })),
  useRoute: vi.fn(() => ({
    path: '/',
    name: 'Dashboard',
    params: {},
    query: {},
    meta: {}
  }))
}))

config.global.mocks = {
  $router: {
    push: vi.fn(),
    replace: vi.fn(),
    go: vi.fn(),
    back: vi.fn()
  },
  $route: {
    path: '/',
    params: {},
    query: {},
    hash: '',
    meta: {}
  }
}

// =========================
// 5. Pinia Store Setup (Allow real Pinia for store tests)
// =========================
// Do not mock pinia itself - let store tests use real Pinia instances

// Store mocks removed - let unit tests use real store implementations

// All store mocks removed to allow proper store unit testing

// =========================
// 5.5. Router Instance Mock
// =========================
vi.mock('@/router', () => ({
  default: {
    push: vi.fn(),
    replace: vi.fn(),
    go: vi.fn(),
    back: vi.fn(),
    forward: vi.fn(),
    beforeEach: vi.fn(),
    afterEach: vi.fn(),
    getRoutes: vi.fn(() => []),
    hasRoute: vi.fn(() => false),
    resolve: vi.fn(() => ({ name: 'Dashboard', path: '/', params: {}, query: {}, meta: {} })),
    currentRoute: {
      value: {
        path: '/login',
        name: 'Login',
        params: {},
        query: {},
        meta: {}
      }
    }
  }
}))

// =========================
// 6. 工具函数Mocks
// =========================
vi.mock('@/utils/auth', () => {
  return {
    getToken: vi.fn(() => {
      try {
        return localStorage?.getItem('access_token') || null
      } catch {
        return null
      }
    }),
    setToken: vi.fn((token) => {
      try {
        localStorage?.setItem('access_token', token)
      } catch {
        // Silently handle localStorage not available
      }
    }),
    removeToken: vi.fn(() => {
      try {
        localStorage?.removeItem('access_token')
      } catch {
        // Silently handle localStorage not available
      }
    }),
    getRefreshToken: vi.fn(() => {
      try {
        return localStorage?.getItem('refresh_token') || null
      } catch {
        return null
      }
    }),
    setRefreshToken: vi.fn((token) => {
      try {
        localStorage?.setItem('refresh_token', token)
      } catch {
        // Silently handle localStorage not available
      }
    }),
    removeRefreshToken: vi.fn(() => {
      try {
        localStorage?.removeItem('refresh_token')
      } catch {
        // Silently handle localStorage not available
      }
    }),
    clearAuthData: vi.fn(() => {
      try {
        localStorage?.removeItem('access_token')
        localStorage?.removeItem('refresh_token')
      } catch {
        // Silently handle localStorage not available
      }
    }),
    isTokenExpired: vi.fn((token) => {
      if (!token) return true
      try {
        const parts = token.split('.')
        if (parts.length !== 3) return true
        const payload = JSON.parse(atob(parts[1]))
        if (!payload.exp) return true
        const currentTime = Math.floor(Date.now() / 1000)
        return payload.exp < currentTime
      } catch {
        return true
      }
    }),
    parseJWT: vi.fn((token) => {
      if (!token) return null
      try {
        const parts = token.split('.')
        if (parts.length !== 3) return null
        const payload = JSON.parse(atob(parts[1]))
        return payload
      } catch {
        return null
      }
    })
  }
})

vi.mock('@/utils/date', () => ({
  formatDate: vi.fn((date, format = 'YYYY-MM-DD') => {
    if (!date) return ''
    const d = new Date(date)
    if (isNaN(d.getTime())) return ''
    
    const year = d.getFullYear()
    const month = String(d.getMonth() + 1).padStart(2, '0')
    const day = String(d.getDate()).padStart(2, '0')
    
    if (format === 'YYYY年MM月DD日') return `${year}年${month}月${day}日`
    if (format === 'MM/DD/YYYY') return `${month}/${day}/${year}`
    if (format === 'DD-MM-YYYY') return `${day}-${month}-${year}`
    return `${year}-${month}-${day}`
  }),
  
  formatDateTime: vi.fn((date, format = 'YYYY-MM-DD HH:mm:ss') => {
    if (!date) return ''
    const d = new Date(date)
    if (isNaN(d.getTime())) return ''
    
    const year = d.getFullYear()
    const month = String(d.getMonth() + 1).padStart(2, '0')
    const day = String(d.getDate()).padStart(2, '0')
    const hours = String(d.getHours()).padStart(2, '0')
    const minutes = String(d.getMinutes()).padStart(2, '0')
    const seconds = String(d.getSeconds()).padStart(2, '0')
    
    if (format.includes('MM/DD/YYYY')) {
      const hour12 = d.getHours() > 12 ? d.getHours() - 12 : d.getHours() || 12
      const ampm = d.getHours() >= 12 ? 'PM' : 'AM'
      return `${month}/${day}/${year} ${String(hour12).padStart(2, '0')}:${minutes} ${ampm}`
    }
    
    return `${year}-${month}-${day} ${hours}:${minutes}:${seconds}`
  }),
  
  formatTime: vi.fn((date, format = 'HH:mm:ss') => {
    if (!date) return ''
    const d = new Date(date)
    if (isNaN(d.getTime())) return ''
    
    const hours = d.getHours()
    const minutes = String(d.getMinutes()).padStart(2, '0')
    const seconds = String(d.getSeconds()).padStart(2, '0')
    
    if (format.includes('hh:mm A')) {
      const hour12 = hours > 12 ? hours - 12 : hours || 12
      const ampm = hours >= 12 ? 'PM' : 'AM'
      return `${String(hour12).padStart(2, '0')}:${minutes} ${ampm}`
    }
    
    return `${String(hours).padStart(2, '0')}:${minutes}:${seconds}`
  }),
  
  isToday: vi.fn((date) => {
    const today = new Date()
    const checkDate = new Date(date)
    return today.toDateString() === checkDate.toDateString()
  }),
  
  isThisWeek: vi.fn((date) => {
    const now = new Date()
    const checkDate = new Date(date)
    const startOfWeek = new Date(now.setDate(now.getDate() - now.getDay()))
    const endOfWeek = new Date(startOfWeek.getTime() + 6 * 24 * 60 * 60 * 1000)
    return checkDate >= startOfWeek && checkDate <= endOfWeek
  }),
  
  isThisMonth: vi.fn((date) => {
    const now = new Date()
    const checkDate = new Date(date)
    return now.getFullYear() === checkDate.getFullYear() && now.getMonth() === checkDate.getMonth()
  }),
  
  getRelativeTime: vi.fn((date) => {
    const now = new Date()
    const checkDate = new Date(date)
    const diffMs = checkDate - now // 注意：未来时间是checkDate > now
    const diffMins = Math.abs(Math.floor(diffMs / (1000 * 60)))
    const diffHours = Math.abs(Math.floor(diffMs / (1000 * 60 * 60)))
    const diffDays = Math.abs(Math.floor(diffMs / (1000 * 60 * 60 * 24)))
    
    if (diffMins < 1) return '刚刚'
    
    // 处理未来时间
    if (diffMs > 0) {
      if (diffMins < 60) return `${diffMins}分钟后`
      if (diffHours < 24) return `${diffHours}小时后`
      return `${diffDays}天后`
    }
    
    // 处理过去时间
    if (diffMins < 60) return `${diffMins}分钟前`
    if (diffHours < 24) return `${diffHours}小时前`
    return `${diffDays}天前`
  }),
  
  parseDate: vi.fn((dateString) => {
    if (!dateString || dateString === null || dateString === undefined) return null
    try {
      const date = new Date(dateString)
      return isNaN(date.getTime()) ? null : date
    } catch {
      return null
    }
  }),
  
  formatDuration: vi.fn((minutes) => {
    if (minutes < 0) return '0分钟'
    const hours = Math.floor(minutes / 60)
    const mins = minutes % 60
    
    if (hours === 0) return `${mins}分钟`
    if (mins === 0) return `${hours}小时`
    return `${hours}小时${mins}分钟`
  }),
  
  addDays: vi.fn((date, days) => {
    const result = new Date(date)
    result.setDate(result.getDate() + days)
    return result
  }),
  
  diffInDays: vi.fn((date1, date2) => {
    const d1 = new Date(date1)
    const d2 = new Date(date2)
    const diffTime = Math.abs(d2 - d1)
    return Math.ceil(diffTime / (1000 * 60 * 60 * 24))
  }),
  
  // 新增缺失的方法
  getDaysBetween: vi.fn((date1, date2) => {
    const d1 = new Date(date1)
    const d2 = new Date(date2)
    const diffTime = Math.abs(d2 - d1)
    return Math.ceil(diffTime / (1000 * 60 * 60 * 24))
  }),
  
  getWeekRange: vi.fn((date) => {
    const d = date ? new Date(date) : new Date()
    // 创建副本避免修改原始日期
    const startOfWeek = new Date(d)
    startOfWeek.setDate(d.getDate() - d.getDay())
    startOfWeek.setHours(0, 0, 0, 0)
    
    const endOfWeek = new Date(startOfWeek)
    endOfWeek.setDate(startOfWeek.getDate() + 6)
    endOfWeek.setHours(23, 59, 59, 999)
    
    return { start: startOfWeek, end: endOfWeek }
  }),
  
  getMonthRange: vi.fn((date) => {
    const d = date ? new Date(date) : new Date()
    const start = new Date(d.getFullYear(), d.getMonth(), 1)
    const end = new Date(d.getFullYear(), d.getMonth() + 1, 0)
    return { start, end }
  })
}))

// =========================
// 7. 浏览器环境Mock
// =========================
// Mock localStorage
const localStorageMock = {
  getItem: vi.fn((key) => localStorageMock._storage[key] || null),
  setItem: vi.fn((key, value) => {
    localStorageMock._storage[key] = String(value)
  }),
  removeItem: vi.fn((key) => {
    delete localStorageMock._storage[key]
  }),
  clear: vi.fn(() => {
    localStorageMock._storage = {}
  }),
  _storage: {} as Record<string, string>
}
vi.stubGlobal('localStorage', localStorageMock)

// Mock sessionStorage
const sessionStorageMock = {
  getItem: vi.fn(),
  setItem: vi.fn(),
  removeItem: vi.fn(),
  clear: vi.fn()
}
vi.stubGlobal('sessionStorage', sessionStorageMock)

// Mock matchMedia
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: vi.fn().mockImplementation(query => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: vi.fn(),
    removeListener: vi.fn(),
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    dispatchEvent: vi.fn()
  }))
})

// Mock fetch
global.fetch = vi.fn()

// Mock ResizeObserver
global.ResizeObserver = vi.fn().mockImplementation(() => ({
  observe: vi.fn(),
  unobserve: vi.fn(),
  disconnect: vi.fn()
}))

// Mock CSS files
vi.mock('*.css', () => ({}))
vi.mock('*.scss', () => ({}))
vi.mock('*.sass', () => ({}))
vi.mock('*.less', () => ({}))
vi.mock('*.styl', () => ({}))
vi.mock('*.stylus', () => ({}))

// Element Plus指令Mock
config.global.directives = {
  loading: {
    mounted: vi.fn(),
    updated: vi.fn(),
    unmounted: vi.fn()
  }
}

// 设置全局测试超时
vi.setConfig({ testTimeout: 10000 })