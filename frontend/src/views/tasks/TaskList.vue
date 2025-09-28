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
        <el-dropdown @command="handleImportCommand">
          <el-button :icon="Upload">
            导入任务
            <el-icon class="el-icon--right">
              <ArrowDown />
            </el-icon>
          </el-button>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="repair">
                <el-icon><Tools /></el-icon>
                导入报修任务 (A-B表匹配)
              </el-dropdown-item>
              <el-dropdown-item command="assistance">
                <el-icon><User /></el-icon>
                导入协助任务
              </el-dropdown-item>
              <el-dropdown-item command="monitoring" disabled>
                <el-icon><Monitor /></el-icon>
                导入监控任务 (敬请期待)
              </el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
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
              :multiple-limit="1"
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
                <el-link type="primary" @click="viewTaskDetail(scope.row)">
                  {{ scope.row.title }}
                </el-link>
                <div class="task-meta">
                  <el-tag
                    v-if="isImportedTask(scope.row)"
                    :type="isUnmatchedImport(scope.row) ? 'danger' : 'info'"
                    size="small"
                    effect="plain"
                  >
                    {{ getImportTagText(scope.row) }}
                  </el-tag>
                  <el-tag
                    :type="
                      getTypeTagType(
                        scope.row.type || scope.row.task_type
                      ) as any
                    "
                    size="small"
                  >
                    {{
                      getTaskTypeConfig(
                        scope.row.type || scope.row.task_type
                      ).label
                    }}
                  </el-tag>
                  <el-tag
                    :type="getPriorityTagType(scope.row.priority) as any"
                    size="small"
                  >
                    {{ getTaskPriorityConfig(scope.row.priority).label }}
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
              <el-tag :type="getStatusTagType(scope.row.status) as any">
                {{ getTaskStatusConfig(scope.row.status).label }}
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
              <span v-if="scope.row.assigneeName || scope.row.member_name">
                {{ scope.row.assigneeName || scope.row.member_name }}
              </span>
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
                :class="
                  getDueDateClass(
                    scope.row.dueDate || scope.row.due_date,
                    scope.row.status
                  )
                "
              >
                {{ formatDate(scope.row.dueDate || scope.row.due_date) }}
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
              {{ formatDate(scope.row.createdAt || scope.row.created_at) }}
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
                  @click="viewTaskDetail(scope.row)"
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
            <div class="task-card" @click="viewTaskDetail(task)">
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
                <el-tag
                  v-if="isImportedTask(task)"
                  :type="isUnmatchedImport(task) ? 'danger' : 'info'"
                  size="small"
                  effect="plain"
                >
                  {{ getImportTagText(task) }}
                </el-tag>
                <el-tag
                  :type="
                    getTypeTagType(task.task_type || task.type || '') as any
                  "
                  size="small"
                  >
                    {{
                      (TASK_TYPE_CONFIG as any)[
                        task.task_type || task.type || ''
                      ]?.label
                    }}
                  </el-tag>
                  <el-tag
                    :type="getPriorityTagType(task.priority || '') as any"
                    size="small"
                  >
                    {{
                      (TASK_PRIORITY_CONFIG as any)[task.priority || '']?.label
                    }}
                  </el-tag>
                  <el-tag
                    :type="
                      getStatusTagType(
                        task.task_status || task.status || ''
                      ) as any
                    "
                    size="small"
                  >
                    {{
                      (TASK_STATUS_CONFIG as any)[
                        task.task_status || task.status || ''
                      ]?.label
                    }}
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
                    {{ task.assigneeName || task.member_name || '未分配' }}
                  </div>
                  <div class="info-item">
                    <el-icon><Clock /></el-icon>
                    {{ formatDate(task.dueDate || task.due_date || '') }}
                  </div>
                </div>
              </div>

              <div class="task-card-footer">
                <el-progress
                  :percentage="getTaskProgress(task)"
                  :color="
                    getProgressColor(task.task_status || task.status || '')
                  "
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
      :task-type="currentTaskType"
      @updated="loadTasks"
    />

    <!-- 导入报修任务对话框 -->
    <ImportTaskDialog
      v-model="showImportTaskDialog"
      @success="handleImportSuccess"
    />

    <!-- 导入协助任务对话框 -->
    <ImportAssistanceDialog
      v-model="showImportAssistanceDialog"
      @success="handleImportSuccess"
    />

    <el-dialog
      v-model="assignDialogVisible"
      title="分配处理人"
      width="480px"
    >
      <el-alert
        :title="`本次将指派 ${assignTargets.length} 个维修任务`"
        type="info"
        show-icon
        style="margin-bottom: 12px"
      />
      <el-form label-width="80px">
        <el-form-item label="处理人">
          <el-select
            v-model="assignForm.assigneeId"
            placeholder="请选择成员"
            filterable
            :loading="assignMembersLoading"
          >
            <el-option
              v-for="member in assignableMembers"
              :key="member.id"
              :label="`${member.name} (${member.username})`"
              :value="member.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="备注">
          <el-input
            v-model="assignForm.note"
            type="textarea"
            :rows="3"
            placeholder="可选，填写指派说明"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="assignDialogVisible = false">取消</el-button>
          <el-button type="primary" :loading="assignLoading" @click="submitAssign">
            确认指派
          </el-button>
        </div>
      </template>
    </el-dialog>
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
  Warning,
  Tools,
  Monitor
} from '@element-plus/icons-vue'
import { tasksApi } from '@/api/tasks'
import { MembersApi, type Member } from '@/api/members'
import { formatDate as formatDateUtil, parseDate } from '@/utils/date'
import type { Task, TaskListParams, TaskStats } from '@/types/task'
import {
  TASK_TYPE_CONFIG,
  TASK_PRIORITY_CONFIG,
  TASK_STATUS_CONFIG
} from '@/types/task'
import {
  getTaskTypeConfig,
  getTaskPriorityConfig,
  getTaskStatusConfig
} from '@/types/type-helpers'
import TaskFormDialog from '@/components/tasks/TaskFormDialog.vue'
import TaskDetailDialog from '@/components/tasks/TaskDetailDialog.vue'
import ImportTaskDialog from '@/components/tasks/ImportTaskDialog.vue'
import ImportAssistanceDialog from '@/components/tasks/ImportAssistanceDialog.vue'

