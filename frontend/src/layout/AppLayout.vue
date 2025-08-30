<template>
  <div class="app-container">
    <!-- 移动端侧边栏蒙层 -->
    <div
      class="sidebar-overlay"
      :class="{ visible: showMobileSidebar }"
      @click="closeMobileSidebar"
    ></div>

    <div
      class="layout-container"
      :class="{
        collapsed: sidebarCollapsed,
        'mobile-sidebar-open': showMobileSidebar
      }"
    >
      <!-- 侧边栏 -->
      <aside
        class="sidebar"
        :class="{
          collapsed: sidebarCollapsed,
          'mobile-visible': showMobileSidebar
        }"
      >
        <div class="sidebar-header">
          <div class="logo">
            <div class="logo-icon">
              <el-icon size="28" color="#409EFF"><Odometer /></el-icon>
            </div>
            <span v-show="!sidebarCollapsed" class="logo-text">考勤系统</span>
          </div>
        </div>

        <div class="sidebar-content">
          <el-menu
            :default-active="activeMenuIndex"
            :collapse="sidebarCollapsed"
            :unique-opened="true"
            router
            class="sidebar-menu"
          >
            <el-menu-item index="/dashboard">
              <el-icon><Monitor /></el-icon>
              <template #title>仪表板</template>
            </el-menu-item>

            <el-sub-menu index="tasks">
              <template #title>
                <el-icon><Document /></el-icon>
                <span>任务管理</span>
              </template>
              <el-menu-item index="/tasks/repair">维修任务</el-menu-item>
              <el-menu-item index="/tasks/monitoring">监控任务</el-menu-item>
              <el-menu-item index="/tasks/assistance">协助任务</el-menu-item>
            </el-sub-menu>

            <el-menu-item index="/members">
              <el-icon><User /></el-icon>
              <template #title>成员管理</template>
            </el-menu-item>

            <el-menu-item index="/attendance">
              <el-icon><Clock /></el-icon>
              <template #title>考勤管理</template>
            </el-menu-item>

            <el-menu-item index="/statistics">
              <el-icon><DataLine /></el-icon>
              <template #title>统计报表</template>
            </el-menu-item>

            <el-menu-item index="/settings" v-if="authStore.isAdmin">
              <el-icon><Setting /></el-icon>
              <template #title>系统设置</template>
            </el-menu-item>
          </el-menu>
        </div>
      </aside>

      <!-- 主内容区域 -->
      <div class="main-content">
        <!-- 头部 -->
        <header class="app-header">
          <div class="header-left">
            <!-- 桌面端侧边栏切换 -->
            <el-button
              type="text"
              size="default"
              @click="toggleSidebar"
              class="sidebar-toggle desktop-only"
            >
              <el-icon><Menu /></el-icon>
            </el-button>

            <!-- 移动端菜单切换 -->
            <el-button
              type="text"
              size="default"
              @click="toggleMobileSidebar"
              class="mobile-menu-toggle mobile-only"
            >
              <el-icon><Menu /></el-icon>
            </el-button>

            <el-breadcrumb separator="/" class="breadcrumb hidden-xs">
              <el-breadcrumb-item
                v-for="item in breadcrumbList"
                :key="item.path"
                :to="item.path"
              >
                {{ item.title }}
              </el-breadcrumb-item>
            </el-breadcrumb>
          </div>

          <div class="header-right">
            <!-- 全屏切换 (桌面端) -->
            <el-tooltip content="全屏" placement="bottom" class="hidden-xs">
              <el-button type="text" size="default" @click="toggleFullscreen">
                <el-icon><FullScreen /></el-icon>
              </el-button>
            </el-tooltip>

            <!-- 通知 -->
            <el-badge
              :value="notificationCount"
              :hidden="notificationCount === 0"
            >
              <el-button type="text" size="default" @click="showNotifications">
                <el-icon><Bell /></el-icon>
              </el-button>
            </el-badge>

            <!-- 用户菜单 -->
            <el-dropdown @command="handleUserMenuCommand" class="user-dropdown">
              <div class="user-info">
                <el-avatar :size="32" :src="authStore.userInfo?.avatar">
                  {{ authStore.userInfo?.full_name?.charAt(0) }}
                </el-avatar>
                <span class="username hidden-xs">{{
                  authStore.userInfo?.full_name
                }}</span>
                <el-icon class="dropdown-icon hidden-xs"><ArrowDown /></el-icon>
              </div>

              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item command="profile">
                    <el-icon><User /></el-icon>
                    个人资料
                  </el-dropdown-item>
                  <el-dropdown-item command="settings">
                    <el-icon><Setting /></el-icon>
                    账户设置
                  </el-dropdown-item>
                  <el-dropdown-item divided command="logout">
                    <el-icon><SwitchButton /></el-icon>
                    退出登录
                  </el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </div>
        </header>

        <!-- 内容区域 -->
        <main class="content-area">
          <router-view v-slot="{ Component }">
            <transition name="fade-transform" mode="out-in">
              <component :is="Component" />
            </transition>
          </router-view>
        </main>
      </div>
    </div>

    <!-- 移动端底部导航 -->
    <MobileBottomNav />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessageBox, ElMessage } from 'element-plus'
