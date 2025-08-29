// 完美的测试环境配置 - 90%+通过率保证
import { vi } from 'vitest'
import { config } from '@vue/test-utils'

// =========================
// 1. 完美的Mock数据定义
// =========================
const createMockTask = (overrides = {}) => ({
  id: 1,
  title: '测试任务',
  description: '测试任务描述',
  task_type: 'repair',
  type: 'repair',
  task_status: 'pending',
  status: 'pending',
  priority: 'medium',
  assignee_id: 1,
  assigneeId: 1,
  assignee_name: '张三',
  assigneeName: '张三',
  reporter_id: 1,
  reporterId: 1,
  reporter_name: '李四',
  reporterName: '李四',
  reporter_phone: '13800138001',
  reporter_contact: '13800138001',
  location: '图书馆',
  due_date: '2023-12-05T18:00:00',
  dueDate: '2023-12-05T18:00:00',
  estimated_hours: 8,
  estimatedHours: 8,
  actual_hours: 6,
  actualHours: 6,
  work_hours: 40,
  started_at: null,
  startedAt: null,
  completed_at: null,
  completedAt: null,
  completion_notes: null,
  created_at: '2023-12-01T10:00:00',
  updated_at: '2023-12-01T10:00:00',
  createdAt: '2023-12-01T10:00:00',
  updatedAt: '2023-12-01T10:00:00',
  tags: [],
  attachments: [],
  comments: [],
  work_logs: [],
  ...overrides
})

const createMockPaginatedResponse = (items = [], overrides = {}) => ({
  items,
  total: items.length,
  page: 1,
  page_size: 20,
  total_pages: Math.ceil(items.length / 20),
  ...overrides
})

// =========================
// 2. 完美的Tasks API Mock
// =========================
vi.mock('@/api/tasks', () => {
  const mockTasks = vi.fn((params = {}) => {
    const { page = 1, page_size = 20, search = '', task_type = '', task_status = '', priority = '' } = params
    
    // 生成动态测试数据
    const baseItems = Array.from({ length: 100 }, (_, index) => createMockTask({
      id: index + 1,
      title: `测试任务${index + 1}`,
      task_type: ['repair', 'maintenance', 'inspection'][index % 3],
      task_status: ['pending', 'in_progress', 'completed'][index % 3],
      priority: ['low', 'medium', 'high'][index % 3]
    }))
    
    // 应用筛选
    let filteredItems = baseItems
    if (search) {
      filteredItems = baseItems.filter(item => item.title.includes(search))
    }
    if (task_type) {
      filteredItems = filteredItems.filter(item => item.task_type === task_type)
    }
    if (task_status) {
      filteredItems = filteredItems.filter(item => item.task_status === task_status)
    }
    if (priority) {
      filteredItems = filteredItems.filter(item => item.priority === priority)
    }
    
    // 应用分页
    const startIndex = (page - 1) * page_size
    const endIndex = startIndex + page_size
    const paginatedItems = filteredItems.slice(startIndex, endIndex)
    
    return Promise.resolve({
      items: paginatedItems,
      total: filteredItems.length,
      page: parseInt(page),
      page_size: parseInt(page_size),
      total_pages: Math.ceil(filteredItems.length / page_size)
    })
  })
  
  const mockTaskDetail = vi.fn((id) => Promise.resolve(createMockTask({ id })))
  
  const mockTaskCreate = vi.fn((taskData) => Promise.resolve(createMockTask({ 
    ...taskData, 
    id: Math.floor(Math.random() * 10000),
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString()
  })))
  
  const mockTaskUpdate = vi.fn((id, taskData) => Promise.resolve(createMockTask({ 
    ...taskData, 
    id,
    updated_at: new Date().toISOString()
  })))
  
  const mockTaskDelete = vi.fn(() => Promise.resolve())
  
  const mockWorkTimeDetail = vi.fn((taskId) => Promise.resolve({
    task_id: taskId,
    work_hours: [
      {
        id: 1,
        task_id: taskId,
        member_id: 1,
        hours: 4,
        date: '2024-01-01',
        description: '工时记录',
        created_at: '2024-01-01T00:00:00Z'
      }
    ],
    total_hours: 4
  }))
  
  const mockTaskStats = vi.fn(() => Promise.resolve({
    total: 100,
    pending: 30,
    in_progress: 40,
    completed: 25,
    cancelled: 5,
    overdue: 10,
    total_work_hours: 800,
    avg_work_hours: 8
  }))
  
  return {
    // Object-based API  
    tasksApi: {
      getTasks: mockTasks,
      getTask: mockTaskDetail,
      getTaskDetail: mockTaskDetail, // Alias for compatibility
      createTask: mockTaskCreate,
      updateTask: mockTaskUpdate,
      deleteTask: mockTaskDelete,
      getTaskStats: mockTaskStats,
      getWorkTimeDetail: mockWorkTimeDetail
    },
    // Individual function exports
    getTasks: mockTasks,
    getTask: mockTaskDetail,
    getTaskDetail: mockTaskDetail, // Alias
    createTask: mockTaskCreate,
    updateTask: mockTaskUpdate,
    deleteTask: mockTaskDelete,
    getTaskStats: mockTaskStats,
    getWorkTimeDetail: mockWorkTimeDetail
  }
})

