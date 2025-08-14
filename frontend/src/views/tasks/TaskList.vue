<template>
  <div class="task-list">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-content">
        <h1 class="page-title">{{ pageInfo.title }}</h1>
        <p class="page-subtitle">{{ pageInfo.subtitle }}</p>
      </div>
      <div class="header-actions">
        <el-button type="primary" :icon="Plus" @click="showCreateDialog">
          {{ pageInfo.createButtonText }}
        </el-button>
        <el-button :icon="Upload" @click="showImportDialog">
          导入任务
        </el-button>
        <el-button :icon="Download" @click="exportTasks"> 导出任务 </el-button>
      </div>
    </div>

    <!-- 统计卡片 -->
    <div class="stats-section">
      <el-row :gutter="20">
        <el-col
          :xs="24"
          :sm="12"
          :md="6"
          v-for="stat in statsCards"
          :key="stat.key"
        >
          <div class="stat-card" :class="stat.className">
            <div class="stat-icon">
              <el-icon :size="24" :color="stat.iconColor">
                <component :is="stat.icon" />
              </el-icon>
            </div>
            <div class="stat-content">
              <div class="stat-value">{{ taskStats[stat.key] || 0 }}</div>
              <div class="stat-label">{{ stat.label }}</div>
            </div>
          </div>
        </el-col>
      </el-row>
    </div>

    <!-- 筛选和搜索 -->
    <el-card class="filter-card" shadow="never">
      <div class="filter-section">
        <div class="filter-row">
          <div class="filter-item">
            <el-input
              v-model="searchQuery"
              placeholder="搜索任务标题、描述或位置..."
              :prefix-icon="Search"
              clearable
              @input="handleSearch"
            />
          </div>

          <div class="filter-item">
            <el-select
              v-model="filters.status"
              placeholder="任务状态"
              multiple
              collapse-tags
              clearable
              @change="loadTasks"
            >
              <el-option
                v-for="(config, status) in TASK_STATUS_CONFIG"
                :key="status"
                :label="config.label"
                :value="status"
              />
            </el-select>
          </div>

          <div class="filter-item">
            <el-select
              v-model="filters.type"
              placeholder="任务类型"
              multiple
              collapse-tags
              clearable
              @change="loadTasks"
            >
              <el-option
                v-for="(config, type) in TASK_TYPE_CONFIG"
                :key="type"
                :label="config.label"
                :value="type"
              />
            </el-select>
          </div>

          <div class="filter-item">
            <el-select
              v-model="filters.priority"
              placeholder="优先级"
              multiple
              collapse-tags
              clearable
              @change="loadTasks"
            >
              <el-option
                v-for="(config, priority) in TASK_PRIORITY_CONFIG"
                :key="priority"
                :label="config.label"
                :value="priority"
              />
            </el-select>
          </div>

          <div class="filter-item">
            <el-date-picker
              v-model="dateRange"
              type="daterange"
              range-separator="至"
              start-placeholder="开始日期"
              end-placeholder="结束日期"
              format="YYYY-MM-DD"
              value-format="YYYY-MM-DD"
              @change="handleDateRangeChange"
            />
          </div>

          <div class="filter-actions">
            <el-button :icon="Refresh" @click="resetFilters">重置</el-button>
          </div>
        </div>
      </div>
    </el-card>

    <!-- 任务列表 -->
    <el-card class="table-card" shadow="never">
      <template #header>
        <div class="table-header">
          <div class="table-title">任务列表 ({{ pagination.total }})</div>
          <div class="table-actions">
            <el-button-group>
              <el-button
                :type="viewMode === 'table' ? 'primary' : 'default'"
                :icon="List"
                @click="viewMode = 'table'"
              >
                列表
              </el-button>
              <el-button
                :type="viewMode === 'card' ? 'primary' : 'default'"
                :icon="Grid"
                @click="viewMode = 'card'"
              >
                卡片
              </el-button>
            </el-button-group>
          </div>
        </div>
      </template>

      <!-- 表格视图 -->
      <div v-if="viewMode === 'table'">
        <el-table
          :data="tasks"
          v-loading="loading"
          row-key="id"
          @selection-change="handleSelectionChange"
          @sort-change="handleSortChange"
        >
          <el-table-column type="selection" width="55" />

          <el-table-column
            prop="title"
            label="任务标题"
            min-width="200"
            show-overflow-tooltip
            sortable="custom"
          >
            <template #default="scope">
              <div class="task-title">
                <el-link type="primary" @click="viewTaskDetail(scope.row.id)">
                  {{ scope.row.title }}
                </el-link>
                <div class="task-meta">
                  <el-tag :type="getTypeTagType(scope.row.type)" size="small">
                    {{ TASK_TYPE_CONFIG[scope.row.type]?.label }}
                  </el-tag>
                  <el-tag
                    :type="getPriorityTagType(scope.row.priority)"
                    size="small"
                  >
                    {{ TASK_PRIORITY_CONFIG[scope.row.priority]?.label }}
                  </el-tag>
                </div>
              </div>
            </template>
          </el-table-column>

          <el-table-column
            prop="status"
            label="状态"
            width="100"
            sortable="custom"
          >
            <template #default="scope">
              <el-tag :type="getStatusTagType(scope.row.status)">
                {{ TASK_STATUS_CONFIG[scope.row.status]?.label }}
              </el-tag>
            </template>
          </el-table-column>

          <el-table-column
            prop="assigneeName"
            label="负责人"
            width="120"
            show-overflow-tooltip
          >
            <template #default="scope">
              <span v-if="scope.row.assigneeName">{{
                scope.row.assigneeName
              }}</span>
              <span v-else class="text-placeholder">未分配</span>
            </template>
          </el-table-column>

          <el-table-column
            prop="location"
            label="位置"
            width="150"
            show-overflow-tooltip
          />

          <el-table-column
            prop="dueDate"
            label="截止时间"
            width="120"
            sortable="custom"
          >
            <template #default="scope">
              <div
                :class="getDueDateClass(scope.row.dueDate, scope.row.status)"
              >
                {{ formatDate(scope.row.dueDate) }}
              </div>
            </template>
          </el-table-column>

          <el-table-column
            prop="createdAt"
            label="创建时间"
            width="120"
            sortable="custom"
          >
            <template #default="scope">
              {{ formatDate(scope.row.createdAt) }}
            </template>
          </el-table-column>

          <el-table-column label="进度" width="100">
            <template #default="scope">
              <el-progress
                :percentage="getTaskProgress(scope.row)"
                :color="getProgressColor(scope.row.status)"
                :show-text="false"
              />
            </template>
          </el-table-column>

          <el-table-column label="操作" width="200" fixed="right">
            <template #default="scope">
              <div class="table-actions">
                <el-button
                  type="text"
                  size="small"
                  @click="viewTaskDetail(scope.row.id)"
                >
                  详情
                </el-button>
                <el-button
                  type="text"
                  size="small"
                  @click="editTask(scope.row)"
                >
                  编辑
                </el-button>
                <el-dropdown
                  @command="command => handleTaskAction(command, scope.row)"
                >
                  <el-button type="text" size="small">
                    更多<el-icon><ArrowDown /></el-icon>
                  </el-button>
                  <template #dropdown>
                    <el-dropdown-menu>
                      <el-dropdown-item
                        command="assign"
                        v-if="scope.row.status === 'pending'"
                      >
                        分配任务
                      </el-dropdown-item>
                      <el-dropdown-item
                        command="start"
                        v-if="
                          scope.row.status === 'pending' ||
                          scope.row.status === 'assigned'
                        "
                      >
                        开始任务
                      </el-dropdown-item>
                      <el-dropdown-item
                        command="complete"
                        v-if="scope.row.status === 'in_progress'"
                      >
                        完成任务
                      </el-dropdown-item>
                      <el-dropdown-item
                        command="cancel"
                        v-if="
                          scope.row.status !== 'completed' &&
                          scope.row.status !== 'cancelled'
                        "
                      >
                        取消任务
                      </el-dropdown-item>
                      <el-dropdown-item
                        command="reopen"
                        v-if="
                          scope.row.status === 'completed' ||
                          scope.row.status === 'cancelled'
                        "
                      >
                        重新打开
                      </el-dropdown-item>
                      <el-dropdown-item command="delete" divided>
                        删除任务
                      </el-dropdown-item>
                    </el-dropdown-menu>
                  </template>
                </el-dropdown>
              </div>
            </template>
          </el-table-column>
        </el-table>

        <!-- 批量操作 -->
        <div class="batch-actions" v-if="selectedTasks.length > 0">
          <div class="batch-info">已选择 {{ selectedTasks.length }} 个任务</div>
          <div class="batch-buttons">
            <el-button @click="batchAssign">批量分配</el-button>
            <el-button @click="batchExport">批量导出</el-button>
            <el-button type="danger" @click="batchDelete">批量删除</el-button>
          </div>
        </div>
      </div>

      <!-- 卡片视图 -->
      <div v-else class="card-view">
        <el-row :gutter="20">
          <el-col
            :xs="24"
            :sm="12"
            :lg="8"
            v-for="task in tasks"
            :key="task.id"
          >
            <div class="task-card" @click="viewTaskDetail(task.id)">
              <div class="task-card-header">
                <div class="task-card-title">{{ task.title }}</div>
                <div class="task-card-actions">
                  <el-dropdown
                    @command="command => handleTaskAction(command, task)"
                  >
                    <el-button type="text" size="small" :icon="MoreFilled" />
                    <template #dropdown>
                      <el-dropdown-menu>
                        <el-dropdown-item command="edit">编辑</el-dropdown-item>
                        <el-dropdown-item command="delete"
                          >删除</el-dropdown-item
                        >
                      </el-dropdown-menu>
                    </template>
                  </el-dropdown>
                </div>
              </div>

              <div class="task-card-content">
                <div class="task-card-meta">
                  <el-tag :type="getTypeTagType(task.type)" size="small">
                    {{ TASK_TYPE_CONFIG[task.type]?.label }}
                  </el-tag>
                  <el-tag
                    :type="getPriorityTagType(task.priority)"
                    size="small"
                  >
                    {{ TASK_PRIORITY_CONFIG[task.priority]?.label }}
                  </el-tag>
                  <el-tag :type="getStatusTagType(task.status)" size="small">
                    {{ TASK_STATUS_CONFIG[task.status]?.label }}
                  </el-tag>
                </div>

                <div class="task-card-desc">{{ task.description }}</div>

                <div class="task-card-info">
                  <div class="info-item">
                    <el-icon><Location /></el-icon>
                    {{ task.location }}
                  </div>
                  <div class="info-item">
                    <el-icon><User /></el-icon>
                    {{ task.assigneeName || '未分配' }}
                  </div>
                  <div class="info-item">
                    <el-icon><Clock /></el-icon>
                    {{ formatDate(task.dueDate) }}
                  </div>
                </div>
              </div>

              <div class="task-card-footer">
                <el-progress
                  :percentage="getTaskProgress(task)"
                  :color="getProgressColor(task.status)"
                />
              </div>
            </div>
          </el-col>
        </el-row>
      </div>

      <!-- 分页 -->
      <div class="pagination-wrapper">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.pageSize"
          :total="pagination.total"
          :page-sizes="[10, 20, 50, 100]"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="loadTasks"
          @current-change="loadTasks"
        />
      </div>
    </el-card>

    <!-- 创建/编辑任务对话框 -->
    <TaskFormDialog
      v-model="showTaskDialog"
      :task="currentTask"
      @success="handleTaskFormSuccess"
    />

    <!-- 任务详情对话框 -->
    <TaskDetailDialog
      v-model="showDetailDialog"
      :task-id="currentTaskId"
      @updated="loadTasks"
    />

    <!-- 导入任务对话框 -->
    <ImportTaskDialog
      v-model="showImportTaskDialog"
      @success="handleImportSuccess"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Plus,
  Search,
  Refresh,
  Upload,
  Download,
  List,
  Grid,
  ArrowDown,
  MoreFilled,
  Location,
  User,
  Clock,
  Document,
  CircleCheck,
  Warning
} from '@element-plus/icons-vue'
import { tasksApi } from '@/api/tasks'
import { useAuthStore } from '@/stores/auth'
import type { Task, TaskListParams, TaskStats } from '@/types/task'
import {
  TASK_TYPE_CONFIG,
  TASK_PRIORITY_CONFIG,
  TASK_STATUS_CONFIG
} from '@/types/task'
import TaskFormDialog from '@/components/tasks/TaskFormDialog.vue'
import TaskDetailDialog from '@/components/tasks/TaskDetailDialog.vue'
import ImportTaskDialog from '@/components/tasks/ImportTaskDialog.vue'

