<template>
  <div class="settings-view">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-left">
        <h1 class="page-title">系统设置</h1>
        <p class="page-description">管理系统配置、用户权限和业务规则</p>
      </div>
      <div class="header-actions">
        <el-button type="primary" :icon="Refresh" @click="refreshSettings">
          刷新配置
        </el-button>
      </div>
    </div>

    <div class="settings-content">
      <el-row :gutter="20">
        <!-- 左侧设置菜单 -->
        <el-col :span="6">
          <el-card class="settings-menu">
            <el-menu
              v-model="activeSection"
              @select="handleSectionChange"
              class="settings-menu-list"
            >
              <el-menu-item index="basic">
                <el-icon><Setting /></el-icon>
                <span>基础设置</span>
              </el-menu-item>
              <el-menu-item index="work-hours">
                <el-icon><Timer /></el-icon>
                <span>工时规则</span>
              </el-menu-item>
              <el-menu-item index="permissions">
                <el-icon><User /></el-icon>
                <span>权限管理</span>
              </el-menu-item>
              <el-menu-item index="notifications">
                <el-icon><Bell /></el-icon>
                <span>通知设置</span>
              </el-menu-item>
              <el-menu-item index="backup">
                <el-icon><Download /></el-icon>
                <span>数据备份</span>
              </el-menu-item>
              <el-menu-item index="system">
                <el-icon><Monitor /></el-icon>
                <span>系统信息</span>
              </el-menu-item>
            </el-menu>
          </el-card>
        </el-col>

        <!-- 右侧设置内容 -->
        <el-col :span="18">
          <!-- 基础设置 -->
          <div v-if="activeSection === 'basic'" class="settings-section">
            <el-card>
              <template #header>
                <div class="card-header">
                  <span>基础设置</span>
                </div>
              </template>

              <el-form :model="basicSettings" label-width="120px">
                <el-form-item label="系统名称">
                  <el-input
                    v-model="basicSettings.systemName"
                    placeholder="请输入系统名称"
                  />
                </el-form-item>
                <el-form-item label="系统描述">
                  <el-input
                    v-model="basicSettings.systemDescription"
                    type="textarea"
                    :rows="3"
                    placeholder="请输入系统描述"
                  />
                </el-form-item>
                <el-form-item label="默认工作组">
                  <el-select
                    v-model="basicSettings.defaultGroup"
                    placeholder="请选择默认工作组"
                  >
                    <el-option label="第一组" value="1" />
                    <el-option label="第二组" value="2" />
                    <el-option label="第三组" value="3" />
                  </el-select>
                </el-form-item>
                <el-form-item label="时间格式">
                  <el-select
                    v-model="basicSettings.timeFormat"
                    placeholder="请选择时间格式"
                  >
                    <el-option label="24小时制" value="24h" />
                    <el-option label="12小时制" value="12h" />
                  </el-select>
                </el-form-item>
                <el-form-item>
                  <el-button type="primary" @click="saveBasicSettings"
                    >保存设置</el-button
                  >
                  <el-button @click="resetBasicSettings">重置</el-button>
                </el-form-item>
              </el-form>
            </el-card>
          </div>

          <!-- 工时规则设置 -->
          <div v-if="activeSection === 'work-hours'" class="settings-section">
            <el-card>
              <template #header>
                <div class="card-header">
                  <span>工时规则配置</span>
                </div>
              </template>

              <el-form :model="workHoursSettings" label-width="150px">
                <el-form-item label="在线任务标准工时">
                  <el-input-number
                    v-model="workHoursSettings.onlineTaskMinutes"
                    :min="1"
                    :max="480"
                    :step="5"
                  />
                  <span class="input-suffix">分钟</span>
                </el-form-item>
                <el-form-item label="线下任务标准工时">
                  <el-input-number
                    v-model="workHoursSettings.offlineTaskMinutes"
                    :min="1"
                    :max="480"
                    :step="5"
                  />
                  <span class="input-suffix">分钟</span>
                </el-form-item>
                <el-form-item label="紧急任务奖励工时">
                  <el-input-number
                    v-model="workHoursSettings.rushBonusMinutes"
                    :min="0"
                    :max="120"
                    :step="5"
                  />
                  <span class="input-suffix">分钟</span>
                </el-form-item>
                <el-form-item label="好评奖励工时">
                  <el-input-number
                    v-model="workHoursSettings.positiveRatingBonus"
                    :min="0"
                    :max="60"
                    :step="5"
                  />
                  <span class="input-suffix">分钟</span>
                </el-form-item>
                <el-form-item label="延迟响应惩罚">
                  <el-input-number
                    v-model="workHoursSettings.lateResponsePenalty"
                    :min="0"
                    :max="60"
                    :step="5"
                  />
                  <span class="input-suffix">分钟</span>
                </el-form-item>
                <el-form-item label="延迟完成惩罚">
                  <el-input-number
                    v-model="workHoursSettings.lateCompletionPenalty"
                    :min="0"
                    :max="60"
                    :step="5"
                  />
                  <span class="input-suffix">分钟</span>
                </el-form-item>
                <el-form-item label="差评惩罚工时">
                  <el-input-number
                    v-model="workHoursSettings.negativeRatingPenalty"
                    :min="0"
                    :max="120"
                    :step="5"
                  />
                  <span class="input-suffix">分钟</span>
                </el-form-item>
                <el-form-item>
                  <el-button type="primary" @click="saveWorkHoursSettings"
                    >保存设置</el-button
                  >
                  <el-button @click="resetWorkHoursSettings"
                    >重置为默认值</el-button
                  >
                </el-form-item>
              </el-form>
            </el-card>
          </div>

          <!-- 权限管理 -->
          <div v-if="activeSection === 'permissions'" class="settings-section">
            <el-card>
              <template #header>
                <div class="card-header">
                  <span>权限管理</span>
                </div>
              </template>

              <el-table :data="permissionSettings" style="width: 100%">
                <el-table-column prop="module" label="功能模块" width="150" />
                <el-table-column prop="description" label="描述" />
                <el-table-column label="管理员" width="80" align="center">
                  <template #default="{ row }">
                    <el-checkbox v-model="row.permissions.admin" disabled />
                  </template>
                </el-table-column>
                <el-table-column label="组长" width="80" align="center">
                  <template #default="{ row }">
                    <el-checkbox v-model="row.permissions.group_leader" />
                  </template>
                </el-table-column>
                <el-table-column label="成员" width="80" align="center">
                  <template #default="{ row }">
                    <el-checkbox v-model="row.permissions.member" />
                  </template>
                </el-table-column>
              </el-table>

              <div class="mt-4">
                <el-button type="primary" @click="savePermissionSettings"
                  >保存权限设置</el-button
                >
                <el-button @click="resetPermissionSettings"
                  >重置为默认</el-button
                >
              </div>
            </el-card>
          </div>

          <!-- 通知设置 -->
          <div
            v-if="activeSection === 'notifications'"
            class="settings-section"
          >
            <el-card>
              <template #header>
                <div class="card-header">
                  <span>通知设置</span>
                </div>
              </template>

              <el-form :model="notificationSettings" label-width="120px">
                <el-form-item label="邮件通知">
                  <el-switch v-model="notificationSettings.emailEnabled" />
                </el-form-item>
                <el-form-item
                  label="SMTP服务器"
                  v-if="notificationSettings.emailEnabled"
                >
                  <el-input
                    v-model="notificationSettings.smtpServer"
                    placeholder="smtp.example.com"
                  />
                </el-form-item>
                <el-form-item
                  label="SMTP端口"
                  v-if="notificationSettings.emailEnabled"
                >
                  <el-input-number
                    v-model="notificationSettings.smtpPort"
                    :min="1"
                    :max="65535"
                  />
                </el-form-item>
                <el-form-item
                  label="发件人邮箱"
                  v-if="notificationSettings.emailEnabled"
                >
                  <el-input
                    v-model="notificationSettings.senderEmail"
                    placeholder="system@example.com"
                  />
                </el-form-item>
                <el-form-item label="系统通知">
                  <el-switch
                    v-model="notificationSettings.systemNotificationEnabled"
                  />
                </el-form-item>
                <el-form-item label="任务分配通知">
                  <el-switch
                    v-model="notificationSettings.taskAssignmentNotification"
                  />
                </el-form-item>
                <el-form-item label="任务完成通知">
                  <el-switch
                    v-model="notificationSettings.taskCompletionNotification"
                  />
                </el-form-item>
                <el-form-item label="工时统计通知">
                  <el-switch
                    v-model="notificationSettings.workHoursNotification"
                  />
                </el-form-item>
                <el-form-item>
                  <el-button type="primary" @click="saveNotificationSettings"
                    >保存设置</el-button
                  >
                  <el-button @click="testNotification">发送测试通知</el-button>
                </el-form-item>
              </el-form>
            </el-card>
          </div>

          <!-- 数据备份 -->
          <div v-if="activeSection === 'backup'" class="settings-section">
            <el-card>
              <template #header>
                <div class="card-header">
                  <span>数据备份与恢复</span>
                </div>
              </template>

              <div class="backup-section">
                <el-alert
                  title="重要提示"
                  description="请定期备份数据，备份文件包含所有系统数据，请妥善保管。"
                  type="warning"
                  :closable="false"
                  class="mb-4"
                />

                <el-row :gutter="20">
                  <el-col :span="12">
                    <el-card shadow="never" class="backup-card">
                      <div class="backup-item">
                        <h4>创建备份</h4>
                        <p>备份当前系统的所有数据</p>
                        <el-button
                          type="primary"
                          @click="createBackup"
                          :loading="backupLoading"
                        >
                          创建备份
                        </el-button>
                      </div>
                    </el-card>
                  </el-col>
                  <el-col :span="12">
                    <el-card shadow="never" class="backup-card">
                      <div class="backup-item">
                        <h4>恢复数据</h4>
                        <p>从备份文件恢复数据</p>
                        <el-upload
                          :auto-upload="false"
                          :on-change="handleBackupFileChange"
                          :show-file-list="false"
                          accept=".sql,.json"
                        >
                          <el-button type="success">选择备份文件</el-button>
                        </el-upload>
                      </div>
                    </el-card>
                  </el-col>
                </el-row>

                <div class="backup-history mt-4">
                  <h4>备份历史</h4>
                  <el-table :data="backupHistory" style="width: 100%">
                    <el-table-column prop="filename" label="文件名" />
                    <el-table-column
                      prop="createTime"
                      label="创建时间"
                      width="180"
                    />
                    <el-table-column prop="size" label="文件大小" width="120" />
                    <el-table-column label="操作" width="150">
                      <template #default="{ row }">
                        <el-button size="small" @click="downloadBackup(row)"
                          >下载</el-button
                        >
                        <el-button
                          size="small"
                          type="danger"
                          @click="deleteBackup(row)"
                          >删除</el-button
                        >
                      </template>
                    </el-table-column>
                  </el-table>
                </div>
              </div>
            </el-card>
          </div>

          <!-- 系统信息 -->
          <div v-if="activeSection === 'system'" class="settings-section">
            <el-card>
              <template #header>
                <div class="card-header">
                  <span>系统信息</span>
                </div>
              </template>

              <el-descriptions :column="2" border>
                <el-descriptions-item label="系统版本">{{
                  systemInfo.version
                }}</el-descriptions-item>
                <el-descriptions-item label="构建时间">{{
                  systemInfo.buildTime
                }}</el-descriptions-item>
                <el-descriptions-item label="Python版本">{{
                  systemInfo.pythonVersion
                }}</el-descriptions-item>
                <el-descriptions-item label="数据库版本">{{
                  systemInfo.databaseVersion
                }}</el-descriptions-item>
                <el-descriptions-item label="系统运行时间">{{
                  systemInfo.uptime
                }}</el-descriptions-item>
                <el-descriptions-item label="当前用户数">{{
                  systemInfo.activeUsers
                }}</el-descriptions-item>
                <el-descriptions-item label="总任务数">{{
                  systemInfo.totalTasks
                }}</el-descriptions-item>
                <el-descriptions-item label="已完成任务">{{
                  systemInfo.completedTasks
                }}</el-descriptions-item>
              </el-descriptions>

              <div class="system-actions mt-4">
                <el-button type="primary" @click="checkSystemHealth"
                  >健康检查</el-button
                >
                <el-button type="warning" @click="clearCache"
                  >清理缓存</el-button
                >
                <el-button type="danger" @click="restartSystem"
                  >重启系统</el-button
                >
              </div>
            </el-card>
          </div>
        </el-col>
      </el-row>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Setting,
  Timer,
  User,
  Bell,
  Download,
  Monitor,
  Refresh
} from '@element-plus/icons-vue'

