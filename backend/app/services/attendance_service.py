"""
考勤服务
处理考勤相关的业务逻辑
"""

import logging
from calendar import monthrange
from datetime import date, datetime, time, timedelta
from typing import Any, Dict, List, Optional

from sqlalchemy import and_, desc, extract, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.models.attendance import (
    AttendanceException,
    AttendanceExceptionStatus,
    AttendanceRecord,
)
from app.models.member import Member
from app.schemas.attendance import (
    AttendanceRecordCreate,
    AttendanceStatisticsResponse,
    AttendanceSummaryResponse,
)
from app.services.work_hours_service import WorkHoursCalculationService

logger = logging.getLogger(__name__)


class AttendanceService:
    """考勤服务"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.work_hours_service = WorkHoursCalculationService(db)

        # 考勤配置
        self.work_start_time = time(9, 0)  # 上班时间 09:00
        self.work_end_time = time(18, 0)  # 下班时间 18:00
        self.lunch_start_time = time(12, 0)  # 午休开始 12:00
        self.lunch_end_time = time(13, 0)  # 午休结束 13:00
        self.late_threshold_minutes = 15  # 迟到阈值（分钟）
        self.early_threshold_minutes = 30  # 早退阈值（分钟）

    async def check_in(
        self,
        member_id: int,
        checkin_time: datetime,
        location: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> AttendanceRecord:
        """
        员工签到

        Args:
            member_id: 员工ID
            checkin_time: 签到时间
            location: 签到地点
            notes: 签到备注

        Returns:
            AttendanceRecord: 考勤记录
        """
        try:
            # 检查今天是否已经签到
            today = checkin_time.date()
            existing_query = select(AttendanceRecord).where(
                and_(
                    AttendanceRecord.member_id == member_id,
                    AttendanceRecord.attendance_date == today,
                )
            )
            existing_result = await self.db.execute(existing_query)
            existing_record = existing_result.scalar_one_or_none()

            if existing_record:
                if existing_record.checkin_time:
                    raise ValueError("今日已签到，无法重复签到")
                else:
                    # 更新现有记录的签到时间
                    existing_record.checkin_time = checkin_time
                    existing_record.location = location or existing_record.location
                    existing_record.notes = notes or existing_record.notes
                    record = existing_record
            else:
                # 创建新的考勤记录
                record = AttendanceRecord(
                    member_id=member_id,
                    attendance_date=today,
                    checkin_time=checkin_time,
                    location=location,
                    notes=notes,
                )
                self.db.add(record)

            # 计算是否迟到
            self._calculate_late_checkin(record)

            # 更新状态
            record.status = "已签到"
            record.updated_at = datetime.utcnow()

            await self.db.commit()
            await self.db.refresh(record)

            logger.info(f"Member {member_id} checked in at {checkin_time}")
            return record

        except Exception as e:
            await self.db.rollback()
            logger.error(f"Check-in error: {str(e)}")
            raise

    async def check_out(
        self,
        member_id: int,
        checkout_time: datetime,
        location: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> AttendanceRecord:
        """
        员工签退

        Args:
            member_id: 员工ID
            checkout_time: 签退时间
            location: 签退地点
            notes: 签退备注

        Returns:
            AttendanceRecord: 考勤记录
        """
        try:
            # 查找今天的考勤记录
            today = checkout_time.date()
            query = select(AttendanceRecord).where(
                and_(
                    AttendanceRecord.member_id == member_id,
                    AttendanceRecord.attendance_date == today,
                )
            )
            result = await self.db.execute(query)
            record = result.scalar_one_or_none()

            if not record:
                raise ValueError("今日未签到，无法签退")

            if record.checkout_time:
                raise ValueError("今日已签退，无法重复签退")

            if not record.checkin_time:
                raise ValueError("今日未签到，无法签退")

            # 更新签退信息
            record.checkout_time = checkout_time
            if location:
                record.location = location
            if notes:
                if record.notes:
                    record.notes += f" | 签退备注: {notes}"
                else:
                    record.notes = f"签退备注: {notes}"

            # 计算工作时长和是否早退
            self._calculate_work_hours(record)
            self._calculate_early_checkout(record)

            # 更新状态
            record.status = "已签退"
            record.updated_at = datetime.utcnow()

            await self.db.commit()
            await self.db.refresh(record)

            logger.info(f"Member {member_id} checked out at {checkout_time}")
            return record

        except Exception as e:
            await self.db.rollback()
            logger.error(f"Check-out error: {str(e)}")
            raise

    async def get_attendance_records(
        self,
        member_id: Optional[int] = None,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
        page: int = 1,
        size: int = 20,
    ) -> List[AttendanceRecord]:
        """
        获取考勤记录列表

        Args:
            member_id: 员工ID
            date_from: 开始日期
            date_to: 结束日期
            page: 页码
            size: 每页大小

        Returns:
            List[AttendanceRecord]: 考勤记录列表
        """
        try:
            query = select(AttendanceRecord).options(
                joinedload(AttendanceRecord.member)
            )

            # 添加筛选条件
            if member_id:
                query = query.where(AttendanceRecord.member_id == member_id)

            if date_from:
                query = query.where(AttendanceRecord.attendance_date >= date_from)

            if date_to:
                query = query.where(AttendanceRecord.attendance_date <= date_to)

            # 排序和分页
            query = query.order_by(desc(AttendanceRecord.attendance_date))
            query = query.offset((page - 1) * size).limit(size)

            result = await self.db.execute(query)
            records = result.scalars().all()

            return list(records)

        except Exception as e:
            logger.error(f"Get attendance records error: {str(e)}")
            raise

    async def get_attendance_record_by_id(
        self, record_id: int
    ) -> Optional[AttendanceRecord]:
        """根据ID获取考勤记录"""
        try:
            query = (
                select(AttendanceRecord)
                .options(joinedload(AttendanceRecord.member))
                .where(AttendanceRecord.id == record_id)
            )

            result = await self.db.execute(query)
            return result.scalar_one_or_none()

        except Exception as e:
            logger.error(f"Get attendance record by ID error: {str(e)}")
            raise

    async def get_today_attendance(self, member_id: int) -> Optional[AttendanceRecord]:
        """获取今日考勤状态"""
        try:
            today = date.today()
            query = select(AttendanceRecord).where(
                and_(
                    AttendanceRecord.member_id == member_id,
                    AttendanceRecord.attendance_date == today,
                )
            )

            result = await self.db.execute(query)
            return result.scalar_one_or_none()

        except Exception as e:
            logger.error(f"Get today attendance error: {str(e)}")
            raise

    async def get_monthly_summary(
        self, member_id: int, year: int, month: int
    ) -> AttendanceSummaryResponse:
        """
        获取月度考勤汇总（集成新的工时计算逻辑）

        Args:
            member_id: 员工ID
            year: 年份
            month: 月份

        Returns:
            AttendanceSummaryResponse: 月度汇总数据
        """
        try:
            # 获取或更新月度工时汇总
            monthly_summary = await self.work_hours_service.update_monthly_summary(
                member_id, year, month
            )

            # 计算月份的第一天和最后一天
            first_day = date(year, month, 1)
            last_day = date(year, month, monthrange(year, month)[1])

            # 查询该月的所有考勤记录
            query = (
                select(AttendanceRecord)
                .where(
                    and_(
                        AttendanceRecord.member_id == member_id,
                        AttendanceRecord.attendance_date >= first_day,
                        AttendanceRecord.attendance_date <= last_day,
                    )
                )
                .order_by(AttendanceRecord.attendance_date)
            )

            result = await self.db.execute(query)
            records = result.scalars().all()

            # 统计计算
            total_work_days = len([r for r in records if r.checkin_time])
            total_attendance_hours = sum(r.work_hours or 0 for r in records)
            total_late_days = len([r for r in records if r.is_late_checkin])
            total_early_days = len([r for r in records if r.is_early_checkout])
            total_late_minutes = sum(r.late_checkin_minutes or 0 for r in records)
            total_early_minutes = sum(r.early_checkout_minutes or 0 for r in records)

            # 计算应出勤天数（工作日）
            expected_work_days = self._calculate_work_days_in_month(year, month)

            # 计算出勤率
            attendance_rate = (
                (total_work_days / expected_work_days * 100)
                if expected_work_days > 0
                else 0
            )

            # 查询异常申请
            exception_query = select(AttendanceException).where(
                and_(
                    AttendanceException.member_id == member_id,
                    extract("year", AttendanceException.exception_date) == year,
                    extract("month", AttendanceException.exception_date) == month,
                )
            )
            exception_result = await self.db.execute(exception_query)
            exceptions = exception_result.scalars().all()

            exception_summary = {}
            for exc in exceptions:
                exc_type = exc.exception_type
                if exc_type not in exception_summary:
                    exception_summary[exc_type] = {
                        "count": 0,
                        "approved": 0,
                        "rejected": 0,
                        "pending": 0,
                    }
                exception_summary[exc_type]["count"] += 1
                exception_summary[exc_type][exc.status.value] += 1

            # 构建响应，包含新的工时分类数据
            return AttendanceSummaryResponse(
                member_id=member_id,
                year=year,
                month=month,
                total_work_days=total_work_days,
                expected_work_days=expected_work_days,
                attendance_rate=round(attendance_rate, 2),
                # 使用新的工时计算结果
                total_work_hours=round(float(monthly_summary.total_hours or 0), 2),
                repair_task_hours=round(
                    float(monthly_summary.repair_task_hours or 0), 2
                ),
                monitoring_hours=round(float(monthly_summary.monitoring_hours or 0), 2),
                assistance_hours=round(float(monthly_summary.assistance_hours or 0), 2),
                carried_hours=round(float(monthly_summary.carried_hours or 0), 2),
                remaining_hours=round(float(monthly_summary.remaining_hours or 0), 2),
                # 详细工时分类
                online_repair_hours=round(
                    float(monthly_summary.online_repair_hours or 0), 2
                ),
                offline_repair_hours=round(
                    float(monthly_summary.offline_repair_hours or 0), 2
                ),
                rush_task_hours=round(float(monthly_summary.rush_task_hours or 0), 2),
                positive_review_hours=round(
                    float(monthly_summary.positive_review_hours or 0), 2
                ),
                # 惩罚统计
                penalty_hours=round(float(monthly_summary.penalty_hours or 0), 2),
                late_response_penalty_hours=round(
                    float(monthly_summary.late_response_penalty_hours or 0), 2
                ),
                late_completion_penalty_hours=round(
                    float(monthly_summary.late_completion_penalty_hours or 0), 2
                ),
                negative_review_penalty_hours=round(
                    float(monthly_summary.negative_review_penalty_hours or 0), 2
                ),
                # 出勤统计
                total_attendance_hours=round(total_attendance_hours, 2),
                average_work_hours=(
                    round(float(monthly_summary.total_hours or 0) / total_work_days, 2)
                    if total_work_days > 0
                    else 0.0
                ),
                total_late_days=total_late_days,
                total_early_days=total_early_days,
                total_late_minutes=total_late_minutes,
                total_early_minutes=total_early_minutes,
                exception_summary=exception_summary,
                # 满勤状态
                is_full_attendance=monthly_summary.total_hours >= 30.0,
                monthly_requirement=30.0,
                records=[
                    {
                        "date": (
                            r.attendance_date.isoformat() if r.attendance_date else None
                        ),
                        "checkin_time": (
                            r.checkin_time.strftime("%H:%M:%S")
                            if r.checkin_time
                            else None
                        ),
                        "checkout_time": (
                            r.checkout_time.strftime("%H:%M:%S")
                            if r.checkout_time
                            else None
                        ),
                        "work_hours": r.work_hours or 0,
                        "status": r.status,
                        "is_late": r.is_late_checkin,
                        "is_early": r.is_early_checkout,
                    }
                    for r in records
                ],
            )

        except Exception as e:
            logger.error(f"Get monthly summary error: {str(e)}")
            raise

    async def create_attendance_exception(
        self,
        member_id: int,
        exception_type: str,
        exception_date: date,
        reason: str,
        supporting_documents: Optional[str] = None,
    ) -> AttendanceException:
        """
        创建考勤异常申请

        Args:
            member_id: 员工ID
            exception_type: 异常类型
            exception_date: 异常日期
            reason: 申请理由
            supporting_documents: 支持材料

        Returns:
            AttendanceException: 异常申请记录
        """
        try:
            # 检查是否已存在同类型的申请
            existing_query = select(AttendanceException).where(
                and_(
                    AttendanceException.member_id == member_id,
                    AttendanceException.exception_date == exception_date,
                    AttendanceException.exception_type == exception_type,
                    AttendanceException.status == AttendanceExceptionStatus.PENDING,
                )
            )
            existing_result = await self.db.execute(existing_query)
            existing_exception = existing_result.scalar_one_or_none()

            if existing_exception:
                raise ValueError("该日期已有相同类型的异常申请正在处理中")

            # 创建新的异常申请
            exception = AttendanceException(
                member_id=member_id,
                exception_type=exception_type,
                exception_date=exception_date,
                reason=reason,
                supporting_documents=supporting_documents,
                status=AttendanceExceptionStatus.PENDING,
                applied_at=datetime.utcnow(),
            )

            self.db.add(exception)
            await self.db.commit()
            await self.db.refresh(exception)

            logger.info(f"Attendance exception created: {exception.id}")
            return exception

        except Exception as e:
            await self.db.rollback()
            logger.error(f"Create attendance exception error: {str(e)}")
            raise

    async def get_attendance_exceptions(
        self,
        member_id: Optional[int] = None,
        status_filter: Optional[str] = None,
        page: int = 1,
        size: int = 20,
    ) -> List[AttendanceException]:
        """获取考勤异常申请列表"""
        try:
            query = select(AttendanceException).options(
                joinedload(AttendanceException.member),
                joinedload(AttendanceException.reviewer),
            )

            if member_id:
                query = query.where(AttendanceException.member_id == member_id)

            if status_filter:
                query = query.where(
                    AttendanceException.status
                    == AttendanceExceptionStatus(status_filter)
                )

            query = query.order_by(desc(AttendanceException.applied_at))
            query = query.offset((page - 1) * size).limit(size)

            result = await self.db.execute(query)
            return list(result.scalars().all())

        except Exception as e:
            logger.error(f"Get attendance exceptions error: {str(e)}")
            raise

    async def update_attendance_exception(
        self,
        exception_id: int,
        status: str,
        reviewer_id: int,
        reviewer_comments: Optional[str] = None,
    ) -> AttendanceException:
        """更新考勤异常申请状态"""
        try:
            query = select(AttendanceException).where(
                AttendanceException.id == exception_id
            )
            result = await self.db.execute(query)
            exception = result.scalar_one_or_none()

            if not exception:
                raise ValueError("考勤异常申请不存在")

            if exception.status != AttendanceExceptionStatus.PENDING:
                raise ValueError("该申请已处理，无法重复处理")

            # 更新状态
            exception.status = AttendanceExceptionStatus(status)
            exception.reviewer_id = reviewer_id
            exception.reviewer_comments = reviewer_comments
            exception.reviewed_at = datetime.utcnow()

            await self.db.commit()
            await self.db.refresh(exception)

            logger.info(f"Attendance exception {exception_id} updated to {status}")
            return exception

        except Exception as e:
            await self.db.rollback()
            logger.error(f"Update attendance exception error: {str(e)}")
            raise

    async def get_attendance_statistics(
        self, date_from: date, date_to: date, department_id: Optional[int] = None
    ) -> AttendanceStatisticsResponse:
        """获取考勤统计信息"""
        try:
            # 构建基础查询
            query = select(AttendanceRecord).options(
                joinedload(AttendanceRecord.member)
            )

            query = query.where(
                and_(
                    AttendanceRecord.attendance_date >= date_from,
                    AttendanceRecord.attendance_date <= date_to,
                )
            )

            if department_id:
                query = query.join(Member).where(Member.department == department_id)

            result = await self.db.execute(query)
            records = result.scalars().all()

            # 统计计算
            total_records = len(records)
            total_members = len(set(r.member_id for r in records))
            total_work_hours = sum(r.work_hours or 0 for r in records)
            total_late_count = len([r for r in records if r.is_late_checkin])
            total_early_count = len([r for r in records if r.is_early_checkout])

            # 按部门统计
            dept_stats: Dict[str, Dict[str, Any]] = {}
            for record in records:
                if record.member and record.member.department:
                    dept_name = record.member.department
                    if dept_name not in dept_stats:
                        dept_stats[dept_name] = {
                            "member_count": set(),
                            "attendance_count": 0,
                            "late_count": 0,
                            "early_count": 0,
                            "total_hours": 0,
                        }

                    dept_stats[dept_name]["member_count"].add(record.member_id)
                    dept_stats[dept_name]["attendance_count"] += 1
                    dept_stats[dept_name]["total_hours"] += record.work_hours or 0
                    if record.is_late_checkin:
                        dept_stats[dept_name]["late_count"] += 1
                    if record.is_early_checkout:
                        dept_stats[dept_name]["early_count"] += 1

            # 转换部门统计格式
            department_statistics = []
            for dept_name, stats in dept_stats.items():
                member_count = len(stats["member_count"])
                attendance_rate = (
                    (
                        stats["attendance_count"]
                        / (member_count * (date_to - date_from).days + 1)
                        * 100
                    )
                    if member_count > 0
                    else 0
                )

                department_statistics.append(
                    {
                        "department": dept_name,
                        "member_count": member_count,
                        "attendance_count": stats["attendance_count"],
                        "attendance_rate": round(attendance_rate, 2),
                        "late_count": stats["late_count"],
                        "early_count": stats["early_count"],
                        "total_work_hours": round(stats["total_hours"], 2),
                        "average_work_hours": (
                            round(stats["total_hours"] / stats["attendance_count"], 2)
                            if stats["attendance_count"] > 0
                            else 0
                        ),
                    }
                )

            # 查询异常申请统计
            exception_query = select(AttendanceException).where(
                and_(
                    AttendanceException.exception_date >= date_from,
                    AttendanceException.exception_date <= date_to,
                )
            )

            if department_id:
                exception_query = exception_query.join(Member).where(
                    Member.department == department_id
                )

            exception_result = await self.db.execute(exception_query)
            exceptions = exception_result.scalars().all()

            exception_stats = {
                "total": len(exceptions),
                "pending": len(
                    [
                        e
                        for e in exceptions
                        if e.status == AttendanceExceptionStatus.PENDING
                    ]
                ),
                "approved": len(
                    [
                        e
                        for e in exceptions
                        if e.status == AttendanceExceptionStatus.APPROVED
                    ]
                ),
                "rejected": len(
                    [
                        e
                        for e in exceptions
                        if e.status == AttendanceExceptionStatus.REJECTED
                    ]
                ),
            }

            return AttendanceStatisticsResponse(
                date_from=date_from,
                date_to=date_to,
                total_records=total_records,
                total_members=total_members,
                total_work_hours=round(total_work_hours, 2),
                average_work_hours=(
                    round(total_work_hours / total_records, 2)
                    if total_records > 0
                    else 0
                ),
                late_rate=(
                    round(total_late_count / total_records * 100, 2)
                    if total_records > 0
                    else 0
                ),
                early_checkout_rate=(
                    round(total_early_count / total_records * 100, 2)
                    if total_records > 0
                    else 0
                ),
                department_statistics=department_statistics,
                exception_statistics=exception_stats,
            )

        except Exception as e:
            logger.error(f"Get attendance statistics error: {str(e)}")
            raise

    async def bulk_import_attendance(
        self, import_data: List[AttendanceRecordCreate], importer_id: int
    ) -> Dict[str, int]:
        """批量导入考勤记录"""
        try:
            created_count = 0
            updated_count = 0
            skipped_count = 0

            for data in import_data:
                try:
                    # 检查是否已存在记录
                    existing_query = select(AttendanceRecord).where(
                        and_(
                            AttendanceRecord.member_id == data.member_id,
                            AttendanceRecord.attendance_date == data.attendance_date,
                        )
                    )
                    existing_result = await self.db.execute(existing_query)
                    existing_record = existing_result.scalar_one_or_none()

                    if existing_record:
                        # 更新现有记录
                        if data.checkin_time:
                            existing_record.checkin_time = data.checkin_time
                        if data.checkout_time:
                            existing_record.checkout_time = data.checkout_time
                        if data.location:
                            existing_record.location = data.location
                        if data.notes:
                            existing_record.notes = data.notes

                        self._calculate_late_checkin(existing_record)
                        self._calculate_work_hours(existing_record)
                        self._calculate_early_checkout(existing_record)

                        updated_count += 1
                    else:
                        # 创建新记录
                        record = AttendanceRecord(
                            member_id=data.member_id,
                            attendance_date=data.attendance_date,
                            checkin_time=data.checkin_time,
                            checkout_time=data.checkout_time,
                            location=data.location,
                            notes=data.notes,
                        )

                        self._calculate_late_checkin(record)
                        self._calculate_work_hours(record)
                        self._calculate_early_checkout(record)

                        self.db.add(record)
                        created_count += 1

                except Exception as e:
                    logger.warning(f"Failed to import attendance record: {str(e)}")
                    skipped_count += 1

            await self.db.commit()

            return {
                "created": created_count,
                "updated": updated_count,
                "skipped": skipped_count,
            }

        except Exception as e:
            await self.db.rollback()
            logger.error(f"Bulk import attendance error: {str(e)}")
            raise

    async def export_attendance_data(
        self,
        date_from: date,
        date_to: date,
        member_ids: Optional[List[int]] = None,
        format: str = "excel",
    ) -> Dict[str, Any]:
        """导出考勤数据"""
        try:
            # 查询数据
            query = select(AttendanceRecord).options(
                joinedload(AttendanceRecord.member)
            )

            query = query.where(
                and_(
                    AttendanceRecord.attendance_date >= date_from,
                    AttendanceRecord.attendance_date <= date_to,
                )
            )

            if member_ids:
                query = query.where(AttendanceRecord.member_id.in_(member_ids))

            query = query.order_by(
                AttendanceRecord.attendance_date, AttendanceRecord.member_id
            )

            result = await self.db.execute(query)
            records = result.scalars().all()

            # 这里应该实现实际的文件导出逻辑
            # 为了简化，返回模拟的导出结果
            filename = f"attendance_export_{date_from}_{date_to}.{format}"

            return {
                "download_url": f"/api/v1/files/download/{filename}",
                "filename": filename,
                "total_records": len(records),
                "expires_at": (datetime.utcnow() + timedelta(hours=24)).isoformat(),
            }

        except Exception as e:
            logger.error(f"Export attendance data error: {str(e)}")
            raise

    # 私有方法

    def _calculate_late_checkin(self, record: AttendanceRecord):
        """计算迟到情况"""
        if not record.checkin_time:
            return

        checkin_time = record.checkin_time.time()
        work_start = self.work_start_time

        if checkin_time > work_start:
            # 计算迟到分钟数
            checkin_datetime = datetime.combine(date.today(), checkin_time)
            work_start_datetime = datetime.combine(date.today(), work_start)
            late_minutes = (checkin_datetime - work_start_datetime).total_seconds() / 60

            if late_minutes > self.late_threshold_minutes:
                record.is_late_checkin = True
                record.late_checkin_minutes = int(late_minutes)
            else:
                record.is_late_checkin = False
                record.late_checkin_minutes = None
        else:
            record.is_late_checkin = False
            record.late_checkin_minutes = None

    def _calculate_early_checkout(self, record: AttendanceRecord):
        """计算早退情况"""
        if not record.checkout_time:
            return

        checkout_time = record.checkout_time.time()
        work_end = self.work_end_time

        if checkout_time < work_end:
            # 计算早退分钟数
            checkout_datetime = datetime.combine(date.today(), checkout_time)
            work_end_datetime = datetime.combine(date.today(), work_end)
            early_minutes = (work_end_datetime - checkout_datetime).total_seconds() / 60

            if early_minutes > self.early_threshold_minutes:
                record.is_early_checkout = True
                record.early_checkout_minutes = int(early_minutes)
            else:
                record.is_early_checkout = False
                record.early_checkout_minutes = None
        else:
            record.is_early_checkout = False
            record.early_checkout_minutes = None

    def _calculate_work_hours(self, record: AttendanceRecord):
        """计算工作时长"""
        if not record.checkin_time or not record.checkout_time:
            record.work_hours = 0.0
            return

        # 计算总时长
        total_time = record.checkout_time - record.checkin_time
        total_minutes = total_time.total_seconds() / 60

        # 扣除午休时间
        lunch_minutes = 60  # 默认午休1小时

        # 如果跨越午休时间，需要扣除
        checkin_time = record.checkin_time.time()
        checkout_time = record.checkout_time.time()

        if (
            checkin_time <= self.lunch_start_time
            and checkout_time >= self.lunch_end_time
        ):
            total_minutes -= lunch_minutes

        # 转换为小时
        record.work_hours = max(0, total_minutes / 60)

    def _calculate_work_days_in_month(self, year: int, month: int) -> int:
        """计算月份中的工作日数量（排除周末）"""
        first_day = date(year, month, 1)
        last_day = date(year, month, monthrange(year, month)[1])

        work_days = 0
        current_date = first_day

        while current_date <= last_day:
            # 0=周一，6=周日
            if current_date.weekday() < 5:  # 周一到周五
                work_days += 1
            current_date += timedelta(days=1)

        return work_days
