<template>
  <a-modal
    v-model:open="visible"
    title="标记为线下任务"
    width="800px"
    @cancel="handleCancel"
    :footer="null"
  >
    <div class="offline-marking-form">
      <a-form
        ref="formRef"
        :model="formData"
        :rules="formRules"
        layout="vertical"
      >
        <a-alert
          message="线下任务说明"
          description="将此任务标记为线下任务后，系统将按照线下任务工时标准（100分钟/单）进行计算。请填写详细的检修信息。"
          type="info"
          show-icon
          style="margin-bottom: 24px"
        />

        <a-row :gutter="16">
          <a-col :span="12">
            <a-form-item label="任务标题" name="title">
              <a-input v-model:value="formData.title" disabled />
            </a-form-item>
          </a-col>
          <a-col :span="12">
            <a-form-item label="报修位置" name="location">
              <a-input v-model:value="formData.location" disabled />
            </a-form-item>
          </a-col>
        </a-row>

        <a-form-item label="检修结果" name="repairResult" required>
          <a-select
            v-model:value="formData.repairResult"
            placeholder="请选择检修结果"
            size="large"
          >
            <a-select-option value="resolved">问题已解决</a-select-option>
            <a-select-option value="partially_resolved">部分解决</a-select-option>
            <a-select-option value="unresolved">未解决</a-select-option>
            <a-select-option value="needs_followup">需要后续跟进</a-select-option>
            <a-select-option value="hardware_replacement">硬件更换</a-select-option>
            <a-select-option value="software_fix">软件修复</a-select-option>
          </a-select>
        </a-form-item>

        <a-form-item label="检修内容" name="repairContent" required>
          <a-textarea
            v-model:value="formData.repairContent"
            placeholder="请详细描述检修过程、采取的措施、遇到的问题等..."
            :rows="4"
            show-count
            :maxlength="500"
          />
        </a-form-item>

        <a-form-item label="检修图片" name="repairImages">
          <div class="image-upload-section">
            <a-upload
              v-model:file-list="imageFileList"
              :custom-request="handleImageUpload"
              :before-upload="beforeImageUpload"
              :on-remove="handleImageRemove"
              list-type="picture-card"
              :multiple="true"
              accept="image/*"
              class="repair-image-uploader"
            >
              <div v-if="imageFileList.length < 6" class="upload-button">
                <PlusOutlined />
                <div style="margin-top: 8px">上传图片</div>
              </div>
            </a-upload>
            
            <div class="upload-tips">
              <a-typography-text type="secondary" style="font-size: 12px;">
                支持格式：JPG、PNG、GIF | 单张不超过5MB | 最多6张图片
              </a-typography-text>
            </div>
          </div>
        </a-form-item>

        <a-form-item label="预计用时" name="estimatedDuration">
          <a-row :gutter="16" align="middle">
            <a-col :span="16">
              <a-slider
                v-model:value="formData.estimatedDuration"
                :min="30"
                :max="300"
                :step="15"
                :marks="durationMarks"
                :tip-formatter="formatDurationTip"
              />
            </a-col>
            <a-col :span="8">
              <a-input-number
                v-model:value="formData.estimatedDuration"
                :min="30"
                :max="300"
                :step="15"
                addon-after="分钟"
                style="width: 100%"
              />
            </a-col>
          </a-row>
          <a-typography-text type="secondary" style="font-size: 12px;">
            系统默认线下任务100分钟，您可以根据实际情况调整
          </a-typography-text>
        </a-form-item>

        <a-form-item label="备注信息" name="remarks">
          <a-textarea
            v-model:value="formData.remarks"
            placeholder="其他需要说明的信息（可选）"
            :rows="2"
            show-count
            :maxlength="200"
          />
        </a-form-item>

        <!-- 重要提醒 -->
        <a-alert
          message="重要提醒"
          type="warning"
          show-icon
        >
          <template #description>
            <ul style="margin: 0; padding-left: 20px;">
              <li>线下任务标记后不可撤销，请确认无误后提交</li>
              <li>此任务将按照线下工时标准计入您的月度工时</li>
              <li>管理员可能会对线下任务进行抽查验证</li>
            </ul>
          </template>
        </a-alert>
      </a-form>
    </div>

    <template #footer>
      <div class="modal-footer">
        <a-button @click="handleCancel" size="large">
          取消
        </a-button>
        <a-button 
          type="primary" 
          @click="handleSubmit" 
          :loading="submitLoading"
          size="large"
        >
          确认标记为线下任务
        </a-button>
      </div>
    </template>
  </a-modal>
</template>

<script setup lang="ts">
import { ref, reactive, computed, watch } from 'vue'
import { message, type FormInstance } from 'ant-design-vue'
import { api } from '@/api/client'
import {
  PlusOutlined
} from '@ant-design/icons-vue'

// Props和Emits
interface Props {
  visible: boolean
  taskData: any
}

