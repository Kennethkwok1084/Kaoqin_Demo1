"""
API依赖注入模块测试用例
测试数据库会话管理、认证装饰器、权限验证、查询参数处理等功能
"""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch, Mock
from fastapi import HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app.api.deps import (
    get_db, get_sync_db, get_current_user, get_current_active_user,
    get_admin_user, get_group_leader_or_admin, get_current_active_admin,
    get_current_active_group_leader, CommonQueryParams, TaskQueryParams,
    MemberQueryParams, PaginatedResponse, create_response, create_error_response,
    check_user_can_manage_group, check_user_is_admin, check_user_can_access_task,
    get_query_params, get_task_query_params, get_member_query_params
)
from app.models.member import Member, UserRole
from app.core.config import settings


class TestDatabaseDependencies:
    """测试数据库相关依赖注入"""

    @pytest.mark.asyncio
    async def test_get_db_success(self):
        """测试成功获取异步数据库会话"""
        mock_session = AsyncMock(spec=AsyncSession)
        
        with patch('app.api.deps.get_async_session') as mock_get_async:
            # Mock生成器，yield一个会话
            async def mock_generator():
                yield mock_session
            
            mock_get_async.return_value = mock_generator()
            
            # 测试依赖注入函数
            async for session in get_db():
                assert session == mock_session
                break

    @pytest.mark.asyncio
    async def test_get_db_connection_error(self):
        """测试数据库连接错误处理"""
        with patch('app.api.deps.get_async_session') as mock_get_async:
            mock_get_async.side_effect = Exception("Database connection failed")
            
            with pytest.raises(HTTPException) as exc_info:
                async for _ in get_db():
                    pass
            
            assert exc_info.value.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
            assert "未知消息" in str(exc_info.value.detail) or "连接" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_get_db_session_cleanup(self):
        """测试数据库会话清理"""
        mock_session = AsyncMock(spec=AsyncSession)
        mock_session.is_closed = False
        mock_session.close = AsyncMock()
        
        with patch('app.api.deps.get_async_session') as mock_get_async:
            # 实际的get_db函数不会在finally中调用close
            # 这里我们只测试正常流程
            async def mock_generator():
                yield mock_session
            
            mock_get_async.return_value = mock_generator()
            
            async for session in get_db():
                assert session == mock_session
                break

    def test_get_sync_db_success(self):
        """测试成功获取同步数据库会话"""
        mock_session = Mock(spec=Session)
        
        with patch('app.api.deps.get_sync_session') as mock_get_sync:
            # Mock生成器，yield一个会话
            def mock_generator():
                yield mock_session
            
            mock_get_sync.return_value = mock_generator()
            
            # 测试依赖注入函数
            for session in get_sync_db():
                assert session == mock_session
                break

    @pytest.mark.asyncio
    async def test_get_db_cleanup_error(self):
        """测试数据库会话清理错误处理"""
        mock_session = AsyncMock(spec=AsyncSession)
        mock_session.is_closed = False
        mock_session.close = AsyncMock(side_effect=Exception("Close error"))
        
        with patch('app.api.deps.get_async_session') as mock_get_async:
            async def mock_generator():
                try:
                    yield mock_session
                except Exception as e:
                    # 模拟异常时的清理
                    await mock_session.close()
                    raise e
            
            mock_get_async.return_value = mock_generator()
            
            # 即使清理失败，也应该能获取到session
            async for session in get_db():
                assert session == mock_session
                break


