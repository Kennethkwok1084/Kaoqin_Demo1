#!/bin/bash

# 数据库迁移回滚脚本
# 支持Alembic迁移的回滚操作

set -e

# 配置
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
BACKEND_DIR="$PROJECT_DIR/backend"
CONFIG_FILE="$PROJECT_DIR/.env.production"

# 默认参数
TARGET_REVISION=""
LIST_REVISIONS=false
BACKUP_BEFORE_ROLLBACK=true
FORCE_ROLLBACK=false
DRY_RUN=false

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
        # 设置默认数据库URL
        export DATABASE_URL=${DATABASE_URL:-"postgresql://kwok:Onjuju1084@localhost:5432/attendence_prod"}
    fi
    
    log_debug "数据库URL: ${DATABASE_URL}"
}

# 检查依赖
check_dependencies() {
    log_info "检查迁移依赖..."
    
    # 检查Python环境
    if ! command -v python3 &> /dev/null; then
        log_error "Python3 未安装"
        exit 1
    fi
    
    # 检查后端目录
    if [[ ! -d "$BACKEND_DIR" ]]; then
        log_error "后端目录不存在: $BACKEND_DIR"
        exit 1
    fi
    
    # 检查alembic配置
    if [[ ! -f "$BACKEND_DIR/alembic.ini" ]]; then
        log_error "Alembic配置文件不存在: $BACKEND_DIR/alembic.ini"
        exit 1
    fi
    
    # 检查migrations目录
    if [[ ! -d "$BACKEND_DIR/alembic/versions" ]]; then
        log_error "迁移文件目录不存在: $BACKEND_DIR/alembic/versions"
        exit 1
    fi
    
    log_info "依赖检查通过"
}

# 激活Python虚拟环境
activate_venv() {
    if [[ -f "$BACKEND_DIR/venv/bin/activate" ]]; then
        log_info "激活虚拟环境"
        source "$BACKEND_DIR/venv/bin/activate"
    elif [[ -f "$BACKEND_DIR/.venv/bin/activate" ]]; then
        log_info "激活虚拟环境"
        source "$BACKEND_DIR/.venv/bin/activate"
    else
        log_warn "未找到虚拟环境，使用系统Python"
    fi
}

# 获取当前迁移版本
get_current_revision() {
    cd "$BACKEND_DIR"
    
    local current_rev=$(alembic current 2>/dev/null | grep -oE '[a-f0-9]{12}' | head -1 || echo "")
    
    if [[ -n "$current_rev" ]]; then
        echo "$current_rev"
    else
        echo "none"
    fi
}

# 获取迁移历史
get_migration_history() {
    cd "$BACKEND_DIR"
    
    log_info "迁移历史:"
    echo
    echo "版本号         日期时间           描述"
    echo "--------------------------------------------------------"
    
    alembic history --verbose 2>/dev/null | while IFS= read -r line; do
        if [[ "$line" =~ ^Rev:\ ([a-f0-9]+)\ \(head\) ]]; then
            # 当前最新版本
            local rev="${BASH_REMATCH[1]}"
            echo -n "$rev (HEAD)  "
        elif [[ "$line" =~ ^Rev:\ ([a-f0-9]+) ]]; then
            # 其他版本
            local rev="${BASH_REMATCH[1]}"
            echo -n "$rev         "
        elif [[ "$line" =~ Parent:\ ([a-f0-9]+) ]]; then
            # 父版本信息
            continue
        elif [[ "$line" =~ Path:\ (.+) ]]; then
            # 文件路径，从中提取时间戳
            local path="${BASH_REMATCH[1]}"
            local filename=$(basename "$path")
            if [[ "$filename" =~ ([0-9]{4})([0-9]{2})([0-9]{2})_([0-9]{2})([0-9]{2})([0-9]{2}) ]]; then
                local timestamp="${BASH_REMATCH[1]}-${BASH_REMATCH[2]}-${BASH_REMATCH[3]} ${BASH_REMATCH[4]}:${BASH_REMATCH[5]}:${BASH_REMATCH[6]}"
                echo -n "$timestamp  "
            else
                echo -n "未知时间          "
            fi
        elif [[ "$line" =~ ^\ +(.+)$ ]]; then
            # 描述信息
            local desc="${BASH_REMATCH[1]}"
            echo "$desc"
        fi
    done
    
    echo
}

