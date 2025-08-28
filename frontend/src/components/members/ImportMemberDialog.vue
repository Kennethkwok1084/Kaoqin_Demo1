<template>
  <el-dialog
    v-model="visible"
    title="批量导入成员"
    width="800px"
    :before-close="handleClose"
    destroy-on-close
  >
    <div class="import-container">
      <!-- 步骤指示器 -->
      <el-steps :active="currentStep" finish-status="success" align-center>
        <el-step title="上传文件" />
        <el-step title="数据预览" />
        <el-step title="导入结果" />
      </el-steps>

      <!-- 第一步：上传文件 -->
      <div v-if="currentStep === 0" class="step-content">
        <div class="upload-section">
          <el-upload
            ref="uploadRef"
            :auto-upload="false"
            :show-file-list="true"
            :on-change="handleFileChange"
            :before-upload="beforeUpload"
            :limit="1"
            accept=".xlsx,.xls"
            drag
          >
            <el-icon class="el-icon--upload"><UploadFilled /></el-icon>
            <div class="el-upload__text">
              将Excel文件拖拽到此处，或<em>点击上传</em>
            </div>
            <template #tip>
              <div class="el-upload__tip">
                仅支持 .xlsx 和 .xls 格式文件，文件大小不超过 10MB
              </div>
            </template>
          </el-upload>
        </div>

        <div class="template-section">
          <el-card>
            <template #header>
              <div class="card-header">
                <span>Excel 模板格式说明</span>
                <el-button type="primary" link @click="downloadTemplate">
                  下载模板
                </el-button>
              </div>
            </template>
            <div class="template-info">
              <p><strong>必填字段：</strong></p>
              <ul>
                <li><code>姓名</code> - 真实姓名（可包含中文和·）</li>
                <li><code>班级</code> - 班级名称</li>
              </ul>

              <p><strong>可选字段：</strong></p>
              <ul>
                <li><code>用户名</code> - 登录用户名（留空则自动生成）</li>
                <li><code>学号</code> - 员工号/学号（纯数字）</li>
                <li><code>手机号</code> - 11位手机号</li>
                <li>
                  <code>角色</code> -
                  admin/group_leader/member/guest（默认：member）
                </li>
                <li><code>部门</code> - 部门名称（默认：信息化建设处）</li>
              </ul>
            </div>
          </el-card>
        </div>
      </div>

      <!-- 第二步：数据预览 -->
      <div v-if="currentStep === 1" class="step-content">
        <div class="preview-header">
          <div class="preview-stats">
            <el-tag type="info">总计 {{ previewData.length }} 条记录</el-tag>
            <el-tag type="success">有效 {{ validCount }} 条</el-tag>
            <el-tag type="warning" v-if="invalidCount > 0"
              >无效 {{ invalidCount }} 条</el-tag
            >
          </div>
          <div class="preview-actions">
            <el-checkbox v-model="skipDuplicates">跳过重复数据</el-checkbox>
          </div>
        </div>

        <el-table
          :data="previewData"
          style="width: 100%"
          max-height="400px"
          stripe
        >
          <el-table-column type="index" label="#" width="50" />
          <el-table-column prop="name" label="姓名" width="100" />
          <el-table-column prop="student_id" label="学号" width="120" />
          <el-table-column prop="username" label="用户名" width="120">
            <template #default="{ row }">
              <span v-if="row.username">{{ row.username }}</span>
              <el-tag v-else type="info" size="small">自动生成</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="phone" label="手机号" width="120" />
          <el-table-column prop="class_name" label="班级" width="150" />
          <el-table-column prop="role" label="角色" width="100">
            <template #default="{ row }">
              {{ getRoleLabel(row.role || 'member') }}
            </template>
          </el-table-column>
          <el-table-column prop="department" label="部门" width="120">
            <template #default="{ row }">
              {{ row.department || '信息化建设处' }}
            </template>
          </el-table-column>
          <el-table-column label="状态" width="80">
            <template #default="{ row }">
              <el-tag v-if="row._valid" type="success" size="small"
                >有效</el-tag
              >
              <el-tag v-else type="danger" size="small">无效</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="_errors" label="错误信息" min-width="200">
            <template #default="{ row }">
              <div
                v-if="row._errors && row._errors.length > 0"
                class="error-list"
              >
                <el-tag
                  v-for="error in row._errors"
                  :key="error"
                  type="danger"
                  size="small"
                  class="error-tag"
                >
                  {{ error }}
                </el-tag>
              </div>
            </template>
          </el-table-column>
        </el-table>
      </div>

      <!-- 第三步：导入结果 -->
      <div v-if="currentStep === 2" class="step-content">
        <div class="result-summary">
          <el-result
            :icon="importResult.successful_imports > 0 ? 'success' : 'warning'"
            :title="
              importResult.successful_imports > 0 ? '导入完成' : '导入失败'
            "
            :sub-title="`处理 ${importResult.total_processed} 条记录，成功 ${importResult.successful_imports} 条，失败 ${importResult.failed_imports} 条`"
          />
        </div>

        <div
          v-if="importResult.errors && importResult.errors.length > 0"
          class="error-details"
        >
          <el-card>
            <template #header>
              <span>错误详情</span>
            </template>
            <div class="error-list">
              <div
                v-for="(error, index) in importResult.errors"
                :key="index"
                class="error-item"
              >
                <el-tag type="danger" size="small">{{ error }}</el-tag>
              </div>
            </div>
          </el-card>
        </div>
      </div>
    </div>

    <template #footer>
      <div class="dialog-footer">
        <el-button @click="handleClose">
          {{ currentStep === 2 ? '关闭' : '取消' }}
        </el-button>

        <el-button
          v-if="currentStep > 0 && currentStep < 2"
          @click="handlePrevStep"
        >
          上一步
        </el-button>

        <el-button
          v-if="currentStep === 0"
          type="primary"
          :disabled="!selectedFile"
          @click="handleNextStep"
        >
          下一步
        </el-button>

        <el-button
          v-if="currentStep === 1"
          type="primary"
          :loading="importing"
          :disabled="validCount === 0"
          @click="handleImport"
        >
          开始导入
        </el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, reactive, computed, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { UploadFilled } from '@element-plus/icons-vue'
