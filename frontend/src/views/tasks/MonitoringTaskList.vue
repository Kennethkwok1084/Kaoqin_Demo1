<template>
  <div class="monitoring-task-list">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-content">
        <h1 class="page-title">监控任务管理</h1>
        <p class="page-subtitle">管理和跟踪所有日常巡检和监控任务</p>
      </div>
      <div class="header-actions">
        <el-button type="primary" :icon="Plus" @click="showCreateDialog">
          新建监控任务
        </el-button>
        <el-button :icon="Upload" @click="showImportDialog">
          导入监控任务
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

    <!-- 监控任务特有的筛选条件 -->
    <el-card class="filter-card" shadow="never">
      <div class="filter-section">
        <div class="filter-row">
          <div class="filter-item">
            <el-input
              v-model="searchQuery"
              placeholder="搜索监控任务名称、巡检地点..."
              :prefix-icon="Search"
              clearable
              @input="handleSearch"
            />
          </div>

          <div class="filter-item">
            <el-select
              v-model="filters.status"
              placeholder="巡检状态"
              multiple
              collapse-tags
              clearable
              @change="loadTasks"
            >
              <el-option label="待巡检" value="pending" />
              <el-option label="巡检中" value="in_progress" />
              <el-option label="已完成" value="completed" />
              <el-option label="异常" value="exception" />
            </el-select>
          </div>

          <div class="filter-item">
            <el-select
              v-model="filters.monitoringType"
              placeholder="监控类型"
              multiple
              collapse-tags
              clearable
              @change="loadTasks"
            >
              <el-option label="设备巡检" value="device_inspection" />
              <el-option label="网络监控" value="network_monitoring" />
              <el-option label="环境检查" value="environment_check" />
              <el-option label="安全巡查" value="security_patrol" />
            </el-select>
          </div>

          <div class="filter-item">
            <el-select
              v-model="filters.frequency"
              placeholder="巡检频率"
              clearable
              @change="loadTasks"
            >
              <el-option label="每日" value="daily" />
              <el-option label="每周" value="weekly" />
              <el-option label="每月" value="monthly" />
              <el-option label="临时" value="ad_hoc" />
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

    <!-- 监控任务列表 -->
    <el-card class="table-card" shadow="never">
      <template #header>
        <div class="table-header">
          <div class="table-title">监控任务列表 ({{ pagination.total }})</div>
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
                :type="viewMode === 'calendar' ? 'primary' : 'default'"
                :icon="Calendar"
                @click="viewMode = 'calendar'"
              >
                日历
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

          <el-table-column prop="title" label="监控任务" min-width="200" show-overflow-tooltip sortable="custom">
            <template #default="scope">
              <div class="task-title">
                <el-link type="primary" @click="viewTaskDetail(scope.row.id)">
                  {{ scope.row.title }}
                </el-link>
                <div class="task-meta">
                  <el-tag :type="getMonitoringTypeColor(scope.row.monitoring_type)" size="small">
                    {{ getMonitoringTypeLabel(scope.row.monitoring_type) }}
                  </el-tag>
                  <el-tag type="info" size="small">
                    {{ getFrequencyLabel(scope.row.frequency) }}
                  </el-tag>
                </div>
              </div>
            </template>
          </el-table-column>

          <el-table-column prop="status" label="巡检状态" width="100" sortable="custom">
            <template #default="scope">
              <el-tag :type="getStatusTagType(scope.row.status)">
                {{ getStatusLabel(scope.row.status) }}
              </el-tag>
            </template>
          </el-table-column>

          <el-table-column prop="member_name" label="负责人" width="120" show-overflow-tooltip>
            <template #default="scope">
              <span v-if="scope.row.member_name">{{ scope.row.member_name }}</span>
              <span v-else class="text-placeholder">未分配</span>
            </template>
          </el-table-column>

          <el-table-column prop="location" label="巡检地点" width="150" show-overflow-tooltip />

          <el-table-column prop="inspection_items" label="巡检项目" width="200" show-overflow-tooltip>
            <template #default="scope">
              <span v-if="scope.row.inspection_items">
                {{ scope.row.inspection_items.slice(0, 3).join(', ') }}
                <span v-if="scope.row.inspection_items.length > 3">...</span>
              </span>
              <span v-else>-</span>
            </template>
          </el-table-column>

          <el-table-column prop="scheduled_time" label="计划时间" width="120" sortable="custom">
            <template #default="scope">
              {{ formatDate(scope.row.scheduled_time) }}
            </template>
          </el-table-column>

          <el-table-column prop="actual_duration" label="实际用时" width="100">
            <template #default="scope">
              <span v-if="scope.row.actual_duration">{{ scope.row.actual_duration }}分钟</span>
              <span v-else>-</span>
            </template>
          </el-table-column>

          <el-table-column prop="completion_rate" label="完成率" width="100">
            <template #default="scope">
              <el-progress
                :percentage="scope.row.completion_rate || 0"
                :color="getProgressColor(scope.row.completion_rate || 0)"
                :show-text="false"
              />
              <span class="progress-text">{{ scope.row.completion_rate || 0 }}%</span>
            </template>
          </el-table-column>

          <el-table-column label="操作" width="200" fixed="right">
            <template #default="scope">
              <div class="table-actions">
                <el-button type="text" size="small" @click="viewTaskDetail(scope.row.id)">
                  详情
                </el-button>
                <el-button type="text" size="small" @click="startInspection(scope.row)" v-if="scope.row.status === 'pending'">
                  开始巡检
                </el-button>
                <el-button type="text" size="small" @click="submitReport(scope.row)" v-if="scope.row.status === 'in_progress'">
                  提交报告
                </el-button>
                <el-dropdown @command="command => handleTaskAction(command, scope.row)">
                  <el-button type="text" size="small">
                    更多<el-icon><ArrowDown /></el-icon>
                  </el-button>
                  <template #dropdown>
                    <el-dropdown-menu>
                      <el-dropdown-item command="edit">编辑任务</el-dropdown-item>
                      <el-dropdown-item command="reschedule">重新安排</el-dropdown-item>
                      <el-dropdown-item command="clone">复制任务</el-dropdown-item>
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
      @updated="loadTasks"
    />

    <ImportTaskDialog
      v-model="showImportDialog"
      @success="handleImportSuccess"
    />

    <el-dialog
      v-model="reportDialogVisible"
      title="提交巡检报告"
      width="520px"
    >
      <el-form label-width="110px">
        <el-form-item label="巡检记录">
          <el-input
            v-model="reportForm.inspectionNotes"
            type="textarea"
            :rows="4"
            placeholder="填写本次巡检发现及处理情况"
          />
        </el-form-item>
        <el-form-item label="检查设备">
          <el-input
            v-model="reportForm.equipmentText"
            type="textarea"
            :rows="3"
            placeholder="可输入多个设备名称，换行或逗号分隔"
          />
        </el-form-item>
        <el-form-item label="发现问题">
          <el-input
            v-model="reportForm.issuesText"
            type="textarea"
            :rows="3"
            placeholder="记录发现的问题，如无可留空"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="reportDialogVisible = false">取消</el-button>
          <el-button type="primary" :loading="reportLoading" @click="confirmSubmitReport">
            提交
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
  Download,
  List,
  Calendar,
  ArrowDown,
  Document,
  CircleCheck,
  Warning,
  Monitor,
  Clock
} from '@element-plus/icons-vue'
import { tasksApi } from '@/api/tasks'
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
const dateRange = ref<[string, string] | null>(null)
const viewMode = ref<'table' | 'calendar'>('table')
const selectedTasks = ref<Task[]>([])

