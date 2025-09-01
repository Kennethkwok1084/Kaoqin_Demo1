<template>
  <div class="desktop-task-list">
    <div class="page-header">
      <div class="header-content">
        <div class="header-text">
          <h1>任务管理</h1>
          <p>管理和跟踪维修任务的执行状态</p>
        </div>
        <div class="header-actions">
          <a-button type="primary" :icon="h(PlusOutlined)" @click="$router.push('/tasks/create')">
            创建任务
          </a-button>
          <a-button :icon="h(ReloadOutlined)" @click="refreshTasks" :loading="loading">
            刷新
          </a-button>
        </div>
      </div>
    </div>
    
    <div class="desktop-task-panel">
      <div class="panel-header">
        <div class="filter-section">
          <a-input-search
            v-model:value="searchText"
            placeholder="搜索任务标题、位置或描述..."
            style="width: 300px"
            @search="handleSearch"
            :loading="loading"
          />
          
          <a-select
            v-model:value="statusFilter"
            placeholder="状态筛选"
            style="width: 140px"
            @change="handleStatusChange"
          >
            <a-select-option value="">全部状态</a-select-option>
            <a-select-option value="pending">待处理</a-select-option>
            <a-select-option value="in_progress">进行中</a-select-option>
            <a-select-option value="completed">已完成</a-select-option>
            <a-select-option value="cancelled">已取消</a-select-option>
          </a-select>
          
          <a-select
            v-model:value="typeFilter"
            placeholder="任务类型"
            style="width: 120px"
            @change="handleTypeChange"
          >
            <a-select-option value="">全部类型</a-select-option>
            <a-select-option value="repair">维修任务</a-select-option>
            <a-select-option value="monitoring">监测任务</a-select-option>
            <a-select-option value="assistance">协助任务</a-select-option>
          </a-select>
        </div>
        
        <div class="summary-info">
          <a-statistic title="总任务" :value="total" />
          <a-statistic title="进行中" :value="getStatusCount('in_progress')" />
          <a-statistic title="待处理" :value="getStatusCount('pending')" />
        </div>
      </div>

      <a-table
        :columns="columns"
        :data-source="tasks"
        :loading="loading"
        row-key="id"
        :scroll="{ x: 1200 }"
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
        <template #status="{ text }">
          <a-tag :color="getStatusColor(text)">
            {{ getStatusText(text) }}
          </a-tag>
        </template>
        
        <template #priority="{ text }">
          <a-tag :color="getPriorityColor(text)">
            {{ getPriorityText(text) }}
          </a-tag>
        </template>
        
        <template #actions="{ record }">
          <a-space>
            <a-tooltip title="查看详情">
              <a-button size="small" :icon="h(EyeOutlined)" @click="viewTask(record.id)" />
            </a-tooltip>
            <a-tooltip title="开始任务" v-if="record.status === 'pending'">
              <a-button
                size="small" 
                type="primary"
                :icon="h(PlayCircleOutlined)"
                @click="startTask(record.id)"
              />
            </a-tooltip>
            <a-tooltip title="完成任务" v-if="record.status === 'in_progress'">
              <a-button
                size="small"
                type="primary"
                :icon="h(CheckCircleOutlined)"
                @click="completeTask(record.id)"
              />
            </a-tooltip>
            <a-tooltip title="编辑任务" v-if="['pending', 'in_progress'].includes(record.status)">
              <a-button
                size="small"
                :icon="h(EditOutlined)"
                @click="editTask(record.id)"
              />
            </a-tooltip>
          </a-space>
        </template>
      </a-table>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, h } from 'vue'
import { message, Modal } from 'ant-design-vue'
import { useTasksStore } from '@/stores/tasks'
import {
  PlusOutlined,
  ReloadOutlined,
  EyeOutlined,
  PlayCircleOutlined,
  CheckCircleOutlined,
  EditOutlined
} from '@ant-design/icons-vue'

const tasksStore = useTasksStore()

// 响应式数据
const searchText = ref('')
const statusFilter = ref('')
const typeFilter = ref('')

// 计算属性
const tasks = computed(() => tasksStore.tasks)
const total = computed(() => tasksStore.total)
const loading = computed(() => tasksStore.loading)
const filters = computed(() => tasksStore.filters)

