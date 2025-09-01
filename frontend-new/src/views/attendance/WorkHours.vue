<template>
  <div class="desktop-work-hours">
    <div class="page-header">
      <div class="header-content">
        <div class="header-text">
          <h1>工时管理</h1>
          <p>查看和管理团队成员的工时统计</p>
        </div>
        <div class="header-actions">
          <a-button type="primary" :icon="h(CalculatorOutlined)" @click="showRecalculateModal = true">
            重新计算工时
          </a-button>
          <a-button :icon="h(DownloadOutlined)" @click="exportWorkHours">
            导出工时
          </a-button>
          <a-button :icon="h(ReloadOutlined)" @click="refreshWorkHours" :loading="loading">
            刷新
          </a-button>
        </div>
      </div>
    </div>
    
    <div class="desktop-work-hours-panel">
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
            v-model:value="memberFilter"
            placeholder="选择成员"
            style="width: 160px"
            @change="handleMemberChange"
            show-search
            allow-clear
          >
            <a-select-option 
              v-for="member in memberOptions" 
              :key="member.id"
              :value="member.id"
            >
              {{ member.name }}
            </a-select-option>
          </a-select>
          
          <a-select
            v-model:value="periodFilter"
            placeholder="统计周期"
            style="width: 120px"
            @change="handlePeriodChange"
          >
            <a-select-option value="week">本周</a-select-option>
            <a-select-option value="month">本月</a-select-option>
            <a-select-option value="quarter">本季度</a-select-option>
            <a-select-option value="year">本年度</a-select-option>
            <a-select-option value="custom">自定义</a-select-option>
          </a-select>

          <a-range-picker
            v-if="periodFilter === 'custom'"
            v-model:value="dateRange"
            format="YYYY-MM-DD"
            @change="handleDateRangeChange"
            style="width: 240px"
          />
        </div>
        
        <div class="summary-info">
          <a-statistic title="总工时" :value="totalHours" suffix="小时" />
          <a-statistic title="本月工时" :value="monthHours" suffix="小时" />
          <a-statistic title="平均工时" :value="averageHours" suffix="小时" />
        </div>
      </div>

      <a-table
        :columns="columns"
        :data-source="workHoursList"
        :loading="loading"
        row-key="id"
        :scroll="{ x: 1400 }"
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
        <template #taskType="{ text }">
          <a-tag :color="getTaskTypeColor(text)">
            {{ getTaskTypeText(text) }}
          </a-tag>
        </template>
        
        <template #status="{ text }">
          <a-tag :color="getStatusColor(text)">
            {{ getStatusText(text) }}
          </a-tag>
        </template>

        <template #baseHours="{ text }">
          <span class="hours-value">{{ text }} 小时</span>
        </template>

        <template #bonusHours="{ text, record }">
          <span 
            class="hours-value"
            :class="{ 
              'bonus-positive': text > 0, 
              'bonus-negative': text < 0 
            }"
          >
            {{ text > 0 ? '+' : '' }}{{ text }} 小时
          </span>
        </template>

        <template #totalHours="{ text }">
          <span class="hours-value total-hours">{{ text }} 小时</span>
        </template>
        
        <template #actions="{ record }">
          <a-space>
            <a-tooltip title="查看详情">
              <a-button size="small" :icon="h(EyeOutlined)" @click="viewWorkHours(record)" />
            </a-tooltip>
            <a-tooltip title="手动调整">
              <a-button 
                size="small" 
                :icon="h(EditOutlined)" 
                @click="adjustWorkHours(record)"
              />
            </a-tooltip>
            <a-tooltip title="重新计算">
              <a-button
                size="small"
                :icon="h(ReloadOutlined)"
                @click="recalculateWorkHours(record)"
              />
            </a-tooltip>
          </a-space>
        </template>
      </a-table>
    </div>

    <!-- 批量重新计算对话框 -->
    <a-modal
      v-model:visible="showRecalculateModal"
      title="批量重新计算工时"
      width="500px"
      @ok="handleBatchRecalculate"
      @cancel="showRecalculateModal = false"
      :confirmLoading="recalculateLoading"
    >
      <div class="recalculate-form">
        <a-form layout="vertical">
          <a-form-item label="计算范围">
            <a-radio-group v-model:value="recalculateScope">
              <a-radio value="all">全部工时记录</a-radio>
              <a-radio value="period">指定时间段</a-radio>
              <a-radio value="member">指定成员</a-radio>
            </a-radio-group>
          </a-form-item>
          
          <a-form-item v-if="recalculateScope === 'period'" label="时间范围">
            <a-range-picker 
              v-model:value="recalculateDateRange"
              format="YYYY-MM-DD"
              style="width: 100%"
            />
          </a-form-item>
          
          <a-form-item v-if="recalculateScope === 'member'" label="选择成员">
            <a-select 
              v-model:value="recalculateMember"
              placeholder="选择要重新计算的成员"
              style="width: 100%"
            >
              <a-select-option 
                v-for="member in memberOptions" 
                :key="member.id"
                :value="member.id"
              >
                {{ member.name }}
              </a-select-option>
            </a-select>
          </a-form-item>
          
          <a-alert
            message="重要提醒"
            description="重新计算将覆盖现有的工时数据，此操作不可撤销，请谨慎操作。"
            type="warning"
            show-icon
          />
        </a-form>
      </div>
    </a-modal>

    <!-- 工时调整对话框 -->
    <a-modal
      v-model:visible="showAdjustModal"
      title="工时调整"
      width="600px"
      @ok="handleAdjust"
      @cancel="showAdjustModal = false"
      :confirmLoading="adjustLoading"
    >
      <div v-if="selectedRecord" class="adjust-form">
        <a-descriptions :column="2" bordered>
          <a-descriptions-item label="任务标题" :span="2">
            {{ selectedRecord.taskTitle }}
          </a-descriptions-item>
          <a-descriptions-item label="执行者">
            {{ selectedRecord.memberName }}
          </a-descriptions-item>
          <a-descriptions-item label="任务类型">
            <a-tag :color="getTaskTypeColor(selectedRecord.taskType)">
              {{ getTaskTypeText(selectedRecord.taskType) }}
            </a-tag>
          </a-descriptions-item>
          <a-descriptions-item label="基础工时">
            {{ selectedRecord.baseHours }} 小时
          </a-descriptions-item>
          <a-descriptions-item label="当前奖罚">
            <span 
              :class="{ 
                'bonus-positive': selectedRecord.bonusHours > 0, 
                'bonus-negative': selectedRecord.bonusHours < 0 
              }"
            >
              {{ selectedRecord.bonusHours > 0 ? '+' : '' }}{{ selectedRecord.bonusHours }} 小时
            </span>
          </a-descriptions-item>
        </a-descriptions>
        
        <div style="margin-top: 24px;">
          <a-form layout="vertical">
            <a-form-item label="调整工时" required>
              <a-input-number
                v-model:value="adjustHours"
                :min="-999"
                :max="999"
                :step="0.5"
                :precision="1"
                style="width: 200px"
                addon-after="小时"
                placeholder="输入调整的工时"
              />
              <div class="adjust-hint">
                正数为增加工时，负数为减少工时
              </div>
            </a-form-item>
            
            <a-form-item label="调整原因" required>
              <a-textarea
                v-model:value="adjustReason"
                :rows="3"
                placeholder="请输入调整原因"
                maxlength="200"
                show-count
              />
            </a-form-item>
          </a-form>
        </div>
      </div>
    </a-modal>

    <!-- 工时详情对话框 -->
    <a-modal
      v-model:visible="showDetailModal"
      title="工时详情"
      width="700px"
      :footer="null"
    >
      <div v-if="selectedRecord" class="work-hours-detail">
        <a-descriptions :column="2" bordered>
          <a-descriptions-item label="任务ID">
            {{ selectedRecord.taskId }}
          </a-descriptions-item>
          <a-descriptions-item label="任务标题">
            {{ selectedRecord.taskTitle }}
          </a-descriptions-item>
          <a-descriptions-item label="执行者">
            {{ selectedRecord.memberName }}
          </a-descriptions-item>
          <a-descriptions-item label="任务类型">
            <a-tag :color="getTaskTypeColor(selectedRecord.taskType)">
              {{ getTaskTypeText(selectedRecord.taskType) }}
            </a-tag>
          </a-descriptions-item>
          <a-descriptions-item label="任务状态">
            <a-tag :color="getStatusColor(selectedRecord.status)">
              {{ getStatusText(selectedRecord.status) }}
            </a-tag>
          </a-descriptions-item>
          <a-descriptions-item label="基础工时">
            {{ selectedRecord.baseHours }} 小时
          </a-descriptions-item>
          <a-descriptions-item label="奖励/惩罚工时">
            <span 
              :class="{ 
                'bonus-positive': selectedRecord.bonusHours > 0, 
                'bonus-negative': selectedRecord.bonusHours < 0 
              }"
            >
              {{ selectedRecord.bonusHours > 0 ? '+' : '' }}{{ selectedRecord.bonusHours }} 小时
            </span>
          </a-descriptions-item>
          <a-descriptions-item label="总工时">
            <span class="total-hours">{{ selectedRecord.totalHours }} 小时</span>
          </a-descriptions-item>
          <a-descriptions-item label="创建时间">
            {{ formatDateTime(selectedRecord.createdAt) }}
          </a-descriptions-item>
          <a-descriptions-item label="完成时间">
            {{ selectedRecord.completedAt ? formatDateTime(selectedRecord.completedAt) : '未完成' }}
          </a-descriptions-item>
          <a-descriptions-item label="实际用时" :span="2">
            {{ selectedRecord.actualHours ? selectedRecord.actualHours + ' 小时' : '未记录' }}
          </a-descriptions-item>
          <a-descriptions-item label="工时说明" :span="2">
            {{ selectedRecord.description || '无' }}
          </a-descriptions-item>
        </a-descriptions>
        
        <!-- 工时变更历史 -->
        <div v-if="selectedRecord.adjustmentHistory && selectedRecord.adjustmentHistory.length > 0" style="margin-top: 24px;">
          <h4>工时调整历史</h4>
          <a-timeline>
            <a-timeline-item 
              v-for="adjustment in selectedRecord.adjustmentHistory" 
              :key="adjustment.id"
              :color="adjustment.hours > 0 ? 'green' : 'red'"
            >
              <div class="adjustment-item">
                <div class="adjustment-header">
                  <span class="adjustment-time">{{ formatDateTime(adjustment.createdAt) }}</span>
                  <span class="adjustment-operator">{{ adjustment.operatorName }}</span>
                </div>
                <div class="adjustment-content">
                  <span class="adjustment-hours">
                    {{ adjustment.hours > 0 ? '+' : '' }}{{ adjustment.hours }} 小时
                  </span>
                  <span class="adjustment-reason">{{ adjustment.reason }}</span>
                </div>
              </div>
            </a-timeline-item>
          </a-timeline>
        </div>
      </div>
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, h } from 'vue'
import { message, Modal } from 'ant-design-vue'
import dayjs, { type Dayjs } from 'dayjs'
import * as XLSX from 'xlsx'
import {
  CalculatorOutlined,
  DownloadOutlined,
  ReloadOutlined,
  EyeOutlined,
  EditOutlined
} from '@ant-design/icons-vue'

