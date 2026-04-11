"""System config, workhour, todo, and internal ops APIs migrated from doc_compat."""

import json
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import create_response, get_current_active_admin, get_current_user, get_db
from app.models.member import Member
from app.models.review_log import ReviewLog
from app.models.system_config import SystemConfig
from app.models.todo_item import TodoItem
from app.models.workhour_entry import WorkhourEntry
from app.models.workhour_rule import WorkhourRule

router = APIRouter()


def _to_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _to_bool(value: Any, default: bool = False) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "on", "y"}


def _to_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _coerce_value_type(sample: Any, raw_value: Any) -> Any:
    if sample is None:
        return raw_value
    if isinstance(sample, bool):
        return _to_bool(raw_value, False)
    if isinstance(sample, int):
        return _to_int(raw_value, sample)
    if isinstance(sample, float):
        return _to_float(raw_value, sample)
    return str(raw_value)


def _match_condition(context: Dict[str, Any], condition: Dict[str, Any]) -> bool:
    field = str(condition.get("field") or "").strip()
    op = str(condition.get("op") or "eq").strip().lower()
    expected = condition.get("value")
    if not field or field not in context:
        return False

    actual = context.get(field)
    expected = _coerce_value_type(actual, expected)

    if op in {"eq", "=="}:
        return actual == expected
    if op in {"ne", "!="}:
        return actual != expected
    if op in {"gt", ">"}:
        return _to_float(actual) > _to_float(expected)
    if op in {"gte", ">="}:
        return _to_float(actual) >= _to_float(expected)
    if op in {"lt", "<"}:
        return _to_float(actual) < _to_float(expected)
    if op in {"lte", "<="}:
        return _to_float(actual) <= _to_float(expected)
    if op == "contains":
        return str(expected) in str(actual)
    if op == "in":
        return actual in (expected or [])
    if op == "not_in":
        return actual not in (expected or [])
    return False


def _compute_final_minutes(
    row: WorkhourEntry,
    rule: WorkhourRule,
    extra_context: Dict[str, Any],
) -> tuple[int, Dict[str, Any]]:
    formula = rule.formula_json if isinstance(rule.formula_json, dict) else {}
    mode = str(formula.get("mode") or "base").strip().lower()

    if mode == "final":
        minutes = _to_float(row.final_minutes)
    elif mode == "zero":
        minutes = 0.0
    else:
        minutes = _to_float(row.base_minutes)

    minutes *= _to_float(formula.get("base_multiplier"), 1.0)
    minutes += _to_float(formula.get("add_minutes"), 0.0)

    context: Dict[str, Any] = {
        "entry_id": row.id,
        "biz_type": row.biz_type,
        "biz_id": row.biz_id,
        "user_id": row.user_id,
        "base_minutes": row.base_minutes,
        "final_minutes": row.final_minutes,
        "review_status": row.review_status,
    }
    for key, value in extra_context.items():
        if key not in context:
            context[key] = value

    matched_conditions: list[Dict[str, Any]] = []
    for item in formula.get("conditions") or []:
        if not isinstance(item, dict) or not _match_condition(context, item):
            continue

        if "then_set" in item:
            minutes = _to_float(item.get("then_set"), minutes)
        minutes *= _to_float(item.get("then_multiplier"), 1.0)
        minutes += _to_float(item.get("then_add"), 0.0)
        matched_conditions.append(
            {
                "field": item.get("field"),
                "op": item.get("op"),
                "value": item.get("value"),
                "reason": item.get("reason"),
            }
        )

    min_minutes = _to_int(formula.get("min_minutes"), 0)
    max_minutes = _to_int(formula.get("max_minutes"), 1440)
    clamped = max(min_minutes, min(int(round(minutes)), max_minutes))

    replay = {
        "rule_id": rule.id,
        "mode": mode,
        "formula": formula,
        "context": context,
        "matched_conditions": matched_conditions,
    }
    return clamped, replay


