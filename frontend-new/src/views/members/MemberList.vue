<template>
  <div class="desktop-member-list">
    <div class="page-header">
      <div class="header-content">
        <div class="header-text">
          <h1>成员管理</h1>
          <p>管理团队成员信息和权限设置</p>
        </div>
        <div class="header-actions">
          <a-button type="primary" :icon="h(UserAddOutlined)" @click="showCreateModal = true">
            添加成员
          </a-button>
          <a-button :icon="h(ImportOutlined)" @click="showImportModal = true">
            导入成员
          </a-button>
          <a-button :icon="h(ReloadOutlined)" @click="refreshMembers" :loading="loading">
            刷新
          </a-button>
        </div>
      </div>
    </div>
    
    <div class="desktop-member-panel">
      <div class="panel-header">
        <div class="filter-section">
          <a-input-search
            v-model:value="searchText"
            placeholder="搜索成员姓名、学号、部门..."
            style="width: 300px"
            @search="handleSearch"
            :loading="loading"
          />
          
          <a-select
            v-model:value="roleFilter"
            placeholder="角色筛选"
            style="width: 140px"
            @change="handleRoleChange"
          >
            <a-select-option value="">全部角色</a-select-option>
            <a-select-option value="admin">管理员</a-select-option>
            <a-select-option value="member">普通成员</a-select-option>
          </a-select>
          
          <a-select
            v-model:value="statusFilter"
            placeholder="状态筛选"
            style="width: 120px"
            @change="handleStatusChange"
          >
            <a-select-option value="">全部状态</a-select-option>
            <a-select-option value="true">在职</a-select-option>
            <a-select-option value="false">离职</a-select-option>
          </a-select>

          <a-select
            v-model:value="departmentFilter"
            placeholder="部门筛选"
            style="width: 140px"
            @change="handleDepartmentChange"
          >
            <a-select-option value="">全部部门</a-select-option>
            <a-select-option value="网络部">网络部</a-select-option>
            <a-select-option value="技术部">技术部</a-select-option>
            <a-select-option value="维修部">维修部</a-select-option>
          </a-select>
        </div>
        
        <div class="summary-info">
          <a-statistic title="总成员" :value="total" />
          <a-statistic title="在职" :value="getActiveCount()" />
          <a-statistic title="离职" :value="getInactiveCount()" />
        </div>
      </div>

      <a-table
        :columns="columns"
        :data-source="members"
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
        <template #avatar="{ record }">
          <a-avatar :size="40" :style="{ backgroundColor: getAvatarColor(record.name) }">
            {{ record.name.charAt(0) }}
          </a-avatar>
        </template>

        <template #role="{ text }">
          <a-tag :color="getRoleColor(text)">
            {{ getRoleText(text) }}
          </a-tag>
        </template>
        
        <template #status="{ text }">
          <a-tag :color="text ? 'green' : 'red'">
            {{ text ? '在职' : '离职' }}
          </a-tag>
        </template>
        
        <template #actions="{ record }">
          <a-space>
            <a-tooltip title="查看详情">
              <a-button size="small" :icon="h(EyeOutlined)" @click="viewMember(record)" />
            </a-tooltip>
            <a-tooltip title="编辑成员">
              <a-button size="small" :icon="h(EditOutlined)" @click="editMember(record)" />
            </a-tooltip>
            <a-tooltip :title="record.isActive ? '设为离职' : '设为在职'">
              <a-button 
                size="small" 
                :icon="h(record.isActive ? UserDeleteOutlined : UserAddOutlined)"
                @click="toggleMemberStatus(record)"
              />
            </a-tooltip>
            <a-tooltip title="重置密码">
              <a-button
                size="small"
                :icon="h(KeyOutlined)"
                @click="resetPassword(record)"
              />
            </a-tooltip>
          </a-space>
        </template>
      </a-table>
    </div>

    <!-- 创建成员模态框 -->
    <a-modal
      v-model:visible="showCreateModal"
      title="添加成员"
      width="600px"
      @ok="handleCreateSubmit"
      @cancel="handleCreateCancel"
      :confirmLoading="createLoading"
    >
      <a-form
        :model="createForm"
        :rules="createRules"
        ref="createFormRef"
        layout="vertical"
        class="member-form"
      >
        <a-row :gutter="16">
          <a-col :span="12">
            <a-form-item name="name" label="姓名" required>
              <a-input v-model:value="createForm.name" placeholder="请输入姓名" />
            </a-form-item>
          </a-col>
          <a-col :span="12">
            <a-form-item name="studentId" label="学号" required>
              <a-input v-model:value="createForm.studentId" placeholder="请输入学号" />
            </a-form-item>
          </a-col>
        </a-row>
        
        <a-row :gutter="16">
          <a-col :span="12">
            <a-form-item name="username" label="用户名" required>
              <a-input v-model:value="createForm.username" placeholder="请输入用户名" />
            </a-form-item>
          </a-col>
          <a-col :span="12">
            <a-form-item name="password" label="密码" required>
              <a-input-password v-model:value="createForm.password" placeholder="请输入密码" />
            </a-form-item>
          </a-col>
        </a-row>

        <a-row :gutter="16">
          <a-col :span="12">
            <a-form-item name="phone" label="手机号" required>
              <a-input v-model:value="createForm.phone" placeholder="请输入手机号" />
            </a-form-item>
          </a-col>
          <a-col :span="12">
            <a-form-item name="role" label="角色" required>
              <a-select v-model:value="createForm.role" placeholder="选择角色">
                <a-select-option value="admin">管理员</a-select-option>
                <a-select-option value="member">普通成员</a-select-option>
              </a-select>
            </a-form-item>
          </a-col>
        </a-row>

        <a-row :gutter="16">
          <a-col :span="12">
            <a-form-item name="department" label="部门" required>
              <a-input v-model:value="createForm.department" placeholder="请输入部门" />
            </a-form-item>
          </a-col>
          <a-col :span="12">
            <a-form-item name="className" label="班级" required>
              <a-input v-model:value="createForm.className" placeholder="请输入班级" />
            </a-form-item>
          </a-col>
        </a-row>

        <a-row :gutter="16">
          <a-col :span="12">
            <a-form-item name="joinDate" label="入职日期" required>
              <a-date-picker 
                v-model:value="createForm.joinDate"
                placeholder="选择入职日期"
                style="width: 100%"
              />
            </a-form-item>
          </a-col>
          <a-col :span="12">
            <a-form-item name="isActive" label="状态">
              <a-switch 
                v-model:checked="createForm.isActive"
                checked-children="在职"
                un-checked-children="离职"
              />
            </a-form-item>
          </a-col>
        </a-row>
      </a-form>
    </a-modal>

    <!-- 导入成员模态框占位 -->
    <a-modal
      v-model:visible="showImportModal"
      title="导入成员"
      width="800px"
      footer=""
    >
      <p>导入功能将在 MemberImport.vue 中实现</p>
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, h } from 'vue'
import { message, Modal } from 'ant-design-vue'
import { api, type Member } from '@/api/client'
import dayjs, { type Dayjs } from 'dayjs'
import {
  UserAddOutlined,
  ImportOutlined,
  ReloadOutlined,
  EyeOutlined,
  EditOutlined,
  UserDeleteOutlined,
  KeyOutlined
} from '@ant-design/icons-vue'

