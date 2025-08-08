<template>
  <div class="member-list">
    <!-- 头部操作区 -->
    <div class="member-list-header">
      <div class="header-left">
        <h2>成员管理</h2>
        <div class="search-box">
          <el-input
            v-model="searchQuery"
            placeholder="搜索用户名、姓名或学号"
            @input="handleSearch"
            clearable
          >
            <template #prefix>
              <el-icon><Search /></el-icon>
            </template>
          </el-input>
        </div>
      </div>
      
      <div class="header-right">
        <el-button type="primary" @click="handleCreate">
          <el-icon><Plus /></el-icon>
          新增成员
        </el-button>
        <el-button type="success" @click="handleImport">
          <el-icon><Upload /></el-icon>
          批量导入
        </el-button>
        <el-button @click="handleRefresh">
          <el-icon><Refresh /></el-icon>
          刷新
        </el-button>
      </div>
    </div>

    <!-- 筛选区 -->
    <div class="filter-bar">
      <el-form :model="filters" inline>
        <el-form-item label="角色">
          <el-select v-model="filters.role" placeholder="选择角色" clearable @change="handleFilter">
            <el-option label="管理员" value="admin" />
            <el-option label="组长" value="group_leader" />
            <el-option label="成员" value="member" />
            <el-option label="访客" value="guest" />
          </el-select>
        </el-form-item>
        
        <el-form-item label="状态">
          <el-select v-model="filters.is_active" placeholder="选择状态" clearable @change="handleFilter">
            <el-option label="在职" :value="true" />
            <el-option label="离职" :value="false" />
          </el-select>
        </el-form-item>
        
        <el-form-item label="部门">
          <el-input 
            v-model="filters.department" 
            placeholder="输入部门名称" 
            clearable 
            @input="handleFilter"
          />
        </el-form-item>
        
        <el-form-item label="班级">
          <el-input 
            v-model="filters.class_name" 
            placeholder="输入班级名称" 
            clearable 
            @input="handleFilter"
          />
        </el-form-item>
      </el-form>
    </div>

    <!-- 数据表格 -->
    <div class="table-container">
      <el-table 
        :data="members" 
        v-loading="loading"
        @selection-change="handleSelectionChange"
        stripe
        border
      >
        <el-table-column type="selection" width="55" />
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="username" label="用户名" width="120" />
        <el-table-column prop="name" label="姓名" width="100" />
        <el-table-column prop="student_id" label="学号" width="120" />
        <el-table-column prop="phone" label="手机号" width="130" />
        <el-table-column prop="department" label="部门" width="140" />
        <el-table-column prop="class_name" label="班级" width="120" />
        <el-table-column prop="role" label="角色" width="100">
          <template #default="{ row }">
            <el-tag :type="getRoleTagType(row.role)">
              {{ getRoleText(row.role) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="is_active" label="状态" width="80">
          <template #default="{ row }">
            <el-tag :type="row.is_active ? 'success' : 'danger'">
              {{ row.status_display }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="join_date" label="入职日期" width="120" />
        <el-table-column prop="last_login" label="最后登录" width="160">
          <template #default="{ row }">
            <span v-if="row.last_login">
              {{ formatDateTime(row.last_login) }}
            </span>
            <span v-else class="text-gray">从未登录</span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="180" fixed="right">
          <template #default="{ row }">
            <el-button size="small" @click="handleView(row)">查看</el-button>
            <el-button size="small" type="primary" @click="handleEdit(row)">编辑</el-button>
            <el-button 
              size="small" 
              type="danger" 
              @click="handleDelete(row)"
              :disabled="row.id === currentUserId"
            >
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <!-- 分页 -->
    <div class="pagination-container">
      <el-pagination
        v-model:current-page="pagination.page"
        v-model:page-size="pagination.page_size"
        :page-sizes="[10, 20, 50, 100]"
        :total="pagination.total"
        layout="total, sizes, prev, pager, next, jumper"
        @size-change="handleSizeChange"
        @current-change="handlePageChange"
      />
    </div>

    <!-- 批量操作区 -->
    <div v-if="selectedMembers.length > 0" class="batch-actions">
      <span>已选择 {{ selectedMembers.length }} 项</span>
      <el-button type="danger" @click="handleBatchDelete">批量删除</el-button>
      <el-button @click="handleBatchDeactivate">批量离职</el-button>
    </div>
  </div>

  <!-- 创建成员对话框 -->
  <CreateMemberDialog
    v-model:visible="createDialogVisible"
    @success="handleCreateSuccess"
  />

  <!-- 批量导入对话框 -->
  <ImportMemberDialog
    v-model:visible="importDialogVisible"
    @success="handleImportSuccess"
  />
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Search, Plus, Upload, Refresh } from '@element-plus/icons-vue'
import { getMembers, deleteMember, type Member, type MemberListParams } from '@/api/members'
import { useAuthStore } from '@/stores/auth'
import CreateMemberDialog from './CreateMemberDialog.vue'
import ImportMemberDialog from './ImportMemberDialog.vue'

// 组件状态
const loading = ref(false)
const members = ref<Member[]>([])
const selectedMembers = ref<Member[]>([])
const searchQuery = ref('')
const createDialogVisible = ref(false)
const importDialogVisible = ref(false)

// 筛选条件
const filters = reactive({
  role: '',
  is_active: null as boolean | null,
  department: '',
  class_name: ''
})

// 分页信息
const pagination = reactive({
  page: 1,
  page_size: 20,
  total: 0,
  total_pages: 0
})

// 获取当前用户信息
const authStore = useAuthStore()
const currentUserId = computed(() => authStore.userInfo?.id)

// 加载成员列表
const loadMembers = async () => {
  loading.value = true
  try {
    const params: MemberListParams = {
      page: pagination.page,
      page_size: pagination.page_size
    }
    
    // 添加搜索条件
    if (searchQuery.value) {
      params.search = searchQuery.value
    }
    
    // 添加筛选条件
    if (filters.role) {
      params.role = filters.role
    }
    if (filters.is_active !== null) {
      params.is_active = filters.is_active
    }
    if (filters.department) {
      params.department = filters.department
    }
    if (filters.class_name) {
      params.class_name = filters.class_name
    }
    
    const response = await getMembers(params)
    members.value = response.items
    pagination.total = response.total
    pagination.total_pages = response.total_pages
    
  } catch (error) {
    ElMessage.error('加载成员列表失败')
    console.error('Load members error:', error)
  } finally {
    loading.value = false
  }
}

// 搜索处理
let searchTimer: NodeJS.Timeout
const handleSearch = () => {
  clearTimeout(searchTimer)
  searchTimer = setTimeout(() => {
    pagination.page = 1
    loadMembers()
  }, 500)
}

// 筛选处理
let filterTimer: NodeJS.Timeout
const handleFilter = () => {
  clearTimeout(filterTimer)
  filterTimer = setTimeout(() => {
    pagination.page = 1
    loadMembers()
  }, 300)
}

// 分页处理
const handlePageChange = (page: number) => {
  pagination.page = page
  loadMembers()
}

const handleSizeChange = (size: number) => {
  pagination.page_size = size
  pagination.page = 1
  loadMembers()
}

// 选择处理
const handleSelectionChange = (selection: Member[]) => {
  selectedMembers.value = selection
}

// 操作处理
const handleCreate = () => {
  createDialogVisible.value = true
}

const handleImport = () => {
  importDialogVisible.value = true
}

const handleCreateSuccess = () => {
  loadMembers()
  ElMessage.success('成员创建成功')
}

const handleImportSuccess = () => {
  loadMembers()
  ElMessage.success('批量导入完成')
}

const handleRefresh = () => {
  loadMembers()
}

const handleView = (member: Member) => {
  // TODO: 打开成员详情对话框
  ElMessage.info(`查看成员：${member.name}`)
}

const handleEdit = (member: Member) => {
  // TODO: 打开编辑成员对话框
  ElMessage.info(`编辑成员：${member.name}`)
}

const handleDelete = async (member: Member) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除成员 "${member.name}" 吗？此操作无法撤销。`,
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    await deleteMember(member.id)
    ElMessage.success('删除成功')
    loadMembers()
    
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
      console.error('Delete member error:', error)
    }
  }
}

const handleBatchDelete = async () => {
  try {
    await ElMessageBox.confirm(
      `确定要删除选中的 ${selectedMembers.value.length} 个成员吗？此操作无法撤销。`,
      '确认批量删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    // TODO: 实现批量删除
    ElMessage.info('批量删除功能开发中')
    
  } catch (error) {
    // 用户取消操作
  }
}

const handleBatchDeactivate = () => {
  // TODO: 实现批量离职
  ElMessage.info('批量离职功能开发中')
}

// 工具方法
const getRoleTagType = (role: string) => {
  const types: Record<string, string> = {
    admin: 'danger',
    group_leader: 'warning',
    member: 'success',
    guest: 'info'
  }
  return types[role] || 'info'
}

const getRoleText = (role: string) => {
  const texts: Record<string, string> = {
    admin: '管理员',
    group_leader: '组长',
    member: '成员',
    guest: '访客'
  }
  return texts[role] || role
}

const formatDateTime = (datetime: string) => {
  if (!datetime) return ''
  return new Date(datetime).toLocaleString('zh-CN')
}

// 组件挂载
onMounted(() => {
  loadMembers()
})
</script>

<style scoped>
.member-list {
  padding: 20px;
}

.member-list-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 20px;
}

.header-left h2 {
  margin: 0;
  color: #303133;
}

.search-box {
  width: 300px;
}

.header-right {
  display: flex;
  gap: 10px;
}

.filter-bar {
  background: #f5f7fa;
  padding: 15px;
  border-radius: 4px;
  margin-bottom: 20px;
}

.table-container {
  margin-bottom: 20px;
}

.pagination-container {
  display: flex;
  justify-content: center;
  margin-top: 20px;
}

.batch-actions {
  position: fixed;
  bottom: 20px;
  left: 50%;
  transform: translateX(-50%);
  background: white;
  padding: 15px 20px;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  border: 1px solid #e4e7ed;
  display: flex;
  align-items: center;
  gap: 15px;
  z-index: 1000;
}

.text-gray {
  color: #909399;
}
</style>