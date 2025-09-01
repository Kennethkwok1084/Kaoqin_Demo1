<template>
  <div class="desktop-settings">
    <div class="page-header">
      <div class="header-content">
        <div class="header-text">
          <h1>ûß¾n</h1>
          <p>MnåöÄûßÂpI8Ã¾n</p>
        </div>
        <div class="header-actions">
          <a-button 
            type="primary" 
            :loading="saveLoading" 
            @click="saveAllSettings"
          >
            ÝXhè¾n
          </a-button>
        </div>
      </div>
    </div>

    <div class="settings-content">
      <a-row :gutter="24">
        <!-- ;¾nb -->
        <a-col :xs="24" :lg="16">
          <div class="settings-panels">
            <!-- åö¡—Ä -->
            <div class="setting-panel">
              <div class="panel-header">
                <h3>åö¡—Ä</h3>
                <p>¾n{‹û¡„ú@åöŒVé:6</p>
              </div>
              
              <a-form layout="vertical">
                <div class="setting-group">
                  <h4>ú@åö¾n</h4>
                  <a-row :gutter="16">
                    <a-col :span="12">
                      <a-form-item label="¿
û¡åö">
                        <a-input-number
                          v-model:value="workHourRules.onlineTaskMinutes"
                          :min="10"
                          :max="300"
                          :step="5"
                          addon-after="Ÿ"
                          style="width: 100%"
                        />
                      </a-form-item>
                    </a-col>
                    <a-col :span="12">
                      <a-form-item label="¿û¡åö">
                        <a-input-number
                          v-model:value="workHourRules.offlineTaskMinutes"
                          :min="30"
                          :max="600"
                          :step="10"
                          addon-after="Ÿ"
                          style="width: 100%"
                        />
                      </a-form-item>
                    </a-col>
                  </a-row>
                </div>

                <div class="setting-group">
                  <h4>V±:6</h4>
                  <a-row :gutter="16">
                    <a-col :span="8">
                      <a-form-item label="Uû¡V±">
                        <a-input-number
                          v-model:value="workHourRules.rushOrderBonus"
                          :min="0"
                          :max="120"
                          :step="5"
                          addon-after="Ÿ"
                          style="width: 100%"
                        />
                      </a-form-item>
                    </a-col>
                    <a-col :span="8">
                      <a-form-item label="^Ø¤}ÄV±">
                        <a-input-number
                          v-model:value="workHourRules.positiveReviewBonus"
                          :min="0"
                          :max="120"
                          :step="5"
                          addon-after="Ÿ"
                          style="width: 100%"
                        />
                      </a-form-item>
                    </a-col>
                    <a-col :span="8">
                      <a-form-item label="O©û¡ûp">
                        <a-input-number
                          v-model:value="workHourRules.assistanceMultiplier"
                          :min="0.5"
                          :max="2.0"
                          :step="0.1"
                          addon-after=""
                          style="width: 100%"
                        />
                      </a-form-item>
                    </a-col>
                  </a-row>
                </div>

                <div class="setting-group">
                  <h4>éZ:6</h4>
                  <a-row :gutter="16">
                    <a-col :span="8">
                      <a-form-item label="…öÍ”cö">
                        <a-input-number
                          v-model:value="workHourRules.lateResponsePenalty"
                          :min="0"
                          :max="120"
                          :step="5"
                          addon-after="Ÿ"
                          style="width: 100%"
                        />
                      </a-form-item>
                    </a-col>
                    <a-col :span="8">
                      <a-form-item label="…öcö">
                        <a-input-number
                          v-model:value="workHourRules.lateCompletionPenalty"
                          :min="0"
                          :max="120"
                          :step="5"
                          addon-after="Ÿ"
                          style="width: 100%"
                        />
                      </a-form-item>
                    </a-col>
                    <a-col :span="8">
                      <a-form-item label="îÄcö">
                        <a-input-number
                          v-model:value="workHourRules.negativeReviewPenalty"
                          :min="0"
                          :max="180"
                          :step="10"
                          addon-after="Ÿ"
                          style="width: 100%"
                        />
                      </a-form-item>
                    </a-col>
                  </a-row>
                </div>

                <div class="setting-group">
                  <h4>öôP6</h4>
                  <a-row :gutter="16">
                    <a-col :span="12">
                      <a-form-item label="Í”öôP6">
                        <a-input-number
                          v-model:value="workHourRules.responseTimeLimit"
                          :min="1"
                          :max="72"
                          :step="1"
                          addon-after="ö"
                          style="width: 100%"
                        />
                      </a-form-item>
                    </a-col>
                    <a-col :span="12">
                      <a-form-item label="öôP6">
                        <a-input-number
                          v-model:value="workHourRules.completionTimeLimit"
                          :min="4"
                          :max="168"
                          :step="4"
                          addon-after="ö"
                          style="width: 100%"
                        />
                      </a-form-item>
                    </a-col>
                  </a-row>
                </div>
              </a-form>
            </div>

            <!-- äÄ¾n -->
            <div class="setting-panel">
              <div class="panel-header">
                <h3>äÄ¾n</h3>
                <p>¾näøs„¡Ä</p>
              </div>

              <a-form layout="vertical">
                <div class="setting-group">
                  <h4>åöÓlÄ</h4>
                  <a-row :gutter="16">
                    <a-col :span="12">
                      <a-form-item label="¦Æåö">
                        <a-input-number
                          v-model:value="attendanceRules.standardMonthlyHours"
                          :min="20"
                          :max="200"
                          :step="5"
                          addon-after="ö"
                          style="width: 100%"
                        />
                      </a-form-item>
                    </a-col>
                    <a-col :span="12">
                      <a-form-item label="Ólåö
P">
                        <a-input-number
                          v-model:value="attendanceRules.carryoverHoursLimit"
                          :min="0"
                          :max="100"
                          :step="5"
                          addon-after="ö"
                          style="width: 100%"
                        />
                      </a-form-item>
                    </a-col>
                  </a-row>
                </div>

                <div class="setting-group">
                  <h4>¡8¾n</h4>
                  <a-row :gutter="16">
                    <a-col :span="12">
                      <a-form-item>
                        <a-checkbox v-model:checked="attendanceRules.autoApproveOnlineTask">
                          ¿
û¡ê¨Ç
                        </a-checkbox>
                      </a-form-item>
                    </a-col>
                    <a-col :span="12">
                      <a-form-item>
                        <a-checkbox v-model:checked="attendanceRules.requireOfflineTaskReview">
                          ¿û¡:6¡8
                        </a-checkbox>
                      </a-form-item>
                    </a-col>
                  </a-row>
                  
                  <a-form-item label="O©û¡¡8P">
                    <a-input-number
                      v-model:value="attendanceRules.assistanceTaskReviewDays"
                      :min="1"
                      :max="30"
                      :step="1"
                      addon-after=")"
                      style="width: 200px"
                    />
                  </a-form-item>
                </div>
              </a-form>
            </div>

            <!-- ûßå¾n -->
            <div class="setting-panel">
              <div class="panel-header">
                <h3>ûßå¾n</h3>
                <p>MnÍûßåŒÐ’</p>
              </div>

              <a-form layout="vertical">
                <div class="setting-group">
                  <h4>û¡å</h4>
                  <a-space direction="vertical" style="width: 100%;">
                    <a-checkbox v-model:checked="notificationSettings.newTaskNotification">
                      °û¡Må
                    </a-checkbox>
                    <a-checkbox v-model:checked="notificationSettings.taskOverdueNotification">
                      û¡…öÐ’
                    </a-checkbox>
                    <a-checkbox v-model:checked="notificationSettings.taskCompletionNotification">
                      û¡Œå
                    </a-checkbox>
                  </a-space>
                </div>

                <div class="setting-group">
                  <h4>¡8å</h4>
                  <a-space direction="vertical" style="width: 100%;">
                    <a-checkbox v-model:checked="notificationSettings.pendingReviewNotification">
                      …¡8û¡Ð’
                    </a-checkbox>
                    <a-checkbox v-model:checked="notificationSettings.reviewResultNotification">
                      ¡8Óœå
                    </a-checkbox>
                  </a-space>
                </div>

                <div class="setting-group">
                  <h4>pnüúå</h4>
                  <a-space direction="vertical" style="width: 100%;">
                    <a-checkbox v-model:checked="notificationSettings.exportCompleteNotification">
                      pnüúŒå
                    </a-checkbox>
                    <a-checkbox v-model:checked="notificationSettings.monthlyReportNotification">
                      ¦¥hÐ’
                    </a-checkbox>
                  </a-space>
                </div>
              </a-form>
            </div>
          </div>
        </a-col>

        <!-- §¹ -->
        <a-col :xs="24" :lg="8">
          <div class="settings-sidebar">
            <!-- SM¾n„È -->
            <a-card title="¾n„È" size="small" style="margin-bottom: 16px;">
              <div class="settings-preview">
                <div class="preview-item">
                  <span class="preview-label">¿
û¡åö:</span>
                  <span class="preview-value">{{ workHourRules.onlineTaskMinutes }}Ÿ</span>
                </div>
                <div class="preview-item">
                  <span class="preview-label">¿û¡åö:</span>
                  <span class="preview-value">{{ workHourRules.offlineTaskMinutes }}Ÿ</span>
                </div>
                <div class="preview-item">
                  <span class="preview-label">}ÄV±:</span>
                  <span class="preview-value">+{{ workHourRules.positiveReviewBonus }}Ÿ</span>
                </div>
                <div class="preview-item">
                  <span class="preview-label">…öcö:</span>
                  <span class="preview-value">-{{ workHourRules.lateResponsePenalty }}Ÿ</span>
                </div>
              </div>
            </a-card>

            <!-- Í\†ò -->
            <a-card title=" Ñî9" size="small" style="margin-bottom: 16px;">
              <div class="history-list">
                <div v-for="item in modifyHistory" :key="item.id" class="history-item">
                  <div class="history-desc">{{ item.description }}</div>
                  <div class="history-time">{{ formatDateTime(item.updatedAt) }}</div>
                  <div class="history-user">{{ item.updatedBy }}</div>
                </div>
              </div>
            </a-card>

            <!-- Ín	y -->
            <a-card title="Ín	y" size="small">
              <a-space direction="vertical" style="width: 100%;">
                <a-button block @click="resetToDefault">
                  bØ¤¾n
                </a-button>
                <a-button block type="primary" ghost @click="exportSettings">
                  üú¾n
                </a-button>
                <a-button block @click="importSettings">
                  üe¾n
                </a-button>
              </a-space>
            </a-card>
          </div>
        </a-col>
      </a-row>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { message } from 'ant-design-vue'
