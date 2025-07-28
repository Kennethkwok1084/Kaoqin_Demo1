"""
考勤统计相关的Pydantic模式定义
包含月度统计、数据分析、报表生成的请求和响应模型
"""

from datetime import datetime, date
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, validator, root_validator
from enum import Enum


class ReportType(str, Enum):
    """报表类型枚举"""
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"
    CUSTOM = "custom"


class ExportFormat(str, Enum):
    """导出格式枚举"""
    EXCEL = "excel"
    PDF = "pdf"
    CSV = "csv"


class AttendanceBase(BaseModel):
    """考勤记录基础模型"""
    
    member_id: int = Field(..., description="成员ID")
    year: int = Field(
        ..., 
        ge=2020, 
        le=2030,
        description="年份"
    )
    month: int = Field(
        ..., 
        ge=1, 
        le=12,
        description="月份"
    )
    
    @root_validator
    def validate_date(cls, values):
        """验证年月组合"""
        year = values.get('year')
        month = values.get('month')
        
        if year and month:
            # 检查日期是否合理（不能是未来月份）
            current_date = datetime.now()
            if year > current_date.year or (year == current_date.year and month > current_date.month):
                raise ValueError('不能统计未来月份的考勤')
        
        return values


class AttendanceCreate(AttendanceBase):
    """创建考勤记录的请求模型"""
    
    total_tasks: int = Field(
        default=0, 
        ge=0,
        description="总任务数"
    )
    completed_tasks: int = Field(
        default=0, 
        ge=0,
        description="已完成任务数"
    )
    total_work_hours: float = Field(
        default=0.0, 
        ge=0.0,
        description="总工时（小时）"
    )
    calculated_work_hours: float = Field(
        default=0.0, 
        ge=0.0,
        description="计算工时（小时）"
    )
    bonus_hours: float = Field(
        default=0.0, 
        ge=0.0,
        description="奖励工时（小时）"
    )
    penalty_hours: float = Field(
        default=0.0, 
        ge=0.0,
        description="扣除工时（小时）"
    )
    attendance_score: float = Field(
        default=0.0, 
        ge=0.0, 
        le=100.0,
        description="考勤得分"
    )
    
    @validator('completed_tasks')
    def validate_completed_tasks(cls, v, values):
        """验证完成任务数不能超过总任务数"""
        total_tasks = values.get('total_tasks', 0)
        if v > total_tasks:
            raise ValueError('完成任务数不能超过总任务数')
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "member_id": 1,
                "year": 2025,
                "month": 1,
                "total_tasks": 15,
                "completed_tasks": 12,
                "total_work_hours": 25.5,
                "calculated_work_hours": 28.0,
                "bonus_hours": 3.5,
                "penalty_hours": 1.0,
                "attendance_score": 85.6
            }
        }


class AttendanceUpdate(BaseModel):
    """更新考勤记录的请求模型"""
    
    total_tasks: Optional[int] = Field(
        None, 
        ge=0,
        description="总任务数"
    )
    completed_tasks: Optional[int] = Field(
        None, 
        ge=0,
        description="已完成任务数"
    )
    total_work_hours: Optional[float] = Field(
        None, 
        ge=0.0,
        description="总工时（小时）"
    )
    calculated_work_hours: Optional[float] = Field(
        None, 
        ge=0.0,
        description="计算工时（小时）"
    )
    bonus_hours: Optional[float] = Field(
        None, 
        ge=0.0,
        description="奖励工时（小时）"
    )
    penalty_hours: Optional[float] = Field(
        None, 
        ge=0.0,
        description="扣除工时（小时）"
    )
    attendance_score: Optional[float] = Field(
        None, 
        ge=0.0, 
        le=100.0,
        description="考勤得分"
    )
    notes: Optional[str] = Field(
        None, 
        max_length=500,
        description="备注信息"
    )
    
    class Config:
        schema_extra = {
            "example": {
                "attendance_score": 88.5,
                "notes": "本月表现良好，任务完成质量较高"
            }
        }