async def _resolve_recalc_rule(
    db: AsyncSession,
    row: WorkhourEntry,
    cached_by_id: Dict[int, Optional[WorkhourRule]],
    cached_by_biz: Dict[str, Optional[WorkhourRule]],
) -> Optional[WorkhourRule]:
    if row.source_rule_id:
        if row.source_rule_id not in cached_by_id:
            cached_by_id[row.source_rule_id] = (
                (
                    await db.execute(
                        select(WorkhourRule).where(
                            WorkhourRule.id == row.source_rule_id,
                            WorkhourRule.is_enabled.is_(True),
                        )
                    )
                )
                .scalar_one_or_none()
            )
        if cached_by_id[row.source_rule_id]:
            return cached_by_id[row.source_rule_id]

    if row.biz_type not in cached_by_biz:
        cached_by_biz[row.biz_type] = (
            (
                await db.execute(
                    select(WorkhourRule)
                    .where(
                        WorkhourRule.biz_type == row.biz_type,
                        WorkhourRule.is_enabled.is_(True),
                    )
                    .order_by(WorkhourRule.id)
                    .limit(1)
                )
            )
            .scalar_one_or_none()
        )
    return cached_by_biz[row.biz_type]


async def _get_system_config_int(
    db: AsyncSession,
    keys: list[str],
    default: int,
    min_value: int = 1,
    max_value: int = 3600,
) -> int:
    for key in keys:
        row = (
            await db.execute(
                select(SystemConfig).where(
                    SystemConfig.config_key == key,
                    SystemConfig.is_active.is_(True),
                )
            )
        ).scalar_one_or_none()
        if not row or row.config_value is None:
            continue
        try:
            value = int(str(row.config_value).strip())
            return max(min_value, min(value, max_value))
        except (TypeError, ValueError):
            continue
    return default


async def _get_system_config_text(
    db: AsyncSession,
    keys: list[str],
    default: str,
) -> str:
    for key in keys:
        row = (
            await db.execute(
                select(SystemConfig).where(
                    SystemConfig.config_key == key,
                    SystemConfig.is_active.is_(True),
                )
            )
        ).scalar_one_or_none()
        if not row or row.config_value is None:
            continue
        value = str(row.config_value).strip()
        if value:
            return value
    return default


@router.get("/admin/configs", response_model=Dict[str, Any])
async def admin_get_configs(
    category: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    _: Member = Depends(get_current_active_admin),
) -> Dict[str, Any]:
    stmt = select(SystemConfig).order_by(SystemConfig.display_order, SystemConfig.id)
    if category:
        stmt = stmt.where(SystemConfig.category == category)
    rows = (await db.execute(stmt)).scalars().all()
    return create_response(
        data={
            "list": [
                {
                    "id": cfg.id,
                    "config_key": cfg.config_key,
                    "config_name": cfg.config_name,
                    "category": cfg.category,
                    "config_group": cfg.config_group,
                    "config_value": cfg.config_value,
                    "value_type": cfg.value_type,
                    "is_active": cfg.is_active,
                }
                for cfg in rows
            ],
            "total": len(rows),
        },
        message="获取配置成功",
    )


@router.put("/admin/configs", response_model=Dict[str, Any])
async def admin_put_configs(
    payload: Dict[str, Any],
    db: AsyncSession = Depends(get_db),
    _: Member = Depends(get_current_active_admin),
) -> Dict[str, Any]:
    updates = payload.get("configs")
    if not isinstance(updates, list):
        updates = [payload]

    updated = 0
    for item in updates:
        config_key = item.get("config_key") or item.get("key")
        if not config_key:
            continue
        row = (
            await db.execute(
                select(SystemConfig).where(SystemConfig.config_key == str(config_key))
            )
        ).scalar_one_or_none()
        if not row:
            continue
        if "config_value" in item:
            row.config_value = str(item["config_value"])
        elif "value" in item:
            row.config_value = str(item["value"])
        updated += 1
    await db.commit()
    return create_response(data={"updated": updated}, message="配置更新成功")


