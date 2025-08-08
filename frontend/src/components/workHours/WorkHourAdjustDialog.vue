<template>
  <el-dialog
    v-model="dialogVisible"
    title="工时调整"
    width="500px"
    @close="handleClose"
  >
    <el-form :model="form" :rules="rules" ref="formRef" label-width="100px">
      <el-form-item label="成员姓名">
        <el-input :value="workHour?.memberName" disabled />
      </el-form-item>

      <el-form-item label="任务标题">
        <el-input :value="workHour?.taskTitle" disabled />
      </el-form-item>

      <el-form-item label="当前工时">
        <div class="current-hours">
          <el-tag type="info">{{ workHour?.totalHours }}h</el-tag>
          <span class="hours-detail">
            (基础: {{ workHour?.baseHours }}h, 
            奖励: +{{ workHour?.bonusHours }}h, 
            惩罚: -{{ workHour?.penaltyHours }}h)
          </span>
        </div>
      </el-form-item>

      <el-form-item label="调整后工时" prop="adjustedHours">
        <el-input-number
          v-model="form.adjustedHours"
          :min="0"
          :max="1000"
          :precision="1"
          :step="0.5"
          style="width: 100%"
        />
      </el-form-item>

      <el-form-item label="调整类型" prop="adjustmentType">
        <el-radio-group v-model="form.adjustmentType">
          <el-radio value="bonus">奖励调整</el-radio>
          <el-radio value="penalty">惩罚调整</el-radio>
          <el-radio value="manual">手动调整</el-radio>
        </el-radio-group>
      </el-form-item>

      <el-form-item label="调整原因" prop="reason">
        <el-select v-model="form.reason" placeholder="请选择调整原因" style="width: 100%">
          <el-option-group label="奖励原因">
            <el-option label="工作质量优秀" value="excellent_quality" />
            <el-option label="提前完成任务" value="early_completion" />
            <el-option label="紧急任务响应" value="emergency_response" />
            <el-option label="技术创新" value="technical_innovation" />
          </el-option-group>
          <el-option-group label="惩罚原因">
            <el-option label="响应延迟" value="late_response" />
            <el-option label="完成延迟" value="late_completion" />
            <el-option label="工作质量问题" value="quality_issue" />
            <el-option label="用户投诉" value="user_complaint" />
          </el-option-group>
          <el-option-group label="其他原因">
            <el-option label="数据录入错误" value="data_error" />
            <el-option label="系统计算错误" value="system_error" />
            <el-option label="特殊情况处理" value="special_case" />
            <el-option label="管理员决定" value="admin_decision" />
          </el-option-group>
        </el-select>
      </el-form-item>

      <el-form-item label="详细说明" prop="notes">
        <el-input
          v-model="form.notes"
          type="textarea"
          :rows="3"
          placeholder="请输入详细的调整说明..."
        />
      </el-form-item>

      <!-- 调整预览 -->
      <el-form-item label="调整预览">
        <div class="adjustment-preview">
          <div class="preview-item">
            <span class="label">调整前：</span>
            <span class="value">{{ workHour?.totalHours }}h</span>
          </div>
          <div class="preview-item">
            <span class="label">调整后：</span>
            <span class="value highlight">{{ form.adjustedHours }}h</span>
          </div>
          <div class="preview-item">
            <span class="label">变化：</span>
            <span :class="['value', getChangeClass()]">
              {{ getChangeText() }}
            </span>
          </div>
        </div>
      </el-form-item>
    </el-form>

    <template #footer>
      <div class="dialog-footer">
        <el-button @click="handleClose">取消</el-button>
        <el-button type="primary" @click="handleSubmit" :loading="loading">
          确认调整
        </el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, reactive, watch, computed } from 'vue'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'
import { workHoursApi } from '@/api/workHours'
import type { WorkHour } from '@/types/workHours'

interface Props {
  visible: boolean
  workHour: WorkHour | null
}

interface Emits {
  (e: 'update:visible', value: boolean): void
  (e: 'success'): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

const dialogVisible = ref(false)
const loading = ref(false)
const formRef = ref<FormInstance>()

const form = reactive({
  adjustedHours: 0,
  adjustmentType: 'manual',
  reason: '',
  notes: ''
})

const rules: FormRules = {
  adjustedHours: [
    { required: true, message: '请输入调整后的工时', trigger: 'blur' },
    { type: 'number', min: 0, max: 1000, message: '工时必须在0-1000之间', trigger: 'blur' }
  ],
  adjustmentType: [
    { required: true, message: '请选择调整类型', trigger: 'change' }
  ],
  reason: [
    { required: true, message: '请选择调整原因', trigger: 'change' }
  ],
  notes: [
    { required: true, message: '请输入详细说明', trigger: 'blur' },
    { min: 10, message: '详细说明至少需要10个字符', trigger: 'blur' }
  ]
}

const changeDifference = computed(() => {
  if (!props.workHour) return 0
  return form.adjustedHours - props.workHour.totalHours
})

watch(() => props.visible, (visible) => {
  dialogVisible.value = visible
  if (visible && props.workHour) {
    form.adjustedHours = props.workHour.totalHours
    form.adjustmentType = 'manual'
    form.reason = ''
    form.notes = ''
  }
})

watch(dialogVisible, (visible) => {
  emit('update:visible', visible)
})

const getChangeClass = () => {
  if (changeDifference.value > 0) return 'positive'
  if (changeDifference.value < 0) return 'negative'
  return 'neutral'
}

const getChangeText = () => {
  const diff = changeDifference.value
  if (diff > 0) return `+${diff.toFixed(1)}h`
  if (diff < 0) return `${diff.toFixed(1)}h`
  return '无变化'
}

const handleSubmit = async () => {
  if (!formRef.value || !props.workHour) return

  try {
    await formRef.value.validate()

    loading.value = true

    await workHoursApi.adjustWorkHours(
      props.workHour.id,
      form.adjustedHours,
      form.reason,
      form.notes
    )

    ElMessage.success('工时调整成功')
    emit('success')
    handleClose()

  } catch (error) {
    console.error('工时调整失败:', error)
    ElMessage.error('工时调整失败')
  } finally {
    loading.value = false
  }
}

const handleClose = () => {
  dialogVisible.value = false
  formRef.value?.resetFields()
  loading.value = false
}
</script>

<style lang="scss" scoped>
.current-hours {
  display: flex;
  align-items: center;
  gap: 10px;

  .hours-detail {
    font-size: 12px;
    color: var(--el-text-color-regular);
  }
}

.adjustment-preview {
  background-color: var(--el-fill-color-light);
  padding: 15px;
  border-radius: 6px;
  border: 1px solid var(--el-border-color-lighter);

  .preview-item {
    display: flex;
    justify-content: space-between;
    margin-bottom: 8px;

    &:last-child {
      margin-bottom: 0;
    }

    .label {
      font-weight: 500;
      color: var(--el-text-color-regular);
    }

    .value {
      font-weight: bold;

      &.highlight {
        color: var(--el-color-primary);
      }

      &.positive {
        color: var(--el-color-success);
      }

      &.negative {
        color: var(--el-color-danger);
      }

      &.neutral {
        color: var(--el-text-color-regular);
      }
    }
  }
}

.dialog-footer {
  text-align: right;
}

:deep(.el-input-number) {
  width: 100%;
}
</style>