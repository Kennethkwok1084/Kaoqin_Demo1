<template>
  <el-dialog
    v-model="dialogVisible"
    title="工时详情"
    width="800px"
    @close="handleClose"
  >
    <div class="work-hour-detail" v-if="workHour">
      <!-- 基本信息 -->
      <el-card class="info-card">
        <template #header>
          <span>基本信息</span>
        </template>
        
        <el-row :gutter="20">
          <el-col :span="12">
            <el-descriptions :column="1" border>
              <el-descriptions-item label="成员姓名">
                {{ workHour.memberName }}
              </el-descriptions-item>
              <el-descriptions-item label="任务标题">
                {{ workHour.taskTitle }}
              </el-descriptions-item>
              <el-descriptions-item label="任务类型">
                <el-tag :type="getTaskTypeColor(workHour.taskType)">
                  {{ getTaskTypeText(workHour.taskType) }}
                </el-tag>
              </el-descriptions-item>
              <el-descriptions-item label="审核状态">
                <el-tag :type="getStatusColor(workHour.status)">
                  {{ getStatusText(workHour.status) }}
                </el-tag>
              </el-descriptions-item>
            </el-descriptions>
          </el-col>
          
          <el-col :span="12">
            <el-descriptions :column="1" border>
              <el-descriptions-item label="创建时间">
                {{ formatDateTime(workHour.createdAt) }}
              </el-descriptions-item>
              <el-descriptions-item label="更新时间">
                {{ formatDateTime(workHour.updatedAt) }}
              </el-descriptions-item>
              <el-descriptions-item label="审核时间" v-if="workHour.approvedAt">
                {{ formatDateTime(workHour.approvedAt) }}
              </el-descriptions-item>
              <el-descriptions-item label="审核人" v-if="workHour.approvedBy">
                {{ workHour.approvedBy }}
              </el-descriptions-item>
            </el-descriptions>
          </el-col>
        </el-row>
      </el-card>

      <!-- 工时详情 -->
      <el-card class="hours-card">
        <template #header>
          <span>工时计算详情</span>
        </template>
        
        <div class="hours-breakdown">
          <el-row :gutter="20">
            <el-col :span="6">
              <div class="hours-item base">
                <div class="hours-value">{{ workHour.baseHours }}h</div>
                <div class="hours-label">基础工时</div>
              </div>
            </el-col>
            
            <el-col :span="6">
              <div class="hours-item bonus">
                <div class="hours-value">+{{ workHour.bonusHours }}h</div>
                <div class="hours-label">奖励工时</div>
              </div>
            </el-col>
            
            <el-col :span="6">
              <div class="hours-item penalty">
                <div class="hours-value">-{{ workHour.penaltyHours }}h</div>
                <div class="hours-label">惩罚工时</div>
              </div>
            </el-col>
            
            <el-col :span="6">
              <div class="hours-item total">
                <div class="hours-value">{{ workHour.totalHours }}h</div>
                <div class="hours-label">总工时</div>
              </div>
            </el-col>
          </el-row>
        </div>

        <!-- 工时计算公式展示 -->
        <el-divider />
        
        <div class="calculation-formula">
          <h4>计算公式</h4>
          <div class="formula">
            总工时 = 基础工时 + 奖励工时 - 惩罚工时
          </div>
          <div class="formula-detail">
            {{ workHour.totalHours }}h = {{ workHour.baseHours }}h + {{ workHour.bonusHours }}h - {{ workHour.penaltyHours }}h
          </div>
        </div>
      </el-card>

      <!-- 调整记录 -->
      <el-card class="adjustments-card" v-if="adjustments.length">
        <template #header>
          <span>调整记录</span>
        </template>
        
        <el-timeline>
          <el-timeline-item
            v-for="adjustment in adjustments"
            :key="adjustment.id"
            :timestamp="formatDateTime(adjustment.adjustedAt)"
            placement="top"
          >
            <el-card>
              <div class="adjustment-content">
                <div class="adjustment-header">
                  <span class="adjustment-type">{{ getAdjustmentTypeText(adjustment.adjustmentType) }}</span>
                  <span class="adjustment-hours">
                    {{ adjustment.originalHours }}h → {{ adjustment.adjustedHours }}h
                  </span>
                </div>
                <div class="adjustment-reason">{{ adjustment.reason }}</div>
                <div class="adjustment-author">调整人：{{ adjustment.adjustedBy }}</div>
              </div>
            </el-card>
          </el-timeline-item>
        </el-timeline>
      </el-card>

      <!-- 审核记录 -->
      <el-card class="reviews-card" v-if="reviews.length">
        <template #header>
          <span>审核记录</span>
        </template>
        
        <el-timeline>
          <el-timeline-item
            v-for="review in reviews"
            :key="review.id"
            :timestamp="formatDateTime(review.reviewedAt)"
            placement="top"
          >
            <el-card>
              <div class="review-content">
                <div class="review-header">
                  <el-tag :type="getReviewTypeColor(review.reviewType)">
                    {{ getReviewTypeText(review.reviewType) }}
                  </el-tag>
                  <span class="review-hours" v-if="review.adjustedHours">
                    调整为：{{ review.adjustedHours }}h
                  </span>
                </div>
                <div class="review-notes" v-if="review.reviewNotes">{{ review.reviewNotes }}</div>
                <div class="review-author">审核人：{{ review.reviewedBy }}</div>
              </div>
            </el-card>
          </el-timeline-item>
        </el-timeline>
      </el-card>

      <!-- 备注信息 -->
      <el-card class="notes-card" v-if="workHour.adjustmentReason || workHour.adminNotes">
        <template #header>
          <span>备注信息</span>
        </template>
        
        <el-descriptions :column="1" border>
          <el-descriptions-item label="调整原因" v-if="workHour.adjustmentReason">
            {{ workHour.adjustmentReason }}
          </el-descriptions-item>
          <el-descriptions-item label="管理员备注" v-if="workHour.adminNotes">
            {{ workHour.adminNotes }}
          </el-descriptions-item>
        </el-descriptions>
      </el-card>
    </div>

    <template #footer>
      <div class="dialog-footer">
        <el-button @click="handleClose">关闭</el-button>
        <el-button type="primary" @click="handleRefresh" :loading="loading">
          <el-icon><Refresh /></el-icon>
          刷新
        </el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, watch, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Refresh } from '@element-plus/icons-vue'
