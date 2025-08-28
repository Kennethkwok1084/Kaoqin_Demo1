<template>
  <el-dialog
    v-model="dialogVisible"
    title="数据导入向导"
    width="800px"
    :close-on-click-modal="false"
    @close="handleClose"
  >
    <div class="import-wizard">
      <!-- 步骤指示器 -->
      <el-steps :active="currentStep" finish-status="success" align-center>
        <el-step title="选择模板" description="选择导入数据类型" />
        <el-step title="上传文件" description="上传Excel或CSV文件" />
        <el-step title="字段映射" description="配置字段对应关系" />
        <el-step title="数据预览" description="预览和验证数据" />
        <el-step title="开始导入" description="执行导入操作" />
      </el-steps>

      <div class="step-content">
        <!-- 步骤1：选择模板 -->
        <div v-show="currentStep === 0" class="step-panel">
          <h3>选择导入模板</h3>
          <div class="template-grid">
            <div
              v-for="template in templates"
              :key="template.id"
              :class="[
                'template-card',
                { active: selectedTemplate?.id === template.id }
              ]"
              @click="selectTemplate(template)"
            >
              <div class="template-icon">
                <el-icon><Document /></el-icon>
              </div>
              <div class="template-info">
                <h4>{{ template.name }}</h4>
                <p>{{ template.description }}</p>
                <div class="template-meta">
                  <span>必填字段: {{ template.requiredFields.length }}</span>
                  <span>可选字段: {{ template.optionalFields.length }}</span>
                </div>
              </div>
              <div class="template-actions">
                <el-button
                  size="small"
                  type="primary"
                  @click.stop="downloadTemplate(template)"
                >
                  <el-icon><Download /></el-icon>
                  下载模板
                </el-button>
              </div>
            </div>
          </div>
        </div>

        <!-- 步骤2：上传文件 -->
        <div v-show="currentStep === 1" class="step-panel">
          <h3>上传数据文件</h3>
          <div class="upload-section">
            <el-upload
              ref="uploadRef"
              class="upload-dragger"
              drag
              :auto-upload="false"
              :show-file-list="false"
              :on-change="handleFileChange"
              accept=".xlsx,.xls,.csv"
            >
              <el-icon class="el-icon--upload"><upload-filled /></el-icon>
              <div class="el-upload__text">
                将文件拖到此处，或<em>点击上传</em>
              </div>
              <template #tip>
                <div class="el-upload__tip">
                  支持 .xlsx, .xls, .csv 格式，文件大小不超过 10MB
                </div>
              </template>
            </el-upload>

            <div v-if="uploadedFile" class="uploaded-file">
              <div class="file-info">
                <el-icon><Document /></el-icon>
                <span class="file-name">{{ uploadedFile.name }}</span>
                <span class="file-size"
                  >({{ formatFileSize(uploadedFile.size) }})</span
                >
                <el-button size="small" type="danger" text @click="removeFile">
                  <el-icon><Close /></el-icon>
                </el-button>
              </div>

              <div v-if="filePreview" class="file-preview">
                <h4>文件预览</h4>
                <div
                  v-if="filePreview.sheets && filePreview.sheets.length > 1"
                  class="sheet-selector"
                >
                  <el-radio-group
                    v-model="selectedSheet"
                    @change="loadSheetPreview"
                  >
                    <el-radio
                      v-for="sheet in filePreview.sheets"
                      :key="sheet.name"
                      :value="sheet.name"
                    >
                      {{ sheet.name }} ({{ sheet.rowCount }} 行)
                    </el-radio>
                  </el-radio-group>
                </div>

                <el-table
                  :data="previewData"
                  max-height="300"
                  style="width: 100%"
                  size="small"
                >
                  <el-table-column
                    v-for="(header, index) in previewHeaders"
                    :key="index"
                    :prop="`col${index}`"
                    :label="header"
                    show-overflow-tooltip
                    width="120"
                  />
                </el-table>

                <div class="preview-info">
                  <span
                    >共
                    {{ (filePreview as any)?.totalRows || 0 }} 行数据，显示前 5
                    行</span
                  >
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- 步骤3：字段映射 -->
        <div v-show="currentStep === 2" class="step-panel">
          <h3>字段映射配置</h3>
          <div class="mapping-section" v-if="selectedTemplate">
            <div class="mapping-header">
              <div class="source-column">源文件字段</div>
              <div class="target-column">目标字段</div>
              <div class="options-column">选项</div>
            </div>

            <div class="mapping-list">
              <div
                v-for="(mapping, index) in fieldMappings"
                :key="index"
                class="mapping-item"
              >
                <div class="source-field">
                  <el-select
                    v-model="mapping.sourceField"
                    placeholder="选择源字段"
                    @change="updateMapping(index)"
                  >
                    <el-option
                      v-for="header in previewHeaders"
                      :key="header"
                      :label="header"
                      :value="header"
                    />
                  </el-select>
                </div>

                <div class="target-field">
                  <div class="field-info">
                    <span class="field-name">{{ mapping.targetField }}</span>
                    <el-tag v-if="mapping.isRequired" type="danger" size="small"
                      >必填</el-tag
                    >
                    <el-tag v-else type="info" size="small">可选</el-tag>
                  </div>
                </div>

                <div class="mapping-options">
                  <el-tooltip content="数据转换" placement="top">
                    <el-button
                      size="small"
                      text
                      @click="showTransformDialog(mapping)"
                    >
                      <el-icon><Setting /></el-icon>
                    </el-button>
                  </el-tooltip>
                  <el-tooltip content="默认值" placement="top">
                    <el-button
                      size="small"
                      text
                      @click="showDefaultValueDialog(mapping)"
                    >
                      <el-icon><EditPen /></el-icon>
                    </el-button>
                  </el-tooltip>
                </div>
              </div>
            </div>

            <div class="mapping-actions">
              <el-button @click="autoMapFields">
                <el-icon><Star /></el-icon>
                智能映射
              </el-button>
              <el-button @click="clearMappings">
                <el-icon><RefreshLeft /></el-icon>
                清空映射
              </el-button>
            </div>
          </div>
        </div>

        <!-- 步骤4：数据预览 -->
        <div v-show="currentStep === 3" class="step-panel">
          <h3>数据预览与验证</h3>
          <div class="validation-section" v-if="validationResults">
            <div class="validation-summary">
              <div class="summary-item">
                <span class="label">总行数:</span>
                <span class="value">{{ validationResults.totalRows }}</span>
              </div>
              <div class="summary-item">
                <span class="label">有效行数:</span>
                <span class="value success">{{ getValidRowCount() }}</span>
              </div>
              <div class="summary-item">
                <span class="label">错误行数:</span>
                <span class="value error">{{ getErrorRowCount() }}</span>
              </div>
            </div>

            <el-tabs v-model="previewTab">
              <el-tab-pane label="数据预览" name="preview">
                <el-table
                  :data="validationResults.rows.slice(0, 10)"
                  max-height="400"
                  style="width: 100%"
                  size="small"
                >
                  <el-table-column
                    v-for="field in selectedTemplate?.requiredFields.concat(
                      selectedTemplate?.optionalFields || []
                    )"
                    :key="field"
                    :prop="field"
                    :label="field"
                    show-overflow-tooltip
                    width="120"
                  />
                </el-table>
                <div class="preview-info">显示前 10 行转换后的数据</div>
              </el-tab-pane>

              <el-tab-pane label="验证结果" name="validation">
                <div class="validation-results">
                  <div
                    v-for="result in validationResults.validationResults"
                    :key="result.field"
                    class="field-validation"
                  >
                    <div class="field-header">
                      <span class="field-name">{{ result.field }}</span>
                      <div class="field-stats">
                        <el-tag type="success" size="small"
                          >有效: {{ result.validCount }}</el-tag
                        >
                        <el-tag
                          v-if="result.invalidCount > 0"
                          type="danger"
                          size="small"
                        >
                          无效: {{ result.invalidCount }}
                        </el-tag>
                      </div>
                    </div>

                    <div v-if="result.errors.length > 0" class="field-errors">
                      <div
                        v-for="error in result.errors.slice(0, 5)"
                        :key="`${error.row}-${error.field}`"
                        class="error-item"
                      >
                        <span class="error-row">第{{ error.row }}行:</span>
                        <span class="error-message">{{ error.error }}</span>
                      </div>
                      <div v-if="result.errors.length > 5" class="more-errors">
                        还有 {{ result.errors.length - 5 }} 个错误...
                      </div>
                    </div>
                  </div>
                </div>
              </el-tab-pane>
            </el-tabs>
          </div>
        </div>

        <!-- 步骤5：开始导入 -->
        <div v-show="currentStep === 4" class="step-panel">
          <h3>导入配置</h3>
          <div class="import-config">
            <el-form :model="importConfig" label-width="120px">
              <el-form-item label="批处理大小">
                <el-input-number
                  v-model="importConfig.options.batchSize"
                  :min="10"
                  :max="1000"
                  :step="10"
                />
                <span class="form-tip">每次处理的记录数，建议100-500</span>
              </el-form-item>

              <el-form-item label="错误处理">
                <el-radio-group v-model="importConfig.options.continueOnError">
                  <el-radio :value="true">遇到错误继续执行</el-radio>
                  <el-radio :value="false">遇到错误停止执行</el-radio>
                </el-radio-group>
              </el-form-item>

              <el-form-item label="重复数据">
                <el-select v-model="importConfig.options.duplicateHandling">
                  <el-option label="跳过重复数据" value="skip" />
                  <el-option label="更新重复数据" value="update" />
                  <el-option label="报错退出" value="error" />
                </el-select>
              </el-form-item>

              <el-form-item label="日期格式">
                <el-select v-model="importConfig.options.dateFormat">
                  <el-option label="YYYY-MM-DD" value="YYYY-MM-DD" />
                  <el-option label="YYYY/MM/DD" value="YYYY/MM/DD" />
                  <el-option label="DD/MM/YYYY" value="DD/MM/YYYY" />
                  <el-option label="MM/DD/YYYY" value="MM/DD/YYYY" />
                </el-select>
              </el-form-item>
            </el-form>

            <div class="import-summary">
              <h4>导入摘要</h4>
              <ul>
                <li>模板类型: {{ selectedTemplate?.name }}</li>
                <li>文件名: {{ uploadedFile?.name }}</li>
                <li>
                  预计导入: {{ validationResults?.totalRows || 0 }} 行数据
                </li>
                <li>有效数据: {{ getValidRowCount() }} 行</li>
                <li v-if="getErrorRowCount() > 0">
                  错误数据: {{ getErrorRowCount() }} 行
                </li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </div>

    <template #footer>
      <div class="dialog-footer">
        <el-button @click="handleClose">取消</el-button>
        <el-button v-if="currentStep > 0" @click="prevStep">上一步</el-button>
        <el-button
          v-if="currentStep < 4"
          type="primary"
          @click="nextStep"
          :disabled="!canProceed()"
        >
          下一步
        </el-button>
        <el-button
          v-if="currentStep === 4"
          type="success"
          @click="startImport"
          :loading="importing"
        >
          开始导入
        </el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, reactive, computed, watch, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import {
  Document,
  Download,
  Close,
  Setting,
  EditPen,
  Star,
  RefreshLeft,
  UploadFilled
} from '@element-plus/icons-vue'
import { dataImportApi } from '@/api/dataImport'
import type {
  ImportTemplate,
  ImportPreview,
  FieldMapping,
  ImportConfiguration,
  FileUploadResponse
} from '@/types/dataImport'

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
const currentStep = ref(0)
const importing = ref(false)
const previewTab = ref('preview')

