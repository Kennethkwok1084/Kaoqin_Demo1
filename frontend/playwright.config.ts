import { defineConfig, devices } from '@playwright/test'

/**
 * @see https://playwright.dev/docs/test-configuration
 */
export default defineConfig({
  testDir: './tests/e2e',

  /* Run tests in files in parallel */
  fullyParallel: true,

  /* Fail the build on CI if you accidentally left test.only in the source code. */
  forbidOnly: !!process.env.CI,

  /* Retry on CI only - 优化重试策略 */
  retries: process.env.CI ? 2 : 0,

  /* Opt out of parallel tests on CI - 优化并发控制 */
  workers: process.env.CI ? 2 : 3,

  /* Reporter to use. See https://playwright.dev/docs/test-reporters */
  reporter: [
    ['html', { open: 'never' }],
    ['json', { outputFile: 'test-results/results.json' }],
    ['junit', { outputFile: 'test-results/results.xml' }],
    ['line']
  ],

  /* Shared settings for all the projects below. See https://playwright.dev/docs/api/class-testoptions. */
  use: {
    /* Base URL to use in actions like `await page.goto('/')`. */
    baseURL: 'http://localhost:3000',

    /* Collect trace when retrying the failed test. See https://playwright.dev/docs/trace-viewer */
    trace: 'on-first-retry',

    /* Take screenshot on failure */
    screenshot: 'only-on-failure',

    /* Record video on failure */
    video: 'retain-on-failure',

    /* Timeout for each action */
    actionTimeout: 15000,

    /* Timeout for navigation */
    navigationTimeout: 30000,

    /* 使用预设的认证状态 */
    storageState: 'tests/fixtures/auth-state.json'
  },

  /* Configure projects for major browsers - 优化为Firefox + Chromium组合 */
  projects: [
    // 设置测试 - 不使用认证状态
    {
      name: 'setup',
      testMatch: /.*\.setup\.ts/,
      use: {
        ...devices['Desktop Chrome'],
        storageState: undefined // 设置阶段不使用认证状态
      }
    },
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
      dependencies: ['setup']
    },
    {
      name: 'firefox',
      use: { ...devices['Desktop Firefox'] },
      dependencies: ['setup']
    }
  ],

  /* Run your local dev server before starting the tests */
  webServer: {
    command: 'npm run dev',
    url: 'http://localhost:3000',
    reuseExistingServer: !process.env.CI,
    timeout: 180 * 1000, // 增加到3分钟等待前端启动
    stdout: 'pipe',
    stderr: 'pipe'
  },

  /* Global setup and teardown */
  globalSetup: './tests/e2e/global-setup.ts',
  globalTeardown: './tests/e2e/global-teardown.ts',

  /* Timeout settings - 增加超时时间 */
  timeout: 90 * 1000, // 单个测试90秒超时
  expect: {
    timeout: 10 * 1000
  },

  /* Output directory for test artifacts */
  outputDir: 'test-results/',

  /* Test metadata */
  metadata: {
    author: 'E2E Test Suite',
    description: '考勤管理系统端到端测试'
  }
})
