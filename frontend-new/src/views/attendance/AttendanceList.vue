<template>
  <div class="desktop-attendance-list">
    <div class="page-header">
      <div class="header-content">
        <div class="header-text">
          <h1>考勤管理</h1>
          <p>查看和管理团队成员的考勤记录</p>
        </div>
        <div class="header-actions">
          <a-button type="primary" :icon="h(PlusOutlined)" @click="showLeaveDialog = true">
            请假申请
          </a-button>
          <a-button :icon="h(ClockCircleOutlined)" @click="showOvertimeDialog = true">
            加班申请
          </a-button>
          <a-button :icon="h(ReloadOutlined)" @click="refreshAttendance" :loading="loading">
            刷新
          </a-button>
        </div>
      </div>
    </div>
    
    <div class="desktop-attendance-panel">
      <div class="panel-header">
        <div class="filter-section">
          <a-input-search
            v-model:value="searchText"
            placeholder="搜索成员姓名..."
            style="width: 250px"
            @search="handleSearch"
            :loading="loading"
          />
          
          <a-select
            v-model:value="typeFilter"
            placeholder="记录类型"
            style="width: 140px"
            @change="handleTypeChange"
          >
            <a-select-option value="">全部类型</a-select-option>
            <a-select-option value="checkin">签到</a-select-option>
            <a-select-option value="checkout">签退</a-select-option>
            <a-select-option value="leave">请假</a-select-option>
            <a-select-option value="overtime">加班</a-select-option>
          </a-select>
          
          <a-select
            v-model:value="statusFilter"
            placeholder="审批状态"
            style="width: 120px"
            @change="handleStatusChange"
          >
            <a-select-option value="">全部状态</a-select-option>
            <a-select-option value="pending">待审批</a-select-option>
            <a-select-option value="approved">已批准</a-select-option>
            <a-select-option value="rejected">已拒绝</a-select-option>
          </a-select>

          <a-range-picker
            v-model:value="dateRange"
            format="YYYY-MM-DD"
            @change="handleDateRangeChange"
            style="width: 240px"
          />
        </div>
        
        <div class="summary-info">
          <a-statistic title="总记录数" :value="total" />
          <a-statistic title="今日签到" :value="getTodayCheckinCount()" />
          <a-statistic title="待审批" :value="getPendingCount()" />
        </div>
      </div>

      <a-table
        :columns="columns"
        :data-source="attendanceList"
        :loading="loading"
        row-key="id"
        :scroll="{ x: 1300 }"
        :pagination="{
          current: filters.page,
          pageSize: filters.pageSize,
          total: total,
          showSizeChanger: true,
          showQuickJumper: true,
          showTotal: (total: number, range: number[]) => `显示 ${range[0]}-${range[1]} 条，共 ${total} 条`,
          onChange: handlePageChange,
          onShowSizeChange: handlePageSizeChange
        }"
      >
        <template #type="{ text }">
          <a-tag :color="getTypeColor(text)">
            {{ getTypeText(text) }}
          </a-tag>
        </template>
        
        <template #status="{ text }">
          <a-tag :color="getStatusColor(text)">
            {{ getStatusText(text) }}
          </a-tag>
        </template>

        <template #duration="{ record }">
          <span v-if="record.type === 'leave' || record.type === 'overtime'">
            {{ formatDuration(record.startTime, record.endTime) }}
          </span>
          <span v-else>-</span>
        </template>
        
        <template #actions="{ record }">
          <a-space>
            <a-tooltip title="查看详情">
              <a-button size="small" :icon="h(EyeOutlined)" @click="viewRecord(record)" />
            </a-tooltip>
            <a-tooltip title="审批" v-if="record.status === 'pending' && canApprove">
              <a-button
                size="small"
                type="primary"
                :icon="h(CheckOutlined)"
                @click="approveRecord(record)"
              />
            </a-tooltip>
            <a-tooltip title="拒绝" v-if="record.status === 'pending' && canApprove">
              <a-button
                size="small"
                danger
                :icon="h(CloseOutlined)"
                @click="rejectRecord(record)"
              />
            </a-tooltip>
          </a-space>
        </template>
      </a-table>
    </div>

    <!-- 请假申请对话框 -->
    <LeaveApplicationDialog
      v-model:visible="showLeaveDialog"
      @success="refreshAttendance"
    />

    <!-- 加班申请对话框 -->
    <OvertimeApplicationDialog
      v-model:visible="showOvertimeDialog"
      @success="refreshAttendance"
    />

    <!-- 详情查看对话框 -->
    <a-modal
      v-model:visible="showDetailModal"
      title="考勤详情"
      width="600px"
      :footer="null"
    >
      <div v-if="selectedRecord" class="attendance-detail">
        <a-descriptions :column="2" bordered>
          <a-descriptions-item label="成员姓名">
            {{ selectedRecord.memberName }}
          </a-descriptions-item>
          <a-descriptions-item label="记录类型">
            <a-tag :color="getTypeColor(selectedRecord.type)">
              {{ getTypeText(selectedRecord.type) }}
            </a-tag>
          </a-descriptions-item>
          <a-descriptions-item label="申请时间">
            {{ formatDateTime(selectedRecord.createdAt) }}
          </a-descriptions-item>
          <a-descriptions-item label="状态">
            <a-tag :color="getStatusColor(selectedRecord.status)">
              {{ getStatusText(selectedRecord.status) }}
            </a-tag>
          </a-descriptions-item>
          <a-descriptions-item 
            v-if="selectedRecord.type === 'leave' || selectedRecord.type === 'overtime'"
            label="开始时间"
          >
            {{ formatDateTime(selectedRecord.startTime) }}
          </a-descriptions-item>
          <a-descriptions-item 
            v-if="selectedRecord.type === 'leave' || selectedRecord.type === 'overtime'"
            label="结束时间"
          >
            {{ formatDateTime(selectedRecord.endTime) }}
          </a-descriptions-item>
          <a-descriptions-item 
            v-if="selectedRecord.type === 'leave' || selectedRecord.type === 'overtime'"
            label="时长"
            :span="2"
          >
            {{ formatDuration(selectedRecord.startTime, selectedRecord.endTime) }}
          </a-descriptions-item>
          <a-descriptions-item label="备注" :span="2">
            {{ selectedRecord.remarks || '无' }}
          </a-descriptions-item>
          <a-descriptions-item 
            v-if="selectedRecord.approvedBy"
            label="审批人"
          >
            {{ selectedRecord.approvedBy }}
          </a-descriptions-item>
          <a-descriptions-item 
            v-if="selectedRecord.approvedAt"
            label="审批时间"
          >
            {{ formatDateTime(selectedRecord.approvedAt) }}
          </a-descriptions-item>
        </a-descriptions>
      </div>
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, h } from 'vue'
import { message, Modal } from 'ant-design-vue'
import dayjs, { type Dayjs } from 'dayjs'
import LeaveApplicationDialog from '@/components/attendance/LeaveApplicationDialog.vue'
import OvertimeApplicationDialog from '@/components/attendance/OvertimeApplicationDialog.vue'
import {
  PlusOutlined,
  ClockCircleOutlined,
  ReloadOutlined,
  EyeOutlined,
  CheckOutlined,
  CloseOutlined
} from '@ant-design/icons-vue'