import { api } from '@/api/client'

// Í”pn
const saveLoading = ref(false)

// åöÄ¾n
const workHourRules = reactive({
  onlineTaskMinutes: 40,
  offlineTaskMinutes: 100,
  rushOrderBonus: 15,
  positiveReviewBonus: 30,
  assistanceMultiplier: 1.0,
  lateResponsePenalty: 30,
  lateCompletionPenalty: 30,
  negativeReviewPenalty: 60,
  responseTimeLimit: 24,
  completionTimeLimit: 48
})

// äÄ¾n
const attendanceRules = reactive({
  standardMonthlyHours: 30,
  carryoverHoursLimit: 50,
  autoApproveOnlineTask: true,
  requireOfflineTaskReview: true,
  assistanceTaskReviewDays: 7
})

// å¾n
const notificationSettings = reactive({
  newTaskNotification: true,
  taskOverdueNotification: true,
  taskCompletionNotification: false,
  pendingReviewNotification: true,
  reviewResultNotification: true,
  exportCompleteNotification: true,
  monthlyReportNotification: true
})

// î9†ò
const modifyHistory = ref<any[]>([
  {
    id: 1,
    description: 'î9¿
û¡åö:40Ÿ',
    updatedAt: '2024-01-20 10:30:00',
    updatedBy: '…§¡X'
  },
  {
    id: 2,
    description: 't}ÄV±:30Ÿ',
    updatedAt: '2024-01-15 14:20:00',
    updatedBy: '…§¡X'
  }
])

