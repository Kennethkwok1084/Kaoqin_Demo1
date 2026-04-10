"""Schemas for repair review workflow and workhour settlement."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class RepairReviewSubmitRequest(BaseModel):
    """Request payload for submitting a repair ticket into review queue."""

    import_repair_row_id: int | None = Field(
        default=None,
        description="关联导入行ID，未传则尝试使用repair_ticket.matched_import_row_id",
    )
    note: str | None = Field(default=None, max_length=500, description="提交备注")
    assignee_user_id: int | None = Field(
        default=None,
        ge=1,
        description="待办指派人，未传则进入公共待办池",
    )
    priority_level: int = Field(default=2, ge=1, le=4, description="待办优先级")


class RepairReviewActionRequest(BaseModel):
    """Request payload for approving or rejecting review."""

    action: str = Field(description="审批动作: approve/reject")
    note: str | None = Field(default=None, max_length=500, description="审批备注")

    model_config = ConfigDict(
        json_schema_extra={"example": {"action": "approve", "note": "信息完整，同意入账"}}
    )


class BizReviewSubmitRequest(BaseModel):
    """Request payload for inspection/sampling review submission."""

    note: str | None = Field(default=None, max_length=500, description="提交备注")
    assignee_user_id: int | None = Field(
        default=None,
        ge=1,
        description="待办指派人，未传则进入公共待办池",
    )
    priority_level: int = Field(default=2, ge=1, le=4, description="待办优先级")


class WorkhourMonthlySettlementRequest(BaseModel):
    """Request payload for monthly workhour settlement."""

    year: int = Field(ge=2000, le=2100, description="结算年份")
    month: int = Field(ge=1, le=12, description="结算月份")
    biz_type: Literal["repair", "inspection", "sampling"] = Field(
        default="repair", description="业务类型"
    )
    user_id: int | None = Field(default=None, ge=1, description="仅结算指定用户")
    dry_run: bool = Field(default=False, description="仅预演，不落库")


class WorkhourEntryQueryRequest(BaseModel):
    """Query request for listing workhour entries."""

    year: int = Field(ge=2000, le=2100, description="查询年份")
    month: int = Field(ge=1, le=12, description="查询月份")
    biz_type: Literal["repair", "inspection", "sampling"] = Field(
        default="repair", description="业务类型"
    )
    user_id: int | None = Field(default=None, ge=1, description="按用户筛选")
    page: int = Field(default=1, ge=1, description="页码")
    page_size: int = Field(default=20, ge=1, le=200, description="每页大小")
