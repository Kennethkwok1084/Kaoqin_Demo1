<template>
  <div class="desktop-member-import">
    <div class="page-header">
      <div class="header-content">
        <div class="header-text">
          <h1>成员批量导入</h1>
          <p>通过Excel文件批量导入成员信息</p>
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
          <a-step title="下载模板" description="下载Excel导入模板" />
          <a-step title="填写数据" description="按模板格式填写成员信息" />
          <a-step title="上传文件" description="选择并上传Excel文件" />
          <a-step title="预览确认" description="预览导入数据并确认" />
          <a-step title="完成导入" description="执行导入操作" />
        </a-steps>
      </div>

      <!-- Step 1: 下载模板 -->
      <div class="step-panel" v-if="currentStep === 0">
        <div class="step-content">
          <div class="template-info">
            <div class="info-header">
              <h3>Excel导入模板下载</h3>
              <p>请先下载标准导入模板，按照模板格式填写成员信息</p>
            </div>
            
            <div class="template-preview">
              <h4>模板字段说明：</h4>
              <a-table 
                :columns="templateColumns" 
                :data-source="templateFields"
                :pagination="false"
                size="small"
                bordered
              />
            </div>

            <div class="template-notes">
              <a-alert
                message="重要提醒"
                type="warning"
                show-icon
              >
                <template #description>
                  <ul>
                    <li>请严格按照模板格式填写，不要修改表头</li>
                    <li>学号必须唯一，系统会自动检查重复</li>
                    <li>手机号格式：11位数字，以1开头</li>
                    <li>角色可填写：admin（管理员）或 member（普通成员）</li>
                    <li>状态可填写：在职 或 离职</li>
                  </ul>
                </template>
              </a-alert>
            </div>
          </div>
          
          <div class="step-actions">
            <a-button 
              type="primary" 
              size="large"
              :icon="h(DownloadOutlined)"
              @click="downloadTemplate"
              :loading="downloadLoading"
            >
              下载Excel模板
            </a-button>
            <a-button size="large" @click="nextStep">
              已有模板，下一步
            </a-button>
          </div>
        </div>
      </div>

      <!-- Step 2: 上传文件 -->
      <div class="step-panel" v-if="currentStep === 1">
        <div class="step-content">
          <div class="upload-section">
            <h3>上传Excel文件</h3>
            <p>请选择填写完成的Excel文件进行上传</p>
            
            <a-upload-dragger
              v-model:file-list="fileList"
              :before-upload="beforeUpload"
              :custom-request="handleUpload"
              :show-upload-list="false"
              accept=".xlsx,.xls"
              class="import-uploader"
            >
              <div class="upload-content">
                <p class="ant-upload-drag-icon">
                  <InboxOutlined />
                </p>
                <p class="ant-upload-text">点击或拖拽Excel文件到此区域上传</p>
                <p class="ant-upload-hint">
                  支持格式：.xlsx, .xls | 文件大小限制：10MB
                </p>
              </div>
            </a-upload-dragger>

            <!-- 上传进度 -->
            <div v-if="uploadProgress > 0" class="upload-progress">
              <a-progress :percent="uploadProgress" :status="uploadStatus" />
              <p v-if="uploadStatus === 'active'">正在解析Excel文件...</p>
              <p v-if="uploadStatus === 'success'">文件解析完成</p>
              <p v-if="uploadStatus === 'exception'">文件解析失败</p>
            </div>

            <!-- 已上传文件信息 -->
            <div v-if="uploadedFile" class="uploaded-file">
              <a-card size="small">
                <div class="file-info">
                  <div class="file-icon">
                    <FileExcelOutlined style="font-size: 24px; color: #52c41a;" />
                  </div>
                  <div class="file-details">
                    <div class="file-name">{{ uploadedFile.name }}</div>
                    <div class="file-size">{{ formatFileSize(uploadedFile.size) }}</div>
                  </div>
                  <div class="file-actions">
                    <a-button size="small" @click="removeFile">
                      移除
                    </a-button>
                  </div>
                </div>
              </a-card>
            </div>
          </div>

          <div class="step-actions">
            <a-button size="large" @click="prevStep">
              上一步
            </a-button>
            <a-button 
              type="primary" 
              size="large" 
              @click="nextStep"
              :disabled="!uploadedFile || uploadProgress < 100"
            >
              下一步，预览数据
            </a-button>
          </div>
        </div>
      </div>

      <!-- Step 3: 数据预览 -->
      <div class="step-panel" v-if="currentStep === 2">
        <div class="step-content">
          <div class="preview-section">
            <div class="preview-header">
              <h3>数据预览</h3>
              <div class="preview-summary">
                <a-statistic title="总记录数" :value="importData.length" />
                <a-statistic title="有效记录" :value="validRecords" />
                <a-statistic title="错误记录" :value="errorRecords" />
              </div>
            </div>

            <!-- 导入选项 -->
            <div class="import-options">
              <a-checkbox v-model:checked="skipDuplicates">
                跳过重复记录（基于学号判断）
              </a-checkbox>
            </div>

            <!-- 数据预览表格 -->
            <div class="preview-table">
              <a-table
                :columns="previewColumns"
                :data-source="importData"
                :scroll="{ x: 1200, y: 400 }"
                :pagination="{
                  pageSize: 50,
                  showSizeChanger: true,
                  showQuickJumper: true
                }"
                row-key="index"
                size="small"
              >
                <template #status="{ record }">
                  <a-tag v-if="record.errors.length === 0" color="green">
                    有效
                  </a-tag>
                  <a-tag v-else color="red">
                    错误
                  </a-tag>
                </template>
                
                <template #errors="{ record }">
                  <div v-if="record.errors.length > 0">
                    <a-tag 
                      v-for="error in record.errors" 
                      :key="error"
                      color="red" 
                      size="small"
                    >
                      {{ error }}
                    </a-tag>
                  </div>
                </template>
              </a-table>
            </div>

            <!-- 错误汇总 -->
            <div v-if="errorRecords > 0" class="error-summary">
              <a-alert
                message="数据验证错误"
                :description="`发现 ${errorRecords} 条错误记录，请检查并修正后重新上传`"
                type="error"
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
              @click="confirmImport"
              :disabled="validRecords === 0"
              :loading="importLoading"
            >
              {{ importLoading ? '导入中...' : `确认导入 ${validRecords} 条记录` }}
            </a-button>
          </div>
        </div>
      </div>

      <!-- Step 4: 导入结果 -->
      <div class="step-panel" v-if="currentStep === 3">
        <div class="step-content">
          <div class="result-section">
            <div class="result-status">
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
            </div>

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
            <a-button type="primary" size="large" @click="goToMemberList">
              查看成员列表
            </a-button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, h } from 'vue'