const router = useRouter()
const authStore = useAuthStore()

// 根据路由确定任务类型
const taskType = computed(() => {
  const path = router.currentRoute.value.path
  if (path.includes('/tasks/monitoring')) return 'monitoring'
  if (path.includes('/tasks/assistance')) return 'assistance'
  if (path.includes('/tasks/repair')) return 'repair'
  return 'all'
})

// 根据任务类型设置页面标题和描述
const pageInfo = computed(() => {
  switch (taskType.value) {
    case 'monitoring':
      return {
        title: '监控任务',
        subtitle: '管理和跟踪所有监控巡检任务',
        createButtonText: '新建监控任务'
      }
    case 'assistance':
      return {
        title: '协助任务',
        subtitle: '管理和跟踪所有协助支援任务',
        createButtonText: '新建协助任务'
      }
    case 'repair':
      return {
        title: '维修任务',
        subtitle: '管理和跟踪所有维修处理任务',
        createButtonText: '新建维修任务'
      }
    default:
      return {
        title: '任务管理',
        subtitle: '管理和跟踪所有维护任务',
        createButtonText: '新建任务'
      }
  }
})

// 响应式数据
const loading = ref(false)
const tasks = ref<Task[]>([])
const taskStats = reactive<TaskStats>({
  total: 0,
  pending: 0,
  inProgress: 0,
  completed: 0,
  cancelled: 0,
  overdue: 0,
  byType: { repair: 0, monitoring: 0, assistance: 0 },
  byPriority: { low: 0, medium: 0, high: 0, urgent: 0 }
})

