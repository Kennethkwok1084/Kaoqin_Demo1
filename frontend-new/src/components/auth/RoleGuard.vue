<template>
  <div v-if="hasPermission">
    <slot />
  </div>
  <div v-else-if="showFallback" class="permission-fallback">
    <slot name="fallback">
      <a-result
        status="403"
        title="权限不足"
        :sub-title="fallbackMessage"
      >
        <template #extra>
          <a-button type="primary" @click="$router.push('/dashboard')">
            返回首页
          </a-button>
        </template>
      </a-result>
    </slot>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useAuthStore } from '@/stores/auth'

interface Props {
  /** 必需权限，支持字符串或数组 */
  require?: string | string[]
  /** 必需角色，支持字符串或数组 */
  role?: string | string[]
  /** 权限模式：'any' 表示满足任一条件即可，'all' 表示需要满足全部条件 */
  mode?: 'any' | 'all'
  /** 无权限时是否显示后备内容 */
  showFallback?: boolean
  /** 后备内容的提示信息 */
  fallbackMessage?: string
}

const props = withDefaults(defineProps<Props>(), {
  mode: 'any',
  showFallback: true,
  fallbackMessage: '您暂时没有访问此内容的权限，请联系管理员获取相应权限。'
})

const authStore = useAuthStore()

// 计算是否有权限
const hasPermission = computed(() => {
  if (!authStore.isAuthenticated) {
    return false
  }

  const user = authStore.user
  if (!user) return false

  let roleCheck = true
  let permissionCheck = true

  // 检查角色权限
  if (props.role) {
    const requiredRoles = Array.isArray(props.role) ? props.role : [props.role]
    
    if (props.mode === 'all') {
      roleCheck = requiredRoles.every(role => checkRole(role))
    } else {
      roleCheck = requiredRoles.some(role => checkRole(role))
    }
  }

  // 检查具体权限
  if (props.require) {
    const requiredPermissions = Array.isArray(props.require) ? props.require : [props.require]
    
    if (props.mode === 'all') {
      permissionCheck = requiredPermissions.every(permission => authStore.hasPermission(permission))
    } else {
      permissionCheck = requiredPermissions.some(permission => authStore.hasPermission(permission))
    }
  }

  return roleCheck && permissionCheck
})

// 检查角色
const checkRole = (role: string) => {
  const user = authStore.user
  if (!user) return false

  switch (role) {
    case 'admin':
    case 'super_admin':
      return user.role === 'admin' || user.role === 'super_admin'
    case 'manager':
      return ['admin', 'super_admin', 'manager'].includes(user.role)
    case 'member':
      return ['admin', 'super_admin', 'manager', 'member'].includes(user.role)
    case 'group_leader':
      return user.role === 'group_leader' || authStore.isAdmin
    default:
      return user.role === role
  }
}
</script>

<style scoped>
.permission-fallback {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 300px;
  padding: 40px 20px;
}

:deep(.ant-result-title) {
  color: #666666;
}

:deep(.ant-result-subtitle) {
  color: #8c8c8c;
}
</style>