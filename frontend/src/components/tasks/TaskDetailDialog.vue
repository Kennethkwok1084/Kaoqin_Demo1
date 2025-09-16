<template>
  <el-dialog
    v-model="visible"
    title="任务详情"
    width="1200px"
    @close="handleClose"
    destroy-on-close
  >
    <div v-loading="loading" class="task-detail-dialog">
      <div v-if="task" class="task-content">
        <!-- 任务基本信息 -->
        <el-card class="task-basic-info" shadow="never">
          <template #header>
            <div class="card-header">
              <div class="header-left">
                <el-icon><Document /></el-icon>
                <span class="title">{{ task.title }}</span>
                <el-tag
                  :type="getStatusTagType(task.status || task.task_status || '')"
                  size="large"
                >
                  {{ getTaskStatusConfig(task.status || task.task_status || '').label }}
                </el-tag>
              </div>
              <div class="header-right">
                <el-button type="primary" size="small" @click="editTask">
                  <el-icon><Edit /></el-icon>
                  编辑任务
                </el-button>
                <el-dropdown @command="handleTaskAction">
                  <el-button size="small">
                    操作<el-icon><ArrowDown /></el-icon>
                  </el-button>
                  <template #dropdown>
                    <el-dropdown-menu>
                      <el-dropdown-item
                        command="start"
                        v-if="task.status === 'pending' || task.status === 'assigned'"
                      >
                        开始任务
                      </el-dropdown-item>
                      <el-dropdown-item
                        command="complete"
                        v-if="task.status === 'in_progress'"
                      >
                        完成任务
                      </el-dropdown-item>
                      <el-dropdown-item
                        command="cancel"
                        v-if="task.status !== 'completed' && task.status !== 'cancelled'"
                      >
                        取消任务
                      </el-dropdown-item>
                      <el-dropdown-item
                        command="reopen"
                        v-if="task.status === 'completed' || task.status === 'cancelled'"
                      >
                        重新打开
                      </el-dropdown-item>
                    </el-dropdown-menu>
                  </template>
                </el-dropdown>
              </div>
            </div>
          </template>

          <div class="basic-info-content">
            <el-row :gutter="24">
              <el-col :span="12">
                <div class="info-section">
                  <h4>基本信息</h4>
                  <el-descriptions :column="1" border>
                    <el-descriptions-item label="任务类型">
                      <el-tag
                        :type="getTypeTagType(task.type || task.task_type || '')"
                        size="small"
                      >
                        {{ getTaskTypeConfig(task.type || task.task_type || '').label }}
                      </el-tag>
                    </el-descriptions-item>
                    <el-descriptions-item label="优先级">
                      <el-tag
                        :type="getPriorityTagType(task.priority || '')"
                        size="small"
                      >
                        {{ getTaskPriorityConfig(task.priority || '').label }}
                      </el-tag>
                    </el-descriptions-item>
                    <el-descriptions-item label="位置">{{ task.location || '-' }}</el-descriptions-item>
                    <el-descriptions-item label="负责人">
                      {{ task.assigneeName || task.assignee || '未分配' }}
                    </el-descriptions-item>
                    <el-descriptions-item label="报修人">
                      {{ task.reporterName || task.reporter_name || '-' }}
                    </el-descriptions-item>
                    <el-descriptions-item label="联系方式">
                      {{ task.contactInfo || task.contact_info || '-' }}
                    </el-descriptions-item>
                  </el-descriptions>
                </div>
              </el-col>

              <el-col :span="12">
                <div class="info-section">
                  <h4>时间信息</h4>
                  <el-descriptions :column="1" border>
                    <el-descriptions-item label="创建时间">
                      {{ formatDateTime(task.createdAt || task.created_at || '') }}
                    </el-descriptions-item>
                    <el-descriptions-item label="截止时间">
                      <span :class="getDueDateClass(task.dueDate || task.due_date || '', task.status || '')">
                        {{ formatDateTime(task.dueDate || task.due_date || '') }}
                      </span>
                    </el-descriptions-item>
                    <el-descriptions-item label="开始时间">
                      {{ formatDateTime(task.startedAt || task.started_at || '') }}
                    </el-descriptions-item>
                    <el-descriptions-item label="完成时间">
                      {{ formatDateTime(task.completedAt || task.completed_at || '') }}
                    </el-descriptions-item>
                    <el-descriptions-item label="预估工时">
                      {{ task.estimatedHours || task.estimated_hours || 0 }} 小时
                    </el-descriptions-item>
                    <el-descriptions-item label="实际工时">
                      {{ task.actualHours || task.actual_hours || 0 }} 小时
                    </el-descriptions-item>
                  </el-descriptions>
                </div>
              </el-col>
            </el-row>

            <div class="description-section">
              <h4>任务描述</h4>
              <div class="description-content">
                {{ task.description || '暂无描述' }}
              </div>
            </div>

            <div v-if="task.tags && task.tags.length > 0" class="tags-section">
              <h4>标签</h4>
              <div class="tags-content">
                <el-tag
                  v-for="tag in task.tags"
                  :key="tag"
                  size="small"
                  style="margin-right: 8px; margin-bottom: 4px"
                >
                  {{ tag }}
                </el-tag>
              </div>
            </div>
          </div>
        </el-card>

        <!-- 工时记录 -->
        <el-card class="work-logs-section" shadow="never">
          <template #header>
            <div class="card-header">
              <div class="header-left">
                <el-icon><Clock /></el-icon>
                <span>工时记录</span>
              </div>
              <el-button type="primary" size="small" @click="showAddWorkLogDialog">
                <el-icon><Plus /></el-icon>
                添加工时
              </el-button>
            </div>
          </template>

          <div v-loading="workLogsLoading">
            <el-table :data="workLogs" stripe>
              <el-table-column type="index" label="#" width="50" />
              <el-table-column prop="description" label="工作内容" min-width="200" />
              <el-table-column prop="hours" label="工时(小时)" width="100" />
              <el-table-column prop="createdAt" label="记录时间" width="180">
                <template #default="{ row }">
                  {{ formatDateTime(row.createdAt || row.created_at || '') }}
                </template>
              </el-table-column>
              <el-table-column label="操作" width="100">
                <template #default="{ row }">
                  <el-button
                    type="danger"
                    size="small"
                    link
                    @click="deleteWorkLog(row)"
                  >
                    删除
                  </el-button>
                </template>
              </el-table-column>
            </el-table>

            <div v-if="workLogs.length === 0" class="empty-state">
              <el-empty description="暂无工时记录" />
            </div>
          </div>
        </el-card>

        <!-- 评论区 -->
        <el-card class="comments-section" shadow="never">
          <template #header>
            <div class="card-header">
              <div class="header-left">
                <el-icon><ChatDotRound /></el-icon>
                <span>评论 ({{ comments.length }})</span>
              </div>
            </div>
          </template>

          <div class="comment-input">
            <el-input
              v-model="newComment"
              type="textarea"
              :rows="3"
              placeholder="添加评论..."
              maxlength="500"
              show-word-limit
            />
            <div class="comment-actions">
              <el-button
                type="primary"
                size="small"
                :disabled="!newComment.trim()"
                :loading="addingComment"
                @click="addComment"
              >
                发表评论
              </el-button>
            </div>
          </div>

          <div v-loading="commentsLoading" class="comments-list">
            <div
              v-for="comment in comments"
              :key="comment.id"
              class="comment-item"
            >
              <div class="comment-header">
                <span class="author">{{ comment.authorName || comment.author_name || '匿名' }}</span>
                <span class="time">{{ formatDateTime(comment.createdAt || comment.created_at || '') }}</span>
                <el-button
                  v-if="canDeleteComment(comment)"
                  type="danger"
                  size="small"
                  link
                  @click="deleteComment(comment)"
                >
                  删除
                </el-button>
              </div>
              <div class="comment-content">{{ comment.content }}</div>
            </div>

            <div v-if="comments.length === 0" class="empty-state">
              <el-empty description="暂无评论" />
            </div>
          </div>
        </el-card>

        <!-- 附件列表 -->
        <el-card class="attachments-section" shadow="never">
          <template #header>
            <div class="card-header">
              <div class="header-left">
                <el-icon><Paperclip /></el-icon>
                <span>附件 ({{ attachments.length }})</span>
              </div>
              <el-upload
                ref="uploadRef"
                :auto-upload="false"
                :show-file-list="false"
                :before-upload="beforeUpload"
                :on-change="handleFileUpload"
                multiple
              >
                <el-button type="primary" size="small">
                  <el-icon><Upload /></el-icon>
                  上传附件
                </el-button>
              </el-upload>
            </div>
          </template>

          <div v-loading="attachmentsLoading">
            <div v-if="attachments.length > 0" class="attachments-list">
              <div
                v-for="attachment in attachments"
                :key="attachment.id"
                class="attachment-item"
              >
                <div class="attachment-info">
                  <el-icon><Document /></el-icon>
                  <span class="filename">{{ attachment.fileName || attachment.file_name }}</span>
                  <span class="filesize">({{ formatFileSize(attachment.fileSize || 0) }})</span>
                </div>
                <div class="attachment-actions">
                  <el-button
                    type="primary"
                    size="small"
                    link
                    @click="downloadAttachment(attachment)"
                  >
                    下载
                  </el-button>
                  <el-button
                    type="danger"
                    size="small"
                    link
                    @click="deleteAttachment(attachment)"
                  >
                    删除
                  </el-button>
                </div>
              </div>
            </div>

            <div v-else class="empty-state">
              <el-empty description="暂无附件" />
            </div>
          </div>
        </el-card>
      </div>

      <div v-else-if="!loading" class="empty-state">
        <el-empty description="任务不存在或已被删除" />
      </div>
    </div>

    <template #footer>
      <div class="dialog-footer">
        <el-button @click="visible = false">关闭</el-button>
        <el-button v-if="task" type="primary" @click="editTask">
          编辑任务
        </el-button>
      </div>
    </template>

    <!-- 添加工时对话框 -->
    <el-dialog
      v-model="showWorkLogDialog"
      title="添加工时记录"
      width="500px"
      @close="resetWorkLogForm"
    >
      <el-form
        ref="workLogFormRef"
        :model="workLogForm"
        :rules="workLogRules"
        label-width="100px"
      >
        <el-form-item label="工作内容" prop="description">
          <el-input
            v-model="workLogForm.description"
            type="textarea"
            :rows="3"
            placeholder="描述具体的工作内容"
            maxlength="200"
            show-word-limit
          />
        </el-form-item>
        <el-form-item label="工时(小时)" prop="hours">
          <el-input-number
            v-model="workLogForm.hours"
            :min="0.1"
            :max="24"
            :step="0.1"
            placeholder="工时"
            style="width: 100%"
          />
        </el-form-item>
      </el-form>

      <template #footer>
        <div class="dialog-footer">
          <el-button @click="showWorkLogDialog = false">取消</el-button>
          <el-button
            type="primary"
            :loading="addingWorkLog"
            @click="addWorkLog"
          >
            添加
          </el-button>
        </div>
      </template>
    </el-dialog>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, reactive, computed, watch, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import type { FormInstance, FormRules, UploadFile } from 'element-plus'
