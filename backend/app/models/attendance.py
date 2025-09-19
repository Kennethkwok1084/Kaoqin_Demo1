"""考勤相關資料庫模型定義。"""

from __future__ import annotations

import enum
from datetime import date, datetime
from typing import TYPE_CHECKING, Any, Dict, Optional

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Enum as SAEnum,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, reconstructor, relationship

from app.models.base import BaseModel

if TYPE_CHECKING:  # pragma: no cover
    from app.models.member import Member


def _safe_float(value: Optional[Any]) -> float:
    """將任意可能為 None/Decimal 的值穩定轉為 float。"""
    try:
        if value is None:
            return 0.0
        return float(value)
    except (TypeError, ValueError):
        return 0.0


class AttendanceExceptionStatus(str, enum.Enum):
    """考勤異常申請狀態。"""

    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class AttendanceRecord(BaseModel):
    """員工每日考勤記錄。"""

    __tablename__ = "attendance_records"

    member_id: Mapped[int] = mapped_column(
        ForeignKey("members.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="成員ID",
    )
    attendance_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        index=True,
        comment="考勤日期",
    )
    checkin_time: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True,
        comment="簽到時間",
    )
    checkout_time: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True,
        comment="簽退時間",
    )
    work_hours: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
        default=0.0,
        comment="工作時長（小時）",
    )
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="未簽到",
        comment="考勤狀態",
    )
    location: Mapped[Optional[str]] = mapped_column(
        String(200), nullable=True, comment="考勤地點"
    )
    notes: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="備註"
    )
    is_late_checkin: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, comment="是否遲到"
    )
    late_checkin_minutes: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True, comment="遲到分鐘"
    )
    is_early_checkout: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, comment="是否早退"
    )
    early_checkout_minutes: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True, comment="早退分鐘"
    )

    member: Mapped["Member"] = relationship(
        "Member",
        lazy="joined",
        foreign_keys=[member_id],
    )

    __table_args__ = (
        UniqueConstraint(
            "member_id", "attendance_date", name="uq_attendance_member_date"
        ),
        Index("idx_attendance_date_member", "attendance_date", "member_id"),
    )

    def __repr__(self) -> str:  # pragma: no cover - 方便除錯
        return (
            f"<AttendanceRecord id={self.id} member_id={self.member_id} "
            f"date={self.attendance_date}>"
        )


class AttendanceException(BaseModel):
    """考勤異常申請記錄。"""

    __tablename__ = "attendance_exceptions"

    member_id: Mapped[int] = mapped_column(
        ForeignKey("members.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="申請成員ID",
    )
    exception_type: Mapped[str] = mapped_column(
        String(50), nullable=False, comment="異常類型"
    )
    exception_date: Mapped[date] = mapped_column(
        Date, nullable=False, index=True, comment="異常日期"
    )
    reason: Mapped[str] = mapped_column(
        Text, nullable=False, comment="申請理由"
    )
    supporting_documents: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="佐證材料"
    )
    status: Mapped[AttendanceExceptionStatus] = mapped_column(
        SAEnum(
            AttendanceExceptionStatus,
            name="attendanceexceptionstatus",
            create_type=False,
        ),
        nullable=False,
        default=AttendanceExceptionStatus.PENDING,
        comment="審核狀態",
    )
    applied_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        comment="提交時間",
    )
    reviewer_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("members.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="審核人ID",
    )
    reviewer_comments: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="審核意見"
    )
    reviewed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True, comment="審核時間"
    )

    member: Mapped["Member"] = relationship(
        "Member",
        foreign_keys=[member_id],
        lazy="joined",
    )
    reviewer: Mapped[Optional["Member"]] = relationship(
        "Member",
        foreign_keys=[reviewer_id],
        lazy="joined",
    )

    __table_args__ = (
        Index("idx_exception_member_date", "member_id", "exception_date"),
        Index("idx_exception_status_date", "status", "applied_at"),
    )

    def __repr__(self) -> str:  # pragma: no cover - 方便除錯
        return (
            f"<AttendanceException id={self.id} member_id={self.member_id} "
            f"date={self.exception_date} status={self.status}>"
        )