// 模拟API调用
const mockApi = {
  async getAttendanceList(params: any) {
    await new Promise(resolve => setTimeout(resolve, 500))
    
    const mockData = [
      {
        id: 1,
        memberId: 1,
        memberName: '张三',
        type: 'checkin',
        status: 'approved',
        createdAt: '2024-01-30 09:00:00',
        remarks: '正常签到'
      },
      {
        id: 2,
        memberId: 2,
        memberName: '李四',
        type: 'leave',
        status: 'pending',
        startTime: '2024-01-31 09:00:00',
        endTime: '2024-01-31 18:00:00',
        createdAt: '2024-01-30 10:30:00',
        remarks: '个人事务请假'
      },
      {
        id: 3,
        memberId: 3,
        memberName: '王五',
        type: 'overtime',
        status: 'approved',
        startTime: '2024-01-30 18:00:00',
        endTime: '2024-01-30 22:00:00',
        createdAt: '2024-01-30 17:45:00',
        approvedBy: '管理员',
        approvedAt: '2024-01-30 18:15:00',
        remarks: '项目紧急需求加班'
      },
      {
        id: 4,
        memberId: 1,
        memberName: '张三',
        type: 'checkout',
        status: 'approved',
        createdAt: '2024-01-30 18:00:00',
        remarks: '正常签退'
      }
    ]
    
    return {
      success: true,
      data: {
        items: mockData,
        total: mockData.length
      }
    }
  },

  async approveAttendance(id: number) {
    await new Promise(resolve => setTimeout(resolve, 300))
    return {
      success: true,
      message: '审批成功'
    }
  },

  async rejectAttendance(id: number, reason: string) {
    await new Promise(resolve => setTimeout(resolve, 300))
    return {
      success: true,
      message: '已拒绝申请'
    }
  }
}

