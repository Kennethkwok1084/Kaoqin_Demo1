<template>
  <div class="work-hours-view">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-left">
        <h1 class="page-title">工时管理</h1>
        <p class="page-description">查看基于任务完成的工时统计、月度汇总和数据导出</p>
      </div>
      <div class="header-actions">
        <el-button 
          :icon="Download" 
          @click="handleExport"
          type="primary"
        >
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
          <div class="stats-grid">
            <div class="stat-card hours">
              <div class="stat-icon">
                <el-icon><Timer /></el-icon>
              </div>
              <div class="stat-content">
                <div class="stat-number">{{ todaySummary.total_hours || 0 }}</div>
                <div class="stat-label">今日总工时</div>
              </div>
            </div>

            <div class="stat-card members">
              <div class="stat-icon">
                <el-icon><User /></el-icon>
              </div>
              <div class="stat-content">
                <div class="stat-number">{{ todaySummary.active_members || 0 }}</div>
                <div class="stat-label">活跃成员</div>
              </div>
            </div>

            <div class="stat-card repair">
              <div class="stat-icon">
                <el-icon><Tools /></el-icon>
              </div>
              <div class="stat-content">
                <div class="stat-number">{{ todaySummary.repair_hours || 0 }}</div>
                <div class="stat-label">维修工时</div>
              </div>
            </div>

            <div class="stat-card monitoring">
              <div class="stat-icon">
                <el-icon><Monitor /></el-icon>
              </div>
              <div class="stat-content">
                <div class="stat-number">{{ todaySummary.monitoring_hours || 0 }}</div>
                <div class="stat-label">监控工时</div>
              </div>
            </div>

            <div class="stat-card average">
              <div class="stat-icon">
                <el-icon><TrendCharts /></el-icon>
              </div>
              <div class="stat-content">
                <div class="stat-number">{{ todaySummary.average_hours || 0 }}</div>
                <div class="stat-label">平均工时</div>
              </div>
            </div>
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
          <el-col :span="8">
            <el-date-picker
              v-model="dateRange"
              type="daterange"
              range-separator="至"
              start-placeholder="开始日期"
              end-placeholder="结束日期"
              @change="loadWorkHoursRecords"
              style="width: 100%"
            />
          </el-col>
          <el-col :span="6">
            <el-select 
              v-model="filters.member_ids" 
              placeholder="选择成员" 
              multiple 
              clearable
              style="width: 100%"
              @change="loadWorkHoursRecords"
            >
              <el-option
                v-for="member in memberOptions"
                :key="member.value"
                :label="member.label"
                :value="member.value"
              />
            </el-select>
          </el-col>
          <el-col :span="6">
            <el-select 
              v-model="filters.task_type" 
              placeholder="任务类型" 
              clearable
              style="width: 100%"
              @change="loadWorkHoursRecords"
            >
              <el-option label="维修任务" value="repair" />
              <el-option label="监控任务" value="monitoring" />
              <el-option label="协助任务" value="assistance" />
            </el-select>
          </el-col>
          <el-col :span="4">
            <el-input
              v-model="filters.search"
              placeholder="搜索任务标题"
              @change="loadWorkHoursRecords"
            />
          </el-col>
        </el-row>
      </div>

      <!-- 表格视图 -->
      <div v-if="viewMode === 'table'">
        <el-table
          :data="workHoursList"
          :loading="loading"
          stripe
          height="600"
        >
          <el-table-column prop="task_id" label="任务ID" width="100" />
          <el-table-column prop="title" label="任务标题" min-width="200" />
          <el-table-column prop="task_type" label="任务类型" width="120">
            <template #default="{ row }">
              <el-tag :type="getTaskTypeTagType(row.task_type)">
                {{ row.task_type }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="member_name" label="成员姓名" width="120" />
          <el-table-column prop="work_date" label="完成日期" width="120">
            <template #default="{ row }">
              {{ formatDate(row.work_date) }}
            </template>
          </el-table-column>
          <el-table-column prop="work_hours" label="工时(小时)" width="100">
            <template #default="{ row }">
              <span class="work-hours-number">{{ row.work_hours }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="rating" label="评分" width="80">
            <template #default="{ row }">
              <el-rate :model-value="row.rating" disabled show-score />
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
            @current-change="loadWorkHoursRecords"
            @size-change="loadWorkHoursRecords"
          />
        </div>
      </div>

      <!-- 图表视图 -->
      <div v-else-if="viewMode === 'chart'" class="chart-container">
        <div id="workHoursChart" style="height: 400px;"></div>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, onUnmounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Download, Refresh, Timer, User, Tools, Monitor, TrendCharts } from '@element-plus/icons-vue'
import { attendanceApi } from '@/api/attendance'
import { MembersApi } from '@/api/members'
import type { WorkHoursRecord } from '@/types/attendance'

// 响应式数据
const loading = ref(false)
const viewMode = ref('table')
const currentTime = ref('')
const dateRange = ref<[string, string]>([])

const todaySummary = reactive({
  total_hours: 0,
  active_members: 0,
  repair_hours: 0,
  monitoring_hours: 0,
  assistance_hours: 0,
  average_hours: 0,
  participation_rate: 0
})

const workHoursList = ref<WorkHoursRecord[]>([])
const memberOptions = ref<Array<{ label: string; value: number }>>([])

const filters = reactive({
  member_ids: [] as number[],
  task_type: '',
  search: ''
})

const pagination = reactive({
  page: 1,
  size: 20,
  total: 0
})

// 更新当前时间
const updateCurrentTime = () => {
  currentTime.value = new Date().toLocaleString('zh-CN')
}

// 获取任务类型标签颜色
const getTaskTypeTagType = (taskType: string) => {
  const typeMap: Record<string, string> = {
    '维修任务': 'primary',
    '监控任务': 'success',
    '协助任务': 'warning'
  }
  return typeMap[taskType] || 'info'
}

// 格式化日期
const formatDate = (date: string | Date) => {
  if (!date) return '-'
  return new Date(date).toLocaleDateString('zh-CN')
}

// 加载今日工时数据
const loadTodayData = async () => {
  try {
    const summary = await attendanceApi.getTodayWorkHoursSummary()
    Object.assign(todaySummary, summary.data || summary)
  } catch (error) {
    console.error('加载今日数据失败:', error)
    ElMessage.error('加载今日数据失败')
  }
}

// 刷新今日数据
const refreshTodayData = async () => {
  await loadTodayData()
  ElMessage.success('数据已刷新')
}

// 加载工时记录
const loadWorkHoursRecords = async () => {
  try {
    loading.value = true
    
    const params: any = {
      page: pagination.page,
      size: pagination.size
    }

    if (dateRange.value?.length === 2) {
      params.date_from = dateRange.value[0]
      params.date_to = dateRange.value[1]
    }

    if (filters.member_ids?.length > 0) {
      params.member_ids = filters.member_ids
    }

    if (filters.search) {
      params.search = filters.search
    }

    const records = await attendanceApi.getWorkHoursRecords(params)
    workHoursList.value = records
    pagination.total = records.length
    
  } catch (error) {
    console.error('加载工时记录失败:', error)
    ElMessage.error('加载工时记录失败')
  } finally {
    loading.value = false
  }
}

// 导出工时数据
const handleExport = async () => {
  try {
    loading.value = true
    const result = await attendanceApi.exportWorkHoursData({
      date_from: dateRange.value?.[0] || '',
      date_to: dateRange.value?.[1] || '',
      member_ids: filters.member_ids,
      format: 'excel'
    })
    
    if (result.success) {
      ElMessage.success(`工时数据导出成功，共 ${result.total_records} 条记录`)
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

// 加载成员选项
const loadMemberOptions = async () => {
  try {
    const response = await MembersApi.getMembers({ 
      page: 1, 
      size: 100,
      is_active: true 
    })
    
    // 适配不同的响应格式
    const members = response.items || response.data || response
    if (Array.isArray(members)) {
      memberOptions.value = members.map((member: any) => ({
        label: member.name,
        value: member.id
      }))
    }
  } catch (error) {
    console.error('加载成员列表失败:', error)
    // 如果加载失败，提供空的选项列表
    memberOptions.value = []
  }
}

// 时间更新定时器
let timeInterval: number

onMounted(async () => {
  updateCurrentTime()
  timeInterval = window.setInterval(updateCurrentTime, 1000)
  
  // 设置默认日期范围为当月
  const now = new Date()
  const firstDay = new Date(now.getFullYear(), now.getMonth(), 1)
  const lastDay = new Date(now.getFullYear(), now.getMonth() + 1, 0)
  dateRange.value = [
    firstDay.toISOString().split('T')[0],
    lastDay.toISOString().split('T')[0]
  ]
  
  await Promise.all([
    loadTodayData(),
    loadWorkHoursRecords(),
    loadMemberOptions()
  ])
})

onUnmounted(() => {
  if (timeInterval) {
    clearInterval(timeInterval)
  }
})
</script>

<style scoped lang="scss">
.work-hours-view {
  padding: 20px;
  background: #f5f7fa;
  min-height: 100vh;
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
}

.today-overview {
  margin-bottom: 20px;

  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;

    .header-actions {
      display: flex;
      align-items: center;
      gap: 16px;

      .current-time {
        color: #909399;
        font-size: 14px;
      }
    }
  }

  .stats-grid {
    display: grid;
    grid-template-columns: repeat(5, 1fr);
    gap: 16px;
    margin-top: 16px;

    .stat-card {
      display: flex;
      align-items: center;
      padding: 16px;
      border-radius: 8px;
      background: white;
      border: 1px solid #e4e7ed;

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

      &.hours .stat-icon { background: #409eff; }
      &.members .stat-icon { background: #67c23a; }
      &.repair .stat-icon { background: #e6a23c; }
      &.monitoring .stat-icon { background: #f56c6c; }
      &.average .stat-icon { background: #909399; }
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

  .work-hours-number {
    font-weight: 600;
    color: #409eff;
  }

  .pagination-wrapper {
    display: flex;
    justify-content: center;
    margin-top: 20px;
  }

  .chart-container {
    padding: 20px 0;
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
}
</style>