@router.get("/admin/workhour-rules", response_model=Dict[str, Any])
async def admin_get_workhour_rules(
    biz_type: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    _: Member = Depends(get_current_active_admin),
) -> Dict[str, Any]:
    stmt = select(WorkhourRule).order_by(WorkhourRule.id)
    if biz_type:
        stmt = stmt.where(WorkhourRule.biz_type == biz_type)
    rows = (await db.execute(stmt)).scalars().all()
    return create_response(
        data={
            "list": [
                {
                    "id": r.id,
                    "rule_code": r.rule_code,
                    "rule_name": r.rule_name,
                    "biz_type": r.biz_type,
                    "formula_desc": r.formula_desc,
                    "formula_json": r.formula_json,
                    "is_enabled": r.is_enabled,
                }
                for r in rows
            ],
            "total": len(rows),
        },
        message="获取工时规则成功",
    )


@router.post("/admin/workhour-rules", response_model=Dict[str, Any])
async def admin_create_workhour_rule(
    payload: Dict[str, Any],
    db: AsyncSession = Depends(get_db),
    _: Member = Depends(get_current_active_admin),
) -> Dict[str, Any]:
    rule_code = (payload.get("rule_code") or payload.get("ruleCode") or "").strip()
    rule_name = (payload.get("rule_name") or payload.get("ruleName") or "").strip()
    default_biz_type = await _get_system_config_text(
        db,
        keys=["workhour_rule_default_biz_type"],
        default="repair",
    )
    biz_type = (
        payload.get("biz_type") or payload.get("bizType") or default_biz_type
    ).strip()
    if not rule_code or not rule_name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="rule_code/rule_name 不能为空",
        )

    exists = (
        await db.execute(select(WorkhourRule).where(WorkhourRule.rule_code == rule_code))
    ).scalar_one_or_none()
    if exists:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="rule_code 已存在")

    default_formula_desc = await _get_system_config_text(
        db,
        keys=["workhour_rule_default_formula_desc"],
        default="",
    )
    default_enabled = await _get_system_config_int(
        db,
        keys=["workhour_rule_default_enabled"],
        default=1,
        min_value=0,
        max_value=1,
    )

    row = WorkhourRule(
        rule_code=rule_code,
        rule_name=rule_name,
        biz_type=biz_type,
        formula_desc=payload.get("formula_desc")
        or payload.get("formulaDesc")
        or default_formula_desc,
        formula_json=payload.get("formula_json") or payload.get("formulaJson") or {},
        is_enabled=_to_bool(payload.get("is_enabled"), bool(default_enabled)),
    )
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return create_response(data={"id": row.id}, message="创建工时规则成功")


@router.put("/admin/workhour-rules/{rule_id}", response_model=Dict[str, Any])
async def admin_update_workhour_rule(
    rule_id: int,
    payload: Dict[str, Any],
    db: AsyncSession = Depends(get_db),
    _: Member = Depends(get_current_active_admin),
) -> Dict[str, Any]:
    row = (
        await db.execute(select(WorkhourRule).where(WorkhourRule.id == rule_id))
    ).scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="规则不存在")

    for key in ["rule_name", "biz_type", "formula_desc", "formula_json", "is_enabled"]:
        if key in payload:
            setattr(row, key, payload[key])
    await db.commit()
    return create_response(data={"id": row.id}, message="更新工时规则成功")


