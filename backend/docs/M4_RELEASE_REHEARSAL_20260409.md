# M4 发布演练与验收记录（2026-04-09）

## 1. 目标
- 验证 M4 出门条件：
  - 认证双读灰度开关与回退链路可用。
  - token 撤销真实性（invalid/revoked/expired）契约稳定。
  - 设备维度登出策略冻结。
  - 核心回归通过。
  - 迁移升降级冒烟通过。

## 2. 本次代码范围
- 双读灰度与埋点：app/api/deps.py
- 认证错误码语义与设备策略：app/api/v1/auth.py
- 全局 HTTP 异常契约透传：app/main.py
- 配置策略：app/core/config.py
- 环境示例：.env.example
- 门禁脚本：scripts/m4_readiness_gate.sh
- 测试补充：tests/core/test_deps.py、tests/core/test_main.py、tests/unit/test_auth_api.py
- docs 基线对齐（phase1）：
  - 模型：app/models/sys_config.py、app/models/building.py、app/models/media_file.py
  - 迁移：alembic/versions/20260409_2200_c4d5e6f7a8b9_align_docs_phase1_foundation_tables.py
  - 启动检查：app/core/startup.py（双轨核心表检测）
  - 测试：tests/integration/test_docs_phase1_schema_alignment.py
- docs 基线对齐（phase2~phase6）：
  - phase2 迁移：alembic/versions/20260409_2330_d5e6f7a8b9c0_align_docs_phase2_governance_workhour_core.py
  - phase3(B3) 迁移：alembic/versions/20260410_0010_e6f7a8b9c0d1_align_docs_phase3_coop_tables.py
  - phase4(B4) 迁移：alembic/versions/20260410_0200_f7a8b9c0d1e2_align_docs_phase4_inspection_tables.py
  - phase5(B5) 迁移：alembic/versions/20260410_0330_08b9c0d1e2f3_align_docs_phase5_sampling_tables.py
  - phase6(B6) 迁移：alembic/versions/20260410_0500_19c0d1e2f304_align_docs_phase6_repair_workhour_entry_tables.py
  - 测试：tests/integration/test_docs_phase2_schema_alignment.py、tests/integration/test_b3_schema_alignment.py、tests/integration/test_b4_schema_alignment.py、tests/integration/test_b5_schema_alignment.py、tests/integration/test_b6_schema_alignment.py

## 3. 策略冻结结果
- 双读策略：
  - `AUTH_APP_USER_READ_FIRST=False`（默认关闭，灰度可开）。
  - 开启后：app_user 优先，members 回退。
- 登出策略：
  - `AUTH_LOGOUT_ALL_DEVICES_DEFAULT=True`（默认全设备登出）。
  - `AUTH_LOGOUT_REQUIRE_DEVICE_ID_WHEN_SINGLE=True`（单设备登出必须 device_id）。
- 错误码语义（已契约化）：
  - TOKEN_INVALID
  - TOKEN_EXPIRED
  - TOKEN_REVOKED
  - DEVICE_ID_REQUIRED
  - LOGOUT_FAILED

## 4. 回归与门禁执行结果
### 4.1 核心回归
执行：`./scripts/m4_readiness_gate.sh`
结果：PASS
- tests/core/test_deps.py 子集：11 passed
- tests/unit/test_auth_api.py 子集：16 passed
- tests/core/test_main.py 子集：2 passed

### 4.2 迁移升降级冒烟
首次执行（复用现有库）失败：
- 原因：现有库与 Alembic 版本历史不一致，`auth_refresh_token` 已存在导致 DuplicateTable。

修复动作：
- 使用本地 PostgreSQL 新建隔离库 `m4_gate`。
- 指定 `DATABASE_URL`/`DATABASE_URL_SYNC` 到 `m4_gate` 后重跑。

执行：
- `RUN_MIGRATION_CHECK=true ./scripts/m4_readiness_gate.sh`
结果：PASS
- upgrade: d1402934c1fc -> a1f2c3d4e5f6 -> b3c4d5e6f7a8
- downgrade: b3c4d5e6f7a8 -> a1f2c3d4e5f6
- upgrade: a1f2c3d4e5f6 -> b3c4d5e6f7a8

