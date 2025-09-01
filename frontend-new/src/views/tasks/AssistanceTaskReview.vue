<template>
  <div class="desktop-assistance-review">
    <div class="page-header">
      <div class="header-content">
        <div class="header-text">
          <h1>协助任务审核</h1>
          <p>审核学生网管自主登记的协助任务</p>
        </div>
        <div class="header-actions">
          <a-button type="primary" :disabled="!selectedRowKeys.length" @click="handleBatchApprove">
            <CheckOutlined />
            批量通过
          </a-button>
          <a-button danger :disabled="!selectedRowKeys.length" @click="handleBatchReject">
            <CloseOutlined />
            批量拒绝
          </a-button>
          <a-button :icon="h(ReloadOutlined)" @click="refreshTasks" :loading="loading">
            刷新
          </a-button>
        </div>
      </div>
    </div>
    
    <div class="review-panel">
      <div class="panel-header">
        <div class="filter-section">
          <a-space>
            <a-select
              v-model:value="statusFilter"
              placeholder="状态筛选"
              style="width: 140px"
              @change="handleStatusChange"
            >
              <a-select-option value="">全部状态</a-select-option>
              <a-select-option value="pending">待审核</a-select-option>
              <a-select-option value="approved">已通过</a-select-option>
              <a-select-option value="rejected">已拒绝</a-select-option>
            </a-select>
            
            <a-date-picker
              v-model:value="dateRange"
              type="date"
              range-picker
              placeholder="选择时间范围"
              @change="handleDateChange"
            />
          </a-space>
        </div>
        
        <div class="summary-info">
          <a-statistic-countdown title="待审核" :value="pendingCount" />
          <a-statistic title="本月已审核" :value="reviewedCount" />
        </div>
      </div>

      <a-table
        :columns="columns"
        :data-source="tasks"
        :loading="loading"
        row-key="id"
        :row-selection="{ 
          selectedRowKeys, 
          onChange: onSelectChange,
          getCheckboxProps: record => ({ 
            disabled: record.status !== 'pending' 
          })
        }"
        :scroll="{ x: 1400 }"
        :pagination="{
          current: pagination.page,
          pageSize: pagination.pageSize,
          total: pagination.total,
          showSizeChanger: true,
          showQuickJumper: true,
          showTotal: (total: number, range: number[]) => `显示 ${range[0]}-${range[1]} 条，共 ${total} 条`,
          onChange: handlePageChange,
          onShowSizeChange: handlePageSizeChange
        }"
      >
        <template #status="{ text, record }">
          <a-tag :color="getStatusColor(text)">
            {{ getStatusText(text) }}
          </a-tag>
        </template>
        
        <template #work_hours="{ text }">
          <span class="work-hours">{{ text }}小时</span>
        </template>
        
        <template #actions="{ record }">
          <a-space>
            <a-button 
              size="small" 
              type="primary" 
              :disabled="record.status !== 'pending'"
              @click="handleApprove(record.id)"
            >
              <CheckOutlined />
              通过
            </a-button>
            <a-button 
              size="small" 
              danger
              :disabled="record.status !== 'pending'"
              @click="handleReject(record.id)"
            >
              <CloseOutlined />
              拒绝
            </a-button>
            <a-button 
              size="small"
              @click="showDetail(record)"
            >
              <EyeOutlined />
              详情
            </a-button>
          </a-space>
        </template>
      </a-table>
    </div>

    <!-- 任务详情模态框 -->
    <a-modal
      v-model:open="detailModalVisible"
      title="协助任务详情"
      :width="800"
      :footer="null"
    >
      <div v-if="selectedTask" class="task-detail">
        <a-descriptions :column="2" bordered>
          <a-descriptions-item label="任务标题" span="2">
            {{ selectedTask.title }}
          </a-descriptions-item>
          <a-descriptions-item label="协助部门">
            {{ selectedTask.assisted_department || '未填写' }}
          </a-descriptions-item>
          <a-descriptions-item label="协助人员">
            {{ selectedTask.assisted_person || '未填写' }}
          </a-descriptions-item>
          <a-descriptions-item label="开始时间">
            {{ formatDateTime(selectedTask.start_time) }}
          </a-descriptions-item>
          <a-descriptions-item label="结束时间">
            {{ formatDateTime(selectedTask.end_time) }}
          </a-descriptions-item>
          <a-descriptions-item label="工作时长">
            {{ selectedTask.work_hours }}小时
          </a-descriptions-item>
          <a-descriptions-item label="提交人员">
            {{ selectedTask.member_name }}
          </a-descriptions-item>
          <a-descriptions-item label="提交时间">
            {{ formatDateTime(selectedTask.created_at) }}
          </a-descriptions-item>
          <a-descriptions-item label="当前状态">
            <a-tag :color="getStatusColor(selectedTask.status)">
              {{ getStatusText(selectedTask.status) }}
            </a-tag>
          </a-descriptions-item>
          <a-descriptions-item label="任务描述" span="2">
            {{ selectedTask.description || '无描述' }}
          </a-descriptions-item>
        </a-descriptions>
      </div>
    </a-modal>

    <!-- 审核理由模态框 -->
    <a-modal
      v-model:open="reviewModalVisible"
      :title="reviewAction === 'approve' ? '通过审核' : '拒绝审核'"
      @ok="confirmReview"
      @cancel="cancelReview"
    >
      <a-form>
        <a-form-item label="审核理由">
          <a-textarea
            v-model:value="reviewComment"
            :placeholder="reviewAction === 'approve' ? '通过理由（可选）' : '拒绝理由（必填）'"
            :rows="4"
          />
        </a-form-item>
      </a-form>
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, h } from 'vue'
import { message, Modal } from 'ant-design-vue'
import { api } from '@/api/client'
import {
  CheckOutlined,
  CloseOutlined,
  ReloadOutlined,
  EyeOutlined
} from '@ant-design/icons-vue'

