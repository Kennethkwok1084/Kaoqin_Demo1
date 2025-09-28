<template>
  <div class="repair-task-list">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-content">
        <h1 class="page-title">报修单管理</h1>
        <p class="page-subtitle">管理和跟踪所有设备维修和网络故障处理任务</p>
      </div>
      <div class="header-actions">
        <el-button type="primary" :icon="Plus" @click="showCreateDialog">
          新建维修任务
        </el-button>
        <el-button :icon="Upload" @click="showImport">
          导入报修任务 (A-B表匹配)
        </el-button>
        <el-button :icon="Download" @click="exportTasks"> 导出任务 </el-button>
      </div>
    </div>

    <!-- 统计卡片 -->
    <div class="stats-section">
      <el-row :gutter="20">
        <el-col :xs="24" :sm="12" :md="6" v-for="stat in statsCards" :key="stat.key">
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

    <!-- 维修任务特有的筛选条件 -->
    <el-card class="filter-card" shadow="never">
      <div class="filter-section">
        <div class="filter-row">
          <div class="filter-item">
            <el-input
              v-model="searchQuery"
              placeholder="搜索维修任务标题、故障描述或维修位置..."
              :prefix-icon="Search"
              clearable
              @input="handleSearch"
            />
          </div>

          <div class="filter-item">
            <el-select
              v-model="filters.status"
              placeholder="维修状态"
              multiple
              collapse-tags
              clearable
              @change="loadTasks"
            >
              <el-option label="待处理" value="pending" />
              <el-option label="维修中" value="in_progress" />
              <el-option label="已完成" value="completed" />
              <el-option label="已取消" value="cancelled" />
            </el-select>
          </div>

          <div class="filter-item">
            <el-select
              v-model="filters.category"
              placeholder="故障类型"
              multiple
              collapse-tags
              clearable
              @change="loadTasks"
            >
              <el-option label="网络维修" value="network_repair" />
              <el-option label="硬件维修" value="hardware_repair" />
              <el-option label="软件支持" value="software_support" />
              <el-option label="其他问题" value="other" />
            </el-select>
          </div>

          <div class="filter-item">
            <el-select
              v-model="filters.taskType"
              placeholder="维修方式"
              multiple
              collapse-tags
              clearable
              @change="loadTasks"
            >
              <el-option label="线上维修" value="online" />
              <el-option label="线下维修" value="offline" />
            </el-select>
          </div>

          <div class="filter-item">
            <el-select
              v-model="filters.priority"
              placeholder="紧急程度"
              multiple
              collapse-tags
              clearable
              @change="loadTasks"
            >
              <el-option label="低" value="low" />
              <el-option label="中" value="medium" />
              <el-option label="高" value="high" />
              <el-option label="紧急" value="urgent" />
            </el-select>
          </div>

          <div class="filter-actions">
            <el-button :icon="Refresh" @click="resetFilters">重置</el-button>
          </div>
        </div>
      </div>
    </el-card>

    <!-- 维修任务列表 -->
    <el-card class="table-card" shadow="never">
      <template #header>
        <div class="table-header">
          <div class="table-title">报修单列表 ({{ pagination.total }})</div>
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

          <el-table-column prop="title" label="故障描述" min-width="200" show-overflow-tooltip sortable="custom">
            <template #default="scope">
              <div class="task-title">
              <el-link type="primary" @click="viewTaskDetail(scope.row.id)">
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
                  :type="isOfflineTask(scope.row) ? 'warning' : 'success'"
                  size="small"
                >
                  {{ isOfflineTask(scope.row) ? '线下维修' : '线上维修' }}
                  </el-tag>
                  <el-tag :type="getPriorityTagType(scope.row.priority)" size="small">
                    {{ getPriorityLabel(scope.row.priority) }}
                  </el-tag>
                </div>
              </div>
            </template>
          </el-table-column>

          <el-table-column prop="category" label="故障类型" width="120">
            <template #default="scope">
              <el-tag type="info" size="small">
                {{ getCategoryLabel(scope.row.category) }}
              </el-tag>
            </template>
          </el-table-column>

          <el-table-column prop="status" label="维修状态" width="100" sortable="custom">
            <template #default="scope">
              <el-tag :type="getStatusTagType(scope.row.status)">
                {{ getStatusLabel(scope.row.status) }}
              </el-tag>
              <el-tag
                v-if="scope.row.is_overdue_response || scope.row.isOverdueResponse"
                type="danger"
                effect="plain"
                size="small"
                style="margin-left: 6px;"
              >
                响应超时
              </el-tag>
              <el-tag
                v-else-if="scope.row.is_overdue_completion || scope.row.isOverdueCompletion"
                type="danger"
                effect="plain"
                size="small"
                style="margin-left: 6px;"
              >
                处理超时
              </el-tag>
            </template>
          </el-table-column>

          <el-table-column prop="member_name" label="处理人" width="120" show-overflow-tooltip>
            <template #default="scope">
              <span v-if="scope.row.member_name">{{ scope.row.member_name }}</span>
              <span v-else class="text-placeholder">未分配</span>
            </template>
          </el-table-column>

          <el-table-column prop="location" label="维修地点" width="150" show-overflow-tooltip />

          <el-table-column prop="contact_person" label="报修人" width="100" show-overflow-tooltip />

          <el-table-column prop="contact_phone" label="联系电话" width="120" show-overflow-tooltip />

          <el-table-column prop="work_minutes" label="工时(分钟)" width="100" sortable="custom" />

          <el-table-column prop="created_at" label="报修时间" width="120" sortable="custom">
            <template #default="scope">
              {{ formatDate(scope.row.created_at) }}
            </template>
          </el-table-column>

          <el-table-column prop="completed_at" label="完成时间" width="120">
            <template #default="scope">
              {{ scope.row.completed_at ? formatDate(scope.row.completed_at) : '-' }}
            </template>
          </el-table-column>

          <el-table-column label="操作" width="200" fixed="right">
            <template #default="scope">
              <div class="table-actions">
                <el-button type="text" size="small" @click="viewTaskDetail(scope.row.id)">
                  详情
                </el-button>
                <el-button type="text" size="small" @click="editTask(scope.row)">
                  编辑
                </el-button>
                <el-dropdown @command="command => handleTaskAction(command, scope.row)">
                  <el-button type="text" size="small">
                    更多<el-icon><ArrowDown /></el-icon>
                  </el-button>
                  <template #dropdown>
                    <el-dropdown-menu>
                      <el-dropdown-item command="assign" v-if="scope.row.status === 'pending'">
                        分配处理人
                      </el-dropdown-item>
                      <el-dropdown-item command="start" v-if="scope.row.status === 'pending'">
                        开始维修
                      </el-dropdown-item>
                      <el-dropdown-item command="complete" v-if="scope.row.status === 'in_progress'">
                        完成维修
                      </el-dropdown-item>
                      <el-dropdown-item command="offline" v-if="!isOfflineTask(scope.row)">
                        标记线下单
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

    <!-- 对话框组件 -->
    <TaskFormDialog
      v-model="showTaskDialog"
      :task="currentTask"
      @success="handleTaskFormSuccess"
    />

    <TaskDetailDialog
      v-model="showDetailDialog"
      :task-id="currentTaskId"
      :task-type="currentTaskType"
      @updated="loadTasks"
    />

    <ImportTaskDialog
      v-model="showImportDialog"
      @success="handleImportSuccess"
    />

    <el-dialog
      v-model="assignDialogVisible"
      title="分配处理人"
      width="480px"
    >
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

    <el-dialog
      v-model="offlineDialogVisible"
      title="标记线下维修"
      width="520px"
    >
      <el-alert
        v-if="offlineTargetTask && isOfflineTask(offlineTargetTask)"
        title="该任务已为线下单，将更新线下记录"
        type="warning"
        show-icon
        style="margin-bottom: 12px"
      />
      <el-form label-width="100px">
        <el-form-item label="检修结果">
          <el-input
            v-model="offlineForm.inspectionResult"
            type="textarea"
            :rows="3"
            placeholder="可记录现场检修情况，选填"
          />
        </el-form-item>
        <el-form-item label="图片地址">
          <el-input
            v-model="offlineForm.imagesText"
            type="textarea"
            :rows="3"
            placeholder="可粘贴图片地址，支持多行或逗号分隔"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="offlineDialogVisible = false">取消</el-button>
          <el-button type="primary" :loading="offlineLoading" @click="submitOfflineMark">
            确认标记
          </el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, watch } from 'vue'
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
  Document,
  CircleCheck,
  Warning,
  Tools
} from '@element-plus/icons-vue'
import { tasksApi } from '@/api/tasks'
import { MembersApi, type Member } from '@/api/members'
import { formatDate as formatDateUtil } from '@/utils/date'
import type { Task, TaskListParams, TaskStats } from '@/types/task'
import TaskFormDialog from '@/components/tasks/TaskFormDialog.vue'
import TaskDetailDialog from '@/components/tasks/TaskDetailDialog.vue'
import ImportTaskDialog from '@/components/tasks/ImportTaskDialog.vue'

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
const viewMode = ref<'table' | 'card'>('table')
const selectedTasks = ref<Task[]>([])

