"""
成员管理API端点
处理成员的增删改查、角色管理、批量操作等功能
"""

import logging
from typing import Any, Dict, List, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func, desc, update, delete
from sqlalchemy.orm import selectinload

from app.api.deps import (
    get_db, get_current_user, get_current_active_admin, 
    get_current_active_group_leader, create_response, create_error_response
)
from app.core.config import settings
from app.core.security import get_password_hash, encrypt_data, decrypt_data
from app.models.member import Member, UserRole
from app.schemas.member import (
    MemberCreate, MemberUpdate, MemberAdminUpdate, MemberResponse, 
    MemberDetailResponse, MemberListResponse, MemberRoleUpdate,
    MemberStatusUpdate, MemberSearchParams, MemberStatistics,
    PasswordResetRequest, BulkMemberOperation, MemberImportRequest,
    MemberImportResult
)

logger = logging.getLogger(__name__)
router = APIRouter()


# 成员列表和搜索
@router.get("/", response_model=Dict[str, Any])
async def get_members(
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=100, description="每页数量"),
    search: Optional[str] = Query(None, description="搜索关键词（姓名或学号）"),
    role: Optional[UserRole] = Query(None, description="角色筛选"),
    group_id: Optional[int] = Query(None, ge=0, description="工作组筛选"),
    class_name: Optional[str] = Query(None, description="班级筛选"),
    is_active: Optional[bool] = Query(None, description="状态筛选"),
    is_verified: Optional[bool] = Query(None, description="验证状态筛选"),
    sort_by: str = Query("created_at", description="排序字段"),
    sort_order: str = Query("desc", regex="^(asc|desc)$", description="排序方向"),
    current_user: Member = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取成员列表
    
    支持分页、搜索、筛选和排序功能
    普通用户只能查看基本信息，管理员可查看详细信息
    """
    try:
        # 构建查询条件
        query = select(Member)
        
        # 搜索条件
        if search:
            search_filter = or_(
                Member.name.ilike(f"%{search}%"),
                Member.student_id.ilike(f"%{search}%")
            )
            query = query.where(search_filter)
        
        # 筛选条件
        filters = []
        if role is not None:
            filters.append(Member.role == role)
        if group_id is not None:
            filters.append(Member.group_id == group_id)
        if class_name:
            filters.append(Member.class_name.ilike(f"%{class_name}%"))
        if is_active is not None:
            filters.append(Member.is_active == is_active)
        if is_verified is not None:
            filters.append(Member.is_verified == is_verified)
        
        if filters:
            query = query.where(and_(*filters))
        
        # 排序
        sort_column = getattr(Member, sort_by, Member.created_at)
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
        members = result.scalars().all()
        
        # 转换响应数据
        items = []
        for member in members:
            if current_user.is_admin or current_user.can_manage_group:
                # 管理员和组长可以看到详细信息
                member_data = member.get_safe_dict()
                if current_user.is_admin:
                    # 管理员可以看到敏感信息（部分隐藏）
                    member_data.update({
                        "dormitory": decrypt_data(member.dormitory) if member.dormitory else None,
                        "phone": _mask_phone(decrypt_data(member.phone)) if member.phone else None
                    })
            else:
                # 普通用户只能看到基本信息
                member_data = {
                    "id": member.id,
                    "name": member.name,
                    "student_id": member.student_id,
                    "group_id": member.group_id,
                    "class_name": member.class_name,
                    "role": member.role.value,
                    "is_active": member.is_active,
                    "created_at": member.created_at
                }
            
            items.append(member_data)
        
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
            "has_prev": has_prev
        }
        
        logger.info(f"Member list retrieved by {current_user.student_id}, total: {total}")
        
        return create_response(
            data=response_data,
            message=f"成功获取成员列表，共 {total} 条记录"
        )
        
    except Exception as e:
        logger.error(f"Get members error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取成员列表失败"
        )


# 获取单个成员详情
@router.get("/{member_id}", response_model=Dict[str, Any])
async def get_member(
    member_id: int,
    current_user: Member = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取单个成员详情
    
    权限：用户可查看自己信息，管理员和组长可查看所有成员信息
    """
    try:
        # 查询成员
        query = select(Member).where(Member.id == member_id)
        result = await db.execute(query)
        member = result.scalar_one_or_none()
        
        if not member:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="成员不存在"
            )
        
        # 权限检查
        if not (current_user.id == member_id or current_user.can_manage_group):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权限查看该成员信息"
            )
        
        # 构建响应数据
        member_data = member.get_safe_dict()
        
        # 根据权限添加敏感信息
        if current_user.is_admin:
            member_data.update({
                "dormitory": decrypt_data(member.dormitory) if member.dormitory else None,
                "phone": decrypt_data(member.phone) if member.phone else None
            })
        elif current_user.can_manage_group and current_user.id != member_id:
            # 组长查看其他成员时，手机号部分隐藏
            member_data.update({
                "phone": _mask_phone(decrypt_data(member.phone)) if member.phone else None
            })
        elif current_user.id == member_id:
            # 查看自己的信息时，显示完整信息
            member_data.update({
                "dormitory": decrypt_data(member.dormitory) if member.dormitory else None,
                "phone": decrypt_data(member.phone) if member.phone else None
            })
        
        # 添加权限信息
        member_data["permissions"] = {
            "is_admin": member.is_admin,
            "is_group_leader": member.is_group_leader,
            "can_manage_group": member.can_manage_group,
            "can_import_data": member.can_import_data,
            "can_mark_rush_tasks": member.can_mark_rush_tasks
        }
        
        logger.info(f"Member {member_id} details viewed by {current_user.student_id}")
        
        return create_response(
            data=member_data,
            message="成功获取成员信息"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get member {member_id} error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取成员信息失败"
        )


