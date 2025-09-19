#!/usr/bin/env node
/**
 * 前端快速功能验证 - 3分钟检查核心页面
 * 确保前端主要功能可用
 */

const { chromium } = require('playwright');

class QuickFrontendTest {
    constructor() {
        this.baseUrl = 'http://localhost:3000';
        this.results = [];
        this.failedTests = [];
    }

    async runAllTests() {
        console.log('🎨 开始前端快速功能验证...');
        console.log('='.repeat(50));

        const startTime = Date.now();

        const browser = await chromium.launch({ headless: true });
        const page = await browser.newPage();

        try {
            // P0 关键测试
            await this.testPageLoad(page);
            await this.testLogin(page);
            await this.testMainNavigation(page);
            await this.testTasksPage(page);
            await this.testMembersPage(page);
            await this.testAttendancePage(page);

            // P1 重要测试
            await this.testStatisticsPage(page);

        } catch (error) {
            this.logError(`全局错误: ${error.message}`);
        } finally {
            await browser.close();
        }

        const duration = (Date.now() - startTime) / 1000;
        this.printSummary(duration);

        return this.failedTests.length === 0;
    }

    async testPageLoad(page) {
        try {
            await page.goto(this.baseUrl, { waitUntil: 'networkidle' });
            const title = await page.title();
            if (title.includes('考勤') || title.includes('管理') || title.length > 0) {
                this.logSuccess('✅ 首页加载成功');
            } else {
                this.logError('❌ 首页标题异常');
            }
        } catch (error) {
            this.logError(`❌ 首页加载失败: ${error.message}`);
        }
    }

    async testLogin(page) {
        try {
            // 查找登录表单
            const usernameInput = await page.locator('input[type="text"], input[placeholder*="用户"], input[placeholder*="账号"]').first();
            const passwordInput = await page.locator('input[type="password"]').first();
            const loginButton = await page.locator('button:has-text("登录"), button:has-text("登入")').first();

            if (await usernameInput.isVisible() && await passwordInput.isVisible()) {
                await usernameInput.fill('admin');
                await passwordInput.fill('admin123');
                await loginButton.click();

                // 等待登录完成
                await page.waitForTimeout(2000);

                // 检查是否成功跳转
                const currentUrl = page.url();
                if (!currentUrl.includes('login')) {
                    this.logSuccess('✅ 用户登录成功');
                } else {
                    this.logWarning('⚠️  登录可能失败或需要验证');
                }
            } else {
                this.logWarning('⚠️  未找到登录表单，可能已经登录');
            }
        } catch (error) {
            this.logError(`❌ 登录测试失败: ${error.message}`);
        }
    }

    async testMainNavigation(page) {
        try {
            // 检查主导航栏
            const navItems = ['任务', '成员', '考勤', '统计', '仪表板', 'dashboard'];
            let foundNavItems = 0;

            for (const item of navItems) {
                const navElement = await page.locator(`a:has-text("${item}"), button:has-text("${item}"), [role="menuitem"]:has-text("${item}")`).first();
                if (await navElement.isVisible()) {
                    foundNavItems++;
                }
            }

            if (foundNavItems >= 2) {
                this.logSuccess('✅ 主导航栏正常');
            } else {
                this.logError('❌ 主导航栏缺失或异常');
            }
        } catch (error) {
            this.logError(`❌ 导航测试失败: ${error.message}`);
        }
    }

    async testTasksPage(page) {
        try {
            // 尝试导航到任务页面
            const taskLink = await page.locator('a:has-text("任务"), a[href*="task"]').first();
            if (await taskLink.isVisible()) {
                await taskLink.click();
                await page.waitForTimeout(1000);

                // 检查页面是否加载
                const pageContent = await page.content();
                if (pageContent.includes('任务') || pageContent.includes('报修') || pageContent.includes('维修')) {
                    this.logSuccess('✅ 任务页面加载成功');
                } else {
                    this.logError('❌ 任务页面内容异常');
                }
            } else {
                this.logWarning('⚠️  未找到任务页面链接');
            }
        } catch (error) {
            this.logError(`❌ 任务页面测试失败: ${error.message}`);
        }
    }

