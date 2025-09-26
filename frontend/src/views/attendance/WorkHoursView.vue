<template>
  <div class="attendance-view">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-left">
        <h1 class="page-title">考勤管理（任务口径）</h1>
        <p class="page-description">按周期汇总所有成员基于任务的工时（报修/监控/协助）</p>
      </div>
      <div class="header-actions">
        <el-button :icon="Download" @click="handleExport" type="primary">
          导出考勤数据
        </el-button>
      </div>
    </div>

    <!-- 错误提示区域 -->
    <div v-if="apiError" class="error-section">
      <el-alert
        type="error"
        title="数据加载失败"
        :description="apiError"
        show-icon
        :closable="true"
        @close="clearError"
      >
        <template #action>
          <el-button type="primary" size="small" @click="retryLoadData">
            重试
          </el-button>
        </template>
      </el-alert>
    </div>

    <!-- 考勤周期选择和总览 -->
    <div class="period-overview">
      <el-card class="overview-card">
        <template #header>
          <div class="card-header">
            <span>考勤统计总览</span>
            <div class="header-actions">
              <el-select v-model="cycleType" style="width: 140px; margin-right: 12px" @change="loadAttendanceData">
                <el-option label="按月" value="monthly" />
                <el-option label="按周" value="weekly" />
                <el-option label="自定义" value="custom" />
              </el-select>

              <el-date-picker
                v-if="cycleType==='monthly'"
                v-model="selectedMonth"
                type="month"
                placeholder="选择月份"
                value-format="YYYY-MM"
                @change="loadAttendanceData"
                style="width: 200px; margin-right: 16px;"
              />
              <el-date-picker
                v-else-if="cycleType==='weekly'"
                v-model="weekStart"
                type="date"
                placeholder="周开始日期"
                value-format="YYYY-MM-DD"
                @change="loadAttendanceData"
                style="width: 200px; margin-right: 16px;"
              />
              <el-date-picker
                v-else
                v-model="customRange"
                type="daterange"
                range-separator="至"
                start-placeholder="开始日期"
                end-placeholder="结束日期"
                value-format="YYYY-MM-DD"
                @change="loadAttendanceData"
                style="width: 340px; margin-right: 16px;"
              />
              <el-button type="primary" link @click="refreshData">
                <el-icon><Refresh /></el-icon>
                刷新
              </el-button>
            </div>
          </div>
        </template>

        <div class="overview-content">
          <div class="stats-grid">
            <div class="stat-card total-members">
              <div class="stat-icon">
                <el-icon><User /></el-icon>
              </div>
              <div class="stat-content">
                <div class="stat-number">{{ attendanceOverview.total_members }}</div>
                <div class="stat-label">参与成员</div>
              </div>
            </div>

            <div class="stat-card total-hours">
              <div class="stat-icon">
                <el-icon><Timer /></el-icon>
              </div>
              <div class="stat-content">
                <div class="stat-number">{{ attendanceOverview.total_hours.toFixed(1) }}</div>
                <div class="stat-label">总工时</div>
              </div>
            </div>

            <div class="stat-card repair-hours">
              <div class="stat-icon">
                <el-icon><Tools /></el-icon>
              </div>
              <div class="stat-content">
                <div class="stat-number">{{ attendanceOverview.repair_hours.toFixed(1) }}</div>
                <div class="stat-label">维修工时</div>
              </div>
            </div>

            <div class="stat-card monitoring-hours">
              <div class="stat-icon">
                <el-icon><Monitor /></el-icon>
              </div>
              <div class="stat-content">
                <div class="stat-number">{{ attendanceOverview.monitoring_hours.toFixed(1) }}</div>
                <div class="stat-label">监控工时</div>
              </div>
            </div>

            <div class="stat-card assistance-hours">
              <div class="stat-icon">
                <el-icon><Star /></el-icon>
              </div>
              <div class="stat-content">
                <div class="stat-number">{{ attendanceOverview.assistance_hours.toFixed(1) }}</div>
                <div class="stat-label">协助工时</div>
              </div>
            </div>

            <div class="stat-card average-hours">
              <div class="stat-icon">
                <el-icon><TrendCharts /></el-icon>
              </div>
              <div class="stat-content">
                <div class="stat-number">{{ attendanceOverview.average_hours.toFixed(1) }}</div>
                <div class="stat-label">人均工时</div>
              </div>
            </div>
          </div>
        </div>
      </el-card>
    </div>

    <!-- 成员考勤列表 -->
    <el-card class="table-card">
      <div class="table-header">
        <div class="table-title">成员工时详情 - {{ periodText }}</div>
        <div class="table-actions">
          <el-button-group>
            <el-button
              :type="viewMode === 'table' ? 'primary' : ''"
              @click="viewMode = 'table'"
            >
              表格视图
            </el-button>
            <el-button
              :type="viewMode === 'chart' ? 'primary' : ''"
              @click="viewMode = 'chart'"
            >
              图表视图
            </el-button>
          </el-button-group>
        </div>
      </div>

      <!-- 筛选器 -->
      <div class="filters">
        <el-row :gutter="16">
          <el-col :span="6">
            <el-input
              v-model="filters.search"
              placeholder="搜索成员姓名"
              @change="filterAttendanceData"
              clearable
            >
              <template #prefix>
                <el-icon><Search /></el-icon>
              </template>
            </el-input>
          </el-col>
          <el-col :span="6">
            <el-select
              v-model="filters.group_id"
              placeholder="选择小组"
              clearable
              @change="filterAttendanceData"
            >
              <el-option label="全部小组" value="" />
              <el-option
                v-for="option in groupOptions"
                :key="option.value"
                :label="option.label"
                :value="option.value"
              />
            </el-select>
          </el-col>
          <el-col :span="6">
            <el-select
              v-model="filters.sort_by"
              placeholder="排序方式"
              @change="filterAttendanceData"
            >
              <el-option label="总工时降序" value="total_hours_desc" />
              <el-option label="总工时升序" value="total_hours_asc" />
              <el-option label="姓名升序" value="name_asc" />
              <el-option label="维修工时降序" value="repair_hours_desc" />
            </el-select>
          </el-col>
          <el-col :span="6">
            <el-select
              v-model="filters.performance_level"
              placeholder="绩效等级"
              clearable
              @change="filterAttendanceData"
            >
              <el-option label="优秀 (≥80h)" value="excellent" />
              <el-option label="良好 (60-80h)" value="good" />
              <el-option label="合格 (40-60h)" value="qualified" />
              <el-option label="待改进 (<40h)" value="needs_improvement" />
            </el-select>
          </el-col>
        </el-row>
      </div>

      <!-- 表格视图 -->
      <div v-if="viewMode === 'table'">
        <el-table
          :data="filteredAttendanceList"
          :loading="loading"
          stripe
          height="600"
          row-class-name="attendance-row"
        >
          <el-table-column prop="member_name" label="成员姓名" width="120" fixed="left">
            <template #default="{ row }">
              <div class="member-info">
                <el-avatar
                  :size="32"
                  :src="row.avatar"
                  style="margin-right: 8px;"
                >
                  {{ row.member_name.charAt(0) }}
                </el-avatar>
                <div>
                  <div class="member-name">{{ row.member_name }}</div>
                  <div class="member-group">{{ formatGroupLabel(row.group_id) }}</div>
                </div>
              </div>
            </template>
          </el-table-column>

          <el-table-column prop="total_hours" label="总工时" width="100" sortable>
            <template #default="{ row }">
              <span class="total-hours-number">{{ row.total_hours?.toFixed(1) || '0.0' }}h</span>
            </template>
          </el-table-column>

          <el-table-column prop="repair_task_hours" label="维修工时" width="100">
            <template #default="{ row }">
              <span class="repair-hours">{{ row.repair_task_hours?.toFixed(1) || '0.0' }}h</span>
            </template>
          </el-table-column>

          <el-table-column prop="monitoring_hours" label="监控工时" width="100">
            <template #default="{ row }">
              <span class="monitoring-hours">{{ row.monitoring_hours?.toFixed(1) || '0.0' }}h</span>
            </template>
          </el-table-column>

          <el-table-column prop="assistance_hours" label="协助工时" width="100">
            <template #default="{ row }">
              <span class="assistance-hours">{{ row.assistance_hours?.toFixed(1) || '0.0' }}h</span>
            </template>
          </el-table-column>

          

          <el-table-column label="绩效等级" width="120">
            <template #default="{ row }">
              <el-tag :type="getPerformanceTagType(row.total_hours || 0)">
                {{ getPerformanceLevel(row.total_hours || 0) }}
              </el-tag>
            </template>
          </el-table-column>

          <el-table-column label="工时分布" width="200">
            <template #default="{ row }">
              <div class="work-hours-chart">
                <el-tooltip content="维修工时" placement="top">
                  <div
                    class="chart-bar repair"
                    :style="{
                      width: `${getHoursPercentage(row.repair_task_hours || 0, row.total_hours || 1)}%`
                    }"
                  ></div>
                </el-tooltip>
                <el-tooltip content="监控工时" placement="top">
                  <div
                    class="chart-bar monitoring"
                    :style="{
                      width: `${getHoursPercentage(row.monitoring_hours || 0, row.total_hours || 1)}%`
                    }"
                  ></div>
                </el-tooltip>
                <el-tooltip content="协助工时" placement="top">
                  <div
                    class="chart-bar assistance"
                    :style="{
                      width: `${getHoursPercentage(row.assistance_hours || 0, row.total_hours || 1)}%`
                    }"
                  ></div>
                </el-tooltip>
              </div>
            </template>
          </el-table-column>

          <el-table-column prop="updated_at" label="更新时间" width="160">
            <template #default="{ row }">
              {{ formatDateTime(row.updated_at) }}
            </template>
          </el-table-column>

          <el-table-column label="操作" width="150" fixed="right">
            <template #default="{ row }">
              <el-button type="primary" link @click="viewMemberDetail(row)">
                <el-icon><View /></el-icon>
                详情
              </el-button>
              <el-button type="warning" link @click="adjustWorkHours(row)">
                <el-icon><Edit /></el-icon>
                调整
              </el-button>
            </template>
          </el-table-column>
        </el-table>

        <!-- 分页 -->
        <div class="pagination-wrapper">
          <el-pagination
            v-model:current-page="pagination.page"
            v-model:page-size="pagination.size"
            :total="pagination.total"
            :page-sizes="[10, 20, 50, 100]"
            layout="total, sizes, prev, pager, next, jumper"
            @current-change="handlePageChange"
            @size-change="handleSizeChange"
          />
        </div>
      </div>

      <!-- 图表视图 -->
      <div v-else-if="viewMode === 'chart'" class="chart-container">
        <div class="charts-grid">
          <div class="chart-item">
            <h3>工时分布统计</h3>
            <div id="hoursDistributionChart" style="height: 300px"></div>
          </div>
          <div class="chart-item">
            <h3>成员绩效分析</h3>
            <div id="performanceChart" style="height: 300px"></div>
          </div>
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import {
  Download,
  Refresh,
  Timer,
  User,
  Tools,
  Monitor,
  Star,
  TrendCharts,
  Search,
  View,
  Edit
} from '@element-plus/icons-vue'
import { attendanceApi } from '@/api/attendance'
import dayjs from 'dayjs'
import type { WorkHoursCycleRecord } from '@/types/attendance'

