<template>
  <el-dialog
    v-model="visible"
    title="协助任务导入"
    width="800px"
    :close-on-click-modal="false"
    @close="handleClose"
  >
    <div class="import-assistance-dialog">
      <!-- 步骤指示器 -->
      <el-steps :active="currentStep" finish-status="success">
        <el-step title="文件导入" description="选择协助任务Excel文件" />
        <el-step title="数据预览" description="预览和验证数据" />
        <el-step title="导入完成" description="生成协助任务记录" />
      </el-steps>

      <!-- 步骤1: 文件导入 -->
      <div v-if="currentStep === 0" class="step-content">
        <div class="step-header">
          <el-card>
            <template #header>
              <div class="step-title">
                <el-icon><Upload /></el-icon>
                <span>第一步：协助任务Excel文件导入</span>
              </div>
            </template>
            <div class="step-description">
              <p>
                请选择包含协助任务数据的Excel文件。系统支持协助日期、协助地点、协助事项、协助任务时长等字段的导入。
              </p>
              <el-alert type="info" :closable="false">
                <strong>重要说明：</strong>协助任务导入将自动处理提交人模糊匹配、时间格式转换等功能，确保数据的准确性和完整性。
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
            <el-icon class="el-icon--upload"><Upload /></el-icon>
            <div class="el-upload__text">
              将协助任务Excel文件拖到此处，或<em>点击上传</em>
            </div>
            <template #tip>
              <div class="el-upload__tip">
                只能上传 xlsx/xls 文件，且不超过 10MB
              </div>
            </template>
          </el-upload>

          <div v-if="selectedFile" class="file-info">
            <el-card>
              <div class="file-details">
                <el-icon><Document /></el-icon>
                <div class="file-meta">
                  <div class="file-name">{{ selectedFile.name }}</div>
                  <div class="file-size">
                    {{ formatFileSize(selectedFile.size) }}
                  </div>
                </div>
                <el-button type="danger" link @click="removeFile">
                  <el-icon><Delete /></el-icon>
                </el-button>
              </div>
            </el-card>
          </div>
        </div>

        <!-- 协助任务导入格式说明 -->
        <div class="template-section">
          <el-card>
            <template #header>
              <div class="card-header">
                <span>协助任务导入格式说明</span>
                <el-button type="primary" link @click="downloadTemplate">
                  <el-icon><Download /></el-icon>
                  下载模板
                </el-button>
              </div>
            </template>

            <div class="format-info">
              <h4>协助任务导入格式说明：</h4>
              <el-table :data="assistanceColumns" stripe max-height="300">
                <el-table-column prop="field" label="字段名" width="150" />
                <el-table-column prop="description" label="说明" />
                <el-table-column prop="required" label="必填" width="80">
                  <template #default="{ row }">
                    <el-tag
                      :type="row.required ? 'danger' : 'info'"
                      size="small"
                    >
                      {{ row.required ? '必填' : '可选' }}
                    </el-tag>
                  </template>
                </el-table-column>
                <el-table-column prop="example" label="示例" width="200" />
              </el-table>

              <el-alert
                title="协助任务导入注意事项"
                type="warning"
                :closable="false"
                style="margin-top: 16px"
              >
                <ul class="notice-list">
                  <li>
                    <strong>必填字段：</strong>协助日期、协助地点、协助事项、协助任务时长、提交人
                  </li>
                  <li>
                    <strong>日期格式：</strong>协助日期支持多种格式，如"2024-03-24 09:00"、"2024/03/24 09:00"等
                  </li>
                  <li>
                    <strong>时长格式：</strong>协助任务时长为纯数字，以分钟为单位
                  </li>
                  <li>
                    <strong>时间格式：</strong>协助时间支持"15.30-17.50"、"15:30-17:50"等多种格式
                  </li>
                  <li>
                    <strong>提交人匹配：</strong>系统将对提交人进行模糊匹配，自动匹配已有成员信息
                  </li>
                  <li>
                    <strong>数据清洗：</strong>系统自动处理数据清洗，防止SQL注入等安全问题
                  </li>
                </ul>
              </el-alert>
            </div>
          </el-card>
        </div>
      </div>

      <!-- 步骤2: 数据预览 -->
      <div v-if="currentStep === 1" class="step-content">
        <div v-loading="parsing" class="preview-section">
          <div class="preview-header">
            <el-card>
              <template #header>
                <div class="step-title">
                  <el-icon><View /></el-icon>
                  <span>第二步：协助任务数据预览</span>
                </div>
              </template>
              <div class="preview-stats">
                <el-row :gutter="20">
                  <el-col :span="8">
                    <el-statistic title="总记录数" :value="assistanceData.length" />
                  </el-col>
                  <el-col :span="8">
                    <el-statistic title="有效记录" :value="validRecords" />
                  </el-col>
                  <el-col :span="8">
                    <el-statistic title="匹配成员" :value="matchedMembers" />
                  </el-col>
                </el-row>
              </div>
            </el-card>
          </div>

          <div class="data-preview">
            <h4>协助任务数据预览：</h4>
            <el-table
              :data="assistanceData"
              stripe
              max-height="400"
              class="preview-table"
            >
              <el-table-column type="index" label="#" width="50" />
              <el-table-column label="协助日期" width="150">
                <template #default="{ row }">
                  <div class="date-info">
                    <div class="date">{{ formatDate(row.assistanceDate) }}</div>
                    <div v-if="row.dateError" class="error">{{ row.dateError }}</div>
                  </div>
                </template>
              </el-table-column>
              <el-table-column label="协助信息" width="200">
                <template #default="{ row }">
                  <div class="assistance-info">
                    <div class="location">{{ row.location }}</div>
                    <div class="task">{{ row.task }}</div>
                  </div>
                </template>
              </el-table-column>
              <el-table-column label="时长信息" width="120">
                <template #default="{ row }">
                  <div class="duration-info">
                    <div class="duration">{{ row.duration }}分钟</div>
                    <div v-if="row.customDuration" class="custom">
                      自定义: {{ row.customDuration }}分钟
                    </div>
                  </div>
                </template>
              </el-table-column>
              <el-table-column label="协助时间" width="120">
                <template #default="{ row }">
                  <div class="time-info">
                    <div v-if="row.timeRange" class="time-range">
                      {{ row.timeRange }}
                    </div>
                    <div v-if="row.timeError" class="error">{{ row.timeError }}</div>
                  </div>
                </template>
              </el-table-column>
              <el-table-column label="提交人" width="100">
                <template #default="{ row }">
                  <div class="submitter-info">
                    <div class="name">{{ row.submitter }}</div>
                    <div v-if="row.matchedMember" class="matched">
                      <el-tag type="success" size="small">已匹配</el-tag>
                    </div>
                    <div v-else class="unmatched">
                      <el-tag type="warning" size="small">未匹配</el-tag>
                    </div>
                  </div>
                </template>
              </el-table-column>
              <el-table-column label="状态" width="80">
                <template #default="{ row }">
                  <el-tag
                    :type="row.valid ? 'success' : 'danger'"
                    size="small"
                  >
                    {{ row.valid ? '有效' : '无效' }}
                  </el-tag>
                </template>
              </el-table-column>
            </el-table>
          </div>
        </div>
      </div>

      <!-- 步骤3: 导入完成 -->
      <div v-if="currentStep === 2" class="step-content">
        <div class="result-section">
          <el-result
            :icon="importResult.success > 0 ? 'success' : 'error'"
            :title="getResultTitle()"
            :sub-title="getResultSubTitle()"
          >
            <template #extra>
              <div class="result-stats">
                <el-card>
                  <el-descriptions :column="2" border>
                    <el-descriptions-item label="成功导入">
                      <el-tag type="success">{{ importResult.success }}</el-tag>
                    </el-descriptions-item>
                    <el-descriptions-item label="导入失败">
                      <el-tag type="danger">{{ importResult.failed }}</el-tag>
                    </el-descriptions-item>
                    <el-descriptions-item label="成员匹配">
                      <el-tag type="primary">{{ importResult.matched_members }}</el-tag>
                    </el-descriptions-item>
                    <el-descriptions-item label="总工时(分钟)">
                      <el-tag type="info">{{ importResult.total_duration }}</el-tag>
                    </el-descriptions-item>
                  </el-descriptions>
                </el-card>

                <div v-if="importResult.errors?.length" class="error-details">
                  <h4>错误详情：</h4>
                  <el-card>
                    <ul class="error-list">
                      <li
                        v-for="(error, index) in importResult.errors"
                        :key="index"
                      >
                        {{ error }}
                      </li>
                    </ul>
                  </el-card>
                </div>
              </div>
            </template>
          </el-result>
        </div>
      </div>
    </div>

    <template #footer>
      <div class="dialog-footer">
        <el-button @click="handleClose">
          {{ currentStep === 2 ? '关闭' : '取消' }}
        </el-button>

        <el-button
          v-if="currentStep === 0"
          type="primary"
          :disabled="!selectedFile"
          :loading="parsing"
          @click="handleParseFile"
        >
          解析文件
        </el-button>

        <el-button v-if="currentStep === 1" @click="handlePrevious">
          上一步
        </el-button>

        <el-button
          v-if="currentStep === 1"
          type="primary"
          :disabled="validRecords === 0"
          :loading="importing"
          @click="handleImport"
        >
          开始导入 ({{ validRecords }}条)
        </el-button>

        <el-button
          v-if="currentStep === 2 && importResult.success > 0"
          type="primary"
          @click="handleFinish"
        >
          完成
        </el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, reactive, computed } from 'vue'
