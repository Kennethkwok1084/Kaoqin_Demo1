import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

interface Breadcrumb {
  title: string
  path: string
}

interface Settings {
  showBreadcrumb: boolean
  showTabs: boolean
}

export const useGlobalStore = defineStore('global', () => {
  // 状态
  const loading = ref(false)
  const appTitle = ref(import.meta.env.VITE_APP_TITLE || '考勤管理系统')
  const sidebar = ref({
    collapsed: false
  })
  const breadcrumbs = ref<Breadcrumb[]>([])
  const theme = ref<'light' | 'dark'>('light')
  const settings = ref<Settings>({
    showBreadcrumb: true,
    showTabs: true
  })

  // 响应式窗口尺寸
  const windowWidth = ref(
    typeof window !== 'undefined' ? window.innerWidth : 1024
  )

  // 计算属性
  const isMobile = computed(() => windowWidth.value < 768)

  const isTablet = computed(
    () => windowWidth.value >= 768 && windowWidth.value < 1024
  )

  // 监听窗口尺寸变化
  if (typeof window !== 'undefined') {
    const handleResize = () => {
      windowWidth.value = window.innerWidth
    }
    window.addEventListener('resize', handleResize)
  }

  // 加载管理
  const setLoading = (isLoading: boolean) => {
    loading.value = isLoading
  }

  const showLoading = () => {
    loading.value = true
  }

  const hideLoading = () => {
    loading.value = false
  }

  // 侧边栏管理
  const toggleSidebar = () => {
    sidebar.value.collapsed = !sidebar.value.collapsed
  }

  const setSidebarCollapsed = (collapsed: boolean) => {
    sidebar.value.collapsed = collapsed
  }

  // 面包屑管理
  const setBreadcrumbs = (items: Breadcrumb[]) => {
    breadcrumbs.value = items
  }

  const addBreadcrumb = (item: Breadcrumb) => {
    breadcrumbs.value.push(item)
  }

  const clearBreadcrumbs = () => {
    breadcrumbs.value = []
  }

  // 主题管理
  const setTheme = (newTheme: 'light' | 'dark') => {
    theme.value = newTheme
  }

  const toggleTheme = () => {
    theme.value = theme.value === 'light' ? 'dark' : 'light'
  }

  // 设置管理
  const updateSettings = (newSettings: Partial<Settings>) => {
    settings.value = { ...settings.value, ...newSettings }
  }

  // 应用初始化
  const initializeApp = async () => {
    setLoading(true)

    try {
      // 预留初始化钩子，避免伪造异步延迟影响页面判断
      await Promise.resolve()
    } catch (error) {
      console.error('App initialization failed:', error)
    } finally {
      setLoading(false)
    }
  }

  // 测试辅助方法 - 手动设置窗口宽度
  const setWindowWidth = (width: number) => {
    windowWidth.value = width
  }

  return {
    // 状态
    loading,
    appTitle,
    sidebar,
    breadcrumbs,
    theme,
    settings,

    // 计算属性
    isMobile,
    isTablet,

    // 方法
    setLoading,
    showLoading,
    hideLoading,
    toggleSidebar,
    setSidebarCollapsed,
    setBreadcrumbs,
    addBreadcrumb,
    clearBreadcrumbs,
    setTheme,
    toggleTheme,
    updateSettings,
    initializeApp,
    setWindowWidth
  }
})