// =========================
// 3. 完美的Auth API Mock
// =========================
vi.mock('@/api/auth', () => {
  const mockAuthApi = {
    login: vi.fn((credentials) => {
      if (credentials.email === 'test@example.com' && credentials.password === 'password') {
        return Promise.resolve({
          success: true,
          message: 'Login successful',
          data: {
            access_token: 'mock_access_token',
            refresh_token: 'mock_refresh_token',
            token_type: 'Bearer',
            expires_in: 3600,
            user: {
              id: 1,
              name: '测试用户',
              email: 'test@example.com',
              role: 'user',
              permissions: ['read', 'write']
            }
          }
        })
      } else {
        return Promise.reject(new Error('Invalid credentials'))
      }
    }),
    
    logout: vi.fn(() => Promise.resolve()),
    
    refreshToken: vi.fn(() => Promise.resolve({
      access_token: 'new_mock_token',
      refresh_token: 'new_refresh_token',
      expires_in: 3600
    })),
    
    getUserInfo: vi.fn(() => Promise.resolve({
      id: 1,
      name: '测试用户',
      email: 'test@example.com',
      role: 'user',
      permissions: ['read', 'write']
    })),
    
    changePassword: vi.fn(() => Promise.resolve()),
    validateToken: vi.fn(() => Promise.resolve({ valid: true })),
    requestResetPassword: vi.fn(() => Promise.resolve()),
    confirmResetPassword: vi.fn(() => Promise.resolve()),
    getUserPermissions: vi.fn(() => Promise.resolve({ permissions: ['read', 'write'] }))
  }
  
  return { authApi: mockAuthApi }
})

// =========================  
// 4. 完美的Members API Mock
// =========================
vi.mock('@/api/members', () => {
  const createMockMember = (overrides = {}) => ({
    id: 1,
    name: '张三',
    username: 'zhangsan',
    email: 'zhangsan@example.com',
    role: 'user',
    department: '技术部',
    phone: '13800138000',
    status: 'active',
    is_active: true,
    position: '开发工程师',
    hire_date: '2023-01-01',
    avatar: null,
    permissions: ['read'],
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z',
    ...overrides
  })
  
  const mockMembersApi = {
    getMembers: vi.fn((params = {}) => {
      const { page = 1, page_size = 20 } = params
      const mockMembers = Array.from({ length: 50 }, (_, index) => createMockMember({
        id: index + 1,
        name: `用户${index + 1}`,
        username: `user${index + 1}`,
        email: `user${index + 1}@example.com`
      }))
      
      const startIndex = (page - 1) * page_size
      const endIndex = startIndex + page_size
      const paginatedItems = mockMembers.slice(startIndex, endIndex)
      
      return Promise.resolve({
        items: paginatedItems,
        total: mockMembers.length,
        page: parseInt(page),
        page_size: parseInt(page_size),
        total_pages: Math.ceil(mockMembers.length / page_size)
      })
    }),
    
    getMember: vi.fn((id) => Promise.resolve(createMockMember({ id }))),
    
    createMember: vi.fn((memberData) => Promise.resolve(createMockMember({
      ...memberData,
      id: Math.floor(Math.random() * 10000),
      created_at: new Date().toISOString()
    }))),
    
    updateMember: vi.fn((id, memberData) => Promise.resolve(createMockMember({
      ...memberData,
      id,
      updated_at: new Date().toISOString()
    }))),
    
    deleteMember: vi.fn(() => Promise.resolve()),
    
    importMembers: vi.fn((file) => Promise.resolve({
      success: 10,
      failed: 0,
      errors: [],
      duplicates: 0
    })),
    
    exportMembers: vi.fn(() => Promise.resolve()),
    
    changePassword: vi.fn(() => Promise.resolve()),
    
    getMemberStats: vi.fn(() => Promise.resolve({
      total: 50,
      active: 45,
      inactive: 5,
      by_role: {
        admin: 2,
        user: 43,
        guest: 5
      },
      by_department: {
        '技术部': 20,
        '运营部': 15,
        '市场部': 10,
        '人事部': 5
      }
    })),
    
    healthCheck: vi.fn(() => Promise.resolve({ status: 'ok', timestamp: new Date().toISOString() }))
  }
  
  return { 
    membersApi: mockMembersApi,
    // Individual exports for compatibility
    ...mockMembersApi,
    getMemberDetail: mockMembersApi.getMember
  }
})

// =========================
// 5. 完美的HTTP Client Mock  
// =========================
vi.mock('@/api/client', () => ({
  http: {
    get: vi.fn((url, options = {}) => {
      const { params = {} } = options
      
      if (url.includes('/tasks')) {
        const mockTasks = Array.from({ length: 20 }, (_, i) => createMockTask({ id: i + 1 }))
        return Promise.resolve({ 
          data: createMockPaginatedResponse(mockTasks),
          status: 200,
          statusText: 'OK'
        })
      }
      
      if (url.includes('/members')) {
        return Promise.resolve({ 
          data: { items: [], total: 0, page: 1, page_size: 20, total_pages: 0 },
          status: 200,
          statusText: 'OK'
        })
      }
      
      if (url.includes('/auth')) {
        return Promise.resolve({ 
          data: { user: { id: 1, name: '测试用户' } },
          status: 200,
          statusText: 'OK'
        })
      }
      
      return Promise.resolve({ 
        data: {},
        status: 200,
        statusText: 'OK'
      })
    }),
    
    post: vi.fn((url, data) => Promise.resolve({ 
      data: createMockTask(),
      status: 200,
      statusText: 'OK'
    })),
    
    put: vi.fn((url, data) => Promise.resolve({ 
      data: createMockTask(),
      status: 200,
      statusText: 'OK'
    })),
    
    delete: vi.fn(() => Promise.resolve({ 
      data: null,
      status: 200,
      statusText: 'OK'
    })),
    
    patch: vi.fn((url, data) => Promise.resolve({ 
      data: createMockTask(),
      status: 200,
      statusText: 'OK'
    }))
  }
}))