// ¹Õ
const fetchSettings = async () => {
  try {
    const response = await api.getSystemSettings()
    if (response.success && response.data) {
      Object.assign(workHourRules, response.data.workHourRules)
      Object.assign(attendanceRules, response.data.attendanceRules)
      Object.assign(notificationSettings, response.data.notificationSettings)
    }
  } catch (error) {
    console.error('·Öûß¾n1%:', error)
  }
}

const saveAllSettings = async () => {
  try {
    saveLoading.value = true
    
    const settingsData = {
      workHourRules: { ...workHourRules },
      attendanceRules: { ...attendanceRules },
      notificationSettings: { ...notificationSettings }
    }
    
    const response = await api.updateSystemSettings(settingsData)
    
    if (response.success) {
      message.success('ûß¾nÝXŸ')
      // 7°î9†ò
      fetchModifyHistory()
    } else {
      throw new Error(response.message || 'ÝX1%')
    }
  } catch (error: any) {
    console.error('ÝXûß¾n1%:', error)
    const errorMessage = error.response?.data?.message || error.message || 'ÝX1%÷ÍÕ'
    message.error(errorMessage)
  } finally {
    saveLoading.value = false
  }
}

const resetToDefault = () => {
  // bØ¤¾n
  Object.assign(workHourRules, {
    onlineTaskMinutes: 40,
    offlineTaskMinutes: 100,
    rushOrderBonus: 15,
    positiveReviewBonus: 30,
    assistanceMultiplier: 1.0,
    lateResponsePenalty: 30,
    lateCompletionPenalty: 30,
    negativeReviewPenalty: 60,
    responseTimeLimit: 24,
    completionTimeLimit: 48
  })
  
  Object.assign(attendanceRules, {
    standardMonthlyHours: 30,
    carryoverHoursLimit: 50,
    autoApproveOnlineTask: true,
    requireOfflineTaskReview: true,
    assistanceTaskReviewDays: 7
  })
  
  Object.assign(notificationSettings, {
    newTaskNotification: true,
    taskOverdueNotification: true,
    taskCompletionNotification: false,
    pendingReviewNotification: true,
    reviewResultNotification: true,
    exportCompleteNotification: true,
    monthlyReportNotification: true
  })
  
  message.success('òbØ¤¾n')
}

