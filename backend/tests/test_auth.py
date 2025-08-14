"""
Tests for authentication API endpoints.
Comprehensive test suite for login, logout, token refresh, and profile management.
"""

import pytest
from app.core.security import create_access_token, create_refresh_token
from app.models.member import Member
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession


class TestAuthLogin:
    """Test cases for login endpoint."""

    def test_successful_login(
        self,
        client_with_db: TestClient,
        test_user: Member,
        sample_login_data: dict,
        test_response,
    ):
        """Test successful user login."""
        response = client_with_db.post("/api/v1/auth/login", json=sample_login_data)

        assert response.status_code == 200
        assert test_response.is_success(response)

        data = test_response.get_data(response)
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
        assert "expires_in" in data
        assert "user" in data

        # Verify user data
        user_data = data["user"]
        assert user_data["student_id"] == test_user.student_id
        assert user_data["name"] == test_user.name
        assert user_data["is_active"] is True

    def test_invalid_credentials(
        self,
        client_with_db: TestClient,
        test_user: Member,
        sample_invalid_login_data: dict,
    ):
        """Test login with invalid credentials."""
        response = client_with_db.post(
            "/api/v1/auth/login", json=sample_invalid_login_data
        )

        assert response.status_code == 401
        assert "Invalid credentials" in response.json()["detail"]

    def test_nonexistent_user(self, client_with_db: TestClient):
        """Test login with non-existent user."""
        login_data = {"student_id": "9999999999", "password": "SomePassword123!"}

        response = client_with_db.post("/api/v1/auth/login", json=login_data)

        assert response.status_code == 401
        assert "Invalid credentials" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_inactive_user_login(
        self, client_with_db: TestClient, async_session: AsyncSession
    ):
        """Test login attempt with inactive user."""
        # Create inactive user
        from app.core.security import get_password_hash
        from app.models.member import UserRole

        inactive_user = Member(
            name="停用用户",
            student_id="2021001999",
            password_hash=get_password_hash("TestPassword123!"),
            role=UserRole.MEMBER,
            is_active=False,  # Inactive user
            is_verified=True,
        )

        async_session.add(inactive_user)
        await async_session.commit()

        login_data = {"student_id": "2021001999", "password": "TestPassword123!"}

        response = client_with_db.post("/api/v1/auth/login", json=login_data)

        assert response.status_code == 403
        assert "Account is disabled" in response.json()["detail"]

    def test_missing_fields(self, client_with_db: TestClient):
        """Test login with missing required fields."""
        # Missing password
        response = client_with_db.post(
            "/api/v1/auth/login", json={"student_id": "2021001001"}
        )
        assert response.status_code == 422

        # Missing student_id
        response = client_with_db.post(
            "/api/v1/auth/login", json={"password": "password"}
        )
        assert response.status_code == 422

        # Empty request
        response = client_with_db.post("/api/v1/auth/login", json={})
        assert response.status_code == 422

    def test_rate_limiting(self, client_with_db: TestClient, test_user: Member):
        """Test rate limiting for login attempts."""
        invalid_login_data = {"student_id": "2021001001", "password": "WrongPassword"}

        # Make 5 failed attempts (should still work)
        for _ in range(5):
            response = client_with_db.post(
                "/api/v1/auth/login", json=invalid_login_data
            )
            assert response.status_code == 401

        # 6th attempt should be rate limited
        response = client_with_db.post("/api/v1/auth/login", json=invalid_login_data)
        assert response.status_code == 429
        assert "Too many login attempts" in response.json()["detail"]


