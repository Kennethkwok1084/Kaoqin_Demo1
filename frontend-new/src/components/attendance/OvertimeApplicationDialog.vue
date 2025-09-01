<template>
  <a-modal
    v-model:open="visible"
    title="申请加班"
    @ok="handleSubmit"
    @cancel="handleCancel"
    :confirm-loading="loading"
  >
    <a-form
      :model="form"
      :label-col="{ span: 6 }"
      :wrapper-col="{ span: 18 }"
    >
      <a-form-item label="加班类型" required>
        <a-select v-model:value="form.overtimeType" placeholder="请选择加班类型">
          <a-select-option value="weekday">平时加班</a-select-option>
          <a-select-option value="weekend">周末加班</a-select-option>
          <a-select-option value="holiday">节假日加班</a-select-option>
          <a-select-option value="urgent">紧急加班</a-select-option>
        </a-select>
      </a-form-item>
      
      <a-form-item label="加班日期" required>
        <a-date-picker
          v-model:value="form.overtimeDate"
          format="YYYY-MM-DD"
          style="width: 100%"
        />
      </a-form-item>
      
      <a-form-item label="开始时间" required>
        <a-time-picker
          v-model:value="form.startTime"
          format="HH:mm"
          style="width: 100%"
        />
      </a-form-item>
      
      <a-form-item label="结束时间" required>
        <a-time-picker
          v-model:value="form.endTime"
          format="HH:mm"
          style="width: 100%"
        />
      </a-form-item>
      
      <a-form-item label="加班时长">
        <a-input-number
          v-model:value="form.hours"
          :min="0.5"
          :step="0.5"
          style="width: 100%"
          suffix="小时"
        />
      </a-form-item>
      
      <a-form-item label="加班原因" required>
        <a-textarea
          v-model:value="form.reason"
          :rows="4"
          placeholder="请详细说明加班原因和工作内容"
        />
      </a-form-item>
      
      <a-form-item label="工作内容" required>
        <a-textarea
          v-model:value="form.workContent"
          :rows="3"
          placeholder="请描述加班期间要完成的具体工作"
        />
      </a-form-item>
      
      <a-form-item label="是否需要调休">
        <a-radio-group v-model:value="form.needTimeOff">
          <a-radio :value="true">是</a-radio>
          <a-radio :value="false">否</a-radio>
        </a-radio-group>
      </a-form-item>
    </a-form>
  </a-modal>
</template>

<script setup lang="ts">
import { ref, reactive, watch } from 'vue'
import { message } from 'ant-design-vue'
import dayjs from 'dayjs'

interface Props {
  open: boolean
  record?: any
}

interface Emits {
  (e: 'update:open', value: boolean): void
  (e: 'success'): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

const visible = ref(false)
const loading = ref(false)

const form = reactive({
  overtimeType: '',
  overtimeDate: null,
  startTime: null,
  endTime: null,
  hours: 2,
  reason: '',
  workContent: '',
  needTimeOff: false
})

watch(() => props.open, (val) => {
  visible.value = val
  if (val && props.record) {
    Object.assign(form, {
      overtimeType: props.record.overtimeType || '',
      overtimeDate: props.record.overtimeDate ? dayjs(props.record.overtimeDate) : null,
      startTime: props.record.startTime ? dayjs(props.record.startTime, 'HH:mm') : null,
      endTime: props.record.endTime ? dayjs(props.record.endTime, 'HH:mm') : null,
      hours: props.record.hours || 2,
      reason: props.record.reason || '',
      workContent: props.record.workContent || '',
      needTimeOff: props.record.needTimeOff || false
    })
  } else if (val) {
    resetForm()
  }
})

watch(visible, (val) => {
  emit('update:open', val)
})

const resetForm = () => {
  Object.assign(form, {
    overtimeType: '',
    overtimeDate: null,
    startTime: null,
    endTime: null,
    hours: 2,
    reason: '',
    workContent: '',
    needTimeOff: false
  })
}

const handleSubmit = async () => {
  if (!form.overtimeType || !form.overtimeDate || !form.startTime || !form.endTime || !form.reason || !form.workContent) {
    message.error('请填写必填项')
    return
  }
  
  loading.value = true
  try {
    await new Promise(resolve => setTimeout(resolve, 1000))
    message.success('加班申请提交成功')
    visible.value = false
    emit('success')
  } catch (error) {
    message.error('提交失败')
  } finally {
    loading.value = false
  }
}

const handleCancel = () => {
  visible.value = false
}
</script>