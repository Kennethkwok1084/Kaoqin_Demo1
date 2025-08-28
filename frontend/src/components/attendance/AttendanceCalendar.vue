<template>
  <div class="attendance-calendar">
    <el-calendar v-model="selectedDate" @panel-change="handlePanelChange">
      <template #date-cell="{ data }">
        <div class="calendar-cell" @click="handleDateClick(data.day)">
          <div class="date-number">{{ data.day.split('-').pop() }}</div>
          <div v-if="getDateAttendance(data.day)" class="attendance-status">
            <el-tag
              :type="getStatusTagType(getDateAttendance(data.day)?.status) as any"
              size="small"
              effect="plain"
            >
              {{
                (ATTENDANCE_STATUS_CONFIG as any)[getDateAttendance(data.day)?.status || '']
                  ?.label
              }}
            </el-tag>
          </div>
        </div>
      </template>
    </el-calendar>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { ATTENDANCE_STATUS_CONFIG } from '@/types/attendance'
import type { AttendanceRecord } from '@/types/attendance'

// Props
interface Props {
  attendanceData: AttendanceRecord[]
  loading?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  loading: false
})

// Emits
const emit = defineEmits<{
  'date-click': [date: string]
  'panel-change': [date: Date]
}>()

// 响应式数据
const selectedDate = ref(new Date())

// 计算属性
const attendanceMap = computed(() => {
  const map = new Map<string, AttendanceRecord>()
  props.attendanceData.forEach(record => {
    map.set(record.date, record)
  })
  return map
})

// 方法
const getDateAttendance = (date: string) => {
  return attendanceMap.value.get(date)
}

const getStatusTagType = (status?: string) => {
  const config = {
    normal: 'success',
    late: 'warning',
    early_leave: 'danger',
    absent: 'info',
    leave: 'primary',
    overtime: ''
  }
  return status ? config[status as keyof typeof config] || 'info' : 'info'
}

const handleDateClick = (date: string) => {
  emit('date-click', date)
}

const handlePanelChange = (date: Date) => {
  emit('panel-change', date)
}
</script>

<style scoped lang="scss">
@use '@/styles/variables.scss' as *;
@use '@/styles/mixins.scss' as *;

.attendance-calendar {
  .calendar-cell {
    height: 100%;
    min-height: 80px;
    padding: 4px;
    cursor: pointer;
    transition: background-color 0.3s ease;

    &:hover {
      background-color: $background-color-page;
    }

    .date-number {
      font-size: 16px;
      font-weight: 500;
      color: $text-color-primary;
    }

    .attendance-status {
      margin-top: 4px;
    }
  }

  :deep(.el-calendar-table) {
    .el-calendar-day {
      height: 100px;
      padding: 0;
    }
  }
}
</style>