// 模拟API调用
const mockApi = {
  async getWorkHoursList(params: any) {
    await new Promise(resolve => setTimeout(resolve, 500))
    
    const mockData = [
      {
        id: 1,
        taskId: 'T001',
        taskTitle: '实验室网络维护',
        memberName: '张三',
        memberId: 1,
        taskType: 'repair',
        status: 'completed',
        baseHours: 2.0,
        bonusHours: 0.5,
        totalHours: 2.5,
        actualHours: 2.3,
        createdAt: '2024-01-29 09:00:00',
        completedAt: '2024-01-29 11:30:00',
        description: '按时完成，获得奖励工时',
        adjustmentHistory: [
          {
            id: 1,
            hours: 0.5,
            reason: '提前完成任务',
            operatorName: '管理员',
            createdAt: '2024-01-29 12:00:00'
          }
        ]
      },
      {
        id: 2,
        taskId: 'T002',
        taskTitle: '机房设备检查',
        memberName: '李四',
        memberId: 2,
        taskType: 'monitoring',
        status: 'completed',
        baseHours: 3.0,
        bonusHours: -0.5,
        totalHours: 2.5,
        actualHours: 3.2,
        createdAt: '2024-01-28 14:00:00',
        completedAt: '2024-01-28 17:30:00',
        description: '延迟完成，扣除工时',
        adjustmentHistory: []
      },
      {
        id: 3,
        taskId: 'T003',
        taskTitle: '协助新生网络配置',
        memberName: '王五',
        memberId: 3,
        taskType: 'assistance',
        status: 'in_progress',
        baseHours: 1.5,
        bonusHours: 0,
        totalHours: 1.5,
        actualHours: null,
        createdAt: '2024-01-30 10:00:00',
        completedAt: null,
        description: '正在进行中',
        adjustmentHistory: []
      }
    ]
    
    return {
      success: true,
      data: {
        items: mockData,
        total: mockData.length,
        summary: {
          totalHours: mockData.reduce((sum, item) => sum + item.totalHours, 0),
          monthHours: 15.5,
          averageHours: 2.2
        }
      }
    }
  },

  async getMemberList() {
    await new Promise(resolve => setTimeout(resolve, 300))
    return {
      success: true,
      data: [
        { id: 1, name: '张三' },
        { id: 2, name: '李四' },
        { id: 3, name: '王五' },
        { id: 4, name: '赵六' }
      ]
    }
  },

  async recalculateWorkHours(params: any) {
    await new Promise(resolve => setTimeout(resolve, 2000))
    return {
      success: true,
      message: '工时重新计算完成',
      data: {
        processedCount: 15,
        updatedCount: 8
      }
    }
  },

  async adjustWorkHours(id: number, hours: number, reason: string) {
    await new Promise(resolve => setTimeout(resolve, 500))
    return {
      success: true,
      message: '工时调整成功'
    }
  }
}

