<template>
  <el-dialog
    v-model="visible"
    title="签到"
    width="500px"
    :close-on-click-modal="false"
    @close="handleClose"
  >
    <div class="check-in-dialog">
      <div class="current-time">
        <div class="time-display">
          <div class="time">{{ currentTime }}</div>
          <div class="date">{{ currentDate }}</div>
        </div>
        <div class="location-info">
          <el-icon><Location /></el-icon>
          <span>{{ currentLocation || '获取位置中...' }}</span>
        </div>
      </div>

      <el-form
        ref="formRef"
        :model="formData"
        :rules="formRules"
        label-width="80px"
        class="check-in-form"
      >
        <el-form-item label="签到地点" prop="location">
          <el-select
            v-model="formData.location"
            placeholder="选择签到地点"
            style="width: 100%"
            filterable
            allow-create
          >
            <el-option
              v-for="location in locationOptions"
              :key="location"
              :label="location"
              :value="location"
            />
          </el-select>
        </el-form-item>

        <el-form-item label="备注">
          <el-input
            v-model="formData.remark"
            type="textarea"
            :rows="3"
            placeholder="请输入签到备注（可选）"
            maxlength="200"
            show-word-limit
          />
        </el-form-item>

        <el-form-item v-if="requirePhoto" label="签到照片">
          <el-upload
            ref="uploadRef"
            :auto-upload="false"
            :limit="1"
            :accept="'image/*'"
            :before-upload="beforeUpload"
            :on-change="handlePhotoChange"
            :on-exceed="handleExceed"
            :file-list="photoList"
            list-type="picture-card"
            class="photo-upload"
          >
            <el-icon><Plus /></el-icon>
            <template #tip>
              <div class="el-upload__tip">
                只能上传 jpg/png 文件，且不超过 2MB
              </div>
            </template>
          </el-upload>
        </el-form-item>
      </el-form>

      <!-- 地图组件（如果需要） -->
      <div v-if="showMap" class="map-container">
        <div id="check-in-map" class="map"></div>
      </div>
    </div>

    <template #footer>
      <div class="dialog-footer">
        <el-button @click="handleClose">取消</el-button>
        <el-button 
          type="primary" 
          :loading="loading"
          @click="handleSubmit"
        >
          确认签到
        </el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, reactive, computed, watch, onMounted, onUnmounted, nextTick } from 'vue'
import { ElMessage, ElForm } from 'element-plus'
import { Location, Plus } from '@element-plus/icons-vue'
import { attendanceApi } from '@/api/attendance'
import type { CheckInRequest } from '@/types/attendance'

// Props
interface Props {
  modelValue: boolean
}

const props = defineProps<Props>()

// Emits
const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  success: []
}>()

// 响应式数据
const formRef = ref<InstanceType<typeof ElForm>>()
const uploadRef = ref()
const loading = ref(false)
const currentTime = ref('')
const currentDate = ref('')
const currentLocation = ref('')
const requirePhoto = ref(false)
const showMap = ref(false)
const photoList = ref<any[]>([])

// 定时器
let timeTimer: NodeJS.Timeout | null = null

// 计算属性
const visible = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value)
})

// 表单数据
const formData = reactive<CheckInRequest>({
  location: '',
  remark: '',
  photo: ''
})

// 表单验证规则
const formRules = {
  location: [
    { required: true, message: '请选择签到地点', trigger: 'blur' }
  ]
}

// 地点选项
const locationOptions = ref<string[]>([
  '公司',
  '客户现场',
  '远程办公',
  '出差'
])

// 方法
const updateCurrentTime = () => {
  const now = new Date()
  currentTime.value = now.toLocaleTimeString('zh-CN', {
    hour12: false,
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  })
  currentDate.value = now.toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
    weekday: 'long'
  })
}

const getCurrentLocation = () => {
  if (navigator.geolocation) {
    navigator.geolocation.getCurrentPosition(
      (position) => {
        const { latitude, longitude } = position.coords
        // 这里可以调用地图API获取详细地址
        currentLocation.value = `${latitude.toFixed(6)}, ${longitude.toFixed(6)}`
      },
      (error) => {
        console.warn('获取位置失败:', error)
        currentLocation.value = '位置获取失败'
      }
    )
  } else {
    currentLocation.value = '浏览器不支持地理定位'
  }
}