import type { UploadInstance, UploadFile } from 'element-plus'
import { MembersApi } from '@/api/members'
import type {
  MemberImportItem,
  MemberImportRequest,
  MemberImportResponse
} from '@/api/members'
import * as XLSX from 'xlsx'

// Props
interface Props {
  visible: boolean
}

// Emits
interface Emits {
  (e: 'update:visible', visible: boolean): void
  (e: 'success'): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

// Refs
const uploadRef = ref<UploadInstance>()
const currentStep = ref(0)
const importing = ref(false)
const selectedFile = ref<File | null>(null)
const skipDuplicates = ref(true)

// Data
const previewData = ref<
  Array<MemberImportItem & { _valid: boolean; _errors: string[] }>
>([])
const importResult = reactive<MemberImportResponse>({
  total_processed: 0,
  successful_imports: 0,
  failed_imports: 0,
  skipped_duplicates: 0,
  errors: []
})

// Computed
const visible = computed({
  get: () => props.visible,
  set: value => emit('update:visible', value)
})

const validCount = computed(
  () => previewData.value.filter(item => item._valid).length
)
const invalidCount = computed(
  () => previewData.value.filter(item => !item._valid).length
)

// Methods
const handleClose = () => {
  emit('update:visible', false)
  resetData()
}

const resetData = () => {
  currentStep.value = 0
  selectedFile.value = null
  previewData.value = []
  skipDuplicates.value = true
  importing.value = false
  Object.assign(importResult, {
    total_processed: 0,
    successful_imports: 0,
    failed_imports: 0,
    skipped_duplicates: 0,
    errors: []
  })
  uploadRef.value?.clearFiles()
}

const handleFileChange = (file: UploadFile) => {
  selectedFile.value = file.raw || null
}

const beforeUpload = (file: File) => {
  const isExcel = /\.(xlsx|xls)$/i.test(file.name)
  const isLt10M = file.size / 1024 / 1024 < 10

  if (!isExcel) {
    ElMessage.error('只能上传 Excel 文件')
    return false
  }
  if (!isLt10M) {
    ElMessage.error('文件大小不能超过 10MB')
    return false
  }
  return false // 阻止自动上传
}

const handleNextStep = async () => {
  if (!selectedFile.value) {
    ElMessage.warning('请先选择文件')
    return
  }

  try {
    await parseExcelFile(selectedFile.value)
    currentStep.value = 1
  } catch (error) {
    console.error('解析文件失败:', error)
    ElMessage.error('文件解析失败，请检查文件格式')
  }
}

const handlePrevStep = () => {
  currentStep.value = Math.max(0, currentStep.value - 1)
}

const parseExcelFile = async (file: File) => {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = e => {
      try {
        const data = new Uint8Array(e.target?.result as ArrayBuffer)
        const workbook = XLSX.read(data, { type: 'array' })
        const worksheet = workbook.Sheets[workbook.SheetNames[0]]
        const jsonData = XLSX.utils.sheet_to_json(worksheet, { header: 1 })

        if (jsonData.length < 2) {
          reject(new Error('文件内容为空或格式不正确'))
          return
        }

        const headers = jsonData[0] as string[]
        const rows = jsonData.slice(1) as string[][]

        // 字段映射
        const fieldMap: Record<string, string> = {
          姓名: 'name',
          用户名: 'username',
          学号: 'student_id',
          员工号: 'student_id',
          手机号: 'phone',
          电话: 'phone',
          角色: 'role',
          部门: 'department',
          班级: 'class_name'
        }

        const parsedData = rows
          // eslint-disable-next-line @typescript-eslint/no-unused-vars
          .map((row, _index) => {
            const item: any = { _valid: true, _errors: [] }

            headers.forEach((header, colIndex) => {
              const field = fieldMap[header]
              if (
                field &&
                row[colIndex] !== undefined &&
                row[colIndex] !== null &&
                row[colIndex] !== ''
              ) {
                let value = String(row[colIndex]).trim()
                // 数据清理和标准化
                if (field === 'student_id') {
                  // 移除非数字字符
                  value = value.replace(/\D/g, '')
                  if (value) {
                    item[field] = value
                  }
                } else if (field === 'phone') {
                  // 移除空格和特殊字符，保留数字
                  value = value.replace(/[^\d]/g, '')
                  if (value && value.length === 11) {
                    item[field] = value
                  }
                } else if (field === 'role') {
                  // 角色标准化
                  const roleMap: Record<string, string> = {
                    管理员: 'admin',
                    组长: 'group_leader',
                    成员: 'member',
                    访客: 'guest'
                  }
                  item[field] = roleMap[value] || value.toLowerCase()
                } else {
                  item[field] = value
                }
              }
            })

            // 增强数据验证
            const errors: string[] = []

            // 必填字段验证
            if (!item.name || item.name.trim() === '') {
              errors.push('姓名不能为空')
            } else {
              // 姓名格式验证（允许中文、字母、·、空格）
              if (!/^[\u4e00-\u9fa5a-zA-Z·\s]+$/.test(item.name)) {
                errors.push('姓名格式不正确，只能包含中文、字母、·和空格')
              }
              // 去除多余空格
              item.name = item.name.replace(/\s+/g, ' ').trim()
            }

            if (!item.class_name || item.class_name.trim() === '') {
              errors.push('班级不能为空')
            } else {
              item.class_name = item.class_name.trim()
            }

            // 可选字段验证
            if (item.student_id) {
              if (!/^\d+$/.test(item.student_id)) {
                errors.push('学号必须为纯数字')
              } else if (item.student_id.length > 20) {
                errors.push('学号长度不能超过20位')
              }
            }

            if (item.phone) {
              if (!/^1[3-9]\d{9}$/.test(item.phone)) {
                errors.push('手机号格式不正确，必须是11位有效手机号')
              }
            }

            if (item.username) {
              if (!/^[a-zA-Z0-9_]+$/.test(item.username)) {
                errors.push('用户名只能包含字母、数字和下划线')
              } else if (
                item.username.length < 3 ||
                item.username.length > 50
              ) {
                errors.push('用户名长度必须在3-50个字符之间')
              }
            }

            if (item.role) {
              if (
                !['admin', 'group_leader', 'member', 'guest'].includes(
                  item.role
                )
              ) {
                errors.push(
                  '角色值不正确，必须是：admin、group_leader、member、guest'
                )
              }
            }

            if (item.department) {
              item.department = item.department.trim()
              if (item.department.length > 100) {
                errors.push('部门名称不能超过100个字符')
              }
            }

            item._valid = errors.length === 0
            item._errors = errors

            return item
          })
          .filter(item => {
            // 过滤完全空行
            return item.name && item.name.trim() !== ''
          })

        previewData.value = parsedData
        resolve(parsedData)
      } catch (error) {
        console.error('Excel解析错误:', error)
        reject(
          new Error(
            `文件解析失败: ${error instanceof Error ? error.message : '未知错误'}`
          )
        )
      }
    }
    reader.onerror = () => reject(new Error('文件读取失败'))
    reader.readAsArrayBuffer(file)
  })
}