// 响应式数据
const activeSection = ref('basic')
const backupLoading = ref(false)

// 基础设置
const basicSettings = reactive({
  systemName: '考勤管理系统',
  systemDescription: '面向高校网络维护团队的考勤管理系统',
  defaultGroup: '1',
  timeFormat: '24h'
})

// 工时规则设置
const workHoursSettings = reactive({
  onlineTaskMinutes: 40,
  offlineTaskMinutes: 100,
  rushBonusMinutes: 15,
  positiveRatingBonus: 30,
  lateResponsePenalty: 30,
  lateCompletionPenalty: 30,
  negativeRatingPenalty: 60
})

// 权限设置
const permissionSettings = ref([
  {
    module: '成员管理',
    description: '管理系统用户和权限',
    permissions: { admin: true, group_leader: true, member: false }
  },
  {
    module: '任务管理',
    description: '创建、分配和管理任务',
    permissions: { admin: true, group_leader: true, member: true }
  },
  {
    module: '工时管理',
    description: '查看和管理工时记录',
    permissions: { admin: true, group_leader: true, member: true }
  },
  {
    module: '统计报表',
    description: '查看统计分析和报表',
    permissions: { admin: true, group_leader: true, member: false }
  },
  {
    module: '数据导入',
    description: '导入外部数据',
    permissions: { admin: true, group_leader: false, member: false }
  },
  {
    module: '系统设置',
    description: '修改系统配置',
    permissions: { admin: true, group_leader: false, member: false }
  }
])

