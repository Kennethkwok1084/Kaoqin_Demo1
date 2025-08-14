"""
统计分析API端点
提供综合的数据统计分析、报表生成和数据可视化接口
"""

import logging
from calendar import monthrange
from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional

from app.api.deps import (create_error_response, create_response,
                          get_current_active_admin,
                          get_current_active_group_leader, get_current_user,
                          get_db)
from app.core.config import settings
from app.models.attendance import (AttendanceException,
                                   AttendanceExceptionStatus, AttendanceRecord)
from app.models.member import Member, UserRole
from app.models.task import (AssistanceTask, MonitoringTask, RepairTask,
                             TaskCategory, TaskPriority, TaskStatus, TaskTag,
                             TaskType)
from app.services.attendance_service import AttendanceService
from app.services.task_service import TaskService
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import and_, case, desc, extract, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

logger = logging.getLogger(__name__)
router = APIRouter()


# ============= 综合数据概览 =============


@router.get("/overview", response_model=Dict[str, Any])
async def get_statistics_overview(
    date_from: Optional[datetime] = Query(None, description="统计开始时间"),
    date_to: Optional[datetime] = Query(None, description="统计结束时间"),
    current_user: Member = Depends(get_current_active_group_leader),
    db: AsyncSession = Depends(get_db),
):
    """
    获取系统概览统计

    权限：组长及以上可查看
    """
    try:
        # 设置默认时间范围（最近30天）
        if not date_to:
            date_to = datetime.utcnow()
        if not date_from:
            date_from = date_to - timedelta(days=30)

        # 基础查询条件
        time_filter = and_(
            RepairTask.created_at >= date_from, RepairTask.created_at <= date_to
        )

        # 任务统计
        task_query = select(
            func.count().label("total_tasks"),
            func.count(case((RepairTask.status == TaskStatus.COMPLETED, 1))).label(
                "completed_tasks"
            ),
            func.count(case((RepairTask.status == TaskStatus.IN_PROGRESS, 1))).label(
                "in_progress_tasks"
            ),
            func.count(case((RepairTask.status == TaskStatus.PENDING, 1))).label(
                "pending_tasks"
            ),
            func.sum(RepairTask.work_minutes).label("total_work_minutes"),
            func.avg(RepairTask.work_minutes).label("avg_work_minutes"),
            func.count(case((RepairTask.task_type == TaskType.ONLINE, 1))).label(
                "online_tasks"
            ),
            func.count(case((RepairTask.task_type == TaskType.OFFLINE, 1))).label(
                "offline_tasks"
            ),
        ).where(time_filter)

        task_result = await db.execute(task_query)
        task_stats = task_result.first()

        # 成员统计
        member_query = select(
            func.count().label("total_members"),
            func.count(case((Member.is_active == True, 1))).label("active_members"),
            func.count(case((Member.role == UserRole.ADMIN, 1))).label("admin_count"),
            func.count(case((Member.role == UserRole.GROUP_LEADER, 1))).label(
                "leader_count"
            ),
            func.count(case((Member.role == UserRole.MEMBER, 1))).label("member_count"),
        )

        member_result = await db.execute(member_query)
        member_stats = member_result.first()

        # 考勤统计（当月）
        current_month_start = datetime.now().replace(
            day=1, hour=0, minute=0, second=0, microsecond=0
        )
        next_month = current_month_start.replace(
            month=current_month_start.month % 12 + 1
        )
        if current_month_start.month == 12:
            next_month = current_month_start.replace(
                year=current_month_start.year + 1, month=1
            )

        attendance_query = select(
            func.count().label("total_attendance"),
            func.count(case((AttendanceRecord.is_late_checkin == True, 1))).label(
                "late_checkins"
            ),
            func.count(case((AttendanceRecord.is_early_checkout == True, 1))).label(
                "early_checkouts"
            ),
            func.avg(AttendanceRecord.work_hours).label("avg_work_hours"),
            func.sum(AttendanceRecord.work_hours).label("total_work_hours"),
        ).where(
            and_(
                AttendanceRecord.attendance_date >= current_month_start.date(),
                AttendanceRecord.attendance_date < next_month.date(),
            )
        )

        attendance_result = await db.execute(attendance_query)
        attendance_stats = attendance_result.first()

        # 近期趋势（最近7天每天的任务创建数）
        seven_days_ago = date_to - timedelta(days=7)
        trend_query = (
            select(
                func.date(RepairTask.created_at).label("date"),
                func.count().label("task_count"),
            )
            .where(
                and_(
                    RepairTask.created_at >= seven_days_ago,
                    RepairTask.created_at <= date_to,
                )
            )
            .group_by(func.date(RepairTask.created_at))
            .order_by(func.date(RepairTask.created_at))
        )

        trend_result = await db.execute(trend_query)
        daily_trends = [
            {"date": str(row.date), "task_count": row.task_count}
            for row in trend_result.fetchall()
        ]

        # 热门故障类别统计
        category_query = (
            select(
                RepairTask.category,
                func.count().label("count"),
                func.avg(RepairTask.work_minutes).label("avg_work_minutes"),
            )
            .where(time_filter)
            .group_by(RepairTask.category)
            .order_by(desc(func.count()))
        )

        category_result = await db.execute(category_query)
        category_stats = [
            {
                "category": row.category.value if row.category else "未分类",
                "count": row.count,
                "avg_work_hours": (
                    round(row.avg_work_minutes / 60.0, 2) if row.avg_work_minutes else 0
                ),
            }
            for row in category_result.fetchall()
        ]

        # 构建响应数据
        overview_data = {
            "period": {"from": date_from.isoformat(), "to": date_to.isoformat()},
            "tasks": {
                "total": task_stats.total_tasks or 0,
                "completed": task_stats.completed_tasks or 0,
                "in_progress": task_stats.in_progress_tasks or 0,
                "pending": task_stats.pending_tasks or 0,
                "completion_rate": round(
                    (task_stats.completed_tasks or 0)
                    / max(task_stats.total_tasks or 1, 1)
                    * 100,
                    2,
                ),
                "total_work_hours": round(
                    (task_stats.total_work_minutes or 0) / 60.0, 2
                ),
                "avg_work_hours": round((task_stats.avg_work_minutes or 0) / 60.0, 2),
                "online_tasks": task_stats.online_tasks or 0,
                "offline_tasks": task_stats.offline_tasks or 0,
            },
            "members": {
                "total": member_stats.total_members or 0,
                "active": member_stats.active_members or 0,
                "admin_count": member_stats.admin_count or 0,
                "leader_count": member_stats.leader_count or 0,
                "member_count": member_stats.member_count or 0,
            },
            "attendance": {
                "total_records": attendance_stats.total_attendance or 0,
                "late_checkins": attendance_stats.late_checkins or 0,
                "early_checkouts": attendance_stats.early_checkouts or 0,
                "avg_work_hours": round(attendance_stats.avg_work_hours or 0, 2),
                "total_work_hours": round(attendance_stats.total_work_hours or 0, 2),
                "late_rate": round(
                    (attendance_stats.late_checkins or 0)
                    / max(attendance_stats.total_attendance or 1, 1)
                    * 100,
                    2,
                ),
            },
            "trends": {"daily_task_creation": daily_trends},
            "categories": category_stats,
        }

        logger.info(f"Statistics overview retrieved by {current_user.student_id}")

        return create_response(data=overview_data, message="系统概览统计获取成功")

    except Exception as e:
        logger.error(f"Get statistics overview error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取系统概览统计失败",
        )