import { useRouter } from 'vue-router'
import { message } from 'ant-design-vue'
import { api } from '@/api/client'
import * as XLSX from 'xlsx'
import {
  DownloadOutlined,
  InboxOutlined,
  FileExcelOutlined
} from '@ant-design/icons-vue'

const router = useRouter()

// 响应式数据
const currentStep = ref(0)
const downloadLoading = ref(false)
const uploadProgress = ref(0)
const uploadStatus = ref<'active' | 'success' | 'exception'>('active')
const uploadedFile = ref<File | null>(null)
const fileList = ref([])
const importData = ref<any[]>([])
const skipDuplicates = ref(true)
const importLoading = ref(false)

// 导入结果
const importResult = reactive({
  success: false,
  message: '',
  successCount: 0,
  errorCount: 0,
  skipCount: 0,
  errors: [] as any[]
})

// 模板字段配置
const templateFields = [
  { field: 'name', label: '姓名', required: true, example: '张三', description: '成员真实姓名' },
  { field: 'studentId', label: '学号', required: true, example: '20200001', description: '8-12位数字，必须唯一' },
  { field: 'username', label: '用户名', required: true, example: 'zhangsan', description: '登录用户名，3-20位字符' },
  { field: 'password', label: '密码', required: true, example: '123456', description: '登录密码，6-20位字符' },
  { field: 'phone', label: '手机号', required: true, example: '13800138000', description: '11位手机号码' },
  { field: 'department', label: '部门', required: true, example: '网络部', description: '所属部门' },
  { field: 'className', label: '班级', required: true, example: '计算机2020-1班', description: '所属班级' },
  { field: 'role', label: '角色', required: true, example: 'member', description: 'admin或member' },
  { field: 'status', label: '状态', required: false, example: '在职', description: '在职或离职，默认在职' },
  { field: 'joinDate', label: '入职日期', required: false, example: '2024-01-01', description: 'YYYY-MM-DD格式' }
]