// 通知设置
const notificationSettings = reactive({
  emailEnabled: false,
  smtpServer: '',
  smtpPort: 587,
  senderEmail: '',
  systemNotificationEnabled: true,
  taskAssignmentNotification: true,
  taskCompletionNotification: true,
  workHoursNotification: false
})

// 备份历史
const backupHistory = ref([
  {
    filename: 'backup_20250801_094500.sql',
    createTime: '2025-08-01 09:45:00',
    size: '2.5 MB'
  },
  {
    filename: 'backup_20250731_183000.sql',
    createTime: '2025-07-31 18:30:00',
    size: '2.3 MB'
  }
])

// 系统信息
const systemInfo = reactive({
  version: 'v1.0.0',
  buildTime: '2025-08-01 08:00:00',
  pythonVersion: '3.12.0',
  databaseVersion: 'PostgreSQL 15.3',
  uptime: '2天 15小时 32分钟',
  activeUsers: 15,
  totalTasks: 1248,
  completedTasks: 1089
})

// 方法
const handleSectionChange = (section: string) => {
  activeSection.value = section
}

const refreshSettings = () => {
  ElMessage.success('配置已刷新')
}

const saveBasicSettings = () => {
  ElMessage.success('基础设置保存成功')
}

const resetBasicSettings = () => {
  basicSettings.systemName = '考勤管理系统'
  basicSettings.systemDescription = '面向高校网络维护团队的考勤管理系统'
  basicSettings.defaultGroup = '1'
  basicSettings.timeFormat = '24h'
  ElMessage.info('基础设置已重置')
}

