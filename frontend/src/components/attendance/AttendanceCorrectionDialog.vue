<template>
  <el-dialog
    v-model="visible"
    title="修正考勤记录"
    width="500px"
    :close-on-click-modal="false"
    @close="handleClose"
  >
    <div v-if="record" class="correction-dialog">
      <div class="record-info">
        <h4>
          {{ record.memberName || '' }} -
          {{ formatDateShort(record.date || '') }}
        </h4>
        <p class="current-status">
          当前状态：
          <el-tag
            :type="getStatusTagType(record.status || '') as any"
            :color="
              (ATTENDANCE_STATUS_CONFIG as any)[record.status || '']?.color
            "
            effect="light"
          >
            {{ (ATTENDANCE_STATUS_CONFIG as any)[record.status || '']?.label }}
          </el-tag>
        </p>
      </div>

      <el-form
        ref="formRef"
        :model="formData"
        :rules="formRules"
        label-width="100px"
        class="correction-form"
      >
        <el-form-item label="签到时间">
          <el-time-picker
            v-model="formData.checkInTime"
            placeholder="选择签到时间"
            format="HH:mm"
            value-format="HH:mm"
            style="width: 100%"
            clearable
          />
          <div class="time-info">
            原时间：{{
              record.checkInTime ? formatTime(record.checkInTime) : '未签到'
            }}
          </div>
        </el-form-item>

        <el-form-item label="签退时间">
          <el-time-picker
            v-model="formData.checkOutTime"
            placeholder="选择签退时间"
            format="HH:mm"
            value-format="HH:mm"
            style="width: 100%"
            clearable
          />
          <div class="time-info">
            原时间：{{
              record.checkOutTime ? formatTime(record.checkOutTime) : '未签退'
            }}
          </div>
        </el-form-item>

        <el-form-item label="修正原因" prop="reason">
          <el-input
            v-model="formData.reason"
            type="textarea"
            :rows="3"
            placeholder="请说明修正考勤记录的原因"
            maxlength="200"
            show-word-limit
          />
        </el-form-item>
      </el-form>
    </div>

    <template #footer>
      <div class="dialog-footer">
        <el-button @click="handleClose">取消</el-button>
        <el-button type="primary" :loading="loading" @click="handleSubmit">
          确认修正
        </el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, reactive, computed, watch, nextTick } from 'vue'
import { ElMessage, ElForm } from 'element-plus'
import { attendanceApi } from '@/api/attendance'
import { ATTENDANCE_STATUS_CONFIG } from '@/types/attendance'
import type { AttendanceRecord } from '@/types/attendance'
import { formatDateShort, formatTime } from '@/utils/date'

// Props
interface Props {
  modelValue: boolean
  record?: AttendanceRecord | null
}

const props = withDefaults(defineProps<Props>(), {
  record: null
})

// Emits
const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  success: []
}>()

// 响应式数据
const formRef = ref<InstanceType<typeof ElForm>>()
const loading = ref(false)

// 计算属性
const visible = computed({
  get: () => props.modelValue,
  set: value => emit('update:modelValue', value)
})

// 表单数据
const formData = reactive({
  checkInTime: '',
  checkOutTime: '',
  reason: ''
})

// 表单验证规则
const formRules = {
  reason: [
    { required: true, message: '请填写修正原因', trigger: 'blur' },
    { min: 5, message: '修正原因至少5个字符', trigger: 'blur' }
  ]
}

// 方法
const handleClose = () => {
  resetForm()
  emit('update:modelValue', false)
}

const resetForm = () => {
  formData.checkInTime = ''
  formData.checkOutTime = ''
  formData.reason = ''
  formRef.value?.resetFields()
}

const handleSubmit = async () => {
  try {
    if (!props.record) return

    // 表单验证
    const valid = await formRef.value?.validate()
    if (!valid) return

    loading.value = true

    const submitData: any = {
      reason: formData.reason
    }

    // 只有修改的时间才提交
    if (formData.checkInTime) {
      submitData.checkInTime = `${props.record.date} ${formData.checkInTime}:00`
    }
    if (formData.checkOutTime) {
      submitData.checkOutTime = `${props.record.date} ${formData.checkOutTime}:00`
    }

    await attendanceApi.correctAttendance({
      id: props.record.id,
      ...submitData
    })

    ElMessage.success('考勤记录修正成功')
    emit('success')
    handleClose()
  } catch (error) {
    console.error('修正失败:', error)
    ElMessage.error('修正失败')
  } finally {
    loading.value = false
  }
}

const getStatusTagType = (status: string) => {
  const config = {
    normal: 'success',
    late: 'warning',
    early_leave: 'danger',
    absent: 'info',
    leave: 'primary',
    overtime: ''
  }
  return config[status as keyof typeof config] || 'info'
}

// 监听
watch(
  () => props.record,
  record => {
    if (record) {
      // 填入当前时间作为默认值
      formData.checkInTime =
        record.checkInTime || '' ? formatTime(record.checkInTime || '') : ''
      formData.checkOutTime =
        record.checkOutTime || '' ? formatTime(record.checkOutTime || '') : ''
    }
  }
)

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
</script>

<style scoped lang="scss">
@use '@/styles/variables.scss' as *;
@use '@/styles/mixins.scss' as *;

.correction-dialog {
  .record-info {
    padding: 16px;
    background: $background-color-page;
    border-radius: 8px;
    margin-bottom: 20px;

    h4 {
      margin: 0 0 8px 0;
      color: $text-color-primary;
    }

    .current-status {
      margin: 0;
      color: $text-color-regular;
    }
  }

  .correction-form {
    .time-info {
      font-size: 12px;
      color: $text-color-secondary;
      margin-top: 4px;
    }
  }
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}
</style>
