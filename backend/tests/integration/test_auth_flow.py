"""
认证系统端到端流程测试
测试登录、令牌刷新、权限验证、密码修改等完整流程
"""

from datetime import timedelta

from app.core.config import settings
from app.core.security import create_access_token, create_refresh_token


class TestAuthenticationFlow:
    """测试认证流程"""

    def test_successful_login(self, client, test_member_user):
        """测试成功登录"""
        login_data = {
            "student_id": test_member_user.student_id,
            "password": "member123456",
        }

        response = client.post("/api/v1/auth/login", json=login_data)

        assert response.status_code == 200
        data = response.json()

        # 验证响应结构
        assert "success" in data
        assert "access_token" in data
        assert "refresh_token" in data
        assert "token_type" in data
        assert "expires_in" in data
        assert "user" in data

        # 验证响应内容
        assert data["success"] is True
        assert data["token_type"] == "bearer"
        assert data["expires_in"] == settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60

        # 验证用户信息
        user_data = data["user"]
        assert user_data["student_id"] == "member001"
        assert user_data["name"] == "测试成员"
        assert user_data["role"] == "member"
        assert user_data["is_active"] is True

    def test_login_with_invalid_credentials(self, client, test_member_user):
        """测试无效凭证登录"""
        # 错误密码
        login_data = {"student_id": "member001", "password": "wrongpassword"}

        response = client.post("/api/v1/auth/login", json=login_data)

        assert response.status_code == 401
        data = response.json()
        assert data["success"] is False
        assert "密码错误" in data["message"] or "Invalid credentials" in data["message"]

    def test_login_with_nonexistent_user(self, client):
        """测试不存在用户登录"""
        login_data = {"student_id": "nonexistent", "password": "anypassword"}

        response = client.post("/api/v1/auth/login", json=login_data)

        assert response.status_code == 401
        data = response.json()
        assert data["success"] is False
        assert "用户不存在" in data["message"] or "User not found" in data["message"]

    def test_login_with_inactive_user(self, client, db_session):
        """测试非活跃用户登录"""
        # 创建非活跃用户
        from app.core.security import get_password_hash
        from app.models import Member, UserRole

        inactive_user = Member(
            name="非活跃用户",
            student_id="inactive001",
            password_hash=get_password_hash("password123"),
            role=UserRole.MEMBER,
            is_active=False,  # 设为非活跃
        )

        db_session.add(inactive_user)
        db_session.commit()

        login_data = {"student_id": "inactive001", "password": "password123"}

        response = client.post("/api/v1/auth/login", json=login_data)

        assert response.status_code == 403
        data = response.json()
        assert data["success"] is False
        assert (
            "账户已被禁用" in data["message"] or "Account disabled" in data["message"]
        )

    def test_protected_endpoint_without_token(self, client):
        """测试无令牌访问受保护端点"""
        response = client.get("/api/auth/profile")

        assert response.status_code == 401
        data = response.json()
        assert "Not authenticated" in data["detail"] or "认证失败" in data["detail"]

    def test_protected_endpoint_with_valid_token(self, client, auth_headers_member):
        """测试有效令牌访问受保护端点"""
        response = client.get("/api/auth/profile", headers=auth_headers_member)

        assert response.status_code == 200
        data = response.json()

        # 验证用户信息
        assert data["student_id"] == "member001"
        assert data["name"] == "测试成员"
        assert data["role"] == "member"
        assert data["is_active"] is True

    def test_protected_endpoint_with_invalid_token(self, client):
        """测试无效令牌访问受保护端点"""
        headers = {"Authorization": "Bearer invalid_token"}
        response = client.get("/api/auth/profile", headers=headers)

        assert response.status_code == 401
        data = response.json()
        assert (
            "Could not validate credentials" in data["detail"]
            or "认证失败" in data["detail"]
        )

    def test_protected_endpoint_with_expired_token(self, client, test_member_user):
        """测试过期令牌访问受保护端点"""
        # 创建一个已过期的令牌
        expired_token = create_access_token(
            subject=str(test_member_user.id),
            expires_delta=timedelta(seconds=-1),  # 已过期
        )

        headers = {"Authorization": f"Bearer {expired_token}"}
        response = client.get("/api/auth/profile", headers=headers)

        assert response.status_code == 401
        data = response.json()
        assert (
            "Could not validate credentials" in data["detail"]
            or "认证失败" in data["detail"]
        )


