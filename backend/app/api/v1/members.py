"""
鍏ㄦ柊鐨勬垚鍛樼鐞咥PI
瀹屽叏閲嶆瀯鍚庣殑涓氬姟閫昏緫鍜屾帴鍙ｈ璁?
"""

import logging
import time
from datetime import date
from io import BytesIO
from typing import Any, Dict, List, Optional
from urllib.parse import quote

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    Query,
    UploadFile,
    status,
)
from fastapi.responses import JSONResponse, StreamingResponse
from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import (
    create_response,
    get_current_active_admin,
    get_current_active_user,
    get_db,
)
from app.core.security import get_password_hash, verify_password
from app.models.member import Member, UserRole
from app.schemas.member import (
    MemberCreate,
    MemberImportRequest,
    MemberUpdate,
    PasswordChangeRequest,
)
from app.services.import_service import DataImportService

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/", response_model=Dict[str, Any])
async def get_members(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    search: Optional[str] = Query(None, description="搜索关键字"),
    role: Optional[str] = Query(None, description="角色筛选"),
    is_active: Optional[bool] = Query(None, description="状态筛选"),
    department: Optional[str] = Query(None, description="部门筛选"),
    class_name: Optional[str] = Query(None, description="班级筛选"),
    current_user: Member = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """
    鑾峰彇鎴愬憳鍒楄〃
    鏀寔鍒嗛〉銆佹悳绱㈠拰澶氬瓧娈电瓫閫?
    """
    try:
        # 鏋勫缓鏌ヨ鏉′欢
        query = select(Member)

        # 鎼滅储鏉′欢
        if search:
            search_pattern = f"%{search}%"
            query = query.where(
                or_(
                    Member.username.ilike(search_pattern),
                    Member.name.ilike(search_pattern),
                    Member.student_id.ilike(search_pattern),
                )
            )

        # 瑙掕壊绛涢€?
        if role and role in [r.value for r in UserRole]:
            query = query.where(Member.role == UserRole(role))

        # 鐘舵€佺瓫閫?
        if is_active is not None:
            query = query.where(Member.is_active == is_active)

        # 閮ㄩ棬绛涢€?
        if department:
            query = query.where(Member.department.ilike(f"%{department}%"))

        # 鐝骇绛涢€?
        if class_name:
            query = query.where(Member.class_name.ilike(f"%{class_name}%"))

        # 鑾峰彇鎬绘暟
        count_query = select(func.count()).select_from(query.subquery())
        result = await db.execute(count_query)
        total = result.scalar()

        # 鍒嗛〉鏌ヨ
        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size).order_by(Member.created_at.desc())

        result = await db.execute(query)
        members = result.scalars().all()

        # 鏋勫缓鍝嶅簲鏁版嵁
        member_list = []
        for member in members:
            if hasattr(member, "get_safe_dict"):
                member_dict = member.get_safe_dict()
                member_list.append(member_dict)

        total_pages = ((total or 0) + page_size - 1) // page_size

        return create_response(
            data={
                "items": member_list,
                "total": total,
                "page": page,
                "page_size": page_size,
                "total_pages": total_pages,
            },
            message=f"成功获取成员列表，共 {total} 条记录",
        )

    except Exception as e:
        logger.error(f"获取成员列表失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="获取成员列表失败"
        )


@router.post("/", response_model=Dict[str, Any])
async def create_member(
    member_data: MemberCreate,
    current_user: Member = Depends(get_current_active_admin),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """
    鍒涘缓鏂版垚鍛?
    浠呯鐞嗗憳鍙搷浣?
    """
    try:
        # 妫€鏌ョ敤鎴峰悕鏄惁宸插瓨鍦?
        query = select(Member).where(Member.username == member_data.username)
        result = await db.execute(query)
        if result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"用户名 {member_data.username} 已存在",
            )

        # 妫€鏌ュ鍙锋槸鍚﹀凡瀛樺湪锛堜粎褰撳鍙蜂笉涓虹┖鏃讹級
        if member_data.student_id:
            query = select(Member).where(Member.student_id == member_data.student_id)
            result = await db.execute(query)
            if result.scalar_one_or_none():
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"学号 {member_data.student_id} 已存在",
                )

        # 鍒涘缓鏂版垚鍛?
        new_member = Member(
            username=member_data.username,
            name=member_data.name,
            student_id=member_data.student_id,
            phone=member_data.phone,
            department=member_data.department,
            class_name=member_data.class_name,
            group_id=member_data.group_id,
            join_date=member_data.join_date,
            password_hash=get_password_hash(member_data.password),
            role=member_data.role,
            is_active=member_data.is_active,
            is_verified=False,
        )

        db.add(new_member)
        await db.commit()
        await db.refresh(new_member)

        logger.info(f"新成员创建成功: {new_member.username} by {current_user.username}")

        return create_response(
            data=new_member.get_safe_dict(),
            message=f"成功创建成员：{new_member.name} ({new_member.student_id})",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"创建成员失败: {str(e)}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="创建成员失败"
        )


