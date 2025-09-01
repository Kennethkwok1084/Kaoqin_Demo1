<template>
  <div class="desktop-task-create">
    <div class="page-header">
      <div class="header-content">
        <div class="header-text">
          <h1>创建任务</h1>
          <p>创建新的维修、监测或协助任务</p>
        </div>
        <div class="header-actions">
          <a-button @click="$router.back()">
            返回
          </a-button>
        </div>
      </div>
    </div>

    <div class="create-form-panel">
      <a-form
        :model="formData"
        :rules="rules"
        ref="formRef"
        layout="vertical"
        @finish="handleSubmit"
        class="task-form"
      >
        <div class="form-sections">
          <!-- 基本信息 -->
          <div class="form-section">
            <div class="section-title">
              <h3>基本信息</h3>
              <p>任务的基本信息和描述</p>
            </div>
            
            <a-row :gutter="24">
              <a-col :span="12">
                <a-form-item name="title" label="任务标题" required>
                  <a-input
                    v-model:value="formData.title"
                    placeholder="请输入任务标题"
                    size="large"
                    :maxlength="100"
                    show-count
                  />
                </a-form-item>
              </a-col>
              <a-col :span="12">
                <a-form-item name="location" label="位置" required>
                  <a-input
                    v-model:value="formData.location"
                    placeholder="请输入任务位置"
                    size="large"
                    :maxlength="100"
                  />
                </a-form-item>
              </a-col>
            </a-row>

            <a-row :gutter="24">
              <a-col :span="12">
                <a-form-item name="type" label="任务类型" required>
                  <a-select
                    v-model:value="formData.type"
                    placeholder="选择任务类型"
                    size="large"
                  >
                    <a-select-option value="repair">维修任务</a-select-option>
                    <a-select-option value="monitoring">监测任务</a-select-option>
                    <a-select-option value="assistance">协助任务</a-select-option>
                  </a-select>
                </a-form-item>
              </a-col>
              <a-col :span="12">
                <a-form-item name="priority" label="优先级" required>
                  <a-select
                    v-model:value="formData.priority"
                    placeholder="选择任务优先级"
                    size="large"
                  >
                    <a-select-option value="low">低</a-select-option>
                    <a-select-option value="medium">中</a-select-option>
                    <a-select-option value="high">高</a-select-option>
                  </a-select>
                </a-form-item>
              </a-col>
            </a-row>

            <a-row :gutter="24">
              <a-col :span="24">
                <a-form-item name="description" label="任务描述">
                  <a-textarea
                    v-model:value="formData.description"
                    placeholder="详细描述任务内容、问题现象等"
                    :rows="4"
                    :maxlength="500"
                    show-count
                  />
                </a-form-item>
              </a-col>
            </a-row>
          </div>

          <!-- 协助任务专用字段 -->
          <div class="form-section" v-if="formData.type === 'assistance'">
            <div class="section-title">
              <h3>协助任务信息</h3>
              <p>协助任务的详细信息</p>
            </div>
            
            <a-row :gutter="24">
              <a-col :span="12">
                <a-form-item name="assisted_department" label="被协助部门">
                  <a-input
                    v-model:value="formData.assisted_department"
                    placeholder="请输入被协助部门"
                    size="large"
                    :maxlength="100"
                  />
                </a-form-item>
              </a-col>
              <a-col :span="12">
                <a-form-item name="assisted_person" label="被协助人员">
                  <a-input
                    v-model:value="formData.assisted_person"
                    placeholder="请输入被协助人员姓名"
                    size="large"
                    :maxlength="50"
                  />
                </a-form-item>
              </a-col>
            </a-row>

            <a-row :gutter="24">
              <a-col :span="12">
                <a-form-item name="start_time" label="开始时间" required>
                  <a-date-picker
                    v-model:value="formData.start_time"
                    show-time
                    placeholder="选择开始时间"
                    size="large"
                    style="width: 100%"
                    format="YYYY-MM-DD HH:mm:ss"
                    value-format="YYYY-MM-DD HH:mm:ss"
                  />
                </a-form-item>
              </a-col>
              <a-col :span="12">
                <a-form-item name="end_time" label="结束时间" required>
                  <a-date-picker
                    v-model:value="formData.end_time"
                    show-time
                    placeholder="选择结束时间"
                    size="large"
                    style="width: 100%"
                    format="YYYY-MM-DD HH:mm:ss"
                    value-format="YYYY-MM-DD HH:mm:ss"
                  />
                </a-form-item>
              </a-col>
            </a-row>
          </div>

          <!-- 报告人信息 -->
          <div class="form-section" v-if="formData.type !== 'assistance'">
            <div class="section-title">
              <h3>报告人信息</h3>
              <p>任务报告人的联系信息</p>
            </div>
            
            <a-row :gutter="24">
              <a-col :span="12">
                <a-form-item name="reporterName" label="报告人姓名" required>
                  <a-input
                    v-model:value="formData.reporterName"
                    placeholder="请输入报告人姓名"
                    size="large"
                    :maxlength="50"
                  />
                </a-form-item>
              </a-col>
              <a-col :span="12">
                <a-form-item name="reporterContact" label="联系方式" required>
                  <a-input
                    v-model:value="formData.reporterContact"
                    placeholder="手机号或微信号"
                    size="large"
                    :maxlength="50"
                  />
                </a-form-item>
              </a-col>
            </a-row>
          </div>

          <!-- 任务分配 -->
          <div class="form-section">
            <div class="section-title">
              <h3>任务分配</h3>
              <p>指定任务执行者和标签（可选）</p>
            </div>
            
            <a-row :gutter="24">
              <a-col :span="12">
                <a-form-item name="assignedTo" label="指派给">
                  <a-select
                    v-model:value="formData.assignedTo"
                    placeholder="选择执行者（可不选）"
                    size="large"
                    allow-clear
                    show-search
                    :options="memberOptions"
                    :loading="membersLoading"
                    @dropdown-visible-change="handleMemberDropdown"
                  />
                </a-form-item>
              </a-col>
              <a-col :span="12">
                <a-form-item name="tagIds" label="任务标签">
                  <a-select
                    v-model:value="formData.tagIds"
                    placeholder="选择相关标签（可选）"
                    size="large"
                    mode="multiple"
                    :options="tagOptions"
                    :loading="tagsLoading"
                    @dropdown-visible-change="handleTagDropdown"
                  />
                </a-form-item>
              </a-col>
            </a-row>
          </div>
        </div>

        <div class="form-actions">
          <a-button @click="handleReset" size="large">
            重置表单
          </a-button>
          <a-button 
            type="primary" 
            html-type="submit" 
            size="large"
            :loading="submitLoading"
          >
            {{ submitLoading ? '创建中...' : '创建任务' }}
          </a-button>
        </div>
      </a-form>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { message } from 'ant-design-vue'
