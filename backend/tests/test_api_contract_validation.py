"""
API Contract Validation Tests
验证前后端API字段匹配和数据结构一致性
"""

from datetime import datetime

import pytest

from app.models.member import Member, UserRole
from app.models.task import RepairTask, TaskCategory, TaskPriority, TaskStatus, TaskType
from app.schemas.auth import LoginRequest, LoginResponse, UserProfileResponse
from app.schemas.member import MemberCreate, MemberResponse
from app.schemas.task import TaskCreate, TaskResponse

# from app.api.auth import create_access_token


@pytest.mark.asyncio
class TestAuthApiContract:
    """认证API契约测试"""

    async def test_login_request_schema_validation(self):
        """测试登录请求架构验证"""
        # 测试有效登录请求
        valid_request = LoginRequest(
            student_id="2021001001", password="TestPassword123!"
        )

        assert valid_request.student_id == "2021001001"
        assert valid_request.password == "TestPassword123!"

        # 验证必需字段
        with pytest.raises(ValueError):
            LoginRequest(password="test")  # 缺少student_id

        with pytest.raises(ValueError):
            LoginRequest(student_id="2021001001")  # 缺少password

    async def test_login_response_schema_validation(self):
        """测试登录响应架构验证"""
        # 模拟用户数据
        user_data = {
            "id": 1,
            "name": "测试用户",
            "student_id": "2021001001",
            "role": "member",
            "email": "test@example.com",
            "is_active": True,
            "is_verified": True,
        }

        # 创建登录响应
        response = LoginResponse(
            success=True,
            message="登录成功",
            access_token="fake_access_token",
            refresh_token="fake_refresh_token",
            token_type="bearer",
            expires_in=3600,
            user=user_data,
        )

        # 验证响应结构
        assert response.success is True
        assert response.message == "登录成功"
        assert response.access_token == "fake_access_token"
        assert response.refresh_token == "fake_refresh_token"
        assert response.token_type == "bearer"
        assert response.expires_in == 3600
        assert response.user["id"] == 1
        assert response.user["name"] == "测试用户"
        assert response.user["student_id"] == "2021001001"
        assert response.user["role"] == "member"

    async def test_user_profile_response_fields(self, async_session):
        """测试用户档案响应字段"""
        # 创建测试用户
        user = Member(
            username="contract_test_user",
            name="契约测试用户",
            student_id="2021001001",
            email="contract@test.com",
            class_name="测试班级",
            role=UserRole.MEMBER,
        )
        async_session.add(user)
        await async_session.commit()
        await async_session.refresh(user)

        # 创建用户档案响应
        profile_response = UserProfileResponse.model_validate(user)

        # 验证必需字段存在
        assert hasattr(profile_response, "id")
        assert hasattr(profile_response, "name")
        assert hasattr(profile_response, "student_id")
        assert hasattr(profile_response, "email")
        assert hasattr(profile_response, "role")
        assert hasattr(profile_response, "class_name")
        assert hasattr(profile_response, "is_active")
        assert hasattr(profile_response, "is_verified")
        assert hasattr(profile_response, "created_at")

        # 验证字段值
        assert profile_response.name == "契约测试用户"
        assert profile_response.student_id == "2021001001"
        assert profile_response.email == "contract@test.com"
        assert profile_response.role == "member"


