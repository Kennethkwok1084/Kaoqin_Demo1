<template>
  <div class="complete-profile-container">
    <div class="complete-profile-card">
      <div class="card-header">
        <h2>完善个人信息</h2>
        <p class="description">
          欢迎首次登录！为了更好地为您提供服务，请完善以下可选信息。
          您也可以选择跳过，稍后在个人设置中完善。
        </p>
      </div>

      <el-form
        ref="formRef"
        :model="formData"
        :rules="formRules"
        label-width="100px"
        label-position="left"
        @submit.prevent="handleSubmit"
      >
        <div class="form-content">
          <el-row :gutter="20">
            <el-col :span="12">
              <el-form-item>
                <template #label>
                  <span>用户信息</span>
                </template>
                <el-alert
                  title="可以修改用户名和手机号"
                  type="info"
                  :closable="false"
                  show-icon
                />
              </el-form-item>
            </el-col>

            <el-col :span="12">
              <el-form-item prop="phone">
                <template #label>
                  <el-icon><Phone /></el-icon>
                  手机号码
                  <el-tag type="info" size="small" style="margin-left: 4px"
                    >可选</el-tag
                  >
                </template>
                <el-input
                  v-model="formData.phone"
                  placeholder="请输入手机号码"
                  clearable
                >
                  <template #prefix>
                    <el-icon><Phone /></el-icon>
                  </template>
                </el-input>
              </el-form-item>
            </el-col>
          </el-row>

          <el-row>
            <el-col :span="24">
              <el-form-item prop="username">
                <template #label>
                  <el-icon><Message /></el-icon>
                  用户名
                  <el-tag type="info" size="small" style="margin-left: 4px"
                    >可选</el-tag
                  >
                </template>
                <el-input
                  v-model="formData.username"
                  placeholder="请输入用户名（仅允许字母、数字和下划线）"
                  clearable
                >
                  <template #prefix>
                    <el-icon><Message /></el-icon>
                  </template>
                </el-input>
              </el-form-item>
            </el-col>
          </el-row>
        </div>

        <div class="form-actions">
          <el-button size="default" @click="handleSkip" :loading="loading">
            跳过，稍后完善
          </el-button>
          <el-button
            type="primary"
            size="default"
            @click="handleSubmit"
            :loading="loading"
          >
            保存信息
          </el-button>
        </div>
      </el-form>
    </div>

    <!-- 进度提示 -->
    <div class="progress-info">
      <el-steps :active="1" finish-status="success" simple>
        <el-step title="登录成功" />
        <el-step title="完善信息" />
        <el-step title="开始使用" />
      </el-steps>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Message, Phone } from '@element-plus/icons-vue'
import { useAuthStore } from '@/stores/auth'
import { MembersApi } from '@/api/members'
import type { MemberUpdateRequest } from '@/api/members'

// 路由和store
const router = useRouter()
const authStore = useAuthStore()

// 响应式数据
const loading = ref(false)
const formRef = ref()

// 表单数据
const formData = reactive({
  phone: '',
  username: ''
})

// 表单验证规则（只验证格式，不强制要求）
const formRules = {
  phone: [
    {
      pattern: /^1[3-9]\d{9}$/,
      message: '请输入11位有效手机号码',
      trigger: 'blur'
    }
  ],
  username: [
    {
      pattern: /^[a-zA-Z0-9_]+$/,
      message: '用户名只能包含字母、数字和下划线',
      trigger: 'blur'
    },
    {
      min: 3,
      max: 50,
      message: '用户名长度必须在3-50个字符之间',
      trigger: 'blur'
    }
  ]
}

// 方法
const handleSubmit = async () => {
  try {
    // 验证表单
    await formRef.value?.validate()

    loading.value = true

    // 过滤空值
    const submitData: MemberUpdateRequest = {}
    if (formData.phone?.trim()) {
      submitData.phone = formData.phone.trim()
    }
    if (formData.username?.trim()) {
      submitData.username = formData.username.trim()
    }

    // 调用API完善信息 - 使用completeProfile方法
    const currentUser = authStore.userInfo
    if (currentUser?.id) {
      // 将submitData转换为completeProfile格式
      const updateData = {
        phone: submitData.phone
        // 可以添加其他需要完善的字段
      }
      await MembersApi.completeProfile(currentUser.id, updateData)

      // 更新用户状态为已完善信息
      authStore.updateUser({ profile_completed: true })
    } else {
      throw new Error('无法获取当前用户信息')
    }

    ElMessage.success('信息保存成功！')

    // 跳转到主页面
    await redirectToMain()
  } catch (error: any) {
    console.error('完善信息失败:', error)
    ElMessage.error(error.message || '保存失败，请重试')
  } finally {
    loading.value = false
  }
}