class AttendanceResponse(AttendanceBase):
    """考勤记录响应模型"""
    
    id: int = Field(..., description="记录ID")
    total_tasks: int = Field(..., description="总任务数")
    completed_tasks: int = Field(..., description="已完成任务数")
    pending_tasks: int = Field(..., description="待处理任务数")
    total_work_hours: float = Field(..., description="总工时（小时）")
    calculated_work_hours: float = Field(..., description="计算工时（小时）")
    bonus_hours: float = Field(..., description="奖励工时（小时）")
    penalty_hours: float = Field(..., description="扣除工时（小时）")
    final_work_hours: float = Field(..., description="最终工时（小时）")
    attendance_score: float = Field(..., description="考勤得分")
    completion_rate: float = Field(..., description="任务完成率（%）")
    average_task_time: float = Field(..., description="平均任务时长（小时）")
    rank_in_group: Optional[int] = Field(None, description="组内排名")
    rank_in_all: Optional[int] = Field(None, description="全体排名")
    notes: Optional[str] = Field(None, description="备注信息")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    
    # 关联信息
    member_name: str = Field(..., description="成员姓名")
    member_student_id: str = Field(..., description="成员学号")
    group_name: Optional[str] = Field(None, description="工作组名称")
    
    class Config:
        orm_mode = True
        schema_extra = {
            "example": {
                "id": 1,
                "member_id": 1,
                "year": 2025,
                "month": 1,
                "total_tasks": 15,
                "completed_tasks": 12,
                "pending_tasks": 3,
                "total_work_hours": 25.5,
                "calculated_work_hours": 28.0,
                "bonus_hours": 3.5,
                "penalty_hours": 1.0,
                "final_work_hours": 30.5,
                "attendance_score": 85.6,
                "completion_rate": 80.0,
                "average_task_time": 2.125,
                "rank_in_group": 2,
                "rank_in_all": 5,
                "notes": "表现良好",
                "created_at": "2025-01-31T00:00:00",
                "updated_at": "2025-01-31T12:00:00",
                "member_name": "张三",
                "member_student_id": "2021001001",
                "group_name": "网络维护组"
            }
        }


class AttendanceListResponse(BaseModel):
    """考勤记录列表响应模型"""
    
    items: List[AttendanceResponse] = Field(..., description="考勤记录列表")
    total: int = Field(..., description="总数量")
    page: int = Field(..., description="当前页码")
    size: int = Field(..., description="每页大小")
    pages: int = Field(..., description="总页数")
    has_next: bool = Field(..., description="是否有下一页")
    has_prev: bool = Field(..., description="是否有上一页")
    summary: Dict[str, Any] = Field(..., description="统计摘要")
    
    class Config:
        schema_extra = {
            "example": {
                "items": [],
                "total": 50,
                "page": 1,
                "size": 20,
                "pages": 3,
                "has_next": True,
                "has_prev": False,
                "summary": {
                    "total_members": 50,
                    "avg_score": 82.5,
                    "avg_work_hours": 28.5,
                    "top_performer": "李四"
                }
            }
        }


class AttendanceSearchParams(BaseModel):
    """考勤记录搜索参数模型"""
    
    member_id: Optional[int] = Field(
        None,
        description="成员ID筛选"
    )
    member_name: Optional[str] = Field(
        None, 
        max_length=50,
        description="成员姓名关键词"
    )
    student_id: Optional[str] = Field(
        None, 
        max_length=20,
        description="学号关键词"
    )
    group_id: Optional[int] = Field(
        None,
        description="工作组筛选"
    )
    year: Optional[int] = Field(
        None, 
        ge=2020, 
        le=2030,
        description="年份筛选"
    )
    month: Optional[int] = Field(
        None, 
        ge=1, 
        le=12,
        description="月份筛选"
    )
    score_min: Optional[float] = Field(
        None, 
        ge=0.0, 
        le=100.0,
        description="最低得分"
    )
    score_max: Optional[float] = Field(
        None, 
        ge=0.0, 
        le=100.0,
        description="最高得分"
    )
    work_hours_min: Optional[float] = Field(
        None, 
        ge=0.0,
        description="最低工时"
    )
    work_hours_max: Optional[float] = Field(
        None, 
        ge=0.0,
        description="最高工时"
    )
    
    @root_validator
    def validate_ranges(cls, values):
        """验证范围参数"""
        score_min = values.get('score_min')
        score_max = values.get('score_max')
        if score_min is not None and score_max is not None and score_min > score_max:
            raise ValueError('最低得分不能大于最高得分')
        
        hours_min = values.get('work_hours_min')
        hours_max = values.get('work_hours_max')
        if hours_min is not None and hours_max is not None and hours_min > hours_max:
            raise ValueError('最低工时不能大于最高工时')
        
        return values
    
    class Config:
        schema_extra = {
            "example": {
                "member_name": "张",
                "group_id": 1,
                "year": 2025,
                "month": 1,
                "score_min": 80.0,
                "work_hours_min": 20.0
            }
        }


