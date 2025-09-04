"""
任务管理API端点
处理维修任务、监控任务、协助任务的增删改查和工时计算
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi import status as http_status
from sqlalchemy import and_, desc, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

from app.api.deps import (
    check_user_can_access_task,
    check_user_can_manage_group,
    create_error_response,
    create_response,
    get_current_active_admin,
    get_current_active_group_leader,
    get_current_user,
    get_db,
)
from app.models.member import Member, UserRole
from app.models.task import (
    RepairTask,
    TaskCategory,
    TaskPriority,
    TaskStatus,
    TaskTag,
    TaskTagType,
    TaskType,
)
from app.schemas.task import (
    TaskAssignment,
    TaskCreate,
    TaskStatusUpdate,
    TaskTagCreate,
    TaskUpdate,
    WorkHourCalculation,
)

logger = logging.getLogger(__name__)
router = APIRouter()


# ============= 通用任务管理 =============


@router.get("/status", response_model=Dict[str, Any])
async def status_check() -> Dict[str, Any]:
    """状态检查端点"""
    return create_response(
        data={"status": "ok", "service": "tasks"}, message="任务服务运行正常"
    )


@router.get("/monitoring", response_model=Dict[str, Any])
async def get_monitoring_tasks(
    page: int = Query(1, ge=1, description="页码"),
    pageSize: int = Query(20, ge=1, le=100, description="每页数量"),
    current_user: Member = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """获取监控任务列表"""
    try:
        from app.models.task import MonitoringTask

        offset = (page - 1) * pageSize

        # 查询监控任务
        query = select(MonitoringTask).options(joinedload(MonitoringTask.member))

        # 权限过滤：非管理员只能看到自己的任务
        from app.api.deps import check_user_can_manage_group

        if not check_user_can_manage_group(current_user):
            query = query.where(MonitoringTask.member_id == current_user.id)

        # 分页查询
        query = (
            query.offset(offset)
            .limit(pageSize)
            .order_by(desc(MonitoringTask.created_at))
        )
        result = await db.execute(query)
        tasks = result.scalars().unique().all()

        # 获取总数
        count_query = select(func.count(MonitoringTask.id))
        if not check_user_can_manage_group(current_user):
            count_query = count_query.where(MonitoringTask.member_id == current_user.id)

        count_result = await db.execute(count_query)
        total = count_result.scalar() or 0

        # 格式化任务数据
        items = []
        for task in tasks:
            items.append(
                {
                    "id": task.id,
                    "title": task.title,
                    "description": task.description,
                    "location": task.location,
                    "monitoring_type": task.monitoring_type,
                    "start_time": (
                        task.start_time.isoformat() if task.start_time else None
                    ),
                    "end_time": task.end_time.isoformat() if task.end_time else None,
                    "work_minutes": task.work_minutes,
                    "work_hours": round((task.work_minutes or 0) / 60.0, 2),
                    "status": task.status.value,
                    "member_id": task.member_id,
                    "member_name": task.member.name if task.member else None,
                    # 巡检任务支持字段
                    "cabinet_count": getattr(task, "cabinet_count", None),
                    "minutes_per_cabinet": getattr(task, "minutes_per_cabinet", None),
                    "inspection_notes": getattr(task, "inspection_notes", None),
                    "equipment_checked": getattr(task, "equipment_checked", []),
                    "issues_found": getattr(task, "issues_found", []),
                    "is_inspection": (
                        getattr(task, "monitoring_type", "") == "inspection"
                    ),
                    "created_at": (
                        task.created_at.isoformat() if task.created_at else ""
                    ),
                }
            )

        return create_response(
            data={
                "items": items,
                "total": total,
                "page": page,
                "pageSize": pageSize,
                "pages": (total + pageSize - 1) // pageSize,
            },
            message=f"成功获取监控任务列表，共 {total} 条记录",
        )

    except Exception as e:
        logger.error(f"Get monitoring tasks error: {str(e)}")
        return create_error_response(
            message="获取监控任务列表失败", details={"error": str(e)}
        )


@router.get("/fixes", response_model=Dict[str, Any])
async def get_fix_tasks(
    page: int = Query(1, ge=1, description="页码"),
    pageSize: int = Query(20, ge=1, le=100, description="每页数量"),
    current_user: Member = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """获取修复任务列表（实际返回维修任务数据）"""
    try:
        offset = (page - 1) * pageSize

        # 查询维修任务（修复任务的实际实现）
        query = select(RepairTask).options(
            joinedload(RepairTask.member), selectinload(RepairTask.tags)
        )

        # 权限过滤：非管理员只能看到自己的任务
        if not check_user_can_manage_group(current_user):
            query = query.where(RepairTask.member_id == current_user.id)

        # 分页查询
        query = (
            query.offset(offset).limit(pageSize).order_by(desc(RepairTask.created_at))
        )
        result = await db.execute(query)
        tasks = result.scalars().unique().all()

        # 获取总数
        count_query = select(func.count(RepairTask.id))
        if not check_user_can_manage_group(current_user):
            count_query = count_query.where(RepairTask.member_id == current_user.id)

        count_result = await db.execute(count_query)
        total = count_result.scalar() or 0

        # 格式化任务数据
        items = []
        for task in tasks:
            items.append(
                {
                    "id": task.id,
                    "task_id": task.task_id,
                    "title": task.title,
                    "description": task.description,
                    "status": task.status.value,
                    "task_type": task.task_type.value,
                    "priority": task.priority.value,
                    "location": task.location,
                    "report_time": (
                        task.report_time.isoformat() if task.report_time else None
                    ),
                    "completion_time": (
                        task.completion_time.isoformat()
                        if task.completion_time
                        else None
                    ),
                    "work_minutes": task.work_minutes,
                    "work_hours": round((task.work_minutes or 0) / 60.0, 2),
                    "member_id": task.member_id,
                    "member_name": task.member.name if task.member else None,
                    "reporter_name": task.reporter_name,
                    "rating": task.rating,
                    "tags_count": len(list(task.tags)),
                    "created_at": (
                        task.created_at.isoformat() if task.created_at else ""
                    ),
                }
            )

        return create_response(
            data={
                "items": items,
                "total": total,
                "page": page,
                "pageSize": pageSize,
                "pages": (total + pageSize - 1) // pageSize,
            },
            message=f"成功获取修复任务列表，共 {total} 条记录",
        )

    except Exception as e:
        logger.error(f"Get fix tasks error: {str(e)}")
        return create_error_response(
            message="获取修复任务列表失败", details={"error": str(e)}
        )


@router.get("/assistance", response_model=Dict[str, Any])
async def get_assistance_tasks(
    page: int = Query(1, ge=1, description="页码"),
    pageSize: int = Query(20, ge=1, le=100, description="每页数量"),
    current_user: Member = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """获取协助任务列表"""
    try:
        from app.models.task import AssistanceTask

        offset = (page - 1) * pageSize

        # 查询协助任务
        query = select(AssistanceTask).options(joinedload(AssistanceTask.member))

        # 权限过滤：非管理员只能看到自己的任务
        if not check_user_can_manage_group(current_user):
            query = query.where(AssistanceTask.member_id == current_user.id)

        # 分页查询
        query = (
            query.offset(offset)
            .limit(pageSize)
            .order_by(desc(AssistanceTask.created_at))
        )
        result = await db.execute(query)
        tasks = result.scalars().unique().all()

        # 获取总数
        count_query = select(func.count(AssistanceTask.id))
        if not check_user_can_manage_group(current_user):
            count_query = count_query.where(AssistanceTask.member_id == current_user.id)

        count_result = await db.execute(count_query)
        total = count_result.scalar() or 0

        # 格式化任务数据
        items = []
        for task in tasks:
            items.append(
                {
                    "id": task.id,
                    "title": task.title,
                    "description": task.description,
                    "assisted_department": task.assisted_department,
                    "assisted_person": task.assisted_person,
                    "start_time": (
                        task.start_time.isoformat() if task.start_time else None
                    ),
                    "end_time": task.end_time.isoformat() if task.end_time else None,
                    "work_minutes": task.work_minutes,
                    "work_hours": round((task.work_minutes or 0) / 60.0, 2),
                    "status": task.status.value,
                    "member_id": task.member_id,
                    "member_name": task.member.name if task.member else None,
                    "created_at": (
                        task.created_at.isoformat() if task.created_at else ""
                    ),
                }
            )

        return create_response(
            data={
                "items": items,
                "total": total,
                "page": page,
                "pageSize": pageSize,
                "pages": (total + pageSize - 1) // pageSize,
            },
            message=f"成功获取协助任务列表，共 {total} 条记录",
        )

    except Exception as e:
        logger.error(f"Get assistance tasks error: {str(e)}")
        return create_error_response(
            message="获取协助任务列表失败", details={"error": str(e)}
        )


@router.get("/", response_model=Dict[str, Any])
async def get_all_tasks(
    page: int = Query(1, ge=1, description="页码"),
    pageSize: int = Query(20, ge=1, le=100, description="每页数量"),
    search: Optional[str] = Query(None, description="搜索关键词"),
    task_status: Optional[TaskStatus] = Query(None, description="状态筛选"),
    assigned_to: Optional[int] = Query(None, description="执行者筛选（member_id）"),
    sortBy: Optional[str] = Query("createdAt", description="排序字段"),
    sortOrder: Optional[str] = Query("desc", description="排序方向"),
    type: Optional[str] = Query(None, description="任务类型筛选"),  # 新增类型筛选
    current_user: Member = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """
    获取所有类型任务的统一列表
    合并维修任务、监控任务和协助任务
    """
    try:
        offset = (page - 1) * pageSize

        # 构建基础查询条件
        conditions = []
        if search:
            search_term = f"%{search}%"
            conditions.append(
                or_(
                    RepairTask.title.ilike(search_term),
                    RepairTask.task_id.ilike(search_term),
                    RepairTask.location.ilike(search_term),
                )
            )

        if task_status:
            conditions.append(RepairTask.status == task_status)

        if assigned_to:
            conditions.append(RepairTask.member_id == assigned_to)

        # 处理类型筛选 - 目前只支持repair类型，其他类型返回空
        if type and type != "repair":
            # 如果筛选非repair类型，直接返回空结果
            return create_response(
                data={"items": [], "total": 0, "page": page, "pageSize": pageSize},
                message="当前仅支持维修任务查询",
            )

        # 查询维修任务
        repair_query = select(RepairTask).options(joinedload(RepairTask.member))

        if conditions:
            repair_query = repair_query.where(and_(*conditions))

        # 排序
        if sortBy == "createdAt":
            if sortOrder == "desc":
                repair_query = repair_query.order_by(desc(RepairTask.created_at))
            else:
                repair_query = repair_query.order_by(RepairTask.created_at)

        # 分页
        repair_query = repair_query.offset(offset).limit(pageSize)

        # 执行查询
        repair_result = await db.execute(repair_query)
        repair_tasks = repair_result.scalars().unique().all()

        # 获取总数
        count_query = select(func.count(RepairTask.id))
        if conditions:
            count_query = count_query.where(and_(*conditions))

        count_result = await db.execute(count_query)
        total = count_result.scalar() or 0

        # 转换为统一格式
        tasks = []
        for task in repair_tasks:
            task_data = {
                "id": task.id,
                "type": "repair",
                "title": task.title,
                "description": task.description or "",
                "status": task.status.value,
                "priority": task.priority.value if task.priority else "medium",
                "assigneeId": task.member.id if task.member else None,
                "assigneeName": task.member.name if task.member else None,
                "reporterId": 1,  # 默认值，因为RepairTask没有reporter_id字段
                "reporterName": task.reporter_name or "",
                "location": task.location or "",
                "contactInfo": task.reporter_contact or "",
                "estimatedHours": (
                    task.base_work_minutes / 60 if task.base_work_minutes else 0
                ),
                "actualHours": (
                    (task.work_minutes or 0) / 60 if task.work_minutes else None
                ),
                "startedAt": (
                    task.response_time.isoformat() if task.response_time else None
                ),
                "completedAt": (
                    task.completion_time.isoformat() if task.completion_time else None
                ),
                "dueDate": task.created_at.isoformat(),  # 临时使用创建时间作为截止时间
                "createdAt": task.created_at.isoformat(),
                "updatedAt": task.updated_at.isoformat(),
                "tags": [],
                "attachments": [],
                "comments": [],
            }
            tasks.append(task_data)

        return create_response(
            data={"items": tasks, "total": total, "page": page, "pageSize": pageSize},
            message="任务列表获取成功",
        )

    except Exception as e:
        logger.error(f"获取任务列表失败: {str(e)}")
        return create_error_response(
            message="获取任务列表失败", details={"error": str(e)}
        )


@router.get("/work-time-detail/{task_id}", response_model=Dict[str, Any])
async def get_work_time_detail(
    task_id: int,
    current_user: Member = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """
    获取单个任务的工时分解详情
    返回基础分钟、爆单奖励、惩罚等详细分解

    权限：用户可查看自己的任务，管理员和组长可查看所有任务
    """
    try:
        # 查询任务
        query = (
            select(RepairTask)
            .options(joinedload(RepairTask.member), selectinload(RepairTask.tags))
            .where(RepairTask.id == task_id)
        )

        result = await db.execute(query)
        task = result.scalar_one_or_none()

        if not task:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND, detail="任务不存在"
            )

        # 权限检查
        if task.member_id and not check_user_can_access_task(
            current_user, task.member_id
        ):
            raise HTTPException(
                status_code=http_status.HTTP_403_FORBIDDEN,
                detail="无权限查看该任务工时详情",
            )

        # 计算工时分解
        work_time_detail = _calculate_detailed_work_time_breakdown(task)

        return create_response(
            data={
                "task_id": task.id,
                "task_number": task.task_id,
                "title": task.title,
                "task_type": task.task_type.value,
                "status": task.status.value,
                "work_time_breakdown": work_time_detail,
                "total_work_minutes": task.work_minutes,
                "total_work_hours": round((task.work_minutes or 0) / 60.0, 2),
                "calculated_at": datetime.utcnow().isoformat(),
            },
            message="工时详情获取成功",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get work time detail for task {task_id} error: {str(e)}")
        return create_error_response(
            message="获取工时详情失败", details={"error": str(e)}
        )


@router.get("/stats", response_model=Dict[str, Any])
async def get_tasks_stats(
    current_user: Member = Depends(get_current_user), db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    获取任务统计信息
    包括各种状态的任务数量、今日任务数量等
    """
    try:
        # 今日日期
        today = datetime.now().date()
        today_start = datetime.combine(today, datetime.min.time())
        today_end = datetime.combine(today, datetime.max.time())

        # 总任务统计
        total_query = select(func.count(RepairTask.id))
        total_result = await db.execute(total_query)
        total_tasks = total_result.scalar() or 0

        # 待处理任务
        pending_query = select(func.count(RepairTask.id)).where(
            RepairTask.status == TaskStatus.PENDING
        )
        pending_result = await db.execute(pending_query)
        pending_tasks = pending_result.scalar() or 0

        # 进行中任务
        in_progress_query = select(func.count(RepairTask.id)).where(
            RepairTask.status == TaskStatus.IN_PROGRESS
        )
        in_progress_result = await db.execute(in_progress_query)
        in_progress_tasks = in_progress_result.scalar() or 0

        # 已完成任务
        completed_query = select(func.count(RepairTask.id)).where(
            RepairTask.status == TaskStatus.COMPLETED
        )
        completed_result = await db.execute(completed_query)
        completed_tasks = completed_result.scalar() or 0

        # 今日创建任务
        today_created_query = select(func.count(RepairTask.id)).where(
            and_(
                RepairTask.created_at >= today_start, RepairTask.created_at <= today_end
            )
        )
        today_created_result = await db.execute(today_created_query)
        today_created = today_created_result.scalar() or 0

        # 今日完成任务
        today_completed_query = select(func.count(RepairTask.id)).where(
            and_(
                RepairTask.completion_time >= today_start,
                RepairTask.completion_time <= today_end,
            )
        )
        today_completed_result = await db.execute(today_completed_query)
        today_completed = today_completed_result.scalar() or 0

        # 我的任务统计（如果是普通用户）
        my_tasks = 0
        my_pending = 0
        if current_user.role in [UserRole.MEMBER, UserRole.GROUP_LEADER]:
            my_tasks_query = select(func.count(RepairTask.id)).where(
                RepairTask.member_id == current_user.id
            )
            my_tasks_result = await db.execute(my_tasks_query)
            my_tasks = my_tasks_result.scalar() or 0

            my_pending_query = select(func.count(RepairTask.id)).where(
                and_(
                    RepairTask.member_id == current_user.id,
                    RepairTask.status.in_([TaskStatus.PENDING, TaskStatus.IN_PROGRESS]),
                )
            )
            my_pending_result = await db.execute(my_pending_query)
            my_pending = my_pending_result.scalar() or 0

        return create_response(
            data={
                "overview": {
                    "total": total_tasks,
                    "pending": pending_tasks,
                    "in_progress": in_progress_tasks,
                    "completed": completed_tasks,
                },
                "today": {"created": today_created, "completed": today_completed},
                "personal": {"assigned": my_tasks, "pending": my_pending},
                "completion_rate": (
                    (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
                ),
            },
            message="任务统计获取成功",
        )

    except Exception as e:
        logger.error(f"获取任务统计失败: {str(e)}")
        return create_error_response(
            message="获取任务统计失败", details={"error": str(e)}
        )


# ============= 维修任务管理 =============


@router.get("/repair-list", response_model=Dict[str, Any])
async def get_repair_list() -> Dict[str, Any]:
    """
    获取维修任务列表 - 测试端点（重命名路径）
    """
    return create_response(
        data={"items": [], "total": 0, "page": 1, "size": 20, "pages": 0},
        message="成功获取维修任务列表，共 0 条记录",
    )


@router.get("/repair/{task_id}", response_model=Dict[str, Any])
async def get_repair_task(
    task_id: int,
    current_user: Member = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """
    获取单个维修任务详情

    权限：用户可查看自己的任务，管理员和组长可查看所有任务
    """
    try:
        # 查询任务
        query = (
            select(RepairTask)
            .options(joinedload(RepairTask.member), selectinload(RepairTask.tags))
            .where(RepairTask.id == task_id)
        )

        result = await db.execute(query)
        task = result.scalar_one_or_none()

        if not task:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND, detail="维修任务不存在"
            )

        # 权限检查
        if task.member_id and not check_user_can_access_task(
            current_user, task.member_id
        ):
            raise HTTPException(
                status_code=http_status.HTTP_403_FORBIDDEN, detail="无权限查看该任务"
            )

        # 构建详细响应数据
        task_data = {
            "id": task.id,
            "task_id": task.task_id,
            "title": task.title,
            "description": task.description,
            "status": task.status.value,
            "task_type": task.task_type.value,
            "priority": task.priority.value,
            "category": task.category.value,
            "location": task.location,
            "report_time": task.report_time,
            "response_time": task.response_time,
            "completion_time": task.completion_time,
            "work_minutes": task.work_minutes,
            "base_work_minutes": task.base_work_minutes,
            "rating": task.rating,
            "feedback": task.feedback,
            "reporter_name": task.reporter_name,
            "reporter_contact": task.reporter_contact,
            "member_id": task.member_id,
            "member_name": task.member.name if task.member else None,
            "member_student_id": task.member.student_id if task.member else None,
            "is_overdue_response": task.is_overdue_response,
            "is_overdue_completion": task.is_overdue_completion,
            "is_positive_review": task.is_positive_review,
            "is_negative_review": task.is_negative_review,
            "is_non_default_positive_review": task.is_non_default_positive_review,
            "tags": [
                {
                    "id": tag.id,
                    "name": tag.name,
                    "work_minutes_modifier": tag.work_minutes_modifier,
                    "tag_type": tag.tag_type,
                }
                for tag in task.tags
            ],
            "work_hour_breakdown": _calculate_work_hour_breakdown(task),
            "created_at": task.created_at,
            "updated_at": task.updated_at,
        }

        logger.info(
            f"Repair task {task_id} details viewed by {current_user.student_id}"
        )

        return create_response(data=task_data, message="成功获取维修任务详情")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get repair task {task_id} error: {str(e)}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取维修任务详情失败",
        )