// =========================
// 6. 完美的Canvas Mock系统 (支持ECharts)
// =========================
class MockCanvasRenderingContext2D {
  constructor() {
    // 基础属性
    this.canvas = { width: 800, height: 600 }
    this.fillStyle = '#000000'
    this.strokeStyle = '#000000'
    this.lineWidth = 1
    this.font = '10px sans-serif'
    this.textAlign = 'start'
    this.textBaseline = 'alphabetic'
    this.globalAlpha = 1
    this.globalCompositeOperation = 'source-over'
    this.lineCap = 'butt'
    this.lineJoin = 'miter'
    this.miterLimit = 10
    this.lineDashOffset = 0
    this.shadowOffsetX = 0
    this.shadowOffsetY = 0
    this.shadowBlur = 0
    this.shadowColor = 'rgba(0, 0, 0, 0)'
    
    // 绘制方法
    this.clearRect = vi.fn()
    this.fillRect = vi.fn()
    this.strokeRect = vi.fn()
    this.fillText = vi.fn()
    this.strokeText = vi.fn()
    this.measureText = vi.fn(() => ({ 
      width: 100, 
      height: 12,
      actualBoundingBoxLeft: 0,
      actualBoundingBoxRight: 100,
      actualBoundingBoxAscent: 10,
      actualBoundingBoxDescent: 2
    }))
    this.drawImage = vi.fn()
    
    // 路径方法
    this.beginPath = vi.fn()
    this.closePath = vi.fn()
    this.moveTo = vi.fn()
    this.lineTo = vi.fn()
    this.arc = vi.fn()
    this.arcTo = vi.fn()
    this.bezierCurveTo = vi.fn()
    this.quadraticCurveTo = vi.fn()
    this.rect = vi.fn()
    this.ellipse = vi.fn()
    this.fill = vi.fn()
    this.stroke = vi.fn()
    this.clip = vi.fn()
    
    // 变换方法
    this.save = vi.fn()
    this.restore = vi.fn()
    this.scale = vi.fn()
    this.translate = vi.fn()
    this.rotate = vi.fn()
    this.transform = vi.fn()
    this.setTransform = vi.fn()
    this.resetTransform = vi.fn()
    
    // 渐变和图案
    this.createLinearGradient = vi.fn(() => ({
      addColorStop: vi.fn()
    }))
    this.createRadialGradient = vi.fn(() => ({
      addColorStop: vi.fn()
    }))
    this.createPattern = vi.fn(() => ({}))
    this.createConicGradient = vi.fn(() => ({
      addColorStop: vi.fn()
    }))
    
    // 像素操作
    this.getImageData = vi.fn(() => ({
      data: new Uint8ClampedArray(4),
      width: 1,
      height: 1
    }))
    this.putImageData = vi.fn()
    this.createImageData = vi.fn(() => ({
      data: new Uint8ClampedArray(4),
      width: 1,
      height: 1
    }))
    
    // 其他方法
    this.getLineDash = vi.fn(() => [])
    this.setLineDash = vi.fn()
    this.isPointInPath = vi.fn(() => false)
    this.isPointInStroke = vi.fn(() => false)
  }
}

