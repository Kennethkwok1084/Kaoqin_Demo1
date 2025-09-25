"""
协助任务 API 路由，负责跨部门支援任务管理。
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Union

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi import status as http_status
from sqlalchemy import and_, delete, desc, func, or_, select
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
    AssistanceTask,
    MonitoringTask,
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

# ============= 通用任务 =============
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
        return create_error_response(
            message="获取协助任务列表失败", details={"error": str(e)}
        )


# ============= 协助任务审核流程 - 扩展现有API =============


@router.get("/assistance/{task_id}", response_model=Dict[str, Any])
async def get_assistance_task_detail(
    task_id: int,
    current_user: Member = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """获取单个协助任务详情"""
    try:
        assistance_task = await db.get(AssistanceTask, task_id)
        if not assistance_task:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND, detail="协助任务不存在"
            )

        if not check_user_can_manage_group(current_user) and assistance_task.member_id != current_user.id:
            raise HTTPException(
                status_code=http_status.HTTP_403_FORBIDDEN, detail="无权限查看该协助任务"
            )

        start_iso = assistance_task.start_time.isoformat() if assistance_task.start_time else None
        end_iso = assistance_task.end_time.isoformat() if assistance_task.end_time else None

        task_data = {
            "id": assistance_task.id,
            "title": assistance_task.title,
            "description": assistance_task.description,
            "status": assistance_task.status.value if assistance_task.status else None,
            "task_type": "assistance",
            "type": "assistance",
            "assisted_department": assistance_task.assisted_department,
            "assisted_person": assistance_task.assisted_person,
            "location": assistance_task.assisted_department,
            "reporter_name": assistance_task.assisted_person,
            "reporter_contact": assistance_task.assisted_person,
            "start_time": start_iso,
            "started_at": start_iso,
            "startedAt": start_iso,
            "end_time": end_iso,
            "completed_at": end_iso,
            "completedAt": end_iso,
            "completion_time": end_iso,
            "due_date": end_iso,
            "dueDate": end_iso,
            "work_minutes": assistance_task.work_minutes,
            "work_hours": round((assistance_task.work_minutes or 0) / 60.0, 2),
            "actual_hours": round((assistance_task.work_minutes or 0) / 60.0, 2),
            "member_id": assistance_task.member_id,
            "member_name": assistance_task.member.name if assistance_task.member else None,
            "approved_by": assistance_task.approved_by,
            "approved_at": assistance_task.approved_at.isoformat() if assistance_task.approved_at else None,
            "review_comment": assistance_task.review_comment,
            "is_overdue_response": False,
            "is_overdue_completion": False,
            "attachments": [],
            "created_at": assistance_task.created_at.isoformat() if assistance_task.created_at else None,
            "updated_at": assistance_task.updated_at.isoformat() if assistance_task.updated_at else None,
        }

        return create_response(data=task_data, message="成功获取协助任务详情")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取协助任务详情失败: {str(e)}")
        return create_error_response(
            message="获取协助任务详情失败", details={"error": str(e)}
        )


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

