"""
Authentication API endpoints.
Handles user login, logout, token refresh, and profile management.
"""

import logging
from datetime import timedelta
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import (
    create_error_response,
    create_response,
    get_current_user,
    get_db,
)
from app.core.config import settings
from app.core.security import (
    create_access_token,
    create_refresh_token,
    get_password_hash,
    rate_limiter,
    validate_password_strength,
    verify_password,
    verify_token,
)
from app.models.member import Member, UserRole
from app.schemas.auth import (
    ChangePasswordRequest,
    LoginRequest,
    LoginResponse,
    RefreshTokenRequest,
    TokenResponse,
    UserProfileResponse,
    UserProfileUpdate,
)

logger = logging.getLogger(__name__)
router = APIRouter()
security = HTTPBearer()


@router.post("/login", response_model=Dict[str, Any])
async def login(
    request: Request, login_data: LoginRequest, db: AsyncSession = Depends(get_db)
):
    """
    User login endpoint.

    Authenticates user with student_id and password.
    Returns access token, refresh token, and user profile.

    Rate limiting: 5 attempts per minute per IP.
    """
    client_ip = request.client.host

    # Rate limiting check
    if not rate_limiter.is_allowed(
        f"login:{client_ip}", max_requests=5, window_seconds=60
    ):
        logger.warning(f"Too many login attempts from IP: {client_ip}")
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many login attempts. Please try again later.",
        )

    try:
        # Find user by student_id
        result = await db.execute(
            select(Member).where(Member.student_id == login_data.student_id)
        )
        user = result.scalar_one_or_none()

        # Check if user exists and is active
        if not user:
            logger.warning(
                f"Login attempt with non-existent student_id: {login_data.student_id}"
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials"
            )

        if not user.is_active:
            logger.warning(f"Login attempt for inactive user: {login_data.student_id}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is disabled. Please contact administrator.",
            )

        # Verify password
        if not verify_password(login_data.password, user.password_hash):
            logger.warning(f"Invalid password for user: {login_data.student_id}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials"
            )

        # Update login info
        user.update_login_info()
        await db.commit()

        # Refresh user object to avoid lazy loading issues
        await db.refresh(user)

        # Create tokens
        access_token = create_access_token(
            subject=user.id,
            expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
        )
        refresh_token = create_refresh_token(
            subject=user.id,
            expires_delta=timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
        )

        logger.info(f"Successful login for user: {user.student_id}")

        response_data = {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            "user": user.get_safe_dict(),
        }

        return create_response(data=response_data, message="Login successful")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error for {login_data.student_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed. Please try again.",
        )


@router.post("/refresh", response_model=Dict[str, Any])
async def refresh_token(
    refresh_data: RefreshTokenRequest, db: AsyncSession = Depends(get_db)
):
    """
    Refresh access token using refresh token.

    Validates refresh token and returns new access token.
    """
    try:
        # Verify refresh token
        payload = verify_token(refresh_data.refresh_token, token_type="refresh")
        if not payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token"
            )

        user_id = int(payload.get("sub"))

        # Get user from database
        result = await db.execute(select(Member).where(Member.id == user_id))
        user = result.scalar_one_or_none()

        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive",
            )

        # Create new access token
        new_access_token = create_access_token(
            subject=user.id,
            expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
        )

        logger.info(f"Token refreshed for user: {user.student_id}")

        response_data = {
            "access_token": new_access_token,
            "token_type": "bearer",
            "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        }

        return create_response(
            data=response_data, message="Token refreshed successfully"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token refresh error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Token refresh failed",
        )


@router.post("/logout", response_model=Dict[str, Any])
async def logout(current_user: Member = Depends(get_current_user)):
    """
    User logout endpoint.

    In a stateless JWT system, logout is mainly handled on client side.
    This endpoint can be used for logging purposes or token blacklisting.
    """
    try:
        logger.info(f"User logged out: {current_user.student_id}")

        return create_response(message="Logout successful")

    except Exception as e:
        logger.error(f"Logout error for user {current_user.student_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Logout failed"
        )


@router.get("/me", response_model=Dict[str, Any])
async def get_current_user_profile(current_user: Member = Depends(get_current_user)):
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
            data=profile_data, message="Profile retrieved successfully"
        )

    except Exception as e:
        logger.error(f"Get profile error for user {current_user.student_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve profile",
        )


@router.put("/me", response_model=Dict[str, Any])
async def update_user_profile(
    profile_update: UserProfileUpdate,
    current_user: Member = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
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
                        f"User {current_user.student_id} attempted to update sensitive field: {field}"
                    )
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=f"Not authorized to update {field}",
                    )

        # Validate email format if provided
        if "email" in update_data:
            from app.core.security import validate_email_format

            if not validate_email_format(update_data["email"]):
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="Invalid email format",
                )

        # Update user fields
        for field, value in update_data.items():
            if hasattr(current_user, field):
                setattr(current_user, field, value)

        await db.commit()
        await db.refresh(current_user)

        logger.info(f"Profile updated for user: {current_user.student_id}")

        return create_response(
            data=current_user.get_safe_dict(), message="Profile updated successfully"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Profile update error for user {current_user.student_id}: {str(e)}"
        )
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Profile update failed",
        )


@router.put("/change-password", response_model=Dict[str, Any])
async def change_password(
    password_data: ChangePasswordRequest,
    current_user: Member = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
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
                detail="Current password is incorrect",
            )

        # Validate new password strength
        is_strong, errors = validate_password_strength(password_data.new_password)
        if not is_strong:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={
                    "message": "Password does not meet strength requirements",
                    "errors": errors,
                },
            )

        # Check if new password is different from current
        if verify_password(password_data.new_password, current_user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="New password must be different from current password",
            )

        # Update password
        current_user.password_hash = get_password_hash(password_data.new_password)
        await db.commit()

        logger.info(f"Password changed for user: {current_user.student_id}")

        return create_response(message="Password changed successfully")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Password change error for user {current_user.student_id}: {str(e)}"
        )
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Password change failed",
        )


@router.get("/verify-token", response_model=Dict[str, Any])
async def verify_user_token(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
):
    """
    Verify token validity.

    Used by frontend to check if current token is still valid.
    """
    try:
        # Verify token
        payload = verify_token(credentials.credentials)
        if not payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
            )

        user_id = int(payload.get("sub"))

        # Check if user still exists and is active
        result = await db.execute(select(Member).where(Member.id == user_id))
        user = result.scalar_one_or_none()

        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive",
            )

        # Calculate token expiration time
        exp_timestamp = payload.get("exp")

        return create_response(
            data={
                "valid": True,
                "user_id": user.id,
                "expires_at": exp_timestamp,
                "user": user.get_safe_dict(),
            },
            message="Token is valid",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token verification error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Token verification failed",
        )


# Health check for auth service
@router.get("/health", response_model=Dict[str, Any])
async def auth_health_check():
    """Authentication service health check."""
    return create_response(
        data={"service": "auth", "status": "healthy"},
        message="Authentication service is running",
    )
