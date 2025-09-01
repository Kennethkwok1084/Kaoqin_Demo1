// 全局应用状态管理
import { defineStore } from 'pinia'
import { ref, readonly } from 'vue'

export interface BreadcrumbItem {
  title: string
  path?: string
}

export interface MenuItem {
  key: string
  title: string
  icon?: string
  path?: string
  children?: MenuItem[]
  permission?: string
}

export const useAppStore = defineStore('app', () => {
  // 状态
  const loading = ref(false)
  const sidebarCollapsed = ref(false)
  const breadcrumb = ref<BreadcrumbItem[]>([])
  const pageTitle = ref('')

  // 菜单配置
  const menuItems = ref<MenuItem[]>([
    {
      key: 'dashboard',
      title: '仪表板',
      icon: 'dashboard',
      path: '/dashboard'
    },
    {
      key: 'tasks',
      title: '任务管理',
      icon: 'project',
      children: [
        { key: 'task-list', title: '任务列表', path: '/tasks' },
        { key: 'task-create', title: '创建任务', path: '/tasks/create', permission: 'manage_tasks' }
      ]
    },
    {
      key: 'members',
      title: '成员管理',
      icon: 'team',
      children: [
        { key: 'member-list', title: '成员列表', path: '/members' },
        { key: 'member-import', title: '批量导入', path: '/members/import', permission: 'import_data' }
      ],
      permission: 'manage_members'
    },
    {
      key: 'attendance',
      title: '考勤管理',
      icon: 'schedule',
      children: [
        { key: 'attendance-record', title: '考勤记录', path: '/attendance' },
        { key: 'work-hours', title: '工时管理', path: '/attendance/work-hours' }
      ]
    },
    {
      key: 'statistics',
      title: '统计报表',
      icon: 'bar-chart',
      children: [
        { key: 'stats-overview', title: '数据概览', path: '/statistics' },
        { key: 'stats-report', title: '详细报表', path: '/statistics/report' }
      ]
    },
    {
      key: 'settings',
      title: '系统设置',
      icon: 'setting',
      path: '/settings',
      permission: 'admin'
    }
  ])

  // 动作
  function setLoading(status: boolean) {
    loading.value = status
  }

  function toggleSidebar() {
    sidebarCollapsed.value = !sidebarCollapsed.value
  }

  function setSidebarCollapsed(collapsed: boolean) {
    sidebarCollapsed.value = collapsed
  }

  function setBreadcrumb(items: BreadcrumbItem[]) {
    breadcrumb.value = items
  }

  function setPageTitle(title: string) {
    pageTitle.value = title
    document.title = title ? `${title} - 考勤管理系统` : '考勤管理系统'
  }

  // 根据路径生成面包屑
  function generateBreadcrumb(path: string) {
    const items: BreadcrumbItem[] = [
      { title: '首页', path: '/dashboard' }
    ]

    const pathSegments = path.split('/').filter(Boolean)
    
    // 根据路径生成面包屑逻辑
    if (pathSegments[0] === 'tasks') {
      items.push({ title: '任务管理', path: '/tasks' })
      if (pathSegments[1] === 'create') {
        items.push({ title: '创建任务' })
      } else if (pathSegments[1]) {
        items.push({ title: '任务详情' })
      }
    } else if (pathSegments[0] === 'members') {
      items.push({ title: '成员管理', path: '/members' })
      if (pathSegments[1] === 'import') {
        items.push({ title: '批量导入' })
      } else if (pathSegments[1]) {
        items.push({ title: '成员详情' })
      }
    } else if (pathSegments[0] === 'attendance') {
      items.push({ title: '考勤管理', path: '/attendance' })
      if (pathSegments[1] === 'work-hours') {
        items.push({ title: '工时管理' })
      }
    } else if (pathSegments[0] === 'statistics') {
      items.push({ title: '统计报表', path: '/statistics' })
      if (pathSegments[1] === 'report') {
        items.push({ title: '详细报表' })
      }
    } else if (pathSegments[0] === 'settings') {
      items.push({ title: '系统设置' })
    }

    setBreadcrumb(items)
  }

  // 获取过滤后的菜单（根据权限）
  function getFilteredMenuItems(hasPermission: (permission: string) => boolean) {
    function filterMenuItem(item: MenuItem): MenuItem | null {
      // 检查权限
      if (item.permission && !hasPermission(item.permission)) {
        return null
      }

      // 处理子菜单
      if (item.children) {
        const filteredChildren = item.children
          .map(child => filterMenuItem(child))
          .filter(Boolean) as MenuItem[]
        
        if (filteredChildren.length === 0) {
          return null
        }

        return {
          ...item,
          children: filteredChildren
        }
      }

      return item
    }

    return menuItems.value
      .map(item => filterMenuItem(item))
      .filter(Boolean) as MenuItem[]
  }

  // 响应式设计断点
  const breakpoints = {
    xs: '480px',
    sm: '576px',
    md: '768px',
    lg: '992px',
    xl: '1200px',
    xxl: '1600px'
  }

  return {
    // 状态
    loading: readonly(loading),
    sidebarCollapsed: readonly(sidebarCollapsed),
    breadcrumb: readonly(breadcrumb),
    pageTitle: readonly(pageTitle),
    menuItems: readonly(menuItems),
    breakpoints,
    
    // 动作
    setLoading,
    toggleSidebar,
    setSidebarCollapsed,
    setBreadcrumb,
    setPageTitle,
    generateBreadcrumb,
    getFilteredMenuItems
  }
})