# ============= 工作效率分析 =============


@router.get("/efficiency", response_model=Dict[str, Any])
async def get_efficiency_analysis(
    date_from: Optional[datetime] = Query(None, description="分析开始时间"),
    date_to: Optional[datetime] = Query(None, description="分析结束时间"),
    member_id: Optional[int] = Query(None, description="指定成员分析"),
    group_by: str = Query(
        "member", regex="^(member|day|week|month)$", description="分组方式"
    ),
    current_user: Member = Depends(get_current_active_group_leader),
    db: AsyncSession = Depends(get_db),
):
    """
    获取工作效率分析

    权限：组长及以上可查看
    """
    try:
        # 设置默认时间范围（最近30天）
        if not date_to:
            date_to = datetime.utcnow()
        if not date_from:
            date_from = date_to - timedelta(days=30)

        # 基础查询条件
        base_query = (
            select(RepairTask)
            .options(joinedload(RepairTask.member))
            .where(
                and_(
                    RepairTask.created_at >= date_from,
                    RepairTask.created_at <= date_to,
                    RepairTask.status == TaskStatus.COMPLETED,
                )
            )
        )

        if member_id:
            base_query = base_query.where(RepairTask.member_id == member_id)

        result = await db.execute(base_query)
        tasks = result.scalars().all()

        if not tasks:
            return create_response(
                data={"message": "指定时间范围内没有已完成的任务"},
                message="效率分析数据为空",
            )

        # 按不同维度分组分析
        analysis_data = {}

        if group_by == "member":
            # 按成员分组分析
            member_groups = {}
            for task in tasks:
                member_key = task.member_id
                if member_key not in member_groups:
                    member_groups[member_key] = {
                        "member_name": task.member.name if task.member else "未知",
                        "tasks": [],
                    }
                member_groups[member_key]["tasks"].append(task)

            member_analysis = []
            for member_key, group_data in member_groups.items():
                member_tasks = group_data["tasks"]

                # 计算各项效率指标
                total_tasks = len(member_tasks)
                total_work_minutes = sum(task.work_minutes for task in member_tasks)
                avg_work_minutes = (
                    total_work_minutes / total_tasks if total_tasks > 0 else 0
                )

                # 计算完成速度（从创建到完成的平均时间）
                completion_times = []
                for task in member_tasks:
                    if task.completed_at:
                        completion_time = (
                            task.completed_at - task.created_at
                        ).total_seconds() / 3600  # 小时
                        completion_times.append(completion_time)

                avg_completion_hours = (
                    sum(completion_times) / len(completion_times)
                    if completion_times
                    else 0
                )

                # 计算评分统计
                ratings = [
                    task.rating for task in member_tasks if task.rating is not None
                ]
                avg_rating = sum(ratings) / len(ratings) if ratings else 0

                # 任务类型分布
                online_count = sum(
                    1 for task in member_tasks if task.task_type == TaskType.ONLINE
                )
                offline_count = total_tasks - online_count

                member_analysis.append(
                    {
                        "member_id": member_key,
                        "member_name": group_data["member_name"],
                        "total_tasks": total_tasks,
                        "total_work_hours": round(total_work_minutes / 60.0, 2),
                        "avg_work_hours": round(avg_work_minutes / 60.0, 2),
                        "avg_completion_hours": round(avg_completion_hours, 2),
                        "avg_rating": round(avg_rating, 2),
                        "online_tasks": online_count,
                        "offline_tasks": offline_count,
                        "efficiency_score": self._calculate_efficiency_score(
                            avg_work_minutes,
                            avg_completion_hours,
                            avg_rating,
                            total_tasks,
                        ),
                    }
                )

            # 按效率分数排序
            member_analysis.sort(key=lambda x: x["efficiency_score"], reverse=True)
            analysis_data["members"] = member_analysis

        elif group_by in ["day", "week", "month"]:
            # 按时间分组分析
            time_groups = {}
            for task in tasks:
                if group_by == "day":
                    time_key = task.created_at.strftime("%Y-%m-%d")
                elif group_by == "week":
                    week_start = task.created_at - timedelta(
                        days=task.created_at.weekday()
                    )
                    time_key = week_start.strftime("%Y-%m-%d")
                else:  # month
                    time_key = task.created_at.strftime("%Y-%m")

                if time_key not in time_groups:
                    time_groups[time_key] = []
                time_groups[time_key].append(task)

            time_analysis = []
            for time_key in sorted(time_groups.keys()):
                period_tasks = time_groups[time_key]
                total_tasks = len(period_tasks)
                total_work_minutes = sum(task.work_minutes for task in period_tasks)
                avg_work_minutes = (
                    total_work_minutes / total_tasks if total_tasks > 0 else 0
                )

                # 完成时间分析
                completion_times = []
                for task in period_tasks:
                    if task.completed_at:
                        completion_time = (
                            task.completed_at - task.created_at
                        ).total_seconds() / 3600
                        completion_times.append(completion_time)

                avg_completion_hours = (
                    sum(completion_times) / len(completion_times)
                    if completion_times
                    else 0
                )

                time_analysis.append(
                    {
                        "period": time_key,
                        "task_count": total_tasks,
                        "total_work_hours": round(total_work_minutes / 60.0, 2),
                        "avg_work_hours": round(avg_work_minutes / 60.0, 2),
                        "avg_completion_hours": round(avg_completion_hours, 2),
                    }
                )

            analysis_data["time_series"] = time_analysis

        # 总体效率指标
        total_tasks = len(tasks)
        total_work_minutes = sum(task.work_minutes for task in tasks)
        avg_work_minutes = total_work_minutes / total_tasks if total_tasks > 0 else 0

        # 完成时间统计
        completion_times = []
        for task in tasks:
            if task.completed_at:
                completion_time = (
                    task.completed_at - task.created_at
                ).total_seconds() / 3600
                completion_times.append(completion_time)

        overall_stats = {
            "total_tasks": total_tasks,
            "total_work_hours": round(total_work_minutes / 60.0, 2),
            "avg_work_hours": round(avg_work_minutes / 60.0, 2),
            "avg_completion_hours": (
                round(sum(completion_times) / len(completion_times), 2)
                if completion_times
                else 0
            ),
            "fastest_completion": (
                round(min(completion_times), 2) if completion_times else 0
            ),
            "slowest_completion": (
                round(max(completion_times), 2) if completion_times else 0
            ),
        }

        response_data = {
            "period": {
                "from": date_from.isoformat(),
                "to": date_to.isoformat(),
                "group_by": group_by,
            },
            "overall": overall_stats,
            **analysis_data,
        }

        logger.info(f"Efficiency analysis retrieved by {current_user.student_id}")

        return create_response(data=response_data, message="工作效率分析获取成功")

    except Exception as e:
        logger.error(f"Get efficiency analysis error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取工作效率分析失败",
        )