interface Emits {
  (e: 'update:visible', value: boolean): void
  (e: 'success'): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

// 响应式数据
const formRef = ref<FormInstance>()
const submitLoading = ref(false)
const imageFileList = ref([])

// 表单数据
const formData = reactive({
  title: '',
  location: '',
  repairResult: '',
  repairContent: '',
  repairImages: [] as string[],
  estimatedDuration: 100,
  remarks: ''
})

// 表单验证规则
const formRules = {
  repairResult: [
    { required: true, message: '请选择检修结果', trigger: 'change' }
  ],
  repairContent: [
    { required: true, message: '请填写检修内容', trigger: 'blur' },
    { min: 10, message: '检修内容不能少于10个字符', trigger: 'blur' }
  ]
}

// 用时标记
const durationMarks = {
  30: '30分',
  60: '1小时',
  100: '默认',
  180: '3小时',
  300: '5小时'
}

// 计算属性
const visible = computed({
  get: () => props.visible,
  set: (val) => emit('update:visible', val)
})

// 监听任务数据变化
watch(() => props.taskData, (newData) => {
  if (newData) {
    formData.title = newData.title || ''
    formData.location = newData.location || ''
  }
}, { immediate: true, deep: true })

// 格式化用时提示
const formatDurationTip = (value: number) => {
  const hours = Math.floor(value / 60)
  const minutes = value % 60
  if (hours > 0) {
    return minutes > 0 ? `${hours}小时${minutes}分钟` : `${hours}小时`
  }
  return `${minutes}分钟`
}

// 图片上传前验证
const beforeImageUpload = (file: File) => {
  const isImage = file.type.startsWith('image/')
  if (!isImage) {
    message.error('只能上传图片文件!')
    return false
  }
  
  const isLt5M = file.size / 1024 / 1024 < 5
  if (!isLt5M) {
    message.error('图片大小不能超过5MB!')
    return false
  }
  
  if (imageFileList.value.length >= 6) {
    message.error('最多只能上传6张图片!')
    return false
  }
  
  return true
}

// 自定义图片上传
const handleImageUpload = ({ file, onSuccess, onError }: any) => {
  const formData = new FormData()
  formData.append('file', file)
  formData.append('type', 'repair_image')
  
  // 模拟上传API调用
  setTimeout(() => {
    try {
      // 这里应该调用真实的上传API
      const mockUrl = URL.createObjectURL(file)
      onSuccess({
        url: mockUrl,
        name: file.name
      })
      message.success(`${file.name} 上传成功`)
    } catch (error) {
      console.error('Upload error:', error)
      onError(error)
      message.error(`${file.name} 上传失败`)
    }
  }, 1000)
}

// 移除图片
const handleImageRemove = (file: any) => {
  const index = formData.repairImages.findIndex(img => img === file.response?.url)
  if (index > -1) {
    formData.repairImages.splice(index, 1)
  }
  message.info('图片已移除')
}

// 监听图片列表变化，更新formData
watch(imageFileList, (newList) => {
  formData.repairImages = newList
    .filter((file: any) => file.status === 'done' && file.response?.url)
    .map((file: any) => file.response.url)
}, { deep: true })

// 提交表单
const handleSubmit = async () => {
  try {
    // 表单验证
    await formRef.value?.validate()
    
    submitLoading.value = true
    
    // 准备提交数据
    const submitData = {
      taskId: props.taskData?.id,
      repairResult: formData.repairResult,
      repairContent: formData.repairContent,
      repairImages: formData.repairImages,
      estimatedDuration: formData.estimatedDuration,
      remarks: formData.remarks,
      isOffline: true
    }
    
    // 调用API标记为线下任务
    const response = await api.markTaskAsOffline(submitData)
    
    if (response.success) {
      message.success('任务已成功标记为线下任务')
      emit('success')
      handleCancel()
    } else {
      throw new Error(response.message || '标记失败')
    }
  } catch (error: any) {
    console.error('Submit offline task error:', error)
    
    if (error.errorFields) {
      // 表单验证错误
      message.error('请完善必填信息')
      return
    }
    
    const errorMessage = error.response?.data?.message || error.message || '标记失败，请稍后重试'
    message.error(errorMessage)
  } finally {
    submitLoading.value = false
  }
}

// 取消操作
const handleCancel = () => {
  // 重置表单
  formRef.value?.resetFields()
  imageFileList.value = []
  Object.assign(formData, {
    title: '',
    location: '',
    repairResult: '',
    repairContent: '',
    repairImages: [],
    estimatedDuration: 100,
    remarks: ''
  })
  
  emit('update:visible', false)
}
</script>

<style scoped>
.offline-marking-form {
  padding: 8px 0;
}

.image-upload-section {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.repair-image-uploader {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

:deep(.ant-upload-select-picture-card) {
  width: 104px;
  height: 104px;
  border-radius: 8px;
}

:deep(.ant-upload-list-picture-card .ant-upload-list-item) {
  width: 104px;
  height: 104px;
  border-radius: 8px;
}

.upload-button {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: #8c8c8c;
  font-size: 14px;
}

.upload-tips {
  margin-top: 8px;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

/* 表单样式优化 */
:deep(.ant-form-item-label) {
  font-weight: 500;
}

:deep(.ant-slider) {
  margin: 16px 0;
}

:deep(.ant-slider-mark-text) {
  font-size: 12px;
}

:deep(.ant-alert) {
  border-radius: 8px;
}

:deep(.ant-alert-message) {
  font-weight: 500;
}

/* 滑块样式优化 */
:deep(.ant-slider-track) {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

:deep(.ant-slider-handle) {
  border: 2px solid #667eea;
  box-shadow: 0 2px 6px rgba(102, 126, 234, 0.3);
}

/* 按钮样式优化 */
:deep(.ant-btn-lg) {
  height: 44px;
  padding: 0 20px;
  font-size: 15px;
  border-radius: 8px;
  font-weight: 500;
}

:deep(.ant-btn-primary) {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border: none;
  box-shadow: 0 3px 10px rgba(102, 126, 234, 0.3);
}

:deep(.ant-btn-primary:hover) {
  transform: translateY(-1px);
  box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
}

/* 响应式优化 */
@media (max-width: 768px) {
  :deep(.ant-modal) {
    width: 95% !important;
    max-width: 95% !important;
  }
  
  .repair-image-uploader {
    justify-content: center;
  }
  
  :deep(.ant-col) {
    margin-bottom: 16px;
  }
}
</style>