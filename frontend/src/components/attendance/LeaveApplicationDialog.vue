<template>
  <el-dialog
    v-model="visible"
    title="请假申请"
    width="600px"
    :close-on-click-modal="false"
    @close="handleClose"
  >
    <div class="leave-application-dialog">
      <el-form
        ref="formRef"
        :model="formData"
        :rules="formRules"
        label-width="100px"
        class="leave-form"
      >
        <el-form-item label="请假类型" prop="type">
          <el-select
            v-model="formData.type"
            placeholder="请选择请假类型"
            style="width: 100%"
          >
            <el-option
              v-for="(config, type) in LEAVE_TYPE_CONFIG"
              :key="type"
              :label="config.label"
              :value="type"
            />
          </el-select>
        </el-form-item>

        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="开始日期" prop="startDate">
              <el-date-picker
                v-model="formData.startDate"
                type="date"
                placeholder="选择开始日期"
                format="YYYY-MM-DD"
                value-format="YYYY-MM-DD"
                style="width: 100%"
                @change="calculateDays"
              />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="开始时间" prop="startTime">
              <el-time-picker
                v-model="formData.startTime"
                placeholder="选择开始时间"
                format="HH:mm"
                value-format="HH:mm"
                style="width: 100%"
                @change="calculateDays"
              />
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="结束日期" prop="endDate">
              <el-date-picker
                v-model="formData.endDate"
                type="date"
                placeholder="选择结束日期"
                format="YYYY-MM-DD"
                value-format="YYYY-MM-DD"
                style="width: 100%"
                @change="calculateDays"
              />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="结束时间" prop="endTime">
              <el-time-picker
                v-model="formData.endTime"
                placeholder="选择结束时间"
                format="HH:mm"
                value-format="HH:mm"
                style="width: 100%"
                @change="calculateDays"
              />
            </el-form-item>
          </el-col>
        </el-row>

        <el-form-item>
          <div class="duration-info">
            <el-alert
              :title="`请假时长：${calculatedDays}天 ${calculatedHours}小时`"
              type="info"
              :closable="false"
              show-icon
            />
          </div>
        </el-form-item>

        <el-form-item label="请假原因" prop="reason">
          <el-input
            v-model="formData.reason"
            type="textarea"
            :rows="4"
            placeholder="请详细说明请假原因"
            maxlength="500"
            show-word-limit
          />
        </el-form-item>

        <el-form-item label="附件">
          <el-upload
            ref="uploadRef"
            :auto-upload="false"
            :limit="3"
            :accept="'image/*,.pdf,.doc,.docx'"
            :before-upload="beforeUpload"
            :on-change="handleFileChange"
            :on-exceed="handleExceed"
            :file-list="fileList"
            multiple
            class="attachment-upload"
          >
            <el-button type="primary">
              <el-icon><Upload /></el-icon>
              选择文件
            </el-button>
            <template #tip>
              <div class="el-upload__tip">
                支持图片、PDF、Word文档，最多3个文件，每个文件不超过5MB
              </div>
            </template>
          </el-upload>
        </el-form-item>
      </el-form>
    </div>

    <template #footer>
      <div class="dialog-footer">
        <el-button @click="handleClose">取消</el-button>
        <el-button type="primary" :loading="loading" @click="handleSubmit">
          提交申请
        </el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, reactive, computed, watch, nextTick } from 'vue'
import { ElMessage, ElForm } from 'element-plus'
import { Upload } from '@element-plus/icons-vue'
import { attendanceApi } from '@/api/attendance'
import { LEAVE_TYPE_CONFIG } from '@/types/attendance'
import type { CreateLeaveRequest } from '@/types/attendance'

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
const formRef = ref<InstanceType<typeof ElForm>>()
const uploadRef = ref()
const loading = ref(false)
const fileList = ref<any[]>([])
const calculatedDays = ref(0)
const calculatedHours = ref(0)

// 计算属性
const visible = computed({
  get: () => props.modelValue,
  set: value => emit('update:modelValue', value)
})

// 表单数据
const formData = reactive<CreateLeaveRequest>({
  type: 'personal',
  startDate: '',
  endDate: '',
  startTime: '09:00',
  endTime: '18:00',
  reason: '',
  attachments: []
})

