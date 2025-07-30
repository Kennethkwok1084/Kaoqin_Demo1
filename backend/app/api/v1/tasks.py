"""
任务管理API端点
处理维修任务、监控任务、协助任务的增删改查和工时计算
"""

import logging
from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func, desc, update, delete
from sqlalchemy.orm import selectinload, joinedload

from app.api.deps import (
    get_db, get_current_user, get_current_active_admin, 
    get_current_active_group_leader, create_response, create_error_response
)
from app.core.config import settings
from app.models.member import Member, UserRole
from app.models.task import (
    RepairTask, MonitoringTask, AssistanceTask, TaskTag, TaskStatus, 
    TaskType, TaskPriority, TaskCategory, task_tag_association
)
from app.schemas.task import (
    TaskCreate, TaskUpdate, TaskResponse, TaskDetailResponse, TaskListResponse,
    TaskSearchParams, TaskStatusUpdate, TaskAssignment, TaskStatistics,
    TaskImportRequest, TaskImportResult, WorkHourCalculation, WorkHourResult,
    TaskTagCreate, TaskTagResponse
)

logger = logging.getLogger(__name__)
router = APIRouter()


# ============= 维修任务管理 =============

@router.get("/repair", response_model=Dict[str, Any])
async def get_repair_tasks(
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=100, description="每页数量"),
    search: Optional[str] = Query(None, description="搜索关键词（标题或任务编号）"),
    status: Optional[TaskStatus] = Query(None, description="状态筛选"),
    task_type: Optional[TaskType] = Query(None, description="任务类型筛选"),
    priority: Optional[TaskPriority] = Query(None, description="优先级筛选"),
    assigned_to: Optional[int] = Query(None, description="执行者筛选"),
    category: Optional[TaskCategory] = Query(None, description="分类筛选"),
    location: Optional[str] = Query(None, description="地点关键词"),
    date_from: Optional[datetime] = Query(None, description="创建时间起始"),
    date_to: Optional[datetime] = Query(None, description="创建时间结束"),
    sort_by: str = Query("report_time", description="排序字段"),
    sort_order: str = Query("desc", regex="^(asc|desc)$", description="排序方向"),
    current_user: Member = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取维修任务列表
    
    支持分页、搜索、筛选和排序功能
    普通用户只能查看自己的任务，管理员和组长可查看所有任务
    """
    try:
        # 构建查询
        query = select(RepairTask).options(
            joinedload(RepairTask.member),
            selectinload(RepairTask.tags)
        )
        
        # 权限筛选
        if not current_user.can_manage_group:
            query = query.where(RepairTask.member_id == current_user.id)
        
        # 搜索条件
        if search:
            search_filter = or_(
                RepairTask.title.ilike(f"%{search}%"),
                RepairTask.task_id.ilike(f"%{search}%"),
                RepairTask.description.ilike(f"%{search}%")
            )
            query = query.where(search_filter)
        
        # 筛选条件
        filters = []
        if status is not None:
            filters.append(RepairTask.status == status)
        if task_type is not None:
            filters.append(RepairTask.task_type == task_type)
        if priority is not None:
            filters.append(RepairTask.priority == priority)
        if assigned_to is not None:
            filters.append(RepairTask.member_id == assigned_to)
        if category is not None:
            filters.append(RepairTask.category == category)
        if location:
            filters.append(RepairTask.location.ilike(f"%{location}%"))
        if date_from:
            filters.append(RepairTask.report_time >= date_from)
        if date_to:
            filters.append(RepairTask.report_time <= date_to)
        
        if filters:
            query = query.where(and_(*filters))
        
        # 排序
        sort_column = getattr(RepairTask, sort_by, RepairTask.report_time)
        if sort_order == "desc":
            query = query.order_by(desc(sort_column))
        else:
            query = query.order_by(sort_column)
        
        # 计算总数
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await db.execute(count_query)
        total = total_result.scalar()
        
        # 分页
        offset = (page - 1) * size
        query = query.offset(offset).limit(size)
        
        # 执行查询
        result = await db.execute(query)
        tasks = result.scalars().all()
        
        # 转换响应数据
        items = []
        for task in tasks:
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
                "member_id": task.member_id,
                "member_name": task.member.name if task.member else None,
                "is_overdue_response": task.is_overdue_response,
                "is_overdue_completion": task.is_overdue_completion,
                "tags": [{"id": tag.id, "name": tag.name, "work_minutes_modifier": tag.work_minutes_modifier} for tag in task.tags],
                "created_at": task.created_at,
                "updated_at": task.updated_at
            }
            items.append(task_data)
        
        # 分页信息
        pages = (total + size - 1) // size
        has_next = page < pages
        has_prev = page > 1
        
        response_data = {
            "items": items,
            "total": total,
            "page": page,
            "size": size,
            "pages": pages,
            "has_next": has_next,
            "has_prev": has_prev,
            "filters_applied": {
                "status": status.value if status else None,
                "task_type": task_type.value if task_type else None,
                "priority": priority.value if priority else None,
                "assigned_to": assigned_to,
                "category": category.value if category else None
            }
        }
        
        logger.info(f"Repair tasks list retrieved by {current_user.student_id}, total: {total}")
        
        return create_response(
            data=response_data,
            message=f"成功获取维修任务列表，共 {total} 条记录"
        )
        
    except Exception as e:
        logger.error(f"Get repair tasks error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取维修任务列表失败"
        )


@router.get("/repair/{task_id}", response_model=Dict[str, Any])
async def get_repair_task(
    task_id: int,
    current_user: Member = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取单个维修任务详情
    
    权限：用户可查看自己的任务，管理员和组长可查看所有任务
    """
    try:
        # 查询任务
        query = select(RepairTask).options(
            joinedload(RepairTask.member),
            selectinload(RepairTask.tags)
        ).where(RepairTask.id == task_id)
        
        result = await db.execute(query)
        task = result.scalar_one_or_none()
        
        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="维修任务不存在"
            )
        
        # 权限检查
        if not (task.member_id == current_user.id or current_user.can_manage_group):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权限查看该任务"
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
                    "tag_type": tag.tag_type
                } for tag in task.tags
            ],
            "work_hour_breakdown": _calculate_work_hour_breakdown(task),
            "created_at": task.created_at,
            "updated_at": task.updated_at
        }
        
        logger.info(f"Repair task {task_id} details viewed by {current_user.student_id}")
        
        return create_response(
            data=task_data,
            message="成功获取维修任务详情"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get repair task {task_id} error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取维修任务详情失败"
        )


