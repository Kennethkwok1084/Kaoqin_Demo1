"""Unit tests for repair-v2/workhour-v2 API endpoints."""

from __future__ import annotations

from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest
from fastapi import HTTPException

from app.api.v1.repair import (
    bridge_legacy_repair_review,
    bridge_legacy_repair_submit_review,
    execute_ab_table_matching,
    enhanced_import_with_ab_matching,
    get_repair_v2_pending_review,
    import_maintenance_orders,
    get_workhour_v2_entries,
    get_workhour_v2_rules,
    get_workhour_v2_tags,
    review_repair_v2_application,
    run_workhour_v2_monthly_settlement,
    submit_repair_v2_review,
)
from app.models.member import Member, UserRole
from app.models.repair_ticket import RepairTicket
from app.models.workhour_rule import WorkhourRule
from app.models.workhour_tag import WorkhourTag
from app.schemas.repair_workhour import (
    RepairReviewActionRequest,
    RepairReviewSubmitRequest,
    WorkhourMonthlySettlementRequest,
)


class _ScalarsResult:
    def __init__(self, items):
        self._items = items

    def all(self):
        return self._items


class _ExecuteResult:
    def __init__(self, items):
        self._items = items

    def scalars(self):
        return _ScalarsResult(self._items)


@pytest.mark.asyncio
class TestRepairApiV2:
    @staticmethod
    def _member(user_id: int = 1, role: UserRole = UserRole.MEMBER) -> Member:
        return Member(
            id=user_id,
            username=f"u{user_id}",
            name="测试用户",
            student_id=f"S{user_id:03d}",
            role=role,
            is_active=True,
        )

    async def test_submit_repair_v2_review_success(self):
        db = AsyncMock()
        current_user = self._member(user_id=10, role=UserRole.MEMBER)

        with patch("app.api.v1.repair.RepairWorkhourService") as mock_service_cls:
            mock_service = mock_service_cls.return_value
            mock_service.submit_review = AsyncMock(return_value={"application_id": 1})

            result = await submit_repair_v2_review(
                ticket_id=101,
                payload=RepairReviewSubmitRequest(note="提交审核"),
                current_user=current_user,
                db=db,
            )

        assert result["success"] is True
        assert result["data"]["application_id"] == 1

    async def test_submit_repair_v2_review_value_error_maps_404(self):
        db = AsyncMock()
        current_user = self._member(user_id=11, role=UserRole.MEMBER)

        with patch("app.api.v1.repair.RepairWorkhourService") as mock_service_cls:
            mock_service = mock_service_cls.return_value
            mock_service.submit_review = AsyncMock(side_effect=ValueError("报修单不存在"))

            with pytest.raises(HTTPException) as exc_info:
                await submit_repair_v2_review(
                    ticket_id=999,
                    payload=RepairReviewSubmitRequest(note="提交审核"),
                    current_user=current_user,
                    db=db,
                )

        assert exc_info.value.status_code == 404

    async def test_review_repair_v2_application_permission_denied(self):
        db = AsyncMock()
        current_user = self._member(user_id=12, role=UserRole.MEMBER)

        with pytest.raises(HTTPException) as exc_info:
            await review_repair_v2_application(
                ticket_id=101,
                payload=RepairReviewActionRequest(action="approve", note="ok"),
                current_user=current_user,
                db=db,
            )

        assert exc_info.value.status_code == 403

    async def test_review_repair_v2_application_success(self):
        db = AsyncMock()
        current_user = self._member(user_id=13, role=UserRole.GROUP_LEADER)

        with patch("app.api.v1.repair.RepairWorkhourService") as mock_service_cls:
            mock_service = mock_service_cls.return_value
            mock_service.review_application = AsyncMock(return_value={"action": "approve"})

            result = await review_repair_v2_application(
                ticket_id=102,
                payload=RepairReviewActionRequest(action="approve", note="通过"),
                current_user=current_user,
                db=db,
            )

        assert result["success"] is True
        assert result["data"]["action"] == "approve"

    async def test_get_repair_v2_pending_review_success(self):
        db = AsyncMock()
        current_user = self._member(user_id=14, role=UserRole.GROUP_LEADER)

        with patch("app.api.v1.repair.RepairWorkhourService") as mock_service_cls:
            mock_service = mock_service_cls.return_value
            mock_service.list_pending_reviews = AsyncMock(
                return_value={"items": [{"application_id": 1}], "total": 1, "page": 1, "page_size": 20}
            )

            result = await get_repair_v2_pending_review(
                page=1,
                pageSize=20,
                current_user=current_user,
                db=db,
            )

        assert result["success"] is True
        assert result["data"]["total"] == 1

    async def test_run_workhour_v2_monthly_settlement_success(self):
        db = AsyncMock()
        current_user = self._member(user_id=15, role=UserRole.ADMIN)

        with patch("app.api.v1.repair.RepairWorkhourService") as mock_service_cls:
            mock_service = mock_service_cls.return_value
            mock_service.run_monthly_settlement = AsyncMock(
                return_value={"processed": 2, "created": 1, "updated": 1, "dry_run": True}
            )

            result = await run_workhour_v2_monthly_settlement(
                payload=WorkhourMonthlySettlementRequest(year=2026, month=4, dry_run=True),
                current_user=current_user,
                db=db,
            )

        assert result["success"] is True
        assert result["data"]["processed"] == 2

    async def test_get_workhour_v2_rules_success(self):
        db = AsyncMock()
        current_user = self._member(user_id=16, role=UserRole.GROUP_LEADER)
        rule = WorkhourRule(
            id=1,
            rule_code="repair_base",
            rule_name="报修基础工时",
            biz_type="repair",
            formula_desc="固定值",
            formula_json={"type": "fixed", "minutes": 40},
            is_enabled=True,
        )
        db.execute = AsyncMock(return_value=_ExecuteResult([rule]))

        result = await get_workhour_v2_rules(
            biz_type="repair",
            enabled_only=True,
            current_user=current_user,
            db=db,
        )

        assert result["success"] is True
        assert result["data"]["total"] == 1
        assert result["data"]["items"][0]["rule_code"] == "repair_base"

    async def test_get_workhour_v2_tags_success(self):
        db = AsyncMock()
        current_user = self._member(user_id=17, role=UserRole.GROUP_LEADER)
        tag = WorkhourTag(
            id=1,
            tag_code="rush_bonus",
            tag_name="爆单加成",
            tag_type="burst_order",
            bonus_mode="add",
            bonus_value=Decimal("15.00"),
            is_enabled=True,
        )
        db.execute = AsyncMock(return_value=_ExecuteResult([tag]))

        result = await get_workhour_v2_tags(
            enabled_only=True,
            tag_type="burst_order",
            current_user=current_user,
            db=db,
        )

        assert result["success"] is True
        assert result["data"]["total"] == 1
        assert result["data"]["items"][0]["tag_code"] == "rush_bonus"

    async def test_get_workhour_v2_entries_success(self):
        db = AsyncMock()
        current_user = self._member(user_id=18, role=UserRole.GROUP_LEADER)

        with patch("app.api.v1.repair.RepairWorkhourService") as mock_service_cls:
            mock_service = mock_service_cls.return_value
            mock_service.list_workhour_entries = AsyncMock(
                return_value={"items": [{"id": 1}], "total": 1, "page": 1, "page_size": 20}
            )

            result = await get_workhour_v2_entries(
                year=2026,
                month=4,
                user_id=None,
                page=1,
                pageSize=20,
                current_user=current_user,
                db=db,
            )

        assert result["success"] is True
        assert result["data"]["total"] == 1

    async def test_bridge_legacy_repair_submit_review_success(self):
        db = AsyncMock()
        current_user = self._member(user_id=19, role=UserRole.MEMBER)
        ticket = RepairTicket(id=500, ticket_source="online", created_by=19)

        with (
            patch(
                "app.api.v1.repair._ensure_v2_ticket_for_legacy_task",
                new=AsyncMock(return_value=ticket),
            ),
            patch("app.api.v1.repair.RepairWorkhourService") as mock_service_cls,
        ):
            mock_service = mock_service_cls.return_value
            mock_service.submit_review = AsyncMock(return_value={"application_id": 9})

            result = await bridge_legacy_repair_submit_review(
                task_id=123,
                payload=RepairReviewSubmitRequest(note="桥接提交"),
                current_user=current_user,
                db=db,
            )

        assert result["success"] is True
        assert result["data"]["legacy_task_id"] == 123

    async def test_bridge_legacy_repair_submit_review_value_error_maps_400(self):
        db = AsyncMock()
        current_user = self._member(user_id=21, role=UserRole.MEMBER)
        ticket = RepairTicket(id=501, ticket_source="online", created_by=21)

        with (
            patch(
                "app.api.v1.repair._ensure_v2_ticket_for_legacy_task",
                new=AsyncMock(return_value=ticket),
            ),
            patch("app.api.v1.repair.RepairWorkhourService") as mock_service_cls,
        ):
            mock_service = mock_service_cls.return_value
            mock_service.submit_review = AsyncMock(side_effect=ValueError("bad request"))

            with pytest.raises(HTTPException) as exc_info:
                await bridge_legacy_repair_submit_review(
                    task_id=124,
                    payload=RepairReviewSubmitRequest(note="桥接提交"),
                    current_user=current_user,
                    db=db,
                )

        assert exc_info.value.status_code == 400

    async def test_bridge_legacy_repair_submit_review_http_exception_passthrough(self):
        db = AsyncMock()
        current_user = self._member(user_id=22, role=UserRole.MEMBER)

        with patch(
            "app.api.v1.repair._ensure_v2_ticket_for_legacy_task",
            new=AsyncMock(
                side_effect=HTTPException(status_code=404, detail="维修任务不存在")
            ),
        ):
            with pytest.raises(HTTPException) as exc_info:
                await bridge_legacy_repair_submit_review(
                    task_id=404,
                    payload=RepairReviewSubmitRequest(note="桥接提交"),
                    current_user=current_user,
                    db=db,
                )

        assert exc_info.value.status_code == 404

    async def test_bridge_legacy_repair_submit_review_db_exception_maps_500(self):
        db = AsyncMock()
        db.rollback = AsyncMock()
        current_user = self._member(user_id=23, role=UserRole.MEMBER)
        ticket = RepairTicket(id=502, ticket_source="online", created_by=23)

        with (
            patch(
                "app.api.v1.repair._ensure_v2_ticket_for_legacy_task",
                new=AsyncMock(return_value=ticket),
            ),
            patch("app.api.v1.repair.RepairWorkhourService") as mock_service_cls,
        ):
            mock_service = mock_service_cls.return_value
            mock_service.submit_review = AsyncMock(side_effect=RuntimeError("db boom"))

            with pytest.raises(HTTPException) as exc_info:
                await bridge_legacy_repair_submit_review(
                    task_id=125,
                    payload=RepairReviewSubmitRequest(note="桥接提交"),
                    current_user=current_user,
                    db=db,
                )

        assert exc_info.value.status_code == 500
        db.rollback.assert_called_once()

    async def test_bridge_legacy_repair_review_permission_denied(self):
        db = AsyncMock()
        current_user = self._member(user_id=20, role=UserRole.MEMBER)

        with pytest.raises(HTTPException) as exc_info:
            await bridge_legacy_repair_review(
                task_id=123,
                payload=RepairReviewActionRequest(action="approve", note="ok"),
                current_user=current_user,
                db=db,
            )

        assert exc_info.value.status_code == 403

    async def test_bridge_legacy_repair_review_value_error_maps_400(self):
        db = AsyncMock()
        current_user = self._member(user_id=24, role=UserRole.GROUP_LEADER)
        ticket = RepairTicket(id=503, ticket_source="online", created_by=24)

        with (
            patch(
                "app.api.v1.repair._ensure_v2_ticket_for_legacy_task",
                new=AsyncMock(return_value=ticket),
            ),
            patch("app.api.v1.repair.RepairWorkhourService") as mock_service_cls,
        ):
            mock_service = mock_service_cls.return_value
            mock_service.review_application = AsyncMock(side_effect=ValueError("bad review"))

            with pytest.raises(HTTPException) as exc_info:
                await bridge_legacy_repair_review(
                    task_id=126,
                    payload=RepairReviewActionRequest(action="approve", note="ok"),
                    current_user=current_user,
                    db=db,
                )

        assert exc_info.value.status_code == 400

    async def test_enhanced_import_with_ab_matching_executes_real_import_flow(self):
        db = AsyncMock()
        current_user = self._member(user_id=31, role=UserRole.GROUP_LEADER)

        parsed_result = {
            "total_rows": 1,
            "valid_rows": 1,
            "invalid_rows": 0,
            "errors": [],
            "maintenance_orders": [
                {
                    "title": "宿舍网络故障",
                    "reporter_name": "张三",
                    "reporter_contact": "13800001111",
                }
            ],
        }
        import_result = SimpleNamespace(created_tasks=1, updated_tasks=0, errors=[])

        match_result = SimpleNamespace(
            is_matched=True,
            member=SimpleNamespace(id=88, name="处理人A"),
            confidence=0.93,
            confidence_level=SimpleNamespace(value="high"),
            strategy_used=SimpleNamespace(value="exact"),
            failure_reason=None,
        )

        with (
            patch("app.api.v1.repair.DataImportService") as mock_import_service_cls,
            patch(
                "app.services.ab_table_matching_service.ABTableMatchingService"
            ) as mock_match_service_cls,
        ):
            mock_import_service = mock_import_service_cls.return_value
            mock_import_service.parse_maintenance_order_import_rows.return_value = parsed_result
            mock_import_service.bulk_import_tasks = AsyncMock(return_value=import_result)

            mock_match_service = mock_match_service_cls.return_value
            mock_match_service.match_ab_tables = AsyncMock(return_value=[match_result])

            resp = await enhanced_import_with_ab_matching(
                request_data={
                    "a_table_data": [{"标题": "宿舍网络故障", "报修人": "张三"}],
                    "import_batch_id": "batch-001",
                },
                current_user=current_user,
                db=db,
            )

        assert resp["success"] is True
        assert resp["data"]["import_summary"]["successful_imports"] == 1
        assert resp["data"]["import_summary"]["matched_records"] == 1
        assert resp["data"]["batch_id"] == "batch-001"

        bulk_kwargs = mock_import_service.bulk_import_tasks.await_args.kwargs
        assert bulk_kwargs["import_batch_id"] == "batch-001"
        assert bulk_kwargs["task_data_list"][0]["assigned_to"] == 88
        assert bulk_kwargs["task_data_list"][0]["assignee_name"] == "处理人A"

    async def test_enhanced_import_with_ab_matching_dry_run_skips_import(self):
        db = AsyncMock()
        current_user = self._member(user_id=32, role=UserRole.GROUP_LEADER)

        parsed_result = {
            "total_rows": 1,
            "valid_rows": 1,
            "invalid_rows": 0,
            "errors": [],
            "maintenance_orders": [
                {
                    "title": "教室断网",
                    "reporter_name": "李四",
                    "reporter_contact": "13900002222",
                }
            ],
        }

        with patch("app.api.v1.repair.DataImportService") as mock_import_service_cls:
            mock_import_service = mock_import_service_cls.return_value
            mock_import_service.parse_maintenance_order_import_rows.return_value = parsed_result
            mock_import_service.bulk_import_tasks = AsyncMock()

            resp = await enhanced_import_with_ab_matching(
                request_data={
                    "a_table_data": [{"标题": "教室断网", "报修人": "李四"}],
                    "dry_run": True,
                    "enable_ab_matching": False,
                },
                current_user=current_user,
                db=db,
            )

        assert resp["success"] is True
        assert resp["message"] == "增强版导入校验完成"
        assert resp["data"]["import_summary"]["successful_imports"] == 1
        mock_import_service.bulk_import_tasks.assert_not_awaited()

    async def test_enhanced_import_with_ab_matching_rejects_invalid_b_table_data(self):
        db = AsyncMock()
        current_user = self._member(user_id=33, role=UserRole.GROUP_LEADER)

        with pytest.raises(HTTPException) as exc_info:
            await enhanced_import_with_ab_matching(
                request_data={
                    "a_table_data": [{"标题": "教室断网", "报修人": "李四"}],
                    "b_table_data": {"invalid": True},
                },
                current_user=current_user,
                db=db,
            )

        assert exc_info.value.status_code == 500
        assert "增强版数据导入失败" in str(exc_info.value.detail)

    async def test_execute_ab_table_matching_success(self):
        db = AsyncMock()
        current_user = self._member(user_id=34, role=UserRole.GROUP_LEADER)

        match_result = SimpleNamespace(
            a_record={"报修人": "张三"},
            member=SimpleNamespace(id=11, name="处理人A", student_id="S001", department="网维"),
            confidence=0.92,
            confidence_level=SimpleNamespace(value="high"),
            strategy_used=SimpleNamespace(value="exact"),
            is_matched=True,
            failure_reason=None,
            match_details={"name": "exact"},
        )

        with patch("app.services.ab_table_matching_service.ABTableMatchingService") as mock_service_cls:
            mock_service = mock_service_cls.return_value
            mock_service.match_ab_tables = AsyncMock(return_value=[match_result])

            resp = await execute_ab_table_matching(
                request_data={
                    "a_table_data": [{"报修人": "张三"}],
                    "b_table_data": [],
                    "strategies": ["exact"],
                },
                current_user=current_user,
                db=db,
            )

        assert resp["success"] is True
        assert resp["data"]["statistics"]["total_records"] == 1
        assert resp["data"]["statistics"]["matched_records"] == 1

    async def test_import_maintenance_orders_dry_run_success(self):
        db = AsyncMock()
        current_user = self._member(user_id=35, role=UserRole.GROUP_LEADER)

        parsed_result = {
            "total_rows": 1,
            "valid_rows": 1,
            "invalid_rows": 0,
            "empty_rows": 0,
            "errors": [],
            "preview_data": [{"title": "测试任务", "reporter_name": "张三"}],
            "matched_rows": 0,
            "partial_rows": 1,
            "a_table_rows": 1,
            "b_table_rows": 0,
            "maintenance_orders": [{"title": "测试任务", "reporter_name": "张三"}],
        }

        with patch("app.api.v1.repair.DataImportService") as mock_service_cls:
            mock_service = mock_service_cls.return_value
            mock_service.parse_maintenance_order_import_rows.return_value = parsed_result

            resp = await import_maintenance_orders(
                import_data={
                    "maintenance_orders": [{"标题": "测试任务", "报修人": "张三"}],
                    "dry_run": True,
                },
                current_user=current_user,
                db=db,
            )

        assert resp["success"] is True
        assert resp["data"]["valid_rows"] == 1

    async def test_bridge_legacy_repair_review_http_exception_passthrough(self):
        db = AsyncMock()
        current_user = self._member(user_id=25, role=UserRole.ADMIN)

        with patch(
            "app.api.v1.repair._ensure_v2_ticket_for_legacy_task",
            new=AsyncMock(
                side_effect=HTTPException(status_code=404, detail="维修任务不存在")
            ),
        ):
            with pytest.raises(HTTPException) as exc_info:
                await bridge_legacy_repair_review(
                    task_id=127,
                    payload=RepairReviewActionRequest(action="approve", note="ok"),
                    current_user=current_user,
                    db=db,
                )

        assert exc_info.value.status_code == 404

    async def test_bridge_legacy_repair_review_db_exception_maps_500_and_rollback(self):
        db = AsyncMock()
        db.rollback = AsyncMock()
        current_user = self._member(user_id=26, role=UserRole.ADMIN)
        ticket = RepairTicket(id=504, ticket_source="online", created_by=26)

        with (
            patch(
                "app.api.v1.repair._ensure_v2_ticket_for_legacy_task",
                new=AsyncMock(return_value=ticket),
            ),
            patch("app.api.v1.repair.RepairWorkhourService") as mock_service_cls,
        ):
            mock_service = mock_service_cls.return_value
            mock_service.review_application = AsyncMock(side_effect=RuntimeError("db boom"))

            with pytest.raises(HTTPException) as exc_info:
                await bridge_legacy_repair_review(
                    task_id=128,
                    payload=RepairReviewActionRequest(action="approve", note="ok"),
                    current_user=current_user,
                    db=db,
                )

        assert exc_info.value.status_code == 500
        db.rollback.assert_called_once()