# 列出可用的迁移版本
list_available_revisions() {
    cd "$BACKEND_DIR"
    
    log_info "可用的迁移版本:"
    echo
    
    local current_rev=$(get_current_revision)
    log_info "当前版本: $current_rev"
    
    echo
    get_migration_history
}

# 验证目标版本
validate_target_revision() {
    local target="$1"
    
    if [[ -z "$target" ]]; then
        log_error "未指定目标版本"
        return 1
    fi
    
    cd "$BACKEND_DIR"
    
    # 检查版本是否存在
    if ! alembic history | grep -q "$target"; then
        log_error "目标版本不存在: $target"
        return 1
    fi
    
    # 检查是否是有效的回滚操作
    local current_rev=$(get_current_revision)
    
    if [[ "$current_rev" == "$target" ]]; then
        log_warn "目标版本与当前版本相同"
        return 1
    fi
    
    log_info "目标版本验证通过: $target"
    return 0
}

# 创建回滚前备份
create_rollback_backup() {
    log_info "创建回滚前备份..."
    
    local timestamp=$(date '+%Y%m%d_%H%M%S')
    local backup_file="$PROJECT_DIR/backups/pre_rollback_backup_${timestamp}.sql"
    
    # 确保备份目录存在
    mkdir -p "$(dirname "$backup_file")"
    
    # 调用备份脚本
    if [[ -f "$SCRIPT_DIR/backup.sh" ]]; then
        if "$SCRIPT_DIR/backup.sh" --type full --no-cleanup; then
            log_info "回滚前备份完成"
            return 0
        else
            log_error "回滚前备份失败"
            return 1
        fi
    else
        # 直接使用pg_dump
        local db_config=$(parse_database_url "$DATABASE_URL")
        
        export PGPASSWORD="$db_password"
        
        if pg_dump -h "$db_host" -p "$db_port" -U "$db_user" \
            --format=custom \
            --no-owner \
            --no-privileges \
            --file="$backup_file" \
            "$db_name"; then
            log_info "回滚前备份完成: $backup_file"
            return 0
        else
            log_error "回滚前备份失败"
            return 1
        fi
    fi
}

