"""
全新的成员管理模型
完全重构后的成员字段结构
"""

import enum
from datetime import date, datetime
from typing import TYPE_CHECKING, List

from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    Enum,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, relationship

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.attendance import (
        AttendanceException,
        AttendanceRecord,
        MonthlyAttendanceSummary,
    )
    from app.models.task import AssistanceTask, MonitoringTask, RepairTask


class UserRole(enum.Enum):
    """用户角色枚举"""

    ADMIN = "admin"  # 系统管理员
    GROUP_LEADER = "group_leader"  # 组长
    MEMBER = "member"  # 普通成员
    GUEST = "guest"  # 访客


class Member(BaseModel):
    """
    全新的成员模型

    重构后的成员管理，包含完整的员工信息管理功能
    """

    __tablename__ = "members"

    # 基础信息
    username = Column(
        String(50),
        unique=True,
        nullable=False,
        index=True,
        comment="登录用户名（不含特殊字符和中文，可修改）",
    )

    name = Column(
        String(50), nullable=False, index=True, comment="真实姓名（可含中文和·符号）"
    )

    student_id = Column(
        String(20),
        unique=True,
        nullable=True,
        index=True,
        comment="学号/员工号（纯数字，可选）",
    )

    # 联系方式
    phone = Column(String(11), nullable=True, comment="手机号（纯数字，可选）")

    # 组织信息
    department = Column(
        String(100),
        nullable=False,
        default="信息化建设处",
        comment="部门（默认信息化建设处）",
    )

    class_name = Column(String(50), nullable=False, comment="班级（必填）")

    # 时间信息
    join_date = Column(
        Date, nullable=False, default=date.today, comment="入职日期（默认导入时间）"
    )

    # 账户信息
    password_hash = Column(
        String(255), nullable=False, comment="密码哈希（初始密码123456）"
    )

    # 状态和权限
    role = Column(
        Enum(UserRole), default=UserRole.MEMBER, nullable=False, comment="用户角色"
    )

    is_active = Column(
        Boolean,
        default=True,
        nullable=False,
        comment="在职状态（True=在职，False=离职）",
    )

    # 完善信息标识
    profile_completed = Column(
        Boolean,
        default=False,
        nullable=False,
        comment="是否已完善个人信息（首次登录需要完善）",
    )

    is_verified = Column(Boolean, default=False, nullable=False, comment="邮箱验证状态")

    # 登录追踪
    last_login = Column(DateTime, nullable=True, comment="最后登录时间")

    login_count = Column(Integer, default=0, nullable=False, comment="登录次数")

    # 关系定义（暂时保留，实际关系会在相关模块中定义）
    repair_tasks: Mapped[List["RepairTask"]] = relationship(
        "RepairTask",
        back_populates="member",
        cascade="all, delete-orphan",
        lazy="dynamic",
    )

    monitoring_tasks: Mapped[List["MonitoringTask"]] = relationship(
        "MonitoringTask",
        back_populates="member",
        cascade="all, delete-orphan",
        lazy="dynamic",
    )

    assistance_tasks: Mapped[List["AssistanceTask"]] = relationship(
        "AssistanceTask",
        back_populates="member",
        cascade="all, delete-orphan",
        lazy="dynamic",
    )

    attendance_records: Mapped[List["AttendanceRecord"]] = relationship(
        "AttendanceRecord",
        back_populates="member",
        cascade="all, delete-orphan",
        lazy="dynamic",
    )

    attendance_exceptions: Mapped[List["AttendanceException"]] = relationship(
        "AttendanceException",
        back_populates="member",
        foreign_keys="AttendanceException.member_id",
        cascade="all, delete-orphan",
        lazy="dynamic",
    )

    monthly_summaries: Mapped[List["MonthlyAttendanceSummary"]] = relationship(
        "MonthlyAttendanceSummary",
        back_populates="member",
        cascade="all, delete-orphan",
        lazy="dynamic",
    )

    # 约束
    __table_args__ = (
        UniqueConstraint("username", name="uq_member_username"),
        UniqueConstraint("student_id", name="uq_member_student_id"),
        {"comment": "成员信息表（重构版）"},
    )

    def __repr__(self) -> str:
        """字符串表示"""
        return (
            f"<Member(id={self.id}, username='{self.username}', "
            f"name='{self.name}', student_id='{self.student_id}')>"
        )

    @property
    def is_admin(self) -> bool:
        """检查是否为管理员"""
        return self.role == UserRole.ADMIN

    @property
    def is_group_leader(self) -> bool:
        """检查是否为组长"""
        return self.role == UserRole.GROUP_LEADER

    @property
    def can_manage_group(self) -> bool:
        """检查是否可以管理组员"""
        return self.role in [UserRole.ADMIN, UserRole.GROUP_LEADER]

    @property
    def can_import_data(self) -> bool:
        """检查是否可以导入数据"""
        return self.role == UserRole.ADMIN

    @property
    def can_mark_rush_tasks(self) -> bool:
        """检查是否可以标记紧急任务"""
        return self.role == UserRole.ADMIN

    @property
    def status_display(self) -> str:
        """状态显示文本"""
        return "在职" if self.is_active else "离职"

    def get_display_name(self) -> str:
        """获取显示名称"""
        return f"{self.name} ({self.student_id})"

    def get_safe_dict(self) -> dict:
        """获取安全的字典表示（用于API返回）"""
        return {
            "id": self.id,
            "username": self.username,
            "name": self.name,
            "student_id": self.student_id,
            "phone": self.phone,
            "department": self.department,
            "class_name": self.class_name,
            "join_date": (
                self.join_date.isoformat()
                if self.join_date
                else date.today().isoformat()
            ),
            "role": self.role.value,
            "is_active": self.is_active,
            "profile_completed": self.profile_completed,
            "needs_profile_completion": not self.profile_completed,
            "status_display": self.status_display,
            "is_verified": self.is_verified,
            "last_login": self.last_login.isoformat() if self.last_login else None,
            "login_count": self.login_count,
            "created_at": (
                self.created_at.isoformat()
                if self.created_at
                else datetime.utcnow().isoformat()
            ),
            "updated_at": (
                self.updated_at.isoformat()
                if self.updated_at
                else datetime.utcnow().isoformat()
            ),
        }

    def update_login_info(self) -> None:
        """更新登录信息"""
        self.last_login = datetime.utcnow()
        self.login_count += 1
