<template>
  <a-modal
    v-model:open="visible"
    title="申请请假"
    @ok="handleSubmit"
    @cancel="handleCancel"
    :confirm-loading="loading"
  >
    <a-form
      :model="form"
      :label-col="{ span: 6 }"
      :wrapper-col="{ span: 18 }"
    >
      <a-form-item label="请假类型" required>
        <a-select v-model:value="form.leaveType" placeholder="请选择请假类型">
          <a-select-option value="sick">病假</a-select-option>
          <a-select-option value="personal">事假</a-select-option>
          <a-select-option value="annual">年假</a-select-option>
          <a-select-option value="maternity">产假</a-select-option>
          <a-select-option value="other">其他</a-select-option>
        </a-select>
      </a-form-item>
      
      <a-form-item label="开始时间" required>
        <a-date-picker
          v-model:value="form.startTime"
          show-time
          format="YYYY-MM-DD HH:mm"
          style="width: 100%"
        />
      </a-form-item>
      
      <a-form-item label="结束时间" required>
        <a-date-picker
          v-model:value="form.endTime"
          show-time
          format="YYYY-MM-DD HH:mm"
          style="width: 100%"
        />
      </a-form-item>
      
      <a-form-item label="请假天数">
        <a-input-number
          v-model:value="form.days"
          :min="0.5"
          :step="0.5"
          style="width: 100%"
          suffix="天"
        />
      </a-form-item>
      
      <a-form-item label="请假原因" required>
        <a-textarea
          v-model:value="form.reason"
          :rows="4"
          placeholder="请详细说明请假原因"
        />
      </a-form-item>
      
      <a-form-item label="附件">
        <a-upload
          v-model:file-list="form.attachments"
          :before-upload="() => false"
          multiple
        >
          <a-button>
            <UploadOutlined />
            上传附件
          </a-button>
        </a-upload>
      </a-form-item>
    </a-form>
  </a-modal>
</template>

<script setup lang="ts">
import { ref, reactive, watch } from 'vue'
import { message } from 'ant-design-vue'
import { UploadOutlined } from '@ant-design/icons-vue'
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
  leaveType: '',
  startTime: null,
  endTime: null,
  days: 1,
  reason: '',
  attachments: []
})

watch(() => props.open, (val) => {
  visible.value = val
  if (val && props.record) {
    Object.assign(form, {
      leaveType: props.record.leaveType || '',
      startTime: props.record.startTime ? dayjs(props.record.startTime) : null,
      endTime: props.record.endTime ? dayjs(props.record.endTime) : null,
      days: props.record.days || 1,
      reason: props.record.reason || '',
      attachments: props.record.attachments || []
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
    leaveType: '',
    startTime: null,
    endTime: null,
    days: 1,
    reason: '',
    attachments: []
  })
}

const handleSubmit = async () => {
  if (!form.leaveType || !form.startTime || !form.endTime || !form.reason) {
    message.error('请填写必填项')
    return
  }
  
  loading.value = true
  try {
    await new Promise(resolve => setTimeout(resolve, 1000))
    message.success('请假申请提交成功')
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