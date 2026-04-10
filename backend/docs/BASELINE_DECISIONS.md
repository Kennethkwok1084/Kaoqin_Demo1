# Backend Baseline Decisions

Last Updated: 2026-04-10

## Scope
This document freezes stage-0 baseline decisions for backend evolution.

## Decision 1: Database Baseline
The only database baseline for stage 0-4 planning is:
- docs/校园网部门综合运维工时平台_PostgreSQL建表SQL_V2.sql

Rules:
1. Any new table/model introduced in stage 3+ must map to this SQL baseline first.
2. If implementation deviates from baseline, add a "Deviation" section with reason and rollback strategy.
3. Migration scripts must include upgrade and downgrade paths.

## Decision 2: API Response Baseline
The only API response baseline is:
- docs/校园网部门综合运维工时平台_接口返回规范_V2.docx

Current enforced top-level fields:
- code
- success
- message
- data
- request_id
- timestamp
- errors (optional)

Backward-compatible fields currently retained:
- status_code
- error_code
- detail (validation compatibility)

## Execution Guardrails
1. Keep old interfaces readable during migration windows.
2. Prioritize additive changes over breaking changes.
3. Require contract tests before removing backward-compatible fields.
4. All auth token operations must be auditable and revocable.

## Stage Status Snapshot
- Stage 1: response contract + request_id pipeline implemented.
- Stage 2: auth_refresh_token persistence, token rotation, revoke flow implemented.
- Stage 3/4/5/6: phased implementation completed (phase1~phase6 completed).
	- Done: auth_refresh_token FK -> app_user; foundation tables `sys_config` / `building` / `dorm_room` / `media_file`; governance/workhour tables `workhour_rule` / `workhour_tag` / `review_log` / `todo_item` / `biz_operation_log`; coop tables `task_coop` / `task_coop_slot` / `task_coop_signup` / `task_coop_attendance`; inspection tables `task_inspection` / `task_inspection_user` / `task_inspection_point` / `inspection_record`; sampling tables `task_sampling` / `task_sampling_user` / `task_sampling_room` / `sampling_record` / `sampling_scan_detail` / `sampling_test_detail`; repair/import/workhour-entry tables `repair_ticket` / `repair_ticket_member` / `import_batch` / `import_repair_row` / `repair_match_application` / `workhour_entry` / `workhour_entry_tag`.
	- Baseline coverage: docs SQL V2 business tables aligned 33/33.
	- Next focus: service/API workflow implementation and end-to-end business closure.
	- Progress: repair/workhour v2 first slice has started (review submit/approve/reject + monthly settlement + legacy bridge endpoints).

## Migration Validation Notes

- Isolated DB gate (5433): verified `upgrade head -> downgrade 08b9c0d1e2f3 -> upgrade head`, and phase1/phase2/B3/B4/B5/B6 schema-alignment tests all pass.
- Local DB rollback capability: validated on a clean local database (`m6_local_verify`) with successful upgrade to head and B6 schema tests.
- If local default DB already contains historical manual tables (for example existing `auth_refresh_token` before migration history), `alembic upgrade head` may fail with DuplicateTable. This indicates DB state drift, not migration script defects.

## Current Progress Snapshot (2026-04-10)

- API contract completion: doc compatibility router has been mounted at `/api/v1` and strict documented-route coverage reached 72/72 (path-level).
- Service/test baseline: inspection/sampling/repair v2 service layer and corresponding unit/integration suites are now present in repository.
- Runtime smoke: backend app import check passed (`import app.main`), and route registration smoke test `tests/unit/test_route_registration_backend_completion.py` passed.
- Remaining focus: harden high-risk business behavior (permissions, input validation, idempotency, transactional consistency) and finish grouped regression before release.