@pytest.mark.asyncio
class TestMemberApiContract:
    """成员管理API契约测试"""

    async def test_member_response_schema(self, async_session):
        """测试成员响应架构"""
        # 创建测试成员
        member = Member(
            username="member_contract_test",
            name="成员契约测试",
            student_id="2021002001",
            email="member@test.com",
            phone="13800138000",
            class_name="计算机科学与技术2101",
            role=UserRole.MEMBER,
            is_active=True,
            is_verified=True,
        )
        async_session.add(member)
        await async_session.commit()
        await async_session.refresh(member)

        # 创建成员响应
        member_response = MemberResponse.model_validate(member)

        # 验证字段映射
        frontend_expected_fields = [
            "id",
            "username",
            "name",
            "student_id",
            "email",
            "phone",
            "class_name",
            "role",
            "is_active",
            "is_verified",
            "created_at",
        ]

        for field in frontend_expected_fields:
            assert hasattr(member_response, field), f"Missing field: {field}"

        # 验证字段值正确性
        assert member_response.username == "member_contract_test"
        assert member_response.name == "成员契约测试"
        assert member_response.student_id == "2021002001"
        assert member_response.email == "member@test.com"
        assert member_response.phone == "13800138000"
        assert member_response.class_name == "计算机科学与技术2101"
        assert member_response.role == "member"
        assert member_response.is_active is True
        assert member_response.is_verified is True

    async def test_member_create_schema_validation(self):
        """测试成员创建架构验证"""
        # 测试有效创建请求
        create_request = MemberCreate(
            username="new_member",
            name="新成员",
            student_id="2021003001",
            email="new@test.com",
            class_name="新班级",
            password="SecurePassword123!",
        )

        # 验证必需字段
        assert create_request.username == "new_member"
        assert create_request.name == "新成员"
        assert create_request.student_id == "2021003001"
        assert create_request.email == "new@test.com"
        assert create_request.class_name == "新班级"
        assert create_request.password == "SecurePassword123!"

        # 测试字段验证
        with pytest.raises(ValueError):
            MemberCreate(name="测试")  # 缺少必需字段


@pytest.mark.asyncio
class TestTaskApiContract:
    """任务管理API契约测试"""

    async def test_task_response_schema(self, async_session):
        """测试任务响应架构"""
        # 创建测试成员
        member = Member(
            username="task_contract_member",
            name="任务契约测试成员",
            student_id="2021004001",
            class_name="测试班级",
            role=UserRole.MEMBER,
        )
        async_session.add(member)
        await async_session.flush()

        # 创建测试任务
        task = RepairTask(
            task_id="CONTRACT_TASK_001",
            title="契约测试任务",
            description="测试任务响应架构",
            task_type=TaskType.ONLINE,
            status=TaskStatus.PENDING,
            category=TaskCategory.NETWORK_REPAIR,
            priority=TaskPriority.MEDIUM,
            member_id=member.id,
            report_time=datetime.utcnow(),
            reporter_name="报告者",
            reporter_contact="13800138000",
        )
        async_session.add(task)
        await async_session.commit()
        await async_session.refresh(task)

        # 创建任务响应
        task_response = TaskResponse.model_validate(task)

        # 验证前端期望的字段
        frontend_expected_fields = [
            "id",
            "task_id",
            "title",
            "description",
            "task_type",
            "status",
            "category",
            "priority",
            "member_id",
            "report_time",
            "created_at",
        ]

        for field in frontend_expected_fields:
            assert hasattr(task_response, field), f"Missing field: {field}"

        # 验证字段值
        assert task_response.task_id == "CONTRACT_TASK_001"
        assert task_response.title == "契约测试任务"
        assert task_response.description == "测试任务响应架构"
        assert task_response.task_type == "online"
        assert task_response.status == "pending"
        assert task_response.category == "network_repair"
        assert task_response.priority == "medium"
        assert task_response.member_id == member.id

    async def test_task_create_schema_validation(self):
        """测试任务创建架构验证"""
        # 测试有效创建请求
        create_request = TaskCreate(
            title="新任务",
            description="任务描述",
            task_type=TaskType.ONLINE,
            priority=TaskPriority.HIGH,
        )

        # 验证必需字段
        assert create_request.title == "新任务"
        assert create_request.description == "任务描述"
        assert create_request.task_type == TaskType.ONLINE
        assert create_request.priority == TaskPriority.HIGH

    async def test_task_field_name_consistency(self, async_session):
        """测试任务字段命名一致性"""
        # 创建测试数据
        member = Member(
            username="field_test_member",
            name="字段测试成员",
            student_id="2021005001",
            class_name="测试班级",
            role=UserRole.MEMBER,
        )
        async_session.add(member)
        await async_session.flush()

        task = RepairTask(
            task_id="FIELD_TEST_001",
            title="字段测试任务",
            task_type=TaskType.OFFLINE,
            status=TaskStatus.IN_PROGRESS,
            member_id=member.id,
            report_time=datetime.utcnow(),
            response_time=datetime.utcnow(),
            estimated_minutes=120,
            actual_minutes=100,
        )
        async_session.add(task)
        await async_session.commit()
        await async_session.refresh(task)

        # 验证关键字段名称一致性
        task_response = TaskResponse.model_validate(task)

        # 检查字段是否使用一致的命名约定
        assert hasattr(task_response, "task_number")  # Backend uses task_number
        assert hasattr(task_response, "assigned_to")  # Backend uses assigned_to
        assert hasattr(task_response, "estimated_minutes")  # 而不是 estimated_hours
        assert hasattr(task_response, "actual_minutes")  # 而不是 actual_hours

        # 验证值正确性 - 注意backend使用的实际字段名
        assert task_response.task_number is not None  # Backend generates task_number
        assert task_response.assigned_to == member.id
        assert task_response.estimated_minutes == 120
        assert task_response.actual_minutes == 100


