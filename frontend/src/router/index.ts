import { createRouter, createWebHistory } from 'vue-router'
import type { RouteRecordRaw } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { getToken } from '@/utils/auth'

const routes: RouteRecordRaw[] = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/auth/LoginView.vue'),
    meta: {
      title: '登录',
      requiresAuth: false,
      hideInMenu: true
    }
  },
  {
    path: '/complete-profile',
    name: 'CompleteProfile',
    component: () => import('@/views/auth/CompleteProfile.vue'),
    meta: {
      title: '完善个人信息',
      requiresAuth: true,
      hideInMenu: true
    }
  },
  {
    path: '/',
    name: 'Layout',
    component: () => import('@/layout/AppLayout.vue'),
    redirect: '/dashboard',
    meta: {
      requiresAuth: true
    },
    children: [
      {
        path: 'dashboard',
        name: 'Dashboard',
        component: () => import('@/views/dashboard/Dashboard.vue'),
        meta: {
          title: '仪表板',
          icon: 'Dashboard',
          requiresAuth: true
        }
      },
      {
        path: 'tasks',
        name: 'TaskList',
        component: () => import('@/views/tasks/TaskList.vue'),
        meta: {
          title: '任务管理',
          icon: 'Document',
          requiresAuth: true
        }
      },
      {
        path: 'tasks/repair',
        name: 'RepairTasks',
        component: () => import('@/views/tasks/RepairTaskList.vue'),
        meta: {
          title: '维修任务',
          requiresAuth: true
        }
      },
      {
        path: 'tasks/monitoring',
        name: 'MonitoringTasks',
        component: () => import('@/views/tasks/MonitoringTaskList.vue'),
        meta: {
          title: '监控任务',
          requiresAuth: true
        }
      },
      {
        path: 'tasks/assistance',
        name: 'AssistanceTasks',
        component: () => import('@/views/tasks/AssistanceTaskList.vue'),
        meta: {
          title: '协助任务',
          requiresAuth: true
        }
      },
      {
        path: 'members',
        name: 'MemberList',
        component: () => import('@/views/members/index.vue'),
        meta: {
          title: '成员管理',
          icon: 'User',
          requiresAuth: true,
          roles: ['admin']
        }
      },
      {
        path: 'attendance',
        name: 'WorkHoursView',
        component: () => import('@/views/attendance/WorkHoursView.vue'),
        meta: {
          title: '工时管理',
          icon: 'Timer',
          requiresAuth: true
        }
      },
      {
        path: 'statistics',
        name: 'StatisticsReport',
        component: () => import('@/views/statistics/StatisticsReport.vue'),
        meta: {
          title: '统计报表',
          icon: 'DataAnalysis',
          requiresAuth: true
        }
      },
      {
        path: 'work-hours',
        name: 'WorkHoursList',
        component: () => import('@/views/workHours/WorkHoursList.vue'),
        meta: {
          title: '工时管理',
          icon: 'Timer',
          requiresAuth: true
        }
      },
      {
        path: 'data-import',
        name: 'DataImportList',
        component: () => import('@/views/dataImport/DataImportList.vue'),
        meta: {
          title: '数据导入',
          icon: 'Upload',
          requiresAuth: true,
          roles: ['admin']
        }
      },
      {
        path: 'settings',
        name: 'Settings',
        component: () => import('@/views/settings/Settings.vue'),
        meta: {
          title: '系统设置',
          icon: 'Setting',
          requiresAuth: true,
          roles: ['admin']
        }
      }
    ]
  },
  {
    path: '/403',
    name: 'Forbidden',
    component: () => import('@/views/error/403.vue'),
    meta: {
      title: '权限不足',
      hideInMenu: true
    }
  },
  {
    path: '/404',
    name: 'NotFound',
    component: () => import('@/views/error/404.vue'),
    meta: {
      title: '页面不存在',
      hideInMenu: true
    }
  },
  {
    path: '/:pathMatch(.*)*',
    redirect: '/404'
  }
]

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes,
  scrollBehavior(_to, _from, savedPosition) {
    if (savedPosition) {
      return savedPosition
    } else {
      return { top: 0 }
    }
  }
})

// 路由守卫
router.beforeEach(async (to, _from, next) => {
  // 设置页面标题
  if (to.meta?.title) {
    document.title = `${to.meta.title} - 考勤管理系统`
  }

  const token = getToken()
  const requiresAuth = to.meta?.requiresAuth !== false

  // 如果路由需要认证
  if (requiresAuth) {
    if (!token) {
      // 没有token，跳转到登录页
      next({
        path: '/login',
        query: { redirect: to.fullPath }
      })
      return
    }

    // 有token，检查用户信息
    const authStore = useAuthStore()
    if (!authStore.userInfo) {
      try {
        // 尝试获取用户信息
        await authStore.fetchUserInfo()
      } catch (error) {
        // 获取用户信息失败，跳转到登录页
        next({
          path: '/login',
          query: { redirect: to.fullPath }
        })
        return
      }
    }

    // 检查权限
    if (
      to.meta?.permission &&
      !authStore.checkPermission(to.meta.permission as string)
    ) {
      next('/403')
      return
    }

    // 检查角色
    if (
      to.meta?.roles &&
      Array.isArray(to.meta.roles) &&
      !to.meta.roles.includes(authStore.userInfo?.role)
    ) {
      next('/403')
      return
    }

    // 检查是否需要完善信息
    if (authStore.needsProfileCompletion && to.name !== 'CompleteProfile') {
      // 需要完善信息且不是在信息完善页面，跳转到信息完善页面
      next({
        path: '/complete-profile',
        query: { redirect: to.fullPath }
      })
      return
    }

    // 如果是信息完善页面但不需要完善，跳转到主页
    if (to.name === 'CompleteProfile' && !authStore.needsProfileCompletion) {
      next('/dashboard')
      return
    }
  } else {
    // 路由不需要认证
    if (to.path === '/login' && token) {
      // 已登录用户访问登录页，检查是否需要完善信息
      const authStore = useAuthStore()
      if (authStore.needsProfileCompletion) {
        next('/complete-profile')
      } else {
        next('/dashboard')
      }
      return
    }
  }

  next()
})

export default router
