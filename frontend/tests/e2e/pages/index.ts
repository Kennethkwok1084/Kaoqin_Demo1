import { Page, Locator, expect } from '@playwright/test'

export class LoginPage {
  readonly page: Page
  readonly usernameInput: Locator
  readonly passwordInput: Locator
  readonly loginButton: Locator
  readonly loginForm: Locator
  readonly errorMessage: Locator

  constructor(page: Page) {
    this.page = page
    this.usernameInput = page.locator('input[type="text"]')
    this.passwordInput = page.locator('input[type="password"]')
    this.loginButton = page.locator('button[type="submit"]')
    this.loginForm = page.locator('form')
    this.errorMessage = page.locator('.error-message')
  }

  async goto() {
    await this.page.goto('/login')
  }

  async login(username: string, password: string) {
    await this.usernameInput.fill(username)
    await this.passwordInput.fill(password)
    await this.loginButton.click()
  }

  async expectLoginForm() {
    await expect(this.loginForm).toBeVisible()
    await expect(this.usernameInput).toBeVisible()
    await expect(this.passwordInput).toBeVisible()
    await expect(this.loginButton).toBeVisible()
  }

  async expectErrorMessage() {
    await expect(this.errorMessage).toBeVisible()
  }
}

export class DashboardPage {
  readonly page: Page
  readonly dashboardContainer: Locator
  readonly userInfo: Locator
  readonly navigationMenu: Locator
  readonly tasksMenuItem: Locator
  readonly membersMenuItem: Locator
  readonly reportsMenuItem: Locator

  constructor(page: Page) {
    this.page = page
    this.dashboardContainer = page.locator('.dashboard-container')
    this.userInfo = page.locator('.user-info')
    this.navigationMenu = page.locator('.navigation-menu')
    this.tasksMenuItem = page.locator('text=任务管理')
    this.membersMenuItem = page.locator('text=成员管理')
    this.reportsMenuItem = page.locator('text=报告管理')
  }

  async expectDashboard() {
    await expect(this.dashboardContainer).toBeVisible()
    await expect(this.userInfo).toBeVisible()
  }

  async navigateToTasks() {
    await this.tasksMenuItem.click()
    await this.page.waitForURL('**/tasks')
  }

  async navigateToMembers() {
    await this.membersMenuItem.click()
    await this.page.waitForURL('**/members')
  }

  async navigateToReports() {
    await this.reportsMenuItem.click()
    await this.page.waitForURL('**/reports')
  }
}

export class TasksPage {
  readonly page: Page
  readonly taskList: Locator
  readonly createTaskButton: Locator
  readonly taskForm: Locator
  readonly titleInput: Locator
  readonly descriptionInput: Locator
  readonly locationInput: Locator
  readonly reporterNameInput: Locator
  readonly reporterPhoneInput: Locator
  readonly prioritySelect: Locator
  readonly taskTypeSelect: Locator
  readonly submitButton: Locator
  readonly cancelButton: Locator

  constructor(page: Page) {
    this.page = page
    this.taskList = page.locator('.task-list')
    this.createTaskButton = page.locator('text=新建任务')
    this.taskForm = page.locator('.task-form')
    this.titleInput = page.locator('input[placeholder*="标题"]')
    this.descriptionInput = page.locator('textarea[placeholder*="描述"]')
    this.locationInput = page.locator('input[placeholder*="地点"]')
    this.reporterNameInput = page.locator('input[placeholder*="报告人"]')
    this.reporterPhoneInput = page.locator('input[placeholder*="电话"]')
    this.prioritySelect = page.locator('select[name="priority"]')
    this.taskTypeSelect = page.locator('select[name="task_type"]')
    this.submitButton = page.locator('button[type="submit"]:has-text("提交")')
    this.cancelButton = page.locator('button:has-text("取消")')
  }

  async expectTasksPage() {
    await expect(this.taskList).toBeVisible()
    await expect(this.createTaskButton).toBeVisible()
  }

  async createNewTask() {
    await this.createTaskButton.click()
    await expect(this.taskForm).toBeVisible()
  }

  async fillTaskForm(task: {
    title: string
    description: string
    location: string
    reporterName: string
    reporterPhone: string
    priority: string
    taskType: string
  }) {
    await this.titleInput.fill(task.title)
    await this.descriptionInput.fill(task.description)
    await this.locationInput.fill(task.location)
    await this.reporterNameInput.fill(task.reporterName)
    await this.reporterPhoneInput.fill(task.reporterPhone)
    await this.prioritySelect.selectOption(task.priority)
    await this.taskTypeSelect.selectOption(task.taskType)
  }

  async submitTask() {
    await this.submitButton.click()
  }

  async cancelTask() {
    await this.cancelButton.click()
  }

  async expectTaskInList(taskTitle: string) {
    await expect(this.page.locator(`.task-item:has-text("${taskTitle}")`)).toBeVisible()
  }
}
