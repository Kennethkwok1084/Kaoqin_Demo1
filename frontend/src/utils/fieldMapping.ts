/**
 * Frontend-Backend Field Mapping Utilities
 * Provides standardized field mapping and transformation between frontend and backend APIs
 */

// ===== CORE FIELD MAPPING TYPES =====

export interface FieldMapping {
  [frontendField: string]: string | ((value: any) => any)
}

export interface ApiResponse<T = any> {
  success: boolean
  message: string
  data: T
  status_code?: number
}

// ===== ENUM VALUE MAPPINGS =====

export const UserRoleMapping = {
  // Backend -> Frontend
  toFrontend: {
    admin: 'admin',
    group_leader: 'group_leader',
    member: 'member',
    guest: 'guest'
  },
  // Frontend -> Backend
  toBackend: {
    admin: 'admin',
    group_leader: 'group_leader',
    member: 'member',
    guest: 'guest'
  }
} as const

export const TaskStatusMapping = {
  // Backend -> Frontend
  toFrontend: {
    pending: 'pending',
    in_progress: 'in_progress',
    completed: 'completed',
    cancelled: 'cancelled',
    on_hold: 'on_hold'
  },
  // Frontend -> Backend
  toBackend: {
    pending: 'pending',
    in_progress: 'in_progress',
    completed: 'completed',
    cancelled: 'cancelled',
    on_hold: 'on_hold'
  }
} as const

export const TaskTypeMapping = {
  // Backend -> Frontend
  toFrontend: {
    online: 'online',
    offline: 'offline'
  },
  // Frontend -> Backend
  toBackend: {
    online: 'online',
    offline: 'offline'
  }
} as const

// ===== FIELD NAME MAPPINGS =====

// Authentication API Field Mapping
export const AuthFieldMapping = {
  // Backend -> Frontend
  toFrontend: {
    student_id: 'studentId',
    class_name: 'className',
    is_active: 'isActive',
    is_verified: 'isVerified',
    profile_completed: 'profileCompleted',
    needs_profile_completion: 'needsProfileCompletion',
    last_login: 'lastLogin',
    login_count: 'loginCount',
    created_at: 'createdAt',
    updated_at: 'updatedAt',
    access_token: 'accessToken',
    refresh_token: 'refreshToken',
    token_type: 'tokenType',
    expires_in: 'expiresIn'
  },
  // Frontend -> Backend
  toBackend: {
    studentId: 'student_id',
    className: 'class_name',
    isActive: 'is_active',
    isVerified: 'is_verified',
    profileCompleted: 'profile_completed',
    needsProfileCompletion: 'needs_profile_completion',
    lastLogin: 'last_login',
    loginCount: 'login_count',
    createdAt: 'created_at',
    updatedAt: 'updated_at',
    accessToken: 'access_token',
    refreshToken: 'refresh_token',
    tokenType: 'token_type',
    expiresIn: 'expires_in'
  }
} as const

// Member Management API Field Mapping
export const MemberFieldMapping = {
  // Backend -> Frontend
  toFrontend: {
    student_id: 'studentId',
    class_name: 'className',
    group_id: 'groupId',
    is_active: 'isActive',
    is_verified: 'isVerified',
    last_login: 'lastLogin',
    login_count: 'loginCount',
    created_at: 'createdAt',
    updated_at: 'updatedAt',
    password_hash: 'passwordHash'
  },
  // Frontend -> Backend
  toBackend: {
    studentId: 'student_id',
    className: 'class_name',
    groupId: 'group_id',
    isActive: 'is_active',
    isVerified: 'is_verified',
    lastLogin: 'last_login',
    loginCount: 'login_count',
    createdAt: 'created_at',
    updatedAt: 'updated_at',
    passwordHash: 'password_hash'
  }
} as const

// Task Management API Field Mapping
export const TaskFieldMapping = {
  // Backend -> Frontend
  toFrontend: {
    task_id: 'taskId',
    task_number: 'taskNumber',
    task_type: 'taskType',
    task_category: 'taskCategory',
    member_id: 'memberId',
    assigned_to: 'assignedTo',
    assigned_by: 'assignedBy',
    assignee_name: 'assigneeName',
    assigner_name: 'assignerName',
    creator_name: 'creatorName',
    created_by: 'createdBy',
    report_time: 'reportTime',
    response_time: 'responseTime',
    completion_time: 'completionTime',
    estimated_minutes: 'estimatedMinutes',
    actual_minutes: 'actualMinutes',
    calculated_minutes: 'calculatedMinutes',
    work_minutes: 'workMinutes',
    due_date: 'dueDate',
    is_rush_order: 'isRushOrder',
    is_urgent: 'isUrgent',
    reporter_name: 'reporterName',
    reporter_contact: 'reporterContact',
    completion_note: 'completionNote',
    internal_note: 'internalNote',
    created_at: 'createdAt',
    updated_at: 'updatedAt'
  },
  // Frontend -> Backend
  toBackend: {
    taskId: 'task_id',
    taskNumber: 'task_number',
    taskType: 'task_type',
    taskCategory: 'task_category',
    memberId: 'member_id',
    assignedTo: 'assigned_to',
    assignedBy: 'assigned_by',
    assigneeName: 'assignee_name',
    assignerName: 'assigner_name',
    creatorName: 'creator_name',
    createdBy: 'created_by',
    reportTime: 'report_time',
    responseTime: 'response_time',
    completionTime: 'completion_time',
    estimatedMinutes: 'estimated_minutes',
    actualMinutes: 'actual_minutes',
    calculatedMinutes: 'calculated_minutes',
    workMinutes: 'work_minutes',
    dueDate: 'due_date',
    isRushOrder: 'is_rush_order',
    isUrgent: 'is_urgent',
    reporterName: 'reporter_name',
    reporterContact: 'reporter_contact',
    completionNote: 'completion_note',
    internalNote: 'internal_note',
    createdAt: 'created_at',
    updatedAt: 'updated_at'
  }
} as const

