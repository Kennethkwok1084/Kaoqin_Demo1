<template>
  <el-dialog
    v-model="visible"
    :title="isEdit ? '编辑任务' : '新建任务'"
    width="900px"
    @close="handleClose"
    destroy-on-close
  >
    <el-form
      ref="formRef"
      :model="formData"
      :rules="formRules"
      label-width="100px"
      @submit.prevent="handleSubmit"
    >
      <!-- 基本信息 -->
      <el-card class="form-section" shadow="never">
        <template #header>
          <div class="card-header">
            <el-icon><DocumentCopy /></el-icon>
            <span>基本信息</span>
          </div>
        </template>

        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="任务标题" prop="title">
              <el-input
                v-model="formData.title"
                placeholder="请输入任务标题"
                clearable
              />
            </el-form-item>
          </el-col>

          <el-col :span="12">
            <el-form-item label="任务类型" prop="type">
              <el-select
                v-model="formData.type"
                placeholder="请选择任务类型"
                clearable
              >
                <el-option
                  v-for="(config, key) in TASK_TYPE_CONFIG"
                  :key="key"
                  :label="config.label"
                  :value="key"
                >
                  <div class="type-option">
                    <el-icon :color="config.color" style="margin-right: 8px">
                      <component :is="config.icon" />
                    </el-icon>
                    <span>{{ config.label }}</span>
                    <span class="description">{{ config.description }}</span>
                  </div>
                </el-option>
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>

        <el-row>
          <el-col :span="24">
            <el-form-item label="任务描述" prop="description">
              <el-input
                v-model="formData.description"
                type="textarea"
                :rows="4"
                placeholder="请详细描述任务内容、要求、注意事项等"
                maxlength="500"
                show-word-limit
              />
            </el-form-item>
          </el-col>
        </el-row>
      </el-card>

      <!-- 任务设置 -->
      <el-card class="form-section" shadow="never">
        <template #header>
          <div class="card-header">
            <el-icon><Setting /></el-icon>
            <span>任务设置</span>
          </div>
        </template>

        <el-row :gutter="20">
          <el-col :span="8">
            <el-form-item label="优先级" prop="priority">
              <el-select v-model="formData.priority" placeholder="请选择优先级">
                <el-option
                  v-for="(config, key) in TASK_PRIORITY_CONFIG"
                  :key="key"
                  :label="config.label"
                  :value="key"
                >
                  <el-tag :color="config.color" size="small">{{
                    config.label
                  }}</el-tag>
                </el-option>
              </el-select>
            </el-form-item>
          </el-col>

          <el-col :span="8">
            <el-form-item label="预估工时" prop="estimatedHours">
              <el-input-number
                v-model="formData.estimatedHours"
                :min="0.5"
                :max="999"
                :step="0.5"
                placeholder="小时"
                style="width: 100%"
              />
            </el-form-item>
          </el-col>

          <el-col :span="8">
            <el-form-item label="截止日期" prop="dueDate">
              <el-date-picker
                v-model="formData.dueDate"
                type="datetime"
                placeholder="选择截止日期"
                style="width: 100%"
                :disabled-date="disabledDate"
                format="YYYY-MM-DD HH:mm"
                value-format="YYYY-MM-DD HH:mm:ss"
              />
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="指派给" prop="assigneeId">
              <el-select
                v-model="formData.assigneeId"
                placeholder="选择负责人"
                clearable
                filterable
                :loading="membersLoading"
              >
                <el-option
                  v-for="member in members"
                  :key="member.id"
                  :label="`${member.name} (${member.username})`"
                  :value="member.id"
                />
              </el-select>
            </el-form-item>
          </el-col>

          <el-col :span="12">
            <el-form-item label="任务标签" prop="tags">
              <el-select
                v-model="formData.tags"
                multiple
                filterable
                allow-create
                placeholder="选择或创建标签"
                style="width: 100%"
              >
                <el-option
                  v-for="tag in availableTags"
                  :key="tag"
                  :label="tag"
                  :value="tag"
                />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
      </el-card>

      <!-- 联系信息 -->
      <el-card class="form-section" shadow="never">
        <template #header>
          <div class="card-header">
            <el-icon><Location /></el-icon>
            <span>联系信息</span>
          </div>
        </template>

        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="任务地点" prop="location">
              <el-input
                v-model="formData.location"
                placeholder="如：教学楼A座201室"
                clearable
              />
            </el-form-item>
          </el-col>

          <el-col :span="12">
            <el-form-item label="联系方式" prop="contactInfo">
              <el-input
                v-model="formData.contactInfo"
                placeholder="联系人及电话"
                clearable
              />
            </el-form-item>
          </el-col>
        </el-row>
      </el-card>

      <!-- 附件上传 -->
      <el-card class="form-section" shadow="never">
        <template #header>
          <div class="card-header">
            <el-icon><Paperclip /></el-icon>
            <span>附件上传</span>
            <el-tag size="small" type="info">可选</el-tag>
          </div>
        </template>

        <el-upload
          ref="uploadRef"
          v-model:file-list="fileList"
          action="#"
          :auto-upload="false"
          :on-change="handleFileChange"
          :on-remove="handleFileRemove"
          multiple
          drag
        >
          <el-icon class="el-icon--upload"><UploadFilled /></el-icon>
          <div class="el-upload__text">
            将文件拖拽到此处，或<em>点击上传</em>
          </div>
          <template #tip>
            <div class="el-upload__tip">
              支持上传jpg/png/pdf/doc/docx/xls/xlsx等格式文件，单个文件大小不超过10MB
            </div>
          </template>
        </el-upload>
      </el-card>
    </el-form>

    <template #footer>
      <div class="dialog-footer">
        <el-button @click="handleClose" :disabled="submitting">取消</el-button>
        <el-button type="primary" @click="handleSubmit" :loading="submitting">
          {{ isEdit ? '更新任务' : '创建任务' }}
        </el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, reactive, computed, watch, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import {
  DocumentCopy,
  Setting,
  Location,
  Paperclip,
  UploadFilled
} from '@element-plus/icons-vue'
import type { FormInstance, FormRules, UploadFile } from 'element-plus'
import type { Task, CreateTaskRequest, UpdateTaskRequest } from '@/types/task'
import type { Member } from '@/api/members'
import { TASK_TYPE_CONFIG, TASK_PRIORITY_CONFIG } from '@/types/task'
import { tasksApi } from '@/api/tasks'
import { MembersApi } from '@/api/members'