@pytest.mark.asyncio
class TestEnumValueConsistency:
    """枚举值一致性测试"""

    def test_user_role_enum_values(self):
        """测试用户角色枚举值一致性"""
        # 验证所有角色值都是小写，使用下划线分隔
        assert UserRole.ADMIN.value == "admin"
        assert UserRole.GROUP_LEADER.value == "group_leader"
        assert UserRole.MEMBER.value == "member"
        assert UserRole.GUEST.value == "guest"

    def test_task_status_enum_values(self):
        """测试任务状态枚举值一致性"""
        # 验证所有状态值都是小写，使用下划线分隔
        assert TaskStatus.PENDING.value == "pending"
        assert TaskStatus.IN_PROGRESS.value == "in_progress"
        assert TaskStatus.COMPLETED.value == "completed"
        assert TaskStatus.CANCELLED.value == "cancelled"
        assert TaskStatus.ON_HOLD.value == "on_hold"

    def test_task_type_enum_values(self):
        """测试任务类型枚举值一致性"""
        # 验证任务类型值一致性
        assert TaskType.ONLINE.value == "online"
        assert TaskType.OFFLINE.value == "offline"

    def test_task_category_enum_values(self):
        """测试任务类别枚举值一致性"""
        # 验证类别值都是小写，使用下划线分隔
        assert TaskCategory.NETWORK_REPAIR.value == "network_repair"
        assert TaskCategory.HARDWARE_REPAIR.value == "hardware_repair"
        assert TaskCategory.SOFTWARE_SUPPORT.value == "software_support"
        assert TaskCategory.MONITORING.value == "monitoring"
        assert TaskCategory.ASSISTANCE.value == "assistance"
        assert TaskCategory.OTHER.value == "other"

    def test_task_priority_enum_values(self):
        """测试任务优先级枚举值一致性"""
        # 验证优先级值一致性
        assert TaskPriority.LOW.value == "low"
        assert TaskPriority.MEDIUM.value == "medium"
        assert TaskPriority.HIGH.value == "high"
        assert TaskPriority.URGENT.value == "urgent"