# 创建新成员
@router.post("/", response_model=Dict[str, Any])
async def create_member(
    member_data: MemberCreate,
    current_user: Member = Depends(get_current_active_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    创建新成员
    
    权限：仅管理员可创建成员
    """
    try:
        # 检查学号是否已存在
        existing_query = select(Member).where(Member.student_id == member_data.student_id)
        existing_result = await db.execute(existing_query)
        if existing_result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"学号 {member_data.student_id} 已存在"
            )
        
        # 检查邮箱是否已存在（如果提供）
        if member_data.email:
            email_query = select(Member).where(Member.email == member_data.email)
            email_result = await db.execute(email_query)
            if email_result.scalar_one_or_none():
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"邮箱 {member_data.email} 已存在"
                )
        
        # 创建新成员
        new_member = Member(
            name=member_data.name,
            student_id=member_data.student_id,
            group_id=member_data.group_id,
            class_name=member_data.class_name,
            email=member_data.email,
            password_hash=get_password_hash(member_data.password),
            role=member_data.role,
            is_active=member_data.is_active,
            is_verified=member_data.is_verified,
            dormitory=encrypt_data(member_data.dormitory) if member_data.dormitory else None,
            phone=encrypt_data(member_data.phone) if member_data.phone else None
        )
        
        db.add(new_member)
        await db.commit()
        await db.refresh(new_member)
        
        logger.info(f"New member created: {new_member.student_id} by {current_user.student_id}")
        
        return create_response(
            data=new_member.get_safe_dict(),
            message=f"成功创建成员：{new_member.name} ({new_member.student_id})"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Create member error: {str(e)}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="创建成员失败"
        )


# 更新成员信息
@router.put("/{member_id}", response_model=Dict[str, Any])
async def update_member(
    member_id: int,
    member_update: MemberUpdate,
    current_user: Member = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    更新成员信息
    
    权限：用户可更新自己的基本信息，管理员可更新所有信息
    """
    try:
        # 查询目标成员
        query = select(Member).where(Member.id == member_id)
        result = await db.execute(query)
        member = result.scalar_one_or_none()
        
        if not member:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="成员不存在"
            )
        
        # 权限检查
        is_self_update = current_user.id == member_id
        if not (is_self_update or current_user.can_manage_group):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权限修改该成员信息"
            )
        
        # 获取更新数据
        update_data = member_update.dict(exclude_unset=True)
        
        # 如果是自己更新，移除敏感字段
        if is_self_update and not current_user.is_admin:
            sensitive_fields = ["role", "is_active", "is_verified", "group_id"]
            for field in sensitive_fields:
                if field in update_data:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=f"无权限修改字段：{field}"
                    )
        
        # 检查邮箱是否重复
        if "email" in update_data and update_data["email"]:
            email_query = select(Member).where(
                and_(Member.email == update_data["email"], Member.id != member_id)
            )
            email_result = await db.execute(email_query)
            if email_result.scalar_one_or_none():
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"邮箱 {update_data['email']} 已被使用"
                )
        
        # 更新字段
        for field, value in update_data.items():
            if field in ["dormitory", "phone"] and value:
                # 加密敏感字段
                setattr(member, field, encrypt_data(value))
            elif hasattr(member, field):
                setattr(member, field, value)
        
        await db.commit()
        await db.refresh(member)
        
        logger.info(f"Member {member_id} updated by {current_user.student_id}")
        
        return create_response(
            data=member.get_safe_dict(),
            message="成员信息更新成功"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update member {member_id} error: {str(e)}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="更新成员信息失败"
        )