const searchQuery = ref('')
const dateRange = ref<[string, string] | null>(null)
const viewMode = ref<'table' | 'card'>('table')
const selectedTasks = ref<Task[]>([])

const filters = reactive({
  status: [] as string[],
  type: [] as string[],
  priority: [] as string[],
  assigneeId: undefined as number | undefined,
  dateRange: undefined as [string, string] | undefined
})

const pagination = reactive({
  page: 1,
  pageSize: 20,
  total: 0
})

const sortConfig = reactive({
  sortBy: 'createdAt',
  sortOrder: 'desc' as 'asc' | 'desc'
})

// 对话框状态
const showTaskDialog = ref(false)
const showDetailDialog = ref(false)
const showImportTaskDialog = ref(false)
const currentTask = ref<Task | null>(null)
const currentTaskId = ref<number | null>(null)

// 统计卡片配置
const statsCards = [
  {
    key: 'total' as keyof TaskStats,
    label: '总任务',
    icon: Document,
    iconColor: '#409EFF',
    className: 'stat-primary'
  },
  {
    key: 'pending' as keyof TaskStats,
    label: '待处理',
    icon: Clock,
    iconColor: '#909399',
    className: 'stat-default'
  },
  {
    key: 'inProgress' as keyof TaskStats,
    label: '进行中',
    icon: Warning,
    iconColor: '#E6A23C',
    className: 'stat-warning'
  },
  {
    key: 'completed' as keyof TaskStats,
    label: '已完成',
    icon: CircleCheck,
    iconColor: '#67C23A',
    className: 'stat-success'
  }
]

