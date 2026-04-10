"""Service for repair review workflow and workhour settlement."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy import and_, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.biz_operation_log import BizOperationLog
from app.models.repair_match_application import RepairMatchApplication
from app.models.repair_ticket import RepairTicket
from app.models.review_log import ReviewLog
from app.models.todo_item import TodoItem
from app.models.workhour_entry import WorkhourEntry
from app.models.workhour_rule import WorkhourRule
from app.schemas.repair_workhour import (
    RepairReviewActionRequest,
    RepairReviewSubmitRequest,
)


class RepairWorkhourService:
    """Orchestrate review and settlement with new B6 tables."""

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
    def _derive_base_minutes(ticket: RepairTicket) -> int:
        # Keep parity with current online/offline convention.
        return 100 if ticket.ticket_source == "offline" else 40

    async def _get_repair_rule_id(self) -> int | None:
        rule_stmt = (
            select(WorkhourRule)
            .where(
                and_(
                    WorkhourRule.biz_type == "repair",
                    WorkhourRule.is_enabled.is_(True),
                )
            )
            .order_by(WorkhourRule.id)
            .limit(1)
        )
        rule_result = await self.db.execute(rule_stmt)
        rule = rule_result.scalar_one_or_none()
        return rule.id if rule else None

    async def submit_review(
        self,
        ticket_id: int,
        operator_id: int,
        payload: RepairReviewSubmitRequest,
    ) -> dict[str, Any]:
        try:
            ticket_stmt = select(RepairTicket).where(RepairTicket.id == ticket_id)
            ticket_result = await self.db.execute(ticket_stmt)
            ticket = ticket_result.scalar_one_or_none()
            if ticket is None:
                raise ValueError("报修单不存在")

            import_row_id = payload.import_repair_row_id or ticket.matched_import_row_id
            if import_row_id is None:
                raise ValueError("缺少 import_repair_row_id，无法提交审核")

            app_stmt = select(RepairMatchApplication).where(
                RepairMatchApplication.repair_ticket_id == ticket_id
            )
            app_result = await self.db.execute(app_stmt)
            application = app_result.scalar_one_or_none()

            now = datetime.now(timezone.utc)
            created = False
            if application is None:
                application = RepairMatchApplication(
                    repair_ticket_id=ticket_id,
                    import_repair_row_id=import_row_id,
                    applied_by=operator_id,
                    apply_note=payload.note,
                    status=0,
                )
                self.db.add(application)
                created = True
                await self.db.flush()
            else:
                if application.status == 0:
                    return {
                        "application_id": application.id,
                        "repair_ticket_id": ticket_id,
                        "status": "pending",
                        "already_pending": True,
                    }

                application.import_repair_row_id = import_row_id
                application.applied_by = operator_id
                application.apply_note = payload.note
                application.status = 0
                application.reviewed_by = None
                application.reviewed_at = None

            ticket.match_status = 1

            todo_stmt = select(TodoItem).where(
                and_(
                    TodoItem.source_biz_type == "repair_match_application",
                    TodoItem.source_biz_id == application.id,
                    TodoItem.status.in_([0, 1]),
                )
            )
            todo_result = await self.db.execute(todo_stmt)
            todo = todo_result.scalar_one_or_none()
            if todo is None:
                todo = TodoItem(
                    todo_type="repair_match_review",
                    source_biz_type="repair_match_application",
                    source_biz_id=application.id,
                    title=f"报修单审核: {ticket.repair_no or ticket.id}",
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
                biz_type="repair_match_application",
                biz_id=application.id,
                operation_type="submit_review",
                operator_user_id=operator_id,
                payload_before=None,
                payload_after={
                    "repair_ticket_id": ticket_id,
                    "application_status": application.status,
                    "priority_level": payload.priority_level,
                },
            )
            self.db.add(op_log)

            await self.db.commit()

            return {
                "application_id": application.id,
                "repair_ticket_id": ticket_id,
                "status": "pending",
                "created": created,
            }
        except Exception:
            await self.db.rollback()
            raise

    async def _upsert_workhour_entry(
        self,
        ticket: RepairTicket,
        reviewer_id: int,
        review_note: str | None,
    ) -> tuple[WorkhourEntry, bool]:
        stmt = select(WorkhourEntry).where(
            and_(
                WorkhourEntry.biz_type == "repair",
                WorkhourEntry.biz_id == ticket.id,
                WorkhourEntry.user_id == ticket.created_by,
            )
        )
        result = await self.db.execute(stmt)
        entry = result.scalar_one_or_none()

        base_minutes = self._derive_base_minutes(ticket)
        rule_id = await self._get_repair_rule_id()
        now = datetime.now(timezone.utc)

        created = False
        if entry is None:
            entry = WorkhourEntry(
                biz_type="repair",
                biz_id=ticket.id,
                user_id=ticket.created_by,
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

    async def review_application(
        self,
        ticket_id: int,
        reviewer_id: int,
        payload: RepairReviewActionRequest,
    ) -> dict[str, Any]:
        action = payload.action.strip().lower()
        if action not in {"approve", "reject"}:
            raise ValueError("审批动作仅支持 approve/reject")

        try:
            app_stmt = select(RepairMatchApplication).where(
                RepairMatchApplication.repair_ticket_id == ticket_id
            )
            app_result = await self.db.execute(app_stmt)
            application = app_result.scalar_one_or_none()
            if application is None:
                raise ValueError("未找到待审核申请")
            if application.status != 0:
                raise ValueError("申请不是待审核状态，不能重复审批")

            ticket_stmt = select(RepairTicket).where(RepairTicket.id == ticket_id)
            ticket_result = await self.db.execute(ticket_stmt)
            ticket = ticket_result.scalar_one_or_none()
            if ticket is None:
                raise ValueError("报修单不存在")

            now = datetime.now(timezone.utc)
            approved = action == "approve"

            application.status = 1 if approved else 2
            application.reviewed_by = reviewer_id
            application.reviewed_at = now

            ticket.match_status = 2 if approved else 3

            review_log = ReviewLog(
                biz_type="repair_match_application",
                biz_id=application.id,
                review_type="match_review",
                reviewer_id=reviewer_id,
                action_code=action,
                review_note=payload.note,
            )
            self.db.add(review_log)

            todo_stmt = select(TodoItem).where(
                and_(
                    TodoItem.source_biz_type == "repair_match_application",
                    TodoItem.source_biz_id == application.id,
                    TodoItem.status.in_([0, 1]),
                )
            )
            todo_result = await self.db.execute(todo_stmt)
            for todo in todo_result.scalars().all():
                todo.status = 2
                todo.resolved_at = now

            entry_created = False
            entry_id = None
            if approved:
                entry, entry_created = await self._upsert_workhour_entry(
                    ticket=ticket,
                    reviewer_id=reviewer_id,
                    review_note=payload.note,
                )
                await self.db.flush()
                entry_id = entry.id

            op_log = BizOperationLog(
                biz_type="repair_match_application",
                biz_id=application.id,
                operation_type="approve_review" if approved else "reject_review",
                operator_user_id=reviewer_id,
                payload_before=None,
                payload_after={
                    "action": action,
                    "application_status": application.status,
                    "match_status": ticket.match_status,
                    "workhour_entry_id": entry_id,
                },
            )
            self.db.add(op_log)

            await self.db.commit()

            return {
                "repair_ticket_id": ticket_id,
                "application_id": application.id,
                "action": action,
                "application_status": application.status,
                "workhour_entry_created": entry_created,
                "workhour_entry_id": entry_id,
            }
        except Exception:
            await self.db.rollback()
            raise

    async def list_pending_reviews(
        self,
        page: int,
        page_size: int,
    ) -> dict[str, Any]:
        offset = (page - 1) * page_size

        base_stmt = (
            select(RepairMatchApplication, RepairTicket)
            .join(RepairTicket, RepairTicket.id == RepairMatchApplication.repair_ticket_id)
            .where(RepairMatchApplication.status == 0)
        )

        count_stmt = select(func.count()).select_from(base_stmt.subquery())
        count_result = await self.db.execute(count_stmt)
        total = count_result.scalar() or 0

        rows_result = await self.db.execute(
            base_stmt
            .order_by(desc(RepairMatchApplication.created_at))
            .offset(offset)
            .limit(page_size)
        )

        items: list[dict[str, Any]] = []
        for application, ticket in rows_result.all():
            items.append(
                {
                    "application_id": application.id,
                    "repair_ticket_id": ticket.id,
                    "repair_no": ticket.repair_no,
                    "ticket_source": ticket.ticket_source,
                    "report_user_name": ticket.report_user_name,
                    "status": application.status,
                    "created_at": (
                        application.created_at.isoformat() if application.created_at else None
                    ),
                }
            )

        return {
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
        }

    async def run_monthly_settlement(
        self,
        year: int,
        month: int,
        operator_id: int,
        user_id: int | None = None,
        dry_run: bool = False,
    ) -> dict[str, Any]:
        start_at, end_at = self._calc_month_window(year, month)

        stmt = (
            select(RepairMatchApplication, RepairTicket)
            .join(RepairTicket, RepairTicket.id == RepairMatchApplication.repair_ticket_id)
            .where(
                and_(
                    RepairMatchApplication.status == 1,
                    RepairMatchApplication.reviewed_at.is_not(None),
                    RepairMatchApplication.reviewed_at >= start_at,
                    RepairMatchApplication.reviewed_at < end_at,
                )
            )
        )

        if user_id is not None:
            stmt = stmt.where(RepairTicket.created_by == user_id)

        rows_result = await self.db.execute(stmt)
        rows = rows_result.all()

        processed = 0
        created = 0
        updated = 0

        try:
            for application, ticket in rows:
                entry, is_created = await self._upsert_workhour_entry(
                    ticket=ticket,
                    reviewer_id=operator_id,
                    review_note=f"monthly_settlement {year}-{month:02d}",
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
                WorkhourEntry.biz_type == "repair",
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
        }
