"""Doc-defined API compatibility endpoints.

This router provides quick compatibility endpoints following
docs/接口清单路径，优先复用现有模型与能力，便于先补齐功能再细化。
"""

import hashlib
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import create_response, get_current_active_admin, get_current_user, get_db
from app.core.security import get_password_hash
from app.models.building import Building, DormRoom
from app.models.import_batch import ImportBatch
from app.models.import_repair_row import ImportRepairRow
from app.models.inspection_record import InspectionRecord
from app.models.media_file import MediaFile
from app.models.member import Member, UserRole
from app.models.repair_match_application import RepairMatchApplication
from app.models.repair_ticket import RepairTicket
from app.models.repair_ticket_member import RepairTicketMember
from app.models.review_log import ReviewLog
from app.models.sampling_record import SamplingRecord
from app.models.system_config import SystemConfig
from app.models.task_coop import TaskCoop
from app.models.task_coop_attendance import TaskCoopAttendance
from app.models.task_coop_signup import TaskCoopSignup
from app.models.task_coop_slot import TaskCoopSlot
from app.models.task_inspection import TaskInspection
from app.models.task_inspection_point import TaskInspectionPoint
from app.models.task_inspection_user import TaskInspectionUser
from app.models.task_sampling import TaskSampling
from app.models.task_sampling_room import TaskSamplingRoom
from app.models.task_sampling_user import TaskSamplingUser
from app.models.todo_item import TodoItem
from app.models.workhour_entry import WorkhourEntry
from app.models.workhour_rule import WorkhourRule
from app.services.user_sync_service import UserSyncService

router = APIRouter()


def _to_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _new_code(prefix: str) -> str:
    now = datetime.now(timezone.utc)
    digest = hashlib.sha1(f"{prefix}:{now.timestamp()}".encode("utf-8")).hexdigest()[:6]
    return f"{prefix}-{now.strftime('%Y%m%d%H%M%S')}-{digest}"


def _uploads_dir() -> Path:
    path = Path(__file__).resolve().parents[3] / "uploads"
    path.mkdir(parents=True, exist_ok=True)
    return path


async def _find_task_any(db: AsyncSession, task_id: int) -> tuple[str, Any] | tuple[None, None]:
    coop = (await db.execute(select(TaskCoop).where(TaskCoop.id == task_id))).scalar_one_or_none()
    if coop:
        return "coop", coop
    inspection = (
        await db.execute(select(TaskInspection).where(TaskInspection.id == task_id))
    ).scalar_one_or_none()
    if inspection:
        return "inspection", inspection
    sampling = (
        await db.execute(select(TaskSampling).where(TaskSampling.id == task_id))
    ).scalar_one_or_none()
    if sampling:
        return "sampling", sampling
    return None, None


@router.get("/admin/users", response_model=Dict[str, Any])
async def admin_get_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
    search: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    _: Member = Depends(get_current_active_admin),
) -> Dict[str, Any]:
    stmt = select(Member)
    if search:
        key = f"%{search}%"
        stmt = stmt.where(
            (Member.name.ilike(key))
            | (Member.username.ilike(key))
            | (Member.student_id.ilike(key))
        )

    total_stmt = select(func.count()).select_from(stmt.subquery())
    total = _to_int((await db.execute(total_stmt)).scalar(), 0)

    rows = (
        await db.execute(
            stmt.order_by(Member.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
    ).scalars().all()

    data = {
        "list": [
            {
                "id": item.id,
                "username": item.username,
                "name": item.name,
                "student_id": item.student_id,
                "role": item.role.value if item.role else None,
                "is_active": item.is_active,
                "created_at": item.created_at.isoformat() if item.created_at else None,
            }
            for item in rows
        ],
        "page": page,
        "page_size": page_size,
        "total": total,
        "total_pages": (total + page_size - 1) // page_size,
        "has_next": page * page_size < total,
    }
    return create_response(data=data, message="获取用户列表成功")


@router.post("/admin/users", response_model=Dict[str, Any])
async def admin_create_user(
    payload: Dict[str, Any],
    db: AsyncSession = Depends(get_db),
    _: Member = Depends(get_current_active_admin),
) -> Dict[str, Any]:
    username = (payload.get("username") or "").strip()
    name = (payload.get("name") or "").strip()
    student_id = (payload.get("student_id") or payload.get("studentNo") or "").strip() or None
    password = payload.get("password") or "123456"
    role_text = (payload.get("role") or "member").strip().lower()

    if not username or not name:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="username/name 不能为空")

    role = UserRole.MEMBER
    if role_text == "admin":
        role = UserRole.ADMIN
    elif role_text in {"group_leader", "leader"}:
        role = UserRole.GROUP_LEADER

    exists = (
        await db.execute(select(Member).where(Member.username == username))
    ).scalar_one_or_none()
    if exists:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="用户名已存在")

    user = Member(
        username=username,
        name=name,
        student_id=student_id,
        phone=payload.get("phone"),
        email=payload.get("email"),
        department=payload.get("department") or "信息化建设处",
        class_name=payload.get("class_name") or payload.get("className") or "默认班级",
        password_hash=get_password_hash(password),
        role=role,
        is_active=bool(payload.get("is_active", True)),
        profile_completed=bool(payload.get("profile_completed", True)),
        is_verified=bool(payload.get("is_verified", True)),
    )
    db.add(user)
    await db.flush()
    await UserSyncService(db).sync_member(user, commit=False)
    await db.commit()
    await db.refresh(user)
    return create_response(
        data={
            "id": user.id,
            "username": user.username,
            "name": user.name,
            "student_id": user.student_id,
        },
        message="创建用户成功",
    )


@router.put("/admin/users/{user_id}/status", response_model=Dict[str, Any])
async def admin_update_user_status(
    user_id: int,
    payload: Dict[str, Any],
    db: AsyncSession = Depends(get_db),
    _: Member = Depends(get_current_active_admin),
) -> Dict[str, Any]:
    user = (await db.execute(select(Member).where(Member.id == user_id))).scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在")

    is_active = payload.get("is_active")
    if is_active is None:
        is_active = payload.get("status") in {1, "1", True, "enabled"}

    user.is_active = bool(is_active)
    await UserSyncService(db).sync_member(user, commit=False)
    await db.commit()
    return create_response(
        data={"id": user.id, "is_active": user.is_active},
        message="更新用户状态成功",
    )