const templates = ref<ImportTemplate[]>([])
const selectedTemplate = ref<ImportTemplate | null>(null)
const uploadedFile = ref<File | null>(null)
const filePreview = ref<FileUploadResponse | null>(null)
const selectedSheet = ref('')
const fieldMappings = ref<FieldMapping[]>([])
const validationResults = ref<ImportPreview | null>(null)

const importConfig = reactive<ImportConfiguration>({
  templateId: '',
  fieldMappings: [],
  options: {
    skipHeader: true,
    batchSize: 100,
    continueOnError: true,
    duplicateHandling: 'skip',
    dateFormat: 'YYYY-MM-DD',
    encoding: 'utf-8'
  }
})

const previewHeaders = computed(() => {
  return (filePreview.value as any)?.headers || []
})

const previewData = computed(() => {
  if (!(filePreview.value as any)?.rows) return []

  return ((filePreview.value as any)?.rows || [])
    .slice(0, 5)
    .map((row: any) => {
      const obj: Record<string, any> = {}
      row.forEach((cell: any, index: number) => {
        obj[`col${index}`] = cell
      })
      return obj
    })
})

watch(
  () => props.visible,
  visible => {
    dialogVisible.value = visible
    if (visible) {
      loadTemplates()
      resetWizard()
    }
  }
)

