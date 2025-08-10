#!/bin/bash

# 快速冒烟测试脚本
# 适用于快速验证系统基本功能

set -e

# 配置
API_BASE_URL="http://localhost:8000"
FRONTEND_URL="http://localhost"
MAX_RETRIES=30
RETRY_INTERVAL=2

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 日志函数
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_test() {
    echo -e "${BLUE}[TEST]${NC} $1"
}

# 等待服务就绪
wait_for_service() {
    local url=$1
    local service_name=$2
    local retries=0
    
    log_info "等待 $service_name 服务就绪..."
    
    while [ $retries -lt $MAX_RETRIES ]; do
        if curl -f -s "$url" > /dev/null 2>&1; then
            log_info "$service_name 服务已就绪"
            return 0
        fi
        
        retries=$((retries + 1))
        echo -n "."
        sleep $RETRY_INTERVAL
    done
    
    log_error "$service_name 服务启动超时"
    return 1
}

# 测试API健康检查
test_health_check() {
    log_test "测试API健康检查..."
    
    response=$(curl -s -w "%{http_code}" -o /dev/null "$API_BASE_URL/health")
    
    if [ "$response" = "200" ]; then
        log_info "✅ 健康检查通过"
        return 0
    else
        log_error "❌ 健康检查失败，HTTP状态码: $response"
        return 1
    fi
}

# 测试API文档访问
test_api_docs() {
    log_test "测试API文档访问..."
    
    response=$(curl -s -w "%{http_code}" -o /dev/null "$API_BASE_URL/docs")
    
    if [ "$response" = "200" ]; then
        log_info "✅ API文档访问正常"
        return 0
    else
        log_error "❌ API文档访问失败，HTTP状态码: $response"
        return 1
    fi
}

# 测试认证接口
test_auth_endpoints() {
    log_test "测试认证接口..."
    
    # 测试登录接口存在性（不测试实际登录，避免需要真实用户）
    response=$(curl -s -w "%{http_code}" -o /dev/null -X POST \
        -H "Content-Type: application/json" \
        -d '{"username":"test","password":"test"}' \
        "$API_BASE_URL/api/v1/auth/login")
    
    # 400或422表示接口存在但参数错误，这是正常的
    if [ "$response" = "400" ] || [ "$response" = "422" ] || [ "$response" = "401" ]; then
        log_info "✅ 登录接口响应正常"
        return 0
    else
        log_warn "⚠️  登录接口响应异常，HTTP状态码: $response"
        return 1
    fi
}

# 测试核心API接口
test_core_apis() {
    log_test "测试核心API接口（无认证）..."
    
    local success_count=0
    local total_count=0
    
    # 测试不需要认证的接口
    local endpoints=(
        "/api/v1/import/field-mapping"
        "/docs"
        "/redoc"
        "/openapi.json"
    )
    
    for endpoint in "${endpoints[@]}"; do
        total_count=$((total_count + 1))
        response=$(curl -s -w "%{http_code}" -o /dev/null "$API_BASE_URL$endpoint")
        
        if [ "$response" = "200" ]; then
            log_info "✅ $endpoint - 成功 ($response)"
            success_count=$((success_count + 1))
        else
            log_warn "⚠️  $endpoint - 失败 ($response)"
        fi
    done
    
    log_info "核心API测试完成: $success_count/$total_count"
    
    # 至少一半接口要成功
    if [ $success_count -ge $((total_count / 2)) ]; then
        return 0
    else
        return 1
    fi
}

# 测试前端页面
test_frontend() {
    log_test "测试前端页面..."
    
    response=$(curl -s -w "%{http_code}" -o /tmp/frontend_response.html "$FRONTEND_URL")
    
    if [ "$response" = "200" ]; then
        # 检查页面内容
        if grep -q -i "考勤\|attendance\|login\|登录" /tmp/frontend_response.html; then
            log_info "✅ 前端页面访问正常"
            rm -f /tmp/frontend_response.html
            return 0
        else
            log_warn "⚠️  前端页面内容可能异常"
            rm -f /tmp/frontend_response.html
            return 1
        fi
    else
        log_error "❌ 前端页面访问失败，HTTP状态码: $response"
        return 1
    fi
}

# 测试数据库连接（通过API）
test_database_connection() {
    log_test "测试数据库连接（通过API）..."
    
    # 尝试访问需要数据库的接口
    response=$(curl -s -w "%{http_code}" -o /dev/null "$API_BASE_URL/api/v1/auth/login" \
        -X POST -H "Content-Type: application/json" \
        -d '{"username":"nonexistent","password":"test"}')
    
    # 400、422或401表示接口正常响应（数据库连接正常）
    # 500表示服务器内部错误（可能是数据库连接问题）
    if [ "$response" != "500" ]; then
        log_info "✅ 数据库连接正常（通过API验证）"
        return 0
    else
        log_error "❌ 数据库连接可能有问题"
        return 1
    fi
}

# 主测试流程
run_smoke_tests() {
    log_info "开始执行快速冒烟测试..."
    
    local passed_tests=0
    local total_tests=0
    
    # 等待服务就绪
    if ! wait_for_service "$API_BASE_URL/health" "后端API"; then
        log_error "后端服务未就绪，终止测试"
        exit 1
    fi
    
    # 执行各项测试
    local tests=(
        "test_health_check"
        "test_api_docs" 
        "test_auth_endpoints"
        "test_core_apis"
        "test_database_connection"
        "test_frontend"
    )
    
    for test_func in "${tests[@]}"; do
        total_tests=$((total_tests + 1))
        if $test_func; then
            passed_tests=$((passed_tests + 1))
        fi
    done
    
    # 输出测试结果
    echo
    echo "=========================================="
    echo "快速冒烟测试结果"
    echo "=========================================="
    echo "通过测试: $passed_tests/$total_tests"
    
    if [ $passed_tests -eq $total_tests ]; then
        log_info "🎉 所有测试通过！"
        exit 0
    elif [ $passed_tests -ge $((total_tests * 2 / 3)) ]; then
        log_warn "⚠️  大部分测试通过，但有部分问题需要关注"
        exit 0
    else
        log_error "❌ 多项测试失败，请检查系统状态"
        exit 1
    fi
}

# 显示帮助信息
show_help() {
    echo "快速冒烟测试脚本"
    echo
    echo "使用方法:"
    echo "  $0 [选项]"
    echo
    echo "选项:"
    echo "  -h, --help              显示此帮助信息"
    echo "  --api-url URL           指定API基础URL (默认: $API_BASE_URL)"
    echo "  --frontend-url URL      指定前端URL (默认: $FRONTEND_URL)"
    echo "  --max-retries N         最大重试次数 (默认: $MAX_RETRIES)"
    echo
    echo "示例:"
    echo "  $0                                    # 使用默认设置"
    echo "  $0 --api-url http://localhost:8080   # 指定API URL"
}

# 处理命令行参数
while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_help
            exit 0
            ;;
        --api-url)
            API_BASE_URL="$2"
            shift 2
            ;;
        --frontend-url)
            FRONTEND_URL="$2"
            shift 2
            ;;
        --max-retries)
            MAX_RETRIES="$2"
            shift 2
            ;;
        *)
            log_error "未知参数: $1"
            show_help
            exit 1
            ;;
    esac
done

# 执行测试
run_smoke_tests