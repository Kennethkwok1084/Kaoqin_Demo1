# V2实现偏差清单

Last Updated: 2026-04-11

## 1. 目的与范围
本清单用于追踪“文档基线”与“代码实现”的偏差，确保修复动作、验收标准、回滚策略可追溯。

唯一外部基线：
- `docs/校园网部门综合运维工时平台_PostgreSQL建表SQL_V2.sql`
- `docs/校园网部门综合运维工时平台_接口返回规范_V2.docx`

## 2. 字段模板
每条偏差必须包含以下字段：
- `ID`: 偏差编号（如 DEV-001）
- `类型`: 文档不一致 | 实现不足 | 实现超规 | 测试契约漂移
- `风险`: P0 | P1 | P2
- `基线条款`: 文档条款描述
- `当前实现`: 代码现状描述
- `证据`: 文件路径 + 行号
- `修复动作`: 具体改造项
- `验收标准`: 可执行的验证条件
- `回滚策略`: 失败时回退方式
- `状态`: open | in_progress | done

## 3. 偏差项

### DEV-001
- 类型: 文档不一致
- 风险: P0
- 基线条款: V2 对外口径应统一在 PostgreSQL V2 + 接口返回规范 V2。
- 当前实现: 已在主 README 与 API 规范中明确唯一外部基线，并将历史口径标注为“仅参考/已废弃”。
- 证据:
  - `readme.md`
  - `API_SPECIFICATION.md`
  - `backend/app/main.py:96`（FastAPI 入口）
- 修复动作: 在基线文档中明确唯一外部基线，历史口径标注为“仅参考/已废弃”。
- 验收标准: 基线文档可明确识别唯一外部基线，评审不再引用旧口径。
- 回滚策略: 无（文档变更）。
- 状态: done

### DEV-002
- 类型: 实现不足
- 风险: P0
- 基线条款: 抽样需支持加权随机与排除周期。
- 当前实现: 已支持加权随机无放回抽样，已接入 `exclude_days` 近N天排除与目标幂等补齐。
- 证据:
  - `backend/app/api/v1/inspection_sampling.py`
  - `backend/tests/unit/test_sampling_strategy.py`
  - `backend/tests/integration/test_sampling_target_strategy_integration.py`
- 修复动作: 新增抽样服务层，按 `exclude_days` 排除近N天样本并执行加权随机。
- 验收标准: 单元测试覆盖“加权命中”“30天排除”“候选不足”场景。
- 回滚策略: 开关回退到旧生成逻辑（保留旧分支）。
- 状态: done

### DEV-003
- 类型: 实现不足
- 风险: P0
- 基线条款: 检测结果需保留主记录 + 扫描明细 + 单项测试明细。
- 当前实现: `network-tests/{record_id}/submit` 与 `network-tests/single-item` 均已支持扫描明细与单项明细“先清后写”落库，并在详情接口回传明细；已补集成测试覆盖主表+两张明细表。
- 证据:
  - `backend/app/api/v1/inspection_sampling.py`
  - `backend/tests/integration/test_sampling_detail_persistence_integration.py`
  - `backend/app/models/sampling_scan_detail.py:11`
  - `backend/app/models/sampling_test_detail.py:12`
- 修复动作: 增加明细写入接口与服务；提交时写主表与明细表。
- 验收标准: 集成测试可验证主表和两张明细表同时落库。
- 回滚策略: 仅保留主表写入，关闭明细写入入口。
- 状态: done

### DEV-004
- 类型: 实现不足
- 风险: P1
- 基线条款: 协助签到需有防作弊校验（定位、二维码、一致性检查）。
- 当前实现: 已在签到签退接口接入定位半径校验、二维码验签、设备一致性校验，并在违规时自动写入 `coop_sign_abnormal` 待办。
- 证据:
  - `backend/app/api/v1/task_lifecycle.py`
  - `backend/app/api/v1/coop.py`
  - `backend/tests/integration/test_coop_anti_cheat_integration.py`
- 修复动作: 接入定位半径、二维码验签、设备/位置一致性校验，并异常入待办。
- 验收标准: 防作弊违规请求被拒绝，且可在待办池看到对应异常。
- 回滚策略: 关闭校验开关，保留日志。
- 状态: done

### DEV-005
- 类型: 实现不足
- 风险: P1
- 基线条款: OCR链路应支持服务端识别与结构化落库。
- 当前实现: 已支持服务端规则识别与结构化结果落库，并提供人工修正接口将修正结果回写工单字段。
- 证据:
  - `backend/app/services/repair_ocr_service.py`
  - `backend/app/api/v1/repair_orders.py`
  - `backend/tests/unit/test_repair_media_api.py`
- 修复动作: 增加服务端OCR流程（上传原图 -> 识别 -> 结构化 -> 人工修正）。
- 验收标准: OCR服务可输出标准结构，失败场景有错误码与重试策略。
- 回滚策略: 回退到“仅写入payload”模式。
- 状态: done

### DEV-006
- 类型: 实现不足
- 风险: P1
- 基线条款: 工时重算应基于规则引擎。
- 当前实现: 已支持按规则 `formula_json` + 上下文条件执行重算，并在 `review_log` 写入可回放审计信息。
- 证据:
  - `backend/app/api/v1/config_workhour.py`
  - `backend/tests/unit/test_config_workhour_recalculate_api.py`
  - `backend/tests/integration/test_workhour_recalculate_replay_integration.py`
- 修复动作: 引入规则解析、条件匹配、上下文计算与重算审计日志。
- 验收标准: 规则变更后重算结果可预测、可回放。
- 回滚策略: 回退到旧重算逻辑。
- 状态: done

### DEV-007
- 类型: 文档不一致
- 风险: P2
- 基线条款: task_qrcode 应有清晰生命周期定义。
- 当前实现: 已在 API 规范与主 README 明确 task_qrcode 生命周期、校验窗口、兼容 token 与无状态策略。
- 证据:
  - `API_SPECIFICATION.md`
  - `readme.md`
  - `backend/app/api/v1/coop.py:402`
  - `backend/app/api/v1/task_lifecycle.py:99`
- 修复动作: 在偏差说明与接口文档中明确当前策略，并统一前后端联调口径。
- 验收标准: 前后端对二维码机制达成统一口径并有接口说明。
- 回滚策略: 无（说明类变更）。
- 状态: done

### DEV-008
- 类型: 测试契约漂移
- 风险: P1
- 基线条款: 关键流程单测应与接口签名和鉴权约定一致。
- 当前实现: 契约兼容与鉴权健壮性修复已完成，目标文件回归与新增防作弊/抽检链路测试均已通过。
- 证据:
  - `backend/tests/unit/test_repair_media_api.py`
  - `backend/tests/unit/test_inspection_sampling_workflow_api.py`
- 修复动作: 兼容旧调用参数并增强鉴权函数健壮性。
- 验收标准: 目标4个测试文件全绿。
- 回滚策略: 回退改动并同步修正测试桩。
- 状态: done
