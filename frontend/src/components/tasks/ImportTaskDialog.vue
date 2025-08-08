<template>
  <el-dialog
    v-model="visible"
    title="A-B表配合流程导入"
    width="900px"
    :close-on-click-modal="false"
    @close="handleClose"
  >
    <div class="import-task-dialog">
      <!-- 步骤指示器 -->
      <el-steps :active="currentStep" finish-status="success">
        <el-step title="A表导入" description="导入报修单基础信息" />
        <el-step title="B表导入" description="导入维护记录信息" />
        <el-step title="数据匹配" description="A-B表数据匹配" />
        <el-step title="导入完成" description="生成任务记录" />
      </el-steps>

      <!-- 步骤1: A表导入 -->
      <div v-if="currentStep === 0" class="step-content">
        <div class="step-header">
          <el-card>
            <template #header>
              <div class="step-title">
                <el-icon><Upload /></el-icon>
                <span>第一步：A表导入 - 报修单基础信息</span>
              </div>
            </template>
            <div class="step-description">
              <p>请先导入A表（报修单），包含工单编号、报修人、联系方式、故障描述等基础信息。</p>
              <el-alert type="info" :closable="false">
                <strong>重要说明：</strong>A表必须先导入，作为后续 B表匹配的基础数据。系统将以"报单人+联系电话"为关键字对A-B表进行匹配。
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
              将A表（报修单）Excel文件拖到此处，或<em>点击上传</em>
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
                  <div class="file-size">{{ formatFileSize(selectedFile.size) }}</div>
                </div>
                <el-button type="danger" link @click="removeFile">
                  <el-icon><Delete /></el-icon>
                </el-button>
              </div>
            </el-card>
          </div>
        </div>

        <!-- A表模板下载和格式说明 -->
        <div class="template-section">
          <el-card>
            <template #header>
              <div class="card-header">
                <span>A表导入格式说明</span>
                <el-button type="primary" link @click="downloadATableTemplate">
                  <el-icon><Download /></el-icon>
                  下载A表模板
                </el-button>
              </div>
            </template>

            <div class="format-info">
              <h4>A表（报修单）导入格式说明：</h4>
              <el-table 
                :data="aTableColumns" 
                stripe 
                max-height="300"
              >
                <el-table-column prop="field" label="字段名" width="120" />
                <el-table-column prop="description" label="说明" />
                <el-table-column prop="required" label="必填" width="80">
                  <template #default="{ row }">
                    <el-tag :type="row.required ? 'danger' : 'info'" size="small">
                      {{ row.required ? '必填' : '可选' }}
                    </el-tag>
                  </template>
                </el-table-column>
                <el-table-column prop="example" label="示例" width="180" />
              </el-table>

              <el-alert
                title="A表导入注意事项"
                type="warning"
                :closable="false"
                style="margin-top: 16px"
              >
                <ul class="notice-list">
                  <li><strong>必填字段：</strong>工单编号、位置、对象、描述、报单人、报单人电话、报单时间、工单状态</li>
                  <li><strong>报单企业：</strong>可以为空，系统会根据其他信息进行推断</li>
                  <li><strong>联系人映射：</strong>联系人对应报单人字段</li>
                  <li><strong>联系方式映射：</strong>联系方式对应报单人电话字段</li>
                  <li><strong>时间格式：</strong>报单时间对应报修时间，格式为 YYYY-MM-DD HH:mm:ss</li>
                  <li><strong>状态字段：</strong>工单状态对应工单状态列</li>
                  <li><strong>任务类型：</strong>系统根据"类型"字段自动识别线上/线下任务</li>
                  <li><strong>匹配关键字：</strong>"报单人+报单人电话"将作为A-B表匹配的唯一标识</li>
                </ul>
              </el-alert>
            </div>
          </el-card>
        </div>
      </div>

      <!-- 步骤2: B表导入（可选） -->
      <div v-if="currentStep === 1" class="step-content">
        <div class="step-header">
          <el-card>
            <template #header>
              <div class="step-title">
                <el-icon><Document /></el-icon>
                <span>第二步：B表导入 - 维护记录信息（可选）</span>
                <el-tag type="success" size="small" style="margin-left: 8px;">A表已导入{{ aTableData.length }}条记录</el-tag>
              </div>
            </template>
            <div class="step-description">
              <p>可选择导入B表（维护记录），包含处理时间、处理人、工时、评价等维护处理信息。</p>
              
              <!-- 导入选择 -->
              <div class="import-option-section">
                <el-radio-group v-model="bTableImportOption" class="import-option-group">
                  <el-radio value="import" size="large">
                    <div class="option-content">
                      <div class="option-title">导入B表维护记录</div>
                      <div class="option-desc">导入详细的维护记录，生成完整的任务数据（推荐）</div>
                    </div>
                  </el-radio>
                  <el-radio value="skip" size="large">
                    <div class="option-content">
                      <div class="option-title">跳过B表导入</div>
                      <div class="option-desc">仅使用A表数据，所有任务将按线上单处理（40分钟/单）</div>
                    </div>
                  </el-radio>
                </el-radio-group>
              </div>
              
              <el-alert 
                v-if="bTableImportOption === 'import'"
                type="warning" 
                :closable="false"
                style="margin-top: 12px;"
              >
                <strong>匹配原理：</strong>系统将以B表中的"联系人+联系方式"与A表中的"报单人+报单人电话"进行全匹配，生成完整的维修任务记录。
              </el-alert>
              
              <el-alert 
                v-if="bTableImportOption === 'skip'"
                type="info" 
                :closable="false"
                style="margin-top: 12px;"
              >
                <strong>跳过说明：</strong>跳过B表导入后，所有A表记录将自动设置为线上任务类型，按40分钟/单计算工时，无处理人员和维护详情信息。
              </el-alert>
            </div>
          </el-card>
        </div>

        <div v-if="bTableImportOption === 'import'" class="upload-section">
          <el-upload
            ref="uploadRefB"
            :auto-upload="false"
            :limit="1"
            :accept="'.xlsx,.xls'"
            :before-upload="beforeUpload"
            :on-change="handleFileBChange"
            :on-exceed="handleExceed"
            drag
            class="upload-dragger"
          >
            <el-icon class="el-icon--upload"><Upload /></el-icon>
            <div class="el-upload__text">
              将B表（维护记录）Excel文件拖到此处，或<em>点击上传</em>
            </div>
            <template #tip>
              <div class="el-upload__tip">
                只能上传 xlsx/xls 文件，且不超过 10MB
              </div>
            </template>
          </el-upload>

          <div v-if="selectedFileB" class="file-info">
            <el-card>
              <div class="file-details">
                <el-icon><Document /></el-icon>
                <div class="file-meta">
                  <div class="file-name">{{ selectedFileB.name }}</div>
                  <div class="file-size">{{ formatFileSize(selectedFileB.size) }}</div>
                </div>
                <el-button type="danger" link @click="removeFileB">
                  <el-icon><Delete /></el-icon>
                </el-button>
              </div>
            </el-card>
          </div>
        </div>

        <!-- B表模板下载和格式说明 -->
        <div v-if="bTableImportOption === 'import'" class="template-section">
          <el-card>
            <template #header>
              <div class="card-header">
                <span>B表导入格式说明</span>
                <el-button type="primary" link @click="downloadBTableTemplate">
                  <el-icon><Download /></el-icon>
                  下载B表模板
                </el-button>
              </div>
            </template>

            <div class="format-info">
              <h4>B表（维护记录）导入格式说明：</h4>
              <el-table 
                :data="bTableColumns" 
                stripe 
                max-height="300"
              >
                <el-table-column prop="field" label="字段名" width="120" />
                <el-table-column prop="description" label="说明" />
                <el-table-column prop="required" label="必填" width="80">
                  <template #default="{ row }">
                    <el-tag :type="row.required ? 'danger' : 'info'" size="small">
                      {{ row.required ? '必填' : '可选' }}
                    </el-tag>
                  </template>
                </el-table-column>
                <el-table-column prop="example" label="示例" width="180" />
              </el-table>

              <el-alert
                title="B表导入注意事项"
                type="warning"
                :closable="false"
                style="margin-top: 16px"
              >
                <ul class="notice-list">
                  <li><strong>必填字段：</strong>工单编号、联系人、联系方式（用于与A表匹配）</li>
                  <li><strong>A/B表匹配：</strong>系统以"联系人+联系方式"为关键字进行匹配</li>
                  <li><strong>工时计算：</strong>线上任务40分钟/单，线下任务100分钟/单，支持爆单标记+15分钟</li>
                  <li><strong>时间格式：</strong>YYYY-MM-DD HH:mm:ss 或 YYYY/MM/DD HH:mm:ss</li>
                  <li><strong>处理记录：</strong>处理人、处理时间、完成时间、工时等维护记录</li>
                  <li><strong>评价处理：</strong>客户评价支持"满意"、"不满意"等文字，满意度支持1-5数字评分</li>
                </ul>
              </el-alert>
            </div>
          </el-card>
        </div>
      </div>

      <!-- 步骤3: 数据匹配和预览 -->
      <div v-if="currentStep === 2" class="step-content">
        <div v-loading="matching" class="preview-section">
          <div class="matching-header">
            <el-card>
              <template #header>
                <div class="step-title">
                  <el-icon><Connection /></el-icon>
                  <span>第三步：A-B表数据匹配预览</span>
                </div>
              </template>
              <div class="matching-stats">
                <el-row :gutter="20">
                  <el-col :span="6">
                    <el-statistic title="A表记录" :value="aTableData.length" />
                  </el-col>
                  <el-col :span="6">
                    <el-statistic title="B表记录" :value="bTableData.length" />
                  </el-col>
                  <el-col :span="6">
                    <el-statistic title="成功匹配" :value="matchedCount" />
                  </el-col>
                  <el-col :span="6">
                    <el-statistic title="匹配率" :value="matchRate" suffix="%" :precision="1" />
                  </el-col>
                </el-row>
              </div>
            </el-card>
          </div>

          <div class="matched-preview">
            <h4>{{ bTableImportOption === 'skip' ? '生成任务预览：' : '匹配结果预览：' }}</h4>
            <el-table
              :data="matchedData"
              stripe
              max-height="400"
              class="preview-table"
            >
              <el-table-column type="index" label="#" width="50" />
              <el-table-column label="工单信息" width="140">
                <template #default="{ row }">
                  <div class="work-order-info">
                    <div class="work-order-id">{{ row.workOrderId }}</div>
                    <div class="company">{{ row.company }}</div>
                  </div>
                </template>
              </el-table-column>
              <el-table-column label="故障信息" width="180">
                <template #default="{ row }">
                  <div class="fault-info">
                    <div class="object">{{ row.title }}</div>
                    <div class="description">{{ row.description }}</div>
                  </div>
                </template>
              </el-table-column>
              <el-table-column label="任务类型" width="90">
                <template #default="{ row }">
                  <el-tag 
                    :type="row.taskType === 'offline_repair' ? 'warning' : 'info'" 
                    size="small"
                  >
                    {{ row.taskType === 'offline_repair' ? '线下' : '线上' }}
                    <span v-if="row.isOnlineOnly" style="margin-left: 4px;" title="跳过B表，自动设为线上">*</span>
                  </el-tag>
                </template>
              </el-table-column>
              <el-table-column label="联系信息" width="120">
                <template #default="{ row }">
                  <div class="contact-info">
                    <div>{{ row.contactPerson }}</div>
                    <div class="phone">{{ row.contactPhone }}</div>
                  </div>
                </template>
              </el-table-column>
              <el-table-column label="处理信息" width="120">
                <template #default="{ row }">
                  <div class="process-info">
                    <div v-if="row.assignee">{{ row.assignee }}</div>
                    <div v-else-if="row.completionStatus" class="completion-status">{{ row.completionStatus }}</div>
                    <div v-if="row.actualHours" class="work-hours">{{ row.actualHours }}小时</div>
                    <div v-else class="work-hours-default">{{ row.taskType === 'offline_repair' ? '100' : '40' }}分钟</div>
                  </div>
                </template>
              </el-table-column>
              <el-table-column label="匹配状态" width="80">
                <template #default="{ row }">
                  <el-tag 
                    :type="row.matched ? 'success' : (row.isOnlineOnly ? 'info' : 'warning')" 
                    size="small"
                  >
                    {{ row.matched ? '已匹配' : (row.isOnlineOnly ? '线上单' : '仅A表') }}
                  </el-tag>
                </template>
              </el-table-column>
            </el-table>
          </div>
        </div>
      </div>

      <!-- 步骤4: 导入完成 -->
      <div v-if="currentStep === 3" class="step-content">
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
                    <el-descriptions-item label="完整匹配">
                      <el-tag type="primary">{{ importResult.matched }}</el-tag>
                    </el-descriptions-item>
                    <el-descriptions-item label="仅A表数据">
                      <el-tag type="warning">{{ importResult.partial }}</el-tag>
                    </el-descriptions-item>
                    <el-descriptions-item label="处理人匹配" v-if="importResult.matched_assignees">
                      <el-tag type="info">{{ importResult.matched_assignees }}个</el-tag>
                    </el-descriptions-item>
                  </el-descriptions>
                </el-card>

                <div v-if="importResult.assignee_matches?.length" class="assignee-matches" style="margin-top: 16px;">
                  <h4>处理人匹配详情：</h4>
                  <el-card>
                    <ul class="match-list">
                      <li v-for="(match, index) in importResult.assignee_matches" :key="index" class="match-item">
                        <el-icon color="#67c23a"><Check /></el-icon>
                        {{ match }}
                      </li>
                    </ul>
                  </el-card>
                </div>

                <div v-if="importResult.errors?.length" class="error-details">
                  <h4>错误详情：</h4>
                  <el-card>
                    <ul class="error-list">
                      <li v-for="(error, index) in importResult.errors" :key="index">
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
          {{ currentStep === 3 ? '关闭' : '取消' }}
        </el-button>
        
        <el-button 
          v-if="currentStep === 0" 
          type="primary" 
          :disabled="!selectedFile"
          :loading="parsing"
          @click="handleParseA"
        >
          解析A表
        </el-button>
        
        <el-button 
          v-if="currentStep === 1" 
          @click="handlePrevious"
        >
          上一步
        </el-button>
        
        <el-button 
          v-if="currentStep === 1" 
          type="primary" 
          :disabled="bTableImportOption === 'import' && !selectedFileB"
          :loading="parsing"
          @click="handleParseBOrSkip"
        >
          {{ bTableImportOption === 'skip' ? '跳过B表，直接生成任务' : '解析B表并匹配' }}
        </el-button>
        
        <el-button 
          v-if="currentStep === 2" 
          @click="handlePrevious"
        >
          上一步
        </el-button>
        
        <el-button 
          v-if="currentStep === 2" 
          type="primary" 
          :disabled="matchedData.length === 0"
          :loading="importing"
          @click="handleImport"
        >
          开始导入 ({{ matchedData.length }}条)
        </el-button>
        
        <el-button 
          v-if="currentStep === 3 && importResult.success > 0" 
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
import { ElMessage, ElMessageBox } from 'element-plus'
import { Upload, Document, Delete, Download, Connection, Check } from '@element-plus/icons-vue'
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
const uploadRefB = ref()
const currentStep = ref(0)
const parsing = ref(false)
const matching = ref(false)
const importing = ref(false)
const selectedFile = ref<File | null>(null)
const selectedFileB = ref<File | null>(null)
const aTableData = ref<any[]>([])
const bTableData = ref<any[]>([])
const matchedData = ref<any[]>([])
const bTableImportOption = ref<'import' | 'skip'>('import')
const importResult = reactive({
  success: 0,
  failed: 0,
  matched: 0,
  partial: 0,
  errors: [] as string[],
  matched_assignees: 0,
  assignee_matches: [] as string[]
})