// Work Hours API Field Mapping
export const WorkHoursFieldMapping = {
  // Backend -> Frontend
  toFrontend: {
    member_id: 'memberId',
    member_name: 'memberName',
    task_id: 'taskId',
    task_type: 'taskType',
    work_minutes: 'workMinutes',
    base_minutes: 'baseMinutes',
    modifier_minutes: 'modifierMinutes',
    total_minutes: 'totalMinutes',
    attendance_date: 'attendanceDate',
    checkin_time: 'checkinTime',
    checkout_time: 'checkoutTime',
    work_hours: 'workHours',
    break_minutes: 'breakMinutes',
    created_at: 'createdAt',
    updated_at: 'updatedAt'
  },
  // Frontend -> Backend
  toBackend: {
    memberId: 'member_id',
    memberName: 'member_name',
    taskId: 'task_id',
    taskType: 'task_type',
    workMinutes: 'work_minutes',
    baseMinutes: 'base_minutes',
    modifierMinutes: 'modifier_minutes',
    totalMinutes: 'total_minutes',
    attendanceDate: 'attendance_date',
    checkinTime: 'checkin_time',
    checkoutTime: 'checkout_time',
    workHours: 'work_hours',
    breakMinutes: 'break_minutes',
    createdAt: 'created_at',
    updatedAt: 'updated_at'
  }
} as const

// ===== TRANSFORMATION UTILITIES =====

/**
 * Transform object field names using mapping
 */
export function transformFields<T = any>(
  obj: any,
  mapping: Record<string, string>
): T {
  if (!obj || typeof obj !== 'object') {
    return obj
  }

  const result: any = {}

  for (const [key, value] of Object.entries(obj)) {
    const mappedKey = mapping[key] || key

    if (Array.isArray(value)) {
      result[mappedKey] = value.map(item =>
        typeof item === 'object' ? transformFields(item, mapping) : item
      )
    } else if (
      value &&
      typeof value === 'object' &&
      value.constructor === Object
    ) {
      result[mappedKey] = transformFields(value, mapping)
    } else {
      result[mappedKey] = value
    }
  }

  return result
}

/**
 * Transform backend response to frontend format
 */
export function transformBackendToFrontend<T = any>(
  data: any,
  mapping: Record<string, string>
): T {
  return transformFields<T>(data, mapping)
}

/**
 * Transform frontend request to backend format
 */
export function transformFrontendToBackend<T = any>(
  data: any,
  mapping: Record<string, string>
): T {
  return transformFields<T>(data, mapping)
}

/**
 * Transform enum values
 */
export function transformEnum(
  value: string,
  mapping: Record<string, string>
): string {
  return mapping[value] || value
}

/**
 * Convert time units (minutes <-> hours)
 */
export const TimeUnitConverters = {
  minutesToHours: (minutes: number): number =>
    Math.round((minutes / 60) * 100) / 100,
  hoursToMinutes: (hours: number): number => Math.round(hours * 60),

  // For displaying purposes
  formatMinutes: (minutes: number): string => {
    const hours = Math.floor(minutes / 60)
    const mins = minutes % 60
    if (hours > 0) {
      return `${hours}小时${mins > 0 ? mins + '分钟' : ''}`
    }
    return `${mins}分钟`
  }
}

// ===== API RESPONSE WRAPPER UTILITIES =====

/**
 * Check if response is wrapped in standard API format
 */
export function isWrappedResponse(response: any): response is ApiResponse {
  return (
    response &&
    typeof response === 'object' &&
    'success' in response &&
    'message' in response &&
    'data' in response
  )
}

/**
 * Extract data from wrapped API response
 */
export function extractResponseData<T>(response: any): T {
  if (isWrappedResponse(response)) {
    return response.data
  }
  return response
}

/**
 * Ensure response is properly formatted
 */
export function normalizeApiResponse<T>(response: any): ApiResponse<T> {
  if (isWrappedResponse(response)) {
    return response
  }

  // If not wrapped, create wrapper
  return {
    success: true,
    message: 'Success',
    data: response
  }
}

// ===== VALIDATION UTILITIES =====

/**
 * Validate required fields exist in object
 */
export function validateRequiredFields(
  obj: any,
  requiredFields: string[]
): { valid: boolean; missing: string[] } {
  const missing: string[] = []

  for (const field of requiredFields) {
    if (!(field in obj) || obj[field] === undefined || obj[field] === null) {
      missing.push(field)
    }
  }

  return {
    valid: missing.length === 0,
    missing
  }
}

/**
 * Create field mapping transformer for specific API
 */
export function createFieldTransformer(mapping: {
  toFrontend: Record<string, string>
  toBackend: Record<string, string>
}) {
  return {
    toFrontend: <T>(data: any): T =>
      transformBackendToFrontend<T>(data, mapping.toFrontend),
    toBackend: <T>(data: any): T =>
      transformFrontendToBackend<T>(data, mapping.toBackend)
  }
}

// ===== PRE-CONFIGURED TRANSFORMERS =====

export const AuthTransformer = createFieldTransformer(AuthFieldMapping)
export const MemberTransformer = createFieldTransformer(MemberFieldMapping)
export const TaskTransformer = createFieldTransformer(TaskFieldMapping)
export const WorkHoursTransformer = createFieldTransformer(
  WorkHoursFieldMapping
)