import { ElMessage } from 'element-plus'
import {
  Upload,
  Document,
  Delete,
  Download,
  View
} from '@element-plus/icons-vue'
import * as XLSX from 'xlsx'
import { tasksApi } from '@/api/tasks'

// Props
interface Props {
  modelValue: boolean
}

const props = defineProps<Props>()

// Emits
const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  success: []
}>()

// 响应式数据
const uploadRef = ref()
const currentStep = ref(0)
const parsing = ref(false)
const importing = ref(false)
const selectedFile = ref<File | null>(null)
const assistanceData = ref<any[]>([])
const importResult = reactive({
  success: 0,
  failed: 0,
  matched_members: 0,
  total_duration: 0,
  errors: [] as string[]
})

// 计算属性
const visible = computed({
  get: () => props.modelValue,
  set: value => emit('update:modelValue', value)
})

const validRecords = computed(() => {
  return assistanceData.value.filter(item => item.valid).length
})

const matchedMembers = computed(() => {
  return assistanceData.value.filter(item => item.matchedMember).length
})

// 协助任务导入格式模板
const assistanceColumns = [
  {
    field: '协助日期',
    description: '协助工作的具体日期和时间',
    required: true,
    example: '2024-03-24 09:00'
  },
  {
    field: '协助地点',
    description: '协助工作的具体地点',
    required: true,
    example: '教学楼A座301'
  },
  {
    field: '协助事项',
    description: '具体的协助工作内容',
    required: true,
    example: '网络故障排查与修复'
  },
  {
    field: '协助任务时长',
    description: '实际协助工作时长，单位：分钟',
    required: true,
    example: '120'
  },
  {
    field: '协助时长-自定义时长（单位分钟）-补充内容',
    description: '自定义时长补充说明，单位：分钟',
    required: false,
    example: '30'
  },
  {
    field: '补充',
    description: '其他补充说明内容',
    required: false,
    example: '需要额外材料购买'
  },
  {
    field: '协助时间（24小时制）',
    description: '协助工作的具体时间段',
    required: false,
    example: '15.30-17.50'
  },
  {
    field: '提交人',
    description: '提交协助任务的人员姓名',
    required: true,
    example: '张工程师'
  },
  {
    field: '提交时间',
    description: '任务提交的时间',
    required: false,
    example: '2024-03-24 18:00:00'
  }
]