// 计算属性
const visible = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value)
})

const matchedCount = computed(() => {
  // 跳过B表时，返回总记录数；否则返回匹配成功的记录数
  if (bTableImportOption.value === 'skip') {
    return matchedData.value.length
  }
  return matchedData.value.filter(item => item.matched).length
})

const matchRate = computed(() => {
  if (aTableData.value.length === 0) return 0
  return (matchedCount.value / aTableData.value.length) * 100
})

// A表（报修单）导入格式模板
const aTableColumns = [
  { field: '工单编号', description: '维修工单唯一编号', required: true, example: 'WO202401001' },
  { field: '报单企业', description: '报修单位/部门（可为空）', required: false, example: '计算机学院' },
  { field: '位置', description: '具体位置信息', required: true, example: '教学楼A座301' },
  { field: '对象', description: '报修设备/对象', required: true, example: '台式电脑' },
  { field: '描述', description: '故障详细描述', required: true, example: '电脑无法正常启动，显示蓝屏' },
  { field: '建筑', description: '所在建筑名称', required: false, example: '教学楼A座' },
  { field: '楼层', description: '楼层信息', required: false, example: '3楼' },
  { field: '房间', description: '房间号', required: false, example: '301室' },
  { field: '报单人', description: '报修人姓名', required: true, example: '张老师' },
  { field: '报单人电话', description: '报修人联系电话', required: true, example: '13800138000' },
  { field: '报单时间', description: '报修提交时间', required: true, example: '2024-01-15 09:30:00' },
  { field: '工单状态', description: '工单当前状态', required: true, example: '已完成' },
  { field: '类型', description: '维修类型（线上/线下）', required: true, example: '线下维修' },
  { field: '优先级', description: '紧急程度', required: false, example: '普通' },
  { field: '分类', description: '故障大类', required: false, example: '硬件故障' }
]

