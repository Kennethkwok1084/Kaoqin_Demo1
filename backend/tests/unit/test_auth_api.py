"""
Unit tests for Authentication API endpoints.
Tests login, refresh token, profile management and password change functionality.
"""

import pytest
from unittest.mock import AsyncMock, Mock, patch
from datetime import datetime, timedelta
from fastapi import HTTPException, status

from app.api.v1.auth import login, refresh_token, change_password, get_current_user_profile, update_user_profile
from app.models.member import Member, UserRole
from app.schemas.auth import LoginRequest, RefreshTokenRequest, ChangePasswordRequest, UserProfileUpdate


class TestAuthAPI:
    """Unit tests for Authentication API endpoints."""

    @pytest.mark.asyncio
    async def test_login_success(self):
        """Test successful login with valid credentials."""
        # Mock dependencies
        mock_db = AsyncMock()
        mock_request = Mock()
        mock_request.client.host = "127.0.0.1"
        
        # Mock user
        mock_user = Member(
            id=1,
            username="test_user",
            name="测试用户", 
            student_id="TEST001",
            password_hash="$2b$12$test_hash",
            role=UserRole.MEMBER,
            is_active=True,
            department="信息化建设处",
            class_name="测试班级"
        )
        
        # Mock database query
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = mock_user
        mock_db.execute.return_value = mock_result

        # Mock password verification and token creation
        with patch('app.api.v1.auth.verify_password', return_value=True), \
             patch('app.api.v1.auth.create_access_token', return_value="mock_access_token"), \
             patch('app.api.v1.auth.create_refresh_token', return_value="mock_refresh_token"), \
             patch('app.api.v1.auth.rate_limiter') as mock_rate_limiter:
            
            mock_rate_limiter.check_rate_limit = AsyncMock()
            
            login_data = LoginRequest(student_id="TEST001", password="test_password")
            
            result = await login(request=mock_request, login_data=login_data, db=mock_db)
            
            # Verify successful login response
            assert result["success"] is True
            assert "access_token" in result["data"]
            assert "refresh_token" in result["data"] 
            assert result["data"]["user"]["student_id"] == "TEST001"
            assert result["data"]["user"]["name"] == "测试用户"

    @pytest.mark.asyncio
    async def test_login_user_not_found(self):
        """Test login with non-existent user."""
        mock_db = AsyncMock()
        mock_request = Mock()
        mock_request.client.host = "127.0.0.1"
        
        # Mock empty database result
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        with patch('app.api.v1.auth.rate_limiter') as mock_rate_limiter:
            mock_rate_limiter.check_rate_limit = AsyncMock()
            
            login_data = LoginRequest(student_id="NONEXISTENT", password="test_password")
            
            with pytest.raises(HTTPException) as exc_info:
                await login(request=mock_request, login_data=login_data, db=mock_db)
            
            assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.asyncio
    async def test_login_invalid_password(self):
        """Test login with invalid password."""
        mock_db = AsyncMock()
        mock_request = Mock()
        mock_request.client.host = "127.0.0.1"
        
        mock_user = Member(
            id=1,
            username="test_user",
            student_id="TEST001",
            password_hash="$2b$12$test_hash",
            role=UserRole.MEMBER,
            is_active=True
        )
        
        # Mock database query
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = mock_user
        mock_db.execute.return_value = mock_result

        # Mock password verification failure
        with patch('app.api.v1.auth.verify_password', return_value=False), \
             patch('app.api.v1.auth.rate_limiter') as mock_rate_limiter:
            
            mock_rate_limiter.check_rate_limit = AsyncMock()
            
            login_data = LoginRequest(student_id="TEST001", password="wrong_password")
            
            with pytest.raises(HTTPException) as exc_info:
                await login(request=mock_request, login_data=login_data, db=mock_db)
            
            assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.asyncio
    async def test_login_inactive_user(self):
        """Test login with inactive user account."""
        mock_db = AsyncMock()
        mock_request = Mock()
        mock_request.client.host = "127.0.0.1"
        
        mock_user = Member(
            id=1,
            username="test_user", 
            student_id="TEST001",
            password_hash="$2b$12$test_hash",
            role=UserRole.MEMBER,
            is_active=False  # Inactive user
        )
        
        # Mock database query
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = mock_user
        mock_db.execute.return_value = mock_result

        with patch('app.api.v1.auth.verify_password', return_value=True), \
             patch('app.api.v1.auth.rate_limiter') as mock_rate_limiter:
            
            mock_rate_limiter.check_rate_limit = AsyncMock()
            
            login_data = LoginRequest(student_id="TEST001", password="test_password")
            
            with pytest.raises(HTTPException) as exc_info:
                await login(request=mock_request, login_data=login_data, db=mock_db)
            
            assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.asyncio
    async def test_refresh_token_success(self):
        """Test successful token refresh."""
        mock_db = AsyncMock()
        
        mock_user = Member(
            id=1,
            username="test_user",
            student_id="TEST001",
            role=UserRole.MEMBER,
            is_active=True
        )
        
        # Mock token verification and user retrieval
        with patch('app.api.v1.auth.verify_token', return_value={"user_id": 1}), \
             patch('app.api.v1.auth.get_current_user', return_value=mock_user), \
             patch('app.api.v1.auth.create_access_token', return_value="new_access_token"), \
             patch('app.api.v1.auth.create_refresh_token', return_value="new_refresh_token"):
            
            refresh_data = RefreshTokenRequest(refresh_token="valid_refresh_token")
            
            result = await refresh_token(refresh_data=refresh_data, db=mock_db)
            
            assert result["success"] is True
            assert result["data"]["access_token"] == "new_access_token"
            assert result["data"]["refresh_token"] == "new_refresh_token"

    @pytest.mark.asyncio
    async def test_refresh_token_invalid(self):
        """Test token refresh with invalid token."""
        mock_db = AsyncMock()
        
        # Mock token verification failure
        with patch('app.api.v1.auth.verify_token', side_effect=HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
        )):
            
            refresh_data = RefreshTokenRequest(refresh_token="invalid_token")
            
            with pytest.raises(HTTPException) as exc_info:
                await refresh_token(refresh_data=refresh_data, db=mock_db)
            
            assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.asyncio
    async def test_change_password_success(self):
        """Test successful password change."""
        mock_db = AsyncMock()
        
        mock_user = Member(
            id=1,
            username="test_user",
            password_hash="$2b$12$old_hash",
            role=UserRole.MEMBER,
            is_active=True
        )
        
        with patch('app.api.v1.auth.verify_password', return_value=True), \
             patch('app.api.v1.auth.validate_password_strength', return_value=True), \
             patch('app.api.v1.auth.get_password_hash', return_value="$2b$12$new_hash"):
            
            password_data = ChangePasswordRequest(
                current_password="old_password",
                new_password="new_strong_password"
            )
            
            result = await change_password(
                password_data=password_data, 
                current_user=mock_user, 
                db=mock_db
            )
            
            assert result["success"] is True
            assert result["message"] == "密码修改成功"

    @pytest.mark.asyncio 
    async def test_change_password_wrong_current(self):
        """Test password change with wrong current password."""
        mock_db = AsyncMock()
        
        mock_user = Member(
            id=1,
            username="test_user",
            password_hash="$2b$12$old_hash",
            role=UserRole.MEMBER,
            is_active=True
        )
        
        with patch('app.api.v1.auth.verify_password', return_value=False):
            
            password_data = ChangePasswordRequest(
                current_password="wrong_password",
                new_password="new_strong_password"
            )
            
            with pytest.raises(HTTPException) as exc_info:
                await change_password(
                    password_data=password_data,
                    current_user=mock_user,
                    db=mock_db
                )
            
            assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST

    @pytest.mark.asyncio
    async def test_get_profile_success(self):
        """Test getting user profile."""
        mock_user = Member(
            id=1,
            username="test_user",
            name="测试用户",
            student_id="TEST001",
            phone="13800138000",
            department="信息化建设处", 
            class_name="测试班级",
            role=UserRole.MEMBER,
            is_active=True
        )
        
        result = await get_current_user_profile(current_user=mock_user)
        
        assert result["success"] is True
        assert result["data"]["student_id"] == "TEST001"
        assert result["data"]["name"] == "测试用户"
        assert result["data"]["role"] == "member"

    @pytest.mark.asyncio
    async def test_update_profile_success(self):
        """Test successful profile update."""
        mock_db = AsyncMock()
        
        mock_user = Member(
            id=1,
            username="test_user",
            name="测试用户",
            phone="13800138000",
            role=UserRole.MEMBER,
            is_active=True
        )
        
        profile_data = UserProfileUpdate(
            name="更新用户",
            phone="13900139000"
        )
        
        result = await update_user_profile(
            profile_data=profile_data,
            current_user=mock_user,
            db=mock_db
        )
        
        assert result["success"] is True
        assert result["message"] == "个人信息更新成功"
        
        # Verify the user object was updated
        assert mock_user.name == "更新用户"
        assert mock_user.phone == "13900139000"
        
        # Verify database commit was called
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_rate_limiting_triggered(self):
        """Test rate limiting functionality."""
        mock_db = AsyncMock()
        mock_request = Mock()
        mock_request.client.host = "127.0.0.1"
        
        # Mock rate limiter to raise exception
        with patch('app.api.v1.auth.rate_limiter') as mock_rate_limiter:
            mock_rate_limiter.check_rate_limit = AsyncMock(
                side_effect=HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Too many requests"
                )
            )
            
            login_data = LoginRequest(student_id="TEST001", password="test_password")
            
            with pytest.raises(HTTPException) as exc_info:
                await login(request=mock_request, login_data=login_data, db=mock_db)
            
            assert exc_info.value.status_code == status.HTTP_429_TOO_MANY_REQUESTS