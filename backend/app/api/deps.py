"""
Dependency injection module for FastAPI.
Provides common dependencies for database sessions, authentication, and pagination.
"""

from typing import Generator, Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from app.core.database import get_async_session, get_sync_session
from app.core.config import settings
from app.models.member import Member, UserRole
from app.core.security import verify_token


# Security scheme
security = HTTPBearer()


async def get_db() -> AsyncSession:
    """Get async database session dependency."""
    async for session in get_async_session():
        yield session


def get_sync_db() -> Generator[Session, None, None]:
    """Get sync database session dependency."""
    with get_sync_session() as session:
        yield session


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
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
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # Verify and decode token
        payload = verify_token(credentials.credentials)
        user_id_str = payload.get("sub")
        if user_id_str is None:
            raise credentials_exception
        user_id = int(user_id_str)  # Convert string to integer
    except Exception:
        raise credentials_exception
    
    # Get user from database
    from sqlalchemy import select
    result = await db.execute(select(Member).where(Member.id == user_id))
    user = result.scalar_one_or_none()
    
    if user is None:
        raise credentials_exception
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user"
        )
    
    return user


async def get_current_active_user(
    current_user: Member = Depends(get_current_user)
) -> Member:
    """Get current active user (redundant check for clarity)."""
    return current_user


async def get_admin_user(
    current_user: Member = Depends(get_current_user)
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
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    return current_user


async def get_group_leader_or_admin(
    current_user: Member = Depends(get_current_user)
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
    if not current_user.can_manage_group:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions. Group leader or admin role required."
        )
    return current_user


async def get_current_active_admin(
    current_user: Member = Depends(get_current_user)
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
            detail="Admin privileges required"
        )
    return current_user


async def get_current_active_group_leader(
    current_user: Member = Depends(get_current_user)
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
    if not current_user.can_manage_group:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Group leader or admin privileges required"
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
        sort_order: str = "desc"
    ):
        # Validate page and size
        self.page = max(1, page)
        self.size = min(max(1, size), settings.MAX_PAGE_SIZE)
        self.search = search
        self.sort_by = sort_by
        self.sort_order = sort_order.lower() if sort_order.lower() in ["asc", "desc"] else "desc"
    
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
    sort_order: str = "desc"
) -> CommonQueryParams:
    """Dependency for common query parameters."""
    return CommonQueryParams(
        page=page,
        size=size,
        search=search,
        sort_by=sort_by,
        sort_order=sort_order
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
        date_to: Optional[str] = None
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
    date_to: Optional[str] = None
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
        date_to=date_to
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
        is_active: Optional[bool] = None
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
    is_active: Optional[bool] = None
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
        is_active=is_active
    )


# Response models for common patterns
class PaginatedResponse:
    """Base class for paginated responses."""
    
    def __init__(self, items: list, total: int, page: int, size: int):
        self.items = items
        self.total = total
        self.page = page
        self.size = size
        self.pages = (total + size - 1) // size  # Ceiling division
        self.has_next = page < self.pages
        self.has_prev = page > 1


def create_response(
    data: any = None,
    message: str = "Success",
    status_code: int = 200
) -> dict:
    """Create standardized API response."""
    return {
        "success": status_code < 400,
        "message": message,
        "data": data,
        "status_code": status_code
    }


def create_error_response(
    message: str = "An error occurred",
    details: dict = None,
    status_code: int = 400
) -> dict:
    """Create standardized API error response."""
    return {
        "success": False,
        "message": message,
        "details": details or {},
        "status_code": status_code
    }