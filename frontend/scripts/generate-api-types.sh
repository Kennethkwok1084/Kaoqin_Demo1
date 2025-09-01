#!/bin/bash

# 自动化API类型生成脚本
# 用于从OpenAPI规范生成TypeScript类型和API客户端

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 项目路径
BACKEND_URL="http://localhost:8000"
OPENAPI_URL="${BACKEND_URL}/openapi.json"
TYPES_OUTPUT="src/types/api.ts"
CLIENT_OUTPUT="src/api/generated"
FETCH_OUTPUT="src/api/generated-fetch"

echo -e "${BLUE}🚀 考勤管理系统API类型自动生成工具${NC}"
echo "=================================================="

# 函数：检查后端服务器是否运行
check_backend() {
    echo -e "${YELLOW}⏳ 检查后端服务器状态...${NC}"
    
    if curl -f -s "${BACKEND_URL}/health" > /dev/null 2>&1; then
        echo -e "${GREEN}✅ 后端服务器运行正常${NC}"
        return 0
    else
        echo -e "${RED}❌ 后端服务器未运行${NC}"
        echo -e "${YELLOW}💡 请先启动后端服务器：${NC}"
        echo "   cd ../backend"
        echo "   uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"
        return 1
    fi
}

# 函数：检查OpenAPI规范是否可用  
check_openapi() {
    echo -e "${YELLOW}⏳ 检查OpenAPI规范...${NC}"
    
    if curl -f -s "${OPENAPI_URL}" > /dev/null 2>&1; then
        echo -e "${GREEN}✅ OpenAPI规范可用${NC}"
        
        # 显示API信息
        API_INFO=$(curl -s "${OPENAPI_URL}" | jq -r '.info | "标题: \(.title), 版本: \(.version)"' 2>/dev/null || echo "API信息解析失败")
        echo -e "${BLUE}📋 ${API_INFO}${NC}"
        return 0
    else
        echo -e "${RED}❌ 无法获取OpenAPI规范${NC}"
        return 1
    fi
}

# 函数：创建必要目录
create_directories() {
    echo -e "${YELLOW}⏳ 创建必要目录...${NC}"
    
    mkdir -p src/types src/api/generated src/api/generated-fetch
    echo -e "${GREEN}✅ 目录创建完成${NC}"
}

# 函数：生成TypeScript类型定义
generate_types() {
    echo -e "${YELLOW}⏳ 生成TypeScript类型定义...${NC}"
    
    if command -v openapi-typescript &> /dev/null; then
        openapi-typescript "${OPENAPI_URL}" --output "${TYPES_OUTPUT}"
        echo -e "${GREEN}✅ TypeScript类型生成成功: ${TYPES_OUTPUT}${NC}"
    else
        echo -e "${RED}❌ openapi-typescript 未安装${NC}"
        echo -e "${YELLOW}💡 安装命令: npm install -D openapi-typescript${NC}"
        return 1
    fi
}

# 函数：生成API客户端（Axios版本）
generate_axios_client() {
    echo -e "${YELLOW}⏳ 生成Axios API客户端...${NC}"
    
    if command -v openapi-generator-cli &> /dev/null; then
        openapi-generator-cli generate \
            -i "${OPENAPI_URL}" \
            -g typescript-axios \
            -o "${CLIENT_OUTPUT}" \
            --additional-properties=supportsES6=true,npmName=attendance-api-client,npmVersion=1.0.0,withSeparateModelsAndApi=true
        
        echo -e "${GREEN}✅ Axios客户端生成成功: ${CLIENT_OUTPUT}${NC}"
    else
        echo -e "${RED}❌ openapi-generator-cli 未安装${NC}" 
        echo -e "${YELLOW}💡 安装命令: npm install -D @openapitools/openapi-generator-cli${NC}"
        return 1
    fi
}

