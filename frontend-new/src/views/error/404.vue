<template>
  <div class="error-page-container">
    <div class="error-content">
      <div class="error-visual">
        <div class="error-code">404</div>
        <div class="error-icon">
          <SearchOutlined />
        </div>
        <div class="floating-elements">
          <div class="floating-element" :style="{ animationDelay: '0s' }"></div>
          <div class="floating-element" :style="{ animationDelay: '1s' }"></div>
          <div class="floating-element" :style="{ animationDelay: '2s' }"></div>
        </div>
      </div>
      
      <div class="error-details">
        <h1 class="error-title">页面走丢了</h1>
        <p class="error-subtitle">抱歉，您访问的页面不存在或已被移动</p>
        
        <div class="error-description">
          <p>可能的原因：</p>
          <ul>
            <li>输入的网址有误</li>
            <li>页面已被删除或移动</li>
            <li>链接已过期失效</li>
            <li>您没有访问权限</li>
          </ul>
        </div>
        
        <div class="search-section">
          <p>试试搜索您需要的内容：</p>
          <div class="search-input">
            <a-input-search
              v-model:value="searchValue"
              placeholder="搜索页面、功能或内容..."
              size="large"
              @search="handleSearch"
            />
          </div>
        </div>
        
        <div class="error-actions">
          <a-button type="primary" size="large" @click="goHome">
            <template #icon><HomeOutlined /></template>
            返回首页
          </a-button>
          <a-button size="large" @click="goBack">
            <template #icon><ArrowLeftOutlined /></template>
            返回上页
          </a-button>
          <a-button size="large" @click="refreshPage">
            <template #icon><ReloadOutlined /></template>
            刷新页面
          </a-button>
        </div>
        
        <div class="quick-links">
          <p>或者您可以访问：</p>
          <div class="link-grid">
            <a href="/dashboard" class="quick-link">
              <DashboardOutlined />
              <span>工作台</span>
            </a>
            <a href="/tasks" class="quick-link">
              <ProjectOutlined />
              <span>任务管理</span>
            </a>
            <a href="/members" class="quick-link">
              <UserOutlined />
              <span>成员管理</span>
            </a>
            <a href="/attendance" class="quick-link">
              <CalendarOutlined />
              <span>考勤管理</span>
            </a>
            <a href="/statistics" class="quick-link">
              <BarChartOutlined />
              <span>统计报表</span>
            </a>
            <a href="/settings" class="quick-link">
              <SettingOutlined />
              <span>系统设置</span>
            </a>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { message } from 'ant-design-vue'
import {
  SearchOutlined,
  HomeOutlined,
  ArrowLeftOutlined,
  ReloadOutlined,
  DashboardOutlined,
  ProjectOutlined,
  UserOutlined,
  CalendarOutlined,
  BarChartOutlined,
  SettingOutlined
} from '@ant-design/icons-vue'

const router = useRouter()
const searchValue = ref('')

const goHome = () => {
  router.push('/dashboard')
}

const goBack = () => {
  if (window.history.length > 1) {
    router.go(-1)
  } else {
    router.push('/dashboard')
  }
}

const refreshPage = () => {
  window.location.reload()
}

const handleSearch = (value: string) => {
  if (!value.trim()) {
    message.warning('请输入搜索内容')
    return
  }
  
  message.info(`正在搜索: ${value}`)
  router.push({
    path: '/search',
    query: { q: value }
  })
}
</script>

<style scoped>
.error-page-container {
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
}

.error-content {
  max-width: 900px;
  width: 100%;
  background: white;
  border-radius: 16px;
  box-shadow: 0 16px 64px rgba(0, 0, 0, 0.15);
  padding: 48px;
  text-align: center;
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 48px;
  align-items: center;
}

.error-visual {
  position: relative;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 24px;
}

.error-code {
  font-size: 120px;
  font-weight: 900;
  color: #4facfe;
  line-height: 1;
  text-shadow: 4px 4px 8px rgba(79, 172, 254, 0.2);
}

.error-icon {
  font-size: 80px;
  color: #52c41a;
  opacity: 0.8;
}

.floating-elements {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  pointer-events: none;
}

.floating-element {
  position: absolute;
  width: 8px;
  height: 8px;
  background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
  border-radius: 50%;
  animation: float 3s ease-in-out infinite;
}

.floating-element:nth-child(1) {
  top: 20%;
  left: 10%;
}

.floating-element:nth-child(2) {
  top: 60%;
  right: 15%;
}

.floating-element:nth-child(3) {
  bottom: 20%;
  left: 50%;
}

@keyframes float {
  0%, 100% { transform: translateY(0px) scale(1); opacity: 0.7; }
  50% { transform: translateY(-20px) scale(1.2); opacity: 1; }
}

.error-details {
  text-align: left;
}

.error-title {
  font-size: 36px;
  font-weight: 700;
  color: #333;
  margin: 0 0 16px 0;
}

.error-subtitle {
  font-size: 20px;
  color: #666;
  margin: 0 0 32px 0;
  line-height: 1.4;
}

.error-description {
  background: #f8f9fa;
  border-radius: 12px;
  padding: 24px;
  margin-bottom: 32px;
  border-left: 4px solid #4facfe;
}

.error-description p {
  font-size: 16px;
  font-weight: 600;
  color: #333;
  margin: 0 0 12px 0;
}

.error-description ul {
  margin: 0;
  padding-left: 20px;
}

.error-description li {
  font-size: 14px;
  color: #666;
  line-height: 1.6;
  margin-bottom: 8px;
}

.search-section {
  margin-bottom: 32px;
}

.search-section p {
  font-size: 16px;
  font-weight: 600;
  color: #333;
  margin: 0 0 16px 0;
}

.search-input {
  margin-bottom: 16px;
}

.error-actions {
  display: flex;
  gap: 16px;
  margin-bottom: 40px;
  flex-wrap: wrap;
}

.quick-links {
  border-top: 1px solid #e8e8e8;
  padding-top: 32px;
}

.quick-links p {
  font-size: 16px;
  font-weight: 600;
  color: #333;
  margin: 0 0 20px 0;
}

.link-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
}

.quick-link {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  padding: 20px 16px;
  border: 1px solid #e8e8e8;
  border-radius: 12px;
  color: #666;
  text-decoration: none;
  transition: all 0.3s ease;
}

.quick-link:hover {
  border-color: #4facfe;
  color: #4facfe;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(79, 172, 254, 0.15);
}

.quick-link .anticon {
  font-size: 24px;
}

.quick-link span {
  font-size: 14px;
  font-weight: 500;
}

@container (max-width: 768px) {
  .error-content {
    grid-template-columns: 1fr;
    gap: 32px;
    padding: 32px 24px;
    text-align: center;
  }
  
  .error-details {
    text-align: center;
  }
  
  .error-code {
    font-size: 80px;
  }
  
  .error-icon {
    font-size: 60px;
  }
  
  .error-title {
    font-size: 28px;
  }
  
  .error-subtitle {
    font-size: 18px;
  }
  
  .error-actions {
    flex-direction: column;
    align-items: center;
  }
  
  .error-actions .ant-btn {
    width: 100%;
    max-width: 200px;
  }
  
  .link-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@container (max-width: 480px) {
  .error-page-container {
    padding: 16px;
  }
  
  .error-content {
    padding: 24px 16px;
  }
  
  .error-code {
    font-size: 64px;
  }
  
  .error-title {
    font-size: 24px;
  }
  
  .error-description {
    padding: 16px;
  }
  
  .link-grid {
    grid-template-columns: 1fr;
  }
}
</style>