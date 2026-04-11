"""
工时管理API路由
处理工时统计查看、月度汇总、数据导出等功能
基于任务完成情况计算和展示工时，而非传统的签到签退
"""

import logging
from datetime import date, datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Body, Depends, HTTPException, Path, Query, status
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import (
    create_response,
    get_current_user,
    get_db,
    get_current_active_group_leader,
)
from app.models.member import Member
from app.models.task import TaskStatus

logger = logging.getLogger(__name__)

router = APIRouter()


# 工时管理API - 基于任务完成的工时统计和展示


def _parse_request_datetime(value: Any, field_name: str) -> Optional[datetime]:
    """解析请求体中的时间字段，支持ISO字符串与datetime对象。"""
    if value is None:
        return None

    if isinstance(value, datetime):
        if value.tzinfo is not None:
            return value.astimezone(timezone.utc).replace(tzinfo=None)
        return value

    if isinstance(value, str):
        raw = value.strip()
        if raw.endswith("Z"):
            raw = raw[:-1] + "+00:00"
        try:
            parsed = datetime.fromisoformat(raw)
            if parsed.tzinfo is not None:
                return parsed.astimezone(timezone.utc).replace(tzinfo=None)
            return parsed
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"{field_name} 格式错误，请使用 ISO8601 时间格式",
            ) from exc

    raise HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        detail=f"{field_name} 类型错误",
    )


@router.post("/check-in", response_model=Dict[str, Any], summary="用户签到")
async def check_in(
    request_data: Dict[str, Any] = Body(default_factory=dict),
    current_user: Member = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """用户签到，按“成员 + 自然日”更新考勤记录。"""
    try:
        from sqlalchemy import select

        from app.models.attendance import AttendanceRecord

        checkin_time = _parse_request_datetime(
            request_data.get("checkinTime") or request_data.get("checkin_time"),
            "checkinTime",
        ) or datetime.now()
        attendance_date = checkin_time.date()

        query = select(AttendanceRecord).where(
            AttendanceRecord.member_id == current_user.id,
            AttendanceRecord.attendance_date == attendance_date,
        )
        result = await db.execute(query)
        record = result.scalar_one_or_none()

        if record is None:
            record = AttendanceRecord(
                member_id=current_user.id,
                attendance_date=attendance_date,
            )
            db.add(record)

        record.checkin_time = checkin_time

        location = request_data.get("location")
        device_info = request_data.get("deviceInfo") or request_data.get("device_info")
        notes = request_data.get("notes")

        if location:
            record.location = str(location)

        note_parts: List[str] = []
        if notes:
            note_parts.append(str(notes))
        if device_info:
            note_parts.append(f"设备: {device_info}")
        if note_parts:
            merged_notes = "；".join(note_parts)
            record.notes = (
                f"{record.notes}\n{merged_notes}" if record.notes else merged_notes
            )

        if record.checkout_time and record.checkout_time >= record.checkin_time:
            duration_hours = (
                record.checkout_time - record.checkin_time
            ).total_seconds() / 3600
            record.work_hours = round(duration_hours, 2)
            record.status = "已签退"
        else:
            record.status = "已签到"

        await db.commit()
        await db.refresh(record)

        return create_response(
            data={
                "record_id": record.id,
                "member_id": record.member_id,
                "attendance_date": str(record.attendance_date),
                "checkin_time": (
                    record.checkin_time.isoformat() if record.checkin_time else None
                ),
                "location": record.location,
                "status": record.status,
            },
            message="签到成功",
        )

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"签到失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="签到失败",
        )


@router.post("/check-out", response_model=Dict[str, Any], summary="用户签退")
async def check_out(
    request_data: Dict[str, Any] = Body(default_factory=dict),
    current_user: Member = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """用户签退，计算当日工时。"""
    try:
        from sqlalchemy import desc, select

        from app.models.attendance import AttendanceRecord

        checkout_time = _parse_request_datetime(
            request_data.get("checkoutTime") or request_data.get("checkout_time"),
            "checkoutTime",
        ) or datetime.now()

        attendance_date = checkout_time.date()
        query = select(AttendanceRecord).where(
            AttendanceRecord.member_id == current_user.id,
            AttendanceRecord.attendance_date == attendance_date,
        )
        result = await db.execute(query)
        record = result.scalar_one_or_none()

        # 兼容跨天签退：兜底取最近一条未签退记录
        if record is None:
            fallback_query = (
                select(AttendanceRecord)
                .where(
                    AttendanceRecord.member_id == current_user.id,
                    AttendanceRecord.checkout_time.is_(None),
                )
                .order_by(desc(AttendanceRecord.attendance_date))
                .limit(1)
            )
            fallback_result = await db.execute(fallback_query)
            record = fallback_result.scalar_one_or_none()

        if record is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="今日尚未签到，无法签退",
            )

        if record.checkin_time and checkout_time < record.checkin_time:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="签退时间不能早于签到时间",
            )

        record.checkout_time = checkout_time

        location = request_data.get("location")
        work_summary = request_data.get("workSummary") or request_data.get(
            "work_summary"
        )
        notes = request_data.get("notes")

        if location:
            record.location = str(location)

        note_parts: List[str] = []
        if work_summary:
            note_parts.append(f"工作总结: {work_summary}")
        if notes:
            note_parts.append(str(notes))
        if note_parts:
            merged_notes = "；".join(note_parts)
            record.notes = (
                f"{record.notes}\n{merged_notes}" if record.notes else merged_notes
            )

        if record.checkin_time:
            duration_hours = (record.checkout_time - record.checkin_time).total_seconds() / 3600
            record.work_hours = round(max(duration_hours, 0.0), 2)

        record.status = "已签退"

        await db.commit()
        await db.refresh(record)

        return create_response(
            data={
                "record_id": record.id,
                "member_id": record.member_id,
                "attendance_date": str(record.attendance_date),
                "checkin_time": (
                    record.checkin_time.isoformat() if record.checkin_time else None
                ),
                "checkout_time": (
                    record.checkout_time.isoformat() if record.checkout_time else None
                ),
                "work_hours": float(record.work_hours or 0),
                "location": record.location,
                "status": record.status,
            },
            message="签退成功",
        )

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"签退失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="签退失败",
        )


def _resolve_cycle_period(
    date_from: Optional[date],
    date_to: Optional[date],
    cycle_type: Optional[str] = None,
    month: Optional[str] = None,
    week_start: Optional[date] = None,
) -> tuple[date, date]:
    """根据cycle_type与可选参数计算周期起止日期。

    - cycle_type: monthly | weekly | custom
    - month: YYYY-MM（当cycle_type=monthly时可用）
    - week_start: 周期开始日期（当cycle_type=weekly时可用）
    - 若提供了date_from/date_to，则优先采用custom
    """
    from calendar import monthrange
    from datetime import timedelta

    # 若显式提供date_from/date_to，视为自定义周期
    if date_from and date_to:
        return date_from, date_to

    today = datetime.now().date()
    ctype = (cycle_type or "").lower()

    if ctype == "monthly":
        if month:
            try:
                year, mon = map(int, month.split("-"))
            except Exception:
                year, mon = today.year, today.month
        else:
            year, mon = today.year, today.month
        first_day = date(year, mon, 1)
        last_day = date(year, mon, monthrange(year, mon)[1])
        return first_day, last_day

    if ctype == "weekly":
        if week_start:
            start = week_start
        else:
            # 以周一为周期开始
            weekday = today.weekday()  # Monday=0
            start = today - timedelta(days=weekday)
        end = start + timedelta(days=6)
        return start, end

    # 默认：当月
    year, mon = today.year, today.month
    first_day = date(year, mon, 1)
    last_day = date(year, mon, monthrange(year, mon)[1])
    return first_day, last_day


