# Backend Baseline Decisions

Last Updated: 2026-04-08

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
- Stage 3/4: not started in production path; planned as milestone rollout.
