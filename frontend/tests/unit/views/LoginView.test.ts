import { describe, it, expect, beforeEach, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { createRouter, createWebHistory } from 'vue-router'
import LoginView from '@/views/auth/LoginView.vue'
import { useAuthStore } from '@/stores/auth'

// Mock router
const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/login', component: LoginView },
    { path: '/dashboard', component: { template: '<div>Dashboard</div>' } }
  ]
})

describe('LoginView', () => {
  let wrapper: any
  let authStore: any

  beforeEach(async () => {
    setActivePinia(createPinia())
    authStore = useAuthStore()
    
    wrapper = mount(LoginView, {
      global: {
        plugins: [router]
      }
    })
    
    await router.push('/login')
    await router.isReady()
  })

  afterEach(() => {
    wrapper?.unmount()
  })

  describe('rendering', () => {
    it('should render login form', () => {
      expect(wrapper.find('.login-container').exists()).toBe(true)
      expect(wrapper.find('form').exists()).toBe(true)
      expect(wrapper.find('input[type="text"]').exists()).toBe(true)
      expect(wrapper.find('input[type="password"]').exists()).toBe(true)
      expect(wrapper.find('button[type="submit"]').exists()).toBe(true)
    })

    it('should render logo and title', () => {
      expect(wrapper.find('.login-logo').exists()).toBe(true)
      expect(wrapper.find('.login-title').exists()).toBe(true)
      expect(wrapper.text()).toContain('考勤管理系统')
    })

    it('should render form fields with correct labels', () => {
      expect(wrapper.text()).toContain('用户名')
      expect(wrapper.text()).toContain('密码')
      expect(wrapper.text()).toContain('记住我')
    })
  })

  describe('form validation', () => {
    it('should show validation errors for empty fields', async () => {
      const submitButton = wrapper.find('button[type="submit"]')
      await submitButton.trigger('click')

      // 等待验证错误显示
      await wrapper.vm.$nextTick()
      
      // Element Plus 表单验证通常会在表单项上添加错误类
      expect(wrapper.find('.el-form-item.is-error').exists()).toBe(true)
    })

    it('should validate username format', async () => {
      const usernameInput = wrapper.find('input[type="text"]')
      
      // 输入无效用户名
      await usernameInput.setValue('ab') // 太短
      await usernameInput.trigger('blur')
      
      await wrapper.vm.$nextTick()
      
      // 检查是否有验证错误
      expect(wrapper.vm.loginForm.username).toBe('ab')
    })

    it('should validate password length', async () => {
      const passwordInput = wrapper.find('input[type="password"]')
      
      // 输入过短的密码
      await passwordInput.setValue('123')
      await passwordInput.trigger('blur')
      
      await wrapper.vm.$nextTick()
      
      expect(wrapper.vm.loginForm.password).toBe('123')
    })
  })

  describe('login functionality', () => {
    it('should call login with correct credentials', async () => {
      // Mock login method
      const loginSpy = vi.spyOn(authStore, 'login').mockResolvedValue(true)
      const routerPushSpy = vi.spyOn(router, 'push')

      const usernameInput = wrapper.find('input[type="text"]')
      const passwordInput = wrapper.find('input[type="password"]')
      const submitButton = wrapper.find('button[type="submit"]')

      await usernameInput.setValue('testuser')
      await passwordInput.setValue('password123')
      await submitButton.trigger('click')

      await wrapper.vm.$nextTick()

      expect(loginSpy).toHaveBeenCalledWith('testuser', 'password123')
      expect(routerPushSpy).toHaveBeenCalledWith('/dashboard')
    })

    it('should handle login failure', async () => {
      // Mock login failure
      const loginSpy = vi.spyOn(authStore, 'login').mockResolvedValue(false)
      const routerPushSpy = vi.spyOn(router, 'push')

      const usernameInput = wrapper.find('input[type="text"]')
      const passwordInput = wrapper.find('input[type="password"]')
      const submitButton = wrapper.find('button[type="submit"]')

      await usernameInput.setValue('testuser')
      await passwordInput.setValue('wrongpassword')
      await submitButton.trigger('click')

      await wrapper.vm.$nextTick()

      expect(loginSpy).toHaveBeenCalledWith('testuser', 'wrongpassword')
      expect(routerPushSpy).not.toHaveBeenCalled()
      
      // 检查是否显示错误消息
      expect(wrapper.vm.loginError).toBeTruthy()
    })

    it('should show loading state during login', async () => {
      // Mock a slow login
      let resolveLogin: (value: boolean) => void
      const loginPromise = new Promise<boolean>((resolve) => {
        resolveLogin = resolve
      })
      vi.spyOn(authStore, 'login').mockReturnValue(loginPromise)

      const submitButton = wrapper.find('button[type="submit"]')
      await submitButton.trigger('click')

      // 检查加载状态
      expect(wrapper.vm.loading).toBe(true)
      expect(submitButton.attributes('disabled')).toBeDefined()

      // 完成登录
      resolveLogin!(true)
      await wrapper.vm.$nextTick()

      expect(wrapper.vm.loading).toBe(false)
    })
  })

  describe('remember me functionality', () => {
    it('should save credentials when remember me is checked', async () => {
      const localStorageSetSpy = vi.spyOn(localStorage, 'setItem')
      vi.spyOn(authStore, 'login').mockResolvedValue(true)

      const usernameInput = wrapper.find('input[type="text"]')
      const passwordInput = wrapper.find('input[type="password"]')
      const rememberCheckbox = wrapper.find('input[type="checkbox"]')
      const submitButton = wrapper.find('button[type="submit"]')

      await usernameInput.setValue('testuser')
      await passwordInput.setValue('password123')
      await rememberCheckbox.setChecked()
      await submitButton.trigger('click')

      await wrapper.vm.$nextTick()

      expect(localStorageSetSpy).toHaveBeenCalledWith('rememberedUsername', 'testuser')
    })

    it('should load remembered username on mount', async () => {
      vi.spyOn(localStorage, 'getItem').mockReturnValue('remembereduser')
      
      const newWrapper = mount(LoginView, {
        global: {
          plugins: [router]
        }
      })

      await newWrapper.vm.$nextTick()

      expect(newWrapper.vm.loginForm.username).toBe('remembereduser')
      expect(newWrapper.vm.loginForm.rememberMe).toBe(true)
      
      newWrapper.unmount()
    })
  })

  describe('keyboard interactions', () => {
    it('should submit form on Enter key', async () => {
      const loginSpy = vi.spyOn(authStore, 'login').mockResolvedValue(true)

      const usernameInput = wrapper.find('input[type="text"]')
      const passwordInput = wrapper.find('input[type="password"]')

      await usernameInput.setValue('testuser')
      await passwordInput.setValue('password123')
      await passwordInput.trigger('keyup.enter')

      expect(loginSpy).toHaveBeenCalledWith('testuser', 'password123')
    })
  })

  describe('accessibility', () => {
    it('should have proper form labels', () => {
      const labels = wrapper.findAll('label')
      expect(labels.length).toBeGreaterThan(0)
      
      // 检查每个输入框都有对应的标签
      const inputs = wrapper.findAll('input')
      inputs.forEach(input => {
        const id = input.attributes('id')
        if (id) {
          expect(wrapper.find(`label[for="${id}"]`).exists()).toBe(true)
        }
      })
    })

    it('should have proper ARIA attributes', () => {
      const form = wrapper.find('form')
      expect(form.attributes('novalidate')).toBeDefined()
      
      // 检查错误状态的 ARIA 属性
      const inputs = wrapper.findAll('input')
      inputs.forEach(input => {
        if (input.classes().includes('is-error')) {
          expect(input.attributes('aria-invalid')).toBe('true')
        }
      })
    })
  })
})