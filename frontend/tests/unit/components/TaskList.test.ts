import { describe, it, expect, beforeEach, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { createRouter, createWebHistory } from 'vue-router'
import { ElMessage } from 'element-plus'
import TaskList from '@/views/tasks/TaskList.vue'
import * as tasksApi from '@/api/tasks'

// Mock Element Plus
vi.mock('element-plus', async () => {
  const actual = await vi.importActual('element-plus')
  return {
    ...actual,
    ElMessage: {
      success: vi.fn(),
      error: vi.fn(),
      info: vi.fn(),
    },
  }
})

// Mock API
vi.mock('@/api/tasks', () => ({
  getTasks: vi.fn(),
  getTaskDetail: vi.fn(),
  createTask: vi.fn(),
  updateTask: vi.fn(),
  deleteTask: vi.fn(),
}))

// Mock router
const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/tasks', component: { template: '<div>Tasks</div>' } }
  ]
})

describe('TaskList', () => {
  let wrapper: any

  const mockTasksData = {
    items: [
      {
        id: 1,
        title: '测试任务1',
        description: '这是一个测试任务',
        task_type: 'repair',
        task_status: 'pending',
        priority: 'high',
        assignee_id: 1,
        assignee_name: '张三',
        reporter_name: '李四',
        reporter_phone: '13800138001',
        location: '图书馆',
        created_at: '2023-12-01T10:00:00',
        updated_at: '2023-12-01T10:00:00',
        due_date: '2023-12-05T18:00:00',
        work_hours: 40,
        completion_notes: null
      },
      {
        id: 2,
        title: '测试任务2',
        description: '这是另一个测试任务',
        task_type: 'monitoring',
        task_status: 'in_progress',
        priority: 'medium',
        assignee_id: 2,
        assignee_name: '王五',
        reporter_name: '赵六',
        reporter_phone: '13800138002',
        location: '宿舍楼',
        created_at: '2023-12-02T09:00:00',
        updated_at: '2023-12-02T14:30:00',
        due_date: '2023-12-06T17:00:00',
        work_hours: 100,
        completion_notes: null
      }
    ],
    total: 2,
    total_pages: 1
  }

  beforeEach(async () => {
    setActivePinia(createPinia())
    
    // Mock API响应
    vi.mocked(tasksApi.getTasks).mockResolvedValue(mockTasksData)
    
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
      expect(wrapper.find('.task-header').exists()).toBe(true)
      expect(wrapper.find('.task-filters').exists()).toBe(true)
      expect(wrapper.find('.task-table').exists()).toBe(true)
    })

    it('应该渲染标题和操作按钮', () => {
      expect(wrapper.find('h2').text()).toContain('任务管理')
      expect(wrapper.text()).toContain('新建任务')
      expect(wrapper.text()).toContain('批量导入')
      expect(wrapper.text()).toContain('导出数据')
    })

    it('应该渲染筛选条件', () => {
      const filters = wrapper.find('.task-filters')
      expect(filters.text()).toContain('任务类型')
      expect(filters.text()).toContain('任务状态')
      expect(filters.text()).toContain('优先级')
      expect(filters.text()).toContain('负责人')
    })
  })

  describe('任务数据加载', () => {
    it('应该在组件挂载时加载任务数据', () => {
      expect(tasksApi.getTasks).toHaveBeenCalledWith({
        page: 1,
        page_size: 20
      })
    })

    it('应该正确处理加载状态', async () => {
      vi.mocked(tasksApi.getTasks).mockImplementation(
        () => new Promise(resolve => setTimeout(() => resolve(mockTasksData), 100))
      )
      
      const newWrapper = mount(TaskList, {
        global: {
          plugins: [router]
        }
      })
      
      expect(newWrapper.vm.loading).toBe(true)
      
      await new Promise(resolve => setTimeout(resolve, 150))
      
      expect(newWrapper.vm.loading).toBe(false)
      newWrapper.unmount()
    })

    it('应该处理数据加载错误', async () => {
      vi.mocked(tasksApi.getTasks).mockRejectedValue(new Error('API Error'))
      
      const newWrapper = mount(TaskList, {
        global: {
          plugins: [router]
        }
      })
      
      await new Promise(resolve => setTimeout(resolve, 50))
      
      expect(ElMessage.error).toHaveBeenCalledWith('加载任务列表失败')
      newWrapper.unmount()
    })
  })

  describe('任务筛选', () => {
    it('应该根据任务类型筛选', async () => {
      await wrapper.setData({
        filters: { ...wrapper.vm.filters, task_type: 'repair' }
      })
      
      wrapper.vm.handleFilter()
      await new Promise(resolve => setTimeout(resolve, 350))
      
      expect(tasksApi.getTasks).toHaveBeenCalledWith({
        page: 1,
        page_size: 20,
        task_type: 'repair'
      })
    })

    it('应该根据任务状态筛选', async () => {
      await wrapper.setData({
        filters: { ...wrapper.vm.filters, task_status: 'pending' }
      })
      
      wrapper.vm.handleFilter()
      await new Promise(resolve => setTimeout(resolve, 350))
      
      expect(tasksApi.getTasks).toHaveBeenCalledWith({
        page: 1,
        page_size: 20,
        task_status: 'pending'
      })
    })

    it('应该根据优先级筛选', async () => {
      await wrapper.setData({
        filters: { ...wrapper.vm.filters, priority: 'high' }
      })
      
      wrapper.vm.handleFilter()
      await new Promise(resolve => setTimeout(resolve, 350))
      
      expect(tasksApi.getTasks).toHaveBeenCalledWith({
        page: 1,
        page_size: 20,
        priority: 'high'
      })
    })

    it('应该根据负责人筛选', async () => {
      await wrapper.setData({
        filters: { ...wrapper.vm.filters, assignee_id: 1 }
      })
      
      wrapper.vm.handleFilter()
      await new Promise(resolve => setTimeout(resolve, 350))
      
      expect(tasksApi.getTasks).toHaveBeenCalledWith({
        page: 1,
        page_size: 20,
        assignee_id: 1
      })
    })
  })

  describe('任务搜索', () => {
    it('应该处理搜索输入', async () => {
      const searchInput = wrapper.find('input[placeholder*="搜索"]')
      if (searchInput.exists()) {
        await searchInput.setValue('测试任务')
        
        await new Promise(resolve => setTimeout(resolve, 600))
        
        expect(tasksApi.getTasks).toHaveBeenCalledWith({
          page: 1,
          page_size: 20,
          search: '测试任务'
        })
      }
    })

    it('应该在搜索时重置页码', async () => {
      wrapper.vm.pagination.page = 3
      wrapper.vm.searchQuery = '新搜索'
      
      wrapper.vm.handleSearch()
      await new Promise(resolve => setTimeout(resolve, 600))
      
      expect(wrapper.vm.pagination.page).toBe(1)
    })
  })

  describe('任务状态管理', () => {
    it('应该正确显示任务状态标签', () => {
      wrapper.vm.tasks = mockTasksData.items
      
      expect(wrapper.vm.getStatusTagType('pending')).toBe('warning')
      expect(wrapper.vm.getStatusTagType('in_progress')).toBe('primary')
      expect(wrapper.vm.getStatusTagType('completed')).toBe('success')
      expect(wrapper.vm.getStatusTagType('cancelled')).toBe('danger')
    })

    it('应该正确显示任务类型标签', () => {
      expect(wrapper.vm.getTypeTagType('repair')).toBe('danger')
      expect(wrapper.vm.getTypeTagType('monitoring')).toBe('primary')
      expect(wrapper.vm.getTypeTagType('assistance')).toBe('success')
    })

    it('应该正确显示优先级标签', () => {
      expect(wrapper.vm.getPriorityTagType('high')).toBe('danger')
      expect(wrapper.vm.getPriorityTagType('medium')).toBe('warning')
      expect(wrapper.vm.getPriorityTagType('low')).toBe('info')
    })
  })

  describe('任务操作', () => {
    beforeEach(() => {
      wrapper.vm.tasks = mockTasksData.items
    })

    it('应该处理任务详情查看', async () => {
      vi.mocked(tasksApi.getTaskDetail).mockResolvedValue(mockTasksData.items[0])
      
      await wrapper.vm.handleViewDetail(mockTasksData.items[0])
      
      expect(tasksApi.getTaskDetail).toHaveBeenCalledWith(1)
    })

    it('应该处理任务编辑', async () => {
      await wrapper.vm.handleEdit(mockTasksData.items[0])
      expect(wrapper.vm.editDialogVisible).toBe(true)
    })

    it('应该处理任务创建', async () => {
      await wrapper.vm.handleCreate()
      expect(wrapper.vm.createDialogVisible).toBe(true)
    })

    it('应该处理批量导入', async () => {
      await wrapper.vm.handleImport()
      expect(wrapper.vm.importDialogVisible).toBe(true)
    })
  })

  describe('分页功能', () => {
    it('应该处理页码变化', async () => {
      await wrapper.vm.handlePageChange(2)
      
      expect(wrapper.vm.pagination.page).toBe(2)
      expect(tasksApi.getTasks).toHaveBeenCalledWith({
        page: 2,
        page_size: 20
      })
    })

    it('应该处理每页大小变化', async () => {
      await wrapper.vm.handleSizeChange(50)
      
      expect(wrapper.vm.pagination.page_size).toBe(50)
      expect(wrapper.vm.pagination.page).toBe(1)
      expect(tasksApi.getTasks).toHaveBeenCalledWith({
        page: 1,
        page_size: 50
      })
    })
  })

  describe('时间相关功能', () => {
    it('应该正确格式化日期时间', () => {
      const datetime = '2023-12-01T10:00:00'
      const result = wrapper.vm.formatDateTime(datetime)
      expect(result).toMatch(/2023.*12.*1.*10.*0.*0/)
    })

    it('应该判断任务是否逾期', () => {
      const overdueTask = {
        ...mockTasksData.items[0],
        due_date: '2023-01-01T10:00:00',
        task_status: 'pending'
      }
      expect(wrapper.vm.isTaskOverdue(overdueTask)).toBe(true)
      
      const normalTask = {
        ...mockTasksData.items[0],
        task_status: 'completed'
      }
      expect(wrapper.vm.isTaskOverdue(normalTask)).toBe(false)
    })

    it('应该计算剩余时间', () => {
      const futureTask = {
        ...mockTasksData.items[0],
        due_date: new Date(Date.now() + 24 * 60 * 60 * 1000).toISOString()
      }
      const remaining = wrapper.vm.getTimeRemaining(futureTask)
      expect(remaining).toContain('天')
    })
  })

  describe('导出功能', () => {
    it('应该处理数据导出', async () => {
      await wrapper.vm.handleExport()
      expect(wrapper.vm.exportDialogVisible).toBe(true)
    })

    it('应该生成导出参数', () => {
      wrapper.vm.filters = {
        task_type: 'repair',
        task_status: 'completed',
        priority: 'high'
      }
      
      const params = wrapper.vm.getExportParams()
      expect(params).toEqual({
        task_type: 'repair',
        task_status: 'completed',
        priority: 'high'
      })
    })
  })

  describe('批量操作', () => {
    beforeEach(() => {
      wrapper.vm.tasks = mockTasksData.items
    })

    it('应该处理批量任务选择', async () => {
      const selectedTasks = [mockTasksData.items[0]]
      await wrapper.vm.handleSelectionChange(selectedTasks)
      
      expect(wrapper.vm.selectedTasks).toEqual(selectedTasks)
    })

    it('应该在有选择时显示批量操作', async () => {
      wrapper.vm.selectedTasks = mockTasksData.items
      await wrapper.vm.$nextTick()
      
      expect(wrapper.vm.selectedTasks.length).toBe(2)
    })

    it('应该处理批量状态更新', async () => {
      wrapper.vm.selectedTasks = mockTasksData.items
      await wrapper.vm.handleBatchStatusUpdate('completed')
      
      expect(ElMessage.info).toHaveBeenCalledWith('批量状态更新功能开发中')
    })
  })

  describe('响应式设计', () => {
    it('应该在移动设备上隐藏某些列', async () => {
      // 模拟移动设备
      Object.defineProperty(window, 'innerWidth', {
        writable: true,
        configurable: true,
        value: 600,
      })
      
      window.dispatchEvent(new Event('resize'))
      await wrapper.vm.$nextTick()
      
      // 检查移动设备适配逻辑
      expect(wrapper.vm.isMobile).toBe(true)
    })
  })
})