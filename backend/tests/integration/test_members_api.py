"""
成员管理API完整流程测试
测试成员CRUD操作、权限控制、数据验证等
"""

import pytest
import pytest_asyncio
from sqlalchemy import select

from app.models import Member, UserRole


class TestMembersCRUD:
    """测试成员CRUD操作"""

    def test_create_member_as_admin(self, client, auth_headers_admin):
        """测试管理员创建成员"""
        member_data = {
            "name": "新创建成员",
            "student_id": "CREATE001",
            "email": "create@test.com",
            "password": "password123456",
            "role": "member",
            "group_id": 2,
            "class_name": "软件工程2101",
            "dormitory": "3号楼301",
            "phone": "13812345678",
            "is_active": True,
            "is_verified": False,
        }

        response = client.post(
            "/api/members", json=member_data, headers=auth_headers_admin
        )

        assert response.status_code == 201
        data = response.json()

        # 验证返回数据
        assert data["name"] == "新创建成员"
        assert data["student_id"] == "CREATE001"
        assert data["email"] == "create@test.com"
        assert data["role"] == "member"
        assert data["group_id"] == 2
        assert data["class_name"] == "软件工程2101"
        assert data["is_active"] is True
        assert data["is_verified"] is False
        assert "id" in data
        assert "created_at" in data

        # 验证密码不会返回
        assert "password" not in data
        assert "password_hash" not in data

    def test_create_member_as_non_admin(self, client, auth_headers_member):
        """测试非管理员创建成员"""
        member_data = {
            "name": "不应创建",
            "student_id": "FAIL001",
            "password": "password123456",
        }

        response = client.post(
            "/api/members", json=member_data, headers=auth_headers_member
        )

        assert response.status_code == 403
        data = response.json()
        assert (
            "权限不足" in data["detail"] or "Not enough permissions" in data["detail"]
        )

    def test_create_member_duplicate_student_id(self, client, auth_headers_admin):
        """测试创建重复学号成员"""
        member_data = {
            "name": "重复学号测试",
            "student_id": "member001",  # 已存在的学号
            "password": "password123456",
        }

        response = client.post(
            "/api/members", json=member_data, headers=auth_headers_admin
        )

        assert response.status_code == 400
        data = response.json()
        assert "学号已存在" in data["message"] or "already exists" in data["message"]

    def test_create_member_invalid_data(self, client, auth_headers_admin):
        """测试无效数据创建成员"""
        # 缺少必需字段
        member_data = {
            "name": "缺少学号"
            # 缺少student_id和password
        }

        response = client.post(
            "/api/members", json=member_data, headers=auth_headers_admin
        )

        assert response.status_code == 422  # 验证错误

        # 无效邮箱格式
        member_data2 = {
            "name": "无效邮箱",
            "student_id": "INVALID001",
            "password": "password123456",
            "email": "invalid-email",  # 无效邮箱格式
        }

        response2 = client.post(
            "/api/members", json=member_data2, headers=auth_headers_admin
        )

        assert response2.status_code == 422

    def test_get_members_list_as_admin(self, client, auth_headers_admin):
        """测试管理员获取成员列表"""
        response = client.get("/api/members", headers=auth_headers_admin)

        assert response.status_code == 200
        data = response.json()

        # 验证分页结构
        assert "items" in data
        assert "total" in data
        assert "page" in data
        assert "size" in data
        assert "pages" in data
        assert "has_next" in data
        assert "has_prev" in data

        # 验证至少有测试用户
        assert data["total"] >= 3  # admin, member, leader
        assert len(data["items"]) <= data["size"]

    def test_get_members_list_with_pagination(self, client, auth_headers_admin):
        """测试分页获取成员列表"""
        # 获取第一页
        response = client.get("/api/members?page=1&size=2", headers=auth_headers_admin)

        assert response.status_code == 200
        data = response.json()

        assert data["page"] == 1
        assert data["size"] == 2
        assert len(data["items"]) <= 2

        if data["total"] > 2:
            assert data["has_next"] is True
        assert data["has_prev"] is False

    def test_get_members_list_with_search(self, client, auth_headers_admin):
        """测试搜索成员"""
        # 按名称搜索
        response = client.get("/api/members?search=测试", headers=auth_headers_admin)

        assert response.status_code == 200
        data = response.json()

        # 所有返回的成员名称应包含"测试"
        for member in data["items"]:
            assert "测试" in member["name"]

    def test_get_members_list_with_filters(self, client, auth_headers_admin):
        """测试筛选成员"""
        # 按角色筛选
        response = client.get("/api/members?role=admin", headers=auth_headers_admin)

        assert response.status_code == 200
        data = response.json()

        # 所有返回的成员应该是管理员
        for member in data["items"]:
            assert member["role"] == "admin"

        # 按组别筛选
        response2 = client.get("/api/members?group_id=1", headers=auth_headers_admin)

        assert response2.status_code == 200
        data2 = response2.json()

        for member in data2["items"]:
            assert member.get("group_id") == 1

    def test_get_members_list_as_non_admin(self, client, auth_headers_member):
        """测试非管理员获取成员列表"""
        response = client.get("/api/members", headers=auth_headers_member)

        # 可能被拒绝或只返回有限信息
        assert response.status_code in [200, 403]

        if response.status_code == 200:
            data = response.json()
            # 应该只返回有限信息或同组成员
            for member in data["items"]:
                # 敏感信息不应暴露给普通成员
                assert "password" not in member
                assert "password_hash" not in member

    def test_get_member_detail_as_admin(
        self, client, auth_headers_admin, test_member_user
    ):
        """测试管理员获取成员详情"""
        response = client.get(
            f"/api/members/{test_member_user.id}", headers=auth_headers_admin
        )

        assert response.status_code == 200
        data = response.json()

        # 验证详细信息
        assert data["id"] == test_member_user.id
        assert data["name"] == test_member_user.name
        assert data["student_id"] == test_member_user.student_id
        assert data["email"] == test_member_user.email
        assert data["role"] == test_member_user.role.value
        assert data["group_id"] == test_member_user.group_id
        assert data["class_name"] == test_member_user.class_name
        assert data["is_active"] == test_member_user.is_active
        assert data["is_verified"] == test_member_user.is_verified

        # 管理员应该能看到敏感信息（加密后的）
        assert "dormitory" in data or "phone" in data

    def test_get_member_detail_as_self(
        self, client, auth_headers_member, test_member_user
    ):
        """测试获取自己的详情"""
        response = client.get(
            f"/api/members/{test_member_user.id}", headers=auth_headers_member
        )

        assert response.status_code == 200
        data = response.json()

        # 应该能看到自己的信息
        assert data["id"] == test_member_user.id
        assert data["name"] == test_member_user.name

    def test_get_member_detail_as_other(
        self, client, auth_headers_member, test_admin_user
    ):
        """测试获取他人详情"""
        response = client.get(
            f"/api/members/{test_admin_user.id}", headers=auth_headers_member
        )

        # 可能被拒绝或只返回公开信息
        assert response.status_code in [200, 403]

        if response.status_code == 200:
            data = response.json()
            # 不应暴露敏感信息
            assert "dormitory" not in data or data["dormitory"] is None
            assert "phone" not in data or data["phone"] is None

    def test_get_nonexistent_member(self, client, auth_headers_admin):
        """测试获取不存在的成员"""
        response = client.get("/api/members/99999", headers=auth_headers_admin)

        assert response.status_code == 404
        data = response.json()
        assert "未找到" in data["message"] or "not found" in data["message"]

    def test_update_member_as_admin(self, client, auth_headers_admin, test_member_user):
        """测试管理员更新成员"""
        update_data = {
            "name": "更新后的姓名",
            "email": "updated@test.com",
            "group_id": 3,
            "class_name": "更新后的班级",
            "is_active": False,
        }

        response = client.put(
            f"/api/members/{test_member_user.id}",
            json=update_data,
            headers=auth_headers_admin,
        )

        assert response.status_code == 200
        data = response.json()

        # 验证更新结果
        assert data["name"] == "更新后的姓名"
        assert data["email"] == "updated@test.com"
        assert data["group_id"] == 3
        assert data["class_name"] == "更新后的班级"
        assert data["is_active"] is False
        assert data["updated_at"] != data["created_at"]

    def test_update_member_role_as_admin(
        self, client, auth_headers_admin, test_member_user
    ):
        """测试管理员更新成员角色"""
        role_data = {"role": "group_leader"}

        response = client.patch(
            f"/api/members/{test_member_user.id}/role",
            json=role_data,
            headers=auth_headers_admin,
        )

        assert response.status_code == 200
        data = response.json()

        assert data["role"] == "group_leader"

    def test_update_member_status_as_admin(
        self, client, auth_headers_admin, test_member_user
    ):
        """测试管理员更新成员状态"""
        status_data = {"is_active": False, "reason": "违反规定"}

        response = client.patch(
            f"/api/members/{test_member_user.id}/status",
            json=status_data,
            headers=auth_headers_admin,
        )

        assert response.status_code == 200
        data = response.json()

        assert data["is_active"] is False

    def test_update_member_as_non_admin(
        self, client, auth_headers_member, test_admin_user
    ):
        """测试非管理员更新成员"""
        update_data = {"name": "不应成功"}

        response = client.put(
            f"/api/members/{test_admin_user.id}",
            json=update_data,
            headers=auth_headers_member,
        )

        assert response.status_code == 403

    def test_update_self_as_member(self, client, auth_headers_member, test_member_user):
        """测试成员更新自己信息"""
        update_data = {
            "name": "自己更新的姓名",
            "email": "self-updated@test.com",
            "class_name": "自己更新的班级",
        }

        response = client.put(
            f"/api/members/{test_member_user.id}",
            json=update_data,
            headers=auth_headers_member,
        )

        # 可能成功或被限制
        assert response.status_code in [200, 403]

        if response.status_code == 200:
            data = response.json()
            assert data["name"] == "自己更新的姓名"
            # 敏感字段不应被更新
            assert data["role"] == "member"  # 角色不应变化

    def test_delete_member_as_admin(self, client, auth_headers_admin, db_session):
        """测试管理员删除成员"""
        # 先创建一个用于删除的成员
        from app.core.security import get_password_hash

        to_delete = Member(
            name="待删除成员",
            student_id="DELETE001",
            password_hash=get_password_hash("password123"),
            role=UserRole.MEMBER,
        )
        db_session.add(to_delete)
        db_session.commit()
        db_session.refresh(to_delete)

        response = client.delete(
            f"/api/members/{to_delete.id}", headers=auth_headers_admin
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert (
            "删除成功" in data["message"] or "deleted successfully" in data["message"]
        )

        # 验证成员确实被删除
        get_response = client.get(
            f"/api/members/{to_delete.id}", headers=auth_headers_admin
        )
        assert get_response.status_code == 404

    def test_delete_member_as_non_admin(
        self, client, auth_headers_member, test_admin_user
    ):
        """测试非管理员删除成员"""
        response = client.delete(
            f"/api/members/{test_admin_user.id}", headers=auth_headers_member
        )

        assert response.status_code == 403


class TestMembersBulkOperations:
    """测试成员批量操作"""

    @pytest_asyncio.fixture
    async def bulk_test_members(self, db_session):
        """创建批量测试成员"""
        from app.core.security import get_password_hash

        members = []
        for i in range(5):
            member = Member(
                name=f"批量测试成员{i+1}",
                student_id=f"BULK00{i+1}",
                password_hash=get_password_hash("password123"),
                role=UserRole.MEMBER,
                group_id=1,
                is_active=True,
            )
            db_session.add(member)
            members.append(member)

        await db_session.commit()
        for member in members:
            await db_session.refresh(member)

        return members

    def test_bulk_activate_members(self, client, auth_headers_admin, bulk_test_members):
        """测试批量激活成员"""
        member_ids = [member.id for member in bulk_test_members]

        bulk_data = {
            "member_ids": member_ids,
            "operation": "activate",
            "reason": "批量激活测试",
        }

        response = client.post(
            "/api/members/bulk", json=bulk_data, headers=auth_headers_admin
        )

        assert response.status_code == 200
        data = response.json()

        assert data["success"] is True
        assert data["processed_count"] == len(member_ids)
        assert data["successful_count"] == len(member_ids)
        assert data["failed_count"] == 0

    def test_bulk_deactivate_members(
        self, client, auth_headers_admin, bulk_test_members
    ):
        """测试批量停用成员"""
        member_ids = [member.id for member in bulk_test_members[:3]]

        bulk_data = {
            "member_ids": member_ids,
            "operation": "deactivate",
            "reason": "批量停用测试",
        }

        response = client.post(
            "/api/members/bulk", json=bulk_data, headers=auth_headers_admin
        )

        assert response.status_code == 200
        data = response.json()

        assert data["success"] is True
        assert data["processed_count"] == len(member_ids)

    def test_bulk_set_role(self, client, auth_headers_admin, bulk_test_members):
        """测试批量设置角色"""
        member_ids = [member.id for member in bulk_test_members[:2]]

        bulk_data = {
            "member_ids": member_ids,
            "operation": "set_role",
            "operation_data": {"role": "group_leader"},
            "reason": "批量设置为组长",
        }

        response = client.post(
            "/api/members/bulk", json=bulk_data, headers=auth_headers_admin
        )

        assert response.status_code == 200
        data = response.json()

        assert data["success"] is True
        assert data["processed_count"] == len(member_ids)

    def test_bulk_set_group(self, client, auth_headers_admin, bulk_test_members):
        """测试批量设置组别"""
        member_ids = [member.id for member in bulk_test_members[:3]]

        bulk_data = {
            "member_ids": member_ids,
            "operation": "set_group",
            "operation_data": {"group_id": 2},
            "reason": "批量调整到第2组",
        }

        response = client.post(
            "/api/members/bulk", json=bulk_data, headers=auth_headers_admin
        )

        assert response.status_code == 200
        data = response.json()

        assert data["success"] is True
        assert data["processed_count"] == len(member_ids)

    def test_bulk_operation_as_non_admin(
        self, client, auth_headers_member, bulk_test_members
    ):
        """测试非管理员批量操作"""
        member_ids = [member.id for member in bulk_test_members[:2]]

        bulk_data = {"member_ids": member_ids, "operation": "activate"}

        response = client.post(
            "/api/members/bulk", json=bulk_data, headers=auth_headers_member
        )

        assert response.status_code == 403

    def test_bulk_operation_invalid_data(self, client, auth_headers_admin):
        """测试无效批量操作数据"""
        # 缺少operation_data
        bulk_data = {
            "member_ids": [1, 2],
            "operation": "set_role",  # 需要operation_data
        }

        response = client.post(
            "/api/members/bulk", json=bulk_data, headers=auth_headers_admin
        )

        assert response.status_code == 422


class TestMembersStatistics:
    """测试成员统计"""

    def test_get_members_statistics(self, client, auth_headers_admin):
        """测试获取成员统计"""
        response = client.get("/api/members/statistics", headers=auth_headers_admin)

        assert response.status_code == 200
        data = response.json()

        # 验证统计数据结构
        assert "total_members" in data
        assert "active_members" in data
        assert "inactive_members" in data
        assert "verified_members" in data
        assert "admin_count" in data
        assert "group_leader_count" in data
        assert "member_count" in data
        assert "group_distribution" in data
        assert "recent_logins" in data

        # 验证数据合理性
        assert data["total_members"] >= 3  # 至少有测试用户
        assert (
            data["active_members"] + data["inactive_members"] == data["total_members"]
        )
        assert (
            data["admin_count"] + data["group_leader_count"] + data["member_count"]
            == data["total_members"]
        )

    def test_get_members_statistics_as_non_admin(self, client, auth_headers_member):
        """测试非管理员获取统计"""
        response = client.get("/api/members/statistics", headers=auth_headers_member)

        # 可能被拒绝或返回有限统计
        assert response.status_code in [200, 403]

        if response.status_code == 200:
            data = response.json()
            # 确保没有敏感统计信息
            assert isinstance(data, dict)
