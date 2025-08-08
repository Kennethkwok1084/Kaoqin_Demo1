import { defineStore } from 'pinia'

export const useGlobalStore = defineStore('global', {
  state: () => ({
    isLoading: false,
    appTitle: import.meta.env.VITE_APP_TITLE || '考勤管理系统'
  }),

  actions: {
    setLoading(loading: boolean) {
      this.isLoading = loading
    },

    async initializeApp() {
      this.setLoading(true)
      
      try {
        // 应用初始化逻辑
        await new Promise(resolve => setTimeout(resolve, 500))
      } catch (error) {
        console.error('App initialization failed:', error)
      } finally {
        this.setLoading(false)
      }
    }
  }
})