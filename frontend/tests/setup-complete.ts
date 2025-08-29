import { config } from '@vue/test-utils'
import { vi } from 'vitest'
import { createApp } from 'vue'
import ElementPlus from 'element-plus'

// 创建Element Plus完整组件存根
const createElementPlusStubs = () => ({
  // 基础组件
  'el-button': { template: '<button class="el-button"><slot /></button>' },
  'el-icon': { template: '<i class="el-icon"><slot /></i>' },
  'el-row': { template: '<div class="el-row"><slot /></div>' },
  'el-col': { template: '<div class="el-col"><slot /></div>' },
  'el-card': { template: '<div class="el-card"><slot /></div>' },
  'el-badge': { template: '<span class="el-badge"><slot /></span>' },
  'el-tag': { template: '<span class="el-tag"><slot /></span>' },
  'el-progress': { template: '<div class="el-progress"><slot /></div>' },
  
  // 表单组件
  'el-form': { template: '<form class="el-form"><slot /></form>' },
  'el-form-item': { template: '<div class="el-form-item"><slot /></div>' },
  'el-input': { template: '<input class="el-input" />' },
  'el-select': { template: '<select class="el-select"><slot /></select>' },
  'el-option': { template: '<option class="el-option"><slot /></option>' },
  'el-radio-group': { template: '<div class="el-radio-group"><slot /></div>' },
  'el-radio': { template: '<input type="radio" class="el-radio" />' },
  'el-radio-button': { template: '<button class="el-radio-button"><slot /></button>' },
  'el-checkbox': { template: '<input type="checkbox" class="el-checkbox" />' },
  'el-switch': { template: '<div class="el-switch"></div>' },
  'el-date-picker': { template: '<input class="el-date-picker" />' },
  
  // 表格组件
  'el-table': { template: '<table class="el-table"><slot /></table>' },
  'el-table-column': { template: '<th class="el-table-column"><slot /></th>' },
  
  // 导航组件
  'el-menu': { template: '<nav class="el-menu"><slot /></nav>' },
  'el-menu-item': { template: '<div class="el-menu-item"><slot /></div>' },
  'el-sub-menu': { template: '<div class="el-sub-menu"><slot /></div>' },
  'el-breadcrumb': { template: '<nav class="el-breadcrumb"><slot /></nav>' },
  'el-breadcrumb-item': { template: '<span class="el-breadcrumb-item"><slot /></span>' },
  
  // 反馈组件
  'el-dialog': { template: '<div class="el-dialog"><slot /></div>' },
  'el-popover': { template: '<div class="el-popover"><slot /></div>' },
  'el-tooltip': { template: '<div class="el-tooltip"><slot /></div>' },
  
  // 其他
  'el-pagination': { template: '<div class="el-pagination"></div>' },
  'el-loading': { template: '<div class="el-loading"></div>' },
  'el-empty': { template: '<div class="el-empty"><slot /></div>' },
  
  // 路由组件存根
  'router-link': { 
    template: '<a class="router-link"><slot /></a>',
    props: ['to']
  },
  'router-view': { template: '<div class="router-view"><slot /></div>' }
})

// 全局配置Vue Test Utils
config.global.stubs = createElementPlusStubs()

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

// Mock全局对象
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

// Mock Element Plus指令
config.global.directives = {
  loading: {
    mounted: vi.fn(),
    updated: vi.fn(),
    unmounted: vi.fn()
  }
}

// Mock所有CSS文件导入
vi.mock('*.css', () => ({}))
vi.mock('*.scss', () => ({}))
vi.mock('*.sass', () => ({}))
vi.mock('*.less', () => ({}))
vi.mock('*.styl', () => ({}))
vi.mock('*.stylus', () => ({}))

// 完整的API Mock配置
vi.mock('@/api/statistics', () => ({
  statisticsApi: {
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

// Pinia Store Mocks
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

// Vue Router Mock
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

// 工具函数Mocks
vi.mock('@/utils/auth', () => ({
  getToken: vi.fn(() => 'mock-token'),
  setToken: vi.fn(),
  removeToken: vi.fn(),
  isTokenExpired: vi.fn(() => false),
  parseJWT: vi.fn(() => ({ userId: 1, username: 'test' }))
}))

vi.mock('@/utils/date', () => ({
  formatDate: vi.fn(() => '2024-01-15'),
  formatDateTime: vi.fn(() => '2024-01-15 10:30:00'),
  isToday: vi.fn(() => true),
  formatDuration: vi.fn(() => '8小时0分钟')
}))

// 设置全局测试超时
vi.setConfig({ testTimeout: 10000 })