import {
  Document,
  Edit,
  ArrowDown,
  Clock,
  Plus,
  ChatDotRound,
  Paperclip,
  Upload
} from '@element-plus/icons-vue'
import { tasksApi } from '@/api/tasks'
import type { Task, TaskWorkLog, TaskComment } from '@/types/task'
import {
  TASK_TYPE_CONFIG,
  TASK_PRIORITY_CONFIG,
  TASK_STATUS_CONFIG
} from '@/types/task'
import {
  getTaskTypeConfig,
  getTaskPriorityConfig,
  getTaskStatusConfig
} from '@/types/type-helpers'

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

// Refs
const uploadRef = ref()
const workLogFormRef = ref<FormInstance>()

// 响应式数据
const loading = ref(false)
const task = ref<Task | null>(null)
const workLogs = ref<TaskWorkLog[]>([])
const comments = ref<TaskComment[]>([])
const attachments = ref<any[]>([])
const workLogsLoading = ref(false)
const commentsLoading = ref(false)
const attachmentsLoading = ref(false)
const addingComment = ref(false)
const addingWorkLog = ref(false)
const newComment = ref('')
const showWorkLogDialog = ref(false)

// 工时表单数据
const workLogForm = reactive({
  description: '',
  hours: 1
})

const workLogRules: FormRules = {
  description: [
    { required: true, message: '请输入工作内容', trigger: 'blur' },
    { min: 5, max: 200, message: '工作内容长度应在5-200个字符之间', trigger: 'blur' }
  ],
  hours: [
    { required: true, message: '请输入工时', trigger: 'blur' },
    { type: 'number', min: 0.1, max: 24, message: '工时应在0.1-24小时之间', trigger: 'change' }
  ]
}

