import { defineConfig } from 'vitest/config'
import vue from '@vitejs/plugin-vue'
import { resolve } from 'path'

export default defineConfig({
  plugins: [vue()],

  resolve: {
    alias: {
      '@': resolve(__dirname, 'src'),
      '@components': resolve(__dirname, 'src/components'),
      '@views': resolve(__dirname, 'src/views'),
      '@stores': resolve(__dirname, 'src/stores'),
      '@api': resolve(__dirname, 'src/api'),
      '@utils': resolve(__dirname, 'src/utils'),
      '@types': resolve(__dirname, 'src/types'),
      '@assets': resolve(__dirname, 'src/assets')
    }
  },

  // 强制Mock映射
  server: {
    fs: {
      allow: [resolve(__dirname, '..')]
    }
  },

  css: {
    preprocessorOptions: {
      scss: {
        api: 'modern-compiler', // 使用现代Sass API，避免弃用警告
        additionalData:
          '@use "@/styles/variables.scss" as *; @use "@/styles/mixins.scss" as *;'
      }
    }
  },

  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: ['./tests/setup.ts'], // 使用优化后的setup文件
    // 关键修复：CSS处理
    css: {
      modules: {
        classNameStrategy: 'non-scoped'
      }
    },
    // 启用手动Mock支持
    deps: {
      external: [/^@\/api\/statistics$/]
    },
    coverage: {
      provider: 'v8',
      reporter: ['text', 'json', 'html'],
      exclude: [
        'node_modules/',
        'tests/',
        'dist/',
        '**/*.d.ts',
        '**/*.config.*',
        'src/main.ts'
      ]
    },
    include: [
      'tests/unit/**/*.{test,spec}.{js,mjs,cjs,ts,mts,cts,jsx,tsx}',
      'src/**/__tests__/**/*.{test,spec}.{js,mjs,cjs,ts,mts,cts,jsx,tsx}'
    ],
    // 优化：排除node_modules提高速度
    exclude: [
      '**/node_modules/**',
      '**/dist/**',
      '.idea/',
      '.git/',
      '.cache/'
    ],
    // 测试超时设置
    testTimeout: 10000,
    // 优化并发性能
    pool: 'forks',
    poolOptions: {
      forks: {
        singleFork: false
      }
    }
  }
})
