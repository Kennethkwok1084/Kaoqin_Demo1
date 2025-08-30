// 任务 API Mock
import { vi } from 'vitest'

// Mock 数据
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

const mockTaskStats = {
  total_tasks: 156,
  pending: 23,
  in_progress: 45,
  completed: 88,
  cancelled: 12,
  repair: 60,
  monitoring: 45,
  assistance: 35,
  high: 30,
  medium: 80,
  low: 46
}

// 导出所有需要的 API 函数
export const getTasks = vi.fn().mockResolvedValue(mockTasksData)
export const getTaskDetail = vi.fn().mockResolvedValue(mockTasksData.items[0])
export const createTask = vi
  .fn()
  .mockResolvedValue({ id: 3, ...mockTasksData.items[0] })
export const updateTask = vi.fn().mockResolvedValue(mockTasksData.items[0])
export const deleteTask = vi.fn().mockResolvedValue(undefined)
export const getTaskStats = vi.fn().mockResolvedValue(mockTaskStats)
export const exportTasks = vi.fn().mockResolvedValue(undefined)

// 导出 tasksApi 对象
export const tasksApi = {
  getTasks,
  getTaskDetail,
  createTask,
  updateTask,
  deleteTask,
  getTaskStats,
  exportTasks
}

// 默认导出
export default tasksApi