@router.put("/users/profile", response_model=Dict[str, Any])
async def update_my_profile(
    payload: Dict[str, Any],
    db: AsyncSession = Depends(get_db),
    current_user: Member = Depends(get_current_user),
) -> Dict[str, Any]:
    for field in ["name", "phone", "email", "department", "class_name"]:
        if field in payload:
            setattr(current_user, field, payload[field])
    if "className" in payload:
        current_user.class_name = payload["className"]
    if "profile_completed" in payload:
        current_user.profile_completed = bool(payload["profile_completed"])

    await UserSyncService(db).sync_member(current_user, commit=False)
    await db.commit()
    return create_response(
        data={
            "id": current_user.id,
            "name": current_user.name,
            "phone": current_user.phone,
            "email": current_user.email,
            "department": current_user.department,
            "class_name": current_user.class_name,
        },
        message="更新个人资料成功",
    )


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
    biz_type = (payload.get("biz_type") or payload.get("bizType") or "repair").strip()
    if not rule_code or not rule_name:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="rule_code/rule_name 不能为空")

    exists = (
        await db.execute(select(WorkhourRule).where(WorkhourRule.rule_code == rule_code))
    ).scalar_one_or_none()
    if exists:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="rule_code 已存在")

    row = WorkhourRule(
        rule_code=rule_code,
        rule_name=rule_name,
        biz_type=biz_type,
        formula_desc=payload.get("formula_desc") or payload.get("formulaDesc") or "",
        formula_json=payload.get("formula_json") or payload.get("formulaJson") or {},
        is_enabled=bool(payload.get("is_enabled", True)),
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
    total = _to_int((await db.execute(select(func.count()).select_from(stmt.subquery()))).scalar(), 0)
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

    total = _to_int((await db.execute(select(func.count()).select_from(stmt.subquery()))).scalar(), 0)
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

    row = WorkhourEntry(
        biz_type=payload.get("biz_type") or payload.get("bizType") or "repair",
        biz_id=_to_int(payload.get("biz_id") or payload.get("bizId"), 0),
        user_id=user_id,
        source_rule_id=payload.get("source_rule_id") or payload.get("sourceRuleId"),
        base_minutes=_to_int(payload.get("base_minutes") or payload.get("baseMinutes"), 0),
        final_minutes=_to_int(payload.get("final_minutes") or payload.get("finalMinutes"), 0),
        review_status=1,
        reviewed_by=current_user.id,
        reviewed_at=datetime.now(timezone.utc),
        review_note=payload.get("note") or "manual",
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
    db: AsyncSession = Depends(get_db),
    _: Member = Depends(get_current_active_admin),
) -> Dict[str, Any]:
    stmt = select(TodoItem)
    if status_filter is not None:
        stmt = stmt.where(TodoItem.status == status_filter)
    total = _to_int((await db.execute(select(func.count()).select_from(stmt.subquery()))).scalar(), 0)
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


@router.get("/admin/stats/workhours", response_model=Dict[str, Any])
async def admin_stats_workhours(
    db: AsyncSession = Depends(get_db),
    _: Member = Depends(get_current_active_admin),
) -> Dict[str, Any]:
    grouped = (
        await db.execute(
            select(
                WorkhourEntry.biz_type,
                func.count(WorkhourEntry.id),
                func.coalesce(func.sum(WorkhourEntry.final_minutes), 0),
            ).group_by(WorkhourEntry.biz_type)
        )
    ).all()
    pending = _to_int(
        (
            await db.execute(
                select(func.count(WorkhourEntry.id)).where(WorkhourEntry.review_status == 0)
            )
        ).scalar(),
        0,
    )
    return create_response(
        data={
            "by_biz_type": [
                {
                    "biz_type": biz,
                    "count": _to_int(cnt),
                    "final_minutes": _to_int(total_minutes),
                }
                for biz, cnt, total_minutes in grouped
            ],
            "pending_count": pending,
        },
        message="工时统计获取成功",
    )


@router.get("/buildings", response_model=Dict[str, Any])
async def get_buildings(
    db: AsyncSession = Depends(get_db),
    _: Member = Depends(get_current_user),
) -> Dict[str, Any]:
    rows = (await db.execute(select(Building).order_by(Building.id))).scalars().all()
    return create_response(
        data={
            "list": [
                {
                    "id": b.id,
                    "building_code": b.building_code,
                    "building_name": b.building_name,
                    "campus_name": b.campus_name,
                    "area_name": b.area_name,
                    "status": b.status,
                }
                for b in rows
            ],
            "total": len(rows),
        },
        message="获取楼栋成功",
    )


@router.get("/buildings/{building_id}/rooms", response_model=Dict[str, Any])
async def get_building_rooms(
    building_id: int,
    db: AsyncSession = Depends(get_db),
    _: Member = Depends(get_current_user),
) -> Dict[str, Any]:
    rows = (
        await db.execute(
            select(DormRoom)
            .where(DormRoom.building_id == building_id)
            .order_by(DormRoom.room_no)
        )
    ).scalars().all()
    return create_response(
        data={
            "list": [
                {
                    "id": r.id,
                    "building_id": r.building_id,
                    "room_no": r.room_no,
                    "floor_no": r.floor_no,
                    "target_ssid": r.target_ssid,
                    "target_bssid": r.target_bssid,
                    "status": r.status,
                }
                for r in rows
            ],
            "total": len(rows),
        },
        message="获取宿舍列表成功",
    )


@router.post("/admin/rooms/import", response_model=Dict[str, Any])
async def admin_import_rooms(
    payload: Dict[str, Any],
    db: AsyncSession = Depends(get_db),
    _: Member = Depends(get_current_active_admin),
) -> Dict[str, Any]:
    rooms = payload.get("rooms") or []
    if not isinstance(rooms, list):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="rooms 必须是数组")

    created = 0
    updated = 0
    for item in rooms:
        building_id = _to_int(item.get("building_id") or item.get("buildingId"), 0)
        room_no = str(item.get("room_no") or item.get("roomNo") or "").strip()
        if building_id <= 0 or not room_no:
            continue

        row = (
            await db.execute(
                select(DormRoom).where(
                    DormRoom.building_id == building_id,
                    DormRoom.room_no == room_no,
                )
            )
        ).scalar_one_or_none()
        if row is None:
            row = DormRoom(
                building_id=building_id,
                room_no=room_no,
                floor_no=item.get("floor_no") or item.get("floorNo"),
                target_ssid=item.get("target_ssid") or item.get("targetSsid") or "GCC",
                target_bssid=item.get("target_bssid") or item.get("targetBssid") or "UNKNOWN",
                dorm_label=item.get("dorm_label") or item.get("dormLabel"),
                status=_to_int(item.get("status"), 1),
            )
            db.add(row)
            created += 1
        else:
            if "target_ssid" in item or "targetSsid" in item:
                row.target_ssid = item.get("target_ssid") or item.get("targetSsid")
            if "target_bssid" in item or "targetBssid" in item:
                row.target_bssid = item.get("target_bssid") or item.get("targetBssid")
            if "status" in item:
                row.status = _to_int(item.get("status"), row.status)
            updated += 1

    await db.commit()
    return create_response(data={"created": created, "updated": updated}, message="宿舍数据导入完成")


@router.put("/admin/rooms/{room_id}/wifi-profile", response_model=Dict[str, Any])
async def admin_update_room_wifi_profile(
    room_id: int,
    payload: Dict[str, Any],
    db: AsyncSession = Depends(get_db),
    _: Member = Depends(get_current_active_admin),
) -> Dict[str, Any]:
    room = (await db.execute(select(DormRoom).where(DormRoom.id == room_id))).scalar_one_or_none()
    if not room:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="宿舍不存在")

    if "target_ssid" in payload or "targetSsid" in payload:
        room.target_ssid = payload.get("target_ssid") or payload.get("targetSsid")
    if "target_bssid" in payload or "targetBssid" in payload:
        room.target_bssid = payload.get("target_bssid") or payload.get("targetBssid")
    await db.commit()
    return create_response(
        data={"id": room.id, "target_ssid": room.target_ssid, "target_bssid": room.target_bssid},
        message="宿舍无线画像更新成功",
    )


@router.get("/tasks", response_model=Dict[str, Any])
async def get_tasks(
    db: AsyncSession = Depends(get_db),
    _: Member = Depends(get_current_user),
) -> Dict[str, Any]:
    coop_rows = (await db.execute(select(TaskCoop))).scalars().all()
    inspection_rows = (await db.execute(select(TaskInspection))).scalars().all()
    sampling_rows = (await db.execute(select(TaskSampling))).scalars().all()
    rows = [
        {
            "id": x.id,
            "task_type": "coop",
            "task_code": x.task_code,
            "title": x.title,
            "status": x.status,
        }
        for x in coop_rows
    ]
    rows.extend(
        {
            "id": x.id,
            "task_type": "inspection",
            "task_code": x.task_code,
            "title": x.title,
            "status": x.status,
        }
        for x in inspection_rows
    )
    rows.extend(
        {
            "id": x.id,
            "task_type": "sampling",
            "task_code": x.task_code,
            "title": x.title,
            "status": x.status,
        }
        for x in sampling_rows
    )
    return create_response(data={"list": rows, "total": len(rows)}, message="获取任务列表成功")


