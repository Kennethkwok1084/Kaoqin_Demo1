"""Coop task workflow APIs (formal domain router).

This module receives migrated endpoints from doc_compat and keeps
stable behaviors while enabling gradual compatibility-layer shrink.
"""

import hashlib
import hmac
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import create_response, get_current_active_admin, get_current_user, get_db
from app.core.config import settings
from app.models.member import Member
from app.models.sampling_record import SamplingRecord
from app.models.system_config import SystemConfig
from app.models.task_coop import TaskCoop
from app.models.task_coop_attendance import TaskCoopAttendance
from app.models.task_coop_signup import TaskCoopSignup
from app.models.task_coop_slot import TaskCoopSlot
from app.models.todo_item import TodoItem

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


def _build_legacy_qr_token(task_id: int, token_bucket: int) -> str:
    return hashlib.sha1(f"task:{task_id}:{token_bucket}".encode("utf-8")).hexdigest()[:16]


def _build_signed_qr_token(task_id: int, token_bucket: int) -> str:
    secret = str(getattr(settings, "SECRET_KEY", "") or "default-secret")
    payload = f"task:{task_id}:{token_bucket}".encode("utf-8")
    signature = hmac.new(secret.encode("utf-8"), payload, hashlib.sha256).hexdigest()[:16]
    return f"{token_bucket}.{signature}"


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


async def _validate_coop_slot_for_signup(
    db: AsyncSession,
    task_id: int,
    slot_id: int,
) -> TaskCoopSlot:
    slot = (
        await db.execute(
            select(TaskCoopSlot).where(
                TaskCoopSlot.id == slot_id,
                TaskCoopSlot.coop_task_id == task_id,
                TaskCoopSlot.status == 1,
            )
        )
    ).scalar_one_or_none()
    if not slot:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="时间段不存在或不可报名")

    active_signup_count = _to_int(
        (
            await db.execute(
                select(func.count()).where(
                    TaskCoopSignup.coop_slot_id == slot_id,
                    TaskCoopSignup.status.in_([0, 1]),
                )
            )
        ).scalar(),
        0,
    )
    if slot.signup_limit > 0 and active_signup_count >= slot.signup_limit:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="该时间段报名名额已满")
    return slot


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

    task = (await db.execute(select(TaskCoop).where(TaskCoop.id == task_id))).scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="协助任务不存在")

    await _validate_coop_slot_for_signup(db, task_id, slot_id)

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
        status=0 if task.signup_need_review else 1,
    )
    db.add(row)
    await db.commit()
    await db.refresh(row)
    if task.signup_need_review:
        return create_response(data={"id": row.id, "status": row.status}, message="报名申请已提交，待审核")
    return create_response(data={"id": row.id, "status": row.status}, message="报名成功")


@router.get("/admin/tasks/{task_id}/signups", response_model=Dict[str, Any])
async def admin_get_task_signups(
    task_id: int,
    status_filter: Optional[int] = Query(None, alias="status"),
    db: AsyncSession = Depends(get_db),
    _: Member = Depends(get_current_active_admin),
) -> Dict[str, Any]:
    stmt = select(TaskCoopSignup).where(TaskCoopSignup.coop_task_id == task_id)
    if status_filter is not None:
        stmt = stmt.where(TaskCoopSignup.status == status_filter)

    rows = (await db.execute(stmt.order_by(TaskCoopSignup.id.desc()))).scalars().all()
    return create_response(
        data={
            "list": [
                {
                    "id": s.id,
                    "coop_slot_id": s.coop_slot_id,
                    "user_id": s.user_id,
                    "status": s.status,
                    "signup_source": s.signup_source,
                    "reviewed_by": s.reviewed_by,
                    "reviewed_at": s.reviewed_at.isoformat() if s.reviewed_at else None,
                    "cancel_reason": s.cancel_reason,
                }
                for s in rows
            ],
            "total": len(rows),
        },
        message="获取报名记录成功",
    )


