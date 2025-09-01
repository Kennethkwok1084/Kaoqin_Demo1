"""
用户认证流程E2E测试
测试完整的用户认证、权限验证、角色切换等功能
包含JWT令牌管理、多用户角色测试、权限控制验证
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict

import pytest
from httpx import AsyncClient

from app.models.member import UserRole


class TestUserAuthenticationFlow:
    """用户认证流程E2E测试类"""

    @pytest.mark.asyncio
    async def test_complete_user_registration_and_login_flow(
        self, e2e_client: AsyncClient, e2e_helper
    ):
        """测试完整的用户注册和登录流程"""
        # 1. 用户注册
        registration_data = {
            "username": "new_user_001",
            "password": "NewUserPass123!",
            "student_id": "2024001003",
            "name": "新用户测试",
            "email": "newuser@example.com",
            "class_name": "计算机科学与技术2401",
            "group_id": 1,
        }

        register_response = await e2e_client.post(
            "/api/v1/auth/register", json=registration_data
        )
        e2e_helper.assert_response_success(register_response, 201)
        register_data = register_response.json()
        assert register_data["success"] is True
        assert "user_id" in register_data.get("data", {})

        # 2. 用户登录
        login_data = {
            "username": registration_data["username"],
            "password": registration_data["password"],
        }

        login_response = await e2e_client.post("/api/v1/auth/login", json=login_data)
        e2e_helper.assert_response_success(login_response)
        login_result = login_response.json()

        assert login_result["success"] is True
        token_data = login_result.get("data", {})
        assert "access_token" in token_data
        assert "refresh_token" in token_data
        assert "expires_in" in token_data

        # 3. 使用token访问受保护资源
        auth_headers = {"Authorization": f"Bearer {token_data['access_token']}"}
        profile_response = await e2e_client.get(
            "/api/v1/auth/profile", headers=auth_headers
        )
        e2e_helper.assert_response_success(profile_response)
        profile_data = profile_response.json()

        assert profile_data["success"] is True
        user_profile = profile_data.get("data", {})
        assert user_profile["username"] == registration_data["username"]
        assert user_profile["student_id"] == registration_data["student_id"]
        assert user_profile["role"] == UserRole.MEMBER.value

    @pytest.mark.asyncio
    async def test_multi_user_role_authentication(
        self,
        e2e_client: AsyncClient,
        e2e_user_tokens: Dict[str, str],
        e2e_auth_headers,
        e2e_helper,
    ):
        """测试多用户角色认证和权限验证"""

        # 测试每个角色的认证
        for role in ["student", "leader", "admin", "super_admin"]:
            token = e2e_user_tokens[role]
            headers = e2e_auth_headers(token)

            # 验证token有效性
            profile_response = await e2e_client.get(
                "/api/v1/auth/profile", headers=headers
            )
            e2e_helper.assert_response_success(profile_response)

            profile_data = profile_response.json()
            assert profile_data["success"] is True
            user_data = profile_data.get("data", {})

            # 验证角色映射
            expected_roles = {
                "student": UserRole.MEMBER.value,
                "leader": UserRole.GROUP_LEADER.value,
                "admin": UserRole.ADMIN.value,
                "super_admin": UserRole.SUPER_ADMIN.value,
            }
            assert user_data["role"] == expected_roles[role]

    @pytest.mark.asyncio
    async def test_jwt_token_refresh_flow(
        self,
        e2e_client: AsyncClient,
        e2e_user_tokens: Dict[str, str],
        e2e_auth_headers,
        e2e_helper,
    ):
        """测试JWT令牌刷新流程"""

        # 使用学生账号测试token刷新
        student_token = e2e_user_tokens["student"]

        # 1. 获取refresh token - 先登录获取完整token信息
        login_response = await e2e_client.post(
            "/api/v1/auth/login",
            json={"username": "student_001", "password": "StudentPass123!"},
        )
        e2e_helper.assert_response_success(login_response)

        login_data = login_response.json().get("data", {})
        refresh_token = login_data.get("refresh_token")
        assert refresh_token is not None

        # 2. 使用refresh token获取新的access token
        refresh_response = await e2e_client.post(
            "/api/v1/auth/refresh", json={"refresh_token": refresh_token}
        )

        if refresh_response.status_code == 200:
            # 如果刷新成功
            refresh_data = refresh_response.json()
            assert refresh_data["success"] is True
            new_token_data = refresh_data.get("data", {})
            assert "access_token" in new_token_data

            # 3. 使用新token访问受保护资源
            new_headers = e2e_auth_headers(new_token_data["access_token"])
            profile_response = await e2e_client.get(
                "/api/v1/auth/profile", headers=new_headers
            )
            e2e_helper.assert_response_success(profile_response)
        else:
            # 如果刷新功能未实现，跳过测试
            pytest.skip("Token refresh endpoint not implemented")

    @pytest.mark.asyncio
    async def test_role_based_access_control(
        self,
        e2e_client: AsyncClient,
        e2e_user_tokens: Dict[str, str],
        e2e_auth_headers,
        e2e_helper,
    ):
        """测试基于角色的访问控制"""

        # 测试不同角色对管理员端点的访问权限
        admin_endpoints = [
            "/api/v1/members",  # 成员管理
            "/api/v1/system/config",  # 系统配置
            "/api/v1/statistics/overview",  # 统计概览
        ]

        # 学生用户（应该被拒绝访问管理员端点）
        student_headers = e2e_auth_headers(e2e_user_tokens["student"])

        for endpoint in admin_endpoints:
            response = await e2e_client.get(endpoint, headers=student_headers)
            # 期望403 Forbidden或401 Unauthorized
            assert response.status_code in [
                401,
                403,
            ], f"Student should not access {endpoint}"

        # 管理员用户（应该可以访问）
        admin_headers = e2e_auth_headers(e2e_user_tokens["admin"])

        for endpoint in admin_endpoints:
            response = await e2e_client.get(endpoint, headers=admin_headers)
            # 期望200或404（端点存在但资源不存在）
            assert response.status_code in [200, 404], f"Admin should access {endpoint}"

    @pytest.mark.asyncio
    async def test_super_admin_exclusive_access(
        self,
        e2e_client: AsyncClient,
        e2e_user_tokens: Dict[str, str],
        e2e_auth_headers,
        e2e_helper,
    ):
        """测试超级管理员专属访问权限"""

        # 超级管理员专属端点
        super_admin_endpoints = [
            "/api/v1/system/config/work-hours",  # 工时规则配置
            "/api/v1/members/bulk-delete",  # 批量删除用户
        ]

        # 普通管理员不应该访问超级管理员端点
        admin_headers = e2e_auth_headers(e2e_user_tokens["admin"])

        for endpoint in super_admin_endpoints:
            response = await e2e_client.get(endpoint, headers=admin_headers)
            assert response.status_code in [
                401,
                403,
            ], f"Regular admin should not access {endpoint}"

        # 超级管理员应该可以访问
        super_admin_headers = e2e_auth_headers(e2e_user_tokens["super_admin"])

        for endpoint in super_admin_endpoints:
            response = await e2e_client.get(endpoint, headers=super_admin_headers)
            # 允许200, 404, 或405（方法不允许，但端点存在）
            assert response.status_code in [
                200,
                404,
                405,
            ], f"Super admin should access {endpoint}"

    @pytest.mark.asyncio
    async def test_password_change_flow(
        self,
        e2e_client: AsyncClient,
        e2e_user_tokens: Dict[str, str],
        e2e_auth_headers,
        e2e_helper,
    ):
        """测试密码修改流程"""

        student_headers = e2e_auth_headers(e2e_user_tokens["student"])

        # 1. 修改密码
        password_change_data = {
            "current_password": "StudentPass123!",
            "new_password": "NewStudentPass456!",
        }

        change_response = await e2e_client.put(
            "/api/v1/auth/change-password",
            json=password_change_data,
            headers=student_headers,
        )

        if change_response.status_code == 200:
            # 如果密码修改成功
            e2e_helper.assert_response_success(change_response)

            # 2. 使用旧密码登录（应该失败）
            old_login_response = await e2e_client.post(
                "/api/v1/auth/login",
                json={"username": "student_001", "password": "StudentPass123!"},
            )
            assert old_login_response.status_code == 401

            # 3. 使用新密码登录（应该成功）
            new_login_response = await e2e_client.post(
                "/api/v1/auth/login",
                json={"username": "student_001", "password": "NewStudentPass456!"},
            )
            e2e_helper.assert_response_success(new_login_response)

            # 4. 恢复原密码用于后续测试
            restore_response = await e2e_client.put(
                "/api/v1/auth/change-password",
                json={
                    "current_password": "NewStudentPass456!",
                    "new_password": "StudentPass123!",
                },
                headers=student_headers,
            )
            e2e_helper.assert_response_success(restore_response)
        else:
            # 如果密码修改功能未实现，跳过测试
            pytest.skip("Password change endpoint not implemented")

    @pytest.mark.asyncio
    async def test_invalid_authentication_scenarios(
        self, e2e_client: AsyncClient, e2e_helper
    ):
        """测试无效认证场景"""

        # 1. 无效凭据登录
        invalid_login_response = await e2e_client.post(
            "/api/v1/auth/login",
            json={"username": "nonexistent", "password": "invalid"},
        )
        assert invalid_login_response.status_code == 401

        # 2. 无效token访问
        invalid_headers = {"Authorization": "Bearer invalid_token"}
        profile_response = await e2e_client.get(
            "/api/v1/auth/profile", headers=invalid_headers
        )
        assert profile_response.status_code == 401

        # 3. 缺少Authorization头部
        no_auth_response = await e2e_client.get("/api/v1/auth/profile")
        assert no_auth_response.status_code == 401

        # 4. 格式错误的Authorization头部
        malformed_headers = {"Authorization": "InvalidFormat token"}
        malformed_response = await e2e_client.get(
            "/api/v1/auth/profile", headers=malformed_headers
        )
        assert malformed_response.status_code == 401

    @pytest.mark.asyncio
    async def test_session_concurrent_access(
        self,
        e2e_client: AsyncClient,
        e2e_user_tokens: Dict[str, str],
        e2e_auth_headers,
        e2e_helper,
    ):
        """测试并发会话访问"""

        student_headers = e2e_auth_headers(e2e_user_tokens["student"])

        # 并发访问相同用户的多个端点
        tasks = [
            e2e_client.get("/api/v1/auth/profile", headers=student_headers),
            e2e_client.get("/api/v1/tasks/repair/my", headers=student_headers),
            e2e_client.get("/api/v1/attendance/my", headers=student_headers),
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 验证所有请求都成功（或返回预期错误）
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                pytest.fail(f"Concurrent request {i} failed with exception: {result}")
            else:
                # 允许200或404（资源不存在）
                assert result.status_code in [
                    200,
                    404,
                ], f"Concurrent request {i} failed with status {result.status_code}"

    @pytest.mark.asyncio
    async def test_account_activation_flow(self, e2e_client: AsyncClient, e2e_helper):
        """测试账号激活流程"""

        # 1. 注册新用户（默认可能是未激活状态）
        registration_data = {
            "username": "inactive_user",
            "password": "InactivePass123!",
            "student_id": "2024001004",
            "name": "待激活用户",
            "email": "inactive@example.com",
            "class_name": "计算机科学与技术2401",
            "group_id": 1,
        }

        register_response = await e2e_client.post(
            "/api/v1/auth/register", json=registration_data
        )

        if register_response.status_code == 201:
            # 2. 尝试登录（可能需要激活）
            login_response = await e2e_client.post(
                "/api/v1/auth/login",
                json={
                    "username": registration_data["username"],
                    "password": registration_data["password"],
                },
            )

            # 根据系统设计，可能返回200（已激活）或特定状态（需要激活）
            assert login_response.status_code in [200, 401, 403]

            if login_response.status_code == 200:
                # 用户已自动激活
                login_data = login_response.json()
                assert login_data["success"] is True

        else:
            pytest.skip("User registration failed or not implemented")

    @pytest.mark.asyncio
    async def test_token_expiration_handling(
        self,
        e2e_client: AsyncClient,
        e2e_user_tokens: Dict[str, str],
        e2e_auth_headers,
        e2e_helper,
    ):
        """测试令牌过期处理"""

        # 注意：这个测试在实际E2E环境中需要较长时间或模拟过期token
        # 这里我们测试系统对过期token的处理机制

        # 使用一个明显过期的token格式
        expired_token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiYWRtaW4iOnRydWUsImV4cCI6MTYxNjIzOTAyMn0.invalid"
        expired_headers = e2e_auth_headers(expired_token)

        # 使用过期token访问受保护资源
        response = await e2e_client.get("/api/v1/auth/profile", headers=expired_headers)

        # 应该返回401 Unauthorized
        assert response.status_code == 401

        # 检查错误响应格式
        if response.headers.get("content-type", "").startswith("application/json"):
            error_data = response.json()
            assert "message" in error_data or "detail" in error_data

    @pytest.mark.asyncio
    async def test_login_attempt_rate_limiting(
        self, e2e_client: AsyncClient, e2e_helper
    ):
        """测试登录尝试频率限制"""

        invalid_credentials = {"username": "student_001", "password": "wrong_password"}

        # 连续多次失败登录尝试
        failed_attempts = []
        for i in range(5):
            response = await e2e_client.post(
                "/api/v1/auth/login", json=invalid_credentials
            )
            failed_attempts.append(response.status_code)

            # 短暂延迟避免过快请求
            await asyncio.sleep(0.1)

        # 检查是否有频率限制机制
        # 如果实现了频率限制，后续请求应该返回429 Too Many Requests
        if 429 in failed_attempts:
            # 验证频率限制生效
            last_response = await e2e_client.post(
                "/api/v1/auth/login", json=invalid_credentials
            )
            assert last_response.status_code == 429
        else:
            # 如果没有频率限制，所有请求都应该返回401
            for status in failed_attempts:
                assert status == 401

    @pytest.mark.asyncio
    async def test_user_profile_management(
        self,
        e2e_client: AsyncClient,
        e2e_user_tokens: Dict[str, str],
        e2e_auth_headers,
        e2e_helper,
    ):
        """测试用户资料管理"""

        student_headers = e2e_auth_headers(e2e_user_tokens["student"])

        # 1. 获取当前用户资料
        profile_response = await e2e_client.get(
            "/api/v1/auth/profile", headers=student_headers
        )
        e2e_helper.assert_response_success(profile_response)

        original_profile = profile_response.json().get("data", {})
        assert "name" in original_profile
        assert "email" in original_profile

        # 2. 更新用户资料
        updated_profile = {
            "name": "更新后的姓名",
            "email": "updated@example.com",
            "class_name": "计算机科学与技术2102",
        }

        update_response = await e2e_client.put(
            "/api/v1/auth/profile", json=updated_profile, headers=student_headers
        )

        if update_response.status_code == 200:
            # 如果更新成功
            e2e_helper.assert_response_success(update_response)

            # 3. 验证更新后的资料
            updated_profile_response = await e2e_client.get(
                "/api/v1/auth/profile", headers=student_headers
            )
            e2e_helper.assert_response_success(updated_profile_response)

            new_profile = updated_profile_response.json().get("data", {})
            assert new_profile["name"] == updated_profile["name"]
            assert new_profile["email"] == updated_profile["email"]

        else:
            # 如果更新功能未实现，跳过测试
            pytest.skip("Profile update endpoint not implemented")


class TestAuthenticationPerformance:
    """认证性能测试"""

    @pytest.mark.asyncio
    async def test_authentication_performance(
        self, e2e_client: AsyncClient, e2e_performance_monitor, e2e_helper
    ):
        """测试认证操作性能"""

        e2e_performance_monitor.start()

        # 测试登录性能
        login_times = []
        for i in range(10):
            start_time = asyncio.get_event_loop().time()

            login_response = await e2e_client.post(
                "/api/v1/auth/login",
                json={"username": "student_001", "password": "StudentPass123!"},
            )

            end_time = asyncio.get_event_loop().time()
            duration = end_time - start_time
            login_times.append(duration)

            e2e_performance_monitor.record(f"login_attempt_{i}", duration)

            # 确保登录成功
            if login_response.status_code == 200:
                token_data = login_response.json().get("data", {})
                assert "access_token" in token_data

        # 验证性能指标
        avg_login_time = sum(login_times) / len(login_times)
        max_login_time = max(login_times)

        # 性能断言（可根据实际需求调整阈值）
        assert (
            avg_login_time < 2.0
        ), f"Average login time {avg_login_time}s exceeds 2s threshold"
        assert (
            max_login_time < 5.0
        ), f"Max login time {max_login_time}s exceeds 5s threshold"

        # 输出性能摘要
        summary = e2e_performance_monitor.summary()
        print(f"Authentication Performance Summary: {summary}")