@router.get("/tasks/{task_id}", response_model=Dict[str, Any])
async def get_task_detail(
    task_id: int,
    db: AsyncSession = Depends(get_db),
    _: Member = Depends(get_current_user),
) -> Dict[str, Any]:
    task_type, task = await _find_task_any(db, task_id)
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="任务不存在")
    return create_response(
        data={
            "id": task.id,
            "task_type": task_type,
            "task_code": task.task_code,
            "title": task.title,
            "description": getattr(task, "description", None),
            "status": task.status,
            "created_at": task.created_at.isoformat() if task.created_at else None,
        },
        message="获取任务详情成功",
    )


@router.post("/admin/tasks", response_model=Dict[str, Any])
async def admin_create_task(
    payload: Dict[str, Any],
    db: AsyncSession = Depends(get_db),
    current_user: Member = Depends(get_current_active_admin),
) -> Dict[str, Any]:
    task_type = (payload.get("task_type") or payload.get("taskType") or "coop").strip()
    title = (payload.get("title") or "新任务").strip()

    if task_type == "inspection":
        row = TaskInspection(
            task_code=_new_code("INSP"),
            title=title,
            description=payload.get("description"),
            building_id=payload.get("building_id") or payload.get("buildingId"),
            assigned_by=current_user.id,
            status=_to_int(payload.get("status"), 1),
        )
    elif task_type == "sampling":
        row = TaskSampling(
            task_code=_new_code("SAMP"),
            title=title,
            description=payload.get("description"),
            building_id=_to_int(payload.get("building_id") or payload.get("buildingId"), 0),
            target_room_count=_to_int(payload.get("target_room_count") or payload.get("targetRoomCount"), 1),
            assigned_by=current_user.id,
            status=_to_int(payload.get("status"), 1),
        )
    else:
        row = TaskCoop(
            task_code=_new_code("COOP"),
            title=title,
            description=payload.get("description"),
            location_text=payload.get("location_text") or payload.get("locationText"),
            building_id=payload.get("building_id") or payload.get("buildingId"),
            signup_need_review=bool(payload.get("signup_need_review", False)),
            sign_in_mode_mask=_to_int(payload.get("sign_in_mode_mask"), 0),
            status=_to_int(payload.get("status"), 1),
            created_by=current_user.id,
        )

    db.add(row)
    await db.commit()
    await db.refresh(row)
    return create_response(data={"id": row.id, "task_code": row.task_code}, message="创建任务成功")


@router.put("/admin/tasks/{task_id}", response_model=Dict[str, Any])
async def admin_update_task(
    task_id: int,
    payload: Dict[str, Any],
    db: AsyncSession = Depends(get_db),
    _: Member = Depends(get_current_active_admin),
) -> Dict[str, Any]:
    _, task = await _find_task_any(db, task_id)
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="任务不存在")

    for field in ["title", "description", "status"]:
        if field in payload:
            setattr(task, field, payload[field])
    await db.commit()
    return create_response(data={"id": task.id}, message="更新任务成功")


@router.post("/admin/tasks/{task_id}/publish", response_model=Dict[str, Any])
async def admin_publish_task(
    task_id: int,
    db: AsyncSession = Depends(get_db),
    _: Member = Depends(get_current_active_admin),
) -> Dict[str, Any]:
    task_type, task = await _find_task_any(db, task_id)
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="任务不存在")
    task.status = 2
    if task_type == "coop":
        task.published_at = datetime.now(timezone.utc)
    await db.commit()
    return create_response(data={"id": task.id, "status": task.status}, message="任务发布成功")


@router.post("/admin/tasks/{task_id}/close", response_model=Dict[str, Any])
async def admin_close_task(
    task_id: int,
    db: AsyncSession = Depends(get_db),
    _: Member = Depends(get_current_active_admin),
) -> Dict[str, Any]:
    _, task = await _find_task_any(db, task_id)
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="任务不存在")
    task.status = 5
    await db.commit()
    return create_response(data={"id": task.id, "status": task.status}, message="任务关闭成功")


@router.post("/admin/tasks/{task_id}/assign", response_model=Dict[str, Any])
async def admin_assign_task(
    task_id: int,
    payload: Dict[str, Any],
    db: AsyncSession = Depends(get_db),
    _: Member = Depends(get_current_active_admin),
) -> Dict[str, Any]:
    user_id = _to_int(payload.get("user_id") or payload.get("userId"), 0)
    if user_id <= 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="user_id 非法")

    task_type, task = await _find_task_any(db, task_id)
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="任务不存在")

    if task_type == "inspection":
        rel = (
            await db.execute(
                select(TaskInspectionUser).where(
                    TaskInspectionUser.inspection_task_id == task_id,
                    TaskInspectionUser.user_id == user_id,
                )
            )
        ).scalar_one_or_none()
        if rel is None:
            db.add(TaskInspectionUser(inspection_task_id=task_id, user_id=user_id, role_in_task="executor"))
    elif task_type == "sampling":
        rel = (
            await db.execute(
                select(TaskSamplingUser).where(
                    TaskSamplingUser.sampling_task_id == task_id,
                    TaskSamplingUser.user_id == user_id,
                )
            )
        ).scalar_one_or_none()
        if rel is None:
            db.add(TaskSamplingUser(sampling_task_id=task_id, user_id=user_id, role_in_task="executor"))
    else:
        slot_id = _to_int(payload.get("slot_id") or payload.get("slotId"), 0)
        if slot_id <= 0:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="协助任务指派需要 slot_id")
        exists = (
            await db.execute(
                select(TaskCoopSignup).where(
                    TaskCoopSignup.coop_slot_id == slot_id,
                    TaskCoopSignup.user_id == user_id,
                )
            )
        ).scalar_one_or_none()
        if exists is None:
            db.add(
                TaskCoopSignup(
                    coop_task_id=task_id,
                    coop_slot_id=slot_id,
                    user_id=user_id,
                    signup_source="assign",
                    status=1,
                )
            )
    await db.commit()
    return create_response(data={"task_id": task_id, "user_id": user_id}, message="任务指派成功")


@router.post("/admin/tasks/{task_id}/slots", response_model=Dict[str, Any])
async def admin_create_task_slot(
    task_id: int,
    payload: Dict[str, Any],
    db: AsyncSession = Depends(get_db),
    _: Member = Depends(get_current_active_admin),
) -> Dict[str, Any]:
    task = (await db.execute(select(TaskCoop).where(TaskCoop.id == task_id))).scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="协助任务不存在")

    start_at = datetime.fromisoformat(str(payload.get("start_time")))
    end_at = datetime.fromisoformat(str(payload.get("end_time")))
    slot = TaskCoopSlot(
        coop_task_id=task_id,
        slot_title=payload.get("slot_title") or payload.get("slotTitle"),
        start_time=start_at,
        end_time=end_at,
        signup_limit=_to_int(payload.get("signup_limit") or payload.get("signupLimit"), 1),
        sort_no=_to_int(payload.get("sort_no") or payload.get("sortNo"), 1),
    )
    db.add(slot)
    await db.commit()
    await db.refresh(slot)
    return create_response(data={"id": slot.id}, message="创建时间段成功")


