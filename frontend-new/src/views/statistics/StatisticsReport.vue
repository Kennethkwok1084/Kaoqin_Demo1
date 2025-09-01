<template>
  <div class="statistics-report-container">
    <div class="main-content">
      <div class="page-header">
        <h2 class="page-title">详细报表</h2>
        <p class="page-description">查看和分析详细的统计报表数据</p>
      </div>

      <div class="report-filters">
        <div class="filter-row">
          <div class="filter-group">
            <label>报表类型：</label>
            <a-select
              v-model:value="filters.reportType"
              style="width: 200px"
              @change="handleReportTypeChange"
            >
              <a-select-option value="member">成员报表</a-select-option>
              <a-select-option value="task">任务报表</a-select-option>
              <a-select-option value="attendance">考勤报表</a-select-option>
              <a-select-option value="workHours">工时报表</a-select-option>
            </a-select>
          </div>

          <div class="filter-group">
            <label>时间范围：</label>
            <a-range-picker
              v-model:value="filters.dateRange"
              style="width: 300px"
              @change="handleDateRangeChange"
            />
          </div>

          <div class="filter-group">
            <label>部门：</label>
            <a-select
              v-model:value="filters.department"
              style="width: 150px"
              allow-clear
              placeholder="全部部门"
              @change="handleDepartmentChange"
            >
              <a-select-option value="技术部">技术部</a-select-option>
              <a-select-option value="运维部">运维部</a-select-option>
              <a-select-option value="网络部">网络部</a-select-option>
            </a-select>
          </div>

          <div class="filter-actions">
            <a-button type="primary" @click="generateReport" :loading="loading">
              <template #icon><SearchOutlined /></template>
              生成报表
            </a-button>
            <a-button @click="exportReport" :loading="exportLoading">
              <template #icon><DownloadOutlined /></template>
              导出Excel
            </a-button>
            <a-button @click="resetFilters">
              <template #icon><ClearOutlined /></template>
              重置
            </a-button>
          </div>
        </div>
      </div>

      <div class="report-content" v-if="reportData">
        <!-- 成员报表 -->
        <div v-if="filters.reportType === 'member'" class="member-report">
          <div class="report-header">
            <h3>成员详细报表</h3>
            <div class="report-summary">
              <a-statistic title="总成员数" :value="reportData.summary.totalMembers" />
              <a-statistic title="活跃成员" :value="reportData.summary.activeMembers" />
              <a-statistic title="平均效率" :value="reportData.summary.avgEfficiency" suffix="%" />
            </div>
          </div>

          <div class="report-table">
            <a-table
              :columns="memberColumns"
              :data-source="reportData.details"
              :pagination="{ pageSize: 10, showSizeChanger: true, showQuickJumper: true }"
              :scroll="{ x: 1200 }"
            >
              <template #bodyCell="{ column, record }">
                <template v-if="column.key === 'avatar'">
                  <a-avatar :src="record.avatar" :alt="record.name">
                    {{ record.name.charAt(0) }}
                  </a-avatar>
                </template>
                <template v-else-if="column.key === 'efficiency'">
                  <a-progress
                    :percent="record.efficiency"
                    :status="record.efficiency >= 80 ? 'success' : record.efficiency >= 60 ? 'normal' : 'exception'"
                    size="small"
                  />
                </template>
                <template v-else-if="column.key === 'workHours'">
                  <span class="work-hours">{{ record.workHours }}小时</span>
                </template>
                <template v-else-if="column.key === 'status'">
                  <a-tag :color="record.status === '在职' ? 'green' : 'red'">
                    {{ record.status }}
                  </a-tag>
                </template>
              </template>
            </a-table>
          </div>
        </div>

        <!-- 任务报表 -->
        <div v-if="filters.reportType === 'task'" class="task-report">
          <div class="report-header">
            <h3>任务详细报表</h3>
            <div class="report-summary">
              <a-statistic title="总任务数" :value="reportData.summary.totalTasks" />
              <a-statistic title="已完成" :value="reportData.summary.completedTasks" />
              <a-statistic title="完成率" :value="reportData.summary.completionRate" suffix="%" />
            </div>
          </div>

          <div class="report-charts">
            <div class="chart-item">
              <h4>任务状态分布</h4>
              <div ref="taskStatusChart" class="chart-container"></div>
            </div>
            <div class="chart-item">
              <h4>任务类型分布</h4>
              <div ref="taskTypeChart" class="chart-container"></div>
            </div>
          </div>

          <div class="report-table">
            <a-table
              :columns="taskColumns"
              :data-source="reportData.details"
              :pagination="{ pageSize: 10, showSizeChanger: true, showQuickJumper: true }"
              :scroll="{ x: 1400 }"
            >
              <template #bodyCell="{ column, record }">
                <template v-if="column.key === 'status'">
                  <a-tag :color="getTaskStatusColor(record.status)">
                    {{ record.status }}
                  </a-tag>
                </template>
                <template v-else-if="column.key === 'priority'">
                  <a-tag :color="getPriorityColor(record.priority)">
                    {{ record.priority }}
                  </a-tag>
                </template>
                <template v-else-if="column.key === 'workHours'">
                  <span class="work-hours">{{ record.workHours }}小时</span>
                </template>
              </template>
            </a-table>
          </div>
        </div>

        <!-- 考勤报表 -->
        <div v-if="filters.reportType === 'attendance'" class="attendance-report">
          <div class="report-header">
            <h3>考勤详细报表</h3>
            <div class="report-summary">
              <a-statistic title="出勤天数" :value="reportData.summary.attendanceDays" />
              <a-statistic title="请假天数" :value="reportData.summary.leaveDays" />
              <a-statistic title="出勤率" :value="reportData.summary.attendanceRate" suffix="%" />
            </div>
          </div>

          <div class="report-charts">
            <div class="chart-item full-width">
              <h4>月度考勤趋势</h4>
              <div ref="attendanceTrendChart" class="chart-container"></div>
            </div>
          </div>

          <div class="report-table">
            <a-table
              :columns="attendanceColumns"
              :data-source="reportData.details"
              :pagination="{ pageSize: 10, showSizeChanger: true, showQuickJumper: true }"
              :scroll="{ x: 1200 }"
            >
              <template #bodyCell="{ column, record }">
                <template v-if="column.key === 'type'">
                  <a-tag :color="getAttendanceTypeColor(record.type)">
                    {{ record.type }}
                  </a-tag>
                </template>
                <template v-else-if="column.key === 'status'">
                  <a-tag :color="getAttendanceStatusColor(record.status)">
                    {{ record.status }}
                  </a-tag>
                </template>
              </template>
            </a-table>
          </div>
        </div>

        <!-- 工时报表 -->
        <div v-if="filters.reportType === 'workHours'" class="work-hours-report">
          <div class="report-header">
            <h3>工时详细报表</h3>
            <div class="report-summary">
              <a-statistic title="总工时" :value="reportData.summary.totalHours" suffix="小时" />
              <a-statistic title="平均工时" :value="reportData.summary.avgHours" suffix="小时" />
              <a-statistic title="效率指数" :value="reportData.summary.efficiencyIndex" suffix="%" />
            </div>
          </div>

          <div class="report-charts">
            <div class="chart-item">
              <h4>工时分布</h4>
              <div ref="workHoursDistChart" class="chart-container"></div>
            </div>
            <div class="chart-item">
              <h4>月度工时趋势</h4>
              <div ref="workHoursTrendChart" class="chart-container"></div>
            </div>
          </div>

          <div class="report-table">
            <a-table
              :columns="workHoursColumns"
              :data-source="reportData.details"
              :pagination="{ pageSize: 10, showSizeChanger: true, showQuickJumper: true }"
              :scroll="{ x: 1300 }"
            >
              <template #bodyCell="{ column, record }">
                <template v-if="column.key === 'efficiency'">
                  <a-progress
                    :percent="record.efficiency"
                    :status="record.efficiency >= 80 ? 'success' : record.efficiency >= 60 ? 'normal' : 'exception'"
                    size="small"
                  />
                </template>
                <template v-else-if="column.key === 'workHours'">
                  <span class="work-hours">{{ record.workHours }}小时</span>
                </template>
                <template v-else-if="column.key === 'overtime'">
                  <span class="overtime-hours">{{ record.overtime }}小时</span>
                </template>
              </template>
            </a-table>
          </div>
        </div>
      </div>

      <div v-else class="no-report">
        <a-empty description="请选择报表类型并生成报表" />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, nextTick } from 'vue'
