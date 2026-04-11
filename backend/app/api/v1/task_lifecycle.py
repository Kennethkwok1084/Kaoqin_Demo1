"""正式任务生命周期相关路由。"""

import json
import hashlib
import hmac
import math
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import create_response, get_current_active_admin, get_current_user, get_db
from app.core.config import settings
from app.models.building import Building
from app.models.member import Member
from app.models.system_config import SystemConfig
from app.models.task_coop import TaskCoop
from app.models.task_coop_attendance import TaskCoopAttendance
from app.models.task_coop_signup import TaskCoopSignup
from app.models.task_coop_slot import TaskCoopSlot
from app.models.task_inspection import TaskInspection
from app.models.task_inspection_user import TaskInspectionUser
from app.models.task_sampling import TaskSampling
from app.models.task_sampling_user import TaskSamplingUser
from app.models.todo_item import TodoItem

router = APIRouter()


def _to_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _to_float(value: Any, default: float | None = None) -> float | None:
    try:
        if value is None:
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _to_bool(value: Any, default: bool = False) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "on", "y"}


def _new_code(prefix: str) -> str:
    now = datetime.now(timezone.utc)
    digest = hashlib.sha1(f"{prefix}:{now.timestamp()}".encode("utf-8")).hexdigest()[:6]
    return f"{prefix}-{now.strftime('%Y%m%d%H%M%S')}-{digest}"


