<template>
  <div id="app">
    <router-view />
    <!-- 全局加载器 -->
    <Teleport to="body">
      <GlobalLoading v-if="globalStore.isLoading" />
    </Teleport>
  </div>
</template>

<script setup lang="ts">
import { onMounted } from 'vue'
import { useGlobalStore } from '@/stores/global'
import GlobalLoading from '@/components/common/GlobalLoading.vue'

const globalStore = useGlobalStore()

onMounted(() => {
  // 初始化应用
  globalStore.initializeApp()

  // 设置页面标题
  document.title = import.meta.env.VITE_APP_TITLE

  // 设置全局版本号
  window.__APP_VERSION__ = import.meta.env.VITE_APP_VERSION
})
</script>

<style lang="scss">
#app {
  height: 100vh;
  font-family:
    'Helvetica Neue', Helvetica, 'PingFang SC', 'Hiragino Sans GB',
    'Microsoft YaHei', '微软雅黑', Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

// 全局滚动条样式
::-webkit-scrollbar {
  width: 6px;
  height: 6px;
}

::-webkit-scrollbar-track {
  background: #f1f1f1;
}

::-webkit-scrollbar-thumb {
  background: #c1c1c1;
  border-radius: 3px;
}

::-webkit-scrollbar-thumb:hover {
  background: #a8a8a8;
}

// 全局动画
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

.slide-up-enter-active,
.slide-up-leave-active {
  transition: all 0.3s ease;
}

.slide-up-enter-from {
  transform: translateY(10px);
  opacity: 0;
}

.slide-up-leave-to {
  transform: translateY(-10px);
  opacity: 0;
}
</style>
