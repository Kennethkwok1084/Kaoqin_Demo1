"""
工时管理API路由
处理工时统计查看、月度汇总、数据导出等功能
基于任务完成情况计算和展示工时，而非传统的签到签退
"""

import logging
from datetime import datetime, date, timedelta
from typing import List, Optional, Dict, Any

from fastapi import APIRouter, Depends, HTTPException, Query, Path, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.models.member import Member
from app.core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter()


# 工时管理API - 基于任务完成的工时统计和展示

@router.get("/records", response_model=List[Dict[str, Any]], summary="获取工时记录")
async def get_work_hours_records(
    member_id: Optional[int] = Query(None, description="成员ID（管理员可查看其他人记录）"),
    date_from: Optional[date] = Query(None, description="开始日期"),
    date_to: Optional[date] = Query(None, description="结束日期"),
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=100, description="每页大小"),
    current_user: Member = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取工时记录列表（基于任务completion_time）
    
    - 显示任务完成后计算的工时记录
    - 普通员工只能查看自己的记录
    - 管理员可查看所有人的记录
    """
    try:
        from sqlalchemy import select, and_, or_
        from app.models.task import RepairTask, MonitoringTask, AssistanceTask
        from app.models.member import Member
        
        # 权限检查
        if member_id and member_id != current_user.id:
            if not current_user.is_admin:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="无权限查看其他人的工时记录"
                )
        
        # 如果没有指定member_id，默认查看当前用户的记录
        target_member_id = member_id or current_user.id
        
        # 构建时间范围过滤条件
        date_filters = []
        if date_from:
            date_from_dt = datetime.combine(date_from, datetime.min.time())
            date_filters.append(RepairTask.completion_time >= date_from_dt)
        if date_to:
            date_to_dt = datetime.combine(date_to, datetime.max.time())
            date_filters.append(RepairTask.completion_time <= date_to_dt)
        
        # 获取维修任务工时记录
        repair_query = select(
            RepairTask.id,
            RepairTask.title,
            RepairTask.completion_time.label('work_date'),
            RepairTask.work_minutes,
            RepairTask.task_type,
            RepairTask.rating,
            RepairTask.member_id,
            Member.name.label('member_name')
        ).join(Member).where(
            and_(
                RepairTask.member_id == target_member_id,
                RepairTask.status == 'COMPLETED',
                RepairTask.completion_time.isnot(None),
                *date_filters
            )
        ).order_by(RepairTask.completion_time.desc())
        
        repair_result = await db.execute(repair_query)
        repair_records = repair_result.fetchall()
        
        # 转换为统一格式
        work_records = []
        for record in repair_records:
            work_records.append({
                "id": record.id,
                "task_type": "维修任务",
                "title": record.title,
                "work_date": record.work_date.date() if record.work_date else None,
                "work_hours": round(record.work_minutes / 60, 2),
                "work_minutes": record.work_minutes,
                "task_category": record.task_type,
                "rating": record.rating,
                "member_id": record.member_id,
                "member_name": record.member_name,
                "source": "repair_task"
            })
        
        # 手动分页
        total_records = len(work_records)
        start_idx = (page - 1) * size
        end_idx = start_idx + size
        paginated_records = work_records[start_idx:end_idx]
        
        return paginated_records
        
    except Exception as e:
        logger.error(f"获取工时记录失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取工时记录失败"
        )




@router.get("/summary/{month}", response_model=Dict[str, Any], summary="获取月度工时汇总")
async def get_monthly_work_hours_summary(
    month: str = Path(..., description="月份，格式：YYYY-MM"),
    member_id: Optional[int] = Query(None, description="成员ID（管理员可查看其他人汇总）"),
    current_user: Member = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取指定月份的工时汇总统计
    
    - **month**: 月份格式为 YYYY-MM，如 2024-01
    - 基于任务完成时间统计当月工时
    """
    try:
        # 解析月份
        try:
            year, month_num = map(int, month.split('-'))
            # 获取月份的开始和结束时间
            from calendar import monthrange
            month_start = datetime(year, month_num, 1)
            month_end = datetime(year, month_num, monthrange(year, month_num)[1], 23, 59, 59)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="月份格式错误，请使用 YYYY-MM 格式"
            )
        
        # 权限检查
        if member_id and member_id != current_user.id:
            if not current_user.is_admin:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="无权限查看其他人的工时汇总"
                )
        
        target_member_id = member_id or current_user.id
        
        from sqlalchemy import select, func
        from app.models.task import RepairTask, MonitoringTask, AssistanceTask
        from app.models.member import Member
        
        # 获取成员信息
        member_query = select(Member).where(Member.id == target_member_id)
        member_result = await db.execute(member_query)
        member = member_result.scalar_one_or_none()
        
        if not member:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="成员不存在"
            )
        
        # 统计维修任务工时
        repair_query = select(
            func.sum(RepairTask.work_minutes).label('total_minutes'),
            func.count(RepairTask.id).label('task_count'),
            func.avg(RepairTask.rating).label('avg_rating')
        ).where(
            RepairTask.member_id == target_member_id,
            RepairTask.completion_time >= month_start,
            RepairTask.completion_time <= month_end,
            RepairTask.status == 'COMPLETED'
        )
        repair_result = await db.execute(repair_query)
        repair_stats = repair_result.fetchone()
        
        # 统计监控任务工时
        monitoring_query = select(
            func.sum(MonitoringTask.work_minutes).label('total_minutes'),
            func.count(MonitoringTask.id).label('task_count')
        ).where(
            MonitoringTask.member_id == target_member_id,
            MonitoringTask.end_time >= month_start,
            MonitoringTask.end_time <= month_end,
            MonitoringTask.status == 'COMPLETED'
        )
        monitoring_result = await db.execute(monitoring_query)
        monitoring_stats = monitoring_result.fetchone()
        
        # 统计协助任务工时
        assistance_query = select(
            func.sum(AssistanceTask.work_minutes).label('total_minutes'),
            func.count(AssistanceTask.id).label('task_count')
        ).where(
            AssistanceTask.member_id == target_member_id,
            AssistanceTask.end_time >= month_start,
            AssistanceTask.end_time <= month_end,
            AssistanceTask.status == 'COMPLETED'
        )
        assistance_result = await db.execute(assistance_query)
        assistance_stats = assistance_result.fetchone()
        
        # 计算总计
        repair_minutes = repair_stats.total_minutes or 0
        monitoring_minutes = monitoring_stats.total_minutes or 0
        assistance_minutes = assistance_stats.total_minutes or 0
        total_minutes = repair_minutes + monitoring_minutes + assistance_minutes
        
        return {
            "success": True,
            "message": "获取月度工时汇总成功",
            "data": {
                "member_id": target_member_id,
                "member_name": member.name,
                "year": year,
                "month": month_num,
                "month_string": f"{year:04d}-{month_num:02d}",
                "repair_tasks": {
                    "hours": round(repair_minutes / 60, 2),
                    "minutes": repair_minutes,
                    "task_count": repair_stats.task_count or 0,
                    "average_rating": round(repair_stats.avg_rating or 0, 2)
                },
                "monitoring_tasks": {
                    "hours": round(monitoring_minutes / 60, 2),
                    "minutes": monitoring_minutes,
                    "task_count": monitoring_stats.task_count or 0
                },
                "assistance_tasks": {
                    "hours": round(assistance_minutes / 60, 2),
                    "minutes": assistance_minutes,
                    "task_count": assistance_stats.task_count or 0
                },
                "total": {
                    "hours": round(total_minutes / 60, 2),
                    "minutes": total_minutes,
                    "task_count": (repair_stats.task_count or 0) + (monitoring_stats.task_count or 0) + (assistance_stats.task_count or 0)
                }
            },
            "status_code": 200
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取月度工时汇总失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取月度工时汇总失败"
        )