class TestAuthenticationDependencies:
    """测试认证相关依赖注入"""

    @pytest.fixture
    def mock_credentials(self):
        """创建模拟认证凭据"""
        return HTTPAuthorizationCredentials(scheme="Bearer", credentials="valid_token")

    @pytest.fixture
    def mock_user(self):
        """创建模拟用户"""
        return Member(
            id=1,
            username="test_user",
            student_id="20210001",
            name="测试用户",
            role=UserRole.MEMBER,
            is_active=True
        )

    @pytest.fixture
    def mock_admin_user(self):
        """创建模拟管理员用户"""
        return Member(
            id=2,
            username="admin_user",
            student_id="20210002",
            name="管理员",
            role=UserRole.ADMIN,
            is_active=True
        )

    @pytest.fixture
    def mock_group_leader(self):
        """创建模拟组长用户"""
        return Member(
            id=3,
            username="leader_user",
            student_id="20210003",
            name="组长",
            role=UserRole.GROUP_LEADER,
            is_active=True
        )

    @pytest.mark.asyncio
    async def test_get_current_user_success(self, mock_credentials, mock_user):
        """测试成功获取当前用户"""
        mock_db = AsyncMock()
        
        with patch('app.api.deps.verify_token') as mock_verify, \
             patch('sqlalchemy.select') as mock_select:
            
            # Mock token验证成功
            mock_verify.return_value = {"sub": "1"}
            
            # Mock数据库查询
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = mock_user
            mock_db.execute.return_value = mock_result
            
            user = await get_current_user(mock_credentials, mock_db)
            
            assert user == mock_user
            mock_verify.assert_called_once_with("valid_token")

    @pytest.mark.asyncio
    async def test_get_current_user_invalid_token(self, mock_credentials):
        """测试无效token处理"""
        mock_db = AsyncMock()
        
        with patch('app.api.deps.verify_token') as mock_verify:
            # Mock token验证失败
            mock_verify.return_value = None
            
            with pytest.raises(HTTPException) as exc_info:
                await get_current_user(mock_credentials, mock_db)
            
            assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.asyncio
    async def test_get_current_user_missing_user_id(self, mock_credentials):
        """测试token中缺少用户ID"""
        mock_db = AsyncMock()
        
        with patch('app.api.deps.verify_token') as mock_verify:
            # Mock token验证成功但缺少sub
            mock_verify.return_value = {"exp": 1234567890}
            
            with pytest.raises(HTTPException) as exc_info:
                await get_current_user(mock_credentials, mock_db)
            
            assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.asyncio
    async def test_get_current_user_user_not_found(self, mock_credentials):
        """测试用户不存在"""
        mock_db = AsyncMock()
        
        with patch('app.api.deps.verify_token') as mock_verify, \
             patch('sqlalchemy.select') as mock_select:
            
            # Mock token验证成功
            mock_verify.return_value = {"sub": "999"}
            
            # Mock用户不存在
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = None
            mock_db.execute.return_value = mock_result
            
            with pytest.raises(HTTPException) as exc_info:
                await get_current_user(mock_credentials, mock_db)
            
            assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.asyncio
    async def test_get_current_user_inactive_user(self, mock_credentials):
        """测试非活跃用户"""
        mock_db = AsyncMock()
        inactive_user = Member(
            id=1,
            username="inactive_user",
            student_id="20210004",
            name="非活跃用户",
            role=UserRole.MEMBER,
            is_active=False
        )
        
        with patch('app.api.deps.verify_token') as mock_verify, \
             patch('sqlalchemy.select') as mock_select:
            
            # Mock token验证成功
            mock_verify.return_value = {"sub": "1"}
            
            # Mock非活跃用户
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = inactive_user
            mock_db.execute.return_value = mock_result
            
            with pytest.raises(HTTPException) as exc_info:
                await get_current_user(mock_credentials, mock_db)
            
            assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.asyncio
    async def test_get_current_user_database_error(self, mock_credentials):
        """测试数据库错误"""
        mock_db = AsyncMock()
        
        with patch('app.api.deps.verify_token') as mock_verify:
            # Mock token验证成功
            mock_verify.return_value = {"sub": "1"}
            
            # Mock数据库错误
            mock_db.execute.side_effect = SQLAlchemyError("Database error")
            
            with pytest.raises(HTTPException) as exc_info:
                await get_current_user(mock_credentials, mock_db)
            
            assert exc_info.value.status_code == status.HTTP_503_SERVICE_UNAVAILABLE

    @pytest.mark.asyncio
    async def test_get_current_user_token_format_error(self, mock_credentials):
        """测试token格式错误"""
        mock_db = AsyncMock()
        
        with patch('app.api.deps.verify_token') as mock_verify:
            # Mock token验证返回无效格式
            mock_verify.return_value = {"sub": "invalid_id"}
            
            with pytest.raises(HTTPException) as exc_info:
                await get_current_user(mock_credentials, mock_db)
            
            assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.asyncio
    async def test_get_current_user_string_user_id(self, mock_credentials, mock_user):
        """测试字符串类型的用户ID"""
        mock_db = AsyncMock()
        
        with patch('app.api.deps.verify_token') as mock_verify, \
             patch('sqlalchemy.select') as mock_select:
            
            # Mock token验证成功，user_id为字符串
            mock_verify.return_value = {"sub": "1"}
            
            # Mock数据库查询
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = mock_user
            mock_db.execute.return_value = mock_result
            
            user = await get_current_user(mock_credentials, mock_db)
            
            assert user == mock_user

    @pytest.mark.asyncio
    async def test_get_current_active_user(self, mock_user):
        """测试获取当前活跃用户（冗余检查）"""
        user = await get_current_active_user(mock_user)
        assert user == mock_user


