"""正式报修单兼容路径路由。"""

from datetime import datetime, timezone
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import create_response, get_current_active_admin, get_current_user, get_db
from app.models.import_batch import ImportBatch
from app.models.import_repair_row import ImportRepairRow
from app.models.member import Member, UserRole
from app.models.repair_match_application import RepairMatchApplication
from app.models.repair_ticket import RepairTicket
from app.models.repair_ticket_member import RepairTicketMember
from app.services.repair_ocr_service import RepairOCRService

router = APIRouter()


def _to_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


async def _is_repair_ticket_participant(
    db: AsyncSession,
    ticket_id: int,
    user_id: int,
) -> bool:
    participant = (
        await db.execute(
            select(RepairTicketMember).where(
                RepairTicketMember.repair_ticket_id == ticket_id,
                RepairTicketMember.user_id == user_id,
            )
        )
    ).scalar_one_or_none()
    return participant is not None


async def _assert_ticket_access(
    db: AsyncSession,
    ticket: RepairTicket,
    current_user: Member,
    *,
    allow_participant: bool,
) -> None:
    if current_user.role == UserRole.ADMIN or ticket.created_by == current_user.id:
        return
    if allow_participant and await _is_repair_ticket_participant(db, ticket.id, current_user.id):
        return
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权访问该报修单")


@router.post("/repair-orders", response_model=Dict[str, Any])
async def create_repair_order(
    payload: Dict[str, Any],
    db: AsyncSession = Depends(get_db),
    current_user: Member = Depends(get_current_user),
) -> Dict[str, Any]:
    row = RepairTicket(
        repair_no=payload.get("repair_no") or payload.get("repairNo"),
        ticket_source=payload.get("ticket_source") or payload.get("ticketSource") or "offline",
        title=payload.get("title"),
        report_user_name=payload.get("report_user_name") or payload.get("reportUserName"),
        report_phone=payload.get("report_phone") or payload.get("reportPhone"),
        building_id=payload.get("building_id") or payload.get("buildingId"),
        dorm_room_id=payload.get("dorm_room_id") or payload.get("dormRoomId"),
        issue_content=payload.get("issue_content") or payload.get("issueContent"),
        issue_category=payload.get("issue_category") or payload.get("issueCategory"),
        created_by=current_user.id,
    )
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return create_response(data={"id": row.id}, message="创建报修单成功")


@router.put("/repair-orders/{ticket_id}", response_model=Dict[str, Any])
async def update_repair_order(
    ticket_id: int,
    payload: Dict[str, Any],
    db: AsyncSession = Depends(get_db),
    current_user: Member = Depends(get_current_user),
) -> Dict[str, Any]:
    row = (
        await db.execute(select(RepairTicket).where(RepairTicket.id == ticket_id))
    ).scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="报修单不存在")
    await _assert_ticket_access(db, row, current_user, allow_participant=False)
    for field in [
        "title",
        "report_user_name",
        "report_phone",
        "issue_content",
        "issue_category",
        "solution_desc",
        "solve_status",
    ]:
        if field in payload:
            setattr(row, field, payload[field])
    await db.commit()
    return create_response(data={"id": row.id}, message="更新报修单成功")


@router.post("/repair-orders/{ticket_id}/participants", response_model=Dict[str, Any])
async def add_repair_order_participant(
    ticket_id: int,
    payload: Dict[str, Any],
    db: AsyncSession = Depends(get_db),
    current_user: Member = Depends(get_current_user),
) -> Dict[str, Any]:
    user_id = _to_int(payload.get("user_id") or payload.get("userId"), 0)
    if user_id <= 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="user_id 非法")

    ticket = (
        await db.execute(select(RepairTicket).where(RepairTicket.id == ticket_id))
    ).scalar_one_or_none()
    if not ticket:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="报修单不存在")
    await _assert_ticket_access(db, ticket, current_user, allow_participant=False)

    exists = (
        await db.execute(
            select(RepairTicketMember).where(
                RepairTicketMember.repair_ticket_id == ticket_id,
                RepairTicketMember.user_id == user_id,
            )
        )
    ).scalar_one_or_none()
    if exists is None:
        db.add(
            RepairTicketMember(
                repair_ticket_id=ticket_id,
                user_id=user_id,
                member_role=payload.get("member_role") or payload.get("memberRole") or "assist",
            )
        )
        await db.commit()
    return create_response(data={"repair_ticket_id": ticket_id, "user_id": user_id}, message="添加参与人成功")


