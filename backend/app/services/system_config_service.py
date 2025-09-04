"""
系统配置管理服务
处理系统参数的增删改查和初始化
"""

import logging
from typing import Any, Dict, List, Optional, cast

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.system_config import SystemConfig

logger = logging.getLogger(__name__)


class SystemConfigService:
    """系统配置管理服务"""

    def __init__(self, db: AsyncSession):
        self.db = db

    # 默认系统配置
    DEFAULT_CONFIGS: List[Dict[str, Any]] = [
        # 工时计算参数
        {
            "config_key": "work_hours.online_task_minutes",
            "config_name": "线上任务工时",
            "config_description": "每个线上任务的标准工时（分钟）",
            "category": "work_hours",
            "config_group": "基础工时",
            "value_type": "integer",
            "default_value": "40",
            "min_value": 1,
            "max_value": 480,
            "display_order": 1,
            "is_system_config": True,
            "required_role": "admin",
        },
        {
            "config_key": "work_hours.offline_task_minutes",
            "config_name": "线下任务工时",
            "config_description": "每个线下任务的标准工时（分钟）",
            "category": "work_hours",
            "config_group": "基础工时",
            "value_type": "integer",
            "default_value": "100",
            "min_value": 1,
            "max_value": 480,
            "display_order": 2,
            "is_system_config": True,
            "required_role": "admin",
        },
        {
            "config_key": "work_hours.rush_bonus_minutes",
            "config_name": "爆单任务奖励",
            "config_description": "爆单任务额外奖励工时（分钟）",
            "category": "work_hours",
            "config_group": "奖励工时",
            "value_type": "integer",
            "default_value": "15",
            "min_value": 0,
            "max_value": 120,
            "display_order": 3,
            "is_system_config": True,
            "required_role": "admin",
        },
        {
            "config_key": "work_hours.good_review_bonus_minutes",
            "config_name": "非默认好评奖励",
            "config_description": "非默认好评额外奖励工时（分钟）",
            "category": "work_hours",
            "config_group": "奖励工时",
            "value_type": "integer",
            "default_value": "30",
            "min_value": 0,
            "max_value": 120,
            "display_order": 4,
            "is_system_config": True,
            "required_role": "admin",
        },
        {
            "config_key": "work_hours.inspection_minutes_per_cabinet",
            "config_name": "巡检时长（每机柜）",
            "config_description": "每个机柜的巡检工时（分钟）",
            "category": "work_hours",
            "config_group": "巡检工时",
            "value_type": "integer",
            "default_value": "5",
            "min_value": 1,
            "max_value": 60,
            "display_order": 5,
            "is_system_config": True,
            "required_role": "admin",
        },
        # 扣时规则参数
        {
            "config_key": "penalties.late_response_minutes",
            "config_name": "超时响应扣时",
            "config_description": "超时响应扣除的工时（分钟/单）",
            "category": "penalties",
            "config_group": "扣时规则",
            "value_type": "integer",
            "default_value": "30",
            "min_value": 0,
            "max_value": 240,
            "display_order": 11,
            "is_system_config": True,
            "required_role": "admin",
        },
        {
            "config_key": "penalties.late_completion_minutes",
            "config_name": "超时处理扣时",
            "config_description": "超时处理扣除的工时（分钟/人）",
            "category": "penalties",
            "config_group": "扣时规则",
            "value_type": "integer",
            "default_value": "30",
            "min_value": 0,
            "max_value": 240,
            "display_order": 12,
            "is_system_config": True,
            "required_role": "admin",
        },
        {
            "config_key": "penalties.bad_review_minutes",
            "config_name": "差评扣时",
            "config_description": "差评扣除的工时（分钟/单）",
            "category": "penalties",
            "config_group": "扣时规则",
            "value_type": "integer",
            "default_value": "60",
            "min_value": 0,
            "max_value": 240,
            "display_order": 13,
            "is_system_config": True,
            "required_role": "admin",
        },
        # 时间阈值参数
        {
            "config_key": "thresholds.response_timeout_hours",
            "config_name": "响应超时阈值",
            "config_description": "报修单响应超时阈值（小时）",
            "category": "thresholds",
            "config_group": "时间阈值",
            "value_type": "integer",
            "default_value": "24",
            "min_value": 1,
            "max_value": 168,
            "display_order": 21,
            "is_system_config": True,
            "required_role": "admin",
        },
        {
            "config_key": "thresholds.completion_timeout_hours",
            "config_name": "处理超时阈值",
            "config_description": "报修单处理超时阈值（小时）",
            "category": "thresholds",
            "config_group": "时间阈值",
            "value_type": "integer",
            "default_value": "48",
            "min_value": 1,
            "max_value": 168,
            "display_order": 22,
            "is_system_config": True,
            "required_role": "admin",
        },
        {
            "config_key": "thresholds.monthly_carryover_hours",
            "config_name": "月度结转阈值",
            "config_description": "上月工时结转到本月的阈值（小时）",
            "category": "thresholds",
            "config_group": "时间阈值",
            "value_type": "integer",
            "default_value": "30",
            "min_value": 0,
            "max_value": 200,
            "display_order": 23,
            "is_system_config": True,
            "required_role": "admin",
        },
        # 系统通用配置
        {
            "config_key": "system.app_name",
            "config_name": "应用名称",
            "config_description": "系统应用显示名称",
            "category": "general",
            "config_group": "系统设置",
            "value_type": "string",
            "default_value": "学生网管考勤系统",
            "display_order": 31,
            "is_system_config": True,
            "required_role": "admin",
        },
        {
            "config_key": "system.maintenance_mode",
            "config_name": "维护模式",
            "config_description": "是否启用系统维护模式",
            "category": "general",
            "config_group": "系统设置",
            "value_type": "boolean",
            "default_value": "false",
            "display_order": 32,
            "is_system_config": True,
            "required_role": "admin",
        },
        {
            "config_key": "system.max_import_rows",
            "config_name": "最大导入行数",
            "config_description": "单次数据导入的最大行数限制",
            "category": "general",
            "config_group": "系统设置",
            "value_type": "integer",
            "default_value": "10000",
            "min_value": 100,
            "max_value": 100000,
            "display_order": 33,
            "is_system_config": True,
            "required_role": "admin",
        },
    ]

    async def initialize_default_configs(self) -> Dict[str, Any]:
        """初始化默认系统配置"""
        try:
            created_count = 0
            updated_count = 0
            skipped_count = 0

            for config_data in self.DEFAULT_CONFIGS:
                config_key = config_data["config_key"]

                # 检查配置是否已存在
                query = select(SystemConfig).where(
                    SystemConfig.config_key == config_key
                )
                result = await self.db.execute(query)
                existing_config = result.scalar_one_or_none()

                if existing_config:
                    # 更新现有配置的元数据（但保留用户设置的值）
                    existing_config.config_name = cast(str, config_data["config_name"])
                    existing_config.config_description = cast(
                        Optional[str], config_data["config_description"]
                    )
                    existing_config.category = cast(str, config_data["category"])
                    existing_config.config_group = cast(
                        Optional[str], config_data["config_group"]
                    )
                    existing_config.value_type = cast(str, config_data["value_type"])
                    existing_config.min_value = cast(
                        Optional[float], config_data.get("min_value")
                    )
                    existing_config.max_value = cast(
                        Optional[float], config_data.get("max_value")
                    )
                    existing_config.display_order = cast(
                        int, config_data["display_order"]
                    )
                    existing_config.is_system_config = cast(
                        bool, config_data["is_system_config"]
                    )
                    existing_config.required_role = cast(
                        str, config_data["required_role"]
                    )

                    # 如果没有设置过值，使用默认值
                    if not existing_config.config_value:
                        existing_config.config_value = cast(
                            Optional[str], config_data["default_value"]
                        )

                    # 更新默认值
                    existing_config.default_value = cast(
                        Optional[str], config_data["default_value"]
                    )

                    updated_count += 1
                    logger.info(f"Updated system config: {config_key}")
                else:
                    # 创建新配置
                    new_config = SystemConfig()
                    new_config.config_key = cast(str, config_data["config_key"])
                    new_config.config_name = cast(str, config_data["config_name"])
                    new_config.config_description = cast(
                        Optional[str], config_data["config_description"]
                    )
                    new_config.category = cast(str, config_data["category"])
                    new_config.config_group = cast(
                        Optional[str], config_data["config_group"]
                    )
                    new_config.config_value = cast(
                        Optional[str], config_data["default_value"]
                    )
                    new_config.default_value = cast(
                        Optional[str], config_data["default_value"]
                    )
                    new_config.value_type = cast(str, config_data["value_type"])
                    new_config.min_value = cast(
                        Optional[float], config_data.get("min_value")
                    )
                    new_config.max_value = cast(
                        Optional[float], config_data.get("max_value")
                    )
                    new_config.display_order = cast(int, config_data["display_order"])
                    new_config.is_system_config = cast(
                        bool, config_data["is_system_config"]
                    )
                    new_config.required_role = cast(str, config_data["required_role"])
                    new_config.is_active = True

                    self.db.add(new_config)
                    created_count += 1
                    logger.info(f"Created system config: {config_key}")

            await self.db.commit()

            initialization_result: Dict[str, Any] = {
                "success": True,
                "created_count": created_count,
                "updated_count": updated_count,
                "skipped_count": skipped_count,
                "total_configs": len(self.DEFAULT_CONFIGS),
            }

            logger.info(
                f"System config initialization completed: {initialization_result}"
            )
            return initialization_result

        except Exception as e:
            logger.error(f"Failed to initialize system configs: {str(e)}")
            await self.db.rollback()
            raise

    async def get_config_value(self, config_key: str, default: Any = None) -> Any:
        """获取配置值（类型转换后）"""
        try:
            query = select(SystemConfig).where(
                and_(
                    SystemConfig.config_key == config_key,
                    SystemConfig.is_active.is_(True),
                )
            )
            result = await self.db.execute(query)
            config = result.scalar_one_or_none()

            if config:
                return config.get_typed_value()
            return default

        except Exception as e:
            logger.error(f"Failed to get config value for {config_key}: {str(e)}")
            return default

    async def set_config_value(self, config_key: str, value: Any) -> bool:
        """设置配置值"""
        try:
            query = select(SystemConfig).where(SystemConfig.config_key == config_key)
            result = await self.db.execute(query)
            config = result.scalar_one_or_none()

            if not config:
                logger.warning(f"Config key not found: {config_key}")
                return False

            # 验证值
            if not config.validate_value(value):
                logger.warning(f"Invalid value for config {config_key}: {value}")
                return False

            # 设置值
            config.set_typed_value(value)
            await self.db.commit()

            logger.info(f"Config updated: {config_key} = {value}")
            return True

        except Exception as e:
            logger.error(f"Failed to set config value for {config_key}: {str(e)}")
            await self.db.rollback()
            return False

    async def get_configs_by_category(self, category: str) -> List[SystemConfig]:
        """按分类获取配置列表"""
        try:
            query = (
                select(SystemConfig)
                .where(
                    and_(
                        SystemConfig.category == category,
                        SystemConfig.is_active.is_(True),
                    )
                )
                .order_by(SystemConfig.display_order, SystemConfig.config_key)
            )
            result = await self.db.execute(query)
            return list(result.scalars().all())

        except Exception as e:
            logger.error(f"Failed to get configs by category {category}: {str(e)}")
            return []

    async def get_all_configs(
        self, include_inactive: bool = False
    ) -> List[SystemConfig]:
        """获取所有配置"""
        try:
            query = select(SystemConfig)
            if not include_inactive:
                query = query.where(SystemConfig.is_active.is_(True))
            query = query.order_by(
                SystemConfig.category,
                SystemConfig.display_order,
                SystemConfig.config_key,
            )

            result = await self.db.execute(query)
            return list(result.scalars().all())

        except Exception as e:
            logger.error(f"Failed to get all configs: {str(e)}")
            return []

    async def bulk_update_configs(
        self, config_updates: Dict[str, Any]
    ) -> Dict[str, Any]:
        """批量更新配置"""
        try:
            success_count = 0
            failed_count = 0
            failed_keys = []

            for config_key, value in config_updates.items():
                success = await self.set_config_value(config_key, value)
                if success:
                    success_count += 1
                else:
                    failed_count += 1
                    failed_keys.append(config_key)

            return {
                "success": failed_count == 0,
                "success_count": success_count,
                "failed_count": failed_count,
                "failed_keys": failed_keys,
            }

        except Exception as e:
            logger.error(f"Failed to bulk update configs: {str(e)}")
            return {"success": False, "error": str(e)}

    async def reset_config_to_default(self, config_key: str) -> bool:
        """重置配置为默认值"""
        try:
            query = select(SystemConfig).where(SystemConfig.config_key == config_key)
            result = await self.db.execute(query)
            config = result.scalar_one_or_none()

            if not config:
                return False

            config.config_value = config.default_value
            await self.db.commit()

            logger.info(f"Config reset to default: {config_key}")
            return True

        except Exception as e:
            logger.error(f"Failed to reset config {config_key}: {str(e)}")
            await self.db.rollback()
            return False

    async def get_work_hours_config(self) -> Dict[str, int]:
        """获取工时计算配置（便捷方法）"""
        return {
            "online_task_minutes": await self.get_config_value(
                "work_hours.online_task_minutes", 40
            ),
            "offline_task_minutes": await self.get_config_value(
                "work_hours.offline_task_minutes", 100
            ),
            "rush_bonus_minutes": await self.get_config_value(
                "work_hours.rush_bonus_minutes", 15
            ),
            "good_review_bonus_minutes": await self.get_config_value(
                "work_hours.good_review_bonus_minutes", 30
            ),
            "inspection_minutes_per_cabinet": await self.get_config_value(
                "work_hours.inspection_minutes_per_cabinet", 5
            ),
        }

    async def get_penalties_config(self) -> Dict[str, int]:
        """获取扣时规则配置（便捷方法）"""
        return {
            "late_response_minutes": await self.get_config_value(
                "penalties.late_response_minutes", 30
            ),
            "late_completion_minutes": await self.get_config_value(
                "penalties.late_completion_minutes", 30
            ),
            "bad_review_minutes": await self.get_config_value(
                "penalties.bad_review_minutes", 60
            ),
        }

    async def get_thresholds_config(self) -> Dict[str, int]:
        """获取时间阈值配置（便捷方法）"""
        return {
            "response_timeout_hours": await self.get_config_value(
                "thresholds.response_timeout_hours", 24
            ),
            "completion_timeout_hours": await self.get_config_value(
                "thresholds.completion_timeout_hours", 48
            ),
            "monthly_carryover_hours": await self.get_config_value(
                "thresholds.monthly_carryover_hours", 30
            ),
        }
