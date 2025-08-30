<template>
  <div class="data-import-list">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-left">
        <h2>数据导入</h2>
        <p>批量导入各类业务数据，支持Excel和CSV格式</p>
      </div>
      <div class="header-actions">
        <el-button type="success" @click="showNewImport = true">
          <el-icon><Upload /></el-icon>
          新建导入
        </el-button>
        <el-button type="info" @click="showTemplateManager = true">
          <el-icon><Document /></el-icon>
          模板管理
        </el-button>
        <el-button @click="loadStatistics">
          <el-icon><Refresh /></el-icon>
          刷新
        </el-button>
      </div>
    </div>

    <!-- 统计卡片 -->
    <div class="statistics-cards">
      <el-row :gutter="20">
        <el-col :span="6">
          <el-card class="stat-card">
            <div class="stat-content">
              <div class="stat-value">{{ statistics.totalImports }}</div>
              <div class="stat-label">总导入次数</div>
            </div>
            <div class="stat-icon total">
              <el-icon><DataBoard /></el-icon>
            </div>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card class="stat-card">
            <div class="stat-content">
              <div class="stat-value">{{ statistics.successfulImports }}</div>
              <div class="stat-label">成功导入</div>
            </div>
            <div class="stat-icon success">
              <el-icon><SuccessFilled /></el-icon>
            </div>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card class="stat-card">
            <div class="stat-content">
              <div class="stat-value">
                {{ statistics.totalRowsProcessed.toLocaleString() }}
              </div>
              <div class="stat-label">处理记录数</div>
            </div>
            <div class="stat-icon records">
              <el-icon><Grid /></el-icon>
            </div>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card class="stat-card">
            <div class="stat-content">
              <div class="stat-value">
                {{ statistics.averageProcessingTime.toFixed(1) }}s
              </div>
              <div class="stat-label">平均处理时间</div>
            </div>
            <div class="stat-icon time">
              <el-icon><Timer /></el-icon>
            </div>
          </el-card>
        </el-col>
      </el-row>
    </div>

    <!-- 筛选条件 -->
    <el-card class="filter-card">
      <el-form :model="filters" inline class="filter-form">
        <el-form-item label="状态">
          <el-select
            v-model="filters.status"
            placeholder="选择状态"
            clearable
            style="width: 120px"
          >
            <el-option label="处理中" value="processing" />
            <el-option label="已完成" value="completed" />
            <el-option label="已失败" value="failed" />
            <el-option label="已取消" value="cancelled" />
          </el-select>
        </el-form-item>

        <el-form-item label="模板类型">
          <el-select
            v-model="filters.templateType"
            placeholder="选择类型"
            clearable
            style="width: 150px"
          >
            <el-option label="维修任务" value="repair_tasks" />
            <el-option label="监控任务" value="monitoring_tasks" />
            <el-option label="协助任务" value="assistance_tasks" />
            <el-option label="成员信息" value="members" />
            <el-option label="考勤记录" value="attendance" />
            <el-option label="工时记录" value="work_hours" />
          </el-select>
        </el-form-item>

        <el-form-item label="时间范围">
          <el-date-picker
            v-model="filters.dateRange"
            type="datetimerange"
            range-separator="至"
            start-placeholder="开始时间"
            end-placeholder="结束时间"
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

    <!-- 导入作业表格 -->
    <el-card class="table-card">
      <el-table
        v-loading="loading"
        :data="importJobs"
        stripe
        style="width: 100%"
      >
        <el-table-column
          prop="fileName"
          label="文件名"
          min-width="200"
          show-overflow-tooltip
        />

        <el-table-column prop="templateName" label="模板类型" width="150">
          <template #default="{ row }">
            <el-tag :type="getTemplateTypeColor(row.templateName) as any">
              {{ getTemplateTypeText(row.templateName) }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column prop="status" label="状态" width="120">
          <template #default="{ row }">
            <el-tag :type="getStatusColor(row.status) as any">
              {{ getStatusText(row.status) }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column label="进度" width="200">
          <template #default="{ row }">
            <div class="progress-container">
              <el-progress
                :percentage="row.progress"
                :status="getProgressStatus(row.status)"
                :show-text="false"
                style="width: 100px"
              />
              <span class="progress-text">{{ row.progress }}%</span>
            </div>
          </template>
        </el-table-column>

        <el-table-column label="处理结果" width="180">
          <template #default="{ row }">
            <div class="result-stats">
              <div class="result-item">
                <span class="result-label">总数:</span>
                <span class="result-value">{{ row.totalRows }}</span>
              </div>
              <div class="result-item">
                <span class="result-label success">成功:</span>
                <span class="result-value">{{ row.successRows }}</span>
              </div>
              <div class="result-item" v-if="row.failedRows > 0">
                <span class="result-label error">失败:</span>
                <span class="result-value">{{ row.failedRows }}</span>
              </div>
            </div>
          </template>
        </el-table-column>

        <el-table-column prop="fileSize" label="文件大小" width="100">
          <template #default="{ row }">
            {{ formatFileSize(row.fileSize) }}
          </template>
        </el-table-column>

        <el-table-column prop="createdAt" label="创建时间" width="160">
          <template #default="{ row }">
            {{ formatDateTime(row.createdAt) }}
          </template>
        </el-table-column>

        <el-table-column label="操作" width="250" fixed="right">
          <template #default="{ row }">
            <el-button-group>
              <el-button size="small" @click="viewDetails(row)">
                <el-icon><View /></el-icon>
                详情
              </el-button>
              <el-button
                size="small"
                type="warning"
                @click="cancelJob(row)"
                v-if="row.status === 'processing'"
              >
                <el-icon><Close /></el-icon>
                取消
              </el-button>
              <el-button
                size="small"
                type="info"
                @click="retryJob(row)"
                v-if="row.status === 'failed'"
              >
                <el-icon><Refresh /></el-icon>
                重试
              </el-button>
              <el-button
                size="small"
                type="success"
                @click="downloadReport(row)"
                v-if="row.status === 'completed'"
              >
                <el-icon><Download /></el-icon>
                报告
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

    <!-- 新建导入弹窗 -->
    <ImportWizardDialog
      v-model:visible="showNewImport"
      @success="handleImportSuccess"
    />

    <!-- 模板管理弹窗 -->
    <TemplateManagerDialog
      v-model:visible="showTemplateManager"
      @refresh="loadImportJobs"
    />

    <!-- 导入详情弹窗 -->
    <ImportDetailDialog
      v-model:visible="showDetail"
      :import-job="selectedJob"
      @refresh="loadImportJobs"
    />
  </div>
</template>

/// <reference types="node" />
<script setup lang="ts">
import { ref, reactive, onMounted, onUnmounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Upload,
  Document,
  Refresh,
  DataBoard,
  SuccessFilled,
  Grid,
  Timer,
  Search,
  RefreshLeft,
  View,
  Close,
  Download
} from '@element-plus/icons-vue'
import { dataImportApi } from '@/api/dataImport'
import type {
  ImportJob,
  ImportStatistics,
  ImportFilters
} from '@/types/dataImport'
import ImportWizardDialog from '@/components/dataImport/ImportWizardDialog.vue'
import TemplateManagerDialog from '@/components/dataImport/TemplateManagerDialog.vue'
import ImportDetailDialog from '@/components/dataImport/ImportDetailDialog.vue'

const loading = ref(false)
const importJobs = ref<ImportJob[]>([])
const selectedJob = ref<ImportJob | null>(null)
const progressPolling = ref<NodeJS.Timeout | null>(null)

const showNewImport = ref(false)
const showTemplateManager = ref(false)
const showDetail = ref(false)

const filters = reactive<ImportFilters>({
  status: undefined,
  templateType: undefined,
  dateRange: undefined,
  createdBy: undefined
})

const pagination = reactive({
  page: 1,
  pageSize: 20,
  total: 0
})

const statistics = reactive<ImportStatistics>({
  totalImports: 0,
  successfulImports: 0,
  failedImports: 0,
  totalRowsProcessed: 0,
  averageProcessingTime: 0,
  recentJobs: [],
  topErrors: []
})

onMounted(() => {
  loadImportJobs()
  loadStatistics()
  startProgressPolling()
})

onUnmounted(() => {
  stopProgressPolling()
})

const loadImportJobs = async () => {
  try {
    loading.value = true
    const response = await dataImportApi.getImportJobs(
      pagination.page,
      pagination.pageSize,
      filters
    )
    importJobs.value = response.data
    pagination.total = response.total
  } catch (error) {
    console.error('加载导入作业失败:', error)
    ElMessage.error('加载导入作业失败')
  } finally {
    loading.value = false
  }
}

const loadStatistics = async () => {
  try {
    const data = await dataImportApi.getImportStatistics(filters.dateRange)
    Object.assign(statistics, data)
  } catch (error) {
    console.error('加载统计数据失败:', error)
  }
}

const startProgressPolling = () => {
  progressPolling.value = setInterval(async () => {
    const processingJobs = importJobs.value.filter(
      job => job.status === 'processing'
    )

    for (const job of processingJobs) {
      try {
        const progress = await dataImportApi.getImportProgress(job.id)
        const index = importJobs.value.findIndex(j => j.id === job.id)
        if (index !== -1) {
          importJobs.value[index].progress = progress.progress
          importJobs.value[index].status = progress.status as any
        }
      } catch (error) {
        console.error('获取进度失败:', error)
      }
    }

    // 如果没有处理中的作业，停止轮询
    if (processingJobs.length === 0) {
      stopProgressPolling()
    }
  }, 3000) // 每3秒更新一次
}

const stopProgressPolling = () => {
  if (progressPolling.value) {
    clearInterval(progressPolling.value)
    progressPolling.value = null
  }
}

const handleSearch = () => {
  pagination.page = 1
  loadImportJobs()
  loadStatistics()
}

const handleReset = () => {
  Object.assign(filters, {
    status: undefined,
    templateType: undefined,
    dateRange: undefined,
    createdBy: undefined
  })
  handleSearch()
}

const handlePageChange = (page: number) => {
  pagination.page = page
  loadImportJobs()
}

const handleSizeChange = (size: number) => {
  pagination.pageSize = size
  pagination.page = 1
  loadImportJobs()
}

const viewDetails = (job: ImportJob) => {
  selectedJob.value = job
  showDetail.value = true
}

const cancelJob = async (job: ImportJob) => {
  try {
    await ElMessageBox.confirm('确定要取消这个导入作业吗？', '确认取消', {
      type: 'warning'
    })

    await dataImportApi.cancelImportJob(job.id)
    ElMessage.success('导入作业已取消')
    loadImportJobs()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('取消作业失败:', error)
      ElMessage.error('取消作业失败')
    }
  }
}

const retryJob = async (job: ImportJob) => {
  try {
    await ElMessageBox.confirm('确定要重试这个导入作业吗？', '确认重试', {
      type: 'warning'
    })

    await dataImportApi.retryImportJob(job.id)
    ElMessage.success('导入作业已重新开始')
    loadImportJobs()
    startProgressPolling()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('重试作业失败:', error)
      ElMessage.error('重试作业失败')
    }
  }
}

