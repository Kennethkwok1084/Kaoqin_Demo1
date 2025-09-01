<template>
  <div class="desktop-permission-management">
    <div class="page-header">
      <div class="header-content">
        <div class="header-text">
          <h1>权限管理</h1>
          <p>管理用户角色和权限设置</p>
        </div>
        <div class="header-actions">
          <a-button 
            type="primary" 
            :icon="h(PlusOutlined)" 
            @click="showCreateRole"
          >
            新建角色
          </a-button>
          <a-button :icon="h(ReloadOutlined)" @click="refreshData" :loading="loading">
            刷新
          </a-button>
        </div>
      </div>
    </div>

    <div class="permission-content">
      <a-row :gutter="24">
        <!-- 角色管理 -->
        <a-col :xs="24" :lg="14">
          <div class="roles-panel">
            <div class="panel-header">
              <h3>角色列表</h3>
              <p>系统中的所有用户角色及其权限配置</p>
            </div>

            <div class="roles-grid">
              <div 
                v-for="role in roles" 
                :key="role.id" 
                class="role-card"
                :class="{ active: selectedRole?.id === role.id }"
                @click="selectRole(role)"
              >
                <div class="role-header">
                  <div class="role-info">
                    <h4>{{ role.name }}</h4>
                    <p>{{ role.description }}</p>
                  </div>
                  <div class="role-stats">
                    <a-tag :color="getRoleColor(role.level)">
                      {{ getRoleLevelText(role.level) }}
                    </a-tag>
                  </div>
                </div>

                <div class="role-details">
                  <div class="detail-item">
                    <span class="detail-label">用户数量:</span>
                    <span class="detail-value">{{ role.userCount || 0 }} 人</span>
                  </div>
                  <div class="detail-item">
                    <span class="detail-label">权限数量:</span>
                    <span class="detail-value">{{ role.permissions?.length || 0 }} 项</span>
                  </div>
                  <div class="detail-item">
                    <span class="detail-label">创建时间:</span>
                    <span class="detail-value">{{ formatDate(role.createdAt) }}</span>
                  </div>
                </div>

                <div class="role-actions">
                  <a-button 
                    size="small" 
                    type="primary" 
                    ghost
                    @click.stop="editRole(role)"
                  >
                    编辑
                  </a-button>
                  <a-button 
                    size="small" 
                    :disabled="role.isSystem"
                    @click.stop="deleteRole(role)"
                  >
                    删除
                  </a-button>
                </div>
              </div>
            </div>
          </div>
        </a-col>

        <!-- 权限详情 -->
        <a-col :xs="24" :lg="10">
          <div class="permissions-panel">
            <div class="panel-header">
              <h3>权限详情</h3>
              <p v-if="selectedRole">{{ selectedRole.name }} 的权限配置</p>
              <p v-else>请选择一个角色查看权限详情</p>
            </div>

            <div v-if="selectedRole" class="permission-details">
              <!-- 角色基本信息 -->
              <div class="role-basic-info">
                <a-descriptions :column="1" size="small">
                  <a-descriptions-item label="角色名称">
                    {{ selectedRole.name }}
                  </a-descriptions-item>
                  <a-descriptions-item label="角色描述">
                    {{ selectedRole.description }}
                  </a-descriptions-item>
                  <a-descriptions-item label="角色等级">
                    <a-tag :color="getRoleColor(selectedRole.level)">
                      {{ getRoleLevelText(selectedRole.level) }}
                    </a-tag>
                  </a-descriptions-item>
                  <a-descriptions-item label="系统角色">
                    <a-tag :color="selectedRole.isSystem ? 'red' : 'green'">
                      {{ selectedRole.isSystem ? '是' : '否' }}
                    </a-tag>
                  </a-descriptions-item>
                </a-descriptions>
              </div>

              <!-- 权限列表 -->
              <div class="permissions-list">
                <h4>功能权限</h4>
                <div class="permissions-grid">
                  <div 
                    v-for="permission in allPermissions" 
                    :key="permission.code"
                    class="permission-item"
                  >
                    <a-checkbox 
                      :checked="hasPermission(permission.code)"
                      :disabled="selectedRole.isSystem || !canEditRole"
                      @change="togglePermission(permission.code, $event)"
                    >
                      <div class="permission-content">
                        <div class="permission-name">{{ permission.name }}</div>
                        <div class="permission-desc">{{ permission.description }}</div>
                      </div>
                    </a-checkbox>
                  </div>
                </div>
              </div>

              <!-- 操作按钮 -->
              <div class="panel-actions" v-if="!selectedRole.isSystem && canEditRole">
                <a-space>
                  <a-button @click="resetRolePermissions">
                    重置权限
                  </a-button>
                  <a-button 
                    type="primary" 
                    @click="saveRolePermissions"
                    :loading="saveLoading"
                  >
                    保存权限
                  </a-button>
                </a-space>
              </div>
            </div>

            <div v-else class="no-role-selected">
              <a-empty description="请先选择一个角色" />
            </div>
          </div>
        </a-col>
      </a-row>
    </div>

    <!-- 新建/编辑角色弹窗 -->
    <a-modal
      v-model:open="roleModalVisible"
      :title="editingRole ? '编辑角色' : '新建角色'"
      width="600px"
      @ok="handleRoleSave"
      @cancel="handleRoleCancel"
      :confirm-loading="saveLoading"
    >
      <a-form
        ref="roleFormRef"
        :model="roleForm"
        :rules="roleFormRules"
        layout="vertical"
      >
        <a-form-item label="角色名称" name="name" required>
          <a-input 
            v-model:value="roleForm.name" 
            placeholder="输入角色名称"
          />
        </a-form-item>

        <a-form-item label="角色描述" name="description" required>
          <a-textarea 
            v-model:value="roleForm.description" 
            placeholder="描述角色的用途和职责"
            :rows="3"
          />
        </a-form-item>

        <a-form-item label="角色等级" name="level" required>
          <a-select v-model:value="roleForm.level" placeholder="选择角色等级">
            <a-select-option value="1">普通用户</a-select-option>
            <a-select-option value="2">小组长</a-select-option>
            <a-select-option value="3">管理员</a-select-option>
            <a-select-option value="4">超级管理员</a-select-option>
          </a-select>
        </a-form-item>

        <a-form-item label="基础权限" name="permissions">
          <a-checkbox-group v-model:value="roleForm.permissions">
            <a-row :gutter="[16, 8]">
              <a-col :span="12" v-for="permission in basicPermissions" :key="permission.code">
                <a-checkbox :value="permission.code">
                  {{ permission.name }}
                </a-checkbox>
              </a-col>
            </a-row>
          </a-checkbox-group>
        </a-form-item>
      </a-form>
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, h } from 'vue'
import { message, Modal, type FormInstance } from 'ant-design-vue'
import { useAuthStore } from '@/stores/auth'
import { api } from '@/api/client'
import {
  PlusOutlined,
  ReloadOutlined
} from '@ant-design/icons-vue'

