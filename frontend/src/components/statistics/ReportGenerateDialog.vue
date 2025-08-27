<template>
  <el-dialog
    v-model="dialogVisible"
    title="生成报表"
    width="600px"
    @close="handleClose"
  >
    <el-form :model="form" :rules="rules" ref="formRef" label-width="100px">
      <el-form-item label="报表类型" prop="type">
        <el-select
          v-model="form.type"
          placeholder="请选择报表类型"
          style="width: 100%"
        >
          <el-option label="月度综合报表" value="monthly_comprehensive" />
          <el-option label="工作效率报表" value="efficiency_analysis" />
          <el-option label="考勤统计报表" value="attendance_summary" />
          <el-option label="任务完成报表" value="task_completion" />
          <el-option label="工时统计报表" value="work_hours_summary" />
          <el-option label="部门对比报表" value="department_comparison" />
        </el-select>
      </el-form-item>

      <el-form-item label="时间范围" prop="dateRange">
        <el-date-picker
          v-model="form.dateRange"
          type="monthrange"
          range-separator="至"
          start-placeholder="开始月份"
          end-placeholder="结束月份"
          style="width: 100%"
        />
      </el-form-item>

      <el-form-item label="部门选择" prop="departments">
        <el-select
          v-model="form.departments"
          multiple
          placeholder="请选择部门（不选择则包含所有部门）"
          style="width: 100%"
        >
          <el-option label="网络维护部" value="network_maintenance" />
          <el-option label="系统运维部" value="system_operations" />
          <el-option label="安全管理部" value="security_management" />
          <el-option label="技术支持部" value="technical_support" />
        </el-select>
      </el-form-item>

      <el-form-item label="成员选择" prop="members">
        <el-select
          v-model="form.members"
          multiple
          filterable
          placeholder="请选择成员（不选择则包含所有成员）"
          style="width: 100%"
        >
          <el-option
            v-for="member in members"
            :key="member.id"
            :label="member.name"
            :value="member.id"
          />
        </el-select>
      </el-form-item>

      <el-form-item label="报表格式" prop="format">
        <el-radio-group v-model="form.format">
          <el-radio value="pdf">PDF</el-radio>
          <el-radio value="excel">Excel</el-radio>
          <el-radio value="word">Word</el-radio>
        </el-radio-group>
      </el-form-item>

      <el-form-item label="包含图表">
        <el-checkbox-group v-model="form.includeCharts">
          <el-checkbox value="overview">概览图表</el-checkbox>
          <el-checkbox value="trend">趋势分析</el-checkbox>
          <el-checkbox value="comparison">对比分析</el-checkbox>
          <el-checkbox value="ranking">排名统计</el-checkbox>
        </el-checkbox-group>
      </el-form-item>

      <el-form-item label="报表描述">
        <el-input
          v-model="form.description"
          type="textarea"
          :rows="3"
          placeholder="请输入报表描述（可选）"
        />
      </el-form-item>
    </el-form>

    <template #footer>
      <div class="dialog-footer">
        <el-button @click="handleClose">取消</el-button>
        <el-button type="primary" @click="handleGenerate" :loading="loading">
          生成报表
        </el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, reactive, watch } from 'vue'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'
import { statisticsApi } from '@/api/statistics'
import type { ReportTemplate, Member } from '@/types/statistics'

interface Props {
  visible: boolean
}

interface Emits {
  (e: 'update:visible', value: boolean): void
  (e: 'success', data: any): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

const dialogVisible = ref(false)
const loading = ref(false)
const formRef = ref<FormInstance>()
const members = ref<Member[]>([])

const form = reactive({
  type: '',
  dateRange: [] as Date[],
  departments: [] as string[],
  members: [] as number[],
  format: 'pdf',
  includeCharts: ['overview', 'trend'],
  description: ''
})

const rules: FormRules = {
  type: [{ required: true, message: '请选择报表类型', trigger: 'change' }],
  dateRange: [{ required: true, message: '请选择时间范围', trigger: 'change' }]
}

watch(
  () => props.visible,
  visible => {
    dialogVisible.value = visible
    if (visible) {
      loadMembers()
    }
  }
)

watch(dialogVisible, visible => {
  emit('update:visible', visible)
})

const loadMembers = async () => {
  try {
    // 这里应该调用获取成员列表的API
    // const response = await membersApi.getMembers()
    // members.value = response.data

    // 临时模拟数据
    members.value = [
      { id: 1, name: '张三', department: 'network_maintenance' },
      { id: 2, name: '李四', department: 'system_operations' },
      { id: 3, name: '王五', department: 'security_management' },
      { id: 4, name: '赵六', department: 'technical_support' }
    ] as Member[]
  } catch (error) {
    console.error('加载成员列表失败:', error)
    ElMessage.error('加载成员列表失败')
  }
}

const handleGenerate = async () => {
  if (!formRef.value) return

  try {
    await formRef.value.validate()

    loading.value = true

    const reportData: ReportTemplate = {
      id: Date.now(),
      name: getReportTypeName(form.type),
      type: form.type,
      description: form.description,
      config: {
        dateRange: form.dateRange,
        departments: form.departments,
        members: form.members,
        format: form.format,
        includeCharts: form.includeCharts
      },
      createdAt: new Date(),
      updatedAt: new Date()
    }

    await statisticsApi.generateReport(reportData)

    ElMessage.success('报表生成成功！')
    emit('success', reportData)
    handleClose()
  } catch (error) {
    console.error('生成报表失败:', error)
    ElMessage.error('生成报表失败')
  } finally {
    loading.value = false
  }
}

const getReportTypeName = (type: string): string => {
  const typeMap: Record<string, string> = {
    monthly_comprehensive: '月度综合报表',
    efficiency_analysis: '工作效率报表',
    attendance_summary: '考勤统计报表',
    task_completion: '任务完成报表',
    work_hours_summary: '工时统计报表',
    department_comparison: '部门对比报表'
  }
  return typeMap[type] || '自定义报表'
}

const handleClose = () => {
  dialogVisible.value = false
  formRef.value?.resetFields()
  loading.value = false
}
</script>

<style lang="scss" scoped>
.dialog-footer {
  text-align: right;
}

:deep(.el-checkbox-group) {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}
</style>
