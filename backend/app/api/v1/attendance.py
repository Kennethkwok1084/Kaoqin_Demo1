"""
考勤记录管理API路由
处理签到签退、考勤记录查询、考勤统计等功能
"""

import logging
from datetime import datetime, date, timedelta
from typing import List, Optional, Dict, Any

from fastapi import APIRouter, Depends, HTTPException, Query, Path, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.models.member import Member
from app.schemas.attendance import (
    AttendanceRecordCreate, AttendanceRecordUpdate, AttendanceRecordResponse,
    AttendanceCheckInRequest, AttendanceCheckOutRequest, AttendanceCheckInResponse,
    AttendanceExceptionRequest, AttendanceExceptionResponse, AttendanceExceptionUpdate,
    AttendanceSummaryResponse, AttendanceStatisticsResponse
)
from app.services.attendance_service import AttendanceService
from app.core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/checkin", response_model=AttendanceCheckInResponse, summary="签到")
async def check_in(
    request: AttendanceCheckInRequest,
    current_user: Member = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    员工签到
    
    - **location**: 签到地点（可选）
    - **notes**: 签到备注（可选）
    - **checkin_time**: 签到时间（可选，默认为当前时间）
    """
    try:
        service = AttendanceService(db)
        
        # 如果没有指定签到时间，使用当前时间
        checkin_time = request.checkin_time or datetime.utcnow()
        
        record = await service.check_in(
            member_id=current_user.id,
            checkin_time=checkin_time,
            location=request.location,
            notes=request.notes
        )
        
        return AttendanceCheckInResponse(
            success=True,
            message="签到成功",
            record_id=record.id,
            checkin_time=record.checkin_time,
            location=record.location,
            is_late=record.is_late_checkin,
            late_minutes=record.late_checkin_minutes or 0
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Check-in error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="签到失败，请重试"
        )


@router.post("/checkout", response_model=AttendanceCheckInResponse, summary="签退")
async def check_out(
    request: AttendanceCheckOutRequest,
    current_user: Member = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    员工签退
    
    - **location**: 签退地点（可选）
    - **notes**: 签退备注（可选）
    - **checkout_time**: 签退时间（可选，默认为当前时间）
    """
    try:
        service = AttendanceService(db)
        
        # 如果没有指定签退时间，使用当前时间
        checkout_time = request.checkout_time or datetime.utcnow()
        
        record = await service.check_out(
            member_id=current_user.id,
            checkout_time=checkout_time,
            location=request.location,
            notes=request.notes
        )
        
        return AttendanceCheckInResponse(
            success=True,
            message="签退成功",
            record_id=record.id,
            checkin_time=record.checkin_time,
            checkout_time=record.checkout_time,
            location=record.location,
            work_hours=record.work_hours,
            is_early_checkout=record.is_early_checkout,
            early_checkout_minutes=record.early_checkout_minutes or 0
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Check-out error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="签退失败，请重试"
        )


@router.get("/records", response_model=List[AttendanceRecordResponse], summary="获取考勤记录")
async def get_attendance_records(
    member_id: Optional[int] = Query(None, description="成员ID（管理员可查看其他人记录）"),
    date_from: Optional[date] = Query(None, description="开始日期"),
    date_to: Optional[date] = Query(None, description="结束日期"),
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=100, description="每页大小"),
    current_user: Member = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取考勤记录列表
    
    - 普通员工只能查看自己的记录
    - 管理员可查看所有人的记录
    """
    try:
        service = AttendanceService(db)
        
        # 权限检查
        if member_id and member_id != current_user.id:
            if not current_user.is_admin:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="无权限查看其他人的考勤记录"
                )
        
        # 如果没有指定member_id，默认查看当前用户的记录
        target_member_id = member_id or current_user.id
        
        records = await service.get_attendance_records(
            member_id=target_member_id,
            date_from=date_from,
            date_to=date_to,
            page=page,
            size=size
        )
        
        return [AttendanceRecordResponse.from_orm(record) for record in records]
        
    except Exception as e:
        logger.error(f"Get attendance records error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取考勤记录失败"
        )


@router.get("/records/{record_id}", response_model=AttendanceRecordResponse, summary="获取考勤记录详情")
async def get_attendance_record(
    record_id: int,
    current_user: Member = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取指定考勤记录的详细信息"""
    try:
        service = AttendanceService(db)
        
        record = await service.get_attendance_record_by_id(record_id)
        
        if not record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="考勤记录不存在"
            )
        
        # 权限检查
        if record.member_id != current_user.id and not current_user.is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权限查看此考勤记录"
            )
        
        return AttendanceRecordResponse.from_orm(record)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get attendance record error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取考勤记录详情失败"
        )


