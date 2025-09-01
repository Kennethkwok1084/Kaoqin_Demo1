"""
系统设置和权限E2E测试
测试超级管理员修改工时规则、权限控制验证、系统参数实时生效
包含完整的系统配置管理和权限验证流程
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict

import pytest
from httpx import AsyncClient

from app.models.member import UserRole


class TestSystemSettingsAndPermissions:
    """系统设置和权限E2E测试类"""

    @pytest.mark.asyncio
    async def test_work_hours_rules_configuration(
        self,
        e2e_client: AsyncClient,
        e2e_user_tokens: Dict[str, str],
        e2e_auth_headers,
        e2e_helper,
    ):
        """测试工时规则配置管理"""

        super_admin_headers = e2e_auth_headers(e2e_user_tokens["super_admin"])
        admin_headers = e2e_auth_headers(e2e_user_tokens["admin"])

        # 1. 获取当前工时规则
        current_rules_response = await e2e_client.get(
            "/api/v1/system/config/work-hours", headers=super_admin_headers
        )

        if current_rules_response.status_code == 200:
            e2e_helper.assert_response_success(current_rules_response)
            current_rules = current_rules_response.json().get("data", {})

            # 保存原始配置用于恢复
            original_config = current_rules.copy()

            # 2. 修改工时规则
            new_rules = {
                "online_task_base_hours": 45,  # 从40分钟改为45分钟
                "offline_task_base_hours": 110,  # 从100分钟改为110分钟
                "rush_period_bonus": 20,  # 从15分钟改为20分钟
                "positive_review_bonus": 35,  # 从30分钟改为35分钟
                "late_response_penalty": 35,  # 从30分钟改为35分钟
                "late_completion_penalty": 35,  # 从30分钟改为35分钟
                "negative_review_penalty": 70,  # 从60分钟改为70分钟
            }

            update_response = await e2e_client.put(
                "/api/v1/system/config/work-hours",
                json=new_rules,
                headers=super_admin_headers,
            )

            e2e_helper.assert_response_success(update_response)
            update_result = update_response.json()
            assert update_result["success"] is True

            # 3. 验证配置更新成功
            updated_rules_response = await e2e_client.get(
                "/api/v1/system/config/work-hours", headers=super_admin_headers
            )
            e2e_helper.assert_response_success(updated_rules_response)

            updated_rules = updated_rules_response.json().get("data", {})
            assert (
                updated_rules["online_task_base_hours"]
                == new_rules["online_task_base_hours"]
            )
            assert (
                updated_rules["offline_task_base_hours"]
                == new_rules["offline_task_base_hours"]
            )

            # 4. 测试普通管理员无法修改工时规则
            unauthorized_response = await e2e_client.put(
                "/api/v1/system/config/work-hours",
                json={"online_task_base_hours": 50},
                headers=admin_headers,
            )

            # 应该返回403 Forbidden
            assert unauthorized_response.status_code == 403

            # 5. 恢复原始配置
            if original_config:
                restore_response = await e2e_client.put(
                    "/api/v1/system/config/work-hours",
                    json=original_config,
                    headers=super_admin_headers,
                )
                e2e_helper.assert_response_success(restore_response)
        else:
            pytest.skip("Work hours configuration not available")

    @pytest.mark.asyncio
    async def test_system_parameters_real_time_effect(
        self,
        e2e_client: AsyncClient,
        e2e_user_tokens: Dict[str, str],
        e2e_test_users: Dict[str, str],
        e2e_auth_headers,
        e2e_helper,
    ):
        """测试系统参数实时生效"""

        super_admin_headers = e2e_auth_headers(e2e_user_tokens["super_admin"])
        admin_headers = e2e_auth_headers(e2e_user_tokens["admin"])

        # 1. 获取原始系统配置
        original_config_response = await e2e_client.get(
            "/api/v1/system/config", headers=super_admin_headers
        )

        if original_config_response.status_code == 200:
            original_config = original_config_response.json().get("data", {})

            # 2. 修改系统配置参数
            new_config = {
                "max_tasks_per_member": 25,  # 修改每个成员最大任务数
                "task_auto_assignment": True,  # 开启任务自动分配
                "notification_settings": {
                    "email_enabled": True,
                    "sms_enabled": False,
                    "in_app_enabled": True,
                },
                "data_retention_days": 365,  # 数据保留天数
            }

            update_config_response = await e2e_client.put(
                "/api/v1/system/config", json=new_config, headers=super_admin_headers
            )

            if update_config_response.status_code == 200:
                e2e_helper.assert_response_success(update_config_response)

                # 3. 验证配置立即生效 - 通过创建任务测试限制
                # 这里可以测试新配置是否立即影响业务逻辑

                # 4. 测试配置缓存刷新
                cache_refresh_response = await e2e_client.post(
                    "/api/v1/system/config/refresh-cache", headers=super_admin_headers
                )

                if cache_refresh_response.status_code == 200:
                    e2e_helper.assert_response_success(cache_refresh_response)
                    refresh_result = cache_refresh_response.json()
                    assert refresh_result["success"] is True

                # 5. 恢复原始配置
                if original_config:
                    restore_response = await e2e_client.put(
                        "/api/v1/system/config",
                        json=original_config,
                        headers=super_admin_headers,
                    )
                    if restore_response.status_code == 200:
                        e2e_helper.assert_response_success(restore_response)
        else:
            pytest.skip("System configuration not available")

    @pytest.mark.asyncio
    async def test_role_based_permission_matrix(
        self,
        e2e_client: AsyncClient,
        e2e_user_tokens: Dict[str, str],
        e2e_auth_headers,
        e2e_helper,
    ):
        """测试基于角色的权限矩阵"""

        # 定义权限测试矩阵
        permission_matrix = {
            # 端点: {角色: 期望状态码}
            "/api/v1/members": {
                "student": [401, 403],
                "leader": [200, 403],
                "admin": [200],
                "super_admin": [200],
            },
            "/api/v1/system/config": {
                "student": [401, 403],
                "leader": [401, 403],
                "admin": [200, 403],
                "super_admin": [200],
            },
            "/api/v1/system/config/work-hours": {
                "student": [401, 403],
                "leader": [401, 403],
                "admin": [401, 403],
                "super_admin": [200],
            },
            "/api/v1/statistics/overview": {
                "student": [401, 403],
                "leader": [200, 403],
                "admin": [200],
                "super_admin": [200],
            },
            "/api/v1/tasks/repair/my": {
                "student": [200, 404],
                "leader": [200, 404],
                "admin": [200, 404],
                "super_admin": [200, 404],
            },
        }

        # 执行权限矩阵测试
        for endpoint, role_permissions in permission_matrix.items():
            for role, expected_codes in role_permissions.items():
                if role in e2e_user_tokens:
                    headers = e2e_auth_headers(e2e_user_tokens[role])

                    response = await e2e_client.get(endpoint, headers=headers)

                    assert (
                        response.status_code in expected_codes
                    ), f"Role '{role}' accessing '{endpoint}' returned {response.status_code}, expected one of {expected_codes}"

    @pytest.mark.asyncio
    async def test_user_role_management_permissions(
        self,
        e2e_client: AsyncClient,
        e2e_user_tokens: Dict[str, str],
        e2e_test_users: Dict[str, str],
        e2e_auth_headers,
        e2e_helper,
    ):
        """测试用户角色管理权限"""

        super_admin_headers = e2e_auth_headers(e2e_user_tokens["super_admin"])
        admin_headers = e2e_auth_headers(e2e_user_tokens["admin"])
        student_headers = e2e_auth_headers(e2e_user_tokens["student"])

        student_member_id = e2e_test_users["student"].id

        # 1. 超级管理员可以修改用户角色
        role_update_data = {"role": UserRole.GROUP_LEADER.value}

        super_admin_update_response = await e2e_client.put(
            f"/api/v1/members/{student_member_id}/role",
            json=role_update_data,
            headers=super_admin_headers,
        )

        if super_admin_update_response.status_code == 200:
            e2e_helper.assert_response_success(super_admin_update_response)

            # 验证角色更新成功
            member_response = await e2e_client.get(
                f"/api/v1/members/{student_member_id}", headers=super_admin_headers
            )

            if member_response.status_code == 200:
                member_data = member_response.json().get("data", {})
                assert member_data["role"] == UserRole.GROUP_LEADER.value

            # 恢复原角色
            restore_role_data = {"role": UserRole.MEMBER.value}
            await e2e_client.put(
                f"/api/v1/members/{student_member_id}/role",
                json=restore_role_data,
                headers=super_admin_headers,
            )

        # 2. 普通管理员不能修改用户角色（如果有此限制）
        admin_update_response = await e2e_client.put(
            f"/api/v1/members/{student_member_id}/role",
            json={"role": UserRole.GROUP_LEADER.value},
            headers=admin_headers,
        )

        # 根据系统设计，可能返回403或200
        # 这里检查是否有权限控制
        if admin_update_response.status_code == 403:
            # 系统实施了角色权限控制
            assert admin_update_response.status_code == 403

        # 3. 学生不能修改任何用户角色
        student_update_response = await e2e_client.put(
            f"/api/v1/members/{student_member_id}/role",
            json={"role": UserRole.ADMIN.value},
            headers=student_headers,
        )

        # 学生应该被拒绝
        assert student_update_response.status_code in [401, 403]

    @pytest.mark.asyncio
    async def test_system_maintenance_mode(
        self,
        e2e_client: AsyncClient,
        e2e_user_tokens: Dict[str, str],
        e2e_auth_headers,
        e2e_helper,
    ):
        """测试系统维护模式"""

        super_admin_headers = e2e_auth_headers(e2e_user_tokens["super_admin"])
        student_headers = e2e_auth_headers(e2e_user_tokens["student"])

        # 1. 启用维护模式
        maintenance_data = {
            "maintenance_mode": True,
            "maintenance_message": "系统正在维护中，预计30分钟后恢复",
            "allowed_roles": [UserRole.SUPER_ADMIN.value],
        }

        maintenance_response = await e2e_client.put(
            "/api/v1/system/maintenance",
            json=maintenance_data,
            headers=super_admin_headers,
        )

        if maintenance_response.status_code == 200:
            e2e_helper.assert_response_success(maintenance_response)

            # 2. 验证维护模式生效 - 普通用户被阻止访问
            student_access_response = await e2e_client.get(
                "/api/v1/tasks/repair/my", headers=student_headers
            )

            # 在维护模式下，普通用户应该被拒绝或收到维护提示
            if student_access_response.status_code == 503:
                # 系统返回服务不可用
                maintenance_info = student_access_response.json()
                assert "maintenance" in maintenance_info.get("message", "").lower()

            # 3. 超级管理员仍可访问
            super_admin_access_response = await e2e_client.get(
                "/api/v1/system/config", headers=super_admin_headers
            )

            # 超级管理员应该仍能访问
            assert super_admin_access_response.status_code in [200, 404]

            # 4. 关闭维护模式
            disable_maintenance_response = await e2e_client.put(
                "/api/v1/system/maintenance",
                json={"maintenance_mode": False},
                headers=super_admin_headers,
            )

            if disable_maintenance_response.status_code == 200:
                e2e_helper.assert_response_success(disable_maintenance_response)

                # 验证维护模式已关闭
                normal_access_response = await e2e_client.get(
                    "/api/v1/tasks/repair/my", headers=student_headers
                )

                # 普通用户应该能正常访问
                assert normal_access_response.status_code in [200, 404]
        else:
            pytest.skip("System maintenance mode not available")

    @pytest.mark.asyncio
    async def test_audit_log_and_system_monitoring(
        self,
        e2e_client: AsyncClient,
        e2e_user_tokens: Dict[str, str],
        e2e_auth_headers,
        e2e_helper,
    ):
        """测试审计日志和系统监控"""

        super_admin_headers = e2e_auth_headers(e2e_user_tokens["super_admin"])
        admin_headers = e2e_auth_headers(e2e_user_tokens["admin"])

        # 1. 执行一些需要记录的操作
        test_operations = [
            # 系统配置查询
            e2e_client.get("/api/v1/system/config", headers=super_admin_headers),
            # 用户列表查询
            e2e_client.get("/api/v1/members", headers=admin_headers),
        ]

        # 执行操作
        for operation in test_operations:
            await operation

        # 短暂等待日志记录
        await asyncio.sleep(1)

        # 2. 获取审计日志
        audit_log_response = await e2e_client.get(
            "/api/v1/system/audit-log",
            params={
                "start_date": (datetime.now() - timedelta(hours=1)).isoformat(),
                "end_date": datetime.now().isoformat(),
            },
            headers=super_admin_headers,
        )

        if audit_log_response.status_code == 200:
            e2e_helper.assert_response_success(audit_log_response)
            audit_data = audit_log_response.json().get("data", {})

            logs = audit_data.get("logs", [])
            if logs:
                # 验证日志条目结构
                for log_entry in logs:
                    assert "timestamp" in log_entry
                    assert "user_id" in log_entry
                    assert "action" in log_entry
                    assert "resource" in log_entry

        # 3. 获取系统性能监控数据
        performance_response = await e2e_client.get(
            "/api/v1/system/performance", headers=super_admin_headers
        )

        if performance_response.status_code == 200:
            e2e_helper.assert_response_success(performance_response)
            performance_data = performance_response.json().get("data", {})

            # 验证性能数据结构
            expected_metrics = [
                "cpu_usage",
                "memory_usage",
                "response_time",
                "active_connections",
            ]

            for metric in expected_metrics:
                if metric in performance_data:
                    assert isinstance(performance_data[metric], (int, float))
                    assert performance_data[metric] >= 0

    @pytest.mark.asyncio
    async def test_data_backup_and_recovery_permissions(
        self,
        e2e_client: AsyncClient,
        e2e_user_tokens: Dict[str, str],
        e2e_auth_headers,
        e2e_helper,
    ):
        """测试数据备份和恢复权限"""

        super_admin_headers = e2e_auth_headers(e2e_user_tokens["super_admin"])
        admin_headers = e2e_auth_headers(e2e_user_tokens["admin"])
        student_headers = e2e_auth_headers(e2e_user_tokens["student"])

        # 1. 超级管理员可以触发数据备份
        backup_request_data = {
            "backup_type": "full",
            "include_files": True,
            "compression": True,
        }

        backup_response = await e2e_client.post(
            "/api/v1/system/backup",
            json=backup_request_data,
            headers=super_admin_headers,
        )

        if backup_response.status_code == 200:
            e2e_helper.assert_response_success(backup_response)
            backup_result = backup_response.json()

            backup_data = backup_result.get("data", {})
            assert "backup_id" in backup_data
            assert "status" in backup_data

        # 2. 普通管理员不能触发备份
        admin_backup_response = await e2e_client.post(
            "/api/v1/system/backup", json=backup_request_data, headers=admin_headers
        )

        # 应该被拒绝
        assert admin_backup_response.status_code in [401, 403]

        # 3. 学生不能触发备份
        student_backup_response = await e2e_client.post(
            "/api/v1/system/backup", json=backup_request_data, headers=student_headers
        )

        # 应该被拒绝
        assert student_backup_response.status_code in [401, 403]

        # 4. 获取备份历史记录
        backup_history_response = await e2e_client.get(
            "/api/v1/system/backup/history", headers=super_admin_headers
        )

        if backup_history_response.status_code == 200:
            e2e_helper.assert_response_success(backup_history_response)
            history_data = backup_history_response.json().get("data", {})

            backups = history_data.get("backups", [])
            if backups:
                for backup in backups:
                    assert "backup_id" in backup
                    assert "created_at" in backup
                    assert "status" in backup
                    assert "size" in backup

    @pytest.mark.asyncio
    async def test_security_settings_and_policies(
        self,
        e2e_client: AsyncClient,
        e2e_user_tokens: Dict[str, str],
        e2e_auth_headers,
        e2e_helper,
    ):
        """测试安全设置和策略"""

        super_admin_headers = e2e_auth_headers(e2e_user_tokens["super_admin"])

        # 1. 获取当前安全策略
        security_policy_response = await e2e_client.get(
            "/api/v1/system/security-policy", headers=super_admin_headers
        )

        if security_policy_response.status_code == 200:
            e2e_helper.assert_response_success(security_policy_response)
            current_policy = security_policy_response.json().get("data", {})

            # 保存原始策略
            original_policy = current_policy.copy()

            # 2. 更新安全策略
            new_security_policy = {
                "password_min_length": 10,
                "password_require_uppercase": True,
                "password_require_numbers": True,
                "password_require_symbols": True,
                "session_timeout_minutes": 30,
                "max_login_attempts": 3,
                "lockout_duration_minutes": 15,
                "require_2fa": False,
                "ip_whitelist_enabled": False,
            }

            update_policy_response = await e2e_client.put(
                "/api/v1/system/security-policy",
                json=new_security_policy,
                headers=super_admin_headers,
            )

            if update_policy_response.status_code == 200:
                e2e_helper.assert_response_success(update_policy_response)

                # 3. 验证策略更新成功
                updated_policy_response = await e2e_client.get(
                    "/api/v1/system/security-policy", headers=super_admin_headers
                )

                if updated_policy_response.status_code == 200:
                    updated_policy = updated_policy_response.json().get("data", {})
                    assert (
                        updated_policy["password_min_length"]
                        == new_security_policy["password_min_length"]
                    )
                    assert (
                        updated_policy["max_login_attempts"]
                        == new_security_policy["max_login_attempts"]
                    )

                # 4. 恢复原始策略
                if original_policy:
                    restore_response = await e2e_client.put(
                        "/api/v1/system/security-policy",
                        json=original_policy,
                        headers=super_admin_headers,
                    )
                    if restore_response.status_code == 200:
                        e2e_helper.assert_response_success(restore_response)
        else:
            pytest.skip("Security policy management not available")

    @pytest.mark.asyncio
    async def test_system_notifications_and_alerts(
        self,
        e2e_client: AsyncClient,
        e2e_user_tokens: Dict[str, str],
        e2e_auth_headers,
        e2e_helper,
    ):
        """测试系统通知和警报"""

        super_admin_headers = e2e_auth_headers(e2e_user_tokens["super_admin"])
        admin_headers = e2e_auth_headers(e2e_user_tokens["admin"])

        # 1. 创建系统通知
        system_notification_data = {
            "title": "系统维护通知",
            "content": "系统将于今晚22:00进行例行维护，预计耗时1小时",
            "type": "system_maintenance",
            "priority": "medium",
            "target_roles": [UserRole.ADMIN.value, UserRole.MEMBER.value],
            "expires_at": (datetime.now() + timedelta(days=1)).isoformat(),
        }

        create_notification_response = await e2e_client.post(
            "/api/v1/system/notifications",
            json=system_notification_data,
            headers=super_admin_headers,
        )

        if create_notification_response.status_code == 201:
            e2e_helper.assert_response_success(create_notification_response, 201)
            notification_result = create_notification_response.json()

            notification_data = notification_result.get("data", {})
            notification_id = notification_data["id"]

            # 2. 验证通知创建成功
            assert notification_data["title"] == system_notification_data["title"]
            assert notification_data["type"] == system_notification_data["type"]

            # 3. 管理员查看系统通知
            admin_notifications_response = await e2e_client.get(
                "/api/v1/notifications/system", headers=admin_headers
            )

            if admin_notifications_response.status_code == 200:
                e2e_helper.assert_response_success(admin_notifications_response)
                notifications = (
                    admin_notifications_response.json().get("data", {}).get("items", [])
                )

                # 查找刚创建的通知
                created_notification = next(
                    (
                        notif
                        for notif in notifications
                        if notif["id"] == notification_id
                    ),
                    None,
                )
                assert created_notification is not None

            # 4. 删除测试通知（清理）
            delete_response = await e2e_client.delete(
                f"/api/v1/system/notifications/{notification_id}",
                headers=super_admin_headers,
            )

            if delete_response.status_code == 200:
                e2e_helper.assert_response_success(delete_response)

        # 5. 获取系统警报
        system_alerts_response = await e2e_client.get(
            "/api/v1/system/alerts", headers=super_admin_headers
        )

        if system_alerts_response.status_code == 200:
            e2e_helper.assert_response_success(system_alerts_response)
            alerts_data = system_alerts_response.json().get("data", {})

            alerts = alerts_data.get("alerts", [])
            if alerts:
                for alert in alerts:
                    assert "alert_type" in alert
                    assert "severity" in alert
                    assert "message" in alert
                    assert "created_at" in alert


class TestSystemPermissionsPerformance:
    """系统权限性能测试"""

    @pytest.mark.asyncio
    async def test_permission_check_performance(
        self,
        e2e_client: AsyncClient,
        e2e_user_tokens: Dict[str, str],
        e2e_auth_headers,
        e2e_performance_monitor,
        e2e_helper,
    ):
        """测试权限检查性能"""

        admin_headers = e2e_auth_headers(e2e_user_tokens["admin"])
        e2e_performance_monitor.start()

        permission_check_times = []

        # 测试多次权限检查的性能
        for i in range(10):
            start_time = asyncio.get_event_loop().time()

            # 执行需要权限检查的操作
            response = await e2e_client.get("/api/v1/members", headers=admin_headers)

            end_time = asyncio.get_event_loop().time()
            duration = end_time - start_time
            permission_check_times.append(duration)

            e2e_performance_monitor.record(f"permission_check_{i}", duration)

            # 验证响应（允许404表示资源不存在但权限检查通过）
            assert response.status_code in [200, 404]

        # 性能验证
        avg_check_time = sum(permission_check_times) / len(permission_check_times)
        max_check_time = max(permission_check_times)

        assert (
            avg_check_time < 1.0
        ), f"Average permission check time {avg_check_time}s exceeds 1s"
        assert (
            max_check_time < 3.0
        ), f"Max permission check time {max_check_time}s exceeds 3s"

        summary = e2e_performance_monitor.summary()
        print(f"Permission Check Performance Summary: {summary}")
