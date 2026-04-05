"""
依赖注入模块
提供数据库会话、认证和分页的通用依赖项，使用统一消息管理
"""

import logging
from typing import Any, AsyncGenerator, Dict, Generator, List, Optional, Union

from fastapi import Depends, HTTPException, status
from fastapi.exceptions import RequestValidationError
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import ValidationError as PydanticValidationError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_async_session, get_sync_session
from app.core.messages import Messages, get_message
from app.core.security import verify_token
from app.models.member import Member

logger = logging.getLogger(__name__)

# Security scheme
security = HTTPBearer()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Get async database session dependency with enhanced error handling."""
    session = None
    try:
        async for session in get_async_session():
            yield session
            # Session yielded successfully - no additional error handling needed
            break
    except HTTPException:
        # Preserve upstream HTTP exceptions (e.g., 401/403).
        if session:
            try:
                await session.close()
            except Exception:
                pass
        raise
    except (RequestValidationError, PydanticValidationError):
        # Preserve request/body validation failures so they remain 422 instead of
        # being wrapped as generic database errors during dependency cleanup.
        if session:
            try:
                await session.close()
            except Exception:
                pass
        raise
    except Exception as e:
        logger.error(f"Database session dependency error: {e}")
        # Ensure session is properly cleaned up on error
        if session:
            try:
                await session.close()
            except:
                pass  # Ignore cleanup errors
        # Convert connection errors to appropriate HTTP status
        error_msg = str(e).lower()
        if "connection" in error_msg or "timeout" in error_msg or "lost" in error_msg:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=get_message("SYSTEM_ERROR_DATABASE_CONNECTION"),
            )
        else:
            # Generic database error
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=get_message("SYSTEM_ERROR_DATABASE"),
            )


def get_sync_db() -> Generator[Session, None, None]:
    """Get sync database session dependency."""
    yield from get_sync_session()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> Member:
    """
    Get current authenticated user from JWT token.

    Args:
        credentials: HTTP Bearer token credentials
        db: Database session

    Returns:
        Member: Current authenticated user

    Raises:
        HTTPException: If token is invalid or user not found
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=get_message("AUTH_ERROR_CREDENTIALS_VALIDATION"),
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        # Verify and decode token
        payload: Optional[Dict[str, Any]] = verify_token(credentials.credentials)
        if not payload:
            raise credentials_exception

        user_id_str: Optional[Union[str, int]] = payload.get("sub")
        if user_id_str is None:
            raise credentials_exception

        # Handle both string and int types
        user_id = int(user_id_str) if isinstance(user_id_str, str) else user_id_str
    except (ValueError, TypeError) as e:
        logger.warning(f"Invalid token format: {e}")
        raise credentials_exception
    except Exception as e:
        logger.error(f"Token verification error: {e}")
        raise credentials_exception

    # Get user from database with enhanced error handling
    try:
        from sqlalchemy import select
        from sqlalchemy.exc import SQLAlchemyError

        result = await db.execute(select(Member).where(Member.id == user_id))
        user = result.scalar_one_or_none()

        if user is None:
            logger.warning(f"User not found for ID: {user_id}")
            raise credentials_exception

        if not user.is_active:
            logger.warning(f"Inactive user attempted access: {user.student_id}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=get_message("AUTH_ERROR_INACTIVE_USER"),
            )

        return user
    except SQLAlchemyError as e:
        logger.error(f"Database error during user authentication: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=get_message("DATABASE_ERROR_QUERY"),
        )
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        logger.error(f"Unexpected error during user authentication: {e}")
        raise credentials_exception


async def get_current_active_user(
    current_user: Member = Depends(get_current_user),
) -> Member:
    """Get current active user (redundant check for clarity)."""
    return current_user


async def get_admin_user(
    current_user: Member = Depends(get_current_user),
) -> Member:
    """
    Get current user and verify admin role.

    Args:
        current_user: Current authenticated user

    Returns:
        Member: Current user (if admin)

    Raises:
        HTTPException: If user is not admin
    """
    # Direct role comparison to avoid property method async issues
    from app.models.member import UserRole

    if not current_user.role or current_user.role != UserRole.ADMIN:
        logger.warning(
            f"Admin access denied for user {current_user.student_id} "
            f"with role {current_user.role}"
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=get_message("AUTH_ERROR_ADMIN_REQUIRED"),
        )
    return current_user