@router.get("/summary/{month}", response_model=AttendanceSummaryResponse, summary="获取月度考勤汇总")
async def get_monthly_summary(
    month: str = Path(..., description="月份，格式：YYYY-MM"),
    member_id: Optional[int] = Query(None, description="成员ID（管理员可查看其他人汇总）"),
    current_user: Member = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取指定月份的考勤汇总
    
    - **month**: 月份格式为 YYYY-MM，如 2024-01
    """
    try:
        # 解析月份
        try:
            year, month_num = map(int, month.split('-'))
            target_date = date(year, month_num, 1)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="月份格式错误，请使用 YYYY-MM 格式"
            )
        
        service = AttendanceService(db)
        
        # 权限检查
        if member_id and member_id != current_user.id:
            if not current_user.is_admin:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="无权限查看其他人的考勤汇总"
                )
        
        target_member_id = member_id or current_user.id
        
        summary = await service.get_monthly_summary(
            member_id=target_member_id,
            year=year,
            month=month_num
        )
        
        return summary
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get monthly summary error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取月度汇总失败"
        )


@router.post("/exception", response_model=AttendanceExceptionResponse, summary="申请考勤异常处理")
async def create_attendance_exception(
    request: AttendanceExceptionRequest,
    current_user: Member = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    申请考勤异常处理
    
    - **exception_type**: 异常类型（迟到、早退、忘记打卡、请假等）
    - **exception_date**: 异常日期
    - **reason**: 申请理由
    - **supporting_documents**: 支持材料（可选）
    """
    try:
        service = AttendanceService(db)
        
        exception_record = await service.create_attendance_exception(
            member_id=current_user.id,
            exception_type=request.exception_type,
            exception_date=request.exception_date,
            reason=request.reason,
            supporting_documents=request.supporting_documents
        )
        
        return AttendanceExceptionResponse.from_orm(exception_record)
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Create attendance exception error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="申请考勤异常处理失败"
        )


@router.get("/exceptions", response_model=List[AttendanceExceptionResponse], summary="获取考勤异常申请列表")
async def get_attendance_exceptions(
    member_id: Optional[int] = Query(None, description="成员ID（管理员可查看所有申请）"),
    status_filter: Optional[str] = Query(None, description="状态筛选（pending/approved/rejected）"),
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=100, description="每页大小"),
    current_user: Member = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取考勤异常申请列表"""
    try:
        service = AttendanceService(db)
        
        # 权限检查
        if member_id and member_id != current_user.id:
            if not current_user.is_admin:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="无权限查看其他人的考勤异常申请"
                )
        
        target_member_id = member_id or current_user.id
        
        exceptions = await service.get_attendance_exceptions(
            member_id=target_member_id if not current_user.is_admin else None,
            status_filter=status_filter,
            page=page,
            size=size
        )
        
        return [AttendanceExceptionResponse.from_orm(exc) for exc in exceptions]
        
    except Exception as e:
        logger.error(f"Get attendance exceptions error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取考勤异常申请失败"
        )


@router.put("/exception/{exception_id}", response_model=AttendanceExceptionResponse, summary="处理考勤异常申请")
async def update_attendance_exception(
    exception_id: int,
    request: AttendanceExceptionUpdate,
    current_user: Member = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    处理考勤异常申请（管理员功能）
    
    - **status**: 处理结果（approved/rejected）
    - **reviewer_comments**: 审核意见
    """
    try:
        # 检查管理员权限
        if not current_user.is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="只有管理员可以处理考勤异常申请"
            )
        
        service = AttendanceService(db)
        
        exception_record = await service.update_attendance_exception(
            exception_id=exception_id,
            status=request.status,
            reviewer_id=current_user.id,
            reviewer_comments=request.reviewer_comments
        )
        
        return AttendanceExceptionResponse.from_orm(exception_record)
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Update attendance exception error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="处理考勤异常申请失败"
        )


