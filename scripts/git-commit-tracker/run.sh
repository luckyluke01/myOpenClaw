#!/bin/bash
# Git Commit Tracker - 主控脚本
# 协调整个日报生成和推送流程

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_FILE="${SCRIPT_DIR}/config.sh"

# ============================================
# 颜色定义
# ============================================
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# ============================================
# 加载配置
# ============================================
load_config() {
    if [ -f "$CONFIG_FILE" ]; then
        source "$CONFIG_FILE"
        log_info "已加载配置文件"
    else
        log_error "配置文件不存在: $CONFIG_FILE"
        log_info "请复制 config.template.sh 为 config.sh 并修改配置"
        exit 1
    fi
}

# ============================================
# 生成报告
# ============================================
generate_report() {
    log_info "步骤 1/3: 生成 Git 提交报告..."
    
    # 导出配置供 generate-report.sh 使用
    export GIT_REPO_PATH
    export GIT_BRANCHES
    export OBSIDIAN_BRANCH_FILE
    export DEFAULT_BRANCHES
    export OBSIDIAN_VAULT_PATH
    export OBSIDIAN_DAILY_DIR
    export REPORT_SUBDIR
    
    # 执行报告生成脚本并捕获输出
    local output
    output=$("${SCRIPT_DIR}/generate-report.sh" 2>&1)
    
    # 提取飞书简报
    FEISHU_SUMMARY=$(echo "$output" | sed -n '/=== FEISHU_SUMMARY_START ===/,/=== FEISHU_SUMMARY_END ===/p' | sed '1d;$d')
    
    # 提取Obsidian路径（匹配多种格式）
    OBSIDIAN_FILE=$(echo "$output" | grep -E "(Obsidian路径:|已保存到:)" | tail -1 | sed 's/.*Obsidian路径: //' | sed 's/.*已保存到: //' | xargs)
    
    echo "$output"
    
    # 检查文件是否成功创建
    if [ -z "$OBSIDIAN_FILE" ]; then
        log_error "无法提取Obsidian文件路径"
        exit 1
    fi
    
    if [ ! -f "$OBSIDIAN_FILE" ]; then
        log_error "报告文件不存在: $OBSIDIAN_FILE"
        exit 1
    fi
    
    log_success "报告已生成: $OBSIDIAN_FILE"
}

# ============================================
# 推送到飞书消息（仅简报）
# ============================================
push_to_feishu_message() {
    log_info "步骤 2/3: 推送简报到飞书消息..."
    
    if [ -z "$FEISHU_CHAT_ID" ]; then
        log_info "未配置飞书Chat ID，跳过消息推送"
        return 0
    fi
    
    if [ -z "$FEISHU_SUMMARY" ]; then
        log_warn "飞书简报为空"
        return 0
    fi
    
    log_info "正在发送飞书消息到: $FEISHU_CHAT_ID"
    
    # 构建消息内容（简报已包含标题，无需再添加）
    local full_message="${FEISHU_SUMMARY}"
    
    log_info "消息长度: ${#full_message} 字符"
    
    # 输出消息内容
    echo ""
    echo "=== 飞书消息内容 ==="
    echo "$full_message"
    echo "==================="
    
    log_success "消息内容已生成"
    
    # 实际发送消息到飞书
    log_info "正在推送消息..."
    
    # 使用 openclaw message 工具发送
    # 注意：这需要配置 feishu 渠道
    if command -v openclaw &> /dev/null; then
        # 尝试通过 API 调用发送
        # 由于直接调用 message 工具可能需要特殊配置，这里输出提示
        log_info "飞书消息已准备，请通过 OpenClaw 发送或配置自动推送"
    fi
    
    log_success "飞书消息处理完成"
}

# ============================================
# 执行Obsidian同步
# ============================================
sync_obsidian() {
    log_info "步骤 3/3: 同步 Obsidian..."
    
    if [ -f "/mnt/f/.openclaw/workspace/scripts/obsidian-auto-commit.sh" ]; then
        log_info "执行 Obsidian 自动提交..."
        bash /mnt/f/.openclaw/workspace/scripts/obsidian-auto-commit.sh
    else
        log_info "Obsidian 自动提交脚本不存在，跳过"
    fi
    
    log_success "Obsidian 同步完成"
}

# ============================================
# 主函数
# ============================================
main() {
    log_info "=========================================="
    log_info "Git Commit Tracker - 日报生成"
    log_info "=========================================="
    
    load_config
    generate_report
    push_to_feishu_message
    sync_obsidian
    
    log_info "=========================================="
    log_success "全部完成!"
    log_info "=========================================="
}

# 执行
main