const handleImport = async () => {
  if (validCount.value === 0) {
    ElMessage.warning('没有有效的数据记录')
    return
  }

  try {
    importing.value = true

    // 数据最终清理和验证
    const validMembers = previewData.value
      .filter(item => item._valid)
      .map(item => {
        // 确保所有字段都存在，即使是null
        const member: MemberImportItem = {
          name: item.name.trim(),
          class_name: item.class_name.trim(),
          student_id: undefined, // 显式设置为undefined
          phone: undefined, // 显式设置为undefined
          username: undefined, // 显式设置为undefined
          role: 'member', // 默认角色
          department: '信息化建设处' // 默认部门
        }

        // 只有在有效值的情况下才赋值
        if (item.username && item.username.trim() !== '') {
          member.username = item.username.trim()
        }

        if (item.student_id && item.student_id.trim() !== '') {
          member.student_id = item.student_id.trim()
        }

        if (item.phone && item.phone.trim() !== '') {
          // 手机号清理和验证
          const phoneClean = item.phone.trim().replace(/\D/g, '')
          if (phoneClean.length === 11 && /^1[3-9]\d{9}$/.test(phoneClean)) {
            member.phone = phoneClean
          }
          // 如果手机号格式不正确，保持为null
        }

        if (item.role && item.role.trim() !== '') {
          const validRoles = ['admin', 'group_leader', 'member', 'guest']
          const role = item.role.trim().toLowerCase()
          member.role = validRoles.includes(role) ? role : 'member'
        }

        if (item.department && item.department.trim() !== '') {
          member.department = item.department.trim()
        }

        return member
      })

    console.log('准备导入的数据:', validMembers)

    const requestData: MemberImportRequest = {
      members: validMembers,
      skip_duplicates: skipDuplicates.value
    }

    console.log('发送的请求数据:', requestData)

    const result = await MembersApi.importMembers(requestData)

    console.log('导入结果:', result)

    Object.assign(importResult, result)
    currentStep.value = 2

    if (result.successful_imports > 0) {
      ElMessage.success(`成功导入 ${result.successful_imports} 条记录`)
      emit('success')
    } else {
      ElMessage.warning('没有成功导入任何记录')
    }
  } catch (error: any) {
    console.error('导入失败:', error)
    console.error('错误响应:', error.response?.data)

    let errorMessage = '导入失败，请重试'

    if (error.response) {
      const status = error.response.status
      const data = (error.response as any)?.data || {}

      console.log('详细错误信息:', JSON.stringify(data, null, 2))

      if (status === 422) {
        if ((data as any)?.detail) {
          if (Array.isArray((data as any).detail)) {
            // Pydantic 验证错误
            const validationErrors =
              (data as any).detail ||
              []
                .map((err: any) => {
                  const field = err.loc ? err.loc.join('.') : 'unknown'
                  const input = err.input
                    ? ` (输入值: ${JSON.stringify(err.input)})`
                    : ''
                  return `${field}: ${err.msg}${input}`
                })
                .join('\n')
            errorMessage = `数据验证失败:\n${validationErrors}`

            // 使用消息框显示详细错误
            ElMessageBox.alert(validationErrors, '数据验证错误', {
              type: 'error',
              dangerouslyUseHTMLString: false
            })
            return
          } else {
            errorMessage = `数据验证失败: ${(data as any).detail || ''}`
          }
        } else {
          errorMessage = '数据格式不正确，请检查Excel文件格式'
        }
      } else if (status === 500) {
        errorMessage = '服务器内部错误，请联系管理员'
      } else {
        errorMessage =
          (data as any)?.message ||
          (data as any)?.detail ||
          `请求失败 (${status})`
      }
    } else if (error.message) {
      errorMessage = error.message
    }

    ElMessage.error(errorMessage)
  } finally {
    importing.value = false
  }
}

