import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/login',
      name: 'login',
      component: () => import('@/views/auth/LoginView.vue'),
      meta: { requiresGuest: true }
    },
    {
      path: '/',
      redirect: '/dashboard'
    },
    {
      path: '/dashboard',
      name: 'dashboard', 
      component: () => import('@/views/dashboard/Dashboard.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/tasks',
      name: 'tasks',
      component: () => import('@/views/tasks/TaskList.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/tasks/create',
      name: 'task-create',
      component: () => import('@/views/tasks/TaskCreate.vue'),
      meta: { requiresAuth: true, permission: 'manage_tasks' }
    },
    {
      path: '/tasks/assistance-review',
      name: 'assistance-review',
      component: () => import('@/views/tasks/AssistanceTaskReview.vue'),
      meta: { requiresAuth: true, permission: 'admin' }
    },
    {
      path: '/members',
      name: 'members',
      component: () => import('@/views/members/MemberList.vue'),
      meta: { requiresAuth: true, permission: 'manage_members' }
    },
    {
      path: '/members/import',
      name: 'member-import',
      component: () => import('@/views/members/MemberImport.vue'),
      meta: { requiresAuth: true, permission: 'import_data' }
    },
    {
      path: '/attendance',
      name: 'attendance',
      component: () => import('@/views/attendance/AttendanceList.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/attendance/work-hours',
      name: 'work-hours',
      component: () => import('@/views/attendance/WorkHours.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/statistics',
      name: 'statistics',
      component: () => import('@/views/statistics/Statistics.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/statistics/report',
      name: 'statistics-report',
      component: () => import('@/views/statistics/StatisticsReport.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/settings',
      name: 'settings',
      component: () => import('@/views/settings/Settings.vue'),
      meta: { requiresAuth: true, permission: 'admin' }
    },
    {
      path: '/403',
      name: 'forbidden',
      component: () => import('@/views/error/403.vue')
    },
    {
      path: '/:pathMatch(.*)*',
      name: 'not-found',
      component: () => import('@/views/error/404.vue')
    }
  ],
})

// 路由守卫
router.beforeEach(async (to, from, next) => {
  const authStore = useAuthStore()

  // 如果需要认证
  if (to.meta.requiresAuth) {
    // 检查是否已登录
    if (!authStore.isAuthenticated) {
      // 尝试从本地存储恢复认证状态
      await authStore.initializeAuth()
      
      if (!authStore.isAuthenticated) {
        next({ name: 'login', query: { redirect: to.fullPath } })
        return
      }
    }

    // 检查权限
    if (to.meta.permission && !authStore.hasPermission(to.meta.permission as string)) {
      next({ name: 'forbidden' })
      return
    }
  }

  // 如果需要游客状态（如登录页）
  if (to.meta.requiresGuest && authStore.isAuthenticated) {
    next({ name: 'dashboard' })
    return
  }

  next()
})

export default router
