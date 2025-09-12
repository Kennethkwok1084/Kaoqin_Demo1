"""
全新的成员管理API
完全重构后的业务逻辑和接口设计
"""

import logging
import time
from datetime import date
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import JSONResponse
from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import (
    create_response,
    get_current_active_admin,
    get_current_active_user,
    get_db,
)
from app.core.security import get_password_hash, verify_password
from app.models.member import Member, UserRole
from app.schemas.member import (
    MemberCreate,
    MemberImportRequest,
    MemberUpdate,
    PasswordChangeRequest,
)

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/", response_model=Dict[str, Any])
async def get_members(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    search: Optional[str] = Query(None, description="搜索关键词"),
    role: Optional[str] = Query(None, description="角色筛选"),
    is_active: Optional[bool] = Query(None, description="状态筛选"),
    department: Optional[str] = Query(None, description="部门筛选"),
    class_name: Optional[str] = Query(None, description="班级筛选"),
    current_user: Member = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """
    获取成员列表
    支持分页、搜索和多字段筛选
    """
    try:
        # 构建查询条件
        query = select(Member)

        # 搜索条件
        if search:
            search_pattern = f"%{search}%"
            query = query.where(
                or_(
                    Member.username.ilike(search_pattern),
                    Member.name.ilike(search_pattern),
                    Member.student_id.ilike(search_pattern),
                )
            )

        # 角色筛选
        if role and role in [r.value for r in UserRole]:
            query = query.where(Member.role == UserRole(role))

        # 状态筛选
        if is_active is not None:
            query = query.where(Member.is_active == is_active)

        # 部门筛选
        if department:
            query = query.where(Member.department.ilike(f"%{department}%"))

        # 班级筛选
        if class_name:
            query = query.where(Member.class_name.ilike(f"%{class_name}%"))

        # 获取总数
        count_query = select(func.count()).select_from(query.subquery())
        result = await db.execute(count_query)
        total = result.scalar()

        # 分页查询
        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size).order_by(Member.created_at.desc())

        result = await db.execute(query)
        members = result.scalars().all()

        # 构建响应数据
        member_list = []
        for member in members:
            if hasattr(member, "get_safe_dict"):
                member_dict = member.get_safe_dict()
                member_list.append(member_dict)

        total_pages = ((total or 0) + page_size - 1) // page_size

        return create_response(
            data={
                "items": member_list,
                "total": total,
                "page": page,
                "page_size": page_size,
                "total_pages": total_pages,
            },
            message=f"成功获取成员列表，共 {total} 条记录",
        )

    except Exception as e:
        logger.error(f"获取成员列表失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="获取成员列表失败"
        )


@router.get("/{member_id}", response_model=Dict[str, Any])
async def get_member(
    member_id: int,
    current_user: Member = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """
    获取单个成员详情
    """
    try:
        query = select(Member).where(Member.id == member_id)
        result = await db.execute(query)
        member = result.scalar_one_or_none()

        if not member:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="成员不存在"
            )

        # 权限检查：管理员和组长可查看所有，普通用户只能查看自己
        if not current_user.can_manage_group and current_user.id != member_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="无权限查看该成员信息"
            )

        return create_response(data=member.get_safe_dict(), message="成功获取成员信息")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取成员详情失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="获取成员详情失败"
        )


@router.post("/", response_model=Dict[str, Any])
async def create_member(
    member_data: MemberCreate,
    current_user: Member = Depends(get_current_active_admin),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """
    创建新成员
    仅管理员可操作
    """
    try:
        # 检查用户名是否已存在
        query = select(Member).where(Member.username == member_data.username)
        result = await db.execute(query)
        if result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"用户名 {member_data.username} 已存在",
            )

        # 检查学号是否已存在（仅当学号不为空时）
        if member_data.student_id:
            query = select(Member).where(Member.student_id == member_data.student_id)
            result = await db.execute(query)
            if result.scalar_one_or_none():
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"学号 {member_data.student_id} 已存在",
                )

        # 创建新成员
        new_member = Member(
            username=member_data.username,
            name=member_data.name,
            student_id=member_data.student_id,
            phone=member_data.phone,
            department=member_data.department,
            class_name=member_data.class_name,
            join_date=member_data.join_date,
            password_hash=get_password_hash(member_data.password),
            role=member_data.role,
            is_active=member_data.is_active,
            is_verified=False,
        )

        db.add(new_member)
        await db.commit()
        await db.refresh(new_member)

        logger.info(f"新成员创建成功: {new_member.username} by {current_user.username}")

        return create_response(
            data=new_member.get_safe_dict(),
            message=f"成功创建成员：{new_member.name} ({new_member.student_id})",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"创建成员失败: {str(e)}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="创建成员失败"
        )