// B表（维护记录）导入格式模板  
const bTableColumns = [
  { field: '工单编号', description: '对应A表的工单编号', required: true, example: 'WO202401001' },
  { field: '联系人', description: '对应A表的报单人', required: true, example: '张老师' },
  { field: '联系方式', description: '对应A表的报单人电话', required: true, example: '13800138000' },
  { field: '响应时间', description: '首次响应时间', required: false, example: '2024-01-15 10:00:00' },
  { field: '处理时间', description: '开始处理时间', required: false, example: '2024-01-15 14:00:00' },
  { field: '完成时间', description: '任务完成时间', required: false, example: '2024-01-15 16:30:00' },
  { field: '故障描述', description: '技术人员故障描述', required: false, example: '硬盘损坏导致系统无法启动' },
  { field: '解决方案', description: '具体解决方法', required: false, example: '更换硬盘并重装系统' },
  { field: '处理人', description: '实际处理人员', required: false, example: '李工程师' },
  { field: '处理说明', description: '处理过程说明', required: false, example: '已更换新硬盘，重装操作系统' },
  { field: '工时', description: '实际耗时（小时）', required: false, example: '2.5' },
  { field: '材料费', description: '材料成本', required: false, example: '200' },
  { field: '人工费', description: '人工成本', required: false, example: '100' },
  { field: '总费用', description: '总计费用', required: false, example: '300' },
  { field: '客户评价', description: '用户反馈评价', required: false, example: '满意' },
  { field: '满意度', description: '满意度评分', required: false, example: '5' },
  { field: '备注', description: '其他备注信息', required: false, example: '用户表示满意' }
]