// 响应式数据
const attendanceList = ref<any[]>([])
const total = ref(0)
const loading = ref(false)
const searchText = ref('')
const typeFilter = ref('')
const statusFilter = ref('')
const dateRange = ref<[Dayjs, Dayjs] | null>(null)

// 对话框状态
const showLeaveDialog = ref(false)
const showOvertimeDialog = ref(false)
const showDetailModal = ref(false)
const selectedRecord = ref<any>(null)

// 权限控制
const canApprove = computed(() => {
  // 这里应该根据用户权限判断
  return true
})

// 分页和筛选参数
const filters = reactive({
  page: 1,
  pageSize: 10,
  search: '',
  type: '',
  status: '',
  dateFrom: '',
  dateTo: ''
})

// 表格列定义
const columns = [
  {
    title: '成员姓名',
    dataIndex: 'memberName',
    key: 'memberName',
    width: 120,
    fixed: 'left'
  },
  {
    title: '记录类型',
    dataIndex: 'type',
    key: 'type',
    width: 100,
    slots: { customRender: 'type' }
  },
  {
    title: '状态',
    dataIndex: 'status',
    key: 'status',
    width: 100,
    slots: { customRender: 'status' }
  },
  {
    title: '申请时间',
    dataIndex: 'createdAt',
    key: 'createdAt',
    width: 160,
    customRender: ({ text }: any) => formatDateTime(text)
  },
  {
    title: '开始时间',
    dataIndex: 'startTime',
    key: 'startTime',
    width: 160,
    customRender: ({ text, record }: any) => {
      return (record.type === 'leave' || record.type === 'overtime') && text 
        ? formatDateTime(text) : '-'
    }
  },
  {
    title: '结束时间',
    dataIndex: 'endTime',
    key: 'endTime',
    width: 160,
    customRender: ({ text, record }: any) => {
      return (record.type === 'leave' || record.type === 'overtime') && text 
        ? formatDateTime(text) : '-'
    }
  },
  {
    title: '时长',
    key: 'duration',
    width: 100,
    slots: { customRender: 'duration' }
  },
  {
    title: '审批人',
    dataIndex: 'approvedBy',
    key: 'approvedBy',
    width: 100,
    customRender: ({ text }: any) => text || '-'
  },
  {
    title: '备注',
    dataIndex: 'remarks',
    key: 'remarks',
    width: 200,
    ellipsis: true,
    customRender: ({ text }: any) => text || '-'
  },
  {
    title: '操作',
    key: 'actions',
    width: 150,
    fixed: 'right',
    slots: { customRender: 'actions' }
  }
]

// 计算属性
const getTodayCheckinCount = () => {
  const today = dayjs().format('YYYY-MM-DD')
  return attendanceList.value.filter(record => 
    record.type === 'checkin' && 
    dayjs(record.createdAt).format('YYYY-MM-DD') === today
  ).length
}

const getPendingCount = () => {
  return attendanceList.value.filter(record => record.status === 'pending').length
}

// 工具方法
const getTypeColor = (type: string) => {
  const colors: Record<string, string> = {
    checkin: 'green',
    checkout: 'blue',
    leave: 'orange',
    overtime: 'purple'
  }
  return colors[type] || 'default'
}

