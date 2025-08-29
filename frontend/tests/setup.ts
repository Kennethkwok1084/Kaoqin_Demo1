import { config } from '@vue/test-utils'
import { vi } from 'vitest'
import ElementPlus from 'element-plus'

// Mock Element Plus全局组件
config.global.plugins = [ElementPlus]

// Mock Element Plus组件
config.global.stubs = {
  'el-button': true,
  'el-icon': true,
  'el-col': true,
  'el-row': true,
  'el-card': true,
  'el-table': true,
  'el-table-column': true,
  'el-form': true,
  'el-form-item': true,
  'el-input': true,
  'el-select': true,
  'el-option': true,
  'el-date-picker': true,
  'el-dialog': true,
  'el-drawer': true,
  'el-pagination': true,
  'el-tag': true,
  'el-tooltip': true,
  'el-popover': true,
  'el-dropdown': true,
  'el-dropdown-menu': true,
  'el-dropdown-item': true,
  'router-link': true,
  'router-view': true
}

// Mock全局对象
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: vi.fn().mockImplementation(query => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: vi.fn(), // deprecated
    removeListener: vi.fn(), // deprecated
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    dispatchEvent: vi.fn()
  }))
})

// Mock IntersectionObserver
global.IntersectionObserver = vi.fn().mockImplementation(() => ({
  observe: vi.fn(),
  unobserve: vi.fn(),
  disconnect: vi.fn()
}))

// Mock ResizeObserver
global.ResizeObserver = vi.fn().mockImplementation(() => ({
  observe: vi.fn(),
  unobserve: vi.fn(),
  disconnect: vi.fn()
}))

// Mock HTMLElement methods
Object.defineProperty(HTMLElement.prototype, 'offsetHeight', {
  configurable: true,
  value: 100
})

Object.defineProperty(HTMLElement.prototype, 'offsetWidth', {
  configurable: true,
  value: 100
})