def _get_export_dir() -> str:
    """获取导出文件目录：使用全局上传目录下的 attendance_exports 子目录。"""
    import os
    from app.core.config import get_upload_path

    base = get_upload_path()  # 默认 uploads
    export_dir = os.path.join(base, "attendance_exports")
    os.makedirs(export_dir, exist_ok=True)
    return export_dir


@router.get("/records", response_model=List[Dict[str, Any]], summary="获取工时记录")
async def get_work_hours_records(
    member_id: Optional[int] = Query(
        None, description="成员ID（管理员可查看其他人记录）"
    ),
    date_from: Optional[date] = Query(None, description="开始日期"),
    date_to: Optional[date] = Query(None, description="结束日期"),
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=100, description="每页大小"),
    current_user: Member = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> List[Dict[str, Any]]:
    """
    获取工时记录列表（基于任务completion_time）

    - 显示任务完成后计算的工时记录
    - 普通员工只能查看自己的记录
    - 管理员可查看所有人的记录
    """
    try:
        from sqlalchemy import select

        from app.models.member import Member
        from app.models.task import RepairTask

        # 权限检查
        if member_id and member_id != current_user.id:
            if not current_user.is_admin:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="无权限查看其他人的工时记录",
                )

        # 如果没有指定member_id，默认查看当前用户的记录
        target_member_id = member_id or current_user.id

        # 构建时间范围过滤条件
        date_filters = []
        if date_from:
            date_from_dt = datetime.combine(date_from, datetime.min.time())
            date_filters.append(RepairTask.completion_time >= date_from_dt)
        if date_to:
            date_to_dt = datetime.combine(date_to, datetime.max.time())
            date_filters.append(RepairTask.completion_time <= date_to_dt)

        # 获取维修任务工时记录
        repair_query = (
            select(
                RepairTask.id,
                RepairTask.title,
                RepairTask.completion_time.label("work_date"),
                RepairTask.work_minutes,
                RepairTask.task_type,
                RepairTask.rating,
                RepairTask.member_id,
                Member.name.label("member_name"),
            )
            # 显式指定关联条件，避免由于多个外键导致的JOIN歧义
            .join(Member, RepairTask.member_id == Member.id)
            .where(
                RepairTask.member_id == target_member_id,
                RepairTask.status == TaskStatus.COMPLETED,
                RepairTask.completion_time.isnot(None),
                *date_filters,
            )
            .order_by(RepairTask.completion_time.desc())
        )

        repair_result = await db.execute(repair_query)
        repair_records = repair_result.fetchall()

        # 转换为统一格式
        work_records = []
        for record in repair_records:
            work_records.append(
                {
                    "id": record.id,
                    "task_type": "维修任务",
                    "title": record.title,
                    "work_date": record.work_date.date() if record.work_date else None,
                    "work_hours": round(record.work_minutes / 60, 2),
                    "work_minutes": record.work_minutes,
                    "task_category": record.task_type,
                    "rating": record.rating,
                    "member_id": record.member_id,
                    "member_name": record.member_name,
                    "source": "repair_task",
                }
            )

        # 手动分页
        start_idx = (page - 1) * size
        end_idx = start_idx + size
        paginated_records = work_records[start_idx:end_idx]

        return paginated_records

    except Exception as e:
        logger.error(f"获取工时记录失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="获取工时记录失败"
        )


@router.get(
    "/cycle-summary",
    response_model=Dict[str, Any],
    summary="获取考勤周期内全员考勤汇总（管理员/组长）",
)
async def get_attendance_cycle_summary(
    date_from: Optional[date] = Query(None, description="开始日期（custom模式）"),
    date_to: Optional[date] = Query(None, description="结束日期（custom模式）"),
    cycle_type: Optional[str] = Query(
        None, description="周期类型：monthly/weekly/custom；默认按月"
    ),
    month: Optional[str] = Query(None, description="当cycle_type=monthly时使用，格式YYYY-MM"),
    week_start: Optional[date] = Query(None, description="当cycle_type=weekly时使用，周起始日"),
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=200, description="每页大小"),
    current_user: Member = Depends(get_current_active_group_leader),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """
    按周期（date_from ~ date_to）统计全员“基于任务”的工时汇总（不使用打卡）。
    - repair_minutes / monitoring_minutes / assistance_minutes
    - total_work_hours（小时） / average_daily_hours（小时）
    - repair_tasks / monitoring_tasks / assistance_tasks / total_tasks
    仅管理员/组长可查看全员。
    """
    try:
        from calendar import monthrange
        from sqlalchemy import func, select
        from app.models.task import RepairTask, MonitoringTask, AssistanceTask, TaskStatus

        # 解析周期
        date_from, date_to = _resolve_cycle_period(
            date_from, date_to, cycle_type, month, week_start
        )

        # 周期天数（包含端点）
        period_days = (date_to - date_from).days + 1

        # 先取所有在职成员，避免成员无任务时丢失
        members_result = await db.execute(
            select(Member.id, Member.name, Member.group_id).where(Member.is_active)
        )
        members: Dict[int, Dict[str, Any]] = {}
        for mid, name, group_id in members_result.fetchall():
            members[int(mid)] = {"name": name, "group_id": group_id}

        # 统计各类任务
        def to_dict(rows: List[Any]) -> Dict[int, Dict[str, int]]:
            d: Dict[int, Dict[str, int]] = {}
            for mid, total_minutes, cnt in rows:
                d[int(mid)] = {"minutes": int(total_minutes or 0), "count": int(cnt or 0)}
            return d

        # 报修任务（完成时间）
        repair_rows = (
            await db.execute(
                select(
                    RepairTask.member_id,
                    func.sum(RepairTask.work_minutes),
                    func.count(RepairTask.id),
                )
                .where(
                    RepairTask.completion_time >= datetime.combine(date_from, datetime.min.time()),
                    RepairTask.completion_time <= datetime.combine(date_to, datetime.max.time()),
                    RepairTask.status == TaskStatus.COMPLETED,
                )
                .group_by(RepairTask.member_id)
            )
        ).fetchall()
        repair_map = to_dict(repair_rows)

        # 监控任务（结束时间）
        monitoring_rows = (
            await db.execute(
                select(
                    MonitoringTask.member_id,
                    func.sum(MonitoringTask.work_minutes),
                    func.count(MonitoringTask.id),
                )
                .where(
                    MonitoringTask.end_time >= datetime.combine(date_from, datetime.min.time()),
                    MonitoringTask.end_time <= datetime.combine(date_to, datetime.max.time()),
                    MonitoringTask.status == TaskStatus.COMPLETED,
                )
                .group_by(MonitoringTask.member_id)
            )
        ).fetchall()
        monitoring_map = to_dict(monitoring_rows)

        # 协助任务（结束时间）
        assistance_rows = (
            await db.execute(
                select(
                    AssistanceTask.member_id,
                    func.sum(AssistanceTask.work_minutes),
                    func.count(AssistanceTask.id),
                )
                .where(
                    AssistanceTask.end_time >= datetime.combine(date_from, datetime.min.time()),
                    AssistanceTask.end_time <= datetime.combine(date_to, datetime.max.time()),
                    AssistanceTask.status == TaskStatus.COMPLETED,
                )
                .group_by(AssistanceTask.member_id)
            )
        ).fetchall()
        assistance_map = to_dict(assistance_rows)

        # 组装记录并分页（先按成员姓名排序）
        rows_all: List[Dict[str, Any]] = []
        for mid, info in members.items():
            name = info.get("name")
            group_id = info.get("group_id")
            rmin = repair_map.get(mid, {}).get("minutes", 0)
            rcnt = repair_map.get(mid, {}).get("count", 0)
            mmin = monitoring_map.get(mid, {}).get("minutes", 0)
            mcnt = monitoring_map.get(mid, {}).get("count", 0)
            amin = assistance_map.get(mid, {}).get("minutes", 0)
            acnt = assistance_map.get(mid, {}).get("count", 0)

            total_minutes = rmin + mmin + amin
            total_hours = round(total_minutes / 60.0, 2)
            average_daily_hours = round(total_hours / period_days, 2) if period_days > 0 else 0.0

            rows_all.append(
                {
                    "member_id": mid,
                    "member_name": name,
                    "group_id": group_id,
                    "group_name": (f"第{group_id}组" if group_id else None),
                    "repair_minutes": rmin,
                    "monitoring_minutes": mmin,
                    "assistance_minutes": amin,
                    "repair_tasks": rcnt,
                    "monitoring_tasks": mcnt,
                    "assistance_tasks": acnt,
                    "total_tasks": rcnt + mcnt + acnt,
                    "total_work_hours": total_hours,
                    "average_daily_hours": average_daily_hours,
                }
            )

        # 排序与分页
        rows_all.sort(key=lambda x: x["member_name"])  # 按姓名升序
        total_members = len(rows_all)
        start = (page - 1) * size
        end = start + size
        records = rows_all[start:end]

        return {
            "success": True,
            "message": "获取考勤周期汇总成功",
            "data": {
                "period": {
                    "start_date": str(date_from),
                    "end_date": str(date_to),
                    "cycle_type": (cycle_type or "monthly"),
                    "days": period_days,
                },
                "page": page,
                "size": size,
                "total_members": total_members,
                "records": records,
            },
            "status_code": 200,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取考勤周期汇总失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="获取考勤周期汇总失败"
        )


