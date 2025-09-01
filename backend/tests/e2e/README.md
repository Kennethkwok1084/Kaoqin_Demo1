# 考勤管理系统 E2E 测试套件

这是考勤管理系统的完整端到端测试套件，涵盖了系统的所有核心业务流程和功能模块。

## 📁 测试文件结构

```
tests/e2e/
├── conftest.py                              # E2E测试配置和夹具
├── test_user_authentication_flow.py         # 用户认证流程测试
├── test_repair_task_lifecycle.py           # 报修单生命周期测试  
├── test_assistance_task_management.py      # 协助任务管理测试
├── test_attendance_data_management.py      # 考勤数据管理测试
├── test_system_settings_and_permissions.py # 系统设置和权限测试
├── test_statistics_and_reports.py          # 统计报表测试
├── run_e2e_tests.py                        # E2E测试运行脚本
├── README.md                               # 本文档
└── results/                                # 测试结果目录
```

## 🧪 测试覆盖范围

### 1. 用户认证流程测试 (`test_user_authentication_flow.py`)
- **完整注册登录流程**: 用户注册、登录、token获取
- **多用户角色认证**: 学生网管、组长、管理员、超级管理员
- **JWT令牌管理**: token刷新、过期处理、权限验证
- **权限控制验证**: 基于角色的访问控制(RBAC)
- **密码管理**: 密码修改、强度验证、安全策略
- **并发会话**: 多用户并发访问、会话管理
- **认证性能**: 登录性能、权限检查性能

### 2. 报修单生命周期测试 (`test_repair_task_lifecycle.py`)
- **A/B表数据导入**: Excel文件解析、数据匹配、批量导入
- **任务创建分配**: 报修任务创建、自动分配、手动分配
- **任务处理流程**: 学生接单、进度更新、任务完成
- **线下任务标记**: 现场图片上传、完成证明、用户确认
- **工时计算验证**: 自动工时计算、奖励惩罚、批量重算
- **状态流转验证**: 任务状态转换规则、流程合规性
- **任务评价反馈**: 用户评价、满意度统计、反馈处理
- **搜索筛选功能**: 任务查询、条件筛选、排序功能

### 3. 协助任务管理测试 (`test_assistance_task_management.py`)
- **学生自主登记**: 协助任务申请、技能匹配、时间安排
- **管理员审核流程**: 申请审批、拒绝处理、批量审核
- **任务执行管理**: 任务开始、进度跟踪、完成确认
- **工时统计计算**: 协助任务工时、奖励计算、统计分析
- **通知提醒系统**: 申请通知、审批通知、状态提醒
- **排行榜统计**: 协助任务排名、贡献统计、激励机制

### 4. 考勤数据管理测试 (`test_attendance_data_management.py`)
- **月度工时统计**: 自动月结、工时汇总、数据完整性
- **批量数据处理**: 全员批量计算、并发处理、性能优化
- **Excel数据导出**: 4个工作表导出、格式验证、数据准确性
- **月度结转逻辑**: 上月数据结转、累计统计、历史追溯
- **考勤记录CRUD**: 记录增删改查、数据验证、权限控制
- **统计分析功能**: 趋势分析、对比统计、异常检测
- **数据完整性检查**: 一致性验证、错误修复、数据清理

### 5. 系统设置和权限测试 (`test_system_settings_and_permissions.py`)
- **工时规则配置**: 超级管理员修改规则、实时生效验证
- **系统参数管理**: 配置更新、缓存刷新、参数验证
- **权限矩阵验证**: 角色权限检查、访问控制、安全测试
- **用户角色管理**: 角色分配、权限变更、级联影响
- **系统维护模式**: 维护开关、用户限制、功能隔离
- **审计日志监控**: 操作记录、安全监控、异常告警
- **数据备份恢复**: 备份权限、数据保护、恢复测试
- **安全策略配置**: 密码策略、登录限制、IP控制

### 6. 统计报表测试 (`test_statistics_and_reports.py`)
- **仪表盘概览**: 实时统计、关键指标、数据可视化
- **任务性能分析**: 完成率分析、响应时间、类型分布
- **成员绩效排名**: 工时排行、任务排名、综合评分
- **地理区域分析**: 区域分布、热力图、效率对比
- **词云分析**: 任务描述、用户反馈、问题分类
- **时间序列分析**: 趋势分析、季节性、工作负载
- **高级数据导出**: 多格式导出、图表生成、报告定制
- **自定义仪表盘**: 个性化配置、组件管理、布局设计
- **统计警报系统**: 阈值监控、异常告警、规则管理

## 🚀 快速开始

### 环境要求

- Python 3.12+
- PostgreSQL 或 SQLite（测试环境）
- 所有项目依赖已安装

### 安装测试依赖

```bash
# 使用uv安装
uv sync

# 或使用pip安装
pip install -r requirements-dev.txt
```

### 运行测试

#### 1. 使用测试运行脚本（推荐）

```bash
# 运行所有E2E测试
python tests/e2e/run_e2e_tests.py

# 运行指定模块
python tests/e2e/run_e2e_tests.py -m test_user_authentication_flow.py test_repair_task_lifecycle.py

# 详细输出模式
python tests/e2e/run_e2e_tests.py -v

# 遇到失败停止
python tests/e2e/run_e2e_tests.py -s

# 检查环境
python tests/e2e/run_e2e_tests.py -c

# 列出所有模块
python tests/e2e/run_e2e_tests.py -l
```

#### 2. 使用pytest直接运行

```bash
# 运行所有E2E测试
pytest tests/e2e/ -v

# 运行指定测试文件
pytest tests/e2e/test_user_authentication_flow.py -v

# 运行指定测试类
pytest tests/e2e/test_user_authentication_flow.py::TestUserAuthenticationFlow -v

# 运行指定测试方法
pytest tests/e2e/test_user_authentication_flow.py::TestUserAuthenticationFlow::test_complete_user_registration_and_login_flow -v
```

