import { createApp } from 'vue'
import { createPinia } from 'pinia'
import ElementPlus from 'element-plus'
import * as ElementPlusIconsVue from '@element-plus/icons-vue'

import App from './App.vue'
import router from './router'
import { useAuthStore } from '@/stores/auth'

// 样式导入
import 'element-plus/dist/index.css'
import '@/styles/index.scss'

// 全局类型声明
declare global {
  interface Window {
    __APP_VERSION__: string
  }
}

const app = createApp(App)

// 注册 Element Plus 图标
for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
  app.component(key, component)
}

// 安装插件
const pinia = createPinia()
app.use(pinia)
app.use(router)
app.use(ElementPlus, {
  size: 'default',
  zIndex: 3000
})

// 全局属性
app.config.globalProperties.$version = import.meta.env.VITE_APP_VERSION

// 全局错误处理
app.config.errorHandler = (err, _instance, info) => {
  console.error('Global error:', err, info)
  // 这里可以集成错误监控服务
}

// 初始化认证状态并挂载应用
const authStore = useAuthStore()
authStore.initAuth().finally(() => {
  app.mount('#app')
})