// Props
interface Props {
  modelValue: boolean
  task?: Task | null
}

const props = withDefaults(defineProps<Props>(), {
  task: null
})

// Emits
const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  success: []
}>()

// Refs
const formRef = ref<FormInstance>()
const uploadRef = ref()
const submitting = ref(false)
const membersLoading = ref(false)

// Data
const members = ref<Member[]>([])
const availableTags = ref<string[]>([])
const fileList = ref<UploadFile[]>([])

// Form data interface that supports both formats
interface TaskFormData extends CreateTaskRequest {
  id?: number
  type?: string
  assigneeId?: number
  estimatedHours?: number
  dueDate?: string
  tags?: string[]
  attachments?: File[]
  contactInfo?: string
}

// 表单数据
const formData = reactive<TaskFormData>({
  title: '',
  description: '',
  task_type: 'repair',
  type: 'repair',
  priority: 'medium',
  assignee_id: undefined,
  assigneeId: undefined,
  reporter_name: '',
  location: '',
  contactInfo: '',
  estimated_hours: 2,
  estimatedHours: 2,
  due_date: '',
  dueDate: '',
  tags: [],
  attachments: []
})

// 表单验证规则
const formRules: FormRules = {
  title: [
    { required: true, message: '请输入任务标题', trigger: 'blur' },
    {
      min: 2,
      max: 100,
      message: '标题长度应在2-100个字符之间',
      trigger: 'blur'
    }
  ],
  description: [
    { required: true, message: '请输入任务描述', trigger: 'blur' },
    {
      min: 10,
      max: 500,
      message: '描述长度应在10-500个字符之间',
      trigger: 'blur'
    }
  ],
  type: [{ required: true, message: '请选择任务类型', trigger: 'change' }],
  priority: [{ required: true, message: '请选择优先级', trigger: 'change' }],
  location: [{ required: true, message: '请输入任务地点', trigger: 'blur' }],
  contactInfo: [{ required: true, message: '请输入联系方式', trigger: 'blur' }],
  estimatedHours: [
    { required: true, message: '请输入预估工时', trigger: 'blur' },
    {
      type: 'number',
      min: 0.5,
      max: 999,
      message: '工时应在0.5-999小时之间',
      trigger: 'change'
    }
  ],
  dueDate: [{ required: true, message: '请选择截止日期', trigger: 'change' }]
}

// Computed
const visible = computed({
  get: () => props.modelValue,
  set: value => emit('update:modelValue', value)
})

const isEdit = computed(() => !!props.task)

// 禁用过去的日期
const disabledDate = (time: Date) => {
  return time.getTime() < Date.now() - 24 * 60 * 60 * 1000
}

// Methods
const loadMembers = async () => {
  try {
    membersLoading.value = true
    const response = await MembersApi.getMembers({
      page: 1,
      page_size: 100,
      is_active: true
    })
    members.value = response.items || []
  } catch (error) {
    console.error('加载成员列表失败:', error)
    ElMessage.error('加载成员列表失败')
  } finally {
    membersLoading.value = false
  }
}

const loadTags = async () => {
  try {
    const tags = await tasksApi.getTags()
    availableTags.value = tags || []
  } catch (error) {
    console.error('加载标签失败:', error)
  }
}