const getTypeText = (type: string) => {
  const texts: Record<string, string> = {
    checkin: '签到',
    checkout: '签退',
    leave: '请假',
    overtime: '加班'
  }
  return texts[type] || type
}

const getStatusColor = (status: string) => {
  const colors: Record<string, string> = {
    pending: 'orange',
    approved: 'green',
    rejected: 'red'
  }
  return colors[status] || 'default'
}

const getStatusText = (status: string) => {
  const texts: Record<string, string> = {
    pending: '待审批',
    approved: '已批准',
    rejected: '已拒绝'
  }
  return texts[status] || status
}

const formatDateTime = (dateTime: string) => {
  return dayjs(dateTime).format('YYYY-MM-DD HH:mm:ss')
}

const formatDuration = (startTime: string, endTime: string) => {
  if (!startTime || !endTime) return '-'
  
  const start = dayjs(startTime)
  const end = dayjs(endTime)
  const diff = end.diff(start, 'minute')
  
  if (diff < 60) {
    return `${diff}分钟`
  } else {
    const hours = Math.floor(diff / 60)
    const minutes = diff % 60
    return minutes > 0 ? `${hours}小时${minutes}分钟` : `${hours}小时`
  }
}

// API 调用方法
const fetchAttendanceList = async () => {
  try {
    loading.value = true
    const params = {
      page: filters.page,
      pageSize: filters.pageSize,
      search: filters.search || undefined,
      type: filters.type || undefined,
      status: filters.status || undefined,
      dateFrom: filters.dateFrom || undefined,
      dateTo: filters.dateTo || undefined
    }
    
    const response = await mockApi.getAttendanceList(params)
    if (response.success && response.data) {
      attendanceList.value = response.data.items || []
      total.value = response.data.total || 0
    } else {
      message.error('获取考勤记录失败')
    }
  } catch (error: any) {
    console.error('Fetch attendance error:', error)
    message.error(error.message || '获取考勤记录失败，请检查网络连接')
  } finally {
    loading.value = false
  }
}

// 事件处理方法
const handleSearch = () => {
  filters.search = searchText.value
  filters.page = 1
  fetchAttendanceList()
}

const handleTypeChange = () => {
  filters.type = typeFilter.value
  filters.page = 1
  fetchAttendanceList()
}

const handleStatusChange = () => {
  filters.status = statusFilter.value
  filters.page = 1
  fetchAttendanceList()
}

const handleDateRangeChange = (dates: [Dayjs, Dayjs] | null) => {
  if (dates) {
    filters.dateFrom = dates[0].format('YYYY-MM-DD')
    filters.dateTo = dates[1].format('YYYY-MM-DD')
  } else {
    filters.dateFrom = ''
    filters.dateTo = ''
  }
  filters.page = 1
  fetchAttendanceList()
}

const refreshAttendance = () => {
  fetchAttendanceList()
}

const handlePageChange = (page: number) => {
  filters.page = page
  fetchAttendanceList()
}

const handlePageSizeChange = (_current: number, size: number) => {
  filters.pageSize = size
  filters.page = 1
  fetchAttendanceList()
}

// 记录操作方法
const viewRecord = (record: any) => {
  selectedRecord.value = record
  showDetailModal.value = true
}

const approveRecord = async (record: any) => {
  Modal.confirm({
    title: '确认审批',
    content: `确定要批准 ${record.memberName} 的${getTypeText(record.type)}申请吗？`,
    onOk: async () => {
      try {
        const response = await mockApi.approveAttendance(record.id)
        if (response.success) {
          message.success(response.message || '审批成功')
          refreshAttendance()
        } else {
          message.error(response.message || '审批失败')
        }
      } catch (error: any) {
        message.error(error.message || '审批失败')
      }
    }
  })
}

