"""
成员管理相关的Pydantic模式定义
包含成员创建、更新、查询的请求和响应模型
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, EmailStr, field_validator, model_validator, ConfigDict

from app.models.member import UserRole


class MemberBase(BaseModel):
    """成员基础信息模型"""
    
    name: str = Field(
        ..., 
        min_length=1, 
        max_length=50,
        description="成员姓名"
    )
    student_id: str = Field(
        ..., 
        min_length=1, 
        max_length=20,
        description="学号（唯一标识）"
    )
    group_id: Optional[int] = Field(
        None,
        ge=0,
        description="工作组ID"
    )
    class_name: Optional[str] = Field(
        None, 
        max_length=50,
        description="班级名称"
    )
    email: Optional[EmailStr] = Field(
        None,
        description="邮箱地址"
    )
    
    @field_validator('name')

    
    @classmethod
    def validate_name(cls, v):
        """验证姓名格式"""
        if not v or not v.strip():
            raise ValueError('姓名不能为空')
        
        # 检查是否包含特殊字符
        import re
        if not re.match(r'^[\u4e00-\u9fa5a-zA-Z\s]+$', v.strip()):
            raise ValueError('姓名只能包含中文、英文字母和空格')
        
        return v.strip()
    
    @field_validator('student_id')

    
    @classmethod
    def validate_student_id(cls, v):
        """验证学号格式"""
        if not v or not v.strip():
            raise ValueError('学号不能为空')
        
        # 检查学号格式（数字或字母数字组合）
        import re
        if not re.match(r'^[a-zA-Z0-9]+$', v.strip()):
            raise ValueError('学号只能包含字母和数字')
        
        return v.strip()


class MemberCreate(MemberBase):
    """创建成员的请求模型"""
    
    password: str = Field(
        ..., 
        min_length=8,
        max_length=128,
        description="初始密码"
    )
    role: UserRole = Field(
        default=UserRole.MEMBER,
        description="用户角色"
    )
    dormitory: Optional[str] = Field(
        None, 
        max_length=50,
        description="宿舍信息"
    )
    phone: Optional[str] = Field(
        None, 
        max_length=20,
        description="手机号码"
    )
    is_active: bool = Field(
        default=True,
        description="是否启用"
    )
    is_verified: bool = Field(
        default=False,
        description="是否已验证邮箱"
    )
    
    @field_validator('password')

    
    @classmethod
    def validate_password(cls, v):
        """验证密码强度"""
        from app.core.security import validate_password_strength
        
        is_strong, errors = validate_password_strength(v)
        if not is_strong:
            raise ValueError(f"密码不符合要求: {', '.join(errors)}")
        
        return v
    
    @field_validator('phone')

    
    @classmethod
    def validate_phone(cls, v):
        """验证手机号格式"""
        if not v:
            return v
        
        from app.core.security import validate_phone_format
        if not validate_phone_format(v):
            raise ValueError('手机号格式不正确')
        
        return v
    
    model_config = ConfigDict(json_schema_extra={
            "example": {
                "name": "张三",
                "student_id": "2021001001",
                "group_id": 1,
                "class_name": "计算机科学与技术2101",
                "email": "zhangsan@example.com",
                "password": "SecurePassword123!",
                "role": "member",
                "dormitory": "1号楼101",
                "phone": "13812345678",
                "is_active": True,
                "is_verified": False
            })
        }


class MemberUpdate(BaseModel):
    """更新成员信息的请求模型"""
    
    name: Optional[str] = Field(
        None, 
        min_length=1, 
        max_length=50,
        description="成员姓名"
    )
    group_id: Optional[int] = Field(
        None,
        ge=0,
        description="工作组ID"
    )
    class_name: Optional[str] = Field(
        None, 
        max_length=50,
        description="班级名称"
    )
    email: Optional[EmailStr] = Field(
        None,
        description="邮箱地址"
    )
    dormitory: Optional[str] = Field(
        None, 
        max_length=50,
        description="宿舍信息"
    )
    phone: Optional[str] = Field(
        None, 
        max_length=20,
        description="手机号码"
    )
    
    @field_validator('name')

    
    @classmethod
    def validate_name(cls, v):
        """验证姓名格式"""
        if v is not None:
            if not v or not v.strip():
                raise ValueError('姓名不能为空')
            
            import re
            if not re.match(r'^[\u4e00-\u9fa5a-zA-Z\s]+$', v.strip()):
                raise ValueError('姓名只能包含中文、英文字母和空格')
            
            return v.strip()
        return v
    
    @field_validator('phone')

    
    @classmethod
    def validate_phone(cls, v):
        """验证手机号格式"""
        if v is not None and v:
            from app.core.security import validate_phone_format
            if not validate_phone_format(v):
                raise ValueError('手机号格式不正确')
        return v
    
    model_config = ConfigDict(json_schema_extra={
            "example": {
                "name": "张三丰",
                "group_id": 2,
                "class_name": "计算机科学与技术2102",
                "email": "zhangsan@newdomain.com",
                "dormitory": "2号楼201",
                "phone": "13987654321"
            })
        }


class MemberAdminUpdate(MemberUpdate):
    """管理员更新成员信息的请求模型（包含敏感字段）"""
    
    role: Optional[UserRole] = Field(
        None,
        description="用户角色"
    )
    is_active: Optional[bool] = Field(
        None,
        description="是否启用"
    )
    is_verified: Optional[bool] = Field(
        None,
        description="是否已验证邮箱"
    )
    
    model_config = ConfigDict(json_schema_extra={
            "example": {
                "name": "张三",
                "role": "group_leader",
                "is_active": True,
                "is_verified": True,
                "group_id": 1
            })
        }


class MemberResponse(MemberBase):
    """成员信息响应模型"""
    
    id: int = Field(..., description="成员ID")
    role: str = Field(..., description="用户角色")
    is_active: bool = Field(..., description="是否启用")
    is_verified: bool = Field(..., description="是否已验证邮箱")
    last_login: Optional[datetime] = Field(None, description="最后登录时间")
    login_count: int = Field(..., description="登录次数")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    
    model_config = ConfigDict(from_attributes=True)
        schema_extra = {
            "example": {
                "id": 1,
                "name": "张三",
                "student_id": "2021001001",
                "group_id": 1,
                "class_name": "计算机科学与技术2101",
                "email": "zhangsan@example.com",
                "role": "member",
                "is_active": True,
                "is_verified": True,
                "last_login": "2025-01-27T10:30:00",
                "login_count": 15,
                "created_at": "2025-01-01T00:00:00",
                "updated_at": "2025-01-27T10:30:00"
            }
        }


class MemberDetailResponse(MemberResponse):
    """成员详细信息响应模型（管理员可见）"""
    
    dormitory: Optional[str] = Field(None, description="宿舍信息（已解密）")
    phone: Optional[str] = Field(None, description="手机号码（部分隐藏）")
    
    model_config = ConfigDict(from_attributes=True)
        schema_extra = {
            "example": {
                "id": 1,
                "name": "张三",
                "student_id": "2021001001",
                "group_id": 1,
                "class_name": "计算机科学与技术2101",
                "email": "zhangsan@example.com",
                "dormitory": "1号楼101",
                "phone": "138****5678",
                "role": "member",
                "is_active": True,
                "is_verified": True,
                "last_login": "2025-01-27T10:30:00",
                "login_count": 15,
                "created_at": "2025-01-01T00:00:00",
                "updated_at": "2025-01-27T10:30:00"
            }
        }


class MemberListResponse(BaseModel):
    """成员列表响应模型"""
    
    items: List[MemberResponse] = Field(..., description="成员列表")
    total: int = Field(..., description="总数量")
    page: int = Field(..., description="当前页码")
    size: int = Field(..., description="每页大小")
    pages: int = Field(..., description="总页数")
    has_next: bool = Field(..., description="是否有下一页")
    has_prev: bool = Field(..., description="是否有上一页")
    
    model_config = ConfigDict(json_schema_extra={
            "example": {
                "items": [
                    {
                        "id": 1,
                        "name": "张三",
                        "student_id": "2021001001",
                        "role": "member",
                        "is_active": True
                    })
                ],
                "total": 50,
                "page": 1,
                "size": 20,
                "pages": 3,
                "has_next": True,
                "has_prev": False
            }
        }


class MemberRoleUpdate(BaseModel):
    """更新成员角色的请求模型"""
    
    role: UserRole = Field(..., description="新角色")
    
    model_config = ConfigDict(json_schema_extra={
            "example": {
                "role": "group_leader"
            })
        }


class MemberStatusUpdate(BaseModel):
    """更新成员状态的请求模型"""
    
    is_active: bool = Field(..., description="是否启用")
    reason: Optional[str] = Field(
        None, 
        max_length=200,
        description="操作原因"
    )
    
    model_config = ConfigDict(json_schema_extra={
            "example": {
                "is_active": False,
                "reason": "违反规定，暂时停用"
            })
        }


class MemberSearchParams(BaseModel):
    """成员搜索参数模型"""
    
    name: Optional[str] = Field(
        None, 
        max_length=50,
        description="姓名关键词"
    )
    student_id: Optional[str] = Field(
        None, 
        max_length=20,
        description="学号关键词"
    )
    role: Optional[UserRole] = Field(
        None,
        description="角色筛选"
    )
    group_id: Optional[int] = Field(
        None,
        ge=0,
        description="工作组筛选"
    )
    class_name: Optional[str] = Field(
        None, 
        max_length=50,
        description="班级筛选"
    )
    is_active: Optional[bool] = Field(
        None,
        description="状态筛选"
    )
    is_verified: Optional[bool] = Field(
        None,
        description="验证状态筛选"
    )
    
    model_config = ConfigDict(json_schema_extra={
            "example": {
                "name": "张",
                "role": "member",
                "group_id": 1,
                "is_active": True
            })
        }


class MemberStatistics(BaseModel):
    """成员统计信息模型"""
    
    total_members: int = Field(..., description="总成员数")
    active_members: int = Field(..., description="活跃成员数")
    inactive_members: int = Field(..., description="停用成员数")
    verified_members: int = Field(..., description="已验证成员数")
    admin_count: int = Field(..., description="管理员数量")
    group_leader_count: int = Field(..., description="组长数量")
    member_count: int = Field(..., description="普通成员数量")
    group_distribution: dict = Field(..., description="组别分布")
    recent_logins: List[dict] = Field(..., description="近期登录统计")
    
    model_config = ConfigDict(json_schema_extra={
            "example": {
                "total_members": 50,
                "active_members": 45,
                "inactive_members": 5,
                "verified_members": 40,
                "admin_count": 2,
                "group_leader_count": 5,
                "member_count": 43,
                "group_distribution": {
                    "1": 20,
                    "2": 15,
                    "3": 15
                }),
                "recent_logins": [
                    {"date": "2025-01-27", "count": 15},
                    {"date": "2025-01-26", "count": 12}
                ]
            }
        }


class PasswordResetRequest(BaseModel):
    """重置密码请求模型"""
    
    member_id: int = Field(..., description="成员ID")
    new_password: str = Field(
        ..., 
        min_length=8,
        max_length=128,
        description="新密码"
    )
    
    @field_validator('new_password')

    
    @classmethod
    def validate_password(cls, v):
        """验证密码强度"""
        from app.core.security import validate_password_strength
        
        is_strong, errors = validate_password_strength(v)
        if not is_strong:
            raise ValueError(f"密码不符合要求: {', '.join(errors)}")
        
        return v
    
    model_config = ConfigDict(json_schema_extra={
            "example": {
                "member_id": 1,
                "new_password": "NewSecurePassword123!"
            })
        }


class BulkMemberOperation(BaseModel):
    """批量成员操作模型"""
    
    member_ids: List[int] = Field(
        ..., 
        min_length=1,
        max_length=100,
        description="成员ID列表"
    )
    operation: str = Field(
        ..., 
        pattern="^(activate|deactivate|delete|set_role|set_group)$",
        description="操作类型"
    )
    operation_data: Optional[dict] = Field(
        None,
        description="操作相关数据"
    )
    reason: Optional[str] = Field(
        None, 
        max_length=200,
        description="操作原因"
    )
    
    @model_validator(mode='after')
    def validate_operation_data(self):
        """验证操作数据"""
        if self.operation == 'set_role':
            if not self.operation_data or 'role' not in self.operation_data:
                raise ValueError('设置角色操作需要提供role参数')
        elif self.operation == 'set_group':
            if not self.operation_data or 'group_id' not in self.operation_data:
                raise ValueError('设置组别操作需要提供group_id参数')
        
        return self
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "member_ids": [1, 2, 3],
                "operation": "set_role",
                "operation_data": {"role": "group_leader"},
                "reason": "批量设置为组长"
            }
        }
    )


class MemberImportRequest(BaseModel):
    """成员批量导入请求模型"""
    
    members: List[MemberCreate] = Field(
        ..., 
        min_length=1,
        max_length=1000,
        description="成员数据列表"
    )
    skip_duplicates: bool = Field(
        default=True,
        description="是否跳过重复学号的成员"
    )
    send_welcome_email: bool = Field(
        default=False,
        description="是否发送欢迎邮件"
    )
    
    model_config = ConfigDict(json_schema_extra={
            "example": {
                "members": [
                    {
                        "name": "张三",
                        "student_id": "2021001001",
                        "password": "TempPassword123!",
                        "group_id": 1
                    })
                ],
                "skip_duplicates": True,
                "send_welcome_email": False
            }
        }


class MemberImportResult(BaseModel):
    """成员导入结果模型"""
    
    total_processed: int = Field(..., description="处理总数")
    successful_imports: int = Field(..., description="成功导入数")
    failed_imports: int = Field(..., description="导入失败数")
    skipped_duplicates: int = Field(..., description="跳过的重复数")
    errors: List[dict] = Field(..., description="错误详情")
    imported_members: List[MemberResponse] = Field(..., description="成功导入的成员")
    
    model_config = ConfigDict(json_schema_extra={
            "example": {
                "total_processed": 10,
                "successful_imports": 8,
                "failed_imports": 1,
                "skipped_duplicates": 1,
                "errors": [
                    {"row": 3, "error": "学号重复"})
                ],
                "imported_members": []
            }
        }