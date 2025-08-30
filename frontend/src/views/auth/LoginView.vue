<template>
  <div class="login-container">
    <div class="login-card">
      <div class="login-header">
        <div class="logo">
          <div class="logo-icon">
            <el-icon size="64" color="#409EFF"><Odometer /></el-icon>
          </div>
        </div>
        <h2 class="login-title">考勤管理系统</h2>
        <p class="login-subtitle">网络维护团队考勤管理平台</p>
      </div>

      <el-form
        ref="loginFormRef"
        :model="loginForm"
        :rules="loginRules"
        class="login-form"
        label-position="top"
        @submit.prevent="handleLogin"
      >
        <el-form-item label="用户名" prop="username">
          <el-input
            v-model="loginForm.username"
            placeholder="请输入用户名"
            size="default"
            :prefix-icon="User"
            clearable
            @keyup.enter="handleLogin"
          />
        </el-form-item>

        <el-form-item label="密码" prop="password">
          <el-input
            v-model="loginForm.password"
            type="password"
            placeholder="请输入密码"
            size="default"
            :prefix-icon="Lock"
            show-password
            clearable
            @keyup.enter="handleLogin"
          />
        </el-form-item>

        <el-form-item>
          <div class="login-options">
            <el-checkbox v-model="loginForm.remember_me"> 记住我 </el-checkbox>
            <el-link
              type="primary"
              :underline="false"
              @click="showForgotPassword"
            >
              忘记密码？
            </el-link>
          </div>
        </el-form-item>

        <el-form-item>
          <el-button
            type="primary"
            size="default"
            class="login-button"
            :loading="isLoading"
            @click="handleLogin"
          >
            {{ isLoading ? '登录中...' : '登录' }}
          </el-button>
        </el-form-item>
      </el-form>

      <div class="login-footer">
        <p class="copyright">© 2024 考勤管理系统 版权所有</p>
      </div>
    </div>

    <!-- 忘记密码对话框 -->
    <el-dialog
      v-model="forgotPasswordVisible"
      title="重置密码"
      width="400px"
      :close-on-click-modal="false"
    >
      <el-form
        ref="resetFormRef"
        :model="resetForm"
        :rules="resetRules"
        label-position="top"
      >
        <el-form-item label="邮箱地址" prop="email">
          <el-input
            v-model="resetForm.email"
            placeholder="请输入注册邮箱"
            :prefix-icon="Message"
          />
        </el-form-item>
      </el-form>

      <template #footer>
        <div class="dialog-footer">
          <el-button @click="forgotPasswordVisible = false">取消</el-button>
          <el-button
            type="primary"
            :loading="isResetting"
            @click="handleResetPassword"
          >
            发送重置邮件
          </el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { User, Lock, Message, Odometer } from '@element-plus/icons-vue'
import { useAuthStore } from '@/stores/auth'
import { authApi } from '@/api/auth'
import type { FormInstance, FormRules } from 'element-plus'

// 响应式数据
const loginFormRef = ref<FormInstance>()
const resetFormRef = ref<FormInstance>()
const isLoading = ref(false)
const isResetting = ref(false)
const forgotPasswordVisible = ref(false)

// 登录表单
const loginForm = reactive({
  username: '',
  password: '',
  remember_me: false
})

// 重置密码表单
const resetForm = reactive({
  email: ''
})

// 表单验证规则
const loginRules: FormRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 20, message: '用户名长度在 3 到 20 个字符', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码长度不能少于 6 个字符', trigger: 'blur' }
  ]
}

const resetRules: FormRules = {
  email: [
    { required: true, message: '请输入邮箱地址', trigger: 'blur' },
    { type: 'email', message: '请输入正确的邮箱格式', trigger: 'blur' }
  ]
}

// Store
const authStore = useAuthStore()