const saveWorkHoursSettings = () => {
  ElMessage.success('工时规则保存成功')
}

const resetWorkHoursSettings = () => {
  workHoursSettings.onlineTaskMinutes = 40
  workHoursSettings.offlineTaskMinutes = 100
  workHoursSettings.rushBonusMinutes = 15
  workHoursSettings.positiveRatingBonus = 30
  workHoursSettings.lateResponsePenalty = 30
  workHoursSettings.lateCompletionPenalty = 30
  workHoursSettings.negativeRatingPenalty = 60
  ElMessage.info('工时规则已重置为默认值')
}

const savePermissionSettings = () => {
  ElMessage.success('权限设置保存成功')
}

const resetPermissionSettings = () => {
  ElMessage.info('权限设置已重置为默认')
}

const saveNotificationSettings = () => {
  ElMessage.success('通知设置保存成功')
}

const testNotification = () => {
  ElMessage.success('测试通知已发送')
}

const createBackup = async () => {
  backupLoading.value = true
  try {
    // 模拟备份过程
    await new Promise(resolve => setTimeout(resolve, 2000))
    const now = new Date()
    const filename = `backup_${now.getFullYear()}${(now.getMonth() + 1).toString().padStart(2, '0')}${now.getDate().toString().padStart(2, '0')}_${now.getHours().toString().padStart(2, '0')}${now.getMinutes().toString().padStart(2, '0')}${now.getSeconds().toString().padStart(2, '0')}.sql`

    backupHistory.value.unshift({
      filename,
      createTime: now.toLocaleString('zh-CN'),
      size: '2.6 MB'
    })

    ElMessage.success('备份创建成功')
  } catch (error) {
    ElMessage.error('备份创建失败')
  } finally {
    backupLoading.value = false
  }
}

