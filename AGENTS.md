# Repository Guidelines
## Always resposed Chinsese/中文
## 原则：“如无必要不增加实体”原则
## Project Structure & Module Organization
- `backend/`: FastAPI app (`app/`), SQLAlchemy models, Alembic config, tests and tooling (`pyproject.toml`).
- `frontend/`: Vue 3 + TypeScript + Vite + Element Plus UI.
- （已废弃）`frontend-new/`：此前的备用前端已移除，不再维护。
- `tests/`: Repository-level pytest suite and DB fixtures.
- `scripts/`: DevOps helpers (backup, deploy, smoke tests). Backend Docker compose lives in `backend/docker-compose.yml`.

## Build, Test, and Development Commands
- Backend (local):
  - `cd backend && python -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt`
  - Run: `uvicorn app.main:app --reload` (or `python -m app.main`).
  - DB Migrations: `alembic upgrade head`.
- Backend tests:
  - Unit/integration: `cd backend && pytest -q` or with markers `pytest -m unit` / `pytest -m integration`.
  - Coverage: `pytest --cov=app --cov-report=term-missing` (Codecov is configured; project target ~40%, patch ~50%).
- Frontend:
- `cd frontend && npm install && npm run dev` (tests: `npm run test:unit`).
- Docker (backend stack): `cd backend && docker compose up -d` (ensure Postgres/Redis env values).

## Coding Style & Naming Conventions
- Python: Black (88 cols), isort profile “black”, Flake8, MyPy strict. Use type hints. Modules/files snake_case; classes PascalCase; functions snake_case. Prefer explicit imports.
- Frontend: ESLint + Prettier, Vue SFCs in `kebab-case.vue`, components PascalCase, composables `useXxx.ts`. Keep API clients/types under `src/api` or `src/types`.

## Testing Guidelines
- Backend: pytest with asyncio; DB is auto-created/cleaned via `tests/conftest_db.py`. Mark long-running tests with `@pytest.mark.slow`.
- Frontend: Vitest for unit/components, Playwright for e2e (`npm run test:e2e`). Include minimal happy-path tests for new routes/components.

## Commit & Pull Request Guidelines
- Use Conventional Commits: `feat(auth): add refresh token endpoint`, `fix(tasks): correct pagination offset`, `test(db): add integrity checks`.
- PRs must: describe the change and rationale, link issues, include screenshots for UI, list test coverage/steps, update docs/examples when applicable, and pass CI.

## Security & Configuration
- Never commit secrets. Start from `.env.example` (root and `backend/`). For local dev, set `DATABASE_URL`, `REDIS_URL`, and `ENVIRONMENT=development`.