@router.get("/tasks/{task_id}/slots", response_model=Dict[str, Any])
async def get_task_slots(
    task_id: int,
    db: AsyncSession = Depends(get_db),
    _: Member = Depends(get_current_user),
) -> Dict[str, Any]:
    rows = (
        await db.execute(
            select(TaskCoopSlot).where(TaskCoopSlot.coop_task_id == task_id).order_by(TaskCoopSlot.start_time)
        )
    ).scalars().all()
    return create_response(
        data={
            "list": [
                {
                    "id": s.id,
                    "slot_title": s.slot_title,
                    "start_time": s.start_time.isoformat() if s.start_time else None,
                    "end_time": s.end_time.isoformat() if s.end_time else None,
                    "signup_limit": s.signup_limit,
                    "status": s.status,
                }
                for s in rows
            ],
            "total": len(rows),
        },
        message="获取时间段成功",
    )


@router.post("/tasks/{task_id}/signup", response_model=Dict[str, Any])
async def task_signup(
    task_id: int,
    payload: Dict[str, Any],
    db: AsyncSession = Depends(get_db),
    current_user: Member = Depends(get_current_user),
) -> Dict[str, Any]:
    slot_id = _to_int(payload.get("slot_id") or payload.get("slotId"), 0)
    if slot_id <= 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="slot_id 非法")

    exists = (
        await db.execute(
            select(TaskCoopSignup).where(
                TaskCoopSignup.coop_slot_id == slot_id,
                TaskCoopSignup.user_id == current_user.id,
            )
        )
    ).scalar_one_or_none()
    if exists:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="你已报名该时间段")

    row = TaskCoopSignup(
        coop_task_id=task_id,
        coop_slot_id=slot_id,
        user_id=current_user.id,
        signup_source="self",
        status=1,
    )
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return create_response(data={"id": row.id}, message="报名成功")


@router.post("/tasks/{task_id}/sign-in", response_model=Dict[str, Any])
async def task_sign_in(
    task_id: int,
    payload: Dict[str, Any],
    db: AsyncSession = Depends(get_db),
    current_user: Member = Depends(get_current_user),
) -> Dict[str, Any]:
    slot_id = _to_int(payload.get("slot_id") or payload.get("slotId"), 0)
    signup_stmt = select(TaskCoopSignup).where(
        TaskCoopSignup.coop_task_id == task_id,
        TaskCoopSignup.user_id == current_user.id,
    )
    if slot_id > 0:
        signup_stmt = signup_stmt.where(TaskCoopSignup.coop_slot_id == slot_id)

    signup = (
        await db.execute(signup_stmt)
    ).scalars().first()
    if not signup:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="未找到报名记录")

    att = (
        await db.execute(
            select(TaskCoopAttendance).where(TaskCoopAttendance.coop_signup_id == signup.id)
        )
    ).scalar_one_or_none()
    if att is None:
        att = TaskCoopAttendance(coop_signup_id=signup.id)
        db.add(att)
    elif att.sign_in_at is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="已签到，请勿重复签到")

    att.sign_in_at = datetime.now(timezone.utc)
    att.sign_in_type = str(payload.get("sign_in_type") or "manual")
    await db.commit()
    return create_response(data={"signup_id": signup.id}, message="签到成功")


@router.post("/tasks/{task_id}/sign-out", response_model=Dict[str, Any])
async def task_sign_out(
    task_id: int,
    payload: Dict[str, Any],
    db: AsyncSession = Depends(get_db),
    current_user: Member = Depends(get_current_user),
) -> Dict[str, Any]:
    slot_id = _to_int(payload.get("slot_id") or payload.get("slotId"), 0)
    signup_stmt = select(TaskCoopSignup).where(
        TaskCoopSignup.coop_task_id == task_id,
        TaskCoopSignup.user_id == current_user.id,
    )
    if slot_id > 0:
        signup_stmt = signup_stmt.where(TaskCoopSignup.coop_slot_id == slot_id)

    signup = (
        await db.execute(signup_stmt)
    ).scalars().first()
    if not signup:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="未找到报名记录")

    att = (
        await db.execute(
            select(TaskCoopAttendance).where(TaskCoopAttendance.coop_signup_id == signup.id)
        )
    ).scalar_one_or_none()
    if not att:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="请先签到")
    if att.sign_out_at is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="已签退，请勿重复签退")
    if att.sign_in_at is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="请先签到")

    att.sign_out_at = datetime.now(timezone.utc)
    att.sign_out_type = str(payload.get("sign_out_type") or "manual")
    if att.sign_in_at and att.sign_out_at and att.sign_out_at >= att.sign_in_at:
        att.duration_minutes = int((att.sign_out_at - att.sign_in_at).total_seconds() // 60)
    await db.commit()
    return create_response(data={"signup_id": signup.id, "duration_minutes": att.duration_minutes}, message="签退成功")


@router.post("/tasks/{task_id}/sign/repair", response_model=Dict[str, Any])
async def task_sign_repair(
    task_id: int,
    payload: Dict[str, Any],
    db: AsyncSession = Depends(get_db),
    current_user: Member = Depends(get_current_active_admin),
) -> Dict[str, Any]:
    attendance_id = _to_int(payload.get("attendance_id") or payload.get("sign_record_id"), 0)
    if attendance_id <= 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="attendance_id 非法")
    att = (
        await db.execute(select(TaskCoopAttendance).where(TaskCoopAttendance.id == attendance_id))
    ).scalar_one_or_none()
    if not att:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="签到记录不存在")

    signup = (
        await db.execute(
            select(TaskCoopSignup).where(
                TaskCoopSignup.id == att.coop_signup_id,
                TaskCoopSignup.coop_task_id == task_id,
            )
        )
    ).scalar_one_or_none()
    if not signup:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="签到记录不属于该任务")

    att.admin_confirmed_by = current_user.id
    att.admin_confirmed_at = datetime.now(timezone.utc)
    att.remark = payload.get("remark")
    await db.commit()
    return create_response(data={"id": att.id}, message="补签成功")


@router.get("/admin/tasks/{task_id}/sign-records", response_model=Dict[str, Any])
async def admin_get_sign_records(
    task_id: int,
    db: AsyncSession = Depends(get_db),
    _: Member = Depends(get_current_active_admin),
) -> Dict[str, Any]:
    signup_rows = (
        await db.execute(select(TaskCoopSignup).where(TaskCoopSignup.coop_task_id == task_id))
    ).scalars().all()
    signup_ids = [x.id for x in signup_rows]
    if not signup_ids:
        return create_response(data={"list": [], "total": 0}, message="获取签到记录成功")
    att_rows = (
        await db.execute(select(TaskCoopAttendance).where(TaskCoopAttendance.coop_signup_id.in_(signup_ids)))
    ).scalars().all()
    return create_response(
        data={
            "list": [
                {
                    "id": a.id,
                    "coop_signup_id": a.coop_signup_id,
                    "sign_in_at": a.sign_in_at.isoformat() if a.sign_in_at else None,
                    "sign_out_at": a.sign_out_at.isoformat() if a.sign_out_at else None,
                    "duration_minutes": a.duration_minutes,
                    "review_status": a.review_status,
                }
                for a in att_rows
            ],
            "total": len(att_rows),
        },
        message="获取签到记录成功",
    )


@router.post("/admin/sign-records/{record_id}/approve", response_model=Dict[str, Any])
async def admin_approve_sign_record(
    record_id: int,
    payload: Dict[str, Any],
    db: AsyncSession = Depends(get_db),
    _: Member = Depends(get_current_active_admin),
) -> Dict[str, Any]:
    row = (
        await db.execute(select(TaskCoopAttendance).where(TaskCoopAttendance.id == record_id))
    ).scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="签到记录不存在")
    approve = bool(payload.get("approve", True))
    row.review_status = 1 if approve else 2
    await db.commit()
    return create_response(data={"id": row.id, "review_status": row.review_status}, message="签到审核完成")


