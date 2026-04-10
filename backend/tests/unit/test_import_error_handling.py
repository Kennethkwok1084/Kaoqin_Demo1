"""Unit tests for import error handling and degradation semantics."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.import_service import DataImportService


class _ScalarResult:
    def __init__(self, value):
        self._value = value

    def scalar_one_or_none(self):
        return self._value


@pytest.mark.asyncio
class TestImportErrorHandling:
    async def test_match_ab_tables_returns_degraded_marker_when_fallback_used(self):
        db = AsyncMock()
        service = DataImportService(db)

        with (
            patch.object(
                service.ab_matching_service,
                "match_ab_tables",
                side_effect=RuntimeError("matcher unavailable"),
            ),
            patch.object(
                service,
                "_fallback_simple_matching",
                new=AsyncMock(
                    return_value={
                        "matched": [],
                        "unmatched": [{"reporter_name": "张三"}],
                        "degraded": False,
                        "fallback_reason": None,
                    }
                ),
            ),
        ):
            result = await service._match_ab_tables(
                data=[{"reporter_name": "张三", "reporter_contact": "13800138001"}],
                table_info={"type": "task_table"},
            )

        assert result["degraded"] is True
        assert "matcher unavailable" in str(result["fallback_reason"])
        assert len(result["unmatched"]) == 1

    async def test_create_tasks_from_import_collects_row_error_details(self):
        db = AsyncMock()
        db.execute = AsyncMock(return_value=_ScalarResult(None))
        db.commit = AsyncMock()

        service = DataImportService(db)
        service._create_repair_task_from_import_data = AsyncMock(
            side_effect=ValueError("invalid imported row")
        )

        result = await service._create_tasks_from_import(
            validated_data=[
                {
                    "title": "测试任务",
                    "reporter_name": "张三",
                    "reporter_contact": "13800138001",
                    "assigned_to": 1,
                }
            ],
            options={"creator_id": 1},
        )

        assert result["created"] == 0
        assert result["updated"] == 0
        assert result["skipped"] == 1
        assert len(result["errors"]) == 1
        assert result["errors"][0]["row_index"] == 1
        assert result["errors"][0]["error_type"] == "ValueError"
        assert "invalid imported row" in result["errors"][0]["message"]

    async def test_import_excel_file_exposes_creation_errors_and_degradation_warning(self):
        db = AsyncMock()
        service = DataImportService(db)

        mock_file = MagicMock()
        mock_file.filename = "demo.xlsx"

        normalized_row = {
            "title": "测试任务",
            "reporter_name": "李四",
            "reporter_contact": "13900139002",
            "assigned_to": 1,
        }

        with (
            patch.object(service, "_save_temp_file", new=AsyncMock(return_value="/tmp/demo.xlsx")),
            patch.object(service, "_parse_excel_data", new=AsyncMock(return_value=[normalized_row])),
            patch.object(service, "_detect_table_structure", return_value={"type": "task_table"}),
            patch.object(service, "_clean_and_normalize_data", return_value=[normalized_row]),
            patch.object(
                service,
                "_match_ab_tables",
                new=AsyncMock(
                    return_value={
                        "matched": [normalized_row],
                        "unmatched": [],
                        "degraded": True,
                        "fallback_reason": "intelligent matcher timeout",
                    }
                ),
            ),
            patch.object(service, "_validate_import_data", return_value={"errors": [], "warnings": []}),
            patch.object(
                service,
                "_create_tasks_from_import",
                new=AsyncMock(
                    return_value={
                        "created": 0,
                        "updated": 0,
                        "skipped": 1,
                        "errors": [
                            {
                                "row_index": 1,
                                "error_type": "ValueError",
                                "message": "invalid data",
                            }
                        ],
                    }
                ),
            ),
        ):
            result = await service.import_excel_file(
                file=mock_file,
                import_options={"enable_ab_matching": True},
            )

        assert result.success is True
        assert result.processed_rows == 1
        assert result.skipped_rows == 1
        assert any("A/B匹配已降级" in item for item in result.warnings)
        assert any("任务创建失败" in item for item in result.errors)

    async def test_task_exists_db_error_is_must_fail(self):
        db = AsyncMock()
        db.execute = AsyncMock(side_effect=RuntimeError("db down"))
        service = DataImportService(db)

        with pytest.raises(RuntimeError, match="检查任务是否存在失败"):
            await service._task_exists("T001")

    async def test_get_task_by_task_id_db_error_is_must_fail(self):
        db = AsyncMock()
        db.execute = AsyncMock(side_effect=RuntimeError("db down"))
        service = DataImportService(db)

        with pytest.raises(RuntimeError, match="根据任务编号查询任务失败"):
            await service._get_task_by_task_id("T001")

    async def test_resolve_member_id_allow_degrade_to_default_member(self):
        db = AsyncMock()
        db.execute = AsyncMock(return_value=_ScalarResult(None))
        service = DataImportService(db)

        with patch.object(
            service,
            "_resolve_default_member_id",
            new=AsyncMock(return_value=88),
        ):
            member_id = await service._resolve_member_id("未知处理人")

        assert member_id == 88

    async def test_resolve_default_member_id_failure_is_must_fail(self):
        db = AsyncMock()
        service = DataImportService(db)

        with patch.object(
            service,
            "_get_or_create_default_member",
            new=AsyncMock(side_effect=RuntimeError("create default failed")),
        ):
            with pytest.raises(RuntimeError, match="create default failed"):
                await service._resolve_default_member_id()
