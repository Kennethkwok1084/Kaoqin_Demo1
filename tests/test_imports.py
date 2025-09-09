"""
测试导入助手
统一管理测试中常用的导入，避免重复和遗漏
"""

# FastAPI相关
from fastapi import HTTPException, status
from fastapi.testclient import TestClient

# 测试相关
import pytest
from httpx import AsyncClient
from unittest.mock import AsyncMock, MagicMock, patch

# 业务异常
from app.core.exceptions import (
    ValidationError,
    NotFoundError,
    PermissionDeniedError,
    DatabaseError,
    AuthenticationError,
    BusinessLogicError,
    ExternalServiceError
)

# 数据模型
from app.models.member import Member, UserRole
from app.models.task import RepairTask, TaskStatus, TaskType, TaskCategory, TaskPriority
from app.models.attendance import AttendanceRecord

# 服务层
from app.services.attendance_service import AttendanceService
from app.services.stats_service import StatisticsService
from app.services.task_service import TaskService
from app.services.work_hours_service import WorkHoursService

# 应用
from app.main import app

__all__ = [
    # FastAPI
    'HTTPException', 'status', 'TestClient',
    
    # 测试工具
    'pytest', 'AsyncClient', 'AsyncMock', 'MagicMock', 'patch',
    
    # 异常
    'ValidationError', 'NotFoundError', 'PermissionDeniedError', 
    'DatabaseError', 'AuthenticationError', 'BusinessLogicError', 
    'ExternalServiceError',
    
    # 模型
    'Member', 'UserRole', 'RepairTask', 'TaskStatus', 'TaskType',
    'TaskCategory', 'TaskPriority', 'AttendanceRecord',
    
    # 服务
    'AttendanceService', 'StatisticsService', 'TaskService', 'WorkHoursService',
    
    # 应用
    'app'
]
