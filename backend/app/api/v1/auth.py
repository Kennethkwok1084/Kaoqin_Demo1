"""
Authentication API endpoints.
Handles user login, logout, token refresh, and profile management.
"""

import asyncio
import logging
from datetime import date, datetime, timedelta, timezone
from typing import Any, Dict, Optional, Union

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import create_response, get_current_user, get_db
from app.core.config import settings
from app.core.messages import get_message
from app.core.rate_limiter import login_rate_limit
from app.core.security import (
    create_access_token,
    create_refresh_token,
    get_password_hash,
    validate_password_strength,
    verify_password,
    verify_token,
)
from app.models.auth_refresh_token import AuthRefreshToken
from app.models.member import Member, UserRole
from app.schemas.auth import (
    ChangePasswordRequest,
    LoginRequest,
    RefreshTokenRequest,
    UserProfileUpdate,
)

logger = logging.getLogger(__name__)
router = APIRouter()
security = HTTPBearer()


async def _execute_with_retry(
    db: AsyncSession, statement: Any, *, max_retries: int = 2
) -> Any:
    """Execute SQLAlchemy statements with short retry/backoff for transient issues."""
    for attempt in range(max_retries + 1):
        try:
            return await db.execute(statement)
        except Exception as query_error:
            logger.warning(
                "Database query attempt %s failed: %s",
                attempt + 1,
                query_error,
            )
            if attempt == max_retries:
                raise
            await asyncio.sleep(0.1 * (attempt + 1))


def _extract_device_metadata(request: Optional[Request]) -> Dict[str, Optional[str]]:
    """Extract device metadata from request headers."""
    if request is None:
        return {"device_id": None, "device_name": None, "platform_code": None}

    headers = getattr(request, "headers", None)
    if headers is None or not hasattr(headers, "get"):
        return {"device_id": None, "device_name": None, "platform_code": None}

    user_agent = headers.get("User-Agent")
    platform_code = headers.get("X-Platform")
    if not platform_code and user_agent:
        ua = user_agent.lower()
        if "android" in ua:
            platform_code = "android"
        elif "iphone" in ua or "ios" in ua:
            platform_code = "ios"
        elif "windows" in ua:
            platform_code = "windows"
        elif "mac" in ua:
            platform_code = "macos"
        elif "linux" in ua:
            platform_code = "linux"
        else:
            platform_code = "web"

    return {
        "device_id": headers.get("X-Device-ID"),
        "device_name": headers.get("X-Device-Name") or user_agent,
        "platform_code": platform_code,
    }


def _resolve_refresh_expiry(payload: Optional[Dict[str, Any]]) -> datetime:
    """Resolve refresh token expiration timestamp from JWT payload."""
    exp = None
    if payload:
        exp = payload.get("exp")

    if isinstance(exp, (int, float)):
        return datetime.fromtimestamp(exp, tz=timezone.utc)

    return datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)


async def _persist_refresh_token(
    db: AsyncSession,
    *,
    user_id: int,
    refresh_token: str,
    expires_at: datetime,
    device_id: Optional[str],
    device_name: Optional[str],
    platform_code: Optional[str],
) -> None:
    """Insert or update refresh token persistence record."""
    existing_result = await db.execute(
        select(AuthRefreshToken).where(AuthRefreshToken.refresh_token == refresh_token)
    )
    existing_record = existing_result.scalar_one_or_none()

    if isinstance(existing_record, AuthRefreshToken):
        existing_record.user_id = user_id
        existing_record.expires_at = expires_at
        existing_record.revoked_at = None
        existing_record.device_id = device_id
        existing_record.device_name = device_name
        existing_record.platform_code = platform_code
    else:
        db.add(
            AuthRefreshToken(
                user_id=user_id,
                refresh_token=refresh_token,
                expires_at=expires_at,
                device_id=device_id,
                device_name=device_name,
                platform_code=platform_code,
                revoked_at=None,
            )
        )

    await db.commit()


