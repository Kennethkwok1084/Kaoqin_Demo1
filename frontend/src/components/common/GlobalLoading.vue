<template>
  <div class="global-loading-overlay">
    <div class="loading-content">
      <div class="loading-spinner"></div>
      <div class="loading-text">{{ message }}</div>
    </div>
  </div>
</template>

<script setup lang="ts">
interface Props {
  message?: string
}

withDefaults(defineProps<Props>(), {
  message: '加载中...'
})
</script>

<style lang="scss" scoped>
.global-loading-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  background: rgba(255, 255, 255, 0.9);
  z-index: 9999;
  @include flex-center;
}

.loading-content {
  @include flex-column-center;
  gap: $spacing-base;
}

.loading-spinner {
  @include loading-spinner(40px, $primary-color);
}

.loading-text {
  font-size: $font-size-medium;
  color: $text-color-secondary;
  font-weight: 500;
}
</style>