@router.post("/repair", response_model=Dict[str, Any])
async def create_repair_task(
    task_data: TaskCreate,
    current_user: Member = Depends(get_current_active_group_leader),
    db: AsyncSession = Depends(get_db)
):
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
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="指定的执行者不存在"
                )
            
            if not assigned_member.is_active:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="指定的执行者账户已被禁用"
                )
        
        # 生成任务编号
        task_id = await _generate_task_id(db)
        
        # 创建维修任务
        new_task = RepairTask(
            task_id=task_id,
            title=task_data.title,
            description=task_data.description,
            category=TaskCategory.NETWORK_REPAIR,  # 默认为网络维修
            priority=task_data.priority,
            task_type=task_data.task_type,
            location=task_data.location,
            member_id=task_data.assigned_to,
            report_time=datetime.utcnow(),
            reporter_name=task_data.reporter_name,
            reporter_contact=task_data.reporter_contact,
            status=TaskStatus.PENDING if task_data.assigned_to else TaskStatus.PENDING
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
                "member_name": assigned_member.name if assigned_member else None
            },
            message=f"成功创建维修任务：{new_task.task_id}"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Create repair task error: {str(e)}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="创建维修任务失败"
        )


@router.put("/repair/{task_id}", response_model=Dict[str, Any])
async def update_repair_task(
    task_id: int,
    task_update: TaskUpdate,
    current_user: Member = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    更新维修任务
    
    权限：任务执行者可更新基本信息，管理员和组长可更新所有信息
    """
    try:
        # 查询任务
        query = select(RepairTask).options(
            selectinload(RepairTask.tags)
        ).where(RepairTask.id == task_id)
        
        result = await db.execute(query)
        task = result.scalar_one_or_none()
        
        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="维修任务不存在"
            )
        
        # 权限检查
        is_task_owner = task.member_id == current_user.id
        if not (is_task_owner or current_user.can_manage_group):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权限修改该任务"
            )
        
        # 获取更新数据
        update_data = task_update.dict(exclude_unset=True)
        
        # 普通用户限制
        if is_task_owner and not current_user.can_manage_group:
            restricted_fields = ["assigned_to", "priority", "task_type"]
            for field in restricted_fields:
                if field in update_data:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=f"无权限修改字段：{field}"
                    )
        
        # 验证新分配的成员
        if "assigned_to" in update_data and update_data["assigned_to"]:
            member_query = select(Member).where(Member.id == update_data["assigned_to"])
            member_result = await db.execute(member_query)
            member = member_result.scalar_one_or_none()
            
            if not member or not member.is_active:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="指定的执行者不存在或已被禁用"
                )
        
        # 更新字段
        for field, value in update_data.items():
            if field == "tag_ids":
                # 更新标签关联
                if current_user.can_manage_group:
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
            message="维修任务更新成功"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update repair task {task_id} error: {str(e)}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="更新维修任务失败"
        )


@router.delete("/repair/{task_id}", response_model=Dict[str, Any])
async def delete_repair_task(
    task_id: int,
    current_user: Member = Depends(get_current_active_admin),
    db: AsyncSession = Depends(get_db)
):
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
                status_code=status.HTTP_404_NOT_FOUND,
                detail="维修任务不存在"
            )
        
        # 检查任务状态
        if task.status == TaskStatus.IN_PROGRESS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="不能删除进行中的任务，请先修改任务状态"
            )
        
        task_id_str = task.task_id
        task_title = task.title
        
        # 删除任务
        await db.delete(task)
        await db.commit()
        
        logger.warning(f"Repair task deleted: {task_id_str} by {current_user.student_id}")
        
        return create_response(
            message=f"成功删除维修任务：{task_title} ({task_id_str})"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete repair task {task_id} error: {str(e)}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="删除维修任务失败"
        )


# ============= 任务状态管理 =============

@router.put("/repair/{task_id}/status", response_model=Dict[str, Any])
async def update_task_status(
    task_id: int,
    status_update: TaskStatusUpdate,
    current_user: Member = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
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
                status_code=status.HTTP_404_NOT_FOUND,
                detail="维修任务不存在"
            )
        
        # 权限检查
        is_task_owner = task.member_id == current_user.id
        if not (is_task_owner or current_user.can_manage_group):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权限修改该任务状态"
            )
        
        old_status = task.status
        new_status = status_update.status
        
        # 状态转换验证
        if not _is_valid_status_transition(old_status, new_status):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"不能从 {old_status.value} 状态转换到 {new_status.value} 状态"
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
        
        logger.info(f"Task {task_id} status updated from {old_status.value} to {new_status.value} by {current_user.student_id}")
        
        return create_response(
            data={
                "id": task.id,
                "task_id": task.task_id,
                "old_status": old_status.value,
                "new_status": new_status.value,
                "work_minutes": task.work_minutes
            },
            message=f"任务状态已从 {old_status.value} 更新为 {new_status.value}"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update task {task_id} status error: {str(e)}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="更新任务状态失败"
        )


@router.put("/repair/{task_id}/assign", response_model=Dict[str, Any])
async def assign_task(
    task_id: int,
    assignment: TaskAssignment,
    current_user: Member = Depends(get_current_active_group_leader),
    db: AsyncSession = Depends(get_db)
):
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
                status_code=status.HTTP_404_NOT_FOUND,
                detail="维修任务不存在"
            )
        
        # 验证目标成员
        member_query = select(Member).where(Member.id == assignment.assigned_to)
        member_result = await db.execute(member_query)
        member = member_result.scalar_one_or_none()
        
        if not member:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="指定的成员不存在"
            )
        
        if not member.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="指定的成员账户已被禁用"
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
        
        logger.info(f"Task {task_id} assigned to {assignment.assigned_to} by {current_user.student_id}")
        
        return create_response(
            data={
                "id": task.id,
                "task_id": task.task_id,
                "assigned_to": assignment.assigned_to,
                "assignee_name": member.name
            },
            message=assignment_msg
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Assign task {task_id} error: {str(e)}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="分配任务失败"
        )


# ============= 任务标签管理 =============

@router.get("/tags", response_model=Dict[str, Any])
async def get_task_tags(
    is_active: Optional[bool] = Query(None, description="是否启用筛选"),
    tag_type: Optional[str] = Query(None, description="标签类型筛选"),
    current_user: Member = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
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
                "updated_at": tag.updated_at
            }
            items.append(tag_data)
        
        logger.info(f"Task tags retrieved by {current_user.student_id}, total: {len(items)}")
        
        return create_response(
            data={"items": items, "total": len(items)},
            message=f"成功获取任务标签列表，共 {len(items)} 个标签"
        )
        
    except Exception as e:
        logger.error(f"Get task tags error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取任务标签失败"
        )


@router.post("/tags", response_model=Dict[str, Any])
async def create_task_tag(
    tag_data: TaskTagCreate,
    current_user: Member = Depends(get_current_active_admin),
    db: AsyncSession = Depends(get_db)
):
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
                status_code=status.HTTP_409_CONFLICT,
                detail=f"标签名称 '{tag_data.name}' 已存在"
            )
        
        # 创建标签
        new_tag = TaskTag(
            name=tag_data.name,
            description=tag_data.description,
            work_minutes_modifier=tag_data.work_minutes_modifier,
            is_active=tag_data.is_active,
            tag_type=tag_data.tag_type
        )
        
        db.add(new_tag)
        await db.commit()
        await db.refresh(new_tag)
        
        logger.info(f"New task tag created: {new_tag.name} by {current_user.student_id}")
        
        return create_response(
            data={
                "id": new_tag.id,
                "name": new_tag.name,
                "work_minutes_modifier": new_tag.work_minutes_modifier
            },
            message=f"成功创建任务标签：{new_tag.name}"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Create task tag error: {str(e)}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="创建任务标签失败"
        )


# ============= 工时计算 =============

@router.post("/repair/{task_id}/calculate-hours", response_model=Dict[str, Any])
async def calculate_work_hours(
    task_id: int,
    calculation: WorkHourCalculation,
    current_user: Member = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    计算任务工时
    
    权限：任务执行者和管理员可计算工时
    """
    try:
        # 查询任务
        query = select(RepairTask).options(
            selectinload(RepairTask.tags)
        ).where(RepairTask.id == task_id)
        
        result = await db.execute(query)
        task = result.scalar_one_or_none()
        
        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="维修任务不存在"
            )
        
        # 权限检查
        is_task_owner = task.member_id == current_user.id
        if not (is_task_owner or current_user.can_manage_group):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权限计算该任务工时"
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
        
        logger.info(f"Work hours calculated for task {task_id} by {current_user.student_id}")
        
        return create_response(
            data={
                "task_id": task.id,
                "base_minutes": task.base_work_minutes,
                "final_minutes": task.work_minutes,
                "breakdown": breakdown
            },
            message="工时计算完成"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Calculate work hours for task {task_id} error: {str(e)}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="工时计算失败"
        )


