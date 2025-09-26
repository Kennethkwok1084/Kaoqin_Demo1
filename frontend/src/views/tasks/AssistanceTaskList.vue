<template>
  <div class="assistance-task-list">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-content">
        <h1 class="page-title">协助任务管理</h1>
        <p class="page-subtitle">管理和跟踪所有跨部门协助和支援任务</p>
      </div>
      <div class="header-actions">
        <el-button type="primary" :icon="Plus" @click="showCreateDialog">
          新建协助任务
        </el-button>
        <el-button :icon="Upload" @click="showImport">
          导入协助任务
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

    <!-- 协助任务特有的筛选条件 -->
    <el-card class="filter-card" shadow="never">
      <div class="filter-section">
        <div class="filter-row">
          <div class="filter-item">
            <el-input
              v-model="searchQuery"
              placeholder="搜索协助任务标题、协助内容..."
              :prefix-icon="Search"
              clearable
              @input="handleSearch"
            />
          </div>

          <div class="filter-item">
            <el-select
              v-model="filters.status"
              placeholder="协助状态"
              multiple
              collapse-tags
              clearable
              @change="loadTasks"
            >
              <el-option label="待协助" value="pending" />
              <el-option label="协助中" value="in_progress" />
              <el-option label="已完成" value="completed" />
              <el-option label="已暂停" value="on_hold" />
            </el-select>
          </div>

          <div class="filter-item">
            <el-select
              v-model="filters.assistanceType"
              placeholder="协助类型"
              multiple
              collapse-tags
              clearable
              @change="loadTasks"
            >
              <el-option label="技术支持" value="technical_support" />
              <el-option label="人员支援" value="staff_support" />
              <el-option label="设备协助" value="equipment_assistance" />
              <el-option label="培训指导" value="training_guidance" />
              <el-option label="其他协助" value="other_assistance" />
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
              <el-option label="低" value="low" />
              <el-option label="中" value="medium" />
              <el-option label="高" value="high" />
              <el-option label="紧急" value="urgent" />
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

    <!-- 协助任务列表 -->
    <el-card class="table-card" shadow="never">
      <template #header>
        <div class="table-header">
          <div class="table-title">协助任务列表 ({{ pagination.total }})</div>
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
                :type="viewMode === 'kanban' ? 'primary' : 'default'"
                :icon="Grid"
                @click="viewMode = 'kanban'"
              >
                看板
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

          <el-table-column prop="title" label="协助任务" min-width="200" show-overflow-tooltip sortable="custom">
            <template #default="scope">
              <div class="task-title">
                <el-link type="primary" @click="viewTaskDetail(scope.row.id)">
                  {{ scope.row.title }}
                </el-link>
                <div class="task-meta">
                  <el-tag :type="getAssistanceTypeColor(scope.row.assistance_type)" size="small">
                    {{ getAssistanceTypeLabel(scope.row.assistance_type) }}
                  </el-tag>
                  <el-tag :type="getPriorityTagType(scope.row.priority)" size="small">
                    {{ getPriorityLabel(scope.row.priority) }}
                  </el-tag>
                </div>
              </div>
            </template>
          </el-table-column>

          <el-table-column prop="status" label="协助状态" width="100" sortable="custom">
            <template #default="scope">
              <el-tag :type="getStatusTagType(scope.row.status)">
                {{ getStatusLabel(scope.row.status) }}
              </el-tag>
            </template>
          </el-table-column>

          <el-table-column prop="member_name" label="协助人员" width="120" show-overflow-tooltip>
            <template #default="scope">
              <span v-if="scope.row.member_name">{{ scope.row.member_name }}</span>
              <span v-else class="text-placeholder">未分配</span>
            </template>
          </el-table-column>

          <el-table-column prop="estimated_hours" label="预计工时" width="100">
            <template #default="scope">
              <span v-if="scope.row.estimated_hours">{{ scope.row.estimated_hours }}小时</span>
              <span v-else>-</span>
            </template>
          </el-table-column>

          <el-table-column prop="actual_hours" label="实际工时" width="100">
            <template #default="scope">
              <span v-if="scope.row.actual_hours">{{ scope.row.actual_hours }}小时</span>
              <span v-else>-</span>
            </template>
          </el-table-column>

          <el-table-column prop="start_time" label="开始时间" width="120" sortable="custom">
            <template #default="scope">
              {{ scope.row.start_time ? formatDate(scope.row.start_time) : '-' }}
            </template>
          </el-table-column>

          <el-table-column prop="end_time" label="结束时间" width="120">
            <template #default="scope">
              {{ scope.row.end_time ? formatDate(scope.row.end_time) : '-' }}
            </template>
          </el-table-column>

          <el-table-column label="操作" width="200" fixed="right">
            <template #default="scope">
              <div class="table-actions">
                <el-button type="text" size="small" @click="viewTaskDetail(scope.row.id)">
                  详情
                </el-button>
                <el-button type="text" size="small" @click="startAssistance(scope.row)" v-if="scope.row.status === 'pending'">
                  开始协助
                </el-button>
                <el-button type="text" size="small" @click="completeAssistance(scope.row)" v-if="scope.row.status === 'in_progress'">
                  完成协助
                </el-button>
                <el-dropdown @command="command => handleTaskAction(command, scope.row)">
                  <el-button type="text" size="small">
                    更多<el-icon><ArrowDown /></el-icon>
                  </el-button>
                  <template #dropdown>
                    <el-dropdown-menu>
                      <el-dropdown-item command="edit">编辑任务</el-dropdown-item>
                      <el-dropdown-item command="assign">分配人员</el-dropdown-item>
                      <el-dropdown-item command="pause" v-if="scope.row.status === 'in_progress'">暂停协助</el-dropdown-item>
                      <el-dropdown-item command="resume" v-if="scope.row.status === 'on_hold'">恢复协助</el-dropdown-item>
                      <el-dropdown-item command="feedback">查看反馈</el-dropdown-item>
                      <el-dropdown-item command="delete" divided>删除任务</el-dropdown-item>
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

    <!-- Import dialog for assistance tasks -->
    <ImportAssistanceTaskDialog
      v-model="showImportDialog"
      @success="handleImportSuccess"
    />
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
  User,
  Clock
} from '@element-plus/icons-vue'
import { tasksApi } from '@/api/tasks'
import { formatDate as formatDateUtil } from '@/utils/date'
import type { Task, TaskListParams, TaskStats } from '@/types/task'
import TaskFormDialog from '@/components/tasks/TaskFormDialog.vue'
import TaskDetailDialog from '@/components/tasks/TaskDetailDialog.vue'
import ImportAssistanceTaskDialog from '@/components/tasks/ImportAssistanceTaskDialog.vue'

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
const viewMode = ref<'table' | 'kanban'>('table')
const selectedTasks = ref<Task[]>([])

