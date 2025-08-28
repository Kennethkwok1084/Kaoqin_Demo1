import { describe, it, expect } from 'vitest'
import {
  formatDate,
  formatDateTime,
  formatTime,
  isToday,
  isThisWeek,
  isThisMonth,
  getRelativeTime,
  parseDate,
  addDays,
  getDaysBetween,
  getWeekRange,
  getMonthRange,
  formatDuration
} from '@/utils/date'

describe('Date Utils', () => {
  const testDate = new Date('2024-03-15T14:30:00Z')
  const testDateString = '2024-03-15'
  const testDateTimeString = '2024-03-15T14:30:00Z'

  describe('formatDate', () => {
    it('should format date with default format', () => {
      expect(formatDate(testDate)).toBe('2024-03-15')
      expect(formatDate(testDateString)).toBe('2024-03-15')
      expect(formatDate(testDateTimeString)).toBe('2024-03-15')
    })

    it('should format date with custom format', () => {
      expect(formatDate(testDate, 'YYYY年MM月DD日')).toBe('2024年03月15日')
      expect(formatDate(testDate, 'MM/DD/YYYY')).toBe('03/15/2024')
      expect(formatDate(testDate, 'DD-MM-YYYY')).toBe('15-03-2024')
    })

    it('should handle invalid dates', () => {
      expect(formatDate('invalid-date')).toBe('')
      expect(formatDate(null as any)).toBe('')
      expect(formatDate(undefined as any)).toBe('')
    })
  })

  describe('formatDateTime', () => {
    it('should format datetime with default format', () => {
      const result = formatDateTime(testDate)
      expect(result).toMatch(/2024-03-15 \d{2}:\d{2}:\d{2}/)
    })

    it('should format datetime with custom format', () => {
      expect(formatDateTime(testDate, 'YYYY-MM-DD HH:mm')).toMatch(
        /2024-03-15 \d{2}:\d{2}/
      )
      expect(formatDateTime(testDate, 'MM/DD/YYYY hh:mm A')).toMatch(
        /03\/15\/2024 \d{2}:\d{2} (AM|PM|上午|下午|晚上)/
      )
    })
  })

  describe('formatTime', () => {
    it('should format time with default format', () => {
      const result = formatTime(testDate)
      expect(result).toMatch(/\d{2}:\d{2}:\d{2}/)
    })

    it('should format time with custom format', () => {
      expect(formatTime(testDate, 'HH:mm')).toMatch(/\d{2}:\d{2}/)
      expect(formatTime(testDate, 'hh:mm A')).toMatch(/\d{2}:\d{2} (AM|PM|上午|下午|晚上)/)
    })
  })

  describe('isToday', () => {
    it('should detect if date is today', () => {
      const today = new Date()
      const tomorrow = new Date(today.getTime() + 24 * 60 * 60 * 1000)
      const yesterday = new Date(today.getTime() - 24 * 60 * 60 * 1000)

      expect(isToday(today)).toBe(true)
      expect(isToday(tomorrow)).toBe(false)
      expect(isToday(yesterday)).toBe(false)
    })

    it('should handle date strings', () => {
      const today = new Date()
      const todayString = formatDate(today)
      expect(isToday(todayString)).toBe(true)
    })
  })

  describe('isThisWeek', () => {
    it('should detect if date is in current week', () => {
      const now = new Date()
      const weekStart = new Date(
        now.getTime() - now.getDay() * 24 * 60 * 60 * 1000
      )
      const weekEnd = new Date(weekStart.getTime() + 6 * 24 * 60 * 60 * 1000)
      const nextWeek = new Date(weekEnd.getTime() + 24 * 60 * 60 * 1000)

      expect(isThisWeek(weekStart)).toBe(true)
      expect(isThisWeek(weekEnd)).toBe(true)
      expect(isThisWeek(nextWeek)).toBe(false)
    })
  })

  describe('isThisMonth', () => {
    it('should detect if date is in current month', () => {
      const now = new Date()
      const monthStart = new Date(now.getFullYear(), now.getMonth(), 1)
      const monthEnd = new Date(now.getFullYear(), now.getMonth() + 1, 0)
      const nextMonth = new Date(now.getFullYear(), now.getMonth() + 1, 1)

      expect(isThisMonth(monthStart)).toBe(true)
      expect(isThisMonth(monthEnd)).toBe(true)
      expect(isThisMonth(nextMonth)).toBe(false)
    })
  })

  describe('getRelativeTime', () => {
    it('should return relative time strings', () => {
      const now = new Date()
      const oneMinuteAgo = new Date(now.getTime() - 60 * 1000)
      const oneHourAgo = new Date(now.getTime() - 60 * 60 * 1000)
      const oneDayAgo = new Date(now.getTime() - 24 * 60 * 60 * 1000)

      expect(getRelativeTime(oneMinuteAgo)).toContain('分钟前')
      expect(getRelativeTime(oneHourAgo)).toContain('小时前')
      expect(getRelativeTime(oneDayAgo)).toContain('天前')
    })

    it('should handle future dates', () => {
      const now = new Date()
      const oneHourLater = new Date(now.getTime() + 60 * 60 * 1000)

      expect(getRelativeTime(oneHourLater)).toMatch(/(小时后|小时内|hour)/)
    })
  })

  describe('parseDate', () => {
    it('should parse various date formats', () => {
      expect(parseDate('2024-03-15')).toBeInstanceOf(Date)
      expect(parseDate('2024-03-15T14:30:00Z')).toBeInstanceOf(Date)
      expect(parseDate('03/15/2024')).toBeInstanceOf(Date)
    })

    it('should handle invalid dates', () => {
      expect(parseDate('invalid-date')).toBeNull()
      expect(parseDate('')).toBeNull()
      expect(parseDate(null as any)).toBeNull()
    })
  })

  describe('addDays', () => {
    it('should add days to date', () => {
      const baseDate = new Date('2024-03-15')
      const futureDate = addDays(baseDate, 5)
      const pastDate = addDays(baseDate, -5)

      expect(formatDate(futureDate)).toBe('2024-03-20')
      expect(formatDate(pastDate)).toBe('2024-03-10')
    })

    it('should handle string dates', () => {
      const result = addDays('2024-03-15', 10)
      expect(formatDate(result)).toBe('2024-03-25')
    })
  })

  describe('getDaysBetween', () => {
    it('should calculate days between dates', () => {
      const start = new Date('2024-03-15')
      const end = new Date('2024-03-20')

      expect(getDaysBetween(start, end)).toBe(5)
      expect(getDaysBetween(end, start)).toBe(5) // 应该返回绝对值
    })

    it('should handle string dates', () => {
      expect(getDaysBetween('2024-03-15', '2024-03-20')).toBe(5)
    })
  })

  describe('getWeekRange', () => {
    it('should get week range for a date', () => {
      const testDate = new Date('2024-03-15') // 假设是周五
      const { start, end } = getWeekRange(testDate)

      expect(start).toBeInstanceOf(Date)
      expect(end).toBeInstanceOf(Date)
      // 应该是6天多一点的时间差（接近7天）
      const diffMs = end.getTime() - start.getTime()
      expect(diffMs).toBeGreaterThan(6 * 24 * 60 * 60 * 1000)
      expect(diffMs).toBeLessThan(7 * 24 * 60 * 60 * 1000 + 24 * 60 * 60 * 1000)
    })

    it('should handle current week when no date provided', () => {
      const { start, end } = getWeekRange()

      expect(start).toBeInstanceOf(Date)
      expect(end).toBeInstanceOf(Date)
      // 应该是6天多一点的时间差（接近7天）
      const diffMs = end.getTime() - start.getTime()
      expect(diffMs).toBeGreaterThan(6 * 24 * 60 * 60 * 1000)
      expect(diffMs).toBeLessThan(7 * 24 * 60 * 60 * 1000 + 24 * 60 * 60 * 1000)
    })
  })

  describe('getMonthRange', () => {
    it('should get month range for a date', () => {
      const testDate = new Date('2024-03-15')
      const { start, end } = getMonthRange(testDate)

      expect(start.getDate()).toBe(1)
      expect(start.getMonth()).toBe(2) // March is month 2 (0-indexed)
      expect(end.getDate()).toBe(31) // March has 31 days
      expect(end.getMonth()).toBe(2)
    })
  })

  describe('formatDuration', () => {
    it('should format duration in minutes', () => {
      expect(formatDuration(60)).toBe('1小时')
      expect(formatDuration(90)).toBe('1小时30分钟')
      expect(formatDuration(30)).toBe('30分钟')
      expect(formatDuration(0)).toBe('0分钟')
    })

    it('should handle large durations', () => {
      expect(formatDuration(1440)).toBe('24小时') // 1 day
      expect(formatDuration(1500)).toBe('25小时') // 25 hours
    })

    it('should handle negative durations', () => {
      expect(formatDuration(-60)).toBe('0分钟') // 应该处理负值
    })
  })
})