// 计算属性
const visible = computed({
  get: () => props.modelValue,
  set: value => emit('update:modelValue', value)
})

// 方法
const loadTaskDetail = async () => {
  if (!props.taskId) return

  try {
    loading.value = true
    task.value = await tasksApi.getTask(props.taskId)

    // 同时加载相关数据
    await Promise.all([
      loadWorkLogs(),
      loadComments(),
      loadAttachments()
    ])
  } catch (error) {
    console.error('加载任务详情失败:', error)
    ElMessage.error('加载任务详情失败')
  } finally {
    loading.value = false
  }
}

const loadWorkLogs = async () => {
  if (!props.taskId) return

  try {
    workLogsLoading.value = true
    workLogs.value = await tasksApi.getWorkLogs(props.taskId)
  } catch (error) {
    console.error('加载工时记录失败:', error)
  } finally {
    workLogsLoading.value = false
  }
}

const loadComments = async () => {
  if (!props.taskId) return

  try {
    commentsLoading.value = true
    comments.value = await tasksApi.getComments(props.taskId)
  } catch (error) {
    console.error('加载评论失败:', error)
  } finally {
    commentsLoading.value = false
  }
}

const loadAttachments = async () => {
  if (!props.taskId || !task.value) return

  try {
    attachmentsLoading.value = true
    // 如果任务对象包含附件信息，直接使用
    attachments.value = (task.value as any).attachments || []
  } catch (error) {
    console.error('加载附件失败:', error)
  } finally {
    attachmentsLoading.value = false
  }
}