// 响应式数据
const tasks = ref<any[]>([])
const loading = ref(false)
const selectedRowKeys = ref<number[]>([])
const statusFilter = ref('')
const dateRange = ref<[string, string] | null>(null)
const detailModalVisible = ref(false)
const reviewModalVisible = ref(false)
const selectedTask = ref<any>(null)
const reviewAction = ref<'approve' | 'reject'>('approve')
const reviewComment = ref('')
const currentReviewIds = ref<number[]>([])

// 分页
const pagination = ref({
  page: 1,
  pageSize: 20,
  total: 0
})

// 统计数据
const pendingCount = computed(() => 
  tasks.value.filter(task => task.status === 'pending').length
)
const reviewedCount = computed(() => 
  tasks.value.filter(task => task.status !== 'pending').length
)

// 表格列定义
const columns = [
  {
    title: '任务信息',
    dataIndex: 'title',
    key: 'title',
    width: 200,
    ellipsis: true
  },
  {
    title: '提交人员',
    dataIndex: 'member_name',
    key: 'member_name',
    width: 100
  },
  {
    title: '协助部门',
    dataIndex: 'assisted_department',
    key: 'assisted_department',
    width: 120,
    ellipsis: true
  },
  {
    title: '协助人员',
    dataIndex: 'assisted_person',
    key: 'assisted_person',
    width: 100
  },
  {
    title: '工作时长',
    dataIndex: 'work_hours',
    key: 'work_hours',
    width: 100,
    slots: { customRender: 'work_hours' }
  },
  {
    title: '状态',
    dataIndex: 'status',
    key: 'status',
    width: 100,
    slots: { customRender: 'status' }
  },
  {
    title: '提交时间',
    dataIndex: 'created_at',
    key: 'created_at',
    width: 160,
    customRender: ({ text }: any) => formatDateTime(text)
  },
  {
    title: '操作',
    key: 'actions',
    width: 200,
    fixed: 'right',
    slots: { customRender: 'actions' }
  }
]

// 方法
const fetchTasks = async () => {
  try {
    loading.value = true
    
    const params: any = {
      page: pagination.value.page,
      pageSize: pagination.value.pageSize
    }
    
    if (statusFilter.value) {
      params.status = statusFilter.value
    }
    
    if (dateRange.value) {
      params.date_from = dateRange.value[0]
      params.date_to = dateRange.value[1]
    }

    // 注意：这个API需要后端实现
    const result = await api.getPendingAssistanceTasks(params)
    
    if (result.success && result.data) {
      tasks.value = result.data.items
      pagination.value.total = result.data.total
    }
  } catch (error: any) {
    console.error('获取协助任务列表失败:', error)
    message.error('获取协助任务列表失败')
  } finally {
    loading.value = false
  }
}