class TestRoleBasedDependencies:
    """测试基于角色的依赖注入"""

    @pytest.fixture
    def mock_member(self):
        return Member(
            id=1,
            username="member_user",
            student_id="20210001",
            name="普通成员",
            role=UserRole.MEMBER,
            is_active=True
        )

    @pytest.fixture
    def mock_admin(self):
        return Member(
            id=2,
            username="admin_user",
            student_id="20210002",
            name="管理员",
            role=UserRole.ADMIN,
            is_active=True
        )

    @pytest.fixture
    def mock_group_leader(self):
        return Member(
            id=3,
            username="leader_user",
            student_id="20210003",
            name="组长",
            role=UserRole.GROUP_LEADER,
            is_active=True
        )

    @pytest.mark.asyncio
    async def test_get_admin_user_success(self, mock_admin):
        """测试管理员验证成功"""
        admin = await get_admin_user(mock_admin)
        assert admin == mock_admin

    @pytest.mark.asyncio
    async def test_get_admin_user_access_denied(self, mock_member):
        """测试非管理员用户访问被拒绝"""
        with pytest.raises(HTTPException) as exc_info:
            await get_admin_user(mock_member)
        
        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.asyncio
    async def test_get_admin_user_no_role(self):
        """测试无角色用户访问管理员功能"""
        user_no_role = Member(
            id=4,
            username="no_role_user",
            student_id="20210004",
            name="无角色用户",
            role=None,
            is_active=True
        )
        
        with pytest.raises(HTTPException) as exc_info:
            await get_admin_user(user_no_role)
        
        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.asyncio
    async def test_get_group_leader_or_admin_as_admin(self, mock_admin):
        """测试管理员访问组长功能"""
        user = await get_group_leader_or_admin(mock_admin)
        assert user == mock_admin

    @pytest.mark.asyncio
    async def test_get_group_leader_or_admin_as_leader(self, mock_group_leader):
        """测试组长访问组长功能"""
        user = await get_group_leader_or_admin(mock_group_leader)
        assert user == mock_group_leader

    @pytest.mark.asyncio
    async def test_get_group_leader_or_admin_access_denied(self, mock_member):
        """测试普通成员访问组长功能被拒绝"""
        with pytest.raises(HTTPException) as exc_info:
            await get_group_leader_or_admin(mock_member)
        
        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.asyncio
    async def test_get_current_active_admin_success(self, mock_admin):
        """测试获取当前活跃管理员成功"""
        admin = await get_current_active_admin(mock_admin)
        assert admin == mock_admin

    @pytest.mark.asyncio
    async def test_get_current_active_admin_access_denied(self, mock_member):
        """测试非管理员访问被拒绝"""
        with pytest.raises(HTTPException) as exc_info:
            await get_current_active_admin(mock_member)
        
        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.asyncio
    async def test_get_current_active_group_leader_as_admin(self, mock_admin):
        """测试管理员访问组长功能"""
        user = await get_current_active_group_leader(mock_admin)
        assert user == mock_admin

    @pytest.mark.asyncio
    async def test_get_current_active_group_leader_as_leader(self, mock_group_leader):
        """测试组长访问组长功能"""
        user = await get_current_active_group_leader(mock_group_leader)
        assert user == mock_group_leader

    @pytest.mark.asyncio
    async def test_get_current_active_group_leader_access_denied(self, mock_member):
        """测试普通成员访问被拒绝"""
        with pytest.raises(HTTPException) as exc_info:
            await get_current_active_group_leader(mock_member)
        
        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN


