"""
仪表板相关的数据模式
"""

from typing import List, Optional

from pydantic import BaseModel


class MetricsData(BaseModel):
    """指标数据"""

    totalTasks: int
    inProgress: int
    pending: int
    completedThisMonth: int
    systemStatus: str


class TrendData(BaseModel):
    """趋势数据"""

    value: float
    direction: str


class TrendsData(BaseModel):
    """趋势数据集合"""

    totalTasksTrend: TrendData
    inProgressTrend: TrendData
    pendingTrend: TrendData
    completedTrend: TrendData


class SystemInfo(BaseModel):
    """系统信息"""

    onlineUsers: int
    lastDataSync: str
    systemUptime: str


class DashboardOverviewResponse(BaseModel):
    """仪表板概览响应"""

    metrics: MetricsData
    trends: TrendsData
    systemInfo: SystemInfo


class TaskSummary(BaseModel):
    """任务汇总"""

    id: int
    title: str
    status: str
    priority: str
    location: str
    createdAt: Optional[str] = None
    dueDate: Optional[str] = None


class TaskStats(BaseModel):
    """任务统计"""

    totalAssigned: int
    pending: int
    inProgress: int
    completed: int


class DashboardTasksResponse(BaseModel):
    """我的任务响应"""

    tasks: List[TaskSummary]
    summary: TaskStats


class Activity(BaseModel):
    """活动记录"""

    id: int
    type: str
    title: str
    description: str
    actorName: str
    actorId: str
    targetId: Optional[int] = None
    targetType: Optional[str] = None
    createdAt: str
    priority: str


class ActivitySummary(BaseModel):
    """活动汇总"""

    total: int
    todayCount: int


class DashboardActivitiesResponse(BaseModel):
    """最近活动响应"""

    activities: List[Activity]
    summary: ActivitySummary
