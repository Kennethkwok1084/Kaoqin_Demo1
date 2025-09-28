<template>
  <el-dialog
    v-model="visible"
    title="任务工时详情"
    width="800px"
    @close="handleClose"
  >
    <div v-if="record" class="task-work-hours-detail">
      <!-- 任务基本信息 -->
      <div class="detail-header">
        <div class="task-info">
          <div class="task-title">
            <h3>{{ record.title || '任务标题' }}</h3>
            <el-tag :type="getTaskTypeTag(record.task_type || '')" size="default">
              {{ getTaskTypeLabel(record.task_type || '') }}
            </el-tag>
          </div>
          <div class="task-meta">
            <span class="task-id">任务编号: {{ record.task_id || record.id || '-' }}</span>
            <span class="task-category">分类: {{ record.task_category || '常规任务' }}</span>
          </div>
        </div>
        <div class="work-hours-summary">
          <div class="hours-display">
            <span class="hours">{{ formatWorkHours(record.work_hours || record.workHours) }}</span>
            <span class="unit">小时</span>
          </div>
          <div class="minutes-display">
            <span class="minutes">{{ record.work_minutes || Math.round((record.workHours || 0) * 60) }}</span>
            <span class="unit">分钟</span>
          </div>
        </div>
      </div>

      <!-- 详细信息 -->
      <el-descriptions :column="2" border class="detail-descriptions">
        <el-descriptions-item label="负责人">
          <div class="member-info">
            <el-avatar
              :size="32"
              :style="{ backgroundColor: getAvatarColor(record.member_name || record.memberName) }"
            >
              {{ (record.member_name || record.memberName)?.charAt(0) }}
            </el-avatar>
            <span class="member-name">{{ record.member_name || record.memberName }}</span>
          </div>
        </el-descriptions-item>

        <el-descriptions-item label="工作日期">
          {{ formatDateShort(record.work_date || record.date) }} {{ getWeekday(record.work_date || record.date) }}
        </el-descriptions-item>

        <el-descriptions-item label="任务来源">
          <el-tag :type="getSourceTypeTag(record.source || 'task')" size="small">
            {{ getSourceLabel(record.source || 'task') }}
          </el-tag>
        </el-descriptions-item>

        <el-descriptions-item label="任务评分">
          <div class="rating-display">
            <el-rate
              :model-value="record.rating || 5"
              disabled
              show-score
              text-color="#ff9900"
              score-template="{value} 分"
            />
          </div>
        </el-descriptions-item>

        <el-descriptions-item label="工时计算" :span="2">
          <div class="work-hours-calculation">
            <div class="calculation-item">
              <span class="label">基础工时:</span>
              <span class="value">{{ getBaseWorkHours(record) }} 分钟</span>
            </div>
            <div class="calculation-item" v-if="getBonusMinutes(record) > 0">
              <span class="label">奖励工时:</span>
              <span class="value positive">+{{ getBonusMinutes(record) }} 分钟</span>
            </div>
            <div class="calculation-item" v-if="getPenaltyMinutes(record) > 0">
              <span class="label">惩罚扣除:</span>
              <span class="value negative">-{{ getPenaltyMinutes(record) }} 分钟</span>
            </div>
            <div class="calculation-total">
              <span class="label">实际工时:</span>
              <span class="value total">{{ record.work_minutes || Math.round((record.workHours || 0) * 60) }} 分钟</span>
            </div>
          </div>
        </el-descriptions-item>

        <el-descriptions-item label="任务详情" :span="2">
          <div class="task-description">
            {{ record.description || record.remark || '暂无详细描述' }}
          </div>
        </el-descriptions-item>
      </el-descriptions>

      <!-- 工时统计图表 -->
      <div class="charts-section" v-if="showCharts">
        <el-card>
          <template #header>
            <div class="chart-header">
              <span>工时趋势分析</span>
              <el-button-group size="small">
                <el-button
                  :type="chartPeriod === 'week' ? 'primary' : ''"
                  @click="chartPeriod = 'week'"
                >
                  近一周
                </el-button>
                <el-button
                  :type="chartPeriod === 'month' ? 'primary' : ''"
                  @click="chartPeriod = 'month'"
                >
                  近一月
                </el-button>
              </el-button-group>
            </div>
          </template>
          <div class="chart-container">
            <div id="workHoursChart" style="height: 300px;"></div>
          </div>
        </el-card>
      </div>

      <!-- 操作日志 -->
      <div class="operation-logs" v-if="showLogs">
        <el-card>
          <template #header>
            <span>操作日志</span>
          </template>
          <el-timeline>
            <el-timeline-item
              v-for="log in operationLogs"
              :key="log.id"
              :timestamp="formatDateTime(log.created_at)"
              :type="getLogType(log.action)"
            >
              <div class="log-content">
                <div class="log-action">{{ log.action_label }}</div>
                <div class="log-detail">{{ log.detail }}</div>
                <div class="log-user">操作人: {{ log.operator_name }}</div>
              </div>
            </el-timeline-item>
          </el-timeline>
        </el-card>
      </div>

      <!-- 相关任务 -->
      <div class="related-tasks" v-if="relatedTasks.length > 0">
        <el-card>
          <template #header>
            <span>相关任务</span>
          </template>
          <el-table :data="relatedTasks" size="small">
            <el-table-column prop="task_id" label="任务编号" width="120" />
            <el-table-column prop="title" label="任务标题" />
            <el-table-column prop="work_date" label="工作日期" width="120">
              <template #default="{ row }">
                {{ formatDateShort(row.work_date || row.date) }}
              </template>
            </el-table-column>
            <el-table-column prop="work_hours" label="工时" width="80">
              <template #default="{ row }">
                {{ formatWorkHours(row.work_hours || row.workHours) }}h
              </template>
            </el-table-column>
            <el-table-column label="操作" width="80">
              <template #default="{ row }">
                <el-button
                  size="small"
                  type="primary"
                  link
                  @click="viewRelatedTask(row)"
                >
                  查看
                </el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </div>
    </div>

    <div v-else class="no-data">
      <el-empty description="暂无工时数据" />
    </div>

    <template #footer>
      <div class="dialog-footer">
        <el-button @click="handleClose">关闭</el-button>
        <el-button v-if="record" type="primary" @click="handleEdit">
          调整工时
        </el-button>
        <el-button v-if="record" type="warning" @click="handleRecalculate">
          重新计算
        </el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'
