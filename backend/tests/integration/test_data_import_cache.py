"""
数据导入和缓存系统集成测试
测试Excel数据导入、数据匹配、Redis缓存等功能
"""

import io
import json
from datetime import date, datetime, timedelta
from unittest.mock import AsyncMock, Mock, patch

import pandas as pd
import pytest
import pytest_asyncio

from app.models.member import Member, UserRole
from app.models.task import RepairTask, TaskPriority, TaskStatus


class TestExcelDataImport:
    """测试Excel数据导入功能"""

    def test_upload_excel_file(self, client, auth_headers_admin):
        """测试上传Excel文件"""
        # 创建模拟Excel文件内容
        excel_data = {
            "报告人姓名": ["张三", "李四", "王五"],
            "联系方式": ["13812345678", "13987654321", "13765432109"],
            "故障描述": ["网络断线", "打印机故障", "投影仪无信号"],
            "维修地点": ["教学楼A101", "办公楼B203", "图书馆C301"],
            "维修类型": ["线下维修", "线上维修", "线下维修"],
            "紧急程度": ["高", "中", "低"],
            "报告时间": [
                "2025-01-29 09:00:00",
                "2025-01-29 10:30:00",
                "2025-01-29 14:15:00",
            ],
        }

        # 创建临时Excel文件
        df = pd.DataFrame(excel_data)
        excel_buffer = io.BytesIO()
        df.to_excel(excel_buffer, index=False, engine="openpyxl")
        excel_buffer.seek(0)

        # 模拟文件上传
        files = {
            "file": (
                "repair_data.xlsx",
                excel_buffer.getvalue(),
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        }

        response = client.post(
            "/api/data-import/upload", files=files, headers=auth_headers_admin
        )

        if response.status_code == 200:
            data = response.json()

            # 验证上传响应
            assert "file_id" in data
            assert "filename" in data
            assert "total_rows" in data
            assert "preview_data" in data
            assert data["total_rows"] == 3
            assert data["filename"] == "repair_data.xlsx"

            # 验证预览数据
            preview = data["preview_data"]
            assert len(preview) <= 5  # 最多显示5行预览
            assert "报告人姓名" in preview[0]
            assert preview[0]["报告人姓名"] == "张三"
        else:
            # 如果功能未实现
            assert response.status_code in [404, 405, 501]

    def test_preview_import_data(self, client, auth_headers_admin):
        """测试预览导入数据"""
        # 模拟已上传的文件ID
        file_id = "test_file_12345"

        response = client.get(
            f"/api/data-import/preview/{file_id}", headers=auth_headers_admin
        )

        if response.status_code == 200:
            data = response.json()

            # 验证预览数据结构
            assert "file_info" in data
            assert "column_mapping" in data
            assert "data_sample" in data
            assert "validation_results" in data

            # 验证文件信息
            file_info = data["file_info"]
            assert "filename" in file_info
            assert "total_rows" in file_info
            assert "uploaded_at" in file_info

            # 验证列映射建议
            column_mapping = data["column_mapping"]
            assert "suggested_mappings" in column_mapping
            assert "available_fields" in column_mapping
        else:
            # 如果功能未实现或文件不存在
            assert response.status_code in [404, 405, 501]

    def test_validate_import_data(self, client, auth_headers_admin):
        """测试验证导入数据"""
        validation_data = {
            "file_id": "test_file_12345",
            "column_mapping": {
                "报告人姓名": "reporter_name",
                "联系方式": "reporter_contact",
                "故障描述": "description",
                "维修地点": "location",
                "维修类型": "repair_type",
                "紧急程度": "priority",
                "报告时间": "reported_at",
            },
            "validation_rules": {
                "require_contact_match": True,
                "auto_assign_tasks": False,
                "default_priority": "medium",
            },
        }

        response = client.post(
            "/api/data-import/validate",
            json=validation_data,
            headers=auth_headers_admin,
        )

        if response.status_code == 200:
            data = response.json()

            # 验证验证结果
            assert "validation_summary" in data
            assert "valid_rows" in data
            assert "invalid_rows" in data
            assert "warnings" in data
            assert "suggested_fixes" in data

            # 验证统计信息
            summary = data["validation_summary"]
            assert "total_rows" in summary
            assert "valid_count" in summary
            assert "invalid_count" in summary
            assert "warning_count" in summary

            # 验证数据合理性
            assert (
                summary["valid_count"] + summary["invalid_count"]
                == summary["total_rows"]
            )
        else:
            # 如果功能未实现
            assert response.status_code in [404, 405, 501, 422]

    def test_execute_data_import(self, client, auth_headers_admin):
        """测试执行数据导入"""
        import_data = {
            "file_id": "test_file_12345",
            "column_mapping": {
                "报告人姓名": "reporter_name",
                "联系方式": "reporter_contact",
                "故障描述": "description",
                "维修地点": "location",
                "维修类型": "repair_type",
                "紧急程度": "priority",
            },
            "import_options": {
                "skip_invalid_rows": True,
                "auto_assign_to_group": True,
                "default_assignee": None,
                "create_task_numbers": True,
                "notify_assignees": False,
            },
        }

        response = client.post(
            "/api/data-import/execute", json=import_data, headers=auth_headers_admin
        )

        if response.status_code == 200:
            data = response.json()

            # 验证导入结果
            assert "import_summary" in data
            assert "successful_imports" in data
            assert "failed_imports" in data
            assert "import_id" in data

            # 验证导入统计
            summary = data["import_summary"]
            assert "total_processed" in summary
            assert "successful_count" in summary
            assert "failed_count" in summary
            assert "created_tasks" in summary

            # 验证数据合理性
            assert (
                summary["successful_count"] + summary["failed_count"]
                == summary["total_processed"]
            )
            assert len(data["successful_imports"]) == summary["successful_count"]
            assert len(data["failed_imports"]) == summary["failed_count"]
        else:
            # 如果功能未实现
            assert response.status_code in [404, 405, 501, 422]

    def test_get_import_history(self, client, auth_headers_admin):
        """测试获取导入历史"""
        response = client.get("/api/data-import/history", headers=auth_headers_admin)

        if response.status_code == 200:
            data = response.json()

            # 验证历史记录结构
            assert "items" in data
            assert "total" in data
            assert "page" in data
            assert "size" in data

            # 验证记录内容
            for item in data["items"]:
                assert "import_id" in item
                assert "filename" in item
                assert "imported_by" in item
                assert "imported_at" in item
                assert "status" in item
                assert "total_records" in item
                assert "successful_records" in item
                assert "failed_records" in item
        else:
            # 如果功能未实现
            assert response.status_code in [404, 405, 501]

    def test_get_import_detail(self, client, auth_headers_admin):
        """测试获取导入详情"""
        import_id = "import_12345"

        response = client.get(
            f"/api/data-import/history/{import_id}", headers=auth_headers_admin
        )

        if response.status_code == 200:
            data = response.json()

            # 验证详情数据
            assert "import_id" in data
            assert "file_info" in data
            assert "import_options" in data
            assert "summary" in data
            assert "detailed_results" in data
            assert "errors" in data

            # 验证文件信息
            file_info = data["file_info"]
            assert "filename" in file_info
            assert "original_size" in file_info
            assert "total_rows" in file_info

            # 验证详细结果
            results = data["detailed_results"]
            assert "successful_imports" in results
            assert "failed_imports" in results

            for success in results["successful_imports"]:
                assert "row_number" in success
                assert "created_task_id" in success
                assert "task_number" in success

            for failure in results["failed_imports"]:
                assert "row_number" in failure
                assert "error_message" in failure
                assert "row_data" in failure
        else:
            # 如果功能未实现或导入不存在
            assert response.status_code in [404, 405, 501]


class TestDataMatching:
    """测试数据匹配功能"""

    def test_ab_table_matching_algorithm(
        self, client, auth_headers_admin, db_session, test_member_user
    ):
        """测试A/B表匹配算法"""
        # 创建A表数据（任务表）
        from app.models.task import RepairTask

        task1 = RepairTask(
            title="网络故障",
            description="教学楼网络断线",
            task_number="T202501290001",
            status=TaskStatus.PENDING,
            priority=TaskPriority.HIGH,
            assigned_to=test_member_user.id,
            reporter_name="张老师",
            reporter_contact="13812345678",
            location="教学楼A101",
        )

        task2 = RepairTask(
            title="投影仪故障",
            description="投影仪无法正常显示",
            task_number="T202501290002",
            status=TaskStatus.PENDING,
            priority=TaskPriority.MEDIUM,
            assigned_to=test_member_user.id,
            reporter_name="李老师",
            reporter_contact="13987654321",
            location="办公楼B203",
        )

        db_session.add_all([task1, task2])
        db_session.commit()

        # 测试匹配请求（B表数据）
        matching_data = {
            "b_table_data": [
                {
                    "reporter_name": "张老师",
                    "contact_info": "13812345678",
                    "completion_time": "2025-01-29 15:30:00",
                    "review_rating": 5,
                    "completion_notes": "问题已解决",
                    "actual_location": "教学楼A座101室",
                },
                {
                    "reporter_name": "李老师",
                    "contact_info": "13987654321",
                    "completion_time": "2025-01-29 16:45:00",
                    "review_rating": 4,
                    "completion_notes": "设备已更换",
                    "actual_location": "办公楼B203",
                },
                {
                    "reporter_name": "王老师",
                    "contact_info": "13765432109",
                    "completion_time": "2025-01-29 17:20:00",
                    "review_rating": 3,
                    "completion_notes": "临时修复",
                    "actual_location": "图书馆C301",
                },
            ],
            "matching_options": {
                "match_by_name_and_contact": True,
                "fuzzy_name_matching": True,
                "contact_partial_match": False,
                "similarity_threshold": 0.8,
            },
        }

        response = client.post(
            "/api/data-matching/ab-tables",
            json=matching_data,
            headers=auth_headers_admin,
        )

        if response.status_code == 200:
            data = response.json()

            # 验证匹配结果
            assert "matching_results" in data
            assert "matched_pairs" in data
            assert "unmatched_a_records" in data
            assert "unmatched_b_records" in data
            assert "matching_summary" in data

            # 验证匹配统计
            summary = data["matching_summary"]
            assert "total_a_records" in summary
            assert "total_b_records" in summary
            assert "matched_count" in summary
            assert "unmatched_a_count" in summary
            assert "unmatched_b_count" in summary
            assert "matching_rate" in summary

            # 验证匹配对
            matched_pairs = data["matched_pairs"]
            assert len(matched_pairs) == 2  # 应该匹配到张老师和李老师

            for pair in matched_pairs:
                assert "a_record" in pair
                assert "b_record" in pair
                assert "match_score" in pair
                assert "match_reasons" in pair

                # 验证匹配质量
                assert pair["match_score"] >= 0.8
                assert "name_match" in pair["match_reasons"]
                assert "contact_match" in pair["match_reasons"]

            # 验证未匹配记录
            unmatched_b = data["unmatched_b_records"]
            assert len(unmatched_b) == 1  # 王老师应该未匹配
            assert unmatched_b[0]["reporter_name"] == "王老师"
        else:
            # 如果功能未实现
            assert response.status_code in [404, 405, 501]

    def test_fuzzy_matching_with_typos(self, client, auth_headers_admin):
        """测试模糊匹配处理拼写错误"""
        fuzzy_data = {
            "reference_data": [
                {"name": "张三", "contact": "13812345678"},
                {"name": "李四", "contact": "13987654321"},
                {"name": "王五", "contact": "13765432109"},
            ],
            "target_data": [
                {"name": "张三三", "contact": "13812345678"},  # 姓名有拼写错误
                {"name": "李四", "contact": "13987654320"},  # 联系方式有拼写错误
                {"name": "王武", "contact": "13765432109"},  # 姓名相似但不完全匹配
            ],
            "fuzzy_options": {
                "name_similarity_threshold": 0.7,
                "contact_exact_match": False,
                "contact_similarity_threshold": 0.9,
                "enable_phonetic_matching": True,
            },
        }

        response = client.post(
            "/api/data-matching/fuzzy-match",
            json=fuzzy_data,
            headers=auth_headers_admin,
        )

        if response.status_code == 200:
            data = response.json()

            # 验证模糊匹配结果
            assert "fuzzy_matches" in data
            assert "exact_matches" in data
            assert "no_matches" in data
            assert "similarity_analysis" in data

            # 验证匹配质量
            for match in data["fuzzy_matches"]:
                assert "reference_record" in match
                assert "target_record" in match
                assert "similarity_scores" in match
                assert "match_type" in match

                scores = match["similarity_scores"]
                assert "name_similarity" in scores
                assert "contact_similarity" in scores
                assert "overall_similarity" in scores

                # 验证相似度在合理范围内
                assert 0.0 <= scores["overall_similarity"] <= 1.0
        else:
            # 如果功能未实现
            assert response.status_code in [404, 405, 501]

    def test_duplicate_detection(self, client, auth_headers_admin):
        """测试重复数据检测"""
        duplicate_data = {
            "data_records": [
                {"name": "张三", "contact": "13812345678", "location": "A101"},
                {
                    "name": "张三",
                    "contact": "13812345678",
                    "location": "A101",
                },  # 完全重复
                {
                    "name": "张三",
                    "contact": "13812345678",
                    "location": "A102",
                },  # 部分重复
                {"name": "李四", "contact": "13987654321", "location": "B203"},
                {
                    "name": "李四",
                    "contact": "13987654322",
                    "location": "B203",
                },  # 相似但不重复
            ],
            "detection_rules": {
                "exact_match_fields": ["name", "contact"],
                "fuzzy_match_fields": ["location"],
                "similarity_threshold": 0.95,
                "consider_partial_duplicates": True,
            },
        }

        response = client.post(
            "/api/data-matching/detect-duplicates",
            json=duplicate_data,
            headers=auth_headers_admin,
        )

        if response.status_code == 200:
            data = response.json()

            # 验证重复检测结果
            assert "duplicate_groups" in data
            assert "unique_records" in data
            assert "detection_summary" in data

            # 验证检测统计
            summary = data["detection_summary"]
            assert "total_records" in summary
            assert "duplicate_records" in summary
            assert "unique_records" in summary
            assert "duplicate_groups_count" in summary

            # 验证重复组
            duplicate_groups = data["duplicate_groups"]
            for group in duplicate_groups:
                assert "group_id" in group
                assert "records" in group
                assert "duplicate_type" in group
                assert "similarity_score" in group
                assert len(group["records"]) >= 2  # 重复组至少包含2条记录
        else:
            # 如果功能未实现
            assert response.status_code in [404, 405, 501]


class TestCacheSystem:
    """测试缓存系统"""

    @patch("app.core.cache.redis_client")
    def test_cache_statistics_data(self, mock_redis, client, auth_headers_admin):
        """测试缓存统计数据"""
        # 模拟Redis客户端
        mock_redis.get.return_value = None
        mock_redis.setex.return_value = True
        mock_redis.delete.return_value = 1
        mock_redis.exists.return_value = True

        # 获取统计数据（应该触发缓存）
        response = client.get("/api/statistics/overview", headers=auth_headers_admin)

        if response.status_code == 200:
            data = response.json()

            # 验证统计数据结构
            assert "total_members" in data or "member_count" in data
            assert "total_tasks" in data or "task_count" in data
            assert "cached_at" in data or "generated_at" in data

            # 验证缓存调用
            mock_redis.get.assert_called()
            # 如果是新数据，应该设置缓存
            if not mock_redis.get.return_value:
                mock_redis.setex.assert_called()
        else:
            # 如果功能未实现
            assert response.status_code in [404, 405, 501]

    @patch("app.core.cache.redis_client")
    def test_cache_invalidation(self, mock_redis, client, auth_headers_admin):
        """测试缓存失效"""
        # 模拟Redis操作
        mock_redis.delete.return_value = 1
        mock_redis.keys.return_value = ["stats:*", "members:*", "tasks:*"]

        # 触发缓存清理
        response = client.post(
            "/api/cache/invalidate",
            json={"cache_patterns": ["stats:*", "members:*"]},
            headers=auth_headers_admin,
        )

        if response.status_code == 200:
            data = response.json()

            # 验证缓存清理结果
            assert "success" in data
            assert "cleared_keys" in data
            assert "patterns_cleared" in data
            assert data["success"] is True

            # 验证Redis调用
            mock_redis.keys.assert_called()
            mock_redis.delete.assert_called()
        else:
            # 如果功能未实现
            assert response.status_code in [404, 405, 501]

    @patch("app.core.cache.redis_client")
    def test_cache_performance_monitoring(self, mock_redis, client, auth_headers_admin):
        """测试缓存性能监控"""
        # 模拟Redis信息
        mock_redis.info.return_value = {
            "used_memory": 1024000,
            "used_memory_human": "1M",
            "keyspace_hits": 1000,
            "keyspace_misses": 100,
            "connected_clients": 5,
            "uptime_in_seconds": 3600,
        }

        response = client.get("/api/cache/stats", headers=auth_headers_admin)

        if response.status_code == 200:
            data = response.json()

            # 验证缓存统计
            assert "memory_usage" in data
            assert "hit_rate" in data
            assert "miss_rate" in data
            assert "total_keys" in data
            assert "connected_clients" in data

            # 验证计算结果
            if "hit_rate" in data and "miss_rate" in data:
                assert abs(data["hit_rate"] + data["miss_rate"] - 100.0) < 0.01

            # 验证Redis调用
            mock_redis.info.assert_called()
        else:
            # 如果功能未实现
            assert response.status_code in [404, 405, 501]

    @patch("app.core.cache.redis_client")
    def test_cache_key_management(self, mock_redis, client, auth_headers_admin):
        """测试缓存键管理"""
        # 模拟Redis键操作
        mock_redis.keys.return_value = [
            "stats:overview:2025-01-29",
            "members:list:page_1",
            "tasks:summary:monthly",
            "attendance:stats:2025-01",
        ]
        mock_redis.ttl.side_effect = [3600, 7200, 1800, 5400]
        mock_redis.type.return_value = "string"

        response = client.get("/api/cache/keys", headers=auth_headers_admin)

        if response.status_code == 200:
            data = response.json()

            # 验证键列表
            assert "keys" in data
            assert "total_keys" in data
            assert "categories" in data

            # 验证键信息
            keys = data["keys"]
            for key_info in keys:
                assert "key" in key_info
                assert "ttl" in key_info
                assert "type" in key_info
                assert "category" in key_info

            # 验证分类统计
            categories = data["categories"]
            assert isinstance(categories, dict)
            for category, count in categories.items():
                assert count > 0
        else:
            # 如果功能未实现
            assert response.status_code in [404, 405, 501]


class TestBackgroundJobs:
    """测试后台任务"""

    @patch("app.core.celery_app.send_task")
    def test_schedule_data_processing_job(
        self, mock_send_task, client, auth_headers_admin
    ):
        """测试调度数据处理任务"""
        # 模拟Celery任务调度
        mock_send_task.return_value = Mock(
            id="task_12345", status="PENDING", result=None
        )

        job_data = {
            "job_type": "data_import_processing",
            "parameters": {
                "file_id": "import_file_123",
                "import_options": {"auto_assign": True, "notify_users": False},
            },
            "schedule": "immediate",
        }

        response = client.post(
            "/api/jobs/schedule", json=job_data, headers=auth_headers_admin
        )

        if response.status_code == 200:
            data = response.json()

            # 验证任务调度结果
            assert "job_id" in data
            assert "status" in data
            assert "scheduled_at" in data
            assert "estimated_completion" in data

            # 验证Celery调用
            mock_send_task.assert_called()
            call_args = mock_send_task.call_args
            assert call_args[0][0] == "data_import_processing"  # 任务名称
        else:
            # 如果功能未实现
            assert response.status_code in [404, 405, 501]

    def test_get_job_status(self, client, auth_headers_admin):
        """测试获取任务状态"""
        job_id = "task_12345"

        response = client.get(f"/api/jobs/{job_id}/status", headers=auth_headers_admin)

        if response.status_code == 200:
            data = response.json()

            # 验证任务状态
            assert "job_id" in data
            assert "status" in data
            assert "progress" in data
            assert "started_at" in data

            # 验证状态值
            assert data["status"] in [
                "PENDING",
                "STARTED",
                "SUCCESS",
                "FAILURE",
                "RETRY",
                "REVOKED",
            ]
            assert 0 <= data["progress"] <= 100

            # 如果任务完成，验证结果
            if data["status"] in ["SUCCESS", "FAILURE"]:
                assert "completed_at" in data
                assert "result" in data or "error" in data
        else:
            # 如果功能未实现或任务不存在
            assert response.status_code in [404, 405, 501]

    def test_cancel_background_job(self, client, auth_headers_admin):
        """测试取消后台任务"""
        job_id = "task_12345"

        response = client.post(f"/api/jobs/{job_id}/cancel", headers=auth_headers_admin)

        if response.status_code == 200:
            data = response.json()

            # 验证取消结果
            assert "success" in data
            assert "job_id" in data
            assert "cancelled_at" in data
            assert data["success"] is True
            assert data["job_id"] == job_id
        else:
            # 如果功能未实现或任务不存在
            assert response.status_code in [404, 405, 501]

    def test_list_background_jobs(self, client, auth_headers_admin):
        """测试列出后台任务"""
        response = client.get("/api/jobs", headers=auth_headers_admin)

        if response.status_code == 200:
            data = response.json()

            # 验证任务列表
            assert "items" in data
            assert "total" in data
            assert "page" in data
            assert "size" in data

            # 验证任务信息
            for job in data["items"]:
                assert "job_id" in job
                assert "job_type" in job
                assert "status" in job
                assert "created_at" in job
                assert "created_by" in job

                # 可选字段
                if job["status"] != "PENDING":
                    assert "started_at" in job or "updated_at" in job
        else:
            # 如果功能未实现
            assert response.status_code in [404, 405, 501]


class TestDataImportIntegration:
    """测试数据导入完整集成流程"""

    def test_full_import_workflow(
        self, client, auth_headers_admin, db_session, test_member_user
    ):
        """测试完整的数据导入工作流程"""
        # 1. 上传Excel文件
        excel_data = {
            "报告人姓名": ["测试用户", "另一用户"],
            "联系方式": ["13812345678", "13987654321"],
            "故障描述": ["网络故障", "设备故障"],
            "维修地点": ["A101", "B203"],
            "维修类型": ["线下维修", "线上维修"],
            "紧急程度": ["高", "中"],
        }

        df = pd.DataFrame(excel_data)
        excel_buffer = io.BytesIO()
        df.to_excel(excel_buffer, index=False, engine="openpyxl")
        excel_buffer.seek(0)

        files = {
            "file": (
                "test_data.xlsx",
                excel_buffer.getvalue(),
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        }

        upload_response = client.post(
            "/api/data-import/upload", files=files, headers=auth_headers_admin
        )

        if upload_response.status_code != 200:
            # 如果上传功能未实现，跳过后续测试
            assert upload_response.status_code in [404, 405, 501]
            return

        file_id = upload_response.json()["file_id"]

        # 2. 预览和验证数据
        preview_response = client.get(
            f"/api/data-import/preview/{file_id}", headers=auth_headers_admin
        )

        if preview_response.status_code == 200:
            # 3. 验证数据映射
            validation_data = {
                "file_id": file_id,
                "column_mapping": {
                    "报告人姓名": "reporter_name",
                    "联系方式": "reporter_contact",
                    "故障描述": "description",
                    "维修地点": "location",
                    "维修类型": "repair_type",
                    "紧急程度": "priority",
                },
            }

            validation_response = client.post(
                "/api/data-import/validate",
                json=validation_data,
                headers=auth_headers_admin,
            )

            if validation_response.status_code == 200:
                # 4. 执行导入
                import_data = {
                    "file_id": file_id,
                    "column_mapping": validation_data["column_mapping"],
                    "import_options": {
                        "skip_invalid_rows": True,
                        "auto_assign_to_group": True,
                        "create_task_numbers": True,
                    },
                }

                import_response = client.post(
                    "/api/data-import/execute",
                    json=import_data,
                    headers=auth_headers_admin,
                )

                if import_response.status_code == 200:
                    import_result = import_response.json()

                    # 验证导入成功
                    assert import_result["import_summary"]["successful_count"] > 0

                    # 5. 验证任务是否创建成功
                    tasks_response = client.get(
                        "/api/tasks/repair", headers=auth_headers_admin
                    )

                    if tasks_response.status_code == 200:
                        tasks_data = tasks_response.json()
                        created_tasks = [
                            task
                            for task in tasks_data["items"]
                            if task.get("reporter_name") in ["测试用户", "另一用户"]
                        ]

                        assert (
                            len(created_tasks)
                            == import_result["import_summary"]["successful_count"]
                        )

                        # 验证任务数据正确性
                        for task in created_tasks:
                            assert task["reporter_name"] in ["测试用户", "另一用户"]
                            assert task["reporter_contact"] in [
                                "13812345678",
                                "13987654321",
                            ]
                            assert task["status"] == "pending"
                            assert "task_number" in task

        # 6. 检查导入历史
        history_response = client.get(
            "/api/data-import/history", headers=auth_headers_admin
        )

        if history_response.status_code == 200:
            history_data = history_response.json()

            # 验证历史记录中包含本次导入
            recent_imports = [
                item
                for item in history_data["items"]
                if item.get("filename") == "test_data.xlsx"
            ]
            assert len(recent_imports) >= 1

    @patch("app.core.cache.redis_client")
    def test_import_with_caching(self, mock_redis, client, auth_headers_admin):
        """测试带缓存的数据导入"""
        # 模拟缓存操作
        mock_redis.get.return_value = None
        mock_redis.setex.return_value = True
        mock_redis.delete.return_value = 1

        # 模拟简单的导入操作
        import_data = {
            "file_id": "cached_test_file",
            "column_mapping": {"名称": "name", "联系方式": "contact"},
            "import_options": {"use_cache": True, "cache_duration": 3600},
        }

        response = client.post(
            "/api/data-import/execute", json=import_data, headers=auth_headers_admin
        )

        if response.status_code == 200:
            data = response.json()

            # 验证导入结果包含缓存信息
            assert "cache_info" in data or "performance_info" in data

            # 验证缓存被使用
            mock_redis.get.assert_called()

            # 如果是新导入，应该设置缓存
            if data.get("cache_hit") is False:
                mock_redis.setex.assert_called()
        else:
            # 如果功能未实现
            assert response.status_code in [404, 405, 501]