watch(dialogVisible, visible => {
  emit('update:visible', visible)
})

onMounted(() => {
  loadTemplates()
})

const loadTemplates = async () => {
  try {
    templates.value = await dataImportApi.getImportTemplates()
  } catch (error) {
    console.error('加载模板失败:', error)
    ElMessage.error('加载模板失败')
  }
}

const resetWizard = () => {
  currentStep.value = 0
  selectedTemplate.value = null
  uploadedFile.value = null
  filePreview.value = null
  selectedSheet.value = ''
  fieldMappings.value = []
  validationResults.value = null
  importing.value = false
}

const selectTemplate = (template: ImportTemplate) => {
  selectedTemplate.value = template
  importConfig.templateId = template.id
}

const downloadTemplate = async (template: ImportTemplate) => {
  try {
    const blob = await dataImportApi.downloadTemplate(template.id, 'xlsx')
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `${template.name}_模板.xlsx`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(url)

    ElMessage.success('模板下载成功')
  } catch (error) {
    console.error('下载模板失败:', error)
    ElMessage.error('下载模板失败')
  }
}

const handleFileChange = async (file: any) => {
  const uploadFile = file.raw as File

  // 文件大小检查
  if (uploadFile.size > 10 * 1024 * 1024) {
    ElMessage.error('文件大小不能超过 10MB')
    return
  }

  try {
    uploadedFile.value = uploadFile
    filePreview.value = await dataImportApi.uploadFile(
      uploadFile,
      selectedTemplate.value?.id
    )

    if (filePreview.value.sheets && filePreview.value.sheets.length > 0) {
      selectedSheet.value = filePreview.value.sheets[0].name
    }

    initializeFieldMappings()
    ElMessage.success('文件上传成功')
  } catch (error) {
    console.error('文件上传失败:', error)
    ElMessage.error('文件上传失败')
    uploadedFile.value = null
    filePreview.value = null
  }
}

