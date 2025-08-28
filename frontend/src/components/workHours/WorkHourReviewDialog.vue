<template>
  <el-dialog
    v-model="dialogVisible"
    :title="getDialogTitle()"
    width="500px"
    @close="handleClose"
  >
    <div class="work-hour-info" v-if="workHour">
      <el-descriptions :column="1" border>
        <el-descriptions-item label="成员姓名">
          {{ workHour.memberName }}
        </el-descriptions-item>
        <el-descriptions-item label="任务标题">
          {{ workHour.taskTitle }}
        </el-descriptions-item>
        <el-descriptions-item label="当前工时">
          <span class="current-hours">{{ workHour.totalHours }}h</span>
          <span class="hours-breakdown">
            (基础: {{ workHour.baseHours }}h, 奖励: +{{ workHour.bonusHours }}h,
            惩罚: -{{ workHour.penaltyHours }}h)
          </span>
        </el-descriptions-item>
      </el-descriptions>
    </div>

    <el-divider />

    <el-form :model="form" :rules="rules" ref="formRef" label-width="100px">
      <el-form-item label="审核类型">
        <el-tag :type="getReviewTypeColor(reviewType) as any">
          {{ getReviewTypeText(reviewType) }}
        </el-tag>
      </el-form-item>

      <el-form-item
        label="调整工时"
        prop="adjustedHours"
        v-if="reviewType === 'adjust' || showAdjustHours"
      >
        <el-input-number
          v-model="form.adjustedHours"
          :min="0"
          :max="1000"
          :precision="1"
          :step="0.5"
          style="width: 100%"
        />
      </el-form-item>

      <el-form-item label="审核说明" prop="reviewNotes">
        <el-input
          v-model="form.reviewNotes"
          type="textarea"
          :rows="4"
          :placeholder="getPlaceholder()"
        />
      </el-form-item>

      <el-form-item v-if="reviewType === 'approve'">
        <el-checkbox v-model="showAdjustHours"> 同时调整工时 </el-checkbox>
      </el-form-item>

      <!-- 审核预览 -->
      <el-form-item
        label="审核预览"
        v-if="reviewType === 'adjust' || showAdjustHours"
      >
        <div class="review-preview">
          <div class="preview-item">
            <span class="label">当前工时：</span>
            <span class="value">{{ workHour?.totalHours }}h</span>
          </div>
          <div
            class="preview-item"
            v-if="form.adjustedHours !== workHour?.totalHours"
          >
            <span class="label">调整后：</span>
            <span class="value highlight">{{ form.adjustedHours }}h</span>
          </div>
          <div class="preview-item">
            <span class="label">审核结果：</span>
            <el-tag :type="getReviewTypeColor(reviewType) as any" size="small">
              {{ getReviewTypeText(reviewType) }}
            </el-tag>
          </div>
        </div>
      </el-form-item>
    </el-form>

    <template #footer>
      <div class="dialog-footer">
        <el-button @click="handleClose">取消</el-button>
        <el-button
          :type="getButtonType() as any"
          @click="handleSubmit"
          :loading="loading"
        >
          {{ getButtonText() }}
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
  reviewType: 'approve' | 'reject' | 'adjust'
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
const showAdjustHours = ref(false)

const form = reactive({
  adjustedHours: 0,
  reviewNotes: ''
})

const rules = computed((): FormRules => {
  const baseRules: FormRules = {
    reviewNotes: [
      { required: true, message: '请输入审核说明', trigger: 'blur' },
      { min: 5, message: '审核说明至少需要5个字符', trigger: 'blur' }
    ]
  }

  if (props.reviewType === 'adjust' || showAdjustHours.value) {
    baseRules.adjustedHours = [
      { required: true, message: '请输入调整后的工时', trigger: 'blur' },
      {
        type: 'number',
        min: 0,
        max: 1000,
        message: '工时必须在0-1000之间',
        trigger: 'blur'
      }
    ]
  }

  return baseRules
})

watch(
  () => props.visible,
  visible => {
    dialogVisible.value = visible
    if (visible && props.workHour) {
      form.adjustedHours = props.workHour.totalHours
      form.reviewNotes = ''
      showAdjustHours.value = false
    }
  }
)

watch(dialogVisible, visible => {
  emit('update:visible', visible)
})

const getDialogTitle = () => {
  const titleMap = {
    approve: '批准工时',
    reject: '拒绝工时',
    adjust: '调整工时'
  }
  return titleMap[props.reviewType] || '审核工时'
}

const getReviewTypeColor = (type: string) => {
  const colorMap = {
    approve: 'success',
    reject: 'danger',
    adjust: 'warning'
  }
  return colorMap[type as keyof typeof colorMap] || 'info'
}

const getReviewTypeText = (type: string) => {
  const textMap = {
    approve: '批准',
    reject: '拒绝',
    adjust: '调整'
  }
  return textMap[type as keyof typeof textMap] || type
}

const getPlaceholder = () => {
  const placeholderMap = {
    approve: '请输入批准理由...',
    reject: '请输入拒绝理由...',
    adjust: '请输入调整理由...'
  }
  return placeholderMap[props.reviewType] || '请输入审核说明...'
}

const getButtonType = () => {
  const typeMap = {
    approve: 'success',
    reject: 'danger',
    adjust: 'warning'
  }
  return typeMap[props.reviewType] || 'primary'
}

const getButtonText = () => {
  const textMap = {
    approve: '批准',
    reject: '拒绝',
    adjust: '确认调整'
  }
  return textMap[props.reviewType] || '确认'
}

const handleSubmit = async () => {
  if (!formRef.value || !props.workHour) return

  try {
    await formRef.value.validate()

    loading.value = true

    const adjustedHours =
      props.reviewType === 'adjust' || showAdjustHours.value
        ? form.adjustedHours
        : undefined

    await workHoursApi.reviewWorkHour(
      props.workHour.id,
      props.reviewType,
      form.reviewNotes,
      adjustedHours
    )

    ElMessage.success('审核完成')
    emit('success')
    handleClose()
  } catch (error) {
    console.error('审核失败:', error)
    ElMessage.error('审核失败')
  } finally {
    loading.value = false
  }
}

const handleClose = () => {
  dialogVisible.value = false
  formRef.value?.resetFields()
  showAdjustHours.value = false
  loading.value = false
}
</script>

<style lang="scss" scoped>
.work-hour-info {
  margin-bottom: 20px;

  .current-hours {
    font-weight: bold;
    color: var(--el-color-primary);
  }

  .hours-breakdown {
    font-size: 12px;
    color: var(--el-text-color-regular);
    margin-left: 8px;
  }
}

.review-preview {
  background-color: var(--el-fill-color-light);
  padding: 15px;
  border-radius: 6px;
  border: 1px solid var(--el-border-color-lighter);

  .preview-item {
    display: flex;
    justify-content: space-between;
    align-items: center;
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