async def _get_system_config_int(
    db: AsyncSession,
    keys: list[str],
    default: int,
    min_value: int = 0,
    max_value: int = 100000,
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


def _build_legacy_qr_token(task_id: int, token_bucket: int) -> str:
    return hashlib.sha1(f"task:{task_id}:{token_bucket}".encode("utf-8")).hexdigest()[:16]


def _build_signed_qr_token(task_id: int, token_bucket: int) -> str:
    secret = str(getattr(settings, "SECRET_KEY", "") or "default-secret")
    payload = f"task:{task_id}:{token_bucket}".encode("utf-8")
    signature = hmac.new(secret.encode("utf-8"), payload, hashlib.sha256).hexdigest()[:16]
    return f"{token_bucket}.{signature}"


async def _validate_qr_token(
    db: AsyncSession,
    task_id: int,
    qr_token: str,
) -> bool:
    expires_in = await _get_system_config_int(
        db,
        keys=["checkin_qrcode_refresh_seconds", "task_qrcode_refresh_seconds", "qrcode_refresh_seconds"],
        default=60,
        min_value=15,
        max_value=1800,
    )
    allow_legacy = bool(
        await _get_system_config_int(
            db,
            keys=["checkin_qr_allow_legacy_token"],
            default=1,
            min_value=0,
            max_value=1,
        )
    )
    now_bucket = int(datetime.now(timezone.utc).timestamp() // expires_in)
    candidate_tokens = {
        _build_signed_qr_token(task_id, now_bucket),
        _build_signed_qr_token(task_id, now_bucket - 1),
    }
    if allow_legacy:
        candidate_tokens.add(_build_legacy_qr_token(task_id, now_bucket))
        candidate_tokens.add(_build_legacy_qr_token(task_id, now_bucket - 1))
    return qr_token in candidate_tokens


def _extract_longitude(payload: Dict[str, Any], prefix: str) -> float | None:
    return _to_float(
        payload.get(f"{prefix}_longitude")
        or payload.get(f"{prefix}Longitude")
        or payload.get("longitude")
        or payload.get("lng")
    )


def _extract_latitude(payload: Dict[str, Any], prefix: str) -> float | None:
    return _to_float(
        payload.get(f"{prefix}_latitude")
        or payload.get(f"{prefix}Latitude")
        or payload.get("latitude")
        or payload.get("lat")
    )


def _distance_meters(lon1: float, lat1: float, lon2: float, lat2: float) -> float:
    radius = 6371000.0
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    d_phi = math.radians(lat2 - lat1)
    d_lambda = math.radians(lon2 - lon1)
    a = (
        math.sin(d_phi / 2.0) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(d_lambda / 2.0) ** 2
    )
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return radius * c


def _parse_attendance_meta(raw_remark: str | None) -> Dict[str, Any]:
    if not raw_remark:
        return {}
    try:
        value = json.loads(raw_remark)
        return value if isinstance(value, dict) else {}
    except (TypeError, ValueError):
        return {"legacy_remark": raw_remark}


async def _create_sign_abnormal_todo(
    db: AsyncSession,
    task_id: int,
    source_biz_type: str,
    source_biz_id: int,
    user_id: int,
    reason: str,
    detail: str,
) -> None:
    exists = (
        await db.execute(
            select(TodoItem).where(
                TodoItem.todo_type == "coop_sign_abnormal",
                TodoItem.source_biz_type == source_biz_type,
                TodoItem.source_biz_id == source_biz_id,
                TodoItem.status.in_([0, 1]),
            )
        )
    ).scalar_one_or_none()
    if exists:
        return

    db.add(
        TodoItem(
            todo_type="coop_sign_abnormal",
            source_biz_type=source_biz_type,
            source_biz_id=source_biz_id,
            title=f"签到异常-任务{task_id}-用户{user_id}",
            content=f"{reason}: {detail}",
            priority_level=1,
            status=0,
        )
    )


async def _reject_with_abnormal_todo(
    db: AsyncSession,
    task_id: int,
    source_biz_type: str,
    source_biz_id: int,
    user_id: int,
    reason: str,
    detail: str,
) -> None:
    await _create_sign_abnormal_todo(
        db=db,
        task_id=task_id,
        source_biz_type=source_biz_type,
        source_biz_id=source_biz_id,
        user_id=user_id,
        reason=reason,
        detail=detail,
    )
    await db.commit()
    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=reason)


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


async def _find_task_any(
    db: AsyncSession,
    task_id: int,
    task_type_hint: Optional[str] = None,
) -> tuple[str, Any] | tuple[None, None]:
    task_type = (task_type_hint or "").strip().lower()

    if task_type == "coop":
        row = (await db.execute(select(TaskCoop).where(TaskCoop.id == task_id))).scalar_one_or_none()
        return ("coop", row) if row else (None, None)
    if task_type == "inspection":
        row = (
            await db.execute(select(TaskInspection).where(TaskInspection.id == task_id))
        ).scalar_one_or_none()
        return ("inspection", row) if row else (None, None)
    if task_type == "sampling":
        row = (
            await db.execute(select(TaskSampling).where(TaskSampling.id == task_id))
        ).scalar_one_or_none()
        return ("sampling", row) if row else (None, None)

    matches: list[tuple[str, Any]] = []
    coop = (await db.execute(select(TaskCoop).where(TaskCoop.id == task_id))).scalar_one_or_none()
    if coop:
        matches.append(("coop", coop))
    inspection = (
        await db.execute(select(TaskInspection).where(TaskInspection.id == task_id))
    ).scalar_one_or_none()
    if inspection:
        matches.append(("inspection", inspection))
    sampling = (
        await db.execute(select(TaskSampling).where(TaskSampling.id == task_id))
    ).scalar_one_or_none()
    if sampling:
        matches.append(("sampling", sampling))

    if not matches:
        return None, None
    if len(matches) > 1:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="任务ID存在歧义，请提供 task_type (coop/inspection/sampling)",
        )
    return matches[0]


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
    task_type: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    _: Member = Depends(get_current_user),
) -> Dict[str, Any]:
    task_type, task = await _find_task_any(db, task_id, task_type)
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
    task_type_hint = payload.get("task_type") or payload.get("taskType")
    _, task = await _find_task_any(db, task_id, task_type_hint)
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
    task_type: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    _: Member = Depends(get_current_active_admin),
) -> Dict[str, Any]:
    task_type, task = await _find_task_any(db, task_id, task_type)
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
    task_type: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    _: Member = Depends(get_current_active_admin),
) -> Dict[str, Any]:
    _, task = await _find_task_any(db, task_id, task_type)
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

    task_type_hint = payload.get("task_type") or payload.get("taskType")
    task_type, task = await _find_task_any(db, task_id, task_type_hint)
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
        await _validate_coop_slot_for_signup(db, task_id, slot_id)
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

    try:
        start_at = datetime.fromisoformat(str(payload.get("start_time")))
        end_at = datetime.fromisoformat(str(payload.get("end_time")))
    except (TypeError, ValueError) as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="start_time/end_time 时间格式非法",
        ) from exc

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