import { api } from '@/api/client'

const router = useRouter()
const formRef = ref()

// 表单数据
const formData = reactive({
  title: '',
  description: '',
  location: '',
  type: 'repair', // 默认为维修任务
  priority: 'medium', // 默认优先级
  assignedTo: undefined,
  reporterName: '',
  reporterContact: '',
  tagIds: [],
  // 协助任务专用字段
  assisted_department: '',
  assisted_person: '',
  start_time: '',
  end_time: ''
})

// 表单验证规则
const rules = {
  title: [
    { required: true, message: '请输入任务标题', trigger: 'blur' },
    { min: 2, max: 100, message: '标题长度应为2-100字符', trigger: 'blur' }
  ],
  location: [
    { required: true, message: '请输入任务位置', trigger: 'blur' },
    { min: 2, max: 100, message: '位置长度应为2-100字符', trigger: 'blur' }
  ],
  reporterName: [
    { required: true, message: '请输入报告人姓名', trigger: 'blur' },
    { min: 2, max: 50, message: '姓名长度应为2-50字符', trigger: 'blur' }
  ],
  reporterContact: [
    { required: true, message: '请输入联系方式', trigger: 'blur' },
    { min: 5, max: 50, message: '联系方式长度应为5-50字符', trigger: 'blur' },
    { pattern: /^1[3-9]\d{9}$|^[a-zA-Z0-9_-]+$/, message: '请输入正确的手机号码或微信号', trigger: 'blur' }
  ],
  type: [
    { required: true, message: '请选择任务类型', trigger: 'change' }
  ],
  priority: [
    { required: true, message: '请选择任务优先级', trigger: 'change' }
  ],
  // 协助任务专用验证
  start_time: [
    { required: true, message: '请选择开始时间', trigger: 'change' }
  ],
  end_time: [
    { required: true, message: '请选择结束时间', trigger: 'change' }
  ]
}

// 响应式状态
const submitLoading = ref(false)
const membersLoading = ref(false)
const tagsLoading = ref(false)
const memberOptions = ref<Array<{label: string, value: number}>>([])
const tagOptions = ref<Array<{label: string, value: number}>>([])

