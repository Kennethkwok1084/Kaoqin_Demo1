<template>
  <div class="desktop-repair-import">
    <div class="page-header">
      <div class="header-content">
        <div class="header-text">
          <h1>报修单AB表导入</h1>
          <p>导入A表（报修单总表）和B表（校园网维护记录）进行数据匹配</p>
        </div>
        <div class="header-actions">
          <a-button @click="$router.back()">
            返回
          </a-button>
        </div>
      </div>
    </div>

    <div class="import-content">
      <!-- 导入步骤指引 -->
      <div class="steps-panel">
        <a-steps :current="currentStep" class="import-steps">
          <a-step title="上传A表" description="上传报修单总表" />
          <a-step title="上传B表" description="上传校园网维护记录" />
          <a-step title="数据匹配" description="自动匹配两表数据" />
          <a-step title="预览确认" description="预览匹配结果" />
          <a-step title="完成导入" description="执行导入操作" />
        </a-steps>
      </div>

      <!-- Step 1: 上传A表 -->
      <div class="step-panel" v-if="currentStep === 0">
        <div class="step-content">
          <div class="upload-section">
            <div class="section-header">
              <h3>上传A表（报修单总表）</h3>
              <p>请上传包含所有报修单基础信息的Excel文件</p>
            </div>
            
            <div class="field-info">
              <h4>A表必需字段：</h4>
              <a-row :gutter="16">
                <a-col :span="8" v-for="field in aTableFields" :key="field.field">
                  <a-card size="small" :bordered="false" class="field-card">
                    <div class="field-name">{{ field.label }}</div>
                    <div class="field-desc">{{ field.description }}</div>
                  </a-card>
                </a-col>
              </a-row>
            </div>
            
            <a-upload-dragger
              v-model:file-list="aTableFileList"
              :before-upload="beforeUploadA"
              :custom-request="handleUploadA"
              :show-upload-list="false"
              accept=".xlsx,.xls"
              class="import-uploader"
            >
              <div class="upload-content">
                <p class="ant-upload-drag-icon">
                  <InboxOutlined />
                </p>
                <p class="ant-upload-text">点击或拖拽A表Excel文件到此区域上传</p>
                <p class="ant-upload-hint">
                  支持格式：.xlsx, .xls | 文件大小限制：50MB
                </p>
              </div>
            </a-upload-dragger>

            <!-- A表上传进度 -->
            <div v-if="aTableProgress > 0" class="upload-progress">
              <a-progress :percent="aTableProgress" :status="aTableStatus" />
              <p v-if="aTableStatus === 'active'">正在解析A表数据...</p>
              <p v-if="aTableStatus === 'success'">A表解析完成，共 {{ aTableData.length }} 条记录</p>
              <p v-if="aTableStatus === 'exception'">A表解析失败</p>
            </div>

            <!-- 已上传A表信息 -->
            <div v-if="aTableFile" class="uploaded-file">
              <a-card size="small">
                <div class="file-info">
                  <div class="file-icon">
                    <FileExcelOutlined style="font-size: 24px; color: #52c41a;" />
                  </div>
                  <div class="file-details">
                    <div class="file-name">{{ aTableFile.name }}</div>
                    <div class="file-stats">{{ aTableData.length }} 条记录</div>
                  </div>
                  <div class="file-actions">
                    <a-button size="small" @click="removeATableFile">
                      移除
                    </a-button>
                  </div>
                </div>
              </a-card>
            </div>
          </div>

          <div class="step-actions">
            <a-button 
              type="primary" 
              size="large" 
              @click="nextStep"
              :disabled="!aTableFile || aTableProgress < 100"
            >
              下一步，上传B表
            </a-button>
          </div>
        </div>
      </div>

      <!-- Step 2: 上传B表 -->
      <div class="step-panel" v-if="currentStep === 1">
        <div class="step-content">
          <div class="upload-section">
            <div class="section-header">
              <h3>上传B表（校园网维护记录）</h3>
              <p>请上传包含具体维护记录的Excel文件</p>
            </div>
            
            <div class="field-info">
              <h4>B表关键匹配字段：</h4>
              <a-alert
                message="数据匹配说明"
                type="info"
                show-icon
              >
                <template #description>
                  系统将以<strong>【报修人姓名 + 联系方式】</strong>为关键字段进行AB表匹配。
                  成功匹配的记录将自动更新任务属性（线上/线下），未匹配的A表记录将默认标记为"线上单"。
                </template>
              </a-alert>
            </div>
            
            <a-upload-dragger
              v-model:file-list="bTableFileList"
              :before-upload="beforeUploadB"
              :custom-request="handleUploadB"
              :show-upload-list="false"
              accept=".xlsx,.xls"
              class="import-uploader"
            >
              <div class="upload-content">
                <p class="ant-upload-drag-icon">
                  <InboxOutlined />
                </p>
                <p class="ant-upload-text">点击或拖拽B表Excel文件到此区域上传</p>
                <p class="ant-upload-hint">
                  支持格式：.xlsx, .xls | 文件大小限制：50MB
                </p>
              </div>
            </a-upload-dragger>

            <!-- B表上传进度 -->
            <div v-if="bTableProgress > 0" class="upload-progress">
              <a-progress :percent="bTableProgress" :status="bTableStatus" />
              <p v-if="bTableStatus === 'active'">正在解析B表数据...</p>
              <p v-if="bTableStatus === 'success'">B表解析完成，共 {{ bTableData.length }} 条记录</p>
              <p v-if="bTableStatus === 'exception'">B表解析失败</p>
            </div>

            <!-- 已上传B表信息 -->
            <div v-if="bTableFile" class="uploaded-file">
              <a-card size="small">
                <div class="file-info">
                  <div class="file-icon">
                    <FileExcelOutlined style="font-size: 24px; color: #1890ff;" />
                  </div>
                  <div class="file-details">
                    <div class="file-name">{{ bTableFile.name }}</div>
                    <div class="file-stats">{{ bTableData.length }} 条记录</div>
                  </div>
                  <div class="file-actions">
                    <a-button size="small" @click="removeBTableFile">
                      移除
                    </a-button>
                  </div>
                </div>
              </a-card>
            </div>

            <!-- A表和B表汇总 -->
            <div v-if="aTableFile && bTableFile" class="tables-summary">
              <a-row :gutter="16">
                <a-col :span="12">
                  <a-statistic title="A表记录数" :value="aTableData.length" />
                </a-col>
                <a-col :span="12">
                  <a-statistic title="B表记录数" :value="bTableData.length" />
                </a-col>
              </a-row>
            </div>
          </div>

          <div class="step-actions">
            <a-button size="large" @click="prevStep">
              上一步
            </a-button>
            <a-button 
              type="primary" 
              size="large" 
              @click="performMatching"
              :disabled="!bTableFile || bTableProgress < 100"
              :loading="matchingLoading"
            >
              {{ matchingLoading ? '匹配中...' : '开始数据匹配' }}
            </a-button>
          </div>
        </div>
      </div>

      <!-- Step 3: 数据匹配结果 -->
      <div class="step-panel" v-if="currentStep === 2">
        <div class="step-content">
          <div class="matching-section">
            <div class="matching-header">
              <h3>数据匹配结果</h3>
              <div class="matching-summary">
                <a-statistic title="总记录" :value="aTableData.length" />
                <a-statistic title="成功匹配" :value="matchedRecords" />
                <a-statistic title="未匹配" :value="unmatchedRecords" />
                <a-statistic title="匹配率" :value="matchRate" suffix="%" />
              </div>
            </div>

            <!-- 匹配统计图表 -->
            <div class="matching-charts">
              <a-row :gutter="16">
                <a-col :span="12">
                  <a-card title="匹配状态分布" size="small">
                    <div id="matchingChart" style="height: 200px;"></div>
                  </a-card>
                </a-col>
                <a-col :span="12">
                  <a-card title="任务类型分布" size="small">
                    <div id="taskTypeChart" style="height: 200px;"></div>
                  </a-card>
                </a-col>
              </a-row>
            </div>

            <!-- 匹配结果预览 -->
            <div class="matching-table">
              <a-tabs>
                <a-tab-pane key="all" tab="全部数据">
                  <a-table
                    :columns="matchingColumns"
                    :data-source="matchedData"
                    :scroll="{ x: 1500, y: 400 }"
                    :pagination="{
                      pageSize: 20,
                      showSizeChanger: true,
                      showQuickJumper: true
                    }"
                    row-key="index"
                    size="small"
                  >
                    <template #matchStatus="{ record }">
                      <a-tag :color="record.isMatched ? 'green' : 'orange'">
                        {{ record.isMatched ? '已匹配' : '未匹配' }}
                      </a-tag>
                    </template>
                    
                    <template #taskType="{ record }">
                      <a-tag :color="record.taskType === 'online' ? 'blue' : 'purple'">
                        {{ record.taskType === 'online' ? '线上单' : '线下单' }}
                      </a-tag>
                    </template>
                  </a-table>
                </a-tab-pane>
                
                <a-tab-pane key="matched" tab="已匹配数据">
                  <a-table
                    :columns="matchingColumns"
                    :data-source="matchedData.filter(r => r.isMatched)"
                    :scroll="{ x: 1500, y: 400 }"
                    :pagination="{ pageSize: 20 }"
                    row-key="index"
                    size="small"
                  />
                </a-tab-pane>
                
                <a-tab-pane key="unmatched" tab="未匹配数据">
                  <a-table
                    :columns="matchingColumns"
                    :data-source="matchedData.filter(r => !r.isMatched)"
                    :scroll="{ x: 1500, y: 400 }"
                    :pagination="{ pageSize: 20 }"
                    row-key="index"
                    size="small"
                  />
                </a-tab-pane>
              </a-tabs>
            </div>
          </div>

          <div class="step-actions">
            <a-button size="large" @click="prevStep">
              重新上传
            </a-button>
            <a-button 
              type="primary" 
              size="large" 
              @click="nextStep"
              :disabled="matchedData.length === 0"
            >
              确认匹配结果
            </a-button>
          </div>
        </div>
      </div>

      <!-- Step 4: 导入确认和执行 -->
      <div class="step-panel" v-if="currentStep === 3">
        <div class="step-content">
          <div class="import-confirm-section">
            <div class="confirm-header">
              <h3>确认导入</h3>
              <p>请确认以下数据无误后执行导入操作</p>
            </div>

            <!-- 导入选项 -->
            <div class="import-options">
              <a-checkbox-group v-model:value="importOptions">
                <a-checkbox value="overwrite">覆盖已存在的记录（基于工单编号）</a-checkbox>
                <a-checkbox value="skipDuplicates">跳过重复记录</a-checkbox>
                <a-checkbox value="autoAssign">自动分配处理人</a-checkbox>
              </a-checkbox-group>
            </div>

            <!-- 导入统计 -->
            <div class="import-stats">
              <a-row :gutter="24">
                <a-col :span="6">
                  <a-statistic title="待导入记录" :value="matchedData.length" />
                </a-col>
                <a-col :span="6">
                  <a-statistic title="线上任务" :value="onlineCount" />
                </a-col>
                <a-col :span="6">
                  <a-statistic title="线下任务" :value="offlineCount" />
                </a-col>
                <a-col :span="6">
                  <a-statistic title="预估工时" :value="estimatedHours" suffix="小时" />
                </a-col>
              </a-row>
            </div>

            <!-- 导入警告 -->
            <div v-if="unmatchedRecords > 0" class="import-warnings">
              <a-alert
                :message="`注意：有 ${unmatchedRecords} 条记录未匹配`"
                description="未匹配的记录将默认标记为线上单，您可以在导入后手动调整任务类型。"
                type="warning"
                show-icon
                closable
              />
            </div>
          </div>

          <div class="step-actions">
            <a-button size="large" @click="prevStep">
              上一步
            </a-button>
            <a-button 
              type="primary" 
              size="large" 
              @click="executeImport"
              :loading="importLoading"
              danger
            >
              {{ importLoading ? '导入中...' : `确认导入 ${matchedData.length} 条记录` }}
            </a-button>
          </div>
        </div>
      </div>

      <!-- Step 5: 导入结果 -->
      <div class="step-panel" v-if="currentStep === 4">
        <div class="step-content">
          <div class="result-section">
            <a-result
              :status="importResult.success ? 'success' : 'error'"
              :title="importResult.success ? '导入成功' : '导入失败'"
              :sub-title="importResult.message"
            >
              <template #extra>
                <div class="result-stats">
                  <a-statistic title="成功导入" :value="importResult.successCount || 0" />
                  <a-statistic title="失败记录" :value="importResult.errorCount || 0" />
                  <a-statistic title="跳过记录" :value="importResult.skipCount || 0" />
                </div>
              </template>
            </a-result>

            <!-- 错误详情 -->
            <div v-if="importResult.errors && importResult.errors.length > 0" class="error-details">
              <h4>错误详情：</h4>
              <a-list
                :data-source="importResult.errors"
                size="small"
                bordered
              >
                <template #renderItem="{ item }">
                  <a-list-item>
                    <a-tag color="red">第{{ item.row }}行</a-tag>
                    {{ item.message }}
                  </a-list-item>
                </template>
              </a-list>
            </div>
          </div>

          <div class="step-actions">
            <a-button size="large" @click="resetImport">
              重新导入
            </a-button>
            <a-button type="primary" size="large" @click="goToTaskList">
              查看任务列表
            </a-button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { message } from 'ant-design-vue'
