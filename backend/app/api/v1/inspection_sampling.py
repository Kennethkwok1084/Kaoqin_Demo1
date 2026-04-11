"""Inspection and sampling workflow APIs (formal domain router)."""

import random
from datetime import datetime, timedelta, timezone
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import create_response, get_current_active_admin, get_current_user, get_db
from app.models.building import DormRoom
from app.models.inspection_record import InspectionRecord
from app.models.member import Member, UserRole
from app.models.sampling_record import SamplingRecord
from app.models.sampling_scan_detail import SamplingScanDetail
from app.models.sampling_test_detail import SamplingTestDetail
from app.models.system_config import SystemConfig
from app.models.task_inspection import TaskInspection
from app.models.task_inspection_point import TaskInspectionPoint
from app.models.task_inspection_user import TaskInspectionUser
from app.models.task_sampling import TaskSampling
from app.models.task_sampling_room import TaskSamplingRoom
from app.models.task_sampling_user import TaskSamplingUser

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


async def _get_system_config_float(
    db: AsyncSession,
    keys: list[str],
    default: float,
    min_value: float = 0.0,
    max_value: float = 100000.0,
) -> float:
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
            value = float(str(row.config_value).strip())
            return max(min_value, min(value, max_value))
        except (TypeError, ValueError):
            continue
    return default


def _normalize_weight(value: Any) -> float:
    try:
        weight = float(value)
    except (TypeError, ValueError):
        weight = 0.0
    # Keep minimum weight > 0 so rooms with zero weight are still eligible.
    return max(weight, 0.0) + 1.0


def _weighted_sample_without_replacement(candidates: list[DormRoom], count: int) -> list[DormRoom]:
    if count <= 0 or not candidates:
        return []

    pool: list[tuple[DormRoom, float]] = [
        (room, _normalize_weight(getattr(room, "active_repair_weight", 0)))
        for room in candidates
    ]
    selected: list[DormRoom] = []
    pick_count = min(count, len(pool))

    for _ in range(pick_count):
        total_weight = sum(weight for _, weight in pool)
        if total_weight <= 0:
            selected.extend(room for room, _ in pool)
            break

        cursor = random.uniform(0, total_weight)
        cumulative = 0.0
        chosen_index = len(pool) - 1
        for index, (_, weight) in enumerate(pool):
            cumulative += weight
            if cursor <= cumulative:
                chosen_index = index
                break

        room, _ = pool.pop(chosen_index)
        selected.append(room)

    return selected