const rejectRecord = async (record: any) => {
  Modal.confirm({
    title: '确认拒绝',
    content: h('div', [
      h('p', `确定要拒绝 ${record.memberName} 的${getTypeText(record.type)}申请吗？`),
      h('a-textarea', {
        placeholder: '请输入拒绝理由（可选）',
        rows: 3,
        style: { marginTop: '12px' },
        onInput: (e: any) => {
          // 这里可以保存拒绝理由
        }
      })
    ]),
    onOk: async () => {
      try {
        const response = await mockApi.rejectAttendance(record.id, '管理员拒绝')
        if (response.success) {
          message.success(response.message || '已拒绝申请')
          refreshAttendance()
        } else {
          message.error(response.message || '操作失败')
        }
      } catch (error: any) {
        message.error(error.message || '操作失败')
      }
    }
  })
}

// 生命周期
onMounted(() => {
  fetchAttendanceList()
})
</script>

<style scoped>
/* 桌面端考勤管理界面样式 */
.desktop-attendance-list {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.page-header {
  background: white;
  border-radius: 12px;
  padding: 32px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.04);
  border: 1px solid #e8e9ea;
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-text h1 {
  margin: 0 0 8px;
  font-size: 28px;
  font-weight: 600;
  color: #1a1a1a;
}

.header-text p {
  margin: 0;
  font-size: 16px;
  color: #666666;
}

.header-actions {
  display: flex;
  gap: 12px;
}

.desktop-attendance-panel {
  background: white;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.04);
  border: 1px solid #e8e9ea;
  overflow: hidden;
  flex: 1;
  display: flex;
  flex-direction: column;
}

.panel-header {
  padding: 24px 32px;
  border-bottom: 1px solid #e8e9ea;
  background: #fafbfc;
}

.filter-section {
  display: flex;
  gap: 16px;
  align-items: center;
  margin-bottom: 20px;
  flex-wrap: wrap;
}

.summary-info {
  display: flex;
  gap: 48px;
  align-items: center;
}

:deep(.ant-statistic-title) {
  font-size: 14px;
  color: #8c8c8c;
  font-weight: 500;
}

:deep(.ant-statistic-content-value) {
  font-size: 24px;
  font-weight: 600;
  color: #1a1a1a;
}

:deep(.ant-table-wrapper) {
  flex: 1;
}

:deep(.ant-table-thead > tr > th) {
  background: #fafbfc;
  border-bottom: 2px solid #e8e9ea;
  font-weight: 600;
  color: #1a1a1a;
  font-size: 14px;
}

:deep(.ant-table-tbody > tr > td) {
  border-bottom: 1px solid #f0f0f0;
  padding: 16px;
}

:deep(.ant-table-tbody > tr:hover > td) {
  background: #f8f9fa;
}

/* 标签样式优化 */
:deep(.ant-tag) {
  border: none;
  font-weight: 500;
  font-size: 12px;
  border-radius: 6px;
  padding: 2px 8px;
}

/* 按钮样式优化 */
:deep(.ant-btn-sm) {
  height: 28px;
  padding: 0 8px;
  font-size: 12px;
  border-radius: 6px;
}

/* 详情对话框样式 */
.attendance-detail :deep(.ant-descriptions-item-label) {
  font-weight: 500;
  color: #1a1a1a;
  background: #fafbfc;
}

.attendance-detail :deep(.ant-descriptions-item-content) {
  color: #666666;
}

/* 分页样式优化 */
:deep(.ant-pagination) {
  margin: 24px 0 0;
  padding: 0 32px 24px;
}

:deep(.ant-pagination-options) {
  margin-left: auto;
}

/* 响应式优化 */
@media (max-width: 1200px) {
  .header-content {
    flex-direction: column;
    gap: 20px;
    text-align: center;
  }
  
  .filter-section {
    flex-wrap: wrap;
    gap: 12px;
  }
  
  .summary-info {
    gap: 24px;
  }
}

@media (max-width: 768px) {
  .page-header {
    padding: 20px;
  }
  
  .panel-header {
    padding: 20px;
  }
  
  .filter-section {
    flex-direction: column;
    align-items: stretch;
  }
  
  .filter-section > * {
    width: 100% !important;
  }
  
  .summary-info {
    justify-content: space-around;
    flex-wrap: wrap;
    gap: 16px;
  }
  
  .header-actions {
    flex-direction: column;
    width: 100%;
  }
}
</style>