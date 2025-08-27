#!/usr/bin/env node

/**
 * 前端测试运行脚本
 * 支持不同类型的测试运行和报告生成
 */

const { spawn } = require('child_process')
const fs = require('fs')
const path = require('path')
const chalk = require('chalk')

class TestRunner {
  constructor() {
    this.testResults = {
      unit: null,
      component: null,
      e2e: null,
      coverage: null
    }
    this.startTime = Date.now()
  }

  log(message, type = 'info') {
    const timestamp = new Date().toLocaleTimeString()
    const colors = {
      info: chalk.blue,
      success: chalk.green,
      warning: chalk.yellow,
      error: chalk.red
    }

    console.log(`[${timestamp}] ${colors[type]('●')} ${message}`)
  }

  async runCommand(command, options = {}) {
    this.log(`执行命令: ${command}`)

    return new Promise((resolve, reject) => {
      const child = spawn('npm', ['run', ...command.split(' ')], {
        stdio: options.silent ? 'pipe' : 'inherit',
        shell: true,
        cwd: process.cwd()
      })

      let stdout = ''
      let stderr = ''

      if (options.silent) {
        child.stdout.on('data', data => {
          stdout += data.toString()
        })

        child.stderr.on('data', data => {
          stderr += data.toString()
        })
      }

      child.on('close', code => {
        if (code === 0) {
          resolve({ code, stdout, stderr })
        } else {
          reject({ code, stdout, stderr, command })
        }
      })
    })
  }

  async runUnitTests() {
    this.log('开始运行单元测试...', 'info')

    try {
      const result = await this.runCommand('test:unit:coverage', {
        silent: true
      })
      this.testResults.unit = {
        success: true,
        output: result.stdout,
        duration: this.getDuration()
      }
      this.log('单元测试完成 ✓', 'success')
    } catch (error) {
      this.testResults.unit = {
        success: false,
        error: error.stderr || error.stdout,
        duration: this.getDuration()
      }
      this.log('单元测试失败 ✗', 'error')
    }
  }

  async runComponentTests() {
    this.log('开始运行组件测试...', 'info')

    try {
      const result = await this.runCommand('test:component --coverage', {
        silent: true
      })
      this.testResults.component = {
        success: true,
        output: result.stdout,
        duration: this.getDuration()
      }
      this.log('组件测试完成 ✓', 'success')
    } catch (error) {
      this.testResults.component = {
        success: false,
        error: error.stderr || error.stdout,
        duration: this.getDuration()
      }
      this.log('组件测试失败 ✗', 'error')
    }
  }

  async runE2ETests() {
    this.log('开始运行端到端测试...', 'info')

    try {
      // 检查服务器是否运行
      const isServerRunning = await this.checkServerHealth()
      if (!isServerRunning) {
        this.log('检测到服务器未运行，尝试启动...', 'warning')
        await this.startDevServer()
      }

      const result = await this.runCommand('test:e2e', { silent: true })
      this.testResults.e2e = {
        success: true,
        output: result.stdout,
        duration: this.getDuration()
      }
      this.log('端到端测试完成 ✓', 'success')
    } catch (error) {
      this.testResults.e2e = {
        success: false,
        error: error.stderr || error.stdout,
        duration: this.getDuration()
      }
      this.log('端到端测试失败 ✗', 'error')
    }
  }

  async checkServerHealth() {
    try {
      const response = await fetch('http://localhost:3000/')
      return response.ok
    } catch {
      return false
    }
  }

  async startDevServer() {
    this.log('启动开发服务器...', 'info')

    spawn('npm', ['run', 'dev'], {
      stdio: 'pipe',
      shell: true,
      detached: true
    })

    // 等待服务器启动
    return new Promise(resolve => {
      const checkServer = async () => {
        if (await this.checkServerHealth()) {
          this.log('开发服务器启动成功', 'success')
          resolve(true)
        } else {
          setTimeout(checkServer, 1000)
        }
      }

      setTimeout(checkServer, 3000)
    })
  }

  async generateCoverageReport() {
    this.log('生成覆盖率报告...', 'info')

    try {
      const unitCoverage = this.readCoverageFile(
        'coverage/coverage-summary.json'
      )
      const componentCoverage = this.readCoverageFile(
        'tests/coverage/coverage-summary.json'
      )

      this.testResults.coverage = {
        unit: unitCoverage,
        component: componentCoverage,
        combined: this.combineCoverage(unitCoverage, componentCoverage)
      }

      this.log('覆盖率报告生成完成', 'success')
    } catch (error) {
      this.log('生成覆盖率报告失败', 'error')
    }
  }

  readCoverageFile(filePath) {
    try {
      const fullPath = path.join(process.cwd(), filePath)
      if (fs.existsSync(fullPath)) {
        return JSON.parse(fs.readFileSync(fullPath, 'utf8'))
      }
    } catch (error) {
      this.log(`读取覆盖率文件失败: ${filePath}`, 'warning')
    }
    return null
  }

  combineCoverage(unitCoverage, componentCoverage) {
    if (!unitCoverage || !componentCoverage) return null

    const combined = {
      lines: { pct: 0 },
      statements: { pct: 0 },
      functions: { pct: 0 },
      branches: { pct: 0 }
    }

    ;['lines', 'statements', 'functions', 'branches'].forEach(metric => {
      const unitPct = unitCoverage.total?.[metric]?.pct || 0
      const componentPct = componentCoverage.total?.[metric]?.pct || 0
      combined[metric].pct = Math.round((unitPct + componentPct) / 2)
    })

    return { total: combined }
  }