// 方法
const handleClose = () => {
  resetDialog()
  emit('update:modelValue', false)
}

const resetDialog = () => {
  currentStep.value = 0
  selectedFile.value = null
  assistanceData.value = []
  importResult.success = 0
  importResult.failed = 0
  importResult.matched_members = 0
  importResult.total_duration = 0
  importResult.errors = []
  uploadRef.value?.clearFiles()
}

const beforeUpload = (file: File) => {
  const isExcel =
    file.type ===
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' ||
    file.type === 'application/vnd.ms-excel'

  if (!isExcel) {
    ElMessage.error('只能上传 Excel 文件！')
    return false
  }

  const isLt10M = file.size / 1024 / 1024 < 10
  if (!isLt10M) {
    ElMessage.error('文件大小不能超过 10MB！')
    return false
  }

  return false // 阻止自动上传
}

const handleFileChange = (file: any) => {
  selectedFile.value = file.raw
}

const handleExceed = () => {
  ElMessage.warning('只能上传一个文件')
}

const removeFile = () => {
  selectedFile.value = null
  uploadRef.value?.clearFiles()
}

const formatFileSize = (size: number) => {
  if (size < 1024) return `${size} B`
  if (size < 1024 * 1024) return `${(size / 1024).toFixed(1)} KB`
  return `${(size / 1024 / 1024).toFixed(1)} MB`
}