import { api } from '@/api/client'
import * as XLSX from 'xlsx'
import * as echarts from 'echarts'
import {
  InboxOutlined,
  FileExcelOutlined
} from '@ant-design/icons-vue'

const router = useRouter()

// 响应式数据
const currentStep = ref(0)

// A表相关
const aTableFile = ref<File | null>(null)
const aTableFileList = ref([])
const aTableProgress = ref(0)
const aTableStatus = ref<'active' | 'success' | 'exception'>('active')
const aTableData = ref<any[]>([])

// B表相关
const bTableFile = ref<File | null>(null)
const bTableFileList = ref([])
const bTableProgress = ref(0)
const bTableStatus = ref<'active' | 'success' | 'exception'>('active')
const bTableData = ref<any[]>([])

// 匹配相关
const matchingLoading = ref(false)
const matchedData = ref<any[]>([])

// 导入相关
const importOptions = ref(['skipDuplicates'])
const importLoading = ref(false)
const importResult = reactive({
  success: false,
  message: '',
  successCount: 0,
  errorCount: 0,
  skipCount: 0,
  errors: [] as any[]
})

// A表字段配置
const aTableFields = [
  { field: 'workOrderId', label: '工单编号', description: '唯一标识符' },
  { field: 'reporterName', label: '报单人', description: '报修人姓名' },
  { field: 'reporterPhone', label: '报单人电话', description: '联系方式' },
  { field: 'location', label: '位置', description: '报修地点' },
  { field: 'description', label: '描述', description: '问题描述' },
  { field: 'reportTime', label: '报单时间', description: '报修时间' },
  { field: 'assigneeName', label: '处理人', description: '负责处理的人员' },
  { field: 'status', label: '工单状态', description: '当前状态' },
  { field: 'completionTime', label: '完工时间', description: '完成时间' }
]