const handleClose = () => {
  emit('update:modelValue', false)
  resetData()
}

const resetData = () => {
  task.value = null
  workLogs.value = []
  comments.value = []
  attachments.value = []
  newComment.value = ''
  showWorkLogDialog.value = false
  resetWorkLogForm()
}

const editTask = () => {
  // 触发编辑事件，父组件处理
  emit('updated')
  ElMessage.info('编辑功能需要在父组件中实现')
}

const handleTaskAction = async (command: string) => {
  if (!task.value) return

  try {
    switch (command) {
      case 'start':
        await tasksApi.startTask(task.value.id)
        ElMessage.success('任务已开始')
        break
      case 'complete':
        await tasksApi.completeTask(task.value.id)
        ElMessage.success('任务已完成')
        break
      case 'cancel':
        const { value: reason } = await ElMessageBox.prompt(
          '请输入取消原因',
          '取消任务'
        )
        await tasksApi.cancelTask(task.value.id, reason)
        ElMessage.success('任务已取消')
        break
      case 'reopen':
        const { value: reopenReason } = await ElMessageBox.prompt(
          '请输入重新打开原因',
          '重新打开任务'
        )
        await tasksApi.reopenTask(task.value.id, reopenReason)
        ElMessage.success('任务已重新打开')
        break
    }

    // 重新加载任务详情
    await loadTaskDetail()
    emit('updated')
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('操作失败')
    }
  }
}

const showAddWorkLogDialog = () => {
  showWorkLogDialog.value = true
}

const resetWorkLogForm = () => {
  Object.assign(workLogForm, {
    description: '',
    hours: 1
  })
  workLogFormRef.value?.clearValidate()
}

const addWorkLog = async () => {
  if (!workLogFormRef.value || !props.taskId) return

  try {
    await workLogFormRef.value.validate()
    addingWorkLog.value = true

    await tasksApi.addWorkLog(
      props.taskId,
      workLogForm.description,
      workLogForm.hours
    )

    ElMessage.success('工时记录添加成功')
    showWorkLogDialog.value = false
    resetWorkLogForm()
    await loadWorkLogs()
    emit('updated')
  } catch (error) {
    ElMessage.error('添加工时记录失败')
  } finally {
    addingWorkLog.value = false
  }
}

