"""
数据导入服务测试用例
测试Excel文件导入、A/B表匹配、数据清洗和验证功能
"""

import io
import os
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List
from unittest.mock import AsyncMock, MagicMock, mock_open, patch

import pandas as pd
import pytest
from fastapi import UploadFile

from app.models.member import Member
from app.models.task import RepairTask, TaskCategory, TaskPriority, TaskStatus, TaskType
from app.services.import_service import DataImportService, ImportResult


class TestImportResult:
    """测试导入结果类"""

    def test_import_result_init(self):
        """测试导入结果初始化"""
        result = ImportResult()

        assert result.success is False
        assert result.total_rows == 0
        assert result.processed_rows == 0
        assert result.created_tasks == 0
        assert result.updated_tasks == 0
        assert result.skipped_rows == 0
        assert result.errors == []
        assert result.warnings == []
        assert result.matched_data == []
        assert result.unmatched_data == []

    def test_import_result_to_dict(self):
        """测试导入结果转换为字典"""
        result = ImportResult()
        result.success = True
        result.total_rows = 100
        result.processed_rows = 95
        result.created_tasks = 80
        result.updated_tasks = 15
        result.skipped_rows = 5
        result.errors = ["错误1", "错误2"]
        result.warnings = ["警告1"]

        result_dict = result.to_dict()

        assert result_dict["success"] is True
        assert result_dict["summary"]["total_rows"] == 100
        assert result_dict["summary"]["processed_rows"] == 95
        assert result_dict["summary"]["created_tasks"] == 80
        assert result_dict["summary"]["updated_tasks"] == 15
        assert result_dict["summary"]["skipped_rows"] == 5
        assert len(result_dict["errors"]) == 2
        assert len(result_dict["warnings"]) == 1


class TestImportServiceInit:
    """测试导入服务初始化"""

    def test_init_with_valid_db_session(self):
        """测试有效数据库会话初始化"""
        mock_db = AsyncMock()
        service = DataImportService(mock_db)

        assert service.db is mock_db
        assert service.ab_matching_service is not None
        assert service.task_service is not None

    def test_init_with_none_db_session(self):
        """测试空数据库会话初始化失败"""
        with pytest.raises(ValueError, match="Database session is required"):
            DataImportService(None)


