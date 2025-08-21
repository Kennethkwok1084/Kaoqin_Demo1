"""
全新的成员管理Schema
完全重构后的数据验证和序列化
"""

import re
from datetime import date, datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator, model_validator

from app.models.member import UserRole


class MemberBase(BaseModel):
    """成员基础Schema"""

    username: str = Field(..., min_length=3, max_length=50, description="登录用户名")
    name: str = Field(..., min_length=1, max_length=50, description="真实姓名")
    student_id: Optional[str] = Field(
        None, min_length=1, max_length=20, description="学号/员工号（可选）"
    )
    phone: Optional[str] = Field(None, max_length=11, description="手机号")
    department: str = Field(default="信息化建设处", max_length=100, description="部门")
    class_name: str = Field(..., min_length=1, max_length=50, description="班级")
    join_date: Optional[date] = Field(
        default_factory=date.today, description="入职日期"
    )
    role: UserRole = Field(default=UserRole.MEMBER, description="用户角色")
    is_active: bool = Field(default=True, description="在职状态")
    profile_completed: bool = Field(default=False, description="是否已完善个人信息")

    @field_validator("username")
    @classmethod
    def validate_username(cls, v: str) -> str:
        """验证用户名格式"""
        if not re.match(r"^[a-zA-Z0-9_]+$", v):
            raise ValueError("用户名只能包含字母、数字和下划线")
        return v

    @field_validator("student_id")
    @classmethod
    def validate_student_id(cls, v: Optional[str]) -> Optional[str]:
        """验证学号格式"""
        if v is not None and not re.match(r"^[A-Za-z0-9]+$", v):
            raise ValueError("学号只能包含字母和数字")
        return v

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: Optional[str]) -> Optional[str]:
        """验证手机号格式"""
        if v is not None and not re.match(r"^\d{11}$", v):
            raise ValueError("手机号必须为11位数字")
        return v

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """验证姓名格式"""
        # 允许中文、字母、空格和·符号
        if not re.match(r"^[\u4e00-\u9fa5a-zA-Z·\s]+$", v):
            raise ValueError("姓名只能包含中文、字母、空格和·符号")
        return v


class MemberCreate(MemberBase):
    """创建成员Schema"""

    password: str = Field(
        default="123456", min_length=6, max_length=50, description="密码"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "username": "zhangsan",
                "name": "张三",
                "student_id": "2023001",
                "phone": "13800138000",
                "department": "信息化建设处",
                "class_name": "计算机1班",
                "join_date": "2024-01-01",
                "role": "member",
                "is_active": True,
                "password": "123456",
            }
        }


class MemberUpdate(BaseModel):
    """更新成员Schema"""

    username: Optional[str] = Field(
        None, min_length=3, max_length=50, description="登录用户名"
    )
    name: Optional[str] = Field(
        None, min_length=1, max_length=50, description="真实姓名"
    )
    phone: Optional[str] = Field(None, max_length=11, description="手机号")
    department: Optional[str] = Field(None, max_length=100, description="部门")
    class_name: Optional[str] = Field(
        None, min_length=1, max_length=50, description="班级"
    )
    role: Optional[UserRole] = Field(None, description="用户角色")
    is_active: Optional[bool] = Field(None, description="在职状态")
    profile_completed: Optional[bool] = Field(None, description="是否已完善个人信息")

    @field_validator("username")
    @classmethod
    def validate_username(cls, v: Optional[str]) -> Optional[str]:
        """验证用户名格式"""
        if v is not None and not re.match(r"^[a-zA-Z0-9_]+$", v):
            raise ValueError("用户名只能包含字母、数字和下划线")
        return v

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: Optional[str]) -> Optional[str]:
        """验证手机号格式"""
        if v is not None and not re.match(r"^\d{11}$", v):
            raise ValueError("手机号必须为11位数字")
        return v

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: Optional[str]) -> Optional[str]:
        """验证姓名格式"""
        if v is not None and not re.match(r"^[\u4e00-\u9fa5a-zA-Z·\s]+$", v):
            raise ValueError("姓名只能包含中文、字母、空格和·符号")
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "username": "zhangsan_new",
                "name": "张三",
                "phone": "13800138001",
                "department": "信息化建设处",
                "class_name": "计算机2班",
                "role": "member",
                "is_active": True,
            }
        }


class MemberResponse(BaseModel):
    """成员响应Schema"""

    id: int
    username: str
    name: str
    student_id: str
    phone: Optional[str]
    department: str
    class_name: str
    join_date: Optional[date]
    role: str
    is_active: bool
    profile_completed: bool
    status_display: str
    is_verified: bool
    last_login: Optional[datetime]
    login_count: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 1,
                "username": "zhangsan",
                "name": "张三",
                "student_id": "2023001",
                "phone": "13800138000",
                "department": "信息化建设处",
                "class_name": "计算机1班",
                "join_date": "2024-01-01",
                "role": "member",
                "is_active": True,
                "status_display": "在职",
                "is_verified": False,
                "last_login": "2024-01-15T10:30:00",
                "login_count": 5,
                "created_at": "2024-01-01T08:00:00",
                "updated_at": "2024-01-15T10:30:00",
            }
        }