@router.put("/{member_id}", response_model=Dict[str, Any])
async def update_member(
    member_id: int,
    member_data: MemberUpdate,
    current_user: Member = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """
    更新成员信息
    管理员可更新所有，普通用户只能更新自己的部分信息
    """
    try:
        query = select(Member).where(Member.id == member_id)
        result = await db.execute(query)
        member = result.scalar_one_or_none()

        if not member:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="成员不存在"
            )

        # 权限检查
        can_update_all = current_user.can_manage_group
        is_self_update = current_user.id == member_id

        if not can_update_all and not is_self_update:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="无权限更新该成员信息"
            )

        # 更新字段
        update_data = member_data.dict(exclude_unset=True)

        # 普通用户只能更新部分字段
        if not can_update_all:
            allowed_fields = {"username", "phone"}
            update_data = {k: v for k, v in update_data.items() if k in allowed_fields}

        # 检查用户名唯一性
        if "username" in update_data and update_data["username"] != member.username:
            query = select(Member).where(
                and_(Member.username == update_data["username"], Member.id != member_id)
            )
            result = await db.execute(query)
            if result.scalar_one_or_none():
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"用户名 {update_data['username']} 已存在",
                )

        # 应用更新
        for field, value in update_data.items():
            setattr(member, field, value)

        await db.commit()
        await db.refresh(member)

        logger.info(f"成员信息更新: {member.username} by {current_user.username}")

        return create_response(data=member.get_safe_dict(), message="成员信息更新成功")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新成员信息失败: {str(e)}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="更新成员信息失败"
        )


@router.delete("/{member_id}", response_model=Dict[str, Any])
async def delete_member(
    member_id: int,
    current_user: Member = Depends(get_current_active_admin),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """
    删除成员
    仅管理员可操作
    """
    try:
        query = select(Member).where(Member.id == member_id)
        result = await db.execute(query)
        member = result.scalar_one_or_none()

        if not member:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="成员不存在"
            )

        # 不能删除自己
        if member.id == current_user.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="不能删除自己的账户"
            )

        member_name = member.name
        member_username = member.username

        await db.delete(member)
        await db.commit()

        logger.info(f"成员删除: {member_username} by {current_user.username}")

        return create_response(
            data={"deleted_id": member_id}, message=f"成功删除成员：{member_name}"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除成员失败: {str(e)}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="删除成员失败"
        )


@router.post("/import", response_model=Dict[str, Any])
async def import_members(
    import_data: MemberImportRequest,
    current_user: Member = Depends(get_current_active_admin),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """
    批量导入成员
    全新的Excel处理逻辑，避免greenlet问题
    """
    logger.info(f"开始批量导入成员，操作者: {current_user.username}")

    total_processed = len(import_data.members)
    successful_imports = 0
    failed_imports = 0
    skipped_duplicates = 0
    errors = []

    timestamp = int(time.time())

    for index, member_item in enumerate(import_data.members):
        try:
            # 生成用户名（如果没有提供）
            username = member_item.username
            if not username:
                username = f"user_{timestamp}_{index + 1:03d}"

            # 检查重复（只有在有值的情况下才检查）
            duplicate_conditions = []
            if username:
                duplicate_conditions.append(Member.username == username)
            if member_item.student_id:
                duplicate_conditions.append(Member.student_id == member_item.student_id)

            existing_member = None
            if duplicate_conditions:
                duplicate_check = select(Member).where(or_(*duplicate_conditions))
                result = await db.execute(duplicate_check)
                existing_member = result.scalar_one_or_none()

            if existing_member:
                if import_data.skip_duplicates:
                    skipped_duplicates += 1
                    logger.info(
                        f"跳过重复成员: {member_item.name} "
                        f"({member_item.student_id or username})"
                    )
                    continue
                else:
                    failed_imports += 1
                    duplicate_field = (
                        "用户名" if existing_member.username == username else "学号"
                    )
                    errors.append(
                        f"第{index + 1}行: {duplicate_field}已存在 - {member_item.name}"
                    )
                    continue

            # 角色映射
            role_mapping = {
                "admin": UserRole.ADMIN,
                "group_leader": UserRole.GROUP_LEADER,
                "member": UserRole.MEMBER,
                "guest": UserRole.GUEST,
            }
            role = role_mapping.get(member_item.role or "member", UserRole.MEMBER)

            # 创建新成员，确保所有必填字段都有值
            try:
                new_member = Member(
                    username=username,
                    name=member_item.name.strip(),
                    student_id=(
                        member_item.student_id.strip()
                        if member_item.student_id
                        else None
                    ),
                    phone=member_item.phone.strip() if member_item.phone else None,
                    department=(member_item.department or "信息化建设处").strip(),
                    class_name=member_item.class_name.strip(),
                    join_date=date.today(),
                    password_hash=get_password_hash("123456"),
                    role=role,
                    is_active=True,
                    is_verified=False,
                    profile_completed=False,
                )
            except Exception as create_error:
                failed_imports += 1
                errors.append(f"第{index + 1}行: 数据创建失败 - {str(create_error)}")
                logger.error(f"创建成员对象失败: {str(create_error)}")
                continue

            db.add(new_member)
            await db.flush()  # 获取ID但不提交

            successful_imports += 1
            logger.info(f"成功创建成员: {new_member.name} ({new_member.student_id})")

        except Exception as e:
            failed_imports += 1
            error_msg = f"第{index + 1}行: {str(e)}"
            errors.append(error_msg)
            logger.error(f"导入第{index + 1}行失败: {str(e)}")

    # 提交事务
    if successful_imports > 0:
        try:
            await db.commit()
            logger.info(f"批量导入提交成功: {successful_imports} 个成员")
        except Exception as e:
            await db.rollback()
            logger.error(f"批量导入提交失败: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="批量导入提交失败",
            )

    result_message = (
        f"导入完成：成功 {successful_imports} 条，"
        f"失败 {failed_imports} 条，跳过 {skipped_duplicates} 条"
    )

    return create_response(
        data={
            "total_processed": total_processed,
            "successful_imports": successful_imports,
            "failed_imports": failed_imports,
            "skipped_duplicates": skipped_duplicates,
            "errors": errors[:10],  # 限制错误数量
        },
        message=result_message,
    )


@router.post("/{member_id}/change-password", response_model=Dict[str, Any])
async def change_password(
    member_id: int,
    password_data: PasswordChangeRequest,
    current_user: Member = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """
    修改密码
    用户只能修改自己的密码，管理员可以重置任何人的密码
    """
    try:
        query = select(Member).where(Member.id == member_id)
        result = await db.execute(query)
        member = result.scalar_one_or_none()

        if not member:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="成员不存在"
            )

        # 权限检查
        if current_user.id != member_id and not current_user.is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="无权限修改该成员密码"
            )

        # 验证旧密码（仅当修改自己的密码时）
        if current_user.id == member_id:
            if not verify_password(password_data.old_password, member.password_hash):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST, detail="旧密码错误"
                )

        # 更新密码
        member.password_hash = get_password_hash(password_data.new_password)
        await db.commit()

        logger.info(f"密码修改成功: {member.username} by {current_user.username}")

        return create_response(
            data={"updated_member_id": member_id}, message="密码修改成功"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"修改密码失败: {str(e)}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="修改密码失败"
        )


