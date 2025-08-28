<template>
  <el-dialog
    v-model="visible"
    title="考勤详情"
    width="600px"
    @close="handleClose"
  >
    <div v-if="record" class="attendance-detail">
      <div class="detail-header">
        <el-avatar
          :src="record.memberAvatar"
          :size="60"
          :style="{ backgroundColor: getAvatarColor(record.memberName) }"
        >
          {{ record.memberName?.charAt(0) }}
        </el-avatar>
        <div class="member-info">
          <h3>{{ record.memberName }}</h3>
          <p>{{ record.employeeId }} | {{ record.department }}</p>
        </div>
        <el-tag
          :type="getStatusTagType(record.status) as any"
          :color="(ATTENDANCE_STATUS_CONFIG as any)[record.status || '']?.color"
          effect="light"
          size="large"
        >
          {{ (ATTENDANCE_STATUS_CONFIG as any)[record.status || '']?.label }}
        </el-tag>
      </div>

      <el-descriptions :column="2" border>
        <el-descriptions-item label="日期">
          {{ formatDateShort(record.date) }} {{ getWeekday(record.date) }}
        </el-descriptions-item>
        <el-descriptions-item label="工作时长">
          {{ record.workHours }}小时
        </el-descriptions-item>
        <el-descriptions-item label="签到时间">
          <span
            v-if="record.checkInTime"
            :class="{ 'late-time': record.lateMinutes > 0 }"
          >
            {{ formatTime(record.checkInTime) }}
          </span>
          <span v-else class="no-record">未签到</span>
        </el-descriptions-item>
        <el-descriptions-item label="签退时间">
          <span
            v-if="record.checkOutTime"
            :class="{ 'early-time': record.earlyLeaveMinutes > 0 }"
          >
            {{ formatTime(record.checkOutTime) }}
          </span>
          <span v-else class="no-record">未签退</span>
        </el-descriptions-item>
        <el-descriptions-item label="迟到">
          <el-tag v-if="record.lateMinutes > 0" type="warning" size="small">
            {{ record.lateMinutes }}分钟
          </el-tag>
          <span v-else class="normal-text">无</span>
        </el-descriptions-item>
        <el-descriptions-item label="早退">
          <el-tag
            v-if="record.earlyLeaveMinutes > 0"
            type="danger"
            size="small"
          >
            {{ record.earlyLeaveMinutes }}分钟
          </el-tag>
          <span v-else class="normal-text">无</span>
        </el-descriptions-item>
        <el-descriptions-item label="加班">
          <el-tag v-if="record.overtimeHours > 0" type="info" size="small">
            {{ record.overtimeHours }}小时
          </el-tag>
          <span v-else class="normal-text">无</span>
        </el-descriptions-item>
        <el-descriptions-item label="位置">
          {{ record.location || '--' }}
        </el-descriptions-item>
        <el-descriptions-item label="IP地址" :span="2">
          {{ record.ip || '--' }}
        </el-descriptions-item>
        <el-descriptions-item label="设备信息" :span="2">
          {{ record.device || '--' }}
        </el-descriptions-item>
        <el-descriptions-item label="备注" :span="2">
          <div v-if="record.remark" class="remark-text">
            {{ record.remark }}
          </div>
          <span v-else class="no-record">无</span>
        </el-descriptions-item>
      </el-descriptions>

      <div class="detail-footer">
        <div class="time-info">
          <span>创建时间：{{ formatDate(record.createdAt) }}</span>
          <span>更新时间：{{ formatDate(record.updatedAt) }}</span>
        </div>
      </div>
    </div>

    <div v-else class="no-data">
      <el-empty description="暂无考勤数据" />
    </div>

    <template #footer>
      <div class="dialog-footer">
        <el-button @click="handleClose">关闭</el-button>
        <el-button v-if="record" type="primary" @click="handleEdit">
          修正记录
        </el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { ATTENDANCE_STATUS_CONFIG } from '@/types/attendance'
import type { AttendanceRecord } from '@/types/attendance'
import { formatDate, formatDateShort, formatTime } from '@/utils/date'

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
}>()

// 计算属性
const visible = computed({
  get: () => props.modelValue,
  set: value => emit('update:modelValue', value)
})

// 方法
const handleClose = () => {
  emit('update:modelValue', false)
}

const handleEdit = () => {
  if (props.record) {
    emit('edit', props.record)
  }
}

// 工具方法
const getAvatarColor = (name: string) => {
  const colors = ['#409EFF', '#67C23A', '#E6A23C', '#F56C6C', '#909399']
  const hash =
    name?.split('').reduce((acc, char) => acc + char.charCodeAt(0), 0) || 0
  return colors[hash % colors.length]
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

const getWeekday = (date: string) => {
  const weekdays = ['周日', '周一', '周二', '周三', '周四', '周五', '周六']
  return weekdays[new Date(date).getDay()]
}
</script>

<style scoped lang="scss">
@use '@/styles/variables.scss' as *;
@use '@/styles/mixins.scss' as *;

.attendance-detail {
  .detail-header {
    @include flex-start;
    gap: 16px;
    margin-bottom: 24px;
    padding: 20px;
    background: linear-gradient(135deg, #f0f9ff, #ecf5ff);
    border-radius: 12px;

    .member-info {
      flex: 1;

      h3 {
        font-size: 18px;
        font-weight: 600;
        color: $text-color-primary;
        margin: 0 0 8px 0;
      }

      p {
        color: $text-color-regular;
        margin: 0;
        font-size: 14px;
      }
    }
  }

  .late-time {
    color: $warning-color;
    font-weight: 500;
  }

  .early-time {
    color: $danger-color;
    font-weight: 500;
  }

  .no-record {
    color: $text-color-placeholder;
    font-style: italic;
  }

  .normal-text {
    color: $text-color-regular;
  }

  .remark-text {
    line-height: 1.6;
    color: $text-color-primary;
    white-space: pre-wrap;
  }

  .detail-footer {
    margin-top: 24px;
    padding-top: 16px;
    border-top: 1px solid $border-color-lighter;

    .time-info {
      display: flex;
      justify-content: space-between;
      font-size: 12px;
      color: $text-color-secondary;
    }
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
  .attendance-detail {
    .detail-header {
      flex-direction: column;
      text-align: center;
      gap: 12px;
    }

    .detail-footer {
      .time-info {
        flex-direction: column;
        gap: 4px;
        text-align: center;
      }
    }
  }
}
</style>
