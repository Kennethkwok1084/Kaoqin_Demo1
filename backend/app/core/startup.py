"""
应用启动初始化服务
处理数据库迁移和初始管理员用户创建
"""

import logging
import subprocess
import sys
from pathlib import Path
from typing import Optional

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import async_engine, get_async_session
from app.core.security import get_password_hash
from app.models.member import Member, UserRole

logger = logging.getLogger(__name__)


class StartupService:
    """启动服务，处理数据库初始化和基础数据创建"""

    @staticmethod
    async def check_database_tables() -> bool:
        """
        检查数据库是否有基础表

        Returns:
            bool: True if tables exist, False otherwise
        """
        try:
            async with async_engine.begin() as conn:
                # 兼容双轨迁移：旧核心表集与新核心表集任一完整即视为可用。
                result = await conn.execute(text("""
                    SELECT
                        SUM(CASE WHEN table_name IN ('members', 'repair_tasks', 'assistance_tasks', 'monitoring_tasks') THEN 1 ELSE 0 END) AS legacy_count,
                        SUM(CASE WHEN table_name IN ('app_user', 'auth_refresh_token', 'building', 'dorm_room') THEN 1 ELSE 0 END) AS baseline_count
                    FROM information_schema.tables
                    WHERE table_schema = 'public'
                    AND table_name IN (
                        'members', 'repair_tasks', 'assistance_tasks', 'monitoring_tasks',
                        'app_user', 'auth_refresh_token', 'building', 'dorm_room'
                    )
                """))
                row = result.one()
                legacy_count = int(row.legacy_count or 0)
                baseline_count = int(row.baseline_count or 0)
                return legacy_count >= 4 or baseline_count >= 4
        except Exception as e:
            logger.error(f"检查数据库表失败: {e}")
            return False

    @staticmethod
    async def run_database_migration() -> bool:
        """
        运行数据库迁移 (使用subprocess方式)

        Returns:
            bool: True if migration successful, False otherwise
        """
        try:
            logger.info("开始执行数据库迁移...")

            # 获取项目根目录
            project_root = Path(__file__).parent.parent.parent

            # 运行alembic upgrade命令
            # 首先尝试直接调用alembic
            alembic_cmd = ["alembic", "upgrade", "head"]

            # 如果在虚拟环境中，优先使用虚拟环境中的alembic
            venv_alembic = project_root / ".venv" / "bin" / "alembic"
            if venv_alembic.exists():
                alembic_cmd = [str(venv_alembic), "upgrade", "head"]
            else:
                # 备选方案：使用python -m alembic
                alembic_cmd = [sys.executable, "-m", "alembic", "upgrade", "head"]

            result = subprocess.run(
                alembic_cmd,
                cwd=project_root,
                capture_output=True,
                text=True,
                timeout=60,  # 1分钟超时
                env={**subprocess.os.environ, "PYTHONPATH": str(project_root)}
            )

            if result.returncode == 0:
                logger.info("数据库迁移完成")
                logger.debug(f"迁移输出: {result.stdout}")
                return True
            else:
                logger.error(f"数据库迁移失败: {result.stderr}")
                logger.error(f"迁移输出: {result.stdout}")
                return False

        except subprocess.TimeoutExpired:
            logger.error("数据库迁移超时")
            return False
        except Exception as e:
            logger.error(f"执行数据库迁移时发生错误: {e}")
            return False

    @staticmethod
    async def check_admin_user_exists() -> bool:
        """
        检查是否存在管理员用户

        Returns:
            bool: True if admin user exists, False otherwise
        """
        try:
            async with async_engine.begin() as conn:
                # 检查是否有管理员用户
                result = await conn.execute(text("""
                    SELECT COUNT(*)
                    FROM members
                    WHERE role = 'admin' OR username = 'admin'
                """))
                admin_count = result.scalar()
                return admin_count > 0
        except Exception as e:
            logger.error(f"检查管理员用户失败: {e}")
            return False

    @staticmethod
    async def create_default_admin_user() -> bool:
        """
        创建默认管理员用户 admin/123456

        Returns:
            bool: True if user created successfully, False otherwise
        """
        try:
            logger.info("创建默认管理员用户...")

            # 获取数据库会话
            async for db_session in get_async_session():
                try:
                    # 检查用户名是否已存在
                    existing_user = await db_session.execute(
                        text("SELECT id FROM members WHERE username = :username"),
                        {"username": "admin"}
                    )
                    if existing_user.scalar():
                        logger.info("管理员用户已存在，跳过创建")
                        return True

                    # 创建管理员用户
                    hashed_password = get_password_hash("123456")

                    admin_user = Member(
                        username="admin",
                        name="系统管理员",
                        student_id="ADMIN001",
                        phone="",
                        email="admin@system.local",
                        department="系统管理部",
                        class_name="Default Class",
                        password_hash=hashed_password,
                        role=UserRole.ADMIN,
                        is_active=True,
                        profile_completed=True,
                        is_verified=True
                    )

                    db_session.add(admin_user)
                    await db_session.commit()
                    await db_session.refresh(admin_user)

                    logger.info(f"成功创建管理员用户: {admin_user.username} (ID: {admin_user.id})")
                    return True

                except Exception as e:
                    await db_session.rollback()
                    logger.error(f"创建管理员用户时发生错误: {e}")
                    return False
                finally:
                    await db_session.close()
                    break  # 只需要第一个会话

        except Exception as e:
            logger.error(f"创建管理员用户失败: {e}")
            return False

    @classmethod
    async def initialize_application(cls) -> bool:
        """
        初始化应用程序
        包括数据库迁移和创建默认管理员用户

        Returns:
            bool: True if initialization successful, False otherwise
        """
        logger.info("开始应用程序初始化...")

        try:
            # 1. 检查数据库表是否存在
            tables_exist = await cls.check_database_tables()

            if not tables_exist:
                logger.info("检测到数据库表不存在或不完整，开始执行迁移...")
                migration_success = await cls.run_database_migration()
                if not migration_success:
                    logger.error("数据库迁移失败，应用程序无法启动")
                    return False
                logger.info("数据库迁移完成")

                # 重新检查表是否存在（等待一秒以确保事务提交）
                import time
                time.sleep(1)
                tables_exist_after_migration = await cls.check_database_tables()
                if not tables_exist_after_migration:
                    logger.error("迁移后数据库表仍不存在，可能存在事务同步问题")
                    return False
                logger.info("迁移后表检查通过")
            else:
                logger.info("数据库表检查通过")

            # 2. 检查是否存在管理员用户
            admin_exists = await cls.check_admin_user_exists()

            if not admin_exists:
                logger.info("未检测到管理员用户，创建默认管理员...")
                admin_creation_success = await cls.create_default_admin_user()
                if not admin_creation_success:
                    logger.warning("创建默认管理员用户失败，但不影响应用启动")
                else:
                    logger.info("默认管理员用户创建完成")
                    logger.info("默认管理员账号: admin / 123456")
                    logger.warning("请在首次登录后立即修改默认密码！")
            else:
                logger.info("管理员用户检查通过")

            logger.info("应用程序初始化完成")
            return True

        except Exception as e:
            logger.error(f"应用程序初始化失败: {e}")
            return False


# 提供便捷的初始化函数
async def initialize_app() -> bool:
    """
    初始化应用程序的便捷函数

    Returns:
        bool: True if successful, False otherwise
    """
    return await StartupService.initialize_application()