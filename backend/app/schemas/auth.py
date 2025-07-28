"""
Authentication-related Pydantic schemas.
Request and response models for authentication endpoints.
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, EmailStr, validator

from app.models.member import UserRole


class LoginRequest(BaseModel):
    """Request model for user login."""
    
    student_id: str = Field(
        ..., 
        min_length=1, 
        max_length=20,
        description="Student ID for authentication"
    )
    password: str = Field(
        ..., 
        min_length=1,
        description="User password"
    )
    
    class Config:
        schema_extra = {
            "example": {
                "student_id": "2021001001",
                "password": "MySecurePassword123!"
            }
        }


class TokenResponse(BaseModel):
    """Response model for token-related endpoints."""
    
    access_token: str = Field(..., description="JWT access token")
    refresh_token: Optional[str] = Field(None, description="JWT refresh token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(..., description="Token expiration time in seconds")
    
    class Config:
        schema_extra = {
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer",
                "expires_in": 3600
            }
        }


class UserProfileResponse(BaseModel):
    """Response model for user profile."""
    
    id: int = Field(..., description="User ID")
    name: str = Field(..., description="User name")
    student_id: str = Field(..., description="Student ID")
    group_id: Optional[int] = Field(None, description="Group ID")
    class_name: Optional[str] = Field(None, description="Class name")
    email: Optional[str] = Field(None, description="Email address")
    role: str = Field(..., description="User role")
    is_active: bool = Field(..., description="Whether user is active")
    is_verified: bool = Field(..., description="Whether email is verified")
    last_login: Optional[datetime] = Field(None, description="Last login time")
    created_at: datetime = Field(..., description="Account creation time")
    updated_at: datetime = Field(..., description="Last update time")
    
    class Config:
        orm_mode = True
        schema_extra = {
            "example": {
                "id": 1,
                "name": "张三",
                "student_id": "2021001001",
                "group_id": 1,
                "class_name": "计算机科学与技术2101",
                "email": "zhangsan@example.com",
                "role": "member",
                "is_active": True,
                "is_verified": True,
                "last_login": "2025-01-27T10:30:00",
                "created_at": "2025-01-01T00:00:00",
                "updated_at": "2025-01-27T10:30:00"
            }
        }


class LoginResponse(BaseModel):
    """Response model for successful login."""
    
    access_token: str = Field(..., description="JWT access token")
    refresh_token: str = Field(..., description="JWT refresh token") 
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(..., description="Token expiration time in seconds")
    user: UserProfileResponse = Field(..., description="User profile")
    
    class Config:
        schema_extra = {
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer",
                "expires_in": 3600,
                "user": {
                    "id": 1,
                    "name": "张三",
                    "student_id": "2021001001",
                    "role": "member"
                }
            }
        }


class RefreshTokenRequest(BaseModel):
    """Request model for token refresh."""
    
    refresh_token: str = Field(
        ..., 
        description="Valid refresh token"
    )
    
    class Config:
        schema_extra = {
            "example": {
                "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
            }
        }


class ChangePasswordRequest(BaseModel):
    """Request model for password change."""
    
    current_password: str = Field(
        ..., 
        min_length=1,
        description="Current password"
    )
    new_password: str = Field(
        ..., 
        min_length=8,
        max_length=128,
        description="New password (must meet strength requirements)"
    )
    
    @validator('new_password')
    def validate_password_strength(cls, password):
        """Validate password strength."""
        from app.core.security import validate_password_strength
        
        is_strong, errors = validate_password_strength(password)
        if not is_strong:
            raise ValueError(f"Password does not meet requirements: {', '.join(errors)}")
        
        return password
    
    class Config:
        schema_extra = {
            "example": {
                "current_password": "OldPassword123!",
                "new_password": "NewSecurePassword456!"
            }
        }


class UserProfileUpdate(BaseModel):
    """Request model for user profile updates."""
    
    name: Optional[str] = Field(
        None, 
        min_length=1, 
        max_length=50,
        description="User name"
    )
    class_name: Optional[str] = Field(
        None, 
        max_length=50,
        description="Class name"
    )
    email: Optional[EmailStr] = Field(
        None,
        description="Email address"
    )
    
    class Config:
        schema_extra = {
            "example": {
                "name": "张三丰",
                "class_name": "计算机科学与技术2102",
                "email": "zhangsan@newdomain.com"
            }
        }


class PasswordResetRequest(BaseModel):
    """Request model for password reset."""
    
    email: EmailStr = Field(
        ...,
        description="User email address"
    )
    
    class Config:
        schema_extra = {
            "example": {
                "email": "user@example.com"
            }
        }


class PasswordResetConfirm(BaseModel):
    """Request model for password reset confirmation."""
    
    token: str = Field(
        ...,
        description="Password reset token"
    )
    new_password: str = Field(
        ...,
        min_length=8,
        max_length=128,
        description="New password"
    )
    
    @validator('new_password')
    def validate_password_strength(cls, password):
        """Validate password strength."""
        from app.core.security import validate_password_strength
        
        is_strong, errors = validate_password_strength(password)
        if not is_strong:
            raise ValueError(f"Password does not meet requirements: {', '.join(errors)}")
        
        return password
    
    class Config:
        schema_extra = {
            "example": {
                "token": "reset_token_here",
                "new_password": "NewSecurePassword123!"
            }
        }


class TokenVerificationResponse(BaseModel):
    """Response model for token verification."""
    
    valid: bool = Field(..., description="Whether token is valid")
    user_id: Optional[int] = Field(None, description="User ID if token is valid")
    expires_at: Optional[int] = Field(None, description="Token expiration timestamp")
    user: Optional[UserProfileResponse] = Field(None, description="User profile if token is valid")
    
    class Config:
        schema_extra = {
            "example": {
                "valid": True,
                "user_id": 1,
                "expires_at": 1706356800,
                "user": {
                    "id": 1,
                    "name": "张三",
                    "student_id": "2021001001",
                    "role": "member"
                }
            }
        }


class UserPermissions(BaseModel):
    """Model for user permissions."""
    
    is_admin: bool = Field(..., description="Whether user is admin")
    is_group_leader: bool = Field(..., description="Whether user is group leader")
    can_manage_group: bool = Field(..., description="Whether user can manage group")
    can_import_data: bool = Field(..., description="Whether user can import data")
    can_mark_rush_tasks: bool = Field(..., description="Whether user can mark rush tasks")
    
    class Config:
        schema_extra = {
            "example": {
                "is_admin": False,
                "is_group_leader": True,
                "can_manage_group": True,
                "can_import_data": False,
                "can_mark_rush_tasks": False
            }
        }


class DetailedUserProfile(UserProfileResponse):
    """Extended user profile with permissions."""
    
    permissions: UserPermissions = Field(..., description="User permissions")
    
    class Config:
        schema_extra = {
            "example": {
                "id": 1,
                "name": "张三",
                "student_id": "2021001001",
                "role": "group_leader",
                "permissions": {
                    "is_admin": False,
                    "is_group_leader": True,
                    "can_manage_group": True,
                    "can_import_data": False,
                    "can_mark_rush_tasks": False
                }
            }
        }