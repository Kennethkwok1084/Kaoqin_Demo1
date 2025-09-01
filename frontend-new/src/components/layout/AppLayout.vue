<template>
  <a-layout class="desktop-layout">
    <!-- 左侧导航栏 - 桌面端固定宽度 -->
    <a-layout-sider
      v-model:collapsed="collapsed"
      :trigger="null"
      collapsible
      width="280"
      collapsed-width="80"
      class="desktop-sider"
    >
      <!-- 系统Logo和标题 -->
      <div class="system-header">
        <div class="logo-section">
          <div class="logo-icon">
            <DashboardOutlined />
          </div>
          <div v-if="!collapsed" class="system-title">
            <h1>考勤管理系统</h1>
            <p>网络维护团队</p>
          </div>
        </div>
      </div>
      
      <!-- 主导航菜单 -->
      <a-menu
        v-model:selectedKeys="selectedKeys"
        v-model:openKeys="openKeys"
        mode="inline"
        theme="dark"
        class="main-menu"
        @click="handleMenuClick"
      >
        <a-menu-item key="dashboard" @click="router.push('/dashboard')">
          <template #icon><DashboardOutlined /></template>
          数据仪表板
        </a-menu-item>
        
        <a-sub-menu key="tasks" title="任务管理中心">
          <template #icon><ProjectOutlined /></template>
          <a-menu-item key="task-list" @click="router.push('/tasks')">
            任务列表
          </a-menu-item>
          <a-menu-item key="task-create" @click="router.push('/tasks/create')">
            新建任务
          </a-menu-item>
        </a-sub-menu>
        
        <a-sub-menu key="members" title="人员管理">
          <template #icon><TeamOutlined /></template>
          <a-menu-item key="member-list" @click="router.push('/members')">
            成员列表
          </a-menu-item>
          <a-menu-item key="member-import" @click="router.push('/members/import')">
            批量导入
          </a-menu-item>
        </a-sub-menu>
        
        <a-sub-menu key="attendance" title="考勤管理">
          <template #icon><ScheduleOutlined /></template>
          <a-menu-item key="attendance-record" @click="router.push('/attendance')">
            考勤记录
          </a-menu-item>
          <a-menu-item key="work-hours" @click="router.push('/attendance/work-hours')">
            工时统计
          </a-menu-item>
        </a-sub-menu>
        
        <a-sub-menu key="statistics" title="数据报表">
          <template #icon><BarChartOutlined /></template>
          <a-menu-item key="stats-overview" @click="router.push('/statistics')">
            数据概览
          </a-menu-item>
          <a-menu-item key="stats-report" @click="router.push('/statistics/report')">
            详细报表
          </a-menu-item>
        </a-sub-menu>
        
        <a-menu-item key="settings" @click="router.push('/settings')">
          <template #icon><SettingOutlined /></template>
          系统设置
        </a-menu-item>
      </a-menu>
      
      <!-- 侧边栏底部信息 -->
      <div class="sidebar-footer" v-if="!collapsed">
        <div class="current-user">
          <a-avatar :size="36">{{ user?.name?.[0] }}</a-avatar>
          <div class="user-info">
            <div class="user-name">{{ user?.name || '未登录' }}</div>
            <div class="user-role">{{ getRoleText(user?.role) }}</div>
          </div>
        </div>
      </div>
    </a-layout-sider>

    <!-- 右侧主内容区域 -->
    <a-layout class="desktop-main">
      <!-- 顶部工具栏 -->
      <a-layout-header class="desktop-header">
        <div class="header-toolbar">
          <!-- 左侧工具 -->
          <div class="toolbar-left">
            <a-button 
              type="text" 
              size="large"
              :icon="collapsed ? h(MenuUnfoldOutlined) : h(MenuFoldOutlined)"
              @click="toggleCollapsed"
              class="collapse-btn"
            />
            
            <!-- 面包屑导航 -->
            <a-breadcrumb class="page-breadcrumb" separator=">">
              <a-breadcrumb-item v-for="item in breadcrumb" :key="item.title">
                <router-link v-if="item.path" :to="item.path">
                  {{ item.title }}
                </router-link>
                <span v-else>{{ item.title }}</span>
              </a-breadcrumb-item>
            </a-breadcrumb>
          </div>

          <!-- 右侧工具 -->
          <div class="toolbar-right">
            <a-space :size="16">
              <!-- 通知中心 -->
              <a-badge :count="5" size="small">
                <a-button type="text" size="large" :icon="h(BellOutlined)" />
              </a-badge>
              
              <!-- 用户操作菜单 -->
              <a-dropdown placement="bottomRight">
                <a-button type="text" class="user-dropdown">
                  <a-space>
                    <a-avatar :size="32">{{ user?.name?.[0] }}</a-avatar>
                    <span class="user-name">{{ user?.name }}</span>
                    <DownOutlined />
                  </a-space>
                </a-button>
                
                <template #overlay>
                  <a-menu class="user-menu">
                    <a-menu-item key="profile">
                      <UserOutlined />
                      个人信息
                    </a-menu-item>
                    <a-menu-item key="settings">
                      <SettingOutlined />
                      账户设置
                    </a-menu-item>
                    <a-menu-divider />
                    <a-menu-item key="logout" @click="handleLogout">
                      <LogoutOutlined />
                      退出登录
                    </a-menu-item>
                  </a-menu>
                </template>
              </a-dropdown>
            </a-space>
          </div>
        </div>
      </a-layout-header>

      <!-- 主内容区域 -->
      <a-layout-content class="desktop-content">
        <div class="content-container">
          <slot />
        </div>
      </a-layout-content>
    </a-layout>
  </a-layout>
