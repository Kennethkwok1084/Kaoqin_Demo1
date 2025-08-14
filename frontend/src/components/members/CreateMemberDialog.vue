<template>
  <el-dialog
    v-model="visible"
    title="新增成员"
    width="600px"
    :before-close="handleClose"
    destroy-on-close
  >
    <el-form
      ref="formRef"
      :model="form"
      :rules="rules"
      label-width="100px"
      label-position="right"
    >
      <el-row :gutter="20">
        <el-col :span="12">
          <el-form-item label="用户名" prop="username">
            <el-input
              v-model="form.username"
              placeholder="用于登录的用户名"
              maxlength="50"
              show-word-limit
            />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="姓名" prop="name">
            <el-input
              v-model="form.name"
              placeholder="真实姓名"
              maxlength="50"
              show-word-limit
            />
          </el-form-item>
        </el-col>
      </el-row>

      <el-row :gutter="20">
        <el-col :span="12">
          <el-form-item label="学号" prop="student_id">
            <el-input
              v-model="form.student_id"
              placeholder="员工号/学号（可选，纯数字）"
              maxlength="20"
              show-word-limit
            />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="手机号" prop="phone">
            <el-input
              v-model="form.phone"
              placeholder="11位手机号（可选）"
              maxlength="11"
              show-word-limit
            />
          </el-form-item>
        </el-col>
      </el-row>

      <el-row :gutter="20">
        <el-col :span="12">
          <el-form-item label="角色" prop="role">
            <el-select
              v-model="form.role"
              placeholder="选择角色"
              style="width: 100%"
            >
              <el-option label="管理员" value="admin" />
              <el-option label="组长" value="group_leader" />
              <el-option label="成员" value="member" />
              <el-option label="访客" value="guest" />
            </el-select>
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="状态" prop="is_active">
            <el-select
              v-model="form.is_active"
              placeholder="选择状态"
              style="width: 100%"
            >
              <el-option label="在职" :value="true" />
              <el-option label="离职" :value="false" />
            </el-select>
          </el-form-item>
        </el-col>
      </el-row>

      <el-row :gutter="20">
        <el-col :span="12">
          <el-form-item label="部门" prop="department">
            <el-input
              v-model="form.department"
              placeholder="默认：信息化建设处"
            />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="班级" prop="class_name">
            <el-input
              v-model="form.class_name"
              placeholder="班级名称（必填）"
              maxlength="100"
              show-word-limit
            />
          </el-form-item>
        </el-col>
      </el-row>

      <el-form-item label="入职日期" prop="join_date">
        <el-date-picker
          v-model="form.join_date"
          type="date"
          placeholder="选择入职日期"
          format="YYYY-MM-DD"
          value-format="YYYY-MM-DD"
          style="width: 100%"
        />
      </el-form-item>

      <el-form-item label="初始密码" prop="password">
        <el-input
          v-model="form.password"
          type="password"
          placeholder="初始密码（默认：123456）"
          show-password
          maxlength="50"
        />
      </el-form-item>
    </el-form>

    <template #footer>
      <div class="dialog-footer">
        <el-button @click="handleClose">取消</el-button>
        <el-button type="primary" :loading="loading" @click="handleSubmit">
          确认创建
        </el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, reactive, computed, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import type { FormInstance, FormRules } from 'element-plus'
import { MembersApi } from '@/api/members'
import type { MemberCreateRequest } from '@/api/members'

// Props
interface Props {
  visible: boolean
}

// Emits
interface Emits {
  (e: 'update:visible', visible: boolean): void
  (e: 'success'): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

// Refs
const formRef = ref<FormInstance>()
const loading = ref(false)

// Form data
const form = reactive<MemberCreateRequest>({
  username: '',
  name: '',
  student_id: '',
  phone: '',
  department: '信息化建设处',
  class_name: '',
  join_date: new Date().toISOString().split('T')[0],
  role: 'member',
  is_active: true,
  password: '123456'
})

// Form rules
const rules: FormRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    {
      pattern: /^[a-zA-Z0-9_]+$/,
      message: '用户名只能包含字母、数字和下划线',
      trigger: 'blur'
    }
  ],
  name: [
    { required: true, message: '请输入姓名', trigger: 'blur' },
    {
      pattern: /^[\u4e00-\u9fa5a-zA-Z·\s]+$/,
      message: '姓名只能包含中文、字母、·和空格',
      trigger: 'blur'
    }
  ],
  student_id: [
    {
      pattern: /^\d+$/,
      message: '学号只能包含数字',
      trigger: 'blur'
    }
  ],
  phone: [
    {
      pattern: /^1[3-9]\d{9}$/,
      message: '请输入正确的手机号',
      trigger: 'blur'
    }
  ],
  role: [{ required: true, message: '请选择角色', trigger: 'change' }],
  is_active: [{ required: true, message: '请选择状态', trigger: 'change' }],
  class_name: [{ required: true, message: '请输入班级', trigger: 'blur' }],
  join_date: [{ required: true, message: '请选择入职日期', trigger: 'change' }]
}

// Computed
const visible = computed({
  get: () => props.visible,
  set: value => emit('update:visible', value)
})

// Methods
const handleClose = () => {
  emit('update:visible', false)
  resetForm()
}

const resetForm = () => {
  formRef.value?.resetFields()
  Object.assign(form, {
    username: '',
    name: '',
    student_id: '',
    phone: '',
    department: '信息化建设处',
    class_name: '',
    join_date: new Date().toISOString().split('T')[0],
    role: 'member',
    is_active: true,
    password: '123456'
  })
}

const handleSubmit = async () => {
  if (!formRef.value) return

  try {
    await formRef.value.validate()
    loading.value = true

    // 准备提交数据
    const submitData = { ...form }

    // 如果手机号为空，删除该字段
    if (!submitData.phone?.trim()) {
      delete submitData.phone
    }

    // 如果学号为空，删除该字段
    if (!submitData.student_id?.trim()) {
      delete submitData.student_id
    }

    await MembersApi.createMember(submitData)

    ElMessage.success('成员创建成功')
    emit('success')
    handleClose()
  } catch (error) {
    console.error('创建成员失败:', error)
    ElMessage.error('创建成员失败，请重试')
  } finally {
    loading.value = false
  }
}

// Watch for visibility changes to reset form
watch(
  () => props.visible,
  newVal => {
    if (newVal) {
      resetForm()
    }
  }
)
</script>

<style scoped>
.dialog-footer {
  text-align: right;
}

:deep(.el-form-item__label) {
  font-weight: 500;
}

:deep(.el-input__count) {
  color: #909399;
  font-size: 12px;
}
</style>
