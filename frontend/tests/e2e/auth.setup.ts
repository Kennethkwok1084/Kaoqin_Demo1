import { test as setup, expect } from '@playwright/test'

const authFile = 'tests/fixtures/auth-state.json'

setup('authenticate', async ({ page, request }) => {
  console.log('🔐 Setting up authentication for E2E tests...')

  // 确保后端服务可用
  let backendReady = false
  for (let i = 0; i < 10; i++) {
    try {
      const healthCheck = await request.get('http://localhost:8000/health')
      if (healthCheck.ok()) {
        backendReady = true
        break
      }
    } catch (error) {
      console.log(`⏳ Waiting for backend... attempt ${i + 1}/10`)
      await page.waitForTimeout(3000)
    }
  }

  if (!backendReady) {
    throw new Error('Backend service not ready for authentication setup')
  }

  // 导航到登录页面
  await page.goto('http://localhost:3000/login')

  // 等待登录表单出现
  await expect(page.locator('form')).toBeVisible({ timeout: 10000 })

  // 输入凭据
  await page.fill('input[type="text"]', 'admin')
  await page.fill('input[type="password"]', 'admin123')

  // 点击登录
  await page.click('button[type="submit"]')

  // 等待登录成功
  await page.waitForURL('**/dashboard', { timeout: 15000 })

  // 确认登录成功
  await expect(page.locator('.dashboard-container')).toBeVisible()

  // 保存认证状态
  await page.context().storageState({ path: authFile })

  console.log('✅ Authentication setup completed successfully')
})