const removeFile = () => {
  uploadedFile.value = null
  filePreview.value = null
  selectedSheet.value = ''
  fieldMappings.value = []
  validationResults.value = null
}

const loadSheetPreview = async () => {
  if (!filePreview.value?.fileId || !selectedSheet.value) return

  try {
    const preview = await dataImportApi.getFilePreview(
      filePreview.value.fileId,
      selectedSheet.value
    )
    ;(filePreview.value as any).headers = (preview as any).headers || []
    ;(filePreview.value as any).rows = (preview as any).rows || []
    ;(filePreview.value as any).totalRows = (preview as any).totalRows || 0

    initializeFieldMappings()
  } catch (error) {
    console.error('加载工作表失败:', error)
    ElMessage.error('加载工作表失败')
  }
}

const initializeFieldMappings = () => {
  if (!selectedTemplate.value) return

  const allFields = [
    ...selectedTemplate.value.requiredFields,
    ...selectedTemplate.value.optionalFields
  ]
  fieldMappings.value = allFields.map(field => ({
    sourceField: '',
    targetField: field,
    isRequired: selectedTemplate.value!.requiredFields.includes(field),
    dataType: 'string'
  }))
}

// eslint-disable-next-line @typescript-eslint/no-unused-vars
const updateMapping = (_index: number) => {
  // 字段映射更新逻辑
}