// 响应式数据
const members = ref<Member[]>([])
const total = ref(0)
const loading = ref(false)
const searchText = ref('')
const roleFilter = ref('')
const statusFilter = ref('')
const departmentFilter = ref('')

// 模态框状态
const showCreateModal = ref(false)
const showImportModal = ref(false)
const createLoading = ref(false)

// 表单引用
const createFormRef = ref()

// 分页和筛选参数
const filters = reactive({
  page: 1,
  pageSize: 10,
  search: '',
  role: '',
  isActive: undefined as boolean | undefined,
  department: '',
  className: ''
})

// 创建表单数据
const createForm = reactive({
  name: '',
  studentId: '',
  username: '',
  password: '',
  phone: '',
  role: 'member',
  department: '',
  className: '',
  joinDate: dayjs() as Dayjs,
  isActive: true
})

// 表单验证规则
const createRules = {
  name: [
    { required: true, message: '请输入姓名', trigger: 'blur' },
    { min: 2, max: 20, message: '姓名长度应为2-20字符', trigger: 'blur' }
  ],
  studentId: [
    { required: true, message: '请输入学号', trigger: 'blur' },
    { pattern: /^\d{8,12}$/, message: '学号应为8-12位数字', trigger: 'blur' }
  ],
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 20, message: '用户名长度应为3-20字符', trigger: 'blur' },
    { pattern: /^[a-zA-Z0-9_]+$/, message: '用户名只能包含字母、数字和下划线', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, max: 20, message: '密码长度应为6-20字符', trigger: 'blur' }
  ],
  phone: [
    { required: true, message: '请输入手机号', trigger: 'blur' },
    { pattern: /^1[3-9]\d{9}$/, message: '请输入正确的手机号码', trigger: 'blur' }
  ],
  role: [
    { required: true, message: '请选择角色', trigger: 'change' }
  ],
  department: [
    { required: true, message: '请输入部门', trigger: 'blur' },
    { max: 50, message: '部门名称不能超过50字符', trigger: 'blur' }
  ],
  className: [
    { required: true, message: '请输入班级', trigger: 'blur' },
    { max: 50, message: '班级名称不能超过50字符', trigger: 'blur' }
  ],
  joinDate: [
    { required: true, message: '请选择入职日期', trigger: 'change' }
  ]
}

