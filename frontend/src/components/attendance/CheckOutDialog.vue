<template>
  <el-dialog
    v-model="visible"
    title="签退"
    width="500px"
    :close-on-click-modal="false"
    @close="handleClose"
  >
    <div class="check-out-dialog">
      <div class="work-summary">
        <div class="time-info">
          <div class="current-time">
            <div class="time">{{ currentTime }}</div>
            <div class="date">{{ currentDate }}</div>
          </div>
          <div class="work-duration">
            <h4>今日工作时长</h4>
            <div class="duration">{{ workDuration }}</div>
          </div>
        </div>

        <!-- 工作总结 -->
        <div class="work-stats">
          <div class="stat-item">
            <span class="label">签到时间：</span>
            <span class="value">{{ checkInTime || '--' }}</span>
          </div>
          <div class="stat-item">
            <span class="label">工作时长：</span>
            <span class="value">{{ workDuration }}</span>
          </div>
          <div class="stat-item">
            <span class="label">当前位置：</span>
            <span class="value">{{ currentLocation || '获取中...' }}</span>
          </div>
        </div>
      </div>

      <el-form
        ref="formRef"
        :model="formData"
        :rules="formRules"
        label-width="80px"
        class="check-out-form"
      >
        <el-form-item label="签退地点" prop="location">
          <el-select
            v-model="formData.location"
            placeholder="选择签退地点"
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

        <el-form-item label="工作总结">
          <el-input
            v-model="formData.remark"
            type="textarea"
            :rows="4"
            placeholder="请简要总结今日工作内容（可选）"
            maxlength="500"
            show-word-limit
          />
        </el-form-item>

        <el-form-item v-if="requirePhoto" label="签退照片">
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

        <!-- 加班申请 -->
        <el-form-item>
          <el-checkbox v-model="applyOvertime">
            申请加班（当前工作时长超过{{ overtimeThreshold }}小时）
          </el-checkbox>
        </el-form-item>

        <el-form-item
          v-if="applyOvertime"
          label="加班原因"
          prop="overtimeReason"
        >
          <el-input
            v-model="overtimeReason"
            type="textarea"
            :rows="2"
            placeholder="请说明加班原因"
            maxlength="200"
            show-word-limit
          />
        </el-form-item>
      </el-form>
    </div>

    <template #footer>
      <div class="dialog-footer">
        <el-button @click="handleClose">取消</el-button>
        <el-button type="success" :loading="loading" @click="handleSubmit">
          确认签退
        </el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import {
  ref,
  reactive,
  computed,
  watch,
  onMounted,
  onUnmounted,
  nextTick
} from 'vue'
import { ElMessage, ElForm } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import { attendanceApi } from '@/api/attendance'
import type { CheckOutRequest } from '@/types/attendance'
import { formatTime } from '@/utils/date'

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
const photoList = ref<any[]>([])
const checkInTime = ref('')
const workDuration = ref('0小时0分钟')
const applyOvertime = ref(false)
const overtimeReason = ref('')
const overtimeThreshold = ref(8)

// 定时器
let timeTimer: NodeJS.Timeout | null = null

// 计算属性
const visible = computed({
  get: () => props.modelValue,
  set: value => emit('update:modelValue', value)
})

// 表单数据
const formData = reactive<CheckOutRequest>({
  location: '',
  remark: '',
  photo: ''
})

// 表单验证规则
const formRules = computed(() => ({
  location: [{ required: true, message: '请选择签退地点', trigger: 'blur' }],
  overtimeReason: [
    {
      required: applyOvertime.value,
      message: '请说明加班原因',
      trigger: 'blur'
    }
  ]
}))

// 地点选项
const locationOptions = ref<string[]>(['公司', '客户现场', '远程办公', '出差'])

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

  // 计算工作时长
  calculateWorkDuration()
}

const calculateWorkDuration = () => {
  if (checkInTime.value) {
    const checkIn = new Date(
      `${new Date().toDateString()} ${checkInTime.value}`
    )
    const now = new Date()
    const diff = now.getTime() - checkIn.getTime()

    const hours = Math.floor(diff / (1000 * 60 * 60))
    const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60))

    workDuration.value = `${hours}小时${minutes}分钟`

    // 自动判断是否需要申请加班
    if (hours >= overtimeThreshold.value && !applyOvertime.value) {
      applyOvertime.value = true
    }
  }
}

