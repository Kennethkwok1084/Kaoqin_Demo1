import { test, expect, type Page } from '@playwright/test'
import { LoginPage, DashboardPage, TasksPage } from './pages/index'

// 测试用例：登录 → 创建任务 → 查看工时的完整流程
test.describe('登录→创建任务→查看工时端到端流程', () => {
  let page: Page
  let dashboardPage: DashboardPage
  let tasksPage: TasksPage

  // 测试数据
  const testUser = {
    username: 'admin',
    password: 'admin123'
  }

  const testTask = {
    title: '测试维修任务_' + Date.now(), // 添加时间戳避免重复
    description: '这是一个端到端测试的维修任务',
    location: '图书馆3楼',
    reporterName: '张三',
    reporterPhone: '13800138001',
    priority: 'high',
    taskType: 'repair'
  }

  test.beforeEach(async ({ page: testPage }) => {
    page = testPage
    loginPage = new LoginPage(page)
    dashboardPage = new DashboardPage(page)
    tasksPage = new TasksPage(page)

    // 设置较长的超时时间
    page.setDefaultTimeout(30000)

    // 监听页面错误
    page.on('pageerror', error => {
      console.error('页面错误:', error.message)
    })

    // 监听控制台错误
    page.on('console', msg => {
      if (msg.type() === 'error') {
        console.error('控制台错误:', msg.text())
      }
    })
  })

  // 注意: 由于使用了预设的认证状态，不再需要手动登录
  test('完整业务流程：已认证用户→创建任务→查看工时', async () => {
    // 步骤1: 访问仪表板页面 (已经认证)
    await test.step('验证已登录状态', async () => {
      await page.goto('/dashboard')
      await dashboardPage.expectDashboard()
      await expect(dashboardPage.userInfo).toContainText(testUser.username)
    })

    // 步骤2: 导航到任务管理页面
    await test.step('导航到任务管理页面', async () => {
      await dashboardPage.navigateToTasks()
      await tasksPage.expectTasksPage()
    })

    // 步骤3: 创建新任务
    await test.step('创建新任务', async () => {
      await tasksPage.createNewTask()

      // 填写任务表单
      await tasksPage.fillTaskForm({
        title: testTask.title,
        description: testTask.description,
        location: testTask.location,
        reporterName: testTask.reporterName,
        reporterPhone: testTask.reporterPhone,
        priority: testTask.priority,
        taskType: testTask.taskType
      })

      // 提交表单
      await tasksPage.submitTask()

      // 验证任务创建成功
      await expect(page.locator('.success-message')).toBeVisible()
      await tasksPage.expectTaskInList(testTask.title)
    })

    // 步骤4: 查看任务详情和工时
    await test.step('查看任务详情和工时', async () => {
      // 点击刚创建的任务
      await page.click(`.task-item:has-text("${testTask.title}")`)

      // 等待任务详情页面加载
      await page.waitForURL('**/tasks/**')

      // 验证任务详情显示正确
      await expect(page.locator('.task-detail')).toBeVisible()
      await expect(page.locator('.task-title')).toContainText(testTask.title)
      await expect(page.locator('.task-description')).toContainText(
        testTask.description
      )
      await expect(page.locator('.task-location')).toContainText(
        testTask.location
      )

      // 验证工时记录区域
      await expect(page.locator('.work-hours-section')).toBeVisible()
      await expect(page.locator('text=工时记录')).toBeVisible()
    })

    // 步骤5: 添加工时记录
    await test.step('添加工时记录', async () => {
      // 点击添加工时按钮
      await page.click('text=添加工时')

      // 等待工时表单出现
      await expect(page.locator('.work-hours-form')).toBeVisible()

      // 填写工时信息
      await page.fill('input[name="hours"]', '2.5')
      await page.fill('textarea[name="description"]', '修复图书馆空调系统')
      await page.selectOption('select[name="status"]', 'in_progress')

      // 提交工时记录
      await page.click('button[type="submit"]:has-text("保存")')

      // 验证工时记录保存成功
      await expect(page.locator('.success-message')).toBeVisible()
      await expect(page.locator('.work-hour-item')).toContainText('2.5')
      await expect(page.locator('.work-hour-item')).toContainText(
        '修复图书馆空调系统'
      )
    })

    // 步骤6: 验证工时统计
    await test.step('验证工时统计', async () => {
      // 检查工时统计信息
      await expect(page.locator('.total-hours')).toContainText('2.5')
      await expect(page.locator('.task-status')).toContainText('进行中')

      // 验证工时历史记录
      await expect(page.locator('.work-hours-history')).toBeVisible()
      await expect(page.locator('.work-hour-item').first()).toBeVisible()
    })
  })

  // 独立的登录测试 (使用独立的页面实例)
  test('手动登录流程测试', async ({ page: freshPage }) => {
    // 使用fresh page避免使用预设认证状态
    const freshLoginPage = new LoginPage(freshPage)
    const freshDashboardPage = new DashboardPage(freshPage)

    await test.step('访问登录页面', async () => {
      await freshLoginPage.goto()
      await freshLoginPage.expectLoginForm()
    })

    await test.step('执行登录操作', async () => {
      await freshLoginPage.login(testUser.username, testUser.password)
      await freshPage.waitForURL('**/dashboard')
      await freshDashboardPage.expectDashboard()
    })
  })

  // 错误场景测试
  test('错误处理：无效登录凭据', async ({ page: freshPage }) => {
    const freshLoginPage = new LoginPage(freshPage)

    await freshLoginPage.goto()
    await freshLoginPage.login('invalid_user', 'wrong_password')

    // 验证错误消息显示
    await freshLoginPage.expectErrorMessage()

    // 确保仍在登录页面
    await expect(freshPage.url()).toContain('/login')
  })
})