#### 3. 并行执行（提升性能）

```bash
# 使用pytest-xdist并行执行
pytest tests/e2e/ -n auto

# 指定并行进程数
pytest tests/e2e/ -n 4
```

## 📊 测试结果

测试执行完成后，结果文件保存在 `tests/e2e/results/` 目录：

- `e2e_test_results_YYYYMMDD_HHMMSS.json` - 详细测试结果（JSON格式）
- `e2e_test_report_YYYYMMDD_HHMMSS.txt` - 测试报告（文本格式）
- `*_results.xml` - JUnit格式结果文件
- `*_results.json` - pytest-json-report格式结果

### 结果文件示例

```json
{
  "start_time": "2024-01-30T10:00:00",
  "end_time": "2024-01-30T10:15:00",
  "total_duration": 900.5,
  "summary": {
    "total_modules": 6,
    "passed_modules": 6,
    "failed_modules": 0,
    "total_tests": 45,
    "passed_tests": 42,
    "failed_tests": 0,
    "skipped_tests": 3
  },
  "test_modules": [...]
}
```

## 🔧 测试配置

### 环境变量

```bash
# 强制使用SQLite进行测试
export FORCE_SQLITE_TESTS=true

# 启用测试模式
export TESTING=true

# 启用E2E测试模式
export E2E_TESTING=true

# 设置测试密钥
export SECRET_KEY=e2e-test-secret-key
```

### 数据库配置

E2E测试使用独立的测试数据库配置，默认使用SQLite以确保测试隔离和速度。

配置文件位置：`tests/database_config.py`

### 测试数据

E2E测试使用以下测试夹具：

- **测试用户**: 学生、组长、管理员、超级管理员各角色用户
- **样本任务**: 不同状态和类型的报修任务
- **考勤记录**: 历史考勤数据用于统计测试
- **系统配置**: 模拟的系统参数和规则

## 🐛 常见问题

### 1. 数据库连接失败

```bash
# 检查数据库配置
python -c "from tests.database_config import test_config; print(test_config.test_database_url)"

# 确保测试数据库权限正确
# PostgreSQL: GRANT ALL PRIVILEGES ON DATABASE test_db TO test_user;
```

### 2. 异步测试问题

```bash
# 确保使用正确的asyncio模式
pytest tests/e2e/ --asyncio-mode=auto
```

### 3. 权限测试失败

```bash
# 检查用户角色是否正确创建
# 查看测试日志确认用户创建和认证流程
pytest tests/e2e/test_user_authentication_flow.py -v -s
```

### 4. 导入导出测试跳过

某些功能可能尚未实现，测试会被跳过。这是正常现象，表示：
- 功能接口存在但返回404（未实现）
- 功能逻辑需要完善
- 测试发现了需要开发的功能点

### 5. 性能测试超时

```bash
# 调整性能测试阈值
# 在相应的测试文件中修改assert语句的时间限制
```

## 📈 测试监控和CI/CD集成

### GitHub Actions集成

```yaml
name: E2E Tests
on: [push, pull_request]
jobs:
  e2e-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.12'
      - name: Install dependencies
        run: |
          pip install uv
          uv sync
      - name: Run E2E tests
        run: |
          python tests/e2e/run_e2e_tests.py --verbose
      - name: Upload test results
        uses: actions/upload-artifact@v3
        with:
          name: e2e-test-results
          path: tests/e2e/results/
```

### 测试覆盖率

```bash
# 生成覆盖率报告
pytest tests/e2e/ --cov=app --cov-report=html --cov-report=xml

# 查看覆盖率
open htmlcov/index.html
```

## 🤝 贡献指南

### 添加新的E2E测试

1. **确定测试范围**: 明确需要测试的业务流程
2. **创建测试类**: 遵循现有的命名和结构约定
3. **编写测试用例**: 包含正常流程、异常处理、性能验证
4. **添加测试数据**: 在`conftest.py`中添加必要的夹具
5. **更新文档**: 在本README中更新测试覆盖范围

### 测试编写规范

```python
class TestNewFeature:
    """新功能E2E测试类"""
    
    @pytest.mark.asyncio
    async def test_complete_workflow(
        self,
        e2e_client: AsyncClient,
        e2e_user_tokens: Dict[str, str],
        e2e_auth_headers,
        e2e_helper
    ):
        """测试完整的业务工作流程"""
        
        # 1. 准备测试数据
        # 2. 执行业务操作
        # 3. 验证结果
        # 4. 清理测试数据（如需要）
```

### 性能测试规范

```python
@pytest.mark.asyncio
async def test_feature_performance(
    self,
    e2e_performance_monitor,
    e2e_helper
):
    """测试功能性能"""
    
    e2e_performance_monitor.start()
    
    # 执行性能测试
    for i in range(10):
        start_time = asyncio.get_event_loop().time()
        # 执行操作
        duration = asyncio.get_event_loop().time() - start_time
        e2e_performance_monitor.record(f"operation_{i}", duration)
    
    # 性能断言
    summary = e2e_performance_monitor.summary()
    assert summary["average_time"] < 1.0
```

## 📞 支持和反馈

如果在运行E2E测试过程中遇到问题，请：

1. **检查环境**: 运行 `python tests/e2e/run_e2e_tests.py -c`
2. **查看日志**: 使用 `-v` 参数获取详细输出
3. **检查结果**: 查看 `results/` 目录中的测试报告
4. **提交Issue**: 包含错误信息、环境配置、复现步骤

---

**注意**: E2E测试设计为独立运行，不依赖外部服务。所有测试数据都是临时创建的，测试完成后会自动清理。