const handleFileChange = (file: UploadFile) => {
  if (file.raw) {
    // 验证文件类型和大小
    const allowedTypes = [
      'image/jpeg',
      'image/png',
      'image/gif',
      'application/pdf',
      'application/msword',
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
      'application/vnd.ms-excel',
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
      'text/plain'
    ]

    if (!allowedTypes.includes(file.raw.type)) {
      ElMessage.error('不支持的文件类型')
      return false
    }

    if (file.raw.size > 10 * 1024 * 1024) {
      ElMessage.error('文件大小不能超过10MB')
      return false
    }

    formData.attachments = formData.attachments || []
    formData.attachments.push(file.raw)
  }
}

const handleFileRemove = (file: UploadFile) => {
  if (formData.attachments && file.raw) {
    const index = formData.attachments.findIndex((f: File) => f === file.raw)
    if (index > -1) {
      formData.attachments.splice(index, 1)
    }
  }
}

const resetForm = () => {
  Object.assign(formData, {
    title: '',
    description: '',
    type: 'network_repair' as any,
    priority: 'medium',
    assigneeId: undefined,
    location: '',
    contactInfo: '',
    estimatedHours: 2,
    dueDate: '',
    tags: [],
    attachments: []
  })
  fileList.value = []
  formRef.value?.clearValidate()
}

const initForm = () => {
  if (props.task && isEdit.value) {
    Object.assign(formData, {
      id: props.task.id,
      title: props.task.title,
      description: props.task.description,
      type: props.task.type,
      priority: props.task.priority,
      assigneeId: props.task.assigneeId,
      location: props.task.location,
      contactInfo: (props.task as any).contactInfo || '',
      estimatedHours: props.task.estimatedHours,
      dueDate: props.task.dueDate,
      tags: props.task.tags || [],
      attachments: []
    })
  } else {
    resetForm()
  }
}

const handleClose = () => {
  emit('update:modelValue', false)
  resetForm()
}

const handleSubmit = async () => {
  if (!formRef.value) return

  try {
    await formRef.value.validate()
    submitting.value = true

    if (isEdit.value && props.task) {
      // 更新任务
      const updateData: UpdateTaskRequest = {
        title: formData.title,
        description: formData.description,
        type: formData.type,
        priority: formData.priority,
        assigneeId: formData.assigneeId,
        location: formData.location,
        contactInfo: formData.contactInfo || '',
        estimatedHours: formData.estimatedHours,
        dueDate: formData.dueDate,
        tags: formData.tags
      }

      await tasksApi.updateTask((props.task as any)?.id || 0, updateData as any)
      ElMessage.success('任务更新成功')
    } else {
      // 创建任务
      const createData = {
        title: formData.title,
        description: formData.description,
        type: formData.type,
        priority: formData.priority,
        assigneeId: formData.assigneeId,
        location: formData.location,
        contactInfo: formData.contactInfo || '',
        estimatedHours: formData.estimatedHours,
        dueDate: formData.dueDate,
        tags: formData.tags,
        attachments: formData.attachments
      }

      await tasksApi.createTask(createData as any)
      ElMessage.success('任务创建成功')
    }

    emit('success')
    handleClose()
  } catch (error: any) {
    console.error('提交失败:', error)
    if (error.response?.data?.message) {
      ElMessage.error(error.response.data.message)
    } else {
      ElMessage.error(isEdit.value ? '更新任务失败' : '创建任务失败')
    }
  } finally {
    submitting.value = false
  }
}

// Watch
watch(
  () => props.modelValue,
  newVal => {
    if (newVal) {
      initForm()
      loadMembers()
      loadTags()
    }
  }
)

// Lifecycle
onMounted(() => {
  if (props.modelValue) {
    initForm()
    loadMembers()
    loadTags()
  }
})
</script>

<style scoped lang="scss">
.form-section {
  margin-bottom: 20px;

  :deep(.el-card__body) {
    padding: 20px;
  }
}

.card-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 500;

  .el-tag {
    margin-left: auto;
  }
}

.type-option {
  display: flex;
  align-items: center;
  width: 100%;

  .description {
    margin-left: auto;
    font-size: 12px;
    color: var(--el-text-color-secondary);
  }
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding: 20px 0 0;
}

:deep(.el-upload-dragger) {
  width: 100%;
  height: 180px;
}

:deep(.el-date-editor.el-input) {
  width: 100%;
}

:deep(.el-form-item__label) {
  font-weight: 500;
}

:deep(.el-card .el-card__header) {
  background-color: var(--el-fill-color-lighter);
  border-bottom: 1px solid var(--el-border-color-light);
}

// 响应式设计
@media (max-width: 768px) {
  .el-col {
    margin-bottom: 10px;
  }
}
</style>
