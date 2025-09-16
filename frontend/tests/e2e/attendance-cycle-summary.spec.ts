import { test, expect } from '@playwright/test'

test.describe('考勤周期汇总（任务口径）页面', () => {
  test('打开工时管理并切换周期', async ({ page }) => {
    // 假设已设置全局登录（可复用现有 e2e 全局登录方案），否则先导航到登录并登录
    await page.goto('/attendance')

    // 页面标题与导出按钮
    await expect(page.locator('h1.page-title')).toHaveText(/考勤管理（任务口径）/)
    await expect(page.getByRole('button', { name: '导出考勤数据' })).toBeVisible()

    // 切换周期选择为按月
    await page.getByRole('combobox').first().click()
    await page.getByRole('option', { name: '按月' }).click()

    // 月份选择器应存在
    await expect(page.locator('.el-date-editor--month')).toBeVisible()

    // 切换为自定义周期
    await page.getByRole('combobox').first().click()
    await page.getByRole('option', { name: '自定义' }).click()
    await expect(page.locator('.el-date-editor--daterange')).toBeVisible()

    // 列表表格可见
    await expect(page.locator('.el-table')).toBeVisible()
  })
})