class MonthlyStatistics(BaseModel):
    """月度统计信息模型"""
    
    year: int = Field(..., description="年份")
    month: int = Field(..., description="月份")
    total_members: int = Field(..., description="总成员数")
    active_members: int = Field(..., description="活跃成员数")
    total_tasks: int = Field(..., description="总任务数")
    completed_tasks: int = Field(..., description="完成任务数")
    total_work_hours: float = Field(..., description="总工时")
    avg_work_hours: float = Field(..., description="平均工时")
    avg_score: float = Field(..., description="平均得分")
    completion_rate: float = Field(..., description="任务完成率")
    top_performers: List[Dict[str, Any]] = Field(..., description="优秀表现者")
    group_rankings: List[Dict[str, Any]] = Field(..., description="组别排名")
    task_distribution: Dict[str, int] = Field(..., description="任务类型分布")
    work_hour_trends: List[Dict[str, Any]] = Field(..., description="工时趋势")
    
    class Config:
        schema_extra = {
            "example": {
                "year": 2025,
                "month": 1,
                "total_members": 50,
                "active_members": 45,
                "total_tasks": 350,
                "completed_tasks": 320,
                "total_work_hours": 1250.5,
                "avg_work_hours": 27.8,
                "avg_score": 82.5,
                "completion_rate": 91.4,
                "top_performers": [
                    {"name": "李四", "score": 95.5, "work_hours": 45.2},
                    {"name": "王五", "score": 92.8, "work_hours": 42.1}
                ],
                "group_rankings": [
                    {"group_name": "网络维护组", "avg_score": 88.5, "members": 15},
                    {"group_name": "设备管理组", "avg_score": 85.2, "members": 20}
                ],
                "task_distribution": {
                    "repair": 200,
                    "monitoring": 100,
                    "assistance": 50
                },
                "work_hour_trends": [
                    {"week": 1, "hours": 280.5},
                    {"week": 2, "hours": 310.2}
                ]
            }
        }


class ComparisonReport(BaseModel):
    """对比报告模型"""
    
    current_period: Dict[str, Any] = Field(..., description="当前期间数据")
    previous_period: Dict[str, Any] = Field(..., description="对比期间数据")
    changes: Dict[str, Any] = Field(..., description="变化情况")
    trends: List[Dict[str, Any]] = Field(..., description="趋势分析")
    recommendations: List[str] = Field(..., description="改进建议")
    
    class Config:
        schema_extra = {
            "example": {
                "current_period": {
                    "period": "2025-01",
                    "avg_score": 82.5,
                    "completion_rate": 91.4
                },
                "previous_period": {
                    "period": "2024-12",
                    "avg_score": 79.8,
                    "completion_rate": 88.6
                },
                "changes": {
                    "score_change": 2.7,
                    "completion_rate_change": 2.8,
                    "improvement": True
                },
                "trends": [
                    {"metric": "avg_score", "trend": "上升", "rate": 3.4}
                ],
                "recommendations": [
                    "继续保持当前的管理方式",
                    "适当增加任务难度以提高成员能力"
                ]
            }
        }


class ReportGenerationRequest(BaseModel):
    """报告生成请求模型"""
    
    report_type: ReportType = Field(..., description="报告类型")
    year: int = Field(
        ..., 
        ge=2020, 
        le=2030,
        description="年份"
    )
    month: Optional[int] = Field(
        None, 
        ge=1, 
        le=12,
        description="月份（月度报告需要）"
    )
    quarter: Optional[int] = Field(
        None, 
        ge=1, 
        le=4,
        description="季度（季度报告需要）"
    )
    start_date: Optional[date] = Field(
        None,
        description="开始日期（自定义报告需要）"
    )
    end_date: Optional[date] = Field(
        None,
        description="结束日期（自定义报告需要）"
    )
    group_ids: Optional[List[int]] = Field(
        None,
        description="指定工作组（可选）"
    )
    member_ids: Optional[List[int]] = Field(
        None,
        description="指定成员（可选）"
    )
    include_comparison: bool = Field(
        default=True,
        description="是否包含对比分析"
    )
    export_format: ExportFormat = Field(
        default=ExportFormat.EXCEL,
        description="导出格式"
    )
    
    @root_validator
    def validate_report_params(cls, values):
        """验证报告参数"""
        report_type = values.get('report_type')
        month = values.get('month')
        quarter = values.get('quarter')
        start_date = values.get('start_date')
        end_date = values.get('end_date')
        
        if report_type == ReportType.MONTHLY and not month:
            raise ValueError('月度报告需要指定月份')
        
        if report_type == ReportType.QUARTERLY and not quarter:
            raise ValueError('季度报告需要指定季度')
        
        if report_type == ReportType.CUSTOM:
            if not start_date or not end_date:
                raise ValueError('自定义报告需要指定开始和结束日期')
            if start_date >= end_date:
                raise ValueError('开始日期必须早于结束日期')
        
        return values
    
    class Config:
        schema_extra = {
            "example": {
                "report_type": "monthly",
                "year": 2025,
                "month": 1,
                "group_ids": [1, 2],
                "include_comparison": True,
                "export_format": "excel"
            }
        }