const formatDate = (dateString: string) => {
  if (!dateString) return '无效日期'
  try {
    const date = new Date(dateString)
    return date.toLocaleDateString('zh-CN') + ' ' + date.toLocaleTimeString('zh-CN', { hour12: false })
  } catch {
    return '格式错误'
  }
}

const downloadTemplate = () => {
  // 协助任务模板数据
  const templateData = [
    {
      '协助日期': '2024-03-24 09:00',
      '协助地点': '教学楼A座301',
      '协助事项': '网络故障排查与修复',
      '协助任务时长': 120,
      '协助时长-自定义时长（单位分钟）-补充内容': 30,
      '补充': '需要购买网线和交换机',
      '协助时间（24小时制）': '15.30-17.50',
      '提交人': '张工程师',
      '提交时间': '2024-03-24 18:00:00'
    },
    {
      '协助日期': '2024-03-25 14:00',
      '协助地点': '实验楼B座205',
      '协助事项': '计算机硬件维修',
      '协助任务时长': 90,
      '协助时长-自定义时长（单位分钟）-补充内容': '',
      '补充': '硬盘更换完成',
      '协助时间（24小时制）': '14:00-15:30',
      '提交人': '李技术员',
      '提交时间': '2024-03-25 16:00:00'
    }
  ]

  const fileName = '协助任务导入模板.xlsx'
  const sheetName = '协助任务'

  // 创建工作簿
  const wb = XLSX.utils.book_new()
  const ws = XLSX.utils.json_to_sheet(templateData)

  const colWidths = [
    { wch: 18 }, // 协助日期
    { wch: 18 }, // 协助地点
    { wch: 25 }, // 协助事项
    { wch: 15 }, // 协助任务时长
    { wch: 25 }, // 协助时长-自定义时长
    { wch: 20 }, // 补充
    { wch: 20 }, // 协助时间
    { wch: 12 }, // 提交人
    { wch: 18 }  // 提交时间
  ]

  ws['!cols'] = colWidths
  XLSX.utils.book_append_sheet(wb, ws, sheetName)

  // 导出文件
  XLSX.writeFile(wb, fileName)
}

const handleParseFile = async () => {
  if (!selectedFile.value) return

  try {
    parsing.value = true
    assistanceData.value = await parseAssistanceFile(selectedFile.value)
    currentStep.value = 1
    ElMessage.success(`文件解析成功，共${assistanceData.value.length}条记录，其中${validRecords.value}条有效`)
  } catch (error) {
    console.error('解析文件失败:', error)
    ElMessage.error('解析文件失败')
  } finally {
    parsing.value = false
  }
}