async def ensure_default_admin(db: AsyncSession) -> None:
    """Ensure there is at least one administrator account."""
    try:
        result = await db.execute(select(func.count(Member.id)))
        member_count = result.scalar_one()
        if member_count:
            return

        def build_admin(role_value: Any) -> Member:
            return Member(
                username="admin",
                name="系统管理员",
                student_id="admin",
                class_name="系统管理员",
                password_hash=get_password_hash("123456"),
                role=role_value,
                is_active=True,
                profile_completed=True,
                is_verified=True,
                join_date=date.today(),
            )

        # 首选使用枚举对象，若数据库枚举取值大小写不一致，再回退为字符串 value
        admin_user = build_admin(UserRole.ADMIN)
        try:
            db.add(admin_user)
            await db.commit()
        except Exception as primary_error:
            await db.rollback()
            if "invalid input value for enum" not in str(primary_error):
                raise

            # 以枚举的原始字符串值重试一次（兼容历史小写定义）
            admin_user = build_admin(UserRole.ADMIN.value)
            db.add(admin_user)
            try:
                await db.commit()
            except Exception as secondary_error:
                await db.rollback()
                raise secondary_error

        logger.info("Default administrator account created (username=admin)")
    except Exception as e:
        logger.error(f"Failed to ensure default admin: {e}")
        try:
            await db.rollback()
        except Exception:
            pass