// 匹配结果表格列
const matchingColumns = [
  { title: '序号', dataIndex: 'index', key: 'index', width: 70 },
  { title: '匹配状态', key: 'matchStatus', width: 100, slots: { customRender: 'matchStatus' } },
  { title: '任务类型', key: 'taskType', width: 100, slots: { customRender: 'taskType' } },
  { title: '工单编号', dataIndex: 'workOrderId', key: 'workOrderId', width: 120 },
  { title: '报修人', dataIndex: 'reporterName', key: 'reporterName', width: 100 },
  { title: '联系方式', dataIndex: 'reporterPhone', key: 'reporterPhone', width: 130 },
  { title: '报修位置', dataIndex: 'location', key: 'location', width: 150, ellipsis: true },
  { title: '问题描述', dataIndex: 'description', key: 'description', width: 200, ellipsis: true },
  { title: '报修时间', dataIndex: 'reportTime', key: 'reportTime', width: 160 },
  { title: '处理人', dataIndex: 'assigneeName', key: 'assigneeName', width: 100 }
]

// 计算属性
const matchedRecords = computed(() => {
  return matchedData.value.filter(record => record.isMatched).length
})

const unmatchedRecords = computed(() => {
  return matchedData.value.filter(record => !record.isMatched).length
})

const matchRate = computed(() => {
  if (matchedData.value.length === 0) return 0
  return Math.round((matchedRecords.value / matchedData.value.length) * 100)
})