class TestImportServiceBasic:
    """测试导入服务基础功能"""

    @pytest.fixture
    def mock_db(self):
        """创建模拟数据库会话"""
        return AsyncMock()

    @pytest.fixture
    def service(self, mock_db):
        """创建导入服务实例"""
        return DataImportService(mock_db)

    @pytest.fixture
    def sample_excel_data(self):
        """创建示例Excel数据"""
        return [
            {
                "报修单号": "T001",
                "故障描述": "网络连接问题",
                "报修人": "张三",
                "联系方式": "13800138001",
                "报修时间": "2025-01-01 10:00:00",
                "处理状态": "已完成",
            },
            {
                "报修单号": "T002",
                "故障描述": "打印机故障",
                "报修人": "李四",
                "联系方式": "13900139002",
                "报修时间": "2025-01-02 14:30:00",
                "处理状态": "处理中",
            },
        ]

    @pytest.fixture
    def sample_upload_file(self):
        """创建示例上传文件"""
        # 创建Excel内容
        df = pd.DataFrame(
            [
                {
                    "报修单号": "T001",
                    "故障描述": "网络问题",
                    "报修人": "张三",
                    "联系方式": "13800138001",
                },
                {
                    "报修单号": "T002",
                    "故障描述": "打印机故障",
                    "报修人": "李四",
                    "联系方式": "13900139002",
                },
            ]
        )

        # 将DataFrame转换为Excel字节流
        excel_buffer = io.BytesIO()
        df.to_excel(excel_buffer, index=False)
        excel_buffer.seek(0)

        # 创建UploadFile对象
        upload_file = UploadFile(
            filename="test_data.xlsx",
            file=excel_buffer,
            headers={
                "content-type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            },
        )
        return upload_file


class TestDataCleaning(TestImportServiceBasic):
    """测试数据清洗功能"""

    def test_clean_contact_info_phone(self, service):
        """测试联系方式清理 - 手机号码"""
        # 测试正常手机号
        assert service._clean_contact_info("13800138001") == "13800138001"

        # 测试带空格的手机号
        assert service._clean_contact_info(" 138 0013 8001 ") == "13800138001"

        # 测试带分隔符的手机号
        assert service._clean_contact_info("138-0013-8001") == "13800138001"

        # 测试带国家代码的手机号
        assert service._clean_contact_info("+86 138 0013 8001") == "13800138001"

    def test_clean_contact_info_email(self, service):
        """测试联系方式清理 - 邮箱"""
        # 测试正常邮箱
        assert service._clean_contact_info("user@example.com") == "user@example.com"

        # 测试带空格的邮箱
        assert service._clean_contact_info(" user@example.com ") == "user@example.com"

        # 测试大写邮箱
        assert service._clean_contact_info("USER@EXAMPLE.COM") == "user@example.com"

    def test_clean_contact_info_invalid(self, service):
        """测试无效联系方式清理"""
        # 测试空值
        assert service._clean_contact_info("") == ""
        assert service._clean_contact_info(None) == ""

        # 测试无效格式
        assert (
            service._clean_contact_info("invalid") == "invalid"
        )  # 保持原样但做基础清理

    def test_clean_datetime_valid_formats(self, service):
        """测试有效日期时间格式清理"""
        # 测试标准ISO格式
        result = service._clean_datetime("2025-01-01 10:00:00")
        assert result == "2025-01-01 10:00:00"

        # 测试中文格式
        result = service._clean_datetime("2025年1月1日 10:00")
        assert result is not None

        # 测试日期只有日期部分
        result = service._clean_datetime("2025-01-01")
        assert result is not None

    def test_clean_datetime_invalid_formats(self, service):
        """测试无效日期时间格式清理"""
        # 测试空值
        assert service._clean_datetime("") is None
        assert service._clean_datetime(None) is None

        # 测试无效格式
        assert service._clean_datetime("invalid date") is None
        assert service._clean_datetime("2025-13-40") is None  # 无效的月日

    def test_clean_and_normalize_data_basic(self, service, sample_excel_data):
        """测试基础数据清洗和标准化"""
        cleaned_data = service._clean_and_normalize_data(
            sample_excel_data, table_type="A"
        )

        # 验证数据清洗结果
        assert len(cleaned_data) == 2

        # 验证第一条数据
        first_record = cleaned_data[0]
        assert first_record["task_id"] == "T001"
        assert first_record["reporter_name"] == "张三"
        assert first_record["reporter_contact"] == "13800138001"
        assert first_record["status"] == "已完成"

        # 验证第二条数据
        second_record = cleaned_data[1]
        assert second_record["task_id"] == "T002"
        assert second_record["reporter_name"] == "李四"
        assert second_record["reporter_contact"] == "13900139002"


class TestTableStructureDetection(TestImportServiceBasic):
    """测试表结构检测功能"""

    def test_detect_table_structure_a_table(self, service):
        """测试A表结构检测"""
        a_table_data = [
            {
                "报修单号": "T001",
                "故障描述": "网络问题",
                "报修人": "张三",
                "联系方式": "13800138001",
                "报修时间": "2025-01-01 10:00:00",
            }
        ]

        structure = service._detect_table_structure(a_table_data)

        assert structure["table_type"] == "A"
        assert structure["confidence"] > 0.5
        assert "报修单号" in structure["detected_columns"]
        assert "报修人" in structure["detected_columns"]

    def test_detect_table_structure_b_table(self, service):
        """测试B表结构检测"""
        b_table_data = [
            {
                "姓名": "张三",
                "联系电话": "13800138001",
                "工号": "E001",
                "部门": "网络中心",
                "检修形式": "远程",
            }
        ]

        structure = service._detect_table_structure(b_table_data)

        assert structure["table_type"] == "B"
        assert structure["confidence"] > 0.5
        assert "姓名" in structure["detected_columns"]
        assert "联系电话" in structure["detected_columns"]

    def test_detect_table_structure_unknown(self, service):
        """测试未知表结构检测"""
        unknown_data = [{"随机列1": "值1", "随机列2": "值2", "无关列3": "值3"}]

        structure = service._detect_table_structure(unknown_data)

        assert structure["table_type"] == "UNKNOWN"
        assert structure["confidence"] < 0.5


class TestExcelParsing(TestImportServiceBasic):
    """测试Excel解析功能"""

    @pytest.mark.asyncio
    async def test_parse_excel_data_basic(self, service):
        """测试基础Excel数据解析"""
        # 创建临时Excel文件
        df = pd.DataFrame(
            [
                {"报修单号": "T001", "故障描述": "网络问题", "报修人": "张三"},
                {"报修单号": "T002", "故障描述": "打印机故障", "报修人": "李四"},
            ]
        )

        with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as tmp_file:
            df.to_excel(tmp_file.name, index=False)

            try:
                # 解析Excel文件
                parsed_data = await service._parse_excel_data(tmp_file.name)

                # 验证解析结果
                assert len(parsed_data) == 2
                assert parsed_data[0]["报修单号"] == "T001"
                assert parsed_data[1]["报修单号"] == "T002"

            finally:
                os.unlink(tmp_file.name)

    @pytest.mark.asyncio
    async def test_parse_excel_data_empty_file(self, service):
        """测试解析空Excel文件"""
        # 创建空Excel文件
        df = pd.DataFrame()

        with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as tmp_file:
            df.to_excel(tmp_file.name, index=False)

            try:
                parsed_data = await service._parse_excel_data(tmp_file.name)
                assert len(parsed_data) == 0

            finally:
                os.unlink(tmp_file.name)

    @pytest.mark.asyncio
    async def test_parse_excel_data_invalid_file(self, service):
        """测试解析无效Excel文件"""
        # 创建非Excel文件
        with tempfile.NamedTemporaryFile(
            suffix=".txt", delete=False, mode="w"
        ) as tmp_file:
            tmp_file.write("这不是Excel文件")

            try:
                with pytest.raises(Exception):
                    await service._parse_excel_data(tmp_file.name)

            finally:
                os.unlink(tmp_file.name)


class TestABTableMatching(TestImportServiceBasic):
    """测试A/B表匹配功能"""

    @pytest.fixture
    def sample_a_data(self):
        """示例A表数据"""
        return [
            {
                "task_id": "T001",
                "reporter_name": "张三",
                "reporter_contact": "13800138001",
                "description": "网络问题",
                "report_time": "2025-01-01 10:00:00",
            }
        ]

    @pytest.fixture
    def sample_b_data(self):
        """示例B表数据"""
        return [
            {
                "name": "张三",
                "phone": "13800138001",
                "employee_id": "E001",
                "department": "网络中心",
                "repair_form": "远程",
            }
        ]

    @pytest.mark.asyncio
    async def test_match_ab_tables_basic(
        self, service, mock_db, sample_a_data, sample_b_data
    ):
        """测试基础A/B表匹配"""
        # Mock匹配服务
        with patch.object(service.matching_service, "match_tables") as mock_match:
            mock_match.return_value = {
                "matched_pairs": [
                    {
                        "a_record": sample_a_data[0],
                        "b_record": sample_b_data[0],
                        "confidence": 0.95,
                        "match_key": "张三_13800138001",
                    }
                ],
                "unmatched_a": [],
                "unmatched_b": [],
            }

            result = await service._match_ab_tables(sample_a_data, sample_b_data)

            # 验证匹配结果
            assert len(result["matched_pairs"]) == 1
            assert result["matched_pairs"][0]["confidence"] == 0.95
            assert len(result["unmatched_a"]) == 0
            assert len(result["unmatched_b"]) == 0

    @pytest.mark.asyncio
    async def test_fallback_simple_matching_exact(
        self, service, mock_db, sample_a_data, sample_b_data
    ):
        """测试简单回退匹配 - 精确匹配"""
        result = await service._fallback_simple_matching(sample_a_data, sample_b_data)

        # 验证精确匹配成功
        assert len(result["matched_pairs"]) == 1
        assert result["matched_pairs"][0]["confidence"] == 1.0
        assert result["matched_pairs"][0]["a_record"]["task_id"] == "T001"
        assert result["matched_pairs"][0]["b_record"]["name"] == "张三"

    @pytest.mark.asyncio
    async def test_fallback_simple_matching_no_match(self, service, mock_db):
        """测试简单回退匹配 - 无匹配"""
        a_data = [
            {
                "task_id": "T001",
                "reporter_name": "张三",
                "reporter_contact": "13800138001",
            }
        ]
        b_data = [{"name": "李四", "phone": "13900139002", "employee_id": "E002"}]

        result = await service._fallback_simple_matching(a_data, b_data)

        # 验证无匹配结果
        assert len(result["matched_pairs"]) == 0
        assert len(result["unmatched_a"]) == 1
        assert len(result["unmatched_b"]) == 1

    def test_create_match_key_basic(self, service):
        """测试匹配键创建"""
        key = service._create_match_key("张三", "13800138001")

        # 验证匹配键格式
        assert key == "张三_13800138001"

        # 测试空值处理
        key_empty = service._create_match_key("", "")
        assert key_empty == "_"

    def test_fuzzy_match_member_high_similarity(self, service):
        """测试模糊匹配 - 高相似度"""
        a_record = {"reporter_name": "张三", "reporter_contact": "13800138001"}
        b_records = [
            {"name": "张三", "phone": "13800138001"},  # 完全匹配
            {"name": "张四", "phone": "13900139002"},  # 不匹配
        ]

        match = service._fuzzy_match_member(a_record, b_records, threshold=0.8)

        # 验证高相似度匹配
        assert match is not None
        assert match["b_record"]["name"] == "张三"
        assert match["confidence"] >= 0.8

    def test_fuzzy_match_member_low_similarity(self, service):
        """测试模糊匹配 - 低相似度"""
        a_record = {"reporter_name": "张三", "reporter_contact": "13800138001"}
        b_records = [
            {"name": "王五", "phone": "13700137001"},  # 完全不匹配
            {"name": "赵六", "phone": "13600136002"},  # 完全不匹配
        ]

        match = service._fuzzy_match_member(a_record, b_records, threshold=0.8)

        # 验证无匹配结果
        assert match is None


class TestTaskDataCreation(TestImportServiceBasic):
    """测试任务数据创建功能"""

    def test_create_standardized_task_data_with_match(self, service):
        """测试创建标准化任务数据 - 有匹配"""
        a_record = {
            "task_id": "T001",
            "title": "网络故障",
            "reporter_name": "张三",
            "reporter_contact": "13800138001",
            "report_time": "2025-01-01 10:00:00",
            "status": "已完成",
        }

        b_record = {
            "name": "张三",
            "phone": "13800138001",
            "employee_id": "E001",
            "repair_form": "线下",
        }

        task_data = service._create_standardized_task_data(a_record, b_record)

        # 验证标准化任务数据
        assert task_data["task_id"] == "T001"
        assert task_data["title"] == "网络故障"
        assert task_data["reporter_name"] == "张三"
        assert task_data["reporter_contact"] == "13800138001"
        assert task_data["task_type"] == TaskType.OFFLINE.value  # 根据线下修正
        assert task_data["status"] == TaskStatus.COMPLETED.value  # 根据"已完成"映射
        assert task_data["is_matched"] is True

    def test_create_standardized_task_data_without_match(self, service):
        """测试创建标准化任务数据 - 无匹配"""
        a_record = {
            "task_id": "T002",
            "title": "打印机故障",
            "reporter_name": "李四",
            "reporter_contact": "13900139002",
            "report_time": "2025-01-02 14:30:00",
            "status": "处理中",
        }

        task_data = service._create_standardized_task_data(a_record, None)

        # 验证无匹配的任务数据
        assert task_data["task_id"] == "T002"
        assert task_data["title"] == "打印机故障"
        assert task_data["task_type"] == TaskType.ONLINE.value  # 默认线上
        assert task_data["status"] == TaskStatus.IN_PROGRESS.value  # 根据"处理中"映射
        assert task_data["is_matched"] is False

    def test_extract_field_value_basic(self, service):
        """测试字段值提取"""
        record = {"报修单号": "T001", "任务编号": "TASK001", "ID": "ID001"}

        # 测试按优先级提取
        value = service._extract_field_value(record, ["报修单号", "任务编号", "ID"])
        assert value == "T001"

        # 测试提取不存在的字段
        value = service._extract_field_value(record, ["不存在的字段"])
        assert value == ""

        # 测试空记录
        value = service._extract_field_value({}, ["任何字段"])
        assert value == ""


class TestFullImportWorkflow(TestImportServiceBasic):
    """测试完整导入工作流"""

    @pytest.mark.asyncio
    async def test_import_excel_file_basic(self, service, sample_upload_file, mock_db):
        """测试基础Excel文件导入"""
        # Mock依赖服务
        with (
            patch.object(service, "_parse_excel_data") as mock_parse,
            patch.object(service, "_match_ab_tables") as mock_match,
            patch.object(service.task_service, "create_repair_task") as mock_create,
        ):

            # 设置mock返回值
            mock_parse.return_value = [
                {
                    "task_id": "T001",
                    "title": "网络问题",
                    "reporter_name": "张三",
                    "reporter_contact": "13800138001",
                }
            ]

            mock_match.return_value = {
                "matched_pairs": [],
                "unmatched_a": [{"task_id": "T001", "title": "网络问题"}],
                "unmatched_b": [],
            }

            mock_create.return_value = RepairTask(
                id=1, task_id="T001", title="网络问题"
            )

            # 执行导入
            result = await service.import_excel_file(
                file=sample_upload_file, table_type="A", operator_id=1
            )

            # 验证导入结果
            assert isinstance(result, ImportResult)
            assert result.success is True
            assert result.total_rows == 1
            assert result.created_tasks == 1
            assert len(result.errors) == 0

    @pytest.mark.asyncio
    async def test_import_excel_file_with_errors(
        self, service, sample_upload_file, mock_db
    ):
        """测试带错误的Excel文件导入"""
        with patch.object(service, "_parse_excel_data") as mock_parse:
            # Mock解析失败
            mock_parse.side_effect = Exception("Excel解析失败")

            result = await service.import_excel_file(
                file=sample_upload_file, table_type="A", operator_id=1
            )

            # 验证错误处理
            assert result.success is False
            assert len(result.errors) > 0
            assert "Excel解析失败" in str(result.errors)

    @pytest.mark.asyncio
    async def test_import_excel_file_mixed_results(
        self, service, sample_upload_file, mock_db
    ):
        """测试混合结果的Excel文件导入"""
        with (
            patch.object(service, "_parse_excel_data") as mock_parse,
            patch.object(service, "_match_ab_tables") as mock_match,
            patch.object(service.task_service, "create_repair_task") as mock_create,
        ):

            # 设置部分成功、部分失败的场景
            mock_parse.return_value = [
                {"task_id": "T001", "title": "成功任务"},
                {"task_id": "", "title": "失败任务"},  # 缺少必要字段
            ]

            mock_match.return_value = {
                "matched_pairs": [],
                "unmatched_a": [
                    {"task_id": "T001", "title": "成功任务"},
                    {"task_id": "", "title": "失败任务"},
                ],
                "unmatched_b": [],
            }

            # 第一次调用成功，第二次调用失败
            mock_create.side_effect = [
                RepairTask(id=1, task_id="T001", title="成功任务"),
                Exception("创建任务失败"),
            ]

            result = await service.import_excel_file(
                file=sample_upload_file, table_type="A", operator_id=1
            )

            # 验证混合结果
            assert result.total_rows == 2
            assert result.created_tasks == 1
            assert result.skipped_rows == 1
            assert len(result.errors) > 0
            assert len(result.warnings) >= 0


class TestErrorHandling(TestImportServiceBasic):
    """测试错误处理"""

    @pytest.mark.asyncio
    async def test_file_upload_error(self, service, mock_db):
        """测试文件上传错误"""
        # 创建损坏的上传文件
        corrupted_file = UploadFile(
            filename="corrupted.xlsx",
            file=io.BytesIO(b"corrupted data"),
            headers={
                "content-type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            },
        )

        result = await service.import_excel_file(
            file=corrupted_file, table_type="A", operator_id=1
        )

        # 验证错误处理
        assert result.success is False
        assert len(result.errors) > 0

    @pytest.mark.asyncio
    async def test_database_transaction_error(
        self, service, sample_upload_file, mock_db
    ):
        """测试数据库事务错误"""
        with patch.object(service, "_parse_excel_data") as mock_parse:
            mock_parse.return_value = [{"task_id": "T001", "title": "测试任务"}]

            # Mock数据库提交失败
            mock_db.commit.side_effect = Exception("Database transaction failed")
            mock_db.rollback = AsyncMock()

            result = await service.import_excel_file(
                file=sample_upload_file, table_type="A", operator_id=1
            )

            # 验证事务回滚
            assert result.success is False
            mock_db.rollback.assert_called()

    def test_data_validation_edge_cases(self, service):
        """测试数据验证边界情况"""
        # 测试空数据处理
        cleaned = service._clean_and_normalize_data([], "A")
        assert len(cleaned) == 0

        # 测试包含None值的数据
        data_with_none = [{"task_id": None, "title": None, "reporter_name": "张三"}]
        cleaned = service._clean_and_normalize_data(data_with_none, "A")
        assert len(cleaned) == 1
        assert cleaned[0]["task_id"] == ""  # None转换为空字符串
        assert cleaned[0]["title"] == ""

    @pytest.mark.asyncio
    async def test_memory_efficient_large_file_handling(self, service, mock_db):
        """测试大文件的内存效率处理"""
        # 模拟大量数据
        large_data = [
            {"task_id": f"T{i:06d}", "title": f"任务{i}"} for i in range(1000)
        ]

        with (
            patch.object(service, "_parse_excel_data") as mock_parse,
            patch.object(service, "_match_ab_tables") as mock_match,
            patch.object(service.task_service, "create_repair_task") as mock_create,
        ):

            mock_parse.return_value = large_data
            mock_match.return_value = {
                "matched_pairs": [],
                "unmatched_a": large_data,
                "unmatched_b": [],
            }
            mock_create.return_value = RepairTask(
                id=1, task_id="T000001", title="任务1"
            )

            # 创建简单的上传文件mock
            mock_file = MagicMock()
            mock_file.filename = "large_file.xlsx"

            result = await service.import_excel_file(
                file=mock_file, table_type="A", operator_id=1
            )

            # 验证大文件处理
            assert result.total_rows == 1000
