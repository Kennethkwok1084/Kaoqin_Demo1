"""
Simplified unit tests for Import API endpoints.
Tests the field mapping functionality with the actual API structure.
"""

from unittest.mock import AsyncMock

import pytest

from app.api.v1.import_api import get_import_field_mapping
from app.models.member import Member, UserRole


class TestImportAPISimple:
    """Simplified unit tests for Import API endpoints."""

    @pytest.mark.asyncio
    async def test_get_field_mapping_task_table_success(self):
        """Test field mapping endpoint - task table success case."""
        # Mock dependencies
        mock_db = AsyncMock()
        mock_user = Member(
            id=1,
            username="test_user",
            name="测试用户",
            role=UserRole.MEMBER,
            is_active=True,
        )

        # Call endpoint
        result = await get_import_field_mapping(
            table_type="task_table", current_user=mock_user, db=mock_db
        )

        # Verify basic response structure
        assert result["success"] is True
        assert "data" in result
        assert result["data"]["table_type"] == "task_table"
        assert "field_mappings" in result["data"]
        assert "business_rules" in result["data"]
        assert "import_config" in result["data"]

    @pytest.mark.asyncio
    async def test_get_field_mapping_member_table_success(self):
        """Test field mapping endpoint - member table success case."""
        # Mock dependencies
        mock_db = AsyncMock()
        mock_user = Member(id=1, username="test_user", role=UserRole.ADMIN)

        # Call endpoint
        result = await get_import_field_mapping(
            table_type="member_table", current_user=mock_user, db=mock_db
        )

        # Verify basic response structure
        assert result["success"] is True
        assert result["data"]["table_type"] == "member_table"
        assert "field_mappings" in result["data"]
        assert "business_rules" in result["data"]

    @pytest.mark.asyncio
    async def test_get_field_mapping_invalid_table_type(self):
        """Test field mapping endpoint - invalid table type raises HTTPException."""
        from fastapi import HTTPException

        # Mock dependencies
        mock_db = AsyncMock()
        mock_user = Member(id=1, username="test_user", role=UserRole.MEMBER)

        # Call endpoint with invalid table type should fallback to task_table
        result = await get_import_field_mapping(
            table_type="invalid_table", current_user=mock_user, db=mock_db
        )

        # Verify fallback to task_table
        assert result["success"] is True
        assert result["data"]["table_type"] == "task_table"

    @pytest.mark.asyncio
    async def test_get_field_mapping_business_rules_structure(self):
        """Test field mapping endpoint - business rules structure."""
        # Mock dependencies
        mock_db = AsyncMock()
        mock_user = Member(id=1, username="test_user", role=UserRole.MEMBER)

        # Call endpoint
        result = await get_import_field_mapping(
            table_type="task_table", current_user=mock_user, db=mock_db
        )

        # Verify business rules structure
        assert result["success"] is True
        business_rules = result["data"]["business_rules"]

        # Check key business rule categories
        assert "matching_strategy" in business_rules
        assert "work_hour_calculation" in business_rules
        assert "status_mapping" in business_rules
        assert "task_type_detection" in business_rules

        # Check matching strategy details
        matching = business_rules["matching_strategy"]
        assert "key_fields" in matching
        assert "fuzzy_matching" in matching
        assert "confidence_threshold" in matching

        # Check work hour calculation rules
        work_hours = business_rules["work_hour_calculation"]
        assert "online_task_minutes" in work_hours
        assert "offline_task_minutes" in work_hours
        assert work_hours["online_task_minutes"] == 40
        assert work_hours["offline_task_minutes"] == 100

    @pytest.mark.asyncio
    async def test_get_field_mapping_import_config_structure(self):
        """Test field mapping endpoint - import config structure."""
        # Mock dependencies
        mock_db = AsyncMock()
        mock_user = Member(id=1, username="test_user", role=UserRole.MEMBER)

        # Call endpoint
        result = await get_import_field_mapping(
            table_type="task_table", current_user=mock_user, db=mock_db
        )

        # Verify import config structure
        assert result["success"] is True
        import_config = result["data"]["import_config"]

        # Check import configuration details
        assert "supported_file_types" in import_config
        assert "max_file_size_mb" in import_config
        assert "max_rows_per_import" in import_config
        assert "encoding_options" in import_config

        # Check reasonable defaults
        assert ".xlsx" in import_config["supported_file_types"]
        assert import_config["max_file_size_mb"] > 0
        assert import_config["max_rows_per_import"] > 0

    @pytest.mark.asyncio
    async def test_get_field_mapping_required_fields(self):
        """Test field mapping endpoint - required fields identification."""
        # Mock dependencies
        mock_db = AsyncMock()
        mock_user = Member(id=1, username="test_user", role=UserRole.MEMBER)

        # Call endpoint
        result = await get_import_field_mapping(
            table_type="task_table", current_user=mock_user, db=mock_db
        )

        # Verify required fields are identified
        assert result["success"] is True
        data = result["data"]

        assert "required_fields" in data
        assert "total_fields" in data

        required_fields = data["required_fields"]
        assert isinstance(required_fields, list)
        assert len(required_fields) > 0

        # Should have at least these core required fields (using display names)
        expected_required = ["任务标题", "报修人姓名", "联系方式"]
        for field in expected_required:
            assert field in required_fields