// 响应式数据
const loading = ref(false)
const saveLoading = ref(false)
const roles = ref<any[]>([])
const selectedRole = ref<any>(null)
const roleModalVisible = ref(false)
const editingRole = ref<any>(null)
const roleFormRef = ref<FormInstance>()

const authStore = useAuthStore()

// 角色表单
const roleForm = reactive({
  name: '',
  description: '',
  level: '1',
  permissions: [] as string[]
})

// 表单验证规则
const roleFormRules = {
  name: [
    { required: true, message: '请输入角色名称', trigger: 'blur' },
    { min: 2, max: 20, message: '角色名称长度为2-20个字符', trigger: 'blur' }
  ],
  description: [
    { required: true, message: '请输入角色描述', trigger: 'blur' },
    { min: 5, max: 100, message: '角色描述长度为5-100个字符', trigger: 'blur' }
  ],
  level: [
    { required: true, message: '请选择角色等级', trigger: 'change' }
  ]
}

// 权限定义
const allPermissions = [
  { code: 'view_dashboard', name: '查看仪表盘', description: '访问系统首页和概览信息', category: 'basic' },
  { code: 'view_tasks', name: '查看任务', description: '查看分配给自己的任务', category: 'task' },
  { code: 'create_task', name: '创建任务', description: '创建新的维修任务', category: 'task' },
  { code: 'edit_task', name: '编辑任务', description: '编辑已有的任务信息', category: 'task' },
  { code: 'delete_task', name: '删除任务', description: '删除任务记录', category: 'task' },
  { code: 'mark_offline_task', name: '标记线下任务', description: '将任务标记为线下任务', category: 'task' },
  { code: 'import_repair_data', name: '导入报修数据', description: '批量导入AB表数据', category: 'data' },
  { code: 'export_data', name: '导出数据', description: '导出各类统计数据', category: 'data' },
  { code: 'view_all_tasks', name: '查看所有任务', description: '查看系统中的所有任务', category: 'management' },
  { code: 'manage_members', name: '成员管理', description: '管理团队成员信息', category: 'management' },
  { code: 'approve_assistance_task', name: '审核协助任务', description: '审核学生提交的协助任务', category: 'management' },
  { code: 'view_statistics', name: '查看统计', description: '查看各类统计报表', category: 'report' },
  { code: 'manage_settings', name: '系统设置', description: '修改系统参数和配置', category: 'admin' },
  { code: 'manage_roles', name: '权限管理', description: '管理用户角色和权限', category: 'admin' }
]

