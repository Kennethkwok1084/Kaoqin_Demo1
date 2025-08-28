<template>
  <div class="mobile-page-header visible-xs">
    <div class="header-content">
      <!-- 左侧内容 -->
      <div class="header-left">
        <el-button
          v-if="showBack"
          type="text"
          size="large"
          @click="handleBack"
          class="back-button"
        >
          <el-icon><ArrowLeft /></el-icon>
        </el-button>

        <div class="title-section">
          <h1 class="page-title">{{ title }}</h1>
          <p v-if="subtitle" class="page-subtitle">{{ subtitle }}</p>
        </div>
      </div>

      <!-- 右侧操作 -->
      <div class="header-right">
        <slot name="actions">
          <!-- 默认操作按钮 -->
          <el-button
            v-if="showSearch"
            type="text"
            size="large"
            @click="handleSearch"
            class="action-button"
          >
            <el-icon><Search /></el-icon>
          </el-button>

          <el-button
            v-if="showMore"
            type="text"
            size="large"
            @click="showMoreMenu = true"
            class="action-button"
          >
            <el-icon><MoreFilled /></el-icon>
          </el-button>
        </slot>
      </div>
    </div>

    <!-- 搜索栏 (可选) -->
    <div v-if="showSearchBar && searchVisible" class="search-section">
      <MobileSearchBar
        v-model="searchQuery"
        :placeholder="searchPlaceholder"
        :show-voice-search="enableVoiceSearch"
        :show-filter-button="showFilterButton"
        @search="handleSearchQuery"
        @clear="handleSearchClear"
        @filter="handleSearchFilter"
      />
    </div>

    <!-- 标签页 (可选) -->
    <div v-if="tabs && tabs.length > 0" class="tabs-section">
      <el-tabs
        v-model="activeTab"
        class="mobile-tabs"
        @tab-change="(tab: any) => handleTabChange(tab)"
      >
        <el-tab-pane
          v-for="tab in tabs"
          :key="tab.name"
          :label="tab.label"
          :name="tab.name"
          :disabled="tab.disabled"
        />
      </el-tabs>
    </div>

    <!-- 更多菜单 -->
    <el-drawer
      v-model="showMoreMenu"
      title="更多操作"
      direction="btt"
      size="auto"
      class="more-menu-drawer"
    >
      <div class="more-menu-content">
        <div
          v-for="item in moreMenuItems"
          :key="item.key"
          class="menu-item"
          @click="handleMoreMenuItem(item)"
        >
          <div class="menu-icon">
            <el-icon><component :is="item.icon" /></el-icon>
          </div>
          <span class="menu-text">{{ item.label }}</span>
        </div>
      </div>
    </el-drawer>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import {
  ArrowLeft,
  Search,
  MoreFilled,
  Share,
  Download,
  Setting
} from '@element-plus/icons-vue'
import MobileSearchBar from './MobileSearchBar.vue'

// 接口定义
interface Tab {
  name: string
  label: string
  disabled?: boolean
}

interface MoreMenuItem {
  key: string
  label: string
  icon: any
  action?: string
}

// Props
interface Props {
  title: string
  subtitle?: string
  showBack?: boolean
  showSearch?: boolean
  showMore?: boolean
  showSearchBar?: boolean
  searchPlaceholder?: string
  enableVoiceSearch?: boolean
  showFilterButton?: boolean
  tabs?: Tab[]
  activeTab?: string
  moreMenuItems?: MoreMenuItem[]
}

const props = withDefaults(defineProps<Props>(), {
  title: '',
  subtitle: '',
  showBack: false,
  showSearch: false,
  showMore: false,
  showSearchBar: false,
  searchPlaceholder: '搜索...',
  enableVoiceSearch: false,
  showFilterButton: false,
  tabs: () => [],
  activeTab: '',
  moreMenuItems: () => [
    { key: 'share', label: '分享', icon: Share },
    { key: 'export', label: '导出', icon: Download },
    { key: 'settings', label: '设置', icon: Setting }
  ]
})

// Emits
interface Emits {
  (e: 'back'): void
  (e: 'search'): void
  (e: 'search-query', query: string): void
  (e: 'search-clear'): void
  (e: 'search-filter', filters: any): void
  (e: 'tab-change', tab: string): void
  (e: 'more-action', action: string): void
}

const emit = defineEmits<Emits>()

// 路由
const router = useRouter()