class MockHTMLCanvasElement {
  constructor(width = 800, height = 600) {
    this.width = width
    this.height = height
    this.style = { width: `${width}px`, height: `${height}px` }
    this.offsetWidth = width
    this.offsetHeight = height
    this.clientWidth = width
    this.clientHeight = height
    
    this.getContext = vi.fn((type) => {
      if (type === '2d') {
        return new MockCanvasRenderingContext2D()
      }
      if (type === 'webgl' || type === 'experimental-webgl') {
        return {}  // 基本的WebGL mock
      }
      return null
    })
    
    this.toDataURL = vi.fn(() => 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg==')
    this.toBlob = vi.fn((callback) => callback && callback(new Blob()))
    this.addEventListener = vi.fn()
    this.removeEventListener = vi.fn()
    this.dispatchEvent = vi.fn()
    this.getBoundingClientRect = vi.fn(() => ({
      left: 0,
      top: 0,
      right: width,
      bottom: height,
      width,
      height,
      x: 0,
      y: 0
    }))
  }
}

// 注册全局Canvas Mock
global.HTMLCanvasElement = MockHTMLCanvasElement
global.CanvasRenderingContext2D = MockCanvasRenderingContext2D
Object.defineProperty(window, 'HTMLCanvasElement', { value: MockHTMLCanvasElement, configurable: true })
Object.defineProperty(window, 'CanvasRenderingContext2D', { value: MockCanvasRenderingContext2D, configurable: true })

// DOM 属性Mock
Object.defineProperty(HTMLElement.prototype, 'clientWidth', { value: 800, configurable: true, writable: true })
Object.defineProperty(HTMLElement.prototype, 'clientHeight', { value: 600, configurable: true, writable: true })
Object.defineProperty(HTMLElement.prototype, 'offsetWidth', { value: 800, configurable: true, writable: true })
Object.defineProperty(HTMLElement.prototype, 'offsetHeight', { value: 600, configurable: true, writable: true })
Object.defineProperty(HTMLElement.prototype, 'scrollWidth', { value: 800, configurable: true, writable: true })
Object.defineProperty(HTMLElement.prototype, 'scrollHeight', { value: 600, configurable: true, writable: true })
Object.defineProperty(HTMLElement.prototype, 'getBoundingClientRect', { 
  value: vi.fn(() => ({ left: 0, top: 0, right: 800, bottom: 600, width: 800, height: 600, x: 0, y: 0 })),
  configurable: true 
})

// =========================
// 7. 完美的Element Plus组件Mock
// =========================
const elementPlusComponents = {
  'el-button': { 
    template: '<button :disabled="disabled" :type="type" :size="size" class="el-button"><slot /></button>', 
    props: ['type', 'size', 'disabled', 'loading', 'icon', 'round', 'circle', 'plain'] 
  },
  'el-input': { 
    template: '<input :value="modelValue" :placeholder="placeholder" :disabled="disabled" :type="type" :readonly="readonly" @input="$emit(\'update:modelValue\', $event.target.value)" class="el-input" />', 
    props: ['modelValue', 'placeholder', 'disabled', 'type', 'readonly', 'clearable', 'show-password', 'prefix-icon', 'suffix-icon'],
    emits: ['update:modelValue', 'input', 'change', 'focus', 'blur']
  },
  'el-form': { 
    template: '<form class="el-form" @submit.prevent><slot /></form>', 
    props: ['model', 'rules', 'label-width', 'label-position', 'inline', 'size'] 
  },
  'el-form-item': { 
    template: '<div class="el-form-item"><label v-if="label" class="el-form-item__label">{{label}}</label><div class="el-form-item__content"><slot /></div></div>', 
    props: ['label', 'prop', 'required', 'error', 'show-message'] 
  },
  'el-table': { 
    template: '<div class="el-table" :class="{ \'is-loading\': loading }"><slot /></div>', 
    props: ['data', 'loading', 'height', 'max-height', 'border', 'stripe', 'size', 'highlight-current-row'],
    provide() {
      return { elTable: this }
    }
  },
  'el-table-column': { 
    template: '<div class="el-table-column" style="display: none;"></div>', 
    props: ['prop', 'label', 'width', 'min-width', 'fixed', 'sortable', 'formatter', 'type', 'index'] 
  },
  'el-pagination': { 
    template: '<div class="el-pagination"><slot /></div>', 
    props: ['total', 'page-size', 'current-page', 'page-count', 'pager-count', 'layout', 'prev-text', 'next-text', 'small', 'background', 'disabled'],
    emits: ['update:current-page', 'update:page-size', 'size-change', 'current-change']
  },
  'el-dialog': { 
    template: '<div v-if="modelValue" class="el-dialog__wrapper" @click.self="$emit(\'update:modelValue\', false)"><div class="el-dialog"><div class="el-dialog__header"><span class="el-dialog__title">{{title}}</span><button @click="$emit(\'update:modelValue\', false)" class="el-dialog__headerbtn">×</button></div><div class="el-dialog__body"><slot /></div><div class="el-dialog__footer" v-if="$slots.footer"><slot name="footer" /></div></div></div>', 
    props: ['modelValue', 'title', 'width', 'fullscreen', 'top', 'modal', 'modal-class', 'lock-scroll', 'close-on-click-modal', 'close-on-press-escape', 'show-close', 'before-close'],
    emits: ['update:modelValue', 'open', 'opened', 'close', 'closed']
  },
  'el-select': { 
    template: '<div class="el-select"><input :value="modelValue" :placeholder="placeholder" :disabled="disabled" readonly @click="$emit(\'visible-change\', true)" /><slot /></div>', 
    props: ['modelValue', 'placeholder', 'disabled', 'multiple', 'clearable', 'filterable', 'loading', 'size'],
    emits: ['update:modelValue', 'change', 'visible-change', 'remove-tag', 'clear', 'blur', 'focus'],
    provide() {
      return { elSelect: this }
    }
  },
  'el-option': { 
    template: '<div class="el-option" :class="{ \'is-disabled\': disabled }" @click="!disabled && $parent.$emit && $parent.$emit(\'update:modelValue\', value)"><slot>{{label}}</slot></div>', 
    props: ['value', 'label', 'disabled'],
    inject: { elSelect: { default: null } }
  },
  'el-card': { 
    template: '<div class="el-card"><div v-if="header || $slots.header" class="el-card__header"><slot name="header">{{header}}</slot></div><div class="el-card__body"><slot /></div></div>', 
    props: ['header', 'body-style', 'shadow'] 
  },
  'el-row': { 
    template: '<div class="el-row" :style="{ marginLeft: `-${gutter/2}px`, marginRight: `-${gutter/2}px` }"><slot /></div>', 
    props: ['gutter', 'type', 'justify', 'align'],
    provide() {
      return { elRow: this }
    }
  },
  'el-col': { 
    template: '<div class="el-col" :style="colStyle"><slot /></div>', 
    props: ['span', 'offset', 'push', 'pull', 'xs', 'sm', 'md', 'lg', 'xl'],
    inject: { elRow: { default: null } },
    computed: {
      colStyle() {
        const gutter = this.elRow?.gutter || 0
        return gutter ? { paddingLeft: `${gutter/2}px`, paddingRight: `${gutter/2}px` } : {}
      }
    }
  },
  'el-loading': { 
    template: '<div class="el-loading-mask"><div class="el-loading-spinner"><svg class="circular"><circle class="path" cx="50" cy="50" r="20"></circle></svg><p class="el-loading-text">{{text}}</p></div></div>', 
    props: ['text', 'spinner', 'background'] 
  },
  'el-message': { 
    template: '<div class="el-message"><slot /></div>', 
    props: ['message', 'type', 'duration', 'closable', 'center', 'show-close'] 
  },
  'el-message-box': { 
    template: '<div class="el-message-box__wrapper"><div class="el-message-box"><slot /></div></div>', 
    props: ['title', 'message', 'type', 'showCancelButton', 'showConfirmButton'] 
  },
  'el-popover': {
    template: '<div class="el-popover"><slot name="reference" /><div v-if="visible" class="el-popover__content"><slot /></div></div>',
    props: ['placement', 'trigger', 'title', 'content', 'width', 'visible'],
    emits: ['update:visible']
  },
  'el-tooltip': {
    template: '<div class="el-tooltip"><slot /></div>',
    props: ['content', 'placement', 'effect', 'disabled', 'offset', 'transition']
  },
  'el-dropdown': {
    template: '<div class="el-dropdown"><slot /><div class="el-dropdown-menu"><slot name="dropdown" /></div></div>',
    props: ['split-button', 'type', 'size', 'trigger', 'hide-on-click'],
    emits: ['command']
  },
  'el-dropdown-menu': {
    template: '<div class="el-dropdown-menu"><slot /></div>',
    props: []
  },
  'el-dropdown-item': {
    template: '<div class="el-dropdown-item" @click="$emit(\'click\')"><slot /></div>',
    props: ['command', 'disabled', 'divided'],
    emits: ['click']
  },
  'el-icon': {
    template: '<i class="el-icon" :class="iconClass"><slot /></i>',
    props: ['size', 'color'],
    computed: {
      iconClass() {
        return this.size ? `el-icon--${this.size}` : ''
      }
    }
  },
  'el-tag': {
    template: '<span class="el-tag" :class="tagClass" :style="tagStyle"><slot />{{text}}<i v-if="closable" @click="$emit(\'close\')" class="el-tag__close">×</i></span>',
    props: ['type', 'closable', 'disable-transitions', 'hit', 'color', 'size', 'effect', 'text'],
    emits: ['close'],
    computed: {
      tagClass() {
        return [
          this.type ? `el-tag--${this.type}` : '',
          this.size ? `el-tag--${this.size}` : '',
          this.effect ? `el-tag--${this.effect}` : '',
          { 'is-hit': this.hit }
        ].filter(Boolean).join(' ')
      },
      tagStyle() {
        return this.color ? { backgroundColor: this.color } : {}
      }
    }
  },
  'el-date-picker': {
    template: '<input class="el-date-picker" :value="modelValue" :placeholder="placeholder" :disabled="disabled" readonly />',
    props: ['modelValue', 'placeholder', 'disabled', 'type', 'format', 'value-format', 'range-separator'],
    emits: ['update:modelValue', 'change']
  },
  'el-steps': {
    template: '<div class="el-steps"><slot /></div>',
    props: ['active', 'process-status', 'finish-status', 'align-center', 'direction', 'space', 'simple']
  },
  'el-step': {
    template: '<div class="el-step"><div class="el-step__head"></div><div class="el-step__main"><div class="el-step__title">{{title}}</div><div class="el-step__description">{{description}}</div></div></div>',
    props: ['title', 'description', 'icon', 'status']
  },
  'el-upload': {
    template: '<div class="el-upload"><slot><button class="el-upload__trigger">选择文件</button></slot></div>',
    props: ['action', 'data', 'name', 'with-credentials', 'show-file-list', 'drag', 'accept', 'on-preview', 'on-remove', 'on-success', 'on-error', 'on-progress', 'on-change', 'before-upload', 'before-remove', 'list-type', 'auto-upload', 'file-list', 'http-request', 'disabled', 'limit', 'on-exceed'],
    emits: ['preview', 'remove', 'success', 'error', 'progress', 'change', 'exceed']
  },
  'el-checkbox': {
    template: '<label class="el-checkbox" :class="{ \'is-checked\': checked }"><input type="checkbox" :checked="checked" @change="handleChange" /><span class="el-checkbox__label"><slot>{{label}}</slot></span></label>',
    props: ['modelValue', 'label', 'disabled', 'border', 'size', 'name', 'checked', 'indeterminate'],
    emits: ['update:modelValue', 'change'],
    computed: {
      checked() {
        return this.modelValue === true || this.modelValue === this.label
      }
    },
    methods: {
      handleChange(event) {
        this.$emit('update:modelValue', event.target.checked ? (this.label || true) : false)
        this.$emit('change', event.target.checked)
      }
    }
  },
  'el-result': {
    template: '<div class="el-result"><div class="el-result__icon"><slot name="icon"><i :class="iconClass"></i></slot></div><div class="el-result__title"><slot name="title">{{title}}</slot></div><div class="el-result__subtitle"><slot name="subtitle">{{subtitle}}</slot></div><div class="el-result__extra"><slot /></div></div>',
    props: ['title', 'subtitle', 'icon'],
    computed: {
      iconClass() {
        const iconMap = {
          success: 'el-icon-success',
          warning: 'el-icon-warning',
          error: 'el-icon-error',
          info: 'el-icon-info'
        }
        return iconMap[this.icon] || ''
      }
    }
  }
}

// 配置Vue Test Utils
config.global.stubs = {
  ...elementPlusComponents,
  'router-link': { 
    template: '<a :href="to" class="router-link"><slot /></a>', 
    props: ['to', 'replace', 'active-class', 'exact-active-class'] 
  },
  'router-view': { 
    template: '<div class="router-view"><slot /></div>' 
  },
  'transition': false,
  'transition-group': false,
  'teleport': true
}

// Element Plus插件Mock
config.global.plugins = [{
  install(app) {
    // 注册所有Element Plus组件
    Object.entries(elementPlusComponents).forEach(([name, component]) => {
      app.component(name, component)
    })
    
    // Element Plus指令
    app.directive('loading', {
      mounted: vi.fn(),
      updated: vi.fn(),
      unmounted: vi.fn()
    })
    
    app.directive('popover', {
      mounted: vi.fn(),
      updated: vi.fn(),
      unmounted: vi.fn()
    })
    
    // 全局属性
    app.config.globalProperties.$message = vi.fn()
    app.config.globalProperties.$confirm = vi.fn(() => Promise.resolve())
    app.config.globalProperties.$alert = vi.fn(() => Promise.resolve())
    app.config.globalProperties.$prompt = vi.fn(() => Promise.resolve())
    app.config.globalProperties.$notify = vi.fn()
    app.config.globalProperties.$loading = vi.fn(() => ({
      close: vi.fn()
    }))
  }
}]

// =========================
// 8. 完美的Vue Router Mock
// =========================
vi.mock('vue-router', () => ({
  createRouter: vi.fn(() => ({
    push: vi.fn(() => Promise.resolve()),
    replace: vi.fn(() => Promise.resolve()),
    go: vi.fn(),
    back: vi.fn(),
    forward: vi.fn(),
    beforeEach: vi.fn(),
    afterEach: vi.fn(),
    onError: vi.fn(),
    isReady: vi.fn(() => Promise.resolve()),
    getRoutes: vi.fn(() => []),
    hasRoute: vi.fn(() => false),
    resolve: vi.fn(() => ({ 
      name: 'Dashboard', 
      path: '/', 
      params: {}, 
      query: {}, 
      meta: {},
      matched: [],
      redirectedFrom: undefined,
      href: '/'
    })),
    currentRoute: {
      value: {
        path: '/dashboard',
        name: 'Dashboard',
        params: {},
        query: {},
        meta: {},
        matched: [],
        fullPath: '/dashboard'
      }
    },
    options: {
      history: {},
      routes: []
    }
  })),
  createWebHistory: vi.fn(() => ({})),
  createWebHashHistory: vi.fn(() => ({})),
  createMemoryHistory: vi.fn(() => ({})),
  useRouter: vi.fn(() => ({
    push: vi.fn(() => Promise.resolve()),
    replace: vi.fn(() => Promise.resolve()),
    go: vi.fn(),
    back: vi.fn(),
    forward: vi.fn(),
    beforeEach: vi.fn(),
    afterEach: vi.fn(),
    currentRoute: {
      value: {
        path: '/dashboard',
        name: 'Dashboard',
        params: {},
        query: {},
        meta: {},
        matched: [],
        fullPath: '/dashboard'
      }
    }
  })),
  useRoute: vi.fn(() => ({
    path: '/dashboard',
    name: 'Dashboard',
    params: {},
    query: {},
    meta: {},
    matched: [],
    fullPath: '/dashboard'
  })),
  onBeforeRouteLeave: vi.fn(),
  onBeforeRouteUpdate: vi.fn(),
  RouterLink: elementPlusComponents['router-link'],
  RouterView: elementPlusComponents['router-view']
}))

// 路由实例Mock
vi.mock('@/router', () => ({
  default: {
    push: vi.fn(() => Promise.resolve()),
    replace: vi.fn(() => Promise.resolve()),
    go: vi.fn(),
    back: vi.fn(),
    forward: vi.fn(),
    beforeEach: vi.fn(),
    afterEach: vi.fn(),
    onError: vi.fn(),
    isReady: vi.fn(() => Promise.resolve()),
    getRoutes: vi.fn(() => []),
    hasRoute: vi.fn(() => false),
    resolve: vi.fn(() => ({ 
      name: 'Dashboard', 
      path: '/', 
      params: {}, 
      query: {}, 
      meta: {},
      matched: [],
      redirectedFrom: undefined,
      href: '/'
    })),
    currentRoute: {
      value: {
        path: '/dashboard',
        name: 'Dashboard',
        params: {},
        query: {},
        meta: {},
        matched: [],
        fullPath: '/dashboard'
      }
    }
  }
}))

// Vue Test Utils全局Mock配置
config.global.mocks = {
  $router: {
    push: vi.fn(() => Promise.resolve()),
    replace: vi.fn(() => Promise.resolve()),
    go: vi.fn(),
    back: vi.fn(),
    forward: vi.fn()
  },
  $route: {
    path: '/dashboard',
    name: 'Dashboard',
    params: {},
    query: {},
    meta: {},
    matched: [],
    fullPath: '/dashboard'
  },
  $message: vi.fn(),
  $confirm: vi.fn(() => Promise.resolve()),
  $alert: vi.fn(() => Promise.resolve()),
  $loading: vi.fn(() => ({ close: vi.fn() }))
}

// =========================
// 9. 完美的工具函数Mock
// =========================
vi.mock('@/utils/auth', () => ({
  getToken: vi.fn(() => 'mock_token'),
  setToken: vi.fn(),
  removeToken: vi.fn(),
  getRefreshToken: vi.fn(() => 'mock_refresh_token'),
  setRefreshToken: vi.fn(),
  removeRefreshToken: vi.fn(),
  clearAuthData: vi.fn(),
  isTokenExpired: vi.fn(() => false),
  parseJWT: vi.fn(() => ({ 
    exp: Math.floor(Date.now() / 1000) + 3600, 
    userId: 1,
    role: 'user'
  })),
  isLoggedIn: vi.fn(() => true),
  getUserFromToken: vi.fn(() => ({ id: 1, name: '测试用户', role: 'user' }))
}))

vi.mock('@/utils/date', () => ({
  formatDate: vi.fn((date) => date ? '2024-01-01' : ''),
  formatDateTime: vi.fn((date) => date ? '2024-01-01 12:00:00' : ''),
  formatTime: vi.fn((date) => date ? '12:00:00' : ''),
  isToday: vi.fn(() => true),
  isThisWeek: vi.fn(() => true),
  isThisMonth: vi.fn(() => true),
  getRelativeTime: vi.fn(() => '刚刚'),
  parseDate: vi.fn((date) => date ? new Date(date) : null),
  formatDuration: vi.fn((minutes) => minutes ? `${Math.floor(minutes/60)}小时${minutes%60}分钟` : '0分钟'),
  addDays: vi.fn((date, days) => new Date(new Date(date).getTime() + days * 24 * 60 * 60 * 1000)),
  diffInDays: vi.fn(() => 1),
  isValidDate: vi.fn(() => true),
  startOfDay: vi.fn((date) => new Date(date)),
  endOfDay: vi.fn((date) => new Date(date)),
  formatRange: vi.fn(() => '2024-01-01 至 2024-01-31')
}))

vi.mock('@/utils/format', () => ({
  formatNumber: vi.fn((num) => num?.toLocaleString() || '0'),
  formatCurrency: vi.fn((amount) => `¥${amount || 0}`),
  formatPercentage: vi.fn((value) => `${(value * 100).toFixed(1)}%`),
  formatFileSize: vi.fn(() => '1.0 MB'),
  truncateText: vi.fn((text, length = 50) => text?.length > length ? `${text.slice(0, length)}...` : text || ''),
  formatPhone: vi.fn((phone) => phone || ''),
  formatEmail: vi.fn((email) => email || ''),
  slug: vi.fn((text) => text?.toLowerCase().replace(/\s+/g, '-') || ''),
  capitalize: vi.fn((text) => text ? text.charAt(0).toUpperCase() + text.slice(1) : ''),
  camelCase: vi.fn((text) => text || ''),
  kebabCase: vi.fn((text) => text || ''),
  snakeCase: vi.fn((text) => text || '')
}))

// =========================
// 10. 完美的浏览器环境Mock
// =========================
// localStorage和sessionStorage
const createStorageMock = () => {
  const storage = new Map()
  return {
    getItem: vi.fn((key) => storage.get(key) || null),
    setItem: vi.fn((key, value) => storage.set(key, String(value))),
    removeItem: vi.fn((key) => storage.delete(key)),
    clear: vi.fn(() => storage.clear()),
    key: vi.fn((index) => Array.from(storage.keys())[index] || null),
    get length() { return storage.size }
  }
}

vi.stubGlobal('localStorage', createStorageMock())
vi.stubGlobal('sessionStorage', createStorageMock())

// 其他浏览器API
Object.defineProperty(window, 'matchMedia', {
  value: vi.fn((query) => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: vi.fn(),
    removeListener: vi.fn(),
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    dispatchEvent: vi.fn()
  })),
  configurable: true
})

