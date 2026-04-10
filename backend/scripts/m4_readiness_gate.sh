#!/usr/bin/env bash
set -euo pipefail

# M4 readiness gate:
# 1) core auth regressions
# 2) structured error-code contract regressions
# 3) optional migration upgrade/downgrade smoke

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

if [[ ! -f ".venv/bin/activate" ]]; then
  echo "[M4-GATE] backend/.venv not found"
  exit 1
fi

source .venv/bin/activate

echo "[M4-GATE] Running auth dependency dual-read regression"
pytest -q tests/core/test_deps.py -k "get_current_user and (app_user or fallback or inactive or success or invalid or missing or database or token_format or string_user_id)"

echo "[M4-GATE] Running auth API regression"
pytest -q tests/unit/test_auth_api.py -k "refresh or logout or login or profile or password"

echo "[M4-GATE] Running HTTP exception contract regression"
pytest -q tests/core/test_main.py -k "http_exception_handler"

if [[ "${RUN_MIGRATION_CHECK:-false}" == "true" ]]; then
  echo "[M4-GATE] Running migration upgrade/downgrade smoke"
  alembic upgrade head
  alembic downgrade a1f2c3d4e5f6
  alembic upgrade head
else
  echo "[M4-GATE] Skipping migration check (set RUN_MIGRATION_CHECK=true to enable)"
fi

echo "[M4-GATE] PASS"
