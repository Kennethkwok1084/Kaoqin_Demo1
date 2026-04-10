#!/usr/bin/env bash
set -euo pipefail

# Full iteration gate:
# - M4 readiness gate
# - clean DB migration smoke
# - extra contract-focused checks

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

if [[ ! -f ".venv/bin/activate" ]]; then
  echo "[ITER-GATE] backend/.venv not found"
  exit 1
fi

source .venv/bin/activate

if ! command -v docker >/dev/null 2>&1; then
  echo "[ITER-GATE] docker is required for clean migration smoke"
  exit 1
fi

# Ensure local postgres exists
cd "$ROOT_DIR"
docker compose up -d postgres >/dev/null

TMP_DB_NAME="${ITERATION_TMP_DB_NAME:-m5_iter_gate}"
DB_HOST="${ITERATION_DB_HOST:-127.0.0.1}"
DB_PORT="${ITERATION_DB_PORT:-5432}"
DB_USER="${ITERATION_DB_USER:-kwok}"
DB_PASSWORD="${ITERATION_DB_PASSWORD:-Onjuju1084}"

# Recreate isolated DB for deterministic migration smoke

docker exec attendance-postgres psql -U "$DB_USER" -d postgres -c "DROP DATABASE IF EXISTS ${TMP_DB_NAME};" >/dev/null

docker exec attendance-postgres psql -U "$DB_USER" -d postgres -c "CREATE DATABASE ${TMP_DB_NAME};" >/dev/null

export DATABASE_URL="postgresql+asyncpg://${DB_USER}:${DB_PASSWORD}@${DB_HOST}:${DB_PORT}/${TMP_DB_NAME}"
export DATABASE_URL_SYNC="postgresql://${DB_USER}:${DB_PASSWORD}@${DB_HOST}:${DB_PORT}/${TMP_DB_NAME}"

echo "[ITER-GATE] Running M4 readiness gate with clean migration DB=${TMP_DB_NAME}"
RUN_MIGRATION_CHECK=true ./scripts/m4_readiness_gate.sh

echo "[ITER-GATE] Running contract-focused auth subset"
pytest -q tests/unit/test_auth_api.py -k "invalid_payload_contract or revoked or expired or logout_single_device_requires_device_id"

echo "[ITER-GATE] Running repair/workhour v2 service subset"
pytest -q tests/unit/test_repair_workhour_service.py

echo "[ITER-GATE] Running docs baseline schema alignment subset (phase1/phase2/b3/b4/b5/b6)"
pytest -q \
  tests/integration/test_docs_phase1_schema_alignment.py \
  tests/integration/test_docs_phase2_schema_alignment.py \
  tests/integration/test_b3_schema_alignment.py \
  tests/integration/test_b4_schema_alignment.py \
  tests/integration/test_b5_schema_alignment.py \
  tests/integration/test_b6_schema_alignment.py

echo "[ITER-GATE] PASS"