const basicPermissions = computed(() => 
  allPermissions.filter(p => ['basic', 'task'].includes(p.category))
)

// 计算属性
const canEditRole = computed(() => authStore.hasPermission('manage_roles'))

// 方法
const fetchRoles = async () => {
  try {
    loading.value = true
    const response = await api.getRoles()
    
    if (response.success && response.data) {
      roles.value = response.data
    }
  } catch (error) {
    console.error('获取角色列表失败:', error)
    message.error('获取角色列表失败')
  } finally {
    loading.value = false
  }
}

const refreshData = () => {
  selectedRole.value = null
  fetchRoles()
}

const selectRole = (role: any) => {
  selectedRole.value = role
}

const hasPermission = (permissionCode: string) => {
  return selectedRole.value?.permissions?.includes(permissionCode) || false
}

const togglePermission = (permissionCode: string, event: any) => {
  if (!selectedRole.value || selectedRole.value.isSystem) return
  
  const checked = event.target.checked
  if (checked) {
    if (!selectedRole.value.permissions.includes(permissionCode)) {
      selectedRole.value.permissions.push(permissionCode)
    }
  } else {
    const index = selectedRole.value.permissions.indexOf(permissionCode)
    if (index > -1) {
      selectedRole.value.permissions.splice(index, 1)
    }
  }
}

const saveRolePermissions = async () => {
  if (!selectedRole.value) return
  
  try {
    saveLoading.value = true
    
    const response = await api.updateRolePermissions(selectedRole.value.id, {
      permissions: selectedRole.value.permissions
    })
    
    if (response.success) {
      message.success('权限保存成功')
      await fetchRoles()
    } else {
      throw new Error(response.message || '保存失败')
    }
  } catch (error: any) {
    console.error('保存角色权限失败:', error)
    message.error(error.message || '保存权限失败')
  } finally {
    saveLoading.value = false
  }
}

const resetRolePermissions = () => {
  if (!selectedRole.value) return
  
  Modal.confirm({
    title: '确认重置',
    content: '确定要重置该角色的所有权限吗？此操作不可撤销。',
    onOk: async () => {
      selectedRole.value.permissions = []
      await saveRolePermissions()
    }
  })
}

const showCreateRole = () => {
  editingRole.value = null
  Object.assign(roleForm, {
    name: '',
    description: '',
    level: '1',
    permissions: []
  })
  roleModalVisible.value = true
}

const editRole = (role: any) => {
  editingRole.value = role
  Object.assign(roleForm, {
    name: role.name,
    description: role.description,
    level: role.level.toString(),
    permissions: [...role.permissions]
  })
  roleModalVisible.value = true
}

const handleRoleSave = async () => {
  try {
    await roleFormRef.value?.validate()
    saveLoading.value = true
    
    const roleData = {
      name: roleForm.name,
      description: roleForm.description,
      level: parseInt(roleForm.level),
      permissions: roleForm.permissions
    }
    
    let response
    if (editingRole.value) {
      response = await api.updateRole(editingRole.value.id, roleData)
    } else {
      response = await api.createRole(roleData)
    }
    
    if (response.success) {
      message.success(editingRole.value ? '角色更新成功' : '角色创建成功')
      roleModalVisible.value = false
      await fetchRoles()
    } else {
      throw new Error(response.message || '操作失败')
    }
  } catch (error: any) {
    if (error.errorFields) {
      message.error('请完善必填信息')
      return
    }
    
    console.error('保存角色失败:', error)
    message.error(error.message || '保存角色失败')
  } finally {
    saveLoading.value = false
  }
}

const handleRoleCancel = () => {
  roleModalVisible.value = false
  roleFormRef.value?.resetFields()
}

const deleteRole = (role: any) => {
  if (role.isSystem) {
    message.warning('系统角色不能删除')
    return
  }
  
  Modal.confirm({
    title: '确认删除',
    content: `确定要删除角色"${role.name}"吗？此操作不可撤销，该角色下的用户将失去相应权限。`,
    okType: 'danger',
    onOk: async () => {
      try {
        const response = await api.deleteRole(role.id)
        
        if (response.success) {
          message.success('角色删除成功')
          if (selectedRole.value?.id === role.id) {
            selectedRole.value = null
          }
          await fetchRoles()
        } else {
          throw new Error(response.message || '删除失败')
        }
      } catch (error: any) {
        console.error('删除角色失败:', error)
        message.error(error.message || '删除角色失败')
      }
    }
  })
}

const getRoleColor = (level: number) => {
  const colors: Record<number, string> = {
    1: 'blue',
    2: 'green', 
    3: 'orange',
    4: 'red'
  }
  return colors[level] || 'default'
}

