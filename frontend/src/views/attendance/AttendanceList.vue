<template>
  <div class="attendance-list">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-left">
        <h1 class="page-title">工时管理</h1>
        <p class="page-description">
          查看基于任务完成的工时统计、月度汇总和数据导出
        </p>
      </div>
      <div class="header-actions">
        <el-button :icon="Download" @click="handleExport" type="primary">
          导出工时数据
        </el-button>
      </div>
    </div>

    <!-- 今日工时概览 -->
    <div class="today-overview">
      <el-card class="overview-card">
        <template #header>
          <div class="card-header">
            <span>今日工时概览</span>
            <div class="header-actions">
              <span class="current-time">{{ currentTime }}</span>
              <el-button type="primary" link @click="refreshTodayData">
                <el-icon><Refresh /></el-icon>
                刷新
              </el-button>
            </div>
          </div>
        </template>

        <div class="overview-content">
          <div class="stats-cards">
            <div class="stat-card total">
              <div class="stat-icon">
                <el-icon><User /></el-icon>
              </div>
              <div class="stat-content">
                <div class="stat-number">{{ todaySummary.totalMembers }}</div>
                <div class="stat-label">总员工数</div>
              </div>
            </div>

            <div class="stat-card present">
              <div class="stat-icon">
                <el-icon><CircleCheck /></el-icon>
              </div>
              <div class="stat-content">
                <div class="stat-number">{{ todaySummary.presentMembers }}</div>
                <div class="stat-label">已签到</div>
              </div>
            </div>

            <div class="stat-card absent">
              <div class="stat-icon">
                <el-icon><Close /></el-icon>
              </div>
              <div class="stat-content">
                <div class="stat-number">{{ todaySummary.absentMembers }}</div>
                <div class="stat-label">未签到</div>
              </div>
            </div>

            <div class="stat-card late">
              <div class="stat-icon">
                <el-icon><Clock /></el-icon>
              </div>
              <div class="stat-content">
                <div class="stat-number">{{ todaySummary.lateMembers }}</div>
                <div class="stat-label">迟到</div>
              </div>
            </div>

            <div class="stat-card leave">
              <div class="stat-icon">
                <el-icon><Document /></el-icon>
              </div>
              <div class="stat-content">
                <div class="stat-number">{{ todaySummary.leaveMembers }}</div>
                <div class="stat-label">请假</div>
              </div>
            </div>

            <div class="stat-card rate">
              <div class="stat-icon">
                <el-icon><TrendCharts /></el-icon>
              </div>
              <div class="stat-content">
                <div class="stat-number">
                  {{ todaySummary.attendanceRate?.toFixed(1) || 0 }}%
                </div>
                <div class="stat-label">出勤率</div>
              </div>
            </div>
          </div>

          <!-- 快速操作 -->
          <div class="quick-actions">
            <div class="personal-status">
              <el-avatar
                :src="userInfo?.avatar"
                :size="40"
                :style="{
                  backgroundColor: getAvatarColor(
                    (userInfo as any)?.full_name || ''
                  )
                }"
              >
                {{ ((userInfo as any)?.full_name || '').charAt(0) }}
              </el-avatar>
              <div class="status-info">
                <div class="user-name">
                  {{ (userInfo as any)?.full_name || '' }}
                </div>
                <div class="status-text">
                  <template v-if="todayStatus.record">
                    <span
                      v-if="
                        todayStatus.record.checkInTime &&
                        !todayStatus.record.checkOutTime
                      "
                    >
                      已签到 {{ formatTime(todayStatus.record.checkInTime) }}
                    </span>
                    <span
                      v-else-if="
                        todayStatus.record.checkInTime &&
                        todayStatus.record.checkOutTime
                      "
                    >
                      已签退 {{ formatTime(todayStatus.record.checkOutTime) }}
                    </span>
                  </template>
                  <span v-else>未签到</span>
                </div>
              </div>
            </div>

            <div class="action-buttons">
              <el-button
                v-if="todayStatus.canCheckIn"
                type="primary"
                size="default"
                :loading="checkingIn"
                @click="handleCheckIn"
              >
                <el-icon><CircleCheck /></el-icon>
                签到
              </el-button>

              <el-button
                v-if="todayStatus.canCheckOut"
                type="success"
                size="default"
                :loading="checkingOut"
                @click="handleCheckOut"
              >
                <el-icon><CircleClose /></el-icon>
                签退
              </el-button>

              <el-tag
                v-if="!todayStatus.canCheckIn && !todayStatus.canCheckOut"
                size="default"
                type="success"
              >
                今日考勤已完成
              </el-tag>
            </div>
          </div>
        </div>
      </el-card>
    </div>

    <!-- 过滤器和搜索 -->
    <div class="filters-section">
      <el-card class="filter-card">
        <div class="filters-row">
          <div class="filter-item">
            <label>日期范围：</label>
            <el-date-picker
              v-model="dateRange"
              type="daterange"
              range-separator="至"
              start-placeholder="开始日期"
              end-placeholder="结束日期"
              format="YYYY-MM-DD"
              value-format="YYYY-MM-DD"
              @change="handleFilterChange"
              style="width: 300px"
            />
          </div>

          <div class="filter-item">
            <label>成员搜索：</label>
            <el-input
              v-model="filters.search"
              placeholder="姓名或员工号"
              :prefix-icon="Search"
              clearable
              @input="handleFilterChange"
              style="width: 200px"
            />
          </div>

          <div class="filter-item">
            <label>部门：</label>
            <el-select
              v-model="filters.department"
              multiple
              placeholder="选择部门"
              clearable
              @change="handleFilterChange"
              style="width: 200px"
            >
              <el-option
                v-for="dept in departmentOptions"
                :key="dept.value"
                :label="dept.label"
                :value="dept.value"
              />
            </el-select>
          </div>

          <div class="filter-item">
            <label>状态：</label>
            <el-select
              v-model="filters.status"
              multiple
              placeholder="选择状态"
              clearable
              @change="handleFilterChange"
              style="width: 200px"
            >
              <el-option
                v-for="(config, status) in ATTENDANCE_STATUS_CONFIG"
                :key="status"
                :label="config.label"
                :value="status"
              />
            </el-select>
          </div>

          <div class="filter-actions">
            <el-button @click="resetFilters" :icon="Refresh">重置</el-button>
          </div>
        </div>
      </el-card>
    </div>

    <!-- 工时记录列表 -->
    <el-card class="table-card">
      <div class="table-header">
        <div class="table-title">工时记录</div>
        <div class="table-actions">
          <el-button-group>
            <el-button
              :type="viewMode === 'table' ? 'primary' : ''"
              :icon="Grid"
              @click="viewMode = 'table'"
            >
              表格视图
            </el-button>
            <el-button
              :type="viewMode === 'calendar' ? 'primary' : ''"
              :icon="Calendar"
              @click="viewMode = 'calendar'"
            >
              日历视图
            </el-button>
          </el-button-group>
        </div>
      </div>

      <!-- 表格视图 -->
      <el-table
        v-if="viewMode === 'table'"
        v-loading="loading"
        :data="attendanceList"
        @sort-change="handleSortChange"
        stripe
        style="width: 100%"
      >
        <el-table-column prop="memberAvatar" label="头像" width="80">
          <template #default="{ row }">
            <el-avatar
              :src="row.memberAvatar"
              :size="40"
              :style="{ backgroundColor: getAvatarColor(row.memberName) }"
            >
              {{ row.memberName?.charAt(0) }}
            </el-avatar>
          </template>
        </el-table-column>

        <el-table-column
          prop="memberName"
          label="姓名"
          min-width="120"
          sortable="custom"
        >
          <template #default="{ row }">
            <div class="member-info">
              <div class="name">{{ row.memberName }}</div>
              <div class="employee-id">{{ row.employeeId }}</div>
            </div>
          </template>
        </el-table-column>

        <el-table-column prop="department" label="部门" width="120" />

        <el-table-column prop="date" label="日期" width="120" sortable="custom">
          <template #default="{ row }">
            <div class="date-info">
              <div>{{ formatDateShort(row.date) }}</div>
              <div class="weekday">{{ getWeekday(row.date) }}</div>
            </div>
          </template>
        </el-table-column>

        <el-table-column label="签到时间" width="100">
          <template #default="{ row }">
            <span
              v-if="row.checkInTime"
              :class="{ 'late-time': row.lateMinutes > 0 }"
            >
              {{ formatTime(row.checkInTime) }}
            </span>
            <span v-else class="no-record">--</span>
          </template>
        </el-table-column>

        <el-table-column label="签退时间" width="100">
          <template #default="{ row }">
            <span
              v-if="row.checkOutTime"
              :class="{ 'early-time': row.earlyLeaveMinutes > 0 }"
            >
              {{ formatTime(row.checkOutTime) }}
            </span>
            <span v-else class="no-record">--</span>
          </template>
        </el-table-column>

        <el-table-column
          prop="workHours"
          label="工时"
          width="80"
          sortable="custom"
        >
          <template #default="{ row }">
            <span class="work-hours">{{ row.workHours }}h</span>
          </template>
        </el-table-column>

        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag
              :type="getStatusTagType(row.status) as any"
              :color="(ATTENDANCE_STATUS_CONFIG as any)[row.status]?.color"
              effect="light"
            >
              {{ (ATTENDANCE_STATUS_CONFIG as any)[row.status]?.label }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column label="异常信息" min-width="150">
          <template #default="{ row }">
            <div class="anomaly-info">
              <el-tag
                v-if="row.lateMinutes > 0"
                type="warning"
                size="small"
                style="margin-right: 4px"
              >
                迟到{{ row.lateMinutes }}分钟
              </el-tag>
              <el-tag
                v-if="row.earlyLeaveMinutes > 0"
                type="danger"
                size="small"
                style="margin-right: 4px"
              >
                早退{{ row.earlyLeaveMinutes }}分钟
              </el-tag>
              <el-tag v-if="row.overtimeHours > 0" type="info" size="small">
                加班{{ row.overtimeHours }}小时
              </el-tag>
            </div>
          </template>
        </el-table-column>

        <el-table-column label="操作" width="150" fixed="right">
          <template #default="{ row }">
            <div class="action-buttons">
              <el-button
                size="small"
                type="primary"
                link
                @click="handleView(row)"
              >
                查看
              </el-button>
              <el-dropdown @command="cmd => handleAction(cmd, row)">
                <el-button size="small" type="primary" link>
                  更多<el-icon class="el-icon--right"><ArrowDown /></el-icon>
                </el-button>
                <template #dropdown>
                  <el-dropdown-menu>
                    <el-dropdown-item command="correct" :icon="Edit">
                      修正记录
                    </el-dropdown-item>
                    <el-dropdown-item command="delete" :icon="Delete" divided>
                      删除记录
                    </el-dropdown-item>
                  </el-dropdown-menu>
                </template>
              </el-dropdown>
            </div>
          </template>
        </el-table-column>
      </el-table>

      <!-- 日历视图 -->
      <div v-if="viewMode === 'calendar'" class="calendar-view">
        <AttendanceCalendar
          :attendance-data="attendanceList"
          :loading="loading"
          @date-click="handleDateClick"
        />
      </div>

      <!-- 分页 -->
      <div class="pagination-wrapper">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.pageSize"
          :total="pagination.total"
          :page-sizes="[10, 20, 50, 100]"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handlePageSizeChange"
          @current-change="handlePageChange"
        />
      </div>
    </el-card>

    <!-- 对话框 -->
    <AttendanceDetailDialog
      v-model="showDetailDialog"
      :record="currentRecord"
    />

    <LeaveApplicationDialog
      v-model="showLeaveDialog"
      @success="handleLeaveSuccess"
    />

    <OvertimeApplicationDialog
      v-model="showOvertimeDialog"
      @success="handleOvertimeSuccess"
    />

    <CheckInDialog
      v-model="showCheckInDialog"
      @success="handleCheckInSuccess"
    />

    <CheckOutDialog
      v-model="showCheckOutDialog"
      @success="handleCheckOutSuccess"
    />

    <AttendanceCorrectionDialog
      v-model="showCorrectionDialog"
      :record="currentRecord"
      @success="handleCorrectionSuccess"
    />
  </div>
</template>

///
<reference types="node" />
<script setup lang="ts">
import { ref, reactive, computed, onMounted, onUnmounted, nextTick } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Download,
  Refresh,
  User,
  CircleCheck,
  Close,
  Clock,
  Document,
  TrendCharts,
  Search,
  Grid,
  Calendar,
  ArrowDown,
  Edit,
  Delete,
  CircleClose
} from '@element-plus/icons-vue'
import { attendanceApi } from '@/api/attendance'
import { useAuthStore } from '@/stores/auth'
import {
  ATTENDANCE_STATUS_CONFIG,
  DEPARTMENT_OPTIONS
} from '@/types/attendance'
import type {
  AttendanceRecord,
  AttendanceListParams,
  AttendanceFilters,
  AttendanceSummary
} from '@/types/attendance'
import { formatDateShort, formatTime } from '@/utils/date'
import AttendanceDetailDialog from '@/components/attendance/AttendanceDetailDialog.vue'
import AttendanceCalendar from '@/components/attendance/AttendanceCalendar.vue'
import LeaveApplicationDialog from '@/components/attendance/LeaveApplicationDialog.vue'
import OvertimeApplicationDialog from '@/components/attendance/OvertimeApplicationDialog.vue'
import CheckInDialog from '@/components/attendance/CheckInDialog.vue'
import CheckOutDialog from '@/components/attendance/CheckOutDialog.vue'
import AttendanceCorrectionDialog from '@/components/attendance/AttendanceCorrectionDialog.vue'

