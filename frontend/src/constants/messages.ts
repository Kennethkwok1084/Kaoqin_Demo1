/**
 * 前端统一消息管理
 * 与后端消息系统保持一致，确保用户体验统一
 */

// 消息类型枚举
export enum MessageType {
  SUCCESS = 'success',
  ERROR = 'error',
  WARNING = 'warning',
  INFO = 'info'
}

// 消息分类枚举
export enum MessageCategory {
  AUTH = 'auth', // 认证相关
  MEMBER = 'member', // 成员管理
  TASK = 'task', // 任务管理
  ATTENDANCE = 'attendance', // 考勤管理
  IMPORT = 'import', // 数据导入
  SYSTEM = 'system', // 系统消息
  VALIDATION = 'validation' // 数据验证
}

// 统一消息定义
export const MESSAGES = {
  // ========== 认证相关消息 ==========
  AUTH_SUCCESS_LOGIN: '登录成功',
  AUTH_SUCCESS_LOGOUT: '退出登录成功',
  AUTH_SUCCESS_REFRESH_TOKEN: '令牌刷新成功',
  AUTH_SUCCESS_PROFILE_UPDATE: '个人信息更新成功',
  AUTH_SUCCESS_PASSWORD_CHANGE: '密码修改成功',
  AUTH_SUCCESS_PROFILE_RETRIEVE: '个人信息获取成功',

  AUTH_ERROR_INVALID_CREDENTIALS: '用户名或密码错误',
  AUTH_ERROR_ACCOUNT_DISABLED: '账户已被禁用，请联系管理员',
  AUTH_ERROR_INVALID_TOKEN: '无效的访问令牌',
  AUTH_ERROR_EXPIRED_TOKEN: '访问令牌已过期',
  AUTH_ERROR_TOKEN_REFRESH_FAILED: '令牌刷新失败',
  AUTH_ERROR_LOGIN_FAILED: '登录失败，请稍后重试',
  AUTH_ERROR_LOGOUT_FAILED: '退出登录失败',
  AUTH_ERROR_PROFILE_UPDATE_FAILED: '个人信息更新失败',
  AUTH_ERROR_PASSWORD_CHANGE_FAILED: '密码修改失败',
  AUTH_ERROR_PROFILE_RETRIEVE_FAILED: '个人信息获取失败',
  AUTH_ERROR_CURRENT_PASSWORD_INCORRECT: '当前密码错误',
  AUTH_ERROR_NEW_PASSWORD_SAME: '新密码不能与当前密码相同',
  AUTH_ERROR_INVALID_EMAIL_FORMAT: '邮箱格式不正确',
  AUTH_ERROR_USER_NOT_FOUND: '用户不存在或已停用',
  AUTH_ERROR_INVALID_TOKEN_PAYLOAD: '令牌数据无效',
  AUTH_ERROR_TOKEN_VERIFICATION_FAILED: '令牌验证失败',
  AUTH_ERROR_CREDENTIALS_VALIDATION: '身份验证失败',
  AUTH_ERROR_INACTIVE_USER: '用户账户未激活',
  AUTH_ERROR_ADMIN_REQUIRED: '需要管理员权限',
  AUTH_ERROR_GROUP_LEADER_REQUIRED: '需要组长或管理员权限',

  AUTH_WARNING_PASSWORD_WEAK:
    '密码强度不足，建议包含大小写字母、数字和特殊字符',

  AUTH_INFO_TOKEN_VALID: '访问令牌有效',
  AUTH_INFO_SERVICE_RUNNING: '认证服务运行正常',

  // ========== 成员管理相关消息 ==========
  MEMBER_SUCCESS_LIST_RETRIEVE: '成功获取成员列表，共 {total} 条记录',
  MEMBER_SUCCESS_DETAIL_RETRIEVE: '成功获取成员信息',
  MEMBER_SUCCESS_CREATE: '成功创建成员：{name} ({student_id})',
  MEMBER_SUCCESS_UPDATE: '成员信息更新成功',
  MEMBER_SUCCESS_DELETE: '成功删除成员：{name}',
  MEMBER_SUCCESS_PASSWORD_CHANGE: '密码修改成功',
  MEMBER_SUCCESS_PROFILE_COMPLETE: '个人信息完善成功',
  MEMBER_SUCCESS_STATS_RETRIEVE: '成员统计信息获取成功',
  MEMBER_SUCCESS_IMPORT:
    '导入完成：成功 {successful} 条，失败 {failed} 条，跳过 {skipped} 条',

  MEMBER_ERROR_LIST_RETRIEVE: '获取成员列表失败',
  MEMBER_ERROR_DETAIL_RETRIEVE: '获取成员详情失败',
  MEMBER_ERROR_NOT_FOUND: '成员不存在',
  MEMBER_ERROR_NO_PERMISSION_VIEW: '无权限查看该成员信息',
  MEMBER_ERROR_NO_PERMISSION_UPDATE: '无权限更新该成员信息',
  MEMBER_ERROR_NO_PERMISSION_DELETE: '无权限删除该成员',
  MEMBER_ERROR_NO_PERMISSION_PASSWORD: '无权限修改该成员密码',
  MEMBER_ERROR_USERNAME_EXISTS: '用户名 {username} 已存在',
  MEMBER_ERROR_STUDENT_ID_EXISTS: '学号 {student_id} 已存在',
  MEMBER_ERROR_CREATE_FAILED: '创建成员失败',
  MEMBER_ERROR_UPDATE_FAILED: '更新成员信息失败',
  MEMBER_ERROR_DELETE_FAILED: '删除成员失败',
  MEMBER_ERROR_DELETE_SELF: '不能删除自己的账户',
  MEMBER_ERROR_PASSWORD_CHANGE_FAILED: '修改密码失败',
  MEMBER_ERROR_OLD_PASSWORD_INCORRECT: '旧密码错误',
  MEMBER_ERROR_PROFILE_COMPLETE_FAILED: '完善信息失败',
  MEMBER_ERROR_STATS_RETRIEVE_FAILED: '获取成员统计失败',
  MEMBER_ERROR_IMPORT_FAILED: '批量导入失败',
  MEMBER_ERROR_IMPORT_COMMIT_FAILED: '批量导入提交失败',
  MEMBER_ERROR_NO_PERMISSION_PROFILE: '无权限完善此用户信息',

  MEMBER_INFO_MODULE_RUNNING: '成员管理模块运行正常',

  // ========== 任务管理相关消息 ==========
  TASK_SUCCESS_LIST_RETRIEVE: '成功获取任务列表',
  TASK_SUCCESS_DETAIL_RETRIEVE: '成功获取任务详情',
  TASK_SUCCESS_CREATE: '任务创建成功',
  TASK_SUCCESS_UPDATE: '任务更新成功',
  TASK_SUCCESS_DELETE: '任务删除成功',
  TASK_SUCCESS_STATUS_UPDATE: '任务状态更新成功',
  TASK_SUCCESS_IMPORT: '任务批量导入成功',

  TASK_ERROR_LIST_RETRIEVE: '获取任务列表失败',
  TASK_ERROR_DETAIL_RETRIEVE: '获取任务详情失败',
  TASK_ERROR_NOT_FOUND: '任务不存在',
  TASK_ERROR_NO_PERMISSION: '无权限访问该任务',
  TASK_ERROR_CREATE_FAILED: '任务创建失败',
  TASK_ERROR_UPDATE_FAILED: '任务更新失败',
  TASK_ERROR_DELETE_FAILED: '任务删除失败',
  TASK_ERROR_STATUS_UPDATE_FAILED: '任务状态更新失败',
  TASK_ERROR_IMPORT_FAILED: '任务批量导入失败',
  TASK_ERROR_INVALID_STATUS: '无效的任务状态',
  TASK_ERROR_PROCESSING_FAILED: '任务处理失败',

  // ========== 考勤工时相关消息 ==========
  ATTENDANCE_SUCCESS_RECORD_RETRIEVE: '成功获取工时记录',
  ATTENDANCE_SUCCESS_SUMMARY_RETRIEVE: '成功获取工时汇总',
  ATTENDANCE_SUCCESS_EXPORT: '工时数据导出成功',
  ATTENDANCE_SUCCESS_STATS_RETRIEVE: '成功获取工时统计',
  ATTENDANCE_SUCCESS_CHART_RETRIEVE: '成功获取图表数据',
  ATTENDANCE_SUCCESS_WORK_HOURS_RECALCULATE: '工时重新计算成功',
  ATTENDANCE_SUCCESS_WORK_HOURS_ADJUST: '工时调整成功',
  ATTENDANCE_SUCCESS_BATCH_REVIEW: '批量审核成功',

  ATTENDANCE_ERROR_RECORD_RETRIEVE: '获取工时记录失败',
  ATTENDANCE_ERROR_SUMMARY_RETRIEVE: '获取月度工时汇总失败',
  ATTENDANCE_ERROR_NO_PERMISSION_VIEW: '无权限查看其他人的工时记录',
  ATTENDANCE_ERROR_NO_PERMISSION_EXPORT: '只有管理员可以导出工时数据',
  ATTENDANCE_ERROR_MEMBER_NOT_FOUND: '成员不存在',
  ATTENDANCE_ERROR_INVALID_MONTH_FORMAT: '月份格式错误，请使用 YYYY-MM 格式',
  ATTENDANCE_ERROR_INVALID_DATE_FORMAT: '日期格式错误，请使用 YYYY-MM-DD 格式',
  ATTENDANCE_ERROR_INVALID_CHART_TYPE:
    '图表类型必须是 daily、weekly 或 monthly',
  ATTENDANCE_ERROR_EXPORT_FAILED: '导出工时数据失败',
  ATTENDANCE_ERROR_STATS_RETRIEVE_FAILED: '获取工时统计失败',
  ATTENDANCE_ERROR_CHART_RETRIEVE_FAILED: '获取图表数据失败',
  ATTENDANCE_ERROR_NO_PERMISSION_STATS: '无权限查看其他人的工时统计',
  ATTENDANCE_ERROR_NO_PERMISSION_CHART: '无权限查看其他人的工时图表',
  ATTENDANCE_ERROR_CALCULATION_FAILED: '考勤计算失败',
  ATTENDANCE_ERROR_WORK_HOURS_CALCULATION: '工时计算错误',

  // ========== 数据导入相关消息 ==========
  IMPORT_SUCCESS_FIELD_MAPPING: '成功获取{table_type}字段映射配置',
  IMPORT_SUCCESS_TEMPLATE_DOWNLOAD: '模板下载成功',
  IMPORT_SUCCESS_DATA_PREVIEW: '数据预览生成成功',
  IMPORT_SUCCESS_DATA_IMPORT: '数据导入成功',

  IMPORT_ERROR_FIELD_MAPPING: '获取字段映射失败',
  IMPORT_ERROR_TEMPLATE_NOT_FOUND: '未找到模板类型: {template_type}',
  IMPORT_ERROR_TEMPLATE_DOWNLOAD: '模板下载失败',
  IMPORT_ERROR_FILE_PROCESSING: '文件处理失败',
  IMPORT_ERROR_INVALID_FILE_FORMAT: '无效的文件格式',
  IMPORT_ERROR_FILE_SIZE_EXCEEDED: '文件大小超出限制',
  IMPORT_ERROR_EXCEL_IMPORT: 'Excel导入失败',
  IMPORT_ERROR_DATA_MATCHING: '数据匹配失败',
  IMPORT_ERROR_DATA_IMPORT: '数据导入失败',

  // ========== 系统相关消息 ==========
  SYSTEM_SUCCESS_HEALTH_CHECK: '系统健康检查通过',
  SYSTEM_SUCCESS_OPERATION: '操作成功',

  SYSTEM_ERROR_INTERNAL: '系统内部错误',
  SYSTEM_ERROR_DATABASE: '数据库错误',
  SYSTEM_ERROR_DATABASE_CONNECTION: '数据库连接失败',
  SYSTEM_ERROR_DATABASE_INTEGRITY: '数据库完整性约束冲突',
  SYSTEM_ERROR_RATE_LIMIT: '请求过于频繁，请稍后重试',
  SYSTEM_ERROR_CONFIGURATION: '系统配置错误',
  SYSTEM_ERROR_CONFIGURATION_MISSING: '缺少必要的系统配置',
  SYSTEM_ERROR_EXTERNAL_SERVICE: '外部服务错误',
  SYSTEM_ERROR_EMAIL_SERVICE: '邮件服务错误',
  SYSTEM_ERROR_REDIS_SERVICE: 'Redis服务错误',

  // ========== 数据验证相关消息 ==========
  VALIDATION_ERROR_GENERAL: '数据验证失败',
  VALIDATION_ERROR_FIELD_REQUIRED: '{field} 为必填项',
  VALIDATION_ERROR_FIELD_INVALID: '{field} 格式不正确',
  VALIDATION_ERROR_DUPLICATE_RESOURCE: '资源已存在',
  VALIDATION_ERROR_RESOURCE_NOT_FOUND: '资源不存在',
  VALIDATION_ERROR_INVALID_DATE_RANGE: '无效的日期范围',
  VALIDATION_ERROR_BUSINESS_LOGIC: '业务逻辑验证失败',
  VALIDATION_ERROR_INVALID_STATUS_TRANSITION: '无效的状态转换',

  // ========== 通用状态消息 ==========
  GENERAL_SUCCESS: '操作成功',
  GENERAL_ERROR: '操作失败',
  GENERAL_WARNING: '操作警告',
  GENERAL_INFO: '操作信息',

  // ========== 网络相关消息 ==========
  NETWORK_ERROR_CONNECTION: '网络连接失败，请检查网络设置',
  NETWORK_ERROR_TIMEOUT: '网络请求超时，请重试',
  NETWORK_ERROR_OFFLINE: '网络连接已断开，请检查网络连接',

  // ========== HTTP状态相关消息 ==========
  HTTP_ERROR_400: '请求错误',
  HTTP_ERROR_401: '登录已过期，请重新登录',
  HTTP_ERROR_403: '权限不足，无法访问',
  HTTP_ERROR_404: '请求的资源不存在',
  HTTP_ERROR_422: '表单验证失败',
  HTTP_ERROR_429: '请求过于频繁，请稍后再试',
  HTTP_ERROR_500: '服务器内部错误',
  HTTP_ERROR_502: '网关错误',
  HTTP_ERROR_503: '服务暂时不可用',
  HTTP_ERROR_504: '网关超时'
} as const