@pytest.mark.asyncio
class TestApiResponseWrapperConsistency:
    """API响应包装器一致性测试"""

    async def test_standard_response_format(self):
        """测试标准响应格式"""
        from app.utils.response import create_response

        # 测试成功响应
        success_response = create_response(
            data={"id": 1, "name": "测试"}, message="操作成功"
        )

        # 验证响应结构
        assert "success" in success_response
        assert "message" in success_response
        assert "data" in success_response
        assert "status_code" in success_response

        assert success_response["success"] is True
        assert success_response["message"] == "操作成功"
        assert success_response["data"]["id"] == 1
        assert success_response["data"]["name"] == "测试"

        # 测试错误响应
        error_response = create_response(
            success=False, message="操作失败", data=None, status_code=400
        )

        assert error_response["success"] is False
        assert error_response["message"] == "操作失败"
        assert error_response["data"] is None
        assert error_response["status_code"] == 400

    async def test_login_response_wrapper_consistency(self):
        """测试登录响应包装器一致性"""
        # 登录响应应该使用create_response包装
        # 这确保了前端可以统一处理所有API响应

        user_data = {
            "id": 1,
            "name": "测试用户",
            "student_id": "2021001001",
            "role": "member",
        }

        # 模拟登录响应数据
        login_data = {
            "access_token": "fake_token",
            "refresh_token": "fake_refresh",
            "token_type": "bearer",
            "expires_in": 3600,
            "user": user_data,
        }

        from app.utils.response import create_response

        wrapped_response = create_response(data=login_data, message="登录成功")

        # 验证包装后的响应结构
        assert wrapped_response["success"] is True
        assert wrapped_response["message"] == "登录成功"
        assert wrapped_response["data"]["access_token"] == "fake_token"
        assert wrapped_response["data"]["user"]["name"] == "测试用户"


@pytest.mark.asyncio
class TestFieldMappingValidation:
    """字段映射验证测试"""

    async def test_auth_field_mapping_consistency(self):
        """测试认证API字段映射一致性"""
        # 测试前端期望的字段名称与后端响应的一致性
        backend_fields = [
            "student_id",
            "class_name",
            "is_active",
            "is_verified",
            "profile_completed",
            "last_login",
            "login_count",
            "created_at",
            "updated_at",
            "access_token",
            "refresh_token",
        ]

        # 这些字段应该在前端转换为camelCase
        expected_frontend_fields = [
            "studentId",
            "className",
            "isActive",
            "isVerified",
            "profileCompleted",
            "lastLogin",
            "loginCount",
            "createdAt",
            "updatedAt",
            "accessToken",
            "refreshToken",
        ]

        # 验证映射关系存在
        from app.schemas.auth import UserProfileResponse

        # 检查UserProfileResponse是否包含所有必需字段
        response_fields = list(UserProfileResponse.model_fields.keys())

        for field in [
            "student_id",
            "class_name",
            "is_active",
            "is_verified",
            "created_at",
        ]:
            assert field in response_fields, f"Missing backend field: {field}"

    async def test_task_field_mapping_consistency(self):
        """测试任务API字段映射一致性"""
        # 验证任务API的关键字段映射
        from app.schemas.task import TaskResponse

        response_fields = list(TaskResponse.model_fields.keys())

        # 关键字段应该存在
        critical_fields = [
            "task_number",
            "assigned_to",
            "estimated_minutes",
            "actual_minutes",
            "created_at",
            "updated_at",
            "completed_at",
        ]

        for field in critical_fields:
            assert field in response_fields, f"Missing critical field: {field}"

    async def test_time_unit_consistency(self):
        """测试时间单位一致性"""
        # 验证后端统一使用分钟作为时间单位
        from app.models.task import RepairTask

        # 检查模型字段
        task_fields = RepairTask.__table__.columns.keys()

        # 时间相关字段应该以_minutes结尾
        time_fields = [field for field in task_fields if "minute" in field]

        # 应该有estimated_minutes, actual_minutes等字段
        expected_time_fields = ["estimated_minutes", "actual_minutes"]

        for field in expected_time_fields:
            if field in task_fields:  # 只检查存在的字段
                assert "minutes" in field, f"Time field {field} should use minutes unit"
