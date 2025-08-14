<template>
  <el-dialog
    v-model="visible"
    title="任务详情"
    width="1000px"
    @close="handleClose"
  >
    <div class="task-detail-dialog">
      <p>任务详情组件开发中...</p>
      <p v-if="taskId">当前查看任务ID：{{ taskId }}</p>
    </div>

    <template #footer>
      <div class="dialog-footer">
        <el-button @click="visible = false">关闭</el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { computed } from 'vue'

// Props
interface Props {
  modelValue: boolean
  taskId?: number | null
}

const props = withDefaults(defineProps<Props>(), {
  taskId: null
})

// Emits
const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  updated: []
}>()

// 计算属性
const visible = computed({
  get: () => props.modelValue,
  set: value => emit('update:modelValue', value)
})

// 方法
const handleClose = () => {
  emit('update:modelValue', false)
}
</script>

<style scoped lang="scss">
.task-detail-dialog {
  padding: 20px;
  text-align: center;
  color: #666;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}
</style>