@router.post("/admin/tasks/{task_id}/no-show", response_model=Dict[str, Any])
async def admin_mark_no_show(
    task_id: int,
    payload: Dict[str, Any],
    db: AsyncSession = Depends(get_db),
    _: Member = Depends(get_current_active_admin),
) -> Dict[str, Any]:
    signup_id = _to_int(payload.get("signup_id") or payload.get("signupId"), 0)
    row = (
        await db.execute(
            select(TaskCoopSignup).where(
                TaskCoopSignup.id == signup_id,
                TaskCoopSignup.coop_task_id == task_id,
            )
        )
    ).scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="报名记录不存在")
    row.status = 4
    row.cancel_reason = payload.get("reason") or "no_show"
    await db.commit()
    return create_response(data={"id": row.id, "status": row.status}, message="已标记爽约")


@router.post("/admin/tasks/{task_id}/qrcode/generate", response_model=Dict[str, Any])
async def admin_generate_task_qrcode(
    task_id: int,
    db: AsyncSession = Depends(get_db),
    _: Member = Depends(get_current_active_admin),
) -> Dict[str, Any]:
    token = hashlib.sha1(f"task:{task_id}:{datetime.now(timezone.utc):%Y%m%d%H%M}".encode("utf-8")).hexdigest()[:16]
    return create_response(
        data={"task_id": task_id, "qr_token": token, "expires_in": 60},
        message="二维码生成成功",
    )


@router.get("/tasks/{task_id}/qrcode/current", response_model=Dict[str, Any])
async def get_task_qrcode_current(
    task_id: int,
    db: AsyncSession = Depends(get_db),
    _: Member = Depends(get_current_user),
) -> Dict[str, Any]:
    _ = db
    token = hashlib.sha1(f"task:{task_id}:{datetime.now(timezone.utc):%Y%m%d%H%M}".encode("utf-8")).hexdigest()[:16]
    return create_response(
        data={"task_id": task_id, "qr_token": token, "expires_in": 60},
        message="获取当前二维码成功",
    )


@router.post("/admin/tasks/{task_id}/inspection-points", response_model=Dict[str, Any])
async def admin_create_inspection_point(
    task_id: int,
    payload: Dict[str, Any],
    db: AsyncSession = Depends(get_db),
    _: Member = Depends(get_current_active_admin),
) -> Dict[str, Any]:
    task = (await db.execute(select(TaskInspection).where(TaskInspection.id == task_id))).scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="巡检任务不存在")
    row = TaskInspectionPoint(
        inspection_task_id=task_id,
        cabinet_name=payload.get("cabinet_name") or payload.get("cabinetName") or "点位",
        cabinet_location=payload.get("cabinet_location") or payload.get("cabinetLocation"),
        sort_no=_to_int(payload.get("sort_no") or payload.get("sortNo"), 1),
        is_mandatory_photo=bool(payload.get("is_mandatory_photo", True)),
    )
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return create_response(data={"id": row.id}, message="巡检点位创建成功")


@router.get("/tasks/{task_id}/inspection-points", response_model=Dict[str, Any])
async def get_inspection_points(
    task_id: int,
    db: AsyncSession = Depends(get_db),
    _: Member = Depends(get_current_user),
) -> Dict[str, Any]:
    rows = (
        await db.execute(
            select(TaskInspectionPoint)
            .where(TaskInspectionPoint.inspection_task_id == task_id)
            .order_by(TaskInspectionPoint.sort_no)
        )
    ).scalars().all()
    return create_response(
        data={
            "list": [
                {
                    "id": p.id,
                    "cabinet_name": p.cabinet_name,
                    "cabinet_location": p.cabinet_location,
                    "sort_no": p.sort_no,
                }
                for p in rows
            ],
            "total": len(rows),
        },
        message="获取巡检点位成功",
    )


@router.post("/tasks/{task_id}/inspection-records", response_model=Dict[str, Any])
async def create_inspection_record(
    task_id: int,
    payload: Dict[str, Any],
    db: AsyncSession = Depends(get_db),
    current_user: Member = Depends(get_current_user),
) -> Dict[str, Any]:
    point_id = _to_int(payload.get("inspection_point_id") or payload.get("inspectionPointId"), 0)
    if point_id <= 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="inspection_point_id 非法")
    row = InspectionRecord(
        inspection_task_id=task_id,
        inspection_point_id=point_id,
        user_id=current_user.id,
        result_status=_to_int(payload.get("result_status"), 1),
        exception_type=payload.get("exception_type"),
        exception_desc=payload.get("exception_desc"),
        handled_desc=payload.get("handled_desc"),
    )
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return create_response(data={"id": row.id}, message="提交巡检记录成功")


@router.get("/tasks/{task_id}/inspection-records", response_model=Dict[str, Any])
async def get_inspection_records(
    task_id: int,
    db: AsyncSession = Depends(get_db),
    _: Member = Depends(get_current_user),
) -> Dict[str, Any]:
    rows = (
        await db.execute(
            select(InspectionRecord).where(InspectionRecord.inspection_task_id == task_id)
        )
    ).scalars().all()
    return create_response(
        data={
            "list": [
                {
                    "id": r.id,
                    "inspection_point_id": r.inspection_point_id,
                    "user_id": r.user_id,
                    "result_status": r.result_status,
                    "review_status": r.review_status,
                }
                for r in rows
            ],
            "total": len(rows),
        },
        message="获取巡检记录成功",
    )


@router.post("/admin/inspection-records/{record_id}/approve", response_model=Dict[str, Any])
async def admin_approve_inspection_record(
    record_id: int,
    payload: Dict[str, Any],
    db: AsyncSession = Depends(get_db),
    current_user: Member = Depends(get_current_active_admin),
) -> Dict[str, Any]:
    row = (
        await db.execute(select(InspectionRecord).where(InspectionRecord.id == record_id))
    ).scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="巡检记录不存在")
    row.review_status = 1 if bool(payload.get("approve", True)) else 2
    row.reviewed_by = current_user.id
    row.reviewed_at = datetime.now(timezone.utc)
    await db.commit()
    return create_response(data={"id": row.id, "review_status": row.review_status}, message="巡检记录审核完成")


@router.post("/admin/tasks/{task_id}/sampling/generate-targets", response_model=Dict[str, Any])
async def admin_generate_sampling_targets(
    task_id: int,
    payload: Dict[str, Any],
    db: AsyncSession = Depends(get_db),
    _: Member = Depends(get_current_active_admin),
) -> Dict[str, Any]:
    task = (await db.execute(select(TaskSampling).where(TaskSampling.id == task_id))).scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="抽检任务不存在")

    target_count = _to_int(payload.get("target_room_count") or payload.get("targetRoomCount"), task.target_room_count)
    dorm_rows = (
        await db.execute(
            select(DormRoom)
            .where(DormRoom.building_id == task.building_id, DormRoom.status == 1)
            .limit(max(target_count, 1))
        )
    ).scalars().all()

    created = 0
    for room in dorm_rows:
        exists = (
            await db.execute(
                select(TaskSamplingRoom).where(
                    TaskSamplingRoom.sampling_task_id == task_id,
                    TaskSamplingRoom.dorm_room_id == room.id,
                )
            )
        ).scalar_one_or_none()
        if exists is None:
            db.add(
                TaskSamplingRoom(
                    sampling_task_id=task_id,
                    dorm_room_id=room.id,
                    generated_weight=room.active_repair_weight,
                )
            )
            created += 1

    await db.commit()
    return create_response(data={"created": created}, message="抽检目标生成成功")