import { message } from 'ant-design-vue'
import {
  SearchOutlined,
  DownloadOutlined,
  ClearOutlined
} from '@ant-design/icons-vue'
import * as echarts from 'echarts'
import type { ECharts } from 'echarts'
import * as XLSX from 'xlsx'

interface ReportFilters {
  reportType: string
  dateRange: [string, string] | null
  department: string | null
}

interface ReportData {
  summary: any
  details: any[]
}

const loading = ref(false)
const exportLoading = ref(false)
const reportData = ref<ReportData | null>(null)

const filters = reactive<ReportFilters>({
  reportType: 'member',
  dateRange: null,
  department: null
})

const taskStatusChart = ref<HTMLElement>()
const taskTypeChart = ref<HTMLElement>()
const attendanceTrendChart = ref<HTMLElement>()
const workHoursDistChart = ref<HTMLElement>()
const workHoursTrendChart = ref<HTMLElement>()

let taskStatusChartInstance: ECharts | null = null
let taskTypeChartInstance: ECharts | null = null
let attendanceTrendChartInstance: ECharts | null = null
let workHoursDistChartInstance: ECharts | null = null
let workHoursTrendChartInstance: ECharts | null = null

const memberColumns = [
  { title: '头像', dataIndex: 'avatar', key: 'avatar', width: 80, align: 'center' },
  { title: '姓名', dataIndex: 'name', key: 'name', width: 120 },
  { title: '员工编号', dataIndex: 'employeeId', key: 'employeeId', width: 120 },
  { title: '部门', dataIndex: 'department', key: 'department', width: 100 },
  { title: '职位', dataIndex: 'position', key: 'position', width: 120 },
  { title: '完成任务', dataIndex: 'completedTasks', key: 'completedTasks', width: 100, align: 'center' },
  { title: '工作时长', dataIndex: 'workHours', key: 'workHours', width: 100, align: 'center' },
  { title: '效率', dataIndex: 'efficiency', key: 'efficiency', width: 120, align: 'center' },
  { title: '状态', dataIndex: 'status', key: 'status', width: 80, align: 'center' }
]