const filters = reactive({
  status: [] as string[],
  category: [] as string[],
  taskType: [] as string[],
  priority: [] as string[],
  assigneeId: undefined as number | undefined
})

const pagination = reactive({
  page: 1,
  pageSize: 20,
  total: 0
})

const sortConfig = reactive({
  sortBy: 'created_at',
  sortOrder: 'desc' as 'asc' | 'desc'
})

// 对话框状态
const showTaskDialog = ref(false)
const showDetailDialog = ref(false)
const showImportDialog = ref(false)
const currentTask = ref<Task | null>(null)
const currentTaskId = ref<number | null>(null)
const currentTaskType = ref<string | null>('repair')

// 指派相关
const assignDialogVisible = ref(false)
const assignLoading = ref(false)
const assignMembersLoading = ref(false)
const assignCandidatesLoaded = ref(false)
const assignableMembers = ref<Member[]>([])
const assignForm = reactive({
  assigneeId: undefined as number | undefined,
  note: ''
})

// 线下单标记
const offlineDialogVisible = ref(false)
const offlineLoading = ref(false)
const offlineTargetTask = ref<Task | null>(null)
const offlineForm = reactive({
  inspectionResult: '',
  imagesText: ''
})

// 统计卡片配置 - 专门针对维修任务
const statsCards = [
  {
    key: 'total' as keyof TaskStats,
    label: '总维修单',
    icon: Document,
    iconColor: '#409EFF',
    className: 'stat-primary'
  },
  {
    key: 'pending' as keyof TaskStats,
    label: '待维修',
    icon: Tools,
    iconColor: '#909399',
    className: 'stat-default'
  },
  {
    key: 'in_progress' as keyof TaskStats,
    label: '维修中',
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

    const params: TaskListParams = {
      page: pagination.page,
      pageSize: pagination.pageSize,
      sortBy: sortConfig.sortBy,
      sortOrder: sortConfig.sortOrder,
      filters: {
        ...filters,
        type: ['repair'], // 固定为维修任务
        search: searchQuery.value || undefined
      }
    }

    const result = await tasksApi.getTasks(params)
    tasks.value = result.items
    pagination.total = result.total
  } catch (error) {
    ElMessage.error('加载报修单列表失败')
  } finally {
    loading.value = false
  }
}

