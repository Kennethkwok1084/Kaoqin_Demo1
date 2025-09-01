<template>
  <div class="desktop-login-container">
    <!-- 左侧品牌展示区 -->
    <div class="brand-section">
      <div class="brand-content">
        <div class="system-logo">
          <div class="logo-icon">
            <DashboardOutlined />
          </div>
          <h1>考勤管理系统</h1>
        </div>
        
        <div class="system-description">
          <h2>网络维护团队专用管理平台</h2>
          <p>集成任务管理、考勤统计、工时计算为一体的现代化管理系统</p>
          
          <div class="feature-list">
            <div class="feature-item">
              <CheckCircleOutlined />
              <span>智能工时计算</span>
            </div>
            <div class="feature-item">
              <CheckCircleOutlined />
              <span>实时任务跟踪</span>
            </div>
            <div class="feature-item">
              <CheckCircleOutlined />
              <span>数据可视化报表</span>
            </div>
          </div>
        </div>
        
        <div class="system-stats">
          <div class="stat-item">
            <div class="stat-number">99.9%</div>
            <div class="stat-label">系统可用性</div>
          </div>
          <div class="stat-item">
            <div class="stat-number">24/7</div>
            <div class="stat-label">技术支持</div>
          </div>
        </div>
      </div>
    </div>

    <!-- 右侧登录表单区 -->
    <div class="login-section">
      <div class="login-form-container">
        <div class="login-header">
          <h2>系统登录</h2>
          <p>请使用您的学号和密码登录系统</p>
        </div>

        <a-form
          :model="loginForm"
          :rules="rules"
          @finish="handleLogin"
          class="enterprise-login-form"
          layout="vertical"
        >
          <a-form-item name="studentId" label="学号" class="form-item">
            <a-input
              v-model:value="loginForm.studentId"
              size="large"
              placeholder="请输入学号"
              class="login-input"
            >
              <template #prefix>
                <UserOutlined class="input-icon" />
              </template>
            </a-input>
          </a-form-item>

          <a-form-item name="password" label="密码" class="form-item">
            <a-input-password
              v-model:value="loginForm.password"
              size="large"
              placeholder="请输入密码"
              class="login-input"
            >
              <template #prefix>
                <LockOutlined class="input-icon" />
              </template>
            </a-input-password>
          </a-form-item>

          <div class="login-options">
            <a-checkbox v-model:checked="loginForm.rememberMe">
              记住登录状态
            </a-checkbox>
            <a href="#" class="forgot-link">忘记密码？</a>
          </div>

          <a-button
            type="primary"
            html-type="submit"
            size="large"
            block
            :loading="loading"
            class="login-button"
          >
            {{ loading ? '登录中...' : '登录系统' }}
          </a-button>
        </a-form>

        <div class="login-help">
          <div class="help-item">
            <QuestionCircleOutlined />
            <span>首次登录请联系管理员获取账号</span>
          </div>
          <div class="help-item">
            <PhoneOutlined />
            <span>技术支持：400-888-8888</span>
          </div>
        </div>

        <div class="login-footer">
          <p>© 2025 网络维护团队考勤管理系统 v2.0</p>
          <p>推荐使用 Chrome、Firefox 等现代浏览器访问</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { message } from 'ant-design-vue'
import { 
  UserOutlined, 
  LockOutlined, 
  DashboardOutlined,
  CheckCircleOutlined,
  QuestionCircleOutlined,
  PhoneOutlined
} from '@ant-design/icons-vue'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()

// 表单数据
const loginForm = ref({
  studentId: '',
  password: '',
  rememberMe: false
})