const filters = reactive({
  status: [] as string[],
  monitoringType: [] as string[],
  frequency: '' as string,
  assigneeId: undefined as number | undefined,
  dateRange: undefined as [string, string] | undefined
})

const pagination = reactive({
  page: 1,
  pageSize: 20,
  total: 0
})

const sortConfig = reactive({
  sortBy: 'scheduled_time',
  sortOrder: 'asc' as 'asc' | 'desc'
})

// 对话框状态
const showTaskDialog = ref(false)
const showDetailDialog = ref(false)
const showImportDialog = ref(false)
const currentTask = ref<Task | null>(null)
const currentTaskId = ref<number | null>(null)

const reportDialogVisible = ref(false)
const reportLoading = ref(false)
const reportTargetTask = ref<Task | null>(null)
const reportForm = reactive({
  inspectionNotes: '',
  equipmentText: '',
  issuesText: ''
})

// 统计卡片配置 - 专门针对监控任务
const statsCards = [
  {
    key: 'total' as keyof TaskStats,
    label: '总监控任务',
    icon: Document,
    iconColor: '#409EFF',
    className: 'stat-primary'
  },
  {
    key: 'pending' as keyof TaskStats,
    label: '待巡检',
    icon: Clock,
    iconColor: '#909399',
    className: 'stat-default'
  },
  {
    key: 'in_progress' as keyof TaskStats,
    label: '巡检中',
    icon: Monitor,
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
        type: ['monitoring'], // 固定为监控任务
        search: searchQuery.value || undefined
      }
    }

    const result = await tasksApi.getTasks(params)
    tasks.value = result.items
    pagination.total = result.total
  } catch (error) {
    ElMessage.error('加载监控任务列表失败')
  } finally {
    loading.value = false
  }
}

const loadTaskStats = async () => {
  try {
    const stats = await tasksApi.getTaskStats({ type: ['monitoring'] })
    Object.assign(taskStats, stats)
  } catch (error) {
    console.error('加载监控任务统计失败:', error)
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
    sortConfig.sortBy = 'scheduled_time'
    sortConfig.sortOrder = 'asc'
  }
  loadTasks()
}