const taskColumns = [
  { title: '任务编号', dataIndex: 'taskId', key: 'taskId', width: 120 },
  { title: '任务标题', dataIndex: 'title', key: 'title', width: 200 },
  { title: '任务类型', dataIndex: 'type', key: 'type', width: 100 },
  { title: '优先级', dataIndex: 'priority', key: 'priority', width: 80, align: 'center' },
  { title: '负责人', dataIndex: 'assignee', key: 'assignee', width: 100 },
  { title: '状态', dataIndex: 'status', key: 'status', width: 100, align: 'center' },
  { title: '工时', dataIndex: 'workHours', key: 'workHours', width: 80, align: 'center' },
  { title: '创建时间', dataIndex: 'createdAt', key: 'createdAt', width: 120 },
  { title: '完成时间', dataIndex: 'completedAt', key: 'completedAt', width: 120 }
]

const attendanceColumns = [
  { title: '姓名', dataIndex: 'name', key: 'name', width: 100 },
  { title: '员工编号', dataIndex: 'employeeId', key: 'employeeId', width: 120 },
  { title: '日期', dataIndex: 'date', key: 'date', width: 120 },
  { title: '考勤类型', dataIndex: 'type', key: 'type', width: 100, align: 'center' },
  { title: '上班时间', dataIndex: 'clockIn', key: 'clockIn', width: 120 },
  { title: '下班时间', dataIndex: 'clockOut', key: 'clockOut', width: 120 },
  { title: '工作时长', dataIndex: 'duration', key: 'duration', width: 100, align: 'center' },
  { title: '状态', dataIndex: 'status', key: 'status', width: 80, align: 'center' },
  { title: '备注', dataIndex: 'remarks', key: 'remarks', width: 150 }
]