// 响应式数据
const authStore = useAuthStore()
const userInfo = computed(() => authStore.userInfo)

const loading = ref(false)
const checkingIn = ref(false)
const checkingOut = ref(false)
const attendanceList = ref<AttendanceRecord[]>([])
const viewMode = ref<'table' | 'calendar'>('table')
const currentTime = ref('')
const currentRecord = ref<AttendanceRecord | null>(null)

// 分页数据
const pagination = reactive({
  page: 1,
  pageSize: 20,
  total: 0
})

// 今日概览数据
const todaySummary = reactive<AttendanceSummary>({
  date: '',
  totalMembers: 0,
  presentMembers: 0,
  absentMembers: 0,
  lateMembers: 0,
  leaveMembers: 0,
  attendanceRate: 0,
  records: [],
  // Add missing properties from WorkHoursSummary
  total_members: 0,
  active_members: 0,
  total_hours: 0,
  repair_hours: 0,
  monitoring_hours: 0,
  assistance_hours: 0,
  average_hours: 0,
  participation_rate: 0
})

// 今日状态
const todayStatus = reactive<{
  record: AttendanceRecord | null
  canCheckIn: boolean
  canCheckOut: boolean
}>({
  record: null,
  canCheckIn: true,
  canCheckOut: false
})

// 过滤器
const dateRange = ref<[string, string]>([
  new Date().toISOString().split('T')[0],
  new Date().toISOString().split('T')[0]
])