const resetFilters = () => {
  Object.assign(filters, {
    status: [],
    monitoringType: [],
    frequency: '',
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

const handleImportSuccess = () => {
  loadTasks()
  loadTaskStats()
}

const viewTaskDetail = (taskId: number) => {
  currentTaskId.value = taskId
  showDetailDialog.value = true
}

const startInspection = async (task: Task) => {
  try {
    await tasksApi.startTask(task.id)
    ElMessage.success('巡检任务已开始')
    loadTasks()
    loadTaskStats()
  } catch (error) {
    ElMessage.error('开始巡检任务失败')
  }
}

const submitReport = (task: Task) => {
  reportTargetTask.value = task
  reportForm.inspectionNotes = ''
  reportForm.equipmentText = ''
  reportForm.issuesText = ''
  reportDialogVisible.value = true
}

const confirmSubmitReport = async () => {
  if (!reportTargetTask.value) return
  try {
    reportLoading.value = true

    const equipmentChecked = reportForm.equipmentText
      .split(/\n|,/)
      .map(item => item.trim())
      .filter(Boolean)

    const issuesFound = reportForm.issuesText
      .split(/\n|,/)
      .map(item => item.trim())
      .filter(Boolean)

    await tasksApi.completeMonitoringInspection(reportTargetTask.value.id, {
      inspection_notes: reportForm.inspectionNotes.trim() || undefined,
      equipment_checked: equipmentChecked.length > 0 ? equipmentChecked : undefined,
      issues_found: issuesFound.length > 0 ? issuesFound : undefined
    })

    ElMessage.success('巡检报告提交成功')
    reportDialogVisible.value = false
    await loadTasks()
    await loadTaskStats()
  } catch (error) {
    console.error('提交巡检报告失败:', error)
    ElMessage.error('提交巡检报告失败，请稍后重试')
  } finally {
    reportLoading.value = false
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
    case 'reschedule':
      ElMessage.info('重新安排功能开发中...')
      break
    case 'clone':
      ElMessage.info('复制任务功能开发中...')
      break
  }
}

const deleteTask = async (task: Task) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除监控任务"${task.title}"吗？此操作不可恢复。`,
      '删除确认',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    await tasksApi.deleteTask(task.id)
    ElMessage.success('监控任务删除成功')
    loadTasks()
    loadTaskStats()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除监控任务失败')
    }
  }
}

const exportTasks = async () => {
  try {
    await tasksApi.exportTasks({ ...filters, type: ['monitoring'] })
    ElMessage.success('监控任务导出成功')
  } catch (error) {
    ElMessage.error('导出监控任务失败')
  }
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

const getMonitoringTypeColor = (type: string): string => {
  const typeMap: Record<string, string> = {
    device_inspection: 'primary',
    network_monitoring: 'success',
    environment_check: 'warning',
    security_patrol: 'danger'
  }
  return typeMap[type] || 'info'
}

const getMonitoringTypeLabel = (type: string): string => {
  const typeMap: Record<string, string> = {
    device_inspection: '设备巡检',
    network_monitoring: '网络监控',
    environment_check: '环境检查',
    security_patrol: '安全巡查'
  }
  return typeMap[type] || '其他'
}

const getFrequencyLabel = (frequency: string): string => {
  const frequencyMap: Record<string, string> = {
    daily: '每日',
    weekly: '每周',
    monthly: '每月',
    ad_hoc: '临时'
  }
  return frequencyMap[frequency] || '临时'
}

const getStatusTagType = (status: string): string => {
  const statusMap: Record<string, string> = {
    pending: 'info',
    in_progress: 'warning',
    completed: 'success',
    exception: 'danger'
  }
  return statusMap[status] || 'info'
}

const getStatusLabel = (status: string): string => {
  const statusMap: Record<string, string> = {
    pending: '待巡检',
    in_progress: '巡检中',
    completed: '已完成',
    exception: '异常'
  }
  return statusMap[status] || '待巡检'
}

const getProgressColor = (percentage: number): string => {
  if (percentage >= 90) return '#67C23A'
  if (percentage >= 70) return '#E6A23C'
  return '#F56C6C'
}

watch(reportDialogVisible, visible => {
  if (!visible) {
    reportLoading.value = false
    reportTargetTask.value = null
    reportForm.inspectionNotes = ''
    reportForm.equipmentText = ''
    reportForm.issuesText = ''
  }
})

// 生命周期
onMounted(() => {
  loadTasks()
  loadTaskStats()
})
</script>

<style scoped lang="scss">
@use '@/styles/variables.scss' as *;
@use '@/styles/mixins.scss' as *;

.monitoring-task-list {
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

.progress-text {
  font-size: $font-size-extra-small;
  color: $text-color-secondary;
  margin-left: $spacing-extra-small;
}

.pagination-wrapper {
  @include flex-center;
  margin-top: $spacing-large;
}

.text-placeholder {
  color: $text-color-placeholder;
}
</style>