const filters = reactive({
  status: [] as string[],
  assistanceType: [] as string[],
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
  sortBy: 'created_at',
  sortOrder: 'desc' as 'asc' | 'desc'
})

// 对话框状态
const showTaskDialog = ref(false)
const showDetailDialog = ref(false)
const showImportDialog = ref(false)
const currentTask = ref<Task | null>(null)
const currentTaskId = ref<number | null>(null)
const currentTaskType = ref<string | null>(null)

// 统计卡片配置 - 专门针对协助任务
const statsCards = [
  {
    key: 'total' as keyof TaskStats,
    label: '总协助任务',
    icon: Document,
    iconColor: '#409EFF',
    className: 'stat-primary'
  },
  {
    key: 'pending' as keyof TaskStats,
    label: '待协助',
    icon: Clock,
    iconColor: '#909399',
    className: 'stat-default'
  },
  {
    key: 'in_progress' as keyof TaskStats,
    label: '协助中',
    icon: User,
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

// 方法实现
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
        type: ['assistance'], // 固定为协助任务
        search: searchQuery.value || undefined
      }
    }

    const result = await tasksApi.getTasks(params)
    tasks.value = result.items
    pagination.total = result.total
  } catch (error) {
    ElMessage.error('加载协助任务列表失败')
  } finally {
    loading.value = false
  }
}

