#!/bin/bash
# Git Commit Tracker - 定时任务配置脚本
# 配置每天20:00自动执行日报生成

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RUNNER_SCRIPT="${SCRIPT_DIR}/run.sh"
CRON_TIME="0 20 * * *"
CRON_COMMENT="# Git Commit Tracker - Daily Report"

# 颜色
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# 检查当前cron任务
check_existing_cron() {
    log_info "检查现有定时任务..."
    
    if crontab -l 2>/dev/null | grep -q "git-commit-tracker"; then
        log_warn "已存在 Git Commit Tracker 的定时任务"
        crontab -l | grep "git-commit-tracker"
        return 1
    fi
    
    return 0
}

# 添加cron任务
add_cron_job() {
    log_info "添加定时任务..."
    
    # 创建临时文件
    local temp_crontab=$(mktemp)
    
    # 导出当前crontab
    crontab -l > "$temp_crontab" 2>/dev/null || true
    
    # 添加新任务
    echo "" >> "$temp_crontab"
    echo "$CRON_COMMENT" >> "$temp_crontab"
    echo "$CRON_TIME cd $SCRIPT_DIR && /bin/bash $RUNNER_SCRIPT >> ${SCRIPT_DIR}/cron.log 2>&1" >> "$temp_crontab"
    
    # 安装新crontab
    crontab "$temp_crontab"
    rm "$temp_crontab"
    
    log_success "定时任务已添加"
}

# 移除cron任务
remove_cron_job() {
    log_info "移除定时任务..."
    
    local temp_crontab=$(mktemp)
    
    # 导出并过滤掉我们的任务
    crontab -l | grep -v "git-commit-tracker" | grep -v "$CRON_COMMENT" > "$temp_crontab" || true
    
    # 安装新crontab
    crontab "$temp_crontab"
    rm "$temp_crontab"
    
    log_success "定时任务已移除"
}

# 显示当前cron任务
show_cron_jobs() {
    log_info "当前定时任务:"
    echo "========================================"
    crontab -l 2>/dev/null || echo "(无定时任务)"
    echo "========================================"
}

# 使用OpenClaw Cron（如果可用）
setup_openclaw_cron() {
    log_info "尝试使用 OpenClaw Cron 配置..."
    
    # 检查 openclaw 是否可用
    if ! command -v openclaw &> /dev/null; then
        log_warn "OpenClaw CLI 不可用，使用系统 crontab"
        return 1
    fi
    
    # 检查 cron 子命令是否可用
    if ! openclaw cron --help &> /dev/null; then
        log_warn "OpenClaw 不支持 cron 命令，使用系统 crontab"
        return 1
    fi
    
    log_info "使用 OpenClaw Cron 配置定时任务..."
    
    # 通过 OpenClaw Cron API 添加任务
    # 这会创建一个每天20:00执行的系统事件
    # 注意：这需要配置 openclaw gateway 的 cron 功能
    
    log_warn "OpenClaw Cron 功能需要额外配置，当前使用系统 crontab"
    return 1
}

# 主菜单
show_menu() {
    echo ""
    echo "========================================"
    echo "  Git Commit Tracker - 定时任务配置"
    echo "========================================"
    echo ""
    echo "1. 添加定时任务 (每天20:00)"
    echo "2. 移除定时任务"
    echo "3. 查看当前任务"
    echo "4. 测试运行一次"
    echo "q. 退出"
    echo ""
}

# 测试运行
test_run() {
    log_info "测试运行..."
    cd "$SCRIPT_DIR" && /bin/bash "$RUNNER_SCRIPT"
}

# 主函数
main() {
    # 确保脚本可执行
    chmod +x "$RUNNER_SCRIPT"
    chmod +x "${SCRIPT_DIR}/generate-report.sh"
    
    while true; do
        show_menu
        read -p "请选择操作: " choice
        
        case $choice in
            1)
                if check_existing_cron; then
                    add_cron_job
                    log_success "配置完成! 每天20:00将自动生成日报"
                    log_info "日志文件: ${SCRIPT_DIR}/cron.log"
                else
                    read -p "是否覆盖现有任务? (y/n): " confirm
                    if [ "$confirm" = "y" ]; then
                        remove_cron_job
                        add_cron_job
                    fi
                fi
                ;;
            2)
                remove_cron_job
                ;;
            3)
                show_cron_jobs
                ;;
            4)
                test_run
                ;;
            q|Q)
                log_info "退出"
                exit 0
                ;;
            *)
                log_error "无效选择"
                ;;
        esac
    done
}

# 如果带参数运行，直接执行对应操作
case "${1:-}" in
    add)
        check_existing_cron && add_cron_job
        ;;
    remove)
        remove_cron_job
        ;;
    show)
        show_cron_jobs
        ;;
    test)
        test_run
        ;;
    *)
        main
        ;;
esac
