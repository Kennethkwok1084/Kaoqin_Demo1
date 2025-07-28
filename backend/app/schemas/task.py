"""
任务管理相关的Pydantic模式定义
包含维修任务、监控任务、工时计算的请求和响应模型
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, validator, root_validator
from enum import Enum

from app.models.task import TaskStatus, TaskType, TaskPriority


class TaskTagBase(BaseModel):
    """任务标签基础模型"""
    
    name: str = Field(
        ..., 
        min_length=1, 
        max_length=50,
        description="标签名称"
    )
    color: str = Field(
        ..., 
        regex=r'^#[0-9A-Fa-f]{6}$',
        description="标签颜色（16进制）"
    )
    work_minutes: int = Field(
        ..., 
        ge=0, 
        le=999,
        description="标准工时（分钟）"
    )
    is_online: bool = Field(
        ...,
        description="是否为线上任务"
    )


class TaskTagCreate(TaskTagBase):
    """创建任务标签的请求模型"""
    
    description: Optional[str] = Field(
        None, 
        max_length=200,
        description="标签描述"
    )
    is_active: bool = Field(
        default=True,
        description="是否启用"
    )
    
    class Config:
        schema_extra = {
            "example": {
                "name": "网络维修",
                "color": "#FF6B6B",
                "work_minutes": 100,
                "is_online": False,
                "description": "校园网络设备维修任务",
                "is_active": True
            }
        }


class TaskTagResponse(TaskTagBase):
    """任务标签响应模型"""
    
    id: int = Field(..., description="标签ID")
    description: Optional[str] = Field(None, description="标签描述")
    is_active: bool = Field(..., description="是否启用")
    usage_count: int = Field(..., description="使用次数")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    
    class Config:
        orm_mode = True
        schema_extra = {
            "example": {
                "id": 1,
                "name": "网络维修",
                "color": "#FF6B6B",
                "work_minutes": 100,
                "is_online": False,
                "description": "校园网络设备维修任务",
                "is_active": True,
                "usage_count": 15,
                "created_at": "2025-01-01T00:00:00",
                "updated_at": "2025-01-27T10:30:00"
            }
        }


class TaskBase(BaseModel):
    """任务基础信息模型"""
    
    title: str = Field(
        ..., 
        min_length=1, 
        max_length=200,
        description="任务标题"
    )
    description: Optional[str] = Field(
        None, 
        max_length=2000,
        description="任务详细描述"
    )
    task_type: TaskType = Field(
        ...,
        description="任务类型"
    )
    priority: TaskPriority = Field(
        default=TaskPriority.MEDIUM,
        description="任务优先级"
    )
    location: Optional[str] = Field(
        None, 
        max_length=100,
        description="任务地点"
    )
    
    @validator('title')
    def validate_title(cls, v):
        """验证任务标题"""
        if not v or not v.strip():
            raise ValueError('任务标题不能为空')
        return v.strip()


class TaskCreate(TaskBase):
    """创建任务的请求模型"""
    
    assigned_to: Optional[int] = Field(
        None,
        description="分配给的成员ID"
    )
    tag_ids: List[int] = Field(
        default=[],
        description="关联的标签ID列表"
    )
    estimated_minutes: Optional[int] = Field(
        None, 
        ge=1, 
        le=999,
        description="预估工时（分钟）"
    )
    deadline: Optional[datetime] = Field(
        None,
        description="截止时间"
    )
    reporter_name: Optional[str] = Field(
        None, 
        max_length=50,
        description="报告人姓名"
    )
    reporter_contact: Optional[str] = Field(
        None, 
        max_length=50,
        description="报告人联系方式"
    )
    is_rush: bool = Field(
        default=False,
        description="是否为紧急任务"
    )
    
    @validator('deadline') 
    def validate_deadline(cls, v):
        """验证截止时间"""
        if v and v <= datetime.now():
            raise ValueError('截止时间必须在当前时间之后')
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "title": "图书馆3楼网络故障维修",
                "description": "图书馆3楼网络设备无法正常连接，需要检查交换机状态",
                "task_type": "repair",
                "priority": "high",
                "location": "图书馆3楼",
                "assigned_to": 2,
                "tag_ids": [1, 3],
                "estimated_minutes": 120,
                "deadline": "2025-01-30T18:00:00",
                "reporter_name": "张老师",
                "reporter_contact": "13812345678",
                "is_rush": True
            }
        }


class TaskUpdate(BaseModel):
    """更新任务的请求模型"""
    
    title: Optional[str] = Field(
        None, 
        min_length=1, 
        max_length=200,
        description="任务标题"
    )
    description: Optional[str] = Field(
        None, 
        max_length=2000,
        description="任务详细描述"
    )
    status: Optional[TaskStatus] = Field(
        None,
        description="任务状态"
    )
    priority: Optional[TaskPriority] = Field(
        None,
        description="任务优先级"
    )
    assigned_to: Optional[int] = Field(
        None,
        description="分配给的成员ID"
    )
    tag_ids: Optional[List[int]] = Field(
        None,
        description="关联的标签ID列表"
    )
    estimated_minutes: Optional[int] = Field(
        None, 
        ge=1, 
        le=999,
        description="预估工时（分钟）"
    )
    actual_minutes: Optional[int] = Field(
        None, 
        ge=0, 
        le=999,
        description="实际工时（分钟）"
    )
    completion_note: Optional[str] = Field(
        None, 
        max_length=500,
        description="完成备注"
    )
    deadline: Optional[datetime] = Field(
        None,
        description="截止时间"
    )
    is_rush: Optional[bool] = Field(
        None,
        description="是否为紧急任务"
    )
    
    @validator('title')
    def validate_title(cls, v):
        """验证任务标题"""
        if v is not None and (not v or not v.strip()):
            raise ValueError('任务标题不能为空')
        return v.strip() if v else v
    
    class Config:
        schema_extra = {
            "example": {
                "status": "completed",
                "actual_minutes": 90,
                "completion_note": "已更换故障交换机，网络恢复正常",
                "priority": "medium"
            }
        }


class TaskResponse(TaskBase):
    """任务响应模型"""
    
    id: int = Field(..., description="任务ID")
    task_number: str = Field(..., description="任务编号")
    status: str = Field(..., description="任务状态")
    created_by: int = Field(..., description="创建者ID")
    assigned_to: Optional[int] = Field(None, description="分配给的成员ID")
    estimated_minutes: Optional[int] = Field(None, description="预估工时")
    actual_minutes: Optional[int] = Field(None, description="实际工时")
    calculated_minutes: int = Field(..., description="计算工时")
    completion_note: Optional[str] = Field(None, description="完成备注")
    deadline: Optional[datetime] = Field(None, description="截止时间")
    completed_at: Optional[datetime] = Field(None, description="完成时间")
    is_rush: bool = Field(..., description="是否为紧急任务")
    is_overdue: bool = Field(..., description="是否超期")
    tags: List[TaskTagResponse] = Field(default=[], description="关联标签")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    
    # 关联信息
    creator_name: Optional[str] = Field(None, description="创建者姓名")
    assignee_name: Optional[str] = Field(None, description="执行者姓名")
    
    class Config:
        orm_mode = True
        schema_extra = {
            "example": {
                "id": 1,
                "task_number": "T202501270001",
                "title": "图书馆3楼网络故障维修",
                "description": "图书馆3楼网络设备无法正常连接",
                "task_type": "repair",
                "status": "completed",
                "priority": "high",
                "location": "图书馆3楼",
                "created_by": 1,
                "assigned_to": 2,
                "estimated_minutes": 120,
                "actual_minutes": 90,
                "calculated_minutes": 115,
                "completion_note": "已更换故障交换机",
                "deadline": "2025-01-30T18:00:00",
                "completed_at": "2025-01-27T16:30:00",
                "is_rush": True,
                "is_overdue": False,
                "tags": [],
                "created_at": "2025-01-27T14:00:00",
                "updated_at": "2025-01-27T16:30:00",
                "creator_name": "管理员",
                "assignee_name": "张三"
            }
        }


class TaskDetailResponse(TaskResponse):
    """任务详细信息响应模型"""
    
    reporter_name: Optional[str] = Field(None, description="报告人姓名")
    reporter_contact: Optional[str] = Field(None, description="报告人联系方式")
    work_hour_breakdown: Dict[str, Any] = Field(default={}, description="工时分解详情")
    status_history: List[Dict[str, Any]] = Field(default=[], description="状态变更历史")
    
    class Config:
        orm_mode = True
        schema_extra = {
            "example": {
                "id": 1,
                "task_number": "T202501270001",
                "title": "图书馆3楼网络故障维修",
                "reporter_name": "张老师",
                "reporter_contact": "13812345678",
                "work_hour_breakdown": {
                    "base_minutes": 100,
                    "rush_bonus": 15,
                    "review_bonus": 0,
                    "penalties": 0,
                    "total_minutes": 115
                },
                "status_history": [
                    {"status": "pending", "changed_at": "2025-01-27T14:00:00", "changed_by": "管理员"},
                    {"status": "in_progress", "changed_at": "2025-01-27T14:30:00", "changed_by": "张三"},
                    {"status": "completed", "changed_at": "2025-01-27T16:30:00", "changed_by": "张三"}
                ]
            }
        }


class TaskListResponse(BaseModel):
    """任务列表响应模型"""
    
    items: List[TaskResponse] = Field(..., description="任务列表")
    total: int = Field(..., description="总数量")
    page: int = Field(..., description="当前页码")
    size: int = Field(..., description="每页大小")
    pages: int = Field(..., description="总页数")
    has_next: bool = Field(..., description="是否有下一页")
    has_prev: bool = Field(..., description="是否有上一页")
    filters_applied: Dict[str, Any] = Field(default={}, description="应用的筛选条件")
    
    class Config:
        schema_extra = {
            "example": {
                "items": [],
                "total": 150,
                "page": 1,
                "size": 20,
                "pages": 8,
                "has_next": True,
                "has_prev": False,
                "filters_applied": {
                    "status": "pending",
                    "task_type": "repair"
                }
            }
        }


class TaskSearchParams(BaseModel):
    """任务搜索参数模型"""
    
    title: Optional[str] = Field(
        None, 
        max_length=100,
        description="标题关键词"
    )
    task_number: Optional[str] = Field(
        None, 
        max_length=20,
        description="任务编号"
    )
    task_type: Optional[TaskType] = Field(
        None,
        description="任务类型筛选"
    )
    status: Optional[TaskStatus] = Field(
        None,
        description="状态筛选"
    )
    priority: Optional[TaskPriority] = Field(
        None,
        description="优先级筛选"
    )
    assigned_to: Optional[int] = Field(
        None,
        description="执行者筛选"
    )
    created_by: Optional[int] = Field(
        None,
        description="创建者筛选"
    )
    tag_ids: Optional[List[int]] = Field(
        None,
        description="标签筛选"
    )
    location: Optional[str] = Field(
        None, 
        max_length=50,
        description="地点关键词"
    )
    is_rush: Optional[bool] = Field(
        None,
        description="紧急任务筛选"
    )
    is_overdue: Optional[bool] = Field(
        None,
        description="超期任务筛选"
    )
    date_from: Optional[datetime] = Field(
        None,
        description="创建时间起始"
    )
    date_to: Optional[datetime] = Field(
        None,
        description="创建时间结束"
    )
    deadline_from: Optional[datetime] = Field(
        None,
        description="截止时间起始"
    )
    deadline_to: Optional[datetime] = Field(
        None,
        description="截止时间结束"
    )
    
    @root_validator
    def validate_date_ranges(cls, values):
        """验证日期范围"""
        date_from = values.get('date_from')
        date_to = values.get('date_to')
        if date_from and date_to and date_from > date_to:
            raise ValueError('创建时间起始不能晚于结束时间')
        
        deadline_from = values.get('deadline_from')
        deadline_to = values.get('deadline_to')
        if deadline_from and deadline_to and deadline_from > deadline_to:
            raise ValueError('截止时间起始不能晚于结束时间')
        
        return values
    
    class Config:
        schema_extra = {
            "example": {
                "title": "网络",
                "status": "pending",
                "task_type": "repair",
                "priority": "high",
                "assigned_to": 2,
                "is_rush": True,
                "date_from": "2025-01-01T00:00:00",
                "date_to": "2025-01-31T23:59:59"
            }
        }


class TaskStatusUpdate(BaseModel):
    """任务状态更新模型"""
    
    status: TaskStatus = Field(..., description="新状态")
    completion_note: Optional[str] = Field(
        None, 
        max_length=500,
        description="状态变更备注"
    )
    actual_minutes: Optional[int] = Field(
        None, 
        ge=0, 
        le=999,
        description="实际工时（仅完成时需要）"
    )
    
    @root_validator
    def validate_completion_data(cls, values):
        """验证完成数据"""
        status = values.get('status')
        actual_minutes = values.get('actual_minutes')
        
        if status == TaskStatus.COMPLETED and actual_minutes is None:
            raise ValueError('完成任务时必须提供实际工时')
        
        return values
    
    class Config:
        schema_extra = {
            "example": {
                "status": "completed",
                "completion_note": "维修完成，设备恢复正常",
                "actual_minutes": 90
            }
        }


class TaskAssignment(BaseModel):
    """任务分配模型"""
    
    assigned_to: int = Field(..., description="分配给的成员ID")
    assignment_note: Optional[str] = Field(
        None, 
        max_length=200,
        description="分配备注"
    )
    
    class Config:
        schema_extra = {
            "example": {
                "assigned_to": 2,
                "assignment_note": "请优先处理此紧急任务"
            }
        }


class TaskStatistics(BaseModel):
    """任务统计信息模型"""
    
    total_tasks: int = Field(..., description="总任务数")
    pending_tasks: int = Field(..., description="待处理任务数")
    in_progress_tasks: int = Field(..., description="进行中任务数")
    completed_tasks: int = Field(..., description="已完成任务数")
    overdue_tasks: int = Field(..., description="超期任务数")
    rush_tasks: int = Field(..., description="紧急任务数")
    total_work_hours: float = Field(..., description="总工时（小时）")
    avg_completion_time: float = Field(..., description="平均完成时间（小时）")
    task_type_distribution: Dict[str, int] = Field(..., description="任务类型分布")
    priority_distribution: Dict[str, int] = Field(..., description="优先级分布")
    monthly_trends: List[Dict[str, Any]] = Field(..., description="月度趋势")
    
    class Config:
        schema_extra = {
            "example": {
                "total_tasks": 150,
                "pending_tasks": 25,
                "in_progress_tasks": 30,
                "completed_tasks": 90,
                "overdue_tasks": 5,
                "rush_tasks": 15,
                "total_work_hours": 450.5,
                "avg_completion_time": 3.2,
                "task_type_distribution": {
                    "repair": 80,
                    "monitoring": 50,
                    "assistance": 20
                },
                "priority_distribution": {
                    "low": 40,
                    "medium": 70,
                    "high": 30,
                    "urgent": 10
                },
                "monthly_trends": [
                    {"month": "2025-01", "completed": 35, "avg_hours": 2.8}
                ]
            }
        }


class TaskImportRequest(BaseModel):
    """任务批量导入请求模型"""
    
    tasks: List[TaskCreate] = Field(
        ..., 
        min_items=1,
        max_items=1000,
        description="任务数据列表"
    )
    auto_assign: bool = Field(
        default=False,
        description="是否自动分配执行者"
    )
    default_priority: TaskPriority = Field(
        default=TaskPriority.MEDIUM,
        description="默认优先级"
    )
    
    class Config:
        schema_extra = {
            "example": {
                "tasks": [
                    {
                        "title": "教学楼A座网络检修",
                        "task_type": "repair",
                        "location": "教学楼A座",
                        "priority": "medium"
                    }
                ],
                "auto_assign": True,
                "default_priority": "medium"
            }
        }


class TaskImportResult(BaseModel):
    """任务导入结果模型"""
    
    total_processed: int = Field(..., description="处理总数")
    successful_imports: int = Field(..., description="成功导入数")
    failed_imports: int = Field(..., description="导入失败数")
    warnings: int = Field(..., description="警告数量")
    errors: List[Dict[str, Any]] = Field(..., description="错误详情")
    warnings_list: List[Dict[str, Any]] = Field(..., description="警告详情")
    imported_tasks: List[TaskResponse] = Field(..., description="成功导入的任务")
    
    class Config:
        schema_extra = {
            "example": {
                "total_processed": 10,
                "successful_imports": 8,
                "failed_imports": 1,
                "warnings": 1,
                "errors": [
                    {"row": 3, "error": "任务标题不能为空"}
                ],
                "warnings_list": [
                    {"row": 5, "warning": "未指定执行者，已设为待分配"}
                ],
                "imported_tasks": []
            }
        }


class WorkHourCalculation(BaseModel):
    """工时计算请求模型"""
    
    task_id: int = Field(..., description="任务ID")
    actual_minutes: int = Field(
        ..., 
        ge=1, 
        le=999,
        description="实际工时（分钟）"
    )
    review_rating: Optional[int] = Field(
        None, 
        ge=1, 
        le=5,
        description="评价等级（1-5分）"
    )
    is_late_response: bool = Field(
        default=False,
        description="是否延迟响应"
    )
    is_late_completion: bool = Field(
        default=False,
        description="是否延迟完成"
    )
    
    class Config:
        schema_extra = {
            "example": {
                "task_id": 1,
                "actual_minutes": 90,
                "review_rating": 4,
                "is_late_response": False,
                "is_late_completion": False
            }
        }


class WorkHourResult(BaseModel):
    """工时计算结果模型"""
    
    base_minutes: int = Field(..., description="基础工时")
    rush_bonus: int = Field(..., description="紧急任务奖励")
    review_bonus: int = Field(..., description="好评奖励")
    response_penalty: int = Field(..., description="延迟响应扣分")
    completion_penalty: int = Field(..., description="延迟完成扣分")
    review_penalty: int = Field(..., description="差评扣分")
    final_minutes: int = Field(..., description="最终工时")
    calculation_details: Dict[str, Any] = Field(..., description="计算详情")
    
    class Config:
        schema_extra = {
            "example": {
                "base_minutes": 100,
                "rush_bonus": 15,
                "review_bonus": 30,
                "response_penalty": 0,
                "completion_penalty": 0,
                "review_penalty": 0,
                "final_minutes": 145,
                "calculation_details": {
                    "calculation_rules": "线下维修任务基础100分钟",
                    "applied_bonuses": ["紧急任务奖励", "好评奖励"],
                    "applied_penalties": []
                }
            }
        }