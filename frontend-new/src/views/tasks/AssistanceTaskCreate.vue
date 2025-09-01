<template>
  <div class="desktop-assistance-create">
    <div class="page-header">
      <div class="header-content">
        <div class="header-text">
          <h1>协助任务登记</h1>
          <p>自主登记协助任务，提交后需等待管理员审核</p>
        </div>
        <div class="header-actions">
          <a-button @click="$router.back()">
            返回
          </a-button>
        </div>
      </div>
    </div>

    <div class="create-content">
      <a-row :gutter="24">
        <!-- 任务表单 -->
        <a-col :xs="24" :lg="16">
          <div class="form-panel">
            <div class="panel-title">
              <h3>协助任务信息</h3>
              <p>请详细填写协助任务的相关信息</p>
            </div>
            
            <a-form
              ref="formRef"
              :model="formData"
              :rules="formRules"
              layout="vertical"
              @finish="handleSubmit"
            >
              <a-form-item label="任务标题" name="title" required>
                <a-input
                  v-model:value="formData.title"
                  placeholder="简要描述协助任务内容，如：协助网络维护、技术支持等"
                  size="large"
                />
              </a-form-item>

              <a-row :gutter="16">
                <a-col :span="12">
                  <a-form-item label="协助部门" name="assistedDepartment" required>
                    <a-select
                      v-model:value="formData.assistedDepartment"
                      placeholder="选择协助的部门"
                      size="large"
                      show-search
                      :filter-option="filterOption"
                    >
                      <a-select-option 
                        v-for="dept in departmentList" 
                        :key="dept.value" 
                        :value="dept.value"
                      >
                        {{ dept.label }}
                      </a-select-option>
                    </a-select>
                  </a-form-item>
                </a-col>
                <a-col :span="12">
                  <a-form-item label="协助人员" name="assistedPerson">
                    <a-input
                      v-model:value="formData.assistedPerson"
                      placeholder="被协助的具体人员（可选）"
                      size="large"
                    />
                  </a-form-item>
                </a-col>
              </a-row>

              <a-form-item label="协助地点" name="location" required>
                <a-input
                  v-model:value="formData.location"
                  placeholder="详细的协助工作地点"
                  size="large"
                />
              </a-form-item>

              <a-form-item label="协助日期" name="assistanceDate" required>
                <a-date-picker
                  v-model:value="formData.assistanceDate"
                  placeholder="选择协助工作日期"
                  style="width: 100%"
                  size="large"
                  :disabled-date="disabledDate"
                />
              </a-form-item>

              <a-form-item label="工作时间" required>
                <div class="time-input-section">
                  <a-radio-group v-model:value="timeInputType" style="margin-bottom: 16px;">
                    <a-radio value="timeRange">按时间段</a-radio>
                    <a-radio value="duration">按工作时长</a-radio>
                  </a-radio-group>
                  
                  <div v-if="timeInputType === 'timeRange'">
                    <a-row :gutter="16">
                      <a-col :span="12">
                        <a-form-item name="startTime" label="开始时间">
                          <a-time-picker
                            v-model:value="formData.startTime"
                            placeholder="选择开始时间"
                            format="HH:mm"
                            style="width: 100%"
                            size="large"
                          />
                        </a-form-item>
                      </a-col>
                      <a-col :span="12">
                        <a-form-item name="endTime" label="结束时间">
                          <a-time-picker
                            v-model:value="formData.endTime"
                            placeholder="选择结束时间"
                            format="HH:mm"
                            style="width: 100%"
                            size="large"
                          />
                        </a-form-item>
                      </a-col>
                    </a-row>
                    <div v-if="calculatedDuration" class="calculated-duration">
                      <a-tag color="blue">计算工时：{{ calculatedDuration }} 小时</a-tag>
                    </div>
                  </div>
                  
                  <div v-else>
                    <a-form-item name="workHours" label="工作时长（小时）">
                      <a-input-number
                        v-model:value="formData.workHours"
                        :min="0.5"
                        :max="12"
                        :step="0.5"
                        placeholder="输入工作时长"
                        style="width: 100%"
                        size="large"
                      >
                        <template #addonAfter>小时</template>
                      </a-input-number>
                    </a-form-item>
                  </div>
                </div>
              </a-form-item>

              <a-form-item label="任务描述" name="description" required>
                <a-textarea
                  v-model:value="formData.description"
                  placeholder="详细描述协助任务的具体内容、过程、结果等"
                  :rows="4"
                  show-count
                  :maxlength="500"
                />
              </a-form-item>

              <a-form-item label="补充说明" name="remarks">
                <a-textarea
                  v-model:value="formData.remarks"
                  placeholder="其他需要说明的信息（可选）"
                  :rows="2"
                  show-count
                  :maxlength="200"
                />
              </a-form-item>

              <a-form-item label="相关附件" name="attachments">
                <a-upload
                  v-model:file-list="attachmentFileList"
                  :custom-request="handleFileUpload"
                  :before-upload="beforeFileUpload"
                  :on-remove="handleFileRemove"
                  :multiple="true"
                  :max-count="5"
                >
                  <a-button :icon="h(UploadOutlined)">上传附件</a-button>
                </a-upload>
                <div class="upload-tips">
                  <a-typography-text type="secondary" style="font-size: 12px;">
                    支持格式：图片、PDF、Word、Excel等 | 单个文件不超过10MB | 最多5个文件
                  </a-typography-text>
                </div>
              </a-form-item>

              <!-- 提醒信息 -->
              <a-alert
                message="提交提醒"
                type="info"
                show-icon
                style="margin-bottom: 24px;"
              >
                <template #description>
                  <ul style="margin: 0; padding-left: 20px;">
                    <li>协助任务提交后需要管理员审核通过才能计入工时</li>
                    <li>请确保填写的信息准确无误，审核通过后不可修改</li>
                    <li>建议上传相关工作证明材料以加快审核速度</li>
                  </ul>
                </template>
              </a-alert>

              <div class="form-actions">
                <a-space>
                  <a-button size="large" @click="resetForm">
                    重置
                  </a-button>
                  <a-button size="large" @click="saveDraft" :loading="draftLoading">
                    保存草稿
                  </a-button>
                  <a-button 
                    type="primary" 
                    size="large" 
                    html-type="submit"
                    :loading="submitLoading"
                  >
                    提交审核
                  </a-button>
                </a-space>
              </div>
            </a-form>
          </div>
        </a-col>

        <!-- 侧边栏信息 -->
        <a-col :xs="24" :lg="8">
          <div class="sidebar">
            <!-- 填写指南 -->
            <a-card title="填写指南" size="small" style="margin-bottom: 16px;">
              <div class="guide-list">
                <div class="guide-item">
                  <div class="guide-title">任务标题</div>
                  <div class="guide-desc">简明扼要，便于管理员快速了解</div>
                </div>
                <div class="guide-item">
                  <div class="guide-title">协助部门</div>
                  <div class="guide-desc">选择您协助的具体部门</div>
                </div>
                <div class="guide-item">
                  <div class="guide-title">工作时间</div>
                  <div class="guide-desc">可按时间段或总时长填写</div>
                </div>
                <div class="guide-item">
                  <div class="guide-title">任务描述</div>
                  <div class="guide-desc">详细描述工作内容和成果</div>
                </div>
              </div>
            </a-card>

            <!-- 我的协助任务 -->
            <a-card title="我的协助任务" size="small">
              <div class="my-tasks-summary">
                <a-row :gutter="8">
                  <a-col :span="8">
                    <a-statistic title="本月提交" :value="myTasksStats.submitted" />
                  </a-col>
                  <a-col :span="8">
                    <a-statistic title="已通过" :value="myTasksStats.approved" />
                  </a-col>
                  <a-col :span="8">
                    <a-statistic title="待审核" :value="myTasksStats.pending" />
                  </a-col>
                </a-row>
                
                <div style="margin-top: 16px;">
                  <a-button type="link" size="small" @click="$router.push('/tasks/assistance/my')">
                    查看我的任务 →
                  </a-button>
                </div>
              </div>
            </a-card>
          </div>
        </a-col>
      </a-row>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, h } from 'vue'