@router.put("/{member_id}", response_model=Dict[str, Any])
async def update_member(
    member_id: int,
    member_data: MemberUpdate,
    current_user: Member = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """
    鏇存柊鎴愬憳淇℃伅
    绠＄悊鍛樺彲鏇存柊鎵€鏈夛紝鏅€氱敤鎴峰彧鑳芥洿鏂拌嚜宸辩殑閮ㄥ垎淇℃伅
    """
    try:
        query = select(Member).where(Member.id == member_id)
        result = await db.execute(query)
        member = result.scalar_one_or_none()

        if not member:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="成员不存在"
            )

        # 鏉冮檺妫€鏌?
        can_update_all = current_user.can_manage_group
        is_self_update = current_user.id == member_id

        if not can_update_all and not is_self_update:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="无权更新该成员信息"
            )

        # 鏇存柊瀛楁
        update_data = member_data.dict(exclude_unset=True)

        # 鏅€氱敤鎴峰彧鑳芥洿鏂伴儴鍒嗗瓧娈?
        if not can_update_all:
            allowed_fields = {"username", "phone"}
            update_data = {k: v for k, v in update_data.items() if k in allowed_fields}

        # 妫€鏌ョ敤鎴峰悕鍞竴鎬?
        if "username" in update_data and update_data["username"] != member.username:
            query = select(Member).where(
                and_(Member.username == update_data["username"], Member.id != member_id)
            )
            result = await db.execute(query)
            if result.scalar_one_or_none():
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"用户名 {update_data['username']} 已存在",
                )

        if "student_id" in update_data:
            student_id_value = update_data["student_id"] or None
            update_data["student_id"] = student_id_value

            if student_id_value:
                query = select(Member).where(
                    and_(
                        Member.student_id == student_id_value,
                        Member.id != member_id,
                    )
                )
                result = await db.execute(query)
                if result.scalar_one_or_none():
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail=f"学号 {student_id_value} 已存在",
                    )

        # 搴旂敤鏇存柊
        for field, value in update_data.items():
            setattr(member, field, value)

        await db.commit()
        await db.refresh(member)

        logger.info(f"成员信息更新: {member.username} by {current_user.username}")

        return create_response(data=member.get_safe_dict(), message="成员信息更新成功")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新成员信息失败: {str(e)}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="更新成员信息失败"
        )


@router.delete("/{member_id}", response_model=Dict[str, Any])
async def delete_member(
    member_id: int,
    current_user: Member = Depends(get_current_active_admin),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """
    鍒犻櫎鎴愬憳
    浠呯鐞嗗憳鍙搷浣?
    """
    try:
        query = select(Member).where(Member.id == member_id)
        result = await db.execute(query)
        member = result.scalar_one_or_none()

        if not member:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="成员不存在"
            )

        # 涓嶈兘鍒犻櫎鑷繁
        if member.id == current_user.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="不能删除自己的账户"
            )

        member_name = member.name
        member_username = member.username

        await db.delete(member)
        await db.commit()

        logger.info(f"成员删除: {member_username} by {current_user.username}")

        return create_response(
            data={"deleted_id": member_id}, message=f"成功删除成员：{member_name}"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除成员失败: {str(e)}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="删除成员失败"
        )