async def get_group_leader_or_admin(
    current_user: Member = Depends(get_current_user),
) -> Member:
    """
    Get current user and verify group leader or admin role.

    Args:
        current_user: Current authenticated user

    Returns:
        Member: Current user (if group leader or admin)

    Raises:
        HTTPException: If user is not group leader or admin
    """
    # Direct role comparison to avoid property method async issues
    from app.models.member import UserRole

    if not current_user.role or current_user.role not in [
        UserRole.ADMIN,
        UserRole.GROUP_LEADER,
    ]:
        logger.warning(
            f"Group leader/admin access denied for user {current_user.student_id} "
            f"with role {current_user.role}"
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=get_message("AUTH_ERROR_GROUP_LEADER_REQUIRED"),
        )
    return current_user


async def get_current_active_admin(
    current_user: Member = Depends(get_current_user),
) -> Member:
    """
    Get current user and verify admin role and active status.

    Args:
        current_user: Current authenticated user

    Returns:
        Member: Current user (if admin and active)

    Raises:
        HTTPException: If user is not admin or not active
    """
    # 直接检查role字段而不是使用计算属性，避免潜在的greenlet问题
    from app.models.member import UserRole

    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=get_message("AUTH_ERROR_ADMIN_REQUIRED"),
        )
    return current_user


async def get_current_active_group_leader(
    current_user: Member = Depends(get_current_user),
) -> Member:
    """
    Get current user and verify group leader or admin role and active status.

    Args:
        current_user: Current authenticated user

    Returns:
        Member: Current user (if group leader/admin and active)

    Raises:
        HTTPException: If user is not group leader/admin or not active
    """
    # Direct role comparison to avoid property method async issues
    from app.models.member import UserRole

    if current_user.role not in [UserRole.ADMIN, UserRole.GROUP_LEADER]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=get_message("AUTH_ERROR_GROUP_LEADER_REQUIRED"),
        )
    return current_user


class CommonQueryParams:
    """Common query parameters for list endpoints."""

    def __init__(
        self,
        page: int = 1,
        size: int = settings.DEFAULT_PAGE_SIZE,
        search: Optional[str] = None,
        sort_by: Optional[str] = None,
        sort_order: str = "desc",
    ):
        # Validate page and size
        self.page = max(1, page)
        self.size = min(max(1, size), settings.MAX_PAGE_SIZE)
        self.search = search
        self.sort_by = sort_by
        self.sort_order = (
            sort_order.lower() if sort_order.lower() in ["asc", "desc"] else "desc"
        )

    @property
    def offset(self) -> int:
        """Calculate offset for database queries."""
        return (self.page - 1) * self.size

    @property
    def limit(self) -> int:
        """Get limit for database queries."""
        return self.size


def get_query_params(
    page: int = 1,
    size: int = settings.DEFAULT_PAGE_SIZE,
    search: Optional[str] = None,
    sort_by: Optional[str] = None,
    sort_order: str = "desc",
) -> CommonQueryParams:
    """Dependency for common query parameters."""
    return CommonQueryParams(
        page=page, size=size, search=search, sort_by=sort_by, sort_order=sort_order
    )


class TaskQueryParams(CommonQueryParams):
    """Query parameters specific to task endpoints."""

    def __init__(
        self,
        page: int = 1,
        size: int = settings.DEFAULT_PAGE_SIZE,
        search: Optional[str] = None,
        sort_by: Optional[str] = None,
        sort_order: str = "desc",
        status: Optional[str] = None,
        category: Optional[str] = None,
        task_type: Optional[str] = None,
        member_id: Optional[int] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
    ):
        super().__init__(page, size, search, sort_by, sort_order)
        self.status = status
        self.category = category
        self.task_type = task_type
        self.member_id = member_id
        self.date_from = date_from
        self.date_to = date_to


def get_task_query_params(
    page: int = 1,
    size: int = settings.DEFAULT_PAGE_SIZE,
    search: Optional[str] = None,
    sort_by: Optional[str] = None,
    sort_order: str = "desc",
    status: Optional[str] = None,
    category: Optional[str] = None,
    task_type: Optional[str] = None,
    member_id: Optional[int] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
) -> TaskQueryParams:
    """Dependency for task query parameters."""
    return TaskQueryParams(
        page=page,
        size=size,
        search=search,
        sort_by=sort_by,
        sort_order=sort_order,
        status=status,
        category=category,
        task_type=task_type,
        member_id=member_id,
        date_from=date_from,
        date_to=date_to,
    )