import { useRouter } from 'vue-router'
import { message, type FormInstance } from 'ant-design-vue'
import { api } from '@/api/client'
import dayjs, { type Dayjs } from 'dayjs'
import {
  UploadOutlined
} from '@ant-design/icons-vue'

const router = useRouter()

// 响应式数据
const formRef = ref<FormInstance>()
const submitLoading = ref(false)
const draftLoading = ref(false)
const attachmentFileList = ref([])
const timeInputType = ref('timeRange')

// 表单数据
const formData = reactive({
  title: '',
  assistedDepartment: '',
  assistedPerson: '',
  location: '',
  assistanceDate: null as Dayjs | null,
  startTime: null as Dayjs | null,
  endTime: null as Dayjs | null,
  workHours: null as number | null,
  description: '',
  remarks: '',
  attachments: [] as string[]
})

// 我的任务统计
const myTasksStats = reactive({
  submitted: 0,
  approved: 0,
  pending: 0
})

// 部门列表
const departmentList = [
  { label: '信息化建设处', value: 'info_tech' },
  { label: '网络中心', value: 'network_center' },
  { label: '教务处', value: 'academic_affairs' },
  { label: '学生处', value: 'student_affairs' },
  { label: '后勤服务处', value: 'logistics' },
  { label: '图书馆', value: 'library' },
  { label: '实验教学中心', value: 'lab_center' },
  { label: '其他部门', value: 'others' }
]

