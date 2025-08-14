<template>
  <div class="error-container">
    <div class="error-content">
      <div class="error-icon">
        <el-icon size="120" color="#909399">
          <DocumentDelete />
        </el-icon>
      </div>

      <h1 class="error-title">404</h1>
      <h2 class="error-subtitle">页面不存在</h2>
      <p class="error-description">
        抱歉，您访问的页面不存在或已被删除。请检查网址是否正确。
      </p>

      <div class="error-actions">
        <el-button type="primary" @click="goHome"> 返回首页 </el-button>
        <el-button @click="goBack"> 返回上页 </el-button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { DocumentDelete } from '@element-plus/icons-vue'
import { useRouter } from 'vue-router'

const router = useRouter()

const goHome = () => {
  router.push('/')
}

const goBack = () => {
  router.go(-1)
}
</script>

<style scoped lang="scss">
@use '@/styles/variables.scss' as *;
@use '@/styles/mixins.scss' as *;

.error-container {
  min-height: 100vh;
  @include flex-center;
  background: $background-color-base;
  padding: $spacing-base;
}

.error-content {
  text-align: center;
  max-width: 500px;

  .error-icon {
    margin-bottom: $spacing-large;
  }

  .error-title {
    font-size: 72px;
    font-weight: 700;
    color: $text-color-placeholder;
    margin: 0 0 $spacing-base 0;
    line-height: 1;
  }

  .error-subtitle {
    font-size: $font-size-extra-large;
    font-weight: 600;
    color: $text-color-primary;
    margin: 0 0 $spacing-base 0;
  }

  .error-description {
    font-size: $font-size-medium;
    color: $text-color-secondary;
    margin: 0 0 $spacing-extra-large 0;
    line-height: 1.6;
  }

  .error-actions {
    @include flex-center;
    gap: $spacing-base;

    @include respond-to(sm) {
      flex-direction: column;

      .el-button {
        width: 200px;
      }
    }
  }
}
</style>