// 表格列定义
const columns = [
  {
    title: '任务信息',
    dataIndex: 'title',
    key: 'title',
    width: 250,
    ellipsis: true,
    customRender: ({ record }: any) => h('div', { class: 'task-info-cell' }, [
      h('div', { class: 'task-title' }, record.title),
      h('div', { class: 'task-desc' }, record.description || '暂无描述')
    ])
  },
  {
    title: '类型',
    dataIndex: 'type',
    key: 'type',
    width: 100,
    customRender: ({ text }: any) => getTypeText(text)
  },
  {
    title: '位置',
    dataIndex: 'location', 
    key: 'location',
    width: 150,
    ellipsis: true
  },
  {
    title: '优先级',
    dataIndex: 'priority',
    key: 'priority',
    width: 100,
    slots: { customRender: 'priority' }
  },
  {
    title: '状态',
    dataIndex: 'status',
    key: 'status',
    width: 100,
    slots: { customRender: 'status' }
  },
  {
    title: '执行者',
    dataIndex: 'assigneeName',
    key: 'assigneeName',
    width: 120,
    customRender: ({ text }: any) => text || '未分配'
  },
  {
    title: '报告人',
    dataIndex: 'reporterName',
    key: 'reporterName',
    width: 120
  },
  {
    title: '创建时间',
    dataIndex: 'createdAt',
    key: 'createdAt',
    width: 160,
    customRender: ({ text }: any) => new Date(text).toLocaleString('zh-CN')
  },
  {
    title: '操作',
    key: 'actions',
    width: 150,
    fixed: 'right',
    slots: { customRender: 'actions' }
  }
]

// 方法
const handleSearch = () => {
  tasksStore.fetchTasks({ search: searchText.value, page: 1 })
}

const handleStatusChange = () => {
  tasksStore.fetchTasks({ status: statusFilter.value, page: 1 })
}

const handleTypeChange = () => {
  tasksStore.fetchTasks({ type: typeFilter.value, page: 1 })
}

const refreshTasks = () => {
  tasksStore.fetchTasks({ page: 1 })
}

const handlePageChange = (page: number) => {
  tasksStore.fetchTasks({ page })
}

const handlePageSizeChange = (_current: number, size: number) => {
  tasksStore.fetchTasks({ page: 1, pageSize: size })
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

const getPriorityColor = (priority: string) => {
  const colors: Record<string, string> = {
    high: 'red',
    medium: 'orange',
    low: 'green'
  }
  return colors[priority] || 'default'
}

const getPriorityText = (priority: string) => {
  const texts: Record<string, string> = {
    high: '高',
    medium: '中',
    low: '低'
  }
  return texts[priority] || priority
}

const getTypeText = (type: string) => {
  const texts: Record<string, string> = {
    repair: '维修任务',
    monitoring: '监测任务',
    assistance: '协助任务'
  }
  return texts[type] || type
}

const getStatusCount = (status: string) => {
  if (!tasks.value) return 0
  return tasks.value.filter((task: any) => task.status === status).length
}

const viewTask = (taskId: number) => {
  // TODO: 跳转到任务详情页面
  message.info(`查看任务详情: ${taskId}`)
}

const editTask = (taskId: number) => {
  // TODO: 跳转到任务编辑页面
  message.info(`编辑任务: ${taskId}`)
}

const startTask = async (taskId: number) => {
  try {
    const result = await tasksStore.startTask(taskId)
    if (result.success) {
      message.success(result.message)
    } else {
      message.error(result.message)
    }
  } catch (error: any) {
    message.error(error.message)
  }
}

const completeTask = async (taskId: number) => {
  try {
    // 显示确认对话框
    Modal.confirm({
      title: '确认完成任务',
      content: '请确认该任务已完成，此操作不可撤销。',
      onOk: async () => {
        const result = await tasksStore.completeTask(taskId, 2) // 默认2小时
        if (result.success) {
          message.success(result.message || '任务已完成')
        } else {
          message.error(result.message || '任务完成失败')
        }
      }
    })
  } catch (error: any) {
    console.error('Complete task failed:', error)
    const errorMessage = error.response?.data?.message || error.message || '任务完成失败'
    message.error(errorMessage)
  }
}

// 生命周期
onMounted(() => {
  tasksStore.fetchTasks()
})
</script>

<style scoped>
/* 桌面端任务管理界面样式 */
.desktop-task-list {
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

.desktop-task-panel {
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

/* 任务信息单元格样式 */
.task-info-cell {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.task-title {
  font-size: 14px;
  font-weight: 500;
  color: #1a1a1a;
  line-height: 1.4;
}

.task-desc {
  font-size: 12px;
  color: #8c8c8c;
  line-height: 1.3;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  max-width: 200px;
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

:deep(.ant-tooltip) {
  font-size: 12px;
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
  
  .summary-info {
    justify-content: space-around;
  }
}
</style>