@router.get("/workhours/my", response_model=Dict[str, Any])
async def get_my_workhours(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    current_user: Member = Depends(get_current_user),
) -> Dict[str, Any]:
    stmt = select(WorkhourEntry).where(WorkhourEntry.user_id == current_user.id)
    total = _to_int(
        (await db.execute(select(func.count()).select_from(stmt.subquery()))).scalar(),
        0,
    )
    rows = (
        await db.execute(
            stmt.order_by(WorkhourEntry.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
    ).scalars().all()
    return create_response(
        data={
            "list": [
                {
                    "id": r.id,
                    "biz_type": r.biz_type,
                    "biz_id": r.biz_id,
                    "base_minutes": r.base_minutes,
                    "final_minutes": r.final_minutes,
                    "review_status": r.review_status,
                    "created_at": r.created_at.isoformat() if r.created_at else None,
                }
                for r in rows
            ],
            "page": page,
            "page_size": page_size,
            "total": total,
            "total_pages": (total + page_size - 1) // page_size,
            "has_next": page * page_size < total,
        },
        message="获取个人工时成功",
    )


@router.get("/admin/workhours", response_model=Dict[str, Any])
async def admin_get_workhours(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
    review_status: Optional[int] = Query(None),
    biz_type: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    _: Member = Depends(get_current_active_admin),
) -> Dict[str, Any]:
    stmt = select(WorkhourEntry)
    if review_status is not None:
        stmt = stmt.where(WorkhourEntry.review_status == review_status)
    if biz_type:
        stmt = stmt.where(WorkhourEntry.biz_type == biz_type)

    total = _to_int(
        (await db.execute(select(func.count()).select_from(stmt.subquery()))).scalar(),
        0,
    )
    rows = (
        await db.execute(
            stmt.order_by(WorkhourEntry.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
    ).scalars().all()
    return create_response(
        data={
            "list": [
                {
                    "id": r.id,
                    "biz_type": r.biz_type,
                    "biz_id": r.biz_id,
                    "user_id": r.user_id,
                    "base_minutes": r.base_minutes,
                    "final_minutes": r.final_minutes,
                    "review_status": r.review_status,
                    "reviewed_by": r.reviewed_by,
                    "reviewed_at": r.reviewed_at.isoformat() if r.reviewed_at else None,
                    "created_at": r.created_at.isoformat() if r.created_at else None,
                }
                for r in rows
            ],
            "page": page,
            "page_size": page_size,
            "total": total,
            "total_pages": (total + page_size - 1) // page_size,
            "has_next": page * page_size < total,
        },
        message="获取工时列表成功",
    )


async def _review_workhour_entry(
    entry_id: int,
    reviewer_id: int,
    action: str,
    note: Optional[str],
    db: AsyncSession,
) -> WorkhourEntry:
    row = (
        await db.execute(select(WorkhourEntry).where(WorkhourEntry.id == entry_id))
    ).scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="工时记录不存在")

    row.review_status = 1 if action == "approve" else 2
    row.reviewed_by = reviewer_id
    row.reviewed_at = datetime.now(timezone.utc)
    row.review_note = note

    db.add(
        ReviewLog(
            biz_type="workhour_entry",
            biz_id=row.id,
            review_type="workhour",
            reviewer_id=reviewer_id,
            action_code=action,
            review_note=note,
        )
    )
    await db.commit()
    await db.refresh(row)
    return row


@router.post("/admin/workhours/{entry_id}/approve", response_model=Dict[str, Any])
async def admin_approve_workhour(
    entry_id: int,
    payload: Dict[str, Any],
    db: AsyncSession = Depends(get_db),
    current_user: Member = Depends(get_current_active_admin),
) -> Dict[str, Any]:
    row = await _review_workhour_entry(
        entry_id=entry_id,
        reviewer_id=current_user.id,
        action="approve",
        note=payload.get("note"),
        db=db,
    )
    return create_response(data={"id": row.id, "review_status": row.review_status}, message="工时审核通过")


@router.post("/admin/workhours/{entry_id}/reject", response_model=Dict[str, Any])
async def admin_reject_workhour(
    entry_id: int,
    payload: Dict[str, Any],
    db: AsyncSession = Depends(get_db),
    current_user: Member = Depends(get_current_active_admin),
) -> Dict[str, Any]:
    row = await _review_workhour_entry(
        entry_id=entry_id,
        reviewer_id=current_user.id,
        action="reject",
        note=payload.get("note"),
        db=db,
    )
    return create_response(data={"id": row.id, "review_status": row.review_status}, message="工时已驳回")


@router.post("/admin/workhours/manual", response_model=Dict[str, Any])
async def admin_manual_workhour(
    payload: Dict[str, Any],
    db: AsyncSession = Depends(get_db),
    current_user: Member = Depends(get_current_active_admin),
) -> Dict[str, Any]:
    user_id = _to_int(payload.get("user_id") or payload.get("userId"), 0)
    if user_id <= 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="user_id 非法")

    default_biz_type = await _get_system_config_text(
        db,
        keys=["manual_workhour_default_biz_type"],
        default="repair",
    )
    default_base_minutes = await _get_system_config_int(
        db,
        keys=["manual_workhour_default_base_minutes"],
        default=0,
        min_value=0,
        max_value=720,
    )
    default_final_minutes = await _get_system_config_int(
        db,
        keys=["manual_workhour_default_final_minutes"],
        default=0,
        min_value=0,
        max_value=720,
    )
    max_minutes = await _get_system_config_int(
        db,
        keys=["manual_workhour_max_minutes"],
        default=720,
        min_value=1,
        max_value=1440,
    )
    default_review_note = await _get_system_config_text(
        db,
        keys=["manual_workhour_default_note"],
        default="manual",
    )

    base_minutes = _to_int(
        payload.get("base_minutes") or payload.get("baseMinutes"),
        default_base_minutes,
    )
    final_minutes = _to_int(
        payload.get("final_minutes") or payload.get("finalMinutes"),
        default_final_minutes,
    )
    base_minutes = max(0, min(base_minutes, max_minutes))
    final_minutes = max(0, min(final_minutes, max_minutes))

    row = WorkhourEntry(
        biz_type=payload.get("biz_type") or payload.get("bizType") or default_biz_type,
        biz_id=_to_int(payload.get("biz_id") or payload.get("bizId"), 0),
        user_id=user_id,
        source_rule_id=payload.get("source_rule_id") or payload.get("sourceRuleId"),
        base_minutes=base_minutes,
        final_minutes=final_minutes,
        review_status=1,
        reviewed_by=current_user.id,
        reviewed_at=datetime.now(timezone.utc),
        review_note=payload.get("note") or default_review_note,
    )
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return create_response(data={"id": row.id}, message="手工工时补录成功")


@router.get("/admin/todos", response_model=Dict[str, Any])
async def admin_get_todos(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
    status_filter: Optional[int] = Query(None, alias="status"),
    todo_type: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    _: Member = Depends(get_current_active_admin),
) -> Dict[str, Any]:
    stmt = select(TodoItem)
    if status_filter is not None:
        stmt = stmt.where(TodoItem.status == status_filter)
    if todo_type:
        stmt = stmt.where(TodoItem.todo_type == todo_type)
    total = _to_int(
        (await db.execute(select(func.count()).select_from(stmt.subquery()))).scalar(),
        0,
    )
    rows = (
        await db.execute(
            stmt.order_by(TodoItem.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
    ).scalars().all()
    return create_response(
        data={
            "list": [
                {
                    "id": t.id,
                    "todo_type": t.todo_type,
                    "source_biz_type": t.source_biz_type,
                    "source_biz_id": t.source_biz_id,
                    "title": t.title,
                    "status": t.status,
                    "assignee_user_id": t.assignee_user_id,
                    "created_at": t.created_at.isoformat() if t.created_at else None,
                    "resolved_at": t.resolved_at.isoformat() if t.resolved_at else None,
                }
                for t in rows
            ],
            "page": page,
            "page_size": page_size,
            "total": total,
            "total_pages": (total + page_size - 1) // page_size,
            "has_next": page * page_size < total,
        },
        message="获取待办列表成功",
    )


@router.post("/admin/todos/{todo_id}/claim", response_model=Dict[str, Any])
async def admin_claim_todo(
    todo_id: int,
    payload: Dict[str, Any],
    db: AsyncSession = Depends(get_db),
    current_user: Member = Depends(get_current_active_admin),
) -> Dict[str, Any]:
    row = (await db.execute(select(TodoItem).where(TodoItem.id == todo_id))).scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="待办不存在")
    row.assignee_user_id = _to_int(payload.get("assignee_user_id"), current_user.id)
    row.status = 1
    await db.commit()
    return create_response(data={"id": row.id, "status": row.status}, message="待办已领取")


@router.post("/admin/todos/{todo_id}/finish", response_model=Dict[str, Any])
async def admin_finish_todo(
    todo_id: int,
    db: AsyncSession = Depends(get_db),
    _: Member = Depends(get_current_active_admin),
) -> Dict[str, Any]:
    row = (await db.execute(select(TodoItem).where(TodoItem.id == todo_id))).scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="待办不存在")
    row.status = 2
    row.resolved_at = datetime.now(timezone.utc)
    await db.commit()
    return create_response(data={"id": row.id, "status": row.status}, message="待办已完成")


@router.post("/internal/workhours/recalculate", response_model=Dict[str, Any])
async def recalculate_workhours(
    payload: Dict[str, Any],
    db: AsyncSession = Depends(get_db),
    current_user: Member = Depends(get_current_active_admin),
) -> Dict[str, Any]:
    entry_id = _to_int(payload.get("entry_id") or payload.get("entryId"), 0)
    reason = str(payload.get("reason") or "manual_recalculate").strip() or "manual_recalculate"
    include_details = _to_bool(payload.get("include_details") or payload.get("includeDetails"), entry_id > 0)
    extra_context = payload.get("context") or payload.get("rule_context") or payload.get("ruleContext") or {}
    if not isinstance(extra_context, dict):
        extra_context = {}

    updated = 0
    changed = 0
    details: list[Dict[str, Any]] = []
    cached_by_id: Dict[int, Optional[WorkhourRule]] = {}
    cached_by_biz: Dict[str, Optional[WorkhourRule]] = {}

    targets: list[WorkhourEntry] = []
    if entry_id > 0:
        row = (
            await db.execute(select(WorkhourEntry).where(WorkhourEntry.id == entry_id))
        ).scalar_one_or_none()
        if row:
            targets = [row]
    else:
        targets = (
            await db.execute(select(WorkhourEntry).where(WorkhourEntry.review_status == 0))
        ).scalars().all()

    for row in targets:
        old_final_minutes = row.final_minutes
        rule = await _resolve_recalc_rule(
            db=db,
            row=row,
            cached_by_id=cached_by_id,
            cached_by_biz=cached_by_biz,
        )

        if rule:
            new_final_minutes, replay = _compute_final_minutes(
                row=row,
                rule=rule,
                extra_context=extra_context,
            )
            if row.source_rule_id is None:
                row.source_rule_id = rule.id
        else:
            new_final_minutes = row.base_minutes
            replay = {
                "rule_id": None,
                "mode": "fallback_base",
                "formula": {},
                "context": {
                    "entry_id": row.id,
                    "biz_type": row.biz_type,
                    "biz_id": row.biz_id,
                    "user_id": row.user_id,
                    "base_minutes": row.base_minutes,
                    "final_minutes": row.final_minutes,
                    "review_status": row.review_status,
                },
                "matched_conditions": [],
            }

        row.final_minutes = new_final_minutes
        updated += 1
        if old_final_minutes != new_final_minutes:
            changed += 1

        review_note = json.dumps(
            {
                "reason": reason,
                "before": old_final_minutes,
                "after": new_final_minutes,
                "replay": replay,
            },
            ensure_ascii=False,
        )
        db.add(
            ReviewLog(
                biz_type="workhour_entry",
                biz_id=row.id,
                review_type="workhour_recalculate",
                reviewer_id=current_user.id,
                action_code="recalculate",
                review_note=review_note,
            )
        )

        if include_details:
            details.append(
                {
                    "entry_id": row.id,
                    "biz_type": row.biz_type,
                    "biz_id": row.biz_id,
                    "before": old_final_minutes,
                    "after": new_final_minutes,
                    "rule_id": replay["rule_id"],
                    "matched_conditions": replay["matched_conditions"],
                }
            )

    await db.commit()
    data: Dict[str, Any] = {"updated": updated, "changed": changed}
    if include_details:
        data["details"] = details
    return create_response(data=data, message="工时重算完成")