@router.get("/tasks/{task_id}/sampling/targets", response_model=Dict[str, Any])
async def get_sampling_targets(
    task_id: int,
    db: AsyncSession = Depends(get_db),
    _: Member = Depends(get_current_user),
) -> Dict[str, Any]:
    rows = (
        await db.execute(select(TaskSamplingRoom).where(TaskSamplingRoom.sampling_task_id == task_id))
    ).scalars().all()
    return create_response(
        data={
            "list": [
                {
                    "id": x.id,
                    "dorm_room_id": x.dorm_room_id,
                    "generated_weight": x.generated_weight,
                    "is_completed": x.is_completed,
                }
                for x in rows
            ],
            "total": len(rows),
        },
        message="获取抽检目标成功",
    )


@router.post("/network-tests/start", response_model=Dict[str, Any])
async def network_test_start(
    payload: Dict[str, Any],
    db: AsyncSession = Depends(get_db),
    current_user: Member = Depends(get_current_user),
) -> Dict[str, Any]:
    task_id = _to_int(payload.get("sampling_task_id") or payload.get("task_id"), 0)
    if task_id <= 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="sampling_task_id 非法")

    room_id = _to_int(payload.get("sampling_task_room_id") or payload.get("task_room_id"), 0)
    dorm_room_id = _to_int(payload.get("dorm_room_id") or payload.get("room_id"), 0)
    if room_id <= 0:
        target = (
            await db.execute(select(TaskSamplingRoom).where(TaskSamplingRoom.sampling_task_id == task_id).limit(1))
        ).scalar_one_or_none()
        if not target:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="无可用抽检目标")
        room_id = target.id
        dorm_room_id = target.dorm_room_id

    row = SamplingRecord(
        sampling_task_id=task_id,
        sampling_task_room_id=room_id,
        dorm_room_id=dorm_room_id,
        user_id=current_user.id,
        detect_mode=str(payload.get("detect_mode") or "full"),
        started_at=datetime.now(timezone.utc),
    )
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return create_response(data={"id": row.id}, message="网络检测已开始")


@router.post("/network-tests/{record_id}/submit", response_model=Dict[str, Any])
async def network_test_submit(
    record_id: int,
    payload: Dict[str, Any],
    db: AsyncSession = Depends(get_db),
    current_user: Member = Depends(get_current_user),
) -> Dict[str, Any]:
    row = (
        await db.execute(select(SamplingRecord).where(SamplingRecord.id == record_id))
    ).scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="检测记录不存在")
    if row.user_id != current_user.id and current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权提交该检测记录")

    for field in [
        "current_ssid",
        "current_bssid",
        "bssid_match",
        "ipv4_addr",
        "gateway_addr",
        "dns_list",
        "operator_name",
        "channel_no",
        "negotiated_rate_mbps",
        "signal_strength_dbm",
        "loss_rate_pct",
        "intranet_ping_ms",
        "internet_ping_ms",
        "udp_jitter_ms",
        "udp_loss_rate_pct",
        "tcp_rtt_ms",
        "down_speed_mbps",
        "up_speed_mbps",
        "interference_score",
        "exception_auto",
        "exception_manual",
        "manual_exception_note",
    ]:
        if field in payload:
            setattr(row, field, payload[field])

    row.finished_at = datetime.now(timezone.utc)
    await db.commit()
    return create_response(data={"id": row.id}, message="网络检测提交成功")


@router.post("/network-tests/single-item", response_model=Dict[str, Any])
async def network_test_single_item(
    payload: Dict[str, Any],
    db: AsyncSession = Depends(get_db),
    current_user: Member = Depends(get_current_user),
) -> Dict[str, Any]:
    task_id = _to_int(payload.get("sampling_task_id") or payload.get("task_id"), 0)
    room_id = _to_int(payload.get("sampling_task_room_id") or payload.get("task_room_id"), 0)
    dorm_room_id = _to_int(payload.get("dorm_room_id") or payload.get("room_id"), 0)
    if task_id <= 0 or room_id <= 0 or dorm_room_id <= 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="sampling_task_id/task_room_id/room_id 必填")

    row = SamplingRecord(
        sampling_task_id=task_id,
        sampling_task_room_id=room_id,
        dorm_room_id=dorm_room_id,
        user_id=current_user.id,
        detect_mode="single_item",
        started_at=datetime.now(timezone.utc),
        finished_at=datetime.now(timezone.utc),
        manual_exception_note=payload.get("item") or "single-item",
    )
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return create_response(data={"id": row.id}, message="单项检测提交成功")


@router.get("/network-tests/{record_id}", response_model=Dict[str, Any])
async def network_test_detail(
    record_id: int,
    db: AsyncSession = Depends(get_db),
    _: Member = Depends(get_current_user),
) -> Dict[str, Any]:
    row = (
        await db.execute(select(SamplingRecord).where(SamplingRecord.id == record_id))
    ).scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="检测记录不存在")
    return create_response(
        data={
            "id": row.id,
            "sampling_task_id": row.sampling_task_id,
            "dorm_room_id": row.dorm_room_id,
            "detect_mode": row.detect_mode,
            "bssid_match": row.bssid_match,
            "down_speed_mbps": row.down_speed_mbps,
            "up_speed_mbps": row.up_speed_mbps,
            "review_status": row.review_status,
            "exception_auto": row.exception_auto,
            "exception_manual": row.exception_manual,
        },
        message="获取检测详情成功",
    )


@router.get("/tasks/{task_id}/network-tests", response_model=Dict[str, Any])
async def task_network_tests(
    task_id: int,
    db: AsyncSession = Depends(get_db),
    _: Member = Depends(get_current_user),
) -> Dict[str, Any]:
    rows = (
        await db.execute(select(SamplingRecord).where(SamplingRecord.sampling_task_id == task_id))
    ).scalars().all()
    return create_response(
        data={
            "list": [
                {
                    "id": r.id,
                    "dorm_room_id": r.dorm_room_id,
                    "detect_mode": r.detect_mode,
                    "review_status": r.review_status,
                }
                for r in rows
            ],
            "total": len(rows),
        },
        message="获取任务检测记录成功",
    )


@router.post("/admin/network-tests/{record_id}/approve", response_model=Dict[str, Any])
async def admin_approve_network_test(
    record_id: int,
    payload: Dict[str, Any],
    db: AsyncSession = Depends(get_db),
    current_user: Member = Depends(get_current_active_admin),
) -> Dict[str, Any]:
    row = (
        await db.execute(select(SamplingRecord).where(SamplingRecord.id == record_id))
    ).scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="检测记录不存在")
    row.review_status = 1 if bool(payload.get("approve", True)) else 2
    row.reviewed_by = current_user.id
    row.reviewed_at = datetime.now(timezone.utc)
    await db.commit()
    return create_response(data={"id": row.id, "review_status": row.review_status}, message="检测记录审核完成")


@router.post("/admin/network-tests/{record_id}/mark-abnormal", response_model=Dict[str, Any])
async def admin_mark_network_abnormal(
    record_id: int,
    payload: Dict[str, Any],
    db: AsyncSession = Depends(get_db),
    _: Member = Depends(get_current_active_admin),
) -> Dict[str, Any]:
    row = (
        await db.execute(select(SamplingRecord).where(SamplingRecord.id == record_id))
    ).scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="检测记录不存在")
    row.exception_manual = True
    row.manual_exception_note = payload.get("note") or "marked_by_admin"
    await db.commit()
    return create_response(data={"id": row.id, "exception_manual": row.exception_manual}, message="已标记异常")