const onlineCount = computed(() => {
  return matchedData.value.filter(record => record.taskType === 'online').length
})

const offlineCount = computed(() => {
  return matchedData.value.filter(record => record.taskType === 'offline').length
})

const estimatedHours = computed(() => {
  // 线上40分钟，线下100分钟
  return Math.round((onlineCount.value * 40 + offlineCount.value * 100) / 60)
})

// 步骤控制方法
const nextStep = () => {
  if (currentStep.value < 4) {
    currentStep.value++
    if (currentStep.value === 2) {
      nextTick(() => {
        renderCharts()
      })
    }
  }
}

const prevStep = () => {
  if (currentStep.value > 0) {
    currentStep.value--
  }
}

// A表上传处理
const beforeUploadA = (file: File) => {
  const isExcel = file.type === 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' || 
                  file.type === 'application/vnd.ms-excel'
  if (!isExcel) {
    message.error('只能上传Excel文件!')
    return false
  }
  
  const isLt50M = file.size / 1024 / 1024 < 50
  if (!isLt50M) {
    message.error('文件大小不能超过50MB!')
    return false
  }
  
  return false
}

const handleUploadA = ({ file }: any) => {
  aTableFile.value = file
  aTableProgress.value = 0
  aTableStatus.value = 'active'
  
  const reader = new FileReader()
  reader.onload = (e) => {
    try {
      const data = new Uint8Array(e.target?.result as ArrayBuffer)
      const workbook = XLSX.read(data, { type: 'array' })
      
      const firstSheetName = workbook.SheetNames[0]
      const worksheet = workbook.Sheets[firstSheetName]
      
      const jsonData = XLSX.utils.sheet_to_json(worksheet, { header: 1 })
      processATableData(jsonData)
      
      aTableProgress.value = 100
      aTableStatus.value = 'success'
      message.success('A表解析成功')
    } catch (error) {
      console.error('Parse A table error:', error)
      aTableProgress.value = 100
      aTableStatus.value = 'exception'
      message.error('A表解析失败，请检查文件格式')
    }
  }
  
  reader.onerror = () => {
    aTableProgress.value = 100
    aTableStatus.value = 'exception'
    message.error('A表文件读取失败')
  }
  
  // 模拟进度
  const interval = setInterval(() => {
    if (aTableProgress.value < 90) {
      aTableProgress.value += 10
    } else {
      clearInterval(interval)
    }
  }, 100)
  
  reader.readAsArrayBuffer(file)
}

