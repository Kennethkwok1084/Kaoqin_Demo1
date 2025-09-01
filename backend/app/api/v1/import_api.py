"""
数据导入API端点
处理Excel数据导入、字段映射、预览等功能
"""

import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi import status as http_status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import (
    create_error_response,
    create_response,
    get_current_user,
    get_db,
)
from app.models.member import Member
from app.services.import_service import DataImportService
from app.services.ab_table_matching_service import ABTableMatchingService

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/field-mapping", response_model=Dict[str, Any])
async def get_import_field_mapping(
    table_type: Optional[str] = Query(
        "task_table", description="表格类型: task_table, member_table, mixed_table"
    ),
    current_user: Member = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """
    获取导入字段映射表
    返回支持的字段映射配置，用于前端显示和数据导入时的字段匹配
    """
    try:
        # 初始化导入服务获取字段映射
        import_service = DataImportService(db)

        # 获取字段映射配置，如果无效则fallback到task_table
        field_mappings = import_service.column_mappings.get(
            table_type or "task_table", {}
        )

        if not field_mappings:
            # Fallback到task_table而不是抛出异常
            table_type = "task_table"
            field_mappings = import_service.column_mappings.get(table_type, {})

        # 构建详细的字段映射信息
        detailed_mapping = {}
        for field_key, possible_columns in field_mappings.items():
            detailed_mapping[field_key] = {
                "field_name": field_key,
                "display_name": _get_field_display_name(field_key),
                "possible_columns": possible_columns,
                "required": _is_field_required(field_key),
                "data_type": _get_field_data_type(field_key),
                "description": _get_field_description(field_key),
                "example_values": _get_field_example_values(field_key),
            }

        # 额外的导入配置信息
        import_config = {
            "supported_file_types": [".xlsx", ".xls", ".csv"],
            "max_file_size_mb": 10,
            "max_rows_per_import": 1000,
            "encoding_options": ["utf-8", "gbk", "gb2312", "utf-8-sig"],
            "table_types": {
                "task_table": {
                    "name": "维修任务表",
                    "description": "包含报修单数据的A表",
                },
                "member_table": {
                    "name": "人员信息表",
                    "description": "包含维护人员信息的B表",
                },
                "mixed_table": {
                    "name": "混合表",
                    "description": "包含任务和人员信息的综合表",
                },
            },
        }

        # 业务规则说明
        business_rules = {
            "matching_strategy": {
                "name": "A/B表匹配策略",
                "description": "使用【报修人姓名 + 联系方式】作为关键字段进行匹配",
                "key_fields": ["reporter_name", "reporter_contact"],
                "fuzzy_matching": True,
                "confidence_threshold": 0.8,
            },
            "work_hour_calculation": {
                "online_task_minutes": 40,
                "offline_task_minutes": 100,
                "rush_task_bonus_minutes": 15,
                "positive_review_bonus_minutes": 30,
                "late_response_penalty_minutes": 30,
                "late_completion_penalty_minutes": 30,
                "negative_review_penalty_minutes": 60,
            },
            "status_mapping": {
                "completed_keywords": ["已完成", "完成", "finished", "completed"],
                "in_progress_keywords": [
                    "进行中",
                    "处理中",
                    "in_progress",
                    "processing",
                ],
                "pending_keywords": ["待处理", "未处理", "pending", "new"],
                "cancelled_keywords": ["已取消", "取消", "cancelled", "canceled"],
            },
            "task_type_detection": {
                "offline_keywords": ["现场", "线下", "实地", "offline", "onsite"],
                "online_keywords": ["远程", "线上", "online", "remote"],
            },
        }

        # 构建期望的响应结构
        response_data = {
            "table_type": table_type,
            "field_mappings": detailed_mapping,
            "fields": {
                v["display_name"]: v["possible_columns"]
                for k, v in detailed_mapping.items()
            },
            "field_types": {
                v["display_name"]: v["data_type"] for k, v in detailed_mapping.items()
            },
            "required_fields": [
                detailed_mapping[k]["display_name"]
                for k, v in detailed_mapping.items()
                if v["required"]
            ],
            "optional_fields": [
                detailed_mapping[k]["display_name"]
                for k, v in detailed_mapping.items()
                if not v["required"]
            ],
            "mapping_rules": {
                "报修人匹配": {
                    "logic": "姓名+联系方式双重匹配",
                    "fallback": "模糊匹配算法",
                },
                "在线/线下判断": {
                    "logic": "基于处理方式字段判断",
                    "online_keywords": ["远程处理", "在线处理"],
                    "offline_keywords": ["现场处理", "现场维修", "上门服务"],
                },
            },
            "validation_rules": {
                "contact_format": "手机号码格式验证",
                "date_format": "支持多种日期格式自动识别",
                "required_check": "必填字段完整性检查",
            },
            "import_examples": {
                "valid_record": {
                    "报修人姓名": "张三",
                    "联系方式": "13800138000",
                    "故障描述": "网络连接异常",
                    "报修时间": "2024-01-20 10:30:00",
                    "维修类型": "网络维修",
                },
                "invalid_records": [
                    {
                        "data": {
                            "姓名": "",
                            "联系方式": "invalid",
                            "故障描述": "网络问题",
                        },
                        "error_reason": "报修人姓名不能为空",
                    },
                    {
                        "data": {"报修人姓名": "李四", "联系方式": "", "故障描述": ""},
                        "error_reason": "联系方式和故障描述不能为空",
                    },
                ],
            },
            "data_processing_rules": {
                "数据预处理": {
                    "去除空格": "自动去除字段前后空格",
                    "标准化格式": "统一日期时间格式",
                    "字段映射": "自动匹配列名到系统字段",
                },
                "数据校验": {
                    "必填字段检查": "验证必填字段是否为空",
                    "格式验证": "验证手机号、邮箱等格式",
                    "业务逻辑验证": "验证数据的业务合理性",
                },
                "duplicate_handling": "基于关键字段去重",
                "data_cleaning": "自动清理无效数据",
                "encoding_detection": "自动检测文件编码",
            },
            "import_config": import_config,
            "business_rules": business_rules,
            "total_fields": len(detailed_mapping),
        }

        return create_response(
            data=response_data,
            message=f"成功获取{table_type}字段映射配置",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get field mapping error: {str(e)}")
        return create_error_response(
            message="获取字段映射失败", details={"error": str(e)}
        )


def _get_field_display_name(field_key: str) -> str:
    """获取字段显示名称"""
    display_names = {
        "task_id": "任务编号",
        "title": "任务标题",
        "description": "故障描述",
        "reporter_name": "报修人姓名",
        "reporter_contact": "联系方式",
        "location": "故障地点",
        "report_time": "报修时间",
        "response_time": "接单时间",
        "completion_time": "完工时间",
        "repair_type": "维修类型",
        "repair_form": "检修形式",
        "priority": "优先级",
        "status": "工单状态",
        "department": "所属部门",
        "assigned_to": "处理人",
        "feedback": "用户反馈",
        "rating": "满意度评分",
        "name": "姓名",
        "contact": "联系方式",
        "email": "邮箱地址",
        "position": "职位",
        "employee_id": "工号",
        "class_name": "班级",
        "skill_level": "技能等级",
        "work_area": "工作区域",
        # attendance_table字段
        "member_name": "成员姓名",
        "check_in_time": "签到时间",
        "check_out_time": "签退时间",
        "work_hours": "工作时长",
        "task_type": "任务类型",
        "remarks": "备注",
    }
    return display_names.get(field_key, field_key.replace("_", " ").title())


def _is_field_required(field_key: str) -> bool:
    """判断字段是否必需"""
    required_fields = ["title", "description", "reporter_name", "reporter_contact"]
    return field_key in required_fields


def _get_field_data_type(field_key: str) -> str:
    """获取字段数据类型"""
    data_types = {
        "task_id": "string",
        "title": "string",
        "description": "text",
        "reporter_name": "string",
        "reporter_contact": "string",
        "location": "string",
        "report_time": "datetime",
        "response_time": "datetime",
        "completion_time": "datetime",
        "repair_type": "string",
        "repair_form": "string",
        "priority": "enum",
        "status": "enum",
        "department": "string",
        "assigned_to": "string",
        "feedback": "text",
        "rating": "integer",
        "name": "string",
        "contact": "string",
        "email": "email",
        "position": "string",
        "employee_id": "string",
        "class_name": "string",
        "skill_level": "string",
        "work_area": "string",
        # attendance_table字段
        "member_name": "string",
        "check_in_time": "datetime",
        "check_out_time": "datetime",
        "work_hours": "decimal",
        "task_type": "string",
        "remarks": "text",
    }
    return data_types.get(field_key, "string")


def _get_field_description(field_key: str) -> str:
    """获取字段描述"""
    descriptions = {
        "task_id": "唯一的任务标识符或工单编号",
        "title": "任务标题或问题简述，必填字段",
        "description": "详细的问题描述或故障内容",
        "reporter_name": "报修人的真实姓名，用于A/B表匹配的关键字段",
        "reporter_contact": "报修人的联系方式（手机号），用于A/B表匹配的关键字段",
        "location": "故障发生的具体地点或位置",
        "report_time": "任务报修的时间，支持多种日期格式",
        "response_time": "接单或开始处理的时间",
        "completion_time": "任务完成的时间，也作为截止时间",
        "repair_type": "维修类型或故障分类",
        "repair_form": "检修形式，用于判断线上/线下任务类型",
        "priority": "任务优先级：低、中、高、紧急",
        "status": "工单当前状态，用于映射任务状态",
        "department": "报修人所属部门",
        "assigned_to": "任务处理人或负责人",
        "feedback": "用户对处理结果的反馈内容",
        "rating": "用户满意度评分，1-5星",
        "name": "人员真实姓名",
        "contact": "联系方式",
        "email": "邮箱地址",
        "position": "职位或岗位",
        "employee_id": "员工编号或学号",
        "class_name": "班级或小组",
        "skill_level": "技能水平等级",
        "work_area": "负责的工作区域",
    }
    return descriptions.get(field_key, f"{field_key}字段")


def _get_field_example_values(field_key: str) -> List[str]:
    """获取字段示例值"""
    examples = {
        "task_id": ["R20240120001", "WO2024-001", "T240120-001"],
        "title": ["网络故障", "无法上网", "WiFi连接问题"],
        "description": ["办公室电脑无法连接网络", "WiFi信号不稳定", "网速缓慢"],
        "reporter_name": ["张三", "李四", "王五"],
        "reporter_contact": ["13800138000", "18900189001", "15600156002"],
        "location": ["办公楼A座201", "教学楼B栋301", "宿舍区1号楼"],
        "report_time": ["2024-01-20 10:30:00", "2024/1/20 10:30", "20240120 1030"],
        "response_time": ["2024-01-20 11:00:00", "2024/1/20 11:00"],
        "completion_time": ["2024-01-20 14:30:00", "2024/1/20 14:30"],
        "repair_type": ["网络维修", "硬件故障", "软件问题"],
        "repair_form": ["远程处理", "现场维修", "线上指导"],
        "priority": ["高", "中", "低", "紧急"],
        "status": ["已完成", "处理中", "待处理", "已取消"],
        "department": ["信息化建设处", "网络中心", "技术部"],
        "assigned_to": ["张三", "李技术员", "网络管理员"],
        "feedback": ["问题已解决", "服务态度好", "处理及时"],
        "rating": ["5", "4", "3", "2", "1"],
        "name": ["张三", "李四", "王五"],
        "contact": ["13800138000", "18900189001"],
        "email": ["zhangsan@example.com", "lisi@company.com"],
        "position": ["技术员", "工程师", "管理员"],
        "employee_id": ["2024001", "EMP001", "20210001"],
        "class_name": ["计算机1班", "网络技术组", "维修小组"],
        "skill_level": ["初级", "中级", "高级"],
        "work_area": ["A区", "B栋", "全校区"],
    }
    return examples.get(field_key, [f"{field_key}示例值"])


@router.get("/template/{template_type}", response_model=Dict[str, Any])
async def get_import_template(
    template_type: str = "repair_task",
    current_user: Member = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """
    获取导入模板
    返回指定类型的导入模板配置
    """
    try:
        import_service = DataImportService(db)
        template = await import_service.get_import_template(template_type)

        if not template:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail=f"未找到模板类型: {template_type}",
            )

        return create_response(
            data=template, message=f"成功获取{template_type}导入模板"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get import template error: {str(e)}")
        return create_error_response(
            message="获取导入模板失败", details={"error": str(e)}
        )


def get_supported_field_mappings() -> Dict[str, Any]:
    """
    获取支持的字段映射 (同步版本，用于测试)

    Returns:
        Dict: 支持的字段映射信息
    """
    return {
        "success": True,
        "data": {
            "task_table": {
                "task_id": ["工单编号", "任务编号", "报修编号"],
                "title": ["标题", "问题描述", "报修内容"],
                "reporter_name": ["报修人", "申请人", "联系人"],
                "reporter_contact": ["联系电话", "手机号", "电话"],
                "location": ["地址", "位置", "故障地点"],
                "report_time": ["报修时间", "申请时间", "创建时间"],
            },
            "member_table": {
                "name": ["姓名", "维修人员", "处理人"],
                "contact": ["联系电话", "手机号", "电话"],
                "employee_id": ["工号", "员工编号", "学号"],
                "skill_level": ["技能等级", "级别", "水平"],
            },
        },
        "message": "成功获取字段映射配置",
    }


def get_field_mapping(table_type: str = "task_table") -> Dict[str, Any]:
    """
    获取字段映射 (同步版本，用于测试兼容性)

    Args:
        table_type: 表格类型，默认为 "task_table"

    Returns:
        Dict: 字段映射配置
    """
    from app.services.import_service import DataImportService

    # 创建临时数据库连接用于初始化服务
    try:
        # 简化版本，直接返回映射配置
        service = DataImportService(None)

        # 获取字段映射配置
        field_mappings = service.column_mappings.get(table_type, {})

        if not field_mappings:
            # Fallback到task_table
            table_type = "task_table"
            field_mappings = service.column_mappings.get(table_type, {})

        return {
            "success": True,
            "table_type": table_type,
            "field_mappings": field_mappings,
            "supported_tables": list(service.column_mappings.keys()),
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "field_mappings": {},
            "supported_tables": [],
        }


# ============= A/B表匹配优化 =============

@router.get("/matching/performance", response_model=Dict[str, Any])
async def get_matching_performance_stats(
    current_user: Member = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """获取A/B表匹配性能统计"""
    try:
        matching_service = ABTableMatchingService(db)
        
        stats = {
            "cache_hits": matching_service._cache_hits,
            "cache_misses": matching_service._cache_misses,
            "total_operations": matching_service._cache_hits + matching_service._cache_misses,
            "hit_rate": matching_service._cache_hits / max(
                matching_service._cache_hits + matching_service._cache_misses, 1
            ),
            "cached_similarities": len(matching_service._similarity_cache),
            "cached_names": len(matching_service._name_cache),
            "cached_phones": len(matching_service._phone_cache),
        }
        
        return create_response(
            data=stats,
            message="A/B表匹配性能统计获取成功"
        )

    except Exception as e:
        logger.error(f"Get matching performance stats error: {str(e)}")
        return create_error_response(
            message="获取性能统计失败", 
            details={"error": str(e)}
        )


@router.post("/matching/clear-cache", response_model=Dict[str, Any])
async def clear_matching_cache(
    current_user: Member = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """清理A/B表匹配缓存"""
    try:
        matching_service = ABTableMatchingService(db)
        
        # 清理缓存并获取统计信息
        cache_stats = matching_service.clear_cache()
        
        logger.info(f"Matching cache cleared by user {current_user.id}: {cache_stats}")
        
        return create_response(
            data=cache_stats,
            message="A/B表匹配缓存清理成功"
        )

    except Exception as e:
        logger.error(f"Clear matching cache error: {str(e)}")
        return create_error_response(
            message="清理缓存失败", 
            details={"error": str(e)}
        )


@router.post("/matching/test-optimization", response_model=Dict[str, Any])
async def test_matching_optimization(
    request_data: Dict[str, Any],
    current_user: Member = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """测试A/B表匹配优化效果"""
    try:
        import time
        
        matching_service = ABTableMatchingService(db)
        
        # 获取测试数据
        test_data = request_data.get("test_data", [])
        if not test_data:
            raise HTTPException(
                status_code=http_status.HTTP_400_BAD_REQUEST,
                detail="需要提供测试数据"
            )
        
        # 清理缓存以确保公平测试
        matching_service.clear_cache()
        
        # 执行匹配测试
        start_time = time.time()
        
        match_results = await matching_service.match_ab_tables(
            a_table_data=test_data,
            timeout_seconds=60  # 1分钟超时
        )
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        # 统计结果
        matched_count = sum(1 for result in match_results if result.is_matched)
        high_confidence_count = sum(
            1 for result in match_results 
            if result.is_matched and result.confidence >= 0.90
        )
        
        # 缓存性能
        cache_stats = {
            "cache_hits": matching_service._cache_hits,
            "cache_misses": matching_service._cache_misses,
            "hit_rate": matching_service._cache_hits / max(
                matching_service._cache_hits + matching_service._cache_misses, 1
            ),
        }
        
        results = {
            "test_summary": {
                "total_records": len(test_data),
                "matched_records": matched_count,
                "high_confidence_matches": high_confidence_count,
                "match_rate": matched_count / len(test_data) if test_data else 0,
                "high_confidence_rate": high_confidence_count / len(test_data) if test_data else 0,
                "execution_time_seconds": execution_time,
                "records_per_second": len(test_data) / execution_time if execution_time > 0 else 0,
            },
            "cache_performance": cache_stats,
            "optimization_benefits": {
                "estimated_speedup": f"{cache_stats['hit_rate'] * 100:.1f}%",
                "memory_efficiency": f"使用了 {len(matching_service._similarity_cache)} 个相似度缓存",
            }
        }
        
        logger.info(f"Matching optimization test completed by user {current_user.id}: {results['test_summary']}")
        
        return create_response(
            data=results,
            message="A/B表匹配优化测试完成"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Test matching optimization error: {str(e)}")
        return create_error_response(
            message="匹配优化测试失败", 
            details={"error": str(e)}
        )