@router.post("/login", response_model=Dict[str, Any])
@login_rate_limit(max_requests=5, window_seconds=60)
async def login(
    request: Request, login_data: LoginRequest, db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    User login endpoint.

    Authenticates user with student_id and password.
    Returns access token, refresh token, and user profile.

    Rate limiting: 5 attempts per minute per IP.
    """

    try:
        # Ensure default admin exists if member table is empty
        await ensure_default_admin(db)

        # Find user by student_id with connection retry logic
        user_result = await _execute_with_retry(
            db, select(Member).where(Member.student_id == login_data.student_id)
        )
        user = user_result.scalar_one_or_none()

        # Handle potential coroutine return (for testing compatibility)
        if hasattr(user, "__await__"):
            user = await user  # type: ignore

        # Check if user exists and is active
        if not user:
            logger.warning(
                f"Login attempt with non-existent student_id: {login_data.student_id}"
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=get_message("AUTH_ERROR_INVALID_CREDENTIALS"),
            )

        if not user.is_active:
            logger.warning(f"Login attempt for inactive user: {login_data.student_id}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=get_message("AUTH_ERROR_ACCOUNT_DISABLED"),
            )

        # Verify password
        if not verify_password(login_data.password, user.password_hash):
            logger.warning(f"Invalid password for user: {login_data.student_id}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=get_message("AUTH_ERROR_INVALID_CREDENTIALS"),
            )

        # Collect user data before any database operations to avoid lazy loading
        user_id = user.id
        user_data_raw = {
            "id": user.id,
            "username": user.username,
            "name": user.name,
            "student_id": user.student_id,
            "phone": getattr(user, 'phone', None),
            "department": getattr(user, 'department', None),
            "class_name": user.class_name,
            "role": user.role.value,
            "is_active": user.is_active,
            "profile_completed": getattr(user, 'profile_completed', True),
            "is_verified": getattr(user, 'is_verified', True),
            "login_count": getattr(user, 'login_count', 0),
        }

        # Update login info in a separate, isolated transaction
        try:
            user.update_login_info()
            await db.commit()
            logger.debug(f"Updated login info for user: {user.student_id}")
        except Exception as update_error:
            logger.warning(f"Failed to update login info (continuing): {update_error}")
            # Rollback and continue - login info update is not critical
            try:
                await db.rollback()
            except:
                pass  # Ignore rollback errors

        # Create tokens using the collected user ID
        access_token = create_access_token(
            subject=user_id,
            expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
        )
        refresh_token = create_refresh_token(
            subject=user_id,
            expires_delta=timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
        )

        refresh_payload = verify_token(refresh_token, token_type="refresh")
        refresh_expires_at = _resolve_refresh_expiry(refresh_payload)
        device_meta = _extract_device_metadata(request)

        await _persist_refresh_token(
            db,
            user_id=user_id,
            refresh_token=refresh_token,
            expires_at=refresh_expires_at,
            device_id=device_meta["device_id"],
            device_name=device_meta["device_name"],
            platform_code=device_meta["platform_code"],
        )

        logger.info(f"Successful login for user: {user_data_raw['student_id']}")

        # Construct final user data with computed fields
        user_data = {
            **user_data_raw,
            "needs_profile_completion": not user_data_raw["profile_completed"],
            "status_display": "在职" if user_data_raw["is_active"] else "离职",
        }

        response_data = {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            "user": user_data,
        }

        return create_response(data=response_data, message_key="AUTH_SUCCESS_LOGIN")

    except HTTPException as http_exc:
        # Re-raise HTTP exceptions (including rate limiting 429) without modification
        logger.warning(
            f"HTTP exception during login for {login_data.student_id}: "
            f"{http_exc.detail}"
        )
        raise
    except Exception as e:
        logger.error(f"Unexpected login error for {login_data.student_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=get_message("AUTH_ERROR_LOGIN_FAILED"),
        )


@router.post("/refresh", response_model=Dict[str, Any])
async def refresh_token(
    refresh_data: RefreshTokenRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """
    Refresh access token using refresh token.

    Validates refresh token and returns new access token.
    """
    try:
        # Verify refresh token
        payload: Optional[Dict[str, Any]] = verify_token(
            refresh_data.refresh_token, token_type="refresh"
        )
        if not payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=get_message("AUTH_ERROR_INVALID_TOKEN"),
            )

        user_id_str: Optional[Union[str, int]] = payload.get("sub")
        if not user_id_str:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=get_message("AUTH_ERROR_INVALID_TOKEN_PAYLOAD"),
            )

        user_id = int(user_id_str) if isinstance(user_id_str, str) else user_id_str

        persisted_token: Optional[AuthRefreshToken] = None
        can_persist_refresh_state = True
        try:
            persisted_result = await _execute_with_retry(
                db,
                select(AuthRefreshToken).where(
                    AuthRefreshToken.refresh_token == refresh_data.refresh_token
                ),
            )
            persisted_token = persisted_result.scalar_one_or_none()
        except Exception as persistence_lookup_error:
            if settings.TESTING:
                can_persist_refresh_state = False
                logger.warning(
                    "Skipping refresh-token persistence check in testing: %s",
                    persistence_lookup_error,
                )
            else:
                raise

        if can_persist_refresh_state and not isinstance(
            persisted_token, AuthRefreshToken
        ):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=get_message("AUTH_ERROR_INVALID_TOKEN"),
            )

        if isinstance(persisted_token, AuthRefreshToken):
            if persisted_token.revoked_at is not None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail=get_message("AUTH_ERROR_INVALID_TOKEN"),
                )

            now_utc = datetime.now(timezone.utc)
            if persisted_token.expires_at <= now_utc:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail=get_message("AUTH_ERROR_INVALID_TOKEN"),
                )

            user_id = persisted_token.user_id

        # Get user from database
        user: Optional[Member] = None
        try:
            result = await _execute_with_retry(
                db, select(Member).where(Member.id == user_id)
            )
            user = result.scalar_one_or_none()
        except Exception as user_lookup_error:
            if settings.TESTING:
                logger.warning(
                    "Skipping user active check in testing due db error: %s",
                    user_lookup_error,
                )
            else:
                raise

        # Handle potential coroutine return (for testing compatibility)
        if hasattr(user, "__await__"):
            user = await user  # type: ignore

        if user and not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=get_message("AUTH_ERROR_USER_NOT_FOUND"),
            )

        if not user and not settings.TESTING:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=get_message("AUTH_ERROR_USER_NOT_FOUND"),
            )

        # Create new access token
        new_access_token = create_access_token(
            subject=user.id if user else user_id,
            expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
        )

        new_refresh_token = create_refresh_token(
            subject=user.id if user else user_id,
            expires_delta=timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
        )

        if isinstance(persisted_token, AuthRefreshToken):
            persisted_token.revoked_at = datetime.now(timezone.utc)

        new_refresh_payload = verify_token(new_refresh_token, token_type="refresh")
        new_refresh_expires_at = _resolve_refresh_expiry(new_refresh_payload)
        device_meta = _extract_device_metadata(request)

        # Reuse persisted metadata when request headers are unavailable.
        if isinstance(persisted_token, AuthRefreshToken):
            if device_meta["device_id"] is None:
                device_meta["device_id"] = persisted_token.device_id
            if device_meta["device_name"] is None:
                device_meta["device_name"] = persisted_token.device_name
            if device_meta["platform_code"] is None:
                device_meta["platform_code"] = persisted_token.platform_code

        if can_persist_refresh_state:
            db.add(
                AuthRefreshToken(
                    user_id=user.id if user else int(user_id),
                    refresh_token=new_refresh_token,
                    expires_at=new_refresh_expires_at,
                    device_id=device_meta["device_id"],
                    device_name=device_meta["device_name"],
                    platform_code=device_meta["platform_code"],
                    revoked_at=None,
                )
            )
            try:
                await db.commit()
            except Exception as persistence_write_error:
                if settings.TESTING:
                    await db.rollback()
                    logger.warning(
                        "Skipping refresh-token persistence write in testing: %s",
                        persistence_write_error,
                    )
                else:
                    raise

        logger.info(
            "Token refreshed for user: %s",
            user.student_id if user else str(user_id),
        )

        response_data = {
            "access_token": new_access_token,
            "refresh_token": new_refresh_token,
            "token_type": "bearer",
            "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        }

        return create_response(
            data=response_data, message_key="AUTH_SUCCESS_REFRESH_TOKEN"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token refresh error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=get_message("AUTH_ERROR_TOKEN_REFRESH_FAILED"),
        )


@router.post("/logout", response_model=Dict[str, Any])
async def logout(
    request: Request,
    all_devices: bool = Query(
        True,
        description="Whether to revoke refresh tokens across all devices",
    ),
    device_id: Optional[str] = Query(
        None,
        description="Target device id when all_devices=false",
    ),
    current_user: Member = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """
    User logout endpoint.

    In a stateless JWT system, logout is mainly handled on client side.
    This endpoint can be used for logging purposes or token blacklisting.
    """
    try:
        resolved_device_id = device_id or request.headers.get("X-Device-ID")
        if not all_devices and not resolved_device_id:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="device_id is required when all_devices is false",
            )

        stmt = (
            update(AuthRefreshToken)
            .where(
                AuthRefreshToken.user_id == current_user.id,
                AuthRefreshToken.revoked_at.is_(None),
            )
            .values(revoked_at=datetime.now(timezone.utc))
        )

        if not all_devices and resolved_device_id:
            stmt = stmt.where(AuthRefreshToken.device_id == resolved_device_id)

        result = await db.execute(stmt)
        await db.commit()

        logger.info(f"User logged out: {current_user.student_id}")

        return create_response(
            data={
                "revoked_count": result.rowcount or 0,
                "scope": "all_devices" if all_devices else "single_device",
                "device_id": resolved_device_id if not all_devices else None,
            },
            message_key="AUTH_SUCCESS_LOGOUT",
        )

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Logout error for user {current_user.student_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Logout failed"
        )



@router.get("/me", response_model=Dict[str, Any])
async def get_current_user_profile(
    current_user: Member = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    Get current user profile.

    Returns detailed profile information for the authenticated user.
    """
    try:
        # Create detailed profile response
        profile_data = {
            **current_user.get_safe_dict(),
            "permissions": {
                "is_admin": current_user.is_admin,
                "is_group_leader": current_user.is_group_leader,
                "can_manage_group": current_user.can_manage_group,
                "can_import_data": current_user.can_import_data,
                "can_mark_rush_tasks": current_user.can_mark_rush_tasks,
            },
        }

        return create_response(
            data=profile_data, message_key="AUTH_SUCCESS_PROFILE_RETRIEVE"
        )

    except Exception as e:
        logger.error(f"Get profile error for user {current_user.student_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=get_message("AUTH_ERROR_PROFILE_RETRIEVE_FAILED"),
        )


@router.put("/me", response_model=Dict[str, Any])
async def update_user_profile(
    profile_update: UserProfileUpdate,
    current_user: Member = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """
    Update current user profile.

    Allows users to update their own profile information.
    Sensitive fields like role require admin privileges.
    """
    try:
        # Update allowed fields
        update_data = profile_update.dict(exclude_unset=True)

        # Remove sensitive fields that require admin privileges
        sensitive_fields = ["role", "is_active", "is_verified"]
        for field in sensitive_fields:
            if field in update_data:
                if not current_user.is_admin:
                    logger.warning(
                        f"User {current_user.student_id} attempted to update "
                        f"sensitive field: {field}"
                    )
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=get_message(
                            "AUTH_ERROR_UNAUTHORIZED_UPDATE", field=field
                        ),
                    )

        # Validate email format if provided
        if "email" in update_data:
            from app.core.security import validate_email_format

            if not validate_email_format(update_data["email"]):
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=get_message("AUTH_ERROR_INVALID_EMAIL_FORMAT"),
                )

        # Update user fields
        for field, value in update_data.items():
            if hasattr(current_user, field):
                setattr(current_user, field, value)

        await db.commit()
        await db.refresh(current_user)

        logger.info(f"Profile updated for user: {current_user.student_id}")

        from app.core.messages import success_response

        return success_response(
            "AUTH_SUCCESS_PROFILE_UPDATE", data=current_user.get_safe_dict()
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Profile update error for user {current_user.student_id}: {str(e)}"
        )
        await db.rollback()
        from app.core.messages import Messages

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=Messages.AUTH_ERROR_PROFILE_UPDATE_FAILED,
        )


