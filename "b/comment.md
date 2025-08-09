# 修改意见

以下修改建议旨在补齐《系统重构报告.md》中尚未完成的功能与质量要求，确保任务模块在上线前达到稳定可靠。

## 1. API 功能补齐
- [ ] 在 `backend/app/api/v1/tasks.py` 实现 `GET /api/tasks/work-time-detail`，返回单任务工时分解（基础分钟、爆单奖励、惩罚等）。
- [ ] 在 `backend/app/api/v1/import.py` 实现 `GET /api/import/field-mapping`，输出导入字段映射表。
- [ ] 清理或完善当前 `/monitoring`、`/fixes` 等占位式路由，避免返回空数据。

## 2. 性能与异常处理
- [ ] 使用 `pytest-benchmark` 在 `tests/perf/` 增加导入 1000 条记录与单次工时计算的性能基准测试，并设定阈值。
- [ ] 在 `WorkHoursCalculationService` 等核心服务中增加输入校验和异常日志，防止负数分钟、缺失标签等问题。

## 3. 测试覆盖率提升
- [ ] 后端：为新增 API 补充单元与集成测试，每个接口至少 3 条正常用例 + 1 条异常用例。
- [ ] 前端：在 `frontend/tests/unit/` 扩充任务列表、工时录入等组件测试；在 `frontend/tests/e2e/` 使用 Playwright 编写登录→创建任务→查看工时的端到端流程。

## 4. CI/CD 流程完善
- [ ] 在 GitHub Actions 中新增 `frontend-test` Job，执行 `pnpm lint`、`pnpm test:unit`、`pnpm test:e2e`。
- [ ] 在后端 CI Job 末尾执行 `pytest tests/perf`，并上传基准报告作为 Artifact。

## 5. 运维与验收
- [ ] 编写 `scripts/e2e_smoke.py`，一键启动后端并执行端到端冒烟测试。
- [ ] 上线前准备数据库备份与迁移回滚脚本，确保数据安全。

