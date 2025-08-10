# 脚本使用说明

本目录包含了考勤管理系统的部署和测试脚本。

## 脚本列表

### 部署脚本

#### `deploy.sh`
完整的部署脚本，支持开发、测试和生产环境。

**使用方法:**
```bash
# 部署到开发环境
./scripts/deploy.sh development

# 部署到生产环境  
./scripts/deploy.sh production latest

# 查看帮助
./scripts/deploy.sh --help
```

**功能:**
- 自动检查依赖
- 备份数据库（生产环境）
- 构建Docker镜像
- 部署服务
- 健康检查

### 测试脚本

#### `e2e_smoke.py`
综合性端到端冒烟测试脚本，包含完整的系统功能验证。

**安装依赖:**
```bash
pip install -r scripts/requirements-smoke.txt
```

**使用方法:**
```bash
# 开发环境测试（自动启动服务）
python scripts/e2e_smoke.py --environment development

# 生产环境测试（假设服务已运行）
python scripts/e2e_smoke.py --environment production --no-start-services

# 详细日志输出
python scripts/e2e_smoke.py --verbose
```

**测试内容:**
- 数据库连接测试
- API健康检查
- 用户认证流程
- 核心API接口
- 前端页面可访问性

#### `quick_smoke.sh`
快速冒烟测试脚本，适用于快速验证系统基本功能。

**使用方法:**
```bash
# 默认配置测试
./scripts/quick_smoke.sh

# 自定义API地址
./scripts/quick_smoke.sh --api-url http://localhost:8080

# 查看帮助
./scripts/quick_smoke.sh --help
```

**测试内容:**
- API健康检查
- API文档访问
- 认证接口响应
- 核心API接口
- 前端页面访问
- 数据库连接（间接）

### CI/CD集成

#### `ci_smoke_test.yml`
GitHub Actions工作流配置，用于在CI/CD流水线中集成冒烟测试。

**集成方法:**
```yaml
# 在主CI文件中引用
jobs:
  deploy:
    # ... 部署步骤

  smoke-test:
    needs: deploy
    uses: ./.github/workflows/ci_smoke_test.yml
    with:
      environment: staging
      api_base_url: https://api-staging.example.com
      frontend_url: https://staging.example.com
```

## 环境配置

### 开发环境
确保以下服务正在运行：
- PostgreSQL (端口 5432)
- Redis (端口 6379) 
- 后端API (端口 8000)
- 前端 (端口 80)

### 生产环境
需要配置以下环境变量：
- `DB_HOST`, `DB_USER`, `DB_PASSWORD`, `DB_NAME`
- `REDIS_PASSWORD`
- `SECRET_KEY`
- `CORS_ORIGINS`

参考 `.env.production.example` 文件。

## 测试结果解释

### 退出码
- `0`: 所有测试通过
- `1`: 测试失败或异常

### 成功标准
- **快速测试**: 至少2/3的测试项目通过
- **综合测试**: 至少80%的测试项目通过

### 日志文件
- `e2e_smoke_test.log`: 详细测试日志
- 控制台输出: 测试进度和结果摘要

## 常见问题

### Q: 测试失败如何排查？
A: 
1. 检查服务是否正常启动: `docker-compose ps`
2. 查看服务日志: `docker-compose logs [service_name]`
3. 检查网络连接: `curl http://localhost:8000/health`
4. 查看详细测试日志: `e2e_smoke_test.log`

### Q: 数据库连接测试失败？
A:
1. 确认PostgreSQL服务运行正常
2. 检查数据库连接配置
3. 验证数据库用户权限
4. 确认防火墙设置

### Q: 前端测试失败？
A:
1. 检查前端服务是否启动
2. 确认端口配置正确
3. 验证前端构建是否成功
4. 检查反向代理配置

### Q: API认证测试失败？
A:
1. 检查JWT配置
2. 确认用户数据库表结构
3. 验证密码哈希算法
4. 检查CORS配置

## 最佳实践

1. **开发阶段**: 使用 `quick_smoke.sh` 进行快速验证
2. **部署前**: 执行完整的 `e2e_smoke.py` 测试
3. **生产部署**: 在CI/CD中集成冒烟测试
4. **定期检查**: 设置定时任务执行冒烟测试
5. **问题排查**: 保留测试日志便于问题分析

## 扩展测试

如需添加新的测试项目：

1. **API测试**: 在 `APISmokeTest` 类中添加新方法
2. **前端测试**: 在 `FrontendSmokeTest` 类中添加新检查
3. **数据库测试**: 在 `DatabaseSmokeTest` 类中添加新验证
4. **快速测试**: 在 `quick_smoke.sh` 中添加新的测试函数