@router.post("/repair-orders/{ticket_id}/ocr", response_model=Dict[str, Any])
async def repair_order_ocr(
    ticket_id: int,
    payload: Dict[str, Any],
    db: AsyncSession = Depends(get_db),
    current_user: Member = Depends(get_current_user),
) -> Dict[str, Any]:
    row = (
        await db.execute(select(RepairTicket).where(RepairTicket.id == ticket_id))
    ).scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="报修单不存在")
    await _assert_ticket_access(db, row, current_user, allow_participant=False)

    apply_to_ticket = bool(payload.get("apply_to_ticket", True))
    force_overwrite = bool(payload.get("force_overwrite", False))
    manual_correction = payload.get("manual_correction") or payload.get("manualCorrection") or {}
    if not isinstance(manual_correction, dict):
        manual_correction = {}

    result = RepairOCRService.analyze(payload)
    structured_data = result["structured_data"]

    corrected_fields: list[str] = []
    for key in [
        "repair_no",
        "report_user_name",
        "report_phone",
        "room_no",
        "issue_content",
        "issue_category",
    ]:
        value = manual_correction.get(key)
        if value is None:
            continue
        text = str(value).strip()
        if not text:
            continue
        structured_data[key] = text
        corrected_fields.append(key)

    applied_fields: list[str] = []
    if apply_to_ticket:
        for field in [
            "repair_no",
            "report_user_name",
            "report_phone",
            "issue_content",
            "issue_category",
        ]:
            value = structured_data.get(field)
            if value in (None, ""):
                continue
            current_value = getattr(row, field, None)
            if force_overwrite or current_value in (None, ""):
                setattr(row, field, value)
                applied_fields.append(field)

    row.ocr_payload = {
        "version": "v2",
        "recognized_at": datetime.now(timezone.utc).isoformat(),
        "engine": payload.get("engine") or "builtin-rule-engine",
        "raw_payload": result["raw_payload"],
        "structured_data": structured_data,
        "confidence": result["confidence"],
        "needs_manual_review": result["needs_manual_review"],
        "warnings": result["warnings"],
        "manual_correction": manual_correction,
        "corrected_fields": corrected_fields,
        "apply_to_ticket": apply_to_ticket,
        "force_overwrite": force_overwrite,
        "applied_fields": applied_fields,
    }

    await db.commit()
    return create_response(
        data={
            "id": row.id,
            "ocr_payload": row.ocr_payload,
            "structured_data": structured_data,
            "confidence": result["confidence"],
            "needs_manual_review": row.ocr_payload["needs_manual_review"],
            "applied_fields": applied_fields,
        },
        message="OCR识别与结构化已完成",
    )


@router.post("/repair-orders/{ticket_id}/ocr/correct", response_model=Dict[str, Any])
async def repair_order_ocr_correct(
    ticket_id: int,
    payload: Dict[str, Any],
    db: AsyncSession = Depends(get_db),
    current_user: Member = Depends(get_current_user),
) -> Dict[str, Any]:
    row = (
        await db.execute(select(RepairTicket).where(RepairTicket.id == ticket_id))
    ).scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="报修单不存在")
    await _assert_ticket_access(db, row, current_user, allow_participant=False)

    corrections = payload.get("manual_correction") or payload.get("manualCorrection") or payload.get("corrections")
    if not isinstance(corrections, dict) or not corrections:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="缺少修正字段")

    force_overwrite = bool(payload.get("force_overwrite", True))

    current_payload = row.ocr_payload if isinstance(row.ocr_payload, dict) else {}
    structured = current_payload.get("structured_data")
    if not isinstance(structured, dict):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="当前无可修正OCR结构化结果")

    corrected_fields: list[str] = []
    for key, value in corrections.items():
        if value is None:
            continue
        text = str(value).strip()
        if not text:
            continue
        structured[key] = text
        corrected_fields.append(key)

    applied_fields: list[str] = []
    for field in [
        "repair_no",
        "report_user_name",
        "report_phone",
        "issue_content",
        "issue_category",
    ]:
        value = structured.get(field)
        if value in (None, ""):
            continue
        current_value = getattr(row, field, None)
        if force_overwrite or current_value in (None, ""):
            setattr(row, field, value)
            applied_fields.append(field)

    current_manual = current_payload.get("manual_correction")
    if not isinstance(current_manual, dict):
        current_manual = {}
    current_manual.update(corrections)

    current_payload.update(
        {
            "structured_data": structured,
            "manual_correction": current_manual,
            "corrected_fields": sorted(set(current_payload.get("corrected_fields", []) + corrected_fields)),
            "corrected_at": datetime.now(timezone.utc).isoformat(),
            "applied_fields": sorted(set(current_payload.get("applied_fields", []) + applied_fields)),
        }
    )
    row.ocr_payload = current_payload

    await db.commit()
    return create_response(
        data={
            "id": row.id,
            "ocr_payload": row.ocr_payload,
            "structured_data": structured,
            "corrected_fields": corrected_fields,
            "applied_fields": applied_fields,
        },
        message="OCR修正已应用",
    )


