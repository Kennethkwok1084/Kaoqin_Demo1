"""Building and dorm room models aligned with docs SQL baseline."""

from datetime import datetime
from typing import List, Optional

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, Integer, Numeric, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel


class Building(BaseModel):
    """Dormitory building master table."""

    __tablename__ = "building"

    building_code: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        unique=True,
        comment="楼栋编码",
    )
    building_name: Mapped[str] = mapped_column(
        String(128),
        nullable=False,
        comment="楼栋名称",
    )
    campus_name: Mapped[Optional[str]] = mapped_column(
        String(128),
        nullable=True,
        comment="校区名称",
    )
    area_name: Mapped[Optional[str]] = mapped_column(
        String(128),
        nullable=True,
        comment="区域名称",
    )
    longitude: Mapped[Optional[float]] = mapped_column(
        Numeric(10, 6),
        nullable=True,
        comment="经度",
    )
    latitude: Mapped[Optional[float]] = mapped_column(
        Numeric(10, 6),
        nullable=True,
        comment="纬度",
    )
    status: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
        comment="0禁用 1启用",
    )

    dorm_rooms: Mapped[List["DormRoom"]] = relationship(
        "DormRoom",
        back_populates="building",
        lazy="selectin",
    )

    __table_args__ = (
        CheckConstraint("status IN (0,1)", name="ck_building_status"),
    )


class DormRoom(BaseModel):
    """Dormitory room master data with SSID/BSSID target."""

    __tablename__ = "dorm_room"

    building_id: Mapped[int] = mapped_column(
        ForeignKey("building.id", ondelete="RESTRICT"),
        nullable=False,
        comment="楼栋ID",
    )
    room_no: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        comment="房间号",
    )
    floor_no: Mapped[Optional[str]] = mapped_column(
        String(16),
        nullable=True,
        comment="楼层",
    )
    target_ssid: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        default="GCC",
        comment="目标SSID",
    )
    target_bssid: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        comment="目标BSSID",
    )
    dorm_label: Mapped[Optional[str]] = mapped_column(
        String(128),
        nullable=True,
        comment="宿舍标签",
    )
    active_repair_weight: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="当期报修权重",
    )
    last_sampled_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="最近抽检时间",
    )
    status: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
        comment="0禁用 1启用",
    )

    building: Mapped["Building"] = relationship(
        "Building",
        back_populates="dorm_rooms",
        lazy="selectin",
    )

    __table_args__ = (
        UniqueConstraint("building_id", "room_no", name="uq_dorm_room_building_room"),
        CheckConstraint("status IN (0,1)", name="ck_dorm_room_status"),
        Index("idx_dorm_room_building_status", "building_id", "status"),
        Index("idx_dorm_room_last_sampled", "last_sampled_at"),
    )
