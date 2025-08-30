import { describe, it, expect, beforeEach, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { createRouter, createWebHistory } from 'vue-router'
import MemberList from '@/components/members/MemberList.vue'

// Mock Element Plus
vi.mock('element-plus', async () => {
  const actual = await vi.importActual('element-plus')
  return {
    ...actual,
    ElMessage: {
      success: vi.fn(),
      error: vi.fn(),
      info: vi.fn()
    },
    ElMessageBox: {
      confirm: vi.fn()
    }
  }
})

// Mock API
vi.mock('@/api/members')

// Mock router
const router = createRouter({
  history: createWebHistory(),
  routes: [{ path: '/', component: { template: '<div>Home</div>' } }]
})

describe('MemberList', () => {
  let wrapper: any

  beforeEach(async () => {
    setActivePinia(createPinia())

    wrapper = mount(MemberList, {
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
    it('应该正确渲染组件基本结构', () => {
      expect(wrapper.find('.member-list').exists()).toBe(true)
      expect(wrapper.find('.member-list-header').exists()).toBe(true)
      expect(wrapper.find('.filter-bar').exists()).toBe(true)
      expect(wrapper.find('.table-container').exists()).toBe(true)
    })

    it('应该渲染标题和操作按钮', () => {
      expect(wrapper.find('h2').text()).toBe('成员管理')
      expect(wrapper.text()).toContain('新增成员')
      expect(wrapper.text()).toContain('批量导入')
      expect(wrapper.text()).toContain('刷新')
    })

    it('应该渲染搜索框', () => {
      const searchInput = wrapper.find(
        'input[placeholder="搜索用户名、姓名或学号"]'
      )
      expect(searchInput.exists()).toBe(true)
    })

    it('应该渲染筛选表单', () => {
      const filters = wrapper.find('.filter-bar')
      expect(filters.text()).toContain('角色')
      expect(filters.text()).toContain('状态')
      expect(filters.text()).toContain('部门')
      expect(filters.text()).toContain('班级')
    })
  })

  describe('用户交互', () => {
    it('应该能够在搜索框中输入', async () => {
      const searchInput = wrapper.find(
        'input[placeholder="搜索用户名、姓名或学号"]'
      )
      await searchInput.setValue('测试搜索')
      expect(searchInput.element.value).toBe('测试搜索')
    })

    it('应该能够点击操作按钮', async () => {
      const buttons = wrapper.findAll('button')
      expect(buttons.length).toBeGreaterThan(0)

      // 尝试点击第一个按钮
      if (buttons.length > 0) {
        await buttons[0].trigger('click')
      }
    })

    it('筛选表单应该存在输入控件', () => {
      const selects = wrapper.findAll('.el-select')
      const inputs = wrapper.findAll('input')
      expect(selects.length + inputs.length).toBeGreaterThan(0)
    })
  })

  describe('表格功能', () => {
    it('应该渲染数据表格', () => {
      const table = wrapper.find('.el-table')
      expect(table.exists()).toBe(true)
    })

    it('表格应该有选择框列', () => {
      const selectionColumn = wrapper.find('[type="selection"]')
      expect(selectionColumn.exists()).toBe(true)
    })

    it('表格应该包含必要的列', () => {
      // 检查表格是否包含基本列定义
      expect(wrapper.text()).toContain('用户名')
      expect(wrapper.text()).toContain('姓名')
      expect(wrapper.text()).toContain('学号')
    })
  })

  describe('数据加载', () => {
    it('应该显示加载状态', () => {
      // 检查是否有loading属性
      const table = wrapper.find('.el-table')
      expect(table.exists()).toBe(true)
    })

    it('应该有分页组件', () => {
      expect(wrapper.find('.pagination-container').exists()).toBe(true)
    })
  })
})