@router.post("/tasks/{task_id}/sign-in", response_model=Dict[str, Any])
async def task_sign_in(
    task_id: int,
    payload: Dict[str, Any],
    db: AsyncSession = Depends(get_db),
    current_user: Member = Depends(get_current_user),
) -> Dict[str, Any]:
    slot_id = _to_int(payload.get("slot_id") or payload.get("slotId"), 0)
    sign_in_type = str(payload.get("sign_in_type") or "manual").strip().lower()
    qr_token = str(payload.get("qr_token") or payload.get("qrToken") or "").strip()
    device_id = str(payload.get("device_id") or payload.get("deviceId") or "").strip()
    longitude = _extract_longitude(payload, "sign_in")
    latitude = _extract_latitude(payload, "sign_in")

    task = (await db.execute(select(TaskCoop).where(TaskCoop.id == task_id))).scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="协助任务不存在")

    signup_stmt = select(TaskCoopSignup).where(
        TaskCoopSignup.coop_task_id == task_id,
        TaskCoopSignup.user_id == current_user.id,
    )
    if slot_id > 0:
        signup_stmt = signup_stmt.where(TaskCoopSignup.coop_slot_id == slot_id)

    signup = (await db.execute(signup_stmt)).scalars().first()
    if not signup:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="未找到报名记录")
    if signup.status != 1:
        if signup.status == 0:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="报名待审核，暂不可签到")
        if signup.status == 2:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="报名已驳回，无法签到")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="当前报名状态不可签到")

    if sign_in_type in {"qr", "hybrid"}:
        if not qr_token:
            await _reject_with_abnormal_todo(
                db=db,
                task_id=task_id,
                source_biz_type="task_coop_signup",
                source_biz_id=signup.id,
                user_id=current_user.id,
                reason="签到失败：缺少二维码令牌",
                detail="sign_in_type=qr/hybrid 但未携带 qr_token",
            )
        if not await _validate_qr_token(db, task_id, qr_token):
            await _reject_with_abnormal_todo(
                db=db,
                task_id=task_id,
                source_biz_type="task_coop_signup",
                source_biz_id=signup.id,
                user_id=current_user.id,
                reason="签到失败：二维码验签未通过",
                detail="qr_token 无效或已过期",
            )

    if sign_in_type in {"gps", "hybrid"}:
        if longitude is None or latitude is None:
            await _reject_with_abnormal_todo(
                db=db,
                task_id=task_id,
                source_biz_type="task_coop_signup",
                source_biz_id=signup.id,
                user_id=current_user.id,
                reason="签到失败：缺少定位信息",
                detail="sign_in_type=gps/hybrid 但未携带经纬度",
            )
        if task.building_id:
            building = (
                await db.execute(select(Building).where(Building.id == task.building_id))
            ).scalar_one_or_none()
            if building and building.longitude is not None and building.latitude is not None:
                max_radius = await _get_system_config_int(
                    db,
                    keys=["checkin_location_radius_meters"],
                    default=200,
                    min_value=10,
                    max_value=5000,
                )
                distance = _distance_meters(
                    float(building.longitude),
                    float(building.latitude),
                    float(longitude),
                    float(latitude),
                )
                if distance > float(max_radius):
                    await _reject_with_abnormal_todo(
                        db=db,
                        task_id=task_id,
                        source_biz_type="task_coop_signup",
                        source_biz_id=signup.id,
                        user_id=current_user.id,
                        reason="签到失败：超出允许定位半径",
                        detail=f"distance={distance:.2f}m > limit={max_radius}m",
                    )

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
    att.sign_in_type = sign_in_type
    att.sign_in_longitude = longitude
    att.sign_in_latitude = latitude
    if qr_token:
        att.qr_token = qr_token

    meta = _parse_attendance_meta(att.remark)
    if device_id:
        meta["anti_cheat_device_id"] = device_id
    if meta:
        att.remark = json.dumps(meta, ensure_ascii=False)

    await db.commit()
    return create_response(
        data={
            "signup_id": signup.id,
            "sign_in_type": att.sign_in_type,
            "qr_verified": sign_in_type not in {"qr", "hybrid"} or bool(qr_token),
        },
        message="签到成功",
    )