class TestTokenRefresh:
    """Test cases for token refresh endpoint."""

    def test_successful_token_refresh(
        self, client_with_db: TestClient, test_user: Member, test_response
    ):
        """Test successful token refresh."""
        # Create a valid refresh token
        refresh_token = create_refresh_token(subject=test_user.id)

        response = client_with_db.post(
            "/api/v1/auth/refresh", json={"refresh_token": refresh_token}
        )

        assert response.status_code == 200
        assert test_response.is_success(response)

        data = test_response.get_data(response)
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert "expires_in" in data

    def test_invalid_refresh_token(self, client_with_db: TestClient):
        """Test refresh with invalid token."""
        response = client_with_db.post(
            "/api/v1/auth/refresh", json={"refresh_token": "invalid.token.here"}
        )

        assert response.status_code == 401
        assert "Invalid refresh token" in response.json()["detail"]

    def test_expired_refresh_token(self, client_with_db: TestClient, test_user: Member):
        """Test refresh with expired token."""
        from datetime import timedelta

        # Create expired refresh token
        expired_token = create_refresh_token(
            subject=test_user.id, expires_delta=timedelta(seconds=-1)  # Already expired
        )

        response = client_with_db.post(
            "/api/v1/auth/refresh", json={"refresh_token": expired_token}
        )

        assert response.status_code == 401
        assert "Invalid refresh token" in response.json()["detail"]

    def test_access_token_as_refresh_token(
        self, client_with_db: TestClient, test_user: Member
    ):
        """Test using access token as refresh token."""
        # Create access token (wrong type)
        access_token = create_access_token(subject=test_user.id)

        response = client_with_db.post(
            "/api/v1/auth/refresh", json={"refresh_token": access_token}
        )

        assert response.status_code == 401
        assert "Invalid refresh token" in response.json()["detail"]


class TestUserProfile:
    """Test cases for user profile endpoints."""

    def test_get_current_user_profile(
        self, client_with_db: TestClient, test_user: Member, auth_headers, test_response
    ):
        """Test getting current user profile."""
        # Create access token
        access_token = create_access_token(subject=test_user.id)
        headers = auth_headers(access_token)

        response = client_with_db.get("/api/v1/auth/me", headers=headers)

        assert response.status_code == 200
        assert test_response.is_success(response)

        data = test_response.get_data(response)
        assert data["id"] == test_user.id
        assert data["student_id"] == test_user.student_id
        assert data["name"] == test_user.name
        assert "permissions" in data

        # Check permissions
        permissions = data["permissions"]
        assert "is_admin" in permissions
        assert "can_manage_group" in permissions

    def test_get_profile_without_auth(self, client_with_db: TestClient):
        """Test getting profile without authentication."""
        response = client_with_db.get("/api/v1/auth/me")

        assert response.status_code == 403  # No Authorization header

    def test_get_profile_with_invalid_token(
        self, client_with_db: TestClient, auth_headers
    ):
        """Test getting profile with invalid token."""
        headers = auth_headers("invalid.token.here")

        response = client_with_db.get("/api/v1/auth/me", headers=headers)

        assert response.status_code == 401

    def test_update_user_profile(
        self,
        client_with_db: TestClient,
        test_user: Member,
        auth_headers,
        sample_profile_update: dict,
        test_response,
    ):
        """Test updating user profile."""
        access_token = create_access_token(subject=test_user.id)
        headers = auth_headers(access_token)

        response = client_with_db.put(
            "/api/v1/auth/me", headers=headers, json=sample_profile_update
        )

        assert response.status_code == 200
        assert test_response.is_success(response)

        data = test_response.get_data(response)
        assert data["name"] == sample_profile_update["name"]
        assert data["class_name"] == sample_profile_update["class_name"]
        assert data["email"] == sample_profile_update["email"]

    def test_update_profile_with_invalid_email(
        self, client_with_db: TestClient, test_user: Member, auth_headers
    ):
        """Test updating profile with invalid email."""
        access_token = create_access_token(subject=test_user.id)
        headers = auth_headers(access_token)

        invalid_update = {"email": "invalid-email-format"}

        response = client_with_db.put(
            "/api/v1/auth/me", headers=headers, json=invalid_update
        )

        assert response.status_code == 422  # Validation error

    def test_regular_user_cannot_update_role(
        self, client_with_db: TestClient, test_user: Member, auth_headers
    ):
        """Test that regular users cannot update sensitive fields."""
        access_token = create_access_token(subject=test_user.id)
        headers = auth_headers(access_token)

        role_update = {"role": "admin", "is_active": False}

        response = client_with_db.put(
            "/api/v1/auth/me", headers=headers, json=role_update
        )

        assert response.status_code == 403
        assert "Not authorized" in response.json()["detail"]