// 响应式数据
const workHoursList = ref<any[]>([])
const total = ref(0)
const loading = ref(false)
const searchText = ref('')
const memberFilter = ref<number | null>(null)
const periodFilter = ref('month')
const dateRange = ref<[Dayjs, Dayjs] | null>(null)

// 成员选项
const memberOptions = ref<any[]>([])

// 对话框状态
const showRecalculateModal = ref(false)
const showAdjustModal = ref(false)
const showDetailModal = ref(false)
const selectedRecord = ref<any>(null)

// 加载状态
const recalculateLoading = ref(false)
const adjustLoading = ref(false)

// 重新计算表单数据
const recalculateScope = ref('all')
const recalculateDateRange = ref<[Dayjs, Dayjs] | null>(null)
const recalculateMember = ref<number | null>(null)

// 调整表单数据
const adjustHours = ref<number | null>(null)
const adjustReason = ref('')

// 统计数据
const totalHours = ref(0)
const monthHours = ref(0)
const averageHours = ref(0)

// 分页和筛选参数
const filters = reactive({
  page: 1,
  pageSize: 10,
  search: '',
  memberId: null as number | null,
  period: 'month',
  dateFrom: '',
  dateTo: ''
})

// 表格列定义
const columns = [
  {
    title: '任务ID',
    dataIndex: 'taskId',
    key: 'taskId',
    width: 100,
    fixed: 'left'
  },
  {
    title: '任务标题',
    dataIndex: 'taskTitle',
    key: 'taskTitle',
    width: 200,
    ellipsis: true
  },
  {
    title: '执行者',
    dataIndex: 'memberName',
    key: 'memberName',
    width: 100
  },
  {
    title: '任务类型',
    dataIndex: 'taskType',
    key: 'taskType',
    width: 100,
    slots: { customRender: 'taskType' }
  },
  {
    title: '状态',
    dataIndex: 'status',
    key: 'status',
    width: 100,
    slots: { customRender: 'status' }
  },
  {
    title: '基础工时',
    dataIndex: 'baseHours',
    key: 'baseHours',
    width: 100,
    slots: { customRender: 'baseHours' }
  },
  {
    title: '奖罚工时',
    dataIndex: 'bonusHours',
    key: 'bonusHours',
    width: 100,
    slots: { customRender: 'bonusHours' }
  },
  {
    title: '总工时',
    dataIndex: 'totalHours',
    key: 'totalHours',
    width: 100,
    slots: { customRender: 'totalHours' }
  },
  {
    title: '实际用时',
    dataIndex: 'actualHours',
    key: 'actualHours',
    width: 100,
    customRender: ({ text }: any) => text ? `${text} 小时` : '未记录'
  },
  {
    title: '完成时间',
    dataIndex: 'completedAt',
    key: 'completedAt',
    width: 160,
    customRender: ({ text }: any) => text ? formatDateTime(text) : '未完成'
  },
  {
    title: '操作',
    key: 'actions',
    width: 150,
    fixed: 'right',
    slots: { customRender: 'actions' }
  }
]