@router.get("/cycle-export", summary="导出考勤周期内全员考勤汇总（管理员/组长）")
async def export_attendance_cycle_summary(
    date_from: Optional[date] = Query(None, description="开始日期（custom模式）"),
    date_to: Optional[date] = Query(None, description="结束日期（custom模式）"),
    cycle_type: Optional[str] = Query(
        None, description="周期类型：monthly/weekly/custom；默认按月"
    ),
    month: Optional[str] = Query(None, description="当cycle_type=monthly时使用，格式YYYY-MM"),
    week_start: Optional[date] = Query(None, description="当cycle_type=weekly时使用，周起始日"),
    format: str = Query("excel", description="导出格式（excel/csv）"),
    current_user: Member = Depends(get_current_active_group_leader),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """
    导出周期内全员考勤汇总（与 /cycle-summary 聚合逻辑一致）。
    返回生成的文件名与下载地址占位（与现有导出风格保持一致）。
    """
    try:
        from datetime import datetime as dt
        import pandas as pd
        from sqlalchemy import func, select
        from app.models.task import RepairTask, MonitoringTask, AssistanceTask, TaskStatus

        # 解析周期
        start_date, end_date = _resolve_cycle_period(
            date_from, date_to, cycle_type, month, week_start
        )

        # 以任务口径统计
        period_days = (end_date - start_date).days + 1

        members_result = await db.execute(
            select(Member.id, Member.name, Member.group_id).where(Member.is_active)
        )
        members: Dict[int, Dict[str, Any]] = {}
        for mid, name, group_id in members_result.fetchall():
            members[int(mid)] = {"name": name, "group_id": group_id}

        def to_dict(rows: List[Any]) -> Dict[int, Dict[str, int]]:
            d: Dict[int, Dict[str, int]] = {}
            for mid, total_minutes, cnt in rows:
                d[int(mid)] = {"minutes": int(total_minutes or 0), "count": int(cnt or 0)}
            return d

        repair_rows = (
            await db.execute(
                select(
                    RepairTask.member_id,
                    func.sum(RepairTask.work_minutes),
                    func.count(RepairTask.id),
                )
                .where(
                    RepairTask.completion_time >= datetime.combine(start_date, datetime.min.time()),
                    RepairTask.completion_time <= datetime.combine(end_date, datetime.max.time()),
                    RepairTask.status == TaskStatus.COMPLETED,
                )
                .group_by(RepairTask.member_id)
            )
        ).fetchall()
        repair_map = to_dict(repair_rows)

        monitoring_rows = (
            await db.execute(
                select(
                    MonitoringTask.member_id,
                    func.sum(MonitoringTask.work_minutes),
                    func.count(MonitoringTask.id),
                )
                .where(
                    MonitoringTask.end_time >= datetime.combine(start_date, datetime.min.time()),
                    MonitoringTask.end_time <= datetime.combine(end_date, datetime.max.time()),
                    MonitoringTask.status == TaskStatus.COMPLETED,
                )
                .group_by(MonitoringTask.member_id)
            )
        ).fetchall()
        monitoring_map = to_dict(monitoring_rows)

        assistance_rows = (
            await db.execute(
                select(
                    AssistanceTask.member_id,
                    func.sum(AssistanceTask.work_minutes),
                    func.count(AssistanceTask.id),
                )
                .where(
                    AssistanceTask.end_time >= datetime.combine(start_date, datetime.min.time()),
                    AssistanceTask.end_time <= datetime.combine(end_date, datetime.max.time()),
                    AssistanceTask.status == TaskStatus.COMPLETED,
                )
                .group_by(AssistanceTask.member_id)
            )
        ).fetchall()
        assistance_map = to_dict(assistance_rows)

        export_data = []
        for mid, info in members.items():
            name = info.get("name")
            group_id = info.get("group_id")
            rmin = repair_map.get(mid, {}).get("minutes", 0)
            rcnt = repair_map.get(mid, {}).get("count", 0)
            mmin = monitoring_map.get(mid, {}).get("minutes", 0)
            mcnt = monitoring_map.get(mid, {}).get("count", 0)
            amin = assistance_map.get(mid, {}).get("minutes", 0)
            acnt = assistance_map.get(mid, {}).get("count", 0)

            total_minutes = rmin + mmin + amin
            total_hours = round(total_minutes / 60.0, 2)
            average_daily_hours = round(total_hours / period_days, 2) if period_days > 0 else 0.0

            export_data.append(
                {
                    "成员ID": mid,
                    "成员姓名": name,
                    "成员小组": (f"第{group_id}组" if group_id else "未分组"),
                    "报修工时(分钟)": rmin,
                    "监控工时(分钟)": mmin,
                    "协助工时(分钟)": amin,
                    "报修任务(个)": rcnt,
                    "监控任务(个)": mcnt,
                    "协助任务(个)": acnt,
                    "任务总数(个)": rcnt + mcnt + acnt,
                    "累计工时(小时)": total_hours,
                    "日均工时(小时)": average_daily_hours,
                    "周期开始": str(start_date),
                    "周期结束": str(end_date),
                }
            )

        if not export_data:
            return {
                "success": True,
                "message": "无可导出的考勤数据",
                "total_records": 0,
            }

        df = pd.DataFrame(export_data)
        timestamp = dt.now().strftime("%Y%m%d_%H%M%S")
        export_dir = _get_export_dir()
        if format.lower() == "csv":
            filename = f"attendance_cycle_summary_{timestamp}.csv"
            import os
            file_path = os.path.join(export_dir, filename)
            df.to_csv(file_path, index=False, encoding="utf-8-sig")
        else:
            filename = f"attendance_cycle_summary_{timestamp}.xlsx"
            import os
            file_path = os.path.join(export_dir, filename)
            df.to_excel(file_path, index=False, engine="openpyxl", sheet_name="考勤汇总")

        return {
            "success": True,
            "message": "考勤汇总导出成功",
            "filename": filename,
            "total_records": len(export_data),
            "download_url": f"/api/v1/attendance/download/{filename}",
            "expires_at": (dt.now().timestamp() + 3600),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"导出考勤周期汇总失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="导出考勤周期汇总失败",
        )


@router.get("/download/{filename}", summary="下载考勤导出文件")
async def download_attendance_export(filename: str) -> FileResponse:
    """下载由导出接口生成的文件。限制在 attendance_exports 目录，并限制文件名前缀。"""
    import os
    import re

    # 简单防路径穿越
    if "/" in filename or ".." in filename:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="非法文件名")

    # 限制可下载前缀
    allowed_prefix = re.compile(r"^(attendance_cycle_summary_|work_hours_export_).+\.(csv|xlsx)$")
    if not allowed_prefix.match(filename):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="不支持的文件类型")

    export_dir = _get_export_dir()
    file_path = os.path.join(export_dir, filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="文件不存在或已过期")

    # 返回文件
    return FileResponse(
        file_path,
        filename=filename,
        media_type=("text/csv" if filename.endswith(".csv") else "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"),
    )


