// 极简测试环境配置 - 专注解决组件测试问题
import { vi } from 'vitest'
import { config } from '@vue/test-utils'

// ===========================
// 1. 全局 Mock 配置
// ===========================

// Mock localStorage
const createStorageMock = () => {
  const storage = new Map()
  return {
    getItem: vi.fn(key => storage.get(key) || null),
    setItem: vi.fn((key, value) => storage.set(key, String(value))),
    removeItem: vi.fn(key => storage.delete(key)),
    clear: vi.fn(() => storage.clear()),
    key: vi.fn(index => Array.from(storage.keys())[index] || null),
    get length() {
      return storage.size
    }
  }
}

vi.stubGlobal('localStorage', createStorageMock())
vi.stubGlobal('sessionStorage', createStorageMock())

// ===========================
// 2. Element Plus 完全模拟
// ===========================

// 创建所有 Element Plus 组件的简单模拟
const createElementComponent = (name: string) => ({
  name,
  template: `<div class="${name.toLowerCase()}"><slot /></div>`,
  props: [
    'modelValue',
    'placeholder',
    'disabled',
    'loading',
    'data',
    'size',
    'type'
  ],
  emits: ['update:modelValue', 'change', 'click', 'input']
})

const elementComponents = {
  // 基础组件
  'el-button': createElementComponent('el-button'),
  'el-input': createElementComponent('el-input'),
  'el-select': createElementComponent('el-select'),
  'el-option': createElementComponent('el-option'),
  'el-form': createElementComponent('el-form'),
  'el-form-item': createElementComponent('el-form-item'),

  // 数据展示
  'el-table': createElementComponent('el-table'),
  'el-table-column': createElementComponent('el-table-column'),
  'el-card': createElementComponent('el-card'),
  'el-tag': createElementComponent('el-tag'),

  // 布局
  'el-row': createElementComponent('el-row'),
  'el-col': createElementComponent('el-col'),

  // 反馈
  'el-dialog': createElementComponent('el-dialog'),
  'el-loading': createElementComponent('el-loading'),
  'el-pagination': createElementComponent('el-pagination'),

  // 图标 - 简单模拟
  'el-icon': {
    name: 'el-icon',
    template: '<i class="el-icon"><slot /></i>',
    props: ['size', 'color']
  }
}

// 全局组件注册
config.global.stubs = {
  ...elementComponents,
  // 路由组件
  'router-link': { template: '<a href="#"><slot /></a>' },
  'router-view': { template: '<div><slot /></div>' },
  // 过渡动画
  transition: false,
  'transition-group': false
}

// ===========================
// 3. API Mocks - 超简化版本
// ===========================

// Mock所有API模块
vi.mock('@/api/tasks', () => ({
  getTasks: vi.fn(() => Promise.resolve({ items: [], total: 0 })),
  getTaskStats: vi.fn(() => Promise.resolve({})),
  createTask: vi.fn(() => Promise.resolve({})),
  updateTask: vi.fn(() => Promise.resolve({})),
  deleteTask: vi.fn(() => Promise.resolve({}))
}))

vi.mock('@/api/members', () => ({
  getMembers: vi.fn(() => Promise.resolve({ items: [], total: 0 })),
  createMember: vi.fn(() => Promise.resolve({})),
  updateMember: vi.fn(() => Promise.resolve({})),
  deleteMember: vi.fn(() => Promise.resolve({}))
}))

vi.mock('@/api/dashboard', () => ({
  getDashboardOverview: vi.fn(() => Promise.resolve({})),
  getRecentTasks: vi.fn(() => Promise.resolve([])),
  getRecentAttendance: vi.fn(() => Promise.resolve([]))
}))

vi.mock('@/api/statistics', () => ({
  getOverviewStats: vi.fn(() => Promise.resolve({}))
}))

// ===========================
// 4. Element Plus Icons - 动态模拟
// ===========================

vi.mock('@element-plus/icons-vue', () => {
  return new Proxy(
    {},
    {
      get(_, prop) {
        return {
          name: String(prop),
          template: `<i class="mock-icon-${String(prop).toLowerCase()}"></i>`
        }
      }
    }
  )
})

// ===========================
// 5. Vue Router Mock
// ===========================