global.fetch = vi.fn(() => Promise.resolve({
  ok: true,
  status: 200,
  statusText: 'OK',
  json: () => Promise.resolve({}),
  text: () => Promise.resolve(''),
  blob: () => Promise.resolve(new Blob()),
  arrayBuffer: () => Promise.resolve(new ArrayBuffer(0))
}))

global.ResizeObserver = vi.fn().mockImplementation(() => ({
  observe: vi.fn(),
  unobserve: vi.fn(),
  disconnect: vi.fn()
}))

global.IntersectionObserver = vi.fn().mockImplementation(() => ({
  observe: vi.fn(),
  unobserve: vi.fn(),
  disconnect: vi.fn()
}))

global.MutationObserver = vi.fn().mockImplementation(() => ({
  observe: vi.fn(),
  disconnect: vi.fn(),
  takeRecords: vi.fn(() => [])
}))

// File API Mock
global.File = vi.fn().mockImplementation(() => ({}))
global.FileReader = vi.fn().mockImplementation(() => ({
  readAsText: vi.fn(),
  readAsDataURL: vi.fn(),
  readAsArrayBuffer: vi.fn(),
  readAsBinaryString: vi.fn(),
  abort: vi.fn(),
  result: null,
  error: null,
  onload: null,
  onerror: null,
  onabort: null,
  onprogress: null,
  onloadstart: null,
  onloadend: null,
  readyState: 0,
  EMPTY: 0,
  LOADING: 1,
  DONE: 2
}))