// 工具方法
const getTaskTypeColor = (type: string) => {
  const colors: Record<string, string> = {
    repair: 'orange',
    monitoring: 'blue',
    assistance: 'green'
  }
  return colors[type] || 'default'
}

const getTaskTypeText = (type: string) => {
  const texts: Record<string, string> = {
    repair: '维修任务',
    monitoring: '监测任务',
    assistance: '协助任务'
  }
  return texts[type] || type
}

const getStatusColor = (status: string) => {
  const colors: Record<string, string> = {
    pending: 'orange',
    in_progress: 'blue',
    completed: 'green',
    cancelled: 'red'
  }
  return colors[status] || 'default'
}

const getStatusText = (status: string) => {
  const texts: Record<string, string> = {
    pending: '待处理',
    in_progress: '进行中',
    completed: '已完成',
    cancelled: '已取消'
  }
  return texts[status] || status
}

const formatDateTime = (dateTime: string) => {
  return dayjs(dateTime).format('YYYY-MM-DD HH:mm:ss')
}

// API 调用方法
const fetchWorkHoursList = async () => {
  try {
    loading.value = true
    const params = {
      page: filters.page,
      pageSize: filters.pageSize,
      search: filters.search || undefined,
      memberId: filters.memberId || undefined,
      period: filters.period,
      dateFrom: filters.dateFrom || undefined,
      dateTo: filters.dateTo || undefined
    }
    
    const response = await mockApi.getWorkHoursList(params)
    if (response.success && response.data) {
      workHoursList.value = response.data.items || []
      total.value = response.data.total || 0
      
      // 更新统计数据
      if (response.data.summary) {
        totalHours.value = response.data.summary.totalHours
        monthHours.value = response.data.summary.monthHours
        averageHours.value = response.data.summary.averageHours
      }
    } else {
      message.error('获取工时列表失败')
    }
  } catch (error: any) {
    console.error('Fetch work hours error:', error)
    message.error(error.message || '获取工时列表失败，请检查网络连接')
  } finally {
    loading.value = false
  }
}