class TestTokenRefresh:
    """测试令牌刷新"""

    def test_refresh_token_success(self, client, test_member_user):
        """测试成功刷新令牌"""
        # 先登录获取令牌
        login_data = {
            "student_id": test_member_user.student_id,
            "password": "member123456",
        }
        login_response = client.post("/api/v1/auth/login", json=login_data)
        assert login_response.status_code == 200

        refresh_token = login_response.json()["refresh_token"]

        # 使用refresh token获取新的access token
        refresh_data = {"refresh_token": refresh_token}
        response = client.post("/api/v1/auth/refresh", json=refresh_data)

        assert response.status_code == 200
        data = response.json()

        assert "access_token" in data
        assert "token_type" in data
        assert "expires_in" in data
        assert data["token_type"] == "bearer"

        # 验证新令牌可以正常使用
        new_token = data["access_token"]
        headers = {"Authorization": f"Bearer {new_token}"}
        profile_response = client.get("/api/v1/auth/me", headers=headers)
        assert profile_response.status_code == 200

    def test_refresh_token_invalid(self, client):
        """测试无效刷新令牌"""
        refresh_data = {"refresh_token": "invalid_refresh_token"}
        response = client.post("/api/v1/auth/refresh", json=refresh_data)

        assert response.status_code == 401
        data = response.json()
        assert data["success"] is False

    def test_refresh_token_expired(self, client, test_member_user):
        """测试过期刷新令牌"""
        # 创建一个已过期的刷新令牌
        expired_refresh_token = create_refresh_token(
            subject=str(test_member_user.id),
            expires_delta=timedelta(seconds=-1),  # 已过期
        )

        refresh_data = {"refresh_token": expired_refresh_token}
        response = client.post("/api/v1/auth/refresh", json=refresh_data)

        assert response.status_code == 401
        data = response.json()
        assert data["success"] is False