// 消息格式化工具类
export class MessageFormatter {
  /**
   * 格式化消息模板
   * @param message 消息模板
   * @param params 格式化参数
   * @returns 格式化后的消息
   */
  static format(message: string, params: Record<string, any> = {}): string {
    try {
      return message.replace(/\{(\w+)\}/g, (match, key) => {
        return params[key] !== undefined ? String(params[key]) : match
      })
    } catch (error) {
      console.warn('消息格式化失败:', error, '原消息:', message)
      return message
    }
  }

  /**
   * 获取格式化后的消息
   * @param messageKey 消息键名
   * @param params 格式化参数
   * @returns 格式化后的消息
   */
  static getMessage(
    messageKey: keyof typeof MESSAGES,
    params: Record<string, any> = {}
  ): string {
    const message = MESSAGES[messageKey] || '未知消息'
    return this.format(message, params)
  }
}

// 消息管理器
export class MessageManager {
  /**
   * 获取成功消息
   */
  static getSuccessMessage(
    key: keyof typeof MESSAGES,
    params?: Record<string, any>
  ): string {
    return MessageFormatter.getMessage(key, params)
  }

  /**
   * 获取错误消息
   */
  static getErrorMessage(
    key: keyof typeof MESSAGES,
    params?: Record<string, any>
  ): string {
    return MessageFormatter.getMessage(key, params)
  }