// 处理登录
const handleLogin = async () => {
  if (!loginFormRef.value) return

  try {
    await loginFormRef.value.validate()
    isLoading.value = true

    await authStore.login(loginForm as any)
    ElMessage.success('登录成功')
  } catch (error: any) {
    console.error('登录失败:', error)

    if (error.response?.status === 401) {
      ElMessage.error('用户名或密码错误')
    } else if (error.response?.status === 423) {
      ElMessage.error('账户已被锁定，请联系管理员')
    } else {
      ElMessage.error(error.response?.data?.message || '登录失败，请重试')
    }
  } finally {
    isLoading.value = false
  }
}

// 显示忘记密码对话框
const showForgotPassword = () => {
  forgotPasswordVisible.value = true
  resetForm.email = ''
}

// 处理重置密码
const handleResetPassword = async () => {
  if (!resetFormRef.value) return

  try {
    await resetFormRef.value.validate()
    isResetting.value = true

    await authApi.requestResetPassword(resetForm)
    ElMessage.success('重置密码邮件已发送，请查收邮箱')
    forgotPasswordVisible.value = false
  } catch (error: any) {
    console.error('重置密码失败:', error)
    ElMessage.error(error.response?.data?.message || '发送重置邮件失败，请重试')
  } finally {
    isResetting.value = false
  }
}

// 组件挂载时
onMounted(() => {
  // 如果已经登录，直接跳转到首页
  if (authStore.isAuthenticated) {
    authStore.login
  }

  // 设置页面标题
  document.title = '登录 - 考勤管理系统'

  // 开发环境下预填充表单（可选）
  if (import.meta.env.DEV) {
    loginForm.username = 'admin'
    loginForm.password = 'admin123'
  }
})
</script>

<style scoped lang="scss">
@use '@/styles/variables.scss' as *;
@use '@/styles/mixins.scss' as *;
@use 'sass:color';

.login-container {
  min-height: 100vh;
  @include flex-center;
  @include gradient-background(
    $primary-color,
    color.adjust($primary-color, $lightness: 20%)
  );
  padding: $spacing-base;
}

.login-card {
  width: 100%;
  max-width: 420px;
  background: $background-color-white;
  border-radius: $border-radius-round;
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
  padding: $spacing-extra-large;

  .login-header {
    text-align: center;
    margin-bottom: $spacing-extra-large;

    .logo {
      margin-bottom: $spacing-base;

      .logo-icon {
        width: 80px;
        height: 80px;
        @include flex-center;
        border-radius: 50%;
        background: color.adjust($primary-color, $lightness: 45%);
        margin: 0 auto;
      }
    }

    .login-title {
      font-size: $font-size-extra-large;
      font-weight: 700;
      color: $text-color-primary;
      margin: 0 0 $spacing-extra-small 0;
    }

    .login-subtitle {
      font-size: $font-size-small;
      color: $text-color-secondary;
      margin: 0;
    }
  }

  .login-form {
    .login-options {
      @include flex-between;
      width: 100%;
    }

    .login-button {
      width: 100%;
      height: 48px;
      font-size: $font-size-medium;
      font-weight: 600;
      border-radius: $border-radius-base;
      @include gradient-background(
        $primary-color,
        color.adjust($primary-color, $lightness: 10%)
      );
      border: none;

      &:hover {
        @include gradient-background(
          color.adjust($primary-color, $lightness: 5%),
          color.adjust($primary-color, $lightness: 15%)
        );
        transform: translateY(-1px);
        box-shadow: 0 6px 20px rgba($primary-color, 0.3);
      }
    }
  }

  .login-footer {
    text-align: center;
    margin-top: $spacing-large;

    .copyright {
      font-size: $font-size-extra-small;
      color: $text-color-placeholder;
      margin: 0;
    }
  }
}

// 响应式设计
@include respond-to(sm) {
  .login-container {
    padding: $spacing-small;
  }

  .login-card {
    padding: $spacing-large;
    border-radius: $border-radius-base;
  }
}

// 对话框样式
.dialog-footer {
  @include flex-end;
  gap: $spacing-small;
}

// 动画效果
.login-card {
  animation: slideUp 0.6s ease-out;
}

@keyframes slideUp {
  from {
    opacity: 0;
    transform: translateY(30px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
</style>