# 管理员更新成员信息（包含敏感字段）
@router.put("/{member_id}/admin", response_model=Dict[str, Any])
async def admin_update_member(
    member_id: int,
    member_update: MemberAdminUpdate,
    current_user: Member = Depends(get_current_active_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    管理员更新成员信息
    
    权限：仅管理员可调用，可更新包括角色在内的所有字段
    """
    try:
        # 查询目标成员
        query = select(Member).where(Member.id == member_id)
        result = await db.execute(query)
        member = result.scalar_one_or_none()
        
        if not member:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="成员不存在"
            )
        
        # 获取更新数据
        update_data = member_update.dict(exclude_unset=True)
        
        # 检查邮箱是否重复
        if "email" in update_data and update_data["email"]:
            email_query = select(Member).where(
                and_(Member.email == update_data["email"], Member.id != member_id)
            )
            email_result = await db.execute(email_query)
            if email_result.scalar_one_or_none():
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"邮箱 {update_data['email']} 已被使用"
                )
        
        # 更新字段
        for field, value in update_data.items():
            if field in ["dormitory", "phone"] and value:
                # 加密敏感字段
                setattr(member, field, encrypt_data(value))
            elif hasattr(member, field):
                setattr(member, field, value)
        
        await db.commit()
        await db.refresh(member)
        
        logger.info(f"Member {member_id} admin updated by {current_user.student_id}")
        
        return create_response(
            data=member.get_safe_dict(),
            message="成员信息更新成功"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Admin update member {member_id} error: {str(e)}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="更新成员信息失败"
        )


# 删除成员
@router.delete("/{member_id}", response_model=Dict[str, Any])
async def delete_member(
    member_id: int,
    current_user: Member = Depends(get_current_active_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    删除成员
    
    权限：仅管理员可删除成员
    注意：删除操作会级联删除相关的任务和考勤记录
    """
    try:
        # 查询目标成员
        query = select(Member).where(Member.id == member_id)
        result = await db.execute(query)
        member = result.scalar_one_or_none()
        
        if not member:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="成员不存在"
            )
        
        # 防止删除最后一个管理员
        if member.is_admin:
            admin_count_query = select(func.count()).where(Member.role == UserRole.ADMIN)
            admin_count_result = await db.execute(admin_count_query)
            admin_count = admin_count_result.scalar()
            
            if admin_count <= 1:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="不能删除最后一个管理员账户"
                )
        
        # 防止删除自己
        if member.id == current_user.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="不能删除自己的账户"
            )
        
        member_name = member.name
        member_student_id = member.student_id
        
        # 删除成员（级联删除相关记录）
        await db.delete(member)
        await db.commit()
        
        logger.warning(f"Member deleted: {member_student_id} by {current_user.student_id}")
        
        return create_response(
            message=f"成功删除成员：{member_name} ({member_student_id})"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete member {member_id} error: {str(e)}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="删除成员失败"
        )