// 表格列定义
const columns = [
  {
    title: '头像',
    key: 'avatar',
    width: 80,
    slots: { customRender: 'avatar' }
  },
  {
    title: '基本信息',
    key: 'basicInfo',
    width: 200,
    customRender: ({ record }: any) => h('div', { class: 'member-info-cell' }, [
      h('div', { class: 'member-name' }, record.name),
      h('div', { class: 'member-detail' }, `${record.studentId} | ${record.username}`)
    ])
  },
  {
    title: '角色',
    dataIndex: 'role',
    key: 'role',
    width: 100,
    slots: { customRender: 'role' }
  },
  {
    title: '部门班级',
    key: 'deptClass',
    width: 150,
    customRender: ({ record }: any) => h('div', { class: 'dept-class-cell' }, [
      h('div', { class: 'dept-name' }, record.department),
      h('div', { class: 'class-name' }, record.className)
    ])
  },
  {
    title: '联系方式',
    dataIndex: 'phone',
    key: 'phone',
    width: 130
  },
  {
    title: '状态',
    dataIndex: 'isActive',
    key: 'status',
    width: 100,
    slots: { customRender: 'status' }
  },
  {
    title: '入职日期',
    key: 'joinDate',
    width: 120,
    customRender: ({ record }: any) => {
      return record.joinDate ? dayjs(record.joinDate).format('YYYY-MM-DD') : '未设置'
    }
  },
  {
    title: '操作',
    key: 'actions',
    width: 180,
    fixed: 'right',
    slots: { customRender: 'actions' }
  }
]

// 计算属性
const getActiveCount = () => {
  return members.value.filter(member => member.isActive).length
}

const getInactiveCount = () => {
  return members.value.filter(member => !member.isActive).length
}

// 工具方法
const getAvatarColor = (name: string) => {
  const colors = ['#f56565', '#ed8936', '#ecc94b', '#48bb78', '#38b2ac', '#4299e1', '#667eea', '#9f7aea']
  const index = name.charCodeAt(0) % colors.length
  return colors[index]
}

const getRoleColor = (role: string) => {
  const colors: Record<string, string> = {
    admin: 'red',
    member: 'blue'
  }
  return colors[role] || 'default'
}

const getRoleText = (role: string) => {
  const texts: Record<string, string> = {
    admin: '管理员',
    member: '普通成员'
  }
  return texts[role] || role
}

// API 调用方法
const fetchMembers = async () => {
  try {
    loading.value = true
    const params = {
      page: filters.page,
      pageSize: filters.pageSize,
      search: filters.search || undefined,
      role: filters.role || undefined,
      isActive: filters.isActive,
      department: filters.department || undefined,
      className: filters.className || undefined
    }
    
    const response = await api.getMembers(params)
    if (response.success && response.data) {
      members.value = response.data.items || []
      total.value = response.data.total || 0
    } else {
      message.error(response.message || '获取成员列表失败')
    }
  } catch (error: any) {
    console.error('Fetch members error:', error)
    message.error(error.message || '获取成员列表失败，请检查网络连接')
  } finally {
    loading.value = false
  }
}

// 事件处理方法
const handleSearch = () => {
  filters.search = searchText.value
  filters.page = 1
  fetchMembers()
}

const handleRoleChange = () => {
  filters.role = roleFilter.value
  filters.page = 1
  fetchMembers()
}

const handleStatusChange = () => {
  filters.isActive = statusFilter.value === '' ? undefined : statusFilter.value === 'true'
  filters.page = 1
  fetchMembers()
}

const handleDepartmentChange = () => {
  filters.department = departmentFilter.value
  filters.page = 1
  fetchMembers()
}

const refreshMembers = () => {
  fetchMembers()
}

const handlePageChange = (page: number) => {
  filters.page = page
  fetchMembers()
}