const parseAssistanceFile = async (file: File) => {
  return new Promise<any[]>((resolve, reject) => {
    const reader = new FileReader()

    reader.onload = e => {
      try {
        const data = new Uint8Array(e.target?.result as ArrayBuffer)
        const workbook = XLSX.read(data, { type: 'array' })
        const sheetName = workbook.SheetNames[0]
        const worksheet = workbook.Sheets[sheetName]
        const jsonData = XLSX.utils.sheet_to_json(worksheet)

        // 处理协助任务数据
        const processedData = jsonData.map((row: any, index) => {
          const errors: string[] = []
          const processedRow = {
            ...row,
            valid: true,
            errors: errors,
            rowIndex: index + 1
          }

          // 必填字段验证
          if (!row['协助日期']) errors.push('协助日期不能为空')
          if (!row['协助地点']) errors.push('协助地点不能为空')
          if (!row['协助事项']) errors.push('协助事项不能为空')
          if (!row['协助任务时长']) errors.push('协助任务时长不能为空')
          if (!row['提交人']) errors.push('提交人不能为空')

          // 处理协助日期
          processedRow.assistanceDate = row['协助日期']
          if (row['协助日期']) {
            try {
              const date = new Date(row['协助日期'])
              if (isNaN(date.getTime())) {
                errors.push('协助日期格式不正确')
                processedRow.dateError = '格式错误'
              }
            } catch {
              errors.push('协助日期格式不正确')
              processedRow.dateError = '格式错误'
            }
          }

          // 处理协助地点和事项（数据清洗）
          processedRow.location = sanitizeText(row['协助地点'])
          processedRow.task = sanitizeText(row['协助事项'])

          // 处理协助时长
          const duration = Number(row['协助任务时长'])
          if (isNaN(duration) || duration <= 0) {
            errors.push('协助任务时长必须是大于0的数字')
            processedRow.duration = 0
          } else {
            processedRow.duration = duration
          }

          // 处理自定义时长
          const customDuration = row['协助时长-自定义时长（单位分钟）-补充内容']
          if (customDuration && !isNaN(Number(customDuration))) {
            processedRow.customDuration = Number(customDuration)
          }

          // 处理补充内容
          processedRow.supplement = sanitizeText(row['补充'] || '')

          // 处理协助时间格式
          const timeRange = row['协助时间（24小时制）']
          if (timeRange) {
            processedRow.timeRange = parseTimeRange(timeRange)
            if (!processedRow.timeRange) {
              processedRow.timeError = '时间格式错误'
            }
          }

          // 处理提交人（模糊匹配）
          processedRow.submitter = sanitizeText(row['提交人'])
          processedRow.matchedMember = matchMember(row['提交人'])

          // 处理提交时间
          if (row['提交时间']) {
            try {
              const submitTime = new Date(row['提交时间'])
              if (!isNaN(submitTime.getTime())) {
                processedRow.submitTime = row['提交时间']
              }
            } catch {
              // 忽略提交时间格式错误
            }
          }

          processedRow.valid = errors.length === 0
          return processedRow
        })

        console.log(`协助任务解析完成：${processedData.length}条记录`)
        resolve(processedData)
      } catch (error) {
        console.error('Excel解析失败:', error)
        reject(error)
      }
    }

    reader.onerror = () => reject(new Error('读取文件失败'))
    reader.readAsArrayBuffer(file)
  })
}

