// Type helpers and utilities for handling type assertions and enum lookups

import { TASK_TYPE_CONFIG, TASK_PRIORITY_CONFIG, TASK_STATUS_CONFIG } from './task'

// Helper to safely get task type config
export function getTaskTypeConfig(type: any) {
  if (type && typeof type === 'string' && type in TASK_TYPE_CONFIG) {
    return TASK_TYPE_CONFIG[type as keyof typeof TASK_TYPE_CONFIG]
  }
  return TASK_TYPE_CONFIG.other // fallback
}

// Helper to safely get task priority config
export function getTaskPriorityConfig(priority: any) {
  if (priority && typeof priority === 'string' && priority in TASK_PRIORITY_CONFIG) {
    return TASK_PRIORITY_CONFIG[priority as keyof typeof TASK_PRIORITY_CONFIG]
  }
  return TASK_PRIORITY_CONFIG.medium // fallback
}

// Helper to safely get task status config
export function getTaskStatusConfig(status: any) {
  if (status && typeof status === 'string' && status in TASK_STATUS_CONFIG) {
    return TASK_STATUS_CONFIG[status as keyof typeof TASK_STATUS_CONFIG]
  }
  return TASK_STATUS_CONFIG.pending // fallback
}

// Type guard for ensuring string is valid task type
export function isValidTaskType(type: any): type is keyof typeof TASK_TYPE_CONFIG {
  return typeof type === 'string' && type in TASK_TYPE_CONFIG
}

// Type guard for ensuring string is valid task priority
export function isValidTaskPriority(priority: any): priority is keyof typeof TASK_PRIORITY_CONFIG {
  return typeof priority === 'string' && priority in TASK_PRIORITY_CONFIG
}

// Type guard for ensuring string is valid task status
export function isValidTaskStatus(status: any): status is keyof typeof TASK_STATUS_CONFIG {
  return typeof status === 'string' && status in TASK_STATUS_CONFIG
}