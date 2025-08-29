// frontend/tests/setup.ts
import { vi } from 'vitest'
import { config } from '@vue/test-utils'

// =========================
// 1. 完整API Mock配置
// =========================
vi.mock('@/api/statistics', () => ({
  statisticsApi: {
    getDashboardStats: vi.fn().mockResolvedValue({
      totalTasks: 100,
      completedTasks: 75,
      pendingTasks: 25,
      totalMembers: 50
    }),
    getTaskDistribution: vi.fn().mockResolvedValue([
      { type: 'repair', count: 30 },
      { type: 'maintenance', count: 45 },
      { type: 'cleaning', count: 25 }
    ]),
    getWorkHoursTrend: vi.fn().mockResolvedValue([
      { date: '2024-01-01', hours: 8.5 },
      { date: '2024-01-02', hours: 7.2 }
    ]),
    getOverview: vi.fn(() => Promise.resolve({
      data: {
        totalMembers: 50,
        activeMembers: 45,
        totalTasks: 120,
        completedTasks: 100,
        pendingTasks: 20,
        totalWorkHours: 2400,
        avgWorkHours: 48,
        efficiency: 85.5
      }
    })),
    getWorkHoursStats: vi.fn(() => Promise.resolve({
      data: {
        thisMonth: 480,
        lastMonth: 450,
        growth: 6.7,
        daily: []
      }
    })),
    getTaskStats: vi.fn(() => Promise.resolve({
      data: {
        byType: {},
        byStatus: {},
        trend: []
      }
    })),
    getMemberStats: vi.fn(() => Promise.resolve({
      data: {
        topPerformers: [],
        departmentStats: []
      }
    }))
  }
}))

vi.mock('@/api/tasks', () => ({
  tasksApi: {
    getTasks: vi.fn(() => Promise.resolve({ data: { items: [], total: 0 } })),
    getTaskDetail: vi.fn(() => Promise.resolve({ data: {} })),
    createTask: vi.fn(() => Promise.resolve({ data: {} })),
    updateTask: vi.fn(() => Promise.resolve({ data: {} })),
    deleteTask: vi.fn(() => Promise.resolve({ data: {} }))
  }
}))

vi.mock('@/api/members', () => ({
  membersApi: {
    getMembers: vi.fn(() => Promise.resolve({ data: { items: [], total: 0 } })),
    getMemberDetail: vi.fn(() => Promise.resolve({ data: {} })),
    createMember: vi.fn(() => Promise.resolve({ data: {} })),
    updateMember: vi.fn(() => Promise.resolve({ data: {} })),
    deleteMember: vi.fn(() => Promise.resolve({ data: {} })),
    importMembers: vi.fn(() => Promise.resolve({ data: {} })),
    exportMembers: vi.fn(() => Promise.resolve({ data: {} }))
  }
}))

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
Object.defineProperty(HTMLCanvasElement.prototype, 'getContext', {
  value: vi.fn(() => ({
    clearRect: vi.fn(),
    fillRect: vi.fn(),
    drawImage: vi.fn(),
    measureText: vi.fn(() => ({ width: 100 })),
    fillText: vi.fn(),
    restore: vi.fn(),
    save: vi.fn(),
    scale: vi.fn(),
    translate: vi.fn(),
    beginPath: vi.fn(),
    closePath: vi.fn(),
    stroke: vi.fn(),
    fill: vi.fn(),
    arc: vi.fn(),
    lineTo: vi.fn(),
    moveTo: vi.fn(),
    quadraticCurveTo: vi.fn(),
    bezierCurveTo: vi.fn(),
    createLinearGradient: vi.fn(() => ({
      addColorStop: vi.fn()
    })),
    createRadialGradient: vi.fn(() => ({
      addColorStop: vi.fn()
    }))
  }))
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
  'el-tag', 'el-badge', 'el-progress', 'el-loading', 'el-empty', 'el-divider'
]

config.global.stubs = elementPlusComponents.reduce((stubs, component) => {
  stubs[component] = true
  return stubs
}, {
  // Router components
  'router-link': true,
  'router-view': true
})

// =========================
// 4. Vue Router Mock
// =========================
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
    go: vi.fn(),
    back: vi.fn(),
    forward: vi.fn()
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
// 5. Pinia Store Mocks
// =========================
vi.mock('pinia', () => ({
  createPinia: vi.fn(),
  defineStore: vi.fn(() => vi.fn()),
  storeToRefs: vi.fn((store) => store),
  setActivePinia: vi.fn(),
  getActivePinia: vi.fn()
}))

vi.mock('@/stores/auth', () => ({
  useAuthStore: vi.fn(() => ({
    user: null,
    token: null,
    isAuthenticated: false,
    login: vi.fn(),
    logout: vi.fn(),
    refreshToken: vi.fn()
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
    pagination: { current: 1, pageSize: 10, total: 0 },
    getTasks: vi.fn(),
    getTaskDetail: vi.fn(),
    createTask: vi.fn(),
    updateTask: vi.fn(),
    deleteTask: vi.fn(),
    resetTasks: vi.fn()
  }))
}))

// =========================
// 6. 工具函数Mocks
// =========================
vi.mock('@/utils/auth', () => ({
  getToken: vi.fn(() => 'mock-token'),
  setToken: vi.fn(),
  removeToken: vi.fn(),
  isTokenExpired: vi.fn(() => false),
  parseJWT: vi.fn(() => ({ userId: 1, username: 'test' }))
}))

vi.mock('@/utils/date', () => ({
  formatDate: vi.fn((date) => {
    if (!date) return ''
    const d = new Date(date)
    return d.toISOString().split('T')[0]
  }),
  formatDateTime: vi.fn((date) => {
    if (!date) return ''
    const d = new Date(date)
    return d.toISOString().replace('T', ' ').split('.')[0]
  }),
  formatTime: vi.fn((date) => {
    if (!date) return ''
    const d = new Date(date)
    return d.toTimeString().split(' ')[0]
  }),
  isToday: vi.fn((date) => {
    const today = new Date()
    const checkDate = new Date(date)
    return today.toDateString() === checkDate.toDateString()
  }),
  isThisWeek: vi.fn(() => true),
  isThisMonth: vi.fn(() => true),
  getRelativeTime: vi.fn(() => '刚刚'),
  parseDate: vi.fn((dateString) => {
    try {
      return new Date(dateString)
    } catch {
      return null
    }
  }),
  formatDuration: vi.fn(() => '8小时0分钟'),
  addDays: vi.fn((date, days) => {
    const result = new Date(date)
    result.setDate(result.getDate() + days)
    return result
  }),
  diffInDays: vi.fn(() => 1)
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