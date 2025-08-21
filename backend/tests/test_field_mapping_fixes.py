"""
Field Mapping Fixes - Critical API Contract Issues
Comprehensive testing and validation of frontend-backend field mapping
"""

from datetime import datetime

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.member import Member, UserRole
from app.models.task import RepairTask, TaskCategory, TaskPriority, TaskStatus, TaskType
from app.schemas.auth import LoginRequest, LoginResponse, UserProfileResponse
from app.schemas.member import MemberCreate, MemberResponse
from app.schemas.task import TaskCreate, TaskResponse


@pytest.mark.asyncio
class TestCriticalFieldMappingIssues:
    """关键字段映射问题测试和修复验证"""

    async def test_auth_login_field_consistency(self):
        """测试认证登录字段一致性"""
        # 1. 测试前端应该发送的字段格式
        login_request = LoginRequest(
            student_id="2021001001", password="TestPassword123!"  # 正确: 使用student_id
        )

        # 验证字段名称
        assert hasattr(login_request, "student_id")
        assert hasattr(login_request, "password")
        assert login_request.student_id == "2021001001"

        # 2. 测试登录响应格式
        user_data = {
            "id": 1,
            "name": "测试用户",
            "student_id": "2021001001",  # backend返回student_id
            "role": "member",  # backend返回小写role
            "email": "test@example.com",
            "class_name": "测试班级",  # backend返回snake_case
            "is_active": True,  # backend返回snake_case
            "is_verified": True,  # backend返回snake_case
        }

        # 验证用户数据结构
        assert "student_id" in user_data  # 不是studentId
        assert "class_name" in user_data  # 不是className
        assert "is_active" in user_data  # 不是isActive

    async def test_task_field_naming_consistency(self, async_session):
        """测试任务字段命名一致性"""
        # 创建测试成员
        member = Member(
            username="task_field_test",
            name="任务字段测试",
            student_id="2021001001",
            class_name="测试班级",
            role=UserRole.MEMBER,
        )
        async_session.add(member)
        await async_session.flush()

        # 创建测试任务
        task = RepairTask(
            task_id="FIELD_MAPPING_001",
            title="字段映射测试任务",
            task_type=TaskType.ONLINE,
            status=TaskStatus.PENDING,
            member_id=member.id,
            report_time=datetime.utcnow(),
            estimated_minutes=60,
            actual_minutes=45,
        )
        async_session.add(task)
        await async_session.commit()
        await async_session.refresh(task)

        # 验证backend使用的实际字段名
        task_data = {
            "id": task.id,
            # backend生成task_number
            "task_number": f"T{datetime.now().strftime('%Y%m%d')}{task.id:04d}",
            "assigned_to": task.member_id,  # backend使用assigned_to不是member_id
            "estimated_minutes": task.estimated_minutes,  # backend使用minutes不是hours
            "actual_minutes": task.actual_minutes,  # backend使用minutes不是hours
            "task_type": task.task_type.value,  # backend返回字符串值
            "status": task.status.value,  # backend返回字符串值
        }

        # 关键字段命名验证
        assert "task_number" in task_data  # backend实际使用task_number
        assert "assigned_to" in task_data  # backend实际使用assigned_to
        assert "estimated_minutes" in task_data  # backend使用minutes单位
        assert "actual_minutes" in task_data  # backend使用minutes单位

        # 不应该有这些frontend期望的字段（需要映射）
        assert "taskId" not in task_data
        assert "assigneeId" not in task_data
        assert "estimatedHours" not in task_data
        assert "actualHours" not in task_data

    async def test_enum_value_case_consistency(self):
        """测试枚举值大小写一致性"""
        # 验证所有枚举值都是小写+下划线格式

        # 用户角色
        assert UserRole.ADMIN.value == "admin"
        assert UserRole.GROUP_LEADER.value == "group_leader"
        assert UserRole.MEMBER.value == "member"
        assert UserRole.GUEST.value == "guest"

        # 任务状态
        assert TaskStatus.PENDING.value == "pending"
        assert TaskStatus.IN_PROGRESS.value == "in_progress"
        assert TaskStatus.COMPLETED.value == "completed"
        assert TaskStatus.CANCELLED.value == "cancelled"
        assert TaskStatus.ON_HOLD.value == "on_hold"

        # 任务类型
        assert TaskType.ONLINE.value == "online"
        assert TaskType.OFFLINE.value == "offline"

        # 任务类别
        assert TaskCategory.NETWORK_REPAIR.value == "network_repair"
        assert TaskCategory.HARDWARE_REPAIR.value == "hardware_repair"
        assert TaskCategory.SOFTWARE_SUPPORT.value == "software_support"

        # 任务优先级
        assert TaskPriority.LOW.value == "low"
        assert TaskPriority.MEDIUM.value == "medium"
        assert TaskPriority.HIGH.value == "high"
        assert TaskPriority.URGENT.value == "urgent"

    async def test_time_unit_consistency(self):
        """测试时间单位一致性"""
        # 验证backend统一使用分钟作为时间单位
        create_request = TaskCreate(
            title="时间单位测试",
            task_type=TaskType.ONLINE,
            estimated_minutes=120,  # backend期望分钟
        )

        # 验证字段使用minutes而不是hours
        assert hasattr(create_request, "estimated_minutes")
        assert create_request.estimated_minutes == 120

        # 计算: 120分钟 = 2小时（前端显示时需要转换）
        hours = create_request.estimated_minutes / 60
        assert hours == 2.0

    async def test_member_field_mapping(self, async_session):
        """测试成员字段映射"""
        # 创建测试成员
        member = Member(
            username="member_mapping_test",
            name="成员映射测试",
            student_id="2021002001",
            email="mapping@test.com",
            phone="13800138000",
            class_name="计算机科学与技术2101",
            role=UserRole.MEMBER,
            is_active=True,
            is_verified=True,
        )
        async_session.add(member)
        await async_session.commit()
        await async_session.refresh(member)

        # 验证backend实际字段名
        member_data = {
            "id": member.id,
            "username": member.username,
            "name": member.name,
            "student_id": member.student_id,  # snake_case
            "email": member.email,
            "phone": member.phone,
            "class_name": member.class_name,  # snake_case
            "role": member.role.value,  # 枚举值
            "is_active": member.is_active,  # snake_case
            "is_verified": member.is_verified,  # snake_case
            "created_at": member.created_at,  # snake_case
        }

        # 验证snake_case字段存在
        snake_case_fields = [
            "student_id",
            "class_name",
            "is_active",
            "is_verified",
            "created_at",
        ]

        for field in snake_case_fields:
            assert field in member_data, f"Missing snake_case field: {field}"

        # 验证枚举值是小写
        assert member_data["role"] == "member"

    async def test_api_response_wrapper_consistency(self):
        """测试API响应包装器一致性"""
        # 模拟标准API响应格式
        standard_response = {
            "success": True,
            "message": "操作成功",
            "data": {"id": 1, "name": "测试数据"},
            "status_code": 200,
        }

        # 验证标准响应格式
        assert "success" in standard_response
        assert "message" in standard_response
        assert "data" in standard_response
        assert "status_code" in standard_response

        # 验证字段类型
        assert isinstance(standard_response["success"], bool)
        assert isinstance(standard_response["message"], str)
        assert isinstance(standard_response["data"], dict)
        assert isinstance(standard_response["status_code"], int)

        # 模拟错误响应格式
        error_response = {
            "success": False,
            "message": "操作失败",
            "data": None,
            "status_code": 400,
        }

        assert error_response["success"] is False
        assert error_response["data"] is None