// 表格列配置
const templateColumns = [
  { title: '字段名', dataIndex: 'field', key: 'field', width: 100 },
  { title: '中文名', dataIndex: 'label', key: 'label', width: 100 },
  { title: '必填', dataIndex: 'required', key: 'required', width: 80,
    customRender: ({ text }: any) => text ? '是' : '否' },
  { title: '示例', dataIndex: 'example', key: 'example', width: 120 },
  { title: '说明', dataIndex: 'description', key: 'description', ellipsis: true }
]

const previewColumns = [
  { title: '行号', dataIndex: 'index', key: 'index', width: 80 },
  { title: '状态', key: 'status', width: 80, slots: { customRender: 'status' } },
  { title: '姓名', dataIndex: 'name', key: 'name', width: 100 },
  { title: '学号', dataIndex: 'studentId', key: 'studentId', width: 120 },
  { title: '用户名', dataIndex: 'username', key: 'username', width: 120 },
  { title: '手机号', dataIndex: 'phone', key: 'phone', width: 130 },
  { title: '部门', dataIndex: 'department', key: 'department', width: 100 },
  { title: '班级', dataIndex: 'className', key: 'className', width: 150 },
  { title: '角色', dataIndex: 'role', key: 'role', width: 80 },
  { title: '错误信息', key: 'errors', width: 200, slots: { customRender: 'errors' } }
]

// 计算属性
const validRecords = computed(() => {
  return importData.value.filter(record => record.errors.length === 0).length
})

const errorRecords = computed(() => {
  return importData.value.filter(record => record.errors.length > 0).length
})

// 步骤控制方法
const nextStep = () => {
  if (currentStep.value < 3) {
    currentStep.value++
  }
}

const prevStep = () => {
  if (currentStep.value > 0) {
    currentStep.value--
  }
}

// 下载模板
const downloadTemplate = () => {
  downloadLoading.value = true
  
  try {
    // 创建模板数据
    const templateData = [
      {
        name: '张三',
        studentId: '20200001',
        username: 'zhangsan',
        password: '123456',
        phone: '13800138000',
        department: '网络部',
        className: '计算机2020-1班',
        role: 'member',
        status: '在职',
        joinDate: '2024-01-01'
      },
      {
        name: '李四',
        studentId: '20200002',
        username: 'lisi',
        password: '123456',
        phone: '13800138001',
        department: '技术部',
        className: '软件工程2020-2班',
        role: 'member',
        status: '在职',
        joinDate: '2024-01-02'
      }
    ]
    
    // 创建工作簿
    const wb = XLSX.utils.book_new()
    
    // 创建工作表
    const ws = XLSX.utils.json_to_sheet(templateData)
    
    // 设置列宽
    const colWidths = [
      { wch: 10 }, // name
      { wch: 12 }, // studentId
      { wch: 15 }, // username
      { wch: 10 }, // password
      { wch: 15 }, // phone
      { wch: 12 }, // department
      { wch: 20 }, // className
      { wch: 10 }, // role
      { wch: 8 },  // status
      { wch: 12 }  // joinDate
    ]
    ws['!cols'] = colWidths
    
    // 添加工作表到工作簿
    XLSX.utils.book_append_sheet(wb, ws, '成员信息')
    
    // 下载文件
    XLSX.writeFile(wb, '成员导入模板.xlsx')
    message.success('模板下载成功')
  } catch (error) {
    console.error('Download template error:', error)
    message.error('模板下载失败')
  } finally {
    downloadLoading.value = false
  }
}

// 文件上传处理
const beforeUpload = (file: File) => {
  const isExcel = file.type === 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' || 
                  file.type === 'application/vnd.ms-excel'
  if (!isExcel) {
    message.error('只能上传Excel文件!')
    return false
  }
  
  const isLt10M = file.size / 1024 / 1024 < 10
  if (!isLt10M) {
    message.error('文件大小不能超过10MB!')
    return false
  }
  
  return false // 阻止自动上传
}