class TestPasswordChange:
    """Test cases for password change endpoint."""

    def test_successful_password_change(
        self,
        client_with_db: TestClient,
        test_user: Member,
        auth_headers,
        sample_password_change: dict,
        test_response,
    ):
        """Test successful password change."""
        access_token = create_access_token(subject=test_user.id)
        headers = auth_headers(access_token)

        response = client_with_db.put(
            "/api/v1/auth/change-password", headers=headers, json=sample_password_change
        )

        assert response.status_code == 200
        assert test_response.is_success(response)
        assert "Password changed successfully" in test_response.get_message(response)

    def test_password_change_with_wrong_current_password(
        self,
        client_with_db: TestClient,
        test_user: Member,
        auth_headers,
        sample_invalid_password_change: dict,
    ):
        """Test password change with wrong current password."""
        access_token = create_access_token(subject=test_user.id)
        headers = auth_headers(access_token)

        response = client_with_db.put(
            "/api/v1/auth/change-password",
            headers=headers,
            json=sample_invalid_password_change,
        )

        assert response.status_code == 400
        assert "Current password is incorrect" in response.json()["detail"]

    def test_password_change_with_weak_password(
        self,
        client_with_db: TestClient,
        test_user: Member,
        auth_headers,
        sample_weak_password_change: dict,
    ):
        """Test password change with weak password."""
        access_token = create_access_token(subject=test_user.id)
        headers = auth_headers(access_token)

        response = client_with_db.put(
            "/api/v1/auth/change-password",
            headers=headers,
            json=sample_weak_password_change,
        )

        assert response.status_code == 422
        assert (
            "Password does not meet strength requirements"
            in response.json()["detail"]["message"]
        )

    def test_password_change_same_as_current(
        self, client_with_db: TestClient, test_user: Member, auth_headers
    ):
        """Test password change with same password as current."""
        access_token = create_access_token(subject=test_user.id)
        headers = auth_headers(access_token)

        same_password_change = {
            "current_password": "TestPassword123!",
            "new_password": "TestPassword123!",
        }

        response = client_with_db.put(
            "/api/v1/auth/change-password", headers=headers, json=same_password_change
        )

        assert response.status_code == 400
        assert "New password must be different" in response.json()["detail"]


class TestTokenVerification:
    """Test cases for token verification endpoint."""

    def test_verify_valid_token(
        self, client_with_db: TestClient, test_user: Member, auth_headers, test_response
    ):
        """Test verifying a valid token."""
        access_token = create_access_token(subject=test_user.id)
        headers = auth_headers(access_token)

        response = client_with_db.get("/api/v1/auth/verify-token", headers=headers)

        assert response.status_code == 200
        assert test_response.is_success(response)

        data = test_response.get_data(response)
        assert data["valid"] is True
        assert data["user_id"] == test_user.id
        assert "expires_at" in data
        assert "user" in data

    def test_verify_invalid_token(self, client_with_db: TestClient, auth_headers):
        """Test verifying an invalid token."""
        headers = auth_headers("invalid.token.here")

        response = client_with_db.get("/api/v1/auth/verify-token", headers=headers)

        assert response.status_code == 401
        assert "Invalid token" in response.json()["detail"]

    def test_verify_expired_token(
        self, client_with_db: TestClient, test_user: Member, auth_headers
    ):
        """Test verifying an expired token."""
        from datetime import timedelta

        expired_token = create_access_token(
            subject=test_user.id, expires_delta=timedelta(seconds=-1)
        )
        headers = auth_headers(expired_token)

        response = client_with_db.get("/api/v1/auth/verify-token", headers=headers)

        assert response.status_code == 401
        assert "Invalid token" in response.json()["detail"]


class TestLogout:
    """Test cases for logout endpoint."""

    def test_successful_logout(
        self, client_with_db: TestClient, test_user: Member, auth_headers, test_response
    ):
        """Test successful logout."""
        access_token = create_access_token(subject=test_user.id)
        headers = auth_headers(access_token)

        response = client_with_db.post("/api/v1/auth/logout", headers=headers)

        assert response.status_code == 200
        assert test_response.is_success(response)
        assert "Logout successful" in test_response.get_message(response)

    def test_logout_without_auth(self, client_with_db: TestClient):
        """Test logout without authentication."""
        response = client_with_db.post("/api/v1/auth/logout")

        assert response.status_code == 403  # No auth header


class TestAuthHealthCheck:
    """Test cases for auth service health check."""

    def test_auth_health_check(self, client_with_db: TestClient, test_response):
        """Test auth service health check."""
        response = client_with_db.get("/api/v1/auth/health")

        assert response.status_code == 200
        assert test_response.is_success(response)

        data = test_response.get_data(response)
        assert data["service"] == "auth"
        assert data["status"] == "healthy"