const fetchMemberList = async () => {
  try {
    const response = await mockApi.getMemberList()
    if (response.success && response.data) {
      memberOptions.value = response.data
    }
  } catch (error: any) {
    console.error('Fetch members error:', error)
  }
}

// 事件处理方法
const handleSearch = () => {
  filters.search = searchText.value
  filters.page = 1
  fetchWorkHoursList()
}

const handleMemberChange = () => {
  filters.memberId = memberFilter.value
  filters.page = 1
  fetchWorkHoursList()
}

const handlePeriodChange = () => {
  filters.period = periodFilter.value
  
  // 根据周期设置日期范围
  const now = dayjs()
  switch (periodFilter.value) {
    case 'week':
      filters.dateFrom = now.startOf('week').format('YYYY-MM-DD')
      filters.dateTo = now.endOf('week').format('YYYY-MM-DD')
      break
    case 'month':
      filters.dateFrom = now.startOf('month').format('YYYY-MM-DD')
      filters.dateTo = now.endOf('month').format('YYYY-MM-DD')
      break
    case 'quarter':
      filters.dateFrom = now.startOf('quarter').format('YYYY-MM-DD')
      filters.dateTo = now.endOf('quarter').format('YYYY-MM-DD')
      break
    case 'year':
      filters.dateFrom = now.startOf('year').format('YYYY-MM-DD')
      filters.dateTo = now.endOf('year').format('YYYY-MM-DD')
      break
    default:
      filters.dateFrom = ''
      filters.dateTo = ''
  }
  
  filters.page = 1
  fetchWorkHoursList()
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
  fetchWorkHoursList()
}