@router.post("/admin/tasks/{task_id}/signups/{signup_id}/review", response_model=Dict[str, Any])
async def admin_review_task_signup(
    task_id: int,
    signup_id: int,
    payload: Dict[str, Any],
    db: AsyncSession = Depends(get_db),
    current_user: Member = Depends(get_current_active_admin),
) -> Dict[str, Any]:
    signup = (
        await db.execute(
            select(TaskCoopSignup).where(
                TaskCoopSignup.id == signup_id,
                TaskCoopSignup.coop_task_id == task_id,
            )
        )
    ).scalar_one_or_none()
    if not signup:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="报名记录不存在")

    if signup.status in {3, 4}:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="当前报名状态不可审核")

    approve = _to_bool(payload.get("approve"), True)
    signup.status = 1 if approve else 2
    signup.reviewed_by = current_user.id
    signup.reviewed_at = datetime.now(timezone.utc)
    signup.cancel_reason = None if approve else (payload.get("reason") or "review_rejected")
    await db.commit()
    return create_response(
        data={"id": signup.id, "status": signup.status},
        message="报名审核通过" if approve else "报名审核驳回",
    )


@router.post("/tasks/{task_id}/sign/repair", response_model=Dict[str, Any])
async def task_sign_repair(
    task_id: int,
    payload: Dict[str, Any],
    db: AsyncSession = Depends(get_db),
    current_user: Member = Depends(get_current_active_admin),
) -> Dict[str, Any]:
    now = datetime.now(timezone.utc)
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

    approve = _to_bool(payload.get("approve"), True)

    if approve:
        if att.sign_in_at is None:
            att.sign_in_at = att.sign_out_at if att.sign_out_at else now
            att.sign_in_type = "admin"
        if att.sign_out_at and att.sign_out_at >= att.sign_in_at:
            att.duration_minutes = int((att.sign_out_at - att.sign_in_at).total_seconds() // 60)
        att.admin_confirmed_by = current_user.id
        att.admin_confirmed_at = now
        att.review_status = 1
    else:
        att.review_status = 2

    remark = payload.get("remark")
    if remark is not None:
        att.remark = remark

    todo_rows = (
        await db.execute(
            select(TodoItem).where(
                TodoItem.todo_type == "coop_sign_repair",
                TodoItem.source_biz_type == "task_coop_attendance",
                TodoItem.source_biz_id == att.id,
                TodoItem.status.in_([0, 1]),
            )
        )
    ).scalars().all()
    for item in todo_rows:
        item.status = 2
        item.assignee_user_id = current_user.id
        item.resolved_at = now

    await db.commit()
    return create_response(
        data={"id": att.id, "review_status": att.review_status},
        message="补签审核通过" if approve else "补签审核驳回",
    )


@router.post("/tasks/{task_id}/sign/repair/request", response_model=Dict[str, Any])
async def task_sign_repair_request(
    task_id: int,
    payload: Dict[str, Any],
    db: AsyncSession = Depends(get_db),
    current_user: Member = Depends(get_current_user),
) -> Dict[str, Any]:
    attendance_id = _to_int(payload.get("attendance_id") or payload.get("sign_record_id"), 0)

    reason = str(payload.get("reason") or payload.get("remark") or "").strip()
    if not reason:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="补签原因不能为空")

    att: Optional[TaskCoopAttendance] = None
    if attendance_id > 0:
        att = (
            await db.execute(
                select(TaskCoopAttendance)
                .join(TaskCoopSignup, TaskCoopSignup.id == TaskCoopAttendance.coop_signup_id)
                .where(
                    TaskCoopAttendance.id == attendance_id,
                    TaskCoopSignup.coop_task_id == task_id,
                    TaskCoopSignup.user_id == current_user.id,
                )
            )
        ).scalar_one_or_none()
        if not att:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="签到记录不存在或无权申请")
    else:
        slot_id = _to_int(payload.get("slot_id") or payload.get("slotId"), 0)
        signup_stmt = select(TaskCoopSignup).where(
            TaskCoopSignup.coop_task_id == task_id,
            TaskCoopSignup.user_id == current_user.id,
        )
        if slot_id > 0:
            signup_stmt = signup_stmt.where(TaskCoopSignup.coop_slot_id == slot_id)

        signup = (await db.execute(signup_stmt.order_by(TaskCoopSignup.id.desc()))).scalars().first()
        if not signup:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="未找到报名记录，无法申请补签")

        att = (
            await db.execute(
                select(TaskCoopAttendance).where(TaskCoopAttendance.coop_signup_id == signup.id)
            )
        ).scalar_one_or_none()
        if not att:
            att = TaskCoopAttendance(coop_signup_id=signup.id)
            db.add(att)
            await db.flush()

    pending_todo = (
        await db.execute(
            select(TodoItem).where(
                TodoItem.todo_type == "coop_sign_repair",
                TodoItem.source_biz_type == "task_coop_attendance",
                TodoItem.source_biz_id == att.id,
                TodoItem.status.in_([0, 1]),
            )
        )
    ).scalars().first()
    if pending_todo:
        return create_response(
            data={"request_id": pending_todo.id, "attendance_id": att.id, "review_status": att.review_status},
            message="补签申请已提交，请勿重复申请",
        )

    now = datetime.now(timezone.utc)
    todo = TodoItem(
        todo_type="coop_sign_repair",
        source_biz_type="task_coop_attendance",
        source_biz_id=att.id,
        title=f"补签申请-任务{task_id}-用户{current_user.id}",
        content=reason,
        priority_level=2,
        status=0,
    )
    db.add(todo)

    att.review_status = 0
    att.remark = reason
    await db.commit()
    await db.refresh(todo)
    return create_response(
        data={"request_id": todo.id, "attendance_id": att.id, "review_status": att.review_status},
        message="补签申请提交成功",
    )