// 表单验证规则
const formRules = {
  type: [{ required: true, message: '请选择请假类型', trigger: 'change' }],
  startDate: [{ required: true, message: '请选择开始日期', trigger: 'change' }],
  endDate: [{ required: true, message: '请选择结束日期', trigger: 'change' }],
  startTime: [{ required: true, message: '请选择开始时间', trigger: 'change' }],
  endTime: [{ required: true, message: '请选择结束时间', trigger: 'change' }],
  reason: [
    { required: true, message: '请填写请假原因', trigger: 'blur' },
    { min: 10, message: '请假原因至少10个字符', trigger: 'blur' }
  ]
}

// 方法
const calculateDays = () => {
  if (
    formData.startDate &&
    formData.endDate &&
    formData.startTime &&
    formData.endTime
  ) {
    const startDateTime = new Date(
      `${formData.startDate} ${formData.startTime}`
    )
    const endDateTime = new Date(`${formData.endDate} ${formData.endTime}`)

    if (endDateTime > startDateTime) {
      const diffMs = endDateTime.getTime() - startDateTime.getTime()
      const diffHours = diffMs / (1000 * 60 * 60)

      calculatedDays.value = Math.floor(diffHours / 24)
      calculatedHours.value = Math.round(diffHours % 24)
    } else {
      calculatedDays.value = 0
      calculatedHours.value = 0
    }
  }
}

const handleClose = () => {
  resetForm()
  emit('update:modelValue', false)
}

const resetForm = () => {
  Object.assign(formData, {
    type: 'personal',
    startDate: '',
    endDate: '',
    startTime: '09:00',
    endTime: '18:00',
    reason: '',
    attachments: []
  })
  fileList.value = []
  calculatedDays.value = 0
  calculatedHours.value = 0
  formRef.value?.resetFields()
}

const handleSubmit = async () => {
  try {
    // 表单验证
    const valid = await formRef.value?.validate()
    if (!valid) return

    // 验证时间逻辑
    const startDateTime = new Date(
      `${formData.startDate} ${formData.startTime}`
    )
    const endDateTime = new Date(`${formData.endDate} ${formData.endTime}`)

    if (endDateTime <= startDateTime) {
      ElMessage.error('结束时间必须晚于开始时间')
      return
    }

    loading.value = true

    // 准备提交数据
    const submitData: CreateLeaveRequest = {
      ...formData,
      attachments: fileList.value.map(file => file.raw).filter(Boolean)
    }

    await attendanceApi.createLeaveApplication(submitData)

    ElMessage.success('请假申请提交成功')
    emit('success')
    handleClose()
  } catch (error) {
    console.error('提交申请失败:', error)
    ElMessage.error('提交申请失败')
  } finally {
    loading.value = false
  }
}

const beforeUpload = (file: File) => {
  const isValidType =
    file.type.startsWith('image/') ||
    file.type === 'application/pdf' ||
    file.type === 'application/msword' ||
    file.type ===
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document'

  if (!isValidType) {
    ElMessage.error('只能上传图片、PDF或Word文档！')
    return false
  }

  const isLt5M = file.size / 1024 / 1024 < 5
  if (!isLt5M) {
    ElMessage.error('文件大小不能超过 5MB！')
    return false
  }

  return false // 阻止自动上传
}

// eslint-disable-next-line @typescript-eslint/no-unused-vars
const handleFileChange = (_file: any, _fileList: any[]) => {
  // 更新文件列表
}

const handleExceed = () => {
  ElMessage.warning('最多只能上传3个文件')
}

// 监听
watch(
  () => visible.value,
  val => {
    if (val) {
      nextTick(() => {
        formRef.value?.clearValidate()
      })
    }
  }
)

watch(
  [
    () => formData.startDate,
    () => formData.endDate,
    () => formData.startTime,
    () => formData.endTime
  ],
  () => {
    calculateDays()
  }
)
</script>

<style scoped lang="scss">
@use '@/styles/variables.scss' as *;
@use '@/styles/mixins.scss' as *;

.leave-application-dialog {
  .leave-form {
    .duration-info {
      margin-bottom: 16px;
    }

    .attachment-upload {
      width: 100%;
    }
  }
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}
</style>
