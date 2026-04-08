# Flutter 客户端重构与多端适配方案（2026-02-25）

## 1. 战略定位与目标

基于“跨设备适配、各端功能差异化”的战略方向，决定**全新开发一套 Flutter 客户端**，最终目标是完全替代现有的 Vue 前端。

### 1.1 端侧定位矩阵

| 端侧 | 核心定位 | 主要功能范围 | 目标用户 |
|------|----------|--------------|----------|
| **Mobile (iOS/Android)** | 敏捷业务处理与移动管理 | **Users**: 报修单登记、任务接单/处理、个人工时查看<br>**Admin**: 移动端轻量管理、任务审批/指派 | 一线成员 (Users) / 管理员 (Admin) |
| **Desktop (Windows/macOS)** | 深度管理与操作 | **Admin 专属**: 复杂任务分配、数据导入/导出、成员管理、全量统计报表 | 管理员 (Admin) |
| **Web (Browser)** | 轻量看板与弱管理 | **Admin 专属**: 数据大屏展示、基础任务浏览、临时访问 | 管理员 (Admin) |

> **注**：本项目**不包含**传统的“考勤打卡/定位签到”功能，核心围绕“工时计算与任务流转”展开。Desktop 和 Web 端暂时仅对 Admin 角色开放。

### 1.2 核心优势（为什么选 Flutter）
- **统一身份认证**：移动端/桌面端可利用系统级安全存储（Keychain/Keystore）管理 Token，比 Web 端 LocalStorage 更安全。
- **硬件能力调用**：移动端扫码（如设备资产码）；桌面端本地文件系统直接读写（Excel 导入导出）。
- **代码复用率**：预计核心业务逻辑（网络、状态、模型）复用率可达 90% 以上，UI 层复用率 60-70%（通过响应式布局）。

---

## 2. 架构设计与技术选型

### 2.1 基础选型
- **状态管理**：`Riverpod`（强类型、编译时安全，适合复杂多端状态）
- **路由管理**：`go_router`（官方推荐，支持 Web URL 深度链接和嵌套路由）
- **网络请求**：`Dio` + `retrofit`（强类型 API 客户端生成）
- **本地存储**：`flutter_secure_storage`（Token） + `shared_preferences`（普通配置）
- **数据序列化**：`json_serializable` + `freezed`（不可变状态模型）
- **图表库**：`fl_chart`（基础图表） + `webview_flutter`（复杂 ECharts 降级方案）

### 2.2 多端适配架构 (Responsive Design)

采用 **"单一代码库，多态 UI"** 策略：

```dart
// 核心响应式断点设计
enum ScreenType { mobile, tablet, desktop }

ScreenType getScreenType(BuildContext context) {
  double width = MediaQuery.of(context).size.width;
  if (width < 600) return ScreenType.mobile;
  if (width < 1200) return ScreenType.tablet;
  return ScreenType.desktop;
}
```

**UI 适配策略**：
- **Mobile (Users/Admin)**：底部导航栏 (BottomNavigationBar) + 堆叠式页面
- **Tablet/Web (Admin)**：侧边导航栏 (NavigationRail) + 分栏布局
- **Desktop (Admin)**：顶部菜单/复杂侧边栏 + 多窗口/弹窗支持

### 2.3 平台能力隔离 (Platform Channels)

通过接口隔离不同平台的特有能力：

```dart
abstract class PlatformService {
  Future<void> exportExcel(List<Task> tasks);
  Future<String?> scanQRCode();
}

// 移动端实现：调用摄像头
// 桌面端实现：不支持或调用外接扫码枪
// Web端实现：不支持
```

---

## 3. 实施阶段与里程碑

### 阶段 0：基础设施与工程骨架（约 2 周）
*目标：搭建可运行的多端空壳，打通网络与鉴权。*
- [ ] 初始化 Flutter 工程，配置多环境（Dev/Prod）。
- [ ] 搭建 Riverpod + go_router 基础架构。
- [ ] 实现 Dio 网络层封装（Token 拦截、刷新、统一错误处理）。
- [ ] 实现登录/登出逻辑，打通安全存储。
- [ ] 建立响应式布局基类（ResponsiveBuilder）。

### 阶段 1：移动端核心业务 MVP（约 3 周）
*目标：一线成员 (Users) 可以处理日常任务，管理员 (Admin) 可进行移动端轻量管理。*
- [ ] 移动端主框架（底部导航，根据角色动态渲染 Tab）。
- [ ] **Users**: 仪表板（个人今日任务、本月工时概览）。
- [ ] **Users**: 报修单登记、任务列表（报修/协助/监控）与基础筛选。
- [ ] **Users**: 任务详情与状态流转操作（接单、完成）、个人工时明细查看。
- [ ] **Admin**: 移动端任务指派、审批、异常工时快速处理。

### 阶段 2：桌面端/Web 端管理能力（约 4 周）
*目标：管理员 (Admin) 可以脱离 Vue 后台，在 PC 端完成深度管理工作。*
- [ ] 桌面端/Web 端主框架（侧边栏布局，**仅 Admin 可登录/访问**）。
- [ ] 复杂表格组件封装（支持排序、宽屏展示）。
- [ ] 成员管理模块（增删改查、角色分配）。
- [ ] 数据导入/导出模块（对接桌面端文件系统）。
- [ ] 统计报表模块（集成图表，大屏展示优化）。

### 阶段 3：双端并行与 Vue 下线（约 2 周）
*目标：平滑过渡，最终下线历史包袱。*
- [ ] 灰度发布：部分团队试用 Flutter 客户端。
- [ ] 收集反馈，修复多端兼容性 Bug。
- [ ] 补齐缺失的边缘功能。
- [ ] 正式停用 Vue 前端，后端移除对 Vue 的静态资源托管（如有）。

---

## 4. 关键风险与应对策略

### 4.1 图表渲染差异
- **风险**：Flutter 原生图表库（如 `fl_chart`）在复杂交互（如数据下钻、复杂 Tooltip）上弱于 ECharts。
- **应对**：常规折线/柱状图使用 `fl_chart` 保证性能；对于复杂的统计大屏（Web/Desktop 端），考虑使用 `webview_flutter` 嵌入轻量级 HTML 页面加载 ECharts 作为降级方案。

### 4.2 Web 端性能与体验
- **风险**：Flutter Web (CanvasKit) 首次加载体积大（约 2-5MB），且文本选择、右键菜单体验不如原生 HTML。
- **应对**：明确 Web 端定位为“弱管理/看板”，不追求极致的 C 端加载速度。对于强管理需求，引导用户下载 Desktop 客户端。

### 4.3 桌面端文件操作
- **风险**：Flutter 桌面端的文件选择、拖拽上传生态相对移动端较弱。
- **应对**：引入成熟的桌面端插件（如 `file_selector`, `desktop_drop`），并在阶段 0 提前进行技术验证（Spike）。

---

## 5. 下一步行动建议

1. **确认 API 契约**：在开始阶段 0 前，确保后端 API（特别是刚修复的 P0 算法相关接口）已稳定，并输出最新的 OpenAPI 文档。
2. **UI/UX 规范统一**：由于从 Vue(Element Plus) 迁移到 Flutter(Material/Cupertino)，需要定义一套新的多端设计规范（颜色、排版、组件风格）。
3. **创建 Flutter 仓库/目录**：在项目中新建 `flutter_app` 目录，开始阶段 0 的工程初始化。