const refreshWorkHours = () => {
  fetchWorkHoursList()
}

const handlePageChange = (page: number) => {
  filters.page = page
  fetchWorkHoursList()
}

const handlePageSizeChange = (_current: number, size: number) => {
  filters.pageSize = size
  filters.page = 1
  fetchWorkHoursList()
}

// 工时操作方法
const viewWorkHours = (record: any) => {
  selectedRecord.value = record
  showDetailModal.value = true
}

const adjustWorkHours = (record: any) => {
  selectedRecord.value = record
  adjustHours.value = null
  adjustReason.value = ''
  showAdjustModal.value = true
}

const recalculateWorkHours = async (record: any) => {
  Modal.confirm({
    title: '确认重新计算',
    content: `确定要重新计算 ${record.memberName} 的工时吗？`,
    onOk: async () => {
      try {
        const response = await mockApi.recalculateWorkHours({ taskId: record.taskId })
        if (response.success) {
          message.success(response.message || '重新计算成功')
          refreshWorkHours()
        } else {
          message.error(response.message || '重新计算失败')
        }
      } catch (error: any) {
        message.error(error.message || '重新计算失败')
      }
    }
  })
}

const handleBatchRecalculate = async () => {
  try {
    recalculateLoading.value = true
    
    const params: any = {
      scope: recalculateScope.value
    }
    
    if (recalculateScope.value === 'period' && recalculateDateRange.value) {
      params.dateFrom = recalculateDateRange.value[0].format('YYYY-MM-DD')
      params.dateTo = recalculateDateRange.value[1].format('YYYY-MM-DD')
    }
    
    if (recalculateScope.value === 'member' && recalculateMember.value) {
      params.memberId = recalculateMember.value
    }
    
    const response = await mockApi.recalculateWorkHours(params)
    if (response.success) {
      message.success(response.message || '批量重新计算完成')
      showRecalculateModal.value = false
      refreshWorkHours()
    } else {
      message.error(response.message || '批量重新计算失败')
    }
  } catch (error: any) {
    message.error(error.message || '批量重新计算失败')
  } finally {
    recalculateLoading.value = false
  }
}