# ============= 月度报表 =============


@router.get("/monthly-report", response_model=Dict[str, Any])
async def get_monthly_report(
    year: int = Query(..., description="年份"),
    month: int = Query(..., ge=1, le=12, description="月份"),
    member_id: Optional[int] = Query(
        None, description="指定成员（不指定则生成团队报表）"
    ),
    current_user: Member = Depends(get_current_active_group_leader),
    db: AsyncSession = Depends(get_db),
):
    """
    生成月度综合报表

    权限：组长及以上可查看团队报表，所有人可查看个人报表
    """
    try:
        # 权限检查
        if (
            member_id
            and member_id != current_user.id
            and not current_user.can_manage_group
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权限查看其他人的月度报表",
            )

        # 计算月份时间范围
        first_day = date(year, month, 1)
        last_day = date(year, month, monthrange(year, month)[1])
        first_datetime = datetime.combine(first_day, datetime.min.time())
        last_datetime = datetime.combine(last_day, datetime.max.time())

        # 任务服务和考勤服务
        task_service = TaskService(db)
        attendance_service = AttendanceService(db)

        report_data = {
            "period": {
                "year": year,
                "month": month,
                "month_name": first_day.strftime("%Y年%m月"),
            }
        }

        if member_id:
            # 个人月度报表
            member_query = select(Member).where(Member.id == member_id)
            member_result = await db.execute(member_query)
            member = member_result.scalar_one_or_none()

            if not member:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail="成员不存在"
                )

            # 个人任务统计
            task_query = select(RepairTask).where(
                and_(
                    RepairTask.member_id == member_id,
                    RepairTask.created_at >= first_datetime,
                    RepairTask.created_at <= last_datetime,
                )
            )
            task_result = await db.execute(task_query)
            tasks = task_result.scalars().all()

            # 个人考勤统计
            attendance_summary = await attendance_service.get_monthly_summary(
                member_id, year, month
            )

            # 个人任务分析
            completed_tasks = [
                task for task in tasks if task.status == TaskStatus.COMPLETED
            ]
            total_work_minutes = sum(task.work_minutes for task in completed_tasks)

            task_stats = {
                "total_tasks": len(tasks),
                "completed_tasks": len(completed_tasks),
                "pending_tasks": len(
                    [task for task in tasks if task.status == TaskStatus.PENDING]
                ),
                "in_progress_tasks": len(
                    [task for task in tasks if task.status == TaskStatus.IN_PROGRESS]
                ),
                "total_work_hours": round(total_work_minutes / 60.0, 2),
                "avg_work_hours": (
                    round(total_work_minutes / len(completed_tasks) / 60.0, 2)
                    if completed_tasks
                    else 0
                ),
                "online_tasks": len(
                    [task for task in tasks if task.task_type == TaskType.ONLINE]
                ),
                "offline_tasks": len(
                    [task for task in tasks if task.task_type == TaskType.OFFLINE]
                ),
            }

            report_data.update(
                {
                    "type": "personal",
                    "member": {
                        "id": member.id,
                        "name": member.name,
                        "student_id": member.student_id,
                        "role": member.role.value,
                    },
                    "tasks": task_stats,
                    "attendance": (
                        attendance_summary.dict()
                        if hasattr(attendance_summary, "dict")
                        else attendance_summary
                    ),
                }
            )

        else:
            # 团队月度报表
            if not current_user.can_manage_group:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="无权限查看团队月度报表",
                )

            # 团队任务统计
            team_task_query = (
                select(RepairTask)
                .options(joinedload(RepairTask.member))
                .where(
                    and_(
                        RepairTask.created_at >= first_datetime,
                        RepairTask.created_at <= last_datetime,
                    )
                )
            )
            team_task_result = await db.execute(team_task_query)
            team_tasks = team_task_result.scalars().all()

            # 按成员分组统计
            member_stats = {}
            for task in team_tasks:
                member_key = task.member_id
                if member_key not in member_stats:
                    member_stats[member_key] = {
                        "member_name": task.member.name if task.member else "未知",
                        "tasks": [],
                    }
                member_stats[member_key]["tasks"].append(task)

            # 生成成员明细
            member_details = []
            for member_key, stats in member_stats.items():
                member_tasks = stats["tasks"]
                completed_tasks = [
                    task for task in member_tasks if task.status == TaskStatus.COMPLETED
                ]
                total_work_minutes = sum(task.work_minutes for task in completed_tasks)

                # 获取该成员的考勤汇总
                attendance_summary = None
                try:
                    attendance_summary = await attendance_service.get_monthly_summary(
                        member_key, year, month
                    )
                except Exception as e:
                    logger.warning(
                        f"Failed to get attendance summary for member {member_key}: {str(e)}"
                    )

                member_details.append(
                    {
                        "member_id": member_key,
                        "member_name": stats["member_name"],
                        "tasks": {
                            "total": len(member_tasks),
                            "completed": len(completed_tasks),
                            "total_work_hours": round(total_work_minutes / 60.0, 2),
                        },
                        "attendance": (
                            attendance_summary.dict()
                            if attendance_summary
                            and hasattr(attendance_summary, "dict")
                            else None
                        ),
                    }
                )

            # 团队整体统计
            total_tasks = len(team_tasks)
            completed_tasks = [
                task for task in team_tasks if task.status == TaskStatus.COMPLETED
            ]
            total_work_minutes = sum(task.work_minutes for task in completed_tasks)

            team_stats = {
                "total_tasks": total_tasks,
                "completed_tasks": len(completed_tasks),
                "completion_rate": round(
                    len(completed_tasks) / max(total_tasks, 1) * 100, 2
                ),
                "total_work_hours": round(total_work_minutes / 60.0, 2),
                "avg_work_hours": (
                    round(total_work_minutes / len(completed_tasks) / 60.0, 2)
                    if completed_tasks
                    else 0
                ),
                "active_members": len(member_stats),
            }

            report_data.update(
                {
                    "type": "team",
                    "team_summary": team_stats,
                    "member_details": member_details,
                }
            )

        logger.info(
            f"Monthly report generated by {current_user.student_id} for {year}-{month}"
        )

        return create_response(
            data=report_data, message=f"{year}年{month}月报表生成成功"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get monthly report error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="生成月度报表失败"
        )