const workHoursColumns = [
  { title: '姓名', dataIndex: 'name', key: 'name', width: 100 },
  { title: '员工编号', dataIndex: 'employeeId', key: 'employeeId', width: 120 },
  { title: '日期', dataIndex: 'date', key: 'date', width: 120 },
  { title: '标准工时', dataIndex: 'standardHours', key: 'standardHours', width: 100, align: 'center' },
  { title: '实际工时', dataIndex: 'workHours', key: 'workHours', width: 100, align: 'center' },
  { title: '加班工时', dataIndex: 'overtime', key: 'overtime', width: 100, align: 'center' },
  { title: '效率', dataIndex: 'efficiency', key: 'efficiency', width: 120, align: 'center' },
  { title: '项目', dataIndex: 'project', key: 'project', width: 120 }
]

const handleReportTypeChange = () => {
  reportData.value = null
}

const handleDateRangeChange = () => {
  // 日期范围变化处理
}

const handleDepartmentChange = () => {
  // 部门变化处理
}

const generateReport = async () => {
  loading.value = true
  try {
    await new Promise(resolve => setTimeout(resolve, 1000))
    
    switch (filters.reportType) {
      case 'member':
        reportData.value = generateMemberReport()
        break
      case 'task':
        reportData.value = generateTaskReport()
        await nextTick()
        initTaskCharts()
        break
      case 'attendance':
        reportData.value = generateAttendanceReport()
        await nextTick()
        initAttendanceCharts()
        break
      case 'workHours':
        reportData.value = generateWorkHoursReport()
        await nextTick()
        initWorkHoursCharts()
        break
    }
    
    message.success('报表生成成功')
  } catch (error) {
    message.error('报表生成失败')
  } finally {
    loading.value = false
  }
}

const generateMemberReport = (): ReportData => {
  return {
    summary: {
      totalMembers: 45,
      activeMembers: 42,
      avgEfficiency: 78.5
    },
    details: [
      {
        key: '1',
        avatar: 'https://randomuser.me/api/portraits/men/1.jpg',
        name: '张三',
        employeeId: 'EMP001',
        department: '技术部',
        position: '高级工程师',
        completedTasks: 28,
        workHours: 156,
        efficiency: 85,
        status: '在职'
      },
      {
        key: '2',
        avatar: 'https://randomuser.me/api/portraits/women/1.jpg',
        name: '李四',
        employeeId: 'EMP002',
        department: '运维部',
        position: '运维工程师',
        completedTasks: 24,
        workHours: 142,
        efficiency: 78,
        status: '在职'
      },
      {
        key: '3',
        avatar: 'https://randomuser.me/api/portraits/men/2.jpg',
        name: '王五',
        employeeId: 'EMP003',
        department: '网络部',
        position: '网络管理员',
        completedTasks: 32,
        workHours: 168,
        efficiency: 92,
        status: '在职'
      }
    ]
  }
}