async def _ensure_inspection_task_access(
    db: AsyncSession,
    task_id: int,
    current_user: Member,
) -> None:
    if getattr(current_user, "role", None) == UserRole.ADMIN:
        return
    if not hasattr(current_user, "id"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权访问该巡检任务")
    rel = (
        await db.execute(
            select(TaskInspectionUser).where(
                TaskInspectionUser.inspection_task_id == task_id,
                TaskInspectionUser.user_id == current_user.id,
            )
        )
    ).scalar_one_or_none()
    if rel is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权访问该巡检任务")


async def _ensure_sampling_task_access(
    db: AsyncSession,
    task_id: int,
    current_user: Member,
) -> None:
    if getattr(current_user, "role", None) == UserRole.ADMIN:
        return
    if not hasattr(current_user, "id"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权访问该抽检任务")
    rel = (
        await db.execute(
            select(TaskSamplingUser).where(
                TaskSamplingUser.sampling_task_id == task_id,
                TaskSamplingUser.user_id == current_user.id,
            )
        )
    ).scalar_one_or_none()
    if rel is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权访问该抽检任务")


async def _get_sampling_target(
    db: AsyncSession,
    task_id: int,
    room_id: int,
) -> TaskSamplingRoom | None:
    return (
        await db.execute(
            select(TaskSamplingRoom).where(
                TaskSamplingRoom.id == room_id,
                TaskSamplingRoom.sampling_task_id == task_id,
            )
        )
    ).scalar_one_or_none()


def _extract_scan_details(payload: Dict[str, Any]) -> list[Dict[str, Any]]:
    candidates = [
        payload.get("scan_details"),
        payload.get("scanDetails"),
        payload.get("scan_results"),
        payload.get("scanResults"),
    ]
    for value in candidates:
        if isinstance(value, list):
            return [item for item in value if isinstance(item, dict)]
    return []


def _extract_test_details(payload: Dict[str, Any]) -> list[Dict[str, Any]]:
    candidates = [
        payload.get("test_details"),
        payload.get("testDetails"),
        payload.get("test_results"),
        payload.get("testResults"),
    ]
    for value in candidates:
        if isinstance(value, list):
            return [item for item in value if isinstance(item, dict)]
    return []


async def _replace_sampling_details(
    db: AsyncSession,
    sampling_record_id: int,
    payload: Dict[str, Any],
) -> tuple[int, int]:
    scan_details = _extract_scan_details(payload)
    test_details = _extract_test_details(payload)

    await db.execute(
        delete(SamplingScanDetail).where(SamplingScanDetail.sampling_record_id == sampling_record_id)
    )
    await db.execute(
        delete(SamplingTestDetail).where(SamplingTestDetail.sampling_record_id == sampling_record_id)
    )

    created_scan = 0
    for item in scan_details:
        db.add(
            SamplingScanDetail(
                sampling_record_id=sampling_record_id,
                ssid=item.get("ssid"),
                bssid=item.get("bssid"),
                channel_no=_to_int(item.get("channel_no") or item.get("channelNo"), 0) or None,
                signal_strength_dbm=_to_int(
                    item.get("signal_strength_dbm")
                    or item.get("signalStrengthDbm")
                    or item.get("rssi"),
                    0,
                )
                or None,
                is_same_channel=_to_bool(item.get("is_same_channel") or item.get("isSameChannel"), False),
                is_adjacent_channel=_to_bool(
                    item.get("is_adjacent_channel") or item.get("isAdjacentChannel"),
                    False,
                ),
            )
        )
        created_scan += 1

    created_test = 0
    for item in test_details:
        result_payload = item.get("result_payload") or item.get("resultPayload") or item.get("result")
        if not isinstance(result_payload, dict):
            result_payload = {
                key: value
                for key, value in item.items()
                if key
                not in {
                    "item_code",
                    "itemCode",
                    "code",
                    "item",
                    "target_host",
                    "targetHost",
                    "host",
                    "save_to_record",
                    "saveToRecord",
                }
            }

        item_code = str(
            item.get("item_code")
            or item.get("itemCode")
            or item.get("code")
            or item.get("item")
            or "unknown"
        ).strip()

        db.add(
            SamplingTestDetail(
                sampling_record_id=sampling_record_id,
                item_code=item_code[:32] or "unknown",
                target_host=(
                    item.get("target_host")
                    or item.get("targetHost")
                    or item.get("host")
                ),
                result_payload=result_payload,
                save_to_record=_to_bool(item.get("save_to_record") or item.get("saveToRecord"), True),
            )
        )
        created_test += 1

    return created_scan, created_test


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
    current_user: Member = Depends(get_current_user),
) -> Dict[str, Any]:
    await _ensure_inspection_task_access(db, task_id, current_user)

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
    await _ensure_inspection_task_access(db, task_id, current_user)

    point_id = _to_int(payload.get("inspection_point_id") or payload.get("inspectionPointId"), 0)
    if point_id <= 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="inspection_point_id 非法")
    point = (
        await db.execute(
            select(TaskInspectionPoint).where(
                TaskInspectionPoint.id == point_id,
                TaskInspectionPoint.inspection_task_id == task_id,
            )
        )
    ).scalar_one_or_none()
    if not point:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="巡检点位不存在或不属于该任务")

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
    current_user: Member = Depends(get_current_user),
) -> Dict[str, Any]:
    await _ensure_inspection_task_access(db, task_id, current_user)

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

    target_count = max(
        _to_int(payload.get("target_room_count") or payload.get("targetRoomCount"), task.target_room_count),
        1,
    )
    exclude_days = max(
        _to_int(payload.get("exclude_days") or payload.get("excludeDays"), task.exclude_days),
        0,
    )

    existing_rows = (
        await db.execute(select(TaskSamplingRoom).where(TaskSamplingRoom.sampling_task_id == task_id))
    ).scalars().all()
    existing_room_ids = {row.dorm_room_id for row in existing_rows}

    need_count = max(target_count - len(existing_room_ids), 0)
    if need_count == 0:
        return create_response(
            data={"created": 0, "existing": len(existing_room_ids), "requested": target_count},
            message="抽检目标生成成功",
        )

    dorm_rows = (
        await db.execute(
            select(DormRoom).where(DormRoom.building_id == task.building_id, DormRoom.status == 1)
        )
    ).scalars().all()

    candidates = [room for room in dorm_rows if room.id not in existing_room_ids]

    if exclude_days > 0:
        cutoff = datetime.now(timezone.utc) - timedelta(days=exclude_days)
        recent_room_ids = set(
            (
                await db.execute(
                    select(SamplingRecord.dorm_room_id).where(
                        SamplingRecord.dorm_room_id.isnot(None),
                        SamplingRecord.created_at >= cutoff,
                    )
                )
            ).scalars().all()
        )
        candidates = [room for room in candidates if room.id not in recent_room_ids]

    selected_rooms = _weighted_sample_without_replacement(candidates, need_count)

    created = 0
    for room in selected_rooms:
        db.add(
            TaskSamplingRoom(
                sampling_task_id=task_id,
                dorm_room_id=room.id,
                generated_weight=_to_int(getattr(room, "active_repair_weight", 0), 0),
            )
        )
        created += 1

    await db.commit()
    return create_response(
        data={
            "created": created,
            "requested": target_count,
            "exclude_days": exclude_days,
            "eligible": len(candidates),
            "existing": len(existing_room_ids),
        },
        message="抽检目标生成成功",
    )


