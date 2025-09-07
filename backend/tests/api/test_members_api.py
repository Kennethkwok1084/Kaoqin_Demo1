"""
成员管理API测试用例
测试所有成员相关的API端点
"""

import pytest
from datetime import datetime, date
from unittest.mock import AsyncMock, MagicMock, patch, mock_open
from httpx import AsyncClient
import io

from app.models.member import Member, UserRole
from app.models.task import RepairTask, TaskStatus
from app.main import app


class TestMembersAPIBasic:
    """测试成员API基础功能"""

    @pytest.fixture
    async def client(self):
        """创建测试客户端"""
        async with AsyncClient(app=app, base_url="http://testserver") as ac:
            yield ac

    @pytest.fixture
    def regular_user(self):
        """创建普通用户"""
        return Member(
            id=1,
            username="regular_user",
            student_id="20210001",
            name="普通用户",
            email="regular@test.com",
            role=UserRole.MEMBER,
            is_active=True
        )

    @pytest.fixture
    def group_leader_user(self):
        """创建组长用户"""
        return Member(
            id=2,
            username="group_leader",
            student_id="20210002",
            name="组长",
            email="leader@test.com",
            role=UserRole.GROUP_LEADER,
            is_active=True
        )

    @pytest.fixture
    def admin_user(self):
        """创建管理员用户"""
        return Member(
            id=3,
            username="admin_user",
            student_id="20210003",
            name="管理员",
            email="admin@test.com",
            role=UserRole.ADMIN,
            is_active=True
        )

    @pytest.fixture
    def sample_members(self):
        """创建示例成员列表"""
        return [
            Member(
                id=1,
                username="user1",
                student_id="20210001",
                name="用户1",
                email="user1@test.com",
                role=UserRole.MEMBER,
                is_active=True
            ),
            Member(
                id=2,
                username="user2", 
                student_id="20210002",
                name="用户2",
                email="user2@test.com",
                role=UserRole.MEMBER,
                is_active=True
            )
        ]


