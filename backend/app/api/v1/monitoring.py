"""
监控任务 API 路由，负责巡检与监控类任务管理。
"""

import logging
from datetime import datetime
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


