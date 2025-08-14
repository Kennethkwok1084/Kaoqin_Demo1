// 日期格式化工具函数

import dayjs from 'dayjs'
import relativeTime from 'dayjs/plugin/relativeTime'
import 'dayjs/locale/zh-cn'

// 配置dayjs
dayjs.extend(relativeTime)
dayjs.locale('zh-cn')

/**
 * 格式化日期
 * @param date 日期字符串或Date对象
 * @param format 格式字符串，默认 'YYYY-MM-DD HH:mm:ss'
 * @returns 格式化后的日期字符串
 */
export function formatDate(
  date: string | Date,
  format = 'YYYY-MM-DD HH:mm:ss'
): string {
  if (!date) return ''
  return dayjs(date).format(format)
}

/**
 * 格式化日期为短格式
 * @param date 日期字符串或Date对象
 * @returns 格式化后的日期字符串 (YYYY-MM-DD)
 */
export function formatDateShort(date: string | Date): string {
  return formatDate(date, 'YYYY-MM-DD')
}

/**
 * 格式化时间
 * @param date 日期字符串或Date对象
 * @returns 格式化后的时间字符串 (HH:mm:ss)
 */
export function formatTime(date: string | Date): string {
  return formatDate(date, 'HH:mm:ss')
}

/**
 * 相对时间格式化 (几分钟前、几小时前等)
 * @param date 日期字符串或Date对象
 * @returns 相对时间字符串
 */
export function formatFromNow(date: string | Date): string {
  if (!date) return ''
  return dayjs(date).fromNow()
}

/**
 * 相对时间格式化，精确到某个时间点
 * @param date 日期字符串或Date对象
 * @param baseDate 基准日期，默认为当前时间
 * @returns 相对时间字符串
 */
export function formatRelativeTo(
  date: string | Date,
  baseDate?: string | Date
): string {
  if (!date) return ''
  return dayjs(date).to(dayjs(baseDate))
}

/**
 * 获取日期范围描述
 * @param startDate 开始日期
 * @param endDate 结束日期
 * @returns 日期范围描述
 */
export function formatDateRange(
  startDate: string | Date,
  endDate: string | Date
): string {
  if (!startDate || !endDate) return ''

  const start = dayjs(startDate)
  const end = dayjs(endDate)

  if (start.isSame(end, 'day')) {
    return start.format('YYYY-MM-DD')
  }

  if (start.isSame(end, 'year')) {
    return `${start.format('MM-DD')} ~ ${end.format('MM-DD')}`
  }

  return `${start.format('YYYY-MM-DD')} ~ ${end.format('YYYY-MM-DD')}`
}

/**
 * 判断是否为今天
 * @param date 日期字符串或Date对象
 * @returns 是否为今天
 */
export function isToday(date: string | Date): boolean {
  if (!date) return false
  return dayjs(date).isSame(dayjs(), 'day')
}

/**
 * 判断是否为昨天
 * @param date 日期字符串或Date对象
 * @returns 是否为昨天
 */
export function isYesterday(date: string | Date): boolean {
  if (!date) return false
  return dayjs(date).isSame(dayjs().subtract(1, 'day'), 'day')
}

/**
 * 判断是否为本周
 * @param date 日期字符串或Date对象
 * @returns 是否为本周
 */
export function isThisWeek(date: string | Date): boolean {
  if (!date) return false
  return dayjs(date).isSame(dayjs(), 'week')
}

/**
 * 判断是否为本月
 * @param date 日期字符串或Date对象
 * @returns 是否为本月
 */
export function isThisMonth(date: string | Date): boolean {
  if (!date) return false
  return dayjs(date).isSame(dayjs(), 'month')
}

/**
 * 获取友好的日期显示
 * @param date 日期字符串或Date对象
 * @returns 友好的日期字符串
 */
