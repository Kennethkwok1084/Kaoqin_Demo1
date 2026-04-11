"""Operational statistics APIs migrated from doc_compat."""

from typing import Any, Dict

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import create_response, get_current_active_admin, get_db
from app.models.member import Member
from app.models.repair_ticket import RepairTicket
from app.models.sampling_record import SamplingRecord
from app.models.workhour_entry import WorkhourEntry

router = APIRouter()


def _to_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


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