const handleBackupFileChange = (file: any) => {
  ElMessageBox.confirm(
    '恢复数据将覆盖当前所有数据，此操作不可逆，确定要继续吗？',
    '警告',
    {
      confirmButtonText: '确定恢复',
      cancelButtonText: '取消',
      type: 'warning'
    }
  )
    .then(() => {
      ElMessage.success(`开始恢复数据：${file.name}`)
    })
    .catch(() => {
      ElMessage.info('已取消恢复操作')
    })
}

const downloadBackup = (backup: any) => {
  ElMessage.success(`开始下载：${backup.filename}`)
}

const deleteBackup = (backup: any) => {
  ElMessageBox.confirm(`确定要删除备份文件 "${backup.filename}" 吗？`, '警告', {
    confirmButtonText: '确定删除',
    cancelButtonText: '取消',
    type: 'warning'
  })
    .then(() => {
      const index = backupHistory.value.findIndex(
        item => item.filename === backup.filename
      )
      if (index > -1) {
        backupHistory.value.splice(index, 1)
        ElMessage.success('备份文件删除成功')
      }
    })
    .catch(() => {
      ElMessage.info('已取消删除操作')
    })
}

const checkSystemHealth = () => {
  ElMessage.success('系统健康检查通过')
}

const clearCache = () => {
  ElMessage.success('缓存清理完成')
}

const restartSystem = () => {
  ElMessageBox.confirm('重启系统会中断所有用户的连接，确定要继续吗？', '警告', {
    confirmButtonText: '确定重启',
    cancelButtonText: '取消',
    type: 'warning'
  })
    .then(() => {
      ElMessage.success('系统重启命令已发送')
    })
    .catch(() => {
      ElMessage.info('已取消重启操作')
    })
}

onMounted(() => {
  // 初始化设置数据
})
</script>

<style scoped lang="scss">
.settings-view {
  padding: 20px;
  background: #f5f7fa;
  min-height: 100vh;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;

  .header-left {
    .page-title {
      font-size: 24px;
      font-weight: 600;
      color: #303133;
      margin: 0 0 8px 0;
    }

    .page-description {
      color: #909399;
      font-size: 14px;
      margin: 0;
    }
  }
}

.settings-content {
  .settings-menu {
    .settings-menu-list {
      border: none;
      background: transparent;

      .el-menu-item {
        margin-bottom: 4px;
        border-radius: 6px;

        &:hover {
          background-color: #f5f7fa;
        }

        &.is-active {
          background-color: #ecf5ff;
          color: #409eff;
        }
      }
    }
  }

  .settings-section {
    .card-header {
      font-size: 16px;
      font-weight: 600;
      color: #303133;
    }

    .input-suffix {
      margin-left: 8px;
      color: #909399;
      font-size: 12px;
    }
  }
}

.backup-section {
  .backup-card {
    height: 120px;
    display: flex;
    align-items: center;
    justify-content: center;

    .backup-item {
      text-align: center;

      h4 {
        margin: 0 0 8px 0;
        color: #303133;
      }

      p {
        margin: 0 0 16px 0;
        color: #909399;
        font-size: 14px;
      }
    }
  }

  .backup-history {
    h4 {
      margin: 0 0 16px 0;
      color: #303133;
    }
  }
}

.system-actions {
  display: flex;
  gap: 12px;
}

.mt-4 {
  margin-top: 16px;
}

.mb-4 {
  margin-bottom: 16px;
}

@media (max-width: 768px) {
  .settings-content {
    :deep(.el-row) {
      flex-direction: column;

      .el-col {
        width: 100% !important;
        max-width: 100% !important;
        margin-bottom: 20px;
      }
    }
  }
}
</style>