const handleUpload = ({ file }: any) => {
  uploadedFile.value = file
  uploadProgress.value = 0
  uploadStatus.value = 'active'
  
  const reader = new FileReader()
  reader.onload = (e) => {
    try {
      const data = new Uint8Array(e.target?.result as ArrayBuffer)
      const workbook = XLSX.read(data, { type: 'array' })
      
      // 读取第一个工作表
      const firstSheetName = workbook.SheetNames[0]
      const worksheet = workbook.Sheets[firstSheetName]
      
      // 转换为JSON数据
      const jsonData = XLSX.utils.sheet_to_json(worksheet, { header: 1 })
      
      // 处理数据
      processImportData(jsonData)
      
      uploadProgress.value = 100
      uploadStatus.value = 'success'
      message.success('文件解析成功')
    } catch (error) {
      console.error('Parse file error:', error)
      uploadProgress.value = 100
      uploadStatus.value = 'exception'
      message.error('文件解析失败，请检查文件格式')
    }
  }
  
  reader.onerror = () => {
    uploadProgress.value = 100
    uploadStatus.value = 'exception'
    message.error('文件读取失败')
  }
  
  // 模拟进度
  const interval = setInterval(() => {
    if (uploadProgress.value < 90) {
      uploadProgress.value += 10
    } else {
      clearInterval(interval)
    }
  }, 100)
  
  reader.readAsArrayBuffer(file)
}

// 处理导入数据
const processImportData = (rawData: any[]) => {
  if (!rawData || rawData.length < 2) {
    message.error('文件数据为空或格式错误')
    return
  }
  
  // 获取表头
  const headers = rawData[0]
  const dataRows = rawData.slice(1)
  
  // 字段映射
  const fieldMap: Record<string, string> = {
    '姓名': 'name',
    'name': 'name',
    '学号': 'studentId',
    'studentId': 'studentId',
    '用户名': 'username',
    'username': 'username',
    '密码': 'password',
    'password': 'password',
    '手机号': 'phone',
    'phone': 'phone',
    '部门': 'department',
    'department': 'department',
    '班级': 'className',
    'className': 'className',
    '角色': 'role',
    'role': 'role',
    '状态': 'status',
    'status': 'status',
    '入职日期': 'joinDate',
    'joinDate': 'joinDate'
  }
  
  // 转换数据
  const processedData = dataRows.map((row: any[], index: number) => {
    const record: any = {
      index: index + 2, // Excel行号（从第2行开始）
      errors: []
    }
    
    // 映射字段
    headers.forEach((header: string, colIndex: number) => {
      const fieldName = fieldMap[header]
      if (fieldName) {
        record[fieldName] = row[colIndex] || ''
      }
    })
    
    // 数据验证
    validateRecord(record)
    
    return record
  })
  
  importData.value = processedData
}

// 验证记录
const validateRecord = (record: any) => {
  const errors: string[] = []
  
  // 必填字段验证
  const requiredFields = ['name', 'studentId', 'username', 'password', 'phone', 'department', 'className', 'role']
  requiredFields.forEach(field => {
    if (!record[field] || record[field].toString().trim() === '') {
      const fieldLabel = templateFields.find(f => f.field === field)?.label || field
      errors.push(`${fieldLabel}不能为空`)
    }
  })
  
  // 格式验证
  if (record.studentId && !/^\d{8,12}$/.test(record.studentId.toString())) {
    errors.push('学号格式错误，应为8-12位数字')
  }
  
  if (record.phone && !/^1[3-9]\d{9}$/.test(record.phone.toString())) {
    errors.push('手机号格式错误')
  }
  
  if (record.username) {
    const username = record.username.toString()
    if (username.length < 3 || username.length > 20) {
      errors.push('用户名长度应为3-20字符')
    }
    if (!/^[a-zA-Z0-9_]+$/.test(username)) {
      errors.push('用户名只能包含字母、数字和下划线')
    }
  }
  
  if (record.password && (record.password.toString().length < 6 || record.password.toString().length > 20)) {
    errors.push('密码长度应为6-20字符')
  }
  
  if (record.role && !['admin', 'member'].includes(record.role.toString().toLowerCase())) {
    errors.push('角色只能是admin或member')
  }
  
  record.errors = errors
}

// 移除文件
const removeFile = () => {
  uploadedFile.value = null
  uploadProgress.value = 0
  importData.value = []
  fileList.value = []
}

