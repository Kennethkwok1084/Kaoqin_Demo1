"""User and profile management APIs migrated from doc_compat."""

import secrets
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import create_response, get_current_active_admin, get_current_user, get_db
from app.core.security import get_password_hash
from app.models.member import Member, UserRole
from app.services.user_sync_service import UserSyncService

router = APIRouter()


def _to_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _to_bool(value: Any, default: bool = False) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "on", "y", "enabled"}


@router.get("/admin/users", response_model=Dict[str, Any])
async def admin_get_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
    search: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    _: Member = Depends(get_current_active_admin),
) -> Dict[str, Any]:
    stmt = select(Member)
    if search:
        key = f"%{search}%"
        stmt = stmt.where(
            (Member.name.ilike(key))
            | (Member.username.ilike(key))
            | (Member.student_id.ilike(key))
        )

    total_stmt = select(func.count()).select_from(stmt.subquery())
    total = _to_int((await db.execute(total_stmt)).scalar(), 0)

    rows = (
        await db.execute(
            stmt.order_by(Member.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
    ).scalars().all()

    data = {
        "list": [
            {
                "id": item.id,
                "username": item.username,
                "name": item.name,
                "student_id": item.student_id,
                "role": item.role.value if item.role else None,
                "is_active": item.is_active,
                "created_at": item.created_at.isoformat() if item.created_at else None,
            }
            for item in rows
        ],
        "page": page,
        "page_size": page_size,
        "total": total,
        "total_pages": (total + page_size - 1) // page_size,
        "has_next": page * page_size < total,
    }
    return create_response(data=data, message="获取用户列表成功")


@router.post("/admin/users", response_model=Dict[str, Any])
async def admin_create_user(
    payload: Dict[str, Any],
    db: AsyncSession = Depends(get_db),
    _: Member = Depends(get_current_active_admin),
) -> Dict[str, Any]:
    username = (payload.get("username") or "").strip()
    name = (payload.get("name") or "").strip()
    student_id = (
        payload.get("student_id") or payload.get("studentNo") or ""
    ).strip() or None
    provided_password = str(payload.get("password") or "").strip()
    generated_password = ""
    if provided_password:
        if len(provided_password) < 8:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="password 长度至少为 8 位",
            )
        password = provided_password
    else:
        generated_password = secrets.token_urlsafe(10)
        password = generated_password
    role_text = (payload.get("role") or "member").strip().lower()

    if not username or not name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="username/name 不能为空",
        )

    role = UserRole.MEMBER
    if role_text == "admin":
        role = UserRole.ADMIN
    elif role_text in {"group_leader", "leader"}:
        role = UserRole.GROUP_LEADER

    exists = (
        await db.execute(select(Member).where(Member.username == username))
    ).scalar_one_or_none()
    if exists:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="用户名已存在")

    user = Member(
        username=username,
        name=name,
        student_id=student_id,
        phone=payload.get("phone"),
        email=payload.get("email"),
        department=payload.get("department") or "信息化建设处",
        class_name=payload.get("class_name") or payload.get("className") or "默认班级",
        password_hash=get_password_hash(password),
        role=role,
        is_active=bool(payload.get("is_active", True)),
        profile_completed=bool(payload.get("profile_completed", True)),
        is_verified=bool(payload.get("is_verified", True)),
    )
    db.add(user)
    await db.flush()
    await UserSyncService(db).sync_member(user, commit=False)
    await db.commit()
    await db.refresh(user)
    data = {
        "id": user.id,
        "username": user.username,
        "name": user.name,
        "student_id": user.student_id,
    }
    if generated_password:
        data["initial_password"] = generated_password

    return create_response(data=data, message="创建用户成功")


@router.put("/admin/users/{user_id}/status", response_model=Dict[str, Any])
async def admin_update_user_status(
    user_id: int,
    payload: Dict[str, Any],
    db: AsyncSession = Depends(get_db),
    _: Member = Depends(get_current_active_admin),
) -> Dict[str, Any]:
    user = (await db.execute(select(Member).where(Member.id == user_id))).scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在")

    is_active = payload.get("is_active")
    if is_active is None:
        is_active = payload.get("status")

    user.is_active = _to_bool(is_active)
    await UserSyncService(db).sync_member(user, commit=False)
    await db.commit()
    return create_response(
        data={"id": user.id, "is_active": user.is_active},
        message="更新用户状态成功",
    )


@router.put("/users/profile", response_model=Dict[str, Any])
async def update_my_profile(
    payload: Dict[str, Any],
    db: AsyncSession = Depends(get_db),
    current_user: Member = Depends(get_current_user),
) -> Dict[str, Any]:
    for field in ["name", "phone", "email", "department", "class_name"]:
        if field in payload:
            setattr(current_user, field, payload[field])
    if "className" in payload:
        current_user.class_name = payload["className"]
    if "profile_completed" in payload:
        current_user.profile_completed = bool(payload["profile_completed"])

    await UserSyncService(db).sync_member(current_user, commit=False)
    await db.commit()
    return create_response(
        data={
            "id": current_user.id,
            "name": current_user.name,
            "phone": current_user.phone,
            "email": current_user.email,
            "department": current_user.department,
            "class_name": current_user.class_name,
        },
        message="更新个人资料成功",
    )