const handleSkip = async () => {
  try {
    const result = await ElMessageBox.confirm(
      '您确定要跳过信息完善吗？您可以稍后在个人设置中完善这些信息。',
      '跳过确认',
      {
        confirmButtonText: '确定跳过',
        cancelButtonText: '继续完善',
        type: 'info'
      }
    )

    if (result === 'confirm') {
      await redirectToMain()
    }
  } catch {
    // 用户取消
  }
}

const redirectToMain = async () => {
  // 更新用户状态
  await authStore.refreshUserInfo()

  // 跳转到仪表板
  router.replace('/dashboard')
}
</script>

<style scoped lang="scss">
@use '@/styles/variables.scss' as *;
@use '@/styles/mixins.scss' as *;

.complete-profile-container {
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  @include flex-center;
  flex-direction: column;
  padding: 20px;
}

.complete-profile-card {
  width: 100%;
  max-width: 600px;
  background: white;
  border-radius: 16px;
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
  overflow: hidden;
  margin-bottom: 40px;

  .card-header {
    padding: 40px 40px 20px;
    text-align: center;
    background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);

    h2 {
      font-size: 28px;
      font-weight: bold;
      color: $text-color-primary;
      margin: 0 0 12px 0;
    }

    .description {
      color: $text-color-regular;
      font-size: 16px;
      line-height: 1.6;
      margin: 0;
    }
  }

  .form-content {
    padding: 40px;
  }

  .form-actions {
    padding: 0 40px 40px;
    @include flex-between;
    gap: 16px;

    .el-button {
      flex: 1;
      max-width: 200px;
    }
  }
}

.progress-info {
  .el-steps {
    background: rgba(255, 255, 255, 0.1);
    padding: 20px;
    border-radius: 12px;
    backdrop-filter: blur(10px);
  }

  :deep(.el-step__title) {
    color: white !important;
    font-weight: 500;
  }

  :deep(.el-step__line) {
    background-color: rgba(255, 255, 255, 0.3) !important;
  }

  :deep(.el-step__icon) {
    border-color: rgba(255, 255, 255, 0.5) !important;
    color: rgba(255, 255, 255, 0.8) !important;
  }

  :deep(.el-step__icon.is-process) {
    border-color: white !important;
    color: white !important;
  }

  :deep(.el-step__icon.is-finish) {
    background-color: $success-color !important;
    border-color: $success-color !important;
    color: white !important;
  }
}

// 表单项样式优化
:deep(.el-form-item__label) {
  @include flex-start;
  align-items: center;
  font-weight: 500;
  color: $text-color-primary;

  .el-icon {
    margin-right: 8px;
    color: $primary-color;
  }
}

:deep(.el-input) {
  .el-input__wrapper {
    border-radius: 8px;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
    transition: all 0.3s ease;

    &:hover {
      box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
    }

    &.is-focus {
      box-shadow: 0 4px 12px rgba($primary-color, 0.3);
    }
  }

  .el-input__prefix-inner {
    color: $text-color-placeholder;
  }
}

// 响应式设计
@include respond-to(sm) {
  .complete-profile-container {
    padding: 10px;
  }

  .complete-profile-card {
    .card-header {
      padding: 30px 20px 15px;

      h2 {
        font-size: 24px;
      }

      .description {
        font-size: 14px;
      }
    }

    .form-content {
      padding: 30px 20px;
    }

    .form-actions {
      padding: 0 20px 30px;
      flex-direction: column;

      .el-button {
        max-width: none;
      }
    }
  }

  .progress-info {
    .el-steps {
      padding: 15px 10px;
    }
  }
}
</style>