@router.get("/today-summary", response_model=Dict[str, Any], summary="获取今日工时统计概览")
@router.get("/today", response_model=Dict[str, Any], summary="获取今日工时统计概览（别名）")
async def get_today_work_hours_summary(
    current_user: Member = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取今日工时统计概览"""
    try:
        from sqlalchemy import select, func
        from app.models.task import RepairTask, MonitoringTask, AssistanceTask
        from app.models.member import Member
        
        today = datetime.now().date()
        today_start = datetime.combine(today, datetime.min.time())
        today_end = datetime.combine(today, datetime.max.time())
        
        # 获取今日完成的维修任务工时
        repair_hours_query = select(func.sum(RepairTask.work_minutes)).where(
            RepairTask.completion_time >= today_start,
            RepairTask.completion_time <= today_end,
            RepairTask.status == 'COMPLETED'
        )
        repair_result = await db.execute(repair_hours_query)
        repair_minutes = repair_result.scalar() or 0
        
        # 获取今日完成的监控任务工时
        monitoring_hours_query = select(func.sum(MonitoringTask.work_minutes)).where(
            MonitoringTask.end_time >= today_start,
            MonitoringTask.end_time <= today_end,
            MonitoringTask.status == 'COMPLETED'
        )
        monitoring_result = await db.execute(monitoring_hours_query)
        monitoring_minutes = monitoring_result.scalar() or 0
        
        # 获取今日完成的协助任务工时
        assistance_hours_query = select(func.sum(AssistanceTask.work_minutes)).where(
            AssistanceTask.end_time >= today_start,
            AssistanceTask.end_time <= today_end,
            AssistanceTask.status == 'COMPLETED'
        )
        assistance_result = await db.execute(assistance_hours_query)
        assistance_minutes = assistance_result.scalar() or 0
        
        # 转换为小时
        total_hours = (repair_minutes + monitoring_minutes + assistance_minutes) / 60
        repair_hours = repair_minutes / 60
        monitoring_hours = monitoring_minutes / 60
        assistance_hours = assistance_minutes / 60
        
        # 获取今日有工时记录的成员数
        active_members_query = select(func.count(func.distinct(RepairTask.member_id))).where(
            RepairTask.completion_time >= today_start,
            RepairTask.completion_time <= today_end,
            RepairTask.status == 'COMPLETED'
        )
        active_result = await db.execute(active_members_query)
        active_members = active_result.scalar() or 0
        
        # 获取总成员数
        total_members_query = select(func.count(Member.id)).where(
            Member.is_active == True
        )
        total_members_result = await db.execute(total_members_query)
        total_members = total_members_result.scalar() or 0
        
        return {
            "success": True,
            "message": "获取今日工时统计成功",
            "data": {
                "date": today.isoformat(),
                "total_members": total_members,
                "active_members": active_members,
                "total_hours": round(total_hours, 2),
                "repair_hours": round(repair_hours, 2),
                "monitoring_hours": round(monitoring_hours, 2),
                "assistance_hours": round(assistance_hours, 2),
                "average_hours": round(total_hours / active_members, 2) if active_members > 0 else 0,
                "participation_rate": round(active_members / total_members * 100, 1) if total_members > 0 else 0
            },
            "status_code": 200
        }
        
    except Exception as e:
        logger.error(f"获取今日工时统计失败: {str(e)}")
        return {
            "success": False,
            "message": "获取今日工时统计失败",
            "details": {"error": str(e)},
            "status_code": 500
        }




@router.get("/export", summary="导出工时数据")
async def export_work_hours_data(
    date_from: date = Query(..., description="开始日期"),
    date_to: date = Query(..., description="结束日期"),
    member_ids: Optional[List[int]] = Query(None, description="成员ID列表"),
    format: str = Query("excel", description="导出格式（excel/csv）"),
    current_user: Member = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    导出工时数据（管理员功能）
    
    - 导出基于任务完成的工时统计数据
    - 支持Excel和CSV格式导出
    """
    try:
        # 检查管理员权限
        if not current_user.is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="只有管理员可以导出工时数据"
            )
        
        from sqlalchemy import select, and_
        from app.models.task import RepairTask, MonitoringTask, AssistanceTask
        from app.models.member import Member
        import pandas as pd
        import io
        import tempfile
        import os
        from datetime import datetime as dt
        
        # 构建时间范围
        date_from_dt = datetime.combine(date_from, datetime.min.time())
        date_to_dt = datetime.combine(date_to, datetime.max.time())
        
        # 构建成员过滤条件
        member_filter = []
        if member_ids:
            member_filter.append(RepairTask.member_id.in_(member_ids))
        
        # 获取维修任务数据
        repair_query = select(
            RepairTask.id,
            RepairTask.task_id,
            RepairTask.title,
            RepairTask.completion_time,
            RepairTask.work_minutes,
            RepairTask.task_type,
            RepairTask.rating,
            RepairTask.member_id,
            Member.name.label('member_name')
        ).join(Member).where(
            and_(
                RepairTask.completion_time >= date_from_dt,
                RepairTask.completion_time <= date_to_dt,
                RepairTask.status == 'COMPLETED',
                *member_filter
            )
        ).order_by(RepairTask.completion_time.desc())
        
        repair_result = await db.execute(repair_query)
        repair_records = repair_result.fetchall()
        
        # 转换为DataFrame
        export_data = []
        for record in repair_records:
            export_data.append({
                "任务ID": record.task_id,
                "任务标题": record.title,
                "任务类型": "维修任务",
                "完成时间": record.completion_time.strftime('%Y-%m-%d %H:%M:%S') if record.completion_time else '',
                "工时(小时)": round(record.work_minutes / 60, 2),
                "工时(分钟)": record.work_minutes,
                "任务分类": record.task_type,
                "用户评分": record.rating or 0,
                "成员ID": record.member_id,
                "成员姓名": record.member_name,
                "导出时间": dt.now().strftime('%Y-%m-%d %H:%M:%S')
            })
        
        if not export_data:
            return {
                "success": True,
                "message": "没有找到符合条件的工时数据",
                "total_records": 0
            }
        
        df = pd.DataFrame(export_data)
        
        # 生成文件
        timestamp = dt.now().strftime('%Y%m%d_%H%M%S')
        if format.lower() == 'csv':
            filename = f"work_hours_export_{timestamp}.csv"
            # 创建临时文件
            with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv', encoding='utf-8-sig') as tmp_file:
                df.to_csv(tmp_file.name, index=False, encoding='utf-8-sig')
                temp_path = tmp_file.name
        else:
            filename = f"work_hours_export_{timestamp}.xlsx"
            # 创建临时文件
            with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp_file:
                df.to_excel(tmp_file.name, index=False, engine='openpyxl', sheet_name='工时统计')
                temp_path = tmp_file.name
        
        return {
            "success": True,
            "message": "工时数据导出成功",
            "filename": filename,
            "total_records": len(export_data),
            "download_url": f"/api/v1/attendance/download/{filename}",
            "expires_at": (dt.now().timestamp() + 3600)  # 1小时后过期
        }
        
    except Exception as e:
        logger.error(f"导出工时数据失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="导出工时数据失败"
        )