// 计算属性
const hasSelectedTasks = computed(() => selectedTasks.value.length > 0)

// 方法
const loadTasks = async () => {
  try {
    loading.value = true

    // 根据当前任务类型添加过滤条件
    const taskTypeFilter = taskType.value !== 'all' ? [taskType.value] : []

    const params: TaskListParams = {
      page: pagination.page,
      pageSize: pagination.pageSize,
      sortBy: sortConfig.sortBy,
      sortOrder: sortConfig.sortOrder,
      filters: {
        ...filters,
        type: taskTypeFilter.length > 0 ? taskTypeFilter : filters.type,
        search: searchQuery.value || undefined
      }
    }

    const result = await tasksApi.getTasks(params)
    tasks.value = result.items
    pagination.total = result.total
  } catch (error) {
    ElMessage.error('加载任务列表失败')
  } finally {
    loading.value = false
  }
}

const loadTaskStats = async () => {
  try {
    // 根据当前任务类型添加过滤条件
    const taskTypeFilter = taskType.value !== 'all' ? [taskType.value] : []
    const statsFilters = {
      ...filters,
      type: taskTypeFilter.length > 0 ? taskTypeFilter : filters.type
    }

    const stats = await tasksApi.getTaskStats(statsFilters)
    Object.assign(taskStats, stats)
  } catch (error) {
    console.error('加载任务统计失败:', error)
  }
}