const generateTaskReport = (): ReportData => {
  return {
    summary: {
      totalTasks: 156,
      completedTasks: 142,
      completionRate: 91.0
    },
    details: [
      {
        key: '1',
        taskId: 'T001',
        title: '网络设备维护',
        type: '维护任务',
        priority: '高',
        assignee: '张三',
        status: '已完成',
        workHours: 4.5,
        createdAt: '2024-01-15',
        completedAt: '2024-01-16'
      },
      {
        key: '2',
        taskId: 'T002',
        title: '系统监控优化',
        type: '优化任务',
        priority: '中',
        assignee: '李四',
        status: '进行中',
        workHours: 6.0,
        createdAt: '2024-01-16',
        completedAt: null
      },
      {
        key: '3',
        taskId: 'T003',
        title: '故障排查',
        type: '故障处理',
        priority: '紧急',
        assignee: '王五',
        status: '已完成',
        workHours: 2.5,
        createdAt: '2024-01-17',
        completedAt: '2024-01-17'
      }
    ]
  }
}

const generateAttendanceReport = (): ReportData => {
  return {
    summary: {
      attendanceDays: 22,
      leaveDays: 3,
      attendanceRate: 88.0
    },
    details: [
      {
        key: '1',
        name: '张三',
        employeeId: 'EMP001',
        date: '2024-01-15',
        type: '正常出勤',
        clockIn: '09:00',
        clockOut: '18:00',
        duration: '8小时',
        status: '正常',
        remarks: ''
      },
      {
        key: '2',
        name: '李四',
        employeeId: 'EMP002',
        date: '2024-01-15',
        type: '请假',
        clockIn: '-',
        clockOut: '-',
        duration: '0小时',
        status: '请假',
        remarks: '病假'
      },
      {
        key: '3',
        name: '王五',
        employeeId: 'EMP003',
        date: '2024-01-15',
        type: '加班',
        clockIn: '09:00',
        clockOut: '20:00',
        duration: '10小时',
        status: '加班',
        remarks: '项目紧急'
      }
    ]
  }
}

const generateWorkHoursReport = (): ReportData => {
  return {
    summary: {
      totalHours: 1856,
      avgHours: 7.8,
      efficiencyIndex: 82.5
    },
    details: [
      {
        key: '1',
        name: '张三',
        employeeId: 'EMP001',
        date: '2024-01-15',
        standardHours: 8,
        workHours: 8.5,
        overtime: 0.5,
        efficiency: 85,
        project: '网络维护项目'
      },
      {
        key: '2',
        name: '李四',
        employeeId: 'EMP002',
        date: '2024-01-15',
        standardHours: 8,
        workHours: 7.5,
        overtime: 0,
        efficiency: 78,
        project: '系统监控项目'
      },
      {
        key: '3',
        name: '王五',
        employeeId: 'EMP003',
        date: '2024-01-15',
        standardHours: 8,
        workHours: 10,
        overtime: 2,
        efficiency: 92,
        project: '故障处理项目'
      }
    ]
  }
}

const initTaskCharts = () => {
  if (taskStatusChart.value && !taskStatusChartInstance) {
    taskStatusChartInstance = echarts.init(taskStatusChart.value)
    const option = {
      tooltip: { trigger: 'item' },
      legend: { orient: 'vertical', left: 'left' },
      series: [{
        name: '任务状态',
        type: 'pie',
        radius: '50%',
        data: [
          { value: 142, name: '已完成' },
          { value: 8, name: '进行中' },
          { value: 4, name: '待开始' },
          { value: 2, name: '已取消' }
        ]
      }]
    }
    taskStatusChartInstance.setOption(option)
  }

  if (taskTypeChart.value && !taskTypeChartInstance) {
    taskTypeChartInstance = echarts.init(taskTypeChart.value)
    const option = {
      tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
      xAxis: { type: 'category', data: ['维护任务', '优化任务', '故障处理', '监控任务', '其他'] },
      yAxis: { type: 'value' },
      series: [{
        name: '任务数量',
        type: 'bar',
        data: [45, 32, 28, 35, 16]
      }]
    }
    taskTypeChartInstance.setOption(option)
  }
}

