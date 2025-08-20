"""
调试版本的导入函数，完全禁用重复检查来隔离greenlet问题
"""

import logging
from typing import Any, Dict, List, Union

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import create_response, get_current_active_admin, get_db
from app.core.security import get_password_hash
from app.models.member import Member, UserRole
from app.schemas.member import MemberImportRequest

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/import-debug", response_model=Dict[str, Any])
async def import_members_debug(
    import_data: MemberImportRequest,
    current_user: Member = Depends(get_current_active_admin),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """
    调试版本的批量导入 - 完全禁用重复检查

    Args:
        import_data: 批量导入请求数据
        current_user: 当前认证的管理员用户
        db: 数据库会话

    Returns:
        Dict[str, Any]: 标准化API响应，包含导入结果统计

    Raises:
        HTTPException: 当导入过程发生错误时抛出
    """
    try:
        current_user_id: int = current_user.id

        logger.info(f"Debug import started by user {current_user_id}")
        logger.info(f"Members count: {len(import_data.members)}")

        successful_imports: int = 0
        failed_imports: int = 0
        errors: List[Dict[str, Union[int, str]]] = []
        imported_members: List[int] = []

        for index, member_data in enumerate(import_data.members):
            try:
                # 安全提取字段
                student_id_safe: str = getattr(
                    member_data, "student_id", f"debug{index}"
                )
                name_safe: str = getattr(member_data, "name", f"Debug User {index}")
                password_safe: str = getattr(member_data, "password", "default123")
                email_safe: Union[str, None] = getattr(member_data, "email", None)

                # 处理角色转换
                role_value: Union[str, UserRole] = getattr(
                    member_data, "role", "member"
                )
                if isinstance(role_value, str):
                    role_mapping: Dict[str, UserRole] = {
                        "admin": UserRole.ADMIN,
                        "group_leader": UserRole.GROUP_LEADER,
                        "member": UserRole.MEMBER,
                        "guest": UserRole.GUEST,
                    }
                    role_safe: UserRole = role_mapping.get(role_value, UserRole.MEMBER)
                else:
                    role_safe = role_value if role_value else UserRole.MEMBER

                logger.info(
                    f"Creating member {index + 1}: {name_safe} ({student_id_safe})"
                )

                # 跳过所有重复检查，直接创建
                new_member: Member = Member(
                    username=(
                        str(student_id_safe) if student_id_safe else str(name_safe)
                    ),  # 使用学号或姓名作为用户名
                    name=str(name_safe),
                    student_id=str(student_id_safe),
                    class_name="导入用户",  # 添加必需的class_name字段
                    password_hash=get_password_hash(str(password_safe)),
                    email=str(email_safe) if email_safe else None,
                    role=role_safe,
                    is_active=True,
                    is_verified=False,
                )

                db.add(new_member)
                await db.flush()  # 获取ID

                imported_members.append(new_member.id)
                successful_imports += 1
                logger.info(
                    f"Member {index + 1} created successfully with ID {new_member.id}"
                )

            except Exception as member_error:
                logger.error(f"Error creating member {index + 1}: {str(member_error)}")
                errors.append({"index": index + 1, "error": str(member_error)})
                failed_imports += 1

        # 提交事务
        if successful_imports > 0:
            await db.commit()
            logger.info(f"Transaction committed: {successful_imports} members imported")
        else:
            await db.rollback()
            logger.info("No members imported, rolling back")

        response_data: Dict[str, Any] = {
            "total_processed": len(import_data.members),
            "successful_imports": successful_imports,
            "failed_imports": failed_imports,
            "skipped_duplicates": 0,
            "errors": errors,
            "imported_members": imported_members[:10],  # 限制返回数量
        }

        return create_response(
            data=response_data,
            message=f"调试导入完成：成功 {successful_imports} 条，失败 {failed_imports} 条",
        )

    except Exception as e:
        logger.error(f"Debug import error: {str(e)}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Debug import failed: {str(e)}",
        )
