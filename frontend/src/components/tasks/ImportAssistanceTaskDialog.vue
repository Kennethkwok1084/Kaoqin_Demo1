<template>
  <el-dialog
    v-model="visible"
    title="导入协助任务"
    width="800px"
    :close-on-click-modal="false"
    @close="handleClose"
  >
    <div class="import-assistance-dialog">
      <!-- 步骤指示器 -->
      <el-steps :active="currentStep" finish-status="success">
        <el-step title="文件选择" description="选择协助任务Excel文件" />
        <el-step title="数据预览" description="预览导入数据" />
        <el-step title="导入完成" description="生成协助任务记录" />
      </el-steps>

      <!-- 步骤1: 文件选择 -->
      <div v-if="currentStep === 0" class="step-content">
        <div class="step-header">
          <el-card>
            <template #header>
              <div class="step-title">
                <el-icon><Upload /></el-icon>
                <span>选择协助任务Excel文件</span>
              </div>
            </template>
            <div class="step-description">
              <p>请选择包含协助任务信息的Excel文件，支持.xlsx和.xls格式</p>
              <el-alert type="info" :closable="false">
                <strong>文件格式要求：</strong>Excel文件应包含以下字段：<br/>
                编号、协助日期、协助地点、协助事项、协助任务时长、协助时长-自定义时长（单位分钟）-补充内容、补充、协助时间（24小时制）、提交人、提交时间
              </el-alert>
            </div>
          </el-card>
        </div>

        <div class="upload-section">
          <el-upload
            ref="uploadRef"
            :auto-upload="false"
            :limit="1"
            :accept="'.xlsx,.xls'"
            :before-upload="beforeUpload"
            :on-change="handleFileChange"
            :on-exceed="handleExceed"
            drag
            class="upload-dragger"
          >
            <el-icon class="upload-icon"><UploadFilled /></el-icon>
            <div class="upload-text">
              <p>拖拽协助任务Excel文件到此处</p>
              <p>或 <em>点击选择文件</em></p>
            </div>
            <template #tip>
              <div class="upload-tip">
                只能上传xlsx/xls文件，且不超过10MB
              </div>
            </template>
          </el-upload>

          <div v-if="selectedFile" class="file-info">
            <el-tag type="success" size="large">
              <el-icon><Document /></el-icon>
              {{ selectedFile.name }}
            </el-tag>
          </div>
        </div>

        <div class="step-actions">
          <el-button @click="handleClose">取消</el-button>
          <el-button
            type="primary"
            :disabled="!selectedFile"
            :loading="uploading"
            @click="parseFile"
          >
            解析文件
          </el-button>
        </div>
      </div>

      <!-- 步骤2: 数据预览 -->
      <div v-if="currentStep === 1" class="step-content">
        <div class="step-header">
          <el-card>
            <template #header>
              <div class="step-title">
                <el-icon><View /></el-icon>
                <span>数据预览</span>
              </div>
            </template>
            <div class="preview-stats">
              <el-row :gutter="20">
                <el-col :span="8">
                  <el-statistic title="总记录数" :value="previewData.length" />
                </el-col>
                <el-col :span="8">
                  <el-statistic title="有效记录" :value="validRecords" />
                </el-col>
                <el-col :span="8">
                  <el-statistic title="无效记录" :value="invalidRecords" />
                </el-col>
              </el-row>
            </div>
          </el-card>
        </div>

        <div class="preview-table">
          <el-table :data="previewData" max-height="400" border>
            <el-table-column prop="number" label="编号" width="80" />
            <el-table-column prop="assistance_date" label="协助日期" width="120" />
            <el-table-column prop="location" label="协助地点" width="120" show-overflow-tooltip />
            <el-table-column prop="task_description" label="协助事项" min-width="150" show-overflow-tooltip />
            <el-table-column prop="duration_minutes" label="时长(分钟)" width="100" />
            <el-table-column prop="submitter" label="提交人" width="100" />
            <el-table-column prop="member_name" label="匹配成员" width="100">
              <template #default="scope">
                <span v-if="scope.row.member_name" class="matched-member">{{ scope.row.member_name }}</span>
                <span v-else class="no-match">未匹配</span>
              </template>
            </el-table-column>
            <el-table-column label="状态" width="80">
              <template #default="scope">
                <el-icon v-if="scope.row.valid" color="#67C23A"><CircleCheck /></el-icon>
                <el-icon v-else color="#F56C6C"><CircleClose /></el-icon>
              </template>
            </el-table-column>
          </el-table>
        </div>

        <div class="step-actions">
          <el-button @click="currentStep = 0">上一步</el-button>
          <el-button @click="handleClose">取消</el-button>
          <el-button
            type="primary"
            :disabled="validRecords === 0"
            :loading="importing"
            @click="importData"
          >
            导入数据
          </el-button>
        </div>
      </div>

      <!-- 步骤3: 导入完成 -->
      <div v-if="currentStep === 2" class="step-content">
        <div class="success-content">
          <el-result
            icon="success"
            title="导入完成"
            :sub-title="`成功导入 ${importResult.success} 条协助任务记录`"
          >
            <template #extra>
              <div class="import-summary">
                <el-descriptions :column="2" border>
                  <el-descriptions-item label="导入总数">{{ importResult.total }}</el-descriptions-item>
                  <el-descriptions-item label="成功导入">{{ importResult.success }}</el-descriptions-item>
                  <el-descriptions-item label="导入失败">{{ importResult.failed }}</el-descriptions-item>
                  <el-descriptions-item label="导入时间">{{ importResult.timestamp }}</el-descriptions-item>
                </el-descriptions>

                <!-- 显示错误详情 -->
                <div v-if="importResult.errors && importResult.errors.length > 0" class="error-details">
                  <el-divider>导入错误详情</el-divider>
                  <el-alert
                    v-for="(error, index) in importResult.errors"
                    :key="index"
                    :title="error"
                    type="error"
                    :closable="false"
                    class="error-item"
                  />
                </div>
              </div>
            </template>
          </el-result>
        </div>

        <div class="step-actions">
          <el-button type="primary" @click="handleClose">完成</el-button>
          <el-button @click="resetDialog">继续导入</el-button>
        </div>
      </div>
    </div>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Upload,
  UploadFilled,
  Document,
  View,
  CircleCheck,
  CircleClose
} from '@element-plus/icons-vue'
import * as XLSX from 'xlsx'
import { tasksApi } from '@/api/tasks'