const handleSearch = () => {
  pagination.page = 1
  loadTasks()
}

const handleDateRangeChange = (value: [string, string] | null) => {
  filters.dateRange = value || undefined
  loadTasks()
}

const handleSelectionChange = (selection: Task[]) => {
  selectedTasks.value = selection
}

const handleSortChange = ({
  prop,
  order
}: {
  prop: string
  order: string | null
}) => {
  if (order) {
    sortConfig.sortBy = prop
    sortConfig.sortOrder = order === 'ascending' ? 'asc' : 'desc'
  } else {
    sortConfig.sortBy = 'createdAt'
    sortConfig.sortOrder = 'desc'
  }
  loadTasks()
}

const resetFilters = () => {
  Object.assign(filters, {
    status: [],
    type: [],
    priority: [],
    assigneeId: undefined,
    dateRange: undefined
  })
  searchQuery.value = ''
  dateRange.value = null
  pagination.page = 1
  loadTasks()
}

// 任务操作
const showCreateDialog = () => {
  currentTask.value = null
  showTaskDialog.value = true
}

const editTask = (task: Task) => {
  currentTask.value = task
  showTaskDialog.value = true
}

const viewTaskDetail = (taskId: number) => {
  currentTaskId.value = taskId
  showDetailDialog.value = true
}

const handleTaskAction = async (command: string, task: Task) => {
  switch (command) {
    case 'edit':
      editTask(task)
      break
    case 'delete':
      await deleteTask(task)
      break
    case 'assign':
      // TODO: 实现分配任务逻辑
      break
    case 'start':
      await startTask(task)
      break
    case 'complete':
      await completeTask(task)
      break
    case 'cancel':
      await cancelTask(task)
      break
    case 'reopen':
      await reopenTask(task)
      break
  }
}