// 表单验证规则
const rules = {
  studentId: [
    { required: true, message: '请输入学号', trigger: 'blur' },
    { min: 8, max: 12, message: '学号长度应为8-12位', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码至少6位', trigger: 'blur' }
  ]
}

// 响应式状态
const loading = ref(false)

// 处理登录
const handleLogin = async () => {
  loading.value = true
  
  try {
    const result = await authStore.login(loginForm.value)
    
    if (result.success) {
      message.success(result.message || '登录成功')
      
      // 跳转到目标页面或仪表板
      const redirect = route.query.redirect as string || '/dashboard'
      router.push(redirect)
    } else {
      message.error(result.message || '登录失败')
    }
  } catch (error: any) {
    console.error('Login error:', error)
    message.error(error.message || '登录失败，请检查网络连接')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
/* 🚀 现代响应式登录界面 - 零断点自适应 */
.desktop-login-container {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
  width: 100vw;
  height: 100vh;
  background: #f5f7fa;
  gap: 0;
  margin: 0;
  padding: 0;
}

/* 左侧品牌展示区 */
.brand-section {
  background: linear-gradient(135deg, #1e2139 0%, #2a2d47 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  overflow: hidden;
  width: 100%;
  height: 100%;
}

.brand-section::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: url('data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><defs><pattern id="grain" width="100" height="100" patternUnits="userSpaceOnUse"><circle cx="25" cy="25" r="1" fill="%23ffffff" fill-opacity="0.02"/><circle cx="75" cy="25" r="1" fill="%23ffffff" fill-opacity="0.02"/><circle cx="50" cy="50" r="1" fill="%23ffffff" fill-opacity="0.02"/><circle cx="25" cy="75" r="1" fill="%23ffffff" fill-opacity="0.02"/><circle cx="75" cy="75" r="1" fill="%23ffffff" fill-opacity="0.02"/></pattern></defs><rect width="100" height="100" fill="url(%23grain)"/></svg>');
}

.brand-content {
  max-width: 480px;
  padding: 60px;
  color: white;
  position: relative;
  z-index: 1;
}

.system-logo {
  display: flex;
  align-items: center;
  gap: 20px;
  margin-bottom: 60px;
}

.logo-icon {
  width: 64px;
  height: 64px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 32px;
  box-shadow: 0 8px 24px rgba(102, 126, 234, 0.4);
}

.system-logo h1 {
  margin: 0;
  font-size: 32px;
  font-weight: 700;
  background: linear-gradient(135deg, #ffffff 0%, #e0e7ff 100%);
  background-clip: text;
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

.system-description {
  margin-bottom: 60px;
}

.system-description h2 {
  font-size: 24px;
  font-weight: 600;
  margin: 0 0 20px;
  color: #e0e7ff;
}

.system-description p {
  font-size: 16px;
  line-height: 1.6;
  color: #8892b0;
  margin: 0 0 40px;
}

.feature-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.feature-item {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 16px;
  color: #e0e7ff;
}

.feature-item .anticon {
  color: #52c41a;
  font-size: 18px;
}

.system-stats {
  display: flex;
  gap: 40px;
}

.stat-item {
  text-align: center;
}

.stat-number {
  font-size: 36px;
  font-weight: 700;
  color: #667eea;
  margin-bottom: 8px;
}

.stat-label {
  font-size: 14px;
  color: #8892b0;
}

/* 右侧登录表单区 */
.login-section {
  background: white;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: -4px 0 24px rgba(0,0,0,0.06);
  width: 100%;
  height: 100%;
}

.login-form-container {
  width: 100%;
  max-width: 400px;
  padding: 60px 40px;
}

.login-header {
  text-align: center;
  margin-bottom: 48px;
}

.login-header h2 {
  font-size: 28px;
  font-weight: 600;
  color: #1a1a1a;
  margin: 0 0 12px;
}

.login-header p {
  font-size: 16px;
  color: #666666;
  margin: 0;
}

.enterprise-login-form {
  margin-bottom: 32px;
}

.form-item {
  margin-bottom: 28px;
}

:deep(.form-item .ant-form-item-label > label) {
  font-size: 16px;
  font-weight: 500;
  color: #262626;
  height: 32px;
}

.login-input {
  height: 56px;
  border-radius: 12px;
  border: 2px solid #e8e9ea;
  font-size: 16px;
  transition: all 0.3s ease;
}

.login-input:hover {
  border-color: #667eea;
}

.login-input:focus,
.login-input.ant-input-focused {
  border-color: #667eea;
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
}

.input-icon {
  color: #8c8c8c;
  font-size: 18px;
}

.login-options {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 32px;
}

:deep(.login-options .ant-checkbox-wrapper) {
  font-size: 15px;
  color: #666666;
}

.forgot-link {
  color: #667eea;
  text-decoration: none;
  font-size: 15px;
  font-weight: 500;
  transition: color 0.3s;
}

.forgot-link:hover {
  color: #764ba2;
  text-decoration: none;
}

.login-button {
  height: 56px;
  border-radius: 12px;
  font-size: 16px;
  font-weight: 600;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border: none;
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
  transition: all 0.3s ease;
}

.login-button:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(102, 126, 234, 0.4);
}

.login-help {
  margin-top: 32px;
  padding: 24px;
  background: #f9fafb;
  border-radius: 12px;
  border: 1px solid #e8e9ea;
}

.help-item {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
  font-size: 14px;
  color: #666666;
}

.help-item:last-child {
  margin-bottom: 0;
}

.help-item .anticon {
  color: #667eea;
}

.login-footer {
  text-align: center;
  margin-top: 40px;
  padding-top: 32px;
  border-top: 1px solid #e8e9ea;
}

.login-footer p {
  font-size: 13px;
  color: #8c8c8c;
  margin: 4px 0;
}

/* 🎯 Container Queries - 真正的智能响应式 */
.desktop-login-container {
  container-type: inline-size;
}

/* 当容器宽度不足800px时，自动竖排 */
@container (max-width: 800px) {
  .desktop-login-container {
    grid-template-columns: 1fr;
    grid-template-rows: 1fr 1fr;
  }
  
  .brand-section {
    order: 2; /* 移动端时，表单在上，品牌在下 */
  }
  
  .login-section {
    order: 1;
    box-shadow: 0 4px 24px rgba(0,0,0,0.08);
  }
}

/* 极窄屏优化 */
@container (max-width: 480px) {
  .brand-section {
    display: none; /* 极小屏幕隐藏品牌区域 */
  }
  
  .desktop-login-container {
    grid-template-rows: 1fr;
  }
  
  .login-section {
    border-radius: 0;
    box-shadow: none;
  }
}

/* 大屏幕优化 - 保持专业感 */
@container (min-width: 1200px) {
  .login-form-container {
    max-width: 480px;
    padding: 80px 60px;
  }
  
  .brand-content {
    max-width: 560px;
    padding: 80px;
  }
}
</style>