// 方法
const handleSubmit = async () => {
  try {
    submitLoading.value = true
    
    let result
    switch (formData.type) {
      case 'repair':
        // 维修任务数据
        const repairTaskData = {
          title: formData.title,
          description: formData.description,
          location: formData.location,
          priority: formData.priority,
          assignedTo: formData.assignedTo,
          reporterName: formData.reporterName,
          reporterContact: formData.reporterContact,
          tagIds: formData.tagIds
        }
        result = await api.createTask(repairTaskData)
        break
      case 'monitoring':
        // 监测任务数据（暂时使用维修任务API）
        const monitoringTaskData = {
          title: formData.title,
          description: formData.description,
          location: formData.location,
          priority: formData.priority,
          assignedTo: formData.assignedTo,
          reporterName: formData.reporterName,
          reporterContact: formData.reporterContact,
          tagIds: formData.tagIds
        }
        result = await api.createTask(monitoringTaskData)
        break
      case 'assistance':
        // 协助任务数据
        const assistanceTaskData = {
          title: formData.title,
          description: formData.description,
          assisted_department: formData.assisted_department,
          assisted_person: formData.assisted_person,
          start_time: formData.start_time,
          end_time: formData.end_time
        }
        result = await api.createAssistanceTask(assistanceTaskData)
        break
      default:
        throw new Error('不支持的任务类型')
    }
    
    if (result.success) {
      message.success(result.message || '任务创建成功')
      router.push('/tasks')
    } else {
      message.error(result.message || '任务创建失败')
    }
  } catch (error: any) {
    console.error('Task creation error:', error)
    message.error(error.message || '任务创建失败，请检查网络连接')
  } finally {
    submitLoading.value = false
  }
}

const handleReset = () => {
  formRef.value.resetFields()
  Object.assign(formData, {
    title: '',
    description: '',
    location: '',
    type: 'repair',
    priority: 'medium',
    assignedTo: undefined,
    reporterName: '',
    reporterContact: '',
    tagIds: [],
    // 协助任务字段
    assisted_department: '',
    assisted_person: '',
    start_time: '',
    end_time: ''
  })
}

const handleMemberDropdown = async (open: boolean) => {
  if (open && memberOptions.value.length === 0) {
    try {
      membersLoading.value = true
      const result = await api.getMembers({ isActive: true, pageSize: 100 })
      if (result.success && result.data) {
        memberOptions.value = result.data.items.map((member: any) => ({
          label: `${member.name} (${member.studentId})`,
          value: member.id
        }))
      }
    } catch (error: any) {
      console.error('Load members error:', error)
    } finally {
      membersLoading.value = false
    }
  }
}

const handleTagDropdown = async (open: boolean) => {
  if (open && tagOptions.value.length === 0) {
    try {
      tagsLoading.value = true
      const result = await api.getTags({ isActive: true })
      if (result.success && result.data) {
        tagOptions.value = result.data.items.map((tag: any) => ({
          label: `${tag.name} (${tag.workMinutesModifier > 0 ? '+' : ''}${tag.workMinutesModifier}分钟)`,
          value: tag.id
        }))
      }
    } catch (error: any) {
      console.error('Load tags error:', error)
    } finally {
      tagsLoading.value = false
    }
  }
}

// 生命周期
onMounted(() => {
  // 页面加载时可以预加载数据
})
</script>

<style scoped>
/* 桌面端任务创建界面样式 */
.desktop-task-create {
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

.create-form-panel {
  background: white;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.04);
  border: 1px solid #e8e9ea;
  overflow: hidden;
  flex: 1;
}

.task-form {
  padding: 32px;
}

.form-sections {
  display: flex;
  flex-direction: column;
  gap: 40px;
}

.form-section {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.section-title {
  border-bottom: 2px solid #e8e9ea;
  padding-bottom: 16px;
}

.section-title h3 {
  margin: 0 0 8px;
  font-size: 18px;
  font-weight: 600;
  color: #1a1a1a;
}

.section-title p {
  margin: 0;
  font-size: 14px;
  color: #8c8c8c;
}

.form-actions {
  display: flex;
  justify-content: flex-end;
  gap: 16px;
  padding-top: 32px;
  border-top: 1px solid #e8e9ea;
  margin-top: 40px;
}

/* 表单控件样式优化 */
:deep(.ant-form-item-label > label) {
  font-size: 16px;
  font-weight: 500;
  color: #262626;
  height: 32px;
}

:deep(.ant-input),
:deep(.ant-select-selector),
:deep(.ant-input-number) {
  border-radius: 8px;
  border: 2px solid #e8e9ea;
  transition: all 0.3s ease;
}

:deep(.ant-input:hover),
:deep(.ant-select:hover .ant-select-selector),
:deep(.ant-input-number:hover) {
  border-color: #667eea;
}

:deep(.ant-input:focus),
:deep(.ant-select-focused .ant-select-selector),
:deep(.ant-input-number-focused) {
  border-color: #667eea;
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
}

:deep(.ant-form-item-has-error .ant-input),
:deep(.ant-form-item-has-error .ant-select-selector),
:deep(.ant-form-item-has-error .ant-input-number) {
  border-color: #ff4d4f;
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

/* 响应式优化 */
@media (max-width: 1200px) {
  .header-content {
    flex-direction: column;
    gap: 20px;
    text-align: center;
  }
  
  :deep(.ant-col) {
    width: 100% !important;
    max-width: none !important;
  }
}

@media (max-width: 768px) {
  .page-header,
  .task-form {
    padding: 20px;
  }
  
  .form-sections {
    gap: 24px;
  }
  
  .form-actions {
    flex-direction: column;
    align-items: stretch;
  }
}
</style>