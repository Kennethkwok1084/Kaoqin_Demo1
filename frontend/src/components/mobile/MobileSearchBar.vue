<template>
  <div class="mobile-search-bar">
    <div class="search-container">
      <el-input
        v-model="searchQuery"
        placeholder="搜索任务、成员、考勤..."
        :prefix-icon="Search"
        class="search-input"
        clearable
        @input="handleSearch"
        @clear="handleClear"
        @keyup.enter="handleEnterSearch"
      >
        <template #suffix>
          <el-icon
            v-if="showVoiceSearch"
            class="voice-search-icon"
            @click="handleVoiceSearch"
          >
            <Microphone />
          </el-icon>
        </template>
      </el-input>

      <el-button
        v-if="showFilterButton"
        type="primary"
        size="small"
        class="filter-button"
        @click="showFilters = true"
      >
        <el-icon><Filter /></el-icon>
        筛选
      </el-button>
    </div>

    <!-- 搜索建议 -->
    <div
      v-if="showSuggestions && suggestions.length > 0"
      class="search-suggestions"
    >
      <div class="suggestions-header">
        <span>搜索建议</span>
        <el-button type="text" size="small" @click="clearSuggestions"
          >清除</el-button
        >
      </div>
      <div class="suggestions-list">
        <div
          v-for="(suggestion, index) in suggestions"
          :key="index"
          class="suggestion-item"
          @click="selectSuggestion(suggestion)"
        >
          <el-icon class="suggestion-icon"><Search /></el-icon>
          <span class="suggestion-text">{{ suggestion }}</span>
        </div>
      </div>
    </div>

    <!-- 历史搜索 -->
    <div v-if="showHistory && searchHistory.length > 0" class="search-history">
      <div class="history-header">
        <span>历史搜索</span>
        <el-button type="text" size="small" @click="clearHistory"
          >清除</el-button
        >
      </div>
      <div class="history-list">
        <el-tag
          v-for="(item, index) in searchHistory"
          :key="index"
          class="history-tag"
          closable
          @click="selectHistory(item)"
          @close="removeHistory(index)"
        >
          {{ item }}
        </el-tag>
      </div>
    </div>

    <!-- 筛选面板 -->
    <el-drawer
      v-model="showFilters"
      title="筛选条件"
      direction="btt"
      size="60%"
      class="filter-drawer"
    >
      <div class="filter-content">
        <slot name="filters">
          <!-- 默认筛选项 -->
          <div class="filter-section">
            <h4>状态</h4>
            <el-checkbox-group v-model="filters.status">
              <el-checkbox value="pending">待处理</el-checkbox>
              <el-checkbox value="processing">处理中</el-checkbox>
              <el-checkbox value="completed">已完成</el-checkbox>
            </el-checkbox-group>
          </div>

          <div class="filter-section">
            <h4>类型</h4>
            <el-checkbox-group v-model="filters.type">
              <el-checkbox value="online">线上任务</el-checkbox>
              <el-checkbox value="offline">线下任务</el-checkbox>
            </el-checkbox-group>
          </div>

          <div class="filter-section">
            <h4>时间范围</h4>
            <el-date-picker
              v-model="filters.dateRange"
              type="daterange"
              range-separator="至"
              start-placeholder="开始日期"
              end-placeholder="结束日期"
              size="small"
              style="width: 100%"
            />
          </div>
        </slot>

        <div class="filter-actions">
          <el-button @click="resetFilters">重置</el-button>
          <el-button type="primary" @click="applyFilters">应用筛选</el-button>
        </div>
      </div>
    </el-drawer>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { Search, Microphone, Filter } from '@element-plus/icons-vue'

// Props
interface Props {
  modelValue?: string
  placeholder?: string
  showVoiceSearch?: boolean
  showFilterButton?: boolean
  suggestions?: string[]
  loading?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  modelValue: '',
  placeholder: '搜索...',
  showVoiceSearch: false,
  showFilterButton: false,
  suggestions: () => [],
  loading: false
})

// Emits
interface Emits {
  (e: 'update:modelValue', value: string): void
  (e: 'search', query: string): void
  (e: 'clear'): void
  (e: 'filter', filters: any): void
  (e: 'voiceSearch'): void
}

const emit = defineEmits<Emits>()

// 响应式数据
const searchQuery = ref(props.modelValue)
const showSuggestions = ref(false)
const showHistory = ref(false)
const showFilters = ref(false)
const searchHistory = ref<string[]>(getStoredHistory())
const filters = ref({
  status: [],
  type: [],
  dateRange: null
})

// 监听搜索框值变化
watch(
  () => props.modelValue,
  newVal => {
    searchQuery.value = newVal
  }
)

watch(searchQuery, newVal => {
  emit('update:modelValue', newVal)

  if (newVal.length > 0) {
    showSuggestions.value = true
    showHistory.value = false
  } else {
    showSuggestions.value = false
    showHistory.value = true
  }
})

// 方法
const handleSearch = (query: string) => {
  if (query.trim()) {
    emit('search', query.trim())
    addToHistory(query.trim())
  }
  showSuggestions.value = false
  showHistory.value = false
}

const handleClear = () => {
  emit('clear')
  showSuggestions.value = false
  showHistory.value = true
}

const handleEnterSearch = () => {
  if (searchQuery.value.trim()) {
    handleSearch(searchQuery.value.trim())
  }
}

