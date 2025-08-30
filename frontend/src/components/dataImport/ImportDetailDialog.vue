<template>
  <el-dialog
    v-model="dialogVisible"
    title="导入详情"
    width="800px"
    @close="handleClose"
  >
    <div class="import-detail" v-if="importJob">
      <!-- 基本信息 -->
      <el-card class="info-card">
        <template #header>
          <span>基本信息</span>
        </template>

        <el-descriptions :column="2" border>
          <el-descriptions-item label="文件名">
            {{ importJob.fileName }}
          </el-descriptions-item>
          <el-descriptions-item label="文件大小">
            {{ formatFileSize(importJob.fileSize) }}
          </el-descriptions-item>
          <el-descriptions-item label="模板类型">
            <el-tag :type="getTemplateTypeColor(importJob.templateName) as any">
              {{ importJob.templateName }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="状态">
            <el-tag :type="getStatusColor(importJob.status) as any">
              {{ getStatusText(importJob.status) }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="创建时间">
            {{ formatDateTime(importJob.createdAt) }}
          </el-descriptions-item>
          <el-descriptions-item label="创建人">
            {{ importJob.createdBy }}
          </el-descriptions-item>
        </el-descriptions>
      </el-card>

      <!-- 处理进度 -->
      <el-card class="progress-card">
        <template #header>
          <span>处理进度</span>
        </template>

        <div class="progress-section">
          <el-progress
            :percentage="Number(importJob.progress) || 0"
            :status="getProgressStatus(importJob.status)"
            :stroke-width="20"
          />

          <div class="progress-stats">
            <div class="stat-item">
              <span class="label">总记录数:</span>
              <span class="value">{{ importJob.totalRows }}</span>
            </div>
            <div class="stat-item">
              <span class="label">成功:</span>
              <span class="value success">{{
                importJob.successRows || 0
              }}</span>
            </div>
            <div class="stat-item">
              <span class="label">失败:</span>
              <span class="value error">{{ importJob.failedRows || 0 }}</span>
            </div>
          </div>
        </div>

        <div v-if="importJob.startTime" class="time-info">
          <div class="time-item">
            <span class="label">开始时间:</span>
            <span class="value">{{ formatDateTime(importJob.startTime) }}</span>
          </div>
          <div v-if="importJob.endTime" class="time-item">
            <span class="label">结束时间:</span>
            <span class="value">{{ formatDateTime(importJob.endTime) }}</span>
          </div>
          <div v-if="importJob.endTime" class="time-item">
            <span class="label">处理耗时:</span>
            <span class="value">{{ getProcessingTime() }}</span>
          </div>
        </div>
      </el-card>

      <!-- 错误信息 -->
      <el-card
        v-if="
          (importJob.validationErrors && importJob.validationErrors.length) ||
          (importJob.processingErrors && importJob.processingErrors.length)
        "
        class="errors-card"
      >
        <template #header>
          <span>错误信息</span>
        </template>

        <el-tabs v-model="errorTab">
          <el-tab-pane
            v-if="importJob.validationErrors.length"
            :label="`验证错误 (${importJob.validationErrors?.length || 0})`"
            name="validation"
          >
            <div class="error-list">
              <div
                v-for="(error, index) in (
                  importJob.validationErrors || []
                ).slice(0, 20)"
                :key="index"
                class="error-item"
              >
                <div class="error-header">
                  <span class="error-row">第{{ error.row }}行</span>
                  <span class="error-field">{{ error.field }}</span>
                  <el-tag
                    :type="error.severity === 'error' ? 'danger' : 'warning'"
                    size="small"
                  >
                    {{ error.severity === 'error' ? '错误' : '警告' }}
                  </el-tag>
                </div>
                <div class="error-message">{{ error.error }}</div>
                <div class="error-value">值: {{ error.value }}</div>
              </div>
              <div
                v-if="(importJob.validationErrors?.length || 0) > 20"
                class="more-errors"
              >
                还有
                {{ (importJob.validationErrors?.length || 0) - 20 }} 个错误...
              </div>
            </div>
          </el-tab-pane>

          <el-tab-pane
            v-if="importJob.processingErrors.length"
            :label="`处理错误 (${importJob.processingErrors?.length || 0})`"
            name="processing"
          >
            <div class="error-list">
              <div
                v-for="(error, index) in (
                  importJob.processingErrors || []
                ).slice(0, 20)"
                :key="index"
                class="error-item"
              >
                <div class="error-header">
                  <span class="error-row">第{{ error.row }}行</span>
                  <span class="error-code">{{ error.errorCode }}</span>
                  <el-tag type="danger" size="small">处理错误</el-tag>
                </div>
                <div class="error-message">{{ error.error }}</div>
                <div class="error-data">
                  数据: {{ JSON.stringify(error.data, null, 2) }}
                </div>
              </div>
              <div
                v-if="(importJob.processingErrors?.length || 0) > 20"
                class="more-errors"
              >
                还有
                {{ (importJob.processingErrors?.length || 0) - 20 }} 个错误...
              </div>
            </div>
          </el-tab-pane>
        </el-tabs>
      </el-card>

      <!-- 操作按钮 -->
      <div class="action-buttons">
        <el-button
          v-if="importJob.status === 'processing'"
          type="warning"
          @click="cancelImport"
        >
          <el-icon><Close /></el-icon>
          取消导入
        </el-button>
        <el-button
          v-if="importJob.status === 'failed'"
          type="info"
          @click="retryImport"
        >
          <el-icon><Refresh /></el-icon>
          重试导入
        </el-button>
        <el-button
          v-if="importJob.status === 'completed'"
          type="success"
          @click="downloadReport"
        >
          <el-icon><Download /></el-icon>
          下载报告
        </el-button>
      </div>
    </div>

    <template #footer>
      <div class="dialog-footer">
        <el-button @click="handleClose">关闭</el-button>
        <el-button type="primary" @click="refreshDetail" :loading="refreshing">
          <el-icon><Refresh /></el-icon>
          刷新
        </el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Close, Refresh, Download } from '@element-plus/icons-vue'
