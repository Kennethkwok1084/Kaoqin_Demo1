<template>
  <el-dialog
    v-model="dialogVisible"
    title="导入模板管理"
    width="900px"
    @close="handleClose"
  >
    <div class="template-manager">
      <div class="manager-header">
        <el-button type="primary" @click="showCreateTemplate = true">
          <el-icon><Plus /></el-icon>
          新建模板
        </el-button>
        <el-button @click="loadTemplates">
          <el-icon><Refresh /></el-icon>
          刷新
        </el-button>
      </div>

      <el-table
        :data="templates"
        v-loading="loading"
        stripe
        style="width: 100%"
      >
        <el-table-column prop="name" label="模板名称" min-width="150" />

        <el-table-column
          prop="description"
          label="描述"
          min-width="200"
          show-overflow-tooltip
        />

        <el-table-column prop="type" label="类型" width="120">
          <template #default="{ row }">
            <el-tag :type="getTypeColor(row.type) as any">
              {{ getTypeText(row.type) }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column label="字段配置" width="150">
          <template #default="{ row }">
            <div class="field-stats">
              <span class="required"
                >必填: {{ row.requiredFields.length }}</span
              >
              <span class="optional"
                >可选: {{ row.optionalFields.length }}</span
              >
            </div>
          </template>
        </el-table-column>

        <el-table-column prop="updatedAt" label="更新时间" width="140">
          <template #default="{ row }">
            {{ formatDate(row.updatedAt) }}
          </template>
        </el-table-column>

        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button-group>
              <el-button size="small" @click="viewTemplate(row)">
                <el-icon><View /></el-icon>
              </el-button>
              <el-button size="small" type="warning" @click="editTemplate(row)">
                <el-icon><Edit /></el-icon>
              </el-button>
              <el-button
                size="small"
                type="success"
                @click="downloadTemplate(row)"
              >
                <el-icon><Download /></el-icon>
              </el-button>
              <el-button
                size="small"
                type="danger"
                @click="deleteTemplate(row)"
              >
                <el-icon><Delete /></el-icon>
              </el-button>
            </el-button-group>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <!-- 创建/编辑模板弹窗 -->
    <TemplateEditDialog
      v-model:visible="showCreateTemplate"
      :template="editingTemplate"
      @success="handleTemplateSuccess"
    />

    <!-- 模板详情弹窗 -->
    <TemplateDetailDialog
      v-model:visible="showTemplateDetail"
      :template="viewingTemplate"
    />

    <template #footer>
      <div class="dialog-footer">
        <el-button @click="handleClose">关闭</el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Plus,
  Refresh,
  View,
  Edit,
  Download,
  Delete
} from '@element-plus/icons-vue'
import { dataImportApi } from '@/api/dataImport'
import type { ImportTemplate } from '@/types/dataImport'
import TemplateEditDialog from './TemplateEditDialog.vue'
import TemplateDetailDialog from './TemplateDetailDialog.vue'

interface Props {
  visible: boolean
}

interface Emits {
  (e: 'update:visible', value: boolean): void
  (e: 'refresh'): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

const dialogVisible = ref(false)
const loading = ref(false)
const templates = ref<ImportTemplate[]>([])
const editingTemplate = ref<ImportTemplate | null>(null)
const viewingTemplate = ref<ImportTemplate | null>(null)

const showCreateTemplate = ref(false)
const showTemplateDetail = ref(false)

watch(
  () => props.visible,
  visible => {
    dialogVisible.value = visible
    if (visible) {
      loadTemplates()
    }
  }
)

watch(dialogVisible, visible => {
  emit('update:visible', visible)
})

onMounted(() => {
  loadTemplates()
})

const loadTemplates = async () => {
  try {
    loading.value = true
    templates.value = await dataImportApi.getImportTemplates()
  } catch (error) {
    console.error('加载模板失败:', error)
    ElMessage.error('加载模板失败')
  } finally {
    loading.value = false
  }
}

const viewTemplate = (template: ImportTemplate) => {
  viewingTemplate.value = template
  showTemplateDetail.value = true
}

const editTemplate = (template: ImportTemplate) => {
  editingTemplate.value = template
  showCreateTemplate.value = true
}

const deleteTemplate = async (template: ImportTemplate) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除模板 "${template.name}" 吗？此操作不可撤销。`,
      '确认删除',
      {
        type: 'warning',
        confirmButtonText: '确认删除',
        cancelButtonText: '取消'
      }
    )

    await dataImportApi.deleteImportTemplate(template.id)
    ElMessage.success('模板删除成功')
    loadTemplates()
    emit('refresh')
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除模板失败:', error)
      ElMessage.error('删除模板失败')
    }
  }
}

const downloadTemplate = async (template: ImportTemplate) => {
  try {
    const blob = await dataImportApi.downloadTemplate(template.id, 'xlsx')
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `${template.name}_模板.xlsx`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(url)

    ElMessage.success('模板下载成功')
  } catch (error) {
    console.error('下载模板失败:', error)
    ElMessage.error('下载模板失败')
  }
}

const handleTemplateSuccess = () => {
  showCreateTemplate.value = false
  editingTemplate.value = null
  loadTemplates()
  emit('refresh')
  ElMessage.success('模板操作成功')
}

const handleClose = () => {
  dialogVisible.value = false
  editingTemplate.value = null
  viewingTemplate.value = null
}

const getTypeColor = (type: string) => {
  const colorMap = {
    repair_tasks: 'danger',
    monitoring_tasks: 'warning',
    assistance_tasks: 'success',
    members: 'info',
    attendance: 'primary',
    work_hours: 'warning'
  }
  return colorMap[type as keyof typeof colorMap] || 'info'
}

const getTypeText = (type: string) => {
  const textMap = {
    repair_tasks: '维修任务',
    monitoring_tasks: '监控任务',
    assistance_tasks: '协助任务',
    members: '成员信息',
    attendance: '考勤记录',
    work_hours: '工时记录'
  }
  return textMap[type as keyof typeof textMap] || type
}

const formatDate = (dateStr: string) => {
  return new Date(dateStr).toLocaleDateString()
}
</script>

<style lang="scss" scoped>
.template-manager {
  .manager-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 20px;
  }

  .field-stats {
    display: flex;
    flex-direction: column;
    gap: 4px;
    font-size: 12px;

    .required {
      color: var(--el-color-danger);
    }

    .optional {
      color: var(--el-color-info);
    }
  }
}

.dialog-footer {
  text-align: right;
}

:deep(.el-button-group) {
  .el-button {
    padding: 5px 8px;
  }
}
</style>
