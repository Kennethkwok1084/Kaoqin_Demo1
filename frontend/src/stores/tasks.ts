import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useTasksStore = defineStore('tasks', () => {
  const tasks = ref([])
  const loading = ref(false)
  const pagination = ref({ current: 1, pageSize: 10, total: 0 })

  const getTasks = () => {}
  const getTaskDetail = (id: string) => {}
  const createTask = (task: any) => {}
  const updateTask = (id: string, task: any) => {}
  const deleteTask = (id: string) => {}
  const resetTasks = () => {}

  return {
    tasks,
    loading,
    pagination,
    getTasks,
    getTaskDetail,
    createTask,
    updateTask,
    deleteTask,
    resetTasks
  }
})