@router.get(
    "/summary/{month}", response_model=Dict[str, Any], summary="获取月度工时汇总"
)
async def get_monthly_work_hours_summary(
    month: str = Path(..., description="月份，格式：YYYY-MM"),
    member_id: Optional[int] = Query(
        None, description="成员ID（管理员可查看其他人汇总）"
    ),
    current_user: Member = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """
    获取指定月份的工时汇总统计

    - **month**: 月份格式为 YYYY-MM，如 2024-01
    - 基于任务完成时间统计当月工时
    """
    try:
        # 解析月份
        try:
            year, month_num = map(int, month.split("-"))
            # 获取月份的开始和结束时间
            from calendar import monthrange

            month_start = datetime(year, month_num, 1)
            month_end = datetime(
                year, month_num, monthrange(year, month_num)[1], 23, 59, 59
            )
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="月份格式错误，请使用 YYYY-MM 格式",
            )

        # 权限检查
        if member_id and member_id != current_user.id:
            if not current_user.is_admin:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="无权限查看其他人的工时汇总",
                )

        target_member_id = member_id or current_user.id

        from sqlalchemy import func, select

        from app.models.member import Member
        from app.models.task import AssistanceTask, MonitoringTask, RepairTask

        # 获取成员信息
        member_query = select(Member).where(Member.id == target_member_id)
        member_result = await db.execute(member_query)
        member = member_result.scalar_one_or_none()

        if not member:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="成员不存在"
            )

        # 统计维修任务工时
        repair_query = select(
            func.sum(RepairTask.work_minutes).label("total_minutes"),
            func.count(RepairTask.id).label("task_count"),
            func.avg(RepairTask.rating).label("avg_rating"),
        ).where(
            RepairTask.member_id == target_member_id,
            RepairTask.completion_time >= month_start,
            RepairTask.completion_time <= month_end,
            RepairTask.status == TaskStatus.COMPLETED,
        )
        repair_result = await db.execute(repair_query)
        repair_stats = repair_result.fetchone()

        # Handle null result for repair stats
        if repair_stats is None:
            repair_total_minutes = 0
            repair_task_count = 0
            repair_avg_rating = 0.0
        else:
            repair_total_minutes = repair_stats.total_minutes or 0
            repair_task_count = repair_stats.task_count or 0
            repair_avg_rating = repair_stats.avg_rating or 0.0

        # 统计监控任务工时
        monitoring_query = select(
            func.sum(MonitoringTask.work_minutes).label("total_minutes"),
            func.count(MonitoringTask.id).label("task_count"),
        ).where(
            MonitoringTask.member_id == target_member_id,
            MonitoringTask.end_time >= month_start,
            MonitoringTask.end_time <= month_end,
            MonitoringTask.status == TaskStatus.COMPLETED,
        )
        monitoring_result = await db.execute(monitoring_query)
        monitoring_stats = monitoring_result.fetchone()

        # Handle null result for monitoring stats
        if monitoring_stats is None:
            monitoring_total_minutes = 0
            monitoring_task_count = 0
        else:
            monitoring_total_minutes = monitoring_stats.total_minutes or 0
            monitoring_task_count = monitoring_stats.task_count or 0

        # 统计协助任务工时
        assistance_query = select(
            func.sum(AssistanceTask.work_minutes).label("total_minutes"),
            func.count(AssistanceTask.id).label("task_count"),
        ).where(
            AssistanceTask.member_id == target_member_id,
            AssistanceTask.end_time >= month_start,
            AssistanceTask.end_time <= month_end,
            AssistanceTask.status == TaskStatus.COMPLETED,
        )
        assistance_result = await db.execute(assistance_query)
        assistance_stats = assistance_result.fetchone()

        # Handle null result for assistance stats
        if assistance_stats is None:
            assistance_total_minutes = 0
            assistance_task_count = 0
        else:
            assistance_total_minutes = assistance_stats.total_minutes or 0
            assistance_task_count = assistance_stats.task_count or 0

        # 计算总计
        total_minutes = (
            repair_total_minutes + monitoring_total_minutes + assistance_total_minutes
        )

        return {
            "success": True,
            "message": "获取月度工时汇总成功",
            "data": {
                "member_id": target_member_id,
                "member_name": member.name,
                "year": year,
                "month": month_num,
                "month_string": f"{year:04d}-{month_num:02d}",
                "repair_tasks": {
                    "hours": round(repair_total_minutes / 60, 2),
                    "minutes": repair_total_minutes,
                    "task_count": repair_task_count,
                    "average_rating": round(repair_avg_rating, 2),
                },
                "monitoring_tasks": {
                    "hours": round(monitoring_total_minutes / 60, 2),
                    "minutes": monitoring_total_minutes,
                    "task_count": monitoring_task_count,
                },
                "assistance_tasks": {
                    "hours": round(assistance_total_minutes / 60, 2),
                    "minutes": assistance_total_minutes,
                    "task_count": assistance_task_count,
                },
                "total": {
                    "hours": round(total_minutes / 60, 2),
                    "minutes": total_minutes,
                    "task_count": repair_task_count
                    + monitoring_task_count
                    + assistance_task_count,
                },
            },
            "status_code": 200,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取月度工时汇总失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取月度工时汇总失败",
        )