// 表单验证规则
const formRules = {
  title: [
    { required: true, message: '请输入任务标题', trigger: 'blur' },
    { min: 3, message: '任务标题至少3个字符', trigger: 'blur' }
  ],
  assistedDepartment: [
    { required: true, message: '请选择协助部门', trigger: 'change' }
  ],
  location: [
    { required: true, message: '请输入协助地点', trigger: 'blur' }
  ],
  assistanceDate: [
    { required: true, message: '请选择协助日期', trigger: 'change' }
  ],
  startTime: [
    { 
      validator: (_rule: any, value: any) => {
        if (timeInputType.value === 'timeRange' && !value) {
          return Promise.reject('请选择开始时间')
        }
        return Promise.resolve()
      },
      trigger: 'change'
    }
  ],
  endTime: [
    {
      validator: (_rule: any, value: any) => {
        if (timeInputType.value === 'timeRange') {
          if (!value) {
            return Promise.reject('请选择结束时间')
          }
          if (formData.startTime && value.isBefore(formData.startTime)) {
            return Promise.reject('结束时间不能早于开始时间')
          }
        }
        return Promise.resolve()
      },
      trigger: 'change'
    }
  ],
  workHours: [
    {
      validator: (_rule: any, value: any) => {
        if (timeInputType.value === 'duration' && !value) {
          return Promise.reject('请输入工作时长')
        }
        if (value && (value < 0.5 || value > 12)) {
          return Promise.reject('工作时长应在0.5-12小时之间')
        }
        return Promise.resolve()
      },
      trigger: 'change'
    }
  ],
  description: [
    { required: true, message: '请填写任务描述', trigger: 'blur' },
    { min: 10, message: '任务描述至少10个字符', trigger: 'blur' }
  ]
}

// 计算属性
const calculatedDuration = computed(() => {
  if (formData.startTime && formData.endTime) {
    const duration = formData.endTime.diff(formData.startTime, 'minute') / 60
    return duration > 0 ? duration.toFixed(1) : null
  }
  return null
})