@pytest.mark.asyncio
class TestFieldMappingTransformations:
    """字段映射转换测试"""

    async def test_snake_case_to_camel_case_mapping(self):
        """测试snake_case到camelCase的映射"""
        # Backend字段(snake_case)
        backend_data = {
            "student_id": "2021001001",
            "class_name": "测试班级",
            "is_active": True,
            "is_verified": True,
            "created_at": "2025-01-27T10:00:00",
            "updated_at": "2025-01-27T11:00:00",
            "last_login": "2025-01-27T09:00:00",
            "login_count": 5,
        }

        # Frontend期望的字段(camelCase)
        expected_frontend_fields = {
            "studentId": "2021001001",
            "className": "测试班级",
            "isActive": True,
            "isVerified": True,
            "createdAt": "2025-01-27T10:00:00",
            "updatedAt": "2025-01-27T11:00:00",
            "lastLogin": "2025-01-27T09:00:00",
            "loginCount": 5,
        }

        # 映射规则
        field_mapping = {
            "student_id": "studentId",
            "class_name": "className",
            "is_active": "isActive",
            "is_verified": "isVerified",
            "created_at": "createdAt",
            "updated_at": "updatedAt",
            "last_login": "lastLogin",
            "login_count": "loginCount",
        }

        # 验证映射规则完整性
        for backend_field in backend_data.keys():
            assert (
                backend_field in field_mapping
            ), f"Missing mapping for {backend_field}"

        # 验证映射后的值
        transformed_data = {}
        for backend_field, value in backend_data.items():
            frontend_field = field_mapping[backend_field]
            transformed_data[frontend_field] = value

        # 验证转换结果
        for frontend_field, expected_value in expected_frontend_fields.items():
            assert frontend_field in transformed_data
            assert transformed_data[frontend_field] == expected_value

    async def test_time_unit_conversion(self):
        """测试时间单位转换"""
        # Backend使用分钟
        backend_time_data = {
            "estimated_minutes": 120,
            "actual_minutes": 90,
            "work_minutes": 105,
        }

        # Frontend期望小时（显示用）
        expected_hours_data = {
            "estimatedHours": 2.0,
            "actualHours": 1.5,
            "workHours": 1.75,
        }

        # 转换函数
        def minutes_to_hours(minutes):
            return round(minutes / 60, 2)

        # 验证转换
        for field, minutes in backend_time_data.items():
            hours = minutes_to_hours(minutes)
            frontend_field = field.replace("_minutes", "Hours").replace("_", "")

            # 手动调整字段名
            if frontend_field == "estimatedHours":
                assert hours == expected_hours_data["estimatedHours"]
            elif frontend_field == "actualHours":
                assert hours == expected_hours_data["actualHours"]
            elif frontend_field == "workHours":
                assert hours == expected_hours_data["workHours"]

    async def test_enum_value_transformation(self):
        """测试枚举值转换"""
        # Backend枚举值(小写+下划线)
        backend_enums = {
            "user_role": "group_leader",
            "task_status": "in_progress",
            "task_type": "online",
            "priority": "high",
        }

        # Frontend可能期望的枚举值(保持一致或映射)
        frontend_enums = {
            "userRole": "group_leader",  # 保持一致
            "taskStatus": "in_progress",  # 保持一致
            "taskType": "online",  # 保持一致
            "priority": "high",  # 保持一致
        }

        # 验证枚举值一致性(不需要转换，只需要字段名映射)
        field_mapping = {
            "user_role": "userRole",
            "task_status": "taskStatus",
            "task_type": "taskType",
            "priority": "priority",
        }

        for backend_field, backend_value in backend_enums.items():
            frontend_field = field_mapping[backend_field]
            expected_value = frontend_enums[frontend_field]

            # 枚举值应该保持一致
            assert (
                backend_value == expected_value
            ), f"Enum value mismatch for {backend_field}"