const loadLocationOptions = async () => {
  try {
    const locations = await attendanceApi.getCheckInLocations()
    locationOptions.value = locations
  } catch (error) {
    console.error('加载地点选项失败:', error)
  }
}

const handleClose = () => {
  resetForm()
  emit('update:modelValue', false)
}

const resetForm = () => {
  formData.location = ''
  formData.remark = ''
  formData.photo = ''
  photoList.value = []
  formRef.value?.resetFields()
}

const handleSubmit = async () => {
  try {
    // 表单验证
    const valid = await formRef.value?.validate()
    if (!valid) return

    loading.value = true

    // 准备提交数据
    const submitData: CheckInRequest = {
      location: formData.location,
      remark: formData.remark
    }

    // 如果有照片，添加到请求中
    if (photoList.value.length > 0) {
      submitData.photo = photoList.value[0].raw
    }

    await attendanceApi.checkIn(submitData)
    
    ElMessage.success('签到成功')
    emit('success')
    handleClose()

  } catch (error) {
    console.error('签到失败:', error)
    ElMessage.error('签到失败')
  } finally {
    loading.value = false
  }
}

const beforeUpload = (file: File) => {
  const isImage = file.type.startsWith('image/')
  if (!isImage) {
    ElMessage.error('只能上传图片文件！')
    return false
  }

  const isLt2M = file.size / 1024 / 1024 < 2
  if (!isLt2M) {
    ElMessage.error('图片大小不能超过 2MB！')
    return false
  }

  return false // 阻止自动上传
}

const handlePhotoChange = (file: any) => {
  photoList.value = [file]
}

const handleExceed = () => {
  ElMessage.warning('只能上传一张照片')
}

// 监听
watch(() => visible.value, (val) => {
  if (val) {
    updateCurrentTime()
    timeTimer = setInterval(updateCurrentTime, 1000)
    getCurrentLocation()
    loadLocationOptions()
    
    nextTick(() => {
      formRef.value?.clearValidate()
    })
  } else {
    if (timeTimer) {
      clearInterval(timeTimer)
      timeTimer = null
    }
  }
})

// 生命周期
onMounted(() => {
  // 这里可以初始化地图等组件
})

onUnmounted(() => {
  if (timeTimer) {
    clearInterval(timeTimer)
  }
})
</script>

<style scoped lang="scss">
@use '@/styles/variables.scss' as *;
@use '@/styles/mixins.scss' as *;

.check-in-dialog {
  .current-time {
    text-align: center;
    padding: 24px;
    background: linear-gradient(135deg, #f0f9ff, #ecf5ff);
    border-radius: 12px;
    margin-bottom: 24px;

    .time-display {
      margin-bottom: 12px;

      .time {
        font-size: 32px;
        font-weight: bold;
        color: $primary-color;
        font-family: 'Courier New', monospace;
      }

      .date {
        font-size: 16px;
        color: $text-color-regular;
        margin-top: 4px;
      }
    }

    .location-info {
      @include flex-center;
      gap: 8px;
      color: $text-color-secondary;
      font-size: 14px;
    }
  }

  .check-in-form {
    .photo-upload {
      :deep(.el-upload--picture-card) {
        width: 80px;
        height: 80px;
      }

      :deep(.el-upload-list__item) {
        width: 80px;
        height: 80px;
      }
    }
  }

  .map-container {
    margin-top: 16px;
    height: 200px;
    border-radius: 8px;
    overflow: hidden;

    .map {
      width: 100%;
      height: 100%;
      background: #f5f5f5;
      @include flex-center;
      color: $text-color-placeholder;
    }
  }
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

@include respond-to(sm) {
  .check-in-dialog {
    .current-time {
      padding: 16px;

      .time-display {
        .time {
          font-size: 24px;
        }
      }
    }
  }
}
</style>