</template>

<script setup lang="ts">
import { ref, computed, h } from 'vue'
import { useRouter } from 'vue-router'
import { message } from 'ant-design-vue'
import {
  MenuFoldOutlined,
  MenuUnfoldOutlined,
  BellOutlined,
  UserOutlined,
  SettingOutlined,
  LogoutOutlined,
  DownOutlined,
  DashboardOutlined,
  ProjectOutlined,
  TeamOutlined,
  ScheduleOutlined,
  BarChartOutlined,
} from '@ant-design/icons-vue'
import { useAuthStore } from '@/stores/auth'
import { useAppStore } from '@/stores/app'

const router = useRouter()
const authStore = useAuthStore()
const appStore = useAppStore()

// 响应式状态
const collapsed = ref(false)
const selectedKeys = ref<string[]>([])
const openKeys = ref<string[]>([])

// 计算属性
const user = computed(() => authStore.user)
const breadcrumb = computed(() => appStore.breadcrumb)

// 菜单项配置
const menuItems = computed(() => [
  {
    key: 'dashboard',
    icon: () => h(DashboardOutlined),
    label: '仪表板',
    onClick: () => router.push('/dashboard')
  },
  {
    key: 'tasks',
    icon: () => h(ProjectOutlined),
    label: '任务管理',
    children: [
      {
        key: 'task-list',
        label: '任务列表',
        onClick: () => router.push('/tasks')
      },
      {
        key: 'task-create',
        label: '创建任务',
        onClick: () => router.push('/tasks/create')
      }
    ]
  },
  {
    key: 'members',
    icon: () => h(TeamOutlined),
    label: '成员管理',
    children: [
      {
        key: 'member-list',
        label: '成员列表',
        onClick: () => router.push('/members')
      },
      {
        key: 'member-import',
        label: '批量导入',
        onClick: () => router.push('/members/import')
      }
    ]
  },
  {
    key: 'attendance',
    icon: () => h(ScheduleOutlined),
    label: '考勤管理',
    children: [
      {
        key: 'attendance-record',
        label: '考勤记录',
        onClick: () => router.push('/attendance')
      },
      {
        key: 'work-hours',
        label: '工时管理',
        onClick: () => router.push('/attendance/work-hours')
      }
    ]
  },
  {
    key: 'statistics',
    icon: () => h(BarChartOutlined),
    label: '统计报表',
    children: [
      {
        key: 'stats-overview',
        label: '数据概览',
        onClick: () => router.push('/statistics')
      },
      {
        key: 'stats-report',
        label: '详细报表',
        onClick: () => router.push('/statistics/report')
      }
    ]
  }
])

// 根据权限过滤菜单
const filteredMenuItems = computed(() => {
  return menuItems.value.filter(item => {
    // 这里可以添加权限检查逻辑
    return true
  })
})

// 方法
const toggleCollapsed = () => {
  collapsed.value = !collapsed.value
  appStore.setSidebarCollapsed(collapsed.value)
}

const handleMenuClick = ({ key }: { key: string }) => {
  selectedKeys.value = [key]
}

const handleLogout = async () => {
  try {
    await authStore.logout()
    message.success('退出登录成功')
    router.push('/login')
  } catch (error) {
    console.error('Logout error:', error)
    message.error('退出登录失败')
  }
}

// 角色文本转换
const getRoleText = (role?: string) => {
  const roleMap: Record<string, string> = {
    admin: '系统管理员',
    group_leader: '组长',
    member: '成员',
    guest: '访客'
  }
  return roleMap[role || 'guest'] || '未知角色'
}
</script>

<style scoped>
/* 🚀 现代响应式管理界面 - 零边框全屏适配 */
.desktop-layout {
  height: 100vh;
  width: 100vw;
  background: #f5f7fa;
  margin: 0;
  padding: 0;
  container-type: inline-size;
}

/* 左侧导航栏样式 */
.desktop-sider {
  background: #1e2139 !important;
  box-shadow: 2px 0 6px rgba(0,0,0,0.1);
}

