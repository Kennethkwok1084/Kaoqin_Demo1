"""Inspection record model aligned with docs SQL baseline."""

from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Integer, SmallInteger, String, Text, UniqueConstraint, func, text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class InspectionRecord(BaseModel):
    """巡检记录表。"""

    __tablename__ = "inspection_record"

    inspection_task_id: Mapped[int] = mapped_column(
        ForeignKey("task_inspection.id", ondelete="CASCADE"),
        nullable=False,
        comment="巡检任务ID",
    )
    inspection_point_id: Mapped[int] = mapped_column(
        ForeignKey("task_inspection_point.id", ondelete="CASCADE"),
        nullable=False,
        comment="巡检点位ID",
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("app_user.id", ondelete="RESTRICT"),
        nullable=False,
        comment="提交人",
    )
    result_status: Mapped[int] = mapped_column(
        SmallInteger,
        nullable=False,
        default=1,
        server_default=text("1"),
        comment="结果状态",
    )
    exception_type: Mapped[str | None] = mapped_column(
        String(64),
        nullable=True,
        comment="异常类型",
    )
    exception_desc: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="异常描述",
    )
    handled_desc: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="处理说明",
    )
    media_image_id: Mapped[int | None] = mapped_column(
        ForeignKey("media_file.id", ondelete="SET NULL"),
        nullable=True,
        comment="图片媒体ID",
    )
    media_video_id: Mapped[int | None] = mapped_column(
        ForeignKey("media_file.id", ondelete="SET NULL"),
        nullable=True,
        comment="视频媒体ID",
    )
    submitted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        comment="提交时间",
    )
    reviewed_by: Mapped[int | None] = mapped_column(
        ForeignKey("app_user.id", ondelete="SET NULL"),
        nullable=True,
        comment="审核人",
    )
    reviewed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="审核时间",
    )
    review_status: Mapped[int] = mapped_column(
        SmallInteger,
        nullable=False,
        default=0,
        server_default=text("0"),
        comment="审核状态",
    )

    __table_args__ = (
        UniqueConstraint(
            "inspection_task_id",
            "inspection_point_id",
            "user_id",
            name="uq_inspection_record_task_point_user",
        ),
        CheckConstraint(
            "result_status IN (1,2,3)",
            name="ck_inspection_record_result",
        ),
        CheckConstraint(
            "review_status IN (0,1,2)",
            name="ck_inspection_record_review",
        ),
    )
