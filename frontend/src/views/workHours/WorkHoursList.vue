<template>
  <div class="work-hours-list">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-left">
        <h2>工时管理</h2>
        <p>管理和审核员工工时记录</p>
      </div>
      <div class="header-actions">
        <el-button
          type="success"
          @click="recalculateAll"
          :loading="recalculating"
        >
          <el-icon><Refresh /></el-icon>
          重新计算
        </el-button>
        <el-button
          type="primary"
          @click="showBatchReview = true"
          :disabled="!selectedRows.length"
        >
          <el-icon><Check /></el-icon>
          批量审核
        </el-button>
        <el-dropdown @command="handleExport">
          <el-button type="info">
            <el-icon><Download /></el-icon>
            导出数据
            <el-icon class="el-icon--right"><ArrowDown /></el-icon>
          </el-button>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="xlsx">导出Excel</el-dropdown-item>
              <el-dropdown-item command="csv">导出CSV</el-dropdown-item>
              <el-dropdown-item command="pdf">导出PDF</el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </div>
    </div>

    <!-- 统计卡片 -->
    <div class="statistics-cards">
      <el-row :gutter="20">
        <el-col :span="6">
          <el-card class="stat-card">
            <div class="stat-content">
              <div class="stat-value">
                {{ statistics.totalHours.toFixed(1) }}
              </div>
              <div class="stat-label">总工时</div>
            </div>
            <div class="stat-icon hours">
              <el-icon><Timer /></el-icon>
            </div>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card class="stat-card">
            <div class="stat-content">
              <div class="stat-value">{{ statistics.pendingReviews }}</div>
              <div class="stat-label">待审核</div>
            </div>
            <div class="stat-icon pending">
              <el-icon><Clock /></el-icon>
            </div>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card class="stat-card">
            <div class="stat-content">
              <div class="stat-value">
                {{ statistics.efficiency.toFixed(1) }}%
              </div>
              <div class="stat-label">平均效率</div>
            </div>
            <div class="stat-icon efficiency">
              <el-icon><TrendCharts /></el-icon>
            </div>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card class="stat-card">
            <div class="stat-content">
              <div class="stat-value">
                {{ statistics.avgHoursPerTask.toFixed(1) }}
              </div>
              <div class="stat-label">平均工时/任务</div>
            </div>
            <div class="stat-icon average">
              <el-icon><DataAnalysis /></el-icon>
            </div>
          </el-card>
        </el-col>
      </el-row>
    </div>

    <!-- 筛选条件 -->
    <el-card class="filter-card">
      <el-form :model="filters" inline class="filter-form">
        <el-form-item label="成员">
          <el-select
            v-model="filters.memberId"
            placeholder="选择成员"
            clearable
            style="width: 150px"
          >
            <el-option
              v-for="member in members"
              :key="member.id"
              :label="member.name"
              :value="member.id"
            />
          </el-select>
        </el-form-item>

        <el-form-item label="任务类型">
          <el-select
            v-model="filters.taskType"
            placeholder="选择类型"
            clearable
            style="width: 120px"
          >
            <el-option label="维修任务" value="repair" />
            <el-option label="监控任务" value="monitoring" />
            <el-option label="协助任务" value="assistance" />
          </el-select>
        </el-form-item>

        <el-form-item label="审核状态">
          <el-select
            v-model="filters.status"
            placeholder="选择状态"
            clearable
            style="width: 120px"
          >
            <el-option label="待审核" value="pending" />
            <el-option label="已通过" value="approved" />
            <el-option label="已拒绝" value="rejected" />
          </el-select>
        </el-form-item>

        <el-form-item label="时间范围">
          <el-date-picker
            v-model="filters.dateRange"
            type="monthrange"
            range-separator="至"
            start-placeholder="开始月份"
            end-placeholder="结束月份"
            @change="handleSearch"
          />
        </el-form-item>

        <el-form-item>
          <el-button type="primary" @click="handleSearch">
            <el-icon><Search /></el-icon>
            搜索
          </el-button>
          <el-button @click="handleReset">
            <el-icon><RefreshLeft /></el-icon>
            重置
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 工时表格 -->
    <el-card class="table-card">
      <el-table
        v-loading="loading"
        :data="workHours"
        @selection-change="handleSelectionChange"
        stripe
        style="width: 100%"
      >
        <el-table-column type="selection" width="55" />

        <el-table-column prop="memberName" label="成员" width="100" />

        <el-table-column
          prop="taskTitle"
          label="任务标题"
          min-width="200"
          show-overflow-tooltip
        />

        <el-table-column prop="taskType" label="任务类型" width="100">
          <template #default="{ row }">
            <el-tag :type="getTaskTypeColor(row.taskType) as any">
              {{ getTaskTypeText(row.taskType) }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column label="工时详情" width="180">
          <template #default="{ row }">
            <div class="hours-breakdown">
              <div class="hours-item">
                <span>基础: {{ row.baseHours }}h</span>
              </div>
              <div class="hours-item" v-if="row.bonusHours > 0">
                <span class="bonus">奖励: +{{ row.bonusHours }}h</span>
              </div>
              <div class="hours-item" v-if="row.penaltyHours > 0">
                <span class="penalty">惩罚: -{{ row.penaltyHours }}h</span>
              </div>
            </div>
          </template>
        </el-table-column>

        <el-table-column prop="totalHours" label="总工时" width="100">
          <template #default="{ row }">
            <span class="total-hours">{{ row.totalHours }}h</span>
          </template>
        </el-table-column>

        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="getStatusColor(row.status) as any">
              {{ getStatusText(row.status) }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column prop="createdAt" label="创建时间" width="120">
          <template #default="{ row }">
            {{ formatDate(row.createdAt) }}
          </template>
        </el-table-column>

        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button-group>
              <el-button size="small" @click="viewDetails(row)">
                <el-icon><View /></el-icon>
              </el-button>
              <el-button
                size="small"
                type="warning"
                @click="adjustHours(row)"
                :disabled="row.status === 'approved'"
              >
                <el-icon><Edit /></el-icon>
              </el-button>
              <el-button
                size="small"
                type="success"
                @click="reviewHour(row, 'approve')"
                v-if="row.status === 'pending'"
              >
                <el-icon><Check /></el-icon>
              </el-button>
              <el-button
                size="small"
                type="danger"
                @click="reviewHour(row, 'reject')"
                v-if="row.status === 'pending'"
              >
                <el-icon><Close /></el-icon>
              </el-button>
              <el-button
                size="small"
                type="info"
                @click="recalculateTask(row.taskId)"
              >
                <el-icon><Refresh /></el-icon>
              </el-button>
            </el-button-group>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <div class="pagination-wrapper">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.pageSize"
          :total="pagination.total"
          :page-sizes="[10, 20, 50, 100]"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleSizeChange"
          @current-change="handlePageChange"
        />
      </div>
    </el-card>

    <!-- 工时详情弹窗 -->
    <WorkHourDetailDialog
      v-model:visible="showDetail"
      :work-hour="selectedWorkHour"
      @refresh="loadWorkHours"
    />

    <!-- 工时调整弹窗 -->
    <WorkHourAdjustDialog
      v-model:visible="showAdjust"
      :work-hour="selectedWorkHour"
      @success="handleAdjustSuccess"
    />

    <!-- 工时审核弹窗 -->
    <WorkHourReviewDialog
      v-model:visible="showReview"
      :work-hour="selectedWorkHour"
      :review-type="reviewType"
      @success="handleReviewSuccess"
    />

    <!-- 批量审核弹窗 -->
    <BatchReviewDialog
      v-model:visible="showBatchReview"
      :work-hours="selectedRows"
      @success="handleBatchReviewSuccess"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Refresh,
  Check,
  Download,
  ArrowDown,
  Timer,
  Clock,
  TrendCharts,
  DataAnalysis,
  Search,
  RefreshLeft,
  View,
  Edit,
  Close
} from '@element-plus/icons-vue'
import { workHoursApi } from '@/api/workHours'
import { MembersApi } from '@/api/members'
import type {
  WorkHour,
  WorkHourFilters,
  WorkHourStatistics
} from '@/types/workHours'
import type { Member } from '@/types/member'
import WorkHourDetailDialog from '@/components/workHours/WorkHourDetailDialog.vue'
import WorkHourAdjustDialog from '@/components/workHours/WorkHourAdjustDialog.vue'
import WorkHourReviewDialog from '@/components/workHours/WorkHourReviewDialog.vue'
import BatchReviewDialog from '@/components/workHours/BatchReviewDialog.vue'

const loading = ref(false)
const recalculating = ref(false)
const workHours = ref<WorkHour[]>([])
const members = ref<Member[]>([])
const selectedRows = ref<WorkHour[]>([])
const selectedWorkHour = ref<WorkHour | null>(null)

const showDetail = ref(false)
const showAdjust = ref(false)
const showReview = ref(false)
const showBatchReview = ref(false)
const reviewType = ref<'approve' | 'reject'>('approve')

const filters = reactive<WorkHourFilters>({
  memberId: undefined,
  taskType: undefined,
  status: undefined,
  dateRange: undefined
})

const pagination = reactive({
  page: 1,
  pageSize: 20,
  total: 0
})

const statistics = reactive<WorkHourStatistics>({
  totalMembers: 0,
  totalHours: 0,
  totalTasks: 0,
  avgHoursPerTask: 0,
  avgHoursPerMember: 0,
  pendingReviews: 0,
  approvedHours: 0,
  rejectedHours: 0,
  efficiency: 0
})

onMounted(() => {
  loadWorkHours()
  loadMembers()
  loadStatistics()
})

const loadWorkHours = async () => {
  try {
    loading.value = true
    const response = await workHoursApi.getWorkHours(
      pagination.page,
      pagination.pageSize,
      filters
    )
    workHours.value = response.data
    pagination.total = response.total
  } catch (error) {
    console.error('加载工时数据失败:', error)
    ElMessage.error('加载工时数据失败')
  } finally {
    loading.value = false
  }
}

const loadMembers = async () => {
  try {
    const response = await MembersApi.getMembers({ page: 1, page_size: 1000 })
    members.value = response.data
  } catch (error) {
    console.error('加载成员列表失败:', error)
  }
}

const loadStatistics = async () => {
  try {
    const data = await workHoursApi.getWorkHourStatistics(filters)
    Object.assign(statistics, data)
  } catch (error) {
    console.error('加载统计数据失败:', error)
  }
}

const handleSearch = () => {
  pagination.page = 1
  loadWorkHours()
  loadStatistics()
}

const handleReset = () => {
  Object.assign(filters, {
    memberId: undefined,
    taskType: undefined,
    status: undefined,
    dateRange: undefined
  })
  handleSearch()
}

const handlePageChange = (page: number) => {
  pagination.page = page
  loadWorkHours()
}

const handleSizeChange = (size: number) => {
  pagination.pageSize = size
  pagination.page = 1
  loadWorkHours()
}

const handleSelectionChange = (selection: WorkHour[]) => {
  selectedRows.value = selection
}

const viewDetails = (workHour: WorkHour) => {
  selectedWorkHour.value = workHour
  showDetail.value = true
}

const adjustHours = (workHour: WorkHour) => {
  selectedWorkHour.value = workHour
  showAdjust.value = true
}

const reviewHour = (workHour: WorkHour, type: 'approve' | 'reject') => {
  selectedWorkHour.value = workHour
  reviewType.value = type
  showReview.value = true
}

const recalculateTask = async (taskId: number) => {
  try {
    await ElMessageBox.confirm('确定要重新计算该任务的工时吗？', '确认操作', {
      type: 'warning'
    })

    const result = await workHoursApi.recalculateTaskWorkHours(taskId)

    if (result.success) {
      ElMessage.success('工时重新计算成功')
      loadWorkHours()
      loadStatistics()
    } else {
      ElMessage.warning(result.message || '工时计算失败')
    }
  } catch (error) {
    if (error !== 'cancel') {
      console.error('重新计算工时失败:', error)
      ElMessage.error('重新计算工时失败')
    }
  }
}

const recalculateAll = async () => {
  try {
    await ElMessageBox.confirm(
      '确定要重新计算所有工时吗？这可能需要一些时间。',
      '确认操作',
      {
        type: 'warning'
      }
    )

    recalculating.value = true
    const results = await workHoursApi.recalculateWorkHours({
      taskIds: [],
      recalculateAll: true,
      applyNewRules: true
    })

    const successCount = results.filter(r => r.success).length
    const failedCount = results.length - successCount

    ElMessage.success(
      `工时重新计算完成：成功 ${successCount} 个，失败 ${failedCount} 个`
    )
    loadWorkHours()
    loadStatistics()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('批量重新计算工时失败:', error)
      ElMessage.error('批量重新计算工时失败')
    }
  } finally {
    recalculating.value = false
  }
}