class MemberQueryParams(CommonQueryParams):
    """Query parameters specific to member endpoints."""

    def __init__(
        self,
        page: int = 1,
        size: int = settings.DEFAULT_PAGE_SIZE,
        search: Optional[str] = None,
        sort_by: Optional[str] = None,
        sort_order: str = "desc",
        role: Optional[str] = None,
        group_id: Optional[int] = None,
        is_active: Optional[bool] = None,
    ):
        super().__init__(page, size, search, sort_by, sort_order)
        self.role = role
        self.group_id = group_id
        self.is_active = is_active


def get_member_query_params(
    page: int = 1,
    size: int = settings.DEFAULT_PAGE_SIZE,
    search: Optional[str] = None,
    sort_by: Optional[str] = None,
    sort_order: str = "desc",
    role: Optional[str] = None,
    group_id: Optional[int] = None,
    is_active: Optional[bool] = None,
) -> MemberQueryParams:
    """Dependency for member query parameters."""
    return MemberQueryParams(
        page=page,
        size=size,
        search=search,
        sort_by=sort_by,
        sort_order=sort_order,
        role=role,
        group_id=group_id,
        is_active=is_active,
    )


# Response models for common patterns
class PaginatedResponse:
    """Base class for paginated responses."""

    def __init__(self, items: List[Any], total: int, page: int, size: int) -> None:
        self.items = items
        self.total = total
        self.page = page
        self.size = size
        self.pages = (total + size - 1) // size  # Ceiling division
        self.has_next = page < self.pages
        self.has_prev = page > 1


def create_response(
    data: Any = None,
    message: Optional[str] = None,
    message_key: Optional[str] = None,
    status_code: int = 200,
    success: Optional[bool] = None,
    error_code: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
    **message_kwargs: Any,
) -> Dict[str, Any]:
    """创建标准化API响应，支持统一消息管理"""
    # 优先使用message_key获取消息
    if message_key:
        final_message = get_message(message_key, **message_kwargs)
    elif message:
        final_message = message
    else:
        final_message = (
            Messages.GENERAL_SUCCESS if status_code < 400 else Messages.GENERAL_ERROR
        )

    # Use provided success value or calculate from status_code
    success_value = success if success is not None else (status_code < 400)

    response = {
        "success": success_value,
        "message": final_message,
        "data": data,
        "status_code": status_code,
    }

    # Add error_code if provided
    if error_code is not None:
        response["error_code"] = error_code

    # Add details if provided
    if details is not None:
        response["details"] = details

    return response


def create_error_response(
    message: Optional[str] = None,
    message_key: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
    status_code: int = 400,
    **message_kwargs: Any,
) -> Dict[str, Any]:
    """创建标准化API错误响应，支持统一消息管理"""
    # 优先使用message_key获取消息
    if message_key:
        final_message = get_message(message_key, **message_kwargs)
    elif message:
        final_message = message
    else:
        final_message = Messages.GENERAL_ERROR

    return {
        "success": False,
        "message": final_message,
        "details": details or {},
        "status_code": status_code,
    }


def check_user_can_manage_group(user: Member) -> bool:
    """
    Safe utility function to check if user can manage group.
    Avoids async/greenlet issues with property methods.
    """
    from app.models.member import UserRole

    if not user or not hasattr(user, "role") or user.role is None:
        return False
    return user.role in [UserRole.ADMIN, UserRole.GROUP_LEADER]


def check_user_is_admin(user: Member) -> bool:
    """
    Safe utility function to check if user is admin.
    Avoids async/greenlet issues with property methods.
    """
    from app.models.member import UserRole

    if not user or not hasattr(user, "role") or user.role is None:
        return False
    return user.role == UserRole.ADMIN


def check_user_can_access_task(user: Member, task_owner_id: int) -> bool:
    """
    Check if user can access a specific task.
    User can access if they own the task or can manage group.
    """
    if not user:
        return False
    return task_owner_id == user.id or check_user_can_manage_group(user)