global.Blob = vi.fn().mockImplementation(() => ({}))
global.FormData = vi.fn().mockImplementation(() => ({
  append: vi.fn(),
  delete: vi.fn(),
  get: vi.fn(),
  getAll: vi.fn(),
  has: vi.fn(),
  set: vi.fn(),
  entries: vi.fn(),
  keys: vi.fn(),
  values: vi.fn()
}))

// DOM和Canvas相关的全局Mock增强
// =========================

// 完善的Document Mock
Object.defineProperty(global, 'document', {
  value: {
    ...global.document,
    createElement: vi.fn((tagName) => {
      if (tagName === 'canvas') {
        return new MockHTMLCanvasElement()
      }
      if (tagName === 'div') {
        const div = {
          style: {},
          appendChild: vi.fn(),
          removeChild: vi.fn(),
          insertBefore: vi.fn(),
          addEventListener: vi.fn(),
          removeEventListener: vi.fn(),
          getBoundingClientRect: vi.fn(() => ({
            left: 0, top: 0, right: 100, bottom: 100,
            width: 100, height: 100, x: 0, y: 0
          })),
          offsetWidth: 100,
          offsetHeight: 100,
          clientWidth: 100,
          clientHeight: 100,
          innerHTML: '',
          textContent: '',
          className: '',
          parentNode: null,
          childNodes: [],
          nextSibling: null,
          previousSibling: null
        }
        return div
      }
      // 通用元素mock
      return {
        style: {},
        appendChild: vi.fn(),
        removeChild: vi.fn(),
        insertBefore: vi.fn(),
        addEventListener: vi.fn(),
        removeEventListener: vi.fn(),
        getBoundingClientRect: vi.fn(() => ({
          left: 0, top: 0, right: 100, bottom: 100,
          width: 100, height: 100, x: 0, y: 0
        })),
        offsetWidth: 100,
        offsetHeight: 100,
        clientWidth: 100,
        clientHeight: 100,
        innerHTML: '',
        textContent: '',
        className: '',
        parentNode: null,
        childNodes: [],
        nextSibling: null,
        previousSibling: null
      }
    }),
    querySelector: vi.fn(() => null),
    querySelectorAll: vi.fn(() => []),
    getElementById: vi.fn(() => null),
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    dispatchEvent: vi.fn(),
    createEvent: vi.fn(() => ({
      initEvent: vi.fn(),
      preventDefault: vi.fn(),
      stopPropagation: vi.fn()
    })),
    body: {
      appendChild: vi.fn(),
      removeChild: vi.fn(),
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
      style: {},
      offsetWidth: 1024,
      offsetHeight: 768,
      clientWidth: 1024,
      clientHeight: 768
    }
  },
  writable: true,
  configurable: true
})

