import sys
from pathlib import Path
from unittest.mock import AsyncMock

import pytest

sys.path.append(str(Path(__file__).resolve().parents[2]))

from app.services.import_service import DataImportService


@pytest.mark.parametrize("column", ["处理人", "处理人员"])
def test_import_service_extract_member_name_from_handler_column(column):
    service = DataImportService(AsyncMock())
    row = {column: "张三"}
    table_info = {"type": "member_table"}

    assert service._extract_field_value(row, "name", table_info) == "张三"