  generateHTMLReport() {
    const reportPath = path.join(
      process.cwd(),
      'tests/reports/test-report.html'
    )
    const reportDir = path.dirname(reportPath)

    if (!fs.existsSync(reportDir)) {
      fs.mkdirSync(reportDir, { recursive: true })
    }

    const html = this.buildHTMLReport()
    fs.writeFileSync(reportPath, html, 'utf8')

    this.log(`HTML报告已生成: ${reportPath}`, 'success')
    return reportPath
  }

  buildHTMLReport() {
    const totalDuration = Date.now() - this.startTime
    const passedTests = Object.values(this.testResults).filter(
      r => r?.success
    ).length
    const totalTests = Object.values(this.testResults).filter(
      r => r !== null
    ).length

    return `
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>前端测试报告</title>
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, sans-serif; margin: 0; padding: 20px; }
        .header { background: #f8f9fa; padding: 20px; border-radius: 8px; margin-bottom: 20px; }
        .summary { display: flex; gap: 20px; margin-bottom: 20px; }
        .metric { background: white; padding: 15px; border-radius: 8px; flex: 1; border: 1px solid #e0e0e0; }
        .test-section { background: white; border-radius: 8px; padding: 20px; margin-bottom: 20px; border: 1px solid #e0e0e0; }
        .success { color: #28a745; }
        .error { color: #dc3545; }
        .coverage-bar { background: #e0e0e0; height: 20px; border-radius: 10px; overflow: hidden; }
        .coverage-fill { height: 100%; background: #28a745; transition: width 0.3s ease; }
        pre { background: #f8f9fa; padding: 10px; border-radius: 4px; overflow-x: auto; }
    </style>
</head>
<body>
    <div class="header">
        <h1>前端测试报告</h1>
        <p>生成时间: ${new Date().toLocaleString()}</p>
        <p>总耗时: ${Math.round(totalDuration / 1000)}秒</p>
    </div>

    <div class="summary">
        <div class="metric">
            <h3>测试概览</h3>
            <p>通过: <span class="success">${passedTests}</span> / ${totalTests}</p>
            <p>成功率: ${totalTests > 0 ? Math.round((passedTests / totalTests) * 100) : 0}%</p>
        </div>
        ${this.buildCoverageMetric()}
    </div>

    ${this.buildTestSection('unit', '单元测试')}
    ${this.buildTestSection('component', '组件测试')}
    ${this.buildTestSection('e2e', '端到端测试')}
</body>
</html>`
  }

  buildCoverageMetric() {
    const coverage = this.testResults.coverage?.combined
    if (!coverage) return ''

    const linesPct = coverage.total?.lines?.pct || 0

    return `
        <div class="metric">
            <h3>代码覆盖率</h3>
            <div class="coverage-bar">
                <div class="coverage-fill" style="width: ${linesPct}%"></div>
            </div>
            <p>${linesPct}% 行覆盖率</p>
        </div>`
  }

  buildTestSection(type, title) {
    const result = this.testResults[type]
    if (!result) return ''

    const statusClass = result.success ? 'success' : 'error'
    const statusIcon = result.success ? '✓' : '✗'

    return `
    <div class="test-section">
        <h2 class="${statusClass}">${statusIcon} ${title}</h2>
        <p>耗时: ${result.duration}ms</p>
        ${
          result.success
            ? `<pre>${this.extractTestSummary(result.output)}</pre>`
            : `<pre class="error">${result.error}</pre>`
        }
    </div>`
  }

  extractTestSummary(output) {
    // 提取测试输出的关键信息
    const lines = output.split('\n')
    const summary = lines
      .filter(
        line =>
          line.includes('Test Files') ||
          line.includes('Tests') ||
          line.includes('passed') ||
          line.includes('failed') ||
          line.includes('Duration')
      )
      .join('\n')

    return summary || '测试完成'
  }

  getDuration() {
    return Date.now() - this.startTime
  }

  async run(testType = 'all') {
    this.log(`开始运行 ${testType} 测试`, 'info')

    switch (testType) {
      case 'unit':
        await this.runUnitTests()
        break
      case 'component':
        await this.runComponentTests()
        break
      case 'e2e':
        await this.runE2ETests()
        break
      case 'all':
        await this.runUnitTests()
        await this.runComponentTests()
        await this.runE2ETests()
        break
      default:
        this.log(`未知的测试类型: ${testType}`, 'error')
        process.exit(1)
    }

    await this.generateCoverageReport()
    const reportPath = this.generateHTMLReport()

    this.printSummary()

    return {
      results: this.testResults,
      reportPath,
      success: Object.values(this.testResults).every(r => !r || r.success)
    }
  }

  printSummary() {
    console.log('\n' + '='.repeat(50))
    console.log(chalk.bold('测试总结'))
    console.log('='.repeat(50))

    Object.entries(this.testResults).forEach(([type, result]) => {
      if (!result) return

      const status = result.success
        ? chalk.green('✓ 通过')
        : chalk.red('✗ 失败')
      const duration = chalk.gray(`(${result.duration}ms)`)

      console.log(`${type.padEnd(12)} ${status} ${duration}`)
    })

    const totalTime = Date.now() - this.startTime
    console.log(`\n总耗时: ${Math.round(totalTime / 1000)}秒`)
    console.log('='.repeat(50) + '\n')
  }
}

// 命令行参数处理
const testType = process.argv[2] || 'all'
const runner = new TestRunner()

runner
  .run(testType)
  .then(({ success, reportPath }) => {
    console.log(chalk.green(`\n报告已生成: ${reportPath}`))
    process.exit(success ? 0 : 1)
  })
  .catch(error => {
    console.error(chalk.red('测试运行失败:'), error)
    process.exit(1)
  })

module.exports = TestRunner
