"""Service for inspection/sampling review workflow and workhour settlement."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Literal

from sqlalchemy import and_, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.biz_operation_log import BizOperationLog
from app.models.inspection_record import InspectionRecord
from app.models.review_log import ReviewLog
from app.models.sampling_record import SamplingRecord
from app.models.todo_item import TodoItem
from app.models.workhour_entry import WorkhourEntry
from app.models.workhour_rule import WorkhourRule
from app.schemas.repair_workhour import BizReviewSubmitRequest, RepairReviewActionRequest

BizType = Literal["inspection", "sampling"]


class InspectionSamplingWorkhourService:
    """Orchestrate review and settlement for inspection/sampling."""

    def __init__(self, db: AsyncSession):
        self.db = db

    @staticmethod
    def _calc_month_window(year: int, month: int) -> tuple[datetime, datetime]:
        start = datetime(year, month, 1, tzinfo=timezone.utc)
        if month == 12:
            end = datetime(year + 1, 1, 1, tzinfo=timezone.utc)
        else:
            end = datetime(year, month + 1, 1, tzinfo=timezone.utc)
        return start, end

    @staticmethod
    def _resolve_record_model(biz_type: BizType):
        if biz_type == "inspection":
            return InspectionRecord
        return SamplingRecord

    @staticmethod
    def _resolve_record_label(biz_type: BizType) -> str:
        return "巡检" if biz_type == "inspection" else "抽检"

    @staticmethod
    def _resolve_todo_source_type(biz_type: BizType) -> str:
        return f"{biz_type}_record_review"

    async def _get_rule_id(self, biz_type: BizType) -> int | None:
        rule_stmt = (
            select(WorkhourRule)
            .where(
                and_(
                    WorkhourRule.biz_type == biz_type,
                    WorkhourRule.is_enabled.is_(True),
                )
            )
            .order_by(WorkhourRule.id)
            .limit(1)
        )
        rule_result = await self.db.execute(rule_stmt)
        rule = rule_result.scalar_one_or_none()
        return rule.id if rule else None

    async def _get_record(self, biz_type: BizType, record_id: int) -> Any:
        model = self._resolve_record_model(biz_type)
        stmt = select(model).where(model.id == record_id)
        result = await self.db.execute(stmt)
        record = result.scalar_one_or_none()
        if record is None:
            raise ValueError(f"{self._resolve_record_label(biz_type)}记录不存在")
        return record

    @staticmethod
    def _derive_base_minutes(biz_type: BizType, record: Any) -> int:
        if biz_type == "inspection":
            if int(getattr(record, "result_status", 1) or 1) == 3:
                return 35
            if int(getattr(record, "result_status", 1) or 1) == 2:
                return 25
            return 20

        # sampling
        detect_mode = getattr(record, "detect_mode", "full") or "full"
        base = 40 if detect_mode == "full" else 20
        if bool(getattr(record, "exception_auto", False)) or bool(
            getattr(record, "exception_manual", False)
        ):
            base += 10
        return base

    async def _upsert_workhour_entry(
        self,
        biz_type: BizType,
        record: Any,
        reviewer_id: int,
        review_note: str | None,
    ) -> tuple[WorkhourEntry, bool]:
        stmt = select(WorkhourEntry).where(
            and_(
                WorkhourEntry.biz_type == biz_type,
                WorkhourEntry.biz_id == record.id,
                WorkhourEntry.user_id == record.user_id,
            )
        )
        result = await self.db.execute(stmt)
        entry = result.scalar_one_or_none()

        base_minutes = self._derive_base_minutes(biz_type, record)
        rule_id = await self._get_rule_id(biz_type)
        now = datetime.now(timezone.utc)

        created = False
        if entry is None:
            entry = WorkhourEntry(
                biz_type=biz_type,
                biz_id=record.id,
                user_id=record.user_id,
                source_rule_id=rule_id,
                base_minutes=base_minutes,
                final_minutes=base_minutes,
                review_status=1,
                reviewed_by=reviewer_id,
                reviewed_at=now,
                review_note=review_note,
            )
            self.db.add(entry)
            created = True
        else:
            entry.source_rule_id = rule_id
            entry.base_minutes = base_minutes
            entry.final_minutes = base_minutes
            entry.review_status = 1
            entry.reviewed_by = reviewer_id
            entry.reviewed_at = now
            entry.review_note = review_note

        return entry, created

    async def submit_review(
        self,
        biz_type: BizType,
        record_id: int,
        operator_id: int,
        payload: BizReviewSubmitRequest,
    ) -> dict[str, Any]:
        try:
            record = await self._get_record(biz_type, record_id)

            if int(getattr(record, "review_status", 0) or 0) == 0:
                return {
                    "record_id": record.id,
                    "biz_type": biz_type,
                    "status": "pending",
                    "already_pending": True,
                }

            record.review_status = 0
            record.reviewed_by = None
            record.reviewed_at = None

            source_type = self._resolve_todo_source_type(biz_type)
            todo_stmt = select(TodoItem).where(
                and_(
                    TodoItem.source_biz_type == source_type,
                    TodoItem.source_biz_id == record.id,
                    TodoItem.status.in_([0, 1]),
                )
            )
            todo_result = await self.db.execute(todo_stmt)
            todo = todo_result.scalar_one_or_none()
            title = (
                f"巡检记录审核: {record.id}"
                if biz_type == "inspection"
                else f"抽检记录审核: {record.id}"
            )
            if todo is None:
                todo = TodoItem(
                    todo_type=f"{biz_type}_record_review",
                    source_biz_type=source_type,
                    source_biz_id=record.id,
                    title=title,
                    content=payload.note,
                    assignee_user_id=payload.assignee_user_id,
                    priority_level=payload.priority_level,
                    status=0,
                )
                self.db.add(todo)
            else:
                todo.status = 0
                todo.content = payload.note
                todo.assignee_user_id = payload.assignee_user_id
                todo.priority_level = payload.priority_level
                todo.resolved_at = None

            op_log = BizOperationLog(
                biz_type=f"{biz_type}_record",
                biz_id=record.id,
                operation_type="submit_review",
                operator_user_id=operator_id,
                payload_before=None,
                payload_after={
                    "biz_type": biz_type,
                    "record_id": record.id,
                    "priority_level": payload.priority_level,
                },
            )
            self.db.add(op_log)

            await self.db.commit()
            return {
                "record_id": record.id,
                "biz_type": biz_type,
                "status": "pending",
                "created": True,
            }
        except Exception:
            await self.db.rollback()
            raise

    async def review_application(
        self,
        biz_type: BizType,
        record_id: int,
        reviewer_id: int,
        payload: RepairReviewActionRequest,
    ) -> dict[str, Any]:
        action = payload.action.strip().lower()
        if action not in {"approve", "reject"}:
            raise ValueError("审批动作仅支持 approve/reject")

        try:
            record = await self._get_record(biz_type, record_id)
            if int(getattr(record, "review_status", 0) or 0) != 0:
                raise ValueError("记录不是待审核状态，不能重复审批")

            now = datetime.now(timezone.utc)
            approved = action == "approve"

            record.review_status = 1 if approved else 2
            record.reviewed_by = reviewer_id
            record.reviewed_at = now

            review_log = ReviewLog(
                biz_type=f"{biz_type}_record",
                biz_id=record.id,
                review_type="record_review",
                reviewer_id=reviewer_id,
                action_code=action,
                review_note=payload.note,
            )
            self.db.add(review_log)

            source_type = self._resolve_todo_source_type(biz_type)
            todo_stmt = select(TodoItem).where(
                and_(
                    TodoItem.source_biz_type == source_type,
                    TodoItem.source_biz_id == record.id,
                    TodoItem.status.in_([0, 1]),
                )
            )
            todo_result = await self.db.execute(todo_stmt)
            for todo in todo_result.scalars().all():
                todo.status = 2
                todo.resolved_at = now

            entry_id = None
            entry_created = False
            if approved:
                entry, entry_created = await self._upsert_workhour_entry(
                    biz_type=biz_type,
                    record=record,
                    reviewer_id=reviewer_id,
                    review_note=payload.note,
                )
                await self.db.flush()
                entry_id = entry.id

            op_log = BizOperationLog(
                biz_type=f"{biz_type}_record",
                biz_id=record.id,
                operation_type="approve_review" if approved else "reject_review",
                operator_user_id=reviewer_id,
                payload_before=None,
                payload_after={
                    "biz_type": biz_type,
                    "record_id": record.id,
                    "action": action,
                    "workhour_entry_id": entry_id,
                },
            )
            self.db.add(op_log)

            await self.db.commit()
            return {
                "record_id": record.id,
                "biz_type": biz_type,
                "action": action,
                "review_status": record.review_status,
                "workhour_entry_created": entry_created,
                "workhour_entry_id": entry_id,
            }
        except Exception:
            await self.db.rollback()
            raise

    async def list_pending_reviews(
        self,
        biz_type: BizType,
        page: int,
        page_size: int,
    ) -> dict[str, Any]:
        model = self._resolve_record_model(biz_type)
        offset = (page - 1) * page_size

        base_stmt = select(model).where(model.review_status == 0)

        count_stmt = select(func.count()).select_from(base_stmt.subquery())
        count_result = await self.db.execute(count_stmt)
        total = count_result.scalar() or 0

        rows_result = await self.db.execute(
            base_stmt.order_by(desc(model.created_at)).offset(offset).limit(page_size)
        )
        records = rows_result.scalars().all()

        items = []
        for item in records:
            base_item = {
                "record_id": item.id,
                "biz_type": biz_type,
                "user_id": item.user_id,
                "review_status": item.review_status,
                "created_at": item.created_at.isoformat() if item.created_at else None,
            }
            if biz_type == "inspection":
                base_item["inspection_task_id"] = item.inspection_task_id
                base_item["inspection_point_id"] = item.inspection_point_id
            else:
                base_item["sampling_task_id"] = item.sampling_task_id
                base_item["sampling_task_room_id"] = item.sampling_task_room_id
            items.append(base_item)

        return {
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
            "biz_type": biz_type,
        }

    async def run_monthly_settlement(
        self,
        biz_type: BizType,
        year: int,
        month: int,
        operator_id: int,
        user_id: int | None = None,
        dry_run: bool = False,
    ) -> dict[str, Any]:
        model = self._resolve_record_model(biz_type)
        start_at, end_at = self._calc_month_window(year, month)

        stmt = select(model).where(
            and_(
                model.review_status == 1,
                model.reviewed_at.is_not(None),
                model.reviewed_at >= start_at,
                model.reviewed_at < end_at,
            )
        )
        if user_id is not None:
            stmt = stmt.where(model.user_id == user_id)

        rows_result = await self.db.execute(stmt)
        records = rows_result.scalars().all()

        processed = 0
        created = 0
        updated = 0
        try:
            for record in records:
                entry, is_created = await self._upsert_workhour_entry(
                    biz_type=biz_type,
                    record=record,
                    reviewer_id=operator_id,
                    review_note=f"monthly_settlement {biz_type} {year}-{month:02d}",
                )
                processed += 1
                if is_created:
                    created += 1
                else:
                    updated += 1

                op_log = BizOperationLog(
                    biz_type="workhour_entry",
                    biz_id=entry.id,
                    operation_type="monthly_settlement",
                    operator_user_id=operator_id,
                    payload_before=None,
                    payload_after={
                        "biz_type": biz_type,
                        "year": year,
                        "month": month,
                        "user_id": entry.user_id,
                        "final_minutes": entry.final_minutes,
                    },
                )
                self.db.add(op_log)

            if dry_run:
                await self.db.rollback()
            else:
                await self.db.commit()

            return {
                "biz_type": biz_type,
                "year": year,
                "month": month,
                "processed": processed,
                "created": created,
                "updated": updated,
                "dry_run": dry_run,
                "window_start": start_at.isoformat(),
                "window_end": end_at.isoformat(),
            }
        except Exception:
            await self.db.rollback()
            raise

    async def list_workhour_entries(
        self,
        biz_type: BizType,
        year: int,
        month: int,
        user_id: int | None,
        page: int,
        page_size: int,
    ) -> dict[str, Any]:
        start_at, end_at = self._calc_month_window(year, month)
        offset = (page - 1) * page_size

        stmt = select(WorkhourEntry).where(
            and_(
                WorkhourEntry.biz_type == biz_type,
                WorkhourEntry.created_at >= start_at,
                WorkhourEntry.created_at < end_at,
            )
        )
        if user_id is not None:
            stmt = stmt.where(WorkhourEntry.user_id == user_id)

        count_stmt = select(func.count()).select_from(stmt.subquery())
        count_result = await self.db.execute(count_stmt)
        total = count_result.scalar() or 0

        rows_result = await self.db.execute(
            stmt.order_by(desc(WorkhourEntry.created_at)).offset(offset).limit(page_size)
        )
        entries = rows_result.scalars().all()

        items = [
            {
                "id": item.id,
                "biz_type": item.biz_type,
                "biz_id": item.biz_id,
                "user_id": item.user_id,
                "base_minutes": item.base_minutes,
                "final_minutes": item.final_minutes,
                "review_status": item.review_status,
                "reviewed_by": item.reviewed_by,
                "reviewed_at": item.reviewed_at.isoformat() if item.reviewed_at else None,
                "created_at": item.created_at.isoformat() if item.created_at else None,
            }
            for item in entries
        ]

        return {
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
            "biz_type": biz_type,
        }
