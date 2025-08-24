"""
Simplified auth test to verify database configuration.
Uses direct session injection to avoid fixture complexity.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_password_hash, verify_password
from app.models.member import Member, UserRole
from app.main import app as fastapi_app
from app.core.database import get_async_session


class TestSimpleAuth:
    """Simple auth tests to verify basic functionality."""

    def test_password_hashing_works(self):
        """Test that password hashing works correctly."""
        password = "TestPassword123!"
        hash_result = get_password_hash(password)
        assert hash_result is not None
        assert len(hash_result) > 20
        assert verify_password(password, hash_result) is True
        assert verify_password("wrong_password", hash_result) is False

    @pytest.mark.asyncio
    async def test_user_creation_and_lookup(self, async_session: AsyncSession):
        """Test that user creation and lookup works in the database."""
        # Create user
        user = Member(
            username="test_simple",
            name="Simple Test User",
            student_id="SIMPLE001",
            group_id=1,
            class_name="Test Class",
            email="simple@test.com",
            password_hash=get_password_hash("TestPassword123!"),
            role=UserRole.MEMBER,
            is_active=True,
            is_verified=True,
        )
        
        async_session.add(user)
        await async_session.commit()
        await async_session.refresh(user)
        
        print(f"Created user: {user.id}, {user.student_id}, {user.name}")
        
        # Find user by student_id
        from sqlalchemy import select
        result = await async_session.execute(
            select(Member).where(Member.student_id == "SIMPLE001")
        )
        found_user = result.scalar_one_or_none()
        
        assert found_user is not None
        assert found_user.student_id == "SIMPLE001"
        assert found_user.name == "Simple Test User"
        assert verify_password("TestPassword123!", found_user.password_hash)

    def test_direct_api_test(self):
        """Test the API directly without complex fixtures."""
        # Create a simple test client
        with TestClient(fastapi_app) as client:
            # Try to login with a user that definitely doesn't exist
            response = client.post("/api/v1/auth/login", json={
                "student_id": "NONEXISTENT999",
                "password": "TestPassword123!"
            })
            
            # Should get 401 because user doesn't exist
            assert response.status_code == 401
            data = response.json()
            assert data["success"] is False