const handleVoiceSearch = () => {
  // 检查浏览器是否支持语音识别
  if (
    !('webkitSpeechRecognition' in window) &&
    !('SpeechRecognition' in window)
  ) {
    ElMessage.warning('您的浏览器不支持语音搜索')
    return
  }

  emit('voiceSearch')
  ElMessage.info('语音搜索功能开发中...')
}

const selectSuggestion = (suggestion: string) => {
  searchQuery.value = suggestion
  handleSearch(suggestion)
}

const selectHistory = (item: string) => {
  searchQuery.value = item
  handleSearch(item)
}

const clearSuggestions = () => {
  showSuggestions.value = false
}

const clearHistory = () => {
  searchHistory.value = []
  localStorage.removeItem('searchHistory')
  showHistory.value = false
}

const removeHistory = (index: number) => {
  searchHistory.value.splice(index, 1)
  storeHistory()
}

const addToHistory = (query: string) => {
  const index = searchHistory.value.indexOf(query)
  if (index > -1) {
    searchHistory.value.splice(index, 1)
  }
  searchHistory.value.unshift(query)

  // 限制历史记录数量
  if (searchHistory.value.length > 10) {
    searchHistory.value = searchHistory.value.slice(0, 10)
  }

  storeHistory()
}

const storeHistory = () => {
  localStorage.setItem('searchHistory', JSON.stringify(searchHistory.value))
}

function getStoredHistory(): string[] {
  try {
    const stored = localStorage.getItem('searchHistory')
    return stored ? JSON.parse(stored) : []
  } catch {
    return []
  }
}

const resetFilters = () => {
  filters.value = {
    status: [],
    type: [],
    dateRange: null
  }
}

const applyFilters = () => {
  emit('filter', { ...filters.value })
  showFilters.value = false
  ElMessage.success('筛选条件已应用')
}

// 暴露方法给父组件
defineExpose({
  focus: () => {
    // 聚焦搜索框的方法
  },
  clear: () => {
    searchQuery.value = ''
    handleClear()
  }
})
</script>

<style scoped lang="scss">
@use '@/styles/variables.scss' as *;
@use '@/styles/mixins.scss' as *;

.mobile-search-bar {
  width: 100%;
  position: relative;

  .search-container {
    display: flex;
    gap: $spacing-small;
    align-items: center;

    .search-input {
      flex: 1;

      :deep(.el-input__wrapper) {
        @include mobile-input;
        border-radius: 20px;
        padding: 0 $spacing-base;

        .el-input__inner {
          font-size: $font-size-base;
        }

        .el-input__prefix,
        .el-input__suffix {
          color: $text-color-secondary;
        }
      }
    }

    .voice-search-icon {
      cursor: pointer;
      color: $text-color-secondary;
      transition: color $transition-base;

      &:hover {
        color: $primary-color;
      }
    }

    .filter-button {
      @include touch-target(36px);
      border-radius: 18px;
      flex-shrink: 0;
    }
  }

  .search-suggestions,
  .search-history {
    position: absolute;
    top: 100%;
    left: 0;
    right: 0;
    background: $background-color-white;
    border: 1px solid $border-color-light;
    border-radius: $border-radius-base;
    box-shadow: $box-shadow-light;
    z-index: 1000;
    margin-top: $spacing-extra-small;
    max-height: 300px;
    overflow-y: auto;
    @include mobile-scroll;
  }

  .suggestions-header,
  .history-header {
    @include flex-between;
    padding: $spacing-small $spacing-base;
    border-bottom: 1px solid $border-color-extra-light;

    span {
      font-size: $font-size-small;
      color: $text-color-secondary;
      font-weight: 500;
    }
  }

  .suggestions-list {
    .suggestion-item {
      @include flex-start;
      gap: $spacing-small;
      padding: $spacing-small $spacing-base;
      cursor: pointer;
      transition: background-color $transition-base;
      @include touch-target(44px);

      &:hover {
        background: $background-color-light;
      }

      .suggestion-icon {
        color: $text-color-placeholder;
        font-size: $font-size-small;
      }

      .suggestion-text {
        flex: 1;
        font-size: $font-size-base;
        color: $text-color-primary;
      }
    }
  }

  .history-list {
    padding: $spacing-base;
    display: flex;
    flex-wrap: wrap;
    gap: $spacing-small;

    .history-tag {
      cursor: pointer;
      @include touch-target(32px);

      &:hover {
        background: color.adjust($primary-color, $lightness: 40%);
      }
    }
  }
}

.filter-drawer {
  :deep(.el-drawer__header) {
    padding: $spacing-base;
    margin-bottom: 0;
  }

  :deep(.el-drawer__body) {
    padding: 0;
  }

  .filter-content {
    padding: $spacing-base;
    height: 100%;
    display: flex;
    flex-direction: column;

    .filter-section {
      margin-bottom: $spacing-large;

      h4 {
        margin: 0 0 $spacing-base 0;
        font-size: $font-size-medium;
        color: $text-color-primary;
        font-weight: 600;
      }

      .el-checkbox-group {
        display: flex;
        flex-direction: column;
        gap: $spacing-small;

        .el-checkbox {
          margin-right: 0;
          @include touch-target(44px);
        }
      }
    }

    .filter-actions {
      margin-top: auto;
      padding-top: $spacing-base;
      border-top: 1px solid $border-color-extra-light;
      display: flex;
      gap: $spacing-base;

      .el-button {
        flex: 1;
        @include touch-target(44px);
      }
    }
  }
}
</style>
