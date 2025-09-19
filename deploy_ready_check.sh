#!/bin/bash
# 一键部署就绪检查 - 确保项目可以安全上线
# 执行时间目标：5-8分钟

echo "🚀 项目部署就绪检查"
echo "目标：快速验证所有关键功能，确保安全上线"
echo "========================================"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

# 测试结果计数
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0
WARNING_TESTS=0

# 日志函数
log_success() {
    echo -e "${GREEN}✅ $1${NC}"
    ((TOTAL_TESTS++))
    ((PASSED_TESTS++))
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
    ((TOTAL_TESTS++))
    ((FAILED_TESTS++))
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
    ((TOTAL_TESTS++))
    ((WARNING_TESTS++))
}

log_info() {
    echo -e "ℹ️  $1"
}

# 检查依赖
check_dependencies() {
    echo "📋 1. 检查系统依赖..."

    # 检查Python
    if command -v python3 &> /dev/null; then
        log_success "Python3 已安装"
    else
        log_error "Python3 未安装"
    fi

    # 检查Node.js
    if command -v node &> /dev/null; then
        log_success "Node.js 已安装"
    else
        log_error "Node.js 未安装"
    fi

    # 检查PostgreSQL或SQLite
    if command -v psql &> /dev/null || command -v sqlite3 &> /dev/null; then
        log_success "数据库工具可用"
    else
        log_warning "未检测到数据库工具"
    fi

    echo ""
}

# 检查后端服务
check_backend() {
    echo "🔧 2. 检查后端服务..."

    # 检查后端端口
    if lsof -Pi :8000 -sTCP:LISTEN -t >/dev/null; then
        log_success "后端服务运行在端口8000"

        # 运行后端快速测试
        if [ -f "backend/quick_smoke_test.py" ]; then
            log_info "运行后端核心功能测试..."
            cd backend
            python3 quick_smoke_test.py
            if [ $? -eq 0 ]; then
                log_success "后端核心功能测试通过"
            else
                log_error "后端核心功能测试失败"
            fi
            cd ..
        else
            log_warning "后端测试脚本不存在"
        fi

        # 运行工时计算准确性测试（新增）
        if [ -f "backend/work_hours_accuracy_test.py" ]; then
            log_info "运行工时计算准确性测试..."
            cd backend
            python3 work_hours_accuracy_test.py
            if [ $? -eq 0 ]; then
                log_success "工时计算准确性测试通过"
            else
                log_error "工时计算准确性测试失败 - 阻塞上线！"
            fi
            cd ..
        else
            log_warning "工时准确性测试脚本不存在"
        fi

        # 运行数据完整性检查（新增）
        if [ -f "backend/data_integrity_check.py" ]; then
            log_info "运行数据完整性检查..."
            cd backend
            python3 data_integrity_check.py
            if [ $? -eq 0 ]; then
                log_success "数据完整性检查通过"
            else
                log_error "数据完整性检查失败 - 阻塞上线！"
            fi
            cd ..
        else
            log_warning "数据完整性检查脚本不存在"
        fi
    else
        log_error "后端服务未运行在端口8000"
    fi

    echo ""
}

# 检查前端服务
check_frontend() {
    echo "🎨 3. 检查前端服务..."

    # 检查前端端口
    if lsof -Pi :3000 -sTCP:LISTEN -t >/dev/null; then
        log_success "前端服务运行在端口3000"

        # 检查是否可以访问
        if curl -s http://localhost:3000 > /dev/null; then
            log_success "前端服务响应正常"

            # 运行前端快速测试（如果有playwright）
            if command -v npx &> /dev/null && [ -f "frontend/quick_frontend_test.js" ]; then
                log_info "运行前端核心功能测试..."
                cd frontend
                # 安装playwright如果没有
                if ! npx playwright --version &> /dev/null; then
                    log_info "安装playwright..."
                    npx playwright install chromium --quiet
                fi

                node quick_frontend_test.js
                if [ $? -eq 0 ]; then
                    log_success "前端核心功能测试通过"
                else
                    log_error "前端核心功能测试失败"
                fi
                cd ..
            else
                log_warning "前端测试脚本不存在或playwright未安装"
            fi
        else
            log_error "前端服务无法访问"
        fi
    else
        log_error "前端服务未运行在端口3000"
    fi

    echo ""
}

# 检查数据库连接
check_database() {
    echo "💾 4. 检查数据库连接..."

    # 尝试从后端检查数据库
    cd backend
    python3 -c "
import sys
sys.path.append('.')
try:
    from app.core.database import engine
    from sqlalchemy import text

    with engine.connect() as conn:
        result = conn.execute(text('SELECT 1'))
        print('数据库连接成功')
        sys.exit(0)
except Exception as e:
    print(f'数据库连接失败: {e}')
    sys.exit(1)
" 2>/dev/null

    if [ $? -eq 0 ]; then
        log_success "数据库连接正常"
    else
        log_error "数据库连接失败"
    fi
    cd ..

    echo ""
}