const deleteTask = async (task: Task) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除任务"${task.title}"吗？此操作不可恢复。`,
      '删除确认',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    await tasksApi.deleteTask(task.id)
    ElMessage.success('任务删除成功')
    loadTasks()
    loadTaskStats()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除任务失败')
    }
  }
}

const startTask = async (task: Task) => {
  try {
    await tasksApi.startTask(task.id)
    ElMessage.success('任务已开始')
    loadTasks()
    loadTaskStats()
  } catch (error) {
    ElMessage.error('开始任务失败')
  }
}

const completeTask = async (task: Task) => {
  try {
    await tasksApi.completeTask(task.id)
    ElMessage.success('任务已完成')
    loadTasks()
    loadTaskStats()
  } catch (error) {
    ElMessage.error('完成任务失败')
  }
}

const cancelTask = async (task: Task) => {
  try {
    const { value: reason } = await ElMessageBox.prompt(
      '请输入取消原因',
      '取消任务',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        inputValidator: value => {
          if (!value || value.trim().length === 0) {
            return '请输入取消原因'
          }
          return true
        }
      }
    )

    await tasksApi.cancelTask(task.id, reason)
    ElMessage.success('任务已取消')
    loadTasks()
    loadTaskStats()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('取消任务失败')
    }
  }
}

const reopenTask = async (task: Task) => {
  try {
    const { value: reason } = await ElMessageBox.prompt(
      '请输入重新打开原因',
      '重新打开任务',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        inputValidator: value => {
          if (!value || value.trim().length === 0) {
            return '请输入重新打开原因'
          }
          return true
        }
      }
    )

    await tasksApi.reopenTask(task.id, reason)
    ElMessage.success('任务已重新打开')
    loadTasks()
    loadTaskStats()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('重新打开任务失败')
    }
  }
}

// 批量操作
const batchAssign = () => {
  // TODO: 实现批量分配逻辑
  ElMessage.info('批量分配功能开发中...')
}

const batchExport = () => {
  const ids = selectedTasks.value.map(task => task.id)
  // TODO: 实现批量导出逻辑
  ElMessage.info('批量导出功能开发中...')
}

const batchDelete = async () => {
  try {
    await ElMessageBox.confirm(
      `确定要删除选中的 ${selectedTasks.value.length} 个任务吗？此操作不可恢复。`,
      '批量删除确认',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    const ids = selectedTasks.value.map(task => task.id)
    await tasksApi.batchDeleteTasks(ids)
    ElMessage.success('批量删除成功')
    selectedTasks.value = []
    loadTasks()
    loadTaskStats()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('批量删除失败')
    }
  }
}

// 导入导出
const showImportDialog = () => {
  showImportTaskDialog.value = true
}

const exportTasks = async () => {
  try {
    await tasksApi.exportTasks(filters)
    ElMessage.success('导出成功')
  } catch (error) {
    ElMessage.error('导出失败')
  }
}

const handleImportSuccess = () => {
  loadTasks()
  loadTaskStats()
}

const handleTaskFormSuccess = () => {
  loadTasks()
  loadTaskStats()
}

// 工具方法
const formatDate = (dateString: string): string => {
  return new Date(dateString).toLocaleDateString('zh-CN')
}

const getTypeTagType = (type: string): string => {
  const typeMap: Record<string, string> = {
    repair: 'primary',
    monitoring: 'success',
    assistance: 'warning'
  }
  return typeMap[type] || 'info'
}

const getPriorityTagType = (priority: string): string => {
  const priorityMap: Record<string, string> = {
    low: 'info',
    medium: 'warning',
    high: 'danger',
    urgent: 'danger'
  }
  return priorityMap[priority] || 'info'
}

const getStatusTagType = (status: string): string => {
  const statusMap: Record<string, string> = {
    pending: 'info',
    in_progress: 'warning',
    completed: 'success',
    cancelled: 'danger'
  }
  return statusMap[status] || 'info'
}

const getDueDateClass = (dueDate: string, status: string): string => {
  if (status === 'completed') return ''

  const now = new Date()
  const due = new Date(dueDate)
  const diffTime = due.getTime() - now.getTime()
  const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24))

  if (diffDays < 0) return 'overdue'
  if (diffDays <= 1) return 'due-soon'
  return ''
}

const getTaskProgress = (task: Task): number => {
  switch (task.status) {
    case 'pending':
      return 0
    case 'in_progress':
      return 50
    case 'completed':
      return 100
    case 'cancelled':
      return 0
    default:
      return 0
  }
}

const getProgressColor = (status: string): string => {
  const colorMap: Record<string, string> = {
    pending: '#909399',
    in_progress: '#E6A23C',
    completed: '#67C23A',
    cancelled: '#F56C6C'
  }
  return colorMap[status] || '#909399'
}

// 生命周期
onMounted(() => {
  loadTasks()
  loadTaskStats()
})

// 监听筛选条件变化
watch(
  () => [filters.status, filters.type, filters.priority, taskType.value],
  () => {
    pagination.page = 1
    loadTasks()
    loadTaskStats()
  },
  { deep: true }
)
</script>

<style scoped lang="scss">
@use '@/styles/variables.scss' as *;
@use '@/styles/mixins.scss' as *;
@use 'sass:color';

.task-list {
  padding: $spacing-base;
}

.page-header {
  @include flex-between;
  margin-bottom: $spacing-large;
  padding: $spacing-base;
  background: $background-color-white;
  border-radius: $border-radius-base;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);

  .header-content {
    .page-title {
      margin: 0 0 $spacing-extra-small 0;
      font-size: $font-size-extra-large;
      font-weight: 600;
      color: $text-color-primary;
    }

    .page-subtitle {
      margin: 0;
      font-size: $font-size-small;
      color: $text-color-secondary;
    }
  }

  .header-actions {
    @include flex-center;
    gap: $spacing-small;
  }
}

.stats-section {
  margin-bottom: $spacing-large;
}

.stat-card {
  @include flex-start;
  padding: $spacing-base;
  background: $background-color-white;
  border-radius: $border-radius-base;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
  transition: all $transition-base;

  &:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
  }

  .stat-icon {
    @include flex-center;
    width: 48px;
    height: 48px;
    border-radius: 50%;
    margin-right: $spacing-base;

    &.stat-primary {
      background: color.adjust($primary-color, $lightness: 45%);
    }

    &.stat-success {
      background: color.adjust($success-color, $lightness: 45%);
    }

    &.stat-warning {
      background: color.adjust($warning-color, $lightness: 45%);
    }

    &.stat-default {
      background: color.adjust($info-color, $lightness: 45%);
    }
  }

  .stat-content {
    .stat-value {
      font-size: $font-size-large;
      font-weight: 700;
      color: $text-color-primary;
      line-height: 1.2;
    }

    .stat-label {
      font-size: $font-size-small;
      color: $text-color-secondary;
      margin-top: 4px;
    }
  }
}

.filter-card {
  margin-bottom: $spacing-base;

  .filter-section {
    .filter-row {
      @include flex-start;
      gap: $spacing-base;
      flex-wrap: wrap;

      .filter-item {
        min-width: 200px;
        flex: 1;

        &:first-child {
          flex: 2;
          min-width: 300px;
        }
      }

      .filter-actions {
        @include flex-center;
      }
    }
  }
}

.table-card {
  .table-header {
    @include flex-between;

    .table-title {
      font-size: $font-size-medium;
      font-weight: 600;
      color: $text-color-primary;
    }
  }
}

.task-title {
  .task-meta {
    @include flex-start;
    gap: $spacing-extra-small;
    margin-top: 4px;
  }
}

.table-actions {
  @include flex-start;
  gap: $spacing-extra-small;
}

.batch-actions {
  @include flex-between;
  padding: $spacing-base;
  background: $background-color-light;
  border-radius: $border-radius-base;
  margin-top: $spacing-base;

  .batch-info {
    color: $text-color-secondary;
  }

  .batch-buttons {
    @include flex-center;
    gap: $spacing-small;
  }
}

.card-view {
  .task-card {
    background: $background-color-white;
    border: 1px solid $border-color-lighter;
    border-radius: $border-radius-base;
    padding: $spacing-base;
    cursor: pointer;
    transition: all $transition-base;
    margin-bottom: $spacing-base;

    &:hover {
      border-color: $primary-color;
      box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
    }

    .task-card-header {
      @include flex-between;
      margin-bottom: $spacing-small;

      .task-card-title {
        font-size: $font-size-medium;
        font-weight: 600;
        color: $text-color-primary;
        @include text-ellipsis;
      }
    }

    .task-card-content {
      .task-card-meta {
        @include flex-start;
        gap: $spacing-extra-small;
        margin-bottom: $spacing-small;
      }

      .task-card-desc {
        color: $text-color-secondary;
        font-size: $font-size-small;
        @include text-ellipsis-multiline(2);
        margin-bottom: $spacing-small;
      }

      .task-card-info {
        .info-item {
          @include flex-start;
          gap: 4px;
          font-size: $font-size-extra-small;
          color: $text-color-placeholder;
          margin-bottom: 4px;

          &:last-child {
            margin-bottom: 0;
          }
        }
      }
    }

    .task-card-footer {
      margin-top: $spacing-small;
    }
  }
}

.pagination-wrapper {
  @include flex-center;
  margin-top: $spacing-large;
}

.text-placeholder {
  color: $text-color-placeholder;
}

.overdue {
  color: $danger-color;
  font-weight: 600;
}

.due-soon {
  color: $warning-color;
  font-weight: 600;
}

// 响应式设计
@include respond-to(md) {
  .page-header {
    flex-direction: column;
    gap: $spacing-base;

    .header-actions {
      align-self: stretch;
      justify-content: flex-end;
    }
  }

  .filter-row {
    .filter-item {
      min-width: auto !important;
      flex: none !important;
      width: 100%;
    }
  }
}

@include respond-to(sm) {
  .task-list {
    padding: $spacing-small;
  }

  .header-actions {
    flex-direction: column;

    .el-button {
      width: 100%;
    }
  }
}
</style>