const initAttendanceCharts = () => {
  if (attendanceTrendChart.value && !attendanceTrendChartInstance) {
    attendanceTrendChartInstance = echarts.init(attendanceTrendChart.value)
    const option = {
      tooltip: { trigger: 'axis' },
      legend: { data: ['出勤率', '请假率'] },
      xAxis: {
        type: 'category',
        data: ['1月', '2月', '3月', '4月', '5月', '6月']
      },
      yAxis: { type: 'value', axisLabel: { formatter: '{value}%' } },
      series: [
        {
          name: '出勤率',
          type: 'line',
          data: [88, 92, 85, 89, 91, 87],
          itemStyle: { color: '#52c41a' }
        },
        {
          name: '请假率',
          type: 'line',
          data: [12, 8, 15, 11, 9, 13],
          itemStyle: { color: '#ff4d4f' }
        }
      ]
    }
    attendanceTrendChartInstance.setOption(option)
  }
}

const initWorkHoursCharts = () => {
  if (workHoursDistChart.value && !workHoursDistChartInstance) {
    workHoursDistChartInstance = echarts.init(workHoursDistChart.value)
    const option = {
      tooltip: { trigger: 'item' },
      legend: { orient: 'vertical', left: 'left' },
      series: [{
        name: '工时分布',
        type: 'pie',
        radius: ['40%', '70%'],
        data: [
          { value: 45, name: '正常工时' },
          { value: 18, name: '加班工时' },
          { value: 12, name: '请假扣减' },
          { value: 8, name: '其他调整' }
        ]
      }]
    }
    workHoursDistChartInstance.setOption(option)
  }

  if (workHoursTrendChart.value && !workHoursTrendChartInstance) {
    workHoursTrendChartInstance = echarts.init(workHoursTrendChart.value)
    const option = {
      tooltip: { trigger: 'axis' },
      legend: { data: ['标准工时', '实际工时', '加班工时'] },
      xAxis: {
        type: 'category',
        data: ['1月', '2月', '3月', '4月', '5月', '6月']
      },
      yAxis: { type: 'value', axisLabel: { formatter: '{value}h' } },
      series: [
        {
          name: '标准工时',
          type: 'bar',
          data: [160, 152, 168, 160, 176, 160],
          itemStyle: { color: '#1890ff' }
        },
        {
          name: '实际工时',
          type: 'bar',
          data: [156, 148, 162, 155, 172, 158],
          itemStyle: { color: '#52c41a' }
        },
        {
          name: '加班工时',
          type: 'line',
          data: [12, 8, 15, 18, 22, 16],
          itemStyle: { color: '#faad14' }
        }
      ]
    }
    workHoursTrendChartInstance.setOption(option)
  }
}

const exportReport = async () => {
  if (!reportData.value) {
    message.warning('请先生成报表')
    return
  }

  exportLoading.value = true
  try {
    await new Promise(resolve => setTimeout(resolve, 1000))
    
    const ws = XLSX.utils.json_to_sheet(reportData.value.details)
    const wb = XLSX.utils.book_new()
    XLSX.utils.book_append_sheet(wb, ws, `${getReportTypeName()}报表`)
    
    const fileName = `${getReportTypeName()}报表_${new Date().toISOString().split('T')[0]}.xlsx`
    XLSX.writeFile(wb, fileName)
    
    message.success('报表导出成功')
  } catch (error) {
    message.error('报表导出失败')
  } finally {
    exportLoading.value = false
  }
}

const resetFilters = () => {
  filters.reportType = 'member'
  filters.dateRange = null
  filters.department = null
  reportData.value = null
}

const getReportTypeName = () => {
  const typeMap: Record<string, string> = {
    member: '成员',
    task: '任务',
    attendance: '考勤',
    workHours: '工时'
  }
  return typeMap[filters.reportType] || '报表'
}