# 函数：生成Fetch API客户端
generate_fetch_client() {
    echo -e "${YELLOW}⏳ 生成Fetch API客户端...${NC}"
    
    if npm list openapi-fetch &> /dev/null; then
        # 创建简单的fetch客户端模板
        cat > "${FETCH_OUTPUT}/index.ts" << 'EOF'
import createClient from 'openapi-fetch';
import type { paths } from '../types/api';

// 创建类型安全的API客户端
const apiClient = createClient<paths>({
  baseUrl: process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000'
});

// 导出配置好的客户端
export { apiClient };
export type { paths };

// 便捷的API方法
export const api = {
  // 认证相关
  auth: {
    login: (credentials: { studentId: string; password: string }) =>
      apiClient.POST('/api/v1/auth/login', { body: credentials }),
    
    refresh: (refreshToken: string) =>
      apiClient.POST('/api/v1/auth/refresh', { body: { refresh_token: refreshToken } }),
    
    logout: () =>
      apiClient.POST('/api/v1/auth/logout'),
    
    getProfile: () =>
      apiClient.GET('/api/v1/auth/me'),
  },
  
  // 成员管理
  members: {
    list: (params?: { page?: number; pageSize?: number; search?: string }) =>
      apiClient.GET('/api/v1/members/', { params: { query: params } }),
    
    get: (memberId: number) =>
      apiClient.GET('/api/v1/members/{member_id}', { params: { path: { member_id: memberId } } }),
    
    create: (memberData: any) =>
      apiClient.POST('/api/v1/members/', { body: memberData }),
    
    update: (memberId: number, memberData: any) =>
      apiClient.PUT('/api/v1/members/{member_id}', { 
        params: { path: { member_id: memberId } },
        body: memberData 
      }),
  },
  
  // 任务管理
  tasks: {
    list: (params?: { page?: number; pageSize?: number; search?: string }) =>
      apiClient.GET('/api/v1/tasks/', { params: { query: params } }),
    
    create: (taskData: any) =>
      apiClient.POST('/api/v1/tasks/repair', { body: taskData }),
    
    get: (taskId: number) =>
      apiClient.GET('/api/v1/tasks/repair/{task_id}', { params: { path: { task_id: taskId } } }),
    
    update: (taskId: number, taskData: any) =>
      apiClient.PUT('/api/v1/tasks/repair/{task_id}', {
        params: { path: { task_id: taskId } },
        body: taskData
      }),
  },
  
  // 统计信息
  statistics: {
    overview: (params?: { dateFrom?: string; dateTo?: string }) =>
      apiClient.GET('/api/v1/statistics/overview', { params: { query: params } }),
    
    workHours: (year: number, month: number, memberId?: number) =>
      apiClient.GET('/api/v1/statistics/work-hours/overview', {
        params: { query: { year, month, member_id: memberId } }
      }),
  },
  
  // 考勤记录
  attendance: {
    records: (params?: { dateFrom?: string; dateTo?: string; memberId?: number }) =>
      apiClient.GET('/api/v1/attendance/records', { params: { query: params } }),
    
    summary: (month: string, memberId?: number) =>
      apiClient.GET('/api/v1/attendance/summary/{month}', {
        params: { 
          path: { month },
          query: { member_id: memberId }
        }
      }),
  }
};
EOF

        echo -e "${GREEN}✅ Fetch客户端生成成功: ${FETCH_OUTPUT}${NC}"
    else
        echo -e "${YELLOW}⚠️  openapi-fetch 未安装，跳过Fetch客户端生成${NC}"
        echo -e "${YELLOW}💡 安装命令: npm install openapi-fetch${NC}"
    fi
}