# 检查核心配置
check_configuration() {
    echo "⚙️  5. 检查核心配置..."

    # 检查环境变量
    if [ -f "backend/.env" ]; then
        log_success "后端环境配置文件存在"
    else
        log_warning "后端环境配置文件不存在"
    fi

    if [ -f "frontend/.env" ]; then
        log_success "前端环境配置文件存在"
    else
        log_warning "前端环境配置文件不存在（可选）"
    fi

    # 检查重要文件
    important_files=(
        "backend/app/main.py"
        "backend/app/api/v1/auth.py"
        "backend/app/models/user.py"
        "frontend/src/main.ts"
        "frontend/src/router/index.ts"
        "frontend/src/api/auth.ts"
    )

    for file in "${important_files[@]}"; do
        if [ -f "$file" ]; then
            log_success "关键文件存在: $file"
        else
            log_error "关键文件缺失: $file"
        fi
    done

    echo ""
}

# 安全检查
security_check() {
    echo "🔒 6. 基础安全检查..."

    # 检查默认密码
    if grep -r "admin123\|password123\|123456" backend/ frontend/ 2>/dev/null | grep -v ".git" | grep -v "node_modules" | grep -v "test" | grep -q .; then
        log_warning "发现可能的默认密码，生产环境需要修改"
    else
        log_success "未发现明显的默认密码"
    fi

    # 检查debug模式
    if grep -r "DEBUG.*=.*True\|debug.*=.*true" backend/ frontend/ 2>/dev/null | grep -v ".git" | grep -v "node_modules" | grep -q .; then
        log_warning "发现debug模式开启，生产环境需要关闭"
    else
        log_success "未发现debug模式开启"
    fi

    echo ""
}

# 启动服务（如果未运行）
start_services() {
    echo "🚀 7. 启动必要服务..."

    # 启动后端（如果未运行）
    if ! lsof -Pi :8000 -sTCP:LISTEN -t >/dev/null; then
        log_info "启动后端服务..."
        cd backend
        # 后台启动后端
        nohup uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 > backend.log 2>&1 &
        sleep 5
        cd ..

        if lsof -Pi :8000 -sTCP:LISTEN -t >/dev/null; then
            log_success "后端服务启动成功"
        else
            log_error "后端服务启动失败"
        fi
    fi

    # 启动前端（如果未运行）
    if ! lsof -Pi :3000 -sTCP:LISTEN -t >/dev/null; then
        log_info "启动前端服务..."
        cd frontend
        # 后台启动前端
        nohup npm run dev > frontend.log 2>&1 &
        sleep 10
        cd ..

        if lsof -Pi :3000 -sTCP:LISTEN -t >/dev/null; then
            log_success "前端服务启动成功"
        else
            log_error "前端服务启动失败"
        fi
    fi

    echo ""
}

# 打印总结
print_summary() {
    echo "========================================"
    echo "📊 部署就绪检查结果"
    echo "========================================"
    echo "总检查项: $TOTAL_TESTS"
    echo -e "${GREEN}✅ 通过: $PASSED_TESTS${NC}"
    echo -e "${YELLOW}⚠️  警告: $WARNING_TESTS${NC}"
    echo -e "${RED}❌ 失败: $FAILED_TESTS${NC}"

    success_rate=$(( PASSED_TESTS * 100 / TOTAL_TESTS ))
    echo "成功率: ${success_rate}%"

    echo ""

    if [ $FAILED_TESTS -eq 0 ]; then
        echo -e "${GREEN}🎉 项目准备就绪，可以部署上线！${NC}"
        echo ""
        echo "快速启动命令："
        echo "  后端: cd backend && uvicorn app.main:app --host 0.0.0.0 --port 8000"
        echo "  前端: cd frontend && npm run build && npm run preview"
        echo ""
        return 0
    else
        echo -e "${RED}🚨 发现 $FAILED_TESTS 个关键问题，需要修复后才能上线！${NC}"
        echo ""
        echo "建议修复顺序："
        echo "1. 确保所有依赖已安装"
        echo "2. 检查数据库连接配置"
        echo "3. 验证服务启动配置"
        echo "4. 运行单独的功能测试"
        echo ""
        return 1
    fi
}

# 主执行流程
main() {
    start_time=$(date +%s)

    check_dependencies
    check_configuration
    check_database
    start_services
    check_backend
    check_frontend
    security_check

    end_time=$(date +%s)
    duration=$((end_time - start_time))

    echo "⏱️  总耗时: ${duration}秒"
    echo ""

    print_summary
    return $?
}

# 运行主程序
main
exit $?