const getTaskStatusColor = (status: string) => {
  const colorMap: Record<string, string> = {
    '已完成': 'success',
    '进行中': 'processing',
    '待开始': 'warning',
    '已取消': 'error'
  }
  return colorMap[status] || 'default'
}

const getPriorityColor = (priority: string) => {
  const colorMap: Record<string, string> = {
    '紧急': 'red',
    '高': 'orange',
    '中': 'blue',
    '低': 'green'
  }
  return colorMap[priority] || 'default'
}

const getAttendanceTypeColor = (type: string) => {
  const colorMap: Record<string, string> = {
    '正常出勤': 'success',
    '加班': 'warning',
    '请假': 'error',
    '迟到': 'orange'
  }
  return colorMap[type] || 'default'
}

const getAttendanceStatusColor = (status: string) => {
  const colorMap: Record<string, string> = {
    '正常': 'success',
    '加班': 'warning',
    '请假': 'error',
    '迟到': 'orange'
  }
  return colorMap[status] || 'default'
}

onMounted(() => {
  generateReport()
})
</script>

<style scoped>
.statistics-report-container {
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 24px;
}

.main-content {
  max-width: 1600px;
  margin: 0 auto;
  background: white;
  border-radius: 12px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
  padding: 32px;
}

.page-header {
  margin-bottom: 32px;
  text-align: center;
}

.page-title {
  font-size: 28px;
  font-weight: 600;
  color: #1a1a1a;
  margin: 0 0 8px 0;
}

.page-description {
  font-size: 16px;
  color: #666;
  margin: 0;
}

.report-filters {
  background: #f8f9fa;
  border-radius: 8px;
  padding: 24px;
  margin-bottom: 32px;
}

.filter-row {
  display: flex;
  align-items: center;
  gap: 24px;
  flex-wrap: wrap;
}

.filter-group {
  display: flex;
  align-items: center;
  gap: 8px;
}

.filter-group label {
  font-weight: 500;
  color: #333;
  white-space: nowrap;
}

.filter-actions {
  display: flex;
  gap: 12px;
  margin-left: auto;
}

.report-content {
  margin-top: 32px;
}

.report-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 24px;
  padding-bottom: 16px;
  border-bottom: 1px solid #e8e8e8;
}

.report-header h3 {
  font-size: 20px;
  font-weight: 600;
  color: #333;
  margin: 0;
}

.report-summary {
  display: flex;
  gap: 48px;
}

.report-charts {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
  gap: 24px;
  margin-bottom: 32px;
}

.chart-item {
  background: #fafafa;
  border-radius: 8px;
  padding: 20px;
}

.chart-item.full-width {
  grid-column: 1 / -1;
}

.chart-item h4 {
  font-size: 16px;
  font-weight: 600;
  color: #333;
  margin: 0 0 16px 0;
  text-align: center;
}

.chart-container {
  height: 300px;
  width: 100%;
}

.report-table {
  background: white;
  border-radius: 8px;
  overflow: hidden;
}

.work-hours {
  font-weight: 500;
  color: #1890ff;
}

.overtime-hours {
  font-weight: 500;
  color: #faad14;
}

.no-report {
  text-align: center;
  padding: 80px 20px;
}

@container (max-width: 768px) {
  .main-content {
    padding: 24px 16px;
  }
  
  .filter-row {
    flex-direction: column;
    align-items: stretch;
  }
  
  .filter-group {
    flex-direction: column;
    align-items: flex-start;
  }
  
  .filter-actions {
    margin-left: 0;
    justify-content: center;
  }
  
  .report-header {
    flex-direction: column;
    gap: 16px;
  }
  
  .report-summary {
    flex-direction: column;
    gap: 16px;
  }
  
  .report-charts {
    grid-template-columns: 1fr;
  }
}
</style>