const deleteWorkLog = async (workLog: TaskWorkLog) => {
  if (!props.taskId) return

  try {
    await ElMessageBox.confirm('确定要删除这条工时记录吗？', '删除确认')
    await tasksApi.deleteWorkLog(props.taskId, workLog.id)
    ElMessage.success('工时记录删除成功')
    await loadWorkLogs()
    emit('updated')
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除工时记录失败')
    }
  }
}

const addComment = async () => {
  if (!props.taskId || !newComment.value.trim()) return

  try {
    addingComment.value = true
    await tasksApi.addComment(props.taskId, newComment.value.trim())
    ElMessage.success('评论添加成功')
    newComment.value = ''
    await loadComments()
  } catch (error) {
    ElMessage.error('添加评论失败')
  } finally {
    addingComment.value = false
  }
}

const deleteComment = async (comment: TaskComment) => {
  if (!props.taskId) return

  try {
    await ElMessageBox.confirm('确定要删除这条评论吗？', '删除确认')
    await tasksApi.deleteComment(props.taskId, comment.id)
    ElMessage.success('评论删除成功')
    await loadComments()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除评论失败')
    }
  }
}

const canDeleteComment = (comment: TaskComment): boolean => {
  // 这里可以根据权限判断是否可以删除评论
  // 暂时返回 true，实际应该检查当前用户权限
  return true
}

const beforeUpload = (file: File) => {
  const isLt10M = file.size / 1024 / 1024 < 10
  if (!isLt10M) {
    ElMessage.error('文件大小不能超过 10MB！')
    return false
  }
  return false // 阻止自动上传
}

const handleFileUpload = async (file: UploadFile) => {
  if (!props.taskId || !file.raw) return

  try {
    const result = await tasksApi.uploadAttachment(props.taskId, file.raw)
    ElMessage.success('附件上传成功')
    await loadAttachments()
  } catch (error) {
    ElMessage.error('附件上传失败')
  }
}

const downloadAttachment = async (attachment: any) => {
  if (!props.taskId) return

  try {
    await tasksApi.downloadAttachment(
      props.taskId,
      attachment.id,
      attachment.fileName || attachment.file_name
    )
  } catch (error) {
    ElMessage.error('下载失败')
  }
}

const deleteAttachment = async (attachment: any) => {
  if (!props.taskId) return

  try {
    await ElMessageBox.confirm('确定要删除这个附件吗？', '删除确认')
    await tasksApi.deleteAttachment(props.taskId, attachment.id)
    ElMessage.success('附件删除成功')
    await loadAttachments()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除附件失败')
    }
  }
}

// 工具方法
const formatDateTime = (dateString: string): string => {
  if (!dateString) return '-'
  return new Date(dateString).toLocaleString('zh-CN')
}

const formatFileSize = (size: number): string => {
  if (size < 1024) return `${size} B`
  if (size < 1024 * 1024) return `${(size / 1024).toFixed(1)} KB`
  return `${(size / 1024 / 1024).toFixed(1)} MB`
}

const getTypeTagType = (type: string): string => {
  const typeMap: Record<string, string> = {
    repair: 'primary',
    monitoring: 'success',
    assistance: 'warning'
  }
  return typeMap[type] || 'info'
}

const getPriorityTagType = (priority: string): string => {
  const priorityMap: Record<string, string> = {
    low: 'info',
    medium: 'warning',
    high: 'danger',
    urgent: 'danger'
  }
  return priorityMap[priority] || 'info'
}

const getStatusTagType = (status: string): string => {
  const statusMap: Record<string, string> = {
    pending: 'info',
    in_progress: 'warning',
    completed: 'success',
    cancelled: 'danger'
  }
  return statusMap[status] || 'info'
}

const getDueDateClass = (dueDate: string, status: string): string => {
  if (!dueDate || status === 'completed') return ''

  const now = new Date()
  const due = new Date(dueDate)
  const diffTime = due.getTime() - now.getTime()
  const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24))

  if (diffDays < 0) return 'overdue'
  if (diffDays <= 1) return 'due-soon'
  return ''
}