const handleAdjust = async () => {
  if (!adjustHours.value || !adjustReason.value) {
    message.error('请填写调整工时和调整原因')
    return
  }
  
  try {
    adjustLoading.value = true
    
    const response = await mockApi.adjustWorkHours(
      selectedRecord.value.id,
      adjustHours.value,
      adjustReason.value
    )
    
    if (response.success) {
      message.success(response.message || '工时调整成功')
      showAdjustModal.value = false
      refreshWorkHours()
    } else {
      message.error(response.message || '工时调整失败')
    }
  } catch (error: any) {
    message.error(error.message || '工时调整失败')
  } finally {
    adjustLoading.value = false
  }
}

const exportWorkHours = () => {
  try {
    // 准备导出数据
    const exportData = workHoursList.value.map(item => ({
      '任务ID': item.taskId,
      '任务标题': item.taskTitle,
      '执行者': item.memberName,
      '任务类型': getTaskTypeText(item.taskType),
      '任务状态': getStatusText(item.status),
      '基础工时': item.baseHours,
      '奖罚工时': item.bonusHours,
      '总工时': item.totalHours,
      '实际用时': item.actualHours || '',
      '创建时间': formatDateTime(item.createdAt),
      '完成时间': item.completedAt ? formatDateTime(item.completedAt) : '未完成'
    }))
    
    // 创建工作簿
    const wb = XLSX.utils.book_new()
    const ws = XLSX.utils.json_to_sheet(exportData)
    
    // 设置列宽
    const colWidths = [
      { wch: 10 }, // 任务ID
      { wch: 25 }, // 任务标题
      { wch: 10 }, // 执行者
      { wch: 12 }, // 任务类型
      { wch: 12 }, // 任务状态
      { wch: 12 }, // 基础工时
      { wch: 12 }, // 奖罚工时
      { wch: 12 }, // 总工时
      { wch: 12 }, // 实际用时
      { wch: 20 }, // 创建时间
      { wch: 20 }  // 完成时间
    ]
    ws['!cols'] = colWidths
    
    XLSX.utils.book_append_sheet(wb, ws, '工时统计')
    
    // 生成文件名
    const fileName = `工时统计_${dayjs().format('YYYY-MM-DD')}.xlsx`
    
    // 下载文件
    XLSX.writeFile(wb, fileName)
    message.success('工时数据导出成功')
  } catch (error) {
    console.error('Export error:', error)
    message.error('工时数据导出失败')
  }
}

// 生命周期
onMounted(() => {
  fetchWorkHoursList()
  fetchMemberList()
})
</script>

<style scoped>
/* 桌面端工时管理界面样式 */
.desktop-work-hours {
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

.desktop-work-hours-panel {
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

/* 工时数值样式 */
.hours-value {
  font-weight: 500;
}

.bonus-positive {
  color: #52c41a;
}

.bonus-negative {
  color: #ff4d4f;
}

.total-hours {
  color: #1890ff;
  font-weight: 600;
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

/* 表单样式优化 */
.recalculate-form,
.adjust-form {
  margin-top: 16px;
}

.adjust-hint {
  margin-top: 8px;
  font-size: 12px;
  color: #8c8c8c;
}

/* 详情对话框样式 */
.work-hours-detail :deep(.ant-descriptions-item-label) {
  font-weight: 500;
  color: #1a1a1a;
  background: #fafbfc;
}

.work-hours-detail :deep(.ant-descriptions-item-content) {
  color: #666666;
}

/* 调整历史样式 */
.adjustment-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.adjustment-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.adjustment-time {
  font-size: 12px;
  color: #8c8c8c;
}

.adjustment-operator {
  font-size: 12px;
  color: #1890ff;
}

.adjustment-content {
  display: flex;
  gap: 16px;
  align-items: center;
}

.adjustment-hours {
  font-weight: 500;
  font-size: 14px;
}

.adjustment-reason {
  color: #666666;
  font-size: 13px;
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