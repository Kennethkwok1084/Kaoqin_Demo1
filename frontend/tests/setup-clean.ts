import { vi } from 'vitest'

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

// Mock所有CSS文件导入
vi.mock(/\.(css|scss|sass|less|styl|stylus)$/, () => ({}))

// 设置全局测试超时
vi.setConfig({ testTimeout: 10000 })
