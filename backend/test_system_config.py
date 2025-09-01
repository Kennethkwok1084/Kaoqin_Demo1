#!/usr/bin/env python3
"""
系统配置测试脚本
用于测试和初始化系统配置功能
"""

import asyncio
import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_db
from app.services.system_config_service import SystemConfigService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_system_config():
    """测试系统配置功能"""
    try:
        logger.info("Starting system config test...")

        # 获取数据库连接
        db_gen = get_async_db()
        db: AsyncSession = await anext(db_gen)

        try:
            # 初始化系统配置服务
            config_service = SystemConfigService(db)

            # 初始化默认配置
            logger.info("Initializing default system configs...")
            result = await config_service.initialize_default_configs()
            logger.info(f"Initialization result: {result}")

            # 测试获取配置值
            logger.info("Testing config value retrieval...")
            online_task_minutes = await config_service.get_config_value(
                "work_hours.online_task_minutes"
            )
            offline_task_minutes = await config_service.get_config_value(
                "work_hours.offline_task_minutes"
            )
            rush_bonus_minutes = await config_service.get_config_value(
                "work_hours.rush_bonus_minutes"
            )

            logger.info(f"Online task minutes: {online_task_minutes}")
            logger.info(f"Offline task minutes: {offline_task_minutes}")
            logger.info(f"Rush bonus minutes: {rush_bonus_minutes}")

            # 测试便捷方法
            logger.info("Testing convenience methods...")
            work_hours_config = await config_service.get_work_hours_config()
            penalties_config = await config_service.get_penalties_config()
            thresholds_config = await config_service.get_thresholds_config()

            logger.info(f"Work hours config: {work_hours_config}")
            logger.info(f"Penalties config: {penalties_config}")
            logger.info(f"Thresholds config: {thresholds_config}")

            # 测试按分类获取配置
            logger.info("Testing get configs by category...")
            work_hours_configs = await config_service.get_configs_by_category(
                "work_hours"
            )
            logger.info(f"Work hours category configs count: {len(work_hours_configs)}")

            # 测试设置配置值
            logger.info("Testing set config value...")
            success = await config_service.set_config_value(
                "work_hours.online_task_minutes", 45
            )
            logger.info(f"Set config success: {success}")

            # 验证设置结果
            updated_value = await config_service.get_config_value(
                "work_hours.online_task_minutes"
            )
            logger.info(f"Updated online task minutes: {updated_value}")

            # 重置为默认值
            logger.info("Testing reset to default...")
            reset_success = await config_service.reset_config_to_default(
                "work_hours.online_task_minutes"
            )
            logger.info(f"Reset to default success: {reset_success}")

            # 验证重置结果
            reset_value = await config_service.get_config_value(
                "work_hours.online_task_minutes"
            )
            logger.info(f"Reset value: {reset_value}")

            logger.info("System config test completed successfully!")

        finally:
            await db.close()

    except Exception as e:
        logger.error(f"System config test failed: {str(e)}")
        raise


if __name__ == "__main__":
    asyncio.run(test_system_config())