@router.post("/repair-orders", response_model=Dict[str, Any])
async def create_repair_order(
    payload: Dict[str, Any],
    db: AsyncSession = Depends(get_db),
    current_user: Member = Depends(get_current_user),
) -> Dict[str, Any]:
    row = RepairTicket(
        repair_no=payload.get("repair_no") or payload.get("repairNo"),
        ticket_source=payload.get("ticket_source") or payload.get("ticketSource") or "offline",
        title=payload.get("title"),
        report_user_name=payload.get("report_user_name") or payload.get("reportUserName"),
        report_phone=payload.get("report_phone") or payload.get("reportPhone"),
        building_id=payload.get("building_id") or payload.get("buildingId"),
        dorm_room_id=payload.get("dorm_room_id") or payload.get("dormRoomId"),
        issue_content=payload.get("issue_content") or payload.get("issueContent"),
        issue_category=payload.get("issue_category") or payload.get("issueCategory"),
        created_by=current_user.id,
    )
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return create_response(data={"id": row.id}, message="创建报修单成功")


@router.put("/repair-orders/{ticket_id}", response_model=Dict[str, Any])
async def update_repair_order(
    ticket_id: int,
    payload: Dict[str, Any],
    db: AsyncSession = Depends(get_db),
    _: Member = Depends(get_current_user),
) -> Dict[str, Any]:
    row = (
        await db.execute(select(RepairTicket).where(RepairTicket.id == ticket_id))
    ).scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="报修单不存在")
    for field in [
        "title",
        "report_user_name",
        "report_phone",
        "issue_content",
        "issue_category",
        "solution_desc",
        "solve_status",
    ]:
        if field in payload:
            setattr(row, field, payload[field])
    await db.commit()
    return create_response(data={"id": row.id}, message="更新报修单成功")


@router.post("/repair-orders/{ticket_id}/participants", response_model=Dict[str, Any])
async def add_repair_order_participant(
    ticket_id: int,
    payload: Dict[str, Any],
    db: AsyncSession = Depends(get_db),
    _: Member = Depends(get_current_user),
) -> Dict[str, Any]:
    user_id = _to_int(payload.get("user_id") or payload.get("userId"), 0)
    if user_id <= 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="user_id 非法")
    exists = (
        await db.execute(
            select(RepairTicketMember).where(
                RepairTicketMember.repair_ticket_id == ticket_id,
                RepairTicketMember.user_id == user_id,
            )
        )
    ).scalar_one_or_none()
    if exists is None:
        db.add(
            RepairTicketMember(
                repair_ticket_id=ticket_id,
                user_id=user_id,
                member_role=payload.get("member_role") or payload.get("memberRole") or "assist",
            )
        )
        await db.commit()
    return create_response(data={"repair_ticket_id": ticket_id, "user_id": user_id}, message="添加参与人成功")


@router.post("/repair-orders/{ticket_id}/ocr", response_model=Dict[str, Any])
async def repair_order_ocr(
    ticket_id: int,
    payload: Dict[str, Any],
    db: AsyncSession = Depends(get_db),
    _: Member = Depends(get_current_user),
) -> Dict[str, Any]:
    row = (
        await db.execute(select(RepairTicket).where(RepairTicket.id == ticket_id))
    ).scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="报修单不存在")
    row.ocr_payload = payload.get("ocr_payload") or payload
    await db.commit()
    return create_response(data={"id": row.id, "ocr_payload": row.ocr_payload}, message="OCR结果已写入")


@router.get("/repair-orders/{ticket_id}/match-candidates", response_model=Dict[str, Any])
async def repair_match_candidates(
    ticket_id: int,
    db: AsyncSession = Depends(get_db),
    _: Member = Depends(get_current_user),
) -> Dict[str, Any]:
    ticket = (
        await db.execute(select(RepairTicket).where(RepairTicket.id == ticket_id))
    ).scalar_one_or_none()
    if not ticket:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="报修单不存在")

    stmt = select(ImportRepairRow)
    if ticket.repair_no:
        stmt = stmt.where(ImportRepairRow.repair_no == ticket.repair_no)
    rows = (await db.execute(stmt.limit(20))).scalars().all()
    return create_response(
        data={
            "list": [
                {
                    "id": r.id,
                    "repair_no": r.repair_no,
                    "report_user_name": r.report_user_name,
                    "report_phone": r.report_phone,
                    "issue_content": r.issue_content,
                }
                for r in rows
            ],
            "total": len(rows),
        },
        message="获取匹配候选成功",
    )


@router.post("/repair-orders/{ticket_id}/match", response_model=Dict[str, Any])
async def repair_apply_match(
    ticket_id: int,
    payload: Dict[str, Any],
    db: AsyncSession = Depends(get_db),
    current_user: Member = Depends(get_current_user),
) -> Dict[str, Any]:
    row_id = _to_int(payload.get("import_repair_row_id") or payload.get("importRepairRowId"), 0)
    if row_id <= 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="import_repair_row_id 非法")

    ticket = (
        await db.execute(select(RepairTicket).where(RepairTicket.id == ticket_id))
    ).scalar_one_or_none()
    if not ticket:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="报修单不存在")

    if ticket.created_by != current_user.id and current_user.role != UserRole.ADMIN:
        participant = (
            await db.execute(
                select(RepairTicketMember).where(
                    RepairTicketMember.repair_ticket_id == ticket_id,
                    RepairTicketMember.user_id == current_user.id,
                )
            )
        ).scalar_one_or_none()
        if participant is None:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权为该报修单申请匹配")

    import_row = (
        await db.execute(select(ImportRepairRow).where(ImportRepairRow.id == row_id))
    ).scalar_one_or_none()
    if not import_row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="导入明细不存在")

    exists = (
        await db.execute(
            select(RepairMatchApplication).where(RepairMatchApplication.repair_ticket_id == ticket_id)
        )
    ).scalar_one_or_none()
    if exists:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="该报修单已提交匹配申请")

    app = RepairMatchApplication(
        repair_ticket_id=ticket_id,
        import_repair_row_id=row_id,
        applied_by=current_user.id,
        apply_note=payload.get("note"),
        status=0,
    )
    db.add(app)
    await db.commit()
    await db.refresh(app)
    return create_response(data={"id": app.id}, message="匹配申请已提交")


@router.post("/admin/repair-orders/{ticket_id}/approve-match", response_model=Dict[str, Any])
async def admin_approve_repair_match(
    ticket_id: int,
    payload: Dict[str, Any],
    db: AsyncSession = Depends(get_db),
    current_user: Member = Depends(get_current_active_admin),
) -> Dict[str, Any]:
    app = (
        await db.execute(
            select(RepairMatchApplication).where(RepairMatchApplication.repair_ticket_id == ticket_id)
        )
    ).scalar_one_or_none()
    ticket = (
        await db.execute(select(RepairTicket).where(RepairTicket.id == ticket_id))
    ).scalar_one_or_none()
    if not app or not ticket:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="匹配申请不存在")
    if app.status != 0:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="匹配申请已审核")

    approve = bool(payload.get("approve", True))
    app.status = 1 if approve else 2
    app.reviewed_by = current_user.id
    app.reviewed_at = datetime.now(timezone.utc)

    if approve:
        import_row = (
            await db.execute(select(ImportRepairRow).where(ImportRepairRow.id == app.import_repair_row_id))
        ).scalar_one_or_none()
        if not import_row:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="关联导入明细不存在")

        ticket.match_status = 2
        ticket.matched_import_row_id = app.import_repair_row_id
    else:
        ticket.match_status = 3

    await db.commit()
    return create_response(data={"repair_ticket_id": ticket_id, "status": app.status}, message="报修匹配审核完成")


