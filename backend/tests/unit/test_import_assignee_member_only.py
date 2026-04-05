from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.services.import_service import DataImportService


def _scalar_one_or_none_result(value):
    result = MagicMock()
    result.scalar_one_or_none.return_value = value
    return result


@pytest.mark.asyncio
async def test_bulk_import_tasks_skips_rows_when_assignee_not_member():
    mock_db = AsyncMock()
    service = DataImportService(mock_db)
    service._find_import_assignee_member = AsyncMock(return_value=None)
    service._create_repair_task_from_import_data = AsyncMock()

    result = await service.bulk_import_tasks(
        task_data_list=[
            {
                "title": "测试工单",
                "reporter_name": "报修人",
                "assignee_name": "外部处理人",
                "work_order_id": "WO-001",
            }
        ],
        importer_id=1,
        import_options={"strict_assignee_member_only": True},
    )

    assert result.created_tasks == 0
    assert result.skipped_rows == 1
    assert "不在已登记成员内" in result.errors[0]
    service._create_repair_task_from_import_data.assert_not_awaited()


@pytest.mark.asyncio
async def test_bulk_import_tasks_imports_rows_when_assignee_is_member():
    mock_db = AsyncMock()
    mock_db.execute.return_value = _scalar_one_or_none_result(None)

    service = DataImportService(mock_db)
    service._find_import_assignee_member = AsyncMock(
        return_value=SimpleNamespace(id=23)
    )
    service._create_repair_task_from_import_data = AsyncMock()

    task_data = {
        "title": "测试工单",
        "reporter_name": "报修人",
        "assignee_name": "已登记成员",
        "work_order_id": "WO-002",
    }

    result = await service.bulk_import_tasks(
        task_data_list=[task_data],
        importer_id=1,
        import_options={"strict_assignee_member_only": True},
    )

    assert result.created_tasks == 1
    assert result.skipped_rows == 0
    assert task_data["assigned_to"] == 23
    service._create_repair_task_from_import_data.assert_awaited_once()
