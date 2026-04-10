"""Unit tests for inspection-v2/sampling-v2 API endpoints."""

from unittest.mock import AsyncMock, patch

import pytest
from fastapi import HTTPException

from app.api.v1.repair import (
    get_inspection_v2_pending_review,
    get_sampling_v2_pending_review,
    get_workhour_v2_entries,
    review_inspection_v2_application,
    review_sampling_v2_application,
    run_workhour_v2_monthly_settlement,
    submit_inspection_v2_review,
    submit_sampling_v2_review,
)
from app.models.member import Member, UserRole
from app.schemas.repair_workhour import (
    BizReviewSubmitRequest,
    RepairReviewActionRequest,
    WorkhourMonthlySettlementRequest,
)


@pytest.mark.asyncio
class TestInspectionSamplingApiV2:
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

    async def test_submit_inspection_v2_review_success(self):
        db = AsyncMock()
        current_user = self._member(user_id=10, role=UserRole.MEMBER)

        with patch(
            "app.api.v1.repair.InspectionSamplingWorkhourService"
        ) as mock_service_cls:
            mock_service = mock_service_cls.return_value
            mock_service.submit_review = AsyncMock(return_value={"record_id": 1})

            result = await submit_inspection_v2_review(
                record_id=1,
                payload=BizReviewSubmitRequest(note="提交审核"),
                current_user=current_user,
                db=db,
            )

        assert result["success"] is True
        assert result["data"]["record_id"] == 1

    async def test_submit_inspection_v2_review_value_error_maps_404(self):
        db = AsyncMock()
        current_user = self._member(user_id=18, role=UserRole.MEMBER)

        with patch(
            "app.api.v1.repair.InspectionSamplingWorkhourService"
        ) as mock_service_cls:
            mock_service = mock_service_cls.return_value
            mock_service.submit_review = AsyncMock(side_effect=ValueError("巡检记录不存在"))

            with pytest.raises(HTTPException) as exc_info:
                await submit_inspection_v2_review(
                    record_id=999,
                    payload=BizReviewSubmitRequest(note="提交审核"),
                    current_user=current_user,
                    db=db,
                )

        assert exc_info.value.status_code == 404

    async def test_submit_inspection_v2_review_value_error_maps_400(self):
        db = AsyncMock()
        current_user = self._member(user_id=19, role=UserRole.MEMBER)

        with patch(
            "app.api.v1.repair.InspectionSamplingWorkhourService"
        ) as mock_service_cls:
            mock_service = mock_service_cls.return_value
            mock_service.submit_review = AsyncMock(side_effect=ValueError("巡检记录状态非法"))

            with pytest.raises(HTTPException) as exc_info:
                await submit_inspection_v2_review(
                    record_id=1,
                    payload=BizReviewSubmitRequest(note="提交审核"),
                    current_user=current_user,
                    db=db,
                )

        assert exc_info.value.status_code == 400

    async def test_submit_inspection_v2_review_http_exception_passthrough(self):
        db = AsyncMock()
        current_user = self._member(user_id=20, role=UserRole.MEMBER)

        with patch(
            "app.api.v1.repair.InspectionSamplingWorkhourService"
        ) as mock_service_cls:
            mock_service = mock_service_cls.return_value
            mock_service.submit_review = AsyncMock(
                side_effect=HTTPException(status_code=422, detail="请求参数错误")
            )

            with pytest.raises(HTTPException) as exc_info:
                await submit_inspection_v2_review(
                    record_id=1,
                    payload=BizReviewSubmitRequest(note="提交审核"),
                    current_user=current_user,
                    db=db,
                )

        assert exc_info.value.status_code == 422

    async def test_submit_inspection_v2_review_unknown_exception_maps_500(self):
        db = AsyncMock()
        current_user = self._member(user_id=21, role=UserRole.MEMBER)

        with patch(
            "app.api.v1.repair.InspectionSamplingWorkhourService"
        ) as mock_service_cls:
            mock_service = mock_service_cls.return_value
            mock_service.submit_review = AsyncMock(side_effect=RuntimeError("db boom"))

            with pytest.raises(HTTPException) as exc_info:
                await submit_inspection_v2_review(
                    record_id=1,
                    payload=BizReviewSubmitRequest(note="提交审核"),
                    current_user=current_user,
                    db=db,
                )

        assert exc_info.value.status_code == 500

    async def test_submit_sampling_v2_review_success(self):
        db = AsyncMock()
        current_user = self._member(user_id=11, role=UserRole.MEMBER)

        with patch(
            "app.api.v1.repair.InspectionSamplingWorkhourService"
        ) as mock_service_cls:
            mock_service = mock_service_cls.return_value
            mock_service.submit_review = AsyncMock(return_value={"record_id": 2})

            result = await submit_sampling_v2_review(
                record_id=2,
                payload=BizReviewSubmitRequest(note="提交审核"),
                current_user=current_user,
                db=db,
            )

        assert result["success"] is True
        assert result["data"]["record_id"] == 2

    async def test_submit_sampling_v2_review_http_exception_passthrough(self):
        db = AsyncMock()
        current_user = self._member(user_id=22, role=UserRole.MEMBER)

        with patch(
            "app.api.v1.repair.InspectionSamplingWorkhourService"
        ) as mock_service_cls:
            mock_service = mock_service_cls.return_value
            mock_service.submit_review = AsyncMock(
                side_effect=HTTPException(status_code=422, detail="抽检参数错误")
            )

            with pytest.raises(HTTPException) as exc_info:
                await submit_sampling_v2_review(
                    record_id=2,
                    payload=BizReviewSubmitRequest(note="提交审核"),
                    current_user=current_user,
                    db=db,
                )

        assert exc_info.value.status_code == 422

    async def test_review_inspection_v2_permission_denied(self):
        db = AsyncMock()
        current_user = self._member(user_id=12, role=UserRole.MEMBER)

        with pytest.raises(HTTPException) as exc_info:
            await review_inspection_v2_application(
                record_id=3,
                payload=RepairReviewActionRequest(action="approve", note="ok"),
                current_user=current_user,
                db=db,
            )

        assert exc_info.value.status_code == 403

    async def test_review_inspection_v2_value_error_maps_404(self):
        db = AsyncMock()
        current_user = self._member(user_id=23, role=UserRole.GROUP_LEADER)

        with patch(
            "app.api.v1.repair.InspectionSamplingWorkhourService"
        ) as mock_service_cls:
            mock_service = mock_service_cls.return_value
            mock_service.review_application = AsyncMock(side_effect=ValueError("巡检记录不存在"))

            with pytest.raises(HTTPException) as exc_info:
                await review_inspection_v2_application(
                    record_id=3,
                    payload=RepairReviewActionRequest(action="approve", note="ok"),
                    current_user=current_user,
                    db=db,
                )

        assert exc_info.value.status_code == 404

    async def test_review_inspection_v2_http_exception_passthrough(self):
        db = AsyncMock()
        current_user = self._member(user_id=24, role=UserRole.GROUP_LEADER)

        with patch(
            "app.api.v1.repair.InspectionSamplingWorkhourService"
        ) as mock_service_cls:
            mock_service = mock_service_cls.return_value
            mock_service.review_application = AsyncMock(
                side_effect=HTTPException(status_code=422, detail="审批参数错误")
            )

            with pytest.raises(HTTPException) as exc_info:
                await review_inspection_v2_application(
                    record_id=3,
                    payload=RepairReviewActionRequest(action="approve", note="ok"),
                    current_user=current_user,
                    db=db,
                )

        assert exc_info.value.status_code == 422

    async def test_review_inspection_v2_unknown_exception_maps_500(self):
        db = AsyncMock()
        current_user = self._member(user_id=25, role=UserRole.GROUP_LEADER)

        with patch(
            "app.api.v1.repair.InspectionSamplingWorkhourService"
        ) as mock_service_cls:
            mock_service = mock_service_cls.return_value
            mock_service.review_application = AsyncMock(side_effect=RuntimeError("db boom"))

            with pytest.raises(HTTPException) as exc_info:
                await review_inspection_v2_application(
                    record_id=3,
                    payload=RepairReviewActionRequest(action="approve", note="ok"),
                    current_user=current_user,
                    db=db,
                )

        assert exc_info.value.status_code == 500

    async def test_review_sampling_v2_permission_denied(self):
        db = AsyncMock()
        current_user = self._member(user_id=13, role=UserRole.MEMBER)

        with pytest.raises(HTTPException) as exc_info:
            await review_sampling_v2_application(
                record_id=4,
                payload=RepairReviewActionRequest(action="approve", note="ok"),
                current_user=current_user,
                db=db,
            )

        assert exc_info.value.status_code == 403

    async def test_review_sampling_v2_http_exception_passthrough(self):
        db = AsyncMock()
        current_user = self._member(user_id=26, role=UserRole.GROUP_LEADER)

        with patch(
            "app.api.v1.repair.InspectionSamplingWorkhourService"
        ) as mock_service_cls:
            mock_service = mock_service_cls.return_value
            mock_service.review_application = AsyncMock(
                side_effect=HTTPException(status_code=422, detail="审批参数错误")
            )

            with pytest.raises(HTTPException) as exc_info:
                await review_sampling_v2_application(
                    record_id=4,
                    payload=RepairReviewActionRequest(action="approve", note="ok"),
                    current_user=current_user,
                    db=db,
                )

        assert exc_info.value.status_code == 422

    async def test_review_sampling_v2_unknown_exception_maps_500(self):
        db = AsyncMock()
        current_user = self._member(user_id=27, role=UserRole.GROUP_LEADER)

        with patch(
            "app.api.v1.repair.InspectionSamplingWorkhourService"
        ) as mock_service_cls:
            mock_service = mock_service_cls.return_value
            mock_service.review_application = AsyncMock(side_effect=RuntimeError("db boom"))

            with pytest.raises(HTTPException) as exc_info:
                await review_sampling_v2_application(
                    record_id=4,
                    payload=RepairReviewActionRequest(action="approve", note="ok"),
                    current_user=current_user,
                    db=db,
                )

        assert exc_info.value.status_code == 500

    async def test_get_inspection_v2_pending_review_success(self):
        db = AsyncMock()
        current_user = self._member(user_id=14, role=UserRole.GROUP_LEADER)

        with patch(
            "app.api.v1.repair.InspectionSamplingWorkhourService"
        ) as mock_service_cls:
            mock_service = mock_service_cls.return_value
            mock_service.list_pending_reviews = AsyncMock(
                return_value={"items": [{"record_id": 1}], "total": 1, "page": 1, "page_size": 20}
            )

            result = await get_inspection_v2_pending_review(
                page=1,
                pageSize=20,
                current_user=current_user,
                db=db,
            )

        assert result["success"] is True
        assert result["data"]["total"] == 1

    async def test_get_sampling_v2_pending_review_success(self):
        db = AsyncMock()
        current_user = self._member(user_id=15, role=UserRole.GROUP_LEADER)

        with patch(
            "app.api.v1.repair.InspectionSamplingWorkhourService"
        ) as mock_service_cls:
            mock_service = mock_service_cls.return_value
            mock_service.list_pending_reviews = AsyncMock(
                return_value={"items": [{"record_id": 2}], "total": 1, "page": 1, "page_size": 20}
            )

            result = await get_sampling_v2_pending_review(
                page=1,
                pageSize=20,
                current_user=current_user,
                db=db,
            )

        assert result["success"] is True
        assert result["data"]["total"] == 1

    async def test_run_workhour_v2_monthly_settlement_sampling_success(self):
        db = AsyncMock()
        current_user = self._member(user_id=16, role=UserRole.ADMIN)

        with patch(
            "app.api.v1.repair.InspectionSamplingWorkhourService"
        ) as mock_service_cls:
            mock_service = mock_service_cls.return_value
            mock_service.run_monthly_settlement = AsyncMock(
                return_value={"processed": 2, "created": 1, "updated": 1, "dry_run": True}
            )

            result = await run_workhour_v2_monthly_settlement(
                payload=WorkhourMonthlySettlementRequest(
                    year=2026, month=4, biz_type="sampling", dry_run=True
                ),
                current_user=current_user,
                db=db,
            )

        assert result["success"] is True
        assert result["data"]["processed"] == 2

    async def test_get_workhour_v2_entries_sampling_success(self):
        db = AsyncMock()
        current_user = self._member(user_id=17, role=UserRole.GROUP_LEADER)

        with patch(
            "app.api.v1.repair.InspectionSamplingWorkhourService"
        ) as mock_service_cls:
            mock_service = mock_service_cls.return_value
            mock_service.list_workhour_entries = AsyncMock(
                return_value={"items": [{"id": 1}], "total": 1, "page": 1, "page_size": 20}
            )

            result = await get_workhour_v2_entries(
                year=2026,
                month=4,
                bizType="sampling",
                user_id=None,
                page=1,
                pageSize=20,
                current_user=current_user,
                db=db,
            )

        assert result["success"] is True
        assert result["data"]["total"] == 1
