"""
Integration tests for Import API endpoints.
Tests the complete import API flow with database interactions.
"""

import pytest
from httpx import AsyncClient

from app.models.member import Member, UserRole


class TestImportIntegration:
    """Integration tests for Import API endpoints."""

    @pytest.mark.asyncio
    async def test_get_field_mapping_integration(
        self,
        async_client: AsyncClient,
        db_session,
        sample_import_member,
        auth_token_for_import_member,
    ):
        """Test field mapping endpoint with real database integration."""
        # Test task table mapping
        headers = {"Authorization": f"Bearer {auth_token_for_import_member}"}
        response = await async_client.get(
            "/api/v1/import/field-mapping",
            headers=headers,
            params={"table_type": "task_table"},
        )

        # Verify response
        assert response.status_code == 200
        data = response.json()

        assert data["success"] is True
        assert "data" in data

        # Verify comprehensive field mapping structure
        mapping_data = data["data"]
        assert mapping_data["table_type"] == "task_table"

        # Check all required sections are present
        required_sections = [
            "fields",
            "field_types",
            "required_fields",
            "optional_fields",
            "mapping_rules",
            "validation_rules",
            "import_examples",
            "data_processing_rules",
        ]

        for section in required_sections:
            assert section in mapping_data, f"Missing required section: {section}"

        # Verify field definitions
        fields = mapping_data["fields"]
        assert "报修人姓名" in fields
        assert "联系方式" in fields
        assert "故障描述" in fields
        assert fields["报修人姓名"] == "任务报修人的姓名"

        # Verify field types
        field_types = mapping_data["field_types"]
        assert field_types["报修人姓名"] == "string"
        assert field_types["报修时间"] == "datetime"
        assert field_types["评分"] == "integer"

        # Verify required fields
        required_fields = mapping_data["required_fields"]
        assert "报修人姓名" in required_fields
        assert "联系方式" in required_fields
        assert "故障描述" in required_fields

    @pytest.mark.asyncio
    async def test_get_field_mapping_member_table_integration(
        self,
        async_client: AsyncClient,
        db_session,
        admin_import_member,
        auth_token_for_admin_import,
    ):
        """Test member table field mapping with admin privileges."""
        headers = {"Authorization": f"Bearer {auth_token_for_admin_import}"}
        response = await async_client.get(
            "/api/v1/import/field-mapping",
            headers=headers,
            params={"table_type": "member_table"},
        )

        # Verify response
        assert response.status_code == 200
        data = response.json()

        assert data["success"] is True
        mapping_data = data["data"]
        assert mapping_data["table_type"] == "member_table"

        # Check member-specific fields
        fields = mapping_data["fields"]
        assert "姓名" in fields
        assert "学号" in fields
        assert "手机号" in fields
        assert "部门" in fields

        # Check validation rules specific to members
        validation_rules = mapping_data["validation_rules"]
        assert "学号格式" in validation_rules
        assert "手机号格式" in validation_rules

        # Verify student ID format rule
        student_id_rule = validation_rules["学号格式"]
        assert "正则表达式" in student_id_rule
        assert student_id_rule["正则表达式"] == "^[A-Z0-9]{8,12}$"

    @pytest.mark.asyncio
    async def test_get_field_mapping_attendance_table_integration(
        self,
        async_client: AsyncClient,
        db_session,
        admin_import_member,
        auth_token_for_admin_import,
    ):
        """Test attendance table field mapping integration."""
        headers = {"Authorization": f"Bearer {auth_token_for_admin_import}"}
        response = await async_client.get(
            "/api/v1/import/field-mapping",
            headers=headers,
            params={"table_type": "attendance_table"},
        )

        # Verify response
        assert response.status_code == 200
        data = response.json()

        mapping_data = data["data"]
        assert mapping_data["table_type"] == "attendance_table"

        # Check attendance-specific fields
        fields = mapping_data["fields"]
        assert "成员姓名" in fields
        assert "签到时间" in fields
        assert "签退时间" in fields
        assert "工作时长" in fields

        # Check business logic rules
        mapping_rules = mapping_data["mapping_rules"]
        assert "工时计算" in mapping_rules
        work_time_calc = mapping_rules["工时计算"]
        assert "自动计算" in work_time_calc["logic"]
        assert work_time_calc["logic"]["自动计算"] == "基于签到签退时间差"

    @pytest.mark.asyncio
    async def test_field_mapping_business_rules_integration(
        self,
        async_client: AsyncClient,
        db_session,
        sample_import_member,
        auth_token_for_import_member,
    ):
        """Test business rules in field mapping integration."""
        headers = {"Authorization": f"Bearer {auth_token_for_import_member}"}
        response = await async_client.get(
            "/api/v1/import/field-mapping",
            headers=headers,
            params={"table_type": "task_table"},
        )

        assert response.status_code == 200
        data = response.json()
        mapping_data = data["data"]

        # Test comprehensive business rules
        mapping_rules = mapping_data["mapping_rules"]

        # Check reporter matching logic
        assert "报修人匹配" in mapping_rules
        reporter_matching = mapping_rules["报修人匹配"]
        assert reporter_matching["logic"]["primary"] == "姓名+联系方式精确匹配"
        assert reporter_matching["logic"]["fallback"] == "姓名模糊匹配"
        assert "忽略括号和职位后缀" in reporter_matching["logic"]["preprocessing"]

        # Check online/offline determination
        assert "在线/线下判断" in mapping_rules
        online_offline = mapping_rules["在线/线下判断"]
        assert "处理方式" in online_offline["logic"]

        online_keywords = online_offline["online_keywords"]
        assert "远程处理" in online_keywords
        assert "在线处理" in online_keywords

        offline_keywords = online_offline["offline_keywords"]
        assert "现场处理" in offline_keywords
        assert "现场维修" in offline_keywords
        assert "上门服务" in offline_keywords

    @pytest.mark.asyncio
    async def test_field_mapping_import_examples_integration(
        self,
        async_client: AsyncClient,
        db_session,
        sample_import_member,
        auth_token_for_import_member,
    ):
        """Test import examples in field mapping integration."""
        headers = {"Authorization": f"Bearer {auth_token_for_import_member}"}
        response = await async_client.get(
            "/api/v1/import/field-mapping",
            headers=headers,
            params={"table_type": "task_table"},
        )

        assert response.status_code == 200
        data = response.json()
        mapping_data = data["data"]

        # Check import examples
        import_examples = mapping_data["import_examples"]

        # Valid record example
        assert "valid_record" in import_examples
        valid_record = import_examples["valid_record"]
        assert valid_record["报修人姓名"] == "张三"
        assert valid_record["联系方式"] == "13800138000"
        assert valid_record["处理方式"] == "现场维修"
        assert valid_record["评分"] == 5

        # Invalid records examples
        assert "invalid_records" in import_examples
        invalid_records = import_examples["invalid_records"]
        assert len(invalid_records) >= 3

        # Check specific invalid record types
        error_types = [record["error_reason"] for record in invalid_records]
        assert "缺少必填字段" in error_types
        assert "联系方式格式错误" in error_types
        assert "日期格式错误" in error_types

    @pytest.mark.asyncio
    async def test_field_mapping_validation_rules_integration(
        self,
        async_client: AsyncClient,
        db_session,
        sample_import_member,
        auth_token_for_import_member,
    ):
        """Test validation rules in field mapping integration."""
        headers = {"Authorization": f"Bearer {auth_token_for_import_member}"}
        response = await async_client.get(
            "/api/v1/import/field-mapping",
            headers=headers,
            params={"table_type": "task_table"},
        )

        assert response.status_code == 200
        data = response.json()
        mapping_data = data["data"]

        # Check validation rules
        validation_rules = mapping_data["validation_rules"]

        # Phone number validation
        assert "联系方式格式" in validation_rules
        phone_validation = validation_rules["联系方式格式"]
        assert phone_validation["pattern"] == "^1[3-9]\\d{9}$"
        assert phone_validation["message"] == "请输入有效的11位手机号码"

        # Rating validation
        assert "评分范围" in validation_rules
        rating_validation = validation_rules["评分范围"]
        assert rating_validation["min"] == 1
        assert rating_validation["max"] == 5
        assert rating_validation["type"] == "integer"

        # Date format validation
        assert "日期时间格式" in validation_rules
        datetime_validation = validation_rules["日期时间格式"]
        supported_formats = datetime_validation["supported_formats"]
        assert "YYYY-MM-DD HH:mm:ss" in supported_formats
        assert "YYYY/MM/DD HH:mm" in supported_formats

    @pytest.mark.asyncio
    async def test_field_mapping_unauthorized_access(
        self, async_client: AsyncClient, db_session
    ):
        """Test field mapping endpoint without authentication."""
        # Request without authorization header
        response = await async_client.get(
            "/api/v1/import/field-mapping", params={"table_type": "task_table"}
        )

        # Should require authentication
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_field_mapping_different_table_types(
        self,
        async_client: AsyncClient,
        db_session,
        sample_import_member,
        auth_token_for_import_member,
    ):
        """Test field mapping for different table types."""
        headers = {"Authorization": f"Bearer {auth_token_for_import_member}"}

        # Test each table type
        table_types = ["task_table", "member_table", "attendance_table"]

        for table_type in table_types:
            response = await async_client.get(
                "/api/v1/import/field-mapping",
                headers=headers,
                params={"table_type": table_type},
            )

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["data"]["table_type"] == table_type

    @pytest.mark.asyncio
    async def test_field_mapping_data_processing_rules_integration(
        self,
        async_client: AsyncClient,
        db_session,
        sample_import_member,
        auth_token_for_import_member,
    ):
        """Test data processing rules in field mapping integration."""
        headers = {"Authorization": f"Bearer {auth_token_for_import_member}"}
        response = await async_client.get(
            "/api/v1/import/field-mapping",
            headers=headers,
            params={"table_type": "task_table"},
        )

        assert response.status_code == 200
        data = response.json()
        mapping_data = data["data"]

        # Check data processing rules
        processing_rules = mapping_data["data_processing_rules"]

        # Preprocessing rules
        assert "数据预处理" in processing_rules
        preprocessing = processing_rules["数据预处理"]
        assert "去除空格" in preprocessing
        assert preprocessing["去除空格"] == "自动去除字段首尾空格"
        assert "标准化格式" in preprocessing
        assert "字段映射" in preprocessing

        # Validation rules
        assert "数据校验" in processing_rules
        validation = processing_rules["数据校验"]
        assert "必填字段检查" in validation
        assert "格式验证" in validation
        assert "业务逻辑验证" in validation

        # Import processing
        assert "导入处理" in processing_rules
        import_processing = processing_rules["导入处理"]
        assert "批量处理" in import_processing
        assert "错误处理" in import_processing
        assert "成功回调" in import_processing