@router.get("/tasks/{task_id}/sampling/targets", response_model=Dict[str, Any])
async def get_sampling_targets(
    task_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: Member = Depends(get_current_user),
) -> Dict[str, Any]:
    await _ensure_sampling_task_access(db, task_id, current_user)

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
    await _ensure_sampling_task_access(db, task_id, current_user)

    room_id = _to_int(payload.get("sampling_task_room_id") or payload.get("task_room_id"), 0)
    dorm_room_id = _to_int(payload.get("dorm_room_id") or payload.get("room_id"), 0)
    if room_id <= 0:
        target = (
            await db.execute(
                select(TaskSamplingRoom).where(TaskSamplingRoom.sampling_task_id == task_id).limit(1)
            )
        ).scalar_one_or_none()
        if not target:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="无可用抽检目标")
        room_id = target.id
        dorm_room_id = target.dorm_room_id
    else:
        target = await _get_sampling_target(db, task_id, room_id)
        if not target:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="抽检目标不存在或不属于该任务")
        if dorm_room_id > 0 and dorm_room_id != target.dorm_room_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="room_id 与抽检目标不匹配")
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

    created_scan_count, created_test_count = await _replace_sampling_details(
        db=db,
        sampling_record_id=row.id,
        payload=payload,
    )

    loss_threshold = await _get_system_config_float(
        db,
        keys=["network_loss_threshold_pct", "sampling_network_loss_threshold_pct"],
        default=5.0,
        min_value=0.0,
        max_value=100.0,
    )
    tcp_rtt_threshold = await _get_system_config_float(
        db,
        keys=["network_tcp_rtt_threshold_ms", "sampling_network_tcp_rtt_threshold_ms"],
        default=200.0,
        min_value=1.0,
        max_value=10000.0,
    )
    down_speed_min = await _get_system_config_float(
        db,
        keys=["network_down_speed_min_mbps", "sampling_network_down_speed_min_mbps"],
        default=20.0,
        min_value=0.1,
        max_value=10000.0,
    )
    up_speed_min = await _get_system_config_float(
        db,
        keys=["network_up_speed_min_mbps", "sampling_network_up_speed_min_mbps"],
        default=2.0,
        min_value=0.1,
        max_value=10000.0,
    )

    auto_reasons: list[str] = []
    loss_rate = _to_float(row.loss_rate_pct)
    tcp_rtt = _to_float(row.tcp_rtt_ms)
    down_speed = _to_float(row.down_speed_mbps)
    up_speed = _to_float(row.up_speed_mbps)

    if loss_rate is not None and loss_rate > loss_threshold:
        auto_reasons.append(f"丢包率超阈值({loss_rate:.2f}%>{loss_threshold:.2f}%)")
    if tcp_rtt is not None and tcp_rtt > tcp_rtt_threshold:
        auto_reasons.append(f"TCP时延超阈值({tcp_rtt:.2f}ms>{tcp_rtt_threshold:.2f}ms)")
    if down_speed is not None and down_speed < down_speed_min:
        auto_reasons.append(f"下行速率低于阈值({down_speed:.2f}<{down_speed_min:.2f}Mbps)")
    if up_speed is not None and up_speed < up_speed_min:
        auto_reasons.append(f"上行速率低于阈值({up_speed:.2f}<{up_speed_min:.2f}Mbps)")

    if auto_reasons:
        row.exception_auto = True
        if not payload.get("manual_exception_note"):
            row.manual_exception_note = "; ".join(auto_reasons)[:500]
    elif "exception_auto" not in payload:
        row.exception_auto = False

    row.finished_at = datetime.now(timezone.utc)
    await db.commit()
    return create_response(
        data={
            "id": row.id,
            "scan_detail_count": created_scan_count,
            "test_detail_count": created_test_count,
        },
        message="网络检测提交成功",
    )


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
    await _ensure_sampling_task_access(db, task_id, current_user)

    target = await _get_sampling_target(db, task_id, room_id)
    if not target:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="抽检目标不存在或不属于该任务")
    if dorm_room_id != target.dorm_room_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="room_id 与抽检目标不匹配")

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
    await db.flush()

    created_scan_count, created_test_count = await _replace_sampling_details(
        db=db,
        sampling_record_id=row.id,
        payload=payload,
    )

    await db.commit()
    await db.refresh(row)
    return create_response(
        data={
            "id": row.id,
            "scan_detail_count": created_scan_count,
            "test_detail_count": created_test_count,
        },
        message="单项检测提交成功",
    )