const handleExport = async (format: string) => {
  try {
    const blob = await workHoursApi.exportWorkHours({
      format: format as 'xlsx' | 'csv' | 'pdf',
      dateRange: filters.dateRange || [new Date(2024, 0, 1), new Date()],
      includeDetails: true,
      includeSummary: true,
      includeCharts: format === 'pdf',
      filters
    })

    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `工时数据.${format}`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(url)

    ElMessage.success('数据导出成功')
  } catch (error) {
    console.error('导出数据失败:', error)
    ElMessage.error('导出数据失败')
  }
}

const handleAdjustSuccess = () => {
  showAdjust.value = false
  loadWorkHours()
  loadStatistics()
  ElMessage.success('工时调整成功')
}

const handleReviewSuccess = () => {
  showReview.value = false
  loadWorkHours()
  loadStatistics()
  ElMessage.success('工时审核成功')
}

const handleBatchReviewSuccess = () => {
  showBatchReview.value = false
  selectedRows.value = []
  loadWorkHours()
  loadStatistics()
  ElMessage.success('批量审核成功')
}

const getTaskTypeColor = (type: string) => {
  const colorMap = {
    repair: 'danger',
    monitoring: 'warning',
    assistance: 'success'
  }
  return colorMap[type as keyof typeof colorMap] || 'info'
}

