<template>
  <el-dialog
    v-model="dialogVisible"
    title="批量审核工时"
    width="700px"
    @close="handleClose"
  >
    <div class="batch-review-content">
      <!-- 选中的工时列表 -->
      <el-card class="selected-hours-card">
        <template #header>
          <span>待审核工时 ({{ workHours.length }} 条)</span>
        </template>

        <el-table :data="workHours" max-height="300" stripe>
          <el-table-column prop="memberName" label="成员" width="100" />
          <el-table-column
            prop="taskTitle"
            label="任务"
            min-width="200"
            show-overflow-tooltip
          />
          <el-table-column prop="taskType" label="类型" width="80">
            <template #default="{ row }">
              <el-tag
                :type="getTaskTypeColor(row.taskType) as any"
                size="small"
              >
                {{ getTaskTypeText(row.taskType) }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="totalHours" label="工时" width="80">
            <template #default="{ row }"> {{ row.totalHours }}h </template>
          </el-table-column>
          <el-table-column prop="status" label="状态" width="80">
            <template #default="{ row }">
              <el-tag :type="getStatusColor(row.status) as any" size="small">
                {{ getStatusText(row.status) }}
              </el-tag>
            </template>
          </el-table-column>
        </el-table>
      </el-card>

      <!-- 批量操作表单 -->
      <el-card class="batch-form-card">
        <template #header>
          <span>批量操作设置</span>
        </template>

        <el-form :model="form" :rules="rules" ref="formRef" label-width="100px">
          <el-form-item label="审核操作" prop="reviewType">
            <el-radio-group v-model="form.reviewType">
              <el-radio value="approve">
                <el-icon><Check /></el-icon>
                批量通过
              </el-radio>
              <el-radio value="reject">
                <el-icon><Close /></el-icon>
                批量拒绝
              </el-radio>
            </el-radio-group>
          </el-form-item>

          <el-form-item label="审核说明" prop="reviewNotes">
            <el-input
              v-model="form.reviewNotes"
              type="textarea"
              :rows="3"
              :placeholder="getPlaceholder()"
            />
          </el-form-item>

          <!-- 统计信息 -->
          <el-form-item label="操作统计">
            <div class="batch-statistics">
              <div class="stat-item">
                <span class="stat-label">总工时：</span>
                <span class="stat-value">{{ totalHours.toFixed(1) }}h</span>
              </div>
              <div class="stat-item">
                <span class="stat-label">涉及成员：</span>
                <span class="stat-value">{{ uniqueMembers }} 人</span>
              </div>
              <div class="stat-item">
                <span class="stat-label">任务数量：</span>
                <span class="stat-value">{{ workHours.length }} 个</span>
              </div>
            </div>
          </el-form-item>
        </el-form>
      </el-card>

      <!-- 风险提示 -->
      <el-alert
        v-if="form.reviewType === 'reject'"
        title="批量拒绝提醒"
        type="warning"
        description="批量拒绝工时将影响员工的工时统计，请确认操作的必要性和合理性。"
        show-icon
        :closable="false"
      />

      <el-alert
        v-if="form.reviewType === 'approve'"
        title="批量通过提醒"
        type="success"
        description="批量通过后，这些工时将被确认并纳入统计，无法撤销。"
        show-icon
        :closable="false"
      />
    </div>

    <template #footer>
      <div class="dialog-footer">
        <el-button @click="handleClose">取消</el-button>
        <el-button
          :type="form.reviewType === 'approve' ? 'success' : 'danger'"
          @click="handleSubmit"
          :loading="loading"
        >
          <el-icon v-if="form.reviewType === 'approve'"><Check /></el-icon>
          <el-icon v-else><Close /></el-icon>
          确认{{ form.reviewType === 'approve' ? '通过' : '拒绝' }}
        </el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, reactive, watch, computed } from 'vue'
import {
  ElMessage,
  ElMessageBox,
  type FormInstance,
  type FormRules
} from 'element-plus'
import { Check, Close } from '@element-plus/icons-vue'
import { workHoursApi } from '@/api/workHours'
import type { WorkHour } from '@/types/workHours'