const filters = reactive<AttendanceFilters>({
  department: [],
  status: [],
  search: ''
})

// 对话框状态
const showDetailDialog = ref(false)
const showLeaveDialog = ref(false)
const showOvertimeDialog = ref(false)
const showCheckInDialog = ref(false)
const showCheckOutDialog = ref(false)
const showCorrectionDialog = ref(false)

const departmentOptions = ref(DEPARTMENT_OPTIONS)

// 定时器
let timeTimer: NodeJS.Timeout | null = null

// 方法
const updateCurrentTime = () => {
  currentTime.value = new Date().toLocaleTimeString('zh-CN', {
    hour12: false,
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  })
}

const loadAttendanceRecords = async () => {
  try {
    loading.value = true
    const params: AttendanceListParams = {
      page: pagination.page,
      pageSize: pagination.pageSize,
      filters: {
        ...filters,
        dateRange: dateRange.value,
        department: filters.department?.length ? filters.department : undefined,
        status: filters.status?.length ? filters.status : undefined,
        search: filters.search || undefined
      }
    }

    const records = await attendanceApi.getWorkHoursRecords(params)
    attendanceList.value = records as any // Type compatibility between WorkHoursRecord[] and AttendanceRecord[]
    pagination.total = records.length
  } catch (error) {
    console.error('加载工时记录失败:', error)
    ElMessage.error('加载工时记录失败')
  } finally {
    loading.value = false
  }
}