@router.post("/admin/repair-imports", response_model=Dict[str, Any])
async def admin_create_repair_import(
    payload: Dict[str, Any],
    db: AsyncSession = Depends(get_db),
    current_user: Member = Depends(get_current_active_admin),
) -> Dict[str, Any]:
    rows = payload.get("rows") or []
    batch = ImportBatch(
        batch_type="repair_total",
        file_name=payload.get("file_name") or payload.get("fileName") or "manual_import",
        imported_by=current_user.id,
        total_rows=len(rows),
        success_rows=len(rows),
        failed_rows=0,
        status=2,
        finished_at=datetime.now(timezone.utc),
    )
    db.add(batch)
    await db.flush()

    for item in rows:
        db.add(
            ImportRepairRow(
                import_batch_id=batch.id,
                repair_no=item.get("repair_no") or item.get("repairNo"),
                report_user_name=item.get("report_user_name") or item.get("reportUserName"),
                report_phone=item.get("report_phone") or item.get("reportPhone"),
                building_name=item.get("building_name") or item.get("buildingName"),
                room_no=item.get("room_no") or item.get("roomNo"),
                issue_content=item.get("issue_content") or item.get("issueContent"),
                raw_payload=item,
            )
        )
    await db.commit()
    return create_response(data={"batch_id": batch.id, "total_rows": len(rows)}, message="报修导入批次创建成功")


@router.post("/media/upload-image", response_model=Dict[str, Any])
async def upload_image(
    file: UploadFile = File(...),
    biz_type: str = Form("general"),
    biz_id: int = Form(0),
    db: AsyncSession = Depends(get_db),
    current_user: Member = Depends(get_current_user),
) -> Dict[str, Any]:
    ext = Path(file.filename or "image.jpg").suffix or ".jpg"
    name = f"img_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}_{hashlib.sha1(os.urandom(16)).hexdigest()[:8]}{ext}"
    target = _uploads_dir() / name
    content = await file.read()
    target.write_bytes(content)

    row = MediaFile(
        biz_type=biz_type,
        biz_id=biz_id,
        file_type="image",
        storage_path=str(target),
        file_name=file.filename or name,
        content_type=file.content_type,
        file_size=len(content),
        uploaded_by=current_user.id,
    )
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return create_response(
        data={"id": row.id, "file_name": row.file_name, "file_url": f"/uploads/{name}", "file_type": row.file_type},
        message="图片上传成功",
    )


@router.post("/media/upload-video", response_model=Dict[str, Any])
async def upload_video(
    file: UploadFile = File(...),
    biz_type: str = Form("general"),
    biz_id: int = Form(0),
    db: AsyncSession = Depends(get_db),
    current_user: Member = Depends(get_current_user),
) -> Dict[str, Any]:
    ext = Path(file.filename or "video.mp4").suffix or ".mp4"
    name = f"video_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}_{hashlib.sha1(os.urandom(16)).hexdigest()[:8]}{ext}"
    target = _uploads_dir() / name
    content = await file.read()
    target.write_bytes(content)

    row = MediaFile(
        biz_type=biz_type,
        biz_id=biz_id,
        file_type="video",
        storage_path=str(target),
        file_name=file.filename or name,
        content_type=file.content_type,
        file_size=len(content),
        uploaded_by=current_user.id,
    )
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return create_response(
        data={"id": row.id, "file_name": row.file_name, "file_url": f"/uploads/{name}", "file_type": row.file_type},
        message="视频上传成功",
    )


@router.get("/media/{media_id}", response_model=Dict[str, Any])
async def get_media(
    media_id: int,
    db: AsyncSession = Depends(get_db),
    _: Member = Depends(get_current_user),
) -> Dict[str, Any]:
    row = (await db.execute(select(MediaFile).where(MediaFile.id == media_id))).scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="媒体不存在")
    return create_response(
        data={
            "id": row.id,
            "biz_type": row.biz_type,
            "biz_id": row.biz_id,
            "file_type": row.file_type,
            "file_name": row.file_name,
            "storage_path": row.storage_path,
            "file_size": row.file_size,
            "watermark_payload": row.watermark_payload,
        },
        message="获取媒体成功",
    )


@router.post("/internal/workhours/recalculate", response_model=Dict[str, Any])
async def recalculate_workhours(
    payload: Dict[str, Any],
    db: AsyncSession = Depends(get_db),
    _: Member = Depends(get_current_active_admin),
) -> Dict[str, Any]:
    entry_id = _to_int(payload.get("entry_id") or payload.get("entryId"), 0)
    updated = 0
    if entry_id > 0:
        row = (
            await db.execute(select(WorkhourEntry).where(WorkhourEntry.id == entry_id))
        ).scalar_one_or_none()
        if row:
            row.final_minutes = row.base_minutes
            updated = 1
    else:
        rows = (
            await db.execute(select(WorkhourEntry).where(WorkhourEntry.review_status == 0))
        ).scalars().all()
        for row in rows:
            row.final_minutes = row.base_minutes
            updated += 1
    await db.commit()
    return create_response(data={"updated": updated}, message="工时重算完成")


@router.get("/admin/stats/repair-problems", response_model=Dict[str, Any])
async def admin_stats_repair_problems(
    db: AsyncSession = Depends(get_db),
    _: Member = Depends(get_current_active_admin),
) -> Dict[str, Any]:
    rows = (
        await db.execute(
            select(RepairTicket.issue_category, func.count(RepairTicket.id)).group_by(RepairTicket.issue_category)
        )
    ).all()
    return create_response(
        data={
            "list": [
                {"issue_category": x[0] or "unknown", "count": _to_int(x[1])}
                for x in rows
            ]
        },
        message="报修问题统计成功",
    )


@router.get("/admin/stats/rankings", response_model=Dict[str, Any])
async def admin_stats_rankings(
    db: AsyncSession = Depends(get_db),
    _: Member = Depends(get_current_active_admin),
) -> Dict[str, Any]:
    rows = (
        await db.execute(
            select(WorkhourEntry.user_id, func.coalesce(func.sum(WorkhourEntry.final_minutes), 0))
            .group_by(WorkhourEntry.user_id)
            .order_by(func.coalesce(func.sum(WorkhourEntry.final_minutes), 0).desc())
            .limit(20)
        )
    ).all()
    return create_response(
        data={"list": [{"user_id": x[0], "final_minutes": _to_int(x[1])} for x in rows]},
        message="工时排行统计成功",
    )


@router.get("/admin/stats/network-quality", response_model=Dict[str, Any])
async def admin_stats_network_quality(
    db: AsyncSession = Depends(get_db),
    _: Member = Depends(get_current_active_admin),
) -> Dict[str, Any]:
    summary = (
        await db.execute(
            select(
                func.count(SamplingRecord.id),
                func.coalesce(func.avg(SamplingRecord.down_speed_mbps), 0),
                func.coalesce(func.avg(SamplingRecord.up_speed_mbps), 0),
                func.coalesce(func.avg(SamplingRecord.internet_ping_ms), 0),
            )
        )
    ).first()
    abnormal = _to_int(
        (
            await db.execute(
                select(func.count(SamplingRecord.id)).where(
                    (SamplingRecord.exception_auto.is_(True))
                    | (SamplingRecord.exception_manual.is_(True))
                )
            )
        ).scalar(),
        0,
    )
    return create_response(
        data={
            "total_tests": _to_int(summary[0] if summary else 0),
            "avg_down_speed_mbps": float(summary[1] if summary else 0),
            "avg_up_speed_mbps": float(summary[2] if summary else 0),
            "avg_internet_ping_ms": float(summary[3] if summary else 0),
            "abnormal_count": abnormal,
        },
        message="网络质量统计成功",
    )