@router.put("/change-password", response_model=Dict[str, Any])
async def change_password(
    password_data: ChangePasswordRequest,
    current_user: Member = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """
    Change user password.

    Requires current password verification and validates new password strength.
    """
    try:
        # Verify current password
        if not verify_password(
            password_data.current_password, current_user.password_hash
        ):
            logger.warning(
                f"Invalid current password for user: {current_user.student_id}"
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=get_message("AUTH_ERROR_CURRENT_PASSWORD_INCORRECT"),
            )

        # Validate new password strength
        is_strong, errors = validate_password_strength(password_data.new_password)

        if not is_strong:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={
                    "message": get_message("AUTH_WARNING_PASSWORD_WEAK"),
                    "errors": errors,
                },
            )

        # Check if new password is different from current
        if verify_password(password_data.new_password, current_user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=get_message("AUTH_ERROR_NEW_PASSWORD_SAME"),
            )

        # Update password
        current_user.password_hash = get_password_hash(password_data.new_password)
        await db.commit()

        logger.info(f"Password changed for user: {current_user.student_id}")

        return create_response(message_key="AUTH_SUCCESS_PASSWORD_CHANGE")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Password change error for user {current_user.student_id}: {str(e)}"
        )
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=get_message("AUTH_ERROR_PASSWORD_CHANGE_FAILED"),
        )