const loadTaskStats = async () => {
  try {
    const stats = await tasksApi.getTaskStats({ type: ['repair'] })
    Object.assign(taskStats, stats)
  } catch (error) {
    console.error('加载维修任务统计失败:', error)
  }
}

const handleSearch = () => {
  pagination.page = 1
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
    sortConfig.sortBy = 'created_at'
    sortConfig.sortOrder = 'desc'
  }
  loadTasks()
}

const resetFilters = () => {
  Object.assign(filters, {
    status: [],
    category: [],
    taskType: [],
    priority: [],
    assigneeId: undefined
  })
  searchQuery.value = ''
  pagination.page = 1
  loadTasks()
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

const isOfflineTask = (task: Task) => {
  if (typeof task.is_offline === 'boolean') {
    return task.is_offline
  }
  // 兼容驼峰命名
  if (typeof (task as any).isOffline === 'boolean') {
    return (task as any).isOffline
  }
  if (typeof (task as any).is_online === 'boolean') {
    return !(task as any).is_online
  }
  const taskType = (task.task_type || (task as any).taskType || '').toString()
  if (taskType) {
    return taskType === 'offline' || taskType === 'offline_repair'
  }
  return false
}

const openAssignDialog = async (task: Task) => {
  currentTask.value = task
  await fetchAssignableMembers()
  assignForm.assigneeId =
    (task.assignee_id as number | undefined) ||
    (task.assigneeId as number | undefined) ||
    undefined
  assignForm.note = ''
  assignDialogVisible.value = true
}

const submitAssign = async () => {
  if (!currentTask.value || !assignForm.assigneeId) {
    ElMessage.warning('请选择要指派的成员')
    return
  }
  try {
    assignLoading.value = true
    await tasksApi.assignTask(currentTask.value.id, assignForm.assigneeId, {
      note: assignForm.note,
      taskType: 'repair'
    })
    ElMessage.success('任务指派成功')
    assignDialogVisible.value = false
    await loadTasks()
    await loadTaskStats()
  } catch (error) {
    console.error('任务指派失败:', error)
    ElMessage.error('任务指派失败，请稍后重试')
  } finally {
    assignLoading.value = false
  }
}

const openOfflineDialog = async (task: Task) => {
  if (isOfflineTask(task)) {
    try {
      await ElMessageBox.confirm(
        '该任务已标记为线下单，继续操作将更新线下信息，确认继续？',
        '重复标记提醒',
        {
          confirmButtonText: '继续',
          cancelButtonText: '取消',
          type: 'warning'
        }
      )
    } catch {
      return
    }
  }

  offlineTargetTask.value = task
  offlineForm.inspectionResult = ''
  offlineForm.imagesText = ''
  offlineDialogVisible.value = true
}

const submitOfflineMark = async () => {
  if (!offlineTargetTask.value) return
  try {
    offlineLoading.value = true

    const images = offlineForm.imagesText
      .split(/\n|,/)
      .map(item => item.trim())
      .filter(Boolean)

    await tasksApi.markTaskOffline(offlineTargetTask.value.id, {
      inspectionResult: offlineForm.inspectionResult.trim() || undefined,
      images: images.length > 0 ? images : undefined
    })

    ElMessage.success('线下单标记成功')
    offlineDialogVisible.value = false
    await loadTasks()
    await loadTaskStats()
  } catch (error) {
    console.error('标记线下单失败:', error)
    ElMessage.error('标记线下单失败，请稍后重试')
  } finally {
    offlineLoading.value = false
  }
}

// 任务操作
const showCreateDialog = () => {
  currentTask.value = null
  showTaskDialog.value = true
}

const showImport = () => {
  showImportDialog.value = true
}

const editTask = (task: Task) => {
  currentTask.value = task
  showTaskDialog.value = true
}

const viewTaskDetail = (taskId: number) => {
  currentTaskId.value = taskId
  currentTaskType.value = 'repair'
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
      await openAssignDialog(task)
      break
    case 'start':
      await startTask(task)
      break
    case 'complete':
      await completeTask(task)
      break
    case 'offline':
      await openOfflineDialog(task)
      break
  }
}