const exportSettings = () => {
  const settingsData = {
    workHourRules,
    attendanceRules,
    notificationSettings,
    exportTime: new Date().toISOString()
  }
  
  const dataStr = JSON.stringify(settingsData, null, 2)
  const dataBlob = new Blob([dataStr], { type: 'application/json' })
  
  const url = URL.createObjectURL(dataBlob)
  const link = document.createElement('a')
  link.href = url
  link.download = `system-settings-${new Date().toISOString().split('T')[0]}.json`
  link.click()
  
  URL.revokeObjectURL(url)
  message.success('¾nüúŸ')
}

const importSettings = () => {
  const input = document.createElement('input')
  input.type = 'file'
  input.accept = '.json'
  
  input.onchange = (e: any) => {
    const file = e.target.files[0]
    if (!file) return
    
    const reader = new FileReader()
    reader.onload = (event: any) => {
      try {
        const settingsData = JSON.parse(event.target.result)
        
        if (settingsData.workHourRules) {
          Object.assign(workHourRules, settingsData.workHourRules)
        }
        if (settingsData.attendanceRules) {
          Object.assign(attendanceRules, settingsData.attendanceRules)
        }
        if (settingsData.notificationSettings) {
          Object.assign(notificationSettings, settingsData.notificationSettings)
        }
        
        message.success('¾nüeŸ')
      } catch (error) {
        message.error('¾n‡ö<ï')
      }
    }
    
    reader.readAsText(file)
  }
  
  input.click()
}