const getCurrentLocation = () => {
  if (navigator.geolocation) {
    navigator.geolocation.getCurrentPosition(
      position => {
        const { latitude, longitude } = position.coords
        currentLocation.value = `${latitude.toFixed(6)}, ${longitude.toFixed(6)}`
      },
      error => {
        console.warn('获取位置失败:', error)
        currentLocation.value = '位置获取失败'
      }
    )
  } else {
    currentLocation.value = '浏览器不支持地理定位'
  }
}

const loadTodayStatus = async () => {
  try {
    const status = await attendanceApi.getTodayAttendanceStatus()
    if (status.record?.checkInTime) {
      checkInTime.value = formatTime(status.record.checkInTime)
    }
  } catch (error) {
    console.error('加载今日状态失败:', error)
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
  applyOvertime.value = false
  overtimeReason.value = ''
  formRef.value?.resetFields()
}

const handleSubmit = async () => {
  try {
    // 表单验证
    const valid = await formRef.value?.validate()
    if (!valid) return

    loading.value = true

    // 准备提交数据
    const submitData: CheckOutRequest = {
      location: formData.location,
      remark: formData.remark
    }

    // 如果申请加班，在备注中添加加班信息
    if (applyOvertime.value && overtimeReason.value) {
      submitData.remark = `${submitData.remark ? submitData.remark + '\n' : ''}加班申请：${overtimeReason.value}`
    }

    // 如果有照片，添加到请求中
    if (photoList.value.length > 0) {
      submitData.photo = photoList.value[0].raw
    }

    await attendanceApi.checkOut(submitData)

    ElMessage.success('签退成功')
    emit('success')
    handleClose()
  } catch (error) {
    console.error('签退失败:', error)
    ElMessage.error('签退失败')
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
watch(
  () => visible.value,
  val => {
    if (val) {
      updateCurrentTime()
      timeTimer = setInterval(updateCurrentTime, 1000)
      getCurrentLocation()
      loadLocationOptions()
      loadTodayStatus()

      nextTick(() => {
        formRef.value?.clearValidate()
      })
    } else {
      if (timeTimer) {
        clearInterval(timeTimer)
        timeTimer = null
      }
    }
  }
)

// 生命周期
onUnmounted(() => {
  if (timeTimer) {
    clearInterval(timeTimer)
  }
})
</script>

<style scoped lang="scss">
@use '@/styles/variables.scss' as *;
@use '@/styles/mixins.scss' as *;

.check-out-dialog {
  .work-summary {
    background: linear-gradient(135deg, #f0f9ff, #ecf5ff);
    border-radius: 12px;
    padding: 24px;
    margin-bottom: 24px;

    .time-info {
      @include flex-between;
      align-items: center;
      margin-bottom: 20px;

      .current-time {
        text-align: left;

        .time {
          font-size: 28px;
          font-weight: bold;
          color: $primary-color;
          font-family: 'Courier New', monospace;
        }

        .date {
          font-size: 14px;
          color: $text-color-regular;
          margin-top: 4px;
        }
      }

      .work-duration {
        text-align: right;

        h4 {
          font-size: 14px;
          color: $text-color-regular;
          margin: 0 0 8px 0;
        }

        .duration {
          font-size: 24px;
          font-weight: bold;
          color: $success-color;
        }
      }
    }

    .work-stats {
      .stat-item {
        @include flex-between;
        padding: 8px 0;
        border-bottom: 1px solid rgba(255, 255, 255, 0.3);

        &:last-child {
          border-bottom: none;
        }

        .label {
          color: $text-color-regular;
          font-size: 14px;
        }

        .value {
          color: $text-color-primary;
          font-weight: 500;
        }
      }
    }
  }

  .check-out-form {
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
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

@include respond-to(sm) {
  .check-out-dialog {
    .work-summary {
      padding: 16px;

      .time-info {
        flex-direction: column;
        gap: 16px;
        text-align: center;

        .work-duration {
          text-align: center;

          .duration {
            font-size: 20px;
          }
        }
      }
    }
  }
}
</style>
