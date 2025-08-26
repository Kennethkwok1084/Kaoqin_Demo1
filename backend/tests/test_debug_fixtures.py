"""Debug test to understand fixture execution."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.member import Member


class TestFixtureDebug:
    """Test fixture execution order."""

    def test_fixture_order(
        self,
        client_with_db: TestClient,
        test_user: Member,
        sample_login_data: dict,
    ):
        """Debug fixture execution order."""
        print(f"\n=== FIXTURE DEBUG ===")
        print(f"test_user: {test_user}")
        print(f"test_user.id: {test_user.id}")
        print(f"test_user.student_id: {test_user.student_id}")
        print(f"test_user.name: {test_user.name}")
        print(f"sample_login_data: {sample_login_data}")
        print(f"client_with_db: {client_with_db}")

        # Try to make a simple request first
        print(f"\n=== Making login request ===")
        response = client_with_db.post("/api/v1/auth/login", json=sample_login_data)
        print(f"Response status: {response.status_code}")
        print(f"Response body: {response.text}")

        # This should work now
        assert test_user is not None
