// 认证工具函数

const TOKEN_KEY = 'access_token'
const REFRESH_TOKEN_KEY = 'refresh_token'

/**
 * 获取token
 */
export function getToken(): string | null {
  try {
    return localStorage.getItem(TOKEN_KEY)
  } catch (error) {
    return null
  }
}

/**
 * 设置token
 */
export function setToken(token: string): void {
  try {
    localStorage.setItem(TOKEN_KEY, token)
  } catch (error) {
    // 忽略localStorage不可用的错误
  }
}

/**
 * 移除token
 */
export function removeToken(): void {
  localStorage.removeItem(TOKEN_KEY)
}

/**
 * 移除刷新token
 */
export function removeRefreshToken(): void {
  localStorage.removeItem(REFRESH_TOKEN_KEY)
}

/**
 * 获取刷新token
 */
export function getRefreshToken(): string | null {
  return localStorage.getItem(REFRESH_TOKEN_KEY)
}

/**
 * 设置刷新token
 */
export function setRefreshToken(refreshToken: string): void {
  localStorage.setItem(REFRESH_TOKEN_KEY, refreshToken)
}

/**
 * 检查token是否过期
 */
export function isTokenExpired(token: string | null): boolean {
  if (!token) return true
  
  try {
    const payload = JSON.parse(atob(token.split('.')[1]))
    if (!payload.exp) return true // 如果没有exp字段，认为已过期
    const exp = payload.exp * 1000 // 转换为毫秒
    return Date.now() >= exp
  } catch (error) {
    console.error('Token解析失败:', error)
    return true
  }
}

/**
 * 获取token载荷
 */
export function getTokenPayload(token: string): any {
  try {
    return JSON.parse(atob(token.split('.')[1]))
  } catch (error) {
    console.error('Token载荷解析失败:', error)
    return null
  }
}

/**
 * 解析JWT token
 */
export function parseJWT(token: string): any {
  if (!token || typeof token !== 'string') return null
  
  try {
    const parts = token.split('.')
    if (parts.length !== 3) return null
    
    const payload = JSON.parse(atob(parts[1]))
    return payload
  } catch (error) {
    return null
  }
}

/**
 * 清除所有认证数据
 */
export function clearAuthData(): void {
  try {
    localStorage.removeItem(TOKEN_KEY)
    localStorage.removeItem(REFRESH_TOKEN_KEY)
  } catch (error) {
    // 忽略localStorage不可用的错误
  }
}

/**
 * 格式化权限字符串
 */
export function formatPermission(permission: string): string {
  return permission
    .split('_')
    .map(word => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ')
}

/**
 * 检查密码强度
 */
export function checkPasswordStrength(password: string): {
  score: number
  strength: 'weak' | 'medium' | 'strong' | 'very-strong'
  suggestions: string[]
} {
  let score = 0
  const suggestions: string[] = []

  // 长度检查
  if (password.length >= 8) {
    score += 1
  } else {
    suggestions.push('密码长度至少8位')
  }

  // 包含小写字母
  if (/[a-z]/.test(password)) {
    score += 1
  } else {
    suggestions.push('至少包含一个小写字母')
  }

  // 包含大写字母
  if (/[A-Z]/.test(password)) {
    score += 1
  } else {
    suggestions.push('至少包含一个大写字母')
  }

  // 包含数字
  if (/\d/.test(password)) {
    score += 1
  } else {
    suggestions.push('至少包含一个数字')
  }

  // 包含特殊字符
  if (/[!@#$%^&*(),.?":{}|<>]/.test(password)) {
    score += 1
  } else {
    suggestions.push('至少包含一个特殊字符')
  }

  // 长度大于12
  if (password.length >= 12) {
    score += 1
  }

  let strength: 'weak' | 'medium' | 'strong' | 'very-strong'
  if (score <= 2) {
    strength = 'weak'
  } else if (score <= 3) {
    strength = 'medium'
  } else if (score <= 4) {
    strength = 'strong'
  } else {
    strength = 'very-strong'
  }

  return { score, strength, suggestions }
}

/**
 * 生成随机密码
 */
export function generateRandomPassword(length: number = 12): string {
  const lowercase = 'abcdefghijklmnopqrstuvwxyz'
  const uppercase = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
  const numbers = '0123456789'
  const symbols = '!@#$%^&*()_+-=[]{}|;:,.<>?'

  const allChars = lowercase + uppercase + numbers + symbols
  let password = ''

  // 确保至少包含每种类型的字符
  password += lowercase[Math.floor(Math.random() * lowercase.length)]
  password += uppercase[Math.floor(Math.random() * uppercase.length)]
  password += numbers[Math.floor(Math.random() * numbers.length)]
  password += symbols[Math.floor(Math.random() * symbols.length)]

  // 填充剩余长度
  for (let i = 4; i < length; i++) {
    password += allChars[Math.floor(Math.random() * allChars.length)]
  }

  // 打乱字符顺序
  return password
    .split('')
    .sort(() => Math.random() - 0.5)
    .join('')
}