class TestGetMembersAPI(TestMembersAPIBasic):
    """测试获取成员列表API"""

    @pytest.mark.asyncio
    async def test_get_members_basic(self, client, admin_user, sample_members):
        """测试获取成员列表基础功能"""
        with patch('app.api.deps.get_db') as mock_get_db, \
             patch('app.api.deps.get_current_active_admin') as mock_get_admin:
            
            mock_db = AsyncMock()
            mock_get_db.return_value = mock_db
            mock_get_admin.return_value = admin_user
            
            # Mock查询结果
            mock_result = MagicMock()
            mock_result.scalars.return_value.all.return_value = sample_members
            mock_db.execute.return_value = mock_result
            
            # Mock计数查询
            mock_count_result = MagicMock()
            mock_count_result.scalar.return_value = len(sample_members)
            
            response = await client.get(
                "/api/v1/members/",
                headers={"Authorization": "Bearer admin_token"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert len(data["data"]["members"]) == 2

    @pytest.mark.asyncio
    async def test_get_members_with_pagination(self, client, admin_user):
        """测试带分页的成员列表"""
        with patch('app.api.deps.get_db') as mock_get_db, \
             patch('app.api.deps.get_current_active_admin') as mock_get_admin:
            
            mock_db = AsyncMock()
            mock_get_db.return_value = mock_db
            mock_get_admin.return_value = admin_user
            
            mock_result = MagicMock()
            mock_result.scalars.return_value.all.return_value = []
            mock_db.execute.return_value = mock_result
            
            mock_count_result = MagicMock()
            mock_count_result.scalar.return_value = 0
            
            response = await client.get(
                "/api/v1/members/?page=1&per_page=10",
                headers={"Authorization": "Bearer admin_token"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert "pagination" in data["data"]

    @pytest.mark.asyncio
    async def test_get_members_with_filters(self, client, admin_user, sample_members):
        """测试带过滤条件的成员列表"""
        with patch('app.api.deps.get_db') as mock_get_db, \
             patch('app.api.deps.get_current_active_admin') as mock_get_admin:
            
            mock_db = AsyncMock()
            mock_get_db.return_value = mock_db
            mock_get_admin.return_value = admin_user
            
            # 过滤结果
            filtered_members = [sample_members[0]]  # 只返回一个用户
            mock_result = MagicMock()
            mock_result.scalars.return_value.all.return_value = filtered_members
            mock_db.execute.return_value = mock_result
            
            mock_count_result = MagicMock()
            mock_count_result.scalar.return_value = 1
            
            response = await client.get(
                "/api/v1/members/?role=member&is_active=true&search=用户1",
                headers={"Authorization": "Bearer admin_token"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert len(data["data"]["members"]) == 1

    @pytest.mark.asyncio
    async def test_get_members_permission_denied(self, client, regular_user):
        """测试普通用户访问成员列表权限拒绝"""
        with patch('app.api.deps.get_current_active_admin') as mock_get_admin:
            mock_get_admin.side_effect = Exception("权限不足")
            
            response = await client.get(
                "/api/v1/members/",
                headers={"Authorization": "Bearer user_token"}
            )
            
            assert response.status_code in [401, 403, 500]


class TestGetMemberAPI(TestMembersAPIBasic):
    """测试获取单个成员API"""

    @pytest.mark.asyncio
    async def test_get_member_basic(self, client, admin_user, regular_user):
        """测试获取单个成员基础功能"""
        with patch('app.api.deps.get_db') as mock_get_db, \
             patch('app.api.deps.get_current_active_admin') as mock_get_admin:
            
            mock_db = AsyncMock()
            mock_get_db.return_value = mock_db
            mock_get_admin.return_value = admin_user
            
            # Mock查询结果
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = regular_user
            mock_db.execute.return_value = mock_result
            
            response = await client.get(
                "/api/v1/members/1",
                headers={"Authorization": "Bearer admin_token"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["data"]["id"] == 1
            assert data["data"]["username"] == "regular_user"

    @pytest.mark.asyncio
    async def test_get_member_not_found(self, client, admin_user):
        """测试获取不存在的成员"""
        with patch('app.api.deps.get_db') as mock_get_db, \
             patch('app.api.deps.get_current_active_admin') as mock_get_admin:
            
            mock_db = AsyncMock()
            mock_get_db.return_value = mock_db
            mock_get_admin.return_value = admin_user
            
            # Mock成员不存在
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = None
            mock_db.execute.return_value = mock_result
            
            response = await client.get(
                "/api/v1/members/999",
                headers={"Authorization": "Bearer admin_token"}
            )
            
            assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_get_member_invalid_id(self, client, admin_user):
        """测试无效成员ID"""
        with patch('app.api.deps.get_current_active_admin') as mock_get_admin:
            mock_get_admin.return_value = admin_user
            
            response = await client.get(
                "/api/v1/members/invalid_id",
                headers={"Authorization": "Bearer admin_token"}
            )
            
            assert response.status_code == 422


class TestCreateMemberAPI(TestMembersAPIBasic):
    """测试创建成员API"""

    @pytest.mark.asyncio
    async def test_create_member_basic(self, client, admin_user):
        """测试创建成员基础功能"""
        member_data = {
            "username": "new_user",
            "student_id": "20210004",
            "name": "新用户",
            "email": "newuser@test.com",
            "role": "member",
            "password": "NewPassword123!"
        }
        
        with patch('app.api.deps.get_db') as mock_get_db, \
             patch('app.api.deps.get_current_active_admin') as mock_get_admin:
            
            mock_db = AsyncMock()
            mock_get_db.return_value = mock_db
            mock_get_admin.return_value = admin_user
            
            # Mock成员创建
            new_member = Member(
                id=4,
                username="new_user",
                student_id="20210004",
                name="新用户",
                email="newuser@test.com",
                role=UserRole.MEMBER
            )
            
            mock_db.add = MagicMock()
            mock_db.commit = AsyncMock()
            mock_db.refresh = AsyncMock()
            
            # Mock唯一性检查
            mock_check_result = MagicMock()
            mock_check_result.scalar_one_or_none.return_value = None  # 用户名不重复
            mock_db.execute.return_value = mock_check_result
            
            with patch('app.core.security.get_password_hash') as mock_hash:
                mock_hash.return_value = "hashed_password"
                
                response = await client.post(
                    "/api/v1/members/",
                    json=member_data,
                    headers={"Authorization": "Bearer admin_token"}
                )
                
                assert response.status_code == 201
                data = response.json()
                assert data["success"] is True
                assert data["data"]["username"] == "new_user"

    @pytest.mark.asyncio
    async def test_create_member_duplicate_username(self, client, admin_user, regular_user):
        """测试创建重复用户名的成员"""
        member_data = {
            "username": "regular_user",  # 重复的用户名
            "student_id": "20210005",
            "name": "重复用户",
            "email": "duplicate@test.com",
            "role": "member",
            "password": "Password123!"
        }
        
        with patch('app.api.deps.get_db') as mock_get_db, \
             patch('app.api.deps.get_current_active_admin') as mock_get_admin:
            
            mock_db = AsyncMock()
            mock_get_db.return_value = mock_db
            mock_get_admin.return_value = admin_user
            
            # Mock用户名重复检查
            mock_check_result = MagicMock()
            mock_check_result.scalar_one_or_none.return_value = regular_user  # 用户名已存在
            mock_db.execute.return_value = mock_check_result
            
            response = await client.post(
                "/api/v1/members/",
                json=member_data,
                headers={"Authorization": "Bearer admin_token"}
            )
            
            assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_create_member_invalid_data(self, client, admin_user):
        """测试创建成员数据验证"""
        invalid_member_data = {
            "username": "",  # 空用户名
            "student_id": "",
            "email": "invalid_email",  # 无效邮箱
            "role": "invalid_role"  # 无效角色
        }
        
        with patch('app.api.deps.get_current_active_admin') as mock_get_admin:
            mock_get_admin.return_value = admin_user
            
            response = await client.post(
                "/api/v1/members/",
                json=invalid_member_data,
                headers={"Authorization": "Bearer admin_token"}
            )
            
            assert response.status_code == 422


class TestUpdateMemberAPI(TestMembersAPIBasic):
    """测试更新成员API"""

    @pytest.mark.asyncio
    async def test_update_member_basic(self, client, admin_user, regular_user):
        """测试更新成员基础功能"""
        update_data = {
            "name": "更新后的用户",
            "email": "updated@test.com",
            "role": "group_leader",
            "is_active": True
        }
        
        with patch('app.api.deps.get_db') as mock_get_db, \
             patch('app.api.deps.get_current_active_admin') as mock_get_admin:
            
            mock_db = AsyncMock()
            mock_get_db.return_value = mock_db
            mock_get_admin.return_value = admin_user
            
            # Mock查询现有成员
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = regular_user
            mock_db.execute.return_value = mock_result
            mock_db.commit = AsyncMock()
            
            response = await client.put(
                "/api/v1/members/1",
                json=update_data,
                headers={"Authorization": "Bearer admin_token"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            
            # 验证更新操作
            assert regular_user.name == "更新后的用户"
            assert regular_user.email == "updated@test.com"
            assert regular_user.role == UserRole.GROUP_LEADER

    @pytest.mark.asyncio
    async def test_update_member_not_found(self, client, admin_user):
        """测试更新不存在的成员"""
        update_data = {"name": "不存在的用户"}
        
        with patch('app.api.deps.get_db') as mock_get_db, \
             patch('app.api.deps.get_current_active_admin') as mock_get_admin:
            
            mock_db = AsyncMock()
            mock_get_db.return_value = mock_db
            mock_get_admin.return_value = admin_user
            
            # Mock成员不存在
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = None
            mock_db.execute.return_value = mock_result
            
            response = await client.put(
                "/api/v1/members/999",
                json=update_data,
                headers={"Authorization": "Bearer admin_token"}
            )
            
            assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_update_member_partial_data(self, client, admin_user, regular_user):
        """测试部分数据更新"""
        update_data = {"name": "部分更新"}  # 只更新名字
        
        with patch('app.api.deps.get_db') as mock_get_db, \
             patch('app.api.deps.get_current_active_admin') as mock_get_admin:
            
            mock_db = AsyncMock()
            mock_get_db.return_value = mock_db
            mock_get_admin.return_value = admin_user
            
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = regular_user
            mock_db.execute.return_value = mock_result
            mock_db.commit = AsyncMock()
            
            original_email = regular_user.email
            
            response = await client.put(
                "/api/v1/members/1",
                json=update_data,
                headers={"Authorization": "Bearer admin_token"}
            )
            
            assert response.status_code == 200
            assert regular_user.name == "部分更新"
            assert regular_user.email == original_email  # 邮箱应该保持不变


class TestDeleteMemberAPI(TestMembersAPIBasic):
    """测试删除成员API"""

    @pytest.mark.asyncio
    async def test_delete_member_basic(self, client, admin_user, regular_user):
        """测试删除成员基础功能"""
        with patch('app.api.deps.get_db') as mock_get_db, \
             patch('app.api.deps.get_current_active_admin') as mock_get_admin:
            
            mock_db = AsyncMock()
            mock_get_db.return_value = mock_db
            mock_get_admin.return_value = admin_user
            
            # Mock查询成员
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = regular_user
            mock_db.execute.return_value = mock_result
            mock_db.delete = MagicMock()
            mock_db.commit = AsyncMock()
            
            response = await client.delete(
                "/api/v1/members/1",
                headers={"Authorization": "Bearer admin_token"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            mock_db.delete.assert_called_once_with(regular_user)

    @pytest.mark.asyncio
    async def test_delete_member_not_found(self, client, admin_user):
        """测试删除不存在的成员"""
        with patch('app.api.deps.get_db') as mock_get_db, \
             patch('app.api.deps.get_current_active_admin') as mock_get_admin:
            
            mock_db = AsyncMock()
            mock_get_db.return_value = mock_db
            mock_get_admin.return_value = admin_user
            
            # Mock成员不存在
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = None
            mock_db.execute.return_value = mock_result
            
            response = await client.delete(
                "/api/v1/members/999",
                headers={"Authorization": "Bearer admin_token"}
            )
            
            assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_self_prevention(self, client, admin_user):
        """测试防止删除自己"""
        with patch('app.api.deps.get_db') as mock_get_db, \
             patch('app.api.deps.get_current_active_admin') as mock_get_admin:
            
            mock_db = AsyncMock()
            mock_get_db.return_value = mock_db
            mock_get_admin.return_value = admin_user
            
            # Mock查询成员（返回当前用户自己）
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = admin_user
            mock_db.execute.return_value = mock_result
            
            response = await client.delete(
                f"/api/v1/members/{admin_user.id}",
                headers={"Authorization": "Bearer admin_token"}
            )
            
            # 应该不能删除自己
            assert response.status_code == 400


class TestImportMembersAPI(TestMembersAPIBasic):
    """测试批量导入成员API"""

    @pytest.mark.asyncio
    async def test_import_members_basic(self, client, admin_user):
        """测试批量导入成员基础功能"""
        # 创建CSV文件内容
        csv_content = """username,student_id,name,email,role
user1,20210001,用户1,user1@test.com,member
user2,20210002,用户2,user2@test.com,member"""
        
        csv_file = io.BytesIO(csv_content.encode('utf-8'))
        
        with patch('app.api.deps.get_db') as mock_get_db, \
             patch('app.api.deps.get_current_active_admin') as mock_get_admin, \
             patch('builtins.open', mock_open(read_data=csv_content)), \
             patch('tempfile.NamedTemporaryFile') as mock_temp:
            
            mock_db = AsyncMock()
            mock_get_db.return_value = mock_db
            mock_get_admin.return_value = admin_user
            
            # Mock临时文件
            mock_temp.return_value.__enter__.return_value.name = '/tmp/test.csv'
            
            # Mock导入过程
            mock_db.add = MagicMock()
            mock_db.commit = AsyncMock()
            
            # Mock唯一性检查（没有重复）
            mock_check_result = MagicMock()
            mock_check_result.scalar_one_or_none.return_value = None
            mock_db.execute.return_value = mock_check_result
            
            response = await client.post(
                "/api/v1/members/import",
                files={"file": ("members.csv", csv_file, "text/csv")},
                headers={"Authorization": "Bearer admin_token"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True

    @pytest.mark.asyncio
    async def test_import_members_invalid_file(self, client, admin_user):
        """测试导入无效文件格式"""
        invalid_file = io.BytesIO(b"invalid file content")
        
        with patch('app.api.deps.get_current_active_admin') as mock_get_admin:
            mock_get_admin.return_value = admin_user
            
            response = await client.post(
                "/api/v1/members/import",
                files={"file": ("invalid.txt", invalid_file, "text/plain")},
                headers={"Authorization": "Bearer admin_token"}
            )
            
            assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_import_members_empty_file(self, client, admin_user):
        """测试导入空文件"""
        empty_file = io.BytesIO(b"")
        
        with patch('app.api.deps.get_current_active_admin') as mock_get_admin:
            mock_get_admin.return_value = admin_user
            
            response = await client.post(
                "/api/v1/members/import",
                files={"file": ("empty.csv", empty_file, "text/csv")},
                headers={"Authorization": "Bearer admin_token"}
            )
            
            assert response.status_code == 400


class TestChangePasswordAPI(TestMembersAPIBasic):
    """测试修改密码API"""

    @pytest.mark.asyncio
    async def test_change_password_basic(self, client, admin_user, regular_user):
        """测试修改密码基础功能"""
        password_data = {
            "current_password": "old_password",
            "new_password": "NewPassword123!"
        }
        
        with patch('app.api.deps.get_db') as mock_get_db, \
             patch('app.api.deps.get_current_user') as mock_get_user:
            
            mock_db = AsyncMock()
            mock_get_db.return_value = mock_db
            mock_get_user.return_value = regular_user
            
            # Mock查询成员
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = regular_user
            mock_db.execute.return_value = mock_result
            mock_db.commit = AsyncMock()
            
            with patch('app.core.security.verify_password') as mock_verify, \
                 patch('app.core.security.get_password_hash') as mock_hash:
                
                mock_verify.return_value = True  # 旧密码正确
                mock_hash.return_value = "new_hashed_password"
                
                response = await client.post(
                    "/api/v1/members/1/change-password",
                    json=password_data,
                    headers={"Authorization": "Bearer user_token"}
                )
                
                assert response.status_code == 200
                data = response.json()
                assert data["success"] is True
                mock_verify.assert_called_once()
                mock_hash.assert_called_once_with("NewPassword123!")

    @pytest.mark.asyncio
    async def test_change_password_wrong_current(self, client, regular_user):
        """测试当前密码错误"""
        password_data = {
            "current_password": "wrong_password",
            "new_password": "NewPassword123!"
        }
        
        with patch('app.api.deps.get_db') as mock_get_db, \
             patch('app.api.deps.get_current_user') as mock_get_user:
            
            mock_db = AsyncMock()
            mock_get_db.return_value = mock_db
            mock_get_user.return_value = regular_user
            
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = regular_user
            mock_db.execute.return_value = mock_result
            
            with patch('app.core.security.verify_password') as mock_verify:
                mock_verify.return_value = False  # 旧密码错误
                
                response = await client.post(
                    "/api/v1/members/1/change-password",
                    json=password_data,
                    headers={"Authorization": "Bearer user_token"}
                )
                
                assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_change_password_weak_new_password(self, client, regular_user):
        """测试新密码强度不足"""
        password_data = {
            "current_password": "old_password",
            "new_password": "123"  # 弱密码
        }
        
        with patch('app.api.deps.get_current_user') as mock_get_user:
            mock_get_user.return_value = regular_user
            
            response = await client.post(
                "/api/v1/members/1/change-password",
                json=password_data,
                headers={"Authorization": "Bearer user_token"}
            )
            
            assert response.status_code == 422


class TestMemberStatsAPI(TestMembersAPIBasic):
    """测试成员统计API"""

    @pytest.mark.asyncio
    async def test_get_member_stats_overview(self, client, admin_user):
        """测试获取成员统计概览"""
        with patch('app.api.deps.get_db') as mock_get_db, \
             patch('app.api.deps.get_current_active_admin') as mock_get_admin:
            
            mock_db = AsyncMock()
            mock_get_db.return_value = mock_db
            mock_get_admin.return_value = admin_user
            
            # Mock统计查询结果
            mock_results = [
                MagicMock(scalar=MagicMock(return_value=50)),   # 总成员数
                MagicMock(scalar=MagicMock(return_value=45)),   # 活跃成员数
                MagicMock(scalar=MagicMock(return_value=40)),   # 普通成员数
                MagicMock(scalar=MagicMock(return_value=8)),    # 组长数
                MagicMock(scalar=MagicMock(return_value=2)),    # 管理员数
                MagicMock(scalar=MagicMock(return_value=10))    # 本月新增成员数
            ]
            mock_db.execute.side_effect = mock_results
            
            response = await client.get(
                "/api/v1/members/stats/overview",
                headers={"Authorization": "Bearer admin_token"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["data"]["total_members"] == 50
            assert data["data"]["active_members"] == 45
            assert data["data"]["role_distribution"]["member"] == 40
            assert data["data"]["role_distribution"]["group_leader"] == 8
            assert data["data"]["role_distribution"]["admin"] == 2


class TestMembersErrorHandling(TestMembersAPIBasic):
    """测试成员API错误处理"""

    @pytest.mark.asyncio
    async def test_database_connection_error(self, client, admin_user):
        """测试数据库连接错误"""
        with patch('app.api.deps.get_db') as mock_get_db, \
             patch('app.api.deps.get_current_active_admin') as mock_get_admin:
            
            mock_get_admin.return_value = admin_user
            mock_get_db.side_effect = Exception("Database connection failed")
            
            response = await client.get(
                "/api/v1/members/",
                headers={"Authorization": "Bearer admin_token"}
            )
            
            assert response.status_code == 500

    @pytest.mark.asyncio
    async def test_unauthorized_access(self, client):
        """测试未授权访问"""
        response = await client.get("/api/v1/members/")
        
        assert response.status_code in [401, 422]

    @pytest.mark.asyncio
    async def test_concurrent_member_creation(self, client, admin_user):
        """测试并发创建成员"""
        member_data = {
            "username": "concurrent_user",
            "student_id": "20210010",
            "name": "并发用户",
            "email": "concurrent@test.com",
            "role": "member",
            "password": "Password123!"
        }
        
        with patch('app.api.deps.get_db') as mock_get_db, \
             patch('app.api.deps.get_current_active_admin') as mock_get_admin:
            
            mock_db = AsyncMock()
            mock_get_db.return_value = mock_db
            mock_get_admin.return_value = admin_user
            
            # Mock并发冲突
            mock_check_result = MagicMock()
            mock_check_result.scalar_one_or_none.return_value = None  # 第一次检查没有重复
            mock_db.execute.return_value = mock_check_result
            
            # Mock提交时出现冲突
            mock_db.commit.side_effect = Exception("Integrity constraint violation")
            
            response = await client.post(
                "/api/v1/members/",
                json=member_data,
                headers={"Authorization": "Bearer admin_token"}
            )
            
            assert response.status_code == 500

    @pytest.mark.asyncio
    async def test_large_member_list_performance(self, client, admin_user):
        """测试大量成员列表性能"""
        with patch('app.api.deps.get_db') as mock_get_db, \
             patch('app.api.deps.get_current_active_admin') as mock_get_admin:
            
            mock_db = AsyncMock()
            mock_get_db.return_value = mock_db
            mock_get_admin.return_value = admin_user
            
            # Mock大量成员数据
            large_member_list = [
                Member(id=i, username=f"user{i}", name=f"用户{i}")
                for i in range(1000)
            ]
            
            mock_result = MagicMock()
            mock_result.scalars.return_value.all.return_value = large_member_list[:100]  # 分页限制
            mock_db.execute.return_value = mock_result
            
            mock_count_result = MagicMock()
            mock_count_result.scalar.return_value = 1000
            
            response = await client.get(
                "/api/v1/members/?per_page=100",
                headers={"Authorization": "Bearer admin_token"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert len(data["data"]["members"]) == 100  # 验证分页有效

    @pytest.mark.asyncio
    async def test_sql_injection_prevention(self, client, admin_user):
        """测试SQL注入防护"""
        with patch('app.api.deps.get_db') as mock_get_db, \
             patch('app.api.deps.get_current_active_admin') as mock_get_admin:
            
            mock_db = AsyncMock()
            mock_get_db.return_value = mock_db
            mock_get_admin.return_value = admin_user
            
            mock_result = MagicMock()
            mock_result.scalars.return_value.all.return_value = []
            mock_db.execute.return_value = mock_result
            
            mock_count_result = MagicMock()
            mock_count_result.scalar.return_value = 0
            
            # 尝试SQL注入
            response = await client.get(
                "/api/v1/members/?search='; DROP TABLE members; --",
                headers={"Authorization": "Bearer admin_token"}
            )
            
            # 应该正常处理，不会执行恶意SQL
            assert response.status_code == 200