// 禁用日期（不能选择未来日期）
const disabledDate = (current: Dayjs) => {
  return current && current.isAfter(dayjs(), 'day')
}

// 下拉框筛选
const filterOption = (input: string, option: any) => {
  return option.children.toLowerCase().indexOf(input.toLowerCase()) >= 0
}

// 文件上传前验证
const beforeFileUpload = (file: File) => {
  const isValidType = [
    'image/jpeg', 'image/png', 'image/gif',
    'application/pdf',
    'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'application/vnd.ms-excel', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
  ].includes(file.type)
  
  if (!isValidType) {
    message.error('不支持的文件格式!')
    return false
  }
  
  const isLt10M = file.size / 1024 / 1024 < 10
  if (!isLt10M) {
    message.error('文件大小不能超过10MB!')
    return false
  }
  
  return true
}

// 自定义文件上传
const handleFileUpload = ({ file, onSuccess, onError }: any) => {
  const formData = new FormData()
  formData.append('file', file)
  formData.append('type', 'assistance_attachment')
  
  setTimeout(() => {
    try {
      // 模拟上传成功
      const mockUrl = URL.createObjectURL(file)
      onSuccess({
        url: mockUrl,
        name: file.name
      })
      message.success(`${file.name} 上传成功`)
    } catch (error) {
      console.error('Upload error:', error)
      onError(error)
      message.error(`${file.name} 上传失败`)
    }
  }, 1000)
}

// 移除文件
const handleFileRemove = (file: any) => {
  const index = formData.attachments.findIndex(url => url === file.response?.url)
  if (index > -1) {
    formData.attachments.splice(index, 1)
  }
  message.info('附件已移除')
}

// 提交表单
const handleSubmit = async () => {
  try {
    await formRef.value?.validate()
    
    submitLoading.value = true
    
    // 计算工作时长
    let workHours = 0
    if (timeInputType.value === 'timeRange') {
      workHours = parseFloat(calculatedDuration.value || '0')
    } else {
      workHours = formData.workHours || 0
    }
    
    const submitData = {
      title: formData.title,
      assistedDepartment: formData.assistedDepartment,
      assistedPerson: formData.assistedPerson,
      location: formData.location,
      assistanceDate: formData.assistanceDate?.format('YYYY-MM-DD'),
      startTime: formData.startTime?.format('HH:mm'),
      endTime: formData.endTime?.format('HH:mm'),
      workHours,
      description: formData.description,
      remarks: formData.remarks,
      attachments: formData.attachments,
      status: 'pending'
    }
    
    const response = await api.createAssistanceTask(submitData)
    
    if (response.success) {
      message.success('协助任务提交成功，等待审核')
      router.push('/tasks/assistance/my')
    } else {
      throw new Error(response.message || '提交失败')
    }
  } catch (error: any) {
    console.error('Submit assistance task error:', error)
    
    if (error.errorFields) {
      message.error('请完善必填信息')
      return
    }
    
    const errorMessage = error.response?.data?.message || error.message || '提交失败，请稍后重试'
    message.error(errorMessage)
  } finally {
    submitLoading.value = false
  }
}

// 保存草稿
const saveDraft = async () => {
  try {
    draftLoading.value = true
    
    const draftData = {
      ...formData,
      assistanceDate: formData.assistanceDate?.format('YYYY-MM-DD'),
      startTime: formData.startTime?.format('HH:mm'),
      endTime: formData.endTime?.format('HH:mm'),
      isDraft: true
    }
    
    // 调用API保存草稿
    const response = await api.saveAssistanceTaskDraft(draftData)
    
    if (response.success) {
      message.success('草稿保存成功')
    }
  } catch (error: any) {
    console.error('Save draft error:', error)
    message.error('草稿保存失败')
  } finally {
    draftLoading.value = false
  }
}