# 解析数据库URL
parse_database_url() {
    local db_url="$1"
    
    # 解析 postgresql://user:password@host:port/database
    if [[ "$db_url" =~ postgresql://([^:]+):([^@]+)@([^:]+):([^/]+)/(.+) ]]; then
        db_user="${BASH_REMATCH[1]}"
        db_password="${BASH_REMATCH[2]}"
        db_host="${BASH_REMATCH[3]}"
        db_port="${BASH_REMATCH[4]}"
        db_name="${BASH_REMATCH[5]}"
        
        log_debug "数据库连接信息: ${db_user}@${db_host}:${db_port}/${db_name}"
        return 0
    else
        log_error "无效的数据库URL格式"
        return 1
    fi
}

# 执行迁移回滚
execute_rollback() {
    local target_revision="$1"
    
    log_info "开始迁移回滚..."
    log_info "目标版本: $target_revision"
    
    cd "$BACKEND_DIR"
    
    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "试运行模式，显示回滚SQL:"
        alembic downgrade "$target_revision" --sql
        return 0
    fi
    
    # 执行回滚
    log_info "执行回滚命令: alembic downgrade $target_revision"
    
    if alembic downgrade "$target_revision"; then
        log_info "迁移回滚成功"
        
        # 验证回滚结果
        local new_current=$(get_current_revision)
        if [[ "$new_current" == "$target_revision" ]]; then
            log_info "回滚验证通过，当前版本: $new_current"
            return 0
        else
            log_error "回滚验证失败，当前版本: $new_current，期望版本: $target_revision"
            return 1
        fi
    else
        log_error "迁移回滚失败"
        return 1
    fi
}

# 验证回滚结果
verify_rollback() {
    log_info "验证回滚结果..."
    
    cd "$BACKEND_DIR"
    
    # 检查数据库连接
    if ! python3 -c "
import asyncio
from app.core.database import async_engine

async def test_connection():
    try:
        async with async_engine.begin() as conn:
            result = await conn.execute('SELECT 1')
            print('数据库连接正常')
        return True
    except Exception as e:
        print(f'数据库连接失败: {e}')
        return False

result = asyncio.run(test_connection())
exit(0 if result else 1)
"; then
        log_error "回滚后数据库连接失败"
        return 1
    fi
    
    # 检查关键表是否存在
    local expected_tables=("alembic_version" "members" "repair_tasks")
    
    for table in "${expected_tables[@]}"; do
        if ! python3 -c "
import asyncio
from app.core.database import async_engine

async def check_table():
    try:
        async with async_engine.begin() as conn:
            result = await conn.execute(
                \"SELECT 1 FROM information_schema.tables WHERE table_name='$table'\"
            )
            return result.scalar() is not None
    except:
        return False

result = asyncio.run(check_table())
exit(0 if result else 1)
"; then
            log_error "关键表不存在: $table"
            return 1
        fi
    done
    
    log_info "回滚验证通过"
    return 0
}

# 显示帮助信息
show_help() {
    cat << EOF
数据库迁移回滚脚本

用法: $0 [选项] [目标版本]

选项:
    -l, --list              列出可用的迁移版本
    -f, --force             强制回滚 (跳过备份)
    --no-backup             不创建回滚前备份
    --dry-run               试运行模式 (仅显示SQL)
    -h, --help              显示帮助信息
    
    --config FILE           指定配置文件
    --debug                 启用调试模式

参数:
    目标版本                要回滚到的迁移版本号 (12位十六进制)

特殊目标版本:
    base                    回滚到最初状态 (清空所有迁移)
    -1                      回滚1个版本
    -2                      回滚2个版本
    head~1                  回滚1个版本 (相当于-1)

示例:
    $0 --list                           # 列出可用版本
    $0 abc123def456                     # 回滚到指定版本
    $0 -1                               # 回滚1个版本
    $0 base                             # 回滚到初始状态
    $0 --dry-run abc123def456           # 试运行回滚操作
    $0 --force --no-backup base         # 强制回滚到初始状态

注意事项:
    1. 回滚操作可能会导致数据丢失，请确保已备份重要数据
    2. 建议在回滚前先停止应用服务
    3. 脚本会自动创建回滚前备份 (除非使用 --no-backup)
    4. 使用 --dry-run 可以预览回滚操作的SQL语句
    5. 强制模式 (--force) 会跳过确认和备份步骤

环境变量:
    DATABASE_URL            数据库连接URL

EOF
}

# 确认回滚操作
confirm_rollback() {
    local target_revision="$1"
    local current_revision="$2"
    
    echo
    log_warn "=========================================="
    log_warn "        数据库迁移回滚确认"
    log_warn "=========================================="
    log_warn "当前版本: $current_revision"
    log_warn "目标版本: $target_revision"
    log_warn "数据库: $DATABASE_URL"
    log_warn "备份设置: $([ "$BACKUP_BEFORE_ROLLBACK" == "true" ] && echo "启用" || echo "禁用")"
    log_warn "=========================================="
    
    log_warn "警告: 回滚操作可能导致数据丢失!"
    
    echo -n "确认执行回滚操作? (y/N): "
    read -r confirmation
    
    case "$confirmation" in
        [Yy]|[Yy][Ee][Ss])
            return 0
            ;;
        *)
            log_info "回滚操作已取消"
            return 1
            ;;
    esac
}

