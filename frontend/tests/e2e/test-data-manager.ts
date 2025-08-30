import { APIRequestContext } from '@playwright/test'

export interface TestUser {
  username: string
  password: string
  email: string
  full_name: string
  is_superuser?: boolean
}

export interface TestTask {
  title: string
  description: string
  location: string
  reporter_name: string
  reporter_phone: string
  priority: 'low' | 'medium' | 'high'
  task_type: 'repair' | 'maintenance' | 'cleaning'
}

export class TestDataManager {
  constructor(private apiContext: APIRequestContext) {}

  // 获取认证token
  async getAuthToken(username: string, password: string): Promise<string> {
    const response = await this.apiContext.post(
      'http://localhost:8000/api/v1/auth/login',
      {
        data: {
          username,
          password
        }
      }
    )

    if (!response.ok()) {
      throw new Error(`Login failed: ${response.status()}`)
    }

    const data = await response.json()
    return data.access_token
  }

  // 创建测试用户
  async createTestUser(user: TestUser): Promise<void> {
    try {
      const response = await this.apiContext.post(
        'http://localhost:8000/api/v1/auth/register',
        {
          data: user
        }
      )

      if (response.ok()) {
        console.log(`✅ Created test user: ${user.username}`)
      } else if (response.status() === 400) {
        console.log(`ℹ️ Test user already exists: ${user.username}`)
      } else {
        console.warn(
          `⚠️ Failed to create user ${user.username}: ${response.status()}`
        )
      }
    } catch (error) {
      console.warn(`⚠️ Error creating user ${user.username}:`, error)
    }
  }

  // 创建测试任务
  async createTestTask(
    task: TestTask,
    authToken: string
  ): Promise<string | null> {
    try {
      const response = await this.apiContext.post(
        'http://localhost:8000/api/v1/tasks/',
        {
          headers: {
            Authorization: `Bearer ${authToken}`
          },
          data: task
        }
      )

      if (response.ok()) {
        const data = await response.json()
        console.log(`✅ Created test task: ${task.title}`)
        return data.id
      } else {
        console.warn(`⚠️ Failed to create task: ${response.status()}`)
        return null
      }
    } catch (error) {
      console.warn(`⚠️ Error creating task:`, error)
      return null
    }
  }

  // 清理测试数据
  async cleanupTestData(): Promise<void> {
    try {
      // 获取管理员token
      const adminToken = await this.getAuthToken('admin', 'admin123')

      // 删除测试任务
      await this.deleteTestTasks(adminToken)

      // 删除测试用户(除了admin)
      await this.deleteTestUsers(adminToken)

      console.log('🧹 Test data cleanup completed')
    } catch (error) {
      console.warn('⚠️ Test data cleanup failed:', error)
    }
  }

  // 删除测试任务
  private async deleteTestTasks(authToken: string): Promise<void> {
    try {
      const response = await this.apiContext.get(
        'http://localhost:8000/api/v1/tasks/',
        {
          headers: {
            Authorization: `Bearer ${authToken}`
          }
        }
      )

      if (response.ok()) {
        const tasks = await response.json()
        for (const task of tasks) {
          if (task.title.includes('测试')) {
            await this.apiContext.delete(
              `http://localhost:8000/api/v1/tasks/${task.id}`,
              {
                headers: {
                  Authorization: `Bearer ${authToken}`
                }
              }
            )
          }
        }
      }
    } catch (error) {
      console.warn('⚠️ Error deleting test tasks:', error)
    }
  }

  // 删除测试用户
  private async deleteTestUsers(authToken: string): Promise<void> {
    try {
      const testUsernames = ['testuser', 'testuser2', 'demo_user']

      for (const username of testUsernames) {
        try {
          await this.apiContext.delete(
            `http://localhost:8000/api/v1/users/${username}`,
            {
              headers: {
                Authorization: `Bearer ${authToken}`
              }
            }
          )
        } catch (error) {
          // 忽略删除失败，用户可能不存在
        }
      }
    } catch (error) {
      console.warn('⚠️ Error deleting test users:', error)
    }
  }

  // 初始化标准测试数据
  async initializeStandardTestData(): Promise<void> {
    const testUsers: TestUser[] = [
      {
        username: 'admin',
        password: 'admin123',
        email: 'admin@example.com',
        full_name: '系统管理员',
        is_superuser: true
      },
      {
        username: 'testuser',
        password: 'testpass123',
        email: 'test@example.com',
        full_name: '测试用户'
      }
    ]

    // 创建测试用户
    for (const user of testUsers) {
      await this.createTestUser(user)
    }

    // 创建测试任务
    try {
      const adminToken = await this.getAuthToken('admin', 'admin123')

      const testTasks: TestTask[] = [
        {
          title: '测试维修任务',
          description: 'E2E测试用的维修任务',
          location: '测试地点A',
          reporter_name: '测试报告人',
          reporter_phone: '13800138000',
          priority: 'medium',
          task_type: 'repair'
        },
        {
          title: '测试维护任务',
          description: 'E2E测试用的维护任务',
          location: '测试地点B',
          reporter_name: '测试报告人2',
          reporter_phone: '13800138001',
          priority: 'high',
          task_type: 'maintenance'
        }
      ]

      for (const task of testTasks) {
        await this.createTestTask(task, adminToken)
      }
    } catch (error) {
      console.warn('⚠️ Failed to create test tasks:', error)
    }
  }
}