const getRoleLevelText = (level: number) => {
  const texts: Record<number, string> = {
    1: '普通用户',
    2: '小组长',
    3: '管理员', 
    4: '超级管理员'
  }
  return texts[level] || '未知'
}

const formatDate = (dateStr: string) => {
  return new Date(dateStr).toLocaleDateString('zh-CN')
}

// 生命周期
onMounted(() => {
  fetchRoles()
})
</script>

<style scoped>
.desktop-permission-management {
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

.permission-content {
  flex: 1;
  overflow: hidden;
}

.roles-panel,
.permissions-panel {
  background: white;
  border-radius: 12px;
  padding: 24px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.04);
  border: 1px solid #e8e9ea;
  height: 100%;
  display: flex;
  flex-direction: column;
}

.panel-header {
  margin-bottom: 24px;
  padding-bottom: 16px;
  border-bottom: 1px solid #e8e9ea;
}

.panel-header h3 {
  margin: 0 0 8px;
  font-size: 18px;
  font-weight: 600;
  color: #1a1a1a;
}

.panel-header p {
  margin: 0;
  color: #666666;
  font-size: 14px;
}

.roles-grid {
  display: flex;
  flex-direction: column;
  gap: 16px;
  overflow-y: auto;
  flex: 1;
}

.role-card {
  border: 1px solid #e8e9ea;
  border-radius: 8px;
  padding: 20px;
  cursor: pointer;
  transition: all 0.3s ease;
  background: white;
}

.role-card:hover {
  border-color: #667eea;
  box-shadow: 0 2px 8px rgba(102, 126, 234, 0.15);
}

.role-card.active {
  border-color: #667eea;
  background: #f6f8ff;
  box-shadow: 0 0 0 2px rgba(102, 126, 234, 0.2);
}

.role-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 16px;
}

.role-info h4 {
  margin: 0 0 4px;
  font-size: 16px;
  font-weight: 600;
  color: #1a1a1a;
}

.role-info p {
  margin: 0;
  font-size: 13px;
  color: #666666;
  line-height: 1.4;
}

.role-details {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-bottom: 16px;
}

.detail-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.detail-label {
  font-size: 12px;
  color: #8c8c8c;
}

.detail-value {
  font-size: 12px;
  font-weight: 500;
  color: #1a1a1a;
}

.role-actions {
  display: flex;
  gap: 8px;
}

.permission-details {
  flex: 1;
  overflow-y: auto;
}

.role-basic-info {
  margin-bottom: 24px;
  padding: 16px;
  background: #f8f9fa;
  border-radius: 8px;
}

.permissions-list h4 {
  margin: 0 0 16px;
  font-size: 16px;
  font-weight: 600;
  color: #1a1a1a;
}

.permissions-grid {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.permission-item {
  padding: 12px;
  border: 1px solid #e8e9ea;
  border-radius: 6px;
  transition: all 0.3s ease;
}

.permission-item:hover {
  border-color: #d9d9d9;
  background: #fafbfc;
}

.permission-content {
  margin-left: 8px;
}

.permission-name {
  font-size: 14px;
  font-weight: 500;
  color: #1a1a1a;
}

.permission-desc {
  font-size: 12px;
  color: #8c8c8c;
  margin-top: 2px;
}

.panel-actions {
  margin-top: 24px;
  padding-top: 16px;
  border-top: 1px solid #e8e9ea;
  display: flex;
  justify-content: center;
}

.no-role-selected {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
}

/* 表单样式优化 */
:deep(.ant-form-item-label) {
  font-weight: 500;
}

:deep(.ant-btn) {
  border-radius: 6px;
  font-weight: 500;
}

:deep(.ant-btn-primary) {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border: none;
  box-shadow: 0 3px 10px rgba(102, 126, 234, 0.3);
}

:deep(.ant-btn-primary:hover) {
  transform: translateY(-1px);
  box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
}

:deep(.ant-checkbox-wrapper) {
  margin-bottom: 0;
}

:deep(.ant-descriptions-item-label) {
  font-weight: 500;
}

/* 响应式优化 */
@media (max-width: 1200px) {
  .header-content {
    flex-direction: column;
    gap: 20px;
    text-align: center;
  }
  
  .permission-content .ant-col {
    margin-bottom: 24px;
  }
  
  .roles-panel,
  .permissions-panel {
    height: auto;
  }
}

@media (max-width: 768px) {
  .page-header {
    padding: 20px;
  }
  
  .roles-panel,
  .permissions-panel {
    padding: 16px;
  }
  
  .role-card {
    padding: 16px;
  }
  
  .role-header {
    flex-direction: column;
    gap: 12px;
  }
  
  .role-actions {
    justify-content: flex-end;
  }
}
</style>