const autoMapFields = async () => {
  if (!selectedTemplate.value || !previewHeaders.value.length) return

  try {
    const suggestions = await dataImportApi.getFieldSuggestions(
      selectedTemplate.value.id,
      previewHeaders.value
    )

    suggestions.forEach(suggestion => {
      if (suggestion.suggestions.length > 0) {
        const mapping = fieldMappings.value.find(
          m => m.targetField === suggestion.suggestions[0].target
        )
        if (mapping) {
          mapping.sourceField = suggestion.field
        }
      }
    })

    ElMessage.success('智能映射完成')
  } catch (error) {
    console.error('智能映射失败:', error)
    ElMessage.error('智能映射失败')
  }
}

const clearMappings = () => {
  fieldMappings.value.forEach(mapping => {
    mapping.sourceField = ''
  })
}

// eslint-disable-next-line @typescript-eslint/no-unused-vars
const showTransformDialog = (_mapping: FieldMapping) => {
  // 显示数据转换对话框
}

// eslint-disable-next-line @typescript-eslint/no-unused-vars
const showDefaultValueDialog = (_mapping: FieldMapping) => {
  // 显示默认值设置对话框
}

const validateData = async () => {
  if (!filePreview.value?.fileId || !selectedTemplate.value) return

  try {
    importConfig.fieldMappings = fieldMappings.value.filter(m => m.sourceField)

    validationResults.value = await dataImportApi.validateImportData(
      filePreview.value.fileId,
      importConfig
    )
  } catch (error) {
    console.error('数据验证失败:', error)
    ElMessage.error('数据验证失败')
  }
}

const getValidRowCount = () => {
  if (!validationResults.value) return 0
  return validationResults.value.validationResults.reduce(
    (sum, result) => sum + result.validCount,
    0
  )
}

const getErrorRowCount = () => {
  if (!validationResults.value) return 0
  return validationResults.value.validationResults.reduce(
    (sum, result) => sum + result.invalidCount,
    0
  )
}

const canProceed = () => {
  switch (currentStep.value) {
    case 0:
      return selectedTemplate.value !== null
    case 1:
      return uploadedFile.value !== null && filePreview.value !== null
    case 2:
      return fieldMappings.value.some(m => m.sourceField && m.isRequired)
    case 3:
      return validationResults.value !== null
    default:
      return true
  }
}

const nextStep = async () => {
  if (currentStep.value === 2) {
    await validateData()
  }

  if (canProceed()) {
    currentStep.value++
  }
}

const prevStep = () => {
  if (currentStep.value > 0) {
    currentStep.value--
  }
}

const startImport = async () => {
  if (!filePreview.value?.fileId) return

  try {
    importing.value = true
    importConfig.fieldMappings = fieldMappings.value.filter(m => m.sourceField)

    await dataImportApi.startImportJob(filePreview.value.fileId, importConfig)

    ElMessage.success('导入作业已创建')
    emit('success')
    handleClose()
  } catch (error) {
    console.error('开始导入失败:', error)
    ElMessage.error('开始导入失败')
  } finally {
    importing.value = false
  }
}

const handleClose = () => {
  dialogVisible.value = false
  resetWizard()
}

const formatFileSize = (bytes: number) => {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}
</script>