# 函数：生成使用示例
generate_examples() {
    echo -e "${YELLOW}⏳ 生成使用示例...${NC}"
    
    cat > "src/api/examples.ts" << 'EOF'
/**
 * API使用示例
 * 展示如何使用自动生成的类型安全API客户端
 */

import { api } from './generated-fetch';
import type { paths } from '../types/api';

// 示例：用户登录
async function loginExample() {
  try {
    const { data, error } = await api.auth.login({
      studentId: '20240001',
      password: 'password123'
    });
    
    if (error) {
      console.error('登录失败:', error);
      return;
    }
    
    console.log('登录成功:', data);
    
    // TypeScript会提供完整的类型检查和智能提示
    if (data.success) {
      const token = data.data.accessToken;
      const user = data.data.user;
      console.log(`欢迎 ${user.name}!`);
    }
  } catch (error) {
    console.error('网络错误:', error);
  }
}

// 示例：获取任务列表  
async function getTasksExample() {
  try {
    const { data, error } = await api.tasks.list({
      page: 1,
      pageSize: 20,
      search: '网络维修'
    });
    
    if (error) {
      console.error('获取任务失败:', error);
      return;
    }
    
    console.log('任务列表:', data);
  } catch (error) {
    console.error('网络错误:', error);
  }
}

// 示例：创建新任务
async function createTaskExample() {
  try {
    const { data, error } = await api.tasks.create({
      title: '机房网络设备维修',
      description: '机房交换机端口故障，需要更换',
      taskType: 'repair',
      priority: 'high',
      location: '教学楼A座机房'
    });
    
    if (error) {
      console.error('创建任务失败:', error);
      return;
    }
    
    console.log('任务创建成功:', data);
  } catch (error) {
    console.error('网络错误:', error);
  }
}

// 示例：获取工时统计
async function getWorkHoursExample() {
  try {
    const { data, error } = await api.statistics.workHours(2024, 1);
    
    if (error) {
      console.error('获取工时统计失败:', error);
      return;
    }
    
    console.log('工时统计:', data);
  } catch (error) {
    console.error('网络错误:', error);
  }
}

// 导出示例函数
export {
  loginExample,
  getTasksExample, 
  createTaskExample,
  getWorkHoursExample
};
EOF

    echo -e "${GREEN}✅ 使用示例生成成功: src/api/examples.ts${NC}"
}

# 函数：显示总结信息
show_summary() {
    echo "=================================================="
    echo -e "${GREEN}🎉 API类型生成完成！${NC}"
    echo ""
    echo -e "${BLUE}📁 生成的文件:${NC}"
    echo "  ├── ${TYPES_OUTPUT} (TypeScript类型定义)"
    echo "  ├── ${CLIENT_OUTPUT}/ (Axios API客户端)" 
    echo "  ├── ${FETCH_OUTPUT}/ (Fetch API客户端)"
    echo "  └── src/api/examples.ts (使用示例)"
    echo ""
    echo -e "${BLUE}🚀 使用方法:${NC}"
    echo "  1. 导入类型: import type { paths } from './types/api'"
    echo "  2. 使用客户端: import { api } from './api/generated-fetch'"
    echo "  3. 查看示例: 参考 src/api/examples.ts"
    echo ""
    echo -e "${YELLOW}💡 提示:${NC}"
    echo "  • 当后端API变更时，重新运行此脚本即可更新类型"
    echo "  • 所有API调用都是类型安全的，支持智能提示"
    echo "  • 可以将此脚本添加到CI/CD流程中实现自动化"
}

# 主函数
main() {
    # 检查后端服务器
    if ! check_backend; then
        exit 1
    fi
    
    # 检查OpenAPI规范
    if ! check_openapi; then
        exit 1
    fi
    
    # 创建目录
    create_directories
    
    # 生成类型定义
    if ! generate_types; then
        echo -e "${YELLOW}⚠️  TypeScript类型生成失败，但继续执行其他步骤${NC}"
    fi
    
    # 生成Axios客户端
    if ! generate_axios_client; then
        echo -e "${YELLOW}⚠️  Axios客户端生成失败，但继续执行其他步骤${NC}"
    fi
    
    # 生成Fetch客户端
    generate_fetch_client
    
    # 生成使用示例
    generate_examples
    
    # 显示总结
    show_summary
}

# 执行主函数
main "$@"
