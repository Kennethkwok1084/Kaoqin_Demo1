# Pre-commit Hooks 设置指南

本项目已配置 pre-commit hooks，可以在每次提交前自动运行代码格式化和检查工具。

## 功能特性

✅ **自动代码格式化**
- **Black**: Python 代码自动格式化
- **isort**: Python 导入语句自动排序

✅ **基础文件检查**
- 移除行尾空白字符
- 确保文件以换行符结尾
- YAML 文件语法检查
- JSON 文件语法检查
- 检查合并冲突标记
- 检查大文件（>1MB）

## 安装和使用

### 1. 安装 pre-commit

```bash
# 如果还没有安装
python -m pip install pre-commit
```

### 2. 安装 hooks

```bash
# 在项目根目录运行
python -m pre_commit install
```

### 3. 验证安装

```bash
# 手动运行所有 hooks
python -m pre_commit run --all-files

# 只运行特定 hook
python -m pre_commit run black
python -m pre_commit run isort
```

## 工作流程

### 正常提交流程

1. **编写代码**（不需要手动格式化）
2. **添加文件到暂存区**
   ```bash
   git add .
   ```
3. **提交代码**
   ```bash
   git commit -m "你的提交信息"
   ```
4. **自动格式化**：pre-commit 会自动运行
   - 如果代码需要格式化，hooks 会自动修改文件
   - 提交会被阻止，需要重新添加修改后的文件
5. **重新提交**（如果需要）
   ```bash
   git add .
   git commit -m "你的提交信息"
   ```

### 示例工作流程

```bash
# 1. 编写代码（故意使用不规范格式）
echo 'def test(a,b):return a+b' > backend/example.py

# 2. 添加并提交
git add backend/example.py
git commit -m "添加示例函数"

# 3. pre-commit 自动运行，格式化代码
# 输出：black....................................Failed
# 文件被自动格式化为：def test(a, b): return a + b

# 4. 重新添加格式化后的文件
git add backend/example.py
git commit -m "添加示例函数"

# 5. 提交成功！
```

## 配置文件

配置文件位于 `.pre-commit-config.yaml`，包含以下主要配置：

- **Black**: 行长度 88 字符
- **isort**: 与 Black 兼容的配置
- **文件范围**: 仅处理 `backend/` 目录下的 Python 文件
- **排除目录**: 自动排除缓存、日志等目录

## 跳过 hooks（不推荐）

如果在特殊情况下需要跳过 pre-commit 检查：

```bash
# 跳过所有 hooks
git commit -m "紧急修复" --no-verify

# 跳过特定 hook
SKIP=black git commit -m "跳过 black 检查"
```

## 故障排除

### 常见问题

1. **权限错误**
   ```bash
   # 使用 python -m 方式运行
   python -m pre_commit install
   ```

2. **Hook 失败**
   ```bash
   # 查看详细错误信息
   python -m pre_commit run --all-files --verbose
   ```

3. **更新 hooks**
   ```bash
   # 更新到最新版本
   python -m pre_commit autoupdate
   ```

4. **清理缓存**
   ```bash
   # 清理 pre-commit 缓存
   python -m pre_commit clean
   ```

### 卸载

```bash
# 卸载 pre-commit hooks
python -m pre_commit uninstall
```

## 团队协作

### 新团队成员设置

1. 克隆项目后立即运行：
   ```bash
   python -m pip install pre-commit
   python -m pre_commit install
   ```

2. 验证设置：
   ```bash
   python -m pre_commit run --all-files
   ```

### CI/CD 集成

项目的 CI/CD 流程也会运行相同的检查，确保代码质量一致性。

## 好处

✅ **自动化**: 无需手动运行格式化工具
✅ **一致性**: 团队代码风格统一
✅ **质量**: 提交前自动检查常见问题
✅ **效率**: 减少 CI/CD 中的格式化错误
✅ **习惯**: 培养良好的代码提交习惯

---

**注意**: 首次设置后，建议运行 `python -m pre_commit run --all-files` 来格式化现有代码。