<style lang="scss" scoped>
.import-wizard {
  .step-content {
    margin-top: 30px;
    min-height: 400px;
  }

  .step-panel {
    h3 {
      margin-bottom: 20px;
      color: var(--el-text-color-primary);
    }
  }

  .template-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
    gap: 20px;

    .template-card {
      border: 2px solid var(--el-border-color);
      border-radius: 8px;
      padding: 20px;
      cursor: pointer;
      transition: all 0.3s;

      &:hover {
        border-color: var(--el-color-primary);
        box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
      }

      &.active {
        border-color: var(--el-color-primary);
        background-color: var(--el-color-primary-light-9);
      }

      .template-icon {
        font-size: 32px;
        color: var(--el-color-primary);
        margin-bottom: 10px;
      }

      .template-info {
        h4 {
          margin: 0 0 8px 0;
          color: var(--el-text-color-primary);
        }

        p {
          margin: 0 0 12px 0;
          color: var(--el-text-color-regular);
          font-size: 14px;
        }

        .template-meta {
          display: flex;
          gap: 15px;
          font-size: 12px;
          color: var(--el-text-color-secondary);
        }
      }

      .template-actions {
        margin-top: 15px;
      }
    }
  }

  .upload-section {
    .uploaded-file {
      margin-top: 20px;

      .file-info {
        display: flex;
        align-items: center;
        gap: 10px;
        padding: 10px;
        background: var(--el-fill-color-light);
        border-radius: 6px;
        margin-bottom: 15px;

        .file-name {
          font-weight: 500;
        }

        .file-size {
          color: var(--el-text-color-secondary);
          font-size: 12px;
        }
      }

      .file-preview {
        h4 {
          margin-bottom: 15px;
        }

        .sheet-selector {
          margin-bottom: 15px;
        }

        .preview-info {
          margin-top: 10px;
          font-size: 12px;
          color: var(--el-text-color-secondary);
          text-align: center;
        }
      }
    }
  }

  .mapping-section {
    .mapping-header {
      display: grid;
      grid-template-columns: 1fr 1fr 100px;
      gap: 20px;
      padding: 10px 0;
      border-bottom: 1px solid var(--el-border-color);
      margin-bottom: 15px;
      font-weight: 600;
      color: var(--el-text-color-primary);
    }

    .mapping-list {
      max-height: 400px;
      overflow-y: auto;

      .mapping-item {
        display: grid;
        grid-template-columns: 1fr 1fr 100px;
        gap: 20px;
        padding: 15px 0;
        border-bottom: 1px solid var(--el-border-color-lighter);
        align-items: center;

        .target-field {
          .field-info {
            display: flex;
            align-items: center;
            gap: 10px;

            .field-name {
              font-weight: 500;
            }
          }
        }

        .mapping-options {
          display: flex;
          gap: 5px;
        }
      }
    }

    .mapping-actions {
      margin-top: 20px;
      display: flex;
      gap: 10px;
    }
  }

  .validation-section {
    .validation-summary {
      display: flex;
      gap: 30px;
      padding: 20px;
      background: var(--el-fill-color-light);
      border-radius: 6px;
      margin-bottom: 20px;

      .summary-item {
        display: flex;
        flex-direction: column;
        align-items: center;

        .label {
          font-size: 12px;
          color: var(--el-text-color-regular);
        }

        .value {
          font-size: 24px;
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

    .validation-results {
      .field-validation {
        margin-bottom: 20px;
        border: 1px solid var(--el-border-color-lighter);
        border-radius: 6px;
        padding: 15px;

        .field-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 10px;

          .field-name {
            font-weight: 600;
          }

          .field-stats {
            display: flex;
            gap: 10px;
          }
        }

        .field-errors {
          .error-item {
            display: flex;
            gap: 10px;
            margin-bottom: 5px;
            font-size: 12px;

            .error-row {
              color: var(--el-color-danger);
              font-weight: 500;
              min-width: 60px;
            }

            .error-message {
              color: var(--el-text-color-regular);
            }
          }

          .more-errors {
            font-size: 12px;
            color: var(--el-text-color-secondary);
            font-style: italic;
          }
        }
      }
    }
  }

  .import-config {
    .form-tip {
      margin-left: 10px;
      font-size: 12px;
      color: var(--el-text-color-secondary);
    }

    .import-summary {
      margin-top: 30px;
      padding: 20px;
      background: var(--el-fill-color-light);
      border-radius: 6px;

      h4 {
        margin: 0 0 15px 0;
        color: var(--el-text-color-primary);
      }

      ul {
        margin: 0;
        padding-left: 20px;

        li {
          margin-bottom: 8px;
          color: var(--el-text-color-regular);
        }
      }
    }
  }
}

.dialog-footer {
  text-align: right;
}

:deep(.el-upload-dragger) {
  width: 100%;
}
</style>
