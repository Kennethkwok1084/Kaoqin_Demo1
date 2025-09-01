#!/bin/bash

# API类型自动生成脚本
# 用法: ./scripts/generate-api-types.sh [backend_url]

set -e

# 默认后端API地址
BACKEND_URL=${1:-"http://localhost:8000"}
OPENAPI_URL="${BACKEND_URL}/openapi.json"

echo "🚀 开始生成API类型和客户端..."
echo "📡 后端API地址: ${BACKEND_URL}"
echo "📄 OpenAPI JSON地址: ${OPENAPI_URL}"

# 检查后端是否可访问
echo "🔍 检查后端API可访问性..."
if ! curl -f -s "${OPENAPI_URL}" > /dev/null; then
    echo "❌ 错误: 无法访问后端API"
    echo "💡 请确保后端服务正在运行: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"
    echo "💡 或者指定正确的后端地址: $0 http://your-backend-url"
    exit 1
fi

echo "✅ 后端API可访问"

# 创建必要的目录
echo "📁 创建目录结构..."
mkdir -p src/types
mkdir -p src/api/generated

# 生成TypeScript类型定义
echo "🔧 生成TypeScript类型定义..."
if npm run generate-api-types; then
    echo "✅ TypeScript类型生成成功"
else
    echo "❌ TypeScript类型生成失败"
    exit 1
fi

# 生成API客户端代码
echo "🔧 生成API客户端代码..."
if npm run generate-api-client; then
    echo "✅ API客户端生成成功"
else
    echo "⚠️ API客户端生成失败，但不影响TypeScript类型使用"
fi

# 验证生成的文件
echo "🔍 验证生成的文件..."
if [ -f "src/types/api.ts" ]; then
    echo "✅ TypeScript类型文件已生成: src/types/api.ts"
    # 显示文件大小和基本信息
    ls -lh src/types/api.ts
else
    echo "❌ TypeScript类型文件生成失败"
    exit 1
fi

if [ -d "src/api/generated" ] && [ "$(ls -A src/api/generated)" ]; then
    echo "✅ API客户端代码已生成: src/api/generated/"
    ls -la src/api/generated/
else
    echo "⚠️ API客户端代码生成失败或为空"
fi

# 运行类型检查
echo "🔍 运行TypeScript类型检查..."
if npm run type-check; then
    echo "✅ 类型检查通过"
else
    echo "⚠️ 类型检查发现问题，请检查生成的类型定义"
fi

echo ""
echo "🎉 API类型生成完成!"
echo ""
echo "📚 使用说明:"
echo "1. 导入生成的类型: import type { paths } from '@/types/api'"
echo "2. 使用API客户端: import { api } from '@/api/client'"
echo "3. 所有API调用都具有完整的类型安全保障"
echo ""
echo "🔄 重新生成类型:"
echo "- 当后端API变更时，重新运行此脚本"
echo "- 或运行: npm run generate-api"
echo ""
echo "📖 更多信息请查看: docs/api/automation-readme.md"