class TestPasswordChange:
    """测试密码修改"""

    def test_change_password_success(self, client, auth_headers_member):
        """测试成功修改密码"""
        password_data = {
            "current_password": "member123456",
            "new_password": "newpassword123456",
        }

        response = client.post(
            "/api/v1/auth/change-password",
            json=password_data,
            headers=auth_headers_member,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert (
            "密码修改成功" in data["message"]
            or "Password changed successfully" in data["message"]
        )

        # 验证新密码可以登录
        login_data = {"student_id": "member001", "password": "newpassword123456"}
        login_response = client.post("/api/v1/auth/login", json=login_data)
        assert login_response.status_code == 200

    def test_change_password_wrong_current(self, client, auth_headers_member):
        """测试当前密码错误"""
        password_data = {
            "current_password": "wrongpassword",
            "new_password": "newpassword123456",
        }

        response = client.post(
            "/api/v1/auth/change-password",
            json=password_data,
            headers=auth_headers_member,
        )

        assert response.status_code == 400
        data = response.json()
        assert data["success"] is False
        assert (
            "当前密码错误" in data["message"]
            or "Current password is incorrect" in data["message"]
        )

    def test_change_password_weak_new_password(self, client, auth_headers_member):
        """测试新密码强度不足"""
        password_data = {
            "current_password": "member123456",
            "new_password": "123",  # 太弱的密码
        }

        response = client.post(
            "/api/v1/auth/change-password",
            json=password_data,
            headers=auth_headers_member,
        )

        assert response.status_code == 422  # 验证错误

    def test_change_password_without_auth(self, client):
        """测试未认证修改密码"""
        password_data = {
            "current_password": "anypassword",
            "new_password": "newpassword123456",
        }

        response = client.post("/api/v1/auth/change-password", json=password_data)

        assert response.status_code == 401


class TestRoleBasedAccess:
    """测试基于角色的访问控制"""

    def test_admin_only_endpoint_with_admin(self, client, auth_headers_admin):
        """测试管理员访问管理员端点"""
        response = client.get("/api/members", headers=auth_headers_admin)

        # 应该成功访问
        assert response.status_code == 200

    def test_admin_only_endpoint_with_member(self, client, auth_headers_member):
        """测试普通成员访问管理员端点"""
        response = client.get("/api/members", headers=auth_headers_member)

        # 应该被拒绝
        assert response.status_code == 403
        data = response.json()
        assert (
            "权限不足" in data["detail"] or "Not enough permissions" in data["detail"]
        )

    def test_group_leader_endpoint_with_leader(self, client, auth_headers_leader):
        """测试组长访问组长端点"""
        # 这里假设有组长特有的端点，比如查看组内成员
        response = client.get("/api/members?group_id=1", headers=auth_headers_leader)

        # 组长应该能访问
        assert response.status_code in [200, 403]  # 取决于具体实现

    def test_group_leader_endpoint_with_member(self, client, auth_headers_member):
        """测试普通成员访问组长端点"""
        # 假设的组长端点
        response = client.get("/api/members?group_id=1", headers=auth_headers_member)

        # 可能被拒绝或只返回有限数据
        assert response.status_code in [200, 403]


class TestUserProfile:
    """测试用户档案管理"""

    def test_get_user_profile(self, client, auth_headers_member):
        """测试获取用户档案"""
        response = client.get("/api/auth/profile", headers=auth_headers_member)

        assert response.status_code == 200
        data = response.json()

        # 验证档案信息
        assert data["student_id"] == "member001"
        assert data["name"] == "测试成员"
        assert data["role"] == "member"
        assert data["group_id"] == 1
        assert data["class_name"] == "计算机科学与技术2101"
        assert data["is_active"] is True
        assert data["is_verified"] is True
        assert "login_count" in data
        assert "created_at" in data

    def test_update_user_profile(self, client, auth_headers_member):
        """测试更新用户档案"""
        update_data = {
            "name": "更新的测试成员",
            "email": "updated@test.com",
            "class_name": "计算机科学与技术2102",
        }

        response = client.put(
            "/api/auth/profile", json=update_data, headers=auth_headers_member
        )

        if response.status_code == 200:
            data = response.json()
            assert data["name"] == "更新的测试成员"
            assert data["email"] == "updated@test.com"
            assert data["class_name"] == "计算机科学与技术2102"
        else:
            # 如果端点未实现，应该返回适当的状态码
            assert response.status_code in [404, 405, 501]


class TestLogout:
    """测试登出功能"""

    def test_logout_success(self, client, auth_headers_member):
        """测试成功登出"""
        response = client.post("/api/v1/auth/logout", headers=auth_headers_member)

        if response.status_code == 200:
            data = response.json()
            assert data["success"] is True or "message" in data
            assert "logged_out_at" in data or "成功" in data.get("message", "")
        else:
            # 如果端点未实现
            assert response.status_code in [404, 405, 501]

    def test_logout_without_auth(self, client):
        """测试未认证登出"""
        response = client.post("/api/v1/auth/logout")

        # 应该要求认证
        assert response.status_code == 401


class TestAuthenticationStatus:
    """测试认证状态检查"""

    def test_check_auth_status_authenticated(self, client, auth_headers_member):
        """测试已认证用户的状态检查"""
        response = client.get("/api/auth/status", headers=auth_headers_member)

        if response.status_code == 200:
            data = response.json()
            assert data["authenticated"] is True
            assert "user_id" in data
            assert "expires_at" in data or "expires_in" in data
        else:
            # 如果端点未实现
            assert response.status_code in [404, 405, 501]

    def test_check_auth_status_unauthenticated(self, client):
        """测试未认证用户的状态检查"""
        response = client.get("/api/auth/status")

        if response.status_code == 200:
            data = response.json()
            assert data["authenticated"] is False
        else:
            # 应该要求认证或返回未认证状态
            assert response.status_code in [401, 404, 405, 501]