class ReportGenerationResponse(BaseModel):
    """报告生成响应模型"""
    
    report_id: str = Field(..., description="报告ID")
    report_title: str = Field(..., description="报告标题")
    report_type: str = Field(..., description="报告类型")
    generation_time: datetime = Field(..., description="生成时间")
    file_url: Optional[str] = Field(None, description="文件下载链接")
    file_size: Optional[int] = Field(None, description="文件大小（字节）")
    expiry_time: Optional[datetime] = Field(None, description="下载链接过期时间")
    summary: Dict[str, Any] = Field(..., description="报告摘要")
    
    class Config:
        schema_extra = {
            "example": {
                "report_id": "RPT202501280001",
                "report_title": "2025年1月考勤统计报告",
                "report_type": "monthly",
                "generation_time": "2025-01-28T14:30:00",
                "file_url": "/api/v1/reports/download/RPT202501280001",
                "file_size": 1048576,
                "expiry_time": "2025-02-28T14:30:00",
                "summary": {
                    "total_members": 50,
                    "avg_score": 82.5,
                    "completion_rate": 91.4
                }
            }
        }


class DataExportRequest(BaseModel):
    """数据导出请求模型"""
    
    export_type: str = Field(
        ..., 
        regex="^(attendance|statistics|comparison|detailed)$",
        description="导出类型"
    )
    format: ExportFormat = Field(
        default=ExportFormat.EXCEL,
        description="导出格式"
    )
    filters: AttendanceSearchParams = Field(
        default=AttendanceSearchParams(),
        description="筛选条件"
    )
    include_charts: bool = Field(
        default=True,
        description="是否包含图表"
    )
    include_raw_data: bool = Field(
        default=False,
        description="是否包含原始数据"
    )
    
    class Config:
        schema_extra = {
            "example": {
                "export_type": "attendance",
                "format": "excel",
                "filters": {
                    "year": 2025,
                    "month": 1
                },
                "include_charts": True,
                "include_raw_data": False
            }
        }


class PerformanceMetrics(BaseModel):
    """绩效指标模型"""
    
    member_id: int = Field(..., description="成员ID")
    period: str = Field(..., description="统计期间")
    efficiency_score: float = Field(..., description="效率得分")
    quality_score: float = Field(..., description="质量得分")
    reliability_score: float = Field(..., description="可靠性得分")
    overall_score: float = Field(..., description="综合得分")
    task_completion_rate: float = Field(..., description="任务完成率")
    average_response_time: float = Field(..., description="平均响应时间（小时）")
    customer_satisfaction: float = Field(..., description="满意度评分")
    improvement_areas: List[str] = Field(..., description="改进建议")
    achievements: List[str] = Field(..., description="突出表现")
    
    class Config:
        schema_extra = {
            "example": {
                "member_id": 1,
                "period": "2025-01",
                "efficiency_score": 85.5,
                "quality_score": 88.2,
                "reliability_score": 92.0,
                "overall_score": 88.6,
                "task_completion_rate": 95.5,
                "average_response_time": 2.5,
                "customer_satisfaction": 4.2,
                "improvement_areas": [
                    "提高复杂任务处理效率",
                    "加强与用户的沟通技巧"
                ],
                "achievements": [
                    "本月零投诉记录",
                    "协助解决3起疑难问题"
                ]
            }
        }


class AttendanceCalculationRequest(BaseModel):
    """考勤计算请求模型"""
    
    member_id: int = Field(..., description="成员ID")
    year: int = Field(..., ge=2020, le=2030, description="年份")
    month: int = Field(..., ge=1, le=12, description="月份")
    recalculate: bool = Field(
        default=False,
        description="是否重新计算"
    )
    
    class Config:
        schema_extra = {
            "example": {
                "member_id": 1,
                "year": 2025,
                "month": 1,
                "recalculate": True
            }
        }


class AttendanceCalculationResult(BaseModel):
    """考勤计算结果模型"""
    
    success: bool = Field(..., description="计算是否成功")
    attendance_record: Optional[AttendanceResponse] = Field(None, description="考勤记录")
    calculation_details: Dict[str, Any] = Field(..., description="计算详情")
    warnings: List[str] = Field(default=[], description="警告信息")
    errors: List[str] = Field(default=[], description="错误信息")
    
    class Config:
        schema_extra = {
            "example": {
                "success": True,
                "attendance_record": None,
                "calculation_details": {
                    "tasks_processed": 15,
                    "base_hours": 25.0,
                    "bonus_hours": 3.5,
                    "penalty_hours": 1.0,
                    "final_score": 85.6
                },
                "warnings": ["任务T202501150003缺少评价信息"],
                "errors": []
            }
        }