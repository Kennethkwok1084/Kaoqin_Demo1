// 任务管理状态
import { defineStore } from 'pinia'
import { ref, computed, readonly } from 'vue'
import type { Task } from '@/api/client'
import { api } from '@/api/client'

// 临时类型定义
export interface TaskStats {
  overview: {
    total: number
    pending: number
    inProgress: number 
    completed: number
  }
}

export interface TaskTag {
  id: number
  name: string
  description: string
}

export interface TaskFilters {
  page?: number
  pageSize?: number
  search?: string
  taskStatus?: string
  type?: string
  assignedTo?: number
  sortBy?: string
  sortOrder?: 'asc' | 'desc'
}

export const useTasksStore = defineStore('tasks', () => {
  // 状态
  const tasks = ref<Task[]>([])
  const total = ref(0)
  const loading = ref(false)
  const error = ref<string | null>(null)
  const stats = ref<TaskStats | null>(null)
  const tags = ref<TaskTag[]>([])
  
  // 当前筛选条件
  const filters = ref<TaskFilters>({
    page: 1,
    pageSize: 20,
    sortBy: 'createdAt',
    sortOrder: 'desc'
  })

  // 计算属性
  const totalPages = computed(() => Math.ceil(total.value / (filters.value.pageSize || 20)))
  const pendingTasks = computed(() => tasks.value.filter(task => task.status === 'pending'))
  const inProgressTasks = computed(() => tasks.value.filter(task => task.status === 'in_progress'))
  const completedTasks = computed(() => tasks.value.filter(task => task.status === 'completed'))

  // 动作
  async function fetchTasks(newFilters?: Partial<TaskFilters>) {
    if (newFilters) {
      filters.value = { ...filters.value, ...newFilters }
    }

    loading.value = true
    error.value = null

    try {
      const response = await api.getTasks(filters.value)
      
      if (response.success && response.data) {
        tasks.value = response.data.items
        total.value = response.data.total
      } else {
        throw new Error(response.message || '获取任务列表失败')
      }
    } catch (err: any) {
      error.value = err.message
      console.error('Fetch tasks error:', err)
    } finally {
      loading.value = false
    }
  }

  async function createTask(taskData: {
    title: string
    description: string
    location: string
    assignedTo?: number
    reporterName: string
    reporterContact: string
    tagIds?: number[]
  }) {
    loading.value = true
    error.value = null

    try {
      const response = await api.createTask(taskData)
      
      if (response.success && response.data) {
        // 重新加载任务列表
        await fetchTasks()
        return { success: true, message: response.message, data: response.data }
      } else {
        throw new Error(response.message || '创建任务失败')
      }
    } catch (err: any) {
      error.value = err.message
      return { success: false, message: error.value }
    } finally {
      loading.value = false
    }
  }

  async function startTask(taskId: number) {
    loading.value = true
    error.value = null

    try {
      const response = await api.startTask(taskId)
      
      if (response.success) {
        // 更新本地任务状态
        const task = tasks.value.find(t => t.id === taskId)
        if (task) {
          task.status = 'in_progress'
          task.startedAt = response.data?.startedAt || new Date().toISOString()
        }
        
        return { success: true, message: response.message }
      } else {
        throw new Error(response.message || '开始任务失败')
      }
    } catch (err: any) {
      error.value = err.message
      return { success: false, message: error.value }
    } finally {
      loading.value = false
    }
  }

  async function completeTask(taskId: number, actualHours: number) {
    loading.value = true
    error.value = null

    try {
      const response = await api.completeTask(taskId, actualHours)
      
      if (response.success) {
        // 更新本地任务状态
        const task = tasks.value.find(t => t.id === taskId)
        if (task) {
          task.status = 'completed'
          task.completedAt = new Date().toISOString()
          task.actualHours = actualHours
        }
        
        return { success: true, message: response.message }
      } else {
        throw new Error(response.message || '完成任务失败')
      }
    } catch (err: any) {
      error.value = err.message
      return { success: false, message: error.value }
    } finally {
      loading.value = false
    }
  }

  async function fetchTaskStats() {
    try {
      const response = await api.getTaskStats()
      
      if (response.success && response.data) {
        stats.value = response.data
      }
    } catch (err: any) {
      console.error('Fetch task stats error:', err)
    }
  }

  async function fetchTags() {
    try {
      const response = await api.getTags({ isActive: true })
      
      if (response.success && response.data) {
        tags.value = response.data.items
      }
    } catch (err: any) {
      console.error('Fetch tags error:', err)
    }
  }

  async function createTag(tagData: {
    name: string
    description: string
    workMinutes: number
    isActive: boolean
    tagType: string
  }) {
    try {
      const response = await api.createTag(tagData)
      
      if (response.success) {
        await fetchTags() // 重新加载标签列表
        return { success: true, message: response.message }
      } else {
        throw new Error(response.message || '创建标签失败')
      }
    } catch (err: any) {
      return { success: false, message: err.message }
    }
  }

  // 重置筛选条件
  function resetFilters() {
    filters.value = {
      page: 1,
      pageSize: 20,
      sortBy: 'createdAt',
      sortOrder: 'desc'
    }
  }

  // 设置筛选条件
  function setFilters(newFilters: Partial<TaskFilters>) {
    filters.value = { ...filters.value, ...newFilters }
  }

  // 清除错误
  function clearError() {
    error.value = null
  }

  // 根据ID获取任务
  function getTaskById(taskId: number): Task | undefined {
    return tasks.value.find(task => task.id === taskId)
  }

  // 获取我的任务
  function getMyTasks(userId: number): Task[] {
    return tasks.value.filter(task => task.assigneeId === userId)
  }

  // 获取今日任务
  function getTodayTasks(): Task[] {
    const today = new Date().toISOString().split('T')[0]
    return tasks.value.filter(task => 
      task.createdAt.startsWith(today) || 
      (task.dueDate && task.dueDate.startsWith(today))
    )
  }

  return {
    // 状态
    tasks: readonly(tasks),
    total: readonly(total),
    loading: readonly(loading),
    error: readonly(error),
    stats: readonly(stats),
    tags: readonly(tags),
    filters: readonly(filters),
    
    // 计算属性
    totalPages,
    pendingTasks,
    inProgressTasks,
    completedTasks,
    
    // 动作
    fetchTasks,
    createTask,
    startTask,
    completeTask,
    fetchTaskStats,
    fetchTags,
    createTag,
    resetFilters,
    setFilters,
    clearError,
    getTaskById,
    getMyTasks,
    getTodayTasks
  }
})