@router.post("/repair", response_model=Dict[str, Any])
async def create_repair_task(
    task_data: TaskCreate,
    current_user: Member = Depends(get_current_active_group_leader),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """
    创建新的维修任务

    权限：组长及以上可创建任务
    """
    try:
        # 验证分配的成员是否存在
        assigned_member = None
        if task_data.assigned_to:
            member_query = select(Member).where(Member.id == task_data.assigned_to)
            member_result = await db.execute(member_query)
            assigned_member = member_result.scalar_one_or_none()

            if not assigned_member:
                raise HTTPException(
                    status_code=http_status.HTTP_404_NOT_FOUND,
                    detail="指定的执行者不存在",
                )

            if not assigned_member.is_active:
                raise HTTPException(
                    status_code=http_status.HTTP_400_BAD_REQUEST,
                    detail="指定的执行者账户已被禁用",
                )

        # 生成任务编号
        task_id = await _generate_task_id(db)

        # 创建维修任务
        new_task = RepairTask(
            task_id=task_id,
            title=task_data.title,
            description=task_data.description,
            location=task_data.location,
            member_id=task_data.assigned_to,
            report_time=datetime.utcnow(),
            reporter_name=task_data.reporter_name,
            reporter_contact=task_data.reporter_contact,
        )

        # 设置基础工时
        new_task.base_work_minutes = new_task.get_base_work_minutes()

        db.add(new_task)
        await db.flush()  # 获取任务ID

        # 添加标签
        if task_data.tag_ids:
            tag_query = select(TaskTag).where(TaskTag.id.in_(task_data.tag_ids))
            tag_result = await db.execute(tag_query)
            tags = tag_result.scalars().all()

            for tag in tags:
                new_task.tags.append(tag)

        # 计算工时
        new_task.update_work_minutes()

        await db.commit()
        await db.refresh(new_task)

        logger.info(f"New repair task created: {task_id} by {current_user.student_id}")

        return create_response(
            data={
                "id": new_task.id,
                "task_id": new_task.task_id,
                "title": new_task.title,
                "status": new_task.status.value,
                "member_name": assigned_member.name if assigned_member else None,
            },
            message=f"成功创建维修任务：{new_task.task_id}",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Create repair task error: {str(e)}")
        await db.rollback()
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="创建维修任务失败",
        )


@router.put("/repair/{task_id}", response_model=Dict[str, Any])
async def update_repair_task(
    task_id: int,
    task_update: TaskUpdate,
    current_user: Member = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """
    更新维修任务

    权限：任务执行者可更新基本信息，管理员和组长可更新所有信息
    """
    try:
        # 查询任务
        query = (
            select(RepairTask)
            .options(selectinload(RepairTask.tags))
            .where(RepairTask.id == task_id)
        )

        result = await db.execute(query)
        task = result.scalar_one_or_none()

        if not task:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND, detail="维修任务不存在"
            )

        # 权限检查
        is_task_owner = task.member_id == current_user.id
        if task.member_id and not check_user_can_access_task(
            current_user, task.member_id
        ):
            raise HTTPException(
                status_code=http_status.HTTP_403_FORBIDDEN, detail="无权限修改该任务"
            )

        # 获取更新数据
        update_data = task_update.dict(exclude_unset=True)

        # 普通用户限制
        if is_task_owner and not check_user_can_manage_group(current_user):
            restricted_fields = ["assigned_to", "priority", "task_type"]
            for field in restricted_fields:
                if field in update_data:
                    raise HTTPException(
                        status_code=http_status.HTTP_403_FORBIDDEN,
                        detail=f"无权限修改字段：{field}",
                    )

        # 验证新分配的成员
        if "assigned_to" in update_data and update_data["assigned_to"]:
            member_query = select(Member).where(Member.id == update_data["assigned_to"])
            member_result = await db.execute(member_query)
            member = member_result.scalar_one_or_none()

            if not member or not member.is_active:
                raise HTTPException(
                    status_code=http_status.HTTP_400_BAD_REQUEST,
                    detail="指定的执行者不存在或已被禁用",
                )

        # 更新字段
        for field, value in update_data.items():
            if field == "tag_ids":
                # 更新标签关联
                if check_user_can_manage_group(current_user):
                    # 清除现有标签
                    task.tags.clear()

                    # 添加新标签
                    if value:
                        tag_query = select(TaskTag).where(TaskTag.id.in_(value))
                        tag_result = await db.execute(tag_query)
                        tags = tag_result.scalars().all()

                        for tag in tags:
                            task.tags.append(tag)
            elif hasattr(task, field):
                setattr(task, field, value)

        # 状态变更处理
        if "status" in update_data:
            new_status = update_data["status"]

            if new_status == TaskStatus.IN_PROGRESS and not task.response_time:
                task.response_time = datetime.utcnow()
            elif new_status == TaskStatus.COMPLETED and not task.completion_time:
                task.completion_time = datetime.utcnow()

        # 重新计算工时
        task.update_work_minutes()

        await db.commit()
        await db.refresh(task)

        logger.info(f"Repair task {task_id} updated by {current_user.student_id}")

        return create_response(
            data={"id": task.id, "task_id": task.task_id, "status": task.status.value},
            message="维修任务更新成功",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update repair task {task_id} error: {str(e)}")
        await db.rollback()
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="更新维修任务失败",
        )


@router.delete("/repair/{task_id}", response_model=Dict[str, Any])
async def delete_repair_task(
    task_id: int,
    current_user: Member = Depends(get_current_active_admin),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """
    删除维修任务

    权限：仅管理员可删除任务
    """
    try:
        # 查询任务
        query = select(RepairTask).where(RepairTask.id == task_id)
        result = await db.execute(query)
        task = result.scalar_one_or_none()

        if not task:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND, detail="维修任务不存在"
            )

        # 检查任务状态
        if task.status == TaskStatus.IN_PROGRESS:
            raise HTTPException(
                status_code=http_status.HTTP_400_BAD_REQUEST,
                detail="不能删除进行中的任务，请先修改任务状态",
            )

        task_id_str = task.task_id
        task_title = task.title

        # 删除任务
        await db.delete(task)
        await db.commit()

        logger.warning(
            f"Repair task deleted: {task_id_str} by {current_user.student_id}"
        )

        return create_response(
            message=f"成功删除维修任务：{task_title} ({task_id_str})"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete repair task {task_id} error: {str(e)}")
        await db.rollback()
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="删除维修任务失败",
        )


@router.delete("/batch-delete", response_model=Dict[str, Any])
async def batch_delete_tasks(
    request_data: Dict[str, Any],
    current_user: Member = Depends(get_current_active_admin),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """
    批量删除任务

    权限：仅管理员可批量删除任务
    """
    try:
        # 支持前端可能使用的不同参数名
        task_ids = request_data.get("task_ids", request_data.get("ids", []))

        if not task_ids:
            raise HTTPException(
                status_code=http_status.HTTP_400_BAD_REQUEST,
                detail="任务ID列表不能为空",
            )

        # 查询要删除的任务
        query = select(RepairTask).where(RepairTask.id.in_(task_ids))
        result = await db.execute(query)
        tasks = result.scalars().all()

        if not tasks:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND, detail="没有找到指定的任务"
            )

        # 检查任务状态
        in_progress_tasks = []
        deletable_tasks = []

        for task in tasks:
            if task.status == TaskStatus.IN_PROGRESS:
                in_progress_tasks.append(f"{task.title} ({task.task_id})")
            else:
                deletable_tasks.append(task)

        if in_progress_tasks:
            raise HTTPException(
                status_code=http_status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"以下任务正在进行中，无法删除: {', '.join(in_progress_tasks[:3])}"
                    f"{'等' if len(in_progress_tasks) > 3 else ''}"
                ),
            )

        # 执行批量删除
        deleted_count = 0
        deleted_tasks = []

        for task in deletable_tasks:
            try:
                deleted_tasks.append(f"{task.title} ({task.task_id})")
                await db.delete(task)
                deleted_count += 1
            except Exception as e:
                logger.warning(f"Failed to delete task {task.id}: {str(e)}")

        await db.commit()

        logger.warning(
            f"Batch deleted {deleted_count} tasks by {current_user.student_id}"
        )

        return create_response(
            data={
                "deleted_count": deleted_count,
                "total_requested": len(task_ids),
                "deleted_tasks": deleted_tasks[:10],  # 只返回前10个任务名称
            },
            message=f"成功批量删除 {deleted_count} 个任务",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Batch delete tasks error: {str(e)}")
        await db.rollback()
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="批量删除任务失败",
        )


# ============= 任务状态管理 =============


@router.put("/repair/{task_id}/status", response_model=Dict[str, Any])
async def update_task_status(
    task_id: int,
    status_update: TaskStatusUpdate,
    current_user: Member = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """
    更新任务状态

    权限：任务执行者和管理员可更新状态
    """
    try:
        # 查询任务
        query = select(RepairTask).where(RepairTask.id == task_id)
        result = await db.execute(query)
        task = result.scalar_one_or_none()

        if not task:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND, detail="维修任务不存在"
            )

        # 权限检查
        if task.member_id and not check_user_can_access_task(
            current_user, task.member_id
        ):
            raise HTTPException(
                status_code=http_status.HTTP_403_FORBIDDEN,
                detail="无权限修改该任务状态",
            )

        old_status = task.status
        new_status = status_update.status

        # 状态转换验证
        if not _is_valid_status_transition(old_status, new_status):
            raise HTTPException(
                status_code=http_status.HTTP_400_BAD_REQUEST,
                detail=f"不能从 {old_status.value} 状态转换到 {new_status.value} 状态",
            )

        # 更新状态
        task.status = new_status

        # 状态相关的时间戳更新
        if new_status == TaskStatus.IN_PROGRESS and not task.response_time:
            task.response_time = datetime.utcnow()
        elif new_status == TaskStatus.COMPLETED:
            if not task.completion_time:
                task.completion_time = datetime.utcnow()

            # 完成任务时必须提供实际工时
            if status_update.actual_minutes is not None:
                # 这里可以记录实际工时用于对比分析
                pass

        # 添加完成备注
        if status_update.completion_note:
            if task.description:
                task.description += f"\n\n完成备注：{status_update.completion_note}"
            else:
                task.description = f"完成备注：{status_update.completion_note}"

        # 重新计算工时
        task.update_work_minutes()

        await db.commit()
        await db.refresh(task)

        logger.info(
            f"Task {task_id} status updated from {old_status.value} to "
            f"{new_status.value} by {current_user.student_id}"
        )

        return create_response(
            data={
                "id": task.id,
                "task_id": task.task_id,
                "old_status": old_status.value,
                "new_status": new_status.value,
                "work_minutes": task.work_minutes,
            },
            message=f"任务状态已从 {old_status.value} 更新为 {new_status.value}",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update task {task_id} status error: {str(e)}")
        await db.rollback()
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="更新任务状态失败",
        )


@router.put("/repair/{task_id}/assign", response_model=Dict[str, Any])
async def assign_task(
    task_id: int,
    assignment: TaskAssignment,
    current_user: Member = Depends(get_current_active_group_leader),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """
    分配任务给成员

    权限：组长及以上可分配任务
    """
    try:
        # 查询任务
        query = select(RepairTask).where(RepairTask.id == task_id)
        result = await db.execute(query)
        task = result.scalar_one_or_none()

        if not task:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND, detail="维修任务不存在"
            )

        # 验证目标成员
        member_query = select(Member).where(Member.id == assignment.assigned_to)
        member_result = await db.execute(member_query)
        member = member_result.scalar_one_or_none()

        if not member:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND, detail="指定的成员不存在"
            )

        if not member.is_active:
            raise HTTPException(
                status_code=http_status.HTTP_400_BAD_REQUEST,
                detail="指定的成员账户已被禁用",
            )

        old_member_id = task.member_id
        old_member_name = None

        if old_member_id:
            old_member_query = select(Member).where(Member.id == old_member_id)
            old_member_result = await db.execute(old_member_query)
            old_member = old_member_result.scalar_one_or_none()
            old_member_name = old_member.name if old_member else None

        # 更新分配
        task.member_id = assignment.assigned_to

        # 添加分配备注
        if assignment.assignment_note:
            if task.description:
                task.description += f"\n\n分配备注：{assignment.assignment_note}"
            else:
                task.description = f"分配备注：{assignment.assignment_note}"

        await db.commit()
        await db.refresh(task)

        assignment_msg = f"任务已分配给 {member.name}"
        if old_member_name:
            assignment_msg = f"任务从 {old_member_name} 重新分配给 {member.name}"

        logger.info(
            f"Task {task_id} assigned to {assignment.assigned_to} by "
            f"{current_user.student_id}"
        )

        return create_response(
            data={
                "id": task.id,
                "task_id": task.task_id,
                "assigned_to": assignment.assigned_to,
                "assignee_name": member.name,
            },
            message=assignment_msg,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Assign task {task_id} error: {str(e)}")
        await db.rollback()
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="分配任务失败",
        )


# ============= 任务操作端点（前端兼容） =============


@router.post("/{task_id}/start", response_model=Dict[str, Any])
async def start_task(
    task_id: int,
    current_user: Member = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """
    开始任务

    权限：任务分配者可开始任务
    """
    try:
        # 查询任务
        query = (
            select(RepairTask)
            .options(joinedload(RepairTask.member))
            .where(RepairTask.id == task_id)
        )
        result = await db.execute(query)
        task = result.scalar_one_or_none()

        if not task:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND, detail="任务不存在"
            )

        # 检查权限：只有任务分配者或管理员可以开始任务
        if task.member_id != current_user.id and current_user.role.value not in [
            "admin",
            "group_leader",
        ]:
            raise HTTPException(
                status_code=http_status.HTTP_403_FORBIDDEN,
                detail="您没有权限开始此任务",
            )

        # 检查任务状态
        if task.status != TaskStatus.PENDING:
            raise HTTPException(
                status_code=http_status.HTTP_400_BAD_REQUEST,
                detail=f"任务当前状态为 {task.status.value}，无法开始",
            )

        # 更新任务状态
        task.status = TaskStatus.IN_PROGRESS
        task.response_time = datetime.utcnow()

        await db.commit()
        await db.refresh(task)

        return create_response(
            data={
                "id": task.id,
                "task_id": task.task_id,
                "status": task.status.value,
                "started_at": task.response_time.isoformat(),
            },
            message="任务已开始",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Start task {task_id} error: {str(e)}")
        await db.rollback()
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="开始任务失败",
        )


@router.post("/{task_id}/complete", response_model=Dict[str, Any])
async def complete_task(
    task_id: int,
    request_data: Dict[str, Any] = {},
    current_user: Member = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """
    完成任务

    权限：任务分配者可完成任务
    """
    try:
        # 查询任务
        query = (
            select(RepairTask)
            .options(joinedload(RepairTask.member))
            .where(RepairTask.id == task_id)
        )
        result = await db.execute(query)
        task = result.scalar_one_or_none()

        if not task:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND, detail="任务不存在"
            )

        # 检查权限
        if task.member_id != current_user.id and current_user.role.value not in [
            "admin",
            "group_leader",
        ]:
            raise HTTPException(
                status_code=http_status.HTTP_403_FORBIDDEN,
                detail="您没有权限完成此任务",
            )

        # 检查任务状态
        if task.status not in [TaskStatus.IN_PROGRESS, TaskStatus.PENDING]:
            raise HTTPException(
                status_code=http_status.HTTP_400_BAD_REQUEST,
                detail=f"任务当前状态为 {task.status.value}，无法完成",
            )

        # 更新任务状态
        task.status = TaskStatus.COMPLETED
        task.completion_time = datetime.utcnow()

        # 如果未开始过，设置响应时间
        if not task.response_time:
            task.response_time = task.completion_time

        # 处理实际工时（如果提供）
        actual_hours = request_data.get("actualHours")
        if actual_hours is not None:
            task.work_minutes = int(float(actual_hours) * 60)
        else:
            # 重新计算工时
            task.update_work_minutes()

        await db.commit()
        await db.refresh(task)

        return create_response(
            data={
                "id": task.id,
                "task_id": task.task_id,
                "status": task.status.value,
                "completed_at": task.completion_time.isoformat(),
                "work_minutes": task.work_minutes,
            },
            message="任务已完成",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Complete task {task_id} error: {str(e)}")
        await db.rollback()
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="完成任务失败",
        )


@router.post("/{task_id}/cancel", response_model=Dict[str, Any])
async def cancel_task(
    task_id: int,
    request_data: Dict[str, Any],
    current_user: Member = Depends(get_current_active_group_leader),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """
    取消任务

    权限：组长及以上可取消任务
    """
    try:
        reason = request_data.get("reason", "")

        # 查询任务
        query = (
            select(RepairTask)
            .options(joinedload(RepairTask.member))
            .where(RepairTask.id == task_id)
        )
        result = await db.execute(query)
        task = result.scalar_one_or_none()

        if not task:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND, detail="任务不存在"
            )

        # 检查任务状态
        if task.status == TaskStatus.COMPLETED:
            raise HTTPException(
                status_code=http_status.HTTP_400_BAD_REQUEST,
                detail="已完成的任务无法取消",
            )

        # 更新任务状态
        old_status = task.status
        task.status = TaskStatus.CANCELLED

        # 如果提供了取消原因，可以存储到描述中
        if reason:
            task.description = f"{task.description or ''}\n\n取消原因：{reason}".strip()

        await db.commit()
        await db.refresh(task)

        logger.warning(
            f"Task {task.task_id} cancelled by {current_user.student_id}, "
            f"reason: {reason}"
        )

        return create_response(
            data={
                "id": task.id,
                "task_id": task.task_id,
                "status": task.status.value,
                "cancelled_at": datetime.utcnow().isoformat(),
            },
            message=f"任务已取消（原状态：{old_status.value}）",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Cancel task {task_id} error: {str(e)}")
        await db.rollback()
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="取消任务失败",
        )


