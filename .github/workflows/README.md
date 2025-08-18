# CI/CD工作流程说明

## 修复内容

### GitHub Actions版本升级
- ✅ `actions/upload-artifact` v3 → v4 (修复弃用警告)
- ✅ `actions/setup-python` v4 → v5
- ✅ `actions/cache` v3 → v4
- ✅ `codecov/codecov-action` v3 → v4 (添加token支持)
- ✅ `docker/build-push-action` v5 → v6

### 前端测试改进
- ✅ 移除pnpm依赖，使用npm (更标准)
- ✅ 添加Playwright依赖安装
- ✅ 改进Node.js缓存配置
- ✅ 添加项目文件检查

### 工作流程优化
- ✅ 添加超时时间 (防止作业无限运行)
- ✅ 设置`fail-fast: false` (允许其他版本继续测试)
- ✅ 添加artifacts保留天数 (30-90天)
- ✅ 改进Docker多架构构建支持

### 错误处理改进
- ✅ 添加条件检查 (文件存在性)
- ✅ 改进错误消息
- ✅ 更好的依赖管理

## 工作流程概述

### 1. 后端测试 (backend-test)
- Python 3.12 & 3.13矩阵测试
- PostgreSQL & Redis服务
- 代码检查 (black, isort, flake8, mypy)
- 单元测试 & 集成测试
- 性能基准测试
- 覆盖率上传到Codecov

### 2. 前端测试 (frontend-test)
- Node.js 18
- ESLint & TypeScript检查
- 单元测试 & 组件测试
- Playwright E2E测试
- 构建验证

### 3. 安全扫描 (security-scan)
- 依赖漏洞检查 (safety)
- 代码安全扫描 (bandit)
- 安全报告生成

### 4. 冒烟测试 (smoke-test)
- 端到端系统测试
- 真实环境验证
- API健康检查

### 5. 构建部署 (build-and-deploy)
- Docker镜像构建
- 多架构支持 (amd64/arm64)
- 分环境部署

### 6. 通知 (notification)
- 成功/失败状态通知
- 可扩展到Slack/Teams

## 触发条件

- **Push**: `main`, `develop` 分支
- **Pull Request**: 目标为 `main`, `develop` 分支

## Artifacts保留

- 测试结果: 30天
- 安全报告: 90天
- 性能基准: 30天
- 冒烟测试: 30天

## 环境变量需求

### Secrets
- `DOCKER_USERNAME`: Docker Hub用户名
- `DOCKER_PASSWORD`: Docker Hub密码
- `CODECOV_TOKEN`: Codecov上传token

### 环境变量
- `DATABASE_URL`: 数据库连接URL
- `REDIS_URL`: Redis连接URL
- `ENVIRONMENT`: 环境标识
- `TESTING`: 测试模式标识

## 使用指南

1. **本地测试**
   ```bash
   # 后端
   cd backend && pytest

   # 前端
   cd frontend && npm test
   ```

2. **手动触发**
   - GitHub Actions页面手动运行
   - 或推送代码到指定分支

3. **查看结果**
   - Actions页面查看详细日志
   - 下载artifacts查看报告
   - Codecov查看覆盖率