@router.post("/tasks/{task_id}/sign-out", response_model=Dict[str, Any])
async def task_sign_out(
    task_id: int,
    payload: Dict[str, Any],
    db: AsyncSession = Depends(get_db),
    current_user: Member = Depends(get_current_user),
) -> Dict[str, Any]:
    slot_id = _to_int(payload.get("slot_id") or payload.get("slotId"), 0)
    sign_out_type = str(payload.get("sign_out_type") or "manual").strip().lower()
    qr_token = str(payload.get("qr_token") or payload.get("qrToken") or "").strip()
    device_id = str(payload.get("device_id") or payload.get("deviceId") or "").strip()
    longitude = _extract_longitude(payload, "sign_out")
    latitude = _extract_latitude(payload, "sign_out")

    task = (await db.execute(select(TaskCoop).where(TaskCoop.id == task_id))).scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="协助任务不存在")

    signup_stmt = select(TaskCoopSignup).where(
        TaskCoopSignup.coop_task_id == task_id,
        TaskCoopSignup.user_id == current_user.id,
    )
    if slot_id > 0:
        signup_stmt = signup_stmt.where(TaskCoopSignup.coop_slot_id == slot_id)

    signup = (await db.execute(signup_stmt)).scalars().first()
    if not signup:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="未找到报名记录")
    if signup.status != 1:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="当前报名状态不可签退")

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

    if sign_out_type in {"qr", "hybrid"}:
        if not qr_token:
            await _reject_with_abnormal_todo(
                db=db,
                task_id=task_id,
                source_biz_type="task_coop_attendance",
                source_biz_id=att.id,
                user_id=current_user.id,
                reason="签退失败：缺少二维码令牌",
                detail="sign_out_type=qr/hybrid 但未携带 qr_token",
            )
        if not await _validate_qr_token(db, task_id, qr_token):
            await _reject_with_abnormal_todo(
                db=db,
                task_id=task_id,
                source_biz_type="task_coop_attendance",
                source_biz_id=att.id,
                user_id=current_user.id,
                reason="签退失败：二维码验签未通过",
                detail="qr_token 无效或已过期",
            )

    if sign_out_type in {"gps", "hybrid"}:
        if longitude is None or latitude is None:
            await _reject_with_abnormal_todo(
                db=db,
                task_id=task_id,
                source_biz_type="task_coop_attendance",
                source_biz_id=att.id,
                user_id=current_user.id,
                reason="签退失败：缺少定位信息",
                detail="sign_out_type=gps/hybrid 但未携带经纬度",
            )
        if task.building_id:
            building = (
                await db.execute(select(Building).where(Building.id == task.building_id))
            ).scalar_one_or_none()
            if building and building.longitude is not None and building.latitude is not None:
                max_radius = await _get_system_config_int(
                    db,
                    keys=["checkin_location_radius_meters"],
                    default=200,
                    min_value=10,
                    max_value=5000,
                )
                distance = _distance_meters(
                    float(building.longitude),
                    float(building.latitude),
                    float(longitude),
                    float(latitude),
                )
                if distance > float(max_radius):
                    await _reject_with_abnormal_todo(
                        db=db,
                        task_id=task_id,
                        source_biz_type="task_coop_attendance",
                        source_biz_id=att.id,
                        user_id=current_user.id,
                        reason="签退失败：超出允许定位半径",
                        detail=f"distance={distance:.2f}m > limit={max_radius}m",
                    )

    if (
        longitude is not None
        and latitude is not None
        and att.sign_in_longitude is not None
        and att.sign_in_latitude is not None
    ):
        max_signin_signout_distance = await _get_system_config_int(
            db,
            keys=["checkin_signout_max_distance_meters"],
            default=500,
            min_value=10,
            max_value=10000,
        )
        drift_distance = _distance_meters(
            float(att.sign_in_longitude),
            float(att.sign_in_latitude),
            float(longitude),
            float(latitude),
        )
        if drift_distance > float(max_signin_signout_distance):
            await _reject_with_abnormal_todo(
                db=db,
                task_id=task_id,
                source_biz_type="task_coop_attendance",
                source_biz_id=att.id,
                user_id=current_user.id,
                reason="签退失败：签到签退位置偏差过大",
                detail=(
                    f"drift={drift_distance:.2f}m > "
                    f"limit={max_signin_signout_distance}m"
                ),
            )

    check_device_consistency = bool(
        await _get_system_config_int(
            db,
            keys=["checkin_device_consistency_required"],
            default=1,
            min_value=0,
            max_value=1,
        )
    )
    if check_device_consistency:
        meta = _parse_attendance_meta(att.remark)
        sign_in_device = str(meta.get("anti_cheat_device_id") or "").strip()
        if sign_in_device and device_id and sign_in_device != device_id:
            await _reject_with_abnormal_todo(
                db=db,
                task_id=task_id,
                source_biz_type="task_coop_attendance",
                source_biz_id=att.id,
                user_id=current_user.id,
                reason="签退失败：设备指纹不一致",
                detail=f"sign_in_device={sign_in_device}, sign_out_device={device_id}",
            )
        if sign_in_device and not device_id:
            await _reject_with_abnormal_todo(
                db=db,
                task_id=task_id,
                source_biz_type="task_coop_attendance",
                source_biz_id=att.id,
                user_id=current_user.id,
                reason="签退失败：缺少设备指纹",
                detail="签到记录存在设备信息，签退未提供 device_id",
            )

    att.sign_out_at = datetime.now(timezone.utc)
    att.sign_out_type = sign_out_type
    att.sign_out_longitude = longitude
    att.sign_out_latitude = latitude
    if qr_token:
        att.qr_token = qr_token

    meta = _parse_attendance_meta(att.remark)
    if device_id:
        meta["anti_cheat_sign_out_device_id"] = device_id
    if meta:
        att.remark = json.dumps(meta, ensure_ascii=False)

    if att.sign_in_at and att.sign_out_at and att.sign_out_at >= att.sign_in_at:
        att.duration_minutes = int((att.sign_out_at - att.sign_in_at).total_seconds() // 60)
    await db.commit()
    return create_response(
        data={
            "signup_id": signup.id,
            "duration_minutes": att.duration_minutes,
            "sign_out_type": att.sign_out_type,
        },
        message="签退成功",
    )


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