import { workHoursApi } from '@/api/workHours'
import type { WorkHour, WorkHourAdjustment, WorkHourReview } from '@/types/workHours'

interface Props {
  visible: boolean
  workHour: WorkHour | null
}

interface Emits {
  (e: 'update:visible', value: boolean): void
  (e: 'refresh'): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

const dialogVisible = ref(false)
const loading = ref(false)
const adjustments = ref<WorkHourAdjustment[]>([])
const reviews = ref<WorkHourReview[]>([])

watch(() => props.visible, (visible) => {
  dialogVisible.value = visible
  if (visible && props.workHour) {
    loadAdjustments()
    loadReviews()
  }
})

watch(dialogVisible, (visible) => {
  emit('update:visible', visible)
})

const loadAdjustments = async () => {
  if (!props.workHour) return

  try {
    adjustments.value = await workHoursApi.getWorkHourAdjustments(props.workHour.id)
  } catch (error) {
    console.error('加载调整记录失败:', error)
  }
}

const loadReviews = async () => {
  if (!props.workHour) return

  try {
    reviews.value = await workHoursApi.getWorkHourReviews(props.workHour.id)
  } catch (error) {
    console.error('加载审核记录失败:', error)
  }
}

const handleRefresh = async () => {
  loading.value = true
  try {
    await Promise.all([loadAdjustments(), loadReviews()])
    emit('refresh')
    ElMessage.success('数据刷新成功')
  } catch (error) {
    ElMessage.error('数据刷新失败')
  } finally {
    loading.value = false
  }
}

const handleClose = () => {
  dialogVisible.value = false
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
    repair: '维修任务',
    monitoring: '监控任务',
    assistance: '协助任务'
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

const getAdjustmentTypeText = (type: string) => {
  const textMap = {
    bonus: '奖励调整',
    penalty: '惩罚调整',
    manual: '手动调整'
  }
  return textMap[type as keyof typeof textMap] || type
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
    approve: '通过',
    reject: '拒绝',
    adjust: '调整'
  }
  return textMap[type as keyof typeof textMap] || type
}

const formatDateTime = (dateStr: string) => {
  return new Date(dateStr).toLocaleString()
}
</script>

<style lang="scss" scoped>
.work-hour-detail {
  .info-card,
  .hours-card,
  .adjustments-card,
  .reviews-card,
  .notes-card {
    margin-bottom: 20px;

    &:last-child {
      margin-bottom: 0;
    }
  }

  .hours-breakdown {
    .hours-item {
      text-align: center;
      padding: 20px;
      border-radius: 8px;
      
      .hours-value {
        font-size: 24px;
        font-weight: bold;
        margin-bottom: 8px;
      }

      .hours-label {
        font-size: 14px;
        color: var(--el-text-color-regular);
      }

      &.base {
        background-color: var(--el-color-info-light-9);
        .hours-value {
          color: var(--el-color-info);
        }
      }

      &.bonus {
        background-color: var(--el-color-success-light-9);
        .hours-value {
          color: var(--el-color-success);
        }
      }

      &.penalty {
        background-color: var(--el-color-danger-light-9);
        .hours-value {
          color: var(--el-color-danger);
        }
      }

      &.total {
        background-color: var(--el-color-primary-light-9);
        .hours-value {
          color: var(--el-color-primary);
        }
      }
    }
  }

  .calculation-formula {
    text-align: center;

    h4 {
      margin-bottom: 10px;
      color: var(--el-text-color-primary);
    }

    .formula {
      font-size: 16px;
      color: var(--el-text-color-regular);
      margin-bottom: 8px;
    }

    .formula-detail {
      font-size: 18px;
      font-weight: bold;
      color: var(--el-color-primary);
    }
  }

  .adjustment-content,
  .review-content {
    .adjustment-header,
    .review-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 10px;

      .adjustment-type {
        font-weight: bold;
      }

      .adjustment-hours,
      .review-hours {
        font-family: monospace;
        font-weight: bold;
        color: var(--el-color-primary);
      }
    }

    .adjustment-reason,
    .review-notes {
      margin-bottom: 8px;
      color: var(--el-text-color-regular);
    }

    .adjustment-author,
    .review-author {
      font-size: 12px;
      color: var(--el-text-color-secondary);
    }
  }
}

.dialog-footer {
  text-align: right;
}
</style>