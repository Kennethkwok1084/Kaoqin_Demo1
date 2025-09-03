"""
角色和权限管理API端点
提供角色创建、更新、删除和权限分配功能
"""

import logging
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException
from fastapi import status as http_status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import (
    create_error_response,
    create_response,
    get_current_active_admin,
    get_current_user,
    get_db,
)
from app.models.member import Member, UserRole

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/", response_model=Dict[str, Any])
async def get_roles(
    current_user: Member = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """获取系统角色列表"""
    try:
        # 系统预定义角色和权限
        roles = [
            {
                "id": 1,
                "name": "管理员",
                "code": "ADMIN",
                "description": "系统管理员，拥有所有权限",
                "permissions": [
                    "user_management",
                    "task_management",
                    "system_config",
                    "data_export",
                    "statistics_view",
                    "approval_management",
                ],
                "userCount": 0,
                "isSystem": True,
                "createdAt": "2025-01-01T00:00:00Z",
                "updatedAt": "2025-01-27T10:30:00Z",
            },
            {
                "id": 2,
                "name": "组长",
                "code": "GROUP_LEADER",
                "description": "组长角色，可以管理组内任务和成员",
                "permissions": [
                    "task_management",
                    "statistics_view",
                    "approval_management",
                ],
                "userCount": 0,
                "isSystem": True,
                "createdAt": "2025-01-01T00:00:00Z",
                "updatedAt": "2025-01-27T10:30:00Z",
            },
            {
                "id": 3,
                "name": "普通成员",
                "code": "MEMBER",
                "description": "普通成员，可以查看和处理分配的任务",
                "permissions": ["task_view", "task_update", "personal_statistics"],
                "userCount": 0,
                "isSystem": True,
                "createdAt": "2025-01-01T00:00:00Z",
                "updatedAt": "2025-01-27T10:30:00Z",
            },
        ]

        # 统计每个角色的用户数量
        for role in roles:
            role_enum = UserRole(role["code"])
            stmt = select(Member).where(Member.role == role_enum)
            result = await db.execute(stmt)
            users = result.scalars().all()
            role["userCount"] = len(users)

        return create_response(
            data={"roles": roles, "total": len(roles)},
            message=f"成功获取角色列表，共 {len(roles)} 个角色",
        )

    except Exception as e:
        logger.error(f"Get roles error: {str(e)}")
        return create_error_response(
            message="获取角色列表失败", details={"error": str(e)}
        )


@router.post("/", response_model=Dict[str, Any])
async def create_role(
    request_data: Dict[str, Any],
    current_user: Member = Depends(get_current_active_admin),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """创建新角色（暂不支持，系统角色预定义）"""
    try:
        raise HTTPException(
            status_code=http_status.HTTP_501_NOT_IMPLEMENTED,
            detail="当前版本暂不支持创建自定义角色，请使用系统预定义角色",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Create role error: {str(e)}")
        return create_error_response(message="创建角色失败", details={"error": str(e)})


@router.put("/{role_id}", response_model=Dict[str, Any])
async def update_role(
    role_id: int,
    request_data: Dict[str, Any],
    current_user: Member = Depends(get_current_active_admin),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """更新角色信息（系统角色不支持修改）"""
    try:
        raise HTTPException(
            status_code=http_status.HTTP_501_NOT_IMPLEMENTED,
            detail="系统预定义角色不支持修改，如需调整权限请联系系统管理员",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update role error: {str(e)}")
        return create_error_response(message="更新角色失败", details={"error": str(e)})


@router.delete("/{role_id}", response_model=Dict[str, Any])
async def delete_role(
    role_id: int,
    current_user: Member = Depends(get_current_active_admin),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """删除角色（系统角色不支持删除）"""
    try:
        raise HTTPException(
            status_code=http_status.HTTP_501_NOT_IMPLEMENTED,
            detail="系统预定义角色不支持删除",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete role error: {str(e)}")
        return create_error_response(message="删除角色失败", details={"error": str(e)})


@router.put("/{role_id}/permissions", response_model=Dict[str, Any])
async def update_role_permissions(
    role_id: int,
    request_data: Dict[str, Any],
    current_user: Member = Depends(get_current_active_admin),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """更新角色权限（系统角色权限固定）"""
    try:
        raise HTTPException(
            status_code=http_status.HTTP_501_NOT_IMPLEMENTED,
            detail="系统预定义角色权限固定，不支持动态修改",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update role permissions error: {str(e)}")
        return create_error_response(
            message="更新角色权限失败", details={"error": str(e)}
        )


@router.get("/permissions", response_model=Dict[str, Any])
async def get_available_permissions(
    current_user: Member = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """获取可用权限列表"""
    try:
        permissions = [
            {
                "code": "user_management",
                "name": "用户管理",
                "description": "管理系统用户、分配角色",
                "category": "用户管理",
            },
            {
                "code": "task_management",
                "name": "任务管理",
                "description": "创建、分配、管理维修任务",
                "category": "任务管理",
            },
            {
                "code": "system_config",
                "name": "系统配置",
                "description": "修改系统参数和配置",
                "category": "系统管理",
            },
            {
                "code": "data_export",
                "name": "数据导出",
                "description": "导出报表和数据文件",
                "category": "数据管理",
            },
            {
                "code": "statistics_view",
                "name": "统计查看",
                "description": "查看系统统计数据和报表",
                "category": "数据管理",
            },
            {
                "code": "approval_management",
                "name": "审批管理",
                "description": "审批协助任务和工时申请",
                "category": "审批流程",
            },
            {
                "code": "task_view",
                "name": "任务查看",
                "description": "查看分配的任务信息",
                "category": "任务管理",
            },
            {
                "code": "task_update",
                "name": "任务更新",
                "description": "更新任务状态和进度",
                "category": "任务管理",
            },
            {
                "code": "personal_statistics",
                "name": "个人统计",
                "description": "查看个人工作统计数据",
                "category": "数据管理",
            },
        ]

        return create_response(
            data={
                "permissions": permissions,
                "categories": list(set(p["category"] for p in permissions)),
                "total": len(permissions),
            },
            message=f"成功获取权限列表，共 {len(permissions)} 个权限",
        )

    except Exception as e:
        logger.error(f"Get permissions error: {str(e)}")
        return create_error_response(
            message="获取权限列表失败", details={"error": str(e)}
        )


@router.get("/{role_id}/users", response_model=Dict[str, Any])
async def get_role_users(
    role_id: int,
    current_user: Member = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """获取指定角色的用户列表"""
    try:
        # 根据role_id映射到UserRole枚举
        role_mapping = {1: UserRole.ADMIN, 2: UserRole.GROUP_LEADER, 3: UserRole.MEMBER}

        if role_id not in role_mapping:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND, detail="角色不存在"
            )

        target_role = role_mapping[role_id]

        # 查询该角色的所有用户
        stmt = select(Member).where(Member.role == target_role)
        result = await db.execute(stmt)
        users = result.scalars().all()

        user_list = []
        for user in users:
            user_list.append(
                {
                    "id": user.id,
                    "name": user.name,
                    "username": user.username,
                    "email": user.email,
                    "isActive": user.is_active,
                    "createdAt": (
                        user.created_at.isoformat() if user.created_at else None
                    ),
                    "lastLoginAt": (
                        user.last_login.isoformat() if user.last_login else None
                    ),
                }
            )

        return create_response(
            data={
                "roleId": role_id,
                "roleName": target_role.value,
                "users": user_list,
                "total": len(user_list),
            },
            message=f"成功获取角色用户列表，共 {len(user_list)} 个用户",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get role users error: {str(e)}")
        return create_error_response(
            message="获取角色用户列表失败", details={"error": str(e)}
        )