# ============= 数据导出 =============


@router.get("/export", response_model=Dict[str, Any])
async def export_statistics_data(
    export_type: str = Query(
        ..., regex="^(overview|efficiency|monthly|attendance)$", description="导出类型"
    ),
    format: str = Query("excel", regex="^(excel|csv|json)$", description="导出格式"),
    date_from: Optional[datetime] = Query(None, description="开始时间"),
    date_to: Optional[datetime] = Query(None, description="结束时间"),
    member_id: Optional[int] = Query(None, description="成员筛选"),
    current_user: Member = Depends(get_current_active_group_leader),
    db: AsyncSession = Depends(get_db),
):
    """
    导出统计数据

    权限：组长及以上可导出
    """
    try:
        # 根据导出类型获取数据
        export_data = {}
        filename_prefix = ""

        if export_type == "overview":
            # 导出概览数据
            overview_response = await get_statistics_overview(
                date_from, date_to, current_user, db
            )
            export_data = overview_response["data"]
            filename_prefix = "overview"

        elif export_type == "efficiency":
            # 导出效率分析数据
            efficiency_response = await get_efficiency_analysis(
                date_from, date_to, member_id, "member", current_user, db
            )
            export_data = efficiency_response["data"]
            filename_prefix = "efficiency"

        elif export_type == "monthly":
            # 导出月度报表
            if not date_from:
                date_from = datetime.now().replace(day=1)
            monthly_response = await get_monthly_report(
                date_from.year, date_from.month, member_id, current_user, db
            )
            export_data = monthly_response["data"]
            filename_prefix = "monthly"

        # 生成文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{filename_prefix}_statistics_{timestamp}.{format}"

        # 这里应该实现实际的文件生成逻辑
        # 为了简化，返回模拟的导出结果
        export_result = {
            "download_url": f"/api/v1/files/download/{filename}",
            "filename": filename,
            "export_type": export_type,
            "format": format,
            "data_summary": {
                "total_records": len(str(export_data)),  # 简化的记录数统计
                "export_time": datetime.now().isoformat(),
            },
            "expires_at": (datetime.now() + timedelta(hours=24)).isoformat(),
        }

        logger.info(
            f"Statistics data exported by {current_user.student_id}: {export_type} in {format} format"
        )

        return create_response(
            data=export_result, message=f"{export_type}统计数据导出成功"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Export statistics data error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="导出统计数据失败"
        )


