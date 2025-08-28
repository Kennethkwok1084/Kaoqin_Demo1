<template>
  <el-dialog
    v-model="dialogVisible"
    title="模板详情"
    width="700px"
    @close="handleClose"
  >
    <div class="template-detail" v-if="template">
      <el-descriptions :column="2" border>
        <el-descriptions-item label="模板名称">
          {{ template.name }}
        </el-descriptions-item>
        <el-descriptions-item label="数据类型">
          <el-tag :type="getTypeColor(template.type) as any">
            {{ getTypeText(template.type) }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="创建时间">
          {{ formatDateTime(template.createdAt) }}
        </el-descriptions-item>
        <el-descriptions-item label="更新时间">
          {{ formatDateTime(template.updatedAt) }}
        </el-descriptions-item>
        <el-descriptions-item label="模板描述" :span="2">
          {{ template.description }}
        </el-descriptions-item>
      </el-descriptions>

      <el-divider />

      <div class="fields-section">
        <h4>字段配置</h4>
        <el-row :gutter="20">
          <el-col :span="12">
            <div class="field-group">
              <h5>必填字段 ({{ template.requiredFields.length }})</h5>
              <div class="field-list">
                <el-tag
                  v-for="field in template.requiredFields"
                  :key="field"
                  type="danger"
                  class="field-tag"
                >
                  {{ field }}
                </el-tag>
              </div>
            </div>
          </el-col>
          <el-col :span="12">
            <div class="field-group">
              <h5>可选字段 ({{ template.optionalFields.length }})</h5>
              <div class="field-list">
                <el-tag
                  v-for="field in template.optionalFields"
                  :key="field"
                  type="info"
                  class="field-tag"
                >
                  {{ field }}
                </el-tag>
              </div>
            </div>
          </el-col>
        </el-row>
      </div>

      <el-divider />

      <div class="validation-rules" v-if="template.validationRules.length">
        <h4>验证规则</h4>
        <el-table :data="template.validationRules" size="small">
          <el-table-column prop="field" label="字段" width="120" />
          <el-table-column prop="type" label="规则类型" width="100">
            <template #default="{ row }">
              <el-tag size="small">{{ row.type }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="message" label="错误信息" />
        </el-table>
      </div>

      <div class="sample-data" v-if="template.sampleData.length">
        <el-divider />
        <h4>示例数据</h4>
        <el-table :data="template.sampleData.slice(0, 3)" size="small">
          <el-table-column
            v-for="field in getAllFields(template)"
            :key="field"
            :prop="field"
            :label="field"
            show-overflow-tooltip
            width="120"
          />
        </el-table>
        <div class="sample-info">显示前 3 行示例数据</div>
      </div>
    </div>

    <template #footer>
      <div class="dialog-footer">
        <el-button @click="handleClose">关闭</el-button>
        <el-button type="primary" @click="downloadTemplate" v-if="template">
          <el-icon><Download /></el-icon>
          下载模板
        </el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { Download } from '@element-plus/icons-vue'
import { dataImportApi } from '@/api/dataImport'
import type { ImportTemplate } from '@/types/dataImport'

interface Props {
  visible: boolean
  template?: ImportTemplate | null
}

interface Emits {
  (e: 'update:visible', value: boolean): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

const dialogVisible = ref(false)

watch(
  () => props.visible,
  visible => {
    dialogVisible.value = visible
  }
)

watch(dialogVisible, visible => {
  emit('update:visible', visible)
})

const downloadTemplate = async () => {
  if (!props.template) return

  try {
    const blob = await dataImportApi.downloadTemplate(props.template.id, 'xlsx')
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `${props.template.name}_模板.xlsx`
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

const handleClose = () => {
  dialogVisible.value = false
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

const getAllFields = (template: ImportTemplate) => {
  return [...template.requiredFields, ...template.optionalFields]
}

const formatDateTime = (dateStr: string) => {
  return new Date(dateStr).toLocaleString()
}
</script>

<style lang="scss" scoped>
.template-detail {
  .fields-section {
    .field-group {
      h5 {
        margin: 0 0 12px 0;
        color: var(--el-text-color-primary);
      }

      .field-list {
        display: flex;
        flex-wrap: wrap;
        gap: 8px;

        .field-tag {
          margin-bottom: 5px;
        }
      }
    }
  }

  .validation-rules,
  .sample-data {
    h4 {
      margin: 0 0 15px 0;
      color: var(--el-text-color-primary);
    }

    .sample-info {
      margin-top: 10px;
      font-size: 12px;
      color: var(--el-text-color-secondary);
      text-align: center;
    }
  }
}

.dialog-footer {
  text-align: right;
}
</style>