vi.mock('vue-router', () => ({
  createRouter: vi.fn(() => ({
    push: vi.fn(() => Promise.resolve()),
    replace: vi.fn(() => Promise.resolve()),
    go: vi.fn(),
    back: vi.fn(),
    forward: vi.fn(),
    beforeEach: vi.fn(),
    afterEach: vi.fn(),
    onError: vi.fn(),
    isReady: vi.fn(() => Promise.resolve()),
    getRoutes: vi.fn(() => []),
    hasRoute: vi.fn(() => false),
    resolve: vi.fn(() => ({
      name: 'Home',
      path: '/',
      params: {},
      query: {},
      meta: {},
      matched: [],
      redirectedFrom: undefined,
      href: '/'
    })),
    currentRoute: {
      value: { path: '/', name: 'Home', params: {}, query: {}, meta: {} }
    }
  })),
  createWebHistory: vi.fn(() => ({})),
  useRouter: vi.fn(() => ({
    push: vi.fn(() => Promise.resolve()),
    replace: vi.fn(() => Promise.resolve()),
    go: vi.fn(),
    back: vi.fn(),
    forward: vi.fn(),
    currentRoute: {
      value: { path: '/', name: 'Home', params: {}, query: {}, meta: {} }
    }
  })),
  useRoute: vi.fn(() => ({
    path: '/',
    name: 'Home',
    params: {},
    query: {},
    meta: {}
  }))
}))

// Mock router instance specifically
vi.mock('@/router', () => ({
  default: {
    push: vi.fn(() => Promise.resolve()),
    replace: vi.fn(() => Promise.resolve()),
    go: vi.fn(),
    back: vi.fn(),
    forward: vi.fn(),
    beforeEach: vi.fn(),
    afterEach: vi.fn(),
    onError: vi.fn(),
    isReady: vi.fn(() => Promise.resolve()),
    getRoutes: vi.fn(() => []),
    hasRoute: vi.fn(() => false),
    resolve: vi.fn(() => ({
      name: 'Home',
      path: '/',
      params: {},
      query: {},
      meta: {},
      matched: [],
      redirectedFrom: undefined,
      href: '/'
    })),
    currentRoute: {
      value: { path: '/', name: 'Home', params: {}, query: {}, meta: {} }
    }
  }
}))

// ===========================
// 6. 工具函数 Mock
// ===========================

vi.mock('@/utils/date', () => ({
  formatDate: vi.fn(() => '2024-01-01'),
  formatDateTime: vi.fn(() => '2024-01-01 12:00:00'),
  formatTime: vi.fn(() => '12:00:00')
}))

vi.mock('@/utils/auth', () => ({
  getToken: vi.fn(),
  setToken: vi.fn(),
  removeToken: vi.fn(),
  isLoggedIn: vi.fn(() => true)
}))

// ===========================
// 7. Element Plus Functions Mock
// ===========================

vi.mock('element-plus', () => ({
  ElMessage: {
    success: vi.fn(),
    error: vi.fn(),
    info: vi.fn(),
    warning: vi.fn()
  },
  ElMessageBox: {
    confirm: vi.fn(() => Promise.resolve()),
    alert: vi.fn(() => Promise.resolve()),
    prompt: vi.fn(() => Promise.resolve())
  },
  ElNotification: {
    success: vi.fn(),
    error: vi.fn(),
    info: vi.fn(),
    warning: vi.fn()
  },
  ElLoading: {
    service: vi.fn(() => ({ close: vi.fn() }))
  }
}))

// ===========================
// 8. 全局错误处理
// ===========================

// 忽略预期的测试错误
const originalError = console.error
console.error = (...args) => {
  const message = args.join(' ')
  if (
    message.includes('Vue warn') ||
    message.includes('[Vue warn]') ||
    message.includes('clearRect') ||
    message.includes('Canvas') ||
    message.includes('ECharts')
  ) {
    return
  }
  originalError.apply(console, args)
}

// Mock Canvas相关
global.HTMLCanvasElement = class MockCanvas {
  getContext() {
    return {
      clearRect: vi.fn(),
      fillRect: vi.fn(),
      strokeRect: vi.fn(),
      fillText: vi.fn(),
      measureText: vi.fn(() => ({ width: 0, height: 0 }))
    }
  }
}

// Mock ResizeObserver
global.ResizeObserver = vi.fn().mockImplementation(() => ({
  observe: vi.fn(),
  unobserve: vi.fn(),
  disconnect: vi.fn()
}))

// Mock IntersectionObserver
global.IntersectionObserver = vi.fn().mockImplementation(() => ({
  observe: vi.fn(),
  unobserve: vi.fn(),
  disconnect: vi.fn()
}))

// Mock window.matchMedia
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

// 全局Vue Test Utils配置
config.global.mocks = {
  $router: {
    push: vi.fn(),
    replace: vi.fn(),
    go: vi.fn()
  },
  $route: {
    path: '/',
    name: 'Home',
    params: {},
    query: {}
  },
  $message: vi.fn(),
  $confirm: vi.fn(() => Promise.resolve()),
  $loading: vi.fn(() => ({ close: vi.fn() }))
}
