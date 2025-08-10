#!/bin/bash

# 数据库恢复脚本
# 支持从全量备份和增量备份进行数据恢复

set -e

# 配置
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
BACKUP_DIR="$PROJECT_DIR/backups"
CONFIG_FILE="$PROJECT_DIR/.env.production"

# 默认参数
FORCE_RESTORE=false
CREATE_DB=false
RESTORE_POINT=""
VERBOSE=false

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
    if [[ "$VERBOSE" == "true" ]]; then
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
    log_info "检查恢复依赖..."
    
    local missing_deps=()
    
    for cmd in pg_restore psql createdb dropdb; do
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

# 测试数据库连接
test_connection() {
    local db_name="${1:-postgres}"  # 默认连接postgres数据库
    
    log_debug "测试数据库连接: $db_name"
    
    export PGPASSWORD="$DB_PASSWORD"
    
    if psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$db_name" -c "SELECT 1;" &> /dev/null; then
        log_debug "数据库连接成功"
        return 0
    else
        log_debug "数据库连接失败"
        return 1
    fi
}

# 检查数据库是否存在
database_exists() {
    export PGPASSWORD="$DB_PASSWORD"
    
    local exists=$(psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "postgres" \
        -t -c "SELECT 1 FROM pg_database WHERE datname='$DB_NAME';" 2>/dev/null | xargs)
    
    [[ "$exists" == "1" ]]
}

# 创建数据库
create_database() {
    log_info "创建数据库: $DB_NAME"
    
    export PGPASSWORD="$DB_PASSWORD"
    
    if createdb -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" \
        -O "$DB_USER" \
        -E UTF8 \
        -T template0 \
        "$DB_NAME"; then
        log_info "数据库创建成功"
        return 0
    else
        log_error "数据库创建失败"
        return 1
    fi
}

# 删除数据库
drop_database() {
    log_warn "删除数据库: $DB_NAME"
    
    export PGPASSWORD="$DB_PASSWORD"
    
    # 断开所有连接
    psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "postgres" -c \
        "SELECT pg_terminate_backend(pg_stat_activity.pid) 
         FROM pg_stat_activity 
         WHERE pg_stat_activity.datname = '$DB_NAME' 
         AND pid <> pg_backend_pid();" &> /dev/null || true
    
    if dropdb -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" "$DB_NAME"; then
        log_info "数据库删除成功"
        return 0
    else
        log_error "数据库删除失败"
        return 1
    fi
}