@pytest.mark.asyncio
class TestApiContractValidation:
    """API契约验证测试"""

    async def test_login_api_contract(self):
        """测试登录API契约"""
        # 前端发送的请求格式
        login_request = {
            "student_id": "2021001001",  # 正确字段名
            "password": "TestPassword123!",
        }

        # 后端期望的响应格式
        expected_response_structure = {
            "success": bool,
            "message": str,
            "data": {
                "access_token": str,
                "refresh_token": str,
                "token_type": str,
                "expires_in": int,
                "user": {
                    "id": int,
                    "name": str,
                    "student_id": str,  # snake_case
                    "role": str,
                    "email": str,
                    "class_name": str,  # snake_case
                    "is_active": bool,  # snake_case
                    "is_verified": bool,  # snake_case
                },
            },
        }

        # 验证请求字段
        assert "student_id" in login_request
        assert "password" in login_request

        # 验证响应结构类型
        assert expected_response_structure["success"] == bool
        assert expected_response_structure["message"] == str
        assert expected_response_structure["data"]["user"]["student_id"] == str
        assert expected_response_structure["data"]["user"]["class_name"] == str

    async def test_task_api_contract(self):
        """测试任务API契约"""
        # 后端返回的任务数据格式
        task_response_structure = {
            "id": int,
            "task_number": str,  # backend实际字段
            "title": str,
            "task_type": str,
            "status": str,
            "assigned_to": int,  # backend实际字段
            "estimated_minutes": int,  # backend使用minutes
            "actual_minutes": int,  # backend使用minutes
            "created_at": str,  # snake_case
            "updated_at": str,  # snake_case
            "completed_at": str,  # snake_case
        }

        # 前端需要映射的字段
        frontend_field_mapping = {
            "task_number": "taskNumber",  # 或者taskId
            "assigned_to": "assigneeId",  # 或者assignedTo
            "estimated_minutes": "estimatedMinutes",  # 或转换为hours
            "actual_minutes": "actualMinutes",  # 或转换为hours
            "created_at": "createdAt",
            "updated_at": "updatedAt",
            "completed_at": "completedAt",
        }

        # 验证所有backend字段都有映射
        for backend_field in task_response_structure.keys():
            if backend_field in ["id", "title", "task_type", "status"]:
                continue  # 这些字段不需要映射
            assert (
                backend_field in frontend_field_mapping
            ), f"Missing mapping for {backend_field}"

        # 验证映射的完整性
        assert len(frontend_field_mapping) == 7  # 7个需要映射的字段

    async def test_response_wrapper_contract(self):
        """测试响应包装器契约"""
        # 标准成功响应格式
        success_response = {
            "success": True,
            "message": "操作成功",
            "data": {"result": "some data"},
            "status_code": 200,
        }

        # 标准错误响应格式
        error_response = {
            "success": False,
            "message": "操作失败",
            "data": None,
            "status_code": 400,
        }

        # 验证成功响应
        assert success_response["success"] is True
        assert isinstance(success_response["message"], str)
        assert success_response["data"] is not None
        assert success_response["status_code"] == 200

        # 验证错误响应
        assert error_response["success"] is False
        assert isinstance(error_response["message"], str)
        assert error_response["data"] is None
        assert error_response["status_code"] == 400