@router.post("/admin/tasks/{task_id}/qrcode/generate", response_model=Dict[str, Any])
async def admin_generate_task_qrcode(
    task_id: int,
    db: AsyncSession = Depends(get_db),
    _: Member = Depends(get_current_active_admin),
) -> Dict[str, Any]:
    task = (await db.execute(select(TaskCoop).where(TaskCoop.id == task_id))).scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="协助任务不存在")

    expires_in = await _get_system_config_int(
        db,
        keys=["checkin_qrcode_refresh_seconds", "task_qrcode_refresh_seconds", "qrcode_refresh_seconds"],
        default=60,
        min_value=15,
        max_value=1800,
    )
    token_bucket = int(datetime.now(timezone.utc).timestamp() // expires_in)
    token = _build_signed_qr_token(task_id, token_bucket)
    legacy_token = _build_legacy_qr_token(task_id, token_bucket)
    return create_response(
        data={
            "task_id": task_id,
            "qr_token": token,
            "qr_token_legacy": legacy_token,
            "expires_in": expires_in,
        },
        message="二维码生成成功",
    )


@router.get("/tasks/{task_id}/qrcode/current", response_model=Dict[str, Any])
async def get_task_qrcode_current(
    task_id: int,
    db: AsyncSession = Depends(get_db),
    _: Member = Depends(get_current_user),
) -> Dict[str, Any]:
    task = (await db.execute(select(TaskCoop).where(TaskCoop.id == task_id))).scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="协助任务不存在")

    expires_in = await _get_system_config_int(
        db,
        keys=["checkin_qrcode_refresh_seconds", "task_qrcode_refresh_seconds", "qrcode_refresh_seconds"],
        default=60,
        min_value=15,
        max_value=1800,
    )
    token_bucket = int(datetime.now(timezone.utc).timestamp() // expires_in)
    token = _build_signed_qr_token(task_id, token_bucket)
    legacy_token = _build_legacy_qr_token(task_id, token_bucket)
    return create_response(
        data={
            "task_id": task_id,
            "qr_token": token,
            "qr_token_legacy": legacy_token,
            "expires_in": expires_in,
        },
        message="获取当前二维码成功",
    )


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

    loss_threshold = await _get_system_config_int(
        db,
        keys=["network_loss_threshold_pct", "sampling_network_loss_threshold_pct"],
        default=5,
        min_value=0,
        max_value=100,
    )
    rtt_threshold = await _get_system_config_int(
        db,
        keys=["network_tcp_rtt_threshold_ms", "sampling_network_tcp_rtt_threshold_ms"],
        default=200,
        min_value=1,
        max_value=10000,
    )

    reasons = []
    if row.loss_rate_pct is not None and float(row.loss_rate_pct) > float(loss_threshold):
        reasons.append(f"丢包率超阈值({float(row.loss_rate_pct):.2f}%>{loss_threshold}%)")
    if row.tcp_rtt_ms is not None and float(row.tcp_rtt_ms) > float(rtt_threshold):
        reasons.append(f"TCP时延超阈值({float(row.tcp_rtt_ms):.2f}ms>{rtt_threshold}ms)")

    only_if_threshold_exceeded = _to_bool(payload.get("only_if_threshold_exceeded"), False)
    if only_if_threshold_exceeded and not reasons:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="检测指标未达到异常阈值，未执行标记")

    default_note = await _get_system_config_text(
        db,
        keys=["network_abnormal_default_note"],
        default="marked_by_admin",
    )
    row.exception_manual = True
    row.manual_exception_note = payload.get("note") or ("; ".join(reasons) if reasons else default_note)
    await db.commit()
    return create_response(data={"id": row.id, "exception_manual": row.exception_manual}, message="已标记异常")