@router.get(
    "/today-summary", response_model=Dict[str, Any], summary="获取今日工时统计概览"
)
@router.get(
    "/today", response_model=Dict[str, Any], summary="获取今日工时统计概览（别名）"
)
async def get_today_work_hours_summary(
    current_user: Member = Depends(get_current_user), db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """获取今日工时统计概览"""
    try:
        from sqlalchemy import func, select

        from app.models.member import Member
        from app.models.task import AssistanceTask, MonitoringTask, RepairTask

        today = datetime.now().date()
        today_start = datetime.combine(today, datetime.min.time())
        today_end = datetime.combine(today, datetime.max.time())

        # 获取今日完成的维修任务工时
        repair_hours_query = select(func.sum(RepairTask.work_minutes)).where(
            RepairTask.completion_time >= today_start,
            RepairTask.completion_time <= today_end,
            RepairTask.status == TaskStatus.COMPLETED,
        )
        repair_result = await db.execute(repair_hours_query)
        repair_minutes = repair_result.scalar() or 0

        # 获取今日完成的监控任务工时
        monitoring_hours_query = select(func.sum(MonitoringTask.work_minutes)).where(
            MonitoringTask.end_time >= today_start,
            MonitoringTask.end_time <= today_end,
            MonitoringTask.status == TaskStatus.COMPLETED,
        )
        monitoring_result = await db.execute(monitoring_hours_query)
        monitoring_minutes = monitoring_result.scalar() or 0

        # 获取今日完成的协助任务工时
        assistance_hours_query = select(func.sum(AssistanceTask.work_minutes)).where(
            AssistanceTask.end_time >= today_start,
            AssistanceTask.end_time <= today_end,
            AssistanceTask.status == TaskStatus.COMPLETED,
        )
        assistance_result = await db.execute(assistance_hours_query)
        assistance_minutes = assistance_result.scalar() or 0

        # 转换为小时
        total_hours = (repair_minutes + monitoring_minutes + assistance_minutes) / 60
        repair_hours = repair_minutes / 60
        monitoring_hours = monitoring_minutes / 60
        assistance_hours = assistance_minutes / 60

        # 获取今日有工时记录的成员数
        active_members_query = select(
            func.count(func.distinct(RepairTask.member_id))
        ).where(
            RepairTask.completion_time >= today_start,
            RepairTask.completion_time <= today_end,
            RepairTask.status == TaskStatus.COMPLETED,
        )
        active_result = await db.execute(active_members_query)
        active_members = active_result.scalar() or 0

        # 获取总成员数
        total_members_query = select(func.count(Member.id)).where(Member.is_active)
        total_members_result = await db.execute(total_members_query)
        total_members = total_members_result.scalar() or 0

        return {
            "success": True,
            "message": "获取今日工时统计成功",
            "data": {
                "date": today.isoformat(),
                "total_members": total_members,
                "active_members": active_members,
                "total_hours": round(total_hours, 2),
                "repair_hours": round(repair_hours, 2),
                "monitoring_hours": round(monitoring_hours, 2),
                "assistance_hours": round(assistance_hours, 2),
                "average_hours": (
                    round(total_hours / active_members, 2) if active_members > 0 else 0
                ),
                "participation_rate": (
                    round(active_members / total_members * 100, 1)
                    if total_members > 0
                    else 0
                ),
            },
            "status_code": 200,
        }

    except Exception as e:
        logger.error(f"获取今日工时统计失败: {str(e)}")
        return {
            "success": False,
            "message": "获取今日工时统计失败",
            "details": {"error": str(e)},
            "status_code": 500,
        }


@router.get("/export", summary="导出工时数据")
async def export_work_hours_data(
    date_from: date = Query(..., description="开始日期"),
    date_to: date = Query(..., description="结束日期"),
    member_ids: Optional[List[int]] = Query(None, description="成员ID列表"),
    format: str = Query("excel", description="导出格式（仅支持excel）"),
    current_user: Member = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """按照既定模板导出考勤工时数据，多工作表Excel版本。"""
    try:
        # 目前仅支持Excel多工作表导出
        if format.lower() != "excel":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="当前仅支持Excel格式导出",
            )

        from datetime import datetime as dt

        import os
        import pandas as pd
        from sqlalchemy import and_, select
        from sqlalchemy.orm import selectinload

        from app.models.attendance import MonthlyAttendanceSummary
        from app.models.task import (
            AssistanceTask,
            MonitoringTask,
            RepairTask,
            TaskTagType,
        )

        # 权限控制：管理员可导出全量，普通成员仅能导出自己的数据
        if current_user.is_admin:
            target_member_ids: Optional[set[int]] = (
                set(map(int, member_ids)) if member_ids else None
            )
        else:
            target_member_ids = {current_user.id}
            if member_ids and any(mid != current_user.id for mid in member_ids):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="无权限导出其他成员的数据",
                )

        if date_from > date_to:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="开始日期不能晚于结束日期",
            )

        if date_from.year != date_to.year or date_from.month != date_to.month:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="导出时间范围必须在同一个自然月内",
            )

        target_year = date_from.year
        target_month = date_from.month
        month_label = f"{target_month}月"
        month_display = f"{target_year}年{target_month:02d}月"

        date_from_dt = datetime.combine(date_from, datetime.min.time())
        date_to_dt = datetime.combine(date_to, datetime.max.time())

        # 查询成员基础信息
        member_query = select(Member).where(Member.is_active.is_(True))
        if target_member_ids is not None:
            if not target_member_ids:
                return {
                    "success": True,
                    "message": "没有找到符合条件的工时数据",
                    "total_records": 0,
                }
            member_query = member_query.where(Member.id.in_(target_member_ids))

        member_result = await db.execute(member_query)
        member_records = list(member_result.scalars().all())

        if not member_records:
            return {
                "success": True,
                "message": "没有找到符合条件的工时数据",
                "total_records": 0,
            }

        member_info: Dict[int, Dict[str, str]] = {}
        for member in member_records:
            member_info[member.id] = {
                "name": member.name,
                "class_name": member.class_name,
            }

        # 校验请求的成员是否都存在
        if current_user.is_admin and target_member_ids is not None:
            missing_members = target_member_ids - set(member_info.keys())
            if missing_members:
                missing_ids = ", ".join(str(mid) for mid in sorted(missing_members))
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"指定成员不存在或已离职: {missing_ids}",
                )

        export_member_ids = set(member_info.keys())

        # 获取指定月份的结转信息
        summary_query = (
            select(
                MonthlyAttendanceSummary.member_id,
                MonthlyAttendanceSummary.carried_hours,
            )
            .where(
                and_(
                    MonthlyAttendanceSummary.year == target_year,
                    MonthlyAttendanceSummary.month == target_month,
                    MonthlyAttendanceSummary.member_id.in_(export_member_ids),
                )
            )
        )
        summary_result = await db.execute(summary_query)
        carried_map: Dict[int, float] = {
            member_id: float(carried or 0.0)
            for member_id, carried in summary_result.all()
        }

        # 预先填充统计结构
        stats_map: Dict[int, Dict[str, Any]] = {}

        def ensure_member_stat(member_id: int, fallback: Optional[Member] = None) -> Dict[str, Any]:
            if member_id not in stats_map:
                info = member_info.get(member_id)
                if not info and fallback is not None:
                    info = {
                        "name": fallback.name,
                        "class_name": fallback.class_name,
                    }
                    member_info[member_id] = info
                if not info:
                    info = {"name": "", "class_name": ""}
                    member_info[member_id] = info

                stats_map[member_id] = {
                    "member_id": member_id,
                    "name": info["name"],
                    "class_name": info["class_name"],
                    "carried_hours": float(carried_map.get(member_id, 0.0)),
                    "repair_minutes": 0.0,
                    "repair_total_minutes": 0.0,
                    "repair_count": 0,
                    "late_response_count": 0,
                    "late_completion_count": 0,
                    "positive_count": 0,
                    "positive_minutes": 0.0,
                    "timeout_penalty_minutes": 0.0,
                    "monitoring_minutes": 0.0,
                    "assistance_minutes": 0.0,
                }
            return stats_map[member_id]

        for mid in export_member_ids:
            ensure_member_stat(mid)

        # 查询并统计报修任务
        repair_query = (
            select(RepairTask)
            .options(selectinload(RepairTask.tags), selectinload(RepairTask.member))
            .where(
                RepairTask.status == TaskStatus.COMPLETED,
                RepairTask.completion_time >= date_from_dt,
                RepairTask.completion_time <= date_to_dt,
            )
        )
        if export_member_ids:
            repair_query = repair_query.where(RepairTask.member_id.in_(export_member_ids))

        repair_result = await db.execute(repair_query)
        repair_tasks = list(repair_result.scalars().all())

        for task in repair_tasks:
            stat = ensure_member_stat(task.member_id, task.member)
            task_minutes = float(task.work_minutes or 0.0)
            stat["repair_minutes"] += task_minutes
            stat["repair_total_minutes"] += task_minutes
            stat["repair_count"] += 1

            positive_minutes = 0.0
            has_positive = False
            late_response_minutes = 0.0
            late_completion_minutes = 0.0

            for tag in getattr(task, "tags", []):
                tag_type = getattr(tag, "tag_type", None)
                if hasattr(tag_type, "value"):
                    tag_type_value = tag_type.value
                else:
                    tag_type_value = str(tag_type or "")
                modifier = float(getattr(tag, "work_minutes_modifier", 0) or 0.0)
                tag_name_lower = (getattr(tag, "name", "") or "").lower()

                if tag_type_value in {TaskTagType.NON_DEFAULT_RATING.value, TaskTagType.BONUS.value} and modifier > 0:
                    positive_minutes += modifier
                    has_positive = True
                    continue

                if tag_type_value == TaskTagType.TIMEOUT_RESPONSE.value:
                    penalty = abs(modifier)
                    late_response_minutes += penalty
                    continue

                if tag_type_value == TaskTagType.TIMEOUT_PROCESSING.value:
                    penalty = abs(modifier)
                    late_completion_minutes += penalty
                    continue

                if tag_type_value == TaskTagType.PENALTY.value and modifier != 0:
                    penalty = abs(modifier)
                    if "响应" in tag_name_lower or "response" in tag_name_lower:
                        late_response_minutes += penalty
                    elif "处理" in tag_name_lower or "completion" in tag_name_lower:
                        late_completion_minutes += penalty

            if has_positive:
                stat["positive_count"] += 1
            stat["positive_minutes"] += positive_minutes

            if late_response_minutes > 0:
                stat["late_response_count"] += 1
            if late_completion_minutes > 0:
                stat["late_completion_count"] += 1
            stat["timeout_penalty_minutes"] += late_response_minutes + late_completion_minutes

        # 查询并统计监控任务
        monitoring_query = (
            select(MonitoringTask)
            .options(selectinload(MonitoringTask.member))
            .where(
                MonitoringTask.status == TaskStatus.COMPLETED,
                MonitoringTask.end_time >= date_from_dt,
                MonitoringTask.end_time <= date_to_dt,
            )
        )
        if export_member_ids:
            monitoring_query = monitoring_query.where(
                MonitoringTask.member_id.in_(export_member_ids)
            )

        monitoring_result = await db.execute(monitoring_query)
        monitoring_tasks = list(monitoring_result.scalars().all())

        for task in monitoring_tasks:
            stat = ensure_member_stat(task.member_id, task.member)
            stat["monitoring_minutes"] += float(task.work_minutes or 0.0)

        # 查询并统计协助任务
        assistance_query = (
            select(AssistanceTask)
            .options(selectinload(AssistanceTask.member))
            .where(
                AssistanceTask.status == TaskStatus.COMPLETED,
                AssistanceTask.end_time >= date_from_dt,
                AssistanceTask.end_time <= date_to_dt,
            )
        )
        if export_member_ids:
            assistance_query = assistance_query.where(
                AssistanceTask.member_id.in_(export_member_ids)
            )

        assistance_result = await db.execute(assistance_query)
        assistance_tasks = list(assistance_result.scalars().all())

        assistance_rows: List[Dict[str, Any]] = []

        for task in assistance_tasks:
            stat = ensure_member_stat(task.member_id, task.member)
            if task.work_minutes is not None:
                duration_minutes = float(task.work_minutes)
            elif task.start_time and task.end_time:
                duration_minutes = (
                    (task.end_time - task.start_time).total_seconds() / 60.0
                )
            else:
                duration_minutes = 0.0

            stat["assistance_minutes"] += duration_minutes

            member_meta = member_info.get(task.member_id, {"name": "", "class_name": ""})
            start_time = task.start_time
            end_time = task.end_time

            date_str = (
                start_time.strftime("%Y-%m-%d")
                if start_time
                else (end_time.strftime("%Y-%m-%d") if end_time else "")
            )
            time_range = ""
            if start_time and end_time:
                time_range = f"{start_time.strftime('%H:%M')} - {end_time.strftime('%H:%M')}"

            assistance_rows.append(
                {
                    "序号": 0,  # 占位，写入前统一编号
                    "班级": member_meta.get("class_name", ""),
                    "姓名": member_meta.get("name", ""),
                    "协助任务名称": task.title or "",
                    "协助任务地点": task.assisted_department or "",
                    "协助任务日期": date_str,
                    "协助任务时间段": time_range,
                    "协助任务小时数": round(duration_minutes / 60.0, 2),
                    "签名": "",
                }
            )

        assistance_rows.sort(
            key=lambda item: (
                item["班级"],
                item["姓名"],
                item["协助任务日期"],
                item["协助任务时间段"],
            )
        )
        for idx, row in enumerate(assistance_rows, start=1):
            row["序号"] = idx

        # 组装汇总数据
        sorted_stats = sorted(
            stats_map.values(), key=lambda item: (item["class_name"], item["name"])
        )

        def _to_hours(minutes: float) -> float:
            return round(float(minutes or 0.0) / 60.0, 2)

        summary_rows: List[Dict[str, Any]] = []
        repair_rows: List[Dict[str, Any]] = []

        for idx, stat in enumerate(sorted_stats, start=1):
            carried_hours = round(float(stat.get("carried_hours", 0.0)), 2)
            repair_hours = _to_hours(stat.get("repair_minutes", 0.0))
            monitoring_hours = _to_hours(stat.get("monitoring_minutes", 0.0))
            assistance_hours = _to_hours(stat.get("assistance_minutes", 0.0))
            total_hours = round(
                carried_hours + repair_hours + monitoring_hours + assistance_hours, 2
            )

            summary_rows.append(
                {
                    "序号": idx,
                    "班级": stat["class_name"],
                    "姓名": stat["name"],
                    "上月结转时长": carried_hours,
                    "报修单协助时长": repair_hours,
                    "日常监控协助时长": monitoring_hours,
                    "协助任务协助时长": assistance_hours,
                    "工作总时长": total_hours,
                    "签名": "",
                }
            )

            repair_rows.append(
                {
                    "序号": idx,
                    "班级": stat["class_name"],
                    "姓名": stat["name"],
                    "报修单总数": stat["repair_count"],
                    "响应超时单数": stat["late_response_count"],
                    "处理超时单数": stat["late_completion_count"],
                    "超时扣除时间数": _to_hours(stat["timeout_penalty_minutes"]),
                    "好评单数": stat["positive_count"],
                    "好评折算时间数": _to_hours(stat["positive_minutes"]),
                    "汇总时间数": _to_hours(stat["repair_total_minutes"]),
                    "签名": "",
                }
            )

        # 导出参数信息工作表
        current_time = dt.now()
        config_rows = [
            {"参数": "导出时间", "数值": current_time.strftime("%Y-%m-%d %H:%M:%S"), "说明": ""},
            {
                "参数": "导出范围",
                "数值": f"{date_from.isoformat()} 至 {date_to.isoformat()}",
                "说明": "含首尾日期，按任务完成时间统计",
            },
            {"参数": "导出月份", "数值": month_display, "说明": ""},
            {
                "参数": "导出人",
                "数值": current_user.name or current_user.username,
                "说明": f"ID: {current_user.id}",
            },
            {
                "参数": "成员数量",
                "数值": len(sorted_stats),
                "说明": "统计范围内的成员数量",
            },
            {
                "参数": "线上任务基础工时(分钟)",
                "数值": 40,
                "说明": "非爆单线上任务默认工时",
            },
            {
                "参数": "线下任务基础工时(分钟)",
                "数值": 100,
                "说明": "非爆单线下任务默认工时",
            },
            {
                "参数": "爆单任务工时(分钟)",
                "数值": 15,
                "说明": "爆单任务固定工时",
            },
            {
                "参数": "非默认好评奖励(分钟)",
                "数值": 30,
                "说明": "带文字好评的额外工时",
            },
            {
                "参数": "响应超时扣时(分钟)",
                "数值": 30,
                "说明": "超过24小时未响应",
            },
            {
                "参数": "处理超时扣时(分钟)",
                "数值": 30,
                "说明": "超过48小时未完成",
            },
            {
                "参数": "差评扣时(分钟)",
                "数值": 60,
                "说明": "差评触发扣时",
            },
            {
                "参数": "响应超时阈值(小时)",
                "数值": 24,
                "说明": "超过阈值视为超时响应",
            },
            {
                "参数": "处理超时阈值(小时)",
                "数值": 48,
                "说明": "超过阈值视为超时处理",
            },
            {
                "参数": "月度满勤标准(小时)",
                "数值": 30,
                "说明": "用于结转判断",
            },
        ]

        summary_df = pd.DataFrame(
            summary_rows,
            columns=[
                "序号",
                "班级",
                "姓名",
                "上月结转时长",
                "报修单协助时长",
                "日常监控协助时长",
                "协助任务协助时长",
                "工作总时长",
                "签名",
            ],
        )
        repair_df = pd.DataFrame(
            repair_rows,
            columns=[
                "序号",
                "班级",
                "姓名",
                "报修单总数",
                "响应超时单数",
                "处理超时单数",
                "超时扣除时间数",
                "好评单数",
                "好评折算时间数",
                "汇总时间数",
                "签名",
            ],
        )
        assistance_df = pd.DataFrame(
            assistance_rows,
            columns=[
                "序号",
                "班级",
                "姓名",
                "协助任务名称",
                "协助任务地点",
                "协助任务日期",
                "协助任务时间段",
                "协助任务小时数",
                "签名",
            ],
        )
        info_df = pd.DataFrame(
            config_rows,
            columns=["参数", "数值", "说明"],
        )

        timestamp = current_time.strftime("%Y%m%d_%H%M%S")
        filename = f"work_hours_export_{target_year}{target_month:02d}_{timestamp}.xlsx"
        export_dir = _get_export_dir()
        file_path = os.path.join(export_dir, filename)

        with pd.ExcelWriter(file_path, engine="openpyxl") as writer:
            summary_df.to_excel(writer, index=False, sheet_name="汇总")
            repair_df.to_excel(
                writer,
                index=False,
                sheet_name=f"报修单工作时长-{month_label}",
            )
            assistance_df.to_excel(
                writer,
                index=False,
                sheet_name=f"协助任务-{month_label}",
            )
            info_df.to_excel(writer, index=False, sheet_name="导出信息")

        return {
            "success": True,
            "message": "工时数据导出成功",
            "filename": filename,
            "total_records": len(summary_rows),
            "download_url": f"/api/v1/attendance/download/{filename}",
            "expires_at": current_time.timestamp() + 3600,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"导出工时数据失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="导出工时数据失败"
        )


