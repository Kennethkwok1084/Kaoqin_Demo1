import { chromium, FullConfig } from '@playwright/test'

async function globalSetup(config: FullConfig) {
  console.log('🚀 Starting global E2E test setup...')

  // Launch browser for setup
  const browser = await chromium.launch()
  const page = await browser.newPage()

  try {
    // 首先检查后端服务是否可用
    console.log('🔍 Checking backend health...')
    try {
      const backendResponse = await page.goto('http://localhost:8000/docs', { timeout: 5000 })
      if (backendResponse && backendResponse.ok()) {
        console.log('✅ Backend service is healthy!')
      } else {
        console.log('⚠️ Backend service may not be available, proceeding anyway...')
      }
    } catch (error) {
      console.log('⚠️ Backend health check failed, proceeding anyway...')
    }

    // 等待前端应用启动
    const baseURL = config.projects[0].use?.baseURL || 'http://localhost:3000'
    console.log(`📡 Waiting for frontend at ${baseURL}...`)

    // 检查应用是否可访问 - 优化等待策略
    let attempts = 0
    const maxAttempts = 20  // 减少尝试次数
    const waitInterval = 3000  // 增加等待间隔

    while (attempts < maxAttempts) {
      try {
        const response = await page.goto(baseURL, { timeout: 8000 })
        if (response && response.ok()) {
          console.log('✅ Frontend is ready!')
          break
        }
      } catch (error) {
        attempts++
        if (attempts >= maxAttempts) {
          throw new Error(
            `Frontend not accessible after ${maxAttempts} attempts`
          )
        }
        console.log(
          `⏳ Attempt ${attempts}/${maxAttempts} - Frontend not ready, retrying...`
        )
        await page.waitForTimeout(waitInterval)
      }
    }

    // 执行预登录，保存认证状态
    console.log('🔐 Setting up authentication state...')

    // 导航到登录页面
    await page.goto(`${baseURL}/login`)

    // 等待登录页面加载
    await page.waitForSelector('.login-container', { timeout: 10000 })

    // 检查是否已经有测试用户数据，如果没有则创建
    // 这里可以调用后端API创建测试用户

    // 执行登录
    await page.fill('input[type="text"]', 'admin')
    await page.fill('input[type="password"]', 'admin123')
    await page.click('button[type="submit"]')

    // 等待登录成功并跳转到仪表板
    try {
      await page.waitForURL('**/dashboard', { timeout: 10000 })
      console.log('✅ Authentication setup completed')

      // 保存认证状态
      await page
        .context()
        .storageState({ path: 'tests/fixtures/auth-state.json' })
      console.log('💾 Authentication state saved')
    } catch (error) {
      console.log('⚠️  Login might have failed, but continuing with tests...')
      // 不抛出错误，让测试继续进行
    }
  } catch (error) {
    console.error('❌ Global setup failed:', error)
    throw error
  } finally {
    await browser.close()
  }

  console.log('🎉 Global setup completed successfully!')
}

export default globalSetup