// B表上传处理
const beforeUploadB = beforeUploadA

const handleUploadB = ({ file }: any) => {
  bTableFile.value = file
  bTableProgress.value = 0
  bTableStatus.value = 'active'
  
  const reader = new FileReader()
  reader.onload = (e) => {
    try {
      const data = new Uint8Array(e.target?.result as ArrayBuffer)
      const workbook = XLSX.read(data, { type: 'array' })
      
      const firstSheetName = workbook.SheetNames[0]
      const worksheet = workbook.Sheets[firstSheetName]
      
      const jsonData = XLSX.utils.sheet_to_json(worksheet, { header: 1 })
      processBTableData(jsonData)
      
      bTableProgress.value = 100
      bTableStatus.value = 'success'
      message.success('B表解析成功')
    } catch (error) {
      console.error('Parse B table error:', error)
      bTableProgress.value = 100
      bTableStatus.value = 'exception'
      message.error('B表解析失败，请检查文件格式')
    }
  }
  
  reader.onerror = () => {
    bTableProgress.value = 100
    bTableStatus.value = 'exception'
    message.error('B表文件读取失败')
  }
  
  // 模拟进度
  const interval = setInterval(() => {
    if (bTableProgress.value < 90) {
      bTableProgress.value += 10
    } else {
      clearInterval(interval)
    }
  }, 100)
  
  reader.readAsArrayBuffer(file)
}

// 处理A表数据
const processATableData = (rawData: any[]) => {
  if (!rawData || rawData.length < 2) {
    message.error('A表数据为空或格式错误')
    return
  }
  
  const headers = rawData[0]
  const dataRows = rawData.slice(1)
  
  // 字段映射
  const fieldMap: Record<string, string> = {
    '工单编号': 'workOrderId',
    '报单人': 'reporterName',
    '报单人电话': 'reporterPhone',
    '位置': 'location',
    '描述': 'description',
    '报单时间': 'reportTime',
    '处理人': 'assigneeName',
    '工单状态': 'status',
    '完工时间': 'completionTime',
    '报单企业': 'company',
    '紧急程度': 'priority',
    '维修评价': 'evaluation'
  }
  
  const processedData = dataRows.map((row: any[], index: number) => {
    const record: any = {
      index: index + 1,
      isMatched: false,
      taskType: 'online' // 默认线上单
    }
    
    headers.forEach((header: string, colIndex: number) => {
      const fieldName = fieldMap[header] || header
      record[fieldName] = row[colIndex] || ''
    })
    
    return record
  })
  
  aTableData.value = processedData
}

