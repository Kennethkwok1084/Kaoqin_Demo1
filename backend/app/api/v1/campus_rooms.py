"""Building and room management APIs migrated from doc_compat."""

from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import create_response, get_current_active_admin, get_current_user, get_db
from app.models.building import Building, DormRoom
from app.models.member import Member

router = APIRouter()


def _to_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


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