# ============= 私有辅助方法 =============


def _calculate_efficiency_score(
    avg_work_minutes: float,
    avg_completion_hours: float,
    avg_rating: float,
    total_tasks: int,
) -> float:
    """
    计算效率评分

    评分逻辑：
    - 工时效率：标准工时与实际工时的比值
    - 完成速度：完成时间的倒数
    - 质量评分：平均评分
    - 工作量：任务数量
    """
    try:
        # 标准工时（在线40分钟，离线100分钟，这里取平均70分钟）
        standard_minutes = 70
        work_efficiency = min(
            standard_minutes / max(avg_work_minutes, 1), 2.0
        )  # 最高2倍效率

        # 完成速度评分（24小时内完成为满分，超过时间递减）
        speed_score = min(24 / max(avg_completion_hours, 1), 2.0)

        # 质量评分（5分制转为2分制）
        quality_score = avg_rating / 2.5 if avg_rating > 0 else 1.0

        # 工作量评分（对数增长，鼓励多做任务但不过分依赖数量）
        import math

        volume_score = math.log(total_tasks + 1) / 5.0  # 归一化到合理范围

        # 综合评分（加权平均）
        efficiency_score = (
            work_efficiency * 0.3  # 工时效率 30%
            + speed_score * 0.3  # 完成速度 30%
            + quality_score * 0.3  # 质量评分 30%
            + volume_score * 0.1  # 工作量 10%
        )

        return round(efficiency_score, 2)

    except Exception as e:
        logger.warning(f"Error calculating efficiency score: {str(e)}")
        return 1.0  # 默认评分


