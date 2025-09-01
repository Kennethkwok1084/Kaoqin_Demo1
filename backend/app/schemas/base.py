"""
基础Schema定义
提供统一的API响应格式，直接输出前端需要的camelCase字段名
"""

from typing import Any, Dict, Generic, Optional, TypeVar
from pydantic import BaseModel, ConfigDict, Field


def to_camel(string: str) -> str:
    """Convert snake_case to camelCase"""
    components = string.split('_')
    return components[0] + ''.join(word.capitalize() for word in components[1:])


# 统一API响应格式 - 直接输出前端需要的字段名
class StandardResponse(BaseModel):
    """标准API响应格式 - 后端直接返回前端需要的camelCase格式"""
    
    success: bool = Field(..., description="操作成功状态")
    message: str = Field(..., description="响应消息")
    data: Optional[Any] = Field(default=None, description="响应数据")
    
    model_config = ConfigDict(
        # 自动将snake_case转换为camelCase
        alias_generator=to_camel,
        populate_by_name=True,
        json_schema_extra={
            "example": {
                "success": True,
                "message": "操作成功",
                "data": {}
            }
        }
    )


DataT = TypeVar('DataT')


class TypedResponse(StandardResponse, Generic[DataT]):
    """类型化的标准响应"""
    data: DataT


# 基础Model，所有响应模型继承此类
class BaseResponse(BaseModel):
    """所有响应使用camelCase字段名的基类"""
    
    model_config = ConfigDict(
        # 自动转换字段名为camelCase
        alias_generator=to_camel,
        populate_by_name=True,
        # 允许额外字段
        extra='allow'
    )


class ErrorResponse(BaseModel):
    """错误响应格式"""
    
    success: bool = Field(default=False, description="操作失败状态") 
    message: str = Field(..., description="错误消息")
    error_code: Optional[str] = Field(default=None, description="错误代码", alias="errorCode")
    details: Optional[Dict[str, Any]] = Field(default=None, description="错误详情")
    
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True
    )