const fetchModifyHistory = async () => {
  try {
    const response = await api.getSettingsModifyHistory()
    if (response.success && response.data) {
      modifyHistory.value = response.data
    }
  } catch (error) {
    console.error('·Öî9†ò1%:', error)
  }
}

const formatDateTime = (dateStr: string) => {
  return new Date(dateStr).toLocaleString('zh-CN')
}

// }h
onMounted(() => {
  fetchSettings()
  fetchModifyHistory()
})
</script>

<style scoped>
.desktop-settings {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.page-header {
  background: white;
  border-radius: 12px;
  padding: 32px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.04);
  border: 1px solid #e8e9ea;
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-text h1 {
  margin: 0 0 8px;
  font-size: 28px;
  font-weight: 600;
  color: #1a1a1a;
}

.header-text p {
  margin: 0;
  font-size: 16px;
  color: #666666;
}

.settings-content {
  flex: 1;
  overflow: auto;
}

.settings-panels {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.setting-panel {
  background: white;
  border-radius: 12px;
  padding: 32px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.04);
  border: 1px solid #e8e9ea;
}

.panel-header {
  margin-bottom: 32px;
  padding-bottom: 16px;
  border-bottom: 1px solid #e8e9ea;
}

.panel-header h3 {
  margin: 0 0 8px;
  font-size: 20px;
  font-weight: 600;
  color: #1a1a1a;
}

.panel-header p {
  margin: 0;
  color: #666666;
}

.setting-group {
  margin-bottom: 32px;
  padding: 20px;
  background: #fafbfc;
  border-radius: 8px;
  border: 1px solid #e8e9ea;
}

.setting-group h4 {
  margin: 0 0 20px;
  font-size: 16px;
  font-weight: 500;
  color: #1a1a1a;
  padding-bottom: 8px;
  border-bottom: 1px solid #e0e0e0;
}

.settings-sidebar {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.settings-preview {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.preview-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 12px;
  background: #f8f9fa;
  border-radius: 6px;
}

.preview-label {
  font-size: 13px;
  color: #666666;
}

.preview-value {
  font-size: 13px;
  font-weight: 500;
  color: #1a1a1a;
}

.history-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
  max-height: 200px;
  overflow-y: auto;
}

.history-item {
  padding: 12px;
  background: #f8f9fa;
  border-radius: 6px;
  border-left: 3px solid #667eea;
}

.history-desc {
  font-size: 13px;
  font-weight: 500;
  color: #1a1a1a;
  margin-bottom: 4px;
}

.history-time {
  font-size: 12px;
  color: #8c8c8c;
  margin-bottom: 2px;
}

.history-user {
  font-size: 12px;
  color: #666666;
}

/* hU7 */
:deep(.ant-form-item-label) {
  font-weight: 500;
}

:deep(.ant-input-number) {
  border-radius: 8px;
}

:deep(.ant-checkbox-wrapper) {
  padding: 8px 12px;
  border-radius: 6px;
  transition: all 0.3s ease;
}

:deep(.ant-checkbox-wrapper:hover) {
  background: #f0f2ff;
}

:deep(.ant-btn) {
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

:deep(.ant-card) {
  border-radius: 8px;
}

:deep(.ant-card-head-title) {
  font-weight: 600;
}

/* Í” */
@media (max-width: 1200px) {
  .header-content {
    flex-direction: column;
    gap: 20px;
    text-align: center;
  }
  
  .settings-content .ant-col {
    margin-bottom: 24px;
  }
}

@media (max-width: 768px) {
  .page-header,
  .setting-panel {
    padding: 20px;
  }
  
  .panel-header {
    margin-bottom: 24px;
  }
  
  .setting-group {
    margin-bottom: 24px;
    padding: 16px;
  }
  
  .preview-item {
    flex-direction: column;
    align-items: flex-start;
    gap: 4px;
  }
}
</style>