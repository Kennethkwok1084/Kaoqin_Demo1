<script setup lang="ts">
import { onMounted } from 'vue'
import { RouterView, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useAppStore } from '@/stores/app'
import AppLayout from '@/components/layout/AppLayout.vue'

const route = useRoute()
const authStore = useAuthStore()
const appStore = useAppStore()

onMounted(async () => {
  // 初始化认证状态
  await authStore.initializeAuth()
  
  // 设置页面标题和面包屑
  appStore.generateBreadcrumb(route.path)
})
</script>

<template>
  <div class="app">
    <!-- 登录页不使用布局 -->
    <template v-if="route.name === 'login'">
      <RouterView />
    </template>
    
    <!-- 其他页面使用应用布局 -->
    <template v-else>
      <AppLayout>
        <RouterView />
      </AppLayout>
    </template>
  </div>
</template>

<style>
/* 全局样式重置 */
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

html, body {
  height: 100%;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
}

#app {
  height: 100%;
}

.app {
  height: 100%;
}

/* Ant Design 主题定制 */
:root {
  --ant-primary-color: #1890ff;
  --ant-success-color: #52c41a;
  --ant-warning-color: #faad14;
  --ant-error-color: #ff4d4f;
  --ant-font-size-base: 14px;
  --ant-line-height-base: 1.5715;
  --ant-border-radius-base: 6px;
}

/* 响应式断点 */
@media (max-width: 576px) {
  .ant-table {
    font-size: 12px;
  }
  
  .ant-btn {
    padding: 4px 8px;
    font-size: 12px;
  }
}

/* 自定义滚动条 */
::-webkit-scrollbar {
  width: 8px;
  height: 8px;
}

::-webkit-scrollbar-track {
  background: #f1f1f1;
  border-radius: 4px;
}

::-webkit-scrollbar-thumb {
  background: #c1c1c1;
  border-radius: 4px;
}

::-webkit-scrollbar-thumb:hover {
  background: #a8a8a8;
}

/* 工具类 */
.text-center {
  text-align: center;
}

.text-right {
  text-align: right;
}

.text-left {
  text-align: left;
}

.flex-center {
  display: flex;
  align-items: center;
  justify-content: center;
}

.flex-between {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.full-height {
  height: 100%;
}

.full-width {
  width: 100%;
}

.cursor-pointer {
  cursor: pointer;
}

.no-select {
  user-select: none;
}

/* 动画 */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

.slide-enter-active,
.slide-leave-active {
  transition: transform 0.3s ease;
}

.slide-enter-from {
  transform: translateX(-100%);
}

.slide-leave-to {
  transform: translateX(100%);
}
</style>
