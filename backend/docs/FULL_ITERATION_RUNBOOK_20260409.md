# 全量迭代执行说明（2026-04-09）

## 目标
- 按“从实现到验收”完成一轮可执行闭环：
  - 认证响应契约收敛（snake_case + camelCase 双兼容）
  - 错误码语义稳定
  - 双读灰度可观测
  - 迁移升降级与核心回归门禁通过
  - docs 基线 phase1 数据层对齐（foundation 表）
  - docs 基线 phase2~phase6 数据层对齐（治理/协助/巡检/抽检/报修+工时落账）

## 本轮新增
- 脚本：`scripts/full_iteration_gate.sh`
- 作用：
  1. 自动准备隔离数据库
  2. 调用 `scripts/m4_readiness_gate.sh` 执行完整门禁（含迁移升降级）
  3. 追加契约聚焦测试
  4. 追加 repair/workhour v2 服务回归测试
  5. 固定执行 phase1/phase2/B3/B4/B5/B6 schema 对齐测试

## 执行方式
```bash
cd backend
source .venv/bin/activate
chmod +x scripts/full_iteration_gate.sh
./scripts/full_iteration_gate.sh
```

## 可调参数
- `ITERATION_TMP_DB_NAME`：隔离库名称，默认 `m5_iter_gate`
- `ITERATION_DB_HOST`：默认 `127.0.0.1`
- `ITERATION_DB_PORT`：默认 `5432`
- `ITERATION_DB_USER`：默认 `kwok`
- `ITERATION_DB_PASSWORD`：默认 `Onjuju1084`

## 成功标准
- 命令输出包含 `[ITER-GATE] PASS`
- `m4_readiness_gate.sh` 输出包含 `[M4-GATE] PASS`
- 迁移链路可完成：
  - upgrade 到 `19c0d1e2f304`
  - downgrade 到 `a1f2c3d4e5f6`
  - 再 upgrade 到 `19c0d1e2f304`

## B6 隔离库严格门禁（推荐）
```bash
cd backend
source .venv/bin/activate

docker rm -f attendance-postgres-5433 2>/dev/null || true
docker run -d --name attendance-postgres-5433 \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=kaoqin_test \
  -p 5433:5432 postgres:15-alpine

export DATABASE_URL='postgresql+asyncpg://postgres:postgres@127.0.0.1:5433/kaoqin_test'
export DATABASE_URL_SYNC='postgresql://postgres:postgres@127.0.0.1:5433/kaoqin_test'

python -m alembic upgrade head
python -m alembic downgrade 08b9c0d1e2f3
python -m alembic upgrade head

pytest -q tests/integration/test_b6_schema_alignment.py

docker rm -f attendance-postgres-5433
```

## Schema 对齐验证（可选但推荐）
```bash
cd backend
source .venv/bin/activate
export DATABASE_URL='postgresql+asyncpg://kwok:Onjuju1084@127.0.0.1:5432/<tmp_db>'
export DATABASE_URL_SYNC='postgresql://kwok:Onjuju1084@127.0.0.1:5432/<tmp_db>'
pytest -q tests/integration/test_docs_phase1_schema_alignment.py
pytest -q tests/integration/test_docs_phase2_schema_alignment.py
pytest -q tests/integration/test_b3_schema_alignment.py
pytest -q tests/integration/test_b4_schema_alignment.py
pytest -q tests/integration/test_b5_schema_alignment.py
pytest -q tests/integration/test_b6_schema_alignment.py
```

## 本地库迁回验证（5432）
```bash
cd backend
source .venv/bin/activate
docker compose up -d postgres

# 建议先在本地干净库验证
docker exec attendance-postgres psql -U kwok -d postgres -c "DROP DATABASE IF EXISTS m6_local_verify;"
docker exec attendance-postgres psql -U kwok -d postgres -c "CREATE DATABASE m6_local_verify;"

export DATABASE_URL='postgresql+asyncpg://kwok:Onjuju1084@127.0.0.1:5432/m6_local_verify'
python -m alembic upgrade head
pytest -q tests/integration/test_b6_schema_alignment.py
```

## 说明
- 使用隔离库可规避历史库“表存在但版本历史不一致”引起的 `DuplicateTable` 干扰。
- 本脚本用于预发演练与发布前门禁，不建议直接对生产库执行。