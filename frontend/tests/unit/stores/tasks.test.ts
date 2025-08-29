import { describe, it, expect, beforeEach, vi } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useTasksStore } from '@/stores/tasks'
import * as tasksApi from '@/api/tasks'
import type { Task, TaskCreateRequest, TaskUpdateRequest } from '@/types/task'

// API is already mocked in setup.ts - no need to mock again

describe('Tasks Store', () => {
  let tasksStore: ReturnType<typeof useTasksStore>

  const mockTask: Task = {
    id: 1,
    title: '测试任务',
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
  }

  const mockTasksList = {
    items: [mockTask],
    total: 1,
    page: 1,
    page_size: 20,
    total_pages: 1
  }

  beforeEach(() => {
    setActivePinia(createPinia())
    tasksStore = useTasksStore()
    vi.clearAllMocks()
  })

  describe('初始状态', () => {
    it('应该有正确的初始状态', () => {
      expect(tasksStore.tasks).toEqual([])
      expect(tasksStore.currentTask).toBeNull()
      expect(tasksStore.loading).toBe(false)
      expect(tasksStore.error).toBeNull()
      expect(tasksStore.pagination.page).toBe(1)
      expect(tasksStore.pagination.page_size).toBe(20)
      expect(tasksStore.pagination.total).toBe(0)
      expect(tasksStore.filters).toEqual({})
      expect(tasksStore.searchQuery).toBe('')
    })

    it('应该有正确的getters初始值', () => {
      expect(tasksStore.pendingTasks).toEqual([])
      expect(tasksStore.inProgressTasks).toEqual([])
      expect(tasksStore.completedTasks).toEqual([])
      expect(tasksStore.totalTasks).toBe(0)
      expect(tasksStore.hasNextPage).toBe(false)
      expect(tasksStore.hasPrevPage).toBe(false)
    })
  })

  describe('fetchTasks', () => {
    it('应该成功获取任务列表', async () => {
      vi.mocked(tasksApi.getTasks).mockResolvedValue(mockTasksList)

      await tasksStore.fetchTasks()

      expect(tasksStore.loading).toBe(false)
      expect(tasksStore.tasks).toEqual(mockTasksList.items)
      expect(tasksStore.pagination.total).toBe(mockTasksList.total)
      expect(tasksStore.pagination.total_pages).toBe(mockTasksList.total_pages)
      expect(tasksStore.error).toBeNull()
    })

    it('应该传递正确的参数给API', async () => {
      vi.mocked(tasksApi.getTasks).mockResolvedValue(mockTasksList)

      tasksStore.pagination.page = 2
      tasksStore.pagination.page_size = 10
      tasksStore.searchQuery = '测试'
      tasksStore.filters = { task_type: 'repair', priority: 'high' }

      await tasksStore.fetchTasks()

      expect(tasksApi.getTasks).toHaveBeenCalledWith({
        page: 2,
        page_size: 10,
        search: '测试',
        task_type: 'repair',
        priority: 'high'
      })
    })

    it('应该处理API错误', async () => {
      const errorMessage = 'Network Error'
      vi.mocked(tasksApi.getTasks).mockRejectedValue(new Error(errorMessage))

      await tasksStore.fetchTasks()

      expect(tasksStore.loading).toBe(false)
      expect(tasksStore.error).toBe(errorMessage)
      expect(tasksStore.tasks).toEqual([])
    })

    it('应该在加载期间设置loading状态', async () => {
      let resolvePromise: (value: any) => void
      const promise = new Promise(resolve => {
        resolvePromise = resolve
      })
      vi.mocked(tasksApi.getTasks).mockReturnValue(promise)

      const fetchPromise = tasksStore.fetchTasks()
      expect(tasksStore.loading).toBe(true)

      resolvePromise!(mockTasksList)
      await fetchPromise

      expect(tasksStore.loading).toBe(false)
    })
  })

  describe('fetchTaskDetail', () => {
    it('应该成功获取任务详情', async () => {
      vi.mocked(tasksApi.getTaskDetail).mockResolvedValue(mockTask)

      await tasksStore.fetchTaskDetail(1)

      expect(tasksApi.getTaskDetail).toHaveBeenCalledWith(1)
      expect(tasksStore.currentTask).toEqual(mockTask)
      expect(tasksStore.error).toBeNull()
    })

    it('应该处理获取详情失败', async () => {
      const errorMessage = 'Task not found'
      vi.mocked(tasksApi.getTaskDetail).mockRejectedValue(
        new Error(errorMessage)
      )

      await tasksStore.fetchTaskDetail(999)

      expect(tasksStore.currentTask).toBeNull()
      expect(tasksStore.error).toBe(errorMessage)
    })
  })

  describe('createTask', () => {
    const createData: TaskCreateRequest = {
      title: '新任务',
      description: '新任务描述',
      task_type: 'repair',
      priority: 'medium',
      assignee_id: 1,
      reporter_name: '王五',
      reporter_phone: '13800138002',
      location: '宿舍楼',
      due_date: '2023-12-10T18:00:00'
    }

    it('应该成功创建任务', async () => {
      const createdTask = { ...mockTask, ...createData, id: 2 }
      vi.mocked(tasksApi.createTask).mockResolvedValue(createdTask)

      const result = await tasksStore.createTask(createData)

      expect(tasksApi.createTask).toHaveBeenCalledWith(createData)
      expect(result).toEqual(createdTask)
      expect(tasksStore.error).toBeNull()
    })

    it('应该在创建成功后刷新列表', async () => {
      const createdTask = { ...mockTask, ...createData, id: 2 }
      vi.mocked(tasksApi.createTask).mockResolvedValue(createdTask)
      vi.mocked(tasksApi.getTasks).mockResolvedValue({
        ...mockTasksList,
        items: [mockTask, createdTask],
        total: 2
      })

      await tasksStore.createTask(createData)

      expect(tasksApi.getTasks).toHaveBeenCalled()
      expect(tasksStore.tasks).toHaveLength(2)
    })

    it('应该处理创建失败', async () => {
      const errorMessage = 'Validation failed'
      vi.mocked(tasksApi.createTask).mockRejectedValue(new Error(errorMessage))

      const result = await tasksStore.createTask(createData)

      expect(result).toBeNull()
      expect(tasksStore.error).toBe(errorMessage)
    })
  })

  describe('updateTask', () => {
    const updateData: TaskUpdateRequest = {
      title: '更新的任务标题',
      task_status: 'in_progress',
      priority: 'low'
    }

    beforeEach(() => {
      tasksStore.tasks = [mockTask]
      tasksStore.currentTask = mockTask
    })

    it('应该成功更新任务', async () => {
      const updatedTask = { ...mockTask, ...updateData }
      vi.mocked(tasksApi.updateTask).mockResolvedValue(updatedTask)

      const result = await tasksStore.updateTask(1, updateData)

      expect(tasksApi.updateTask).toHaveBeenCalledWith(1, updateData)
      expect(result).toEqual(updatedTask)
      expect(tasksStore.error).toBeNull()
    })

    it('应该更新本地任务列表中的任务', async () => {
      const updatedTask = { ...mockTask, ...updateData }
      vi.mocked(tasksApi.updateTask).mockResolvedValue(updatedTask)

      await tasksStore.updateTask(1, updateData)

      expect(tasksStore.tasks[0]).toEqual(updatedTask)
    })

    it('应该更新当前任务详情', async () => {
      const updatedTask = { ...mockTask, ...updateData }
      vi.mocked(tasksApi.updateTask).mockResolvedValue(updatedTask)

      await tasksStore.updateTask(1, updateData)

      expect(tasksStore.currentTask).toEqual(updatedTask)
    })

    it('应该处理更新失败', async () => {
      const errorMessage = 'Update failed'
      vi.mocked(tasksApi.updateTask).mockRejectedValue(new Error(errorMessage))

      const result = await tasksStore.updateTask(1, updateData)

      expect(result).toBeNull()
      expect(tasksStore.error).toBe(errorMessage)
    })
  })

  describe('deleteTask', () => {
    beforeEach(() => {
      tasksStore.tasks = [mockTask, { ...mockTask, id: 2 }]
    })

    it('应该成功删除任务', async () => {
      vi.mocked(tasksApi.deleteTask).mockResolvedValue(undefined)

      const success = await tasksStore.deleteTask(1)

      expect(tasksApi.deleteTask).toHaveBeenCalledWith(1)
      expect(success).toBe(true)
      expect(tasksStore.error).toBeNull()
    })

    it('应该从本地列表中移除删除的任务', async () => {
      vi.mocked(tasksApi.deleteTask).mockResolvedValue(undefined)

      await tasksStore.deleteTask(1)

      expect(tasksStore.tasks).toHaveLength(1)
      expect(tasksStore.tasks[0].id).toBe(2)
    })

    it('应该处理删除失败', async () => {
      const errorMessage = 'Delete failed'
      vi.mocked(tasksApi.deleteTask).mockRejectedValue(new Error(errorMessage))

      const success = await tasksStore.deleteTask(1)

      expect(success).toBe(false)
      expect(tasksStore.error).toBe(errorMessage)
      expect(tasksStore.tasks).toHaveLength(2) // 任务仍然存在
    })
  })

  describe('搜索和筛选', () => {
    beforeEach(() => {
      tasksStore.tasks = [
        mockTask,
        {
          ...mockTask,
          id: 2,
          task_type: 'monitoring',
          task_status: 'in_progress'
        },
        {
          ...mockTask,
          id: 3,
          task_type: 'assistance',
          task_status: 'completed'
        }
      ]
    })

    it('应该设置搜索查询并触发搜索', async () => {
      vi.mocked(tasksApi.getTasks).mockResolvedValue(mockTasksList)

      await tasksStore.setSearchQuery('测试')

      expect(tasksStore.searchQuery).toBe('测试')
      expect(tasksStore.pagination.page).toBe(1) // 重置页码
      expect(tasksApi.getTasks).toHaveBeenCalledWith({
        page: 1,
        page_size: 20,
        search: '测试'
      })
    })

    it('应该设置筛选条件并触发搜索', async () => {
      vi.mocked(tasksApi.getTasks).mockResolvedValue(mockTasksList)

      await tasksStore.setFilters({ task_type: 'repair', priority: 'high' })

      expect(tasksStore.filters).toEqual({
        task_type: 'repair',
        priority: 'high'
      })
      expect(tasksStore.pagination.page).toBe(1)
      expect(tasksApi.getTasks).toHaveBeenCalledWith({
        page: 1,
        page_size: 20,
        task_type: 'repair',
        priority: 'high'
      })
    })

    it('应该清除筛选条件', async () => {
      tasksStore.filters = { task_type: 'repair' }
      vi.mocked(tasksApi.getTasks).mockResolvedValue(mockTasksList)

      await tasksStore.clearFilters()

      expect(tasksStore.filters).toEqual({})
      expect(tasksStore.searchQuery).toBe('')
      expect(tasksStore.pagination.page).toBe(1)
      expect(tasksApi.getTasks).toHaveBeenCalled()
    })
  })

  describe('分页', () => {
    it('应该设置页码并重新获取数据', async () => {
      vi.mocked(tasksApi.getTasks).mockResolvedValue(mockTasksList)

      await tasksStore.setPage(3)

      expect(tasksStore.pagination.page).toBe(3)
      expect(tasksApi.getTasks).toHaveBeenCalledWith({
        page: 3,
        page_size: 20
      })
    })

    it('应该设置页面大小并重新获取数据', async () => {
      vi.mocked(tasksApi.getTasks).mockResolvedValue(mockTasksList)

      await tasksStore.setPageSize(50)

      expect(tasksStore.pagination.page_size).toBe(50)
      expect(tasksStore.pagination.page).toBe(1) // 重置页码
      expect(tasksApi.getTasks).toHaveBeenCalledWith({
        page: 1,
        page_size: 50
      })
    })
  })

  describe('Getters', () => {
    beforeEach(() => {
      tasksStore.tasks = [
        { ...mockTask, id: 1, task_status: 'pending' },
        { ...mockTask, id: 2, task_status: 'in_progress' },
        { ...mockTask, id: 3, task_status: 'completed' },
        { ...mockTask, id: 4, task_status: 'pending' }
      ]
      tasksStore.pagination.total = 100
      tasksStore.pagination.page = 2
      tasksStore.pagination.total_pages = 5
    })

    it('应该正确过滤待处理任务', () => {
      expect(tasksStore.pendingTasks).toHaveLength(2)
      expect(
        tasksStore.pendingTasks.every(task => task.task_status === 'pending')
      ).toBe(true)
    })

    it('应该正确过滤进行中任务', () => {
      expect(tasksStore.inProgressTasks).toHaveLength(1)
      expect(tasksStore.inProgressTasks[0].task_status).toBe('in_progress')
    })

    it('应该正确过滤已完成任务', () => {
      expect(tasksStore.completedTasks).toHaveLength(1)
      expect(tasksStore.completedTasks[0].task_status).toBe('completed')
    })

    it('应该返回正确的总任务数', () => {
      expect(tasksStore.totalTasks).toBe(100) // 来自pagination.total
    })

    it('应该正确判断是否有下一页', () => {
      expect(tasksStore.hasNextPage).toBe(true)

      tasksStore.pagination.page = 5 // 最后一页
      expect(tasksStore.hasNextPage).toBe(false)
    })

    it('应该正确判断是否有上一页', () => {
      expect(tasksStore.hasPrevPage).toBe(true)

      tasksStore.pagination.page = 1 // 第一页
      expect(tasksStore.hasPrevPage).toBe(false)
    })
  })

  describe('工时详情', () => {
    const mockWorkTimeDetail = {
      task_id: 1,
      base_work_hours: 40,
      bonus_hours: 15,
      penalty_hours: -30,
      total_work_hours: 25,
      calculation_details: {
        base_calculation: '维修任务基础工时',
        bonuses: ['紧急处理奖励 +15分钟'],
        penalties: ['超时完成惩罚 -30分钟']
      }
    }

    it('应该获取任务工时详情', async () => {
      vi.mocked(tasksApi.getWorkTimeDetail).mockResolvedValue(
        mockWorkTimeDetail
      )

      const result = await tasksStore.getWorkTimeDetail(1)

      expect(tasksApi.getWorkTimeDetail).toHaveBeenCalledWith(1)
      expect(result).toEqual(mockWorkTimeDetail)
    })

    it('应该处理获取工时详情失败', async () => {
      vi.mocked(tasksApi.getWorkTimeDetail).mockRejectedValue(
        new Error('Work time not found')
      )

      const result = await tasksStore.getWorkTimeDetail(999)

      expect(result).toBeNull()
      expect(tasksStore.error).toBe('Work time not found')
    })
  })

  describe('批量操作', () => {
    beforeEach(() => {
      tasksStore.tasks = [
        { ...mockTask, id: 1 },
        { ...mockTask, id: 2 },
        { ...mockTask, id: 3 }
      ]
    })

    it('应该批量更新任务状态', async () => {
      const taskIds = [1, 2]
      const newStatus = 'completed'

      // Mock批量更新API
      vi.mocked(tasksApi.updateTask).mockResolvedValue({
        ...mockTask,
        task_status: newStatus
      })

      await tasksStore.batchUpdateStatus(taskIds, newStatus)

      expect(tasksApi.updateTask).toHaveBeenCalledTimes(2)
      expect(tasksApi.updateTask).toHaveBeenCalledWith(1, {
        task_status: newStatus
      })
      expect(tasksApi.updateTask).toHaveBeenCalledWith(2, {
        task_status: newStatus
      })
    })

    it('应该批量删除任务', async () => {
      const taskIds = [1, 3]

      vi.mocked(tasksApi.deleteTask).mockResolvedValue(undefined)

      const success = await tasksStore.batchDeleteTasks(taskIds)

      expect(success).toBe(true)
      expect(tasksApi.deleteTask).toHaveBeenCalledTimes(2)
      expect(tasksStore.tasks).toHaveLength(1)
      expect(tasksStore.tasks[0].id).toBe(2)
    })

    it('应该处理批量操作部分失败', async () => {
      const taskIds = [1, 2]

      vi.mocked(tasksApi.deleteTask)
        .mockResolvedValueOnce(undefined)
        .mockRejectedValueOnce(new Error('Delete failed'))

      const success = await tasksStore.batchDeleteTasks(taskIds)

      expect(success).toBe(false)
      expect(tasksStore.tasks).toHaveLength(2) // 只删除了一个任务
    })
  })

  describe('状态重置', () => {
    beforeEach(() => {
      tasksStore.tasks = [mockTask]
      tasksStore.currentTask = mockTask
      tasksStore.error = 'Some error'
      tasksStore.searchQuery = '搜索关键词'
      tasksStore.filters = { task_type: 'repair' }
      tasksStore.pagination.page = 3
    })

    it('应该重置所有状态', () => {
      tasksStore.resetState()

      expect(tasksStore.tasks).toEqual([])
      expect(tasksStore.currentTask).toBeNull()
      expect(tasksStore.error).toBeNull()
      expect(tasksStore.searchQuery).toBe('')
      expect(tasksStore.filters).toEqual({})
      expect(tasksStore.pagination.page).toBe(1)
      expect(tasksStore.pagination.page_size).toBe(20)
      expect(tasksStore.pagination.total).toBe(0)
    })

    it('应该只清除错误状态', () => {
      tasksStore.clearError()

      expect(tasksStore.error).toBeNull()
      expect(tasksStore.tasks).toHaveLength(1) // 其他状态保持不变
    })
  })
})
