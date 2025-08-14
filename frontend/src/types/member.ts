// 成员相关类型定义

export interface Member {
  id: number
  // 关键信息：必填
  username: string // 用户名
  fullName: string // 真实姓名
  role: 'admin' | 'user' | 'viewer' // 角色
  department: string // 部门
  className: string // 班级
  joinDate: string // 入职时间

  // 可选信息：用户可后续填写
  email?: string // 邮箱（可选）
  phone?: string // 手机号（可选）
  employeeId?: string // 员工号（可选）
  avatar?: string // 头像（可选）

  // 系统字段
  status: 'active' | 'inactive' | 'suspended'
  lastLoginAt: string | null
  createdAt: string
  updatedAt: string
  permissions: string[]
  stats?: MemberStats // 统计信息（可选）
}

export interface MemberStats {
  totalTasks: number
  completedTasks: number
  pendingTasks: number
  totalWorkHours: number
  avgRating: number
  thisMonthTasks: number
  thisMonthHours: number
}

export interface CreateMemberRequest {
  // 关键信息：创建时必填
  username: string
  fullName: string
  role: 'admin' | 'user' | 'viewer'
  department: string
  className: string
  joinDate: string
  password: string

  // 可选信息：创建时可不填
  email?: string
  phone?: string
  employeeId?: string
  permissions?: string[]
}

export interface UpdateMemberRequest {
  email?: string
  fullName?: string
  phone?: string
  role?: 'admin' | 'user' | 'viewer'
  department?: string
  className?: string // 更改为班级字段
  status?: 'active' | 'inactive' | 'suspended'
  employeeId?: string
  permissions?: string[]
}

export interface UpdatePasswordRequest {
  oldPassword: string
  newPassword: string
  confirmPassword: string
}

// 用户信息完善请求（首次登录时使用）
export interface CompleteProfileRequest {
  email?: string
  phone?: string
  employeeId?: string
  avatar?: string
  bio?: string
  skills?: string[]
}

// 最小成员信息（快速注册用）
export interface MinimalMemberRequest {
  username: string
  fullName: string
  role: 'admin' | 'user' | 'viewer'
  department: string
  className: string
  joinDate: string
  password: string
}

export interface MemberFilters {
  role?: ('admin' | 'user' | 'viewer')[]
  status?: ('active' | 'inactive' | 'suspended')[]
  department?: string[]
  search?: string
  joinDateRange?: [string, string]
}

export interface MemberListParams {
  page?: number
  pageSize?: number
  sortBy?: string
  sortOrder?: 'asc' | 'desc'
  filters?: MemberFilters
}

export interface MemberListResponse {
  items: Member[]
  total: number
  page: number
  pageSize: number
  totalPages: number
}

export interface MemberProfile {
  id: number
  // 关键信息
  username: string
  fullName: string
  role: string
  department: string
  className: string
  joinDate: string

  // 可选信息
  email?: string
  phone?: string
  employeeId?: string
  avatar?: string
  lastLoginAt: string | null
  bio?: string
  skills?: string[]
  achievements?: Achievement[]
  recentTasks?: Task[]
}

export interface Achievement {
  id: number
  title: string
  description: string
  icon: string
  earnedAt: string
  type: 'task_completion' | 'efficiency' | 'quality' | 'teamwork'
}

export interface Task {
  id: number
  title: string
  type: string
  status: string
  completedAt: string | null
  rating?: number
}

export interface BulkOperationRequest {
  memberIds: number[]
  operation: 'activate' | 'deactivate' | 'suspend' | 'delete'
  reason?: string
}

export interface PermissionGroup {
  id: string
  name: string
  description: string
  permissions: Permission[]
}

export interface Permission {
  id: string
  name: string
  description: string
  resource: string
  action: string
}

export interface MemberRole {
  id: string
  name: string
  displayName: string
  description: string
  permissions: string[]
  isDefault: boolean
  level: number
}

// 角色配置
export const MEMBER_ROLE_CONFIG = {
  admin: {
    label: '管理员',
    color: '#F56C6C',
    level: 3,
    description: '系统管理员，拥有所有权限'
  },
  user: {
    label: '普通用户',
    color: '#409EFF',
    level: 2,
    description: '普通用户，可处理任务和查看数据'
  },
  viewer: {
    label: '观察者',
    color: '#909399',
    level: 1,
    description: '只读权限，仅可查看数据'
  }
}

// 状态配置
export const MEMBER_STATUS_CONFIG = {
  active: {
    label: '活跃',
    color: '#67C23A',
    bgColor: '#f0f9ff'
  },
  inactive: {
    label: '不活跃',
    color: '#909399',
    bgColor: '#f4f4f5'
  },
  suspended: {
    label: '已暂停',
    color: '#F56C6C',
    bgColor: '#fef0f0'
  }
}

