import { describe, it, expect, beforeEach, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { createRouter, createWebHistory } from 'vue-router'
import TaskList from '@/views/tasks/TaskList.vue'

// Mock Element Plus
vi.mock('element-plus', async () => {
  const actual = await vi.importActual('element-plus')
  return {
    ...actual,
    ElMessage: {
      success: vi.fn(),
      error: vi.fn(),
      info: vi.fn()
    }
  }
})

// Mock API - 提供完整的 tasksApi Mock
vi.mock('@/api/tasks', () => ({
  tasksApi: {
    getTasks: vi.fn(() =>
      Promise.resolve({ items: [], total: 0, page: 1, pageSize: 20 })
    ),
    getTaskDetail: vi.fn(() => Promise.resolve({})),
    createTask: vi.fn(() => Promise.resolve({})),
    updateTask: vi.fn(() => Promise.resolve({})),
    deleteTask: vi.fn(() => Promise.resolve()),
    getWorkTimeDetail: vi.fn(() => Promise.resolve([])),
    getTaskStats: vi.fn(() => Promise.resolve({})),
    exportTasks: vi.fn(() => Promise.resolve()),
    importTasks: vi.fn(() =>
      Promise.resolve({ success: 0, failed: 0, errors: [] })
    )
  },
  getTasks: vi.fn(() =>
    Promise.resolve({ items: [], total: 0, page: 1, pageSize: 20 })
  ),
  getTaskDetail: vi.fn(() => Promise.resolve({})),
  createTask: vi.fn(() => Promise.resolve({})),
  updateTask: vi.fn(() => Promise.resolve({})),
  deleteTask: vi.fn(() => Promise.resolve()),
  getWorkTimeDetail: vi.fn(() => Promise.resolve([]))
}))

// Mock router
const router = createRouter({
  history: createWebHistory(),
  routes: [{ path: '/tasks', component: { template: '<div>Tasks</div>' } }]
})

describe('TaskList', () => {
  let wrapper: any

  beforeEach(async () => {
    setActivePinia(createPinia())

    wrapper = mount(TaskList, {
      global: {
        plugins: [router]
      }
    })

    await wrapper.vm.$nextTick()
  })

  afterEach(() => {
    wrapper?.unmount()
    vi.clearAllMocks()
  })

  describe('组件渲染', () => {
    it('应该正确渲染任务列表组件', () => {
      expect(wrapper.find('.task-list').exists()).toBe(true)
    })

    it('应该存在页面头部', () => {
      expect(wrapper.find('.page-header').exists()).toBe(true)
    })

    it('应该存在统计卡片区域', () => {
      expect(wrapper.find('.stats-section').exists()).toBe(true)
    })

    it('应该存在筛选区域', () => {
      expect(wrapper.find('.filter-card').exists()).toBe(true)
    })
  })

  describe('基本功能', () => {
    it('应该包含搜索输入框', () => {
      const searchInput = wrapper.find('input[placeholder*="搜索"]')
      expect(searchInput.exists()).toBe(true)
    })

    it('应该包含操作按钮', () => {
      expect(wrapper.text()).toContain('导入任务')
      expect(wrapper.text()).toContain('导出任务')
    })

    it('应该包含筛选选项', () => {
      expect(wrapper.text()).toContain('任务状态')
      expect(wrapper.text()).toContain('任务类型')
      expect(wrapper.text()).toContain('优先级')
    })
  })

  describe('用户交互', () => {
    it('搜索框应该可以输入', async () => {
      const searchInput = wrapper.find('input[placeholder*="搜索"]')
      if (searchInput.exists()) {
        await searchInput.setValue('测试搜索')
        expect(searchInput.element.value).toBe('测试搜索')
      }
    })

    it('应该能够点击按钮', async () => {
      const buttons = wrapper.findAll('button')
      expect(buttons.length).toBeGreaterThan(0)

      // 尝试点击第一个按钮
      if (buttons.length > 0) {
        await buttons[0].trigger('click')
      }
    })
  })
})