const loadTaskStats = async () => {
  try {
    const stats = await tasksApi.getTaskStats({ type: ['assistance'] })
    Object.assign(taskStats, stats)
  } catch (error) {
    console.error('加载协助任务统计失败:', error)
  }
}

// 其他方法
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

const handleSortChange = ({ prop, order }: { prop: string; order: string | null }) => {
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
    assistanceType: [],
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

const viewTaskDetail = (taskId: number) => {
  currentTaskId.value = taskId
  currentTaskType.value = 'assistance'
  showDetailDialog.value = true
}

const startAssistance = async (task: Task) => {
  try {
    await tasksApi.startTask(task.id)
    ElMessage.success('协助任务已开始')
    loadTasks()
    loadTaskStats()
  } catch (error) {
    ElMessage.error('开始协助任务失败')
  }
}

const completeAssistance = async (task: Task) => {
  try {
    await tasksApi.completeTask(task.id)
    ElMessage.success('协助任务已完成')
    loadTasks()
    loadTaskStats()
  } catch (error) {
    ElMessage.error('完成协助任务失败')
  }
}

const handleTaskAction = async (command: string, task: Task) => {
  switch (command) {
    case 'edit':
      currentTask.value = task
      showTaskDialog.value = true
      break
    case 'delete':
      await deleteTask(task)
      break
    case 'assign':
      ElMessage.info('分配人员功能开发中...')
      break
    case 'pause':
      await pauseAssistance(task)
      break
    case 'resume':
      await resumeAssistance(task)
      break
    case 'feedback':
      ElMessage.info('查看反馈功能开发中...')
      break
  }
}

const deleteTask = async (task: Task) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除协助任务"${task.title}"吗？此操作不可恢复。`,
      '删除确认',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    await tasksApi.deleteTask(task.id)
    ElMessage.success('协助任务删除成功')
    loadTasks()
    loadTaskStats()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除协助任务失败')
    }
  }
}

const pauseAssistance = async (task: Task) => {
  try {
    await tasksApi.pauseTask(task.id)
    ElMessage.success('协助任务已暂停')
    loadTasks()
    loadTaskStats()
  } catch (error) {
    ElMessage.error('暂停协助任务失败')
  }
}

const resumeAssistance = async (task: Task) => {
  try {
    await tasksApi.resumeTask(task.id)
    ElMessage.success('协助任务已恢复')
    loadTasks()
    loadTaskStats()
  } catch (error) {
    ElMessage.error('恢复协助任务失败')
  }
}

const exportTasks = async () => {
  try {
    await tasksApi.exportTasks({ ...filters, type: ['assistance'] })
    ElMessage.success('协助任务导出成功')
  } catch (error) {
    ElMessage.error('导出协助任务失败')
  }
}

const showImport = () => {
  showImportDialog.value = true
}

const handleTaskFormSuccess = () => {
  loadTasks()
  loadTaskStats()
}

const handleImportSuccess = () => {
  loadTasks()
  loadTaskStats()
}

// 工具方法
const formatDate = (dateString: string): string => {
  if (!dateString) return '-'
  return formatDateUtil(dateString) || '-'
}

const getAssistanceTypeColor = (type: string): string => {
  const typeMap: Record<string, string> = {
    technical_support: 'primary',
    staff_support: 'success',
    equipment_assistance: 'warning',
    training_guidance: 'info',
    other_assistance: 'default'
  }
  return typeMap[type] || 'info'
}

const getAssistanceTypeLabel = (type: string): string => {
  const typeMap: Record<string, string> = {
    technical_support: '技术支持',
    staff_support: '人员支援',
    equipment_assistance: '设备协助',
    training_guidance: '培训指导',
    other_assistance: '其他协助'
  }
  return typeMap[type] || '其他协助'
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
    on_hold: 'default'
  }
  return statusMap[status] || 'info'
}

const getStatusLabel = (status: string): string => {
  const statusMap: Record<string, string> = {
    pending: '待协助',
    in_progress: '协助中',
    completed: '已完成',
    on_hold: '已暂停'
  }
  return statusMap[status] || '待协助'
}

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
</script>

<style scoped lang="scss">
@use '@/styles/variables.scss' as *;
@use '@/styles/mixins.scss' as *;

.assistance-task-list {
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