const loadTodayData = async () => {
  try {
    const summary = await attendanceApi.getTodayWorkHoursSummary()

    Object.assign(todaySummary, (summary as any).data || summary)
  } catch (error) {
    console.error('加载今日数据失败:', error)
    ElMessage.error('加载今日数据失败')
  }
}

const refreshTodayData = () => {
  loadTodayData()
}

const handleCheckIn = () => {
  showCheckInDialog.value = true
}

const handleCheckOut = () => {
  showCheckOutDialog.value = true
}

const handleCheckInSuccess = () => {
  loadTodayData()
  loadAttendanceRecords()
}

const handleCheckOutSuccess = () => {
  loadTodayData()
  loadAttendanceRecords()
}

const handleView = (record: AttendanceRecord) => {
  currentRecord.value = record
  showDetailDialog.value = true
}

const handleAction = async (command: string, record: AttendanceRecord) => {
  currentRecord.value = record

  switch (command) {
    case 'correct':
      showCorrectionDialog.value = true
      break
    case 'delete':
      await handleDelete(record)
      break
  }
}

const handleDelete = async (record: AttendanceRecord) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除 ${record.memberName || record.member_name} 在 ${formatDateShort(record.work_date)} 的工时记录吗？`,
      '删除工时记录',
      { type: 'warning' }
    )

    // 工时记录不支持删除，因为它们基于任务完成情况
    ElMessage.info('工时记录基于任务完成情况生成，不支持直接删除')
    await loadAttendanceRecords()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除失败:', error)
      ElMessage.error('删除失败')
    }
  }
}

const handleExport = async () => {
  try {
    loading.value = true
    const result = await attendanceApi.exportWorkHoursData({
      date_from: dateRange.value[0],
      date_to: dateRange.value[1],
      format: 'excel'
    })

    if (result.success) {
      ElMessage.success(
        `工时数据导出成功，共 ${(result as any).total_records || result.total || 0} 条记录`
      )
      // 如果有下载链接，可以引导用户下载
      if (result.download_url) {
        ElMessage.info('文件已生成，请联系管理员获取下载链接')
      }
    } else {
      ElMessage.warning(result.message || '导出失败')
    }
  } catch (error) {
    console.error('导出失败:', error)
    ElMessage.error('导出失败')
  } finally {
    loading.value = false
  }
}

const handleFilterChange = () => {
  pagination.page = 1
  nextTick(() => {
    loadAttendanceRecords()
  })
}

const resetFilters = () => {
  dateRange.value = [
    new Date().toISOString().split('T')[0],
    new Date().toISOString().split('T')[0]
  ]
  filters.department = []
  filters.status = []
  filters.search = ''
  handleFilterChange()
}

const handleSortChange = (sort: any) => {
  // TODO: 实现排序逻辑
  console.log('排序变更:', sort)
}

const handlePageChange = (page: number) => {
  pagination.page = page
  loadAttendanceRecords()
}

const handlePageSizeChange = (pageSize: number) => {
  pagination.pageSize = pageSize
  pagination.page = 1
  loadAttendanceRecords()
}

const handleDateClick = (date: string) => {
  // 日历日期点击处理
  console.log('日期点击:', date)
}

const handleLeaveSuccess = () => {
  ElMessage.success('请假申请提交成功')
}

const handleOvertimeSuccess = () => {
  ElMessage.success('加班申请提交成功')
}

const handleCorrectionSuccess = () => {
  loadAttendanceRecords()
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

// 生命周期
onMounted(() => {
  updateCurrentTime()
  timeTimer = setInterval(updateCurrentTime, 1000)

  loadTodayData()
  loadAttendanceRecords()
})

onUnmounted(() => {
  if (timeTimer) {
    clearInterval(timeTimer)
  }
})
</script>

<style scoped lang="scss">
@use '@/styles/variables.scss' as *;
@use '@/styles/mixins.scss' as *;

.attendance-list {
  padding: 24px;

  .page-header {
    @include flex-between;
    margin-bottom: 24px;

    .header-left {
      .page-title {
        font-size: $font-size-title;
        font-weight: 600;
        margin: 0 0 8px 0;
        color: $text-color-primary;
      }

      .page-description {
        color: $text-color-regular;
        margin: 0;
      }
    }

    .header-actions {
      display: flex;
      gap: 12px;
    }
  }

  .today-overview {
    margin-bottom: 24px;

    .overview-card {
      .card-header {
        @include flex-between;
        align-items: center;

        .header-actions {
          @include flex-center;
          gap: 16px;

          .current-time {
            font-family: 'Courier New', monospace;
            font-size: 16px;
            font-weight: 600;
            color: $primary-color;
          }
        }
      }

      .overview-content {
        .stats-cards {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
          gap: 16px;
          margin-bottom: 24px;

          .stat-card {
            @include flex-start;
            padding: 16px;
            border-radius: 8px;
            gap: 12px;
            transition: all 0.3s ease;

            &:hover {
              transform: translateY(-2px);
            }

            .stat-icon {
              width: 40px;
              height: 40px;
              border-radius: 8px;
              @include flex-center;
              color: white;
            }

            .stat-content {
              .stat-number {
                font-size: 20px;
                font-weight: 600;
                color: $text-color-primary;
                margin-bottom: 2px;
              }

              .stat-label {
                color: $text-color-regular;
                font-size: 12px;
              }
            }

            &.total .stat-icon {
              background: $primary-color;
            }
            &.present .stat-icon {
              background: $success-color;
            }
            &.absent .stat-icon {
              background: $info-color;
            }
            &.late .stat-icon {
              background: $warning-color;
            }
            &.leave .stat-icon {
              background: $primary-color;
            }
            &.rate .stat-icon {
              background: linear-gradient(135deg, $primary-color, #409eff);
            }
          }
        }

        .quick-actions {
          @include flex-between;
          align-items: center;
          padding: 20px;
          background: linear-gradient(135deg, #f0f9ff, #ecf5ff);
          border-radius: 12px;
          border: 1px solid $border-color-lighter;

          .personal-status {
            @include flex-start;
            gap: 16px;

            .status-info {
              .user-name {
                font-size: 16px;
                font-weight: 500;
                color: $text-color-primary;
                margin-bottom: 4px;
              }

              .status-text {
                color: $text-color-regular;
                font-size: 14px;
              }
            }
          }

          .action-buttons {
            display: flex;
            gap: 12px;
          }
        }
      }
    }
  }

  .filters-section {
    margin-bottom: 16px;

    .filter-card {
      .filters-row {
        display: flex;
        align-items: center;
        gap: 24px;
        flex-wrap: wrap;

        .filter-item {
          display: flex;
          align-items: center;
          gap: 8px;

          label {
            font-size: 14px;
            color: $text-color-regular;
            white-space: nowrap;
          }
        }

        .filter-actions {
          margin-left: auto;
        }
      }
    }
  }

  .table-card {
    .table-header {
      @include flex-between;
      margin-bottom: 16px;

      .table-title {
        font-size: 16px;
        font-weight: 600;
        color: $text-color-primary;
      }
    }

    .member-info {
      .name {
        font-weight: 500;
        color: $text-color-primary;
      }

      .employee-id {
        font-size: 12px;
        color: $text-color-secondary;
        margin-top: 2px;
      }
    }

    .date-info {
      .weekday {
        font-size: 12px;
        color: $text-color-secondary;
        margin-top: 2px;
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
    }

    .work-hours {
      font-weight: 500;
      color: $primary-color;
    }

    .anomaly-info {
      display: flex;
      flex-wrap: wrap;
      gap: 4px;
    }

    .action-buttons {
      display: flex;
      gap: 8px;
    }
  }

  .calendar-view {
    min-height: 500px;
  }

  .pagination-wrapper {
    margin-top: 24px;
    text-align: right;
  }

  @include respond-to(sm) {
    padding: 16px;

    .today-overview {
      .overview-content {
        .stats-cards {
          grid-template-columns: repeat(2, 1fr);
        }

        .quick-actions {
          flex-direction: column;
          gap: 16px;
          text-align: center;
        }
      }
    }

    .filters-section {
      .filter-card {
        .filters-row {
          flex-direction: column;
          align-items: stretch;
          gap: 16px;

          .filter-item {
            flex-direction: column;
            align-items: flex-start;
            gap: 8px;
          }

          .filter-actions {
            margin-left: 0;
          }
        }
      }
    }
  }
}
</style>
