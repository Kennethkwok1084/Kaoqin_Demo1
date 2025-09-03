"""
系统设置API端点
提供系统设置的统一管理接口，匹配前端期望的API路径
"""

import logging
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException
from fastapi import status as http_status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import (
    create_error_response,
    create_response,
    get_current_active_admin,
    get_current_user,
    get_db,
)
from app.models.member import Member
from app.services.system_config_service import SystemConfigService

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/settings", response_model=Dict[str, Any])
async def get_system_settings(
    current_user: Member = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """获取系统设置"""
    try:
        config_service = SystemConfigService(db)

        # 获取所有配置
        configs = await config_service.get_all_configs()

        # 按照前端期望的格式组织数据
        settings: Dict[str, Dict[str, Any]] = {
            "workHours": {
                "onlineTaskMinutes": 40,
                "offlineTaskMinutes": 100,
                "rushBonusMinutes": 15,
                "positiveReviewBonusMinutes": 30,
                "lateResponsePenaltyMinutes": 30,
                "lateCompletionPenaltyMinutes": 30,
                "negativeReviewPenaltyMinutes": 60,
            },
            "thresholds": {
                "responseTimeHours": 2,
                "completionTimeHours": 24,
                "monthlyTargetHours": 40,
            },
            "penalties": {
                "enableAutoPenalty": True,
                "enableLateResponsePenalty": True,
                "enableLateCompletionPenalty": True,
                "enableNegativeReviewPenalty": True,
            },
            "notifications": {
                "enableEmailNotifications": True,
                "enableSmsNotifications": False,
                "enablePushNotifications": True,
            },
        }

        # 从数据库中获取实际配置值覆盖默认值
        for config in configs:
            config_key = config.config_key
            config_value = config.get_typed_value()

            if config_key.startswith("work_hours."):
                key = config_key.replace("work_hours.", "").replace("_", "")
                if key in [
                    "onlinetaskminutes",
                    "offlinetaskminutes",
                    "rushbonusminutes",
                    "positivereviewbonusminutes",
                    "lateresponsepenaltyminutes",
                    "latecompletionpenaltyminutes",
                    "negativereviewpenaltyminutes",
                ]:
                    camel_key = _snake_to_camel(key)
                    settings["workHours"][camel_key] = config_value
            elif config_key.startswith("thresholds."):
                key = config_key.replace("thresholds.", "").replace("_", "")
                camel_key = _snake_to_camel(key)
                settings["thresholds"][camel_key] = config_value
            elif config_key.startswith("penalties."):
                key = config_key.replace("penalties.", "").replace("_", "")
                camel_key = _snake_to_camel(key)
                settings["penalties"][camel_key] = config_value
            elif config_key.startswith("notifications."):
                key = config_key.replace("notifications.", "").replace("_", "")
                camel_key = _snake_to_camel(key)
                settings["notifications"][camel_key] = config_value

        return create_response(data=settings, message="成功获取系统设置")

    except Exception as e:
        logger.error(f"Get system settings error: {str(e)}")
        return create_error_response(
            message="获取系统设置失败", details={"error": str(e)}
        )


@router.put("/settings", response_model=Dict[str, Any])
async def update_system_settings(
    request_data: Dict[str, Any],
    current_user: Member = Depends(get_current_active_admin),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """更新系统设置"""
    try:
        config_service = SystemConfigService(db)

        # 从请求数据中提取配置更新
        config_updates = {}

        if "workHours" in request_data:
            work_hours = request_data["workHours"]
            for key, value in work_hours.items():
                snake_key = _camel_to_snake(key)
                config_updates[f"work_hours.{snake_key}"] = value

        if "thresholds" in request_data:
            thresholds = request_data["thresholds"]
            for key, value in thresholds.items():
                snake_key = _camel_to_snake(key)
                config_updates[f"thresholds.{snake_key}"] = value

        if "penalties" in request_data:
            penalties = request_data["penalties"]
            for key, value in penalties.items():
                snake_key = _camel_to_snake(key)
                config_updates[f"penalties.{snake_key}"] = value

        if "notifications" in request_data:
            notifications = request_data["notifications"]
            for key, value in notifications.items():
                snake_key = _camel_to_snake(key)
                config_updates[f"notifications.{snake_key}"] = value

        if not config_updates:
            raise HTTPException(
                status_code=http_status.HTTP_400_BAD_REQUEST,
                detail="没有提供有效的配置更新数据",
            )

        # 批量更新配置
        result = await config_service.bulk_update_configs(config_updates)

        logger.info(
            f"System settings updated by user {current_user.id}: {config_updates}"
        )

        return create_response(
            data={
                "updatedCount": result.get("success_count", 0),
                "failedCount": result.get("failed_count", 0),
                "updatedKeys": list(config_updates.keys()),
            },
            message=f"系统设置更新完成，成功更新 {result.get('success_count', 0)} 项",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update system settings error: {str(e)}")
        return create_error_response(
            message="更新系统设置失败", details={"error": str(e)}
        )


@router.get("/settings/history", response_model=Dict[str, Any])
async def get_system_settings_history(
    limit: int = 50,
    current_user: Member = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """获取系统设置历史记录"""
    try:
        # 这里应该有一个设置历史记录的服务，目前返回模拟数据
        from datetime import datetime, timedelta

        history_records = []
        for i in range(min(limit, 10)):
            history_records.append(
                {
                    "id": i + 1,
                    "action": "update_settings",
                    "description": f"更新工时配置第{i+1}次",
                    "changedBy": current_user.id,
                    "changedByName": current_user.name,
                    "changedAt": (datetime.utcnow() - timedelta(days=i)).isoformat(),
                    "changes": {
                        "work_hours.online_task_minutes": {"from": 35, "to": 40},
                        "thresholds.response_time_hours": {"from": 1, "to": 2},
                    },
                }
            )

        return create_response(
            data={"records": history_records, "total": len(history_records)},
            message="成功获取系统设置历史记录",
        )

    except Exception as e:
        logger.error(f"Get system settings history error: {str(e)}")
        return create_error_response(
            message="获取系统设置历史记录失败", details={"error": str(e)}
        )


def _snake_to_camel(snake_str: str) -> str:
    """将蛇形命名转换为驼峰命名"""
    components = snake_str.split("_")
    return components[0] + "".join(word.capitalize() for word in components[1:])


def _camel_to_snake(camel_str: str) -> str:
    """将驼峰命名转换为蛇形命名"""
    import re

    s1 = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", camel_str)
    return re.sub("([a-z0-9])([A-Z])", r"\1_\2", s1).lower()
