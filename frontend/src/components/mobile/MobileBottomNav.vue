<template>
  <div class="mobile-bottom-nav visible-xs">
    <div class="nav-items">
      <div 
        v-for="item in navItems" 
        :key="item.path"
        class="nav-item"
        :class="{ active: isActive(item.path) }"
        @click="navigateTo(item.path)"
      >
        <div class="nav-icon">
          <el-icon :size="20">
            <component :is="item.icon" />
          </el-icon>
        </div>
        <div class="nav-label">{{ item.label }}</div>
        <div v-if="item.badge" class="nav-badge">{{ item.badge }}</div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { 
  Monitor, 
  Document, 
  User, 
  Clock, 
  DataLine 
} from '@element-plus/icons-vue'

// 路由
const route = useRoute()
const router = useRouter()

// 导航项配置
const navItems = [
  {
    path: '/dashboard',
    label: '首页',
    icon: Monitor
  },
  {
    path: '/tasks',
    label: '任务',
    icon: Document,
    // badge: 5 // 可选的徽章数量
  },
  {
    path: '/members',
    label: '成员',
    icon: User
  },
  {
    path: '/attendance',
    label: '考勤',
    icon: Clock
  },
  {
    path: '/statistics',
    label: '统计',
    icon: DataLine
  }
]

// 检查当前路由是否激活
const isActive = (path: string) => {
  if (path === '/dashboard') {
    return route.path === path
  }
  return route.path.startsWith(path)
}

// 导航到指定路径
const navigateTo = (path: string) => {
  if (path === '/tasks') {
    // 任务默认跳转到维修任务
    router.push('/tasks/repair')
  } else {
    router.push(path)
  }
}
</script>

<style scoped lang="scss">
@use '@/styles/variables.scss' as *;
@use '@/styles/mixins.scss' as *;

.mobile-bottom-nav {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  height: 60px;
  background: $background-color-white;
  border-top: 1px solid $border-color-light;
  box-shadow: 0 -2px 8px rgba(0, 0, 0, 0.1);
  z-index: 999;
  @include safe-area-padding;
  padding-bottom: env(safe-area-inset-bottom, 0px);
  
  .nav-items {
    display: flex;
    height: 100%;
    align-items: center;
    
    .nav-item {
      flex: 1;
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      position: relative;
      cursor: pointer;
      transition: all $transition-base;
      padding: $spacing-extra-small 0;
      @include touch-target(60px);
      
      &:active {
        background: $background-color-light;
      }
      
      &.active {
        .nav-icon {
          color: $primary-color;
          transform: scale(1.1);
        }
        
        .nav-label {
          color: $primary-color;
          font-weight: 600;
        }
      }
      
      .nav-icon {
        margin-bottom: 2px;
        color: $text-color-secondary;
        transition: all $transition-base;
      }
      
      .nav-label {
        font-size: 10px;
        color: $text-color-secondary;
        transition: all $transition-base;
        line-height: 1.2;
        text-align: center;
      }
      
      .nav-badge {
        position: absolute;
        top: 4px;
        right: 50%;
        transform: translateX(10px);
        background: $danger-color;
        color: white;
        font-size: 10px;
        min-width: 16px;
        height: 16px;
        border-radius: 8px;
        display: flex;
        align-items: center;
        justify-content: center;
        line-height: 1;
        padding: 0 4px;
      }
    }
  }
}

// 为页面内容留出底部导航的空间
:global(.content-area) {
  @include mobile-only {
    padding-bottom: calc(#{$spacing-small} + 60px + env(safe-area-inset-bottom, 0px)) !important;
  }
}
</style>