@router.get("/statistics", response_model=AttendanceStatisticsResponse, summary="获取考勤统计信息")
async def get_attendance_statistics(
    date_from: Optional[date] = Query(None, description="开始日期"),
    date_to: Optional[date] = Query(None, description="结束日期"),
    department_id: Optional[int] = Query(None, description="部门ID筛选"),
    current_user: Member = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取考勤统计信息（管理员功能）
    
    包括出勤率、迟到早退统计、异常申请统计等
    """
    try:
        # 检查管理员权限
        if not current_user.is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="只有管理员可以查看考勤统计信息"
            )
        
        service = AttendanceService(db)
        
        # 如果没有指定日期范围，默认查看当月
        if not date_from:
            today = date.today()
            date_from = date(today.year, today.month, 1)
        
        if not date_to:
            date_to = date.today()
        
        statistics = await service.get_attendance_statistics(
            date_from=date_from,
            date_to=date_to,
            department_id=department_id
        )
        
        return statistics
        
    except Exception as e:
        logger.error(f"Get attendance statistics error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取考勤统计信息失败"
        )


@router.get("/today", response_model=AttendanceRecordResponse, summary="获取今日考勤状态")
async def get_today_attendance(
    current_user: Member = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取当前用户今日的考勤状态"""
    try:
        service = AttendanceService(db)
        
        today_record = await service.get_today_attendance(current_user.id)
        
        if today_record:
            return AttendanceRecordResponse.from_orm(today_record)
        else:
            # 返回空的考勤记录表示未签到
            return AttendanceRecordResponse(
                id=0,
                member_id=current_user.id,
                attendance_date=date.today(),
                checkin_time=None,
                checkout_time=None,
                work_hours=0.0,
                status="未签到",
                location=None,
                notes=None,
                is_late_checkin=False,
                is_early_checkout=False,
                late_checkin_minutes=0,
                early_checkout_minutes=0,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
        
    except Exception as e:
        logger.error(f"Get today attendance error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取今日考勤状态失败"
        )


@router.post("/bulk-import", summary="批量导入考勤记录")
async def bulk_import_attendance(
    import_data: List[AttendanceRecordCreate],
    current_user: Member = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    批量导入考勤记录（管理员功能）
    
    用于从外部系统迁移考勤数据或批量补录考勤记录
    """
    try:
        # 检查管理员权限
        if not current_user.is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="只有管理员可以批量导入考勤记录"
            )
        
        service = AttendanceService(db)
        
        result = await service.bulk_import_attendance(import_data, current_user.id)
        
        return {
            "success": True,
            "message": "批量导入完成",
            "summary": result
        }
        
    except Exception as e:
        logger.error(f"Bulk import attendance error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="批量导入考勤记录失败"
        )


@router.get("/export", summary="导出考勤数据")
async def export_attendance_data(
    date_from: date = Query(..., description="开始日期"),
    date_to: date = Query(..., description="结束日期"),
    member_ids: Optional[List[int]] = Query(None, description="成员ID列表"),
    format: str = Query("excel", description="导出格式（excel/csv）"),
    current_user: Member = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    导出考勤数据（管理员功能）
    
    支持Excel和CSV格式导出
    """
    try:
        # 检查管理员权限
        if not current_user.is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="只有管理员可以导出考勤数据"
            )
        
        service = AttendanceService(db)
        
        export_result = await service.export_attendance_data(
            date_from=date_from,
            date_to=date_to,
            member_ids=member_ids,
            format=format
        )
        
        return {
            "success": True,
            "download_url": export_result["download_url"],
            "filename": export_result["filename"],
            "total_records": export_result["total_records"],
            "expires_at": export_result["expires_at"]
        }
        
    except Exception as e:
        logger.error(f"Export attendance data error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="导出考勤数据失败"
        )