interface Props {
  visible: boolean
  workHours: WorkHour[]
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
  reviewType: 'approve' as 'approve' | 'reject',
  reviewNotes: ''
})

const rules: FormRules = {
  reviewType: [
    { required: true, message: '请选择审核操作', trigger: 'change' }
  ],
  reviewNotes: [
    { required: true, message: '请输入审核说明', trigger: 'blur' },
    { min: 10, message: '审核说明至少需要10个字符', trigger: 'blur' }
  ]
}

const totalHours = computed(() => {
  return props.workHours.reduce((sum, hour) => sum + hour.totalHours, 0)
})

const uniqueMembers = computed(() => {
  const memberIds = new Set(props.workHours.map(hour => hour.memberId))
  return memberIds.size
})

watch(
  () => props.visible,
  visible => {
    dialogVisible.value = visible
    if (visible) {
      form.reviewType = 'approve'
      form.reviewNotes = ''
    }
  }
)

watch(dialogVisible, visible => {
  emit('update:visible', visible)
})

const getPlaceholder = () => {
  if (form.reviewType === 'approve') {
    return '请输入批量通过的理由，如：工时记录准确，任务完成质量良好...'
  } else {
    return '请输入批量拒绝的理由，如：工时记录存在问题，需要重新核实...'
  }
}

const getTaskTypeColor = (type: string) => {
  const colorMap = {
    repair: 'danger',
    monitoring: 'warning',
    assistance: 'success'
  }
  return colorMap[type as keyof typeof colorMap] || 'info'
}

const getTaskTypeText = (type: string) => {
  const textMap = {
    repair: '维修',
    monitoring: '监控',
    assistance: '协助'
  }
  return textMap[type as keyof typeof textMap] || type
}

const getStatusColor = (status: string) => {
  const colorMap = {
    pending: 'warning',
    approved: 'success',
    rejected: 'danger'
  }
  return colorMap[status as keyof typeof colorMap] || 'info'
}

const getStatusText = (status: string) => {
  const textMap = {
    pending: '待审核',
    approved: '已通过',
    rejected: '已拒绝'
  }
  return textMap[status as keyof typeof textMap] || status
}

const handleSubmit = async () => {
  if (!formRef.value) return

  try {
    await formRef.value.validate()

    const actionText = form.reviewType === 'approve' ? '通过' : '拒绝'
    await ElMessageBox.confirm(
      `确定要批量${actionText} ${props.workHours.length} 条工时记录吗？此操作不可撤销。`,
      `确认批量${actionText}`,
      {
        type: 'warning',
        confirmButtonText: `确认${actionText}`,
        cancelButtonText: '取消'
      }
    )

    loading.value = true

    const workHourIds = props.workHours.map(hour => hour.id)
    await workHoursApi.batchReviewWorkHours(
      workHourIds,
      form.reviewType,
      form.reviewNotes
    )

    ElMessage.success(`批量${actionText}成功`)
    emit('success')
    handleClose()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('批量审核失败:', error)
      ElMessage.error('批量审核失败')
    }
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
.batch-review-content {
  .selected-hours-card,
  .batch-form-card {
    margin-bottom: 20px;

    &:last-child {
      margin-bottom: 0;
    }
  }

  .batch-statistics {
    display: flex;
    gap: 20px;
    padding: 10px 0;

    .stat-item {
      display: flex;
      align-items: center;

      .stat-label {
        color: var(--el-text-color-regular);
        margin-right: 8px;
      }

      .stat-value {
        font-weight: bold;
        color: var(--el-color-primary);
      }
    }
  }
}

:deep(.el-alert) {
  margin-top: 16px;
}

.dialog-footer {
  text-align: right;
}

:deep(.el-radio) {
  display: flex;
  align-items: center;
  margin-bottom: 10px;

  .el-icon {
    margin-right: 5px;
  }
}
</style>