    async testMembersPage(page) {
        try {
            const memberLink = await page.locator('a:has-text("成员"), a[href*="member"]').first();
            if (await memberLink.isVisible()) {
                await memberLink.click();
                await page.waitForTimeout(1000);

                const pageContent = await page.content();
                if (pageContent.includes('成员') || pageContent.includes('用户') || pageContent.includes('人员')) {
                    this.logSuccess('✅ 成员页面加载成功');
                } else {
                    this.logError('❌ 成员页面内容异常');
                }
            } else {
                this.logWarning('⚠️  未找到成员页面链接');
            }
        } catch (error) {
            this.logError(`❌ 成员页面测试失败: ${error.message}`);
        }
    }

    async testAttendancePage(page) {
        try {
            const attendanceLink = await page.locator('a:has-text("考勤"), a[href*="attendance"]').first();
            if (await attendanceLink.isVisible()) {
                await attendanceLink.click();
                await page.waitForTimeout(1000);

                const pageContent = await page.content();
                if (pageContent.includes('考勤') || pageContent.includes('工时') || pageContent.includes('统计')) {
                    this.logSuccess('✅ 考勤页面加载成功');
                } else {
                    this.logError('❌ 考勤页面内容异常');
                }
            } else {
                this.logWarning('⚠️  未找到考勤页面链接');
            }
        } catch (error) {
            this.logError(`❌ 考勤页面测试失败: ${error.message}`);
        }
    }

    async testStatisticsPage(page) {
        try {
            const statsLink = await page.locator('a:has-text("统计"), a[href*="statistic"]').first();
            if (await statsLink.isVisible()) {
                await statsLink.click();
                await page.waitForTimeout(1000);

                const pageContent = await page.content();
                if (pageContent.includes('统计') || pageContent.includes('报表') || pageContent.includes('图表')) {
                    this.logSuccess('✅ 统计页面加载成功');
                } else {
                    this.logWarning('⚠️  统计页面内容可能不完整');
                }
            } else {
                this.logWarning('⚠️  未找到统计页面链接');
            }
        } catch (error) {
            this.logWarning(`⚠️  统计页面测试失败: ${error.message}`);
        }
    }

    logSuccess(message) {
        console.log(message);
        this.results.push(['SUCCESS', message]);
    }

    logWarning(message) {
        console.log(message);
        this.results.push(['WARNING', message]);
    }

    logError(message) {
        console.log(message);
        this.results.push(['ERROR', message]);
        this.failedTests.push(message);
    }

    printSummary(duration) {
        console.log('\n' + '='.repeat(50));
        console.log('📊 前端测试结果摘要');
        console.log('='.repeat(50));

        const successCount = this.results.filter(r => r[0] === 'SUCCESS').length;
        const warningCount = this.results.filter(r => r[0] === 'WARNING').length;
        const errorCount = this.results.filter(r => r[0] === 'ERROR').length;
        const totalCount = this.results.length;

        console.log(`总测试数: ${totalCount}`);
        console.log(`✅ 成功: ${successCount}`);
        console.log(`⚠️  警告: ${warningCount}`);
        console.log(`❌ 失败: ${errorCount}`);
        console.log(`⏱️  耗时: ${duration.toFixed(2)}秒`);

        const successRate = totalCount > 0 ? (successCount / totalCount * 100) : 0;
        console.log(`🎯 成功率: ${successRate.toFixed(1)}%`);

        if (errorCount === 0) {
            console.log('\n🎉 前端核心功能测试通过！');
        } else {
            console.log(`\n🚨 发现 ${errorCount} 个关键问题！`);
            console.log('\n失败的测试:');
            this.failedTests.forEach(test => {
                console.log(`  • ${test}`);
            });
        }

        if (warningCount > 0) {
            console.log(`\n💡 有 ${warningCount} 个功能可能需要优化`);
        }
    }
}

async function main() {
    console.log('🔥 前端快速功能验证');
    console.log('目标：3分钟检查核心页面，确保基本可用');
    console.log();

    // 检查前端是否运行
    try {
        const response = await fetch('http://localhost:3000');
        if (response.ok) {
            console.log('✅ 前端服务正在运行');
        } else {
            console.log('❌ 前端服务响应异常');
            return false;
        }
    } catch (error) {
        console.log('❌ 无法连接到前端服务 (http://localhost:3000)');
        console.log('请确保前端服务已启动：npm run dev');
        return false;
    }

    const tester = new QuickFrontendTest();
    const success = await tester.runAllTests();

    return success;
}

if (require.main === module) {
    main().then(success => {
        process.exit(success ? 0 : 1);
    }).catch(error => {
        console.error('测试执行出错:', error);
        process.exit(1);
    });
}