# 更新成员角色
@router.put("/{member_id}/role", response_model=Dict[str, Any])
async def update_member_role(
    member_id: int,
    role_update: MemberRoleUpdate,
    current_user: Member = Depends(get_current_active_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    更新成员角色
    
    权限：仅管理员可更新成员角色
    """
    try:
        # 查询目标成员
        query = select(Member).where(Member.id == member_id)
        result = await db.execute(query)
        member = result.scalar_one_or_none()
        
        if not member:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="成员不存在"
            )
        
        old_role = member.role
        new_role = role_update.role
        
        # 防止降级最后一个管理员
        if old_role == UserRole.ADMIN and new_role != UserRole.ADMIN:
            admin_count_query = select(func.count()).where(Member.role == UserRole.ADMIN)
            admin_count_result = await db.execute(admin_count_query)
            admin_count = admin_count_result.scalar()
            
            if admin_count <= 1:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="不能降级最后一个管理员账户"
                )
        
        # 更新角色
        member.role = new_role
        await db.commit()
        await db.refresh(member)
        
        logger.info(f"Member {member_id} role updated from {old_role.value} to {new_role.value} by {current_user.student_id}")
        
        return create_response(
            data=member.get_safe_dict(),
            message=f"成功将 {member.name} 的角色从 {old_role.value} 更新为 {new_role.value}"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update member {member_id} role error: {str(e)}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="更新成员角色失败"
        )


# 更新成员状态
@router.put("/{member_id}/status", response_model=Dict[str, Any])
async def update_member_status(
    member_id: int,
    status_update: MemberStatusUpdate,
    current_user: Member = Depends(get_current_active_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    更新成员状态（启用/禁用）
    
    权限：仅管理员可更新成员状态
    """
    try:
        # 查询目标成员
        query = select(Member).where(Member.id == member_id)
        result = await db.execute(query)
        member = result.scalar_one_or_none()
        
        if not member:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="成员不存在"
            )
        
        # 防止禁用自己
        if member.id == current_user.id and not status_update.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="不能禁用自己的账户"
            )
        
        # 防止禁用最后一个活跃管理员
        if member.is_admin and not status_update.is_active:
            active_admin_query = select(func.count()).where(
                and_(Member.role == UserRole.ADMIN, Member.is_active == True)
            )
            active_admin_result = await db.execute(active_admin_query)
            active_admin_count = active_admin_result.scalar()
            
            if active_admin_count <= 1:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="不能禁用最后一个活跃管理员账户"
                )
        
        old_status = member.is_active
        member.is_active = status_update.is_active
        
        await db.commit()
        await db.refresh(member)
        
        action = "启用" if status_update.is_active else "禁用"
        reason = f"，原因：{status_update.reason}" if status_update.reason else ""
        
        logger.info(f"Member {member_id} status changed from {old_status} to {status_update.is_active} by {current_user.student_id}")
        
        return create_response(
            data=member.get_safe_dict(),
            message=f"成功{action}成员：{member.name}{reason}"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update member {member_id} status error: {str(e)}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="更新成员状态失败"
        )


