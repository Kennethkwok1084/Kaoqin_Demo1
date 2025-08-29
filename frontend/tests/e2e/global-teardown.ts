import { request } from '@playwright/test'
import { TestDataManager } from './test-data-manager'

async function globalTeardown() {
  console.log('🧹 Starting global E2E test teardown...')
  
  const apiContext = await request.newContext()
  const testDataManager = new TestDataManager(apiContext)
  
  try {
    // 清理测试数据
    await testDataManager.cleanupTestData()
    console.log('✅ Test data cleanup completed')
    
    // 清理认证状态文件
    try {
      const fs = await import('fs')
      const path = './tests/fixtures/auth-state.json'
      if (fs.existsSync(path)) {
        fs.unlinkSync(path)
        console.log('🗑️ Authentication state file cleaned up')
      }
    } catch (error) {
      console.warn('⚠️ Failed to cleanup auth state file:', error)
    }
    
  } catch (error) {
    console.error('❌ Global teardown error:', error)
  } finally {
    await apiContext.dispose()
  }
  
  console.log('🎉 Global teardown completed!')
}

export default globalTeardown