// Props & Emits
interface Props {
  modelValue: boolean
}

interface Emits {
  (e: 'update:modelValue', value: boolean): void
  (e: 'success'): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

// 响应式数据
const visible = computed({
  get: () => props.modelValue,
  set: (value: boolean) => emit('update:modelValue', value)
})

const currentStep = ref(0)
const uploading = ref(false)
const importing = ref(false)
const selectedFile = ref<File | null>(null)
const uploadRef = ref()

// 数据相关
const previewData = ref<any[]>([])
const importResult = ref({
  total: 0,
  success: 0,
  failed: 0,
  timestamp: '',
  errors: [] as string[]
})

// 计算属性
const validRecords = computed(() => previewData.value.filter(item => item.valid).length)
const invalidRecords = computed(() => previewData.value.filter(item => !item.valid).length)

// 文件上传处理
const beforeUpload = (file: File) => {
  const isExcel = file.type === 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' ||
                  file.type === 'application/vnd.ms-excel'
  const isLt10M = file.size / 1024 / 1024 < 10

  if (!isExcel) {
    ElMessage.error('只能上传Excel文件!')
    return false
  }
  if (!isLt10M) {
    ElMessage.error('文件大小不能超过10MB!')
    return false
  }
  return false // 阻止自动上传
}

const handleFileChange = (file: any) => {
  selectedFile.value = file.raw
}

const handleExceed = () => {
  ElMessage.warning('只能选择一个文件')
}

// 解析Excel文件
const parseFile = async () => {
  if (!selectedFile.value) return

  uploading.value = true
  try {
    const fileBuffer = await selectedFile.value.arrayBuffer()
    const workbook = XLSX.read(fileBuffer, { type: 'array' })
    const worksheet = workbook.Sheets[workbook.SheetNames[0]]
    const jsonData = XLSX.utils.sheet_to_json(worksheet)

    // 转换和验证数据
    previewData.value = await Promise.all(jsonData.map(async (row: any, index: number) => {
      // 处理Excel日期格式
      const assistanceDate = parseExcelDate(row['协助日期'])

      // 解析时长字段，支持多种可能的字段名
      let durationMinutes = 0
      const durationSources = [
        row['协助时长-自定义时长（单位分钟）-补充内容'],
        row['协助时长'],
        row['时长'],
        row['协助任务时长']
      ]

      for (const source of durationSources) {
        if (source !== undefined && source !== null && source !== '') {
          const parsed = parseInt(String(source).replace(/[^\d]/g, '')) // 提取数字部分
          if (!isNaN(parsed) && parsed > 0) {
            durationMinutes = parsed
            break
          }
        }
      }

      // 如果时长为0，默认设置为30分钟
      if (durationMinutes === 0) {
        durationMinutes = 30
        console.warn(`第${index + 1}行：时长为0，默认设置为30分钟`)
      }

      const item = {
        number: row['编号'] || '',
        assistance_date: assistanceDate,
        location: row['协助地点'] || '',
        task_description: row['协助事项'] || '',
        task_duration: row['协助任务时长'] || '',
        duration_minutes: durationMinutes,
        supplement: row['补充'] || '',
        assistance_time: row['协助时间（24小时制）'] || '',
        submitter: row['提交人'] || '',
        submit_time: row['提交时间'] || '',
        member_name: '', // 将通过成员匹配填充
        valid: true,
        rowIndex: index + 1
      }

      // 根据协助日期、协助时长、提交人匹配成员
      if (assistanceDate && item.duration_minutes && item.submitter) {
        try {
          const matchedMember = await matchMemberByAssistanceData({
            date: assistanceDate,
            duration: item.duration_minutes,
            submitter: item.submitter
          })
          if (matchedMember) {
            item.member_name = matchedMember.name
          }
        } catch (error) {
          console.warn('成员匹配失败:', error)
        }
      }

      // 验证必填字段
      if (!item.number || !item.assistance_date || !item.task_description || !item.submitter) {
        item.valid = false
      }

      return item
    }))

    currentStep.value = 1
    ElMessage.success(`解析完成，共${jsonData.length}条记录`)
  } catch (error) {
    console.error('文件解析失败:', error)
    ElMessage.error('文件解析失败，请检查文件格式')
  } finally {
    uploading.value = false
  }
}

// 解析Excel日期格式
const parseExcelDate = (dateValue: any): string => {
  if (!dateValue) return ''

  // 如果是Excel日期数字格式 (例如 44834)
  if (typeof dateValue === 'number' && dateValue > 25000) {
    // Excel日期起始于1900年1月1日，需要转换
    const excelEpoch = new Date(1899, 11, 30) // Excel的1900-01-01实际是1899-12-30
    const date = new Date(excelEpoch.getTime() + dateValue * 24 * 60 * 60 * 1000)
    return date.toISOString().split('T')[0] // YYYY-MM-DD格式
  }

  // 如果已经是日期字符串格式
  if (typeof dateValue === 'string') {
    // 尝试直接使用，如果格式正确
    if (/^\d{4}-\d{2}-\d{2}$/.test(dateValue)) {
      return dateValue
    }

    // 尝试解析其他日期格式
    const date = new Date(dateValue)
    if (!isNaN(date.getTime())) {
      return date.toISOString().split('T')[0]
    }
  }

  // 默认返回当前日期
  console.warn('无法解析日期格式:', dateValue)
  return new Date().toISOString().split('T')[0]
}

// 根据协助数据匹配成员
const matchMemberByAssistanceData = async (data: {
  date: string
  duration: number
  submitter: string
}): Promise<{ name: string } | null> => {
  try {
    // 这里应该调用后端API来匹配成员
    // 暂时返回提交人作为成员名称
    return { name: data.submitter }
  } catch (error) {
    console.error('成员匹配失败:', error)
    return null
  }
}

// 导入数据
const importData = async () => {
  const validData = previewData.value.filter(item => item.valid)
  if (validData.length === 0) {
    ElMessage.warning('没有有效的数据可以导入')
    return
  }

  // 转换数据格式为后端期望的格式
  const transformedData = validData.map(item => ({
    assistance_date: item.assistance_date,
    location: item.location,
    task_description: item.task_description,
    duration_minutes: item.duration_minutes,
    submitter: item.submitter,
    // 可选字段
    number: item.number,
    task_duration: item.task_duration,
    supplement: item.supplement,
    assistance_time: item.assistance_time,
    submit_time: item.submit_time
  }))

  importing.value = true
  try {
    const response = await tasksApi.importAssistanceTasks(transformedData)
    importResult.value = {
      total: previewData.value.length,
      success: response.success || response.success_count || validData.length,
      failed: response.failed || response.failed_count || (previewData.value.length - (response.success || response.success_count || validData.length)),
      timestamp: new Date().toLocaleString(),
      errors: response.errors || []
    }

    currentStep.value = 2
    emit('success')

    // 显示详细结果
    if (importResult.value.failed > 0) {
      ElMessage.warning(`导入完成：成功${importResult.value.success}条，失败${importResult.value.failed}条`)
      console.warn('导入错误详情:', response.errors)
    } else {
      ElMessage.success(`协助任务导入成功：${importResult.value.success}条`)
    }
  } catch (error) {
    console.error('导入失败:', error)
    ElMessage.error('导入协助任务失败')
  } finally {
    importing.value = false
  }
}

// 工具函数

// 对话框处理
const handleClose = () => {
  visible.value = false
}

const resetDialog = () => {
  currentStep.value = 0
  selectedFile.value = null
  previewData.value = []
  importResult.value = { total: 0, success: 0, failed: 0, timestamp: '', errors: [] }
  uploadRef.value?.clearFiles()
}

// 监听对话框关闭，重置状态
watch(visible, (newVal) => {
  if (!newVal) {
    resetDialog()
  }
})
</script>

<style scoped lang="scss">
@use '@/styles/variables.scss' as *;
@use '@/styles/mixins.scss' as *;

.import-assistance-dialog {
  .step-content {
    margin-top: $spacing-large;
    min-height: 400px;
  }

  .step-header {
    margin-bottom: $spacing-base;

    .step-title {
      @include flex-start;
      gap: $spacing-small;
      font-size: $font-size-medium;
      font-weight: 600;
    }

    .step-description {
      p {
        margin: $spacing-small 0;
        color: $text-color-secondary;
      }
    }

    .preview-stats {
      margin-top: $spacing-base;
    }
  }

  .upload-section {
    margin: $spacing-large 0;

    .upload-dragger {
      width: 100%;
    }

    .upload-icon {
      font-size: 48px;
      color: $primary-color;
      margin-bottom: $spacing-base;
    }

    .upload-text {
      p {
        margin: 4px 0;
        color: $text-color-secondary;

        &:first-child {
          font-size: $font-size-medium;
          color: $text-color-primary;
        }
      }
    }

    .upload-tip {
      color: $text-color-placeholder;
      font-size: $font-size-small;
      margin-top: $spacing-small;
    }

    .file-info {
      margin-top: $spacing-base;
      text-align: center;
    }
  }

  .preview-table {
    margin: $spacing-base 0;
  }

  .success-content {
    text-align: center;

    .import-summary {
      margin-top: $spacing-large;
      max-width: 600px;
      margin-left: auto;
      margin-right: auto;
    }
  }

  .step-actions {
    @include flex-end;
    gap: $spacing-small;
    margin-top: $spacing-large;
    padding-top: $spacing-base;
    border-top: 1px solid $border-color-light;
  }

  .matched-member {
    color: $success-color;
    font-weight: 600;
  }

  .no-match {
    color: $text-color-placeholder;
    font-style: italic;
  }

  .error-details {
    margin-top: $spacing-large;

    .error-item {
      margin-bottom: $spacing-small;

      &:last-child {
        margin-bottom: 0;
      }
    }
  }
}
</style>