import type { WorkHoursRecord, AttendanceRecord } from '@/types/attendance'
import { formatDate, formatDateShort, formatTime, formatDateTime } from '@/utils/date'
import { attendanceApi } from '@/api/attendance'

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
  edit: [record: AttendanceRecord]
  recalculate: [record: AttendanceRecord]
}>()

// 响应式数据
const visible = computed({
  get: () => props.modelValue,
  set: value => emit('update:modelValue', value)
})

const showCharts = ref(true)
const showLogs = ref(true)
const chartPeriod = ref<'week' | 'month'>('week')
const relatedTasks = ref<AttendanceRecord[]>([])
const operationLogs = ref<any[]>([])

// 方法
const handleClose = () => {
  emit('update:modelValue', false)
}

const handleEdit = () => {
  if (props.record) {
    emit('edit', props.record)
  }
}

const handleRecalculate = () => {
  if (props.record) {
    emit('recalculate', props.record)
  }
}

const formatWorkHours = (hours: number) => {
  return (hours || 0).toFixed(1)
}

const getTaskTypeLabel = (taskType: string) => {
  const labels = {
    'repair': '维修任务',
    'monitoring': '监控任务',
    'assistance': '协助任务',
    'maintenance': '维护任务',
    'emergency': '紧急任务'
  }
  return labels[taskType as keyof typeof labels] || taskType
}

const getTaskTypeTag = (taskType: string) => {
  const tags = {
    'repair': 'warning',
    'monitoring': 'info',
    'assistance': 'success',
    'maintenance': 'primary',
    'emergency': 'danger'
  }
  return tags[taskType as keyof typeof tags] || 'info'
}

const getSourceLabel = (source: string) => {
  const labels = {
    'repair_task': '维修工单',
    'monitoring_task': '监控任务',
    'assistance_task': '协助任务'
  }
  return labels[source as keyof typeof labels] || source
}

const getSourceTypeTag = (source: string) => {
  const tags = {
    'repair_task': 'warning',
    'monitoring_task': 'info',
    'assistance_task': 'success'
  }
  return tags[source as keyof typeof tags] || 'info'
}

const getBaseWorkHours = (record: AttendanceRecord) => {
  // 基础工时逻辑：线上40分钟，线下100分钟
  const isOnline = record.task_category?.includes('线上') ||
                  record.task_category?.includes('在线')
  return isOnline ? 40 : 100
}

const getBonusMinutes = (record: AttendanceRecord) => {
  // 奖励分钟数计算逻辑
  let bonus = 0

  // 高评分奖励
  if (record.rating >= 4.5) {
    bonus += 30
  } else if (record.rating >= 4.0) {
    bonus += 15
  }

  // 其他奖励逻辑可以在这里添加

  return bonus
}

const getPenaltyMinutes = (record: AttendanceRecord) => {
  // 惩罚分钟数计算逻辑
  let penalty = 0

  // 低评分惩罚
  if (record.rating < 3.0) {
    penalty += 60
  } else if (record.rating < 3.5) {
    penalty += 30
  }

  // 其他惩罚逻辑可以在这里添加

  return penalty
}

const getAvatarColor = (name: string) => {
  const colors = ['#409EFF', '#67C23A', '#E6A23C', '#F56C6C', '#909399']
  const hash = name?.split('').reduce((acc, char) => acc + char.charCodeAt(0), 0) || 0
  return colors[hash % colors.length]
}

const getWeekday = (date: string | Date) => {
  const weekdays = ['周日', '周一', '周二', '周三', '周四', '周五', '周六']
  return weekdays[new Date(date).getDay()]
}