const refreshTasks = () => {
  selectedRowKeys.value = []
  fetchTasks()
}

const handleStatusChange = () => {
  pagination.value.page = 1
  fetchTasks()
}

const handleDateChange = () => {
  pagination.value.page = 1
  fetchTasks()
}

const handlePageChange = (page: number) => {
  pagination.value.page = page
  fetchTasks()
}

const handlePageSizeChange = (current: number, size: number) => {
  pagination.value.page = 1
  pagination.value.pageSize = size
  fetchTasks()
}

const onSelectChange = (keys: number[]) => {
  selectedRowKeys.value = keys
}

const handleApprove = (taskId: number) => {
  currentReviewIds.value = [taskId]
  reviewAction.value = 'approve'
  reviewComment.value = ''
  reviewModalVisible.value = true
}

const handleReject = (taskId: number) => {
  currentReviewIds.value = [taskId]
  reviewAction.value = 'reject'
  reviewComment.value = ''
  reviewModalVisible.value = true
}

const handleBatchApprove = () => {
  if (!selectedRowKeys.value.length) return
  currentReviewIds.value = [...selectedRowKeys.value]
  reviewAction.value = 'approve'
  reviewComment.value = ''
  reviewModalVisible.value = true
}

const handleBatchReject = () => {
  if (!selectedRowKeys.value.length) return
  currentReviewIds.value = [...selectedRowKeys.value]
  reviewAction.value = 'reject'
  reviewComment.value = ''
  reviewModalVisible.value = true
}

const confirmReview = async () => {
  try {
    if (reviewAction.value === 'reject' && !reviewComment.value.trim()) {
      message.error('拒绝审核时必须填写理由')
      return
    }

    if (currentReviewIds.value.length === 1) {
      // 单个审核
      const result = await api.approveAssistanceTask(currentReviewIds.value[0], {
        action: reviewAction.value,
        comment: reviewComment.value
      })
      
      if (result.success) {
        message.success(result.message || '审核成功')
      }
    } else {
      // 批量审核
      const result = await api.batchApproveAssistanceTasks(
        currentReviewIds.value, 
        reviewAction.value
      )
      
      if (result.success) {
        message.success(`批量${reviewAction.value === 'approve' ? '通过' : '拒绝'}成功`)
      }
    }
    
    reviewModalVisible.value = false
    selectedRowKeys.value = []
    await fetchTasks()
    
  } catch (error: any) {
    console.error('审核失败:', error)
    message.error('审核操作失败')
  }
}

const cancelReview = () => {
  reviewModalVisible.value = false
  reviewComment.value = ''
  currentReviewIds.value = []
}

const showDetail = (task: any) => {
  selectedTask.value = task
  detailModalVisible.value = true
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
    pending: '待审核',
    approved: '已通过',
    rejected: '已拒绝'
  }
  return texts[status] || status
}

const formatDateTime = (dateStr?: string) => {
  if (!dateStr) return '-'
  return new Date(dateStr).toLocaleString('zh-CN')
}

// 生命周期
onMounted(() => {
  fetchTasks()
})
</script>

<style scoped>
.desktop-assistance-review {
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
  color: #666666;
  font-size: 16px;
}

.header-actions {
  display: flex;
  gap: 12px;
}

.review-panel {
  background: white;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.04);
  border: 1px solid #e8e9ea;
  overflow: hidden;
  flex: 1;
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 24px 32px;
  border-bottom: 1px solid #e8e9ea;
  background: #fafbfc;
}

.filter-section .ant-space {
  gap: 16px;
}

.summary-info {
  display: flex;
  gap: 32px;
}

.work-hours {
  font-weight: 500;
  color: #1890ff;
}

.task-detail {
  padding: 16px 0;
}

/* 响应式优化 */
@media (max-width: 768px) {
  .header-content {
    flex-direction: column;
    gap: 20px;
    text-align: center;
  }
  
  .panel-header {
    flex-direction: column;
    gap: 16px;
  }
}
</style>