// 重置表单
const resetForm = () => {
  formRef.value?.resetFields()
  attachmentFileList.value = []
  Object.assign(formData, {
    title: '',
    assistedDepartment: '',
    assistedPerson: '',
    location: '',
    assistanceDate: null,
    startTime: null,
    endTime: null,
    workHours: null,
    description: '',
    remarks: '',
    attachments: []
  })
  timeInputType.value = 'timeRange'
}

// 获取我的任务统计
const fetchMyTasksStats = async () => {
  try {
    const response = await api.getMyAssistanceTasksStats()
    if (response.success && response.data) {
      Object.assign(myTasksStats, response.data)
    }
  } catch (error) {
    console.error('获取任务统计失败:', error)
  }
}

// 生命周期
onMounted(() => {
  fetchMyTasksStats()
})
</script>

<style scoped>
.desktop-assistance-create {
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

.create-content {
  flex: 1;
  overflow: auto;
}

.form-panel {
  background: white;
  border-radius: 12px;
  padding: 32px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.04);
  border: 1px solid #e8e9ea;
}

.panel-title {
  margin-bottom: 32px;
  padding-bottom: 16px;
  border-bottom: 1px solid #e8e9ea;
}

.panel-title h3 {
  margin: 0 0 8px;
  font-size: 20px;
  font-weight: 600;
  color: #1a1a1a;
}

.panel-title p {
  margin: 0;
  color: #666666;
}

.time-input-section {
  border: 1px solid #d9d9d9;
  border-radius: 8px;
  padding: 16px;
  background: #fafbfc;
}

.calculated-duration {
  margin-top: 12px;
  text-align: center;
}

.upload-tips {
  margin-top: 8px;
}

.form-actions {
  display: flex;
  justify-content: center;
  padding-top: 24px;
  border-top: 1px solid #e8e9ea;
}

.sidebar {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.guide-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.guide-item {
  padding: 12px;
  background: #f8f9fa;
  border-radius: 6px;
  border-left: 3px solid #667eea;
}

.guide-title {
  font-weight: 500;
  color: #1a1a1a;
  margin-bottom: 4px;
}

.guide-desc {
  font-size: 12px;
  color: #666666;
}

.my-tasks-summary {
  text-align: center;
}

/* 表单样式优化 */
:deep(.ant-form-item-label) {
  font-weight: 500;
}

:deep(.ant-input-lg) {
  border-radius: 8px;
}

:deep(.ant-select-lg) {
  border-radius: 8px;
}

:deep(.ant-picker-large) {
  border-radius: 8px;
}

:deep(.ant-btn-lg) {
  height: 44px;
  padding: 0 20px;
  font-size: 15px;
  border-radius: 8px;
  font-weight: 500;
}

:deep(.ant-btn-primary) {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border: none;
  box-shadow: 0 3px 10px rgba(102, 126, 234, 0.3);
}

:deep(.ant-btn-primary:hover) {
  transform: translateY(-1px);
  box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
}

:deep(.ant-alert) {
  border-radius: 8px;
}

:deep(.ant-card) {
  border-radius: 8px;
}

:deep(.ant-statistic-title) {
  font-size: 12px;
  color: #8c8c8c;
}

:deep(.ant-statistic-content-value) {
  font-size: 18px;
  font-weight: 600;
  color: #1a1a1a;
}

/* 响应式优化 */
@media (max-width: 1200px) {
  .header-content {
    flex-direction: column;
    gap: 20px;
    text-align: center;
  }
  
  .create-content .ant-col {
    margin-bottom: 24px;
  }
}

@media (max-width: 768px) {
  .page-header,
  .form-panel {
    padding: 20px;
  }
  
  .panel-title {
    margin-bottom: 24px;
  }
  
  .form-actions .ant-space {
    flex-direction: column;
    width: 100%;
  }
  
  .form-actions .ant-btn {
    width: 100%;
  }
}
</style>