// 处理B表数据
const processBTableData = (rawData: any[]) => {
  if (!rawData || rawData.length < 2) {
    message.error('B表数据为空或格式错误')
    return
  }
  
  const headers = rawData[0]
  const dataRows = rawData.slice(1)
  
  const processedData = dataRows.map((row: any[], index: number) => {
    const record: any = { index: index + 1 }
    headers.forEach((header: string, colIndex: number) => {
      record[header] = row[colIndex] || ''
    })
    return record
  })
  
  bTableData.value = processedData
}

// 执行数据匹配
const performMatching = () => {
  matchingLoading.value = true
  
  setTimeout(() => {
    try {
      const matched = aTableData.value.map(aRecord => {
        // 查找B表中匹配的记录
        const bMatch = bTableData.value.find(bRecord => {
          const aKey = `${aRecord.reporterName}${aRecord.reporterPhone}`.replace(/\s+/g, '')
          const bKey = `${bRecord.reporterName || bRecord['报修人'] || ''}${bRecord.reporterPhone || bRecord['联系方式'] || ''}`.replace(/\s+/g, '')
          return aKey === bKey
        })
        
        if (bMatch) {
          aRecord.isMatched = true
          aRecord.taskType = 'offline' // 匹配成功的标记为线下单
          aRecord.bTableData = bMatch
        }
        
        return aRecord
      })
      
      matchedData.value = matched
      currentStep.value = 2
      message.success(`匹配完成，成功匹配 ${matchedRecords.value} 条记录`)
    } catch (error) {
      console.error('Matching error:', error)
      message.error('数据匹配失败')
    } finally {
      matchingLoading.value = false
    }
  }, 2000)
}

// 渲染图表
const renderCharts = () => {
  // 匹配状态图表
  const matchingChart = echarts.init(document.getElementById('matchingChart'))
  matchingChart.setOption({
    tooltip: { trigger: 'item' },
    series: [{
      type: 'pie',
      radius: ['40%', '70%'],
      data: [
        { value: matchedRecords.value, name: '已匹配' },
        { value: unmatchedRecords.value, name: '未匹配' }
      ],
      label: { show: false },
      emphasis: { itemStyle: { shadowBlur: 10, shadowOffsetX: 0, shadowColor: 'rgba(0, 0, 0, 0.5)' } }
    }]
  })
  
  // 任务类型图表
  const taskTypeChart = echarts.init(document.getElementById('taskTypeChart'))
  taskTypeChart.setOption({
    tooltip: { trigger: 'item' },
    series: [{
      type: 'pie',
      radius: ['40%', '70%'],
      data: [
        { value: onlineCount.value, name: '线上单' },
        { value: offlineCount.value, name: '线下单' }
      ],
      label: { show: false },
      emphasis: { itemStyle: { shadowBlur: 10, shadowOffsetX: 0, shadowColor: 'rgba(0, 0, 0, 0.5)' } }
    }]
  })
}

// 执行导入
const executeImport = async () => {
  try {
    importLoading.value = true
    
    const importData = matchedData.value.map(record => ({
      workOrderId: record.workOrderId,
      title: record.description?.substring(0, 100) || '报修任务',
      description: record.description,
      location: record.location,
      reporterName: record.reporterName,
      reporterPhone: record.reporterPhone,
      assigneeName: record.assigneeName,
      status: mapStatus(record.status),
      priority: mapPriority(record.priority),
      type: 'repair',
      isOffline: record.taskType === 'offline',
      reportTime: record.reportTime,
      completionTime: record.completionTime,
      evaluation: record.evaluation
    }))
    
    const response = await api.importRepairTasks({
      tasks: importData,
      options: {
        overwrite: importOptions.value.includes('overwrite'),
        skipDuplicates: importOptions.value.includes('skipDuplicates'),
        autoAssign: importOptions.value.includes('autoAssign')
      }
    })
    
    if (response.success) {
      importResult.success = true
      importResult.message = response.message || '导入成功'
      importResult.successCount = response.data?.successCount || importData.length
      importResult.errorCount = response.data?.errorCount || 0
      importResult.skipCount = response.data?.skipCount || 0
      importResult.errors = response.data?.errors || []
      
      currentStep.value = 4
      message.success(importResult.message)
    } else {
      throw new Error(response.message || '导入失败')
    }
  } catch (error: any) {
    console.error('Import error:', error)
    importResult.success = false
    importResult.message = error.message || '导入失败，请检查网络连接'
    importResult.errorCount = matchedData.value.length
    currentStep.value = 4
    message.error(importResult.message)
  } finally {
    importLoading.value = false
  }
}