const getLogType = (action: string) => {
  const types = {
    'create': 'primary',
    'update': 'warning',
    'recalculate': 'info',
    'approve': 'success',
    'reject': 'danger'
  }
  return types[action as keyof typeof types] || 'info'
}

const viewRelatedTask = (task: AttendanceRecord) => {
  // 查看相关任务详情
  console.log('查看相关任务:', task)
}

const loadRelatedTasks = async () => {
  if (!props.record) return

  try {
    // 加载同一成员的相关任务
    const tasks = await attendanceApi.getMemberWorkHoursRecords(
      props.record.member_id,
      {
        page: 1,
        size: 5,
        date_from: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
        date_to: new Date().toISOString().split('T')[0]
      }
    )

    // 过滤掉当前记录
    relatedTasks.value = tasks.filter(task => task.id !== props.record?.id)
  } catch (error) {
    console.error('加载相关任务失败:', error)
  }
}

const loadOperationLogs = async () => {
  // 模拟操作日志数据
  operationLogs.value = [
    {
      id: 1,
      action: 'create',
      action_label: '创建工时记录',
      detail: '系统自动根据任务完成情况生成工时记录',
      operator_name: '系统',
      created_at: props.record?.work_date
    },
    {
      id: 2,
      action: 'recalculate',
      action_label: '重新计算工时',
      detail: '根据最新的评分和奖惩规则重新计算工时',
      operator_name: '管理员',
      created_at: new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString()
    }
  ]
}

// 监听记录变化
watch(() => props.record, (newRecord) => {
  if (newRecord) {
    loadRelatedTasks()
    loadOperationLogs()
  }
}, { immediate: true })
</script>

<style scoped lang="scss">
@use '@/styles/variables.scss' as *;
@use '@/styles/mixins.scss' as *;

.task-work-hours-detail {
  .detail-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    margin-bottom: 24px;
    padding: 20px;
    background: linear-gradient(135deg, #f0f9ff, #ecf5ff);
    border-radius: 12px;

    .task-info {
      flex: 1;

      .task-title {
        display: flex;
        align-items: center;
        gap: 12px;
        margin-bottom: 8px;

        h3 {
          font-size: 18px;
          font-weight: 600;
          color: $text-color-primary;
          margin: 0;
        }
      }

      .task-meta {
        display: flex;
        gap: 16px;
        font-size: 14px;
        color: $text-color-regular;

        .task-id, .task-category {
          white-space: nowrap;
        }
      }
    }

    .work-hours-summary {
      text-align: right;

      .hours-display {
        margin-bottom: 4px;

        .hours {
          font-size: 28px;
          font-weight: 600;
          color: $primary-color;
        }

        .unit {
          font-size: 14px;
          color: $text-color-regular;
          margin-left: 4px;
        }
      }

      .minutes-display {
        .minutes {
          font-size: 16px;
          font-weight: 500;
          color: $text-color-secondary;
        }

        .unit {
          font-size: 12px;
          color: $text-color-regular;
          margin-left: 2px;
        }
      }
    }
  }

  .detail-descriptions {
    margin-bottom: 24px;

    .member-info {
      display: flex;
      align-items: center;
      gap: 8px;

      .member-name {
        font-weight: 500;
        color: $text-color-primary;
      }
    }

    .rating-display {
      display: flex;
      align-items: center;
    }

    .work-hours-calculation {
      .calculation-item {
        display: flex;
        justify-content: space-between;
        margin-bottom: 8px;
        padding: 4px 0;

        .label {
          color: $text-color-regular;
        }

        .value {
          font-weight: 500;

          &.positive {
            color: $success-color;
          }

          &.negative {
            color: $danger-color;
          }

          &.total {
            color: $primary-color;
            font-size: 16px;
          }
        }
      }

      .calculation-total {
        border-top: 1px solid $border-color-lighter;
        padding-top: 8px;
        margin-top: 8px;
        display: flex;
        justify-content: space-between;
      }
    }

    .task-description {
      line-height: 1.6;
      color: $text-color-primary;
      white-space: pre-wrap;
      background: #f8f9fa;
      padding: 12px;
      border-radius: 6px;
      border-left: 3px solid $primary-color;
    }
  }

  .charts-section {
    margin-bottom: 24px;

    .chart-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
    }

    .chart-container {
      margin-top: 16px;
    }
  }

  .operation-logs {
    margin-bottom: 24px;

    .log-content {
      .log-action {
        font-weight: 500;
        color: $text-color-primary;
        margin-bottom: 4px;
      }

      .log-detail {
        color: $text-color-regular;
        font-size: 14px;
        margin-bottom: 4px;
      }

      .log-user {
        color: $text-color-secondary;
        font-size: 12px;
      }
    }
  }

  .related-tasks {
    margin-bottom: 16px;
  }
}

.no-data {
  padding: 40px;
  text-align: center;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

@include respond-to(sm) {
  .task-work-hours-detail {
    .detail-header {
      flex-direction: column;
      gap: 16px;

      .work-hours-summary {
        text-align: left;
      }
    }

    .charts-section {
      .chart-header {
        flex-direction: column;
        gap: 12px;
        align-items: flex-start;
      }
    }
  }
}
</style>