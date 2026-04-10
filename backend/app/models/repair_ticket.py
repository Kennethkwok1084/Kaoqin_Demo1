"""Repair ticket model aligned with docs SQL baseline."""

from sqlalchemy import CheckConstraint, ForeignKey, Index, Integer, SmallInteger, String, Text, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class RepairTicket(BaseModel):
    """报修单表，兼容线上单和线下单。"""

    __tablename__ = "repair_ticket"

    repair_no: Mapped[str | None] = mapped_column(String(64), nullable=True, comment="报修编号")
    ticket_source: Mapped[str] = mapped_column(String(16), nullable=False, comment="报修来源")
    title: Mapped[str | None] = mapped_column(String(255), nullable=True, comment="标题")
    report_user_name: Mapped[str | None] = mapped_column(
        String(64), nullable=True, comment="报修人"
    )
    report_phone: Mapped[str | None] = mapped_column(
        String(32), nullable=True, comment="报修电话"
    )
    building_id: Mapped[int | None] = mapped_column(
        ForeignKey("building.id", ondelete="SET NULL"),
        nullable=True,
        comment="楼栋ID",
    )
    dorm_room_id: Mapped[int | None] = mapped_column(
        ForeignKey("dorm_room.id", ondelete="SET NULL"),
        nullable=True,
        comment="宿舍ID",
    )
    issue_content: Mapped[str | None] = mapped_column(Text, nullable=True, comment="问题描述")
    issue_category: Mapped[str | None] = mapped_column(
        String(64), nullable=True, comment="问题分类"
    )
    solution_desc: Mapped[str | None] = mapped_column(Text, nullable=True, comment="处理方案")
    solve_status: Mapped[int] = mapped_column(
        SmallInteger,
        nullable=False,
        default=0,
        server_default=text("0"),
        comment="处理状态",
    )
    source_screenshot_id: Mapped[int | None] = mapped_column(
        ForeignKey("media_file.id", ondelete="SET NULL"),
        nullable=True,
        comment="来源截图ID",
    )
    doorplate_image_id: Mapped[int | None] = mapped_column(
        ForeignKey("media_file.id", ondelete="SET NULL"),
        nullable=True,
        comment="门牌图片ID",
    )
    ocr_payload: Mapped[dict | None] = mapped_column(JSONB, nullable=True, comment="OCR数据")
    match_status: Mapped[int] = mapped_column(
        SmallInteger,
        nullable=False,
        default=0,
        server_default=text("0"),
        comment="匹配状态",
    )
    matched_import_row_id: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        comment="匹配导入行ID",
    )
    created_by: Mapped[int] = mapped_column(
        ForeignKey("app_user.id", ondelete="RESTRICT"),
        nullable=False,
        comment="创建人",
    )

    __table_args__ = (
        CheckConstraint(
            "ticket_source IN ('online','offline')",
            name="ck_repair_ticket_source",
        ),
        CheckConstraint("solve_status IN (0,1,2)", name="ck_repair_ticket_solve_status"),
        CheckConstraint("match_status IN (0,1,2,3)", name="ck_repair_ticket_match_status"),
        Index("idx_repair_ticket_no", "repair_no"),
        Index("idx_repair_ticket_source_status", "ticket_source", "match_status", "created_at"),
    )