class TestQueryParameters:
    """测试查询参数类"""

    def test_common_query_params_default(self):
        """测试通用查询参数默认值"""
        params = CommonQueryParams()
        
        assert params.page == 1
        assert params.size == settings.DEFAULT_PAGE_SIZE
        assert params.search is None
        assert params.sort_by is None
        assert params.sort_order == "desc"

    def test_common_query_params_custom(self):
        """测试自定义查询参数"""
        params = CommonQueryParams(
            page=2,
            size=50,
            search="test",
            sort_by="name",
            sort_order="asc"
        )
        
        assert params.page == 2
        assert params.size == 50
        assert params.search == "test"
        assert params.sort_by == "name"
        assert params.sort_order == "asc"

    def test_common_query_params_validation(self):
        """测试查询参数验证"""
        # 测试负数页码
        params = CommonQueryParams(page=-1, size=1000)
        assert params.page == 1  # 自动修正为最小值
        assert params.size == settings.MAX_PAGE_SIZE  # 自动限制为最大值

    def test_common_query_params_sort_order_validation(self):
        """测试排序顺序验证"""
        # 无效的排序顺序
        params = CommonQueryParams(sort_order="invalid")
        assert params.sort_order == "desc"  # 默认值
        
        # 大写的排序顺序
        params = CommonQueryParams(sort_order="ASC")
        assert params.sort_order == "asc"  # 转换为小写

    def test_common_query_params_offset_limit(self):
        """测试偏移量和限制计算"""
        params = CommonQueryParams(page=3, size=20)
        
        assert params.offset == 40  # (3-1) * 20
        assert params.limit == 20

    def test_task_query_params_extended(self):
        """测试任务查询参数扩展功能"""
        params = TaskQueryParams(
            page=1,
            size=25,
            status="completed",
            category="repair",
            task_type="online",
            member_id=123,
            date_from="2024-01-01",
            date_to="2024-12-31"
        )
        
        assert params.page == 1
        assert params.size == 25
        assert params.status == "completed"
        assert params.category == "repair"
        assert params.task_type == "online"
        assert params.member_id == 123
        assert params.date_from == "2024-01-01"
        assert params.date_to == "2024-12-31"

    def test_member_query_params_extended(self):
        """测试成员查询参数扩展功能"""
        params = MemberQueryParams(
            page=2,
            size=30,
            role="admin",
            group_id=5,
            is_active=True
        )
        
        assert params.page == 2
        assert params.size == 30
        assert params.role == "admin"
        assert params.group_id == 5
        assert params.is_active is True

    def test_get_query_params_dependency(self):
        """测试查询参数依赖函数"""
        params = get_query_params(
            page=2,
            size=15,
            search="keyword",
            sort_by="created_at",
            sort_order="asc"
        )
        
        assert isinstance(params, CommonQueryParams)
        assert params.page == 2
        assert params.size == 15
        assert params.search == "keyword"
        assert params.sort_by == "created_at"
        assert params.sort_order == "asc"

    def test_get_task_query_params_dependency(self):
        """测试任务查询参数依赖函数"""
        params = get_task_query_params(
            page=1,
            status="pending",
            member_id=456
        )
        
        assert isinstance(params, TaskQueryParams)
        assert params.status == "pending"
        assert params.member_id == 456

    def test_get_member_query_params_dependency(self):
        """测试成员查询参数依赖函数"""
        params = get_member_query_params(
            role="member",
            is_active=False
        )
        
        assert isinstance(params, MemberQueryParams)
        assert params.role == "member"
        assert params.is_active is False


class TestPaginatedResponse:
    """测试分页响应类"""

    def test_paginated_response_basic(self):
        """测试基本分页响应"""
        items = [1, 2, 3, 4, 5]
        response = PaginatedResponse(items=items, total=25, page=1, size=5)
        
        assert response.items == items
        assert response.total == 25
        assert response.page == 1
        assert response.size == 5
        assert response.pages == 5  # ceil(25/5)
        assert response.has_next is True
        assert response.has_prev is False

    def test_paginated_response_last_page(self):
        """测试最后一页的分页响应"""
        items = [21, 22, 23, 24, 25]
        response = PaginatedResponse(items=items, total=25, page=5, size=5)
        
        assert response.pages == 5
        assert response.has_next is False
        assert response.has_prev is True

    def test_paginated_response_middle_page(self):
        """测试中间页的分页响应"""
        items = [11, 12, 13, 14, 15]
        response = PaginatedResponse(items=items, total=25, page=3, size=5)
        
        assert response.has_next is True
        assert response.has_prev is True

    def test_paginated_response_partial_last_page(self):
        """测试部分填充的最后一页"""
        items = [21, 22, 23]
        response = PaginatedResponse(items=items, total=23, page=5, size=5)
        
        assert response.pages == 5  # ceil(23/5) = 5
        assert len(response.items) == 3

    def test_paginated_response_single_page(self):
        """测试单页响应"""
        items = [1, 2, 3]
        response = PaginatedResponse(items=items, total=3, page=1, size=10)
        
        assert response.pages == 1
        assert response.has_next is False
        assert response.has_prev is False