class MonthlyAttendanceSummary(BaseModel):
    """月度工時與考勤匯總。"""

    __tablename__ = "monthly_attendance_summaries"

    member_id: Mapped[int] = mapped_column(
        ForeignKey("members.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="成員ID",
    )
    year: Mapped[int] = mapped_column(Integer, nullable=False, comment="年份")
    month: Mapped[int] = mapped_column(Integer, nullable=False, comment="月份")

    repair_task_hours: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True, default=0.0, comment="報修任務工時"
    )
    monitoring_hours: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True, default=0.0, comment="監控任務工時"
    )
    assistance_hours: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True, default=0.0, comment="協助任務工時"
    )
    carried_hours: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True, default=0.0, comment="上月結轉工時"
    )
    total_hours: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True, default=0.0, comment="實際總工時"
    )
    remaining_hours: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True, default=0.0, comment="可結轉剩餘工時"
    )
    online_repair_hours: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True, default=0.0, comment="線上報修工時"
    )
    offline_repair_hours: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True, default=0.0, comment="線下報修工時"
    )
    rush_task_hours: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True, default=0.0, comment="爆單任務加成"
    )
    positive_review_hours: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True, default=0.0, comment="好評獎勵工時"
    )
    penalty_hours: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True, default=0.0, comment="懲罰扣時"
    )
    late_response_penalty_hours: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True, default=0.0, comment="超時響應扣時"
    )
    late_completion_penalty_hours: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True, default=0.0, comment="超時處理扣時"
    )
    negative_review_penalty_hours: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True, default=0.0, comment="差評扣時"
    )
    total_work_days: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True, default=0, comment="總工作日"
    )
    attended_days: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True, default=0, comment="實際出勤日"
    )
    late_days: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True, default=0, comment="遲到天數"
    )
    early_checkout_days: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True, default=0, comment="早退天數"
    )
    task_completion_count: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True, default=0, comment="完成任務數"
    )
    average_task_rating: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True, default=0.0, comment="平均評分"
    )
    summary_notes: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="匯總備註"
    )

    member: Mapped["Member"] = relationship(
        "Member",
        foreign_keys=[member_id],
        lazy="joined",
    )

    __table_args__ = (
        UniqueConstraint(
            "member_id", "year", "month", name="uq_attendance_summary_member_month"
        ),
        Index("idx_summary_member_year", "member_id", "year"),
        Index("idx_summary_year_month", "year", "month"),
    )

    def __init__(self, *args: Any, created: bool = False, **kwargs: Any) -> None:
        self._extra: Dict[str, Any] = {"created": bool(created)}
        super().__init__(*args, **kwargs)

    @reconstructor
    def _init_on_load(self) -> None:  # pragma: no cover - SQLAlchemy 回載使用
        if not hasattr(self, "_extra"):
            self._extra = {"created": False}
        else:
            self._extra.setdefault("created", False)

    # ------- 輔助屬性與工具方法 -------
    @property
    def month_string(self) -> str:
        return f"{int(self.year):04d}-{int(self.month):02d}"

    def set_created(self, value: bool) -> None:
        self._extra["created"] = bool(value)

    def __getitem__(self, item: str) -> Any:
        if item in self._extra:
            return self._extra[item]
        if hasattr(self, item):
            return getattr(self, item)
        raise KeyError(item)

    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data.update(self._extra)
        data["month_string"] = self.month_string
        return data

    # ------- 業務計算方法 -------
    def apply_carryover_from_previous(
        self, previous: Optional["MonthlyAttendanceSummary"]
    ) -> None:
        prev_remaining = _safe_float(previous.remaining_hours) if previous else 0.0
        previous_carried = _safe_float(self.carried_hours)
        base_total = _safe_float(self.total_hours) - previous_carried

        self.carried_hours = prev_remaining
        self.total_hours = base_total + prev_remaining

    def calculate_carryover_hours(self, standard_hours: float = 30.0) -> float:
        effective_total = _safe_float(self.total_hours)
        remaining = max(0.0, effective_total - float(standard_hours))
        self.remaining_hours = remaining
        return remaining

    def get_carryover_info(self) -> Dict[str, Any]:
        carried = _safe_float(self.carried_hours)
        total = _safe_float(self.total_hours)
        current_hours = max(total - carried, 0.0)
        remaining = _safe_float(self.remaining_hours)

        return {
            "current_month": self.month_string,
            "carried_from_previous": carried,
            "current_month_hours": current_hours,
            "total_effective_hours": total,
            "remaining_for_carryover": remaining,
            "is_eligible_for_carryover": remaining > 0,
            "excess_hours": remaining,
        }

    def __repr__(self) -> str:  # pragma: no cover - 方便除錯
        return (
            f"<MonthlyAttendanceSummary id={self.id} member_id={self.member_id} "
            f"period={self.month_string}>"
        )
