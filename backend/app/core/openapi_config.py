"""
OpenAPI文档配置增强
完善的API元数据和机器可读配置
"""

from typing import Any, Dict

# API标签配置 - 用于组织API端点
OPENAPI_TAGS = [
    {
        "name": "Authentication",
        "description": "用户认证相关API - JWT登录、刷新令牌、用户信息管理等",
        "externalDocs": {"description": "JWT认证说明", "url": "https://jwt.io/"},
    },
    {
        "name": "Members",
        "description": "成员管理API - 用户增删改查、批量导入、角色管理等",
    },
    {
        "name": "Tasks",
        "description": "任务管理API - 维修任务、监控任务、协助任务的完整生命周期管理",
    },
    {
        "name": "Dashboard",
        "description": "仪表板API - 统计概览、数据可视化、实时监控和快捷操作",
    },
    {
        "name": "Statistics",
        "description": "统计报表API - 工时统计、效率分析、月度报表等数据分析功能",
    },
    {
        "name": "Attendance",
        "description": "考勤管理API - 基于任务完成时间的工时记录和考勤统计",
    },
    {
        "name": "Import",
        "description": "数据导入API - 支持Excel/CSV批量导入成员和任务数据",
    },
    {
        "name": "Health",
        "description": "系统健康检查API - 服务状态监控和健康检查端点",
    },
    {
        "name": "Root",
        "description": "根路径API - 基础信息和系统状态",
    },
]


# OpenAPI配置
def get_openapi_config() -> Dict:
    """获取完整的OpenAPI配置"""
    return {
        "title": "考勤管理系统API",
        "version": "1.0.0",
        "description": """
## 🎯 考勤管理系统API文档

基于FastAPI构建的现代化考勤管理系统，专为大学网络维护团队设计，提供完整的任务管理和工时统计功能。

### ✨ 核心功能
- 🔐 **JWT认证系统** - 基于角色的访问控制
- 👥 **成员管理** - 用户信息、权限管理、批量导入
- 📋 **任务管理** - 维修/监控/协助任务全生命周期
- ⏱️ **工时统计** - 智能工时计算、爆单奖励、延迟惩罚  
- 📊 **数据分析** - 效率统计、月度报表、趋势分析
- 📅 **考勤记录** - 基于任务完成的考勤统计

### 🏗️ 系统架构
- **后端**: FastAPI + SQLAlchemy + PostgreSQL
- **认证**: JWT Bearer Token
- **数据库**: PostgreSQL
- **缓存**: Redis (可选)
- **API规范**: OpenAPI 3.1 + 统一响应格式

### 🔗 相关链接
- [项目主页](https://github.com/KangJianLin/Kaoqin_Demo)
- [API状态监控](/health)  
- [系统根路径](/)

### 🛠️ 前端集成工具
使用以下工具实现前后端自动化同步：
```bash
# 生成TypeScript类型定义
npx openapi-typescript http://localhost:8000/openapi.json --output src/types/api.ts

# 生成API客户端代码  
npx @openapitools/openapi-generator-cli generate \\
  -i http://localhost:8000/openapi.json \\
  -g typescript-axios \\
  -o src/api/generated
```

### 📋 API使用规范
- 所有API返回统一格式: `{code: number, success: boolean, message: string, data: any, request_id: string, timestamp: string}`
- 后端字段命名采用snake_case（与数据库字段保持一致）
- 认证头格式: `Authorization: Bearer <token>`
- 分页参数: `page` (页码), `pageSize` (每页大小)
- 时间格式: ISO 8601 (YYYY-MM-DDTHH:mm:ssZ)
        """,
        "terms_of_service": "https://github.com/KangJianLin/Kaoqin_Demo/blob/main/LICENSE",
        "contact": {
            "name": "API技术支持",
            "url": "https://github.com/KangJianLin/Kaoqin_Demo/issues",
            "email": "kangjianlin@example.com",
        },
        "license": {
            "name": "MIT License",
            "url": "https://opensource.org/licenses/MIT",
        },
        "servers": [
            {"url": "http://localhost:8000", "description": "本地开发环境"},
            {"url": "http://127.0.0.1:8000", "description": "本地开发环境 (127.0.0.1)"},
            {
                "url": "https://api.attendance.example.com",
                "description": "生产环境 (请替换为实际域名)",
            },
        ],
        "openapi_tags": OPENAPI_TAGS,
    }


# 自定义OpenAPI Schema增强
def get_custom_openapi_schema() -> Dict[str, Any]:
    """返回自定义的OpenAPI schema增强配置"""
    return {
        "components": {
            "securitySchemes": {
                "BearerAuth": {
                    "type": "http",
                    "scheme": "bearer",
                    "bearerFormat": "JWT",
                    "description": "JWT访问令牌，格式：Bearer <token>。通过/api/v1/auth/login获取。",
                }
            },
            "responses": {
                "UnauthorizedError": {
                    "description": "认证失败或令牌无效",
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "success": {"type": "boolean", "example": False},
                                    "message": {
                                        "type": "string",
                                        "example": "Token验证失败",
                                    },
                                    "errorCode": {
                                        "type": "string",
                                        "example": "INVALID_TOKEN",
                                    },
                                },
                            }
                        }
                    },
                },
                "ForbiddenError": {
                    "description": "权限不足",
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "success": {"type": "boolean", "example": False},
                                    "message": {
                                        "type": "string",
                                        "example": "权限不足",
                                    },
                                    "errorCode": {
                                        "type": "string",
                                        "example": "INSUFFICIENT_PERMISSIONS",
                                    },
                                },
                            }
                        }
                    },
                },
                "ValidationError": {
                    "description": "请求数据验证失败",
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "success": {"type": "boolean", "example": False},
                                    "message": {
                                        "type": "string",
                                        "example": "数据验证失败",
                                    },
                                    "errorCode": {
                                        "type": "string",
                                        "example": "VALIDATION_ERROR",
                                    },
                                    "details": {
                                        "type": "object",
                                        "example": {
                                            "fieldErrors": {
                                                "title": "任务标题不能为空",
                                                "taskType": "任务类型必须是有效值",
                                            }
                                        },
                                    },
                                },
                            }
                        }
                    },
                },
            },
        }
    }


# 需要认证的API路径配置
PROTECTED_PATHS = [
    "/api/v1/auth/me",
    "/api/v1/auth/logout",
    "/api/v1/auth/change-password",
    "/api/v1/auth/verify-token",
    "/api/v1/members",
    "/api/v1/tasks",
    "/api/v1/statistics",
    "/api/v1/attendance",
    "/api/v1/import",
]

# 公开API路径（不需要认证）
PUBLIC_PATHS = [
    "/",
    "/health",
    "/api/health",
    "/api/v1/auth/login",
    "/api/v1/auth/refresh",
    "/docs",
    "/redoc",
    "/openapi.json",
]


def is_protected_path(path: str) -> bool:
    """判断路径是否需要认证"""
    for protected in PROTECTED_PATHS:
        if path.startswith(protected):
            return True
    return False


def is_public_path(path: str) -> bool:
    """判断路径是否为公开路径"""
    for public in PUBLIC_PATHS:
        if path.startswith(public):
            return True
    return False
