"""
系统配置管理API端点
提供系统参数的配置、查询和管理功能
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


@router.get("/", response_model=Dict[str, Any])
async def get_all_system_configs(
    category: str = None,
    current_user: Member = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """获取系统配置列表"""
    try:
        config_service = SystemConfigService(db)
        
        if category:
            configs = await config_service.get_configs_by_category(category)
        else:
            configs = await config_service.get_all_configs()
            
        # 按分类和分组整理配置
        organized_configs = {}
        for config in configs:
            cat = config.category
            group = config.config_group or "其他"
            
            if cat not in organized_configs:
                organized_configs[cat] = {}
            if group not in organized_configs[cat]:
                organized_configs[cat][group] = []
                
            organized_configs[cat][group].append(config.to_dict())
        
        return create_response(
            data={
                "configs": organized_configs,
                "total_count": len(configs),
                "categories": list(organized_configs.keys())
            },
            message=f"成功获取系统配置，共 {len(configs)} 项"
        )
        
    except Exception as e:
        logger.error(f"Get system configs error: {str(e)}")
        return create_error_response(
            message="获取系统配置失败", 
            details={"error": str(e)}
        )


@router.get("/categories", response_model=Dict[str, Any])
async def get_config_categories(
    current_user: Member = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """获取配置分类列表"""
    try:
        config_service = SystemConfigService(db)
        configs = await config_service.get_all_configs()
        
        categories = {}
        for config in configs:
            cat = config.category
            if cat not in categories:
                categories[cat] = {
                    "category": cat,
                    "count": 0,
                    "groups": set()
                }
            categories[cat]["count"] += 1
            if config.config_group:
                categories[cat]["groups"].add(config.config_group)
        
        # 转换set为list
        for cat in categories.values():
            cat["groups"] = list(cat["groups"])
        
        return create_response(
            data={"categories": list(categories.values())},
            message="成功获取配置分类"
        )
        
    except Exception as e:
        logger.error(f"Get config categories error: {str(e)}")
        return create_error_response(
            message="获取配置分类失败", 
            details={"error": str(e)}
        )


@router.get("/work-hours", response_model=Dict[str, Any])
async def get_work_hours_config(
    current_user: Member = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """获取工时计算配置"""
    try:
        config_service = SystemConfigService(db)
        work_hours_config = await config_service.get_work_hours_config()
        
        return create_response(
            data=work_hours_config,
            message="成功获取工时计算配置"
        )
        
    except Exception as e:
        logger.error(f"Get work hours config error: {str(e)}")
        return create_error_response(
            message="获取工时配置失败", 
            details={"error": str(e)}
        )


@router.get("/penalties", response_model=Dict[str, Any])
async def get_penalties_config(
    current_user: Member = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """获取扣时规则配置"""
    try:
        config_service = SystemConfigService(db)
        penalties_config = await config_service.get_penalties_config()
        
        return create_response(
            data=penalties_config,
            message="成功获取扣时规则配置"
        )
        
    except Exception as e:
        logger.error(f"Get penalties config error: {str(e)}")
        return create_error_response(
            message="获取扣时配置失败", 
            details={"error": str(e)}
        )


@router.get("/thresholds", response_model=Dict[str, Any])
async def get_thresholds_config(
    current_user: Member = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """获取时间阈值配置"""
    try:
        config_service = SystemConfigService(db)
        thresholds_config = await config_service.get_thresholds_config()
        
        return create_response(
            data=thresholds_config,
            message="成功获取时间阈值配置"
        )
        
    except Exception as e:
        logger.error(f"Get thresholds config error: {str(e)}")
        return create_error_response(
            message="获取时间阈值配置失败", 
            details={"error": str(e)}
        )


@router.put("/", response_model=Dict[str, Any])
async def update_system_config(
    request_data: Dict[str, Any],
    current_user: Member = Depends(get_current_active_admin),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """更新系统配置（单个）"""
    try:
        config_key = request_data.get("config_key")
        config_value = request_data.get("config_value")
        
        if not config_key:
            raise HTTPException(
                status_code=http_status.HTTP_400_BAD_REQUEST,
                detail="缺少配置键名"
            )
            
        config_service = SystemConfigService(db)
        success = await config_service.set_config_value(config_key, config_value)
        
        if success:
            logger.info(f"System config updated by user {current_user.id}: {config_key} = {config_value}")
            return create_response(
                data={"config_key": config_key, "config_value": config_value},
                message="系统配置更新成功"
            )
        else:
            return create_error_response(
                message="配置更新失败，请检查配置键名和值的有效性"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update system config error: {str(e)}")
        return create_error_response(
            message="更新系统配置失败", 
            details={"error": str(e)}
        )


@router.put("/bulk", response_model=Dict[str, Any])
async def bulk_update_system_configs(
    request_data: Dict[str, Any],
    current_user: Member = Depends(get_current_active_admin),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """批量更新系统配置"""
    try:
        config_updates = request_data.get("configs", {})
        
        if not config_updates:
            raise HTTPException(
                status_code=http_status.HTTP_400_BAD_REQUEST,
                detail="没有提供配置更新数据"
            )
            
        config_service = SystemConfigService(db)
        result = await config_service.bulk_update_configs(config_updates)
        
        if result["success"]:
            logger.info(f"System configs bulk updated by user {current_user.id}: {result}")
            return create_response(
                data=result,
                message=f"批量更新完成，成功 {result['success_count']} 项"
            )
        else:
            return create_error_response(
                message=f"批量更新部分失败，成功 {result['success_count']} 项，失败 {result['failed_count']} 项",
                details={"failed_keys": result["failed_keys"]}
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Bulk update system configs error: {str(e)}")
        return create_error_response(
            message="批量更新系统配置失败", 
            details={"error": str(e)}
        )


@router.post("/reset/{config_key}", response_model=Dict[str, Any])
async def reset_config_to_default(
    config_key: str,
    current_user: Member = Depends(get_current_active_admin),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """重置配置为默认值"""
    try:
        config_service = SystemConfigService(db)
        success = await config_service.reset_config_to_default(config_key)
        
        if success:
            logger.info(f"System config reset to default by user {current_user.id}: {config_key}")
            return create_response(
                data={"config_key": config_key},
                message="配置重置为默认值成功"
            )
        else:
            return create_error_response(
                message="配置重置失败，请检查配置键名是否存在"
            )
        
    except Exception as e:
        logger.error(f"Reset config to default error: {str(e)}")
        return create_error_response(
            message="重置配置失败", 
            details={"error": str(e)}
        )


@router.post("/initialize", response_model=Dict[str, Any])
async def initialize_system_configs(
    current_user: Member = Depends(get_current_active_admin),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """初始化系统默认配置"""
    try:
        config_service = SystemConfigService(db)
        result = await config_service.initialize_default_configs()
        
        logger.info(f"System configs initialized by user {current_user.id}: {result}")
        
        return create_response(
            data=result,
            message=f"系统配置初始化完成，创建 {result['created_count']} 项，更新 {result['updated_count']} 项"
        )
        
    except Exception as e:
        logger.error(f"Initialize system configs error: {str(e)}")
        return create_error_response(
            message="初始化系统配置失败", 
            details={"error": str(e)}
        )


@router.get("/export", response_model=Dict[str, Any])
async def export_system_configs(
    current_user: Member = Depends(get_current_active_admin),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """导出系统配置"""
    try:
        config_service = SystemConfigService(db)
        configs = await config_service.get_all_configs()
        
        export_data = []
        for config in configs:
            export_data.append({
                "config_key": config.config_key,
                "config_name": config.config_name,
                "category": config.category,
                "config_group": config.config_group,
                "current_value": config.get_typed_value(),
                "default_value": config.get_typed_default_value(),
                "value_type": config.value_type,
                "description": config.config_description,
            })
        
        logger.info(f"System configs exported by user {current_user.id}")
        
        return create_response(
            data={
                "configs": export_data,
                "export_count": len(export_data),
                "export_time": "今天导出时间占位符"  # 实际实现时可以添加具体时间
            },
            message=f"系统配置导出成功，共 {len(export_data)} 项"
        )
        
    except Exception as e:
        logger.error(f"Export system configs error: {str(e)}")
        return create_error_response(
            message="导出系统配置失败", 
            details={"error": str(e)}
        )