// 格式化文件大小
const formatFileSize = (bytes: number) => {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

// 确认导入
const confirmImport = async () => {
  try {
    importLoading.value = true
    
    // 过滤有效记录
    const validData = importData.value
      .filter(record => record.errors.length === 0)
      .map(record => ({
        name: record.name,
        studentId: record.studentId,
        username: record.username,
        password: record.password,
        phone: record.phone,
        department: record.department,
        className: record.className,
        role: record.role.toLowerCase(),
        isActive: record.status ? record.status === '在职' : true,
        joinDate: record.joinDate || new Date().toISOString().split('T')[0]
      }))
    
    const response = await api.importMembers({
      skipDuplicates: skipDuplicates.value,
      members: validData
    })
    
    if (response.success) {
      importResult.success = true
      importResult.message = response.message || '导入成功'
      importResult.successCount = response.data?.successCount || validData.length
      importResult.errorCount = response.data?.errorCount || 0
      importResult.skipCount = response.data?.skipCount || 0
      importResult.errors = response.data?.errors || []
      
      currentStep.value = 3
      message.success(importResult.message)
    } else {
      throw new Error(response.message || '导入失败')
    }
  } catch (error: any) {
    console.error('Import error:', error)
    importResult.success = false
    importResult.message = error.message || '导入失败，请检查网络连接'
    importResult.errorCount = validRecords.value
    currentStep.value = 3
    message.error(importResult.message)
  } finally {
    importLoading.value = false
  }
}

// 重置导入
const resetImport = () => {
  currentStep.value = 0
  uploadedFile.value = null
  uploadProgress.value = 0
  importData.value = []
  fileList.value = []
  Object.assign(importResult, {
    success: false,
    message: '',
    successCount: 0,
    errorCount: 0,
    skipCount: 0,
    errors: []
  })
}

// 跳转到成员列表
const goToMemberList = () => {
  router.push('/members')
}
</script>

<style scoped>
/* 桌面端成员导入界面样式 */
.desktop-member-import {
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

.header-actions {
  display: flex;
  gap: 12px;
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
  max-width: 800px;
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

.template-info {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.info-header h3 {
  margin: 0 0 8px;
  font-size: 20px;
  font-weight: 600;
  color: #1a1a1a;
}

.info-header p {
  margin: 0;
  color: #666666;
}

.template-preview h4 {
  margin: 0 0 16px;
  font-size: 16px;
  font-weight: 500;
  color: #1a1a1a;
}

.template-notes {
  background: #fff7e6;
  border-radius: 8px;
  padding: 16px;
}

.template-notes ul {
  margin: 0;
  padding-left: 20px;
}

.template-notes li {
  margin: 4px 0;
  color: #666666;
}

.upload-section {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.upload-section h3 {
  margin: 0;
  font-size: 20px;
  font-weight: 600;
  color: #1a1a1a;
}

.upload-section p {
  margin: 0;
  color: #666666;
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

.file-size {
  font-size: 12px;
  color: #8c8c8c;
}

.preview-section {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.preview-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.preview-header h3 {
  margin: 0;
  font-size: 20px;
  font-weight: 600;
  color: #1a1a1a;
}

.preview-summary {
  display: flex;
  gap: 32px;
  align-items: center;
}

:deep(.ant-statistic-title) {
  font-size: 14px;
  color: #8c8c8c;
  font-weight: 500;
}

:deep(.ant-statistic-content-value) {
  font-size: 24px;
  font-weight: 600;
  color: #1a1a1a;
}

.import-options {
  padding: 16px;
  background: #f8f9fa;
  border-radius: 8px;
}

.preview-table {
  flex: 1;
  overflow: hidden;
}

.error-summary {
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

/* 按钮样式优化 */
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

/* 步骤条样式优化 */
:deep(.ant-steps-item-title) {
  font-weight: 500;
}

:deep(.ant-steps-item-description) {
  color: #8c8c8c;
}

/* 表格样式优化 */
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
  .header-content {
    flex-direction: column;
    gap: 20px;
    text-align: center;
  }
  
  .preview-header {
    flex-direction: column;
    gap: 20px;
  }
  
  .preview-summary {
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
  
  .import-steps {
    max-width: none;
  }
  
  :deep(.ant-steps-vertical .ant-steps-item-content) {
    min-height: 48px;
  }
  
  .step-actions {
    flex-direction: column;
  }
  
  .preview-summary {
    flex-direction: column;
    gap: 16px;
  }
  
  .result-stats {
    flex-direction: column;
    gap: 16px;
  }
}
</style>