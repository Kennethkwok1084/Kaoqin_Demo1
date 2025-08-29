import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import * as tasksApi from '@/api/tasks'
import type { Task, TaskCreateRequest, TaskUpdateRequest, TaskListParams } from '@/types/task'

export const useTasksStore = defineStore('tasks', () => {
  // State
  const tasks = ref<Task[]>([])
  const currentTask = ref<Task | null>(null)
  const loading = ref(false)
  const error = ref<string | null>(null)
  
  // Pagination state - as an object to match test expectations
  const pagination = ref({
    page: 1,
    page_size: 20,
    total: 0,
    total_pages: 0
  })
  
  // Filters state
  const searchQuery = ref('')
  const filters = ref<Record<string, any>>({})

  // Getters
  const pendingTasks = computed(() => 
    tasks.value.filter(task => task.task_status === 'pending' || task.status === 'pending')
  )
  
  const inProgressTasks = computed(() => 
    tasks.value.filter(task => task.task_status === 'in_progress' || task.status === 'in_progress')
  )
  
  const completedTasks = computed(() => 
    tasks.value.filter(task => task.task_status === 'completed' || task.status === 'completed')
  )
  
  const totalTasks = computed(() => pagination.value.total)
  const hasNextPage = computed(() => pagination.value.page < pagination.value.total_pages)
  const hasPrevPage = computed(() => pagination.value.page > 1)

  // Actions
  const fetchTasks = async (params?: TaskListParams) => {
    loading.value = true
    error.value = null
    
    try {
      const queryParams = {
        page: params?.page || pagination.value.page,
        page_size: params?.page_size || pagination.value.page_size,
        search: params?.search || searchQuery.value,
        ...params,
        ...filters.value
      }
      
      const response = await tasksApi.getTasks(queryParams)
      
      tasks.value = response.items || []
      pagination.value = {
        page: response.page || 1,
        page_size: response.page_size || 20,
        total: response.total || 0,
        total_pages: response.total_pages || 0
      }
      
      return response
    } catch (err: any) {
      error.value = err?.message || 'Failed to fetch tasks'
      throw err
    } finally {
      loading.value = false
    }
  }

  const fetchTaskDetail = async (id: number) => {
    loading.value = true
    error.value = null
    
    try {
      const task = await tasksApi.getTaskDetail(id)
      currentTask.value = task
      return task
    } catch (err: any) {
      error.value = err?.message || 'Failed to fetch task detail'
      throw err
    } finally {
      loading.value = false
    }
  }

  const createTask = async (taskData: TaskCreateRequest) => {
    loading.value = true
    error.value = null
    
    try {
      const newTask = await tasksApi.createTask(taskData)
      tasks.value.unshift(newTask)
      pagination.value.total += 1
      
      // Refresh list to ensure consistency
      await fetchTasks()
      
      return newTask
    } catch (err: any) {
      error.value = err?.message || 'Failed to create task'
      throw err
    } finally {
      loading.value = false
    }
  }

  const updateTask = async (id: number, taskData: TaskUpdateRequest) => {
    loading.value = true
    error.value = null
    
    try {
      const updatedTask = await tasksApi.updateTask(id, taskData)
      
      // Update in tasks list
      const index = tasks.value.findIndex(task => task.id === id)
      if (index !== -1) {
        tasks.value[index] = { ...tasks.value[index], ...updatedTask }
      }
      
      // Update current task if it's the same
      if (currentTask.value?.id === id) {
        currentTask.value = { ...currentTask.value, ...updatedTask }
      }
      
      return updatedTask
    } catch (err: any) {
      error.value = err?.message || 'Failed to update task'
      throw err
    } finally {
      loading.value = false
    }
  }

  const deleteTask = async (id: number) => {
    loading.value = true
    error.value = null
    
    try {
      await tasksApi.deleteTask(id)
      
      // Remove from tasks list
      tasks.value = tasks.value.filter(task => task.id !== id)
      pagination.value.total = Math.max(0, pagination.value.total - 1)
      
      // Clear current task if it's the deleted one
      if (currentTask.value?.id === id) {
        currentTask.value = null
      }
      
      return true
    } catch (err: any) {
      error.value = err?.message || 'Failed to delete task'
      throw err
    } finally {
      loading.value = false
    }
  }

  const setSearchQuery = (query: string) => {
    searchQuery.value = query
    fetchTasks()
  }

  const setFilters = (newFilters: Record<string, any>) => {
    filters.value = { ...filters.value, ...newFilters }
    fetchTasks()
  }

  const clearFilters = () => {
    filters.value = {}
    searchQuery.value = ''
    fetchTasks()
  }

  const setPage = (newPage: number) => {
    pagination.value.page = newPage
    fetchTasks()
  }

  const setPageSize = (size: number) => {
    pagination.value.page_size = size
    pagination.value.page = 1 // Reset to first page
    fetchTasks()
  }

  const resetTasks = () => {
    tasks.value = []
    currentTask.value = null
    loading.value = false
    error.value = null
    pagination.value = {
      page: 1,
      page_size: 20,
      total: 0,
      total_pages: 0
    }
    searchQuery.value = ''
    filters.value = {}
  }

  return {
    // State
    tasks,
    currentTask,
    loading,
    error,
    pagination,
    searchQuery,
    filters,
    
    // Getters
    pendingTasks,
    inProgressTasks,
    completedTasks,
    totalTasks,
    hasNextPage,
    hasPrevPage,
    
    // Actions
    fetchTasks,
    fetchTaskDetail,
    createTask,
    updateTask,
    deleteTask,
    setSearchQuery,
    setFilters,
    clearFilters,
    setPage,
    setPageSize,
    resetTasks,
    
    // Legacy aliases for compatibility
    getTasks: fetchTasks,
    getTaskDetail: fetchTaskDetail
  }
})