// Mock for @/api/dashboard
import { vi } from 'vitest'

export const getDashboardOverview = vi.fn().mockResolvedValue({
  total_tasks: 156,
  pending_tasks: 23,
  in_progress_tasks: 45,
  completed_tasks: 88,
  total_members: 42,
  active_members: 38,
  total_work_hours: 3240,
  avg_completion_time: 2.5
})

export const getRecentTasks = vi.fn().mockResolvedValue([
  {
    id: 1,
    title: '图书馆网络故障',
    task_type: 'repair',
    task_status: 'pending',
    priority: 'high',
    created_at: '2023-12-01T10:00:00',
    assignee_name: '张三'
  },
  {
    id: 2,
    title: '宿舍楼监控检查',
    task_type: 'monitoring',
    task_status: 'in_progress',
    priority: 'medium',
    created_at: '2023-12-01T09:30:00',
    assignee_name: '李四'
  }
])

export const getRecentAttendance = vi.fn().mockResolvedValue([
  {
    id: 1,
    member_name: '张三',
    check_in_time: '2023-12-01T08:30:00',
    check_out_time: '2023-12-01T17:30:00',
    work_hours: 8.5,
    status: 'normal'
  },
  {
    id: 2,
    member_name: '李四',
    check_in_time: '2023-12-01T08:45:00',
    check_out_time: null,
    work_hours: 0,
    status: 'working'
  }
])