@router.get("/stats", response_model=Dict[str, Any], summary="获取工时统计")
async def get_work_hours_stats(
    memberId: Optional[int] = Query(None, description="成员ID"),
    startDate: str = Query(..., description="开始日期 YYYY-MM-DD"),
    endDate: str = Query(..., description="结束日期 YYYY-MM-DD"),
    current_user: Member = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """
    获取指定时间范围内的工时统计数据
    """
    try:
        from sqlalchemy import func, select

        from app.models.member import Member
        from app.models.task import RepairTask

        # 解析日期
        try:
            start_date = datetime.strptime(startDate, "%Y-%m-%d").date()
            end_date = datetime.strptime(endDate, "%Y-%m-%d").date()
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="日期格式错误，请使用 YYYY-MM-DD 格式",
            )

        start_datetime = datetime.combine(start_date, datetime.min.time())
        end_datetime = datetime.combine(end_date, datetime.max.time())

        # 权限检查
        if memberId and memberId != current_user.id:
            if not current_user.is_admin:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="无权限查看其他人的工时统计",
                )

        target_member_id = memberId or current_user.id

        # 统计维修任务工时
        repair_query = select(
            func.sum(RepairTask.work_minutes).label("total_minutes"),
            func.count(RepairTask.id).label("task_count"),
            func.avg(RepairTask.rating).label("avg_rating"),
            func.min(RepairTask.work_minutes).label("min_minutes"),
            func.max(RepairTask.work_minutes).label("max_minutes"),
        ).where(
            RepairTask.member_id == target_member_id,
            RepairTask.completion_time >= start_datetime,
            RepairTask.completion_time <= end_datetime,
            RepairTask.status == TaskStatus.COMPLETED,
        )

        repair_result = await db.execute(repair_query)
        repair_stats = repair_result.fetchone()

        # Handle null result for repair stats
        if repair_stats is None:
            total_minutes = 0
            task_count = 0
            avg_rating = 0.0
            min_minutes = 0
            max_minutes = 0
        else:
            total_minutes = repair_stats.total_minutes or 0
            task_count = repair_stats.task_count or 0
            avg_rating = repair_stats.avg_rating or 0.0
            min_minutes = repair_stats.min_minutes or 0
            max_minutes = repair_stats.max_minutes or 0

        # 获取成员信息
        member_query = select(Member).where(Member.id == target_member_id)
        member_result = await db.execute(member_query)
        member = member_result.scalar_one_or_none()

        if not member:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="成员不存在"
            )

        # 统计数据已在上面处理完成

        return {
            "success": True,
            "message": "获取工时统计成功",
            "data": {
                "member_id": target_member_id,
                "member_name": member.name,
                "period": {"start_date": startDate, "end_date": endDate},
                "total_hours": round(total_minutes / 60, 2),
                "total_minutes": total_minutes,
                "task_count": task_count,
                "average_hours_per_task": (
                    round(total_minutes / task_count / 60, 2) if task_count > 0 else 0
                ),
                "average_rating": round(avg_rating, 2),
                "min_hours_per_task": round(min_minutes / 60, 2),
                "max_hours_per_task": round(max_minutes / 60, 2),
                "working_days": (end_date - start_date).days + 1,
                "average_daily_hours": round(
                    total_minutes / ((end_date - start_date).days + 1) / 60, 2
                ),
            },
            "status_code": 200,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取工时统计失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="获取工时统计失败"
        )