# 主函数
main() {
    local target_revision=""
    
    # 解析命令行参数
    while [[ $# -gt 0 ]]; do
        case $1 in
            -l|--list)
                LIST_REVISIONS=true
                shift
                ;;
            -f|--force)
                FORCE_ROLLBACK=true
                BACKUP_BEFORE_ROLLBACK=false
                shift
                ;;
            --no-backup)
                BACKUP_BEFORE_ROLLBACK=false
                shift
                ;;
            --dry-run)
                DRY_RUN=true
                shift
                ;;
            --config)
                CONFIG_FILE="$2"
                shift 2
                ;;
            --debug)
                DEBUG=true
                shift
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
                target_revision="$1"
                shift
                ;;
        esac
    done
    
    log_info "开始数据库迁移回滚任务..."
    
    # 执行回滚流程
    load_config
    check_dependencies
    activate_venv
    
    # 列出版本信息
    if [[ "$LIST_REVISIONS" == "true" ]]; then
        list_available_revisions
        exit 0
    fi
    
    # 检查目标版本
    if [[ -z "$target_revision" ]]; then
        log_error "请指定目标版本"
        log_info "使用 --list 查看可用版本"
        exit 1
    fi
    
    # 获取当前版本
    local current_revision=$(get_current_revision)
    log_info "当前版本: $current_revision"
    
    # 处理特殊目标版本
    case "$target_revision" in
        -[0-9]*)
            # 相对回滚 (-1, -2 等)
            cd "$BACKEND_DIR"
            target_revision=$(alembic downgrade "$target_revision" --sql | grep -oE 'INFO.*downgrade [a-f0-9]+' | tail -1 | grep -oE '[a-f0-9]{12}' || echo "")
            if [[ -z "$target_revision" ]]; then
                log_error "无法确定相对回滚目标版本"
                exit 1
            fi
            ;;
        head~[0-9]*)
            # Git风格的相对版本 (head~1, head~2 等)
            local steps="${target_revision#head~}"
            target_revision="-$steps"
            cd "$BACKEND_DIR"
            target_revision=$(alembic downgrade "$target_revision" --sql | grep -oE 'INFO.*downgrade [a-f0-9]+' | tail -1 | grep -oE '[a-f0-9]{12}' || echo "")
            if [[ -z "$target_revision" ]]; then
                log_error "无法确定相对回滚目标版本"
                exit 1
            fi
            ;;
        base)
            # 回滚到初始状态
            log_info "回滚到初始状态"
            ;;
        *)
            # 验证目标版本
            if ! validate_target_revision "$target_revision"; then
                exit 1
            fi
            ;;
    esac
    
    log_info "目标版本: $target_revision"
    
    # 确认回滚操作
    if [[ "$FORCE_ROLLBACK" == "false" ]] && [[ "$DRY_RUN" == "false" ]]; then
        if ! confirm_rollback "$target_revision" "$current_revision"; then
            exit 1
        fi
    fi
    
    # 创建备份
    if [[ "$BACKUP_BEFORE_ROLLBACK" == "true" ]] && [[ "$DRY_RUN" == "false" ]]; then
        if ! create_rollback_backup; then
            log_error "回滚前备份失败，终止回滚操作"
            exit 1
        fi
    fi
    
    # 执行回滚
    if execute_rollback "$target_revision"; then
        if [[ "$DRY_RUN" == "false" ]]; then
            log_info "迁移回滚成功完成"
            
            # 验证回滚结果
            if verify_rollback; then
                log_info "回滚验证通过"
            else
                log_warn "回滚验证失败，请手动检查数据库状态"
            fi
            
            log_info "回滚任务完成！"
        else
            log_info "试运行完成"
        fi
    else
        log_error "迁移回滚失败"
        exit 1
    fi
}

# 错误处理
trap 'log_error "回滚过程中发生错误，退出码: $?"' ERR

# 执行主函数
main "$@"