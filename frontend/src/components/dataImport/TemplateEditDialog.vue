<template>
  <el-dialog
    v-model="dialogVisible"
    :title="isEdit ? '编辑模板' : '新建模板'"
    width="600px"
    @close="handleClose"
  >
    <el-form :model="form" :rules="rules" ref="formRef" label-width="100px">
      <el-form-item label="模板名称" prop="name">
        <el-input v-model="form.name" placeholder="请输入模板名称" />
      </el-form-item>

      <el-form-item label="模板描述" prop="description">
        <el-input
          v-model="form.description"
          type="textarea"
          :rows="3"
          placeholder="请输入模板描述"
        />
      </el-form-item>

      <el-form-item label="数据类型" prop="type">
        <el-select v-model="form.type" placeholder="请选择数据类型" style="width: 100%">
          <el-option label="维修任务" value="repair_tasks" />
          <el-option label="监控任务" value="monitoring_tasks" />
          <el-option label="协助任务" value="assistance_tasks" />
          <el-option label="成员信息" value="members" />
          <el-option label="考勤记录" value="attendance" />
          <el-option label="工时记录" value="work_hours" />
        </el-select>
      </el-form-item>

      <el-form-item label="必填字段" prop="requiredFields">
        <el-select
          v-model="form.requiredFields"
          multiple
          filterable
          allow-create
          placeholder="请选择或输入必填字段"
          style="width: 100%"
        >
          <el-option
            v-for="field in availableFields"
            :key="field"
            :label="field"
            :value="field"
          />
        </el-select>
      </el-form-item>

      <el-form-item label="可选字段" prop="optionalFields">
        <el-select
          v-model="form.optionalFields"
          multiple
          filterable
          allow-create
          placeholder="请选择或输入可选字段"
          style="width: 100%"
        >
          <el-option
            v-for="field in availableFields"
            :key="field"
            :label="field"
            :value="field"
          />
        </el-select>
      </el-form-item>
    </el-form>

    <template #footer>
      <div class="dialog-footer">
        <el-button @click="handleClose">取消</el-button>
        <el-button type="primary" @click="handleSubmit" :loading="loading">
          {{ isEdit ? '更新' : '创建' }}
        </el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, reactive, computed, watch } from 'vue'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'
import { dataImportApi } from '@/api/dataImport'
import type { ImportTemplate } from '@/types/dataImport'

interface Props {
  visible: boolean
  template?: ImportTemplate | null
}

interface Emits {
  (e: 'update:visible', value: boolean): void
  (e: 'success'): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

const dialogVisible = ref(false)
const loading = ref(false)
const formRef = ref<FormInstance>()

const form = reactive({
  name: '',
  description: '',
  type: '',
  requiredFields: [] as string[],
  optionalFields: [] as string[]
})

const rules: FormRules = {
  name: [
    { required: true, message: '请输入模板名称', trigger: 'blur' }
  ],
  description: [
    { required: true, message: '请输入模板描述', trigger: 'blur' }
  ],
  type: [
    { required: true, message: '请选择数据类型', trigger: 'change' }
  ],
  requiredFields: [
    { required: true, type: 'array', min: 1, message: '请至少选择一个必填字段', trigger: 'change' }
  ]
}

const isEdit = computed(() => !!props.template)

const availableFields = [
  'id', 'name', 'title', 'description', 'type', 'status', 'priority',
  'assignee', 'reporter', 'department', 'location', 'phone', 'email',
  'start_time', 'end_time', 'created_at', 'updated_at', 'completed_at',
  'work_hours', 'base_hours', 'bonus_hours', 'penalty_hours'
]

watch(() => props.visible, (visible) => {
  dialogVisible.value = visible
  if (visible) {
    if (props.template) {
      Object.assign(form, {
        name: props.template.name,
        description: props.template.description,
        type: props.template.type,
        requiredFields: [...props.template.requiredFields],
        optionalFields: [...props.template.optionalFields]
      })
    } else {
      resetForm()
    }
  }
})

watch(dialogVisible, (visible) => {
  emit('update:visible', visible)
})

const resetForm = () => {
  Object.assign(form, {
    name: '',
    description: '',
    type: '',
    requiredFields: [],
    optionalFields: []
  })
}

const handleSubmit = async () => {
  if (!formRef.value) return

  try {
    await formRef.value.validate()
    loading.value = true

    const templateData = {
      name: form.name,
      description: form.description,
      type: form.type as any,
      requiredFields: form.requiredFields,
      optionalFields: form.optionalFields,
      sampleData: [],
      validationRules: []
    }

    if (isEdit.value && props.template) {
      await dataImportApi.updateImportTemplate(props.template.id, templateData)
    } else {
      await dataImportApi.createImportTemplate(templateData)
    }

    emit('success')
    handleClose()
  } catch (error) {
    console.error('模板操作失败:', error)
    ElMessage.error('模板操作失败')
  } finally {
    loading.value = false
  }
}

const handleClose = () => {
  dialogVisible.value = false
  resetForm()
  loading.value = false
}
</script>

<style lang="scss" scoped>
.dialog-footer {
  text-align: right;
}
</style>