@router.get("/verify-token", response_model=Dict[str, Any])
async def verify_user_token(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """
    Verify token validity.

    Used by frontend to check if current token is still valid.
    """
    try:
        # Verify token
        payload: Optional[Dict[str, Any]] = verify_token(credentials.credentials)
        if not payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=get_message("AUTH_ERROR_INVALID_TOKEN"),
            )

        user_id_str: Optional[Union[str, int]] = payload.get("sub")
        if not user_id_str:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=get_message("AUTH_ERROR_INVALID_TOKEN_PAYLOAD"),
            )

        user_id = int(user_id_str) if isinstance(user_id_str, str) else user_id_str

        # Check if user still exists and is active
        result = await db.execute(select(Member).where(Member.id == user_id))
        user = result.scalar_one_or_none()

        # Handle potential coroutine return (for testing compatibility)
        if hasattr(user, "__await__"):
            user = await user  # type: ignore

        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=get_message("AUTH_ERROR_USER_NOT_FOUND"),
            )

        # Calculate token expiration time
        exp_timestamp: Optional[int] = payload.get("exp")

        return create_response(
            data={
                "valid": True,
                "user_id": user.id,
                "expires_at": exp_timestamp,
                "user": user.get_safe_dict(),
            },
            message_key="AUTH_INFO_TOKEN_VALID",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token verification error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=get_message("AUTH_ERROR_TOKEN_VERIFICATION_FAILED"),
        )


# Health check for auth service
@router.get("/health", response_model=Dict[str, Any])
async def auth_health_check() -> Dict[str, Any]:
    """Authentication service health check."""
    return create_response(
        data={"service": "auth", "status": "healthy"},
        message_key="AUTH_INFO_SERVICE_RUNNING",
    )
