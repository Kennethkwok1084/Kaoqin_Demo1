"""
系统参数配置模型
管理所有可配置的工时和扣时规则参数
"""

from typing import Any, Dict, Optional

from sqlalchemy import Boolean, Float, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class SystemConfig(BaseModel):
    """
    系统参数配置模型

    用于存储和管理系统中所有可配置的参数，
    包括工时计算规则、扣时规则、时间阈值等
    """

    __tablename__ = "system_configs"

    # 配置标识
    config_key: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
        index=True,
        comment="配置键名（唯一标识）",
    )

    config_name: Mapped[str] = mapped_column(
        String(200), nullable=False, comment="配置显示名称"
    )

    config_description: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="配置描述"
    )

    # 配置分类
    category: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="general",
        comment="配置分类（work_hours, penalties, thresholds, general等）",
    )

    # 配置值
    config_value: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="配置值（字符串格式）"
    )

    default_value: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="默认配置值"
    )

    # 数据类型和验证
    value_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="string",
        comment="值类型（string, integer, float, boolean, json）",
    )

    min_value: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True, comment="最小值（数值类型有效）"
    )

    max_value: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True, comment="最大值（数值类型有效）"
    )

    validation_rule: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="验证规则（正则表达式或其他规则）"
    )

    # 状态和权限
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False, comment="是否启用"
    )

    is_system_config: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False, comment="是否为系统内置配置（不可删除）"
    )

    required_role: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="admin",
        comment="修改此配置所需的最低角色权限",
    )

    # 元数据
    display_order: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, comment="显示顺序"
    )

    config_group: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True, comment="配置分组（用于前端分组显示）"
    )

    # 扩展字段
    extra_data: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON, nullable=True, comment="扩展数据（JSON格式）"
    )

    def __repr__(self) -> str:
        """字符串表示"""
        return (
            f"<SystemConfig(key='{self.config_key}', "
            f"name='{self.config_name}', value='{self.config_value}')>"
        )

    def get_typed_value(self) -> Any:
        """获取按类型转换后的配置值"""
        if not self.config_value:
            return self.get_typed_default_value()

        try:
            if self.value_type == "integer":
                return int(self.config_value)
            elif self.value_type == "float":
                return float(self.config_value)
            elif self.value_type == "boolean":
                return self.config_value.lower() in ("true", "1", "yes", "on")
            elif self.value_type == "json":
                import json

                return json.loads(self.config_value)
            else:  # string
                return self.config_value
        except (ValueError, TypeError, json.JSONDecodeError):
            return self.get_typed_default_value()

    def get_typed_default_value(self) -> Any:
        """获取按类型转换后的默认值"""
        if not self.default_value:
            if self.value_type == "integer":
                return 0
            elif self.value_type == "float":
                return 0.0
            elif self.value_type == "boolean":
                return False
            elif self.value_type == "json":
                return {}
            else:
                return ""

        try:
            if self.value_type == "integer":
                return int(self.default_value)
            elif self.value_type == "float":
                return float(self.default_value)
            elif self.value_type == "boolean":
                return self.default_value.lower() in ("true", "1", "yes", "on")
            elif self.value_type == "json":
                import json

                return json.loads(self.default_value)
            else:  # string
                return self.default_value
        except (ValueError, TypeError, json.JSONDecodeError):
            return self.default_value

    def set_typed_value(self, value: Any) -> None:
        """设置配置值并自动转换类型"""
        if value is None:
            self.config_value = None
            return

        if self.value_type == "json":
            import json

            self.config_value = json.dumps(value, ensure_ascii=False)
        else:
            self.config_value = str(value)

    def validate_value(self, value: Any) -> bool:
        """验证配置值是否有效"""
        try:
            # 类型验证
            if self.value_type == "integer":
                int_value = int(value)
                if self.min_value is not None and int_value < self.min_value:
                    return False
                if self.max_value is not None and int_value > self.max_value:
                    return False
            elif self.value_type == "float":
                float_value = float(value)
                if self.min_value is not None and float_value < self.min_value:
                    return False
                if self.max_value is not None and float_value > self.max_value:
                    return False
            elif self.value_type == "boolean":
                # 布尔类型验证
                if not isinstance(value, bool) and str(value).lower() not in (
                    "true",
                    "false",
                    "1",
                    "0",
                    "yes",
                    "no",
                    "on",
                    "off",
                ):
                    return False
            elif self.value_type == "json":
                import json

                if isinstance(value, str):
                    json.loads(value)
                else:
                    json.dumps(value)

            # 正则验证
            if self.validation_rule and self.value_type == "string":
                import re

                if not re.match(self.validation_rule, str(value)):
                    return False

            return True
        except (ValueError, TypeError, json.JSONDecodeError):
            return False

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "id": self.id,
            "config_key": self.config_key,
            "config_name": self.config_name,
            "config_description": self.config_description,
            "category": self.category,
            "config_value": self.config_value,
            "typed_value": self.get_typed_value(),
            "default_value": self.default_value,
            "typed_default_value": self.get_typed_default_value(),
            "value_type": self.value_type,
            "min_value": self.min_value,
            "max_value": self.max_value,
            "validation_rule": self.validation_rule,
            "is_active": self.is_active,
            "is_system_config": self.is_system_config,
            "required_role": self.required_role,
            "display_order": self.display_order,
            "config_group": self.config_group,
            "extra_data": self.extra_data,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