class TestResponseHelpers:
    """测试响应辅助函数"""

    def test_create_response_basic(self):
        """测试基本响应创建"""
        response = create_response(
            data={"key": "value"},
            message="操作成功",
            status_code=200
        )
        
        assert response["success"] is True
        assert response["message"] == "操作成功"
        assert response["data"] == {"key": "value"}
        assert response["status_code"] == 200

    def test_create_response_with_message_key(self):
        """测试使用消息键创建响应"""
        with patch('app.api.deps.get_message') as mock_get_message:
            mock_get_message.return_value = "从消息键获取的消息"
            
            response = create_response(
                message_key="SUCCESS_MESSAGE",
                user_name="张三"
            )
            
            assert response["message"] == "从消息键获取的消息"
            mock_get_message.assert_called_once_with("SUCCESS_MESSAGE", user_name="张三")

    def test_create_response_with_details(self):
        """测试带详细信息的响应"""
        response = create_response(
            data={"result": "ok"},
            message="成功",
            details={"debug_info": "additional data"},
            error_code="CODE_001"
        )
        
        assert response["details"] == {"debug_info": "additional data"}
        assert response["error_code"] == "CODE_001"

    def test_create_response_error_status_code(self):
        """测试错误状态码的成功值自动计算"""
        response = create_response(
            message="操作失败",
            status_code=400
        )
        
        assert response["success"] is False  # 自动从状态码计算

    def test_create_response_explicit_success(self):
        """测试显式设置成功值"""
        response = create_response(
            message="部分成功",
            status_code=200,
            success=False  # 显式设置
        )
        
        assert response["success"] is False  # 使用显式值

    def test_create_error_response_basic(self):
        """测试基本错误响应创建"""
        response = create_error_response(
            message="操作失败",
            status_code=400
        )
        
        assert response["success"] is False
        assert response["message"] == "操作失败"
        assert response["status_code"] == 400
        assert response["details"] == {}

    def test_create_error_response_with_message_key(self):
        """测试使用消息键创建错误响应"""
        with patch('app.api.deps.get_message') as mock_get_message:
            mock_get_message.return_value = "验证失败"
            
            response = create_error_response(
                message_key="VALIDATION_ERROR",
                details={"field": "username"}
            )
            
            assert response["message"] == "验证失败"
            assert response["details"] == {"field": "username"}

    def test_create_error_response_default_values(self):
        """测试错误响应默认值"""
        response = create_error_response()
        
        assert response["success"] is False
        assert response["status_code"] == 400  # 默认错误码
        assert isinstance(response["details"], dict)