async def _import_members_from_payload(
    import_data: MemberImportRequest,
    db: AsyncSession,
) -> Dict[str, Any]:
    """Share member import execution between JSON and Excel endpoints."""
    total_processed = len(import_data.members)
    successful_imports = 0
    failed_imports = 0
    skipped_duplicates = 0
    errors: List[str] = []

    timestamp = int(time.time())

    for index, member_item in enumerate(import_data.members):
        try:
            username = member_item.username
            if not username:
                username = f"user_{timestamp}_{index + 1:03d}"

            duplicate_conditions = []
            if username:
                duplicate_conditions.append(Member.username == username)
            if member_item.student_id:
                duplicate_conditions.append(Member.student_id == member_item.student_id)

            existing_member = None
            if duplicate_conditions:
                duplicate_check = select(Member).where(or_(*duplicate_conditions))
                duplicate_result = await db.execute(duplicate_check)
                existing_member = duplicate_result.scalar_one_or_none()

            if existing_member:
                if import_data.skip_duplicates:
                    skipped_duplicates += 1
                    continue

                failed_imports += 1
                duplicate_field = (
                    "用户名" if existing_member.username == username else "学号"
                )
                errors.append(
                    f"第 {index + 1} 行: {duplicate_field}已存在 - {member_item.name}"
                )
                continue

            role_mapping = {
                "admin": UserRole.ADMIN,
                "group_leader": UserRole.GROUP_LEADER,
                "member": UserRole.MEMBER,
                "guest": UserRole.GUEST,
            }
            role = role_mapping.get(member_item.role or "member", UserRole.MEMBER)

            # Use a savepoint per row so a single bad record does not poison the
            # whole transaction and turn a partial-success import into a 500.
            async with db.begin_nested():
                new_member = Member(
                    username=username,
                    name=member_item.name.strip(),
                    student_id=member_item.student_id.strip()
                    if member_item.student_id
                    else None,
                    phone=member_item.phone.strip() if member_item.phone else None,
                    department=(member_item.department or "信息化建设处").strip(),
                    class_name=member_item.class_name.strip(),
                    group_id=member_item.group_id,
                    join_date=date.today(),
                    password_hash=get_password_hash("123456"),
                    role=role,
                    is_active=True,
                    is_verified=False,
                    profile_completed=False,
                )

                db.add(new_member)
                await db.flush()
            successful_imports += 1

        except Exception as exc:
            failed_imports += 1
            errors.append(f"第 {index + 1} 行: {str(exc)}")
            logger.error(f"Failed to import member row {index + 1}: {str(exc)}")

    if successful_imports > 0:
        try:
            await db.commit()
        except Exception as exc:
            await db.rollback()
            logger.error(f"Commit member import failed: {str(exc)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="成员批量导入提交失败",
            ) from exc

    return {
        "total_processed": total_processed,
        "successful_imports": successful_imports,
        "failed_imports": failed_imports,
        "skipped_duplicates": skipped_duplicates,
        "errors": errors,
    }


@router.post("/import", response_model=Dict[str, Any])
async def import_members(
    import_data: MemberImportRequest,
    current_user: Member = Depends(get_current_active_admin),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """批量导入成员（JSON 结构）。"""
    logger.info("开始成员批量导入: operator=%s", current_user.username)
    result = await _import_members_from_payload(import_data, db)
    result_message = (
        f"导入完成：成功 {result['successful_imports']} 条，"
        f"失败 {result['failed_imports']} 条，跳过 {result['skipped_duplicates']} 条"
    )
    return create_response(data=result, message=result_message)


@router.post("/import-excel", response_model=Dict[str, Any])
async def import_members_excel(
    file: UploadFile = File(...),
    skip_duplicates: bool = Form(True),
    dry_run: bool = Form(False),
    current_user: Member = Depends(get_current_active_admin),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """通过 Excel/CSV 文件批量导入成员。"""
    logger.info(
        "开始 Excel 成员导入: operator=%s, filename=%s",
        current_user.username,
        file.filename,
    )

    import_service = DataImportService(db)

    try:
        parsed_result = await import_service.parse_member_import_file(file)
    except ValueError as exc:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=create_response(
                data=None,
                message=str(exc),
                status_code=status.HTTP_400_BAD_REQUEST,
                success=False,
            ),
        )

    if parsed_result["valid_rows"] == 0:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=create_response(
                data={
                    "total_rows": parsed_result["total_rows"],
                    "valid_rows": 0,
                    "invalid_rows": parsed_result["invalid_rows"],
                    "empty_rows": parsed_result["empty_rows"],
                    "errors": parsed_result["errors"],
                },
                message="导入文件校验失败，没有可导入的成员数据",
                status_code=status.HTTP_400_BAD_REQUEST,
                success=False,
            ),
        )

    if dry_run:
        return create_response(
            data={
                "total_rows": parsed_result["total_rows"],
                "valid_rows": parsed_result["valid_rows"],
                "invalid_rows": parsed_result["invalid_rows"],
                "empty_rows": parsed_result["empty_rows"],
                "preview_data": parsed_result["preview_data"],
                "errors": parsed_result["errors"],
            },
            message="成员导入校验完成",
        )

    import_payload = MemberImportRequest(
        members=parsed_result["members"],
        skip_duplicates=skip_duplicates,
    )
    result = await _import_members_from_payload(import_payload, db)
    result["total_processed"] += parsed_result["invalid_rows"]
    result["failed_imports"] += parsed_result["invalid_rows"]
    result["errors"].extend(parsed_result["errors"])
    result["file_summary"] = {
        "total_rows": parsed_result["total_rows"],
        "valid_rows": parsed_result["valid_rows"],
        "invalid_rows": parsed_result["invalid_rows"],
        "empty_rows": parsed_result["empty_rows"],
    }

    result_message = (
        f"导入完成：成功 {result['successful_imports']} 条，"
        f"失败 {result['failed_imports']} 条，跳过 {result['skipped_duplicates']} 条"
    )
    return create_response(data=result, message=result_message)