## 5. 预发放量建议
1. 在预发先开启 `AUTH_APP_USER_READ_FIRST=true`。
2. 执行认证与鉴权冒烟：登录、刷新、登出、资料更新、改密。
3. 观察双读埋点日志关键事件：
   - app_user_hit
   - app_user_miss
   - app_user_query_error
   - member_fallback_by_id_hit
   - member_fallback_by_student_no_hit
4. 若 24 小时内无异常，再逐步放量到生产。

## 6. 风险与处置
- 风险：旧库可能存在“表已建但版本未记录”情况，导致迁移失败。
- 处置：发布前在预发执行一次“版本对齐检查 + 隔离库冒烟”，必要时使用版本补记策略后再升级。

## 7. 结论
- M4 代码与回归门禁已达成。
- 迁移门禁在隔离库验证通过。
- 可以进入 M5 的联调与发布节奏。

## 8. 基于 docs SQL 的差距证据（当前口径）
- 对比方式：提取 docs SQL 中 `CREATE TABLE IF NOT EXISTS` 与 Alembic `op.create_table` 集合做差集。
- 对比结果：
  - docs 基线表数量：33
  - 当前迁移覆盖表数量：33
  - 说明：数据层已完成 docs SQL 全量迁移覆盖，后续工作聚焦服务/API 与联调闭环。

### 8.1 docs 存在但迁移尚未落地（主要缺口）
- 无（0 张）。

### 8.2 当前迁移存在但 docs 新体系未直接对应（旧体系存量）
- assistance_tasks
- attendance_exceptions
- attendance_records
- members
- monitoring_tasks
- monthly_attendance_summaries
- repair_tasks
- system_configs
- task_tag_associations
- task_tags

## 9. M5 第一批可执行清单（直接开工）
1. 契约收敛：登录/刷新接口完成 camelCase 主契约切换并保留兼容字段，前端按主契约读取。
2. 全链路联调：登录 -> 导入 -> 任务处理 -> 工时结算 -> 统计导出，形成联调记录。
3. 双读灰度放量：预发开启 AUTH_APP_USER_READ_FIRST，按 10% -> 50% -> 100% 观察并放量。
4. 迁移门禁常态化：每次发布前执行 `scripts/full_iteration_gate.sh`，固定使用隔离库进行升降级冒烟。
5. M5 退出标准：
   - 联调链路全通过
   - 回滚演练全通过
   - P0 项 100% 通过，P1 达标

## 10. M5 当前推进状态（2026-04-09）
已落地并验证通过：
1. 双读按比例灰度：
  - 新增 `AUTH_APP_USER_READ_PERCENT`（0-100）用于放量控制。
  - 与 `AUTH_APP_USER_READ_FIRST` 形成“强制开关 + 百分比放量”双控制模式。
2. 双读可观测增强：
  - 新增 `app_user_rollout_selected` / `app_user_rollout_skipped` 观测事件。
  - 可区分“命中 app_user”“回退 members”“按比例跳过”。
3. 认证契约收敛（后端兼容层）：
  - 登录/刷新 token 响应持续输出 snake_case + camelCase。
  - 用户信息在登录/个人资料/verify-token 返回中增加 camelCase 别名字段。
4. docs 基线 phase1 数据层落地：
  - 已新增并迁移：`sys_config`、`building`、`dorm_room`、`media_file`。
  - `auth_refresh_token.user_id` 外键已修正为指向 `app_user.id`。
  - 在隔离库 `phase1_tmp` 完成升级至 `c4d5e6f7a8b9 (head)` 验证。