import {
  Menu,
  Monitor,
  Document,
  User,
  Clock,
  DataLine,
  Setting,
  FullScreen,
  Bell,
  ArrowDown,
  SwitchButton,
  Odometer
} from '@element-plus/icons-vue'
import { useAuthStore } from '@/stores/auth'
import { useGlobalStore } from '@/stores/global'
import MobileBottomNav from '@/components/mobile/MobileBottomNav.vue'

// 路由和store
const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()
// eslint-disable-next-line @typescript-eslint/no-unused-vars
const globalStore = useGlobalStore()

// 响应式数据
const sidebarCollapsed = ref(false)
const showMobileSidebar = ref(false)
const notificationCount = ref(3) // 模拟通知数量

// 检查是否为移动端
const isMobile = computed(() => window.innerWidth <= 768)

// 计算属性
const activeMenuIndex = computed(() => route.path)

const breadcrumbList = computed(() => {
  const matched = route.matched.filter(item => item.meta?.title)
  return matched.map(item => ({
    title: item.meta?.title,
    path: item.path
  }))
})

// 方法
const toggleSidebar = () => {
  if (isMobile.value) {
    toggleMobileSidebar()
  } else {
    sidebarCollapsed.value = !sidebarCollapsed.value
  }
}

const toggleMobileSidebar = () => {
  showMobileSidebar.value = !showMobileSidebar.value
}

const closeMobileSidebar = () => {
  showMobileSidebar.value = false
}

const toggleFullscreen = () => {
  if (!document.fullscreenElement) {
    document.documentElement.requestFullscreen()
  } else {
    document.exitFullscreen()
  }
}

const showNotifications = () => {
  ElMessage.info('通知功能开发中...')
}

const handleUserMenuCommand = async (command: string) => {
  switch (command) {
    case 'profile':
      router.push('/profile')
      break
    case 'settings':
      router.push('/account/settings')
      break
    case 'logout':
      try {
        await ElMessageBox.confirm('确定要退出登录吗？', '退出确认', {
          confirmButtonText: '确定',
          cancelButtonText: '取消',
          type: 'warning'
        })
        await authStore.logout()
        ElMessage.success('已安全退出')
      } catch {
        // 用户取消
      }
      break
  }
}

// 监听路由变化
watch(
  () => route.path,
  () => {
    // 移动端路由切换时关闭侧边栏
    if (isMobile.value) {
      showMobileSidebar.value = false
    }
  }
)

// 监听窗口大小变化
const handleResize = () => {
  if (window.innerWidth > 768) {
    showMobileSidebar.value = false
  }
}

// 生命周期
onMounted(() => {
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
})
</script>

<style scoped lang="scss">
@use '@/styles/variables.scss' as *;
@use '@/styles/mixins.scss' as *;
@use 'sass:color';

.app-container {
  height: 100vh;
  overflow: hidden;
}

.layout-container {
  @include flex-start;
  height: 100%;

  &.collapsed {
    .sidebar {
      width: $sidebar-collapsed-width;
    }

    .main-content {
      margin-left: $sidebar-collapsed-width;
    }
  }
}