const downloadReport = async (job: ImportJob) => {
  try {
    const blob = await dataImportApi.downloadImportReport(job.id, 'xlsx')
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `导入报告_${job.fileName}.xlsx`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(url)

    ElMessage.success('报告下载成功')
  } catch (error) {
    console.error('下载报告失败:', error)
    ElMessage.error('下载报告失败')
  }
}

const handleImportSuccess = () => {
  showNewImport.value = false
  loadImportJobs()
  loadStatistics()
  startProgressPolling()
  ElMessage.success('导入作业已创建')
}

const getStatusColor = (status: string) => {
  const colorMap = {
    pending: 'info',
    processing: 'warning',
    completed: 'success',
    failed: 'danger',
    cancelled: 'info'
  }
  return colorMap[status as keyof typeof colorMap] || 'info'
}

const getStatusText = (status: string) => {
  const textMap = {
    pending: '等待中',
    processing: '处理中',
    completed: '已完成',
    failed: '已失败',
    cancelled: '已取消'
  }
  return textMap[status as keyof typeof textMap] || status
}

const getProgressStatus = (status: string) => {
  if (status === 'completed') return 'success'
  if (status === 'failed') return 'exception'
  return undefined
}

const getTemplateTypeColor = (templateName: string) => {
  const colorMap = {
    维修任务: 'danger',
    监控任务: 'warning',
    协助任务: 'success',
    成员信息: 'info',
    考勤记录: 'primary',
    工时记录: 'warning'
  }
  return colorMap[templateName as keyof typeof colorMap] || 'info'
}

const getTemplateTypeText = (templateName: string) => {
  return templateName || '未知类型'
}

const formatFileSize = (bytes: number) => {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

const formatDateTime = (dateStr: string) => {
  return new Date(dateStr).toLocaleString()
}
</script>

<style lang="scss" scoped>
.data-import-list {
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

      &.total {
        background: linear-gradient(45deg, #409eff, #66b3ff);
      }

      &.success {
        background: linear-gradient(45deg, #67c23a, #85ce61);
      }

      &.records {
        background: linear-gradient(45deg, #e6a23c, #f0c94e);
      }

      &.time {
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
  .progress-container {
    display: flex;
    align-items: center;
    gap: 10px;

    .progress-text {
      font-size: 12px;
      color: var(--el-text-color-regular);
      min-width: 30px;
    }
  }

  .result-stats {
    font-size: 12px;

    .result-item {
      display: flex;
      justify-content: space-between;
      margin-bottom: 2px;

      .result-label {
        color: var(--el-text-color-regular);

        &.success {
          color: var(--el-color-success);
        }

        &.error {
          color: var(--el-color-danger);
        }
      }

      .result-value {
        font-weight: bold;
      }
    }
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
    font-size: 12px;
  }
}
</style>