5. docs 基线 phase2/phase3/phase4 数据层落地：
  - phase2 已新增并迁移：`workhour_rule`、`workhour_tag`、`review_log`、`todo_item`、`biz_operation_log`。
  - phase3(B3) 已新增并迁移：`task_coop`、`task_coop_slot`、`task_coop_signup`、`task_coop_attendance`。
  - phase4(B4) 已新增并迁移：`task_inspection`、`task_inspection_user`、`task_inspection_point`、`inspection_record`。
  - 在隔离库 `kaoqin_test@5433` 完成 `upgrade -> downgrade(e6f7a8b9c0d1) -> upgrade` 可逆验证。
6. docs 基线 phase5(B5) 数据层落地：
  - phase5(B5) 已新增并迁移：`task_sampling`、`task_sampling_user`、`task_sampling_room`、`sampling_record`、`sampling_scan_detail`、`sampling_test_detail`。
  - 在隔离库 `kaoqin_test@5433` 完成 `upgrade -> downgrade(f7a8b9c0d1e2) -> upgrade` 可逆验证。
7. docs 基线 phase6(B6) 数据层落地：
  - phase6(B6) 已新增并迁移：`repair_ticket`、`repair_ticket_member`、`import_batch`、`import_repair_row`、`repair_match_application`、`workhour_entry`、`workhour_entry_tag`。
  - 在隔离库 `kaoqin_test@5433` 完成 `upgrade -> downgrade(08b9c0d1e2f3) -> upgrade` 可逆验证。
  - 在本地 5432 新建干净库 `m6_local_verify` 完成全链路升级验证。
8. repair/workhour v2 服务层启动落地（第一批）：
  - 新增 `app/services/repair_workhour_service.py`，打通“提交审核 -> 审批 -> 工时入账 -> 月结算”跨表事务编排。
  - 在 `app/api/v1/repair.py` 新增 v2 端点：`/repair-v2/*` 与 `/workhour-v2/*`。
  - 保留旧入口并桥接：新增 `/repair/{task_id}/submit-review`、`/repair/{task_id}/review` 对接新流程。
  - 新增单测 `tests/unit/test_repair_workhour_service.py`，覆盖非法动作、重复提交、审批通过、结算 dry-run。

回归结果：
- `tests/core/test_deps.py`（含 rollout 100% / 0%）通过。
- `tests/unit/test_auth_api.py`（含 camelCase 兼容断言）通过。
- `scripts/full_iteration_gate.sh` 全量门禁通过（含迁移升降级冒烟）。
- `tests/integration/test_docs_phase1_schema_alignment.py`（schema 对齐）通过。
- `tests/integration/test_docs_phase2_schema_alignment.py`（phase2 schema 对齐）通过。
- `tests/integration/test_b3_schema_alignment.py`（B3 schema 对齐）通过。
- `tests/integration/test_b4_schema_alignment.py`（B4 schema 对齐）通过。
- `tests/integration/test_b5_schema_alignment.py`（B5 schema 对齐）通过。
- phase1/phase2/B3/B4/B5 schema 回归：`10 passed`。
- `tests/integration/test_b6_schema_alignment.py`（B6 schema 对齐）通过。
- phase1/phase2/B3/B4/B5/B6 schema 回归：`12 passed`。
- `tests/unit/test_repair_workhour_service.py`：`4 passed`。

## 11. 当前剩余量（2026-04-10）
- docs SQL 基线剩余未落地：0 张表。
- 已完成：33/33（docs SQL 全量建表已覆盖到迁移链）。
- 下一批建议优先级（非数据层）：
  1. 服务层与接口层对齐（inspection/sampling/repair_v2/workhour_v2/review_todo）
  2. 双轨回填与对账脚本
  3. 全链路联调与发布门禁收口

## 12. 本次提交同步说明（2026-04-10）
- 已将 doc compatibility 路由层纳入主应用并用于文档契约补齐，当前文档路径层面覆盖为 72/72。
- 已完成最小可运行性验证：`python -c "import app.main"` 通过。
- 已完成最小路由回归：`tests/unit/test_route_registration_backend_completion.py` 通过（2 passed）。
- 下一步收口目标：按高风险优先完成 doc_compat 关键接口的权限与输入校验加固，并执行分组回归后给出可上线清单。