export function formatFriendlyDate(date: string | Date): string {
  if (!date) return ''

  const target = dayjs(date)

  if (isToday(date)) {
    return `今天 ${target.format('HH:mm')}`
  }

  if (isYesterday(date)) {
    return `昨天 ${target.format('HH:mm')}`
  }

  if (isThisWeek(date)) {
    const weekdays = ['周日', '周一', '周二', '周三', '周四', '周五', '周六']
    return `${weekdays[target.day()]} ${target.format('HH:mm')}`
  }

  if (isThisMonth(date)) {
    return target.format('MM-DD HH:mm')
  }

  return target.format('YYYY-MM-DD')
}

/**
 * 计算时间差
 * @param startDate 开始日期
 * @param endDate 结束日期，默认为当前时间
 * @returns 时间差对象
 */
export function getTimeDiff(startDate: string | Date, endDate?: string | Date) {
  if (!startDate) return null

  const start = dayjs(startDate)
  const end = dayjs(endDate)

  const diffMs = end.diff(start)
  const duration = dayjs.duration(diffMs)

  return {
    milliseconds: diffMs,
    seconds: duration.asSeconds(),
    minutes: duration.asMinutes(),
    hours: duration.asHours(),
    days: duration.asDays(),
    weeks: duration.asWeeks(),
    months: duration.asMonths(),
    years: duration.asYears(),
    humanize: duration.humanize()
  }
}

/**
 * 获取工作日天数（排除周末）
 * @param startDate 开始日期
 * @param endDate 结束日期
 * @returns 工作日天数
 */
export function getWorkdays(
  startDate: string | Date,
  endDate: string | Date
): number {
  if (!startDate || !endDate) return 0

  let start = dayjs(startDate)
  const end = dayjs(endDate)
  let workdays = 0

  while (start.isBefore(end) || start.isSame(end, 'day')) {
    if (start.day() !== 0 && start.day() !== 6) {
      // 不是周末
      workdays++
    }
    start = start.add(1, 'day')
  }

  return workdays
}

/**
 * 格式化持续时间
 * @param duration 持续时间（毫秒）
 * @returns 格式化的持续时间字符串
 */
export function formatDuration(duration: number): string {
  if (!duration || duration < 0) return '0秒'

  const d = dayjs.duration(duration)

  if (d.asDays() >= 1) {
    return `${Math.floor(d.asDays())}天${d.hours()}小时${d.minutes()}分钟`
  }

  if (d.asHours() >= 1) {
    return `${d.hours()}小时${d.minutes()}分钟`
  }

  if (d.asMinutes() >= 1) {
    return `${d.minutes()}分钟${d.seconds()}秒`
  }

  return `${d.seconds()}秒`
}

/**
 * 获取月份的开始和结束日期
 * @param date 日期字符串或Date对象，默认为当前日期
 * @returns 月份开始和结束日期
 */
export function getMonthRange(date?: string | Date): [string, string] {
  const target = dayjs(date)
  const start = target.startOf('month').format('YYYY-MM-DD')
  const end = target.endOf('month').format('YYYY-MM-DD')
  return [start, end]
}

/**
 * 获取周的开始和结束日期
 * @param date 日期字符串或Date对象，默认为当前日期
 * @returns 周开始和结束日期
 */
export function getWeekRange(date?: string | Date): [string, string] {
  const target = dayjs(date)
  const start = target.startOf('week').format('YYYY-MM-DD')
  const end = target.endOf('week').format('YYYY-MM-DD')
  return [start, end]
}

/**
 * 获取季度的开始和结束日期
 * @param date 日期字符串或Date对象，默认为当前日期
 * @returns 季度开始和结束日期
 */
export function getQuarterRange(date?: string | Date): [string, string] {
  const target = dayjs(date)
  const start = target.startOf('quarter').format('YYYY-MM-DD')
  const end = target.endOf('quarter').format('YYYY-MM-DD')
  return [start, end]
}

/**
 * 获取年的开始和结束日期
 * @param date 日期字符串或Date对象，默认为当前日期
 * @returns 年开始和结束日期
 */
export function getYearRange(date?: string | Date): [string, string] {
  const target = dayjs(date)
  const start = target.startOf('year').format('YYYY-MM-DD')
  const end = target.endOf('year').format('YYYY-MM-DD')
  return [start, end]
}