const deleteTask = async (task: Task) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除维修任务"${task.title}"吗？此操作不可恢复。`,
      '删除确认',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    await tasksApi.deleteTask(task.id)
    ElMessage.success('维修任务删除成功')
    loadTasks()
    loadTaskStats()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除维修任务失败')
    }
  }
}

const startTask = async (task: Task) => {
  try {
    await tasksApi.startTask(task.id)
    ElMessage.success('维修任务已开始')
    loadTasks()
    loadTaskStats()
  } catch (error) {
    ElMessage.error('开始维修任务失败')
  }
}

const completeTask = async (task: Task) => {
  try {
    await tasksApi.completeTask(task.id)
    ElMessage.success('维修任务已完成')
    loadTasks()
    loadTaskStats()
  } catch (error) {
    ElMessage.error('完成维修任务失败')
  }
}

const exportTasks = async () => {
  try {
    await tasksApi.exportTasks({ ...filters, type: ['repair'] })
    ElMessage.success('维修任务导出成功')
  } catch (error) {
    ElMessage.error('导出维修任务失败')
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

const getPriorityTagType = (priority: string): string => {
  const priorityMap: Record<string, string> = {
    low: 'info',
    medium: 'warning',
    high: 'danger',
    urgent: 'danger'
  }
  return priorityMap[priority] || 'info'
}

const getPriorityLabel = (priority: string): string => {
  const priorityMap: Record<string, string> = {
    low: '低',
    medium: '中',
    high: '高',
    urgent: '紧急'
  }
  return priorityMap[priority] || '中'
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

const getStatusLabel = (status: string): string => {
  const statusMap: Record<string, string> = {
    pending: '待处理',
    in_progress: '维修中',
    completed: '已完成',
    cancelled: '已取消'
  }
  return statusMap[status] || '待处理'
}

const getCategoryLabel = (category: string): string => {
  const categoryMap: Record<string, string> = {
    network_repair: '网络维修',
    hardware_repair: '硬件维修',
    software_support: '软件支持',
    other: '其他'
  }
  return categoryMap[category] || '其他'
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
  }
})

watch(offlineDialogVisible, visible => {
  if (!visible) {
    offlineLoading.value = false
    offlineTargetTask.value = null
    offlineForm.inspectionResult = ''
    offlineForm.imagesText = ''
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
      currentTaskType.value = 'repair'
    }
  }
)
</script>

<style scoped lang="scss">
@use '@/styles/variables.scss' as *;
@use '@/styles/mixins.scss' as *;

.repair-task-list {
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

.pagination-wrapper {
  @include flex-center;
  margin-top: $spacing-large;
}

.text-placeholder {
  color: $text-color-placeholder;
}
</style>
