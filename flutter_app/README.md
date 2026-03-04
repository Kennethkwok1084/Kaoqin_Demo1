# Flutter 客户端开发规范

> 参考文档：`docs/flutter/flutter_development_guidelines.md`、`docs/reports/flutter-migration-strategy-2026-02-25.md`

## 快速开始

### 环境要求
- Flutter SDK >= 3.19.0
- Dart SDK >= 3.3.0

### 安装 Flutter（Linux/macOS）
```bash
# 使用 snap（Ubuntu）
sudo snap install flutter --classic
flutter doctor

# 或使用 FVM（多版本管理）
dart pub global activate fvm
fvm install stable && fvm use stable
```

### 初始化项目
```bash
cd flutter_app
flutter pub get
dart run build_runner build -d   # 生成 .g.dart / .freezed.dart 文件
```

### 运行
```bash
flutter run                      # 连接设备/模拟器
flutter run -d chrome            # Web 端
flutter run -d linux             # Linux 桌面端
flutter run -d windows           # Windows 桌面端（需 Windows 机器）
```

### 代码生成（修改模型/Provider/API 后必须执行）
```bash
dart run build_runner build -d
# 或监听模式（开发期间持续生成）
dart run build_runner watch -d
```

---

## 目录结构

```
flutter_app/
├── lib/
│   ├── main.dart                    # 应用入口
│   ├── core/
│   │   ├── api/
│   │   │   ├── api_client.dart      # Retrofit 客户端定义（对应所有后端接口）
│   │   │   ├── api_providers.dart   # ApiClient Provider
│   │   │   ├── dio_factory.dart     # Dio 实例 + Token 拦截器 + 刷新逻辑
│   │   │   └── storage_service.dart # Token 安全存储（flutter_secure_storage）
│   │   ├── constants/
│   │   │   ├── app_constants.dart   # API 路径、存储 Key、超时配置
│   │   │   └── app_colors.dart      # 颜色 + 尺寸常量
│   │   ├── errors/
│   │   │   └── app_exceptions.dart  # 全局异常类型体系
│   │   ├── router/
│   │   │   └── app_router.dart      # go_router 路由配置
│   │   ├── theme/
│   │   │   └── app_theme.dart       # Cupertino 主题
│   │   └── utils/
│   │       └── responsive_helper.dart  # 响应式断点 + 日期工具
│   ├── features/
│   │   ├── auth/                    # 认证模块
│   │   │   ├── domain/user_model.dart
│   │   │   ├── data/auth_repository.dart
│   │   │   └── presentation/
│   │   │       ├── auth_controller.dart
│   │   │       └── pages/
│   │   │           ├── login_page.dart
│   │   │           └── splash_page.dart
│   │   ├── tasks/                   # 报修/任务模块
│   │   │   ├── domain/task_model.dart
│   │   │   ├── data/task_repository.dart
│   │   │   └── presentation/
│   │   │       ├── tasks_controller.dart
│   │   │       └── pages/
│   │   │           ├── task_list_page.dart
│   │   │           ├── task_detail_page.dart
│   │   │           └── create_task_page.dart
│   │   ├── work_hours/              # 工时模块
│   │   │   ├── domain/work_hours_model.dart
│   │   │   ├── data/work_hours_repository.dart
│   │   │   └── presentation/pages/work_hours_page.dart
│   │   └── admin/                   # 管理员专属模块
│   │       ├── data/admin_repository.dart
│   │       └── presentation/pages/
│   │           ├── admin_dashboard_page.dart
│   │           └── admin_members_page.dart
│   └── shared/
│       └── widgets/
│           ├── app_shell.dart        # 导航壳（Mobile 底部 Tab / Desktop 侧边栏）
│           ├── task_card.dart        # 任务卡片
│           ├── status_badge.dart     # 状态徽标
│           ├── empty_state.dart      # 空状态
│           └── error_state.dart      # 错误状态
├── pubspec.yaml
└── analysis_options.yaml
```

---

## 架构说明

### 技术选型
| 层次 | 技术 |
|------|------|
| UI | Flutter + **Cupertino** 风格 |
| 状态管理 | **Riverpod** + Riverpod Generator |
| 路由 | **go_router** |
| 网络 | **Dio** + **Retrofit**（强类型 API 客户端） |
| 数据模型 | **Freezed** + json_serializable |
| 安全存储 | flutter_secure_storage |
| 图表 | fl_chart |

### 多端适配策略
- **Mobile (< 600px)**：底部 `CupertinoTabBar` 导航。
- **Tablet / Web (600–1200px)** 和 **Desktop (> 1200px)**：侧边栏导航（`_SideNavShell`）。
- 由 `ResponsiveBuilder` 和 `ResponsiveHelper` 根据 `MediaQuery` 自动切换。

### 角色权限
- **User / Leader**：任务相关功能 + 个人工时。
- **Admin**：额外拥有「管理概览」和「成员管理」Tab/菜单项。

### Token 生命周期
1. 登录 → 保存 `access_token` + `refresh_token` 到安全存储。
2. 每次请求由 `_AuthInterceptor` 自动注入 Bearer Token。
3. 401 时自动用 refreshToken 换新 Token 并重发原请求。
4. refresh 失败 → 清除存储 → 跳转登录页。

---

## 下一步（阶段 0 剩余工作）

- [ ] 运行 `dart run build_runner build -d` 生成所有 `.g.dart` / `.freezed.dart` 文件
- [ ] 配置 `lib/core/constants/app_constants.dart` 中的 `prodBaseUrl`
- [ ] 针对 iOS/Android 配置 `flutter_secure_storage` 所需权限
- [ ] 针对桌面端配置 `file_selector` 权限（macOS entitlements）
- [ ] 添加 `assets/images/` 目录下的 Logo 图片
- [ ] 编写各模块单元测试（`test/` 目录）