@router.get("/stats/overview", response_model=Dict[str, Any])
async def get_member_stats(
    current_user: Member = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """
    获取成员统计信息
    """
    try:
        # 总成员数
        total_query = select(func.count(Member.id))
        result = await db.execute(total_query)
        total_members = result.scalar()

        # 在职成员数
        active_query = select(func.count(Member.id)).where(Member.is_active)
        result = await db.execute(active_query)
        active_members = result.scalar()

        # 离职成员数
        inactive_members = (total_members or 0) - (active_members or 0)

        # 按角色统计
        role_stats = {}
        for role in UserRole:
            role_query = select(func.count(Member.id)).where(Member.role == role)
            result = await db.execute(role_query)
            role_stats[role.value] = result.scalar()

        # 按部门统计
        dept_query = select(Member.department, func.count(Member.id)).group_by(
            Member.department
        )
        result = await db.execute(dept_query)
        dept_stats = {dept: count for dept, count in result.fetchall()}

        return create_response(
            data={
                "total_members": total_members,
                "active_members": active_members,
                "inactive_members": inactive_members,
                "role_stats": role_stats,
                "department_stats": dept_stats,
            },
            message="成员统计信息获取成功",
        )

    except Exception as e:
        logger.error(f"获取成员统计失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="获取成员统计失败"
        )


@router.get("/health", response_model=Dict[str, Any])
async def members_health_check() -> Dict[str, Any]:
    """成员管理模块健康检查"""
    return create_response(
        data={"module": "members", "status": "healthy", "version": "2.0"},
        message="成员管理模块运行正常",
    )


@router.post("/{member_id}/complete-profile")
async def complete_profile(
    member_id: int,
    profile_data: MemberUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: Member = Depends(get_current_active_user),
) -> JSONResponse:
    """
    完善个人信息
    用于首次登录时完善用户信息
    """
    logger.info(f"User {current_user.id} completing profile for member {member_id}")

    # 检查权限：只能完善自己的信息或管理员可以完善任何人的信息
    if current_user.id != member_id and current_user.role != UserRole.ADMIN:
        logger.warning(
            f"User {current_user.id} attempted to complete profile "
            f"for member {member_id}"
        )
        raise HTTPException(status_code=403, detail="无权限完善此用户信息")

    try:
        # 查询成员
        result = await db.execute(select(Member).where(Member.id == member_id))
        member = result.scalar_one_or_none()

        if not member:
            raise HTTPException(status_code=404, detail="成员不存在")

        # 更新信息
        update_data = profile_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(member, field, value)

        # 标记为已完善信息
        member.profile_completed = True

        await db.commit()
        await db.refresh(member)

        logger.info(f"Profile completed for member {member_id}")

        # 返回更新后的成员信息
        response_data = create_response(
            data={
                "id": member.id,
                "username": member.username,
                "profile_completed": member.profile_completed,
                "message": "个人信息完善成功",
            }
        )
        return JSONResponse(content=response_data)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error completing profile for member {member_id}: {str(e)}")
        await db.rollback()
        raise HTTPException(status_code=500, detail="完善信息失败")