@router.post("/import/preview", response_model=Dict[str, Any])
async def preview_members_import(
    file: UploadFile = File(...),
    current_user: Member = Depends(get_current_active_admin),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """预览成员导入文件。"""
    return await import_members_excel(
        file=file,
        skip_duplicates=True,
        dry_run=True,
        current_user=current_user,
        db=db,
    )


@router.post("/import/file", response_model=Dict[str, Any])
async def import_members_file(
    file: UploadFile = File(...),
    skip_duplicates: bool = Form(True),
    current_user: Member = Depends(get_current_active_admin),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """通过文件批量导入成员。"""
    return await import_members_excel(
        file=file,
        skip_duplicates=skip_duplicates,
        dry_run=False,
        current_user=current_user,
        db=db,
    )


@router.get("/import-template")
async def get_member_import_template(
    current_user: Member = Depends(get_current_active_admin),
    db: AsyncSession = Depends(get_db),
) -> StreamingResponse:
    """下载成员导入模板 Excel 文件。"""
    _ = current_user
    filename, file_bytes = await DataImportService(db).generate_import_template_excel(
        "member_table"
    )
    encoded_filename = quote(filename)
    headers = {
        "Content-Disposition": (
            f"attachment; filename={filename}; filename*=UTF-8''{encoded_filename}"
        )
    }
    return StreamingResponse(
        BytesIO(file_bytes),
        media_type=(
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        ),
        headers=headers,
    )


@router.get("/{member_id}", response_model=Dict[str, Any])
async def get_member(
    member_id: int,
    current_user: Member = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """
    鑾峰彇鍗曚釜鎴愬憳璇︽儏
    """
    try:
        query = select(Member).where(Member.id == member_id)
        result = await db.execute(query)
        member = result.scalar_one_or_none()

        if not member:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="成员不存在"
            )

        # 鏉冮檺妫€鏌ワ細绠＄悊鍛樺拰缁勯暱鍙煡鐪嬫墍鏈夛紝鏅€氱敤鎴峰彧鑳芥煡鐪嬭嚜宸?
        if not current_user.can_manage_group and current_user.id != member_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="无权查看该成员信息"
            )

        return create_response(data=member.get_safe_dict(), message="成功获取成员信息")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取成员详情失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="获取成员详情失败"
        )


@router.post("/{member_id}/change-password", response_model=Dict[str, Any])
async def change_password(
    member_id: int,
    password_data: PasswordChangeRequest,
    current_user: Member = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """
    淇敼瀵嗙爜
    鐢ㄦ埛鍙兘淇敼鑷繁鐨勫瘑鐮侊紝绠＄悊鍛樺彲浠ラ噸缃换浣曚汉鐨勫瘑鐮?
    """
    try:
        query = select(Member).where(Member.id == member_id)
        result = await db.execute(query)
        member = result.scalar_one_or_none()

        if not member:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="成员不存在"
            )

        # 鏉冮檺妫€鏌?
        if current_user.id != member_id and not current_user.is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="无权修改该成员密码"
            )

        # 楠岃瘉鏃у瘑鐮侊紙浠呭綋淇敼鑷繁鐨勫瘑鐮佹椂锛?
        if current_user.id == member_id:
            if not verify_password(password_data.old_password, member.password_hash):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST, detail="旧密码错误"
                )

        # 鏇存柊瀵嗙爜
        member.password_hash = get_password_hash(password_data.new_password)
        await db.commit()

        logger.info(f"密码修改成功: {member.username} by {current_user.username}")

        return create_response(
            data={"updated_member_id": member_id}, message="密码修改成功"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"修改密码失败: {str(e)}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="修改密码失败"
        )


