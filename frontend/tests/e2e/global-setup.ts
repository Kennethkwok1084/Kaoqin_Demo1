import { chromium, FullConfig, request, APIRequestContext } from '@playwright/test'

// 等待后端服务就绪的函数
async function waitForBackendReady(apiContext: APIRequestContext, maxAttempts = 30): Promise<void> {
  console.log('⏳ Waiting for backend service to be ready...')
  
  for (let attempt = 1; attempt <= maxAttempts; attempt++) {
    try {
      // 检查健康端点
      const healthResponse = await apiContext.get('http://localhost:8000/health')
      if (healthResponse.ok()) {
        console.log('✅ Backend health endpoint responding')
        
        // 检查数据库连接
        const dbResponse = await apiContext.get('http://localhost:8000/api/v1/system/status')
        if (dbResponse.ok()) {
          console.log('✅ Database connection verified')
          return
        }
      }
    } catch (error) {
      console.log(`🔄 Attempt ${attempt}/${maxAttempts} - Backend not ready yet...`)
    }
    
    if (attempt < maxAttempts) {
      await new Promise(resolve => setTimeout(resolve, 2000))
    }
  }
  
  throw new Error('Backend service failed to start within expected time')
}

// 初始化测试数据的函数
async function initializeTestData(apiContext: APIRequestContext): Promise<void> {
  try {
    // 创建测试用户
    const userResponse = await apiContext.post('http://localhost:8000/api/v1/auth/register', {
      data: {
        username: 'testuser',
        password: 'testpass123',
        email: 'test@example.com',
        full_name: '测试用户'
      }
    })
    
    if (userResponse.ok() || userResponse.status() === 400) {
      console.log('✅ Test user ready (created or already exists)')
    }
    
    // 创建管理员用户
    const adminResponse = await apiContext.post('http://localhost:8000/api/v1/auth/register', {
      data: {
        username: 'admin',
        password: 'admin123',
        email: 'admin@example.com',
        full_name: '系统管理员',
        is_superuser: true
      }
    })
    
    if (adminResponse.ok() || adminResponse.status() === 400) {
      console.log('✅ Admin user ready (created or already exists)')
    }
    
  } catch (error) {
    console.warn('⚠️ Test data initialization had issues, but continuing...', error)
  }
}

async function globalSetup(config: FullConfig) {
  console.log('🚀 Starting global E2E test setup...')

  // Launch browser for setup
  const browser = await chromium.launch()
  const page = await browser.newPage()
  const apiContext = await request.newContext()

  try {
    // 健壮的后端服务检查
    console.log('🔍 Performing comprehensive backend health check...')
    await waitForBackendReady(apiContext)
    
    // 初始化测试数据
    console.log('📊 Initializing test data...')
    await initializeTestData(apiContext)

    // 等待前端应用启动并执行认证
    const baseURL = config.projects[0].use?.baseURL || 'http://localhost:3000'
    console.log(`📡 Waiting for frontend at ${baseURL}...`)
    
    await waitForFrontendReady(page, baseURL)
    
    // 执行登录认证
    console.log('🔐 Setting up authentication state...')
    await setupAuthentication(page, baseURL)

  } catch (error) {
    console.error('❌ Global setup failed:', error)
    throw error
  } finally {
    await browser.close()
    await apiContext.dispose()
  }

  console.log('🎉 Global setup completed successfully!')
}

// 等待前端应用就绪
async function waitForFrontendReady(page: any, baseURL: string): Promise<void> {
  let attempts = 0
  const maxAttempts = 15
  const waitInterval = 4000

  while (attempts < maxAttempts) {
    try {
      const response = await page.goto(baseURL, { timeout: 8000 })
      if (response && response.ok()) {
        console.log('✅ Frontend is ready!')
        return
      }
    } catch (error) {
      attempts++
      if (attempts >= maxAttempts) {
        throw new Error(`Frontend not accessible after ${maxAttempts} attempts`)
      }
      console.log(`⏳ Attempt ${attempts}/${maxAttempts} - Frontend not ready, retrying...`)
      await page.waitForTimeout(waitInterval)
    }
  }
}

// 设置认证状态
async function setupAuthentication(page: any, baseURL: string): Promise<void> {
  try {
    // 导航到登录页面
    await page.goto(`${baseURL}/login`)

    // 等待登录页面加载
    await page.waitForSelector('.login-container', { timeout: 10000 })

    // 执行登录
    await page.fill('input[type="text"]', 'admin')
    await page.fill('input[type="password"]', 'admin123')
    await page.click('button[type="submit"]')

    // 等待登录成功
    await page.waitForURL('**/dashboard', { timeout: 15000 })
    console.log('✅ Authentication successful')

    // 保存认证状态到文件
    await page.context().storageState({ 
      path: 'tests/fixtures/auth-state.json' 
    })
    console.log('💾 Authentication state saved')

  } catch (error) {
    console.error('❌ Authentication setup failed:', error)
    throw new Error('Failed to setup authentication - this will cause all E2E tests to fail')
  }
}

export default globalSetup