import { dataImportApi } from '@/api/dataImport'
import type { ImportJob } from '@/types/dataImport'

interface Props {
  visible: boolean
  importJob?: ImportJob | null
}

interface Emits {
  (e: 'update:visible', value: boolean): void
  (e: 'refresh'): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

const dialogVisible = ref(false)
const refreshing = ref(false)
const errorTab = ref('validation')

watch(
  () => props.visible,
  visible => {
    dialogVisible.value = visible
  }
)

watch(dialogVisible, visible => {
  emit('update:visible', visible)
})

const refreshDetail = async () => {
  if (!props.importJob) return

  try {
    refreshing.value = true
    // 这里可以重新获取导入作业详情
    emit('refresh')
    ElMessage.success('详情已刷新')
  } catch (error) {
    console.error('刷新详情失败:', error)
    ElMessage.error('刷新详情失败')
  } finally {
    refreshing.value = false
  }
}

const cancelImport = async () => {
  if (!props.importJob) return

  try {
    await ElMessageBox.confirm('确定要取消这个导入作业吗？', '确认取消', {
      type: 'warning'
    })

    await dataImportApi.cancelImportJob(props.importJob.id)
    ElMessage.success('导入作业已取消')
    emit('refresh')
  } catch (error) {
    if (error !== 'cancel') {
      console.error('取消导入失败:', error)
      ElMessage.error('取消导入失败')
    }
  }
}

const retryImport = async () => {
  if (!props.importJob) return

  try {
    await ElMessageBox.confirm('确定要重试这个导入作业吗？', '确认重试', {
      type: 'warning'
    })

    await dataImportApi.retryImportJob(props.importJob.id)
    ElMessage.success('导入作业已重新开始')
    emit('refresh')
  } catch (error) {
    if (error !== 'cancel') {
      console.error('重试导入失败:', error)
      ElMessage.error('重试导入失败')
    }
  }
}

const downloadReport = async () => {
  if (!props.importJob) return

  try {
    const blob = await dataImportApi.downloadImportReport(
      props.importJob.id,
      'xlsx'
    )
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `导入报告_${props.importJob.fileName}.xlsx`
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

const handleClose = () => {
  dialogVisible.value = false
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

const getProcessingTime = () => {
  if (!props.importJob?.startTime || !props.importJob?.endTime) return ''

  const start = new Date(props.importJob.startTime)
  const end = new Date(props.importJob.endTime)
  const diff = end.getTime() - start.getTime()

  const seconds = Math.floor(diff / 1000)
  const minutes = Math.floor(seconds / 60)
  const hours = Math.floor(minutes / 60)

  if (hours > 0) {
    return `${hours}小时${minutes % 60}分钟${seconds % 60}秒`
  } else if (minutes > 0) {
    return `${minutes}分钟${seconds % 60}秒`
  } else {
    return `${seconds}秒`
  }
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
.import-detail {
  .info-card,
  .progress-card,
  .errors-card {
    margin-bottom: 20px;

    &:last-child {
      margin-bottom: 0;
    }
  }

  .progress-section {
    .progress-stats {
      display: flex;
      justify-content: space-around;
      margin-top: 20px;

      .stat-item {
        display: flex;
        flex-direction: column;
        align-items: center;

        .label {
          font-size: 12px;
          color: var(--el-text-color-regular);
        }

        .value {
          font-size: 18px;
          font-weight: bold;
          margin-top: 5px;

          &.success {
            color: var(--el-color-success);
          }

          &.error {
            color: var(--el-color-danger);
          }
        }
      }
    }
  }

  .time-info {
    margin-top: 20px;
    padding-top: 20px;
    border-top: 1px solid var(--el-border-color-lighter);

    .time-item {
      display: flex;
      justify-content: space-between;
      margin-bottom: 8px;

      .label {
        color: var(--el-text-color-regular);
      }

      .value {
        font-weight: 500;
      }
    }
  }

  .error-list {
    max-height: 400px;
    overflow-y: auto;

    .error-item {
      border: 1px solid var(--el-border-color-lighter);
      border-radius: 6px;
      padding: 15px;
      margin-bottom: 10px;

      .error-header {
        display: flex;
        align-items: center;
        gap: 10px;
        margin-bottom: 8px;

        .error-row,
        .error-field,
        .error-code {
          font-weight: 500;
          font-size: 12px;
        }

        .error-row {
          color: var(--el-color-primary);
        }

        .error-field {
          color: var(--el-color-warning);
        }

        .error-code {
          color: var(--el-color-danger);
        }
      }

      .error-message {
        margin-bottom: 5px;
        color: var(--el-text-color-regular);
      }

      .error-value,
      .error-data {
        font-size: 12px;
        color: var(--el-text-color-secondary);
        font-family: monospace;
        background: var(--el-fill-color-light);
        padding: 5px;
        border-radius: 3px;
      }
    }

    .more-errors {
      text-align: center;
      color: var(--el-text-color-secondary);
      font-style: italic;
      margin-top: 10px;
    }
  }

  .action-buttons {
    display: flex;
    gap: 10px;
    justify-content: center;
    margin-top: 20px;
  }
}

.dialog-footer {
  text-align: right;
}
</style>