// 响应式数据
const searchVisible = ref(false)
const searchQuery = ref('')
const showMoreMenu = ref(false)
const activeTab = ref(props.activeTab)

// 方法
const handleBack = () => {
  emit('back')
  // 默认行为：返回上一页
  // if (!emit('back')) {
    router.back()
  }
}

const handleSearch = () => {
  if (props.showSearchBar) {
    searchVisible.value = !searchVisible.value
  } else {
    emit('search')
  }
}

const handleSearchQuery = (query: string) => {
  emit('search-query', query)
}

const handleSearchClear = () => {
  searchQuery.value = ''
  emit('search-clear')
}

const handleSearchFilter = (filters: any) => {
  emit('search-filter', filters)
}

const handleTabChange = (tab: string) => {
  activeTab.value = tab
  emit('tab-change', tab)
}

const handleMoreMenuItem = (item: MoreMenuItem) => {
  showMoreMenu.value = false
  emit('more-action', item.key)
}

// 暴露方法
defineExpose({
  showSearch: () => {
    searchVisible.value = true
  },
  hideSearch: () => {
    searchVisible.value = false
  },
  setActiveTab: (tab: string) => {
    activeTab.value = tab
  }
})
</script>

<style scoped lang="scss">
@use '@/styles/variables.scss' as *;
@use '@/styles/mixins.scss' as *;

.mobile-page-header {
  background: $background-color-white;
  border-bottom: 1px solid $border-color-light;
  position: sticky;
  top: 0;
  z-index: 998;
  @include safe-area-padding;

  .header-content {
    @include flex-between;
    align-items: flex-start;
    padding: $spacing-base;
    min-height: 56px;

    .header-left {
      @include flex-start;
      gap: $spacing-small;
      flex: 1;

      .back-button {
        @include touch-target(44px);
        margin-right: $spacing-small;

        .el-icon {
          font-size: 20px;
        }
      }

      .title-section {
        flex: 1;
        min-width: 0; // 允许文字截断

        .page-title {
          font-size: $font-size-large;
          font-weight: 600;
          color: $text-color-primary;
          margin: 0;
          line-height: 1.4;
          @include text-ellipsis;
        }

        .page-subtitle {
          font-size: $font-size-small;
          color: $text-color-secondary;
          margin: 2px 0 0 0;
          line-height: 1.3;
          @include text-ellipsis;
        }
      }
    }

    .header-right {
      @include flex-end;
      gap: $spacing-extra-small;
      flex-shrink: 0;

      .action-button {
        @include touch-target(44px);

        .el-icon {
          font-size: 20px;
        }
      }
    }
  }

  .search-section {
    padding: 0 $spacing-base $spacing-base $spacing-base;
    animation: slideDown 0.3s ease;
  }

  .tabs-section {
    .mobile-tabs {
      :deep(.el-tabs__header) {
        margin: 0;

        .el-tabs__nav-wrap {
          padding: 0 $spacing-base;

          .el-tabs__nav-scroll {
            .el-tabs__nav {
              .el-tabs__item {
                height: 44px;
                line-height: 44px;
                font-size: $font-size-base;
                padding: 0 $spacing-base;
                @include touch-target(44px);
              }
            }
          }
        }
      }

      :deep(.el-tabs__content) {
        display: none; // 隐藏内容，只显示标签
      }
    }
  }
}

.more-menu-drawer {
  :deep(.el-drawer) {
    border-radius: $spacing-base $spacing-base 0 0;
  }

  :deep(.el-drawer__header) {
    padding: $spacing-base;
    margin-bottom: 0;
  }

  :deep(.el-drawer__body) {
    padding: 0 0 $spacing-base 0;
  }

  .more-menu-content {
    .menu-item {
      @include flex-start;
      gap: $spacing-base;
      padding: $spacing-base $spacing-large;
      cursor: pointer;
      transition: background-color $transition-base;
      @include touch-target(56px);

      &:hover {
        background: $background-color-light;
      }

      .menu-icon {
        width: 24px;
        height: 24px;
        @include flex-center;
        color: $text-color-secondary;

        .el-icon {
          font-size: 20px;
        }
      }

      .menu-text {
        font-size: $font-size-base;
        color: $text-color-primary;
      }
    }
  }
}

// 动画
@keyframes slideDown {
  from {
    opacity: 0;
    transform: translateY(-10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
</style>