// 考勤记录类型定义
interface AttendanceRecord {
  id: number
  member_id: number
  member_name: string
  group_id?: number
  group_name?: string
  month: string
  repair_task_hours: number
  monitoring_hours: number
  assistance_hours: number
  carried_hours: number
  total_hours: number
  remaining_hours: number
  updated_at: string
  avatar?: string
}

interface AttendanceOverview {
  total_members: number
  total_hours: number
  repair_hours: number
  monitoring_hours: number
  assistance_hours: number
  average_hours: number
}

interface GroupOption {
  value: string
  label: string
}

const GROUP_UNASSIGNED_VALUE = '__NO_GROUP__'

// 响应式数据
const loading = ref(false)
const viewMode = ref('table')
const selectedMonth = ref('')
const cycleType = ref<'monthly' | 'weekly' | 'custom'>('monthly')
const weekStart = ref('')
const customRange = ref<[string, string] | null>(null)
const apiError = ref('')
const retryCount = ref(0)
const maxRetries = 3

// 考勤统计总览数据
const attendanceOverview = reactive<AttendanceOverview>({
  total_members: 0,
  total_hours: 0,
  repair_hours: 0,
  monitoring_hours: 0,
  assistance_hours: 0,
  average_hours: 0
})

// 考勤记录列表
const attendanceList = ref<AttendanceRecord[]>([])