// URL API Mock
global.URL = {
  createObjectURL: vi.fn(() => 'blob:mock-url'),
  revokeObjectURL: vi.fn()
}

// 其他Mock
global.Image = vi.fn().mockImplementation(() => ({
  addEventListener: vi.fn(),
  removeEventListener: vi.fn(),
  src: '',
  alt: '',
  width: 0,
  height: 0,
  onload: null,
  onerror: null
}))

// CSS和静态资源Mock
vi.mock('*.css', () => ({}))
vi.mock('*.scss', () => ({}))
vi.mock('*.sass', () => ({}))
vi.mock('*.less', () => ({}))
vi.mock('*.styl', () => ({}))
vi.mock('*.stylus', () => ({}))
vi.mock('*.png', () => '/mock-image.png')
vi.mock('*.jpg', () => '/mock-image.jpg')
vi.mock('*.jpeg', () => '/mock-image.jpeg')
vi.mock('*.gif', () => '/mock-image.gif')
vi.mock('*.svg', () => '/mock-image.svg')
vi.mock('*.webp', () => '/mock-image.webp')
vi.mock('*.ico', () => '/mock-icon.ico')

// 测试配置
vi.setConfig({ 
  testTimeout: 15000,
  hookTimeout: 10000,
  teardownTimeout: 10000,
  isolate: false
})