const downloadTemplate = () => {
  // 创建模板数据
  const templateData = [
    ['姓名', '班级', '学号', '用户名', '手机号', '角色', '部门'],
    [
      '张三',
      '计算机科学与技术2101',
      '20210001',
      'zhangsan',
      '13800138001',
      'member',
      '信息化建设处'
    ],
    [
      '李四',
      '网络工程2101',
      '20210002',
      'lisi',
      '13800138002',
      'member',
      '信息化建设处'
    ]
  ]

  const ws = XLSX.utils.aoa_to_sheet(templateData)
  const wb = XLSX.utils.book_new()
  XLSX.utils.book_append_sheet(wb, ws, '成员导入模板')

  XLSX.writeFile(wb, '成员导入模板.xlsx')
  ElMessage.success('模板下载成功')
}

const getRoleLabel = (role: string) => {
  const roleMap: Record<string, string> = {
    admin: '管理员',
    group_leader: '组长',
    member: '成员',
    guest: '访客'
  }
  return roleMap[role] || '成员'
}

// Watch for visibility changes to reset data
watch(
  () => props.visible,
  newVal => {
    if (newVal) {
      resetData()
    }
  }
)
</script>

<style scoped>
.import-container {
  padding: 20px 0;
}

.step-content {
  margin-top: 30px;
  min-height: 400px;
}

.upload-section {
  margin-bottom: 20px;
}

.template-section {
  margin-top: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.template-info ul {
  margin: 10px 0;
  padding-left: 20px;
}

.template-info li {
  margin: 5px 0;
}

.template-info code {
  background: #f5f5f5;
  padding: 2px 4px;
  border-radius: 2px;
  font-family: monospace;
}

.preview-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
}

.preview-stats .el-tag {
  margin-right: 10px;
}

.error-list {
  display: flex;
  flex-wrap: wrap;
  gap: 5px;
}

.error-tag {
  margin: 2px 0;
}

.result-summary {
  margin-bottom: 20px;
}

.error-details {
  margin-top: 20px;
}

.error-item {
  margin-bottom: 8px;
}

.dialog-footer {
  text-align: right;
}

:deep(.el-upload-dragger) {
  width: 100%;
}

:deep(.el-steps) {
  margin-bottom: 20px;
}
</style>