const groupOptions = ref<GroupOption[]>([])

// 筛选条件
const filters = reactive({
  search: '',
  group_id: '',
  sort_by: 'total_hours_desc',
  performance_level: ''
})

const pagination = reactive({
  page: 1,
  size: 20,
  total: 0
})

// 计算属性：过滤后的考勤数据
const filteredAttendanceList = computed(() => {
  let filtered = [...attendanceList.value]

  // 搜索过滤
  if (filters.search) {
    filtered = filtered.filter(item =>
      item.member_name.toLowerCase().includes(filters.search.toLowerCase())
    )
  }

  // 小组过滤
  if (filters.group_id) {
    if (filters.group_id === GROUP_UNASSIGNED_VALUE) {
      filtered = filtered.filter(
        item => item.group_id === null || item.group_id === undefined
      )
    } else {
      filtered = filtered.filter(
        item => String(item.group_id ?? '') === filters.group_id
      )
    }
  }

  // 绩效等级过滤
  if (filters.performance_level) {
    filtered = filtered.filter(item => {
      const hours = item.total_hours || 0
      switch (filters.performance_level) {
        case 'excellent':
          return hours >= 80
        case 'good':
          return hours >= 60 && hours < 80
        case 'qualified':
          return hours >= 40 && hours < 60
        case 'needs_improvement':
          return hours < 40
        default:
          return true
      }
    })
  }

  // 排序
  filtered.sort((a, b) => {
    switch (filters.sort_by) {
      case 'total_hours_desc':
        return (b.total_hours || 0) - (a.total_hours || 0)
      case 'total_hours_asc':
        return (a.total_hours || 0) - (b.total_hours || 0)
      case 'name_asc':
        return a.member_name.localeCompare(b.member_name, 'zh')
      case 'repair_hours_desc':
        return (b.repair_task_hours || 0) - (a.repair_task_hours || 0)
      default:
        return 0
    }
  })

  // 更新分页总数
  pagination.total = filtered.length

  // 分页处理
  const start = (pagination.page - 1) * pagination.size
  const end = start + pagination.size
  return filtered.slice(start, end)
})