@router.get("/chart-data", response_model=Dict[str, Any], summary="获取工时图表数据")
async def get_work_hours_chart_data(
    type: str = Query(..., description="图表类型: daily/weekly/monthly"),
    startDate: str = Query(..., description="开始日期 YYYY-MM-DD"),
    endDate: str = Query(..., description="结束日期 YYYY-MM-DD"),
    memberId: Optional[int] = Query(None, description="成员ID"),
    current_user: Member = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """
    获取工时图表数据，支持按日、周、月聚合
    """
    try:
        from sqlalchemy import String, func, select

        from app.models.task import RepairTask

        # 验证图表类型
        if type not in ["daily", "weekly", "monthly"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="图表类型必须是 daily、weekly 或 monthly",
            )

        # 解析日期
        try:
            start_date = datetime.strptime(startDate, "%Y-%m-%d").date()
            end_date = datetime.strptime(endDate, "%Y-%m-%d").date()
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="日期格式错误，请使用 YYYY-MM-DD 格式",
            )

        start_datetime = datetime.combine(start_date, datetime.min.time())
        end_datetime = datetime.combine(end_date, datetime.max.time())

        # 权限检查
        if memberId and memberId != current_user.id:
            if not current_user.is_admin:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="无权限查看其他人的工时图表",
                )

        # 构建查询条件
        query_conditions = [
            RepairTask.completion_time >= start_datetime,
            RepairTask.completion_time <= end_datetime,
            RepairTask.status == TaskStatus.COMPLETED,
        ]

        if memberId:
            query_conditions.append(RepairTask.member_id == memberId)

        # 根据图表类型构建查询
        if type == "daily":
            # 按日期分组
            chart_query = (
                select(
                    func.date(RepairTask.completion_time).label("period"),
                    func.sum(RepairTask.work_minutes).label("total_minutes"),
                    func.count(RepairTask.id).label("task_count"),
                )
                .where(
                    RepairTask.completion_time >= start_datetime,
                    RepairTask.completion_time <= end_datetime,
                    RepairTask.status == TaskStatus.COMPLETED,
                    *([RepairTask.member_id == memberId] if memberId else []),
                )
                .group_by(func.date(RepairTask.completion_time))
                .order_by(func.date(RepairTask.completion_time))
            )

        elif type == "weekly":
            # 按周分组 (ISO周)
            chart_query = (
                select(
                    func.concat(
                        func.extract("year", RepairTask.completion_time),
                        "-W",
                        func.lpad(
                            func.extract("week", RepairTask.completion_time).cast(
                                String
                            ),
                            2,
                            "0",
                        ),
                    ).label("period"),
                    func.sum(RepairTask.work_minutes).label("total_minutes"),
                    func.count(RepairTask.id).label("task_count"),
                )
                .where(
                    RepairTask.completion_time >= start_datetime,
                    RepairTask.completion_time <= end_datetime,
                    RepairTask.status == TaskStatus.COMPLETED,
                    *([RepairTask.member_id == memberId] if memberId else []),
                )
                .group_by(
                    func.extract("year", RepairTask.completion_time),
                    func.extract("week", RepairTask.completion_time),
                )
                .order_by(
                    func.extract("year", RepairTask.completion_time),
                    func.extract("week", RepairTask.completion_time),
                )
            )

        else:  # monthly
            # 按月分组
            chart_query = (
                select(
                    func.concat(
                        func.extract("year", RepairTask.completion_time),
                        "-",
                        func.lpad(
                            func.extract("month", RepairTask.completion_time).cast(
                                String
                            ),
                            2,
                            "0",
                        ),
                    ).label("period"),
                    func.sum(RepairTask.work_minutes).label("total_minutes"),
                    func.count(RepairTask.id).label("task_count"),
                )
                .where(
                    RepairTask.completion_time >= start_datetime,
                    RepairTask.completion_time <= end_datetime,
                    RepairTask.status == TaskStatus.COMPLETED,
                    *([RepairTask.member_id == memberId] if memberId else []),
                )
                .group_by(
                    func.extract("year", RepairTask.completion_time),
                    func.extract("month", RepairTask.completion_time),
                )
                .order_by(
                    func.extract("year", RepairTask.completion_time),
                    func.extract("month", RepairTask.completion_time),
                )
            )

        chart_result = await db.execute(chart_query)
        chart_data = chart_result.fetchall()

        # 格式化数据
        labels = []
        hours_data = []
        task_counts = []

        for row in chart_data:
            labels.append(str(row.period))
            hours_data.append(round((row.total_minutes or 0) / 60, 2))
            task_counts.append(row.task_count or 0)

        return {
            "success": True,
            "message": "获取图表数据成功",
            "data": {
                "type": type,
                "period": {"start_date": startDate, "end_date": endDate},
                "chart": {
                    "labels": labels,
                    "datasets": [
                        {
                            "label": "工时(小时)",
                            "data": hours_data,
                            "backgroundColor": "#409EFF",
                            "borderColor": "#409EFF",
                            "type": "line" if type == "daily" else "bar",
                        },
                        {
                            "label": "任务数量",
                            "data": task_counts,
                            "backgroundColor": "#67C23A",
                            "borderColor": "#67C23A",
                            "type": "bar",
                            "yAxisID": "y1",
                        },
                    ],
                },
                "summary": {
                    "total_hours": sum(hours_data),
                    "total_tasks": sum(task_counts),
                    "average_hours": (
                        round(sum(hours_data) / len(hours_data), 2) if hours_data else 0
                    ),
                    "periods": len(labels),
                },
            },
            "status_code": 200,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取图表数据失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="获取图表数据失败"
        )


@router.get("/health", response_model=Dict[str, Any], summary="健康检查")
async def health_check() -> Dict[str, Any]:
    """
    工时管理服务健康检查
    """
    from datetime import datetime

    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "work_hours_management",
        "message": "工时管理服务运行正常",
    }
