"""
Unit tests for Authentication API endpoints.
Tests login, refresh token, profile management and password change functionality.
"""

from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, Mock, patch

import pytest
from fastapi import HTTPException, status

from app.api.v1.auth import (
    change_password,
    get_current_user_profile,
    login,
    logout,
    refresh_token,
    update_user_profile,
)
from app.models.member import Member, UserRole
from app.models.auth_refresh_token import AuthRefreshToken
from app.schemas.auth import (
    ChangePasswordRequest,
    LoginRequest,
    RefreshTokenRequest,
    UserProfileUpdate,
)


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
            class_name="测试班级",
        )

        # Mock database query
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = mock_user
        mock_db.execute.return_value = mock_result

        # Mock password verification and token creation
        with (
            patch("app.api.v1.auth.verify_password", return_value=True),
            patch(
                "app.api.v1.auth.create_access_token", return_value="mock_access_token"
            ),
            patch(
                "app.api.v1.auth.create_refresh_token",
                return_value="mock_refresh_token",
            ),
            patch("app.core.rate_limiter.global_rate_limiter") as mock_rate_limiter,
        ):
            mock_rate_limiter.is_allowed.return_value = True

            login_data = LoginRequest(student_id="TEST001", password="test_password")

            result = await login(
                request=mock_request, login_data=login_data, db=mock_db
            )

            # Verify successful login response
            assert result["success"] is True
            assert "access_token" in result["data"]
            assert "refresh_token" in result["data"]
            assert "accessToken" in result["data"]
            assert "refreshToken" in result["data"]
            assert "tokenType" in result["data"]
            assert "expiresIn" in result["data"]
            assert result["data"]["access_token"] == result["data"]["accessToken"]
            assert result["data"]["refresh_token"] == result["data"]["refreshToken"]
            assert result["data"]["user"]["student_id"] == "TEST001"
            assert result["data"]["user"]["studentId"] == "TEST001"
            assert result["data"]["user"]["className"] == "测试班级"
            assert result["data"]["user"]["isActive"] is True
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

        with patch("app.core.rate_limiter.global_rate_limiter") as mock_rate_limiter:
            mock_rate_limiter.is_allowed.return_value = True

            login_data = LoginRequest(
                student_id="NONEXISTENT", password="test_password"
            )

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
            username="test_user",
            name="测试用户",
            student_id="TEST001",
            password_hash="$2b$12$test_hash",
            role=UserRole.MEMBER,
            is_active=True,
        )

        # Mock database query
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = mock_user
        mock_db.execute.return_value = mock_result

        # Mock password verification failure
        with (
            patch("app.api.v1.auth.verify_password", return_value=False),
            patch("app.core.rate_limiter.global_rate_limiter") as mock_rate_limiter,
        ):
            mock_rate_limiter.is_allowed.return_value = True

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
            username="test_user",
            name="测试用户",
            student_id="TEST001",
            password_hash="$2b$12$test_hash",
            role=UserRole.MEMBER,
            is_active=False,  # Inactive user
        )

        # Mock database query
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = mock_user
        mock_db.execute.return_value = mock_result

        with (
            patch("app.api.v1.auth.verify_password", return_value=True),
            patch("app.core.rate_limiter.global_rate_limiter") as mock_rate_limiter,
        ):
            mock_rate_limiter.is_allowed.return_value = True

            login_data = LoginRequest(student_id="TEST001", password="test_password")

            with pytest.raises(HTTPException) as exc_info:
                await login(request=mock_request, login_data=login_data, db=mock_db)

            assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.asyncio
    async def test_refresh_token_success(self):
        """Test successful token refresh."""
        mock_db = AsyncMock()
        mock_request = Mock()
        mock_request.headers = {}

        mock_user = Member(
            id=1,
            username="test_user",
            name="测试用户",
            student_id="TEST001",
            role=UserRole.MEMBER,
            is_active=True,
        )

        # Mock persisted refresh token result
        mock_persisted_result = Mock()
        mock_persisted_result.scalar_one_or_none.return_value = AuthRefreshToken(
            user_id=1,
            refresh_token="valid_refresh_token",
            expires_at=datetime.now(timezone.utc) + timedelta(days=1),
            revoked_at=None,
        )

        # Mock user query result
        mock_user_result = Mock()
        mock_user_result.scalar_one_or_none.return_value = mock_user

        mock_db.execute = AsyncMock(
            side_effect=[mock_persisted_result, mock_user_result]
        )

        # Mock token verification and user retrieval
        with (
            patch("app.api.v1.auth.verify_token", return_value={"sub": 1}),
            patch(
                "app.api.v1.auth.create_access_token", return_value="new_access_token"
            ),
        ):
            refresh_data = RefreshTokenRequest(refresh_token="valid_refresh_token")

            result = await refresh_token(
                refresh_data=refresh_data, request=mock_request, db=mock_db
            )

            assert result["success"] is True
            assert result["data"]["access_token"] == "new_access_token"
            assert result["data"]["token_type"] == "bearer"
            assert "expires_in" in result["data"]
            assert result["data"]["accessToken"] == "new_access_token"
            assert result["data"]["tokenType"] == "bearer"
            assert result["data"]["expiresIn"] == result["data"]["expires_in"]

    @pytest.mark.asyncio
    async def test_refresh_token_invalid(self):
        """Test token refresh with invalid token."""
        mock_db = AsyncMock()
        mock_request = Mock()
        mock_request.headers = {}

        # Mock token verification failure
        with patch(
            "app.api.v1.auth.verify_token",
            side_effect=HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
            ),
        ):
            refresh_data = RefreshTokenRequest(refresh_token="invalid_token")

            with pytest.raises(HTTPException) as exc_info:
                await refresh_token(
                    refresh_data=refresh_data, request=mock_request, db=mock_db
                )

            assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.asyncio
    async def test_refresh_token_invalid_payload_contract(self):
        """Test invalid refresh token uses TOKEN_INVALID contract code."""
        mock_db = AsyncMock()
        mock_request = Mock()
        mock_request.headers = {}

        with patch("app.api.v1.auth.verify_token", return_value=None):
            refresh_data = RefreshTokenRequest(refresh_token="invalid")

            with pytest.raises(HTTPException) as exc_info:
                await refresh_token(
                    refresh_data=refresh_data,
                    request=mock_request,
                    db=mock_db,
                )

            assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
            assert isinstance(exc_info.value.detail, dict)
            assert exc_info.value.detail["error_code"] == "TOKEN_INVALID"

    @pytest.mark.asyncio
    async def test_refresh_token_revoked(self):
        """Test refresh with revoked persisted token should fail."""
        mock_db = AsyncMock()
        mock_request = Mock()
        mock_request.headers = {}

        mock_persisted_result = Mock()
        mock_persisted_result.scalar_one_or_none.return_value = AuthRefreshToken(
            user_id=1,
            refresh_token="revoked_refresh_token",
            expires_at=datetime.now(timezone.utc) + timedelta(days=1),
            revoked_at=datetime.now(timezone.utc),
        )
        mock_db.execute = AsyncMock(return_value=mock_persisted_result)

        with patch("app.api.v1.auth.verify_token", return_value={"sub": 1}):
            refresh_data = RefreshTokenRequest(refresh_token="revoked_refresh_token")

            with pytest.raises(HTTPException) as exc_info:
                await refresh_token(
                    refresh_data=refresh_data,
                    request=mock_request,
                    db=mock_db,
                )

            assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
            assert isinstance(exc_info.value.detail, dict)
            assert exc_info.value.detail["error_code"] == "TOKEN_REVOKED"

    @pytest.mark.asyncio
    async def test_refresh_token_expired(self):
        """Test refresh with expired persisted token should fail."""
        mock_db = AsyncMock()
        mock_request = Mock()
        mock_request.headers = {}

        mock_persisted_result = Mock()
        mock_persisted_result.scalar_one_or_none.return_value = AuthRefreshToken(
            user_id=1,
            refresh_token="expired_refresh_token",
            expires_at=datetime.now(timezone.utc) - timedelta(seconds=1),
            revoked_at=None,
        )
        mock_db.execute = AsyncMock(return_value=mock_persisted_result)

        with patch("app.api.v1.auth.verify_token", return_value={"sub": 1}):
            refresh_data = RefreshTokenRequest(refresh_token="expired_refresh_token")

            with pytest.raises(HTTPException) as exc_info:
                await refresh_token(
                    refresh_data=refresh_data,
                    request=mock_request,
                    db=mock_db,
                )

            assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
            assert isinstance(exc_info.value.detail, dict)
            assert exc_info.value.detail["error_code"] == "TOKEN_EXPIRED"

    @pytest.mark.asyncio
    async def test_change_password_success(self):
        """Test successful password change."""
        mock_db = AsyncMock()

        mock_user = Member(
            id=1,
            username="test_user",
            name="测试用户",
            password_hash="$2b$12$old_hash",
            role=UserRole.MEMBER,
            is_active=True,
        )

        # Mock verify_password to return True for old password, False for new
        def mock_verify_password(plain_password, hashed_password):
            if plain_password == "old_password":
                return True  # Current password is correct
            return False  # New password is different from current

        with (
            patch("app.api.v1.auth.verify_password", side_effect=mock_verify_password),
            patch(
                "app.api.v1.auth.validate_password_strength", return_value=(True, [])
            ),
            patch("app.api.v1.auth.get_password_hash", return_value="$2b$12$new_hash"),
        ):
            password_data = ChangePasswordRequest(
                current_password="old_password", new_password="new_strong_password123"
            )

            result = await change_password(
                password_data=password_data, current_user=mock_user, db=mock_db
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
            name="测试用户",
            password_hash="$2b$12$old_hash",
            role=UserRole.MEMBER,
            is_active=True,
        )

        with patch("app.api.v1.auth.verify_password", return_value=False):
            password_data = ChangePasswordRequest(
                current_password="wrong_password", new_password="new_strong_password"
            )

            with pytest.raises(HTTPException) as exc_info:
                await change_password(
                    password_data=password_data, current_user=mock_user, db=mock_db
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
            is_active=True,
        )

        result = await get_current_user_profile(current_user=mock_user)

        assert result["success"] is True
        assert result["data"]["student_id"] == "TEST001"
        assert result["data"]["studentId"] == "TEST001"
        assert result["data"]["className"] == "测试班级"
        assert result["data"]["name"] == "测试用户"
        assert result["data"]["role"] == "member"
        assert result["data"]["permissions"]["isAdmin"] is False

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
            is_active=True,
        )

        profile_data = UserProfileUpdate(name="更新用户", phone="13900139000")

        result = await update_user_profile(
            profile_update=profile_data, current_user=mock_user, db=mock_db
        )

        assert result["success"] is True
        assert result["message"] == "个人信息更新成功"

        # Verify the user object was updated
        assert mock_user.name == "更新用户"
        assert mock_user.phone == "13900139000"

        # Verify database commit was called
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_logout_all_devices_success(self):
        """Test logout revokes tokens for all devices by default."""
        mock_db = AsyncMock()
        mock_request = Mock()
        mock_request.headers = {}

        mock_user = Member(
            id=1,
            username="test_user",
            name="测试用户",
            student_id="TEST001",
            role=UserRole.MEMBER,
            is_active=True,
        )

        mock_exec_result = Mock()
        mock_exec_result.rowcount = 3
        mock_db.execute = AsyncMock(return_value=mock_exec_result)

        result = await logout(
            request=mock_request,
            all_devices=True,
            device_id=None,
            current_user=mock_user,
            db=mock_db,
        )

        assert result["success"] is True
        assert result["data"]["scope"] == "all_devices"
        assert result["data"]["revoked_count"] == 3
        assert result["data"]["policy"]["default_all_devices"] is True
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_logout_single_device_requires_device_id(self):
        """Test logout requires device id when all_devices is false."""
        mock_db = AsyncMock()
        mock_request = Mock()
        mock_request.headers = {}

        mock_user = Member(
            id=1,
            username="test_user",
            name="测试用户",
            student_id="TEST001",
            role=UserRole.MEMBER,
            is_active=True,
        )

        with pytest.raises(HTTPException) as exc_info:
            await logout(
                request=mock_request,
                all_devices=False,
                device_id=None,
                current_user=mock_user,
                db=mock_db,
            )

        assert exc_info.value.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        assert isinstance(exc_info.value.detail, dict)
        assert exc_info.value.detail["error_code"] == "DEVICE_ID_REQUIRED"

    @pytest.mark.asyncio
    async def test_logout_single_device_from_header(self):
        """Test logout uses request header device id for single-device revoke."""
        mock_db = AsyncMock()
        mock_request = Mock()
        mock_request.headers = {"X-Device-ID": "device-1"}

        mock_user = Member(
            id=1,
            username="test_user",
            name="测试用户",
            student_id="TEST001",
            role=UserRole.MEMBER,
            is_active=True,
        )

        mock_exec_result = Mock()
        mock_exec_result.rowcount = 1
        mock_db.execute = AsyncMock(return_value=mock_exec_result)

        result = await logout(
            request=mock_request,
            all_devices=False,
            device_id=None,
            current_user=mock_user,
            db=mock_db,
        )

        assert result["success"] is True
        assert result["data"]["scope"] == "single_device"
        assert result["data"]["device_id"] == "device-1"
        assert result["data"]["revoked_count"] == 1
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_rate_limiting_triggered(self):
        """Test rate limiting functionality."""
        mock_db = AsyncMock()
        mock_request = Mock()
        mock_request.client.host = "127.0.0.1"

        # Mock global rate limiter to return False (rate limit exceeded)
        with patch("app.core.rate_limiter.global_rate_limiter") as mock_rate_limiter:
            mock_rate_limiter.is_allowed.return_value = False

            login_data = LoginRequest(student_id="TEST001", password="test_password")

            with pytest.raises(HTTPException) as exc_info:
                await login(request=mock_request, login_data=login_data, db=mock_db)

            assert exc_info.value.status_code == status.HTTP_429_TOO_MANY_REQUESTS
            assert "Too many login attempts" in str(exc_info.value.detail)
