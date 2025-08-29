import { test, expect, type Page } from '@playwright/test'
import { LoginPage, DashboardPage, TasksPage } from './pages/index'

// 测试用例：登录 → 创建任务 → 查看工时的完整流程
test.describe('登录→创建任务→查看工时端到端流程', () => {
  let page: Page
  let loginPage: LoginPage
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
      await expect(page.locator('.task-description')).toContainText(testTask.description)
      await expect(page.locator('.task-location')).toContainText(testTask.location)

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
      await expect(page.locator('.work-hour-item')).toContainText('修复图书馆空调系统')
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

      // 等待任务创建对话框出现
      await expect(page.locator('.el-dialog')).toBeVisible()
      await expect(page.locator('.el-dialog__title')).toContainText('创建任务')

      // 填写任务表单
      await page.fill('input[placeholder*="任务标题"]', testTask.title)
      await page.fill('textarea[placeholder*="任务描述"]', testTask.description)
      await page.fill('input[placeholder*="地点"]', testTask.location)
      await page.fill(
        'input[placeholder*="报修人姓名"]',
        testTask.reporter_name
      )
      await page.fill('input[placeholder*="联系电话"]', testTask.reporter_phone)

      // 选择任务类型
      await page.click('.el-select:has-text("任务类型")')
      await page.click(
        `text=${testTask.task_type === 'repair' ? '维修任务' : '监控任务'}`
      )

      // 选择优先级
      await page.click('.el-select:has-text("优先级")')
      await page.click(
        `text=${testTask.priority === 'high' ? '高' : testTask.priority === 'medium' ? '中' : '低'}`
      )

      // 提交任务创建
      await page.click('.el-dialog .el-button--primary:has-text("确定")')

      // 等待任务创建成功消息
      await expect(page.locator('.el-message--success')).toContainText(
        '任务创建成功'
      )

      // 等待对话框关闭
      await expect(page.locator('.el-dialog')).not.toBeVisible()
    })

    // 步骤5: 验证任务出现在列表中
    await test.step('验证任务出现在列表中', async () => {
      // 刷新任务列表
      await page.click('text=刷新')

      // 等待加载完成
      await page.waitForSelector('.task-table tbody tr', { timeout: 10000 })

      // 验证新创建的任务在列表中
      await expect(page.locator('.task-table')).toContainText(testTask.title)
      await expect(page.locator('.task-table')).toContainText(
        testTask.reporter_name
      )
      await expect(page.locator('.task-table')).toContainText('待处理')
    })

    // 步骤6: 查看任务详情
    await test.step('查看任务详情', async () => {
      // 找到刚创建的任务行
      const taskRow = page
        .locator('.task-table tbody tr')
        .filter({
          hasText: testTask.title
        })
        .first()

      await expect(taskRow).toBeVisible()

      // 点击查看详情按钮
      await taskRow.locator('text=查看').click()

      // 验证任务详情对话框
      await expect(page.locator('.task-detail-dialog')).toBeVisible()
      await expect(page.locator('.task-detail-dialog')).toContainText(
        testTask.title
      )
      await expect(page.locator('.task-detail-dialog')).toContainText(
        testTask.description
      )
      await expect(page.locator('.task-detail-dialog')).toContainText(
        testTask.location
      )

      // 关闭详情对话框
      await page.click('.task-detail-dialog .el-dialog__close')
      await expect(page.locator('.task-detail-dialog')).not.toBeVisible()
    })

    // 步骤7: 导航到工时管理页面
    await test.step('导航到工时管理页面', async () => {
      // 点击工时管理菜单
      await page.click('text=工时管理')

      // 等待页面加载
      await page.waitForURL('**/work-hours')

      // 验证工时列表页面
      await expect(page.locator('.work-hours-list')).toBeVisible()
      await expect(page.locator('text=工时管理')).toBeVisible()
    })

    // 步骤8: 查看新任务的工时详情
    await test.step('查看新任务的工时详情', async () => {
      // 搜索刚创建的任务
      await page.fill('input[placeholder*="搜索任务"]', testTask.title)
      await page.press('input[placeholder*="搜索任务"]', 'Enter')

      // 等待搜索结果
      await page.waitForTimeout(1000)

      // 验证任务出现在工时列表中
      const workHourRow = page
        .locator('.work-hours-table tbody tr')
        .filter({
          hasText: testTask.title
        })
        .first()

      await expect(workHourRow).toBeVisible()

      // 验证工时信息
      await expect(workHourRow).toContainText('待处理')

      // 点击查看工时详情
      await workHourRow.locator('text=详情').click()

      // 验证工时详情对话框
      await expect(page.locator('.work-hour-detail-dialog')).toBeVisible()
      await expect(page.locator('.work-hour-detail-dialog')).toContainText(
        '工时详情'
      )
      await expect(page.locator('.work-hour-detail-dialog')).toContainText(
        testTask.title
      )

      // 验证工时计算规则显示
      await expect(page.locator('.work-hour-detail-dialog')).toContainText(
        '基础工时'
      )
      await expect(page.locator('.work-hour-detail-dialog')).toContainText(
        testTask.task_type === 'repair' ? '40分钟' : '100分钟'
      )
    })

    // 步骤9: 模拟任务状态变更并验证工时变化
    await test.step('模拟任务状态变更', async () => {
      // 关闭工时详情对话框
      await page.click('.work-hour-detail-dialog .el-dialog__close')

      // 返回任务管理页面
      await page.click('text=任务管理')
      await page.waitForURL('**/tasks')

      // 找到任务并点击编辑
      const taskRow = page
        .locator('.task-table tbody tr')
        .filter({
          hasText: testTask.title
        })
        .first()

      await taskRow.locator('text=编辑').click()

      // 等待编辑对话框
      await expect(page.locator('.task-edit-dialog')).toBeVisible()

      // 修改任务状态为进行中
      await page.click('.task-edit-dialog .el-select:has-text("状态")')
      await page.click('text=进行中')

      // 保存修改
      await page.click('.task-edit-dialog .el-button--primary:has-text("确定")')

      // 等待保存成功消息
      await expect(page.locator('.el-message--success')).toContainText(
        '任务更新成功'
      )
    })

    // 步骤10: 验证状态变更后的工时更新
    await test.step('验证状态变更后的工时更新', async () => {
      // 回到工时管理页面
      await page.click('text=工时管理')
      await page.waitForURL('**/work-hours')

      // 搜索任务
      await page.fill('input[placeholder*="搜索任务"]', testTask.title)
      await page.press('input[placeholder*="搜索任务"]', 'Enter')

      // 等待搜索结果
      await page.waitForTimeout(1000)

      // 验证任务状态已更新
      const workHourRow = page
        .locator('.work-hours-table tbody tr')
        .filter({
          hasText: testTask.title
        })
        .first()

      await expect(workHourRow).toBeVisible()
      await expect(workHourRow).toContainText('进行中')

      // 查看更新后的工时详情
      await workHourRow.locator('text=详情').click()

      await expect(page.locator('.work-hour-detail-dialog')).toBeVisible()
      await expect(page.locator('.work-hour-detail-dialog')).toContainText(
        '进行中'
      )

      // 验证工时记录包含状态变更历史
      await expect(page.locator('.work-hour-detail-dialog')).toContainText(
        '状态变更记录'
      )
    })

    // 步骤11: 测试数据导出功能
    await test.step('测试数据导出功能', async () => {
      // 关闭详情对话框
      await page.click('.work-hour-detail-dialog .el-dialog__close')

      // 点击导出按钮
      await page.click('text=导出数据')

      // 等待导出对话框
      await expect(page.locator('.export-dialog')).toBeVisible()

      // 选择导出格式
      await page.click('.export-dialog .el-radio:has-text("Excel")')

      // 开始导出（不实际下载，只验证请求）
      const downloadPromise = page.waitForEvent('download')
      await page.click('.export-dialog .el-button--primary:has-text("导出")')

      // 验证导出成功消息
      await expect(page.locator('.el-message--success')).toContainText(
        '导出成功'
      )

      // 验证文件下载
      const download = await downloadPromise
      expect(download.suggestedFilename()).toContain('work-hours')
      expect(download.suggestedFilename()).toMatch(/\.(xlsx|xls)$/)
    })

    // 步骤12: 清理测试数据
    await test.step('清理测试数据', async () => {
      // 返回任务管理页面
      await page.click('text=任务管理')
      await page.waitForURL('**/tasks')

      // 找到测试任务并删除
      const taskRow = page
        .locator('.task-table tbody tr')
        .filter({
          hasText: testTask.title
        })
        .first()

      // 点击删除按钮
      await taskRow.locator('text=删除').click()

      // 确认删除
      await expect(page.locator('.el-message-box')).toBeVisible()
      await page.click('.el-message-box .el-button--primary:has-text("确定")')

      // 验证删除成功
      await expect(page.locator('.el-message--success')).toContainText(
        '删除成功'
      )

      // 验证任务不再存在于列表中
      await page.waitForTimeout(1000)
      const taskCount = await page
        .locator('.task-table tbody tr')
        .filter({
          hasText: testTask.title
        })
        .count()
      expect(taskCount).toBe(0)
    })

    // 步骤13: 退出登录
    await test.step('退出登录', async () => {
      // 点击用户头像或用户菜单
      await page.click('.user-menu')

      // 点击退出登录
      await page.click('text=退出登录')

      // 验证返回到登录页面
      await page.waitForURL('**/login')
      await expect(page.locator('form')).toBeVisible()
      await expect(page.locator('text=考勤管理系统')).toBeVisible()
    })
  })

  test('错误处理：网络异常情况', async () => {
    // 模拟网络异常
    await page.route('**/api/**', route => {
      route.abort('failed')
    })

    await page.goto('http://localhost:3000/login')

    // 尝试登录
    await page.fill('input[type="text"]', testUser.username)
    await page.fill('input[type="password"]', testUser.password)
    await page.click('button[type="submit"]')

    // 验证错误消息显示
    await expect(page.locator('.el-message--error')).toContainText(
      '网络连接失败'
    )
  })

  test('表单验证：输入验证测试', async () => {
    await page.goto('http://localhost:3000/login')

    // 测试空表单提交
    await page.click('button[type="submit"]')

    // 验证验证错误显示
    await expect(page.locator('.el-form-item.is-error')).toHaveCount(2)

    // 测试用户名长度验证
    await page.fill('input[type="text"]', 'ab')
    await page.blur('input[type="text"]')

    // 验证用户名长度错误
    await expect(page.locator('.el-form-item.is-error')).toBeVisible()

    // 测试密码长度验证
    await page.fill('input[type="password"]', '123')
    await page.blur('input[type="password"]')

    // 验证密码长度错误
    await expect(page.locator('.el-form-item.is-error')).toBeVisible()
  })

  test('响应式设计：移动设备适配', async () => {
    // 设置移动设备视窗
    await page.setViewportSize({ width: 375, height: 667 })

    await page.goto('http://localhost:3000/login')

    // 验证移动端布局
    await expect(page.locator('.login-container')).toHaveCSS('padding', '20px')

    // 验证表单在移动端的样式
    const form = page.locator('form')
    await expect(form).toBeVisible()

    // 验证按钮在移动端的样式
    const submitButton = page.locator('button[type="submit"]')
    await expect(submitButton).toHaveCSS('width', '100%')
  })

  test('无障碍访问：键盘导航', async () => {
    await page.goto('http://localhost:3000/login')

    // 使用Tab键导航
    await page.press('body', 'Tab')
    await expect(page.locator('input[type="text"]')).toBeFocused()

    await page.press('body', 'Tab')
    await expect(page.locator('input[type="password"]')).toBeFocused()

    await page.press('body', 'Tab')
    await expect(page.locator('input[type="checkbox"]')).toBeFocused()

    await page.press('body', 'Tab')
    await expect(page.locator('button[type="submit"]')).toBeFocused()

    // 测试Enter键提交
    await page.fill('input[type="text"]', testUser.username)
    await page.fill('input[type="password"]', testUser.password)
    await page.press('input[type="password"]', 'Enter')

    // 验证表单提交
    await expect(page.locator('button[type="submit"]')).toHaveAttribute(
      'loading',
      'true'
    )
  })
})