// 状态映射
const mapStatus = (status: string) => {
  const statusMap: Record<string, string> = {
    '待处理': 'pending',
    '进行中': 'in_progress', 
    '已完成': 'completed',
    '已取消': 'cancelled'
  }
  return statusMap[status] || 'pending'
}

// 优先级映射
const mapPriority = (priority: string) => {
  const priorityMap: Record<string, string> = {
    '高': 'high',
    '中': 'medium',
    '低': 'low'
  }
  return priorityMap[priority] || 'medium'
}

// 移除文件
const removeATableFile = () => {
  aTableFile.value = null
  aTableProgress.value = 0
  aTableData.value = []
  aTableFileList.value = []
}

const removeBTableFile = () => {
  bTableFile.value = null
  bTableProgress.value = 0
  bTableData.value = []
  bTableFileList.value = []
  matchedData.value = []
}

// 重置导入
const resetImport = () => {
  currentStep.value = 0
  removeATableFile()
  removeBTableFile()
  Object.assign(importResult, {
    success: false,
    message: '',
    successCount: 0,
    errorCount: 0,
    skipCount: 0,
    errors: []
  })
}

// 跳转到任务列表
const goToTaskList = () => {
  router.push('/tasks')
}
</script>

<style scoped>
/* 桌面端报修单导入界面样式 */
.desktop-repair-import {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.page-header {
  background: white;
  border-radius: 12px;
  padding: 32px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.04);
  border: 1px solid #e8e9ea;
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-text h1 {
  margin: 0 0 8px;
  font-size: 28px;
  font-weight: 600;
  color: #1a1a1a;
}

.header-text p {
  margin: 0;
  font-size: 16px;
  color: #666666;
}

.import-content {
  background: white;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.04);
  border: 1px solid #e8e9ea;
  overflow: hidden;
  flex: 1;
  display: flex;
  flex-direction: column;
}

.steps-panel {
  padding: 32px;
  border-bottom: 1px solid #e8e9ea;
  background: #fafbfc;
}

.import-steps {
  max-width: 1000px;
  margin: 0 auto;
}