// Mock localStorage
const localStorageMock = {
  getItem: vi.fn(key => {
    return localStorageMock._storage[key] || null
  }),
  setItem: vi.fn((key, value) => {
    localStorageMock._storage[key] = String(value)
  }),
  removeItem: vi.fn(key => {
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

// Mock fetch
global.fetch = vi.fn()

// Mock CSS导入 - 解决Element Plus CSS导入错误
vi.mock('element-plus/theme-chalk/base.css', () => ({}))
vi.mock('element-plus/theme-chalk/el-message.css', () => ({}))
vi.mock('element-plus/theme-chalk/el-notification.css', () => ({}))
vi.mock('element-plus/theme-chalk/el-loading.css', () => ({}))
vi.mock('element-plus/theme-chalk/el-overlay.css', () => ({}))
vi.mock('element-plus/theme-chalk/el-popper.css', () => ({}))
vi.mock('element-plus/theme-chalk/el-button.css', () => ({}))
vi.mock('element-plus/theme-chalk/el-form.css', () => ({}))
vi.mock('element-plus/theme-chalk/el-input.css', () => ({}))
vi.mock('element-plus/theme-chalk/el-table.css', () => ({}))
vi.mock('element-plus/theme-chalk/el-pagination.css', () => ({}))
vi.mock('element-plus/theme-chalk/el-dialog.css', () => ({}))
vi.mock('element-plus/theme-chalk/el-card.css', () => ({}))
vi.mock('element-plus/theme-chalk/el-menu.css', () => ({}))
vi.mock('element-plus/theme-chalk/el-breadcrumb.css', () => ({}))

// Mock所有CSS和SCSS文件导入 - 修复语法
vi.mock('*.css', () => ({}))
vi.mock('*.scss', () => ({}))
vi.mock('*.sass', () => ({}))
vi.mock('*.less', () => ({}))
vi.mock('*.styl', () => ({}))
vi.mock('*.stylus', () => ({}))

// 全局CSS模式匹配
Object.defineProperty(window, 'CSS', {
  value: null
})

Object.defineProperty(window, 'getComputedStyle', {
  writable: true,
  value: vi.fn().mockImplementation(() => ({
    display: 'none',
    appearance: ['-webkit-appearance']
  }))
})

// 批量Mock API模块 - 解决76个Mock错误
vi.mock('@/api/client', () => ({
  http: {
    get: vi.fn(() => Promise.resolve({ data: {}, status: 200 })),
    post: vi.fn(() => Promise.resolve({ data: {}, status: 200 })),
    put: vi.fn(() => Promise.resolve({ data: {}, status: 200 })),
    delete: vi.fn(() => Promise.resolve({ data: {}, status: 200 })),
    patch: vi.fn(() => Promise.resolve({ data: {}, status: 200 })),
    create: vi.fn(() => ({
      get: vi.fn(),
      post: vi.fn(),
      put: vi.fn(),
      delete: vi.fn(),
      patch: vi.fn(),
      defaults: {
        baseURL: '/api/v1',
        timeout: 30000,
        headers: { 'Content-Type': 'application/json' }
      },
      interceptors: {
        request: { use: vi.fn() },
        response: { use: vi.fn() }
      }
    }))
  },
  client: {
    get: vi.fn(() => Promise.resolve({ data: {}, status: 200 })),
    post: vi.fn(() => Promise.resolve({ data: {}, status: 200 })),
    put: vi.fn(() => Promise.resolve({ data: {}, status: 200 })),
    delete: vi.fn(() => Promise.resolve({ data: {}, status: 200 })),
    patch: vi.fn(() => Promise.resolve({ data: {}, status: 200 }))
  },
  setupInterceptors: vi.fn()
}))

vi.mock('@/api/auth', () => ({
  authApi: {
    login: vi.fn(),
    logout: vi.fn(),
    refreshToken: vi.fn(),
    getCurrentUser: vi.fn()
  }
}))

vi.mock('@/api/members', () => ({
  membersApi: {
    getMembers: vi.fn(),
    getMemberDetail: vi.fn(),
    createMember: vi.fn(),
    updateMember: vi.fn(),
    deleteMember: vi.fn(),
    exportMembers: vi.fn(),
    importMembers: vi.fn(),
    batchUpdateMembers: vi.fn()
  }
}))

vi.mock('vue-router', () => ({
  createRouter: vi.fn(() => ({
    push: vi.fn(),
    replace: vi.fn(),
    go: vi.fn(),
    back: vi.fn(),
    forward: vi.fn()
  })),
  createWebHistory: vi.fn(),
  useRouter: vi.fn(() => ({
    push: vi.fn(),
    replace: vi.fn(),
    go: vi.fn()
  })),
  useRoute: vi.fn(() => ({
    params: {},
    query: {},
    path: '/',
    name: 'home'
  }))
}))

vi.mock('pinia', () => ({
  createPinia: vi.fn(),
  defineStore: vi.fn(() => vi.fn()),
  storeToRefs: vi.fn(store => store),
  setActivePinia: vi.fn(),
  getActivePinia: vi.fn(),
  useAuthStore: vi.fn(() => ({
    user: null,
    token: null,
    isAuthenticated: false,
    login: vi.fn(),
    logout: vi.fn()
  }))
}))

// 添加更多API Mock
vi.mock('@/api/tasks', () => ({
  tasksApi: {
    getTasks: vi.fn(),
    getTaskDetail: vi.fn(),
    createTask: vi.fn(),
    updateTask: vi.fn(),
    deleteTask: vi.fn(),
    importMaintenanceOrders: vi.fn()
  }
}))

vi.mock('@/api/attendance', () => ({
  attendanceApi: {
    getAttendanceRecords: vi.fn(),
    checkIn: vi.fn(),
    checkOut: vi.fn(),
    getTodayAttendanceStatus: vi.fn(),
    getCheckInLocations: vi.fn(),
    correctAttendance: vi.fn()
  }
}))

vi.mock('@/api/statistics', () => ({
  statisticsApi: {
    getOverview: vi.fn(),
    generateReport: vi.fn(),
    exportData: vi.fn()
  }
}))

// Mock stores
vi.mock('@/stores/auth', () => ({
  useAuthStore: vi.fn(() => ({
    user: null,
    token: null,
    isAuthenticated: false,
    login: vi.fn(),
    logout: vi.fn()
  }))
}))

vi.mock('@/stores/global', () => ({
  useGlobalStore: vi.fn(() => ({
    theme: 'light',
    language: 'zh-CN',
    setTheme: vi.fn(),
    setLanguage: vi.fn()
  }))
}))

vi.mock('@/stores/tasks', () => ({
  useTasksStore: vi.fn(() => ({
    tasks: [],
    loading: false,
    fetchTasks: vi.fn(),
    createTask: vi.fn(),
    updateTask: vi.fn(),
    deleteTask: vi.fn()
  }))
}))

// 全局测试环境配置完成

// Mock验证工具
vi.mock('@/utils/validation', () => ({
  validateEmail: vi.fn(() => true),
  validatePhone: vi.fn(() => true),
  validateRequired: vi.fn(() => true),
  validatePassword: vi.fn(() => true)
}))

// Mock token工具
vi.mock('@/utils/token', () => ({
  parseToken: vi.fn(() => ({
    userId: 1,
    username: 'testuser',
    exp: Date.now() + 3600000
  })),
  isTokenExpired: vi.fn(() => false),
  getTokenExpiry: vi.fn(() => new Date(Date.now() + 3600000)),
  removeToken: vi.fn(),
  setToken: vi.fn(),
  getToken: vi.fn(() => 'mock-token')
}))

// Mock Element Plus组件方法
vi.mock('@/utils/elementUtils', () => ({
  showMessage: vi.fn(),
  showNotification: vi.fn(),
  showConfirm: vi.fn(() => Promise.resolve(true)),
  showLoading: vi.fn(() => ({ close: vi.fn() }))
}))

// Mock文件工具
vi.mock('@/utils/fileUtils', () => ({
  downloadFile: vi.fn(),
  uploadFile: vi.fn(() => Promise.resolve('uploaded-file-id')),
  validateFileType: vi.fn(() => true),
  validateFileSize: vi.fn(() => true),
  getFileExtension: vi.fn(() => '.xlsx'),
  formatFileSize: vi.fn(() => '1.5 MB')
}))

// 设置全局测试超时
vi.setConfig({ testTimeout: 10000 })