// 监听
watch(
  () => [props.modelValue, props.taskId],
  ([visible, taskId]) => {
    if (visible && taskId) {
      loadTaskDetail()
    }
  },
  { immediate: true }
)
</script>

<style scoped lang="scss">
@use '@/styles/variables.scss' as *;
@use '@/styles/mixins.scss' as *;
@use 'sass:color';

.task-detail-dialog {
  .task-content {
    .task-basic-info,
    .work-logs-section,
    .comments-section,
    .attachments-section {
      margin-bottom: 20px;

      &:last-child {
        margin-bottom: 0;
      }
    }

    .card-header {
      @include flex-between;
      align-items: center;

      .header-left {
        @include flex-start;
        align-items: center;
        gap: 8px;
        font-weight: 500;

        .title {
          font-size: 16px;
          color: $text-color-primary;
        }
      }

      .header-right {
        @include flex-center;
        gap: 8px;
      }
    }

    .basic-info-content {
      .info-section {
        h4 {
          margin: 0 0 12px 0;
          font-size: 14px;
          font-weight: 600;
          color: $text-color-primary;
        }
      }

      .description-section,
      .tags-section {
        margin-top: 20px;

        h4 {
          margin: 0 0 12px 0;
          font-size: 14px;
          font-weight: 600;
          color: $text-color-primary;
        }

        .description-content {
          padding: 12px;
          background: $background-color-light;
          border-radius: $border-radius-base;
          color: $text-color-regular;
          line-height: 1.6;
          min-height: 60px;
        }

        .tags-content {
          display: flex;
          flex-wrap: wrap;
          gap: 4px;
        }
      }
    }

    .comments-section {
      .comment-input {
        margin-bottom: 20px;

        .comment-actions {
          @include flex-end;
          margin-top: 8px;
        }
      }

      .comments-list {
        .comment-item {
          padding: 12px;
          border: 1px solid $border-color-lighter;
          border-radius: $border-radius-base;
          margin-bottom: 12px;

          &:last-child {
            margin-bottom: 0;
          }

          .comment-header {
            @include flex-between;
            align-items: center;
            margin-bottom: 8px;

            .author {
              font-weight: 500;
              color: $text-color-primary;
            }

            .time {
              font-size: 12px;
              color: $text-color-placeholder;
            }
          }

          .comment-content {
            color: $text-color-regular;
            line-height: 1.6;
          }
        }
      }
    }

    .attachments-section {
      .attachments-list {
        .attachment-item {
          @include flex-between;
          align-items: center;
          padding: 12px;
          border: 1px solid $border-color-lighter;
          border-radius: $border-radius-base;
          margin-bottom: 12px;

          &:last-child {
            margin-bottom: 0;
          }

          .attachment-info {
            @include flex-start;
            align-items: center;
            gap: 8px;
            flex: 1;

            .filename {
              font-weight: 500;
              color: $text-color-primary;
            }

            .filesize {
              font-size: 12px;
              color: $text-color-placeholder;
            }
          }

          .attachment-actions {
            @include flex-center;
            gap: 8px;
          }
        }
      }
    }
  }

  .empty-state {
    padding: 40px 20px;
    text-align: center;
  }
}

.dialog-footer {
  @include flex-end;
  gap: 12px;
}

// 状态样式
.overdue {
  color: $danger-color;
  font-weight: 600;
}

.due-soon {
  color: $warning-color;
  font-weight: 600;
}

// 响应式设计
@include respond-to(md) {
  .task-detail-dialog {
    .basic-info-content {
      .el-row .el-col {
        margin-bottom: 20px;
      }
    }

    .card-header {
      flex-direction: column;
      gap: 12px;
      align-items: stretch;

      .header-right {
        justify-content: flex-start;
      }
    }
  }
}

@include respond-to(sm) {
  .task-detail-dialog {
    .attachments-section {
      .attachment-item {
        flex-direction: column;
        align-items: stretch;
        gap: 12px;

        .attachment-actions {
          justify-content: flex-start;
        }
      }
    }
  }
}
</style>