const router = useRouter()

// 根据路由确定任务类型
const taskType = computed(() => {
  const path = router.currentRoute.value.path
  if (path.includes('/tasks/monitoring')) return 'monitoring'
  if (path.includes('/tasks/assistance')) return 'assistance'
  return 'repair'
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
        title: '维修任务',
        subtitle: '管理和跟踪所有维修处理任务',
        createButtonText: '新建维修任务'
      }
  }
})

// 响应式数据
const loading = ref(false)
const tasks = ref<Task[]>([])
const taskStats = reactive<TaskStats>({
  total: 0,
  pending: 0,
  in_progress: 0,
  completed: 0,
  cancelled: 0,
  overdue: 0,
  total_work_hours: 0,
  avg_work_hours: 0
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
const showImportAssistanceDialog = ref(false)
const currentTask = ref<Task | null>(null)
const currentTaskId = ref<number | null>(null)
const currentTaskType = ref<string | null>(null)

const assignDialogVisible = ref(false)
const assignLoading = ref(false)
const assignMembersLoading = ref(false)
const assignCandidatesLoaded = ref(false)
const assignableMembers = ref<Member[]>([])
const assignTargets = ref<Task[]>([])
const assignForm = reactive({
  assigneeId: undefined as number | undefined,
  note: ''
})

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

// 方法
const loadTasks = async () => {
  try {
    loading.value = true

    // 根据当前任务类型确定查询类型
    const selectedType =
      filters.type.length > 0 && filters.type[0] === taskType.value
        ? filters.type[0]
        : taskType.value

    if (selectedType) {
      if (filters.type.length !== 1 || filters.type[0] !== selectedType) {
        filters.type = [selectedType]
      }
    } else if (filters.type.length > 0) {
      filters.type = []
    }

    const params: TaskListParams = {
      page: pagination.page,
      page_size: pagination.pageSize,
      pageSize: pagination.pageSize, // Keep for compatibility
      sortBy: sortConfig.sortBy,
      sortOrder: sortConfig.sortOrder,
      filters: {
        ...filters,
        type: selectedType ? [selectedType] : [],
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
    const selectedType =
      filters.type.length > 0 && filters.type[0] === taskType.value
        ? filters.type[0]
        : taskType.value
    if (selectedType) {
      if (filters.type.length !== 1 || filters.type[0] !== selectedType) {
        filters.type = [selectedType]
      }
    } else if (filters.type.length > 0) {
      filters.type = []
    }
    const statsFilters = {
      ...filters,
      type: selectedType ? [selectedType] : []
    }

    const stats = await tasksApi.getTaskStats(statsFilters)
    Object.assign(taskStats, stats)
  } catch (error) {
    console.error('加载任务统计失败:', error)
  }
}

const fetchAssignableMembers = async () => {
  if (assignCandidatesLoaded.value) return
  try {
    assignMembersLoading.value = true
    const response = await MembersApi.getMembers({
      page: 1,
      page_size: 200,
      is_active: true
    })
    assignableMembers.value = response.items || []
    assignCandidatesLoaded.value = true
  } catch (error) {
    console.error('加载成员列表失败:', error)
    ElMessage.error('无法加载可指派的成员名单')
  } finally {
    assignMembersLoading.value = false
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

const viewTaskDetail = (task: Task | { id: number; type?: string; task_type?: string }) => {
  currentTaskId.value = task.id
  const resolvedType =
    (task as any).type ||
    (task as any).task_type ||
    taskType.value
  currentTaskType.value = resolvedType as string | null
  showDetailDialog.value = true
}

const openAssignDialog = async (targets: Task[]) => {
  if (!targets.length) {
    ElMessage.info('请选择要指派的任务')
    return
  }

  const eligible = targets.filter(item => resolveTaskType(item) === 'repair')
  if (eligible.length === 0) {
    ElMessage.warning('当前仅支持为维修任务指派处理人')
    return
  }

  if (eligible.length < targets.length) {
    ElMessage.warning('已忽略非维修类型任务，仅指派维修任务')
  }

  await fetchAssignableMembers()

  assignTargets.value = eligible
  assignForm.assigneeId =
    eligible.length === 1
      ? ((eligible[0].assignee_id as number | undefined) ||
        (eligible[0].assigneeId as number | undefined) ||
        undefined)
      : undefined
  assignForm.note = ''
  assignDialogVisible.value = true
}

const submitAssign = async () => {
  if (!assignForm.assigneeId) {
    ElMessage.warning('请选择要指派的成员')
    return
  }
  if (assignTargets.value.length === 0) {
    assignDialogVisible.value = false
    return
  }

  try {
    assignLoading.value = true
    for (const task of assignTargets.value) {
      await tasksApi.assignTask(task.id, assignForm.assigneeId, {
        note: assignForm.note,
        taskType: 'repair'
      })
    }
    ElMessage.success('任务指派成功')
    assignDialogVisible.value = false
    selectedTasks.value = []
    await loadTasks()
    await loadTaskStats()
  } catch (error) {
    console.error('任务指派失败:', error)
    ElMessage.error('任务指派失败，请稍后重试')
  } finally {
    assignLoading.value = false
  }
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
      await openAssignDialog([task])
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
  if (selectedTasks.value.length === 0) {
    ElMessage.info('请先选择需要指派的任务')
    return
  }
  openAssignDialog(selectedTasks.value)
}

const batchExport = async () => {
  if (selectedTasks.value.length === 0) {
    ElMessage.info('请先选择需要导出的任务')
    return
  }
  const ids = selectedTasks.value.map(task => task.id)
  try {
    await tasksApi.exportTasks({ ...filters, ids, task_ids: ids })
    ElMessage.success('批量导出任务成功')
  } catch (error) {
    console.error('批量导出任务失败:', error)
    ElMessage.error('批量导出失败，请稍后重试')
  }
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
const handleImportCommand = (command: string) => {
  switch (command) {
    case 'repair':
      showImportTaskDialog.value = true
      break
    case 'assistance':
      showImportAssistanceDialog.value = true
      break
    case 'monitoring':
      ElMessage.info('监控任务导入功能开发中，敬请期待')
      break
  }
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
  if (!dateString) return '-'
  return formatDateUtil(dateString) || '-'
}

const getTypeTagType = (type: string): string => {
  const typeMap: Record<string, string> = {
    repair: 'primary',
    monitoring: 'success',
    assistance: 'warning',
    online: 'info',
    offline: 'warning'
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

const getDueDateClass = (dueDate: string | undefined, status: string): string => {
  if (status === 'completed') return ''

  const dueDateObj = parseDate(dueDate)
  if (!dueDateObj) return ''

  const now = new Date()
  const diffTime = dueDateObj.getTime() - now.getTime()
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

const resolveTaskType = (task: Task): string => {
  const type = (task.task_type || (task as any).type || '').toString()
  return type || 'repair'
}

const isImportedTask = (task: Task): boolean => {
  return Boolean(task.import_batch_id || (task as any).importBatchId)
}

const isUnmatchedImport = (task: Task): boolean => {
  const summary = (task.import_summary || (task as any).importSummary) as
    | { is_matched?: boolean }
    | undefined
  if (summary && typeof summary.is_matched === 'boolean') {
    return summary.is_matched === false
  }
  const raw = (task as any).is_matched ?? (task as any).isMatched
  if (typeof raw === 'boolean') {
    return raw === false
  }
  return false
}

const getImportTagText = (task: Task): string => {
  return isUnmatchedImport(task) ? '未匹配' : '已导入'
}

watch(assignDialogVisible, visible => {
  if (!visible) {
    assignLoading.value = false
    assignForm.assigneeId = undefined
    assignForm.note = ''
    assignTargets.value = []
  }
})

// 生命周期
onMounted(() => {
  loadTasks()
  loadTaskStats()
})

watch(
  () => showDetailDialog.value,
  value => {
    if (!value) {
      currentTaskType.value = null
    }
  }
)

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