// 方法
const handleClose = () => {
  resetDialog()
  emit('update:modelValue', false)
}

const resetDialog = () => {
  currentStep.value = 0
  selectedFile.value = null
  selectedFileB.value = null
  aTableData.value = []
  bTableData.value = []
  matchedData.value = []
  bTableImportOption.value = 'import'
  importResult.success = 0
  importResult.failed = 0
  importResult.matched = 0
  importResult.partial = 0
  importResult.errors = []
  importResult.matched_assignees = 0
  importResult.assignee_matches = []
  uploadRef.value?.clearFiles()
  uploadRefB.value?.clearFiles()
}

const beforeUpload = (file: File) => {
  const isExcel = file.type === 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' ||
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

const handleFileBChange = (file: any) => {
  selectedFileB.value = file.raw
}

const handleExceed = () => {
  ElMessage.warning('只能上传一个文件')
}

const removeFile = () => {
  selectedFile.value = null
  uploadRef.value?.clearFiles()
}

const removeFileB = () => {
  selectedFileB.value = null
  uploadRefB.value?.clearFiles()
}

const formatFileSize = (size: number) => {
  if (size < 1024) return `${size} B`
  if (size < 1024 * 1024) return `${(size / 1024).toFixed(1)} KB`
  return `${(size / 1024 / 1024).toFixed(1)} MB`
}

const downloadATableTemplate = () => {
  // A表（报修单）模板数据
  const templateData = [
    {
      '工单编号': 'WO202401001',
      '报单企业': '计算机学院',
      '位置': '教学楼A座301',
      '对象': '台式电脑',
      '描述': '电脑无法正常启动，显示蓝屏错误',
      '建筑': '教学楼A座',
      '楼层': '3楼',
      '房间': '301室',
      '报单人': '张老师',
      '报单人电话': '13800138000',
      '报单时间': '2024-01-15 09:30:00',
      '工单状态': '已完成',
      '类型': '线下维修',
      '优先级': '普通',
      '分类': '硬件故障'
    },
    {
      '工单编号': 'WO202401002',
      '报单企业': '',
      '位置': '网络机房',
      '对象': '网络交换机',
      '描述': '交换机端口故障，网络连接不稳定',
      '建筑': '信息楼',
      '楼层': '1楼',
      '房间': '机房A',
      '报单人': '王工',
      '报单人电话': '13900139000',
      '报单时间': '2024-01-16 08:00:00',
      '工单状态': '已完成',
      '类型': '线上处理',
      '优先级': '紧急',
      '分类': '网络故障'
    }
  ]
  const fileName = 'A表导入模板_报修单.xlsx'
  const sheetName = 'A表-报修单'

  // 创建工作簿
  const wb = XLSX.utils.book_new()
  const ws = XLSX.utils.json_to_sheet(templateData)
  
  const colWidths = [
    { wch: 12 }, // 工单编号
    { wch: 15 }, // 报单企业
    { wch: 18 }, // 位置
    { wch: 12 }, // 对象
    { wch: 25 }, // 描述
    { wch: 12 }, // 建筑
    { wch: 8 },  // 楼层
    { wch: 10 }, // 房间
    { wch: 10 }, // 报单人
    { wch: 15 }, // 报单人电话
    { wch: 18 }, // 报单时间
    { wch: 10 }, // 工单状态
    { wch: 12 }, // 类型
    { wch: 10 }, // 优先级
    { wch: 12 }  // 分类
  ]
  
  ws['!cols'] = colWidths
  XLSX.utils.book_append_sheet(wb, ws, sheetName)
  
  // 导出文件
  XLSX.writeFile(wb, fileName)
}

const downloadBTableTemplate = () => {
  // B表（维护记录）模板数据
  const templateData = [
    {
      '工单编号': 'WO202401001',
      '联系人': '张老师',
      '联系方式': '13800138000',
      '响应时间': '2024-01-15 10:00:00',
      '处理时间': '2024-01-15 14:00:00',
      '完成时间': '2024-01-15 16:30:00',
      '故障描述': '硬盘损坏导致系统无法启动',
      '解决方案': '更换硬盘并重装系统',
      '处理人': '李工程师',
      '处理说明': '已更换新硬盘，重装操作系统，测试正常',
      '工时': '2.5',
      '材料费': '200',
      '人工费': '100',
      '总费用': '300',
      '客户评价': '满意',
      '满意度': '5',
      '备注': '用户表示非常满意，设备运行正常'
    },
    {
      '工单编号': 'WO202401002',
      '联系人': '王工',
      '联系方式': '13900139000',
      '响应时间': '2024-01-16 08:30:00',
      '处理时间': '2024-01-16 09:00:00',
      '完成时间': '2024-01-16 11:00:00',
      '故障描述': '交换机第8端口物理故障',
      '解决方案': '远程配置端口，调整网络拓扑',
      '处理人': '网络工程师',
      '处理说明': '通过远程配置解决，网络恢复正常',
      '工时': '1.0',
      '材料费': '0',
      '人工费': '50',
      '总费用': '50',
      '客户评价': '很好',
      '满意度': '4',
      '备注': '响应及时，处理迅速'
    }
  ]
  const fileName = 'B表导入模板_维护记录.xlsx'
  const sheetName = 'B表-维护记录'

  // 创建工作簿
  const wb = XLSX.utils.book_new()
  const ws = XLSX.utils.json_to_sheet(templateData)
  
  const colWidths = [
    { wch: 12 }, // 工单编号
    { wch: 10 }, // 联系人
    { wch: 15 }, // 联系方式
    { wch: 18 }, // 响应时间
    { wch: 18 }, // 处理时间
    { wch: 18 }, // 完成时间
    { wch: 25 }, // 故障描述
    { wch: 25 }, // 解决方案
    { wch: 12 }, // 处理人
    { wch: 25 }, // 处理说明
    { wch: 8 },  // 工时
    { wch: 10 }, // 材料费
    { wch: 10 }, // 人工费
    { wch: 10 }, // 总费用
    { wch: 10 }, // 客户评价
    { wch: 8 },  // 满意度
    { wch: 20 }  // 备注
  ]
  
  ws['!cols'] = colWidths
  XLSX.utils.book_append_sheet(wb, ws, sheetName)
  
  // 导出文件
  XLSX.writeFile(wb, fileName)
}

const handleParseA = async () => {
  if (!selectedFile.value) return

  try {
    parsing.value = true
    aTableData.value = await parseExcelFile(selectedFile.value, 'a-table')
    currentStep.value = 1
    ElMessage.success(`A表解析成功，共${aTableData.value.length}条记录`)
  } catch (error) {
    console.error('解析A表失败:', error)
    ElMessage.error('解析A表文件失败')
  } finally {
    parsing.value = false
  }
}

const handleParseBOrSkip = async () => {
  try {
    parsing.value = true
    
    if (bTableImportOption.value === 'skip') {
      // 跳过B表导入，直接生成仅A表的任务数据
      bTableData.value = []
      matching.value = true
      matchedData.value = generateOnlineOnlyTasks()
      currentStep.value = 2
      ElMessage.success(`已跳过B表导入，A表${aTableData.value.length}条记录将全部按线上单处理`)
    } else {
      // 正常B表导入流程
      if (!selectedFileB.value) {
        ElMessage.warning('请先选择B表文件')
        return
      }
      
      bTableData.value = await parseExcelFile(selectedFileB.value, 'b-table')
      
      // 进行A-B表匹配
      matching.value = true
      matchedData.value = performABMatching()
      
      currentStep.value = 2
      ElMessage.success(`B表解析成功，匹配完成。A表${aTableData.value.length}条，B表${bTableData.value.length}条，成功匹配${matchedCount.value}条`)
    }
  } catch (error) {
    console.error('处理B表失败:', error)
    ElMessage.error('处理B表失败')
  } finally {
    parsing.value = false
    matching.value = false
  }
}

const handleParseB = handleParseBOrSkip // 保持向后兼容

const handlePrevious = () => {
  if (currentStep.value > 0) {
    currentStep.value--
  }
}

const parseExcelFile = async (file: File, tableType: 'a-table' | 'b-table') => {
  return new Promise<any[]>((resolve, reject) => {
    const reader = new FileReader()
    
    reader.onload = (e) => {
      try {
        const data = new Uint8Array(e.target?.result as ArrayBuffer)
        const workbook = XLSX.read(data, { type: 'array' })
        const sheetName = workbook.SheetNames[0]
        const worksheet = workbook.Sheets[sheetName]
        const jsonData = XLSX.utils.sheet_to_json(worksheet)

        // 根据表类型验证和转换数据
        const processedData = jsonData.map((row: any, index) => {
          const errors: string[] = []
          const processedRow = { 
            ...row, 
            _valid: true, 
            _errors: errors,
            _rowIndex: index + 1,
            _tableType: tableType
          }

          if (tableType === 'a-table') {
            // A表验证必填字段
            if (!row['工单编号']) errors.push('工单编号不能为空')
            if (!row['位置']) errors.push('位置不能为空')
            if (!row['对象']) errors.push('报修对象不能为空')
            if (!row['描述']) errors.push('故障描述不能为空')
            if (!row['报单人']) errors.push('报单人不能为空')
            if (!row['报单人电话']) errors.push('报单人电话不能为空')
            if (!row['报单时间']) errors.push('报单时间不能为空')
            if (!row['工单状态']) errors.push('工单状态不能为空')
            
            // 构建A表匹配关键字
            processedRow._matchKey = `${row['报单人'] || ''}_${row['报单人电话'] || ''}`.trim()
          } else {
            // B表验证必填字段
            if (!row['工单编号']) errors.push('工单编号不能为空')
            if (!row['联系人']) errors.push('联系人不能为空')
            if (!row['联系方式']) errors.push('联系方式不能为空')
            
            // 构建B表匹配关键字
            processedRow._matchKey = `${row['联系人'] || ''}_${row['联系方式'] || ''}`.trim()
          }

          // 验证时间格式
          const timeFields = tableType === 'a-table' 
            ? ['报单时间'] 
            : ['响应时间', '处理时间', '完成时间']
          
          timeFields.forEach(field => {
            if (row[field]) {
              const date = new Date(row[field])
              if (isNaN(date.getTime())) {
                errors.push(`${field}格式不正确`)
              }
            }
          })

          // B表特有验证
          if (tableType === 'b-table') {
            if (row['工时'] && isNaN(Number(row['工时']))) {
              errors.push('工时必须是数字')
            }
            if (row['满意度'] && (isNaN(Number(row['满意度'])) || Number(row['满意度']) < 1 || Number(row['满意度']) > 5)) {
              errors.push('满意度必须是1-5之间的数字')
            }
          }

          processedRow._valid = errors.length === 0
          return processedRow
        })

        // 只返回有效数据
        const validData = processedData.filter(item => item._valid)
        console.log(`${tableType}表解析完成：${validData.length}条有效记录`)
        resolve(validData)
      } catch (error) {
        console.error('Excel解析失败:', error)
        reject(error)
      }
    }

    reader.onerror = () => reject(new Error('读取文件失败'))
    reader.readAsArrayBuffer(file)
  })
}

// 生成仅线上任务数据（跳过B表时使用）
const generateOnlineOnlyTasks = () => {
  const onlineResults: any[] = []
  
  aTableData.value.forEach(aRow => {
    onlineResults.push({
      // A表数据
      workOrderId: aRow['工单编号'],
      title: `${aRow['对象']} - ${aRow['描述']}`,
      description: aRow['描述'],
      company: aRow['报单企业'] || '',
      location: aRow['位置'],
      contactPerson: aRow['报单人'],
      contactPhone: aRow['报单人电话'],
      reportTime: aRow['报单时间'],
      status: aRow['工单状态'],
      taskType: 'online_repair', // 强制设为线上任务
      priority: getPriority(aRow['优先级']),
      category: aRow['分类'],
      completionStatus: aRow['完成情况'] || aRow['工单状态'], // 新增完成情况字段
      
      // B表数据为空（跳过B表）
      assignee: null,
      responseTime: null,
      processTime: null,
      completeTime: null,
      faultDescription: null,
      solution: null,
      processingNote: null,
      actualHours: null,
      materialCost: 0,
      laborCost: 0,
      totalCost: 0,
      customerRating: null,
      satisfaction: null,
      remark: null,
      
      // 匹配状态（跳过B表）
      matched: false,
      matchKey: aRow._matchKey,
      isOnlineOnly: true // 标记为仅线上任务
    })
  })
  
  return onlineResults
}

const performABMatching = () => {
  const matchedResults: any[] = []
  
  // 为每个A表记录尝试匹配B表记录
  aTableData.value.forEach(aRow => {
    const matchingBRows = bTableData.value.filter(bRow => 
      aRow._matchKey === bRow._matchKey && aRow['工单编号'] === bRow['工单编号']
    )
    
    if (matchingBRows.length > 0) {
      // 成功匹配，合并A-B表数据
      matchingBRows.forEach(bRow => {
        matchedResults.push({
          // A表数据
          workOrderId: aRow['工单编号'],
          title: `${aRow['对象']} - ${aRow['描述']}`,
          description: aRow['描述'],
          company: aRow['报单企业'] || '',
          location: aRow['位置'],
          contactPerson: aRow['报单人'],
          contactPhone: aRow['报单人电话'],
          reportTime: aRow['报单时间'],
          status: aRow['工单状态'],
          taskType: getTaskType(aRow['类型']),
          priority: getPriority(aRow['优先级']),
          category: aRow['分类'],
          completionStatus: aRow['完成情况'] || aRow['工单状态'], // 新增完成情况字段
          
          // B表数据
          assignee: bRow['处理人'],
          responseTime: bRow['响应时间'],
          processTime: bRow['处理时间'],
          completeTime: bRow['完成时间'],
          faultDescription: bRow['故障描述'],
          solution: bRow['解决方案'],
          processingNote: bRow['处理说明'],
          actualHours: bRow['工时'] ? Number(bRow['工时']) : null,
          materialCost: bRow['材料费'] ? Number(bRow['材料费']) : 0,
          laborCost: bRow['人工费'] ? Number(bRow['人工费']) : 0,
          totalCost: bRow['总费用'] ? Number(bRow['总费用']) : 0,
          customerRating: bRow['客户评价'],
          satisfaction: bRow['满意度'] ? Number(bRow['满意度']) : null,
          remark: bRow['备注'],
          
          // 匹配状态
          matched: true,
          matchKey: aRow._matchKey
        })
      })
    } else {
      // 仅A表数据，没有匹配的B表（按线上单处理）
      matchedResults.push({
        // A表数据
        workOrderId: aRow['工单编号'],
        title: `${aRow['对象']} - ${aRow['描述']}`,
        description: aRow['描述'],
        company: aRow['报单企业'] || '',
        location: aRow['位置'],
        contactPerson: aRow['报单人'],
        contactPhone: aRow['报单人电话'],
        reportTime: aRow['报单时间'],
        status: aRow['工单状态'],
        taskType: 'online_repair', // 无B表数据时默认为线上任务
        priority: getPriority(aRow['优先级']),
        category: aRow['分类'],
        completionStatus: aRow['完成情况'] || aRow['工单状态'], // 新增完成情况字段
        
        // B表数据为空
        assignee: null,
        responseTime: null,
        processTime: null,
        completeTime: null,
        faultDescription: null,
        solution: null,
        processingNote: null,
        actualHours: null,
        materialCost: 0,
        laborCost: 0,
        totalCost: 0,
        customerRating: null,
        satisfaction: null,
        remark: null,
        
        // 匹配状态
        matched: false,
        matchKey: aRow._matchKey
      })
    }
  })
  
  return matchedResults
}

const getTaskType = (type: string): string => {
  if (!type) return 'online_repair'
  const typeText = type.toString().toLowerCase()
  if (typeText.includes('线下') || typeText.includes('现场')) {
    return 'offline_repair'
  } else if (typeText.includes('监控')) {
    return 'monitoring'
  } else if (typeText.includes('协助')) {
    return 'assistance'
  } else {
    return 'online_repair'
  }
}

const getPriority = (priority: string): string => {
  if (!priority) return 'medium'
  const priorityText = priority.toString()
  if (priorityText.includes('紧急') || priorityText.includes('高')) {
    return 'urgent'
  } else if (priorityText.includes('普通') || priorityText.includes('中')) {
    return 'medium'
  } else if (priorityText.includes('低')) {
    return 'low'
  }
  return 'medium'
}

const handleImport = async () => {
  try {
    importing.value = true
    
    console.log('准备导入数据...', {
      导入模式: bTableImportOption.value,
      匹配数据数量: matchedData.value.length,
      A表数量: aTableData.value.length,
      B表数量: bTableData.value.length
    })
    
    // 准备导入数据
    const importData = {
      matched_data: matchedData.value.map(item => ({
        // A表字段
        work_order_id: item.workOrderId,
        title: item.title,
        description: item.description,
        type: 'repair', // 默认为维修任务
        task_type: item.taskType,
        priority: item.priority,
        location: item.location,
        contact_person: item.contactPerson,
        contact_phone: item.contactPhone,
        company: item.company,
        report_time: item.reportTime,
        status: item.status,
        category: item.category,
        completion_status: item.completionStatus, // 新增完成情况字段
        
        // B表字段
        assignee: item.assignee,
        response_time: item.responseTime,
        process_time: item.processTime,
        complete_time: item.completeTime,
        fault_description: item.faultDescription,
        solution: item.solution,
        processing_note: item.processingNote,
        actual_hours: item.actualHours,
        material_cost: item.materialCost,
        labor_cost: item.laborCost,
        total_cost: item.totalCost,
        customer_rating: item.customerRating,
        satisfaction: item.satisfaction,
        remark: item.remark,
        
        // 匹配状态
        is_matched: item.matched,
        match_key: item.matchKey,
        is_online_only: item.isOnlineOnly || false // 是否为跳过B表的线上单
      })),
      import_type: bTableImportOption.value === 'skip' ? 'online_only' : 'ab_matched'
    }
    
    console.log('导入数据样本:', importData.matched_data.slice(0, 2))
    
    // 发送数据到后端
    const response = await tasksApi.importMaintenanceOrders(importData)
    
    const result = response.data || response
    importResult.success = result.success || 0
    importResult.failed = result.failed || 0
    importResult.matched = result.matched || 0
    importResult.partial = result.partial || 0
    importResult.errors = result.errors || []
    importResult.matched_assignees = result.matched_assignees || 0
    importResult.assignee_matches = result.assignee_matches || []
    
    console.log(`A-B表匹配导入完成：成功${importResult.success}条，失败${importResult.failed}条`)
    currentStep.value = 3

  } catch (error) {
    console.error('导入失败:', error)
    console.error('错误详情:', error.response?.data)
    if (error.response?.data?.message) {
      ElMessage.error(`导入失败: ${error.response.data.message}`)
    } else {
      ElMessage.error('A-B表匹配导入失败，请检查数据格式')
    }
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
    return 'A-B表匹配导入成功'
  } else if (importResult.success > 0 && importResult.failed > 0) {
    return 'A-B表匹配部分导入成功'
  } else {
    return 'A-B表匹配导入失败'
  }
}

const getResultSubTitle = () => {
  if (bTableImportOption.value === 'skip') {
    return `成功导入 ${importResult.success} 条线上任务记录，失败 ${importResult.failed} 条`
  }
  return `成功导入 ${importResult.success} 条记录，完整匹配 ${importResult.matched} 条，仅A表 ${importResult.partial} 条，失败 ${importResult.failed} 条`
}
</script>

<style scoped lang="scss">
@use '@/styles/variables.scss' as *;
@use '@/styles/mixins.scss' as *;
@use 'sass:color';

.import-task-dialog {
  .step-content {
    margin: 24px 0;
    min-height: 500px;
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

  .import-option-section {
    margin: 16px 0;

    .import-option-group {
      display: flex;
      flex-direction: column;
      gap: 12px;

      .el-radio {
        margin: 0;
        padding: 12px;
        border: 1px solid $border-color-lighter;
        border-radius: $border-radius-base;
        transition: all $transition-base;

        &:hover {
          border-color: $primary-color;
          background: color.adjust($primary-color, $lightness: 48%);
        }

        &.is-checked {
          border-color: $primary-color;
          background: color.adjust($primary-color, $lightness: 45%);
        }

        .option-content {
          margin-left: 8px;
          
          .option-title {
            font-weight: 500;
            font-size: 14px;
            color: $text-color-primary;
            margin-bottom: 4px;
          }
          
          .option-desc {
            font-size: 12px;
            color: $text-color-regular;
            line-height: 1.4;
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
    .matching-header {
      margin-bottom: 24px;

      .matching-stats {
        margin-top: 16px;
      }
    }

    .matched-preview {
      h4 {
        margin: 0 0 16px 0;
        color: $text-color-primary;
      }

      .preview-table {
        .work-order-info {
          .work-order-id {
            font-weight: 500;
            color: $text-color-primary;
            margin-bottom: 2px;
          }
          .company {
            font-size: 12px;
            color: $text-color-secondary;
          }
        }

        .fault-info {
          .object {
            font-weight: 500;
            color: $text-color-primary;
            margin-bottom: 2px;
          }
          .description {
            font-size: 12px;
            color: $text-color-regular;
            display: -webkit-box;
            -webkit-line-clamp: 2;
            -webkit-box-orient: vertical;
            overflow: hidden;
          }
        }

        .contact-info, .process-info {
          font-size: 12px;
          line-height: 1.4;
          
          > div:first-child {
            font-weight: 500;
            color: $text-color-primary;
            margin-bottom: 2px;
          }
          
          .phone, .work-hours {
            color: $text-color-secondary;
          }
          
          .completion-status {
            color: $text-color-primary;
            font-weight: 500;
          }
          
          .work-hours-default {
            color: $text-color-placeholder;
            font-size: 11px;
            font-style: italic;
          }
        }
      }
    }
  }

  .result-section {
    .result-stats {
      .result-stats > * + * {
        margin-top: 16px;
      }

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
        
        .match-list {
          margin: 0;
          padding-left: 20px;
          max-height: 200px;
          overflow-y: auto;

          li.match-item {
            margin-bottom: 4px;
            color: #67c23a;
            display: flex;
            align-items: center;
            gap: 8px;
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

@include respond-to(sm) {
  .import-task-dialog {
    .matching-header {
      .matching-stats {
        .el-row .el-col {
          margin-bottom: 12px;
        }
      }
    }
  }
}
</style>