# ============= 任务统计 =============

@router.get("/statistics/overview", response_model=Dict[str, Any])
async def get_task_statistics(
    date_from: Optional[datetime] = Query(None, description="统计开始时间"),
    date_to: Optional[datetime] = Query(None, description="统计结束时间"),
    member_id: Optional[int] = Query(None, description="成员筛选"),
    current_user: Member = Depends(get_current_active_group_leader),
    db: AsyncSession = Depends(get_db)
):
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
        work_minutes_query = select(func.sum(RepairTask.work_minutes)).select_from(base_query.subquery())
        work_minutes_result = await db.execute(work_minutes_query)
        total_work_minutes = work_minutes_result.scalar() or 0
        total_work_hours = round(total_work_minutes / 60.0, 2)
        
        # 平均完成时间（已完成任务）
        completed_query = base_query.where(
            and_(
                RepairTask.status == TaskStatus.COMPLETED,
                RepairTask.completion_time.isnot(None),
                RepairTask.report_time.isnot(None)
            )
        )
        
        # 这里简化计算，实际应该计算平均完成时间
        avg_completion_hours = 0.0
        completed_count = status_stats.get("completed", 0)
        if completed_count > 0:
            avg_completion_hours = round(total_work_hours / completed_count, 2)
        
        # 超期任务统计
        current_time = datetime.utcnow()
        overdue_response_query = base_query.where(
            and_(
                RepairTask.status == TaskStatus.PENDING,
                RepairTask.report_time < current_time - timedelta(hours=24)
            )
        )
        overdue_count_query = select(func.count()).select_from(overdue_response_query.subquery())
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
            "status_distribution": status_stats
        }
        
        logger.info(f"Task statistics retrieved by {current_user.student_id}")
        
        return create_response(
            data=statistics_data,
            message="成功获取任务统计信息"
        )
        
    except Exception as e:
        logger.error(f"Get task statistics error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取任务统计失败"
        )


