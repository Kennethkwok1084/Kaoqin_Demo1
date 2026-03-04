# Flutter 客户端开发规范与架构指南

## 1. 技术栈选型
基于多端适配与敏捷开发的战略目标，本项目采用以下核心技术栈：
- **UI 框架**: Flutter (**Cupertino 风格为主**，提供精致的类 iOS 体验)
- **状态管理**: Riverpod + Riverpod Generator (代码生成，强类型安全)
- **路由管理**: go_router (支持 Web URL 深度链接和嵌套路由)
- **网络请求**: Dio + Retrofit (基于 FastAPI OpenAPI 自动生成强类型 API 客户端)
- **数据模型**: Freezed + json_serializable (不可变状态模型与 JSON 序列化)
- **本地存储**: flutter_secure_storage (Token 安全存储) + shared_preferences (普通配置)
- **图表库**: fl_chart (基础图表) + webview_flutter (复杂 ECharts 降级方案)

## 2. 目录结构 (Feature-first)
项目采用按功能模块划分（Feature-first）的目录结构，以提高代码的高内聚和低耦合，非常适合 Riverpod 状态管理。

```text
lib/
├── core/                   # 核心层：跨功能复用的基础代码
│   ├── api/                # Dio 实例配置、拦截器、Retrofit 客户端
│   ├── constants/          # 全局常量（颜色、尺寸、API 路径等）
│   ├── errors/             # 全局异常处理与自定义错误类
│   ├── router/             # go_router 路由配置
│   ├── theme/              # Cupertino 主题配置
│   └── utils/              # 工具类（日期格式化、验证器等）
├── features/               # 功能层：按业务模块划分
│   ├── auth/               # 认证模块 (登录、登出、Token 管理)
│   │   ├── data/           # 数据层：Repositories, Data Sources
│   │   ├── domain/         # 领域层：Models (Freezed), Entities
│   │   └── presentation/   # 表现层：UI (Widgets, Pages), Controllers (Riverpod)
│   ├── tasks/              # 任务模块 (报修、接单、审批)
│   ├── work_hours/         # 工时模块 (个人工时、统计)
│   └── admin/              # 管理员专属模块 (成员管理、数据导出)
├── shared/                 # 共享层：跨功能复用的 UI 组件 (如通用的 Cupertino 按钮、弹窗)
└── main.dart               # 应用入口
```

## 3. UI/UX 规范 (Cupertino 风格)
本项目主要采用 **Cupertino (iOS 风格)** 进行 UI 开发，以提供精致的移动端体验，并在桌面端/Web端保持一致的视觉语言。
- **组件使用**: 优先使用 `CupertinoApp`, `CupertinoPageScaffold`, `CupertinoNavigationBar`, `CupertinoButton` 等 Cupertino 系列组件。
- **响应式布局**: 
  - 移动端 (Mobile): 底部导航栏 (`CupertinoTabBar`) + 堆叠式页面。
  - 平板/Web/桌面端 (Tablet/Desktop): 侧边导航栏 + 分栏布局 (Split View)。
  - 使用 `LayoutBuilder` 或自定义 `ResponsiveBuilder` 根据屏幕宽度 (`MediaQuery`) 动态切换布局。

## 4. 状态管理与数据流 (Riverpod + Freezed)
- **不可变模型**: 所有数据模型必须使用 `@freezed` 注解生成，确保状态的不可变性。
- **代码生成**: 使用 `@riverpod` 注解自动生成 Provider，避免手动编写样板代码。
- **状态分离**: UI 层只负责展示和触发事件，业务逻辑和状态变更必须在 Riverpod 的 `Notifier` 或 `AsyncNotifier` 中处理。

## 5. API 对接规范
- **OpenAPI 驱动**: 后端基于 FastAPI，直接利用其提供的 `/openapi.json` 接口文档。
- **Retrofit 客户端**: 在 `lib/core/api/` 下使用 Retrofit 定义接口，通过 `build_runner` 自动生成 Dio 请求代码。
- **Token 管理**: 在 Dio 拦截器中统一处理 Token 的注入、过期刷新和 401 跳转登录逻辑。

## 6. 多端适配与平台隔离
- **平台通道 (Platform Channels)**: 对于特定平台的功能（如桌面端导出 Excel、移动端扫码），定义抽象接口，并针对不同平台提供具体实现。
- **条件编译**: 使用 `kIsWeb` 或 `Platform.isWindows` 等常量进行平台特定的逻辑分支处理。

## 7. 开发工作流
1. **生成代码**: 每次修改带有 `@freezed`, `@riverpod`, `@RestApi` 注解的文件后，必须运行 `dart run build_runner build -d`。
2. **代码规范**: 遵循 Dart 官方 Linter 规则，提交前确保 `dart analyze` 无警告。