const getTaskTypeText = (type: string) => {
  const textMap = {
    repair: '维修',
    monitoring: '监控',
    assistance: '协助'
  }
  return textMap[type as keyof typeof textMap] || type
}

const getStatusColor = (status: string) => {
  const colorMap = {
    pending: 'warning',
    approved: 'success',
    rejected: 'danger'
  }
  return colorMap[status as keyof typeof colorMap] || 'info'
}

const getStatusText = (status: string) => {
  const textMap = {
    pending: '待审核',
    approved: '已通过',
    rejected: '已拒绝'
  }
  return textMap[status as keyof typeof textMap] || status
}

const formatDate = (dateStr: string) => {
  return new Date(dateStr).toLocaleDateString()
}
</script>

<style lang="scss" scoped>
.work-hours-list {
  padding: 20px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;

  .header-left {
    h2 {
      margin: 0 0 8px 0;
      color: var(--el-text-color-primary);
    }

    p {
      margin: 0;
      color: var(--el-text-color-regular);
      font-size: 14px;
    }
  }

  .header-actions {
    display: flex;
    gap: 10px;
  }
}

.statistics-cards {
  margin-bottom: 20px;

  .stat-card {
    :deep(.el-card__body) {
      padding: 20px;
      display: flex;
      justify-content: space-between;
      align-items: center;
    }

    .stat-content {
      .stat-value {
        font-size: 28px;
        font-weight: bold;
        color: var(--el-text-color-primary);
        margin-bottom: 5px;
      }

      .stat-label {
        font-size: 14px;
        color: var(--el-text-color-regular);
      }
    }

    .stat-icon {
      width: 50px;
      height: 50px;
      border-radius: 50%;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 24px;
      color: white;

      &.hours {
        background: linear-gradient(45deg, #409eff, #66b3ff);
      }

      &.pending {
        background: linear-gradient(45deg, #e6a23c, #f0c94e);
      }

      &.efficiency {
        background: linear-gradient(45deg, #67c23a, #85ce61);
      }

      &.average {
        background: linear-gradient(45deg, #909399, #b1b3b8);
      }
    }
  }
}

.filter-card {
  margin-bottom: 20px;

  .filter-form {
    :deep(.el-form-item) {
      margin-bottom: 0;
    }
  }
}

.table-card {
  .hours-breakdown {
    font-size: 12px;

    .hours-item {
      margin-bottom: 2px;

      .bonus {
        color: var(--el-color-success);
      }

      .penalty {
        color: var(--el-color-danger);
      }
    }
  }

  .total-hours {
    font-weight: bold;
    font-size: 16px;
    color: var(--el-color-primary);
  }

  .pagination-wrapper {
    margin-top: 20px;
    display: flex;
    justify-content: center;
  }
}

:deep(.el-button-group) {
  .el-button {
    padding: 5px 8px;
  }
}
</style>