// 数据清洗函数（防止SQL注入）
const sanitizeText = (text: string): string => {
  if (!text) return ''
  return text.toString()
    .replace(/[<>'"&]/g, '') // 移除危险字符
    .replace(/\s+/g, ' ') // 合并多个空格
    .trim()
}

// 时间范围解析
const parseTimeRange = (timeStr: string): string | null => {
  if (!timeStr) return null

  // 支持多种格式：15.30-17.50, 15:30-17:50, 15点30分-17点50分
  const patterns = [
    /(\d{1,2})\.(\d{2})-(\d{1,2})\.(\d{2})/, // 15.30-17.50
    /(\d{1,2}):(\d{2})-(\d{1,2}):(\d{2})/, // 15:30-17:50
    /(\d{1,2})点(\d{2})分?-(\d{1,2})点(\d{2})分?/, // 15点30分-17点50分
    /(\d{1,2})时(\d{2})分?-(\d{1,2})时(\d{2})分?/ // 15时30分-17时50分
  ]

  for (const pattern of patterns) {
    const match = timeStr.match(pattern)
    if (match) {
      const [, startHour, startMin, endHour, endMin] = match
      const start = `${startHour.padStart(2, '0')}:${startMin.padStart(2, '0')}`
      const end = `${endHour.padStart(2, '0')}:${endMin.padStart(2, '0')}`
      return `${start}-${end}`
    }
  }

  return null
}

// 成员模糊匹配（简化版本）
const matchMember = (memberName: string): boolean => {
  if (!memberName) return false

  // 这里应该调用实际的成员匹配API
  // 暂时使用简单的模拟逻辑
  const commonNames = ['张工程师', '李技术员', '王工', '刘师傅', '陈主任']
  return commonNames.some(name =>
    name.includes(memberName) || memberName.includes(name)
  )
}

const handlePrevious = () => {
  if (currentStep.value > 0) {
    currentStep.value--
  }
}

const handleImport = async () => {
  try {
    importing.value = true

    // 准备导入数据
    const validData = assistanceData.value.filter(item => item.valid)
    const importData = {
      assistance_tasks: validData.map(item => ({
        assistance_date: item.assistanceDate,
        location: item.location,
        task_description: item.task,
        duration_minutes: item.duration,
        custom_duration_minutes: item.customDuration || null,
        supplement: item.supplement,
        time_range: item.timeRange,
        submitter: item.submitter,
        submit_time: item.submitTime || null,
        type: 'assistance' // 任务类型为协助
      }))
    }

    console.log('准备导入协助任务数据...', importData)

    // 发送数据到后端
    const response = await tasksApi.importAssistanceTasks(importData)

    // 处理导入结果
    importResult.success = response.success || validData.length
    importResult.failed = response.failed || (assistanceData.value.length - validData.length)
    importResult.matched_members = response.matched_members || matchedMembers.value
    importResult.total_duration = response.total_duration || validData.reduce((sum, item) => sum + item.duration + (item.customDuration || 0), 0)
    importResult.errors = response.errors || assistanceData.value
      .filter(item => !item.valid)
      .map(item => `第${item.rowIndex}行: ${item.errors.join(', ')}`)

    console.log(`协助任务导入完成：成功${importResult.success}条，失败${importResult.failed}条`)
    currentStep.value = 2
  } catch (error) {
    console.error('导入失败:', error)
    ElMessage.error('协助任务导入失败，请检查数据格式')
  } finally {
    importing.value = false
  }
}

const handleFinish = () => {
  emit('success')
  handleClose()
}

const getResultTitle = () => {
  if (importResult.success > 0 && importResult.failed === 0) {
    return '协助任务导入成功'
  } else if (importResult.success > 0 && importResult.failed > 0) {
    return '协助任务部分导入成功'
  } else {
    return '协助任务导入失败'
  }
}

const getResultSubTitle = () => {
  return `成功导入 ${importResult.success} 条协助任务，失败 ${importResult.failed} 条，总工时 ${importResult.total_duration} 分钟`
}
</script>

<style scoped lang="scss">
@use '@/styles/variables.scss' as *;
@use '@/styles/mixins.scss' as *;
@use 'sass:color';

.import-assistance-dialog {
  .step-content {
    margin: 24px 0;
    min-height: 400px;
  }

  .step-header {
    margin-bottom: 24px;

    .step-title {
      @include flex-start;
      align-items: center;
      gap: 8px;
      font-size: 16px;
      font-weight: 600;
      color: $text-color-primary;
    }

    .step-description {
      margin-top: 12px;

      p {
        margin: 0 0 12px 0;
        color: $text-color-regular;
        line-height: 1.6;
      }
    }
  }

  .upload-section {
    margin-bottom: 24px;

    .upload-dragger {
      width: 100%;
    }

    .file-info {
      margin-top: 16px;

      .file-details {
        @include flex-between;
        align-items: center;

        .file-meta {
          flex: 1;
          margin-left: 12px;

          .file-name {
            font-weight: 500;
            color: $text-color-primary;
          }

          .file-size {
            font-size: 12px;
            color: $text-color-secondary;
            margin-top: 2px;
          }
        }
      }
    }
  }

  .template-section {
    .card-header {
      @include flex-between;
      align-items: center;
    }

    .format-info {
      h4 {
        margin: 0 0 16px 0;
        color: $text-color-primary;
      }

      .notice-list {
        margin: 0;
        padding-left: 20px;
        color: $text-color-regular;

        li {
          margin-bottom: 4px;
          line-height: 1.5;
        }
      }
    }
  }

  .preview-section {
    .preview-header {
      margin-bottom: 24px;

      .preview-stats {
        margin-top: 16px;
      }
    }

    .data-preview {
      h4 {
        margin: 0 0 16px 0;
        color: $text-color-primary;
      }

      .preview-table {
        .date-info, .assistance-info, .duration-info, .time-info, .submitter-info {
          font-size: 12px;
          line-height: 1.4;

          > div:first-child {
            font-weight: 500;
            color: $text-color-primary;
            margin-bottom: 2px;
          }

          .error {
            color: $danger-color;
            font-size: 11px;
          }

          .custom {
            color: $text-color-secondary;
            font-size: 11px;
          }

          .time-range {
            color: $text-color-primary;
          }

          .matched, .unmatched {
            margin-top: 2px;
          }
        }
      }
    }
  }

  .result-section {
    .result-stats {
      .error-details {
        margin-top: 16px;

        h4 {
          margin: 0 0 8px 0;
          color: $text-color-primary;
        }

        .error-list {
          margin: 0;
          padding-left: 20px;
          color: $text-color-regular;
          max-height: 200px;
          overflow-y: auto;

          li {
            margin-bottom: 4px;
          }
        }
      }
    }
  }
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

:deep(.el-steps) {
  margin-bottom: 24px;
}

:deep(.el-upload-dragger) {
  padding: 40px;
}

:deep(.el-statistic) {
  text-align: center;
}
</style>