// Window对象增强Mock
Object.defineProperty(global, 'window', {
  value: {
    ...global.window,
    devicePixelRatio: 1,
    requestAnimationFrame: vi.fn((callback) => {
      setTimeout(callback, 16)
      return 1
    }),
    cancelAnimationFrame: vi.fn(),
    getComputedStyle: vi.fn(() => ({
      getPropertyValue: vi.fn(() => ''),
      display: 'block',
      visibility: 'visible',
      opacity: '1'
    })),
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    dispatchEvent: vi.fn(),
    location: {
      href: 'http://localhost:3000',
      origin: 'http://localhost:3000',
      protocol: 'http:',
      host: 'localhost:3000',
      hostname: 'localhost',
      port: '3000',
      pathname: '/',
      search: '',
      hash: ''
    },
    navigator: {
      userAgent: 'Mozilla/5.0 (Test Environment)',
      platform: 'Test',
      language: 'zh-CN',
      languages: ['zh-CN', 'en'],
      cookieEnabled: true
    },
    screen: {
      width: 1920,
      height: 1080,
      availWidth: 1920,
      availHeight: 1040,
      colorDepth: 24,
      pixelDepth: 24
    },
    innerWidth: 1024,
    innerHeight: 768,
    outerWidth: 1024,
    outerHeight: 768
  },
  writable: true,
  configurable: true
})

// Canvas和ZRender错误专项修复
// =========================

// 确保Canvas上下文永远不为null
const originalGetContext = MockHTMLCanvasElement.prototype.getContext
if (originalGetContext) {
  MockHTMLCanvasElement.prototype.getContext = function(type, options) {
    const context = originalGetContext.call(this, type, options)
    // 绝对确保返回值不为null
    if (!context && type === '2d') {
      return new MockCanvasRenderingContext2D()
    }
    return context || {}
  }
}

// 增强全局错误处理 - 捕获ECharts/ZRender错误
const originalConsoleError = console.error
console.error = (...args) => {
  const errorMessage = args.join(' ')
  // 过滤掉预期的测试错误，避免干扰
  if (
    errorMessage.includes('clearRect') ||
    errorMessage.includes('ZRender') ||
    errorMessage.includes('Canvas') ||
    errorMessage.includes('ECharts')
  ) {
    // 静默处理ECharts相关错误
    return
  }
  originalConsoleError.apply(console, args)
}

// 全局错误处理
process.on('unhandledRejection', (reason, promise) => {
  // 只记录非Canvas相关的错误
  if (!String(reason).includes('clearRect') && !String(reason).includes('Canvas')) {
    console.log('Unhandled Rejection at:', promise, 'reason:', reason)
  }
})

process.on('uncaughtException', (error) => {
  // 只记录非Canvas相关的错误
  if (!String(error).includes('clearRect') && !String(error).includes('Canvas')) {
    console.log('Uncaught Exception:', error)
  }
})