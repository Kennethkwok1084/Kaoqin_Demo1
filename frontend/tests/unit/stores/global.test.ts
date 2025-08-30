import { describe, it, expect, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useGlobalStore } from '@/stores/global'

describe('Global Store', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  describe('initial state', () => {
    it('should have correct initial state', () => {
      const globalStore = useGlobalStore()

      expect(globalStore.loading).toBe(false)
      expect(globalStore.sidebar.collapsed).toBe(false)
      expect(globalStore.breadcrumbs).toEqual([])
      expect(globalStore.theme).toBe('light')
      expect(globalStore.settings.showBreadcrumb).toBe(true)
      expect(globalStore.settings.showTabs).toBe(true)
    })
  })

  describe('loading management', () => {
    it('should set loading state', () => {
      const globalStore = useGlobalStore()

      globalStore.setLoading(true)
      expect(globalStore.loading).toBe(true)

      globalStore.setLoading(false)
      expect(globalStore.loading).toBe(false)
    })

    it('should show and hide loading', () => {
      const globalStore = useGlobalStore()

      globalStore.showLoading()
      expect(globalStore.loading).toBe(true)

      globalStore.hideLoading()
      expect(globalStore.loading).toBe(false)
    })
  })

  describe('sidebar management', () => {
    it('should toggle sidebar', () => {
      const globalStore = useGlobalStore()

      expect(globalStore.sidebar.collapsed).toBe(false)

      globalStore.toggleSidebar()
      expect(globalStore.sidebar.collapsed).toBe(true)

      globalStore.toggleSidebar()
      expect(globalStore.sidebar.collapsed).toBe(false)
    })

    it('should set sidebar collapsed state', () => {
      const globalStore = useGlobalStore()

      globalStore.setSidebarCollapsed(true)
      expect(globalStore.sidebar.collapsed).toBe(true)

      globalStore.setSidebarCollapsed(false)
      expect(globalStore.sidebar.collapsed).toBe(false)
    })
  })

  describe('breadcrumb management', () => {
    it('should set breadcrumbs', () => {
      const globalStore = useGlobalStore()
      const testBreadcrumbs = [
        { title: '首页', path: '/dashboard' },
        { title: '用户管理', path: '/users' }
      ]

      globalStore.setBreadcrumbs(testBreadcrumbs)
      expect(globalStore.breadcrumbs).toEqual(testBreadcrumbs)
    })

    it('should add breadcrumb', () => {
      const globalStore = useGlobalStore()
      const breadcrumb = { title: '首页', path: '/dashboard' }

      globalStore.addBreadcrumb(breadcrumb)
      expect(globalStore.breadcrumbs).toHaveLength(1)
      expect(globalStore.breadcrumbs[0]).toEqual(breadcrumb)
    })

    it('should clear breadcrumbs', () => {
      const globalStore = useGlobalStore()
      globalStore.breadcrumbs = [{ title: '首页', path: '/dashboard' }]

      globalStore.clearBreadcrumbs()
      expect(globalStore.breadcrumbs).toEqual([])
    })
  })

  describe('theme management', () => {
    it('should set theme', () => {
      const globalStore = useGlobalStore()

      globalStore.setTheme('dark')
      expect(globalStore.theme).toBe('dark')

      globalStore.setTheme('light')
      expect(globalStore.theme).toBe('light')
    })

    it('should toggle theme', () => {
      const globalStore = useGlobalStore()

      expect(globalStore.theme).toBe('light')

      globalStore.toggleTheme()
      expect(globalStore.theme).toBe('dark')

      globalStore.toggleTheme()
      expect(globalStore.theme).toBe('light')
    })
  })

  describe('settings management', () => {
    it('should update settings', () => {
      const globalStore = useGlobalStore()

      globalStore.updateSettings({ showBreadcrumb: false })
      expect(globalStore.settings.showBreadcrumb).toBe(false)
      expect(globalStore.settings.showTabs).toBe(true) // 其他设置保持不变

      globalStore.updateSettings({ showTabs: false, showBreadcrumb: true })
      expect(globalStore.settings.showTabs).toBe(false)
      expect(globalStore.settings.showBreadcrumb).toBe(true)
    })
  })

  describe('computed properties', () => {
    it('should compute isMobile correctly', () => {
      const globalStore = useGlobalStore()

      // Use setWindowWidth method to trigger reactive updates
      globalStore.setWindowWidth(1200)
      expect(globalStore.isMobile).toBe(false)

      globalStore.setWindowWidth(600)
      expect(globalStore.isMobile).toBe(true)
    })

    it('should compute isTablet correctly', () => {
      const globalStore = useGlobalStore()

      globalStore.setWindowWidth(1000)
      expect(globalStore.isTablet).toBe(true)

      globalStore.setWindowWidth(600)
      expect(globalStore.isTablet).toBe(false)
    })
  })
})