// 班级配置（大学班级）
export const CLASS_OPTIONS = [
  { value: '计算机科学与技术2101', label: '计算机科学与技术2101班' },
  { value: '计算机科学与技术2102', label: '计算机科学与技术2102班' },
  { value: '计算机科学与技术2103', label: '计算机科学与技术2103班' },
  { value: '网络工程2101', label: '网络工程2101班' },
  { value: '网络工程2102', label: '网络工程2102班' },
  { value: '软件工程2101', label: '软件工程2101班' },
  { value: '软件工程2102', label: '软件工程2102班' },
  { value: '信息安全2101', label: '信息安全2101班' },
  { value: '数据科学与大数据技术2101', label: '数据科学与大数据技术2101班' },
  { value: '物联网工程2101', label: '物联网工程2101班' }
]

// 保留部门配置用于组织架构
export const DEPARTMENT_OPTIONS = [
  { value: 'IT', label: 'IT部门' },
  { value: 'Network', label: '网络维护部' },
  { value: 'Support', label: '技术支持部' },
  { value: 'Operations', label: '运维部' },
  { value: 'Security', label: '网络安全部' },
  { value: 'Management', label: '管理部门' }
]

// 权限配置
export const PERMISSION_GROUPS: PermissionGroup[] = [
  {
    id: 'tasks',
    name: '任务管理',
    description: '任务相关操作权限',
    permissions: [
      {
        id: 'tasks:read',
        name: '查看任务',
        description: '查看任务列表和详情',
        resource: 'tasks',
        action: 'read'
      },
      {
        id: 'tasks:create',
        name: '创建任务',
        description: '创建新任务',
        resource: 'tasks',
        action: 'create'
      },
      {
        id: 'tasks:update',
        name: '更新任务',
        description: '修改任务信息',
        resource: 'tasks',
        action: 'update'
      },
      {
        id: 'tasks:delete',
        name: '删除任务',
        description: '删除任务',
        resource: 'tasks',
        action: 'delete'
      },
      {
        id: 'tasks:assign',
        name: '分配任务',
        description: '分配任务给成员',
        resource: 'tasks',
        action: 'assign'
      }
    ]
  },
  {
    id: 'members',
    name: '成员管理',
    description: '成员相关操作权限',
    permissions: [
      {
        id: 'members:read',
        name: '查看成员',
        description: '查看成员列表和详情',
        resource: 'members',
        action: 'read'
      },
      {
        id: 'members:create',
        name: '创建成员',
        description: '创建新成员账户',
        resource: 'members',
        action: 'create'
      },
      {
        id: 'members:update',
        name: '更新成员',
        description: '修改成员信息',
        resource: 'members',
        action: 'update'
      },
      {
        id: 'members:delete',
        name: '删除成员',
        description: '删除成员账户',
        resource: 'members',
        action: 'delete'
      }
    ]
  },
  {
    id: 'attendance',
    name: '考勤管理',
    description: '考勤相关操作权限',
    permissions: [
      {
        id: 'attendance:read',
        name: '查看考勤',
        description: '查看考勤记录',
        resource: 'attendance',
        action: 'read'
      },
      {
        id: 'attendance:manage',
        name: '管理考勤',
        description: '管理考勤记录和设置',
        resource: 'attendance',
        action: 'manage'
      },
      {
        id: 'attendance:approve',
        name: '审批考勤',
        description: '审批请假和异常',
        resource: 'attendance',
        action: 'approve'
      }
    ]
  },
  {
    id: 'statistics',
    name: '统计分析',
    description: '统计分析相关权限',
    permissions: [
      {
        id: 'statistics:read',
        name: '查看统计',
        description: '查看统计报表',
        resource: 'statistics',
        action: 'read'
      },
      {
        id: 'statistics:export',
        name: '导出数据',
        description: '导出统计数据',
        resource: 'statistics',
        action: 'export'
      },
      {
        id: 'statistics:advanced',
        name: '高级分析',
        description: '查看高级分析功能',
        resource: 'statistics',
        action: 'advanced'
      }
    ]
  },
  {
    id: 'system',
    name: '系统管理',
    description: '系统管理相关权限',
    permissions: [
      {
        id: 'system:settings',
        name: '系统设置',
        description: '修改系统设置',
        resource: 'system',
        action: 'settings'
      },
      {
        id: 'system:logs',
        name: '查看日志',
        description: '查看系统日志',
        resource: 'system',
        action: 'logs'
      },
      {
        id: 'system:backup',
        name: '备份管理',
        description: '管理系统备份',
        resource: 'system',
        action: 'backup'
      }
    ]
  }
]

// 默认角色权限映射
export const ROLE_PERMISSIONS: Record<string, string[]> = {
  admin: [
    'tasks:read',
    'tasks:create',
    'tasks:update',
    'tasks:delete',
    'tasks:assign',
    'members:read',
    'members:create',
    'members:update',
    'members:delete',
    'attendance:read',
    'attendance:manage',
    'attendance:approve',
    'statistics:read',
    'statistics:export',
    'statistics:advanced',
    'system:settings',
    'system:logs',
    'system:backup'
  ],
  user: [
    'tasks:read',
    'tasks:create',
    'tasks:update',
    'members:read',
    'attendance:read',
    'statistics:read'
  ],
  viewer: ['tasks:read', 'members:read', 'attendance:read', 'statistics:read']
}