  /**
   * 获取警告消息
   */
  static getWarningMessage(
    key: keyof typeof MESSAGES,
    params?: Record<string, any>
  ): string {
    return MessageFormatter.getMessage(key, params)
  }

  /**
   * 获取信息消息
   */
  static getInfoMessage(
    key: keyof typeof MESSAGES,
    params?: Record<string, any>
  ): string {
    return MessageFormatter.getMessage(key, params)
  }

  /**
   * 根据HTTP状态码获取对应消息
   */
  static getHttpErrorMessage(status: number, defaultMessage?: string): string {
    const statusMessages: Record<number, keyof typeof MESSAGES> = {
      400: 'HTTP_ERROR_400',
      401: 'HTTP_ERROR_401',
      403: 'HTTP_ERROR_403',
      404: 'HTTP_ERROR_404',
      422: 'HTTP_ERROR_422',
      429: 'HTTP_ERROR_429',
      500: 'HTTP_ERROR_500',
      502: 'HTTP_ERROR_502',
      503: 'HTTP_ERROR_503',
      504: 'HTTP_ERROR_504'
    }

    const messageKey = statusMessages[status]
    return messageKey
      ? MessageFormatter.getMessage(messageKey)
      : defaultMessage || `请求失败 (${status})`
  }
}

// 导出便捷函数
export const getMessage = MessageFormatter.getMessage
export const formatMessage = MessageFormatter.format

// 类型定义
export type MessageKey = keyof typeof MESSAGES
export type MessageParams = Record<string, any>

export default MESSAGES