const handlePageSizeChange = (_current: number, size: number) => {
  filters.pageSize = size
  filters.page = 1
  fetchMembers()
}

// 成员操作方法
const viewMember = (member: Member) => {
  message.info(`查看成员详情: ${member.name}`)
}

const editMember = (member: Member) => {
  message.info(`编辑成员: ${member.name}`)
}

const toggleMemberStatus = async (member: Member) => {
  const action = member.isActive ? '设为离职' : '设为在职'
  Modal.confirm({
    title: `确认${action}`,
    content: `确定要将 ${member.name} ${action}吗？`,
    onOk: async () => {
      try {
        message.success(`${member.name} 已${action}`)
        refreshMembers()
      } catch (error: any) {
        message.error(error.message || `${action}失败`)
      }
    }
  })
}

const resetPassword = async (member: Member) => {
  Modal.confirm({
    title: '确认重置密码',
    content: `确定要重置 ${member.name} 的密码吗？新密码将通过系统消息发送。`,
    onOk: async () => {
      try {
        message.success(`${member.name} 的密码已重置`)
      } catch (error: any) {
        message.error(error.message || '重置密码失败')
      }
    }
  })
}

// 创建成员相关方法
const handleCreateSubmit = async () => {
  try {
    await createFormRef.value.validate()
    createLoading.value = true
    
    const memberData = {
      name: createForm.name,
      studentId: createForm.studentId,
      username: createForm.username,
      password: createForm.password,
      phone: createForm.phone,
      role: createForm.role,
      department: createForm.department,
      className: createForm.className,
      joinDate: createForm.joinDate.format('YYYY-MM-DD'),
      isActive: createForm.isActive
    }
    
    const response = await api.createMember(memberData)
    if (response.success) {
      message.success(response.message || '成员创建成功')
      showCreateModal.value = false
      resetCreateForm()
      refreshMembers()
    } else {
      message.error(response.message || '成员创建失败')
    }
  } catch (error: any) {
    if (error.errorFields) {
      return
    }
    console.error('Create member error:', error)
    message.error(error.message || '成员创建失败，请检查网络连接')
  } finally {
    createLoading.value = false
  }
}

const handleCreateCancel = () => {
  showCreateModal.value = false
  resetCreateForm()
}

const resetCreateForm = () => {
  createFormRef.value?.resetFields()
  Object.assign(createForm, {
    name: '',
    studentId: '',
    username: '',
    password: '',
    phone: '',
    role: 'member',
    department: '',
    className: '',
    joinDate: dayjs(),
    isActive: true
  })
}

// 生命周期
onMounted(() => {
  fetchMembers()
})
</script>

<style scoped>
/* 桌面端成员管理界面样式 */
.desktop-member-list {
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

.desktop-member-panel {
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

/* 成员信息单元格样式 */
.member-info-cell {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.member-name {
  font-size: 14px;
  font-weight: 500;
  color: #1a1a1a;
  line-height: 1.4;
}

.member-detail {
  font-size: 12px;
  color: #8c8c8c;
  line-height: 1.3;
}

.dept-class-cell {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.dept-name {
  font-size: 13px;
  font-weight: 500;
  color: #1a1a1a;
}

.class-name {
  font-size: 12px;
  color: #8c8c8c;
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

/* 模态框表单样式 */
.member-form :deep(.ant-form-item-label > label) {
  font-size: 14px;
  font-weight: 500;
  color: #262626;
}

.member-form :deep(.ant-input),
.member-form :deep(.ant-select-selector),
.member-form :deep(.ant-picker) {
  border-radius: 6px;
  border: 1px solid #d9d9d9;
}

.member-form :deep(.ant-input:hover),
.member-form :deep(.ant-select:hover .ant-select-selector),
.member-form :deep(.ant-picker:hover) {
  border-color: #667eea;
}

.member-form :deep(.ant-input:focus),
.member-form :deep(.ant-select-focused .ant-select-selector),
.member-form :deep(.ant-picker-focused) {
  border-color: #667eea;
  box-shadow: 0 0 0 2px rgba(102, 126, 234, 0.1);
}

/* 分页样式优化 */
:deep(.ant-pagination) {
  margin: 24px 0 0;
  padding: 0 32px 24px;
}

:deep(.ant-pagination-options) {
  margin-left: auto;
}

/* 头像样式 */
:deep(.ant-avatar) {
  font-weight: 600;
  font-size: 16px;
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
  }
  
  .header-actions {
    flex-direction: column;
    width: 100%;
  }
}
</style>