@router.get("/network-tests/{record_id}", response_model=Dict[str, Any])
async def network_test_detail(
    record_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: Member = Depends(get_current_user),
) -> Dict[str, Any]:
    row = (
        await db.execute(select(SamplingRecord).where(SamplingRecord.id == record_id))
    ).scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="检测记录不存在")
    if row.user_id != current_user.id and current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权查看该检测记录")

    scan_rows = (
        await db.execute(
            select(SamplingScanDetail)
            .where(SamplingScanDetail.sampling_record_id == row.id)
            .order_by(SamplingScanDetail.id)
        )
    ).scalars().all()
    test_rows = (
        await db.execute(
            select(SamplingTestDetail)
            .where(SamplingTestDetail.sampling_record_id == row.id)
            .order_by(SamplingTestDetail.id)
        )
    ).scalars().all()

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
            "scan_details": [
                {
                    "id": item.id,
                    "ssid": item.ssid,
                    "bssid": item.bssid,
                    "channel_no": item.channel_no,
                    "signal_strength_dbm": item.signal_strength_dbm,
                    "is_same_channel": item.is_same_channel,
                    "is_adjacent_channel": item.is_adjacent_channel,
                }
                for item in scan_rows
            ],
            "test_details": [
                {
                    "id": item.id,
                    "item_code": item.item_code,
                    "target_host": item.target_host,
                    "result_payload": item.result_payload,
                    "save_to_record": item.save_to_record,
                }
                for item in test_rows
            ],
        },
        message="获取检测详情成功",
    )


@router.get("/tasks/{task_id}/network-tests", response_model=Dict[str, Any])
async def task_network_tests(
    task_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: Member = Depends(get_current_user),
) -> Dict[str, Any]:
    await _ensure_sampling_task_access(db, task_id, current_user)

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