@pytest.fixture
async def sample_import_member(db_session) -> Member:
    """Create a sample member for import testing."""
    member = Member(
        username="import_test_user",
        name="导入测试用户",
        student_id="IMPORT001",
        phone="13800138002",
        department="信息化建设处",
        class_name="导入测试班",
        password_hash="import_test_hash",
        role=UserRole.MEMBER,
        is_active=True,
    )
    db_session.add(member)
    await db_session.flush()
    return member


@pytest.fixture
async def admin_import_member(db_session) -> Member:
    """Create an admin member for import testing."""
    member = Member(
        username="import_admin_user",
        name="导入管理员用户",
        student_id="IMPORTADMIN",
        phone="13800138003",
        department="信息化建设处",
        class_name="管理员班",
        password_hash="import_admin_hash",
        role=UserRole.ADMIN,
        is_active=True,
    )
    db_session.add(member)
    await db_session.flush()
    return member


@pytest.fixture
def auth_token_for_import_member(sample_import_member) -> str:
    """Create authentication token for import test member."""
    from app.core.security import create_access_token

    return create_access_token({"sub": sample_import_member.username})


@pytest.fixture
def auth_token_for_admin_import(admin_import_member) -> str:
    """Create authentication token for admin import member."""
    from app.core.security import create_access_token

    return create_access_token({"sub": admin_import_member.username})