# 重置成员密码
@router.put("/{member_id}/reset-password", response_model=Dict[str, Any])
async def reset_member_password(
    member_id: int,
    password_reset: PasswordResetRequest,
    current_user: Member = Depends(get_current_active_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    重置成员密码
    
    权限：仅管理员可重置成员密码
    """
    try:
        # 查询目标成员
        query = select(Member).where(Member.id == member_id)
        result = await db.execute(query)
        member = result.scalar_one_or_none()
        
        if not member:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="成员不存在"
            )
        
        # 更新密码
        member.password_hash = get_password_hash(password_reset.new_password)
        await db.commit()
        
        logger.info(f"Password reset for member {member_id} by {current_user.student_id}")
        
        return create_response(
            message=f"成功重置 {member.name} ({member.student_id}) 的密码"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Reset password for member {member_id} error: {str(e)}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="重置密码失败"
        )


# 获取成员统计信息
@router.get("/statistics/overview", response_model=Dict[str, Any])
async def get_member_statistics(
    current_user: Member = Depends(get_current_active_group_leader),
    db: AsyncSession = Depends(get_db)
):
    """
    获取成员统计信息
    
    权限：组长及以上可查看
    """
    try:
        # 基础统计
        total_query = select(func.count()).select_from(Member)
        total_result = await db.execute(total_query)
        total_members = total_result.scalar()
        
        active_query = select(func.count()).where(Member.is_active == True)
        active_result = await db.execute(active_query)
        active_members = active_result.scalar()
        
        verified_query = select(func.count()).where(Member.is_verified == True)
        verified_result = await db.execute(verified_query)
        verified_members = verified_result.scalar()
        
        # 角色统计
        admin_query = select(func.count()).where(Member.role == UserRole.ADMIN)
        admin_result = await db.execute(admin_query)
        admin_count = admin_result.scalar()
        
        leader_query = select(func.count()).where(Member.role == UserRole.GROUP_LEADER)
        leader_result = await db.execute(leader_query)
        group_leader_count = leader_result.scalar()
        
        member_query = select(func.count()).where(Member.role == UserRole.MEMBER)
        member_result = await db.execute(member_query)
        member_count = member_result.scalar()
        
        # 组别分布
        group_query = select(
            Member.group_id,
            func.count().label('count')
        ).where(
            Member.group_id.isnot(None)
        ).group_by(Member.group_id)
        group_result = await db.execute(group_query)
        group_distribution = {str(row[0]): row[1] for row in group_result.fetchall()}
        
        # 近期登录统计（最近7天）
        from datetime import datetime, timedelta
        seven_days_ago = datetime.utcnow() - timedelta(days=7)
        
        recent_login_query = select(
            func.date(Member.last_login).label('date'),
            func.count().label('count')
        ).where(
            Member.last_login >= seven_days_ago
        ).group_by(
            func.date(Member.last_login)
        ).order_by(
            func.date(Member.last_login)
        )
        recent_login_result = await db.execute(recent_login_query)
        recent_logins = [
            {"date": str(row[0]), "count": row[1]} 
            for row in recent_login_result.fetchall()
        ]
        
        statistics_data = {
            "total_members": total_members,
            "active_members": active_members,
            "inactive_members": total_members - active_members,
            "verified_members": verified_members,
            "admin_count": admin_count,
            "group_leader_count": group_leader_count,
            "member_count": member_count,
            "group_distribution": group_distribution,
            "recent_logins": recent_logins
        }
        
        logger.info(f"Member statistics viewed by {current_user.student_id}")
        
        return create_response(
            data=statistics_data,
            message="成功获取成员统计信息"
        )
        
    except Exception as e:
        logger.error(f"Get member statistics error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取统计信息失败"
        )


# 批量操作成员
@router.post("/bulk-operation", response_model=Dict[str, Any])
async def bulk_member_operation(
    operation: BulkMemberOperation,
    current_user: Member = Depends(get_current_active_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    批量操作成员
    
    权限：仅管理员可执行批量操作
    支持的操作：activate, deactivate, delete, set_role, set_group
    """
    try:
        # 查询目标成员
        query = select(Member).where(Member.id.in_(operation.member_ids))
        result = await db.execute(query)
        members = result.scalars().all()
        
        if len(members) != len(operation.member_ids):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="部分成员不存在"
            )
        
        # 执行操作
        success_count = 0
        errors = []
        
        for member in members:
            try:
                if operation.operation == "activate":
                    member.is_active = True
                    success_count += 1
                    
                elif operation.operation == "deactivate":
                    # 防止禁用自己和最后的管理员
                    if member.id == current_user.id:
                        errors.append(f"{member.name}: 不能禁用自己")
                        continue
                    if member.is_admin:
                        admin_count_query = select(func.count()).where(
                            and_(Member.role == UserRole.ADMIN, Member.is_active == True)
                        )
                        admin_count_result = await db.execute(admin_count_query)
                        if admin_count_result.scalar() <= 1:
                            errors.append(f"{member.name}: 不能禁用最后一个管理员")
                            continue
                    member.is_active = False
                    success_count += 1
                    
                elif operation.operation == "delete":
                    # 防止删除自己和最后的管理员
                    if member.id == current_user.id:
                        errors.append(f"{member.name}: 不能删除自己")
                        continue
                    if member.is_admin:
                        admin_count_query = select(func.count()).where(Member.role == UserRole.ADMIN)
                        admin_count_result = await db.execute(admin_count_query)
                        if admin_count_result.scalar() <= 1:
                            errors.append(f"{member.name}: 不能删除最后一个管理员")
                            continue
                    await db.delete(member)
                    success_count += 1
                    
                elif operation.operation == "set_role":
                    new_role = UserRole(operation.operation_data["role"])
                    # 防止降级最后的管理员
                    if member.is_admin and new_role != UserRole.ADMIN:
                        admin_count_query = select(func.count()).where(Member.role == UserRole.ADMIN)
                        admin_count_result = await db.execute(admin_count_query)
                        if admin_count_result.scalar() <= 1:
                            errors.append(f"{member.name}: 不能降级最后一个管理员")
                            continue
                    member.role = new_role
                    success_count += 1
                    
                elif operation.operation == "set_group":
                    member.group_id = operation.operation_data["group_id"]
                    success_count += 1
                    
            except Exception as e:
                errors.append(f"{member.name}: {str(e)}")
        
        await db.commit()
        
        logger.info(f"Bulk operation {operation.operation} executed by {current_user.student_id}, success: {success_count}, errors: {len(errors)}")
        
        return create_response(
            data={
                "success_count": success_count,
                "error_count": len(errors),
                "errors": errors
            },
            message=f"批量操作完成：成功 {success_count} 个，失败 {len(errors)} 个"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Bulk member operation error: {str(e)}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="批量操作失败"
        )


# 辅助函数：手机号脱敏
def _mask_phone(phone: str) -> str:
    """手机号脱敏处理"""
    if not phone or len(phone) < 7:
        return phone
    return phone[:3] + "****" + phone[-4:]


# 健康检查
@router.get("/health", response_model=Dict[str, Any])
async def members_health_check():
    """成员管理服务健康检查"""
    return create_response(
        data={"service": "members", "status": "healthy"},
        message="成员管理服务运行正常"
    )