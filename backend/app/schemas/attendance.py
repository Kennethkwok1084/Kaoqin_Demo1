"""
考勤相关的Pydantic模式定义
包含考勤记录、异常申请、统计分析的请求和响应模型
"""

from datetime import date, datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class AttendanceExceptionStatus(str, Enum):
    """考勤异常状态枚举"""

    PENDING = "pending"  # 待审核
    APPROVED = "approved"  # 已批准
    REJECTED = "rejected"  # 已拒绝


class ExportFormat(str, Enum):
    """导出格式枚举"""

    EXCEL = "excel"
    CSV = "csv"


# 考勤记录相关schemas


class AttendanceRecordBase(BaseModel):
    """考勤记录基础模型"""

    member_id: int = Field(..., description="成员ID")
    attendance_date: date = Field(..., description="考勤日期")
    location: Optional[str] = Field(None, max_length=200, description="考勤地点")
    notes: Optional[str] = Field(None, description="考勤备注")


class AttendanceRecordCreate(AttendanceRecordBase):
    """创建考勤记录的请求模型"""

    checkin_time: Optional[datetime] = Field(None, description="签到时间")
    checkout_time: Optional[datetime] = Field(None, description="签退时间")


class AttendanceRecordUpdate(BaseModel):
    """更新考勤记录的请求模型"""

    checkin_time: Optional[datetime] = Field(None, description="签到时间")
    checkout_time: Optional[datetime] = Field(None, description="签退时间")
    location: Optional[str] = Field(None, max_length=200, description="考勤地点")
    notes: Optional[str] = Field(None, description="考勤备注")


class AttendanceRecordResponse(AttendanceRecordBase):
    """考勤记录响应模型"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    checkin_time: Optional[datetime]
    checkout_time: Optional[datetime]
    work_hours: float
    status: str
    is_late_checkin: bool
    is_early_checkout: bool
    late_checkin_minutes: Optional[int]
    early_checkout_minutes: Optional[int]
    created_at: datetime
    updated_at: datetime


# 签到签退相关schemas


class AttendanceCheckInRequest(BaseModel):
    """签到请求模型"""

    checkin_time: Optional[datetime] = Field(
        None, description="签到时间，为空则使用当前时间"
    )
    location: Optional[str] = Field(None, max_length=200, description="签到地点")
    notes: Optional[str] = Field(None, description="签到备注")


class AttendanceCheckOutRequest(BaseModel):
    """签退请求模型"""

    checkout_time: Optional[datetime] = Field(
        None, description="签退时间，为空则使用当前时间"
    )
    location: Optional[str] = Field(None, max_length=200, description="签退地点")
    notes: Optional[str] = Field(None, description="签退备注")


class AttendanceCheckInResponse(BaseModel):
    """签到签退响应模型"""

    success: bool
    message: str
    record_id: int
    checkin_time: datetime
    checkout_time: Optional[datetime] = None
    location: Optional[str] = None
    work_hours: Optional[float] = None
    is_late: Optional[bool] = None
    late_minutes: Optional[int] = None
    is_early_checkout: Optional[bool] = None
    early_checkout_minutes: Optional[int] = None


# 考勤异常相关schemas


class AttendanceExceptionBase(BaseModel):
    """考勤异常基础模型"""

    member_id: int = Field(..., description="成员ID")
    exception_type: str = Field(
        ..., max_length=50, description="异常类型（迟到/早退/忘记打卡/请假等）"
    )
    exception_date: date = Field(..., description="异常日期")
    reason: str = Field(..., description="申请理由")


class AttendanceExceptionRequest(AttendanceExceptionBase):
    """考勤异常申请请求模型"""

    supporting_documents: Optional[str] = Field(None, description="支持材料")


class AttendanceExceptionUpdate(BaseModel):
    """考勤异常处理请求模型"""

    status: AttendanceExceptionStatus = Field(..., description="处理结果")
    reviewer_comments: Optional[str] = Field(None, description="审核意见")


class AttendanceExceptionResponse(AttendanceExceptionBase):
    """考勤异常响应模型"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    supporting_documents: Optional[str]
    status: AttendanceExceptionStatus
    applied_at: datetime
    reviewer_id: Optional[int]
    reviewer_comments: Optional[str]
    reviewed_at: Optional[datetime]


# 考勤统计相关schemas


class AttendanceSummaryResponse(BaseModel):
    """月度考勤汇总响应模型"""

    member_id: int
    year: int
    month: int
    total_work_days: int
    expected_work_days: int
    attendance_rate: float
    total_work_hours: float
    average_work_hours: float
    total_late_days: int
    total_early_days: int
    total_late_minutes: int
    total_early_minutes: int
    exception_summary: Dict[str, Dict[str, int]]
    records: List[Dict[str, Any]]


class AttendanceStatisticsResponse(BaseModel):
    """考勤统计响应模型"""

    date_from: date
    date_to: date
    total_records: int
    total_members: int
    total_work_hours: float
    average_work_hours: float
    late_rate: float
    early_checkout_rate: float
    department_statistics: List[Dict[str, Any]]
    exception_statistics: Dict[str, int]


# 批量操作schemas


class BulkAttendanceImportRequest(BaseModel):
    """批量导入考勤记录请求模型"""

    records: List[AttendanceRecordCreate] = Field(..., description="考勤记录列表")

    @field_validator("records")
    @classmethod
    def validate_records_count(
        cls, v: List[AttendanceRecordCreate]
    ) -> List[AttendanceRecordCreate]:
        """验证记录数量"""
        if len(v) > 1000:
            raise ValueError("一次最多导入1000条记录")
        if len(v) == 0:
            raise ValueError("导入记录不能为空")
        return v


class BulkOperationResult(BaseModel):
    """批量操作结果模型"""

    success: bool
    total_records: int
    successful_records: int
    failed_records: int
    errors: List[str]


# 查询参数schemas


class AttendanceQueryParams(BaseModel):
    """考勤查询参数模型"""

    member_id: Optional[int] = None
    date_from: Optional[date] = None
    date_to: Optional[date] = None
    status: Optional[str] = None
    page: int = Field(1, ge=1, description="页码")
    size: int = Field(20, ge=1, le=100, description="每页大小")

    @model_validator(mode="after")
    def validate_date_range(self):
        """验证日期范围"""
        if self.date_from and self.date_to:
            if self.date_to < self.date_from:
                raise ValueError("结束日期不能早于开始日期")

            # 限制查询范围不超过一年
            if (self.date_to - self.date_from).days > 365:
                raise ValueError("查询时间范围不能超过一年")

        return self


class AttendanceExportRequest(BaseModel):
    """考勤数据导出请求模型"""

    date_from: date = Field(..., description="开始日期")
    date_to: date = Field(..., description="结束日期")
    member_ids: Optional[List[int]] = Field(None, description="成员ID列表")
    format: ExportFormat = Field(ExportFormat.EXCEL, description="导出格式")
    include_summary: bool = Field(True, description="是否包含汇总信息")

    @model_validator(mode="after")
    def validate_export_params(self):
        """验证导出参数"""
        if self.date_to < self.date_from:
            raise ValueError("结束日期不能早于开始日期")

        # 限制导出范围不超过一年
        if (self.date_to - self.date_from).days > 365:
            raise ValueError("导出时间范围不能超过一年")

        return self


class AttendanceExportResponse(BaseModel):
    """考勤数据导出响应模型"""

    success: bool
    download_url: str
    filename: str
    file_size: Optional[int] = None
    total_records: int
    expires_at: datetime