@router.get("/stats", response_model=Dict[str, Any], summary="获取工时统计")
async def get_work_hours_stats(
    memberId: Optional[int] = Query(None, description="成员ID"),
    startDate: str = Query(..., description="开始日期 YYYY-MM-DD"),
    endDate: str = Query(..., description="结束日期 YYYY-MM-DD"),
    current_user: Member = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取指定时间范围内的工时统计数据
    """
    try:
        from sqlalchemy import select, func
        from app.models.task import RepairTask, MonitoringTask, AssistanceTask
        from app.models.member import Member
        
        # 解析日期
        try:
            start_date = datetime.strptime(startDate, '%Y-%m-%d').date()
            end_date = datetime.strptime(endDate, '%Y-%m-%d').date()
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="日期格式错误，请使用 YYYY-MM-DD 格式"
            )
        
        start_datetime = datetime.combine(start_date, datetime.min.time())
        end_datetime = datetime.combine(end_date, datetime.max.time())
        
        # 权限检查
        if memberId and memberId != current_user.id:
            if not current_user.is_admin:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="无权限查看其他人的工时统计"
                )
        
        target_member_id = memberId or current_user.id
        
        # 统计维修任务工时
        repair_query = select(
            func.sum(RepairTask.work_minutes).label('total_minutes'),
            func.count(RepairTask.id).label('task_count'),
            func.avg(RepairTask.rating).label('avg_rating'),
            func.min(RepairTask.work_minutes).label('min_minutes'),
            func.max(RepairTask.work_minutes).label('max_minutes')
        ).where(
            RepairTask.member_id == target_member_id,
            RepairTask.completion_time >= start_datetime,
            RepairTask.completion_time <= end_datetime,
            RepairTask.status == 'COMPLETED'
        )
        
        repair_result = await db.execute(repair_query)
        repair_stats = repair_result.fetchone()
        
        # 获取成员信息
        member_query = select(Member).where(Member.id == target_member_id)
        member_result = await db.execute(member_query)
        member = member_result.scalar_one_or_none()
        
        if not member:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="成员不存在"
            )
        
        # 计算统计数据
        total_minutes = repair_stats.total_minutes or 0
        task_count = repair_stats.task_count or 0
        avg_rating = repair_stats.avg_rating or 0
        min_minutes = repair_stats.min_minutes or 0
        max_minutes = repair_stats.max_minutes or 0
        
        return {
            "success": True,
            "message": "获取工时统计成功",
            "data": {
                "member_id": target_member_id,
                "member_name": member.name,
                "period": {
                    "start_date": startDate,
                    "end_date": endDate
                },
                "total_hours": round(total_minutes / 60, 2),
                "total_minutes": total_minutes,
                "task_count": task_count,
                "average_hours_per_task": round(total_minutes / task_count / 60, 2) if task_count > 0 else 0,
                "average_rating": round(avg_rating, 2),
                "min_hours_per_task": round(min_minutes / 60, 2),
                "max_hours_per_task": round(max_minutes / 60, 2),
                "working_days": (end_date - start_date).days + 1,
                "average_daily_hours": round(total_minutes / ((end_date - start_date).days + 1) / 60, 2)
            },
            "status_code": 200
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取工时统计失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取工时统计失败"
        )


@router.get("/chart-data", response_model=Dict[str, Any], summary="获取工时图表数据")
async def get_work_hours_chart_data(
    type: str = Query(..., description="图表类型: daily/weekly/monthly"),
    startDate: str = Query(..., description="开始日期 YYYY-MM-DD"),
    endDate: str = Query(..., description="结束日期 YYYY-MM-DD"),
    memberId: Optional[int] = Query(None, description="成员ID"),
    current_user: Member = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取工时图表数据，支持按日、周、月聚合
    """
    try:
        from sqlalchemy import select, func, text
        from app.models.task import RepairTask
        from app.models.member import Member
        import calendar
        
        # 验证图表类型
        if type not in ['daily', 'weekly', 'monthly']:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="图表类型必须是 daily、weekly 或 monthly"
            )
        
        # 解析日期
        try:
            start_date = datetime.strptime(startDate, '%Y-%m-%d').date()
            end_date = datetime.strptime(endDate, '%Y-%m-%d').date()
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="日期格式错误，请使用 YYYY-MM-DD 格式"
            )
        
        start_datetime = datetime.combine(start_date, datetime.min.time())
        end_datetime = datetime.combine(end_date, datetime.max.time())
        
        # 权限检查
        if memberId and memberId != current_user.id:
            if not current_user.is_admin:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="无权限查看其他人的工时图表"
                )
        
        # 构建查询条件
        query_conditions = [
            RepairTask.completion_time >= start_datetime,
            RepairTask.completion_time <= end_datetime,
            RepairTask.status == 'COMPLETED'
        ]
        
        if memberId:
            query_conditions.append(RepairTask.member_id == memberId)
        
        # 根据图表类型构建查询
        if type == 'daily':
            # 按日期分组
            chart_query = select(
                func.date(RepairTask.completion_time).label('period'),
                func.sum(RepairTask.work_minutes).label('total_minutes'),
                func.count(RepairTask.id).label('task_count')
            ).where(
                *query_conditions
            ).group_by(
                func.date(RepairTask.completion_time)
            ).order_by(
                func.date(RepairTask.completion_time)
            )
            
        elif type == 'weekly':
            # 按周分组 (ISO周)
            chart_query = select(
                func.concat(
                    func.extract('year', RepairTask.completion_time),
                    '-W',
                    func.lpad(func.extract('week', RepairTask.completion_time).cast(text('varchar')), 2, '0')
                ).label('period'),
                func.sum(RepairTask.work_minutes).label('total_minutes'),
                func.count(RepairTask.id).label('task_count')
            ).where(
                *query_conditions
            ).group_by(
                func.extract('year', RepairTask.completion_time),
                func.extract('week', RepairTask.completion_time)
            ).order_by(
                func.extract('year', RepairTask.completion_time),
                func.extract('week', RepairTask.completion_time)
            )
            
        else:  # monthly
            # 按月分组
            chart_query = select(
                func.concat(
                    func.extract('year', RepairTask.completion_time),
                    '-',
                    func.lpad(func.extract('month', RepairTask.completion_time).cast(text('varchar')), 2, '0')
                ).label('period'),
                func.sum(RepairTask.work_minutes).label('total_minutes'),
                func.count(RepairTask.id).label('task_count')
            ).where(
                *query_conditions
            ).group_by(
                func.extract('year', RepairTask.completion_time),
                func.extract('month', RepairTask.completion_time)
            ).order_by(
                func.extract('year', RepairTask.completion_time),
                func.extract('month', RepairTask.completion_time)
            )
        
        chart_result = await db.execute(chart_query)
        chart_data = chart_result.fetchall()
        
        # 格式化数据
        labels = []
        hours_data = []
        task_counts = []
        
        for row in chart_data:
            labels.append(str(row.period))
            hours_data.append(round((row.total_minutes or 0) / 60, 2))
            task_counts.append(row.task_count or 0)
        
        return {
            "success": True,
            "message": "获取图表数据成功",
            "data": {
                "type": type,
                "period": {
                    "start_date": startDate,
                    "end_date": endDate
                },
                "chart": {
                    "labels": labels,
                    "datasets": [
                        {
                            "label": "工时(小时)",
                            "data": hours_data,
                            "backgroundColor": "#409EFF",
                            "borderColor": "#409EFF",
                            "type": "line" if type == "daily" else "bar"
                        },
                        {
                            "label": "任务数量",
                            "data": task_counts,
                            "backgroundColor": "#67C23A",
                            "borderColor": "#67C23A",
                            "type": "bar",
                            "yAxisID": "y1"
                        }
                    ]
                },
                "summary": {
                    "total_hours": sum(hours_data),
                    "total_tasks": sum(task_counts),
                    "average_hours": round(sum(hours_data) / len(hours_data), 2) if hours_data else 0,
                    "periods": len(labels)
                }
            },
            "status_code": 200
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取图表数据失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取图表数据失败"
        )


@router.get("/health", response_model=Dict[str, Any], summary="健康检查")
async def health_check():
    """
    工时管理服务健康检查
    """
    from datetime import datetime
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "work_hours_management",
        "message": "工时管理服务运行正常"
    }