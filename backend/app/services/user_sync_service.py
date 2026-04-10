"""Best-effort synchronization from legacy member to app_user/profile."""

import logging
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.app_user import AppUser, AppUserRole, AppUserStatus
from app.models.member import Member, UserRole
from app.models.user_profile import UserProfile

logger = logging.getLogger(__name__)


class UserSyncService:
    """Synchronize legacy member records to new dual-write tables."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    @staticmethod
    def _resolve_student_no(member: Member) -> str:
        """Provide a non-empty student number for app_user."""
        if member.student_id and member.student_id.strip():
            return member.student_id.strip()
        return member.username

    @staticmethod
    def _map_role(member_role: UserRole) -> str:
        """Map legacy role enum to app_user role code."""
        if member_role == UserRole.ADMIN:
            return AppUserRole.ADMIN.value
        return AppUserRole.USER.value

    @staticmethod
    def _map_status(is_active: bool) -> int:
        """Map member active flag to app_user status."""
        return int(AppUserStatus.ENABLED if is_active else AppUserStatus.DISABLED)

    async def _find_existing_app_user(self, member: Member) -> Optional[AppUser]:
        """Find existing app_user by id first, then by student_no."""
        by_id_result = await self.db.execute(
            select(AppUser).where(AppUser.id == member.id)
        )
        by_id = by_id_result.scalar_one_or_none()
        if isinstance(by_id, AppUser):
            return by_id

        student_no = self._resolve_student_no(member)
        by_student_result = await self.db.execute(
            select(AppUser).where(AppUser.student_no == student_no)
        )
        by_student = by_student_result.scalar_one_or_none()
        if isinstance(by_student, AppUser):
            if by_student.id != member.id:
                logger.warning(
                    "app_user id mismatch for member %s: app_user=%s",
                    member.id,
                    by_student.id,
                )
            return by_student

        return None

    async def sync_member(
        self, member: Member, *, commit: bool = False
    ) -> Optional[AppUser]:
        """Upsert app_user and user_profile from member snapshot."""
        if member.id is None:
            logger.warning("Skip user sync because member.id is None")
            return None

        student_no = self._resolve_student_no(member)
        app_user = await self._find_existing_app_user(member)

        if app_user is None:
            app_user = AppUser(
                id=member.id,
                student_no=student_no,
                password_hash=member.password_hash,
                real_name=member.name,
            )
            self.db.add(app_user)

        app_user.student_no = student_no
        app_user.password_hash = member.password_hash
        app_user.real_name = member.name
        app_user.role_code = self._map_role(member.role)
        app_user.phone = member.phone
        app_user.email = member.email
        app_user.status = self._map_status(member.is_active)
        app_user.last_login_at = member.last_login

        await self.db.flush()

        profile_result = await self.db.execute(
            select(UserProfile).where(UserProfile.user_id == app_user.id)
        )
        profile = profile_result.scalar_one_or_none()

        if not isinstance(profile, UserProfile):
            profile = UserProfile(user_id=app_user.id)
            self.db.add(profile)

        profile.nickname = member.name
        profile.department_name = member.department
        profile.class_name = member.class_name

        if commit:
            await self.db.commit()

        return app_user