# 列出可用的备份文件
list_available_backups() {
    log_info "可用的备份文件:"
    
    local backup_files=()
    
    # 查找全量备份
    if [[ -d "$BACKUP_DIR/full" ]]; then
        while IFS= read -r -d '' file; do
            backup_files+=("$file")
        done < <(find "$BACKUP_DIR/full" -name "*.sql*" -type f -print0 2>/dev/null | sort -z)
    fi
    
    if [[ ${#backup_files[@]} -eq 0 ]]; then
        log_error "未找到可用的备份文件"
        return 1
    fi
    
    echo
    echo "全量备份文件:"
    echo "序号  文件名                           大小      修改时间"
    echo "------------------------------------------------------------"
    
    local index=1
    for file in "${backup_files[@]}"; do
        local filename=$(basename "$file")
        local size=$(ls -lh "$file" | awk '{print $5}')
        local mtime=$(ls -l "$file" | awk '{print $6, $7, $8}')
        
        printf "%-4d  %-30s  %-8s  %s\n" "$index" "$filename" "$size" "$mtime"
        ((index++))
    done
    
    echo
    return 0
}

# 选择备份文件
select_backup_file() {
    local backup_file="$1"
    
    if [[ -n "$backup_file" ]]; then
        # 使用指定的备份文件
        if [[ -f "$backup_file" ]]; then
            echo "$backup_file"
            return 0
        else
            log_error "指定的备份文件不存在: $backup_file"
            return 1
        fi
    fi
    
    # 交互式选择
    list_available_backups
    
    local backup_files=()
    if [[ -d "$BACKUP_DIR/full" ]]; then
        while IFS= read -r -d '' file; do
            backup_files+=("$file")
        done < <(find "$BACKUP_DIR/full" -name "*.sql*" -type f -print0 2>/dev/null | sort -z)
    fi
    
    if [[ ${#backup_files[@]} -eq 0 ]]; then
        return 1
    fi
    
    echo -n "请选择要恢复的备份文件 (输入序号): "
    read -r selection
    
    if [[ "$selection" =~ ^[0-9]+$ ]] && [[ $selection -ge 1 ]] && [[ $selection -le ${#backup_files[@]} ]]; then
        local selected_file="${backup_files[$((selection-1))]}"
        echo "$selected_file"
        return 0
    else
        log_error "无效的选择: $selection"
        return 1
    fi
}

# 验证备份文件
verify_backup_file() {
    local backup_file="$1"
    
    log_info "验证备份文件: $(basename "$backup_file")"
    
    # 检查文件是否存在
    if [[ ! -f "$backup_file" ]]; then
        log_error "备份文件不存在"
        return 1
    fi
    
    # 检查文件大小
    local file_size=$(stat -c%s "$backup_file" 2>/dev/null || echo "0")
    if [[ $file_size -eq 0 ]]; then
        log_error "备份文件为空"
        return 1
    fi
    
    log_debug "备份文件大小: $(numfmt --to=iec $file_size)"
    
    # 检查文件格式
    export PGPASSWORD="$DB_PASSWORD"
    
    if [[ "$backup_file" =~ \.gz$ ]]; then
        # 压缩文件
        if zcat "$backup_file" | head -c 100 | grep -q "PostgreSQL"; then
            log_info "压缩备份文件验证通过"
        else
            log_error "压缩备份文件格式验证失败"
            return 1
        fi
    else
        # 检查pg_dump格式
        if pg_restore --list "$backup_file" &> /dev/null; then
            log_info "备份文件格式验证通过"
            
            # 显示备份信息
            local table_count=$(pg_restore --list "$backup_file" | grep "TABLE DATA" | wc -l)
            local function_count=$(pg_restore --list "$backup_file" | grep "FUNCTION" | wc -l)
            
            log_info "备份内容: ${table_count}个表, ${function_count}个函数"
        else
            log_error "备份文件格式验证失败"
            return 1
        fi
    fi
    
    return 0
}

# 创建恢复前的备份
create_pre_restore_backup() {
    if database_exists; then
        log_warn "目标数据库已存在，创建恢复前备份..."
        
        local timestamp=$(date '+%Y%m%d_%H%M%S')
        local backup_file="$BACKUP_DIR/pre_restore_backup_${timestamp}.sql"
        
        export PGPASSWORD="$DB_PASSWORD"
        
        if pg_dump -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" \
            --format=custom \
            --file="$backup_file" \
            "$DB_NAME"; then
            log_info "恢复前备份完成: $backup_file"
            echo "$backup_file"
            return 0
        else
            log_error "恢复前备份失败"
            return 1
        fi
    fi
    
    return 0
}

# 执行数据库恢复
restore_database() {
    local backup_file="$1"
    
    log_info "开始恢复数据库: $DB_NAME"
    log_info "备份文件: $(basename "$backup_file")"
    
    # 验证备份文件
    if ! verify_backup_file "$backup_file"; then
        return 1
    fi
    
    # 创建恢复前备份
    local pre_restore_backup=""
    if [[ "$FORCE_RESTORE" == "false" ]]; then
        pre_restore_backup=$(create_pre_restore_backup)
    fi
    
    export PGPASSWORD="$DB_PASSWORD"
    
    # 处理数据库
    if database_exists; then
        if [[ "$FORCE_RESTORE" == "true" ]]; then
            log_warn "强制恢复模式，删除现有数据库"
            if ! drop_database; then
                return 1
            fi
            if ! create_database; then
                return 1
            fi
        else
            log_warn "数据库已存在，将尝试在现有数据库上恢复"
        fi
    else
        if [[ "$CREATE_DB" == "true" ]] || [[ "$FORCE_RESTORE" == "true" ]]; then
            if ! create_database; then
                return 1
            fi
        else
            log_error "目标数据库不存在，请使用 --create-db 选项"
            return 1
        fi
    fi
    
    # 执行恢复
    log_info "执行数据库恢复..."
    
    local restore_options=""
    if [[ "$VERBOSE" == "true" ]]; then
        restore_options="--verbose"
    fi
    
    if [[ "$backup_file" =~ \.gz$ ]]; then
        # 压缩文件恢复
        if zcat "$backup_file" | psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME"; then
            log_info "数据库恢复完成"
        else
            log_error "数据库恢复失败"
            
            # 尝试恢复到恢复前状态
            if [[ -n "$pre_restore_backup" ]] && [[ -f "$pre_restore_backup" ]]; then
                log_warn "尝试回滚到恢复前状态..."
                restore_database "$pre_restore_backup"
            fi
            
            return 1
        fi
    else
        # pg_dump格式恢复
        if pg_restore $restore_options \
            -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" \
            --dbname="$DB_NAME" \
            --no-owner \
            --no-privileges \
            --clean \
            --if-exists \
            "$backup_file"; then
            log_info "数据库恢复完成"
        else
            log_error "数据库恢复失败"
            
            # 尝试恢复到恢复前状态
            if [[ -n "$pre_restore_backup" ]] && [[ -f "$pre_restore_backup" ]]; then
                log_warn "尝试回滚到恢复前状态..."
                restore_database "$pre_restore_backup"
            fi
            
            return 1
        fi
    fi
    
    return 0
}

# 验证恢复结果
verify_restore() {
    log_info "验证恢复结果..."
    
    export PGPASSWORD="$DB_PASSWORD"
    
    # 检查数据库连接
    if ! test_connection "$DB_NAME"; then
        log_error "恢复后数据库连接失败"
        return 1
    fi
    
    # 检查基本表结构
    local expected_tables=("members" "repair_tasks" "attendance_records" "task_tags")
    local missing_tables=()
    
    for table in "${expected_tables[@]}"; do
        local exists=$(psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" \
            -t -c "SELECT 1 FROM information_schema.tables WHERE table_name='$table';" | xargs)
        
        if [[ "$exists" != "1" ]]; then
            missing_tables+=("$table")
        fi
    done
    
    if [[ ${#missing_tables[@]} -gt 0 ]]; then
        log_error "缺少关键表: ${missing_tables[*]}"
        return 1
    fi
    
    # 检查数据行数
    local total_rows=0
    for table in "${expected_tables[@]}"; do
        local row_count=$(psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" \
            -t -c "SELECT COUNT(*) FROM $table;" 2>/dev/null | xargs || echo "0")
        total_rows=$((total_rows + row_count))
        log_debug "表 $table: $row_count 行"
    done
    
    log_info "恢复验证通过，总数据行数: $total_rows"
    return 0
}

# 显示帮助信息
show_help() {
    cat << EOF
数据库恢复脚本

用法: $0 [选项] [备份文件路径]

选项:
    -f, --force             强制恢复 (删除现有数据库)
    -c, --create-db         创建目标数据库 (如果不存在)
    -l, --list              列出可用的备份文件
    -v, --verbose           详细输出
    -h, --help              显示帮助信息
    
    --config FILE           指定配置文件
    --restore-point TIME    恢复到指定时间点 (暂未实现)

参数:
    备份文件路径            要恢复的备份文件路径 (可选，不指定则交互式选择)

示例:
    $0                                          # 交互式选择备份文件进行恢复
    $0 /path/to/backup.sql                      # 恢复指定的备份文件
    $0 --force --create-db backup.sql          # 强制恢复并创建数据库
    $0 --list                                   # 列出可用的备份文件
    
环境变量:
    DB_HOST                 数据库主机 (默认: localhost)
    DB_PORT                 数据库端口 (默认: 5432)
    DB_USER                 数据库用户 (默认: kwok)
    DB_PASSWORD             数据库密码
    DB_NAME                 数据库名称 (默认: attendence_prod)

注意事项:
    1. 恢复操作会修改或替换现有数据，请确保已备份重要数据
    2. 建议在恢复前先停止应用服务
    3. 恢复过程中会自动创建恢复前备份 (除非使用 --force 选项)
    4. 请确保有足够的磁盘空间进行恢复操作

EOF
}

# 确认操作
confirm_restore() {
    local backup_file="$1"
    
    echo
    log_warn "=========================================="
    log_warn "          数据库恢复确认"
    log_warn "=========================================="
    log_warn "目标数据库: ${DB_HOST}:${DB_PORT}/${DB_NAME}"
    log_warn "备份文件: $(basename "$backup_file")"
    log_warn "恢复模式: $([ "$FORCE_RESTORE" == "true" ] && echo "强制恢复" || echo "常规恢复")"
    log_warn "=========================================="
    
    if [[ "$FORCE_RESTORE" == "true" ]]; then
        log_warn "警告: 强制恢复将删除现有数据库!"
    fi
    
    echo -n "确认执行恢复操作? (y/N): "
    read -r confirmation
    
    case "$confirmation" in
        [Yy]|[Yy][Ee][Ss])
            return 0
            ;;
        *)
            log_info "恢复操作已取消"
            return 1
            ;;
    esac
}

# 主函数
main() {
    local backup_file=""
    
    # 解析命令行参数
    while [[ $# -gt 0 ]]; do
        case $1 in
            -f|--force)
                FORCE_RESTORE=true
                shift
                ;;
            -c|--create-db)
                CREATE_DB=true
                shift
                ;;
            -l|--list)
                load_config
                list_available_backups
                exit 0
                ;;
            -v|--verbose)
                VERBOSE=true
                shift
                ;;
            --config)
                CONFIG_FILE="$2"
                shift 2
                ;;
            --restore-point)
                RESTORE_POINT="$2"
                log_warn "时间点恢复功能暂未实现"
                shift 2
                ;;
            -h|--help)
                show_help
                exit 0
                ;;
            -*)
                log_error "未知选项: $1"
                show_help
                exit 1
                ;;
            *)
                backup_file="$1"
                shift
                ;;
        esac
    done
    
    log_info "开始数据库恢复任务..."
    
    # 执行恢复流程
    load_config
    check_dependencies
    
    if ! test_connection "postgres"; then
        log_error "无法连接到数据库服务器"
        exit 1
    fi
    
    # 选择备份文件
    if [[ -z "$backup_file" ]]; then
        backup_file=$(select_backup_file)
        if [[ $? -ne 0 ]] || [[ -z "$backup_file" ]]; then
            log_error "未选择有效的备份文件"
            exit 1
        fi
    else
        if [[ ! -f "$backup_file" ]]; then
            log_error "备份文件不存在: $backup_file"
            exit 1
        fi
    fi
    
    # 确认恢复操作
    if ! confirm_restore "$backup_file"; then
        exit 1
    fi
    
    # 执行恢复
    if restore_database "$backup_file"; then
        log_info "数据库恢复成功完成"
        
        # 验证恢复结果
        if verify_restore; then
            log_info "恢复验证通过"
        else
            log_warn "恢复验证失败，请手动检查数据完整性"
        fi
        
        log_info "恢复任务完成！"
    else
        log_error "数据库恢复失败"
        exit 1
    fi
}

# 错误处理
trap 'log_error "恢复过程中发生错误，退出码: $?"' ERR

# 执行主函数
main "$@"