@router.get("/repair-orders/{ticket_id}/match-candidates", response_model=Dict[str, Any])
async def repair_match_candidates(
    ticket_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: Member = Depends(get_current_user),
) -> Dict[str, Any]:
    ticket = (
        await db.execute(select(RepairTicket).where(RepairTicket.id == ticket_id))
    ).scalar_one_or_none()
    if not ticket:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="报修单不存在")
    await _assert_ticket_access(db, ticket, current_user, allow_participant=True)

    if not ticket.repair_no:
        return create_response(
            data={"list": [], "total": 0},
            message="报修单缺少 repair_no，无法匹配候选",
        )

    stmt = select(ImportRepairRow).where(ImportRepairRow.repair_no == ticket.repair_no)
    rows = (await db.execute(stmt.limit(20))).scalars().all()
    return create_response(
        data={
            "list": [
                {
                    "id": r.id,
                    "repair_no": r.repair_no,
                    "report_user_name": r.report_user_name,
                    "report_phone": r.report_phone,
                    "issue_content": r.issue_content,
                }
                for r in rows
            ],
            "total": len(rows),
        },
        message="获取匹配候选成功",
    )


@router.post("/repair-orders/{ticket_id}/match", response_model=Dict[str, Any])
async def repair_apply_match(
    ticket_id: int,
    payload: Dict[str, Any],
    db: AsyncSession = Depends(get_db),
    current_user: Member = Depends(get_current_user),
) -> Dict[str, Any]:
    row_id = _to_int(payload.get("import_repair_row_id") or payload.get("importRepairRowId"), 0)
    if row_id <= 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="import_repair_row_id 非法")

    ticket = (
        await db.execute(select(RepairTicket).where(RepairTicket.id == ticket_id))
    ).scalar_one_or_none()
    if not ticket:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="报修单不存在")

    await _assert_ticket_access(db, ticket, current_user, allow_participant=True)

    import_row = (
        await db.execute(select(ImportRepairRow).where(ImportRepairRow.id == row_id))
    ).scalar_one_or_none()
    if not import_row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="导入明细不存在")

    exists = (
        await db.execute(
            select(RepairMatchApplication).where(RepairMatchApplication.repair_ticket_id == ticket_id)
        )
    ).scalar_one_or_none()
    if exists:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="该报修单已提交匹配申请")

    app = RepairMatchApplication(
        repair_ticket_id=ticket_id,
        import_repair_row_id=row_id,
        applied_by=current_user.id,
        apply_note=payload.get("note"),
        status=0,
    )
    db.add(app)
    await db.commit()
    await db.refresh(app)
    return create_response(data={"id": app.id}, message="匹配申请已提交")


@router.post("/admin/repair-orders/{ticket_id}/approve-match", response_model=Dict[str, Any])
async def admin_approve_repair_match(
    ticket_id: int,
    payload: Dict[str, Any],
    db: AsyncSession = Depends(get_db),
    current_user: Member = Depends(get_current_active_admin),
) -> Dict[str, Any]:
    app = (
        await db.execute(
            select(RepairMatchApplication).where(RepairMatchApplication.repair_ticket_id == ticket_id)
        )
    ).scalar_one_or_none()
    ticket = (
        await db.execute(select(RepairTicket).where(RepairTicket.id == ticket_id))
    ).scalar_one_or_none()
    if not app or not ticket:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="匹配申请不存在")
    if app.status != 0:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="匹配申请已审核")

    approve = bool(payload.get("approve", True))
    app.status = 1 if approve else 2
    app.reviewed_by = current_user.id
    app.reviewed_at = datetime.now(timezone.utc)

    if approve:
        import_row = (
            await db.execute(select(ImportRepairRow).where(ImportRepairRow.id == app.import_repair_row_id))
        ).scalar_one_or_none()
        if not import_row:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="关联导入明细不存在")

        ticket.match_status = 2
        ticket.matched_import_row_id = app.import_repair_row_id
    else:
        ticket.match_status = 3

    await db.commit()
    return create_response(data={"repair_ticket_id": ticket_id, "status": app.status}, message="报修匹配审核完成")


@router.post("/admin/repair-imports", response_model=Dict[str, Any])
async def admin_create_repair_import(
    payload: Dict[str, Any],
    db: AsyncSession = Depends(get_db),
    current_user: Member = Depends(get_current_active_admin),
) -> Dict[str, Any]:
    rows = payload.get("rows") or []
    batch = ImportBatch(
        batch_type="repair_total",
        file_name=payload.get("file_name") or payload.get("fileName") or "manual_import",
        imported_by=current_user.id,
        total_rows=len(rows),
        success_rows=len(rows),
        failed_rows=0,
        status=2,
        finished_at=datetime.now(timezone.utc),
    )
    db.add(batch)
    await db.flush()

    for item in rows:
        db.add(
            ImportRepairRow(
                import_batch_id=batch.id,
                repair_no=item.get("repair_no") or item.get("repairNo"),
                report_user_name=item.get("report_user_name") or item.get("reportUserName"),
                report_phone=item.get("report_phone") or item.get("reportPhone"),
                building_name=item.get("building_name") or item.get("buildingName"),
                room_no=item.get("room_no") or item.get("roomNo"),
                issue_content=item.get("issue_content") or item.get("issueContent"),
                raw_payload=item,
            )
        )
    await db.commit()
    return create_response(data={"batch_id": batch.id, "total_rows": len(rows)}, message="报修导入批次创建成功")
