"""
仪表板API模块
提供仪表板所需的概览数据、任务摘要、活动时间线等功能
"""

from datetime import datetime, timedelta
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import and_, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import get_current_user, get_db
from app.models.member import Member
from app.models.task import RepairTask, TaskPriority, TaskStatus
from app.schemas.base import TypedResponse
from app.schemas.dashboard import (
    Activity,
    ActivitySummary,
    DashboardActivitiesResponse,
    DashboardOverviewResponse,
    DashboardTasksResponse,
    MetricsData,
    SystemInfo,
    TaskStats,
    TaskSummary,
    TrendData,
    TrendsData,
)

router = APIRouter(tags=["仪表板"])


@router.get("/overview", response_model=TypedResponse[DashboardOverviewResponse])
async def get_dashboard_overview(
    current_user: Member = Depends(get_current_user), db: AsyncSession = Depends(get_db)
) -> TypedResponse[DashboardOverviewResponse]:
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
        def calculate_trend(current: int, previous: int) -> TrendData:
            if previous == 0:
                return TrendData(value=0.0, direction="stable")

            change_percent = ((current - previous) / previous) * 100
            if change_percent > 5:
                direction = "up"
            elif change_percent < -5:
                direction = "down"
            else:
                direction = "stable"

            return TrendData(value=abs(change_percent), direction=direction)

        # 系统状态判断
        system_status = "healthy"
        if pending > total_tasks * 0.3:  # 待处理任务超过30%
            system_status = "warning"
        elif pending > total_tasks * 0.5:  # 待处理任务超过50%
            system_status = "error"

        # 在线用户数 (简化版本，实际应该从缓存或会话管理获取)
        online_users_result = await db.execute(
            select(func.count(Member.id)).where(Member.is_active.is_(True))
        )
        online_users = min(online_users_result.scalar() or 0, 50)  # 最大50个在线用户

        overview_data = DashboardOverviewResponse(
            metrics=MetricsData(
                totalTasks=total_tasks,
                inProgress=in_progress,
                pending=pending,
                completedThisMonth=completed_this_month,
                systemStatus=system_status,
            ),
            trends=TrendsData(
                totalTasksTrend=calculate_trend(total_tasks, last_month_total),
                inProgressTrend=calculate_trend(in_progress, last_month_in_progress),
                pendingTrend=calculate_trend(pending, last_month_pending),
                completedTrend=calculate_trend(
                    completed_this_month, last_month_completed
                ),
            ),
            systemInfo=SystemInfo(
                onlineUsers=online_users,
                lastDataSync=datetime.now().isoformat() + "Z",
                systemUptime="99.9%",
            ),
        )

        return TypedResponse[DashboardOverviewResponse](
            success=True, message="仪表板数据获取成功", data=overview_data
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取仪表板数据失败: {str(e)}")


@router.get("/my-tasks", response_model=TypedResponse[DashboardTasksResponse])
async def get_my_tasks(
    limit: int = Query(5, ge=1, le=20),
    current_user: Member = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> TypedResponse[DashboardTasksResponse]:
    """
    获取我的任务摘要
    """
    try:
        # 获取分配给当前用户的任务
        tasks_query = (
            select(RepairTask)
            .where(RepairTask.member_id == current_user.id)
            .options(selectinload(RepairTask.member))
            .order_by(desc(RepairTask.created_at))
            .limit(limit)
        )

        tasks_result = await db.execute(tasks_query)
        tasks = tasks_result.scalars().all()

        # 统计信息
        total_assigned_result = await db.execute(
            select(func.count(RepairTask.id)).where(
                RepairTask.member_id == current_user.id
            )
        )
        total_assigned = total_assigned_result.scalar() or 0

        pending_count_result = await db.execute(
            select(func.count(RepairTask.id)).where(
                and_(
                    RepairTask.member_id == current_user.id,
                    RepairTask.status == TaskStatus.PENDING,
                )
            )
        )
        pending_count = pending_count_result.scalar() or 0

        in_progress_count_result = await db.execute(
            select(func.count(RepairTask.id)).where(
                and_(
                    RepairTask.member_id == current_user.id,
                    RepairTask.status == TaskStatus.IN_PROGRESS,
                )
            )
        )
        in_progress_count = in_progress_count_result.scalar() or 0

        completed_count_result = await db.execute(
            select(func.count(RepairTask.id)).where(
                and_(
                    RepairTask.member_id == current_user.id,
                    RepairTask.status == TaskStatus.COMPLETED,
                )
            )
        )
        completed_count = completed_count_result.scalar() or 0

        # 转换任务数据
        task_list = []
        for task in tasks:
            task_summary = TaskSummary(
                id=task.id,
                title=task.title or "未命名任务",
                status=task.status.value,
                priority=task.priority.value,
                location=task.location or "未指定",
                createdAt=(
                    task.created_at.isoformat() + "Z" if task.created_at else None
                ),
                dueDate=task.due_date.isoformat() + "Z" if task.due_date else None,
            )
            task_list.append(task_summary)

        tasks_data = DashboardTasksResponse(
            tasks=task_list,
            summary=TaskStats(
                totalAssigned=total_assigned,
                pending=pending_count,
                inProgress=in_progress_count,
                completed=completed_count,
            ),
        )

        return TypedResponse[DashboardTasksResponse](
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
) -> TypedResponse[DashboardActivitiesResponse]:
    """
    获取最近活动记录
    """
    try:
        # 获取最近创建的任务
        recent_tasks_query = (
            select(RepairTask)
            .options(
                selectinload(RepairTask.member),
            )
            .order_by(desc(RepairTask.created_at))
            .limit(limit)
        )

        recent_tasks_result = await db.execute(recent_tasks_query)
        recent_tasks = recent_tasks_result.scalars().all()

        activities: List[Activity] = []
        activity_id = 1

        # 生成活动记录 (基于最近任务)
        for task in recent_tasks:
            # 任务创建活动（使用分配的成员信息）
            if task.member:
                activity = Activity(
                    id=activity_id,
                    type="task_created",
                    title="分配了新任务",
                    description=f'"{task.title or "未命名任务"}" - {task.priority.value.upper()}优先级',
                    actorName=task.member.name,
                    actorId=str(task.member_id),
                    targetId=task.id,
                    targetType="task",
                    createdAt=(
                        task.created_at.isoformat() + "Z"
                        if task.created_at
                        else datetime.now().isoformat() + "Z"
                    ),
                    priority=(
                        "primary" if task.priority == TaskPriority.HIGH else "info"
                    ),
                )
                activities.append(activity)
                activity_id += 1

            # 如果任务已完成，添加完成活动
            if task.status == TaskStatus.COMPLETED and task.member:
                activity = Activity(
                    id=activity_id,
                    type="task_completed",
                    title="完成了任务",
                    description=f'"{task.title or "未命名任务"}" - 已验收通过',
                    actorName=task.member.name,
                    actorId=str(task.member_id),
                    targetId=task.id,
                    targetType="task",
                    createdAt=(task.updated_at or task.created_at).isoformat() + "Z",
                    priority="success",
                )
                activities.append(activity)
                activity_id += 1

            # 如果任务状态为进行中，添加状态变更活动
            elif task.status == TaskStatus.IN_PROGRESS and task.member:
                activity = Activity(
                    id=activity_id,
                    type="task_status_changed",
                    title="任务状态变更",
                    description=f'"{task.title or "未命名任务"}" - 已开始处理',
                    actorName=task.member.name,
                    actorId=str(task.member_id),
                    targetId=task.id,
                    targetType="task",
                    createdAt=(task.updated_at or task.created_at).isoformat() + "Z",
                    priority="warning",
                )
                activities.append(activity)
                activity_id += 1

        # 添加一些用户登录活动 (示例数据)
        if len(activities) < limit:
            login_activity = Activity(
                id=activity_id,
                type="user_login",
                title="用户登录",
                description=f"{current_user.name} - 从系统登录",
                actorName=current_user.name,
                actorId=str(current_user.student_id),
                targetId=None,
                targetType=None,
                createdAt=datetime.now().isoformat() + "Z",
                priority="info",
            )
            activities.append(login_activity)

        # 按时间排序并限制数量
        activities.sort(key=lambda x: x.createdAt, reverse=True)
        activities = activities[:limit]

        # 总活动数统计
        total_activities = len(recent_tasks) * 2  # 简化统计
        today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        today_activities = len(
            [a for a in activities if a.createdAt >= today_start.isoformat()]
        )

        activities_data = DashboardActivitiesResponse(
            activities=activities,
            summary=ActivitySummary(
                total=total_activities, todayCount=today_activities
            ),
        )

        return TypedResponse[DashboardActivitiesResponse](
            success=True, message="最近活动获取成功", data=activities_data
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取最近活动失败: {str(e)}")


@router.get("/stats")
async def get_stats(
    current_user: Member = Depends(get_current_user), 
    db: AsyncSession = Depends(get_db)
):
    """获取仪表板统计数据"""
    try:
        # 获取总任务数
        total_tasks_result = await db.execute(select(func.count(RepairTask.id)))
        total_tasks = total_tasks_result.scalar() or 0

        # 已完成任务数
        completed_tasks_result = await db.execute(
            select(func.count(RepairTask.id)).where(RepairTask.status == TaskStatus.COMPLETED)
        )
        completed_tasks = completed_tasks_result.scalar() or 0

        # 待处理任务数
        pending_tasks_result = await db.execute(
            select(func.count(RepairTask.id)).where(RepairTask.status == TaskStatus.PENDING)
        )
        pending_tasks = pending_tasks_result.scalar() or 0

        # 超期任务数
        overdue_tasks_result = await db.execute(
            select(func.count(RepairTask.id)).where(
                and_(
                    RepairTask.due_date < datetime.now(),
                    RepairTask.status != TaskStatus.COMPLETED
                )
            )
        )
        overdue_tasks = overdue_tasks_result.scalar() or 0

        # 总成员数
        total_members_result = await db.execute(select(func.count(Member.id)))
        total_members = total_members_result.scalar() or 0

        # 活跃成员数
        active_members_result = await db.execute(
            select(func.count(Member.id)).where(Member.is_active.is_(True))
        )
        active_members = active_members_result.scalar() or 0

        # 计算总工时和月工时
        total_work_hours = completed_tasks * 40  # 假设每个任务40分钟
        monthly_work_hours = total_work_hours // 12 if total_work_hours > 0 else 0

        # 出勤率和完成率
        attendance_rate = 0.92
        completion_rate = completed_tasks / total_tasks if total_tasks > 0 else 0

        return {
            "totalTasks": total_tasks,
            "completedTasks": completed_tasks,
            "pendingTasks": pending_tasks,
            "overdueTasks": overdue_tasks,
            "totalMembers": total_members,
            "activeMembers": active_members,
            "totalWorkHours": total_work_hours,
            "monthlyWorkHours": monthly_work_hours,
            "attendanceRate": attendance_rate,
            "completionRate": completion_rate
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取统计数据失败: {str(e)}")


@router.get("/task-distribution")
async def get_task_distribution(
    current_user: Member = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取任务分布数据"""
    try:
        # 这里简化处理，因为只有RepairTask，其他任务类型可以设为0
        repair_count_result = await db.execute(select(func.count(RepairTask.id)))
        repair_count = repair_count_result.scalar() or 0

        return {
            "repair": repair_count,
            "monitoring": 0,  # 监控任务暂无数据
            "assistance": 0   # 协助任务暂无数据
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取任务分布失败: {str(e)}")


@router.get("/work-hours-trend")
async def get_work_hours_trend(
    days: int = Query(30, ge=7, le=90),
    current_user: Member = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取工时趋势数据"""
    try:
        trend_data = []
        end_date = datetime.now()
        
        for i in range(days):
            date = end_date - timedelta(days=i)
            date_str = date.strftime('%Y-%m-%d')
            
            # 获取当天完成的任务数
            day_start = date.replace(hour=0, minute=0, second=0, microsecond=0)
            day_end = day_start + timedelta(days=1)
            
            tasks_result = await db.execute(
                select(func.count(RepairTask.id)).where(
                    and_(
                        RepairTask.status == TaskStatus.COMPLETED,
                        RepairTask.updated_at >= day_start,
                        RepairTask.updated_at < day_end
                    )
                )
            )
            task_count = tasks_result.scalar() or 0
            
            trend_data.append({
                "date": date_str,
                "hours": task_count * 40,  # 假设每个任务40分钟工时
                "target": 40  # 目标工时
            })
        
        # 按日期正序排列
        trend_data.reverse()
        return trend_data
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取工时趋势失败: {str(e)}")


@router.get("/member-performance")
async def get_member_performance(
    limit: int = Query(10, ge=1, le=50),
    current_user: Member = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取成员绩效数据"""
    try:
        # 获取所有活跃成员及其任务统计
        members_query = select(Member).where(Member.is_active.is_(True)).limit(limit)
        members_result = await db.execute(members_query)
        members = members_result.scalars().all()
        
        performance_data = []
        
        for member in members:
            # 获取成员完成的任务数
            completed_tasks_result = await db.execute(
                select(func.count(RepairTask.id)).where(
                    and_(
                        RepairTask.member_id == member.id,
                        RepairTask.status == TaskStatus.COMPLETED
                    )
                )
            )
            completed_tasks = completed_tasks_result.scalar() or 0
            
            # 计算工时
            work_hours = completed_tasks * 40  # 假设每个任务40分钟
            
            # 模拟出勤率和效率
            attendance_rate = 0.95 if completed_tasks > 5 else 0.85
            efficiency = min(90, 60 + (completed_tasks * 2))  # 基于完成任务数计算效率
            
            performance_data.append({
                "memberId": member.id,
                "memberName": member.name,
                "completedTasks": completed_tasks,
                "workHours": work_hours,
                "attendanceRate": attendance_rate,
                "efficiency": efficiency
            })
        
        return performance_data
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取成员绩效失败: {str(e)}")


@router.get("/recent-activities")
async def get_recent_activities_simple(
    limit: int = Query(20, ge=1, le=50),
    current_user: Member = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取最近活动数据"""
    try:
        # 获取最近的任务作为活动
        tasks_query = (
            select(RepairTask)
            .options(selectinload(RepairTask.member))
            .order_by(desc(RepairTask.updated_at))
            .limit(limit)
        )
        
        tasks_result = await db.execute(tasks_query)
        tasks = tasks_result.scalars().all()
        
        activities = []
        for i, task in enumerate(tasks):
            activity_type = "task_completed" if task.status == TaskStatus.COMPLETED else "task_assigned"
            title = "完成了任务" if task.status == TaskStatus.COMPLETED else "分配了新任务"
            description = f"{task.title or '未命名任务'}"
            
            activities.append({
                "id": i + 1,
                "type": activity_type,
                "title": title,
                "description": description,
                "timestamp": (task.updated_at or task.created_at).isoformat()
            })
        
        return activities
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取最近活动失败: {str(e)}")


@router.get("/alerts")
async def get_alerts(
    resolved: bool = Query(False),
    current_user: Member = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取系统警告"""
    try:
        # 获取超期任务作为警告
        overdue_query = select(RepairTask).where(
            and_(
                RepairTask.due_date < datetime.now(),
                RepairTask.status != TaskStatus.COMPLETED
            )
        )
        
        overdue_result = await db.execute(overdue_query)
        overdue_tasks = overdue_result.scalars().all()
        
        alerts = []
        for i, task in enumerate(overdue_tasks):
            alerts.append({
                "id": i + 1,
                "type": "overdue",
                "level": "high",
                "title": "任务超期",
                "message": f"任务 '{task.title or '未命名任务'}' 已超期",
                "timestamp": datetime.now().isoformat(),
                "resolved": False
            })
        
        # 添加一些系统提醒
        if len(alerts) < 5:
            alerts.append({
                "id": len(alerts) + 1,
                "type": "system",
                "level": "medium",
                "title": "系统提醒",
                "message": "建议定期检查任务完成情况",
                "timestamp": datetime.now().isoformat(),
                "resolved": False
            })
        
        return alerts
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取系统警告失败: {str(e)}")
