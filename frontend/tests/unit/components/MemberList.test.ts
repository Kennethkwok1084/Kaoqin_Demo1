import { describe, it, expect, beforeEach, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { createRouter, createWebHistory } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import MemberList from '@/components/members/MemberList.vue'
import { useAuthStore } from '@/stores/auth'
import * as membersApi from '@/api/members'

// Mock Element Plus消息组件
vi.mock('element-plus', async () => {
  const actual = await vi.importActual('element-plus')
  return {
    ...actual,
    ElMessage: {
      success: vi.fn(),
      error: vi.fn(),
      info: vi.fn(),
    },
    ElMessageBox: {
      confirm: vi.fn(),
    },
  }
})

// Mock API
vi.mock('@/api/members', () => ({
  getMembers: vi.fn(),
  deleteMember: vi.fn(),
}))

// Mock router
const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', component: { template: '<div>Home</div>' } }
  ]
})

describe('MemberList', () => {
  let wrapper: any
  let authStore: any

  const mockMembersData = {
    items: [
      {
        id: 1,
        username: 'test1',
        name: '测试用户1',
        student_id: '2021001',
        phone: '13800138001',
        department: '网络维护部',
        class_name: '计算机1班',
        role: 'member',
        is_active: true,
        status_display: '在职',
        join_date: '2023-01-01',
        last_login: '2023-12-01T10:00:00',
      },
      {
        id: 2,
        username: 'test2',
        name: '测试用户2',
        student_id: '2021002',
        phone: '13800138002',
        department: '网络维护部',
        class_name: '计算机2班',
        role: 'group_leader',
        is_active: true,
        status_display: '在职',
        join_date: '2023-01-01',
        last_login: null,
      }
    ],
    total: 2,
    total_pages: 1
  }

  beforeEach(async () => {
    setActivePinia(createPinia())
    authStore = useAuthStore()
    authStore.userInfo = { id: 999, username: 'admin', name: '管理员' }
    
    // Mock API响应
    vi.mocked(membersApi.getMembers).mockResolvedValue(mockMembersData)
    
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
      expect(wrapper.find('.pagination-container').exists()).toBe(true)
    })

    it('应该渲染标题和操作按钮', () => {
      expect(wrapper.find('h2').text()).toBe('成员管理')
      expect(wrapper.find('[data-testid="create-btn"]').exists()).toBe(true)
      expect(wrapper.find('[data-testid="import-btn"]').exists()).toBe(true)
      expect(wrapper.find('[data-testid="refresh-btn"]').exists()).toBe(true)
    })

    it('应该渲染搜索框', () => {
      const searchInput = wrapper.find('input[placeholder="搜索用户名、姓名或学号"]')
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

  describe('数据加载', () => {
    it('应该在组件挂载时加载成员数据', () => {
      expect(membersApi.getMembers).toHaveBeenCalledWith({
        page: 1,
        page_size: 20
      })
    })

    it('应该正确显示加载状态', async () => {
      // 模拟加载状态
      vi.mocked(membersApi.getMembers).mockImplementation(
        () => new Promise(resolve => setTimeout(() => resolve(mockMembersData), 100))
      )
      
      const newWrapper = mount(MemberList, {
        global: {
          plugins: [router]
        }
      })
      
      expect(newWrapper.vm.loading).toBe(true)
      
      await new Promise(resolve => setTimeout(resolve, 150))
      
      expect(newWrapper.vm.loading).toBe(false)
      newWrapper.unmount()
    })

    it('应该处理API错误', async () => {
      vi.mocked(membersApi.getMembers).mockRejectedValue(new Error('Network error'))
      
      const newWrapper = mount(MemberList, {
        global: {
          plugins: [router]
        }
      })
      
      await new Promise(resolve => setTimeout(resolve, 50))
      
      expect(ElMessage.error).toHaveBeenCalledWith('加载成员列表失败')
      newWrapper.unmount()
    })
  })

  describe('搜索功能', () => {
    it('应该处理搜索输入', async () => {
      const searchInput = wrapper.find('input[placeholder="搜索用户名、姓名或学号"]')
      await searchInput.setValue('测试')
      
      // 等待防抖
      await new Promise(resolve => setTimeout(resolve, 600))
      
      expect(membersApi.getMembers).toHaveBeenCalledWith({
        page: 1,
        page_size: 20,
        search: '测试'
      })
    })

    it('应该在搜索时重置页码', async () => {
      wrapper.vm.pagination.page = 3
      
      const searchInput = wrapper.find('input[placeholder="搜索用户名、姓名或学号"]')
      await searchInput.setValue('新搜索')
      
      await new Promise(resolve => setTimeout(resolve, 600))
      
      expect(wrapper.vm.pagination.page).toBe(1)
    })
  })

  describe('筛选功能', () => {
    it('应该处理角色筛选', async () => {
      await wrapper.setData({
        filters: { ...wrapper.vm.filters, role: 'admin' }
      })
      
      wrapper.vm.handleFilter()
      
      await new Promise(resolve => setTimeout(resolve, 350))
      
      expect(membersApi.getMembers).toHaveBeenCalledWith({
        page: 1,
        page_size: 20,
        role: 'admin'
      })
    })

    it('应该处理状态筛选', async () => {
      await wrapper.setData({
        filters: { ...wrapper.vm.filters, is_active: false }
      })
      
      wrapper.vm.handleFilter()
      
      await new Promise(resolve => setTimeout(resolve, 350))
      
      expect(membersApi.getMembers).toHaveBeenCalledWith({
        page: 1,
        page_size: 20,
        is_active: false
      })
    })

    it('应该处理部门和班级筛选', async () => {
      await wrapper.setData({
        filters: { 
          ...wrapper.vm.filters, 
          department: '网络部',
          class_name: '计算机1班'
        }
      })
      
      wrapper.vm.handleFilter()
      
      await new Promise(resolve => setTimeout(resolve, 350))
      
      expect(membersApi.getMembers).toHaveBeenCalledWith({
        page: 1,
        page_size: 20,
        department: '网络部',
        class_name: '计算机1班'
      })
    })
  })

  describe('分页功能', () => {
    it('应该处理页码变化', async () => {
      await wrapper.vm.handlePageChange(2)
      
      expect(membersApi.getMembers).toHaveBeenCalledWith({
        page: 2,
        page_size: 20
      })
    })

    it('应该处理每页大小变化', async () => {
      await wrapper.vm.handleSizeChange(50)
      
      expect(wrapper.vm.pagination.page_size).toBe(50)
      expect(wrapper.vm.pagination.page).toBe(1)
      expect(membersApi.getMembers).toHaveBeenCalledWith({
        page: 1,
        page_size: 50
      })
    })
  })

  describe('成员操作', () => {
    beforeEach(() => {
      wrapper.vm.members = mockMembersData.items
    })

    it('应该处理创建成员', async () => {
      await wrapper.vm.handleCreate()
      expect(wrapper.vm.createDialogVisible).toBe(true)
    })

    it('应该处理批量导入', async () => {
      await wrapper.vm.handleImport()
      expect(wrapper.vm.importDialogVisible).toBe(true)
    })

    it('应该处理刷新操作', async () => {
      vi.clearAllMocks()
      await wrapper.vm.handleRefresh()
      expect(membersApi.getMembers).toHaveBeenCalled()
    })

    it('应该处理查看成员', async () => {
      await wrapper.vm.handleView(mockMembersData.items[0])
      expect(ElMessage.info).toHaveBeenCalledWith('查看成员：测试用户1')
    })

    it('应该处理编辑成员', async () => {
      await wrapper.vm.handleEdit(mockMembersData.items[0])
      expect(ElMessage.info).toHaveBeenCalledWith('编辑成员：测试用户1')
    })

    it('应该处理删除成员确认', async () => {
      vi.mocked(ElMessageBox.confirm).mockResolvedValue('confirm')
      vi.mocked(membersApi.deleteMember).mockResolvedValue(undefined)
      
      await wrapper.vm.handleDelete(mockMembersData.items[0])
      
      expect(ElMessageBox.confirm).toHaveBeenCalledWith(
        '确定要删除成员 "测试用户1" 吗？此操作无法撤销。',
        '确认删除',
        expect.any(Object)
      )
      expect(membersApi.deleteMember).toHaveBeenCalledWith(1)
      expect(ElMessage.success).toHaveBeenCalledWith('删除成功')
    })

    it('应该处理删除操作取消', async () => {
      vi.mocked(ElMessageBox.confirm).mockRejectedValue('cancel')
      
      await wrapper.vm.handleDelete(mockMembersData.items[0])
      
      expect(membersApi.deleteMember).not.toHaveBeenCalled()
      expect(ElMessage.error).not.toHaveBeenCalled()
    })

    it('应该禁用删除当前用户按钮', async () => {
      const currentUser = { ...mockMembersData.items[0], id: 999 }
      wrapper.vm.members = [currentUser]
      await wrapper.vm.$nextTick()
      
      // 当前用户的删除按钮应该被禁用
      expect(wrapper.vm.currentUserId).toBe(999)
    })
  })

  describe('选择和批量操作', () => {
    beforeEach(() => {
      wrapper.vm.members = mockMembersData.items
    })

    it('应该处理表格选择变化', async () => {
      const selectedMembers = [mockMembersData.items[0]]
      await wrapper.vm.handleSelectionChange(selectedMembers)
      
      expect(wrapper.vm.selectedMembers).toEqual(selectedMembers)
    })

    it('应该在有选择时显示批量操作区域', async () => {
      wrapper.vm.selectedMembers = mockMembersData.items
      await wrapper.vm.$nextTick()
      
      const batchActions = wrapper.find('.batch-actions')
      expect(batchActions.exists()).toBe(true)
      expect(batchActions.text()).toContain('已选择 2 项')
    })

    it('应该处理批量删除确认', async () => {
      wrapper.vm.selectedMembers = mockMembersData.items
      vi.mocked(ElMessageBox.confirm).mockResolvedValue('confirm')
      
      await wrapper.vm.handleBatchDelete()
      
      expect(ElMessageBox.confirm).toHaveBeenCalledWith(
        '确定要删除选中的 2 个成员吗？此操作无法撤销。',
        '确认批量删除',
        expect.any(Object)
      )
    })

    it('应该处理批量离职', async () => {
      wrapper.vm.selectedMembers = mockMembersData.items
      await wrapper.vm.handleBatchDeactivate()
      
      expect(ElMessage.info).toHaveBeenCalledWith('批量离职功能开发中')
    })
  })

  describe('工具方法', () => {
    it('应该正确返回角色标签类型', () => {
      expect(wrapper.vm.getRoleTagType('admin')).toBe('danger')
      expect(wrapper.vm.getRoleTagType('group_leader')).toBe('warning')
      expect(wrapper.vm.getRoleTagType('member')).toBe('success')
      expect(wrapper.vm.getRoleTagType('guest')).toBe('info')
      expect(wrapper.vm.getRoleTagType('unknown')).toBe('info')
    })

    it('应该正确返回角色文本', () => {
      expect(wrapper.vm.getRoleText('admin')).toBe('管理员')
      expect(wrapper.vm.getRoleText('group_leader')).toBe('组长')
      expect(wrapper.vm.getRoleText('member')).toBe('成员')
      expect(wrapper.vm.getRoleText('guest')).toBe('访客')
      expect(wrapper.vm.getRoleText('unknown')).toBe('unknown')
    })

    it('应该正确格式化日期时间', () => {
      const datetime = '2023-12-01T10:00:00'
      const result = wrapper.vm.formatDateTime(datetime)
      expect(result).toMatch(/2023.*12.*1.*10.*0.*0/)
    })

    it('应该处理空的日期时间', () => {
      expect(wrapper.vm.formatDateTime('')).toBe('')
      expect(wrapper.vm.formatDateTime(null)).toBe('')
    })
  })

  describe('对话框事件', () => {
    it('应该处理创建成功事件', async () => {
      vi.clearAllMocks()
      await wrapper.vm.handleCreateSuccess()
      
      expect(membersApi.getMembers).toHaveBeenCalled()
      expect(ElMessage.success).toHaveBeenCalledWith('成员创建成功')
    })

    it('应该处理导入成功事件', async () => {
      vi.clearAllMocks()
      await wrapper.vm.handleImportSuccess()
      
      expect(membersApi.getMembers).toHaveBeenCalled()
      expect(ElMessage.success).toHaveBeenCalledWith('批量导入完成')
    })
  })
})