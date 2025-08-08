<template>
  <el-dialog
    v-model="visible"
    title="加班申请"
    width="500px"
    :close-on-click-modal="false"
    @close="handleClose"
  >
    <div class="overtime-application-dialog">
      <el-form
        ref="formRef"
        :model="formData"
        :rules="formRules"
        label-width="100px"
        class="overtime-form"
      >
        <el-form-item label="加班日期" prop="date">
          <el-date-picker
            v-model="formData.date"
            type="date"
            placeholder="选择加班日期"
            format="YYYY-MM-DD"
            value-format="YYYY-MM-DD"
            style="width: 100%"
          />
        </el-form-item>

        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="开始时间" prop="startTime">
              <el-time-picker
                v-model="formData.startTime"
                placeholder="开始时间"
                format="HH:mm"
                value-format="HH:mm"
                style="width: 100%"
                @change="calculateHours"
              />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="结束时间" prop="endTime">
              <el-time-picker
                v-model="formData.endTime"
                placeholder="结束时间"
                format="HH:mm"
                value-format="HH:mm"
                style="width: 100%"
                @change="calculateHours"
              />
            </el-form-item>
          </el-col>
        </el-row>

        <el-form-item>
          <el-alert
            :title="`预计加班时长：${calculatedHours}小时`"
            type="info"
            :closable="false"
            show-icon
          />
        </el-form-item>

        <el-form-item label="加班原因" prop="reason">
          <el-input
            v-model="formData.reason"
            type="textarea"
            :rows="4"
            placeholder="请详细说明加班原因和工作内容"
            maxlength="300"
            show-word-limit
          />
        </el-form-item>
      </el-form>
    </div>

    <template #footer>
      <div class="dialog-footer">
        <el-button @click="handleClose">取消</el-button>
        <el-button 
          type="primary" 
          :loading="loading"
          @click="handleSubmit"
        >
          提交申请
        </el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, reactive, computed, watch, nextTick } from 'vue'
import { ElMessage, ElForm } from 'element-plus'
import { attendanceApi } from '@/api/attendance'
import type { CreateOvertimeRequest } from '@/types/attendance'

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
const loading = ref(false)
const calculatedHours = ref(0)

// 计算属性
const visible = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value)
})

// 表单数据
const formData = reactive<CreateOvertimeRequest>({
  date: new Date().toISOString().split('T')[0],
  startTime: '18:00',
  endTime: '20:00',
  reason: ''
})

// 表单验证规则
const formRules = {
  date: [
    { required: true, message: '请选择加班日期', trigger: 'change' }
  ],
  startTime: [
    { required: true, message: '请选择开始时间', trigger: 'change' }
  ],
  endTime: [
    { required: true, message: '请选择结束时间', trigger: 'change' }
  ],
  reason: [
    { required: true, message: '请填写加班原因', trigger: 'blur' },
    { min: 10, message: '加班原因至少10个字符', trigger: 'blur' }
  ]
}

// 方法
const calculateHours = () => {
  if (formData.startTime && formData.endTime) {
    const [startHour, startMin] = formData.startTime.split(':').map(Number)
    const [endHour, endMin] = formData.endTime.split(':').map(Number)
    
    const startMinutes = startHour * 60 + startMin
    const endMinutes = endHour * 60 + endMin
    
    if (endMinutes > startMinutes) {
      calculatedHours.value = Math.round((endMinutes - startMinutes) / 60 * 10) / 10
    } else {
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
    date: new Date().toISOString().split('T')[0],
    startTime: '18:00',
    endTime: '20:00',
    reason: ''
  })
  calculatedHours.value = 0
  formRef.value?.resetFields()
}

const handleSubmit = async () => {
  try {
    // 表单验证
    const valid = await formRef.value?.validate()
    if (!valid) return

    // 验证时间逻辑
    if (calculatedHours.value <= 0) {
      ElMessage.error('结束时间必须晚于开始时间')
      return
    }

    loading.value = true

    await attendanceApi.createOvertimeApplication(formData)
    
    ElMessage.success('加班申请提交成功')
    emit('success')
    handleClose()

  } catch (error) {
    console.error('提交申请失败:', error)
    ElMessage.error('提交申请失败')
  } finally {
    loading.value = false
  }
}

// 监听
watch(() => visible.value, (val) => {
  if (val) {
    calculateHours()
    nextTick(() => {
      formRef.value?.clearValidate()
    })
  }
})

watch([() => formData.startTime, () => formData.endTime], () => {
  calculateHours()
})
</script>

<style scoped lang="scss">
@use '@/styles/variables.scss' as *;
@use '@/styles/mixins.scss' as *;

.overtime-application-dialog {
  .overtime-form {
    // 样式在这里添加
  }
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}
</style>