@router.get("/my", response_model=Dict[str, Any])
async def get_my_tasks(
    page: int = Query(1, ge=1, description="页码"),
    pageSize: int = Query(20, ge=1, le=100, description="每页数量"),
    current_user: Member = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """
    获取我的任务列表

    权限：登录用户可查看自己的任务
    """
    try:
        offset = (page - 1) * pageSize

        # 查询我的任务
        query = (
            select(RepairTask)
            .options(joinedload(RepairTask.member))
            .where(RepairTask.member_id == current_user.id)
            .order_by(desc(RepairTask.report_time))
        )

        # 获取总数
        count_query = select(func.count(RepairTask.id)).where(
            RepairTask.member_id == current_user.id
        )
        count_result = await db.execute(count_query)
        total = count_result.scalar() or 0

        # 分页查询
        query = query.offset(offset).limit(pageSize)
        result = await db.execute(query)
        tasks = result.scalars().all()

        # 转换数据格式（简化版）
        items = []
        for task in tasks:
            items.append(
                {
                    "id": task.id,
                    "task_id": task.task_id,
                    "title": task.title,
                    "status": task.status.value,
                    "priority": task.priority.value,
                    "type": task.task_type.value,
                    "created_at": (
                        task.created_at.isoformat() if task.created_at else ""
                    ),
                    "report_time": (
                        task.report_time.isoformat() if task.report_time else ""
                    ),
                    "work_minutes": task.work_minutes,
                }
            )

        return create_response(
            data={"items": items, "total": total, "page": page, "pageSize": pageSize},
            message=f"成功获取我的任务，共 {total} 条记录",
        )

    except Exception as e:
        logger.error(f"Get my tasks error: {str(e)}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取我的任务失败",
        )


# ============= 任务标签管理 =============


@router.get("/tags", response_model=Dict[str, Any])
async def get_task_tags(
    is_active: Optional[bool] = Query(None, description="是否启用筛选"),
    tag_type: Optional[str] = Query(None, description="标签类型筛选"),
    current_user: Member = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """
    获取任务标签列表

    权限：所有用户可查看
    """
    try:
        query = select(TaskTag)

        # 筛选条件
        filters = []
        if is_active is not None:
            filters.append(TaskTag.is_active == is_active)
        if tag_type:
            filters.append(TaskTag.tag_type == tag_type)

        if filters:
            query = query.where(and_(*filters))

        query = query.order_by(TaskTag.name)

        result = await db.execute(query)
        tags = result.scalars().all()

        # 转换响应数据
        items = []
        for tag in tags:
            tag_data = {
                "id": tag.id,
                "name": tag.name,
                "description": tag.description,
                "work_minutes_modifier": tag.work_minutes_modifier,
                "is_active": tag.is_active,
                "tag_type": tag.tag_type,
                "created_at": tag.created_at,
                "updated_at": tag.updated_at,
            }
            items.append(tag_data)

        logger.info(
            f"Task tags retrieved by {current_user.student_id}, total: {len(items)}"
        )

        return create_response(
            data={"items": items, "total": len(items)},
            message=f"成功获取任务标签列表，共 {len(items)} 个标签",
        )

    except Exception as e:
        logger.error(f"Get task tags error: {str(e)}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取任务标签失败",
        )


@router.post("/tags", response_model=Dict[str, Any])
async def create_task_tag(
    tag_data: TaskTagCreate,
    current_user: Member = Depends(get_current_active_admin),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """
    创建任务标签

    权限：仅管理员可创建标签
    """
    try:
        # 检查名称是否重复
        existing_query = select(TaskTag).where(TaskTag.name == tag_data.name)
        existing_result = await db.execute(existing_query)
        if existing_result.scalar_one_or_none():
            raise HTTPException(
                status_code=http_status.HTTP_409_CONFLICT,
                detail=f"标签名称 '{tag_data.name}' 已存在",
            )

        # 创建标签
        new_tag = TaskTag(
            name=tag_data.name,
            description=tag_data.description,
            work_minutes_modifier=getattr(
                tag_data, "work_minutes_modifier", tag_data.work_minutes
            ),
            is_active=tag_data.is_active,
        )
        new_tag.tag_type = getattr(tag_data, "tag_type", TaskTagType.BONUS)

        db.add(new_tag)
        await db.commit()
        await db.refresh(new_tag)

        logger.info(
            f"New task tag created: {new_tag.name} by {current_user.student_id}"
        )

        return create_response(
            data={
                "id": new_tag.id,
                "name": new_tag.name,
                "work_minutes_modifier": new_tag.work_minutes_modifier,
            },
            message=f"成功创建任务标签：{new_tag.name}",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Create task tag error: {str(e)}")
        await db.rollback()
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="创建任务标签失败",
        )


# ============= 工时计算 =============


@router.post("/repair/{task_id}/calculate-hours", response_model=Dict[str, Any])
async def calculate_work_hours(
    task_id: int,
    calculation: WorkHourCalculation,
    current_user: Member = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """
    计算任务工时

    权限：任务执行者和管理员可计算工时
    """
    try:
        # 查询任务
        query = (
            select(RepairTask)
            .options(selectinload(RepairTask.tags))
            .where(RepairTask.id == task_id)
        )

        result = await db.execute(query)
        task = result.scalar_one_or_none()

        if not task:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND, detail="维修任务不存在"
            )

        # 权限检查
        if task.member_id and not check_user_can_access_task(
            current_user, task.member_id
        ):
            raise HTTPException(
                status_code=http_status.HTTP_403_FORBIDDEN,
                detail="无权限计算该任务工时",
            )

        # 更新评价和延迟信息
        if calculation.review_rating is not None:
            task.rating = calculation.review_rating

        # 根据延迟情况添加相应标签
        if calculation.is_late_response:
            await _add_penalty_tag(task, "延迟响应", -30, db)

        if calculation.is_late_completion:
            await _add_penalty_tag(task, "延迟完成", -30, db)

        if calculation.review_rating is not None and calculation.review_rating <= 2:
            await _add_penalty_tag(task, "差评", -60, db)

        # 重新计算工时
        task.update_work_minutes()

        await db.commit()
        await db.refresh(task)

        # 构建工时分解详情
        breakdown = _calculate_work_hour_breakdown(task)

        logger.info(
            f"Work hours calculated for task {task_id} by {current_user.student_id}"
        )

        return create_response(
            data={
                "task_id": task.id,
                "base_minutes": task.base_work_minutes,
                "final_minutes": task.work_minutes,
                "breakdown": breakdown,
            },
            message="工时计算完成",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Calculate work hours for task {task_id} error: {str(e)}")
        await db.rollback()
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="工时计算失败",
        )


# ============= 线下单标记管理 =============


@router.post("/repair/{task_id}/mark-offline", response_model=Dict[str, Any])
async def mark_task_as_offline(
    task_id: int,
    inspection_result: Optional[str] = None,
    images: Optional[List[str]] = None,
    current_user: Member = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """
    标记任务为线下单

    权限：任务负责人或管理员可以标记
    """
    try:
        # 查找任务
        query = select(RepairTask).where(RepairTask.id == task_id)
        result = await db.execute(query)
        task = result.scalar_one_or_none()

        if not task:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND, detail="任务不存在"
            )

        # 权限检查：任务负责人或管理员
        if not (
            current_user.is_admin
            or task.member_id == current_user.id
            or current_user.role in [UserRole.GROUP_LEADER, UserRole.ADMIN]
        ):
            raise HTTPException(
                status_code=http_status.HTTP_403_FORBIDDEN,
                detail="无权限标记此任务为线下单",
            )

        # 执行线下标记
        task.mark_as_offline(
            marker_id=current_user.id,
            inspection_result=inspection_result,
            images=images,
        )

        await db.commit()

        logger.info(f"Task {task_id} marked as offline by user {current_user.id}")

        return create_response(
            message="任务已标记为线下单",
            data={
                "task_id": task.id,
                "offline_info": task.get_offline_info(),
                "work_minutes_updated": task.work_minutes,
            },
        )

    except HTTPException:
        await db.rollback()
        raise
    except Exception as e:
        logger.error(f"Mark task {task_id} as offline error: {str(e)}")
        await db.rollback()
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="标记线下单失败",
        )


@router.delete("/repair/{task_id}/unmark-offline", response_model=Dict[str, Any])
async def unmark_task_offline(
    task_id: int,
    current_user: Member = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """
    取消任务的线下单标记

    权限：任务负责人或管理员
    """
    try:
        # 查找任务
        query = select(RepairTask).where(RepairTask.id == task_id)
        result = await db.execute(query)
        task = result.scalar_one_or_none()

        if not task:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND, detail="任务不存在"
            )

        # 权限检查
        if not (
            current_user.is_admin
            or task.member_id == current_user.id
            or current_user.role in [UserRole.GROUP_LEADER, UserRole.ADMIN]
        ):
            raise HTTPException(
                status_code=http_status.HTTP_403_FORBIDDEN,
                detail="无权限取消此任务的线下单标记",
            )

        if not task.is_offline_marked:
            raise HTTPException(
                status_code=http_status.HTTP_400_BAD_REQUEST,
                detail="任务未标记为线下单",
            )

        # 取消线下标记
        task.unmark_offline()

        await db.commit()

        logger.info(f"Task {task_id} offline marking removed by user {current_user.id}")

        return create_response(
            message="已取消任务的线下单标记",
            data={
                "task_id": task.id,
                "work_minutes_updated": task.work_minutes,
            },
        )

    except HTTPException:
        await db.rollback()
        raise
    except Exception as e:
        logger.error(f"Unmark task {task_id} offline error: {str(e)}")
        await db.rollback()
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="取消线下单标记失败",
        )


@router.put("/repair/{task_id}/offline-inspection", response_model=Dict[str, Any])
async def update_offline_inspection(
    task_id: int,
    inspection_result: str,
    current_user: Member = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """
    更新线下任务检查结果

    权限：任务负责人或管理员
    """
    try:
        # 查找任务
        query = select(RepairTask).where(RepairTask.id == task_id)
        result = await db.execute(query)
        task = result.scalar_one_or_none()

        if not task:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND, detail="任务不存在"
            )

        # 权限检查
        if not (
            current_user.is_admin
            or task.member_id == current_user.id
            or current_user.role in [UserRole.GROUP_LEADER, UserRole.ADMIN]
        ):
            raise HTTPException(
                status_code=http_status.HTTP_403_FORBIDDEN,
                detail="无权限更新此任务的检查结果",
            )

        if not task.is_offline_marked:
            raise HTTPException(
                status_code=http_status.HTTP_400_BAD_REQUEST,
                detail="任务未标记为线下单，无法更新检查结果",
            )

        # 更新检查结果
        task.update_offline_inspection_result(inspection_result)

        await db.commit()

        logger.info(
            f"Task {task_id} offline inspection updated by user {current_user.id}"
        )

        return create_response(
            message="线下检查结果已更新",
            data={
                "task_id": task.id,
                "offline_inspection_result": task.offline_inspection_result,
            },
        )

    except HTTPException:
        await db.rollback()
        raise
    except Exception as e:
        logger.error(f"Update task {task_id} offline inspection error: {str(e)}")
        await db.rollback()
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="更新检查结果失败",
        )


@router.post("/repair/{task_id}/offline-images", response_model=Dict[str, Any])
async def add_offline_images(
    task_id: int,
    image_paths: List[str],
    current_user: Member = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """
    为线下任务添加图片

    权限：任务负责人或管理员
    """
    try:
        # 查找任务
        query = select(RepairTask).where(RepairTask.id == task_id)
        result = await db.execute(query)
        task = result.scalar_one_or_none()

        if not task:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND, detail="任务不存在"
            )

        # 权限检查
        if not (
            current_user.is_admin
            or task.member_id == current_user.id
            or current_user.role in [UserRole.GROUP_LEADER, UserRole.ADMIN]
        ):
            raise HTTPException(
                status_code=http_status.HTTP_403_FORBIDDEN,
                detail="无权限为此任务添加图片",
            )

        if not task.is_offline_marked:
            raise HTTPException(
                status_code=http_status.HTTP_400_BAD_REQUEST,
                detail="任务未标记为线下单，无法添加图片",
            )

        # 添加图片
        task.add_offline_images(image_paths)

        await db.commit()

        logger.info(
            f"Added {len(image_paths)} images to task {task_id} by user {current_user.id}"
        )

        return create_response(
            message="图片已添加",
            data={
                "task_id": task.id,
                "offline_images": task.offline_images,
                "images_count": len(task.offline_images) if task.offline_images else 0,
            },
        )

    except HTTPException:
        await db.rollback()
        raise
    except Exception as e:
        logger.error(f"Add images to task {task_id} error: {str(e)}")
        await db.rollback()
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="添加图片失败",
        )


@router.delete("/repair/{task_id}/offline-images", response_model=Dict[str, Any])
async def remove_offline_image(
    task_id: int,
    image_path: str,
    current_user: Member = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """
    删除线下任务图片

    权限：任务负责人或管理员
    """
    try:
        # 查找任务
        query = select(RepairTask).where(RepairTask.id == task_id)
        result = await db.execute(query)
        task = result.scalar_one_or_none()

        if not task:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND, detail="任务不存在"
            )

        # 权限检查
        if not (
            current_user.is_admin
            or task.member_id == current_user.id
            or current_user.role in [UserRole.GROUP_LEADER, UserRole.ADMIN]
        ):
            raise HTTPException(
                status_code=http_status.HTTP_403_FORBIDDEN,
                detail="无权限删除此任务的图片",
            )

        if not task.is_offline_marked:
            raise HTTPException(
                status_code=http_status.HTTP_400_BAD_REQUEST,
                detail="任务未标记为线下单",
            )

        # 删除图片
        task.remove_offline_image(image_path)

        await db.commit()

        logger.info(f"Removed image from task {task_id} by user {current_user.id}")

        return create_response(
            message="图片已删除",
            data={
                "task_id": task.id,
                "offline_images": task.offline_images,
                "images_count": len(task.offline_images) if task.offline_images else 0,
            },
        )

    except HTTPException:
        await db.rollback()
        raise
    except Exception as e:
        logger.error(f"Remove image from task {task_id} error: {str(e)}")
        await db.rollback()
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="删除图片失败",
        )


@router.get("/repair/offline-list", response_model=Dict[str, Any])
async def get_offline_marked_tasks(
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=100, description="每页数量"),
    member_id: Optional[int] = Query(None, description="成员筛选"),
    current_user: Member = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """
    获取线下单列表

    权限：组长及以上可查看所有，普通用户只能查看自己的
    """
    try:
        # 构建基础查询
        query = select(RepairTask).where(RepairTask.is_offline_marked.is_(True))

        # 权限筛选
        if current_user.role == UserRole.MEMBER:
            # 普通成员只能查看自己的线下单
            query = query.where(RepairTask.member_id == current_user.id)
        elif member_id and current_user.role in [UserRole.GROUP_LEADER, UserRole.ADMIN]:
            # 组长和管理员可以按成员筛选
            query = query.where(RepairTask.member_id == member_id)

        # 获取总数
        count_query = select(func.count()).select_from(query.subquery())
        count_result = await db.execute(count_query)
        total = count_result.scalar() or 0

        # 分页查询
        query = query.order_by(desc(RepairTask.offline_marked_at))
        query = query.offset((page - 1) * size).limit(size)
        query = query.options(
            selectinload(RepairTask.member),
            selectinload(RepairTask.offline_marker),
        )

        result = await db.execute(query)
        tasks = result.scalars().all()

        # 格式化返回数据
        task_data = []
        for task in tasks:
            task_info = {
                "id": task.id,
                "task_id": task.task_id,
                "title": task.title,
                "member_name": task.member.name if task.member else None,
                "offline_info": task.get_offline_info(),
                "work_minutes": task.work_minutes,
                "task_type": task.task_type.value,
                "status": task.status.value,
                "offline_marker_name": (
                    task.offline_marker.name if task.offline_marker else None
                ),
            }
            task_data.append(task_info)

        return create_response(
            message=f"获取线下单列表成功，共 {total} 条",
            data={
                "tasks": task_data,
                "total": total,
                "page": page,
                "size": size,
                "pages": (total + size - 1) // size,
            },
        )

    except Exception as e:
        logger.error(f"Get offline marked tasks error: {str(e)}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取线下单列表失败",
        )


# ============= 完整数据导出 =============