.system-header {
  height: 80px;
  padding: 20px 24px;
  border-bottom: 1px solid #2a2d47;
  background: #1a1d36;
}

.logo-section {
  display: flex;
  align-items: center;
  gap: 12px;
  color: white;
}

.logo-icon {
  width: 40px;
  height: 40px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
  color: white;
}

.system-title h1 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: white;
}

.system-title p {
  margin: 0;
  font-size: 12px;
  color: #8892b0;
}

/* 主导航菜单样式 */
.main-menu {
  background: transparent !important;
  border-right: none !important;
  margin-top: 20px;
}

:deep(.main-menu .ant-menu-item) {
  margin: 4px 12px;
  border-radius: 8px;
  height: 48px;
  line-height: 48px;
  color: #8892b0;
  font-weight: 500;
}

:deep(.main-menu .ant-menu-item:hover) {
  background: rgba(255, 255, 255, 0.08) !important;
  color: white;
}

:deep(.main-menu .ant-menu-item-selected) {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
  color: white !important;
  font-weight: 600;
}

:deep(.main-menu .ant-menu-submenu-title) {
  margin: 4px 12px;
  border-radius: 8px;
  height: 48px;
  line-height: 48px;
  color: #8892b0;
  font-weight: 500;
}

:deep(.main-menu .ant-menu-submenu-title:hover) {
  background: rgba(255, 255, 255, 0.08) !important;
  color: white;
}

:deep(.main-menu .ant-menu-sub) {
  background: #242640 !important;
}

/* 侧边栏底部用户信息 */
.sidebar-footer {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  padding: 20px 24px;
  border-top: 1px solid #2a2d47;
  background: #1a1d36;
}

.current-user {
  display: flex;
  align-items: center;
  gap: 12px;
  color: white;
}

.user-info {
  flex: 1;
  overflow: hidden;
}

.user-name {
  font-size: 14px;
  font-weight: 500;
  margin-bottom: 2px;
}

.user-role {
  font-size: 12px;
  color: #8892b0;
}

/* 右侧主内容区域 */
.desktop-main {
  background: #f5f7fa;
}

/* 顶部工具栏 */
.desktop-header {
  background: white;
  box-shadow: 0 2px 8px rgba(0,0,0,0.06);
  border-bottom: 1px solid #e8e9ea;
  padding: 0;
  height: 64px;
  line-height: 64px;
}

.header-toolbar {
  height: 100%;
  padding: 0 32px;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.toolbar-left {
  display: flex;
  align-items: center;
  gap: 24px;
}

.collapse-btn {
  font-size: 18px;
  width: 40px;
  height: 40px;
}

.page-breadcrumb {
  font-size: 14px;
}

:deep(.page-breadcrumb .ant-breadcrumb-separator) {
  color: #8c8c8c;
  font-weight: 600;
}

.toolbar-right {
  display: flex;
  align-items: center;
}

.user-dropdown {
  padding: 8px 16px;
  height: auto;
  border-radius: 8px;
  transition: all 0.3s;
}

.user-dropdown:hover {
  background: #f5f5f5;
}

.user-dropdown .user-name {
  font-weight: 500;
  color: #262626;
}

/* 主内容区域 - 零边框充满设计 */
.desktop-content {
  padding: 16px;
  background: #f5f7fa;
  overflow-y: auto;
  height: calc(100vh - 64px);
}

.content-container {
  width: 100%;
  margin: 0;
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.04);
  padding: 16px;
  min-height: calc(100vh - 96px);
}

/* 用户菜单样式 */
:deep(.user-menu) {
  width: 200px;
  box-shadow: 0 4px 12px rgba(0,0,0,0.15);
}

/* 收缩状态适配 */
:deep(.ant-layout-sider-collapsed) .system-header {
  padding: 20px 16px;
  text-align: center;
}

:deep(.ant-layout-sider-collapsed) .logo-section {
  justify-content: center;
}

:deep(.ant-layout-sider-collapsed) .main-menu .ant-menu-item,
:deep(.ant-layout-sider-collapsed) .main-menu .ant-menu-submenu-title {
  margin: 4px 8px;
  text-align: center;
  padding-left: 0 !important;
  padding-right: 0 !important;
}

/* 🎯 Container Queries - 智能适配任何屏幕 */
@container (min-width: 1200px) {
  .content-container {
    padding: 24px;
    border-radius: 12px;
  }
  
  .desktop-content {
    padding: 24px;
  }
}

@container (min-width: 1600px) {
  .content-container {
    padding: 32px;
  }
  
  .desktop-content {
    padding: 32px;
  }
}

/* 移动端自适应 - 保持可用性 */
@container (max-width: 768px) {
  .desktop-content {
    padding: 8px;
  }
  
  .content-container {
    padding: 12px;
    border-radius: 0;
    min-height: calc(100vh - 80px);
  }
  
  .header-toolbar {
    padding: 0 16px;
  }
}
</style>