.step-panel {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.step-content {
  flex: 1;
  padding: 32px;
  display: flex;
  flex-direction: column;
  gap: 32px;
}

.upload-section {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.section-header h3 {
  margin: 0 0 8px;
  font-size: 20px;
  font-weight: 600;
  color: #1a1a1a;
}

.section-header p {
  margin: 0;
  color: #666666;
}

.field-info h4 {
  margin: 0 0 16px;
  font-size: 16px;
  font-weight: 500;
  color: #1a1a1a;
}

.field-card {
  background: #f8f9fa;
  border: 1px solid #e8e9ea;
  margin-bottom: 12px;
}

.field-name {
  font-weight: 500;
  color: #1a1a1a;
  margin-bottom: 4px;
}

.field-desc {
  font-size: 12px;
  color: #8c8c8c;
}

.import-uploader {
  background: #fafbfc;
  border: 2px dashed #d9d9d9;
  border-radius: 12px;
  transition: all 0.3s ease;
}

.import-uploader:hover {
  border-color: #667eea;
  background: #f6f8ff;
}

.upload-content {
  padding: 40px 20px;
  text-align: center;
}

.upload-progress {
  margin-top: 20px;
}

.upload-progress p {
  margin: 8px 0 0;
  text-align: center;
  font-size: 14px;
  color: #666666;
}

.uploaded-file {
  margin-top: 20px;
}

.file-info {
  display: flex;
  align-items: center;
  gap: 16px;
}

.file-details {
  flex: 1;
}

.file-name {
  font-size: 14px;
  font-weight: 500;
  color: #1a1a1a;
  margin-bottom: 4px;
}

.file-stats {
  font-size: 12px;
  color: #8c8c8c;
}

.tables-summary {
  margin-top: 24px;
  padding: 20px;
  background: #f8f9fa;
  border-radius: 8px;
}

.matching-section {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.matching-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.matching-header h3 {
  margin: 0;
  font-size: 20px;
  font-weight: 600;
  color: #1a1a1a;
}

.matching-summary {
  display: flex;
  gap: 32px;
  align-items: center;
}

.matching-charts {
  margin: 24px 0;
}

.matching-table {
  flex: 1;
  overflow: hidden;
}

.import-confirm-section {
  display: flex;
  flex-direction: column;
  gap: 32px;
}

.confirm-header h3 {
  margin: 0 0 8px;
  font-size: 20px;
  font-weight: 600;
  color: #1a1a1a;
}

.confirm-header p {
  margin: 0;
  color: #666666;
}

.import-options {
  padding: 20px;
  background: #f8f9fa;
  border-radius: 8px;
}

.import-stats {
  padding: 24px;
  background: #fafbfc;
  border-radius: 8px;
  border: 1px solid #e8e9ea;
}

.import-warnings {
  margin-top: 16px;
}

.result-section {
  text-align: center;
}

.result-stats {
  display: flex;
  justify-content: center;
  gap: 48px;
  margin-top: 24px;
}

.error-details {
  margin-top: 32px;
  text-align: left;
}

.error-details h4 {
  margin: 0 0 16px;
  font-size: 16px;
  font-weight: 500;
  color: #1a1a1a;
}

.step-actions {
  display: flex;
  justify-content: center;
  gap: 16px;
  padding-top: 32px;
  border-top: 1px solid #e8e9ea;
  margin-top: auto;
}

/* 统一样式 */
:deep(.ant-upload-drag-icon) {
  margin-bottom: 16px;
  font-size: 48px;
  color: #d9d9d9;
}

:deep(.ant-upload-text) {
  font-size: 16px;
  font-weight: 500;
  color: #1a1a1a;
  margin: 0 0 8px;
}

:deep(.ant-upload-hint) {
  font-size: 14px;
  color: #8c8c8c;
  margin: 0;
}

:deep(.ant-statistic-title) {
  font-size: 14px;
  color: #8c8c8c;
  font-weight: 500;
}

:deep(.ant-statistic-content-value) {
  font-size: 20px;
  font-weight: 600;
  color: #1a1a1a;
}

:deep(.ant-btn-lg) {
  height: 48px;
  padding: 0 24px;
  font-size: 16px;
  border-radius: 8px;
  font-weight: 500;
}

:deep(.ant-btn-primary) {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border: none;
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
}

:deep(.ant-btn-primary:hover) {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(102, 126, 234, 0.4);
}

:deep(.ant-steps-item-title) {
  font-weight: 500;
}

:deep(.ant-table-thead > tr > th) {
  background: #fafbfc;
  border-bottom: 2px solid #e8e9ea;
  font-weight: 600;
  color: #1a1a1a;
  font-size: 14px;
}

:deep(.ant-table-tbody > tr > td) {
  border-bottom: 1px solid #f0f0f0;
  padding: 12px 16px;
}

:deep(.ant-table-tbody > tr:hover > td) {
  background: #f8f9fa;
}

/* 响应式优化 */
@media (max-width: 1200px) {
  .header-content,
  .matching-header {
    flex-direction: column;
    gap: 20px;
    text-align: center;
  }
  
  .matching-summary {
    gap: 20px;
  }
  
  .result-stats {
    gap: 24px;
  }
}

@media (max-width: 768px) {
  .page-header,
  .step-content {
    padding: 20px;
  }
  
  .steps-panel {
    padding: 20px;
  }
  
  .field-info .ant-row {
    flex-direction: column;
  }
  
  .step-actions {
    flex-direction: column;
  }
  
  .matching-summary {
    flex-direction: column;
    gap: 16px;
  }
  
  .result-stats {
    flex-direction: column;
    gap: 16px;
  }
}
</style>