# ============= 辅助函数 =============

async def _generate_task_id(db: AsyncSession) -> str:
    """生成任务编号"""
    today = datetime.now().strftime("%Y%m%d")
    
    # 查询今天已有的任务数量
    count_query = select(func.count()).where(
        RepairTask.task_id.like(f"R{today}%")
    )
    count_result = await db.execute(count_query)
    count = count_result.scalar()
    
    # 生成新的任务编号
    return f"R{today}{str(count + 1).zfill(4)}"


def _is_valid_status_transition(old_status: TaskStatus, new_status: TaskStatus) -> bool:
    """验证状态转换是否有效"""
    valid_transitions = {
        TaskStatus.PENDING: [TaskStatus.IN_PROGRESS, TaskStatus.CANCELLED],
        TaskStatus.IN_PROGRESS: [TaskStatus.COMPLETED, TaskStatus.ON_HOLD, TaskStatus.CANCELLED],
        TaskStatus.ON_HOLD: [TaskStatus.IN_PROGRESS, TaskStatus.CANCELLED],
        TaskStatus.COMPLETED: [],  # 已完成的任务不能转换状态
        TaskStatus.CANCELLED: []   # 已取消的任务不能转换状态
    }
    
    return new_status in valid_transitions.get(old_status, [])


async def _add_penalty_tag(task: RepairTask, tag_name: str, modifier: int, db: AsyncSession):
    """添加惩罚标签"""
    # 查找或创建标签
    tag_query = select(TaskTag).where(TaskTag.name == tag_name)
    tag_result = await db.execute(tag_query)
    tag = tag_result.scalar_one_or_none()
    
    if not tag:
        tag = TaskTag(
            name=tag_name,
            work_minutes_modifier=modifier,
            tag_type="penalty",
            is_active=True
        )
        db.add(tag)
        await db.flush()
    
    # 添加到任务
    if tag not in task.tags:
        task.tags.append(tag)


def _calculate_work_hour_breakdown(task: RepairTask) -> Dict[str, Any]:
    """计算工时分解详情"""
    base_minutes = task.base_work_minutes
    total_modifier = 0
    applied_tags = []
    
    for tag in task.tags:
        if tag.is_active:
            total_modifier += tag.work_minutes_modifier
            applied_tags.append({
                "name": tag.name,
                "modifier": tag.work_minutes_modifier,
                "type": tag.tag_type
            })
    
    return {
        "base_minutes": base_minutes,
        "tag_modifiers": total_modifier,
        "final_minutes": max(0, base_minutes + total_modifier),
        "applied_tags": applied_tags,
        "task_type": task.task_type.value,
        "is_overdue_response": task.is_overdue_response,
        "is_overdue_completion": task.is_overdue_completion,
        "rating": task.rating
    }


# 健康检查
@router.get("/health", response_model=Dict[str, Any])
async def tasks_health_check():
    """任务管理服务健康检查"""
    return create_response(
        data={"service": "tasks", "status": "healthy"},
        message="任务管理服务运行正常"
    )