@router.get("/stats/overview", response_model=Dict[str, Any])
async def get_member_stats(
    current_user: Member = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """
    鑾峰彇鎴愬憳缁熻淇℃伅
    """
    try:
        # 鎬绘垚鍛樻暟
        total_query = select(func.count(Member.id))
        result = await db.execute(total_query)
        total_members = result.scalar()

        # 鍦ㄨ亴鎴愬憳鏁?
        active_query = select(func.count(Member.id)).where(Member.is_active)
        result = await db.execute(active_query)
        active_members = result.scalar()

        # 绂昏亴鎴愬憳鏁?
        inactive_members = (total_members or 0) - (active_members or 0)

        # 鎸夎鑹茬粺璁?
        role_stats = {}
        for role in UserRole:
            role_query = select(func.count(Member.id)).where(Member.role == role)
            result = await db.execute(role_query)
            role_stats[role.value] = result.scalar()

        # 鎸夐儴闂ㄧ粺璁?
        dept_query = select(Member.department, func.count(Member.id)).group_by(
            Member.department
        )
        result = await db.execute(dept_query)
        dept_stats = {dept: count for dept, count in result.fetchall()}

        return create_response(
            data={
                "total_members": total_members,
                "active_members": active_members,
                "inactive_members": inactive_members,
                "role_stats": role_stats,
                "department_stats": dept_stats,
            },
            message="成员统计信息获取成功",
        )

    except Exception as e:
        logger.error(f"获取成员统计失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="获取成员统计失败"
        )


@router.get("/health", response_model=Dict[str, Any])
async def members_health_check() -> Dict[str, Any]:
    """成员模块健康检查。"""
    return create_response(
        data={"module": "members", "status": "healthy", "version": "2.0"},
        message="成员管理模块运行正常",
    )


@router.post("/{member_id}/complete-profile")
async def complete_profile(
    member_id: int,
    profile_data: MemberUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: Member = Depends(get_current_active_user),
) -> JSONResponse:
    """
    瀹屽杽涓汉淇℃伅
    鐢ㄤ簬棣栨鐧诲綍鏃跺畬鍠勭敤鎴蜂俊鎭?
    """
    logger.info(f"User {current_user.id} completing profile for member {member_id}")

    # 妫€鏌ユ潈闄愶細鍙兘瀹屽杽鑷繁鐨勪俊鎭垨绠＄悊鍛樺彲浠ュ畬鍠勪换浣曚汉鐨勪俊鎭?
    if current_user.id != member_id and current_user.role != UserRole.ADMIN:
        logger.warning(
            f"User {current_user.id} attempted to complete profile "
            f"for member {member_id}"
        )
        raise HTTPException(status_code=403, detail="无权完善该用户信息")

    try:
        # 鏌ヨ鎴愬憳
        result = await db.execute(select(Member).where(Member.id == member_id))
        member = result.scalar_one_or_none()

        if not member:
            raise HTTPException(status_code=404, detail="成员不存在")

        # 鏇存柊淇℃伅
        update_data = profile_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(member, field, value)

        # 鏍囪涓哄凡瀹屽杽淇℃伅
        member.profile_completed = True

        await db.commit()
        await db.refresh(member)

        logger.info(f"Profile completed for member {member_id}")

        # 杩斿洖鏇存柊鍚庣殑鎴愬憳淇℃伅
        response_data = create_response(
            data={
                "id": member.id,
                "username": member.username,
                "profile_completed": member.profile_completed,
                "message": "个人信息完善成功",
            }
        )
        return JSONResponse(content=response_data)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error completing profile for member {member_id}: {str(e)}")
        await db.rollback()
        raise HTTPException(status_code=500, detail="完善信息失败")
