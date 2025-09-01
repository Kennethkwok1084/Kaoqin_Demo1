"""
身份认证相关的Pydantic模式定义
包含登录、令牌、用户信息的请求和响应模型
"""

from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator
from .base import BaseResponse, StandardResponse


class LoginResponse(StandardResponse):
    """登录响应 - 直接输出前端需要的camelCase格式"""
    
    class LoginData(BaseResponse):
        """登录数据"""
        access_token: str = Field(..., description="JWT访问令牌", alias="accessToken")
        refresh_token: str = Field(..., description="JWT刷新令牌", alias="refreshToken") 
        token_type: str = Field(default="bearer", description="令牌类型", alias="tokenType")
        expires_in: int = Field(..., description="令牌过期时间(秒)", alias="expiresIn")
        user: Dict[str, Any] = Field(..., description="用户信息")
    
    data: LoginData = Field(..., description="登录数据")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "success": True,
                "message": "登录成功",
                "data": {
                    "accessToken": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                    "refreshToken": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                    "tokenType": "bearer",
                    "expiresIn": 3600,
                    "user": {
                        "id": 1,
                        "name": "张三",
                        "studentId": "2021001001",
                        "role": "member"
                    }
                }
            }
        }
    )


class ChangePasswordRequest(BaseModel):
    """Request model for changing password - alias for PasswordChangeRequest."""

    current_password: str = Field(..., description="Current password")
    new_password: str = Field(
        ..., min_length=8, max_length=128, description="New password"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "current_password": "OldPassword123!",
                "new_password": "NewSecurePassword123!",
            }
        }
    )


class UserProfileUpdate(BaseModel):
    """Request model for updating user profile."""

    name: Optional[str] = Field(None, max_length=50, description="User name")
    email: Optional[str] = Field(None, description="Email address")
    phone: Optional[str] = Field(None, max_length=11, description="Phone number")
    class_name: Optional[str] = Field(None, max_length=50, description="Class name")

    # Ensure all fields can be None for partial updates
    @model_validator(mode="after")
    def validate_at_least_one_field(self) -> "UserProfileUpdate":
        """Ensure at least one field is provided for update or allow empty updates."""
        # Allow empty updates - validation will be handled at API level
        return self

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "张三丰",
                "email": "zhangsan@newdomain.com",
                "phone": "13800138000",
                "class_name": "计算机科学与技术2102",
            }
        }
    )


class LoginRequest(BaseModel):
    """Login request model."""

    student_id: str = Field(..., min_length=1, max_length=20, description="Student ID")
    password: str = Field(..., min_length=1, description="User password")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {"student_id": "2021001001", "password": "MySecurePassword123!"}
        }
    )


class TokenResponse(BaseModel):
    """Response model for token-related endpoints."""

    access_token: str = Field(..., description="JWT access token")
    refresh_token: Optional[str] = Field(None, description="JWT refresh token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(..., description="Token expiration time in seconds")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer",
                "expires_in": 3600,
            }
        }
    )


class UserProfileResponse(BaseModel):
    """Response model for user profile."""

    id: int = Field(..., description="User ID")
    name: str = Field(..., description="User name")
    student_id: str = Field(..., description="Student ID")
    email: Optional[str] = Field(None, description="Email address")
    role: str = Field(..., description="User role")
    group_id: Optional[int] = Field(None, description="Group ID")
    class_name: Optional[str] = Field(None, description="Class name")
    is_active: bool = Field(..., description="Whether user is active")
    is_verified: bool = Field(..., description="Whether email is verified")
    last_login: Optional[datetime] = Field(None, description="Last login time")
    login_count: int = Field(..., description="Login count")
    created_at: datetime = Field(..., description="Account creation time")

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": 1,
                "name": "张三",
                "student_id": "2021001001",
                "email": "zhangsan@example.com",
                "role": "member",
                "group_id": 1,
                "class_name": "计算机科学与技术2101",
                "is_active": True,
                "is_verified": True,
                "last_login": "2025-01-27T10:30:00",
                "login_count": 15,
                "created_at": "2025-01-01T00:00:00",
            }
        },
    )


class RefreshTokenRequest(BaseModel):
    """Request model for refreshing tokens."""

    refresh_token: str = Field(..., description="Refresh token")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {"refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."}
        }
    )


class PasswordChangeRequest(BaseModel):
    """Request model for changing password."""

    current_password: str = Field(..., description="Current password")
    new_password: str = Field(
        ..., min_length=8, max_length=128, description="New password"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "current_password": "OldPassword123!",
                "new_password": "NewSecurePassword123!",
            }
        }
    )


class LogoutResponse(BaseModel):
    """Response model for logout."""

    message: str = Field(..., description="Logout message")
    logged_out_at: datetime = Field(..., description="Logout timestamp")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "message": "成功退出登录",
                "logged_out_at": "2025-01-27T15:30:00",
            }
        }
    )


class AuthStatusResponse(BaseModel):
    """Response model for authentication status check."""

    authenticated: bool = Field(..., description="Whether user is authenticated")
    user_id: Optional[int] = Field(None, description="User ID if authenticated")
    expires_at: Optional[datetime] = Field(None, description="Token expiration time")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "authenticated": True,
                "user_id": 1,
                "expires_at": "2025-01-27T16:30:00",
            }
        }
    )