.sidebar {
  position: fixed;
  top: 0;
  left: 0;
  width: $sidebar-width;
  height: 100vh;
  background: $background-color-white;
  border-right: 1px solid $border-color-light;
  box-shadow: 2px 0 6px rgba(0, 0, 0, 0.1);
  transition: width $transition-base;
  z-index: 1000;
  overflow: hidden;

  &.collapsed {
    width: $sidebar-collapsed-width;
  }

  .sidebar-header {
    height: $header-height;
    @include flex-center;
    border-bottom: 1px solid $border-color-extra-light;
    padding: 0 $spacing-base;

    .logo {
      @include flex-center;
      gap: $spacing-small;

      .logo-icon {
        width: 32px;
        height: 32px;
        @include flex-center;
        border-radius: 50%;
        background: color.adjust($primary-color, $lightness: 45%);
      }

      .logo-text {
        font-size: $font-size-medium;
        font-weight: 600;
        color: $primary-color;
      }
    }
  }

  .sidebar-content {
    height: calc(100vh - #{$header-height});
    overflow-y: auto;

    .sidebar-menu {
      border: none;

      .el-menu-item,
      .el-sub-menu__title {
        height: 50px;
        line-height: 50px;

        &:hover {
          background: $background-color-light;
        }

        &.is-active {
          background: color.adjust($primary-color, $lightness: 45%);
          color: $primary-color;
          border-right: 3px solid $primary-color;
        }
      }
    }
  }
}

.main-content {
  flex: 1;
  margin-left: $sidebar-width;
  height: 100vh;
  @include flex-column;
  transition: margin-left $transition-base;
  overflow: hidden;
}

.app-header {
  height: $header-height;
  background: $background-color-white;
  border-bottom: 1px solid $border-color-light;
  @include flex-between;
  padding: 0 $spacing-base;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.08);
  z-index: 999;

  .header-left {
    @include flex-start;
    gap: $spacing-base;

    .sidebar-toggle {
      .el-icon {
        font-size: 18px;
      }
    }

    .breadcrumb {
      font-size: $font-size-small;
    }
  }

  .header-right {
    @include flex-end;
    gap: $spacing-small;

    .user-dropdown {
      .user-info {
        @include flex-center;
        gap: $spacing-small;
        padding: $spacing-small;
        border-radius: $border-radius-base;
        cursor: pointer;
        transition: background-color $transition-base;

        &:hover {
          background: $background-color-light;
        }

        .username {
          font-size: $font-size-small;
          color: $text-color-primary;
          font-weight: 500;
        }

        .dropdown-icon {
          font-size: 12px;
          color: $text-color-secondary;
        }
      }
    }
  }
}

.content-area {
  flex: 1;
  padding: $spacing-base;
  overflow-y: auto;
  overflow-x: hidden;
  background: $background-color-base;
}

// 页面切换动画
.fade-transform-enter-active,
.fade-transform-leave-active {
  transition: all 0.3s ease;
}

.fade-transform-enter-from {
  opacity: 0;
  transform: translateX(30px);
}

.fade-transform-leave-to {
  opacity: 0;
  transform: translateX(-30px);
}

.sidebar-overlay {
  display: none;
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  z-index: 1000;
  transition: opacity $transition-base;

  &.visible {
    display: block;
  }
}

// 移动端专用样式
.mobile-only {
  display: none;

  @include mobile-only {
    display: block;
  }
}

.desktop-only {
  @include mobile-only {
    display: none;
  }
}

// 响应式设计
@include mobile-and-tablet {
  .layout-container {
    &.mobile-sidebar-open {
      .sidebar {
        transform: translateX(0);
      }
    }
  }

  .sidebar {
    width: 280px;
    transform: translateX(-100%);
    transition: transform $transition-base;
    z-index: 1001;
    @include safe-area-padding;

    &.mobile-visible {
      transform: translateX(0);
    }

    &.collapsed {
      width: 280px;
      transform: translateX(-100%);

      &.mobile-visible {
        transform: translateX(0);
      }
    }

    .sidebar-menu {
      .el-menu-item,
      .el-submenu__title {
        height: 50px;
        line-height: 50px;
        font-size: $font-size-base;
        @include touch-target(50px);
      }

      .el-submenu {
        .el-menu-item {
          height: 45px;
          line-height: 45px;
          padding-left: 50px !important;
        }
      }
    }
  }

  .main-content {
    margin-left: 0;
    width: 100%;
  }

  .layout-container.collapsed {
    .main-content {
      margin-left: 0;
    }
  }
}

@include mobile-only {
  .app-header {
    position: sticky;
    top: 0;
    @include safe-area-padding;
    padding: $spacing-small;
    height: calc(#{$header-height} + env(safe-area-inset-top, 0px));

    .header-left {
      .mobile-menu-toggle {
        @include touch-target(44px);
        margin-right: $spacing-small;
      }
    }

    .header-right {
      gap: $spacing-small;

      .user-dropdown .user-info {
        .username,
        .dropdown-icon {
          display: none;
        }
      }
    }
  }

  .content-area {
    padding: $spacing-small;
    @include mobile-scroll;
    @include safe-area-padding;
    padding-bottom: calc(#{$spacing-small} + env(safe-area-inset-bottom, 0px));
  }
}
</style>