class MemberListResponse(BaseModel):
    """成员列表响应Schema"""

    items: List[MemberResponse]
    total: int
    page: int
    page_size: int
    total_pages: int

    class Config:
        json_schema_extra = {
            "example": {
                "items": [
                    {
                        "id": 1,
                        "username": "zhangsan",
                        "name": "张三",
                        "student_id": "2023001",
                        "phone": "13800138000",
                        "department": "信息化建设处",
                        "class_name": "计算机1班",
                        "join_date": "2024-01-01",
                        "role": "member",
                        "is_active": True,
                        "status_display": "在职",
                        "is_verified": False,
                        "last_login": "2024-01-15T10:30:00",
                        "login_count": 5,
                        "created_at": "2024-01-01T08:00:00",
                        "updated_at": "2024-01-15T10:30:00",
                    }
                ],
                "total": 1,
                "page": 1,
                "page_size": 20,
                "total_pages": 1,
            }
        }


class MemberImportItem(BaseModel):
    """批量导入单个成员Schema"""

    username: Optional[str] = Field(
        default=None, description="用户名（可选，自动生成）"
    )
    name: str = Field(..., description="真实姓名")
    student_id: Optional[str] = Field(default=None, description="学号/员工号（可选）")
    phone: Optional[str] = Field(default=None, description="手机号")
    department: Optional[str] = Field(default="信息化建设处", description="部门")
    class_name: str = Field(..., description="班级")
    role: Optional[str] = Field(default="member", description="角色")

    @field_validator("student_id", mode="before")
    @classmethod
    def validate_student_id(cls, v: Any) -> Optional[str]:
        """验证学号格式"""
        if v is None or v == "" or v == "null" or v == "undefined":
            return None
        if not re.match(r"^[A-Za-z0-9]+$", str(v)):
            raise ValueError("学号只能包含字母和数字")
        return str(v)

    @field_validator("phone", mode="before")
    @classmethod
    def validate_phone(cls, v: Any) -> Optional[str]:
        """验证手机号格式"""
        if v is None or v == "" or v == "null" or v == "undefined":
            return None
        phone_str = str(v).strip()
        if not re.match(r"^1[3-9]\d{9}$", phone_str):
            raise ValueError("手机号必须为11位数字，且以1开头")
        return phone_str

    @field_validator("name", mode="before")
    @classmethod
    def validate_name(cls, v: Any) -> str:
        """验证姓名格式"""
        if not v or not str(v).strip():
            raise ValueError("姓名不能为空")
        name_str = str(v).strip()
        if not re.match(r"^[\u4e00-\u9fa5a-zA-Z·\s]+$", name_str):
            raise ValueError("姓名只能包含中文、字母、·和空格")
        return name_str

    @model_validator(mode="before")
    @classmethod
    def clean_empty_fields(cls, values: Any) -> Any:
        """清理空字段"""
        cleaned: Dict[str, Any] = {}
        for key, value in values.items():
            if value is None or value == "" or value == "null" or value == "undefined":
                if key in ["student_id", "phone", "username"]:
                    cleaned[key] = (
                        ""  # Use empty string instead of None for string fields
                    )
                elif key == "role":
                    cleaned[key] = "member"
                elif key == "department":
                    cleaned[key] = "信息化建设处"
                else:
                    cleaned[key] = value
            else:
                cleaned[key] = value
        return cleaned

    class Config:
        json_schema_extra = {
            "example": {
                "username": "zhangsan",
                "name": "张三",
                "student_id": "2023001",
                "phone": "13800138000",
                "department": "信息化建设处",
                "class_name": "计算机1班",
                "role": "member",
            }
        }


class MemberImportRequest(BaseModel):
    """批量导入请求Schema"""

    members: List[MemberImportItem] = Field(description="成员列表", min_length=1)
    skip_duplicates: bool = Field(default=True, description="是否跳过重复数据")

    class Config:
        json_schema_extra = {
            "example": {
                "members": [
                    {
                        "name": "张三",
                        "student_id": "2023001",
                        "phone": "13800138000",
                        "class_name": "计算机1班",
                    },
                    {
                        "name": "李四",
                        "student_id": "2023002",
                        "class_name": "计算机2班",
                    },
                ],
                "skip_duplicates": True,
            }
        }


class MemberImportResponse(BaseModel):
    """批量导入响应Schema"""

    total_processed: int = Field(..., description="总处理数量")
    successful_imports: int = Field(..., description="成功导入数量")
    failed_imports: int = Field(..., description="失败导入数量")
    skipped_duplicates: int = Field(..., description="跳过重复数量")
    errors: List[str] = Field(default=[], description="错误信息列表")

    class Config:
        json_schema_extra = {
            "example": {
                "total_processed": 2,
                "successful_imports": 2,
                "failed_imports": 0,
                "skipped_duplicates": 0,
                "errors": [],
            }
        }


class PasswordChangeRequest(BaseModel):
    """修改密码请求Schema"""

    old_password: str = Field(..., min_length=6, description="旧密码")
    new_password: str = Field(..., min_length=6, max_length=50, description="新密码")

    class Config:
        json_schema_extra = {
            "example": {"old_password": "123456", "new_password": "newpassword123"}
        }