// 获取绩效等级
const getPerformanceLevel = (totalHours: number): string => {
  if (totalHours >= 80) return '优秀'
  if (totalHours >= 60) return '良好'
  if (totalHours >= 40) return '合格'
  return '待改进'
}

const formatGroupLabel = (groupId?: number | null): string => {
  if (groupId === null || groupId === undefined) {
    return '未分组'
  }
  return `第${groupId}组`
}

// 获取绩效标签类型
const getPerformanceTagType = (totalHours: number): 'success' | 'warning' | 'info' | 'danger' => {
  if (totalHours >= 80) return 'success'
  if (totalHours >= 60) return 'info'
  if (totalHours >= 40) return 'warning'
  return 'danger'
}

// 计算工时百分比
const getHoursPercentage = (hours: number, total: number): number => {
  if (total === 0) return 0
  return Math.round((hours / total) * 100)
}

// 格式化日期时间
const formatDateTime = (dateTime: string | Date) => {
  if (!dateTime) return '-'
  return new Date(dateTime).toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

const updateGroupOptions = (records: AttendanceRecord[]) => {
  const map = new Map<string, string>()
  records.forEach(record => {
    const gid = record.group_id ?? null
    const value = gid === null ? GROUP_UNASSIGNED_VALUE : String(gid)
    if (!map.has(value)) {
      const label = gid === null ? '未分组' : formatGroupLabel(gid)
      map.set(value, label)
    }
  })

  const entries = Array.from(map.entries()).sort((a, b) => {
    if (a[0] === GROUP_UNASSIGNED_VALUE) return 1
    if (b[0] === GROUP_UNASSIGNED_VALUE) return -1
    return Number(a[0]) - Number(b[0])
  })

  groupOptions.value = entries.map(([value, label]) => ({ value, label }))

  const availableValues = new Set(entries.map(([value]) => value))
  if (filters.group_id && !availableValues.has(filters.group_id)) {
    filters.group_id = ''
  }
}

// 加载考勤数据
const loadAttendanceData = async (isRetry = false) => {
  try {
    loading.value = true

    if (!isRetry) {
      apiError.value = ''
      retryCount.value = 0
    }

    const params: any = { page: pagination.page, size: pagination.size }
    if (cycleType.value === 'monthly') {
      params.cycle_type = 'monthly'
      params.month = selectedMonth.value || getCurrentMonth()
    } else if (cycleType.value === 'weekly') {
      params.cycle_type = 'weekly'
      params.week_start = weekStart.value || dayjs().format('YYYY-MM-DD')
    } else {
      params.cycle_type = 'custom'
      const [from, to] = customRange.value || [dayjs().startOf('month').format('YYYY-MM-DD'), dayjs().endOf('month').format('YYYY-MM-DD')]
      params.date_from = from
      params.date_to = to
    }

    const { data } = await attendanceApi.getCycleSummary(params)
    const recs = data.records || []
    attendanceOverview.total_members = data.total_members || 0
    attendanceOverview.total_hours = recs.reduce((s: number, r: any) => s + (r.total_work_hours || 0), 0)
    attendanceOverview.repair_hours = recs.reduce((s: number, r: any) => s + (r.repair_minutes || 0) / 60, 0)
    attendanceOverview.monitoring_hours = recs.reduce((s: number, r: any) => s + (r.monitoring_minutes || 0) / 60, 0)
    attendanceOverview.assistance_hours = recs.reduce((s: number, r: any) => s + (r.assistance_minutes || 0) / 60, 0)
    attendanceOverview.average_hours = attendanceOverview.total_members > 0 ? attendanceOverview.total_hours / attendanceOverview.total_members : 0

    const mappedRecords = recs.map((r: WorkHoursCycleRecord) => {
      const groupId = r.group_id ?? null
      return {
        id: r.member_id,
        member_id: r.member_id,
        member_name: r.member_name,
        group_id: groupId,
        group_name:
          r.group_name ?? (groupId === null ? '未分组' : formatGroupLabel(groupId)),
        month: '',
        repair_task_hours: (r.repair_minutes || 0) / 60,
        monitoring_hours: (r.monitoring_minutes || 0) / 60,
        assistance_hours: (r.assistance_minutes || 0) / 60,
        carried_hours: 0,
        total_hours: r.total_work_hours || 0,
        remaining_hours: 0,
        updated_at: new Date().toISOString(),
        avatar: ''
      } as AttendanceRecord
    })

    attendanceList.value = mappedRecords
    updateGroupOptions(mappedRecords)

    // 成功加载时清除错误状态
    apiError.value = ''
    retryCount.value = 0
  } catch (error: any) {
    console.error('加载考勤数据失败:', error)

    // 设置详细的错误信息
    const errorMsg = error?.response?.status === 500
      ? '考勤服务暂不可用，请稍后重试或联系管理员'
      : '网络连接异常，请检查网络状态'

    apiError.value = errorMsg

    if (retryCount.value < maxRetries && !isRetry) {
      retryCount.value++
      setTimeout(() => {
        loadAttendanceData(true)
      }, 1000 * retryCount.value)
    } else {
      ElMessage.error(`${errorMsg}（已重试${retryCount.value}次）`)
    }
  } finally {
    loading.value = false
  }
}

// 刷新数据
const refreshData = async () => {
  await loadAttendanceData()
  ElMessage.success('数据已刷新')
}

// 过滤考勤数据
const filterAttendanceData = () => {
  // 重置分页
  pagination.page = 1
}

// 分页处理
const handlePageChange = () => {
  // filteredAttendanceList 计算属性会自动处理分页
}

const handleSizeChange = () => {
  pagination.page = 1
}

const periodText = computed(() => {
  if (cycleType.value === 'monthly') return selectedMonth.value || getCurrentMonth()
  if (cycleType.value === 'weekly') return `${weekStart.value || dayjs().format('YYYY-MM-DD')}（一周）`
  if (customRange.value) return `${customRange.value[0]} 至 ${customRange.value[1]}`
  return '当前周期'
})

const resolveExportRange = () => {
  const fallbackStart = dayjs().startOf('month').format('YYYY-MM-DD')
  const fallbackEnd = dayjs().endOf('month').format('YYYY-MM-DD')

  if (cycleType.value === 'monthly') {
    const monthValue = selectedMonth.value || getCurrentMonth()
    const monthDay = dayjs(monthValue)
    return {
      dateFrom: monthDay.startOf('month').format('YYYY-MM-DD'),
      dateTo: monthDay.endOf('month').format('YYYY-MM-DD')
    }
  }

  if (cycleType.value === 'weekly') {
    const startValue = weekStart.value || dayjs().format('YYYY-MM-DD')
    const startDay = dayjs(startValue)
    return {
      dateFrom: startDay.format('YYYY-MM-DD'),
      dateTo: startDay.add(6, 'day').format('YYYY-MM-DD')
    }
  }

  const [customStart, customEnd] = customRange.value || [fallbackStart, fallbackEnd]
  return { dateFrom: customStart, dateTo: customEnd }
}

// 导出考勤数据（按新模板）
const handleExport = async () => {
  try {
    loading.value = true
    const { dateFrom, dateTo } = resolveExportRange()

    const startMonth = dayjs(dateFrom)
    const endMonth = dayjs(dateTo)

    if (!startMonth.isValid() || !endMonth.isValid()) {
      ElMessage.error('导出时间范围无效，请重新选择')
      return
    }

    if (startMonth.format('YYYY-MM') !== endMonth.format('YYYY-MM')) {
      ElMessage.warning('导出时间范围需在同一月份内，请调整筛选条件')
      return
    }

    if (startMonth.isAfter(endMonth)) {
      ElMessage.error('开始日期不能晚于结束日期')
      return
    }

    const exportResult = await attendanceApi.exportWorkHoursData({
      date_from: dateFrom,
      date_to: dateTo,
      format: 'excel'
    })

    if (exportResult?.success) {
      const totalRecords = exportResult.total_records ?? attendanceList.value?.length ?? 0
      ElMessage.success(`考勤数据导出成功，共 ${totalRecords} 条记录`)

      if (!exportResult.download_url) {
        ElMessage.warning('导出文件生成成功，但未返回下载链接')
        return
      }

      try {
        const filename = exportResult.filename || `attendance_${dateFrom}.xlsx`
        const { getToken } = await import('@/utils/auth')
        const token = getToken()
        const downloadUrl = `${window.location.origin}${exportResult.download_url}`

        const response = await fetch(downloadUrl, {
          method: 'GET',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          }
        })

        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`)
        }

        const blob = await response.blob()
        const url = window.URL.createObjectURL(blob)
        const link = document.createElement('a')
        link.href = url
        link.download = filename
        document.body.appendChild(link)
        link.click()
        document.body.removeChild(link)
        window.URL.revokeObjectURL(url)
      } catch (downloadError: any) {
        console.error('下载文件失败:', downloadError)
        ElMessage.error(`下载文件失败: ${downloadError?.message || '未知错误'}`)
      }
    } else {
      const message = exportResult?.message || '导出失败，请稍后再试'
      ElMessage.error(message)
    }
  } catch (error) {
    console.error('导出失败:', error)
    ElMessage.error('导出失败')
  } finally {
    loading.value = false
  }
}

// 计算考勤功能移除（不使用打卡，不需要后台重算）

// 查看成员详情
const viewMemberDetail = (record: AttendanceRecord) => {
  // TODO: 实现成员考勤详情页面
  ElMessage.info(`查看 ${record.member_name} 的详细考勤信息`)
}

// 调整工时
const adjustWorkHours = (record: AttendanceRecord) => {
  // TODO: 实现工时调整功能
  ElMessage.info(`调整 ${record.member_name} 的工时`)
}

// 获取当前月份
const getCurrentMonth = (): string => {
  const now = new Date()
  return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}`
}

// 清除错误状态
const clearError = () => {
  apiError.value = ''
  retryCount.value = 0
}

// 手动重试加载数据
const retryLoadData = async () => {
  await loadAttendanceData(false)
}

onMounted(async () => {
  // 设置默认月份为当前月
  selectedMonth.value = getCurrentMonth()

  // 加载考勤数据
  await loadAttendanceData()
})
</script>

<style scoped lang="scss">
.attendance-view {
  padding: 20px;
  background: #f5f7fa;
  min-height: 100vh;
}

.error-section {
  margin-bottom: 20px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;

  .header-left {
    .page-title {
      font-size: 24px;
      font-weight: 600;
      color: #303133;
      margin: 0 0 8px 0;
    }

    .page-description {
      color: #909399;
      font-size: 14px;
      margin: 0;
    }
  }

  .header-actions {
    display: flex;
    gap: 12px;
  }
}

.period-overview {
  margin-bottom: 20px;

  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;

    .header-actions {
      display: flex;
      align-items: center;
      gap: 16px;
    }
  }

  .stats-grid {
    display: grid;
    grid-template-columns: repeat(6, 1fr);
    gap: 16px;
    margin-top: 16px;

    .stat-card {
      display: flex;
      align-items: center;
      padding: 16px;
      border-radius: 8px;
      background: white;
      border: 1px solid #e4e7ed;
      transition: all 0.3s ease;

      &:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
      }

      .stat-icon {
        width: 40px;
        height: 40px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        margin-right: 12px;
        color: white;
      }

      .stat-content {
        .stat-number {
          font-size: 24px;
          font-weight: 600;
          color: #303133;
          line-height: 1;
        }

        .stat-label {
          font-size: 12px;
          color: #909399;
          margin-top: 4px;
        }
      }

      &.total-members .stat-icon {
        background: #67c23a;
      }
      &.total-hours .stat-icon {
        background: #409eff;
      }
      &.repair-hours .stat-icon {
        background: #e6a23c;
      }
      &.monitoring-hours .stat-icon {
        background: #f56c6c;
      }
      &.assistance-hours .stat-icon {
        background: #909399;
      }
      &.average-hours .stat-icon {
        background: #9c27b0;
      }
    }
  }
}

.table-card {
  .table-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 16px;

    .table-title {
      font-size: 18px;
      font-weight: 600;
      color: #303133;
    }
  }

  .filters {
    margin-bottom: 16px;
    padding: 16px;
    background: #f8f9fa;
    border-radius: 4px;
  }

  .member-info {
    display: flex;
    align-items: center;

    .member-name {
      font-weight: 500;
      color: #303133;
    }

    .member-group {
      font-size: 12px;
      color: #909399;
    }
  }

  .total-hours-number {
    font-weight: 600;
    color: #409eff;
  }

  .repair-hours {
    font-weight: 500;
    color: #e6a23c;
  }

  .monitoring-hours {
    font-weight: 500;
    color: #f56c6c;
  }

  .assistance-hours {
    font-weight: 500;
    color: #909399;
  }

  .carried-hours {
    font-weight: 500;
    color: #67c23a;
  }

  .remaining-hours {
    font-weight: 500;
    color: #409eff;

    &.negative {
      color: #f56c6c;
    }
  }

  .work-hours-chart {
    display: flex;
    height: 20px;
    border-radius: 4px;
    overflow: hidden;
    background: #f5f7fa;

    .chart-bar {
      height: 100%;
      min-width: 2px;

      &.repair {
        background: #e6a23c;
      }
      &.monitoring {
        background: #f56c6c;
      }
      &.assistance {
        background: #909399;
      }
    }
  }

  .pagination-wrapper {
    display: flex;
    justify-content: center;
    margin-top: 20px;
  }

  .chart-container {
    padding: 20px 0;

    .charts-grid {
      display: grid;
      grid-template-columns: repeat(2, 1fr);
      gap: 20px;

      .chart-item {
        h3 {
          font-size: 16px;
          font-weight: 600;
          color: #303133;
          margin-bottom: 12px;
        }
      }
    }
  }
}

.attendance-row {
  &:hover {
    background-color: #f8f9fa;
  }
}

@media (max-width: 1200px) {
  .stats-grid {
    grid-template-columns: repeat(3, 1fr) !important;
  }

  .charts-grid {
    grid-template-columns: 1fr !important;
  }
}

@media (max-width: 768px) {
  .stats-grid {
    grid-template-columns: repeat(2, 1fr) !important;
  }

  .page-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 16px;
  }

  .work-hours-chart {
    height: 16px;
  }
}
</style>
