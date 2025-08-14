"""
Unit tests for Import API endpoints.
Tests the field mapping and import functionality with mocked dependencies.
"""

from unittest.mock import AsyncMock

import pytest

from app.api.v1.import_api import get_import_field_mapping
from app.models.member import Member, UserRole


class TestImportAPI:
    """Unit tests for Import API endpoints."""

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

        # Verify results
        assert result["success"] is True
        assert result["data"]["table_type"] == "task_table"
        assert "field_mappings" in result["data"]
        assert "business_rules" in result["data"]
        assert "import_config" in result["data"]

        # Check field mappings structure
        field_mappings = result["data"]["field_mappings"]
        assert len(field_mappings) > 0

        # Check business rules
        business_rules = result["data"]["business_rules"]
        assert "matching_strategy" in business_rules
        assert "work_hour_calculation" in business_rules
        assert "status_mapping" in business_rules

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

        # Verify results
        assert result["success"] is True
        assert result["data"]["table_type"] == "member_table"

        # Verify response structure
        assert result["success"] is True
        assert result["data"]["table_type"] == "member_table"
        assert "field_mappings" in result["data"]
        assert "business_rules" in result["data"]

    @pytest.mark.asyncio
    async def test_get_field_mapping_attendance_table_success(self):
        """Test field mapping endpoint - attendance table success case."""
        # Mock dependencies
        mock_db = AsyncMock()
        mock_user = Member(id=1, username="test_user", role=UserRole.ADMIN)

        # Call endpoint
        result = await get_import_field_mapping(
            table_type="attendance_table", current_user=mock_user, db=mock_db
        )

        # Verify results
        assert result["success"] is True
        assert result["data"]["table_type"] == "attendance_table"

        # Check attendance table specific fields
        fields = result["data"]["fields"]
        assert "成员姓名" in fields
        assert "签到时间" in fields
        assert "签退时间" in fields
        assert "工作时长" in fields
        assert "任务类型" in fields

    @pytest.mark.asyncio
    async def test_get_field_mapping_invalid_table_type(self):
        """Test field mapping endpoint - invalid table type."""
        # Mock dependencies
        mock_db = AsyncMock()
        mock_user = Member(id=1, username="test_user", role=UserRole.MEMBER)

        # Call endpoint with invalid table type
        result = await get_import_field_mapping(
            table_type="invalid_table", current_user=mock_user, db=mock_db
        )

        # Verify fallback to task_table
        assert result["success"] is True
        assert result["data"]["table_type"] == "task_table"

    @pytest.mark.asyncio
    async def test_get_field_mapping_comprehensive_response(self):
        """Test field mapping endpoint - comprehensive response structure."""
        # Mock dependencies
        mock_db = AsyncMock()
        mock_user = Member(id=1, username="test_user", role=UserRole.ADMIN)

        # Call endpoint
        result = await get_import_field_mapping(
            table_type="task_table", current_user=mock_user, db=mock_db
        )

        # Verify comprehensive response structure
        assert result["success"] is True
        data = result["data"]

        # Check all required top-level keys
        required_keys = [
            "table_type",
            "fields",
            "field_types",
            "required_fields",
            "optional_fields",
            "mapping_rules",
            "validation_rules",
            "import_examples",
            "data_processing_rules",
        ]

        for key in required_keys:
            assert key in data, f"Missing required key: {key}"

        # Check fields structure
        fields = data["fields"]
        assert isinstance(fields, dict)
        assert len(fields) > 0

        # Check field types
        field_types = data["field_types"]
        assert isinstance(field_types, dict)
        assert "报修人姓名" in field_types
        assert field_types["报修人姓名"] == "string"

        # Check required vs optional fields
        required_fields = data["required_fields"]
        optional_fields = data["optional_fields"]
        assert isinstance(required_fields, list)
        assert isinstance(optional_fields, list)
        assert "报修人姓名" in required_fields
        assert "故障描述" in required_fields

    @pytest.mark.asyncio
    async def test_get_field_mapping_business_rules_detailed(self):
        """Test field mapping endpoint - detailed business rules."""
        # Mock dependencies
        mock_db = AsyncMock()
        mock_user = Member(id=1, username="test_user", role=UserRole.MEMBER)

        # Call endpoint
        result = await get_import_field_mapping(
            table_type="task_table", current_user=mock_user, db=mock_db
        )

        # Verify business rules details
        data = result["data"]
        mapping_rules = data["mapping_rules"]

        # Check specific business logic rules
        assert "报修人匹配" in mapping_rules
        reporter_matching = mapping_rules["报修人匹配"]
        assert "姓名+联系方式" in reporter_matching["logic"]
        assert "模糊匹配" in reporter_matching["fallback"]

        assert "在线/线下判断" in mapping_rules
        online_offline = mapping_rules["在线/线下判断"]
        assert "处理方式" in online_offline["logic"]
        assert ["远程处理", "在线处理"] == online_offline["online_keywords"]
        assert ["现场处理", "现场维修", "上门服务"] == online_offline[
            "offline_keywords"
        ]

    @pytest.mark.asyncio
    async def test_get_field_mapping_import_examples(self):
        """Test field mapping endpoint - import examples provided."""
        # Mock dependencies
        mock_db = AsyncMock()
        mock_user = Member(id=1, username="test_user", role=UserRole.MEMBER)

        # Call endpoint
        result = await get_import_field_mapping(
            table_type="task_table", current_user=mock_user, db=mock_db
        )

        # Verify import examples
        data = result["data"]
        import_examples = data["import_examples"]

        assert "valid_record" in import_examples
        valid_record = import_examples["valid_record"]
        assert "报修人姓名" in valid_record
        assert "联系方式" in valid_record
        assert "故障描述" in valid_record

        assert "invalid_records" in import_examples
        invalid_records = import_examples["invalid_records"]
        assert isinstance(invalid_records, list)
        assert len(invalid_records) > 0

        # Check that invalid records have error descriptions
        for invalid_record in invalid_records:
            assert "data" in invalid_record
            assert "error_reason" in invalid_record

    @pytest.mark.asyncio
    async def test_get_field_mapping_data_processing_rules(self):
        """Test field mapping endpoint - data processing rules."""
        # Mock dependencies
        mock_db = AsyncMock()
        mock_user = Member(id=1, username="test_user", role=UserRole.ADMIN)

        # Call endpoint
        result = await get_import_field_mapping(
            table_type="task_table", current_user=mock_user, db=mock_db
        )

        # Verify data processing rules
        data = result["data"]
        processing_rules = data["data_processing_rules"]

        # Check preprocessing rules
        assert "数据预处理" in processing_rules
        preprocessing = processing_rules["数据预处理"]
        assert "去除空格" in preprocessing
        assert "标准化格式" in preprocessing
        assert "字段映射" in preprocessing

        # Check validation rules
        assert "数据校验" in processing_rules
        validation = processing_rules["数据校验"]
        assert "必填字段检查" in validation
        assert "格式验证" in validation
        assert "业务逻辑验证" in validation

    @pytest.mark.asyncio
    async def test_get_field_mapping_permission_levels(self):
        """Test field mapping endpoint - different permission levels."""
        # Mock dependencies
        mock_db = AsyncMock()

        # Test member permission
        mock_member = Member(id=1, username="member", role=UserRole.MEMBER)
        member_result = await get_import_field_mapping(
            table_type="task_table", current_user=mock_member, db=mock_db
        )

        # Test admin permission
        mock_admin = Member(id=2, username="admin", role=UserRole.ADMIN)
        admin_result = await get_import_field_mapping(
            table_type="member_table", current_user=mock_admin, db=mock_db
        )

        # Both should succeed but may have different content
        assert member_result["success"] is True
        assert admin_result["success"] is True

        # Admin should have access to member table details
        assert admin_result["data"]["table_type"] == "member_table"
