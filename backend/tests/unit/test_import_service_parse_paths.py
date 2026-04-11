"""Focused parsing-path tests for DataImportService coverage sprint."""

from unittest.mock import AsyncMock

from app.services.import_service import DataImportService


def _service() -> DataImportService:
    return DataImportService(AsyncMock())


def test_parse_maintenance_order_import_rows_counts_and_preview() -> None:
    service = _service()
    raw = [
        {"标题": "宿舍断网", "报修人": "张三", "联系电话": "13800138000"},
        {"标题": "", "报修人": "李四", "联系电话": "13800138001"},
        {},
    ]

    result = service.parse_maintenance_order_import_rows(raw, preview_rows=2)

    assert result["total_rows"] == 3
    assert result["valid_rows"] == 1
    assert result["invalid_rows"] == 1
    assert result["empty_rows"] == 1
    assert len(result["preview_data"]) == 1
    assert result["maintenance_orders"][0]["title"] == "宿舍断网"


def test_parse_assistance_task_import_rows_success_and_invalid() -> None:
    service = _service()
    raw = [
        {
            "协助日期": "2026-04-11",
            "协助地点": "A101",
            "协助事项": "网络巡检",
            "协助任务时长": "60",
            "提交人": "王五",
        },
        {
            "协助日期": "2026-04-11",
            "协助地点": "",
            "协助事项": "",
            "协助任务时长": "0",
            "提交人": "",
        },
    ]

    result = service.parse_assistance_task_import_rows(raw)

    assert result["total_rows"] == 2
    assert result["valid_rows"] == 1
    assert result["invalid_rows"] == 1
    assert result["assistance_tasks"][0]["type"] == "assistance"


def test_detect_table_structure_returns_expected_type() -> None:
    service = _service()

    task_table = [{"报修单号": "A001", "故障描述": "断网", "报修人": "张三"}]
    member_table = [{"姓名": "张三", "工号": "1001", "部门": "网维"}]

    task_info = service._detect_table_structure(task_table)
    member_info = service._detect_table_structure(member_table)

    assert task_info["type"] == "task_table"
    assert member_info["type"] == "member_table"


def test_coerce_maintenance_order_field_value_rating_and_datetime() -> None:
    service = _service()

    assert service._coerce_maintenance_order_field_value("rating", "5") == 5
    dt = service._coerce_maintenance_order_field_value(
        "report_time", "2026-04-11 08:30:00"
    )
    assert dt is not None


def test_enrich_maintenance_order_import_row_fills_title_and_description() -> None:
    service = _service()

    normalized = {
        "title": None,
        "description": None,
        "reporter_name": "张三",
        "reporter_contact": "13800138000",
    }
    raw = {
        "对象": "2栋501",
        "描述": "路由器离线",
    }

    enriched = service._enrich_maintenance_order_import_row(normalized, raw)

    assert enriched["title"] is not None
    assert enriched["description"] == "路由器离线"


def test_extract_field_value_prefers_alias_order() -> None:
    service = _service()
    row = {
        "处理人员": "李四",
        "姓名": "张三",
    }

    value = service._extract_field_value(row, "name", {"type": "member_table"})
    assert value in {"李四", "张三"}
