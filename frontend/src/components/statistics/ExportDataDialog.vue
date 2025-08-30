<template>
  <el-dialog
    v-model="dialogVisible"
    title="导出数据"
    width="500px"
    @close="handleClose"
  >
    <el-form :model="form" :rules="rules" ref="formRef" label-width="100px">
      <el-form-item label="导出类型" prop="type">
        <el-radio-group v-model="form.type">
          <el-radio value="current">当前数据</el-radio>
          <el-radio value="filtered">筛选数据</el-radio>
          <el-radio value="all">全部数据</el-radio>
        </el-radio-group>
      </el-form-item>

      <el-form-item label="导出格式" prop="format">
        <el-select
          v-model="form.format"
          placeholder="请选择导出格式"
          style="width: 100%"
        >
          <el-option label="Excel (.xlsx)" value="xlsx" />
          <el-option label="CSV (.csv)" value="csv" />
          <el-option label="PDF (.pdf)" value="pdf" />
          <el-option label="JSON (.json)" value="json" />
        </el-select>
      </el-form-item>

      <el-form-item label="包含字段" prop="fields">
        <el-checkbox-group v-model="form.fields">
          <div class="field-group">
            <div class="field-category">
              <h4>基础信息</h4>
              <el-checkbox value="id">ID</el-checkbox>
              <el-checkbox value="name">姓名</el-checkbox>
              <el-checkbox value="department">部门</el-checkbox>
              <el-checkbox value="position">职位</el-checkbox>
            </div>

            <div class="field-category">
              <h4>任务统计</h4>
              <el-checkbox value="taskCount">任务数量</el-checkbox>
              <el-checkbox value="completedTasks">完成任务</el-checkbox>
              <el-checkbox value="pendingTasks">待处理任务</el-checkbox>
              <el-checkbox value="completionRate">完成率</el-checkbox>
            </div>

            <div class="field-category">
              <h4>工时统计</h4>
              <el-checkbox value="totalHours">总工时</el-checkbox>
              <el-checkbox value="regularHours">正常工时</el-checkbox>
              <el-checkbox value="overtimeHours">加班工时</el-checkbox>
              <el-checkbox value="efficiency">工作效率</el-checkbox>
            </div>

            <div class="field-category">
              <h4>考勤统计</h4>
              <el-checkbox value="attendanceDays">出勤天数</el-checkbox>
              <el-checkbox value="lateCount">迟到次数</el-checkbox>
              <el-checkbox value="leaveCount">请假次数</el-checkbox>
              <el-checkbox value="attendanceRate">出勤率</el-checkbox>
            </div>
          </div>
        </el-checkbox-group>
      </el-form-item>

      <el-form-item label="时间范围" v-if="form.type !== 'current'">
        <el-date-picker
          v-model="form.dateRange as any"
          type="monthrange"
          range-separator="至"
          start-placeholder="开始月份"
          end-placeholder="结束月份"
          style="width: 100%"
        />
      </el-form-item>

      <el-form-item label="部门筛选" v-if="form.type === 'filtered'">
        <el-select
          v-model="form.departments"
          multiple
          placeholder="请选择部门"
          style="width: 100%"
        >
          <el-option label="网络维护部" value="network_maintenance" />
          <el-option label="系统运维部" value="system_operations" />
          <el-option label="安全管理部" value="security_management" />
          <el-option label="技术支持部" value="technical_support" />
        </el-select>
      </el-form-item>

      <el-form-item label="附加选项">
        <el-checkbox-group v-model="form.options">
          <el-checkbox value="includeCharts">包含图表</el-checkbox>
          <el-checkbox value="includeSummary">包含汇总</el-checkbox>
          <el-checkbox value="includeDetails">包含详细信息</el-checkbox>
          <el-checkbox value="compressFile">压缩文件</el-checkbox>
        </el-checkbox-group>
      </el-form-item>

      <el-form-item label="文件名称">
        <el-input
          v-model="form.filename"
          placeholder="请输入文件名称（不含扩展名）"
        >
          <template #append>.{{ form.format }}</template>
        </el-input>
      </el-form-item>
    </el-form>

    <div class="preview-section" v-if="previewData.length">
      <el-divider>数据预览</el-divider>
      <div class="preview-info">
        <el-tag type="info">预计导出 {{ previewData.length }} 条记录</el-tag>
        <el-tag type="success">文件大小约 {{ estimatedSize }}</el-tag>
      </div>

      <el-table
        :data="previewData.slice(0, 5)"
        stripe
        style="width: 100%; margin-top: 10px"
        max-height="200"
      >
        <el-table-column
          v-for="field in selectedFields"
          :key="field"
          :prop="field"
          :label="getFieldLabel(field)"
          show-overflow-tooltip
        />
      </el-table>

      <div class="preview-more" v-if="previewData.length > 5">
        <el-text type="info"
          >... 还有 {{ previewData.length - 5 }} 条记录</el-text
        >
      </div>
    </div>

    <template #footer>
      <div class="dialog-footer">
        <el-button @click="handlePreview" :loading="previewing"
          >预览数据</el-button
        >
        <el-button @click="handleClose">取消</el-button>
        <el-button type="primary" @click="handleExport" :loading="loading">
          导出数据
        </el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, reactive, computed, watch } from 'vue'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'
