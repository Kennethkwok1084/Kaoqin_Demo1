#!/bin/bash

# 考勤管理系统部署脚本
# 使用方法: ./deploy.sh [environment] [version]

set -e

# 默认参数
ENVIRONMENT=${1:-staging}
VERSION=${2:-latest}
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

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

# 检查必要的工具
check_dependencies() {
    log_info "检查依赖工具..."
    
    for cmd in docker docker-compose git; do
        if ! command -v $cmd &> /dev/null; then
            log_error "$cmd 未安装或不在PATH中"
            exit 1
        fi
    done
    
    log_info "依赖检查通过"
}

# 检查环境配置
check_environment() {
    log_info "检查环境配置..."
    
    ENV_FILE="$PROJECT_DIR/.env.$ENVIRONMENT"
    if [[ ! -f "$ENV_FILE" ]]; then
        log_error "环境配置文件不存在: $ENV_FILE"
        log_info "请复制并配置环境文件:"
        log_info "cp .env.$ENVIRONMENT.example $ENV_FILE"
        exit 1
    fi
    
    # 加载环境变量
    set -a
    source "$ENV_FILE"
    set +a
    
    log_info "环境配置加载完成: $ENVIRONMENT"
}

# 备份数据库
backup_database() {
    if [[ "$ENVIRONMENT" == "production" ]]; then
        log_info "创建数据库备份..."
        
        BACKUP_DIR="$PROJECT_DIR/backups"
        mkdir -p "$BACKUP_DIR"
        
        BACKUP_FILE="$BACKUP_DIR/backup_$(date +%Y%m%d_%H%M%S).sql"
        
        docker-compose -f docker-compose.prod.yml exec postgres \
            pg_dump -U "$DB_USER" "$DB_NAME" > "$BACKUP_FILE"
        
        log_info "数据库备份完成: $BACKUP_FILE"
    fi
}

# 构建镜像
build_images() {
    log_info "构建Docker镜像..."
    
    cd "$PROJECT_DIR"
    
    # 构建后端镜像
    docker build -t "$REGISTRY_URL/$IMAGE_PREFIX/backend:$VERSION" \
        --build-arg VERSION="$VERSION" \
        --build-arg BUILD_DATE="$(date -u +'%Y-%m-%dT%H:%M:%SZ')" \
        ./backend
    
    # 构建前端镜像
    docker build -t "$REGISTRY_URL/$IMAGE_PREFIX/frontend:$VERSION" \
        --build-arg VERSION="$VERSION" \
        --build-arg BUILD_DATE="$(date -u +'%Y-%m-%dT%H:%M:%SZ')" \
        ./frontend
    
    log_info "镜像构建完成"
}

# 推送镜像到仓库
push_images() {
    if [[ "$ENVIRONMENT" == "production" ]]; then
        log_info "推送镜像到容器仓库..."
        
        docker push "$REGISTRY_URL/$IMAGE_PREFIX/backend:$VERSION"
        docker push "$REGISTRY_URL/$IMAGE_PREFIX/frontend:$VERSION"
        
        log_info "镜像推送完成"
    fi
}

# 部署服务
deploy_services() {
    log_info "部署服务..."
    
    cd "$PROJECT_DIR"
    
    if [[ "$ENVIRONMENT" == "production" ]]; then
        COMPOSE_FILE="docker-compose.prod.yml"
    else
        COMPOSE_FILE="docker-compose.yml"
    fi
    
    # 停止旧服务
    docker-compose -f "$COMPOSE_FILE" down
    
    # 启动新服务
    docker-compose -f "$COMPOSE_FILE" up -d
    
    log_info "服务部署完成"
}

# 健康检查
health_check() {
    log_info "执行健康检查..."
    
    local max_attempts=30
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        log_info "健康检查 ($attempt/$max_attempts)..."
        
        if curl -f -s http://localhost:8000/health > /dev/null; then
            log_info "后端服务健康检查通过"
            break
        fi
        
        if [ $attempt -eq $max_attempts ]; then
            log_error "健康检查失败，服务可能未正常启动"
            exit 1
        fi
        
        sleep 10
        ((attempt++))
    done
    
    log_info "所有服务健康检查通过"
}

# 部署完成通知
deploy_notification() {
    log_info "==================================="
    log_info "部署完成!"
    log_info "环境: $ENVIRONMENT"
    log_info "版本: $VERSION"
    log_info "时间: $(date)"
    log_info "==================================="
    
    if [[ "$ENVIRONMENT" == "production" ]]; then
        log_info "生产环境访问地址:"
        log_info "- 前端: https://attendance.yourdomain.com"
        log_info "- API: https://api.attendance.yourdomain.com"
        log_info "- 监控: https://monitoring.yourdomain.com"
    else
        log_info "开发环境访问地址:"
        log_info "- 前端: http://localhost"
        log_info "- API: http://localhost:8000"
        log_info "- 监控: http://localhost:3000"
    fi
}

# 主函数
main() {
    log_info "开始部署考勤管理系统..."
    log_info "环境: $ENVIRONMENT"
    log_info "版本: $VERSION"
    
    check_dependencies
    check_environment
    backup_database
    build_images
    push_images
    deploy_services
    health_check
    deploy_notification
    
    log_info "部署成功完成!"
}

# 错误处理
trap 'log_error "部署过程中发生错误，退出码: $?"' ERR

# 执行主函数
main