from datetime import datetime
from unittest.mock import AsyncMock

import pytest
from fastapi.responses import JSONResponse

from app.api.v1.repair import _execute_maintenance_order_import
from app.services.import_service import DataImportService, ImportResult


def test_clean_datetime_returns_datetime_instance():
    service = DataImportService(AsyncMock())

    cleaned = service._clean_datetime("2026-02-25 08:58:34")

    assert isinstance(cleaned, datetime)
    assert cleaned == datetime(2026, 2, 25, 8, 58, 34)


@pytest.mark.asyncio
async def test_execute_maintenance_order_import_returns_400_when_all_rows_fail():
    parsed_result = {
        "total_rows": 2,
        "valid_rows": 2,
        "invalid_rows": 0,
        "empty_rows": 0,
        "matched_rows": 0,
        "partial_rows": 2,
        "maintenance_orders": [
            {"title": "工单1", "reporter_name": "报修人1"},
            {"title": "工单2", "reporter_name": "报修人2"},
        ],
        "errors": [],
    }

    import_result = ImportResult()
    import_result.created_tasks = 0
    import_result.updated_tasks = 0
    import_result.skipped_rows = 2
    import_result.errors = ["第1行导入失败", "第2行导入失败"]

    import_service = AsyncMock()
    import_service.bulk_import_tasks.return_value = import_result

    current_user = type("CurrentUser", (), {"id": 1})()

    response = await _execute_maintenance_order_import(
        parsed_result=parsed_result,
        current_user=current_user,
        import_service=import_service,
        dry_run=False,
        skip_duplicates=True,
    )

    assert isinstance(response, JSONResponse)
    assert response.status_code == 400