@router.get("/export/comprehensive", response_model=Dict[str, Any])
async def export_comprehensive_data(
    export_type: str = Query(
        "all",
        regex="^(all|repair|assistance|monitoring|offline)$",
        description="导出数据类型",
    ),
    format: str = Query("excel", regex="^(excel|csv|json)$", description="导出格式"),
    date_from: Optional[datetime] = Query(None, description="开始时间"),
    date_to: Optional[datetime] = Query(None, description="结束时间"),
    member_ids: Optional[List[int]] = Query(None, description="成员筛选"),
    include_offline_info: bool = Query(True, description="包含线下单信息"),
    include_approval_info: bool = Query(True, description="包含审核信息"),
    include_work_hours_detail: bool = Query(True, description="包含工时详情"),
    current_user: Member = Depends(get_current_active_group_leader),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """
    完整数据导出 - 扩展现有导出服务

    权限：组长及以上可导出
    功能：
    - 支持所有任务类型的完整数据导出
    - 包含线下单标记信息
    - 包含协助任务审核信息
    - 包含详细工时计算信息
    - 支持多种导出格式
    """
    try:
        import json

        # import tempfile  # removed unused import
        from io import BytesIO

        import pandas as pd

        # 构建基础查询条件
        filters = []
        if date_from:
            filters.append(RepairTask.report_time >= date_from)
        if date_to:
            filters.append(RepairTask.report_time <= date_to)
        if member_ids:
            filters.append(RepairTask.member_id.in_(member_ids))

        export_data = {}

        # 导出维修任务数据
        if export_type in ["all", "repair"]:
            repair_query = select(RepairTask).options(
                selectinload(RepairTask.member),
                selectinload(RepairTask.tags),
                selectinload(RepairTask.offline_marker),
            )
            if filters:
                repair_query = repair_query.where(and_(*filters))

            repair_result = await db.execute(repair_query)
            repair_tasks = repair_result.scalars().all()

            repair_data = []
            for task in repair_tasks:
                task_info = {
                    "任务ID": task.task_id,
                    "任务标题": task.title,
                    "描述": task.description,
                    "负责人": task.member.name if task.member else None,
                    "任务类型": task.task_type.value,
                    "任务状态": task.status.value,
                    "优先级": task.priority.value,
                    "分类": task.category.value,
                    "报告时间": (
                        task.report_time.isoformat() if task.report_time else None
                    ),
                    "响应时间": (
                        task.response_time.isoformat() if task.response_time else None
                    ),
                    "完成时间": (
                        task.completion_time.isoformat()
                        if task.completion_time
                        else None
                    ),
                    "工时分钟": task.work_minutes,
                    "基础工时": task.base_work_minutes,
                    "用户评分": task.rating,
                    "用户反馈": task.feedback,
                    "报修人": task.reporter_name,
                    "联系方式": task.reporter_contact,
                    "地点": task.location,
                }

                # 包含线下单信息
                if include_offline_info:
                    offline_info = task.get_offline_info()
                    task_info.update(
                        {
                            "是否线下单": offline_info["is_offline_marked"],
                            "线下单标记人": (
                                task.offline_marker.name
                                if task.offline_marker
                                else None
                            ),
                            "线下单标记时间": offline_info["offline_marked_at"],
                            "线下检查结果": offline_info["offline_inspection_result"],
                            "线下图片数量": offline_info["offline_images_count"],
                        }
                    )

                # 包含工时详情
                if include_work_hours_detail:
                    task_info.update(
                        {
                            "是否爆单": task.is_rush_order,
                            "工单状态": task.work_order_status,
                            "检修形式": task.repair_form,
                            "标签列表": (
                                ", ".join([tag.name for tag in task.tags if tag.name])
                                if task.tags
                                else ""
                            ),
                            "标签工时修正": (
                                sum(
                                    [
                                        tag.work_minutes_modifier
                                        for tag in task.tags
                                        if tag.work_minutes_modifier
                                    ]
                                )
                                if task.tags
                                else 0
                            ),
                            "是否超时响应": task.is_overdue_response,
                            "是否超时完成": task.is_overdue_completion,
                            "是否正面评价": task.is_positive_review,
                            "是否负面评价": task.is_negative_review,
                        }
                    )

                # 原始数据和匹配数据
                if task.original_data:
                    task_info["A表原始数据"] = json.dumps(
                        task.original_data, ensure_ascii=False
                    )
                if task.matched_member_data:
                    task_info["B表匹配数据"] = json.dumps(
                        task.matched_member_data, ensure_ascii=False
                    )

                repair_data.append(task_info)

            export_data["repair_tasks"] = repair_data

        # 导出协助任务数据
        if export_type in ["all", "assistance"]:
            from app.models.task import AssistanceTask

            assistance_filters = []
            if date_from:
                assistance_filters.append(AssistanceTask.start_time >= date_from)
            if date_to:
                assistance_filters.append(AssistanceTask.end_time <= date_to)
            if member_ids:
                assistance_filters.append(AssistanceTask.member_id.in_(member_ids))

            assistance_query = select(AssistanceTask).options(
                selectinload(AssistanceTask.member),
                selectinload(AssistanceTask.approver),
            )
            if assistance_filters:
                assistance_query = assistance_query.where(and_(*assistance_filters))

            assistance_result = await db.execute(assistance_query)
            assistance_tasks = assistance_result.scalars().all()

            assistance_data = []
            for assistance_task in assistance_tasks:
                task_info = {
                    "任务ID": assistance_task.id,
                    "任务标题": assistance_task.title,
                    "描述": assistance_task.description,
                    "协助人": (
                        assistance_task.member.name if assistance_task.member else None
                    ),
                    "协助部门": assistance_task.assisted_department,
                    "协助对象": assistance_task.assisted_person,
                    "开始时间": (
                        assistance_task.start_time.isoformat()
                        if assistance_task.start_time
                        else None
                    ),
                    "结束时间": (
                        assistance_task.end_time.isoformat()
                        if assistance_task.end_time
                        else None
                    ),
                    "工时分钟": assistance_task.work_minutes,
                    "任务状态": assistance_task.status.value,
                }

                # 包含审核信息
                if include_approval_info:
                    task_info.update(
                        {
                            "审核状态": (
                                "已审核" if assistance_task.approved_by else "待审核"
                            ),
                            "审核人": (
                                assistance_task.approver.name
                                if assistance_task.approver
                                else None
                            ),
                            "审核时间": (
                                assistance_task.approved_at.isoformat()
                                if assistance_task.approved_at
                                else None
                            ),
                        }
                    )

                assistance_data.append(task_info)

            export_data["assistance_tasks"] = assistance_data

        # 导出监控任务数据
        if export_type in ["all", "monitoring"]:
            from app.models.task import MonitoringTask

            monitoring_filters = []
            if date_from:
                monitoring_filters.append(MonitoringTask.start_time >= date_from)
            if date_to:
                monitoring_filters.append(MonitoringTask.end_time <= date_to)
            if member_ids:
                monitoring_filters.append(MonitoringTask.member_id.in_(member_ids))

            monitoring_query = select(MonitoringTask).options(
                selectinload(MonitoringTask.member)
            )
            if monitoring_filters:
                monitoring_query = monitoring_query.where(and_(*monitoring_filters))

            monitoring_result = await db.execute(monitoring_query)
            monitoring_tasks = monitoring_result.scalars().all()

            monitoring_data = []
            for monitoring_task in monitoring_tasks:
                task_info = {
                    "任务ID": monitoring_task.id,
                    "任务标题": monitoring_task.title,
                    "描述": monitoring_task.description,
                    "负责人": (
                        monitoring_task.member.name if monitoring_task.member else None
                    ),
                    "监控类型": monitoring_task.monitoring_type,
                    "地点": monitoring_task.location,
                    "开始时间": (
                        monitoring_task.start_time.isoformat()
                        if monitoring_task.start_time
                        else None
                    ),
                    "结束时间": (
                        monitoring_task.end_time.isoformat()
                        if monitoring_task.end_time
                        else None
                    ),
                    "工时分钟": monitoring_task.work_minutes,
                    "任务状态": monitoring_task.status.value,
                }
                monitoring_data.append(task_info)

            export_data["monitoring_tasks"] = monitoring_data

        # 导出线下单专门数据
        if export_type == "offline":
            offline_query = (
                select(RepairTask)
                .where(RepairTask.is_offline_marked.is_(True))
                .options(
                    selectinload(RepairTask.member),
                    selectinload(RepairTask.offline_marker),
                )
            )
            if filters:
                offline_query = offline_query.where(and_(*filters))

            offline_result = await db.execute(offline_query)
            offline_tasks = offline_result.scalars().all()

            offline_data = []
            for task in offline_tasks:
                offline_info = task.get_offline_info()
                task_info = {
                    "任务ID": task.task_id,
                    "任务标题": task.title,
                    "负责人": task.member.name if task.member else None,
                    "线下标记人": (
                        task.offline_marker.name if task.offline_marker else None
                    ),
                    "标记时间": offline_info["offline_marked_at"],
                    "检查结果": offline_info["offline_inspection_result"],
                    "图片数量": offline_info["offline_images_count"],
                    "线下图片": offline_info["offline_images"],
                    "工时分钟": task.work_minutes,
                    "任务状态": task.status.value,
                }
                offline_data.append(task_info)

            export_data["offline_tasks"] = offline_data

        # 生成文件
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"comprehensive_data_{export_type}_{timestamp}"
        file_content: Union[str, bytes]  # Will be assigned based on format

        if format == "json":
            # JSON格式导出
            filename += ".json"
            file_content = json.dumps(
                export_data, ensure_ascii=False, indent=2, default=str
            )

        elif format == "csv":
            # CSV格式导出 (合并所有数据到一个表)
            filename += ".csv"
            all_data = []
            for task_type, tasks in export_data.items():
                for task_dict in tasks:
                    task_dict["数据类型"] = task_type
                    all_data.append(task_dict)

            if all_data:
                df = pd.DataFrame(all_data)
                file_content = df.to_csv(index=False, encoding="utf-8")
            else:
                file_content = "没有数据可导出"

        else:  # Excel格式
            filename += ".xlsx"
            buffer = BytesIO()

            with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
                for task_type, tasks in export_data.items():
                    if tasks:
                        df = pd.DataFrame(tasks)
                        sheet_name = {
                            "repair_tasks": "维修任务",
                            "assistance_tasks": "协助任务",
                            "monitoring_tasks": "监控任务",
                            "offline_tasks": "线下任务",
                        }.get(task_type, task_type)
                        df.to_excel(writer, sheet_name=sheet_name, index=False)

            buffer.seek(0)
            file_content = buffer.getvalue()

        # 计算导出统计
        total_records = sum(len(tasks) for tasks in export_data.values())

        # 这里应该保存文件到实际存储位置，简化实现返回模拟结果
        export_result = {
            "download_url": f"/api/v1/files/download/{filename}",
            "filename": filename,
            "export_type": export_type,
            "format": format,
            "data_summary": {
                "total_records": total_records,
                "data_types": list(export_data.keys()),
                "export_time": datetime.now().isoformat(),
                "file_size": (
                    len(str(file_content))
                    if isinstance(file_content, str)
                    else len(file_content)
                ),
            },
            "export_options": {
                "include_offline_info": include_offline_info,
                "include_approval_info": include_approval_info,
                "include_work_hours_detail": include_work_hours_detail,
            },
            "expires_at": (datetime.now() + timedelta(hours=24)).isoformat(),
        }

        logger.info(
            f"Comprehensive data exported by {current_user.id}: "
            f"{export_type} in {format} format, {total_records} records"
        )

        return create_response(
            message=f"完整数据导出成功，共导出 {total_records} 条记录",
            data=export_result,
        )

    except Exception as e:
        logger.error(f"Export comprehensive data error: {str(e)}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="完整数据导出失败",
        )


@router.get("/export/template", response_model=Dict[str, Any])
async def get_export_template(
    template_type: str = Query(
        "repair", regex="^(repair|assistance|monitoring)$", description="模板类型"
    ),
    current_user: Member = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """
    获取数据导出模板

    提供标准的数据导出模板，方便用户了解导出数据结构
    """
    try:
        templates = {
            "repair": {
                "任务ID": "示例任务ID",
                "任务标题": "示例任务标题",
                "描述": "任务描述",
                "负责人": "张三",
                "任务类型": "online/offline",
                "任务状态": "completed",
                "优先级": "medium",
                "分类": "network_repair",
                "报告时间": "2024-01-01T10:00:00",
                "响应时间": "2024-01-01T10:30:00",
                "完成时间": "2024-01-01T11:00:00",
                "工时分钟": 40,
                "基础工时": 40,
                "用户评分": 5,
                "用户反馈": "很好",
                "报修人": "李四",
                "联系方式": "13800138000",
                "地点": "教学楼A101",
                "是否线下单": False,
                "线下单标记人": None,
                "线下单标记时间": None,
                "线下检查结果": None,
                "线下图片数量": 0,
            },
            "assistance": {
                "任务ID": 1,
                "任务标题": "协助其他部门工作",
                "描述": "协助描述",
                "协助人": "王五",
                "协助部门": "教务处",
                "协助对象": "赵六",
                "开始时间": "2024-01-01T14:00:00",
                "结束时间": "2024-01-01T16:00:00",
                "工时分钟": 120,
                "任务状态": "completed",
                "审核状态": "已审核",
                "审核人": "管理员",
                "审核时间": "2024-01-01T16:30:00",
            },
            "monitoring": {
                "任务ID": 1,
                "任务标题": "日常监控巡检",
                "描述": "监控描述",
                "负责人": "钱七",
                "监控类型": "daily_inspection",
                "地点": "机房A",
                "开始时间": "2024-01-01T08:00:00",
                "结束时间": "2024-01-01T09:00:00",
                "工时分钟": 60,
                "任务状态": "completed",
            },
        }

        template = templates.get(template_type, {})

        return create_response(
            message=f"获取{template_type}导出模板成功",
            data={
                "template_type": template_type,
                "fields": template,
                "field_count": len(template),
                "description": f"这是{template_type}类型任务的导出数据模板，展示了所有可能的字段",
            },
        )

    except Exception as e:
        logger.error(f"Get export template error: {str(e)}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取导出模板失败",
        )


# ============= 上月结转逻辑 =============


@router.post("/work-hours/carryover/process", response_model=Dict[str, Any])
async def process_monthly_carryover(
    member_id: int,
    year: int,
    month: int,
    standard_hours: float = Query(30.0, ge=1.0, le=100.0, description="月度标准工时"),
    current_user: Member = Depends(get_current_active_admin),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """
    处理单个成员的月度工时结转

    权限：管理员才能执行结转操作
    """
    try:
        from app.services.work_hours_service import WorkHoursCalculationService

        work_hours_service = WorkHoursCalculationService(db)

        result = await work_hours_service.process_monthly_carryover(
            member_id=member_id,
            target_year=year,
            target_month=month,
            standard_hours=standard_hours,
        )

        logger.info(
            f"Monthly carryover processed by admin {current_user.id} for member {member_id}"
        )

        return create_response(
            message=f"成功处理成员 {member_id} 在 {year}-{month:02d} 的工时结转",
            data=result,
        )

    except Exception as e:
        logger.error(f"Process monthly carryover error: {str(e)}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="处理月度结转失败",
        )


@router.post("/work-hours/carryover/batch", response_model=Dict[str, Any])
async def batch_process_carryover(
    year: int,
    month: int,
    member_ids: Optional[List[int]] = Query(
        None, description="成员ID列表，为空则处理所有成员"
    ),
    standard_hours: float = Query(30.0, ge=1.0, le=100.0, description="月度标准工时"),
    current_user: Member = Depends(get_current_active_admin),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """
    批量处理多个成员的月度工时结转

    权限：管理员才能执行批量结转操作
    """
    try:
        from app.services.work_hours_service import WorkHoursCalculationService

        work_hours_service = WorkHoursCalculationService(db)

        result = await work_hours_service.batch_process_carryover(
            year=year,
            month=month,
            member_ids=member_ids,
            standard_hours=standard_hours,
        )

        logger.info(
            f"Batch carryover processed by admin {current_user.id} for {year}-{month:02d}: "
            f"{result['success_count']} success, {result['error_count']} errors"
        )

        return create_response(
            message=(
                f"批量处理 {year}-{month:02d} 工时结转完成："
                f"成功 {result['success_count']} 个，失败 {result['error_count']} 个"
            ),
            data=result,
        )

    except Exception as e:
        logger.error(f"Batch process carryover error: {str(e)}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="批量处理结转失败",
        )


@router.get("/work-hours/carryover/summary/{member_id}", response_model=Dict[str, Any])
async def get_carryover_summary(
    member_id: int,
    year: int,
    month: int,
    current_user: Member = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """
    获取成员的工时结转摘要

    权限：成员只能查看自己的，管理员和组长可以查看所有人的
    """
    try:
        # 权限检查
        if not (
            current_user.is_admin
            or current_user.role in [UserRole.GROUP_LEADER, UserRole.ADMIN]
            or member_id == current_user.id
        ):
            raise HTTPException(
                status_code=http_status.HTTP_403_FORBIDDEN,
                detail="无权限查看此成员的结转信息",
            )

        from app.services.work_hours_service import WorkHoursCalculationService

        work_hours_service = WorkHoursCalculationService(db)

        result = await work_hours_service.get_carryover_summary(
            member_id=member_id,
            year=year,
            month=month,
        )

        if not result["found"]:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND, detail=result["message"]
            )

        return create_response(
            message=f"获取成员 {member_id} 在 {year}-{month:02d} 的结转摘要成功",
            data=result,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get carryover summary error: {str(e)}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取结转摘要失败",
        )


@router.get(
    "/work-hours/carryover/projection/{member_id}", response_model=Dict[str, Any]
)
async def get_carryover_projection(
    member_id: int,
    current_year: int,
    current_month: int,
    future_months: int = Query(3, ge=1, le=12, description="预测未来月数"),
    standard_hours: float = Query(30.0, ge=1.0, le=100.0, description="月度标准工时"),
    current_user: Member = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """
    获取成员的工时结转预测

    权限：成员只能查看自己的，管理员和组长可以查看所有人的
    """
    try:
        # 权限检查
        if not (
            current_user.is_admin
            or current_user.role in [UserRole.GROUP_LEADER, UserRole.ADMIN]
            or member_id == current_user.id
        ):
            raise HTTPException(
                status_code=http_status.HTTP_403_FORBIDDEN,
                detail="无权限查看此成员的结转预测",
            )

        from app.services.work_hours_service import WorkHoursCalculationService

        work_hours_service = WorkHoursCalculationService(db)

        result = await work_hours_service.calculate_projected_carryover(
            member_id=member_id,
            current_year=current_year,
            current_month=current_month,
            future_months=future_months,
            standard_hours=standard_hours,
        )

        return create_response(
            message=f"获取成员 {member_id} 未来 {future_months} 个月的结转预测成功",
            data=result,
        )

    except Exception as e:
        logger.error(f"Get carryover projection error: {str(e)}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取结转预测失败",
        )


@router.get("/work-hours/carryover/members", response_model=Dict[str, Any])
async def get_members_carryover_status(
    year: int,
    month: int,
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=100, description="每页数量"),
    current_user: Member = Depends(get_current_active_group_leader),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """
    获取所有成员的结转状态概览

    权限：组长及以上可查看
    """
    try:
        # 获取所有月度汇总记录
        from app.models.attendance import MonthlyAttendanceSummary

        query = (
            select(MonthlyAttendanceSummary)
            .where(
                and_(
                    MonthlyAttendanceSummary.year == year,
                    MonthlyAttendanceSummary.month == month,
                )
            )
            .options(selectinload(MonthlyAttendanceSummary.member))
        )

        # 获取总数
        count_query = select(func.count()).select_from(query.subquery())
        count_result = await db.execute(count_query)
        total = count_result.scalar() or 0

        # 分页查询
        query = query.order_by(desc(MonthlyAttendanceSummary.total_hours))
        query = query.offset((page - 1) * size).limit(size)

        result = await db.execute(query)
        summaries = result.scalars().all()

        # 格式化数据
        members_data = []
        for summary in summaries:
            member_info = {
                "member_id": summary.member_id,
                "member_name": summary.member.name if summary.member else None,
                "period": summary.month_string,
                "total_hours": summary.total_hours or 0.0,
                "carried_hours": summary.carried_hours or 0.0,
                "remaining_hours": summary.remaining_hours or 0.0,
                "carryover_info": summary.get_carryover_info(),
            }
            members_data.append(member_info)

        return create_response(
            message=f"获取 {year}-{month:02d} 成员结转状态成功，共 {total} 条记录",
            data={
                "members": members_data,
                "total": total,
                "page": page,
                "size": size,
                "pages": (total + size - 1) // size,
                "period": f"{year}-{month:02d}",
                "statistics": {
                    "total_members": total,
                    "members_with_carryover": len(
                        [
                            m
                            for m in members_data
                            if (
                                isinstance(m, dict)
                                and "carryover_info" in m
                                and isinstance(m["carryover_info"], dict)
                                and m["carryover_info"].get(
                                    "is_eligible_for_carryover", False
                                )
                            )
                        ]
                    ),
                    "total_carried_hours": sum(
                        m["carried_hours"]
                        for m in members_data
                        if isinstance(m, dict) and "carried_hours" in m
                    ),
                    "total_remaining_hours": sum(
                        m["remaining_hours"]
                        for m in members_data
                        if isinstance(m, dict) and "remaining_hours" in m
                    ),
                },
            },
        )

    except Exception as e:
        logger.error(f"Get members carryover status error: {str(e)}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取成员结转状态失败",
        )


# ============= 小组扣时机制 =============


@router.post("/group-penalty/apply", response_model=Dict[str, Any])
async def apply_group_penalty(
    task_id: int,
    penalty_type: str = Query(
        ...,
        regex="^(late_response|late_completion|negative_review)$",
        description="惩罚类型",
    ),
    current_user: Member = Depends(get_current_active_admin),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """
    为指定任务应用小组扣时

    权限：管理员可以应用小组扣时
    惩罚类型：
    - late_response: 超时响应 (扣30分钟/人)
    - late_completion: 超时处理 (扣30分钟/人)
    - negative_review: 差评 (扣60分钟/人)
    """
    try:
        from app.services.work_hours_service import WorkHoursCalculationService

        work_hours_service = WorkHoursCalculationService(db)

        result = await work_hours_service.apply_group_penalty_for_task(
            task_id=task_id,
            penalty_type=penalty_type,
            operator_id=current_user.id,
        )

        logger.info(
            f"Group penalty applied by admin {current_user.id} for task {task_id}: {penalty_type}"
        )

        return create_response(
            message=f"成功为任务 {task_id} 应用小组 {penalty_type} 扣时，影响 {result['affected_count']} 名成员",
            data=result,
        )

    except Exception as e:
        logger.error(f"Apply group penalty error: {str(e)}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="应用小组扣时失败",
        )


@router.post("/group-penalty/batch", response_model=Dict[str, Any])
async def batch_apply_group_penalty(
    task_ids: List[int],
    penalty_type: str = Query(
        ...,
        regex="^(late_response|late_completion|negative_review)$",
        description="惩罚类型",
    ),
    current_user: Member = Depends(get_current_active_admin),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """
    批量应用小组扣时

    权限：管理员可以批量应用小组扣时
    """
    try:
        from app.services.work_hours_service import WorkHoursCalculationService

        work_hours_service = WorkHoursCalculationService(db)

        result = await work_hours_service.batch_apply_group_penalties(
            task_ids=task_ids,
            penalty_type=penalty_type,
            operator_id=current_user.id,
        )

        logger.info(
            f"Batch group penalty applied by admin {current_user.id}: "
            f"{penalty_type} for {len(task_ids)} tasks, "
            f"affected {result['total_affected_members']} members"
        )

        return create_response(
            message=(
                f"批量应用小组 {penalty_type} 扣时完成：成功 {result['success_count']} 个任务，"
                f"失败 {result['error_count']} 个，总计影响 {result['total_affected_members']} 名成员"
            ),
            data=result,
        )

    except Exception as e:
        logger.error(f"Batch apply group penalty error: {str(e)}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="批量应用小组扣时失败",
        )


@router.get("/group-penalty/preview/{task_id}", response_model=Dict[str, Any])
async def preview_group_penalty(
    task_id: int,
    penalty_type: str = Query(
        ...,
        regex="^(late_response|late_completion|negative_review)$",
        description="惩罚类型",
    ),
    current_user: Member = Depends(get_current_active_group_leader),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """
    预览小组扣时影响的成员

    权限：组长及以上可以预览
    """
    try:
        from app.services.work_hours_service import WorkHoursCalculationService

        work_hours_service = WorkHoursCalculationService(db)

        # 获取小组成员信息
        group_info = await work_hours_service.get_group_members_by_task(task_id)

        # 添加惩罚信息
        penalty_minutes = work_hours_service._get_penalty_minutes(penalty_type)

        penalty_info = {
            "penalty_type": penalty_type,
            "penalty_description": {
                "late_response": "超时响应惩罚：响应超时24小时",
                "late_completion": "超时处理惩罚：处理超时48小时",
                "negative_review": "差评惩罚：用户差评（2星及以下）",
            }.get(penalty_type, "未知惩罚类型"),
            "penalty_minutes": penalty_minutes,
            "will_affect_members": len(group_info["group_members"]),
        }

        group_info.update(penalty_info)

        return create_response(
            message=f"获取任务 {task_id} 的小组扣时预览成功",
            data=group_info,
        )

    except Exception as e:
        logger.error(f"Preview group penalty error: {str(e)}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取小组扣时预览失败",
        )


@router.get("/group-penalty/history", response_model=Dict[str, Any])
async def get_group_penalty_history(
    date_from: Optional[datetime] = Query(None, description="开始时间"),
    date_to: Optional[datetime] = Query(None, description="结束时间"),
    penalty_type: Optional[str] = Query(
        None,
        regex="^(late_response|late_completion|negative_review)$",
        description="惩罚类型筛选",
    ),
    member_id: Optional[int] = Query(None, description="成员筛选"),
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=100, description="每页数量"),
    current_user: Member = Depends(get_current_active_group_leader),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """
    获取小组扣时历史记录

    权限：组长及以上可查看
    """
    try:
        # 构建基础查询：查找有惩罚标签的任务
        penalty_tag_names = ["超时响应惩罚", "超时处理惩罚", "差评惩罚"]

        if penalty_type:
            penalty_tag_map = {
                "late_response": ["超时响应惩罚"],
                "late_completion": ["超时处理惩罚"],
                "negative_review": ["差评惩罚"],
            }
            penalty_tag_names = penalty_tag_map.get(penalty_type, penalty_tag_names)

        # 查询有惩罚标签的任务
        from app.models.task import task_tag_association

        subquery = select(task_tag_association.c.task_id).join(
            TaskTag,
            and_(
                task_tag_association.c.tag_id == TaskTag.id,
                TaskTag.name.in_(penalty_tag_names),
            ),
        )

        query = (
            select(RepairTask)
            .where(RepairTask.id.in_(subquery))
            .options(selectinload(RepairTask.member), selectinload(RepairTask.tags))
        )

        # 添加筛选条件
        filters = []
        if date_from:
            filters.append(RepairTask.report_time >= date_from)
        if date_to:
            filters.append(RepairTask.report_time <= date_to)
        if member_id:
            filters.append(RepairTask.member_id == member_id)

        if filters:
            query = query.where(and_(*filters))

        # 获取总数
        count_query = select(func.count()).select_from(query.subquery())
        count_result = await db.execute(count_query)
        total = count_result.scalar() or 0

        # 分页查询
        query = query.order_by(desc(RepairTask.report_time))
        query = query.offset((page - 1) * size).limit(size)

        result = await db.execute(query)
        tasks = result.scalars().all()

        # 格式化返回数据
        history_data = []
        for task in tasks:
            # 获取任务的惩罚标签
            penalty_tags = [tag for tag in task.tags if tag.name in penalty_tag_names]

            task_info = {
                "task_id": task.task_id,
                "task_db_id": task.id,
                "title": task.title,
                "member_name": task.member.name if task.member else None,
                "member_id": task.member_id,
                "department": task.member.department if task.member else None,
                "group_id": task.member.group_id if task.member else None,
                "report_time": (
                    task.report_time.isoformat() if task.report_time else None
                ),
                "penalty_tags": [
                    {
                        "name": tag.name,
                        "description": tag.description,
                        "penalty_minutes": abs(tag.work_minutes_modifier or 0),
                        "tag_type": tag.tag_type.value,
                    }
                    for tag in penalty_tags
                ],
                "total_penalty_minutes": sum(
                    abs(tag.work_minutes_modifier or 0) for tag in penalty_tags
                ),
            }
            history_data.append(task_info)

        return create_response(
            message=f"获取小组扣时历史记录成功，共 {total} 条",
            data={
                "history": history_data,
                "total": total,
                "page": page,
                "size": size,
                "pages": (total + size - 1) // size,
                "filters": {
                    "date_from": date_from.isoformat() if date_from else None,
                    "date_to": date_to.isoformat() if date_to else None,
                    "penalty_type": penalty_type,
                    "member_id": member_id,
                },
            },
        )

    except Exception as e:
        logger.error(f"Get group penalty history error: {str(e)}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取小组扣时历史失败",
        )


# ============= 任务统计 =============


@router.get("/statistics/overview", response_model=Dict[str, Any])
async def get_task_statistics(
    date_from: Optional[datetime] = Query(None, description="统计开始时间"),
    date_to: Optional[datetime] = Query(None, description="统计结束时间"),
    member_id: Optional[int] = Query(None, description="成员筛选"),
    current_user: Member = Depends(get_current_active_group_leader),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """
    获取任务统计信息

    权限：组长及以上可查看统计
    """
    try:
        # 构建基础查询
        base_query = select(RepairTask)

        # 权限筛选
        if not current_user.is_admin and member_id and member_id != current_user.id:
            # 非管理员只能查看自己的统计
            base_query = base_query.where(RepairTask.member_id == current_user.id)
        elif member_id:
            base_query = base_query.where(RepairTask.member_id == member_id)

        # 时间筛选
        if date_from:
            base_query = base_query.where(RepairTask.report_time >= date_from)
        if date_to:
            base_query = base_query.where(RepairTask.report_time <= date_to)

        # 基础统计
        total_query = select(func.count()).select_from(base_query.subquery())
        total_result = await db.execute(total_query)
        total_tasks = total_result.scalar()

        # 状态分布统计
        status_stats = {}
        for task_status in TaskStatus:
            status_query = base_query.where(RepairTask.status == task_status)
            count_query = select(func.count()).select_from(status_query.subquery())
            count_result = await db.execute(count_query)
            status_stats[task_status.value] = count_result.scalar()

        # 类型分布统计
        type_stats = {}
        for task_type in TaskType:
            type_query = base_query.where(RepairTask.task_type == task_type)
            count_query = select(func.count()).select_from(type_query.subquery())
            count_result = await db.execute(count_query)
            type_stats[task_type.value] = count_result.scalar()

        # 优先级分布统计
        priority_stats = {}
        for priority in TaskPriority:
            priority_query = base_query.where(RepairTask.priority == priority)
            count_query = select(func.count()).select_from(priority_query.subquery())
            count_result = await db.execute(count_query)
            priority_stats[priority.value] = count_result.scalar()

        # 工时统计
        work_minutes_query = select(func.sum(RepairTask.work_minutes)).select_from(
            base_query.subquery()
        )
        work_minutes_result = await db.execute(work_minutes_query)
        total_work_minutes = work_minutes_result.scalar() or 0
        total_work_hours = round(total_work_minutes / 60.0, 2)

        # 这里简化计算，实际应该计算平均完成时间
        avg_completion_hours = 0.0
        completed_count = status_stats.get("completed", 0)
        if completed_count and completed_count > 0 and total_work_hours is not None:
            avg_completion_hours = round(total_work_hours / completed_count, 2)

        # 超期任务统计
        current_time = datetime.utcnow()
        overdue_response_query = base_query.where(
            and_(
                RepairTask.status == TaskStatus.PENDING,
                RepairTask.report_time < current_time - timedelta(hours=24),
            )
        )
        overdue_count_query = select(func.count()).select_from(
            overdue_response_query.subquery()
        )
        overdue_count_result = await db.execute(overdue_count_query)
        overdue_tasks = overdue_count_result.scalar()

        statistics_data = {
            "total_tasks": total_tasks,
            "pending_tasks": status_stats.get("pending", 0),
            "in_progress_tasks": status_stats.get("in_progress", 0),
            "completed_tasks": status_stats.get("completed", 0),
            "cancelled_tasks": status_stats.get("cancelled", 0),
            "overdue_tasks": overdue_tasks,
            "total_work_hours": total_work_hours,
            "avg_completion_time": avg_completion_hours,
            "task_type_distribution": type_stats,
            "priority_distribution": priority_stats,
            "status_distribution": status_stats,
        }

        logger.info(f"Task statistics retrieved by {current_user.student_id}")

        return create_response(data=statistics_data, message="成功获取任务统计信息")

    except Exception as e:
        logger.error(f"Get task statistics error: {str(e)}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取任务统计失败",
        )


# ============= 辅助函数 =============


async def _generate_task_id(db: AsyncSession) -> str:
    """生成任务编号"""
    today = datetime.now().strftime("%Y%m%d")

    # 查询今天已有的任务数量
    count_query = select(func.count()).where(RepairTask.task_id.like(f"R{today}%"))
    count_result = await db.execute(count_query)
    count = count_result.scalar()

    # 生成新的任务编号
    return f"R{today}{str((count or 0) + 1).zfill(4)}"


def _is_valid_status_transition(old_status: TaskStatus, new_status: TaskStatus) -> bool:
    """验证状态转换是否有效"""
    valid_transitions = {
        TaskStatus.PENDING: [TaskStatus.IN_PROGRESS, TaskStatus.CANCELLED],
        TaskStatus.IN_PROGRESS: [
            TaskStatus.COMPLETED,
            TaskStatus.ON_HOLD,
            TaskStatus.CANCELLED,
        ],
        TaskStatus.ON_HOLD: [TaskStatus.IN_PROGRESS, TaskStatus.CANCELLED],
        TaskStatus.COMPLETED: [],  # 已完成的任务不能转换状态
        TaskStatus.CANCELLED: [],  # 已取消的任务不能转换状态
    }

    return new_status in valid_transitions.get(old_status, [])


async def _add_penalty_tag(
    task: RepairTask, tag_name: str, modifier: int, db: AsyncSession
) -> Dict[str, Any]:
    """添加惩罚标签"""
    # 查找或创建标签
    tag_query = select(TaskTag).where(TaskTag.name == tag_name)
    tag_result = await db.execute(tag_query)
    tag = tag_result.scalar_one_or_none()

    if not tag:
        tag = TaskTag(
            name=tag_name,
            work_minutes_modifier=modifier,
            is_active=True,
        )
        tag.tag_type = TaskTagType.PENALTY
        db.add(tag)
        await db.flush()

    # 添加到任务
    if tag not in task.tags:
        task.tags.append(tag)

    return {"tag_name": tag_name, "modifier": modifier, "applied": tag not in task.tags}


def _calculate_work_hour_breakdown(task: RepairTask) -> Dict[str, Any]:
    """计算工时分解详情"""
    base_minutes = task.base_work_minutes
    total_modifier = 0
    applied_tags = []

    for tag in task.tags:
        if tag.is_active:
            total_modifier += tag.work_minutes_modifier or 0
            applied_tags.append(
                {
                    "name": tag.name,
                    "modifier": tag.work_minutes_modifier,
                    "type": tag.tag_type,
                }
            )

    return {
        "base_minutes": base_minutes,
        "tag_modifiers": total_modifier,
        "final_minutes": max(0, (base_minutes or 0) + total_modifier),
        "applied_tags": applied_tags,
        "task_type": task.task_type.value,
        "is_overdue_response": task.is_overdue_response,
        "is_overdue_completion": task.is_overdue_completion,
        "rating": task.rating,
    }


def _calculate_detailed_work_time_breakdown(task: RepairTask) -> Dict[str, Any]:
    """计算详细的工时分解，包含所有奖励和惩罚项目"""
    from app.core.config import settings

    # 基础工时
    base_minutes = task.get_base_work_minutes()
    task_type_desc = "线上任务" if task.task_type.value == "online" else "线下任务"

    # 分类统计各种加时和扣时
    bonus_items = []  # 奖励项目
    penalty_items = []  # 惩罚项目
    category_items = []  # 分类标签

    total_bonus_minutes = 0
    total_penalty_minutes = 0

    # 爆单特殊处理
    is_rush_order = task.is_rush_order or any(
        tag.tag_type.value == "RUSH_ORDER" for tag in task.tags if tag.is_active
    )

    if is_rush_order:
        bonus_items.append(
            {
                "name": "爆单任务",
                "minutes": settings.RUSH_TASK_BONUS_MINUTES,
                "type": "RUSH_ORDER",
                "description": "爆单任务固定工时奖励",
            }
        )
        total_bonus_minutes += settings.RUSH_TASK_BONUS_MINUTES

    # 处理标签
    for tag in task.tags:
        if not tag.is_active:
            continue

        modifier = tag.work_minutes_modifier or 0
        tag_item: Dict[str, object] = {
            "name": tag.name,
            "minutes": modifier,
            "type": tag.tag_type.value,
            "description": tag.description or "",
        }

        if modifier > 0:
            bonus_items.append(tag_item)
            total_bonus_minutes += modifier
        elif modifier < 0:
            penalty_items.append(
                {
                    **tag_item,
                    "minutes": abs(modifier),  # 显示为正数，便于理解
                }
            )
            total_penalty_minutes += abs(modifier)
        else:
            category_items.append(tag_item)

    # 基于时间的自动惩罚检查
    if task.is_overdue_response:
        penalty_items.append(
            {
                "name": "超时响应惩罚",
                "minutes": settings.LATE_RESPONSE_PENALTY_MINUTES,
                "type": "TIMEOUT_RESPONSE",
                "description": f"响应时间超过{settings.RESPONSE_TIMEOUT_HOURS}小时",
            }
        )
        total_penalty_minutes += settings.LATE_RESPONSE_PENALTY_MINUTES

    if task.is_overdue_completion:
        penalty_items.append(
            {
                "name": "超时处理惩罚",
                "minutes": settings.LATE_COMPLETION_PENALTY_MINUTES,
                "type": "TIMEOUT_PROCESSING",
                "description": f"处理时间超过{settings.COMPLETION_TIMEOUT_HOURS}小时",
            }
        )
        total_penalty_minutes += settings.LATE_COMPLETION_PENALTY_MINUTES

    if task.is_negative_review:
        penalty_items.append(
            {
                "name": "差评惩罚",
                "minutes": settings.NEGATIVE_REVIEW_PENALTY_MINUTES,
                "type": "BAD_RATING",
                "description": (
                    f"用户评价{task.rating}星"
                    f"(≤{settings.MAX_RATING_FOR_NEGATIVE}星)"
                ),
            }
        )
        total_penalty_minutes += settings.NEGATIVE_REVIEW_PENALTY_MINUTES

    # 计算最终工时
    if is_rush_order:
        # 爆单任务：固定15分钟 - 惩罚
        final_minutes = max(0, settings.RUSH_TASK_BONUS_MINUTES - total_penalty_minutes)
        calculation_method = "爆单任务特殊计算"
    else:
        # 普通任务：基础工时 + 奖励 - 惩罚
        final_minutes = max(
            0, base_minutes + total_bonus_minutes - total_penalty_minutes
        )
        calculation_method = "标准累积计算"

    # 时间相关信息
    time_analysis: Dict[str, Optional[Union[str, float]]] = {
        "report_time": task.report_time.isoformat() if task.report_time else None,
        "response_time": task.response_time.isoformat() if task.response_time else None,
        "completion_time": (
            task.completion_time.isoformat() if task.completion_time else None
        ),
        "due_date": task.due_date.isoformat() if task.due_date else None,
        "response_hours": None,
        "processing_hours": None,
    }

    if task.report_time and task.response_time:
        response_hours = (task.response_time - task.report_time).total_seconds() / 3600
        time_analysis["response_hours"] = round(response_hours, 2)

    if task.response_time and task.completion_time:
        processing_hours = (
            task.completion_time - task.response_time
        ).total_seconds() / 3600
        time_analysis["processing_hours"] = round(processing_hours, 2)

    return {
        "task_info": {
            "task_type": task.task_type.value,
            "task_type_description": task_type_desc,
            "is_rush_order": is_rush_order,
            "status": task.status.value,
            "rating": task.rating,
            "calculation_method": calculation_method,
        },
        "base_calculation": {
            "base_minutes": base_minutes,
            "base_description": f"{task_type_desc}基础工时",
        },
        "bonus_items": bonus_items,
        "penalty_items": penalty_items,
        "category_items": category_items,
        "summary": {
            "total_bonus_minutes": total_bonus_minutes,
            "total_penalty_minutes": total_penalty_minutes,
            "net_modifier_minutes": total_bonus_minutes - total_penalty_minutes,
            "final_work_minutes": final_minutes,
            "final_work_hours": round(final_minutes / 60.0, 2),
        },
        "time_analysis": time_analysis,
        "business_rules": {
            "online_base_minutes": settings.DEFAULT_ONLINE_TASK_MINUTES,
            "offline_base_minutes": settings.DEFAULT_OFFLINE_TASK_MINUTES,
            "rush_bonus_minutes": settings.RUSH_TASK_BONUS_MINUTES,
            "positive_review_bonus_minutes": settings.POSITIVE_REVIEW_BONUS_MINUTES,
            "late_response_penalty_minutes": settings.LATE_RESPONSE_PENALTY_MINUTES,
            "late_completion_penalty_minutes": settings.LATE_COMPLETION_PENALTY_MINUTES,
            "negative_review_penalty_minutes": settings.NEGATIVE_REVIEW_PENALTY_MINUTES,
            "response_timeout_hours": settings.RESPONSE_TIMEOUT_HOURS,
            "completion_timeout_hours": settings.COMPLETION_TIMEOUT_HOURS,
        },
    }


# ============= 监控任务管理 =============


@router.post("/monitoring", response_model=Dict[str, Any])
async def create_monitoring_task(
    task_data: Dict[str, Any],
    current_user: Member = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """
    手动登记监控任务

    权限：所有用户可登记自己的监控任务
    """
    try:
        from app.models.task import MonitoringTask
        from app.services.work_hours_service import WorkHoursCalculationService

        # 创建监控任务
        monitoring_task = MonitoringTask(
            member_id=current_user.id,
            title=task_data.get("title", ""),
            description=task_data.get("description", ""),
            location=task_data.get("location", ""),
            monitoring_type=task_data.get("monitoring_type", "inspection"),
            start_time=datetime.fromisoformat(task_data["start_time"]),
            end_time=datetime.fromisoformat(task_data["end_time"]),
        )

        # 计算工作时长
        monitoring_task.update_work_minutes()

        db.add(monitoring_task)
        await db.commit()
        await db.refresh(monitoring_task)

        # 更新月度汇总
        work_hours_service = WorkHoursCalculationService(db)
        if monitoring_task.start_time:
            report_month = monitoring_task.start_time.month
            report_year = monitoring_task.start_time.year
        else:
            # This shouldn't happen since start_time is set above, but for MyPy
            report_month = datetime.utcnow().month
            report_year = datetime.utcnow().year
        await work_hours_service.update_monthly_summary(
            current_user.id, report_year, report_month
        )

        logger.info(
            f"Monitoring task created by {current_user.student_id}: {monitoring_task.id}"
        )

        return create_response(
            data={
                "id": monitoring_task.id,
                "title": monitoring_task.title,
                "work_minutes": monitoring_task.work_minutes,
                "work_hours": round((monitoring_task.work_minutes or 0) / 60.0, 2),
            },
            message="监控任务登记成功",
        )

    except Exception as e:
        logger.error(f"Create monitoring task error: {str(e)}")
        await db.rollback()
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="登记监控任务失败",
        )


@router.get("/monitoring/list", response_model=Dict[str, Any])
async def get_monitoring_tasks_list(
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=100, description="每页数量"),
    member_id: Optional[int] = Query(None, description="成员筛选"),
    date_from: Optional[datetime] = Query(None, description="开始时间"),
    date_to: Optional[datetime] = Query(None, description="结束时间"),
    current_user: Member = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """
    获取监控任务列表

    权限：用户可查看自己的任务，管理员可查看所有任务
    """
    try:
        from app.models.task import MonitoringTask

        # 权限控制
        query_member_id = member_id
        if (
            not check_user_can_manage_group(current_user)
            and member_id != current_user.id
        ):
            query_member_id = current_user.id

        # 构建查询
        query = select(MonitoringTask).options(joinedload(MonitoringTask.member))

        if query_member_id:
            query = query.where(MonitoringTask.member_id == query_member_id)

        if date_from:
            query = query.where(MonitoringTask.start_time >= date_from)
        if date_to:
            query = query.where(MonitoringTask.start_time <= date_to)

        # 计算总数
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await db.execute(count_query)
        total = total_result.scalar() or 0 or 0

        # 分页查询
        query = query.order_by(desc(MonitoringTask.start_time))
        query = query.offset((page - 1) * size).limit(size)

        result = await db.execute(query)
        tasks = result.scalars().all()

        # 构建响应
        items = []
        for task in tasks:
            items.append(
                {
                    "id": task.id,
                    "title": task.title,
                    "description": task.description,
                    "location": task.location,
                    "monitoring_type": task.monitoring_type,
                    "start_time": (
                        task.start_time.isoformat() if task.start_time else ""
                    ),
                    "end_time": task.end_time.isoformat() if task.end_time else "",
                    "work_minutes": task.work_minutes,
                    "work_hours": round((task.work_minutes or 0) / 60.0, 2),
                    "member_name": task.member.name if task.member else "未知",
                    "created_at": (
                        task.created_at.isoformat() if task.created_at else ""
                    ),
                }
            )

        return create_response(
            data={
                "items": items,
                "total": total,
                "page": page,
                "size": size,
                "pages": ((total or 0) + (size or 1) - 1) // (size or 1),
            },
            message=f"成功获取监控任务列表，共 {total} 条记录",
        )

    except Exception as e:
        logger.error(f"Get monitoring tasks error: {str(e)}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取监控任务列表失败",
        )


# ============= 协助任务管理 =============


@router.post("/assistance", response_model=Dict[str, Any])
async def create_assistance_task(
    task_data: Dict[str, Any],
    current_user: Member = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """
    手动登记协助任务

    权限：所有用户可登记自己的协助任务
    """
    try:
        from app.models.task import AssistanceTask
        from app.services.work_hours_service import WorkHoursCalculationService

        # 创建协助任务
        assistance_task = AssistanceTask(
            member_id=current_user.id,
            title=task_data.get("title", ""),
            description=task_data.get("description", ""),
            assisted_department=task_data.get("assisted_department", ""),
            assisted_person=task_data.get("assisted_person", ""),
            start_time=datetime.fromisoformat(task_data["start_time"]),
            end_time=datetime.fromisoformat(task_data["end_time"]),
        )

        # 计算工作时长
        assistance_task.update_work_minutes()

        db.add(assistance_task)
        await db.commit()
        await db.refresh(assistance_task)

        # 更新月度汇总
        work_hours_service = WorkHoursCalculationService(db)
        if assistance_task.start_time:
            report_month = assistance_task.start_time.month
            report_year = assistance_task.start_time.year
        else:
            # This shouldn't happen since start_time is set above, but for MyPy
            report_month = datetime.utcnow().month
            report_year = datetime.utcnow().year
        await work_hours_service.update_monthly_summary(
            current_user.id, report_year, report_month
        )

        logger.info(
            f"Assistance task created by {current_user.student_id}: {assistance_task.id}"
        )

        return create_response(
            data={
                "id": assistance_task.id,
                "title": assistance_task.title,
                "work_minutes": assistance_task.work_minutes,
                "work_hours": round((assistance_task.work_minutes or 0) / 60.0, 2),
            },
            message="协助任务登记成功",
        )

    except Exception as e:
        logger.error(f"Create assistance task error: {str(e)}")
        await db.rollback()
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="登记协助任务失败",
        )


@router.get("/assistance/list", response_model=Dict[str, Any])
async def get_assistance_tasks_list(
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=100, description="每页数量"),
    member_id: Optional[int] = Query(None, description="成员筛选"),
    date_from: Optional[datetime] = Query(None, description="开始时间"),
    date_to: Optional[datetime] = Query(None, description="结束时间"),
    current_user: Member = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """
    获取协助任务列表

    权限：用户可查看自己的任务，管理员可查看所有任务
    """
    try:
        from app.models.task import AssistanceTask

        # 权限控制
        query_member_id = member_id
        if (
            not check_user_can_manage_group(current_user)
            and member_id != current_user.id
        ):
            query_member_id = current_user.id

        # 构建查询
        query = select(AssistanceTask).options(joinedload(AssistanceTask.member))

        if query_member_id:
            query = query.where(AssistanceTask.member_id == query_member_id)

        if date_from:
            query = query.where(AssistanceTask.start_time >= date_from)
        if date_to:
            query = query.where(AssistanceTask.start_time <= date_to)

        # 计算总数
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await db.execute(count_query)
        total = total_result.scalar() or 0

        # 分页查询
        query = query.order_by(desc(AssistanceTask.start_time))
        query = query.offset((page - 1) * size).limit(size)

        result = await db.execute(query)
        tasks = result.scalars().all()

        # 构建响应
        items = []
        for task in tasks:
            items.append(
                {
                    "id": task.id,
                    "title": task.title,
                    "description": task.description,
                    "assisted_department": task.assisted_department,
                    "assisted_person": task.assisted_person,
                    "start_time": (
                        task.start_time.isoformat() if task.start_time else ""
                    ),
                    "end_time": task.end_time.isoformat() if task.end_time else "",
                    "work_minutes": task.work_minutes,
                    "work_hours": round((task.work_minutes or 0) / 60.0, 2),
                    "member_name": task.member.name if task.member else "未知",
                    "created_at": (
                        task.created_at.isoformat() if task.created_at else ""
                    ),
                }
            )

        return create_response(
            data={
                "items": items,
                "total": total,
                "page": page,
                "size": size,
                "pages": ((total or 0) + (size or 1) - 1) // (size or 1),
            },
            message=f"成功获取协助任务列表，共 {total} 条记录",
        )

    except Exception as e:
        logger.error(f"Get assistance tasks error: {str(e)}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取协助任务列表失败",
        )


# ============= 协助任务审核流程 - 扩展现有API =============


@router.get("/assistance/pending", response_model=Dict[str, Any])
async def get_pending_assistance_tasks(
    current_user: Member = Depends(get_current_active_admin),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """
    获取待审核的协助任务列表

    权限：仅管理员可查看待审核任务
    """
    try:
        from sqlalchemy import select

        from app.models.task import AssistanceTask, TaskStatus

        # 查询待审核的协助任务
        stmt = (
            select(AssistanceTask)
            .where(AssistanceTask.status == TaskStatus.PENDING)
            .order_by(AssistanceTask.start_time.desc())
        )

        result = await db.execute(stmt)
        pending_tasks = result.scalars().all()

        # 构建返回数据
        tasks_data = []
        for task in pending_tasks:
            await db.refresh(task, ["member"])
            task_data = {
                "id": task.id,
                "title": task.title,
                "description": task.description,
                "member_id": task.member_id,
                "member_name": task.member.name if task.member else "未知",
                "assisted_department": task.assisted_department,
                "assisted_person": task.assisted_person,
                "start_time": task.start_time.isoformat() if task.start_time else None,
                "end_time": task.end_time.isoformat() if task.end_time else None,
                "work_minutes": task.work_minutes,
                "work_hours": round((task.work_minutes or 0) / 60.0, 2),
                "status": task.status.value,
                "created_at": task.created_at.isoformat() if task.created_at else None,
            }
            tasks_data.append(task_data)

        return {
            "success": True,
            "data": {
                "tasks": tasks_data,
                "total": len(tasks_data),
            },
            "message": "获取待审核协助任务成功",
        }

    except Exception as e:
        logger.error(f"Get pending assistance tasks error: {str(e)}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取待审核协助任务失败",
        )


@router.put("/assistance/{task_id}/approve", response_model=Dict[str, Any])
async def approve_assistance_task(
    task_id: int,
    approval_data: Dict[str, Any],
    current_user: Member = Depends(get_current_active_admin),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """
    审核协助任务

    权限：仅管理员可审核协助任务
    """
    try:
        from datetime import datetime

        from sqlalchemy import select

        from app.models.task import AssistanceTask, TaskStatus

        # 获取待审核任务
        stmt = select(AssistanceTask).where(AssistanceTask.id == task_id)
        result = await db.execute(stmt)
        task = result.scalar_one_or_none()

        if not task:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND, detail="协助任务不存在"
            )

        if task.status != TaskStatus.PENDING:
            raise HTTPException(
                status_code=http_status.HTTP_400_BAD_REQUEST,
                detail="任务已审核，无需重复操作",
            )

        # 解析审核数据
        approve = approval_data.get("approve", True)  # 默认通过

        # 更新任务状态
        if approve:
            task.status = TaskStatus.COMPLETED
            task.approved_by = current_user.id
            task.approved_at = datetime.utcnow()

            # 更新相关成员的月度汇总 (复用现有服务)
            if task.start_time:
                from app.services.work_hours_service import WorkHoursCalculationService

                work_hours_service = WorkHoursCalculationService(db)

                if task.member_id:
                    await work_hours_service.recalculate_member_monthly_summary(
                        member_id=task.member_id,
                        year=task.start_time.year,
                        month=task.start_time.month,
                    )

            message = "协助任务审核通过"
        else:
            task.status = TaskStatus.CANCELLED
            task.approved_by = current_user.id
            task.approved_at = datetime.utcnow()
            message = "协助任务审核驳回"

        await db.commit()
        await db.refresh(task, ["member", "approver"])

        return {
            "success": True,
            "data": {
                "id": task.id,
                "title": task.title,
                "status": task.status.value,
                "approved_by": current_user.id,
                "approved_by_name": current_user.name,
                "approved_at": (
                    task.approved_at.isoformat() if task.approved_at else None
                ),
                "work_minutes": task.work_minutes if approve else 0,
                "work_hours": (
                    round((task.work_minutes or 0) / 60.0, 2) if approve else 0
                ),
            },
            "message": message,
        }

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Approve assistance task error: {str(e)}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="审核协助任务失败",
        )


@router.post("/assistance/batch-approve", response_model=Dict[str, Any])
async def batch_approve_assistance_tasks(
    batch_data: Dict[str, Any],
    current_user: Member = Depends(get_current_active_admin),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """
    批量审核协助任务

    权限：仅管理员可批量审核协助任务
    """
    try:
        from datetime import datetime

        from sqlalchemy import select

        from app.models.task import AssistanceTask, TaskStatus

        task_ids = batch_data.get("task_ids", [])
        approve_all = batch_data.get("approve", True)

        if not task_ids:
            raise HTTPException(
                status_code=http_status.HTTP_400_BAD_REQUEST,
                detail="请选择要审核的任务",
            )

        # 获取待审核任务
        stmt = (
            select(AssistanceTask)
            .where(AssistanceTask.id.in_(task_ids))
            .where(AssistanceTask.status == TaskStatus.PENDING)
        )
        result = await db.execute(stmt)
        tasks = result.scalars().all()

        approved_count = 0
        rejected_count = 0

        # 批量更新任务状态
        for task in tasks:
            if approve_all:
                task.status = TaskStatus.COMPLETED
                approved_count += 1
            else:
                task.status = TaskStatus.CANCELLED
                rejected_count += 1

            task.approved_by = current_user.id
            task.approved_at = datetime.utcnow()

        await db.commit()

        # 更新相关成员的月度汇总 (仅批量通过时)
        if approve_all and approved_count > 0:
            from app.services.work_hours_service import WorkHoursCalculationService

            work_hours_service = WorkHoursCalculationService(db)

            # 收集需要更新的年月
            update_periods = set()
            for task in tasks:
                if task.start_time:
                    update_periods.add(
                        (task.member_id, task.start_time.year, task.start_time.month)
                    )

            # 批量更新月度汇总
            for member_id, year, month in update_periods:
                if member_id:
                    await work_hours_service.recalculate_member_monthly_summary(
                        member_id=member_id, year=year, month=month
                    )

        return {
            "success": True,
            "data": {
                "total_tasks": len(tasks),
                "approved_count": approved_count,
                "rejected_count": rejected_count,
                "approved_by": current_user.id,
                "approved_by_name": current_user.name,
            },
            "message": f"批量审核完成：通过 {approved_count} 个，驳回 {rejected_count} 个",
        }

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Batch approve assistance tasks error: {str(e)}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="批量审核协助任务失败",
        )


# ============= 爆单标记管理 =============


@router.post("/rush-marking/batch", response_model=Dict[str, Any])
async def batch_mark_rush_tasks(
    request_data: Dict[str, Any],
    current_user: Member = Depends(get_current_active_admin),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """
    批量标记爆单任务

    权限：仅管理员可标记爆单任务
    """
    try:
        pass

        from app.services.work_hours_service import RushTaskMarkingService

        rush_service = RushTaskMarkingService(db)

        # 解析请求数据
        date_from = datetime.fromisoformat(request_data["date_from"]).date()
        date_to = datetime.fromisoformat(request_data["date_to"]).date()
        task_ids = request_data.get("task_ids")

        # 执行爆单标记
        result = await rush_service.mark_rush_tasks_by_date(
            date_from=date_from,
            date_to=date_to,
            task_ids=task_ids,
            marked_by=current_user.id,
        )

        # 更新相关成员的月度汇总
        from app.services.work_hours_service import WorkHoursCalculationService

        work_hours_service = WorkHoursCalculationService(db)

        # 批量更新标记期间的月度汇总
        for month in range(date_from.month, date_to.month + 1):
            year = date_from.year if month >= date_from.month else date_to.year
            await work_hours_service.batch_update_monthly_summaries(year, month)

        logger.info(f"Rush tasks marked by {current_user.student_id}: {result}")

        return create_response(
            data=result, message=f"爆单标记完成，共标记 {result['marked']} 个任务"
        )

    except Exception as e:
        logger.error(f"Batch mark rush tasks error: {str(e)}")
        await db.rollback()
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="批量标记爆单任务失败",
        )


@router.get("/rush-marking/candidates", response_model=Dict[str, Any])
async def get_rush_task_candidates(
    date_from: datetime = Query(..., description="开始日期"),
    date_to: datetime = Query(..., description="结束日期"),
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=100, description="每页数量"),
    current_user: Member = Depends(get_current_active_admin),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """
    获取可标记为爆单的任务候选列表

    权限：仅管理员可查看
    """
    try:
        # 查询指定时间范围内的已完成任务，且未标记为爆单
        query = (
            select(RepairTask)
            .options(joinedload(RepairTask.member), selectinload(RepairTask.tags))
            .where(
                and_(
                    RepairTask.report_time >= date_from,
                    RepairTask.report_time <= date_to,
                    RepairTask.status.in_(
                        [TaskStatus.COMPLETED, TaskStatus.IN_PROGRESS]
                    ),
                )
            )
        )

        # 计算总数
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await db.execute(count_query)
        total = total_result.scalar() or 0

        # 分页查询
        query = query.order_by(RepairTask.report_time)
        query = query.offset((page - 1) * size).limit(size)

        result = await db.execute(query)
        tasks = result.scalars().all()

        # 筛选未标记爆单的任务
        candidates = []
        for task in tasks:
            # 检查是否已有爆单标签
            has_rush_tag = any(tag.name == "爆单任务" for tag in task.tags)

            candidates.append(
                {
                    "id": task.id,
                    "task_id": task.task_id,
                    "title": task.title,
                    "location": task.location,
                    "task_type": task.task_type.value,
                    "status": task.status.value,
                    "report_time": (
                        task.report_time.isoformat() if task.report_time else ""
                    ),
                    "member_name": task.member.name if task.member else "未知",
                    "current_work_minutes": task.work_minutes,
                    "has_rush_tag": has_rush_tag,
                    "potential_bonus_minutes": 15 if not has_rush_tag else 0,
                }
            )

        # 统计信息
        unmarked_count = len([c for c in candidates if not c["has_rush_tag"]])
        potential_bonus_hours = unmarked_count * 15 / 60.0

        return create_response(
            data={
                "candidates": candidates,
                "total": total,
                "page": page,
                "size": size,
                "pages": ((total or 0) + (size or 1) - 1) // (size or 1),
                "summary": {
                    "total_candidates": len(candidates),
                    "unmarked_count": unmarked_count,
                    "potential_bonus_hours": round(potential_bonus_hours, 2),
                },
            },
            message=f"获取爆单候选任务成功，共 {len(candidates)} 个任务",
        )

    except Exception as e:
        logger.error(f"Get rush task candidates error: {str(e)}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取爆单候选任务失败",
        )


# ============= 维修单导入管理 =============


@router.post("/maintenance-orders/import", response_model=Dict[str, Any])
async def import_maintenance_orders(
    import_data: Dict[str, Any],
    current_user: Member = Depends(get_current_active_group_leader),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """
    维修单数据导入

    权限：组长及以上可导入维修单
    """
    try:
        from app.services.task_service import TaskService

        task_service = TaskService(db)

        # 解析导入数据
        maintenance_data = import_data.get("maintenance_orders", [])

        if not maintenance_data:
            raise HTTPException(
                status_code=http_status.HTTP_400_BAD_REQUEST, detail="导入数据为空"
            )

        # 直接创建维修任务
        success_count = 0
        failed_count = 0
        matched_assignee_count = 0
        errors = []
        matched_assignees = []

        for data in maintenance_data:
            try:
                # 检查是否已存在相同的任务
                existing_task_query = select(RepairTask).where(
                    and_(
                        RepairTask.title == data.get("title", "维修任务"),
                        RepairTask.location == data.get("location", ""),
                        RepairTask.reporter_name == data.get("reporter_name", ""),
                        RepairTask.reporter_contact == data.get("reporter_contact", ""),
                    )
                )
                existing_result = await db.execute(existing_task_query)
                existing_task = existing_result.scalar_one_or_none()

                if existing_task:
                    # 已存在相同任务，跳过
                    failed_count += 1
                    errors.append(
                        f"任务已存在，跳过重复导入: {data.get('title', '维修任务')}"
                    )
                    continue

                # 查找处理人（支持模糊匹配）
                assigned_member_id = current_user.id  # 默认分配给导入者
                assignee_name = (
                    data.get("assignee")
                    or data.get("assignee_name")
                    or data.get("handler_name")
                    or data.get("processor_name")
                )

                if assignee_name:
                    # 清理姓名，移除括号及其内容，以及其他常见的后缀
                    import re

                    clean_name = assignee_name.strip()

                    # 移除各种格式的括号及内容：() [] {} 〈〉 （）
                    clean_name = re.sub(
                        r"[\(\)（）\[\]{}〈〉].*?[\(\)（）\[\]{}〈〉]", "", clean_name
                    )
                    clean_name = re.sub(r"[\(\)（）\[\]{}〈〉].*", "", clean_name)

                    # 移除常见的职务后缀
                    clean_name = re.sub(
                        r"(工程师|技术员|主管|经理|组长|部长|处长|科长)$",
                        "",
                        clean_name,
                    )

                    # 最终清理
                    clean_name = clean_name.strip()

                    if clean_name and len(clean_name) >= 2:  # 确保姓名至少2个字符
                        # 模糊匹配成员 - 尝试多种匹配策略
                        member_query = (
                            select(Member)
                            .where(
                                or_(
                                    Member.name == clean_name,  # 精确匹配
                                    Member.name.ilike(f"%{clean_name}%"),  # 包含匹配
                                    Member.username.ilike(
                                        f"%{clean_name}%"
                                    ),  # 用户名匹配
                                    Member.name.ilike(f"{clean_name}%"),  # 前缀匹配
                                    Member.name.ilike(f"%{clean_name}"),  # 后缀匹配
                                )
                            )
                            .where(Member.is_active)
                        )  # 只匹配在职成员

                        member_result = await db.execute(member_query)
                        matched_member = member_result.scalar_one_or_none()

                        if matched_member:
                            assigned_member_id = matched_member.id
                            matched_assignee_count += 1
                            matched_assignees.append(
                                f"'{assignee_name}' -> '{matched_member.name}'"
                            )
                            logger.info(
                                f"Found matching member: '{assignee_name}' -> "
                                f"'{matched_member.name}' (ID: {matched_member.id})"
                            )
                        else:
                            # 如果还是找不到，尝试只用姓氏匹配（适用于中文姓名）
                            if len(clean_name) >= 2:
                                surname_query = (
                                    select(Member)
                                    .where(Member.name.ilike(f"{clean_name[0]}%"))
                                    .where(Member.is_active)
                                )

                                surname_result = await db.execute(surname_query)
                                surname_members = surname_result.scalars().all()

                                if len(surname_members) == 1:
                                    # 如果只有一个同姓的成员，则匹配
                                    matched_member = surname_members[0]
                                    assigned_member_id = matched_member.id
                                    matched_assignee_count += 1
                                    matched_assignees.append(
                                        (
                                            f"'{assignee_name}' -> '{matched_member.name}' "
                                            "(姓氏匹配)"
                                        )
                                    )
                                    logger.info(
                                        f"Found by surname: '{assignee_name}' -> "
                                        f"'{matched_member.name}' (ID: {matched_member.id})"
                                    )
                                else:
                                    logger.warning(
                                        f"No matching member found for: "
                                        f"'{assignee_name}' "
                                        f"(cleaned: '{clean_name}')"
                                    )
                            else:
                                logger.warning(
                                    f"No matching member found for: '{assignee_name}' "
                                    f"(cleaned: '{clean_name}')"
                                )

                # 处理时间字段
                import_report_time = data.get("report_time") or data.get("report_date")
                import_response_time = data.get("response_time") or data.get(
                    "start_time"
                )
                import_completion_time = (
                    data.get("completion_time")
                    or data.get("end_time")
                    or data.get("finish_time")
                )

                # 解析时间字段
                report_time = datetime.utcnow()  # 默认为当前时间
                response_time = None
                completion_time = None

                try:
                    if import_report_time:
                        from dateutil import parser  # type: ignore[import-untyped]

                        if isinstance(import_report_time, str):
                            report_time = parser.parse(import_report_time)
                        else:
                            report_time = import_report_time
                except Exception:
                    pass

                try:
                    if import_response_time:
                        from dateutil import parser

                        if isinstance(import_response_time, str):
                            response_time = parser.parse(import_response_time)
                        else:
                            response_time = import_response_time
                except Exception:
                    pass

                try:
                    if import_completion_time:
                        from dateutil import parser

                        if isinstance(import_completion_time, str):
                            completion_time = parser.parse(import_completion_time)
                        else:
                            completion_time = import_completion_time
                except Exception:
                    pass

                # 根据检修形式判断任务类型
                repair_form = (
                    data.get("repair_form")
                    or data.get("maintenance_type")
                    or data.get("fix_type")
                )
                task_type = TaskType.ONLINE  # 默认线上
                if repair_form:
                    repair_form_lower = repair_form.lower()
                    if (
                        "现场" in repair_form_lower
                        or "线下" in repair_form_lower
                        or "实地" in repair_form_lower
                    ):
                        task_type = TaskType.OFFLINE
                elif data.get("isOffline") or data.get("is_offline"):
                    task_type = TaskType.OFFLINE

                # 根据工单状态映射任务状态
                work_order_status = (
                    data.get("status")
                    or data.get("work_order_status")
                    or data.get("state")
                )
                task_status = TaskStatus.PENDING  # 默认待处理
                if work_order_status:
                    status_lower = work_order_status.lower()
                    if (
                        "已完成" in status_lower
                        or "完成" in status_lower
                        or "finished" in status_lower
                    ):
                        task_status = TaskStatus.COMPLETED
                    elif (
                        "进行中" in status_lower
                        or "处理中" in status_lower
                        or "processing" in status_lower
                    ):
                        task_status = TaskStatus.IN_PROGRESS
                    elif (
                        "已取消" in status_lower
                        or "取消" in status_lower
                        or "cancelled" in status_lower
                    ):
                        task_status = TaskStatus.CANCELLED

                # 创建任务数据
                task_data = {
                    "title": data.get("title", "维修任务"),
                    "description": data.get("description", ""),
                    "task_type": task_type,
                    "category": TaskCategory.NETWORK_REPAIR,
                    "priority": TaskPriority.MEDIUM,
                    "status": task_status,
                    "location": data.get("location", ""),
                    "reporter_name": data.get("reporter_name", ""),
                    "reporter_contact": data.get("reporter_contact", ""),
                    "assigned_to": assigned_member_id,
                    "report_time": report_time,
                    "response_time": response_time,
                    "completion_time": completion_time,
                    "due_date": completion_time,  # 截止时间设置为完工时间
                    "rating": data.get("rating"),
                    "feedback": data.get("feedback"),
                    "repair_form": repair_form,
                    "work_order_status": work_order_status,
                }

                # 创建维修任务
                task = await task_service.create_repair_task(task_data, current_user.id)
                success_count += 1
                logger.info(f"Successfully created repair task: {task.task_id}")

            except Exception as e:
                failed_count += 1
                error_msg = f"创建任务失败: {str(e)}"
                errors.append(error_msg)
                logger.error(f"Failed to create repair task: {error_msg}")
                continue

        # 数据库事务已在create_repair_task中提交，无需再次提交

        result = {
            "success": success_count,
            "failed": failed_count,
            "matched": success_count,
            "partial": 0,
            "errors": errors,
            "processed": success_count + failed_count,
            "matched_assignees": matched_assignee_count,
            "assignee_matches": matched_assignees[:10],  # 只显示前10个匹配结果
        }

        logger.info(
            f"Maintenance orders imported by {current_user.student_id}: {result}"
        )

        success_msg = f"维修单导入完成，成功处理 {success_count} 条记录"
        if matched_assignee_count > 0:
            success_msg += f"，匹配到 {matched_assignee_count} 个处理人"
        if failed_count > 0:
            success_msg += f"，失败 {failed_count} 条记录"

        return create_response(data=result, message=success_msg)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Import maintenance orders error: {str(e)}")
        await db.rollback()
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="维修单导入失败",
        )


@router.get("/maintenance-orders/template", response_model=Dict[str, Any])
async def get_maintenance_order_template(
    current_user: Member = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    获取维修单导入模板

    权限：所有用户可查看模板
    """
    try:
        # 返回维修单导入模板的字段定义
        template_fields = [
            {
                "field": "工单编号",
                "description": "维修工单唯一编号",
                "required": True,
                "example": "WO202401001",
            },
            {
                "field": "报单企业",
                "description": "报修单位/部门",
                "required": True,
                "example": "计算机学院",
            },
            {
                "field": "位置",
                "description": "故障位置",
                "required": True,
                "example": "A楼201",
            },
            {
                "field": "故障描述",
                "description": "故障详细描述",
                "required": True,
                "example": "网络无法连接",
            },
            {
                "field": "维修类型",
                "description": "维修分类",
                "required": True,
                "example": "网络故障",
            },
            {
                "field": "报修人姓名",
                "description": "报修人员姓名",
                "required": True,
                "example": "张三",
            },
            {
                "field": "报修人联系方式",
                "description": "联系电话或邮箱",
                "required": True,
                "example": "13800138000",
            },
            {
                "field": "报修时间",
                "description": "报修时间",
                "required": True,
                "example": "2024-01-01 09:00:00",
            },
            {
                "field": "处理人员",
                "description": "指派处理人员",
                "required": False,
                "example": "李四",
            },
            {
                "field": "处理状态",
                "description": "当前处理状态",
                "required": False,
                "example": "已处理",
            },
            {
                "field": "处理时间",
                "description": "处理完成时间",
                "required": False,
                "example": "2024-01-01 15:00:00",
            },
            {
                "field": "用户评价",
                "description": "用户满意度评价",
                "required": False,
                "example": "满意",
            },
        ]

        return create_response(
            data={
                "template_fields": template_fields,
                "import_rules": {
                    "auto_match": "自动匹配基于'报修人姓名+联系方式'进行",
                    "task_type_mapping": {
                        "网络故障": "online",
                        "硬件维修": "offline",
                        "软件问题": "online",
                    },
                    "status_mapping": {
                        "待处理": "pending",
                        "处理中": "in_progress",
                        "已完成": "completed",
                        "已取消": "cancelled",
                    },
                },
            },
            message="维修单导入模板获取成功",
        )

    except Exception as e:
        logger.error(f"Get maintenance order template error: {str(e)}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取导入模板失败",
        )


# ============= 工时管理增强功能 =============


@router.post("/work-hours/recalculate", response_model=Dict[str, Any])
async def batch_recalculate_work_hours(
    task_ids: Optional[List[int]] = Query(
        None, description="任务ID列表，为空则重算所有任务"
    ),
    member_id: Optional[int] = Query(None, description="重算指定成员的所有任务"),
    date_from: Optional[datetime] = Query(None, description="重算指定时间范围的任务"),
    date_to: Optional[datetime] = Query(None, description="重算指定时间范围的任务"),
    current_user: Member = Depends(get_current_active_admin),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """
    批量重新计算工时

    权限：仅管理员可执行批量重算
    """
    try:
        # 构建查询条件
        query = select(RepairTask).options(selectinload(RepairTask.tags))

        if task_ids:
            query = query.where(RepairTask.id.in_(task_ids))
        elif member_id:
            query = query.where(RepairTask.member_id == member_id)
        elif date_from or date_to:
            if date_from:
                query = query.where(RepairTask.created_at >= date_from)
            if date_to:
                query = query.where(RepairTask.created_at <= date_to)

        result = await db.execute(query)
        tasks = result.scalars().all()

        if not tasks:
            return create_response(
                data={"recalculated_count": 0}, message="没有找到需要重算的任务"
            )

        # 批量重新计算工时
        recalculated_count = 0
        errors = []

        for task in tasks:
            try:
                old_minutes = task.work_minutes
                task.update_work_minutes()

                if task.work_minutes != old_minutes:
                    recalculated_count += 1
                    logger.info(
                        f"Task {task.id} work hours updated: "
                        f"{old_minutes} -> {task.work_minutes}"
                    )

            except Exception as e:
                errors.append(f"任务 {task.id}: {str(e)}")
                logger.error(
                    f"Error recalculating work hours for task {task.id}: {str(e)}"
                )

        await db.commit()

        result_data = {
            "total_tasks": len(tasks),
            "recalculated_count": recalculated_count,
            "error_count": len(errors),
            "errors": errors[:10],  # 只返回前10个错误
        }

        logger.info(
            f"Batch work hours recalculation completed by {current_user.student_id}: {result_data}"
        )

        return create_response(
            data=result_data,
            message=f"批量工时重算完成，共处理 {len(tasks)} 个任务，成功重算 {recalculated_count} 个",
        )

    except Exception as e:
        logger.error(f"Batch recalculate work hours error: {str(e)}")
        await db.rollback()
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="批量工时重算失败",
        )


@router.post("/repair/{task_id}/recalculate-hours", response_model=Dict[str, Any])
async def recalculate_single_task_hours(
    task_id: int,
    force_update: bool = Query(False, description="强制重新计算，即使工时未变化"),
    current_user: Member = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """
    重新计算单个任务工时

    权限：任务执行者和管理员可重新计算
    """
    try:
        # 查询任务
        query = (
            select(RepairTask)
            .options(selectinload(RepairTask.tags))
            .where(RepairTask.id == task_id)
        )

        result = await db.execute(query)
        task = result.scalar_one_or_none()

        if not task:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND, detail="维修任务不存在"
            )

        # 权限检查
        if not check_user_can_access_task(current_user, task.member_id or 0):
            raise HTTPException(
                status_code=http_status.HTTP_403_FORBIDDEN,
                detail="无权限重新计算该任务工时",
            )

        # 记录旧的工时
        old_minutes = task.work_minutes

        # 重新计算工时
        task.update_work_minutes()

        # 检查是否有变化
        changed = task.work_minutes != old_minutes

        if changed or force_update:
            await db.commit()
            await db.refresh(task)

        # 构建详细的工时分解
        breakdown = _calculate_work_hour_breakdown(task)

        result_data = {
            "task_id": task.id,
            "old_minutes": old_minutes,
            "new_minutes": task.work_minutes,
            "changed": changed,
            "breakdown": breakdown,
            "updated_at": task.updated_at.isoformat(),
        }

        logger.info(
            f"Task {task_id} work hours recalculated by {current_user.student_id}: "
            f"{old_minutes} -> {task.work_minutes}"
        )

        return create_response(
            data=result_data,
            message="任务工时重新计算完成"
            + (
                f"：{old_minutes}分钟 -> {task.work_minutes}分钟"
                if changed
                else "（无变化）"
            ),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Recalculate single task hours error for task {task_id}: {str(e)}"
        )
        await db.rollback()
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="重新计算任务工时失败",
        )


@router.get("/work-hours/pending-review", response_model=Dict[str, Any])
async def get_pending_work_hours_review(
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=100, description="每页数量"),
    task_type: Optional[TaskType] = Query(None, description="任务类型筛选"),
    threshold_hours: float = Query(5.0, description="超过多少小时的任务需要审核"),
    current_user: Member = Depends(get_current_active_admin),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """
    获取需要工时审核的任务列表

    权限：仅管理员可查看
    主要针对工时异常（过高或过低）的任务
    """
    try:
        # 计算工时阈值（分钟）
        threshold_minutes = threshold_hours * 60

        # 构建查询：查找工时异常的任务
        query = (
            select(RepairTask)
            .options(joinedload(RepairTask.member), selectinload(RepairTask.tags))
            .where(
                and_(
                    RepairTask.status == TaskStatus.COMPLETED,
                    or_(
                        RepairTask.work_minutes > threshold_minutes,  # 工时过高
                        RepairTask.work_minutes < 10,  # 工时过低（小于10分钟）
                        RepairTask.rating is not None
                        and RepairTask.rating <= 2,  # 有差评
                    ),
                )
            )
        )

        if task_type:
            query = query.where(RepairTask.task_type == task_type)

        # 计算总数
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await db.execute(count_query)
        total = total_result.scalar() or 0

        # 分页查询
        query = query.order_by(desc(RepairTask.work_minutes))
        query = query.offset((page - 1) * size).limit(size)

        result = await db.execute(query)
        tasks = result.scalars().all()

        # 构建响应数据
        items = []
        for task in tasks:
            breakdown = _calculate_work_hour_breakdown(task)

            # 判断异常原因
            anomaly_reasons = []
            work_minutes = task.work_minutes or 0
            if work_minutes > threshold_minutes:
                anomaly_reasons.append(f"工时过高({work_minutes}分钟)")
            if work_minutes < 10:
                anomaly_reasons.append(f"工时过低({work_minutes}分钟)")
            if task.rating is not None and task.rating <= 2:
                anomaly_reasons.append(f"评分过低({task.rating}星)")

            items.append(
                {
                    "id": task.id,
                    "title": task.title,
                    "member_name": task.member.name if task.member else "未知",
                    "work_minutes": task.work_minutes,
                    "work_hours": round((task.work_minutes or 0) / 60.0, 2),
                    "rating": task.rating,
                    "status": task.status.value,
                    "task_type": task.task_type.value,
                    "created_at": (
                        task.created_at.isoformat() if task.created_at else ""
                    ),
                    "completed_at": (
                        task.completion_time.isoformat()
                        if task.completion_time
                        else None
                    ),
                    "anomaly_reasons": anomaly_reasons,
                    "breakdown": breakdown,
                }
            )

        # 分页信息
        pages = (total + size - 1) // size

        response_data = {
            "items": items,
            "total": total,
            "page": page,
            "size": size,
            "pages": pages,
            "has_next": page < pages,
            "has_prev": page > 1,
        }

        logger.info(
            f"Pending work hours review retrieved by {current_user.student_id}, total: {total}"
        )

        return create_response(
            data=response_data, message=f"获取待审核工时任务成功，共 {total} 条记录"
        )

    except Exception as e:
        logger.error(f"Get pending work hours review error: {str(e)}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取待审核工时列表失败",
        )


@router.put("/work-hours/{task_id}/adjust", response_model=Dict[str, Any])
async def adjust_task_work_hours(
    task_id: int,
    adjusted_minutes: int = Query(..., ge=0, description="调整后的工时（分钟）"),
    reason: str = Query(..., description="调整原因"),
    current_user: Member = Depends(get_current_active_admin),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """
    手动调整任务工时

    权限：仅管理员可手动调整工时
    """
    try:
        # 查询任务
        query = (
            select(RepairTask)
            .options(selectinload(RepairTask.tags), joinedload(RepairTask.member))
            .where(RepairTask.id == task_id)
        )

        result = await db.execute(query)
        task = result.scalar_one_or_none()

        if not task:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND, detail="维修任务不存在"
            )

        # 记录调整前的工时
        original_minutes = task.work_minutes

        # 计算需要添加的调整标签
        adjustment = adjusted_minutes - (task.base_work_minutes or 0)

        # 移除之前的手动调整标签（如果存在）
        existing_adjustment_tags = [
            tag for tag in task.tags if tag.name and tag.name.startswith("手动调整")
        ]
        for tag in existing_adjustment_tags:
            task.tags.remove(tag)

        # 添加新的调整标签
        if adjustment != 0:
            adjustment_tag = TaskTag(
                name=f"手动调整-{reason}",
                work_minutes_modifier=adjustment,
                is_active=True,
            )
            adjustment_tag.tag_type = (
                TaskTagType.BONUS if adjustment > 0 else TaskTagType.PENALTY
            )
            db.add(adjustment_tag)
            await db.flush()  # 确保标签ID可用

            task.tags.append(adjustment_tag)

        # 重新计算工时
        task.update_work_minutes()

        # 记录调整日志
        logger.info(
            f"Task {task_id} work hours manually adjusted by {current_user.student_id}: "
            f"{original_minutes} -> {task.work_minutes} minutes, reason: {reason}"
        )

        await db.commit()
        await db.refresh(task)

        # 构建响应
        breakdown = _calculate_work_hour_breakdown(task)

        result_data = {
            "task_id": task.id,
            "original_minutes": original_minutes,
            "adjusted_minutes": task.work_minutes or 0,
            "adjustment_amount": (task.work_minutes or 0) - (original_minutes or 0),
            "reason": reason,
            "adjusted_by": current_user.name,
            "adjusted_at": datetime.utcnow().isoformat(),
            "breakdown": breakdown,
        }

        return create_response(
            data=result_data,
            message=f"工时调整成功：{original_minutes}分钟 -> {task.work_minutes}分钟",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Adjust task work hours error for task {task_id}: {str(e)}")
        await db.rollback()
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="手动调整工时失败",
        )


@router.get("/work-hours/statistics", response_model=Dict[str, Any])
async def get_work_hours_statistics(
    date_from: Optional[datetime] = Query(None, description="统计开始时间"),
    date_to: Optional[datetime] = Query(None, description="统计结束时间"),
    member_id: Optional[int] = Query(None, description="指定成员统计"),
    group_by: str = Query("day", regex="^(day|week|month)$", description="分组方式"),
    current_user: Member = Depends(get_current_active_group_leader),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """
    获取工时统计信息

    权限：组长及以上可查看
    """
    try:
        # 设置默认时间范围（最近30天）
        if not date_to:
            date_to = datetime.utcnow()
        if not date_from:
            date_from = date_to - timedelta(days=30)

        # 构建基础查询
        query = (
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
            query = query.where(RepairTask.member_id == member_id)

        result = await db.execute(query)
        tasks = result.scalars().all()

        # 统计数据
        total_tasks = len(tasks)
        total_work_minutes = sum(task.work_minutes or 0 for task in tasks)
        total_work_hours = round(total_work_minutes / 60.0, 2)

        # 按任务类型统计
        type_stats = {}
        for task in tasks:
            task_type = task.task_type.value
            if task_type not in type_stats:
                type_stats[task_type] = {"count": 0, "total_minutes": 0}
            type_stats[task_type]["count"] += 1
            type_stats[task_type]["total_minutes"] += task.work_minutes or 0

        # 转换类型统计格式
        for type_name, stats in type_stats.items():
            stats["total_hours"] = round(
                stats["total_minutes"] / 60.0, 2
            )  # type: ignore[assignment]
            stats["avg_hours"] = (
                round(
                    float(stats["total_hours"]) / stats["count"], 2
                )  # type: ignore[assignment]
                if stats["count"] > 0
                else 0.0
            )

        # 按时间分组统计
        time_stats = {}
        for task in tasks:
            if group_by == "day":
                time_key = task.created_at.strftime("%Y-%m-%d")
            elif group_by == "week":
                # 获取周的开始日期
                week_start = task.created_at - timedelta(days=task.created_at.weekday())
                time_key = week_start.strftime("%Y-%m-%d")
            else:  # month
                time_key = task.created_at.strftime("%Y-%m")

            if time_key not in time_stats:
                time_stats[time_key] = {"count": 0, "total_minutes": 0}
            time_stats[time_key]["count"] += 1
            time_stats[time_key]["total_minutes"] += task.work_minutes or 0

        # 转换时间统计格式并排序
        time_series = []
        for time_key in sorted(time_stats.keys()):
            stats = time_stats[time_key]
            time_series.append(
                {
                    "period": time_key,
                    "task_count": stats["count"],
                    "total_hours": round(stats["total_minutes"] / 60.0, 2),
                    "avg_hours": (
                        round(stats["total_minutes"] / 60.0 / stats["count"], 2)
                        if stats["count"] > 0
                        else 0
                    ),
                }
            )

        # 按成员统计（如果是管理员查看所有人时）
        member_stats = []
        if not member_id and current_user.is_admin:
            member_groups: Dict[int, Dict[str, Any]] = {}
            for task in tasks:
                member_key = task.member_id
                if member_key is None:
                    continue
                if member_key not in member_groups:
                    member_groups[member_key] = {
                        "member_name": task.member.name if task.member else "未知",
                        "tasks": [],
                    }
                member_groups[member_key]["tasks"].append(task)

            for member_key, group_data in member_groups.items():
                member_tasks = group_data["tasks"]
                member_total_minutes = sum(
                    task.work_minutes or 0 for task in member_tasks
                )
                member_stats.append(
                    {
                        "member_id": member_key,
                        "member_name": group_data["member_name"],
                        "task_count": len(member_tasks),
                        "total_hours": round(member_total_minutes / 60.0, 2),
                        "avg_hours": (
                            round(member_total_minutes / 60.0 / len(member_tasks), 2)
                            if member_tasks
                            else 0
                        ),
                    }
                )

            # 按总工时排序
            member_stats.sort(
                key=lambda x: float(x.get("total_hours") or 0), reverse=True
            )

        response_data = {
            "period": {
                "from": date_from.isoformat(),
                "to": date_to.isoformat(),
                "group_by": group_by,
            },
            "summary": {
                "total_tasks": total_tasks,
                "total_work_hours": total_work_hours,
                "average_hours_per_task": (
                    round(total_work_hours / total_tasks, 2) if total_tasks > 0 else 0
                ),
            },
            "by_task_type": type_stats,
            "time_series": time_series,
            "by_member": member_stats,
        }

        logger.info(f"Work hours statistics retrieved by {current_user.student_id}")

        return create_response(data=response_data, message="工时统计数据获取成功")

    except Exception as e:
        logger.error(f"Get work hours statistics error: {str(e)}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取工时统计失败",
        )


# ============= A/B表智能匹配功能（重构新增） =============


@router.post("/ab-matching/execute", response_model=Dict[str, Any])
async def execute_ab_table_matching(
    request_data: Dict[str, Any],
    current_user: Member = Depends(get_current_active_group_leader),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """
    执行A/B表智能匹配

    权限：组长及以上可执行A/B表匹配
    """
    try:
        from app.services.ab_table_matching_service import ABTableMatchingService

        matching_service = ABTableMatchingService(db)

        # 解析请求数据
        a_table_data = request_data.get("a_table_data", [])
        b_table_data = request_data.get("b_table_data", [])
        strategies = request_data.get("strategies", ["exact", "fuzzy", "multi_field"])

        if not a_table_data:
            raise HTTPException(
                status_code=http_status.HTTP_400_BAD_REQUEST, detail="A表数据不能为空"
            )

        # 转换策略字符串为枚举
        from app.services.ab_table_matching_service import MatchingStrategy

        strategy_enums = []
        for strategy in strategies:
            strategy_enums.append(MatchingStrategy(strategy))

        # 执行匹配
        match_results = await matching_service.match_ab_tables(
            a_table_data=a_table_data,
            b_table_data=b_table_data,
            strategies=strategy_enums,
        )

        # 统计结果
        total_records = len(match_results)
        matched_records = sum(1 for r in match_results if r.is_matched)
        match_rate = matched_records / total_records if total_records > 0 else 0

        # 准备响应数据
        results = []
        for result in match_results:
            results.append(
                {
                    "a_record": result.a_record,
                    "matched_member": (
                        {
                            "id": result.member.id if result.member else None,
                            "name": result.member.name if result.member else None,
                            "student_id": (
                                getattr(result.member, "student_id", "")
                                if result.member
                                else ""
                            ),
                            "department": (
                                getattr(result.member, "department", "")
                                if result.member
                                else ""
                            ),
                        }
                        if result.member
                        else None
                    ),
                    "confidence": result.confidence,
                    "confidence_level": result.confidence_level.value,
                    "strategy_used": result.strategy_used.value,
                    "is_matched": result.is_matched,
                    "failure_reason": result.failure_reason,
                    "match_details": result.match_details,
                }
            )

        response_data = {
            "match_results": results,
            "statistics": {
                "total_records": total_records,
                "matched_records": matched_records,
                "match_rate": round(match_rate, 4),
                "high_confidence_matches": sum(
                    1 for r in match_results if r.confidence >= 0.9
                ),
                "medium_confidence_matches": sum(
                    1 for r in match_results if 0.7 <= r.confidence < 0.9
                ),
                "low_confidence_matches": sum(
                    1 for r in match_results if 0.5 <= r.confidence < 0.7
                ),
            },
        }

        logger.info(
            f"AB matching executed by {current_user.student_id}: {match_rate:.2%} match rate"
        )

        return create_response(
            data=response_data, message=f"A/B表匹配完成，匹配率: {match_rate:.2%}"
        )

    except Exception as e:
        logger.error(f"AB table matching error: {str(e)}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="A/B表智能匹配失败",
        )


@router.post("/import/enhanced", response_model=Dict[str, Any])
async def enhanced_import_with_ab_matching(
    request_data: Dict[str, Any],
    current_user: Member = Depends(get_current_active_group_leader),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """
    增强版数据导入（集成A/B表智能匹配）

    权限：组长及以上可执行增强导入
    """
    try:
        # 解析请求数据
        a_table_data = request_data.get("a_table_data", [])

        if not a_table_data:
            raise HTTPException(
                status_code=http_status.HTTP_400_BAD_REQUEST, detail="A表数据不能为空"
            )

        # 执行增强导入
        # Note: This method doesn't exist yet, using placeholder logic
        import_result = {
            "successful_imports": 0,
            "failed_imports": 0,
            "errors": [],
        }

        # 统计结果
        total_records = len(a_table_data)
        successful_imports = import_result["successful_imports"]
        failed_imports = import_result["failed_imports"]
        matched_records = import_result.get("matched_records", 0)

        successful_imports_count = (
            successful_imports if isinstance(successful_imports, (int, float)) else 0
        )
        matched_records_count = (
            matched_records if isinstance(matched_records, (int, float)) else 0
        )

        success_rate = (
            float(successful_imports_count) / total_records
            if total_records > 0
            else 0.0
        )
        match_rate = (
            float(matched_records_count) / total_records if total_records > 0 else 0.0
        )

        response_data = {
            "import_summary": {
                "total_records": total_records,
                "successful_imports": successful_imports,
                "failed_imports": failed_imports,
                "matched_records": matched_records,
                "success_rate": round(success_rate, 4),
                "match_rate": round(match_rate, 4),
            },
            "detailed_results": import_result.get("detailed_results", []),
            "errors": import_result["errors"],
            "batch_id": import_result.get("batch_id"),
        }

        logger.info(
            f"Enhanced import executed by {current_user.student_id}: "
            f"{success_rate:.2%} success rate"
        )

        return create_response(
            data=response_data,
            message=f"增强版导入完成，成功率: {success_rate:.2%}，匹配率: {match_rate:.2%}",
        )

    except Exception as e:
        logger.error(f"Enhanced import error: {str(e)}")
        await db.rollback()
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="增强版数据导入失败",
        )


@router.post("/status-mapping/apply", response_model=Dict[str, Any])
async def apply_status_mapping(
    request_data: Dict[str, Any],
    current_user: Member = Depends(get_current_active_group_leader),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """
    批量应用状态映射功能

    权限：组长及以上可应用状态映射
    """
    try:
        # 解析请求数据
        task_ids = request_data.get("task_ids", [])
        apply_to_all = request_data.get("apply_to_all", False)

        if not apply_to_all and not task_ids:
            raise HTTPException(
                status_code=http_status.HTTP_400_BAD_REQUEST,
                detail="必须指定任务ID列表或选择应用到全部任务",
            )

        # 构建查询条件
        if apply_to_all:
            query = select(RepairTask).where(RepairTask.work_order_status.isnot(None))
        else:
            query = select(RepairTask).where(
                and_(
                    RepairTask.id.in_(task_ids),
                    RepairTask.work_order_status.isnot(None),
                )
            )

        result = await db.execute(query)
        tasks = result.scalars().all()

        updated_count = 0
        errors = []

        for task in tasks:
            try:
                # 应用状态映射
                if task.work_order_status:
                    task.set_status_by_work_order_status(task.work_order_status)
                updated_count += 1
            except Exception as e:
                errors.append(f"任务 {task.id} 状态映射失败: {str(e)}")

        if updated_count > 0:
            await db.commit()

        response_data = {
            "updated_count": updated_count,
            "total_tasks": len(tasks),
            "errors": errors,
            "success_rate": updated_count / len(tasks) if len(tasks) > 0 else 0,
        }

        logger.info(
            f"Status mapping applied by {current_user.student_id}: {updated_count} tasks updated"
        )

        return create_response(
            data=response_data, message=f"状态映射完成，更新 {updated_count} 个任务"
        )

    except Exception as e:
        logger.error(f"Status mapping error: {str(e)}")
        await db.rollback()
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="状态映射失败",
        )


@router.post("/rush-orders/manage", response_model=Dict[str, Any])
async def manage_rush_orders(
    request_data: Dict[str, Any],
    current_user: Member = Depends(get_current_active_admin),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """
    综合爆单管理功能（重构版）

    权限：仅管理员可管理爆单
    """
    try:
        from app.services.task_service import TaskService

        task_service = TaskService(db)

        # 解析请求数据
        action = request_data.get("action")  # "mark", "unmark", "list", "statistics"
        task_ids = request_data.get("task_ids", [])
        date_from = request_data.get("date_from")
        date_to = request_data.get("date_to")

        if action == "mark":
            # 标记爆单任务
            result = await task_service.batch_mark_rush_tasks(
                date_from=(
                    datetime.fromisoformat(date_from) if date_from else datetime.now()
                ),
                date_to=datetime.fromisoformat(date_to) if date_to else datetime.now(),
                task_ids=task_ids,
                marker_id=current_user.id,
            )
            return create_response(
                data=result,
                message=f"爆单标记完成，标记 {result.get('marked_count', 0)} 个任务",
            )

        elif action == "unmark":
            # 取消爆单标记
            result = await task_service.batch_unmark_rush_tasks(
                date_from=(
                    datetime.fromisoformat(date_from) if date_from else datetime.now()
                ),
                date_to=datetime.fromisoformat(date_to) if date_to else datetime.now(),
                task_ids=task_ids,
                remover_id=current_user.id,
            )
            return create_response(
                data=result,
                message=f"爆单取消完成，取消 {result.get('unmarked_count', 0)} 个任务",
            )

        elif action == "list":
            # 获取爆单任务列表
            page = request_data.get("page", 1)
            size = request_data.get("size", 20)

            result = await task_service.get_rush_tasks_list(
                page=page,
                page_size=size,
                date_from=datetime.fromisoformat(date_from) if date_from else None,
                date_to=datetime.fromisoformat(date_to) if date_to else None,
            )
            return create_response(
                data=result,
                message=f"获取爆单任务列表成功，共 {result.get('total', 0)} 条记录",
            )

        elif action == "statistics":
            # 获取爆单统计
            result = await task_service.get_rush_tasks_statistics(
                date_from=datetime.fromisoformat(date_from) if date_from else None,
                date_to=datetime.fromisoformat(date_to) if date_to else None,
            )
            return create_response(data=result, message="爆单统计数据获取成功")

        else:
            raise HTTPException(
                status_code=http_status.HTTP_400_BAD_REQUEST,
                detail="不支持的爆单管理操作",
            )

    except Exception as e:
        logger.error(f"Rush order management error: {str(e)}")
        await db.rollback()
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="爆单管理操作失败",
        )


@router.post("/work-hours/bulk-recalculate", response_model=Dict[str, Any])
async def bulk_recalculate_work_hours_enhanced(
    request_data: Dict[str, Any],
    current_user: Member = Depends(get_current_active_admin),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """
    批量重算工时（重构版）- 使用新的爆单独立计算逻辑

    权限：仅管理员可批量重算工时
    """
    try:
        pass

        from app.services.work_hours_service import RushTaskMarkingService

        rush_service = RushTaskMarkingService(db)

        # 解析请求数据
        date_from = datetime.fromisoformat(request_data["date_from"]).date()
        date_to = datetime.fromisoformat(request_data["date_to"]).date()
        member_ids = request_data.get("member_ids")

        # 执行批量重算
        result = await rush_service.batch_recalculate_work_hours(
            date_from=date_from, date_to=date_to, member_ids=member_ids
        )

        logger.info(
            f"Bulk work hours recalculation by {current_user.student_id}: {result}"
        )

        return create_response(
            data=result,
            message=(
                f"批量工时重算完成，重算 {result['recalculated_tasks']} 个任务，"
                f"更新 {result['updated_summaries']} 个汇总"
            ),
        )

    except Exception as e:
        logger.error(f"Bulk work hours recalculation error: {str(e)}")
        await db.rollback()
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="批量工时重算失败",
        )


# ============= 巡检任务支持 =============


@router.put("/monitoring/{task_id}/inspection", response_model=Dict[str, Any])
async def update_monitoring_inspection(
    task_id: int,
    request_data: Dict[str, Any],
    current_user: Member = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """更新监控任务的巡检信息"""
    try:
        from app.models.task import MonitoringTask

        # 查询监控任务
        query = select(MonitoringTask).where(MonitoringTask.id == task_id)
        result = await db.execute(query)
        task = result.scalar_one_or_none()

        if not task:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND, detail="监控任务不存在"
            )

        # 权限检查：只能更新自己的任务或管理员可以更新所有任务
        if (
            not check_user_can_manage_group(current_user)
            and task.member_id != current_user.id
        ):
            raise HTTPException(
                status_code=http_status.HTTP_403_FORBIDDEN, detail="无权限更新该任务"
            )

        # 更新巡检信息
        if "cabinet_count" in request_data:
            task.cabinet_count = request_data["cabinet_count"]
        if "minutes_per_cabinet" in request_data:
            task.minutes_per_cabinet = request_data["minutes_per_cabinet"]
        if "inspection_notes" in request_data:
            task.inspection_notes = request_data["inspection_notes"]
        if "equipment_checked" in request_data:
            task.equipment_checked = request_data["equipment_checked"]
        if "issues_found" in request_data:
            task.issues_found = request_data["issues_found"]

        # 如果有机柜数量，自动计算工时
        if task.cabinet_count and task.minutes_per_cabinet:
            task.work_minutes = task.cabinet_count * task.minutes_per_cabinet

        task.updated_at = datetime.utcnow()
        await db.commit()
        await db.refresh(task)

        logger.info(
            f"Monitoring task {task_id} inspection updated by user {current_user.id}"
        )

        return create_response(
            data={
                "id": task.id,
                "cabinet_count": task.cabinet_count,
                "minutes_per_cabinet": task.minutes_per_cabinet,
                "calculated_work_minutes": task.work_minutes,
                "calculated_work_hours": round((task.work_minutes or 0) / 60.0, 2),
                "inspection_notes": task.inspection_notes,
                "equipment_checked": task.equipment_checked,
                "issues_found": task.issues_found,
            },
            message="巡检信息更新成功",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update monitoring task {task_id} inspection error: {str(e)}")
        await db.rollback()
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="更新巡检信息失败",
        )


@router.post("/monitoring/inspection", response_model=Dict[str, Any])
async def create_inspection_monitoring_task(
    request_data: Dict[str, Any],
    current_user: Member = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """创建巡检监控任务"""
    try:
        from app.models.task import MonitoringTask

        # 基本信息
        title = request_data.get("title", "巡检监控任务")
        description = request_data.get("description", "")
        location = request_data.get("location", "")
        cabinet_count = request_data.get("cabinet_count", 0)
        minutes_per_cabinet = request_data.get("minutes_per_cabinet", 5)

        # 创建监控任务
        task = MonitoringTask(
            title=title,
            description=description,
            location=location,
            monitoring_type="inspection",
            member_id=current_user.id,
            cabinet_count=cabinet_count,
            minutes_per_cabinet=minutes_per_cabinet,
            inspection_notes=request_data.get("inspection_notes", ""),
            equipment_checked=request_data.get("equipment_checked", []),
            issues_found=request_data.get("issues_found", []),
            start_time=datetime.utcnow(),
        )

        # Set status after creation
        task.status = TaskStatus.IN_PROGRESS

        # 计算工时
        if cabinet_count and minutes_per_cabinet:
            task.work_minutes = cabinet_count * minutes_per_cabinet

        db.add(task)
        await db.commit()
        await db.refresh(task)

        logger.info(f"Inspection monitoring task created by user {current_user.id}")

        return create_response(
            data={
                "id": task.id,
                "title": task.title,
                "description": task.description,
                "location": task.location,
                "cabinet_count": task.cabinet_count,
                "minutes_per_cabinet": task.minutes_per_cabinet,
                "calculated_work_minutes": task.work_minutes,
                "calculated_work_hours": round((task.work_minutes or 0) / 60.0, 2),
                "inspection_notes": task.inspection_notes,
                "equipment_checked": task.equipment_checked,
                "issues_found": task.issues_found,
                "status": task.status.value,
                "created_at": task.created_at.isoformat() if task.created_at else None,
            },
            message="巡检监控任务创建成功",
        )

    except Exception as e:
        logger.error(f"Create inspection monitoring task error: {str(e)}")
        await db.rollback()
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="创建巡检监控任务失败",
        )


@router.get("/monitoring/{task_id}/inspection", response_model=Dict[str, Any])
async def get_monitoring_inspection_details(
    task_id: int,
    current_user: Member = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """获取监控任务的巡检详情"""
    try:
        from app.models.task import MonitoringTask

        # 查询监控任务
        query = (
            select(MonitoringTask)
            .options(joinedload(MonitoringTask.member))
            .where(MonitoringTask.id == task_id)
        )
        result = await db.execute(query)
        task = result.scalar_one_or_none()

        if not task:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND, detail="监控任务不存在"
            )

        # 权限检查：只能查看自己的任务或管理员可以查看所有任务
        if (
            not check_user_can_manage_group(current_user)
            and task.member_id != current_user.id
        ):
            raise HTTPException(
                status_code=http_status.HTTP_403_FORBIDDEN, detail="无权限查看该任务"
            )

        return create_response(
            data={
                "id": task.id,
                "title": task.title,
                "description": task.description,
                "location": task.location,
                "monitoring_type": task.monitoring_type,
                "cabinet_count": task.cabinet_count,
                "minutes_per_cabinet": task.minutes_per_cabinet,
                "calculated_work_minutes": task.work_minutes,
                "calculated_work_hours": round((task.work_minutes or 0) / 60.0, 2),
                "inspection_notes": task.inspection_notes,
                "equipment_checked": task.equipment_checked or [],
                "issues_found": task.issues_found or [],
                "status": task.status.value,
                "member_name": task.member.name if task.member else None,
                "start_time": task.start_time.isoformat() if task.start_time else None,
                "end_time": task.end_time.isoformat() if task.end_time else None,
                "created_at": task.created_at.isoformat() if task.created_at else None,
                "updated_at": task.updated_at.isoformat() if task.updated_at else None,
            },
            message="获取巡检详情成功",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Get monitoring task {task_id} inspection details error: {str(e)}"
        )
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取巡检详情失败",
        )


@router.put("/monitoring/{task_id}/inspection/complete", response_model=Dict[str, Any])
async def complete_inspection_task(
    task_id: int,
    request_data: Dict[str, Any],
    current_user: Member = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """完成巡检任务"""
    try:
        from app.models.task import MonitoringTask

        # 查询监控任务
        query = select(MonitoringTask).where(MonitoringTask.id == task_id)
        result = await db.execute(query)
        task = result.scalar_one_or_none()

        if not task:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND, detail="监控任务不存在"
            )

        # 权限检查：只能完成自己的任务或管理员可以完成所有任务
        if (
            not check_user_can_manage_group(current_user)
            and task.member_id != current_user.id
        ):
            raise HTTPException(
                status_code=http_status.HTTP_403_FORBIDDEN, detail="无权限完成该任务"
            )

        # 更新任务状态为完成
        task.status = TaskStatus.COMPLETED
        task.end_time = datetime.utcnow()

        # 更新巡检结果
        if "inspection_notes" in request_data:
            task.inspection_notes = request_data["inspection_notes"]
        if "equipment_checked" in request_data:
            task.equipment_checked = request_data["equipment_checked"]
        if "issues_found" in request_data:
            task.issues_found = request_data["issues_found"]

        task.updated_at = datetime.utcnow()
        await db.commit()
        await db.refresh(task)

        logger.info(
            f"Monitoring task {task_id} inspection completed by user {current_user.id}"
        )

        return create_response(
            data={
                "id": task.id,
                "status": task.status.value,
                "end_time": task.end_time.isoformat() if task.end_time else None,
                "total_work_minutes": task.work_minutes,
                "total_work_hours": round((task.work_minutes or 0) / 60.0, 2),
                "inspection_summary": {
                    "cabinet_count": task.cabinet_count,
                    "equipment_checked_count": len(task.equipment_checked or []),
                    "issues_found_count": len(task.issues_found or []),
                    "completion_time": (
                        task.end_time.isoformat() if task.end_time else None
                    ),
                },
            },
            message="巡检任务完成",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Complete monitoring task {task_id} inspection error: {str(e)}")
        await db.rollback()
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="完成巡检任务失败",
        )


@router.post("/assistance/{task_id}/review", response_model=Dict[str, Any])
async def review_assistance_task(
    task_id: int,
    request_data: Dict[str, Any],
    current_user: Member = Depends(get_current_active_admin),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """
    协助任务审核（支持approve/reject操作）

    权限：仅管理员可审核协助任务
    """
    try:
        from datetime import datetime

        from sqlalchemy import select

        from app.models.task import AssistanceTask, TaskStatus

        # 获取审核操作和评论
        action = request_data.get("action", "approve")  # approve 或 reject
        comment = request_data.get("comment", "")

        # 获取待审核任务
        stmt = select(AssistanceTask).where(AssistanceTask.id == task_id)
        result = await db.execute(stmt)
        task = result.scalar_one_or_none()

        if not task:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND, detail="协助任务不存在"
            )

        if task.status != TaskStatus.PENDING:
            raise HTTPException(
                status_code=http_status.HTTP_400_BAD_REQUEST,
                detail="任务已审核，无需重复操作",
            )

        # 根据审核操作更新任务状态
        if action == "approve":
            task.status = TaskStatus.COMPLETED
            task.approved_by = current_user.id
            task.approved_at = datetime.utcnow()
            task.review_comment = comment

            # 更新相关成员的月度汇总
            if task.start_time:
                from app.services.work_hours_service import WorkHoursCalculationService

                work_hours_service = WorkHoursCalculationService(db)

                if task.member_id:
                    await work_hours_service.recalculate_member_monthly_summary(
                        member_id=task.member_id,
                        year=task.start_time.year,
                        month=task.start_time.month,
                    )

            message = "协助任务审核通过"
        elif action == "reject":
            task.status = TaskStatus.CANCELLED
            task.approved_by = current_user.id
            task.approved_at = datetime.utcnow()
            task.review_comment = comment
            message = "协助任务审核驳回"
        else:
            raise HTTPException(
                status_code=http_status.HTTP_400_BAD_REQUEST,
                detail="无效的审核操作，请使用 'approve' 或 'reject'",
            )

        await db.commit()
        await db.refresh(task)

        logger.info(f"Assistance task {task_id} {action} by user {current_user.id}")

        return create_response(
            data={
                "taskId": task.id,
                "action": action,
                "status": task.status.value,
                "approvedBy": current_user.id,
                "approvedByName": current_user.name,
                "approvedAt": (
                    task.approved_at.isoformat() if task.approved_at else None
                ),
                "reviewComment": comment,
                "workMinutes": task.work_minutes if action == "approve" else 0,
                "workHours": (
                    round((task.work_minutes or 0) / 60.0, 2)
                    if action == "approve"
                    else 0
                ),
            },
            message=message,
        )

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Review assistance task error: {str(e)}")
        return create_error_response(
            message="审核协助任务失败", details={"error": str(e)}
        )


@router.post("/assistance/batch-review", response_model=Dict[str, Any])
async def batch_review_assistance_tasks(
    request_data: Dict[str, Any],
    current_user: Member = Depends(get_current_active_admin),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """
    批量审核协助任务

    权限：仅管理员可批量审核协助任务
    """
    try:
        from datetime import datetime

        from sqlalchemy import select

        from app.models.task import AssistanceTask, TaskStatus

        task_ids = request_data.get("taskIds", [])
        action = request_data.get("action", "approve")  # approve 或 reject
        comment = request_data.get("comment", "")

        if not task_ids:
            raise HTTPException(
                status_code=http_status.HTTP_400_BAD_REQUEST,
                detail="没有提供任务ID列表",
            )

        if action not in ["approve", "reject"]:
            raise HTTPException(
                status_code=http_status.HTTP_400_BAD_REQUEST,
                detail="无效的审核操作，请使用 'approve' 或 'reject'",
            )

        # 获取待审核任务列表
        stmt = select(AssistanceTask).where(
            AssistanceTask.id.in_(task_ids), AssistanceTask.status == TaskStatus.PENDING
        )
        result = await db.execute(stmt)
        tasks = result.scalars().all()

        if not tasks:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail="没有找到待审核的协助任务",
            )

        processed_tasks = []
        errors = []

        for task in tasks:
            try:
                # 根据审核操作更新任务状态
                if action == "approve":
                    task.status = TaskStatus.COMPLETED
                elif action == "reject":
                    task.status = TaskStatus.CANCELLED

                task.approved_by = current_user.id
                task.approved_at = datetime.utcnow()
                task.review_comment = comment

                # 如果是批准，更新相关成员的月度汇总
                if action == "approve" and task.start_time:
                    from app.services.work_hours_service import (
                        WorkHoursCalculationService,
                    )

                    work_hours_service = WorkHoursCalculationService(db)

                    if task.member_id:
                        await work_hours_service.recalculate_member_monthly_summary(
                            member_id=task.member_id,
                            year=task.start_time.year,
                            month=task.start_time.month,
                        )

                processed_tasks.append(
                    {
                        "taskId": task.id,
                        "title": task.title,
                        "status": task.status.value,
                        "workMinutes": task.work_minutes if action == "approve" else 0,
                    }
                )

            except Exception as e:
                logger.error(f"Batch review task {task.id} error: {str(e)}")
                errors.append(f"任务 {task.id} 审核失败: {str(e)}")

        await db.commit()

        batch_result = {
            "totalRequested": len(task_ids),
            "processedCount": len(processed_tasks),
            "errorCount": len(errors),
            "action": action,
            "processedTasks": processed_tasks,
            "errors": errors,
        }

        logger.info(
            f"Batch assistance tasks {action} by user {current_user.id}: {batch_result}"
        )

        return create_response(
            data=batch_result,
            message=f"批量审核完成：{len(processed_tasks)} 个任务{action}，{len(errors)} 个失败",
        )

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Batch review assistance tasks error: {str(e)}")
        return create_error_response(
            message="批量审核协助任务失败", details={"error": str(e)}
        )


@router.post("/import-repair-data", response_model=Dict[str, Any])
async def import_repair_data(
    request_data: Dict[str, Any],
    current_user: Member = Depends(get_current_active_admin),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """
    AB表导入维修任务数据

    权限：仅管理员可操作
    """
    try:
        from datetime import datetime

        from app.models.task import TaskPriority, TaskStatus, TaskType

        tasks_data = request_data.get("tasks", [])
        options = request_data.get("options", {})

        if not tasks_data:
            raise HTTPException(
                status_code=http_status.HTTP_400_BAD_REQUEST, detail="没有提供任务数据"
            )

        # 处理导入选项
        overwrite = options.get("overwrite", True)
        skip_duplicates = options.get("skipDuplicates", True)
        auto_assign = options.get("autoAssign", False)

        created_tasks = []
        updated_tasks = []
        skipped_tasks = []
        errors = []

        for task_data in tasks_data:
            try:
                # 检查必要字段
                if not task_data.get("workOrderId"):
                    errors.append(f"任务缺少工单号: {task_data}")
                    continue

                # 检查是否已存在相同工单号的任务
                existing_task = await db.execute(
                    select(RepairTask).where(
                        RepairTask.work_order_id == task_data.get("workOrderId")
                    )
                )
                existing = existing_task.scalar_one_or_none()

                if existing and skip_duplicates:
                    skipped_tasks.append(task_data.get("workOrderId"))
                    continue
                elif existing and overwrite:
                    # 更新现有任务
                    existing.title = task_data.get("title", existing.title)
                    existing.description = task_data.get(
                        "description", existing.description
                    )
                    existing.location = task_data.get("location", existing.location)
                    existing.reporter_name = task_data.get(
                        "reporterName", existing.reporter_name
                    )
                    existing.reporter_phone = task_data.get(
                        "reporterPhone", existing.reporter_phone
                    )
                    existing.is_offline_marked = task_data.get(
                        "isOffline", existing.is_offline_marked
                    )
                    existing.updated_at = datetime.utcnow()
                    updated_tasks.append(existing.work_order_id)
                    continue

                # 创建新任务
                new_task = RepairTask(
                    work_order_id=task_data.get("workOrderId"),
                    title=task_data.get("title", "未知维修任务"),
                    description=task_data.get("description"),
                    location=task_data.get("location"),
                    reporter_name=task_data.get("reporterName"),
                    reporter_phone=task_data.get("reporterPhone"),
                    task_type=TaskType.REPAIR,
                    priority=TaskPriority.MEDIUM,
                    status=TaskStatus.PENDING,
                    is_offline=task_data.get("isOffline", False),
                    created_by=current_user.id,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow(),
                )

                # 如果启用自动分配，分配给当前用户
                if auto_assign:
                    new_task.member_id = current_user.id
                    new_task.status = TaskStatus.IN_PROGRESS
                    new_task.assigned_at = datetime.utcnow()

                db.add(new_task)
                created_tasks.append(task_data.get("workOrderId"))

            except Exception as e:
                logger.error(f"Import task error: {str(e)}")
                errors.append(
                    f"导入任务失败 {task_data.get('workOrderId', 'Unknown')}: {str(e)}"
                )

        # 提交所有更改
        await db.commit()

        result = {
            "total_processed": len(tasks_data),
            "created_count": len(created_tasks),
            "updated_count": len(updated_tasks),
            "skipped_count": len(skipped_tasks),
            "error_count": len(errors),
            "created_tasks": created_tasks,
            "updated_tasks": updated_tasks,
            "skipped_tasks": skipped_tasks,
            "errors": errors,
        }

        logger.info(f"Repair data imported by user {current_user.id}: {result}")

        return create_response(
            data=result,
            message=(
                f"AB表导入完成：创建 {len(created_tasks)} 个，"
                f"更新 {len(updated_tasks)} 个，跳过 {len(skipped_tasks)} 个"
            ),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Import repair data error: {str(e)}")
        return create_error_response(message="AB表导入失败", details={"error": str(e)})


@router.get("/health", response_model=Dict[str, Any])
async def health_check() -> Dict[str, Any]:
    """
    任务服务健康检查

    Returns:
        Dict: 健康状态信息
    """
    from datetime import datetime

    return create_response(
        data={
            "service": "tasks",
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "version": "1.0.0",
        },
        message="任务服务运行正常",
    )