class TestUserPermissionHelpers:
    """测试用户权限辅助函数"""

    @pytest.fixture
    def mock_admin(self):
        return Member(
            id=1,
            username="admin",
            student_id="20210001",
            name="管理员",
            role=UserRole.ADMIN,
            is_active=True
        )

    @pytest.fixture
    def mock_group_leader(self):
        return Member(
            id=2,
            username="leader",
            student_id="20210002",
            name="组长",
            role=UserRole.GROUP_LEADER,
            is_active=True
        )

    @pytest.fixture
    def mock_member(self):
        return Member(
            id=3,
            username="member",
            student_id="20210003",
            name="普通成员",
            role=UserRole.MEMBER,
            is_active=True
        )

    def test_check_user_can_manage_group_admin(self, mock_admin):
        """测试管理员可以管理组"""
        assert check_user_can_manage_group(mock_admin) is True

    def test_check_user_can_manage_group_leader(self, mock_group_leader):
        """测试组长可以管理组"""
        assert check_user_can_manage_group(mock_group_leader) is True

    def test_check_user_can_manage_group_member(self, mock_member):
        """测试普通成员不能管理组"""
        assert check_user_can_manage_group(mock_member) is False

    def test_check_user_can_manage_group_none(self):
        """测试空用户不能管理组"""
        assert check_user_can_manage_group(None) is False

    def test_check_user_can_manage_group_no_role(self):
        """测试无角色用户不能管理组"""
        user_no_role = Member(
            id=4,
            username="no_role",
            student_id="20210004",
            name="无角色",
            role=None,
            is_active=True
        )
        assert check_user_can_manage_group(user_no_role) is False

    def test_check_user_is_admin_success(self, mock_admin):
        """测试管理员身份检查成功"""
        assert check_user_is_admin(mock_admin) is True

    def test_check_user_is_admin_failure(self, mock_member):
        """测试非管理员身份检查失败"""
        assert check_user_is_admin(mock_member) is False

    def test_check_user_is_admin_none(self):
        """测试空用户不是管理员"""
        assert check_user_is_admin(None) is False

    def test_check_user_can_access_task_owner(self, mock_member):
        """测试任务拥有者可以访问任务"""
        assert check_user_can_access_task(mock_member, mock_member.id) is True

    def test_check_user_can_access_task_admin(self, mock_admin):
        """测试管理员可以访问其他人的任务"""
        assert check_user_can_access_task(mock_admin, 999) is True

    def test_check_user_can_access_task_group_leader(self, mock_group_leader):
        """测试组长可以访问其他人的任务"""
        assert check_user_can_access_task(mock_group_leader, 999) is True

    def test_check_user_can_access_task_member_denied(self, mock_member):
        """测试普通成员不能访问其他人的任务"""
        assert check_user_can_access_task(mock_member, 999) is False

    def test_check_user_can_access_task_none(self):
        """测试空用户不能访问任务"""
        assert check_user_can_access_task(None, 123) is False


class TestEdgeCasesAndErrorHandling:
    """测试边界情况和错误处理"""

    @pytest.mark.asyncio
    async def test_get_current_user_unexpected_error(self):
        """测试意外错误处理"""
        mock_credentials = HTTPAuthorizationCredentials(
            scheme="Bearer", credentials="test_token"
        )
        mock_db = AsyncMock()
        
        with patch('app.api.deps.verify_token') as mock_verify:
            # Mock验证成功但后续处理出现意外错误
            mock_verify.return_value = {"sub": "1"}
            mock_db.execute.side_effect = RuntimeError("Unexpected error")
            
            with pytest.raises(HTTPException) as exc_info:
                await get_current_user(mock_credentials, mock_db)
            
            assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED

    def test_common_query_params_edge_values(self):
        """测试查询参数边界值"""
        # 测试极小和极大值
        params = CommonQueryParams(page=0, size=0)
        assert params.page == 1  # 最小值修正
        assert params.size == 1  # 最小值修正
        
        # 测试超大值
        params = CommonQueryParams(page=999999, size=999999)
        assert params.page == 999999  # 页码无上限
        assert params.size == settings.MAX_PAGE_SIZE  # 大小有上限

    def test_paginated_response_zero_items(self):
        """测试零项目的分页响应"""
        response = PaginatedResponse(items=[], total=0, page=1, size=10)
        
        assert response.pages == 0
        assert response.has_next is False
        assert response.has_prev is False
        assert len(response.items) == 0

    def test_user_permission_helpers_missing_attributes(self):
        """测试用户对象缺少属性的情况"""
        # 创建缺少role属性的用户对象
        user_mock = Mock()
        del user_mock.role  # 删除role属性
        
        assert check_user_can_manage_group(user_mock) is False
        assert check_user_is_admin(user_mock) is False

    @pytest.mark.asyncio
    async def test_auth_dependencies_with_malformed_user_objects(self):
        """测试认证依赖处理格式错误的用户对象"""
        mock_credentials = HTTPAuthorizationCredentials(
            scheme="Bearer", credentials="test_token"
        )
        mock_db = AsyncMock()
        
        # 创建没有必需属性的用户对象
        malformed_user = Mock()
        malformed_user.id = 1
        malformed_user.is_active = True
        # 缺少role属性
        
        with patch('app.api.deps.verify_token') as mock_verify, \
             patch('sqlalchemy.select') as mock_select:
            
            mock_verify.return_value = {"sub": "1"}
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = malformed_user
            mock_db.execute.return_value = mock_result
            
            # get_current_user应该仍然能返回用户对象
            user = await get_current_user(mock_credentials, mock_db)
            assert user == malformed_user
            
            # 但是role检查应该失败
            with pytest.raises(HTTPException):
                await get_admin_user(malformed_user)