import { statisticsApi } from '@/api/statistics'
import type { ExportConfig } from '@/types/statistics'

interface Props {
  visible: boolean
}

interface Emits {
  (e: 'update:visible', value: boolean): void
  (e: 'success'): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

const dialogVisible = ref(false)
const loading = ref(false)
const previewing = ref(false)
const formRef = ref<FormInstance>()
const previewData = ref<any[]>([])

const form = reactive({
  type: 'current',
  format: 'xlsx',
  fields: [
    'name',
    'department',
    'taskCount',
    'completionRate',
    'totalHours',
    'attendanceRate'
  ],
  dateRange: [] as Date[],
  departments: [] as string[],
  options: ['includeSummary'],
  filename: `统计数据_${new Date().toISOString().slice(0, 10)}`
})

const rules: FormRules = {
  type: [{ required: true, message: '请选择导出类型', trigger: 'change' }],
  format: [{ required: true, message: '请选择导出格式', trigger: 'change' }],
  fields: [
    {
      required: true,
      type: 'array',
      min: 1,
      message: '请至少选择一个字段',
      trigger: 'change'
    }
  ]
}

const selectedFields = computed(() => {
  return form.fields.filter(field => form.fields.includes(field))
})

const estimatedSize = computed(() => {
  const recordCount = previewData.value.length
  const fieldCount = selectedFields.value.length
  const avgFieldSize = 20 // 平均每个字段字节数
  const totalBytes = recordCount * fieldCount * avgFieldSize

  if (totalBytes < 1024) return `${totalBytes} B`
  if (totalBytes < 1024 * 1024) return `${(totalBytes / 1024).toFixed(1)} KB`
  return `${(totalBytes / (1024 * 1024)).toFixed(1)} MB`
})

watch(
  () => props.visible,
  visible => {
    dialogVisible.value = visible
    if (visible) {
      resetForm()
    }
  }
)

watch(dialogVisible, visible => {
  emit('update:visible', visible)
})

const resetForm = () => {
  form.filename = `统计数据_${new Date().toISOString().slice(0, 10)}`
  previewData.value = []
}

const getFieldLabel = (field: string): string => {
  const labelMap: Record<string, string> = {
    id: 'ID',
    name: '姓名',
    department: '部门',
    position: '职位',
    taskCount: '任务数量',
    completedTasks: '完成任务',
    pendingTasks: '待处理任务',
    completionRate: '完成率',
    totalHours: '总工时',
    regularHours: '正常工时',
    overtimeHours: '加班工时',
    efficiency: '工作效率',
    attendanceDays: '出勤天数',
    lateCount: '迟到次数',
    leaveCount: '请假次数',
    attendanceRate: '出勤率'
  }
  return labelMap[field] || field
}

const handlePreview = async () => {
  if (!formRef.value) return

  try {
    await formRef.value.validate()

    previewing.value = true

    const config: ExportConfig = {
      type: form.type,
      format: form.format,
      fields: form.fields,
      dateRange: form.dateRange,
      departments: form.departments,
      options: form.options
    }

    const response = await statisticsApi.previewExportData(config)
    previewData.value = response.data || response

    ElMessage.success('数据预览成功')
  } catch (error) {
    console.error('预览数据失败:', error)
    ElMessage.error('预览数据失败')
  } finally {
    previewing.value = false
  }
}

const handleExport = async () => {
  if (!formRef.value) return

  try {
    await formRef.value.validate()

    loading.value = true

    const config: ExportConfig = {
      type: form.type,
      format: form.format,
      fields: form.fields,
      dateRange: form.dateRange,
      departments: form.departments,
      options: form.options,
      filename: form.filename
    }

    const response = await statisticsApi.exportData(config)

    // 下载文件
    const blob = new Blob([response.data || response.downloadUrl || response], {
      type: getContentType(form.format)
    })
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `${form.filename}.${form.format}`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(url)

    ElMessage.success('数据导出成功')
    emit('success')
    handleClose()
  } catch (error) {
    console.error('导出数据失败:', error)
    ElMessage.error('导出数据失败')
  } finally {
    loading.value = false
  }
}

const getContentType = (format: string): string => {
  const typeMap: Record<string, string> = {
    xlsx: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    csv: 'text/csv',
    pdf: 'application/pdf',
    json: 'application/json'
  }
  return typeMap[format] || 'application/octet-stream'
}

const handleClose = () => {
  dialogVisible.value = false
  formRef.value?.resetFields()
  previewData.value = []
  loading.value = false
  previewing.value = false
}
</script>

<style lang="scss" scoped>
.field-group {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 20px;

  .field-category {
    h4 {
      margin: 0 0 10px 0;
      font-size: 14px;
      font-weight: 600;
      color: var(--el-text-color-primary);
      border-bottom: 1px solid var(--el-border-color-lighter);
      padding-bottom: 5px;
    }

    :deep(.el-checkbox) {
      display: block;
      margin: 8px 0;
    }
  }
}

.preview-section {
  margin-top: 20px;

  .preview-info {
    display: flex;
    gap: 10px;
    margin-bottom: 10px;
  }

  .preview-more {
    text-align: center;
    margin-top: 10px;
  }
}

.dialog-footer {
  text-align: right;
}

:deep(.el-input-group__append) {
  background-color: var(--el-fill-color-light);
  border-left: 0;
  color: var(--el-text-color-regular);
}
</style>
