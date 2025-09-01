"""
仪表板API模块
提供仪表板所需的概览数据、任务摘要、活动时间线等功能
"""

from datetime import datetime, timedelta
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import and_, desc, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import get_current_user, get_db
from app.models.member import Member
from app.models.task import RepairTask, TaskPriority, TaskStatus
from app.schemas.base import StandardResponse, TypedResponse
from app.schemas.dashboard import (
    DashboardActivitiesResponse,
    DashboardOverviewResponse,
    DashboardTasksResponse,
)

router = APIRouter(tags=["仪表板"])


@router.get("/overview", response_model=TypedResponse[DashboardOverviewResponse])
async def get_dashboard_overview(
    current_user: Member = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    """
    获取仪表板概览数据
    """
    try:
        # 获取基础任务统计
        total_tasks_result = await db.execute(select(func.count(RepairTask.id)))
        total_tasks = total_tasks_result.scalar() or 0

        # 各状态任务统计
        in_progress_result = await db.execute(
            select(func.count(RepairTask.id)).where(
                RepairTask.status == TaskStatus.IN_PROGRESS
            )
        )
        in_progress = in_progress_result.scalar() or 0

        pending_result = await db.execute(
            select(func.count(RepairTask.id)).where(
                RepairTask.status == TaskStatus.PENDING
            )
        )
        pending = pending_result.scalar() or 0

        # 本月完成任务数
        current_month_start = datetime.now().replace(
            day=1, hour=0, minute=0, second=0, microsecond=0
        )
        completed_this_month_result = await db.execute(
            select(func.count(RepairTask.id)).where(
                and_(
                    RepairTask.status == TaskStatus.COMPLETED,
                    RepairTask.updated_at >= current_month_start,
                )
            )
        )
        completed_this_month = completed_this_month_result.scalar() or 0

        # 计算趋势数据 (对比上个月同期)
        last_month_start = (current_month_start - timedelta(days=32)).replace(day=1)
        last_month_end = current_month_start - timedelta(days=1)

        # 上月同期数据
        last_month_total_result = await db.execute(
            select(func.count(RepairTask.id)).where(
                RepairTask.created_at.between(last_month_start, last_month_end)
            )
        )
        last_month_total = last_month_total_result.scalar() or 1  # 避免除零

        last_month_in_progress_result = await db.execute(
            select(func.count(RepairTask.id)).where(
                and_(
                    RepairTask.status == TaskStatus.IN_PROGRESS,
                    RepairTask.created_at.between(last_month_start, last_month_end),
                )
            )
        )
        last_month_in_progress = last_month_in_progress_result.scalar() or 1

        last_month_pending_result = await db.execute(
            select(func.count(RepairTask.id)).where(
                and_(
                    RepairTask.status == TaskStatus.PENDING,
                    RepairTask.created_at.between(last_month_start, last_month_end),
                )
            )
        )
        last_month_pending = last_month_pending_result.scalar() or 1

        last_month_completed_result = await db.execute(
            select(func.count(RepairTask.id)).where(
                and_(
                    RepairTask.status == TaskStatus.COMPLETED,
                    RepairTask.updated_at.between(last_month_start, last_month_end),
                )
            )
        )
        last_month_completed = last_month_completed_result.scalar() or 1

        # 计算趋势百分比和方向
        def calculate_trend(current: int, previous: int):
            if previous == 0:
                return {"value": 0.0, "direction": "stable"}

            change_percent = ((current - previous) / previous) * 100
            if change_percent > 5:
                direction = "up"
            elif change_percent < -5:
                direction = "down"
            else:
                direction = "stable"

            return {"value": abs(change_percent), "direction": direction}

        # 系统状态判断
        system_status = "healthy"
        if pending > total_tasks * 0.3:  # 待处理任务超过30%
            system_status = "warning"
        elif pending > total_tasks * 0.5:  # 待处理任务超过50%
            system_status = "error"

        # 在线用户数 (简化版本，实际应该从缓存或会话管理获取)
        online_users_result = await db.execute(
            select(func.count(Member.id)).where(Member.is_active == True)
        )
        online_users = min(online_users_result.scalar() or 0, 50)  # 最大50个在线用户

        overview_data = DashboardOverviewResponse(
            metrics={
                "totalTasks": total_tasks,
                "inProgress": in_progress,
                "pending": pending,
                "completedThisMonth": completed_this_month,
                "systemStatus": system_status,
            },
            trends={
                "totalTasksTrend": calculate_trend(total_tasks, last_month_total),
                "inProgressTrend": calculate_trend(in_progress, last_month_in_progress),
                "pendingTrend": calculate_trend(pending, last_month_pending),
                "completedTrend": calculate_trend(
                    completed_this_month, last_month_completed
                ),
            },
            systemInfo={
                "onlineUsers": online_users,
                "lastDataSync": datetime.now().isoformat() + "Z",
                "systemUptime": "99.9%",
            },
        )

        return StandardResponse(
            success=True, message="仪表板数据获取成功", data=overview_data
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取仪表板数据失败: {str(e)}")


@router.get("/my-tasks", response_model=TypedResponse[DashboardTasksResponse])
async def get_my_tasks(
    limit: int = Query(5, ge=1, le=20),
    current_user: Member = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    获取我的任务摘要
    """
    try:
        # 获取分配给当前用户的任务
        tasks_query = (
            select(RepairTask)
            .where(RepairTask.assigned_to == current_user.id)
            .options(selectinload(RepairTask.assigned_member))
            .order_by(desc(RepairTask.created_at))
            .limit(limit)
        )

        tasks_result = await db.execute(tasks_query)
        tasks = tasks_result.scalars().all()

        # 统计信息
        total_assigned_result = await db.execute(
            select(func.count(RepairTask.id)).where(
                RepairTask.assigned_to == current_user.id
            )
        )
        total_assigned = total_assigned_result.scalar() or 0

        pending_count_result = await db.execute(
            select(func.count(RepairTask.id)).where(
                and_(
                    RepairTask.assigned_to == current_user.id,
                    RepairTask.status == TaskStatus.PENDING,
                )
            )
        )
        pending_count = pending_count_result.scalar() or 0

        in_progress_count_result = await db.execute(
            select(func.count(RepairTask.id)).where(
                and_(
                    RepairTask.assigned_to == current_user.id,
                    RepairTask.status == TaskStatus.IN_PROGRESS,
                )
            )
        )
        in_progress_count = in_progress_count_result.scalar() or 0

        completed_count_result = await db.execute(
            select(func.count(RepairTask.id)).where(
                and_(
                    RepairTask.assigned_to == current_user.id,
                    RepairTask.status == TaskStatus.COMPLETED,
                )
            )
        )
        completed_count = completed_count_result.scalar() or 0

        # 转换任务数据
        task_list = []
        for task in tasks:
            task_data = {
                "id": task.id,
                "title": task.title,
                "status": task.status.value,
                "priority": task.priority.value,
                "location": task.location or "未指定",
                "createdAt": (
                    task.created_at.isoformat() + "Z" if task.created_at else None
                ),
                "dueDate": task.due_date.isoformat() + "Z" if task.due_date else None,
            }
            task_list.append(task_data)

        tasks_data = DashboardTasksResponse(
            tasks=task_list,
            summary={
                "totalAssigned": total_assigned,
                "pending": pending_count,
                "inProgress": in_progress_count,
                "completed": completed_count,
            },
        )

        return StandardResponse(
            success=True, message="我的任务获取成功", data=tasks_data
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取我的任务失败: {str(e)}")


@router.get(
    "/recent-activities", response_model=TypedResponse[DashboardActivitiesResponse]
)
async def get_recent_activities(
    limit: int = Query(10, ge=1, le=50),
    current_user: Member = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    获取最近活动记录
    """
    try:
        # 获取最近创建的任务
        recent_tasks_query = (
            select(RepairTask)
            .options(
                selectinload(RepairTask.created_by_member),
                selectinload(RepairTask.assigned_member),
            )
            .order_by(desc(RepairTask.created_at))
            .limit(limit)
        )

        recent_tasks_result = await db.execute(recent_tasks_query)
        recent_tasks = recent_tasks_result.scalars().all()

        activities = []
        activity_id = 1

        # 生成活动记录 (基于最近任务)
        for task in recent_tasks:
            # 任务创建活动
            if task.created_by_member:
                activities.append(
                    {
                        "id": activity_id,
                        "type": "task_created",
                        "title": "创建了新任务",
                        "description": f'"{task.title}" - {task.priority.value.upper()}优先级',
                        "actorName": task.created_by_member.name,
                        "actorId": task.created_by,
                        "targetId": task.id,
                        "targetType": "task",
                        "createdAt": (
                            task.created_at.isoformat() + "Z"
                            if task.created_at
                            else None
                        ),
                        "priority": (
                            "primary" if task.priority == TaskPriority.HIGH else "info"
                        ),
                    }
                )
                activity_id += 1

            # 如果任务已完成，添加完成活动
            if task.status == TaskStatus.COMPLETED and task.assigned_member:
                activities.append(
                    {
                        "id": activity_id,
                        "type": "task_completed",
                        "title": "完成了任务",
                        "description": f'"{task.title}" - 已验收通过',
                        "actorName": task.assigned_member.name,
                        "actorId": task.assigned_to,
                        "targetId": task.id,
                        "targetType": "task",
                        "createdAt": (task.updated_at or task.created_at).isoformat()
                        + "Z",
                        "priority": "success",
                    }
                )
                activity_id += 1

            # 如果任务状态为进行中，添加状态变更活动
            elif task.status == TaskStatus.IN_PROGRESS and task.assigned_member:
                activities.append(
                    {
                        "id": activity_id,
                        "type": "task_status_changed",
                        "title": "任务状态变更",
                        "description": f'"{task.title}" - 已开始处理',
                        "actorName": task.assigned_member.name,
                        "actorId": task.assigned_to,
                        "targetId": task.id,
                        "targetType": "task",
                        "createdAt": (task.updated_at or task.created_at).isoformat()
                        + "Z",
                        "priority": "warning",
                    }
                )
                activity_id += 1

        # 添加一些用户登录活动 (示例数据)
        if len(activities) < limit:
            activities.append(
                {
                    "id": activity_id,
                    "type": "user_login",
                    "title": "用户登录",
                    "description": f"{current_user.name} - 从系统登录",
                    "actorName": current_user.name,
                    "actorId": current_user.student_id,
                    "targetId": None,
                    "targetType": None,
                    "createdAt": datetime.now().isoformat() + "Z",
                    "priority": "info",
                }
            )

        # 按时间排序并限制数量
        activities.sort(key=lambda x: x.get("createdAt", ""), reverse=True)
        activities = activities[:limit]

        # 总活动数统计
        total_activities = len(recent_tasks) * 2  # 简化统计
        today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        today_activities = len(
            [a for a in activities if a.get("createdAt", "") >= today_start.isoformat()]
        )

        activities_data = DashboardActivitiesResponse(
            activities=activities,
            summary={"total": total_activities, "todayCount": today_activities},
        )

        return StandardResponse(
            success=True, message="最近活动获取成功", data=activities_data
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取最近活动失败: {str(e)}")