# 图表数据端点
@router.get("/charts", response_model=Dict[str, Any])
async def get_chart_data(
    type: str = Query(..., description="图表类型"),
    metric: str = Query(..., description="指标类型"),
    current_user: Member = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取图表数据"""
    try:
        # 模拟图表数据
        chart_data = {
            "labels": ["维修任务", "监控任务", "协助任务"],
            "datasets": [
                {
                    "label": "任务数量",
                    "data": [45, 25, 30],
                    "backgroundColor": ["#409EFF", "#67C23A", "#E6A23C"],
                }
            ],
        }

        return create_response(data=chart_data, message="获取图表数据成功")
    except Exception as e:
        logger.error(f"获取图表数据失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="获取图表数据失败"
        )


# 排行榜端点
@router.get("/rankings", response_model=Dict[str, Any])
async def get_rankings(
    type: str = Query(..., description="排行榜类型"),
    metric: str = Query(..., description="指标类型"),
    period_start: str = Query(..., description="开始时间"),
    period_end: str = Query(..., description="结束时间"),
    limit: int = Query(10, description="返回数量"),
    current_user: Member = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取排行榜数据"""
    try:
        # 模拟排行榜数据
        rankings = [
            {"member_id": 1, "member_name": "张三", "score": 95.5, "rank": 1},
            {"member_id": 2, "member_name": "李四", "score": 92.3, "rank": 2},
            {"member_id": 3, "member_name": "王五", "score": 88.7, "rank": 3},
        ]

        return create_response(data=rankings[:limit], message="获取排行榜数据成功")
    except Exception as e:
        logger.error(f"获取排行榜数据失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取排行榜数据失败",
        )


# 考勤统计端点（兼容旧版本）
@router.get("/attendance", response_model=Dict[str, Any])
async def get_attendance_statistics(
    start_date: str = Query(..., description="开始日期"),
    end_date: str = Query(..., description="结束日期"),
    current_user: Member = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取考勤统计数据（基于工时）"""
    try:
        from app.models.task import AssistanceTask, MonitoringTask, RepairTask
        from sqlalchemy import func, select

        # 解析日期范围
        start_date_obj = datetime.strptime(start_date, "%Y-%m-%d").date()
        end_date_obj = datetime.strptime(end_date, "%Y-%m-%d").date()

        # 统计工时数据作为考勤数据
        repair_query = select(
            func.sum(RepairTask.work_minutes).label("total_minutes"),
            func.count(func.distinct(RepairTask.member_id)).label("active_members"),
        ).where(
            RepairTask.completion_time >= start_date_obj,
            RepairTask.completion_time <= end_date_obj,
            RepairTask.status == "COMPLETED",
        )

        repair_result = await db.execute(repair_query)
        repair_stats = repair_result.fetchone()

        attendance_stats = {
            "total_members": 10,  # 可以从成员表查询
            "active_members": repair_stats.active_members or 0,
            "total_work_hours": round((repair_stats.total_minutes or 0) / 60, 2),
            "average_work_hours": 0,
            "departments": [],  # 暂时为空，因为我们弱化部门概念
        }

        if attendance_stats["active_members"] > 0:
            attendance_stats["average_work_hours"] = round(
                attendance_stats["total_work_hours"]
                / attendance_stats["active_members"],
                2,
            )

        return create_response(data=attendance_stats, message="获取考勤统计成功")
    except Exception as e:
        logger.error(f"获取考勤统计失败: {str(e)}")
        # 返回默认数据
        return create_response(
            data={
                "total_members": 0,
                "active_members": 0,
                "total_work_hours": 0.0,
                "average_work_hours": 0.0,
                "departments": [],
            },
            message="获取考勤统计成功（使用默认数据）",
        )


# ============= 新增工时统计分析 =============


@router.get("/work-hours/overview", response_model=Dict[str, Any])
async def get_work_hours_overview(
    year: int = Query(..., description="年份"),
    month: int = Query(..., ge=1, le=12, description="月份"),
    member_id: Optional[int] = Query(
        None, description="指定成员（为空则查看团队概览）"
    ),
    current_user: Member = Depends(get_current_active_group_leader),
    db: AsyncSession = Depends(get_db),
):
    """
    获取工时统计概览（基于新的工时计算逻辑）

    权限：组长及以上可查看团队概览，所有人可查看个人概览
    """
    try:
        from app.services.work_hours_service import WorkHoursCalculationService

        # 权限检查
        if (
            member_id
            and member_id != current_user.id
            and not current_user.can_manage_group
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权限查看其他人的工时统计",
            )

        work_hours_service = WorkHoursCalculationService(db)

        if member_id:
            # 个人工时概览
            work_hours_data = await work_hours_service.calculate_monthly_work_hours(
                member_id, year, month
            )

            # 获取成员信息
            member_query = select(Member).where(Member.id == member_id)
            member_result = await db.execute(member_query)
            member = member_result.scalar_one_or_none()

            if not member:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail="成员不存在"
                )

            overview_data = {
                "type": "personal",
                "member": {
                    "id": member.id,
                    "name": member.name,
                    "student_id": member.student_id,
                },
                "period": {"year": year, "month": month},
                "work_hours": work_hours_data,
            }
        else:
            # 团队工时概览
            if not current_user.can_manage_group:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="无权限查看团队工时概览",
                )

            # 批量更新所有成员的月度汇总
            update_result = await work_hours_service.batch_update_monthly_summaries(
                year, month
            )

            # 获取所有活跃成员的工时数据
            members_query = select(Member).where(Member.is_active == True)
            members_result = await db.execute(members_query)
            members = members_result.scalars().all()

            team_summary = {
                "total_members": len(members),
                "updated_members": update_result["updated"],
                "total_hours": 0.0,
                "total_repair_hours": 0.0,
                "total_monitoring_hours": 0.0,
                "total_assistance_hours": 0.0,
                "full_attendance_count": 0,
                "member_details": [],
            }

            for member in members:
                try:
                    member_data = await work_hours_service.calculate_monthly_work_hours(
                        member.id, year, month
                    )

                    team_summary["total_hours"] += member_data["total_hours"]
                    team_summary["total_repair_hours"] += member_data[
                        "repair_task_hours"
                    ]
                    team_summary["total_monitoring_hours"] += member_data[
                        "monitoring_hours"
                    ]
                    team_summary["total_assistance_hours"] += member_data[
                        "assistance_hours"
                    ]

                    if member_data["is_full_attendance"]:
                        team_summary["full_attendance_count"] += 1

                    team_summary["member_details"].append(
                        {
                            "member_id": member.id,
                            "member_name": member.name,
                            "total_hours": member_data["total_hours"],
                            "is_full_attendance": member_data["is_full_attendance"],
                            "task_counts": {
                                "repair": member_data["repair_task_count"],
                                "monitoring": member_data["monitoring_task_count"],
                                "assistance": member_data["assistance_task_count"],
                            },
                        }
                    )
                except Exception as e:
                    logger.warning(
                        f"Failed to get work hours for member {member.id}: {str(e)}"
                    )

            # 排序（按总工时降序）
            team_summary["member_details"].sort(
                key=lambda x: x["total_hours"], reverse=True
            )

            overview_data = {
                "type": "team",
                "period": {"year": year, "month": month},
                "team_summary": team_summary,
            }

        logger.info(f"Work hours overview retrieved by {current_user.student_id}")

        return create_response(data=overview_data, message="工时统计概览获取成功")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get work hours overview error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取工时统计概览失败",
        )


@router.get("/work-hours/analysis", response_model=Dict[str, Any])
async def get_work_hours_analysis(
    year: int = Query(..., description="年份"),
    month: int = Query(..., ge=1, le=12, description="月份"),
    analysis_type: str = Query(
        "breakdown",
        regex="^(breakdown|penalty|bonus|comparison)$",
        description="分析类型",
    ),
    current_user: Member = Depends(get_current_active_group_leader),
    db: AsyncSession = Depends(get_db),
):
    """
    获取工时详细分析

    分析类型：
    - breakdown: 工时构成分析
    - penalty: 惩罚分析
    - bonus: 奖励分析
    - comparison: 成员对比分析

    权限：组长及以上可查看
    """
    try:
        from app.models.attendance import MonthlyAttendanceSummary
        from app.services.work_hours_service import WorkHoursCalculationService

        work_hours_service = WorkHoursCalculationService(db)
        analysis_data = {
            "analysis_type": analysis_type,
            "period": {"year": year, "month": month},
        }

        # 获取该月所有成员的工时汇总
        summary_query = (
            select(MonthlyAttendanceSummary)
            .options(joinedload(MonthlyAttendanceSummary.member))
            .where(
                and_(
                    MonthlyAttendanceSummary.year == year,
                    MonthlyAttendanceSummary.month == month,
                )
            )
        )

        summary_result = await db.execute(summary_query)
        summaries = summary_result.scalars().all()

        if analysis_type == "breakdown":
            # 工时构成分析
            breakdown_data = {
                "total_repair_hours": 0.0,
                "total_monitoring_hours": 0.0,
                "total_assistance_hours": 0.0,
                "total_penalty_hours": 0.0,
                "total_bonus_hours": 0.0,
                "member_breakdown": [],
            }

            for summary in summaries:
                breakdown_data["total_repair_hours"] += summary.repair_task_hours
                breakdown_data["total_monitoring_hours"] += summary.monitoring_hours
                breakdown_data["total_assistance_hours"] += summary.assistance_hours
                breakdown_data["total_penalty_hours"] += summary.penalty_hours

                # 计算奖励工时（爆单+好评）
                bonus_hours = summary.rush_task_hours + summary.positive_review_hours
                breakdown_data["total_bonus_hours"] += bonus_hours

                breakdown_data["member_breakdown"].append(
                    {
                        "member_id": summary.member_id,
                        "member_name": (
                            summary.member.name if summary.member else "未知"
                        ),
                        "repair_hours": summary.repair_task_hours,
                        "monitoring_hours": summary.monitoring_hours,
                        "assistance_hours": summary.assistance_hours,
                        "penalty_hours": summary.penalty_hours,
                        "bonus_hours": bonus_hours,
                        "total_hours": summary.total_hours,
                    }
                )

            analysis_data["breakdown"] = breakdown_data

        elif analysis_type == "penalty":
            # 惩罚分析
            penalty_data = {
                "total_penalty_hours": 0.0,
                "late_response_penalty": 0.0,
                "late_completion_penalty": 0.0,
                "negative_review_penalty": 0.0,
                "penalty_details": [],
            }

            for summary in summaries:
                penalty_data["total_penalty_hours"] += summary.penalty_hours
                penalty_data[
                    "late_response_penalty"
                ] += summary.late_response_penalty_hours
                penalty_data[
                    "late_completion_penalty"
                ] += summary.late_completion_penalty_hours
                penalty_data[
                    "negative_review_penalty"
                ] += summary.negative_review_penalty_hours

                if summary.penalty_hours > 0:
                    penalty_data["penalty_details"].append(
                        {
                            "member_id": summary.member_id,
                            "member_name": (
                                summary.member.name if summary.member else "未知"
                            ),
                            "total_penalty": summary.penalty_hours,
                            "late_response": summary.late_response_penalty_hours,
                            "late_completion": summary.late_completion_penalty_hours,
                            "negative_review": summary.negative_review_penalty_hours,
                        }
                    )

            # 按惩罚时间排序
            penalty_data["penalty_details"].sort(
                key=lambda x: x["total_penalty"], reverse=True
            )
            analysis_data["penalties"] = penalty_data

        elif analysis_type == "bonus":
            # 奖励分析
            bonus_data = {
                "total_rush_hours": 0.0,
                "total_positive_review_hours": 0.0,
                "bonus_details": [],
            }

            for summary in summaries:
                bonus_data["total_rush_hours"] += summary.rush_task_hours
                bonus_data[
                    "total_positive_review_hours"
                ] += summary.positive_review_hours

                total_bonus = summary.rush_task_hours + summary.positive_review_hours
                if total_bonus > 0:
                    bonus_data["bonus_details"].append(
                        {
                            "member_id": summary.member_id,
                            "member_name": (
                                summary.member.name if summary.member else "未知"
                            ),
                            "rush_hours": summary.rush_task_hours,
                            "positive_review_hours": summary.positive_review_hours,
                            "total_bonus": total_bonus,
                        }
                    )

            # 按奖励时间排序
            bonus_data["bonus_details"].sort(
                key=lambda x: x["total_bonus"], reverse=True
            )
            analysis_data["bonuses"] = bonus_data

        elif analysis_type == "comparison":
            # 成员对比分析
            comparison_data = {
                "member_comparison": [],
                "averages": {
                    "avg_total_hours": 0.0,
                    "avg_repair_hours": 0.0,
                    "avg_monitoring_hours": 0.0,
                    "avg_assistance_hours": 0.0,
                },
            }

            if summaries:
                total_members = len(summaries)
                sum_total_hours = sum(s.total_hours for s in summaries)
                sum_repair_hours = sum(s.repair_task_hours for s in summaries)
                sum_monitoring_hours = sum(s.monitoring_hours for s in summaries)
                sum_assistance_hours = sum(s.assistance_hours for s in summaries)

                comparison_data["averages"] = {
                    "avg_total_hours": round(sum_total_hours / total_members, 2),
                    "avg_repair_hours": round(sum_repair_hours / total_members, 2),
                    "avg_monitoring_hours": round(
                        sum_monitoring_hours / total_members, 2
                    ),
                    "avg_assistance_hours": round(
                        sum_assistance_hours / total_members, 2
                    ),
                }

                for summary in summaries:
                    comparison_data["member_comparison"].append(
                        {
                            "member_id": summary.member_id,
                            "member_name": (
                                summary.member.name if summary.member else "未知"
                            ),
                            "total_hours": summary.total_hours,
                            "vs_avg_total": round(
                                summary.total_hours
                                - comparison_data["averages"]["avg_total_hours"],
                                2,
                            ),
                            "repair_hours": summary.repair_task_hours,
                            "vs_avg_repair": round(
                                summary.repair_task_hours
                                - comparison_data["averages"]["avg_repair_hours"],
                                2,
                            ),
                            "is_full_attendance": summary.total_hours >= 30.0,
                            "efficiency_rank": 0,  # 稍后计算排名
                        }
                    )

                # 计算效率排名
                comparison_data["member_comparison"].sort(
                    key=lambda x: x["total_hours"], reverse=True
                )
                for i, member in enumerate(comparison_data["member_comparison"]):
                    member["efficiency_rank"] = i + 1

            analysis_data["comparison"] = comparison_data

        logger.info(
            f"Work hours analysis ({analysis_type}) retrieved by {current_user.student_id}"
        )

        return create_response(
            data=analysis_data, message=f"工时{analysis_type}分析获取成功"
        )

    except Exception as e:
        logger.error(f"Get work hours analysis error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="获取工时分析失败"
        )


@router.post("/work-hours/batch-update", response_model=Dict[str, Any])
async def batch_update_work_hours_summaries(
    year: int = Query(..., description="年份"),
    month: int = Query(..., ge=1, le=12, description="月份"),
    member_ids: Optional[List[int]] = Query(
        None, description="指定成员ID列表（为空则更新所有成员）"
    ),
    current_user: Member = Depends(get_current_active_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    批量更新工时汇总数据

    权限：仅管理员可执行批量更新
    """
    try:
        from app.services.work_hours_service import WorkHoursCalculationService

        work_hours_service = WorkHoursCalculationService(db)

        # 执行批量更新
        result = await work_hours_service.batch_update_monthly_summaries(
            year, month, member_ids
        )

        logger.info(
            f"Batch work hours summaries updated by {current_user.student_id}: {result}"
        )

        return create_response(
            data=result,
            message=f"批量更新完成，成功更新 {result['updated']} 个成员的工时汇总",
        )

    except Exception as e:
        logger.error(f"Batch update work hours summaries error: {str(e)}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="批量更新工时汇总失败",
        )


@router.get("/work-hours/trend", response_model=Dict[str, Any])
async def get_work_hours_trend(
    member_id: Optional[int] = Query(
        None, description="指定成员（为空则查看团队趋势）"
    ),
    months: int = Query(6, ge=1, le=12, description="查看最近几个月的趋势"),
    current_user: Member = Depends(get_current_active_group_leader),
    db: AsyncSession = Depends(get_db),
):
    """
    获取工时趋势分析

    权限：组长及以上可查看团队趋势，所有人可查看个人趋势
    """
    try:
        from app.models.attendance import MonthlyAttendanceSummary

        # 权限检查
        if (
            member_id
            and member_id != current_user.id
            and not current_user.can_manage_group
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权限查看其他人的工时趋势",
            )

        # 计算查询的月份范围
        current_date = datetime.now()
        trend_months = []
        for i in range(months):
            target_date = current_date - timedelta(days=i * 30)  # 近似月份计算
            trend_months.append(
                {
                    "year": target_date.year,
                    "month": target_date.month,
                    "month_key": f"{target_date.year}-{target_date.month:02d}",
                }
            )

        trend_months.reverse()  # 按时间正序

        if member_id:
            # 个人工时趋势
            query = select(MonthlyAttendanceSummary).where(
                MonthlyAttendanceSummary.member_id == member_id
            )

            # 获取成员信息
            member_query = select(Member).where(Member.id == member_id)
            member_result = await db.execute(member_query)
            member = member_result.scalar_one_or_none()

            if not member:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail="成员不存在"
                )

            # 构建个人趋势数据
            trend_data = {
                "type": "personal",
                "member": {
                    "id": member.id,
                    "name": member.name,
                    "student_id": member.student_id,
                },
                "trend_series": [],
            }

        else:
            # 团队工时趋势
            query = select(MonthlyAttendanceSummary).options(
                joinedload(MonthlyAttendanceSummary.member)
            )

            trend_data = {"type": "team", "trend_series": []}

        # 添加月份筛选条件
        month_conditions = []
        for month_info in trend_months:
            month_conditions.append(
                and_(
                    MonthlyAttendanceSummary.year == month_info["year"],
                    MonthlyAttendanceSummary.month == month_info["month"],
                )
            )

        if month_conditions:
            query = query.where(or_(*month_conditions))

        result = await db.execute(query)
        summaries = result.scalars().all()

        # 按月份组织数据
        monthly_data = {}
        for summary in summaries:
            month_key = f"{summary.year}-{summary.month:02d}"
            if month_key not in monthly_data:
                monthly_data[month_key] = []
            monthly_data[month_key].append(summary)

        # 构建趋势序列
        for month_info in trend_months:
            month_key = month_info["month_key"]
            month_summaries = monthly_data.get(month_key, [])

            if member_id:
                # 个人趋势数据点
                personal_summary = next(
                    (s for s in month_summaries if s.member_id == member_id), None
                )
                if personal_summary:
                    trend_data["trend_series"].append(
                        {
                            "period": month_key,
                            "total_hours": personal_summary.total_hours,
                            "repair_hours": personal_summary.repair_task_hours,
                            "monitoring_hours": personal_summary.monitoring_hours,
                            "assistance_hours": personal_summary.assistance_hours,
                            "penalty_hours": personal_summary.penalty_hours,
                            "is_full_attendance": personal_summary.total_hours >= 30.0,
                        }
                    )
                else:
                    # 无数据月份
                    trend_data["trend_series"].append(
                        {
                            "period": month_key,
                            "total_hours": 0.0,
                            "repair_hours": 0.0,
                            "monitoring_hours": 0.0,
                            "assistance_hours": 0.0,
                            "penalty_hours": 0.0,
                            "is_full_attendance": False,
                        }
                    )
            else:
                # 团队趋势数据点
                team_total = sum(s.total_hours for s in month_summaries)
                team_repair = sum(s.repair_task_hours for s in month_summaries)
                team_monitoring = sum(s.monitoring_hours for s in month_summaries)
                team_assistance = sum(s.assistance_hours for s in month_summaries)
                team_penalty = sum(s.penalty_hours for s in month_summaries)
                full_attendance_count = sum(
                    1 for s in month_summaries if s.total_hours >= 30.0
                )

                trend_data["trend_series"].append(
                    {
                        "period": month_key,
                        "total_hours": team_total,
                        "repair_hours": team_repair,
                        "monitoring_hours": team_monitoring,
                        "assistance_hours": team_assistance,
                        "penalty_hours": team_penalty,
                        "active_members": len(month_summaries),
                        "full_attendance_count": full_attendance_count,
                        "avg_hours_per_member": (
                            round(team_total / len(month_summaries), 2)
                            if month_summaries
                            else 0
                        ),
                    }
                )

        logger.info(f"Work hours trend retrieved by {current_user.student_id}")

        return create_response(data=trend_data, message="工时趋势分析获取成功")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get work hours trend error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取工时趋势分析失败",
        )


# 健康检查
@router.get("/health", response_model=Dict[str, Any])
async def statistics_health_check():
    """统计分析服务健康检查"""
    return create_response(
        data={"service": "statistics", "status": "healthy"},
        message="统计分析服务运行正常",
    )
