#!/bin/bash

# 数据库备份脚本
# 支持全量备份、增量备份和定时备份

set -e

# 配置
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
BACKUP_DIR="$PROJECT_DIR/backups"
CONFIG_FILE="$PROJECT_DIR/.env.production"

# 默认参数
BACKUP_TYPE="full"
RETENTION_DAYS=30
COMPRESS=true
VERIFY=true

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 日志函数
log_info() {
    echo -e "${GREEN}[INFO]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

log_debug() {
    if [[ "$DEBUG" == "true" ]]; then
        echo -e "${BLUE}[DEBUG]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"
    fi
}

# 加载环境配置
load_config() {
    if [[ -f "$CONFIG_FILE" ]]; then
        log_info "加载配置文件: $CONFIG_FILE"
        set -a
        source "$CONFIG_FILE"
        set +a
    else
        log_warn "配置文件不存在，使用默认配置"
        # 默认配置
        DB_HOST=${DB_HOST:-localhost}
        DB_PORT=${DB_PORT:-5432}
        DB_USER=${DB_USER:-kwok}
        DB_PASSWORD=${DB_PASSWORD:-Onjuju1084}
        DB_NAME=${DB_NAME:-attendence_prod}
    fi
    
    log_debug "数据库配置: ${DB_HOST}:${DB_PORT}/${DB_NAME}"
}

# 检查依赖
check_dependencies() {
    log_info "检查备份依赖..."
    
    local missing_deps=()
    
    for cmd in pg_dump pg_restore psql gzip; do
        if ! command -v $cmd &> /dev/null; then
            missing_deps+=("$cmd")
        fi
    done
    
    if [[ ${#missing_deps[@]} -gt 0 ]]; then
        log_error "缺少必要的工具: ${missing_deps[*]}"
        log_info "请安装PostgreSQL客户端工具"
        exit 1
    fi
    
    log_info "依赖检查通过"
}

# 创建备份目录
create_backup_dir() {
    if [[ ! -d "$BACKUP_DIR" ]]; then
        mkdir -p "$BACKUP_DIR"
        log_info "创建备份目录: $BACKUP_DIR"
    fi
    
    # 创建子目录
    mkdir -p "$BACKUP_DIR/full"
    mkdir -p "$BACKUP_DIR/incremental" 
    mkdir -p "$BACKUP_DIR/logs"
    mkdir -p "$BACKUP_DIR/archive"
}

# 测试数据库连接
test_connection() {
    log_info "测试数据库连接..."
    
    export PGPASSWORD="$DB_PASSWORD"
    
    if psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c "SELECT 1;" &> /dev/null; then
        log_info "数据库连接成功"
        return 0
    else
        log_error "数据库连接失败"
        return 1
    fi
}

# 获取数据库大小
get_db_size() {
    export PGPASSWORD="$DB_PASSWORD"
    
    local size=$(psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" \
        -t -c "SELECT pg_size_pretty(pg_database_size('$DB_NAME'));" 2>/dev/null | xargs)
    
    echo "$size"
}

# 全量备份
full_backup() {
    log_info "开始全量备份..."
    
    local timestamp=$(date '+%Y%m%d_%H%M%S')
    local backup_file="$BACKUP_DIR/full/full_backup_${timestamp}.sql"
    local log_file="$BACKUP_DIR/logs/backup_${timestamp}.log"
    
    log_info "备份文件: $backup_file"
    log_info "日志文件: $log_file"
    
    # 获取数据库大小
    local db_size=$(get_db_size)
    log_info "数据库大小: $db_size"
    
    export PGPASSWORD="$DB_PASSWORD"
    
    # 执行备份
    {
        log_info "执行pg_dump命令..."
        pg_dump -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" \
            --verbose \
            --format=custom \
            --no-owner \
            --no-privileges \
            --compress=9 \
            --file="$backup_file" \
            "$DB_NAME"
    } 2>&1 | tee "$log_file"
    
    if [[ ${PIPESTATUS[0]} -eq 0 ]]; then
        log_info "全量备份完成"
        
        # 压缩备份文件
        if [[ "$COMPRESS" == "true" ]]; then
            compress_backup "$backup_file"
        fi
        
        # 验证备份
        if [[ "$VERIFY" == "true" ]]; then
            verify_backup "$backup_file"
        fi
        
        # 记录备份信息
        record_backup_info "$backup_file" "full" "$db_size"
        
        return 0
    else
        log_error "全量备份失败"
        return 1
    fi
}

# 增量备份 (WAL归档)
incremental_backup() {
    log_info "开始增量备份..."
    
    local timestamp=$(date '+%Y%m%d_%H%M%S')
    local backup_dir="$BACKUP_DIR/incremental/incr_${timestamp}"
    local log_file="$BACKUP_DIR/logs/incremental_${timestamp}.log"
    
    mkdir -p "$backup_dir"
    
    export PGPASSWORD="$DB_PASSWORD"
    
    # 执行基础备份
    {
        log_info "执行pg_basebackup命令..."
        pg_basebackup -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" \
            -D "$backup_dir" \
            -Ft -z -P \
            --wal-method=stream
    } 2>&1 | tee "$log_file"
    
    if [[ ${PIPESTATUS[0]} -eq 0 ]]; then
        log_info "增量备份完成"
        record_backup_info "$backup_dir" "incremental" "N/A"
        return 0
    else
        log_error "增量备份失败"
        return 1
    fi
}

# 压缩备份文件
compress_backup() {
    local backup_file="$1"
    
    if [[ -f "$backup_file" ]]; then
        log_info "压缩备份文件..."
        
        gzip "$backup_file"
        local compressed_file="${backup_file}.gz"
        
        if [[ -f "$compressed_file" ]]; then
            log_info "压缩完成: $compressed_file"
            local original_size=$(stat -c%s "$backup_file" 2>/dev/null || echo "0")
            local compressed_size=$(stat -c%s "$compressed_file" 2>/dev/null || echo "0")
            
            if [[ $original_size -gt 0 && $compressed_size -gt 0 ]]; then
                local ratio=$(( (original_size - compressed_size) * 100 / original_size ))
                log_info "压缩率: ${ratio}%"
            fi
        else
            log_error "压缩失败"
        fi
    fi
}

# 验证备份文件
verify_backup() {
    local backup_file="$1"
    
    log_info "验证备份文件完整性..."
    
    export PGPASSWORD="$DB_PASSWORD"
    
    # 检查备份文件格式
    if pg_restore --list "$backup_file" &> /dev/null; then
        log_info "备份文件格式验证通过"
        
        # 统计备份内容
        local table_count=$(pg_restore --list "$backup_file" | grep "TABLE DATA" | wc -l)
        local function_count=$(pg_restore --list "$backup_file" | grep "FUNCTION" | wc -l)
        
        log_info "备份内容: ${table_count}个表, ${function_count}个函数"
        
        return 0
    else
        log_error "备份文件验证失败"
        return 1
    fi
}

# 记录备份信息
record_backup_info() {
    local backup_path="$1"
    local backup_type="$2"
    local db_size="$3"
    
    local info_file="$BACKUP_DIR/backup_registry.json"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    local backup_size="0"
    
    if [[ -f "$backup_path" ]]; then
        backup_size=$(stat -c%s "$backup_path" 2>/dev/null || echo "0")
    elif [[ -d "$backup_path" ]]; then
        backup_size=$(du -sb "$backup_path" 2>/dev/null | cut -f1 || echo "0")
    fi
    
    # 创建备份记录
    local backup_record=$(cat <<EOF
{
    "timestamp": "$timestamp",
    "type": "$backup_type",
    "path": "$backup_path",
    "database_size": "$db_size",
    "backup_size": "$backup_size",
    "status": "completed"
}
EOF
)
    
    # 更新注册表
    if [[ -f "$info_file" ]]; then
        # 添加到现有文件
        local temp_file=$(mktemp)
        jq ". += [$backup_record]" "$info_file" > "$temp_file" && mv "$temp_file" "$info_file"
    else
        # 创建新文件
        echo "[$backup_record]" > "$info_file"
    fi
    
    log_info "备份信息已记录: $info_file"
}

# 清理过期备份
cleanup_old_backups() {
    log_info "清理 ${RETENTION_DAYS} 天前的备份文件..."
    
    local deleted_count=0
    
    # 清理全量备份
    if [[ -d "$BACKUP_DIR/full" ]]; then
        while IFS= read -r -d '' file; do
            rm -f "$file"
            ((deleted_count++))
            log_debug "删除过期备份: $(basename "$file")"
        done < <(find "$BACKUP_DIR/full" -name "*.sql*" -mtime +$RETENTION_DAYS -print0 2>/dev/null)
    fi
    
    # 清理增量备份
    if [[ -d "$BACKUP_DIR/incremental" ]]; then
        while IFS= read -r -d '' dir; do
            rm -rf "$dir"
            ((deleted_count++))
            log_debug "删除过期增量备份: $(basename "$dir")"
        done < <(find "$BACKUP_DIR/incremental" -maxdepth 1 -type d -mtime +$RETENTION_DAYS -print0 2>/dev/null)
    fi
    
    # 清理日志文件
    if [[ -d "$BACKUP_DIR/logs" ]]; then
        find "$BACKUP_DIR/logs" -name "*.log" -mtime +$RETENTION_DAYS -delete 2>/dev/null || true
    fi
    
    log_info "清理完成，删除了 $deleted_count 个过期备份"
}

# 列出备份文件
list_backups() {
    log_info "列出所有备份文件:"
    
    echo
    echo "全量备份:"
    if [[ -d "$BACKUP_DIR/full" ]] && [[ -n "$(ls -A "$BACKUP_DIR/full" 2>/dev/null)" ]]; then
        ls -lh "$BACKUP_DIR/full"/*.sql* 2>/dev/null | awk '{print $9, $5, $6, $7, $8}' || echo "无备份文件"
    else
        echo "无全量备份文件"
    fi
    
    echo
    echo "增量备份:"
    if [[ -d "$BACKUP_DIR/incremental" ]] && [[ -n "$(ls -A "$BACKUP_DIR/incremental" 2>/dev/null)" ]]; then
        ls -ld "$BACKUP_DIR/incremental"/*/ 2>/dev/null | awk '{print $9, $6, $7, $8}' || echo "无备份目录"
    else
        echo "无增量备份文件"
    fi
    
    echo
}

# 显示帮助信息
show_help() {
    cat << EOF
数据库备份脚本

用法: $0 [选项]

选项:
    -t, --type TYPE         备份类型: full|incremental (默认: full)
    -r, --retention DAYS    备份保留天数 (默认: 30)
    -c, --no-compress       不压缩备份文件
    -v, --no-verify         不验证备份文件
    -l, --list              列出所有备份文件
    -C, --cleanup           清理过期备份文件
    -h, --help              显示帮助信息
    
    --debug                 启用调试模式
    --config FILE           指定配置文件

示例:
    $0                                  # 执行全量备份
    $0 --type incremental               # 执行增量备份
    $0 --retention 7                    # 保留7天的备份
    $0 --list                          # 列出所有备份
    $0 --cleanup                       # 清理过期备份
    
环境变量:
    DB_HOST                 数据库主机 (默认: localhost)
    DB_PORT                 数据库端口 (默认: 5432)
    DB_USER                 数据库用户 (默认: kwok)
    DB_PASSWORD             数据库密码
    DB_NAME                 数据库名称 (默认: attendence_prod)

EOF
}

# 主函数
main() {
    # 解析命令行参数
    while [[ $# -gt 0 ]]; do
        case $1 in
            -t|--type)
                BACKUP_TYPE="$2"
                shift 2
                ;;
            -r|--retention)
                RETENTION_DAYS="$2"
                shift 2
                ;;
            -c|--no-compress)
                COMPRESS=false
                shift
                ;;
            -v|--no-verify)
                VERIFY=false
                shift
                ;;
            -l|--list)
                load_config
                create_backup_dir
                list_backups
                exit 0
                ;;
            -C|--cleanup)
                load_config
                create_backup_dir
                cleanup_old_backups
                exit 0
                ;;
            --debug)
                DEBUG=true
                shift
                ;;
            --config)
                CONFIG_FILE="$2"
                shift 2
                ;;
            -h|--help)
                show_help
                exit 0
                ;;
            *)
                log_error "未知参数: $1"
                show_help
                exit 1
                ;;
        esac
    done
    
    log_info "开始数据库备份任务..."
    log_info "备份类型: $BACKUP_TYPE"
    log_info "保留期限: $RETENTION_DAYS 天"
    
    # 执行备份流程
    load_config
    check_dependencies
    create_backup_dir
    
    if ! test_connection; then
        log_error "数据库连接失败，终止备份"
        exit 1
    fi
    
    # 执行备份
    case "$BACKUP_TYPE" in
        full)
            if full_backup; then
                log_info "全量备份成功完成"
            else
                log_error "全量备份失败"
                exit 1
            fi
            ;;
        incremental)
            if incremental_backup; then
                log_info "增量备份成功完成" 
            else
                log_error "增量备份失败"
                exit 1
            fi
            ;;
        *)
            log_error "不支持的备份类型: $BACKUP_TYPE"
            exit 1
            ;;
    esac
    
    # 清理过期备份
    cleanup_old_backups
    
    log_info "备份任务完成！"
}

# 错误处理
trap 'log_error "备份过程中发生错误，退出码: $?"' ERR

# 执行主函数
main "$@"