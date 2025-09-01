<template>
  <div class="error-page-container">
    <div class="error-content">
      <div class="error-visual">
        <div class="error-code">403</div>
        <div class="error-icon">
          <LockOutlined />
        </div>
      </div>
      
      <div class="error-details">
        <h1 class="error-title">访问被拒绝</h1>
        <p class="error-subtitle">抱歉，您没有权限访问此页面</p>
        
        <div class="error-description">
          <p>可能的原因：</p>
          <ul>
            <li>您的账户权限不足</li>
            <li>页面需要特定的角色权限</li>
            <li>会话已过期，请重新登录</li>
            <li>管理员限制了此功能的访问</li>
          </ul>
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
          <a-button size="large" @click="contactSupport">
            <template #icon><CustomerServiceOutlined /></template>
            联系客服
          </a-button>
        </div>
        
        <div class="help-section">
          <p>需要帮助？</p>
          <div class="help-links">
            <a href="#" class="help-link">查看帮助文档</a>
            <a href="#" class="help-link">申请权限</a>
            <a href="#" class="help-link">意见反馈</a>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router'
import { message } from 'ant-design-vue'
import {
  LockOutlined,
  HomeOutlined,
  ArrowLeftOutlined,
  CustomerServiceOutlined
} from '@ant-design/icons-vue'

const router = useRouter()

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

const contactSupport = () => {
  message.info('正在跳转到客服页面...')
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
  max-width: 800px;
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
  color: #ff6b6b;
  line-height: 1;
  text-shadow: 4px 4px 8px rgba(255, 107, 107, 0.2);
}

.error-icon {
  font-size: 80px;
  color: #ffa726;
  opacity: 0.8;
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
  border-left: 4px solid #ffa726;
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

.error-actions {
  display: flex;
  gap: 16px;
  margin-bottom: 40px;
  flex-wrap: wrap;
}

.help-section {
  border-top: 1px solid #e8e8e8;
  padding-top: 24px;
}

.help-section p {
  font-size: 16px;
  font-weight: 600;
  color: #333;
  margin: 0 0 16px 0;
}

.help-links {
  display: flex;
  gap: 24px;
  flex-wrap: wrap;
}

.help-link {
  color: #1890ff;
  text-decoration: none;
  font-size: 14px;
  transition: all 0.3s ease;
}

.help-link:hover {
  color: #40a9ff;
  text-decoration: underline;
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
  
  .help-links {
    justify-content: center;
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
}
</style>