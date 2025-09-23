<template>
  <el-dialog
    v-model="visible"
    :title="dialogTitle"
    width="620px"
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

      <el-row :gutter="20">
        <el-col :span="12">
          <el-form-item label="小组" prop="group_id">
            <el-input
              v-model="groupIdInput"
              placeholder="输入正整数，留空则未分组"
              maxlength="5"
            />
          </el-form-item>
        </el-col>
        <el-col :span="12">
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
        </el-col>
      </el-row>

      <el-form-item v-if="!isEditMode" label="初始密码" prop="password">
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
          {{ submitButtonText }}
        </el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, reactive, computed, watch } from 'vue'
import { ElMessage } from 'element-plus'
import type { FormInstance, FormRules } from 'element-plus'
import { MembersApi } from '@/api/members'
import type { Member, MemberCreateRequest, MemberUpdateRequest } from '@/api/members'

// Props
interface Props {
  visible: boolean
  mode?: 'create' | 'edit'
  member?: Member | null
}

interface Emits {
  (e: 'update:visible', visible: boolean): void
  (e: 'success', payload?: Member): void
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
  group_id: null,
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
  join_date: [{ required: true, message: '请选择入职日期', trigger: 'change' }],
  group_id: [
    {
      validator: (_rule, value, callback) => {
        if (value === null || value === undefined || value === '') {
          callback()
          return
        }
        if (!Number.isInteger(value) || value < 1) {
          callback(new Error('小组编号必须为正整数'))
          return
        }
        callback()
      },
      trigger: 'blur'
    }
  ]
}

// Computed
const visible = computed({
  get: () => props.visible,
  set: value => emit('update:visible', value)
})

const mode = computed(() => props.mode ?? 'create')
const isEditMode = computed(() => mode.value === 'edit')

const dialogTitle = computed(() =>
  isEditMode.value ? '编辑成员' : '新增成员'
)

const submitButtonText = computed(() =>
  isEditMode.value ? '保存修改' : '确认创建'
)

const groupIdInput = computed({
  get: () => (form.group_id ? String(form.group_id) : ''),
  set: value => {
    const normalized = value?.trim() ?? ''
    if (!normalized) {
      form.group_id = null
      return
    }
    const digits = normalized.replace(/[^0-9]/g, '')
    form.group_id = digits ? Number(digits) : null
  }
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
    group_id: null,
    join_date: new Date().toISOString().split('T')[0],
    role: 'member',
    is_active: true,
    password: '123456'
  })
}

const populateForm = (member: Member) => {
  Object.assign(form, {
    username: member.username,
    name: member.name,
    student_id: member.student_id || '',
    phone: member.phone || '',
    department: member.department || '信息化建设处',
    class_name: member.class_name,
    group_id: member.group_id ?? null,
    join_date: member.join_date || new Date().toISOString().split('T')[0],
    role: member.role || 'member',
    is_active: member.is_active,
    password: '123456'
  })
}

const handleSubmit = async () => {
  if (!formRef.value) return

  try {
    await formRef.value.validate()
    loading.value = true

    if (isEditMode.value) {
      if (!props.member) {
        throw new Error('未找到待编辑的成员信息')
      }

      const normalizedStudentId = form.student_id?.trim() ?? ''
      const normalizedPhone = form.phone?.trim() ?? ''
      const normalizedDepartment = form.department?.trim() ?? ''

      const submitData: MemberUpdateRequest = {
        username: form.username.trim(),
        name: form.name.trim(),
        student_id: normalizedStudentId ? normalizedStudentId : null,
        phone: normalizedPhone || undefined,
        department: normalizedDepartment || undefined,
        class_name: form.class_name.trim(),
        group_id: form.group_id ?? null,
        role: form.role,
        is_active: form.is_active
      }

      const updatedMember = await MembersApi.updateMember(
        props.member.id,
        submitData
      )

      ElMessage.success('成员信息更新成功')
      emit('success', updatedMember)
      handleClose()
    } else {
      const normalizedStudentId = form.student_id?.trim() ?? ''
      const normalizedPhone = form.phone?.trim() ?? ''
      const normalizedDepartment = form.department?.trim() ?? ''

      const submitData: MemberCreateRequest = {
        username: form.username.trim(),
        name: form.name.trim(),
        student_id: normalizedStudentId || undefined,
        phone: normalizedPhone || undefined,
        department: normalizedDepartment || undefined,
        class_name: form.class_name.trim(),
        group_id: form.group_id ?? null,
        join_date: form.join_date,
        role: form.role,
        is_active: form.is_active,
        password: form.password?.trim() || '123456'
      }

      const createdMember = await MembersApi.createMember(submitData)

      ElMessage.success('成员创建成功')
      emit('success', createdMember)
      handleClose()
    }
  } catch (error) {
    console.error('保存成员失败:', error)
    ElMessage.error(isEditMode.value ? '更新成员失败，请重试' : '创建成员失败，请重试')
  } finally {
    loading.value = false
  }
}

// Watch for visibility changes to reset form
watch(
  () => props.visible,
  newVal => {
    if (newVal) {
      if (isEditMode.value && props.member) {
        populateForm(props.member)
      } else {
        resetForm()
      }
    }
  }
)

watch(
  () => props.member,
  newMember => {
    if (visible.value && newMember && isEditMode.value) {
      populateForm(newMember)
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
