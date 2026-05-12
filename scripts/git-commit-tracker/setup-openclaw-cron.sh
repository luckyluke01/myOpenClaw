#!/bin/bash
# 使用 OpenClaw Cron 配置 Git Commit Tracker 定时任务
# 每天20:00自动生成代码提交日报

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

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

echo "========================================"
echo "Git Commit Tracker - OpenClaw Cron 配置"
echo "========================================"
echo ""

# 检查配置是否存在
if [ ! -f "${SCRIPT_DIR}/config.sh" ]; then
    log_error "配置文件不存在，请先运行 ./install.sh 进行初始化"
    exit 1
fi

# 检查 run.sh 是否可执行
if [ ! -x "${SCRIPT_DIR}/run.sh" ]; then
    chmod +x "${SCRIPT_DIR}/run.sh"
fi

log_info "创建 Cron 任务..."
log_info "执行时间: 每天 20:00"
log_info "时区: Asia/Shanghai"

# 使用 openclaw cron 命令添加任务
# 由于 openclaw cron 通过 systemEvent 触发，我们需要创建一个触发脚本执行的系统事件

# 创建触发脚本
cat > "${SCRIPT_DIR}/trigger.sh" << 'EOF'
#!/bin/bash
# Git Commit Tracker - OpenClaw Cron 触发脚本
# 由 OpenClaw Cron systemEvent 触发执行

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_FILE="${SCRIPT_DIR}/cron.log"

echo "========================================" >> "$LOG_FILE"
echo "Trigger time: $(date '+%Y-%m-%d %H:%M:%S')" >> "$LOG_FILE"
echo "========================================" >> "$LOG_FILE"

# 执行主脚本
/bin/bash "${SCRIPT_DIR}/run.sh" >> "$LOG_FILE" 2>&1

EXIT_CODE=$?

if [ $EXIT_CODE -eq 0 ]; then
    echo "[SUCCESS] Report generated at $(date)" >> "$LOG_FILE"
else
    echo "[ERROR] Failed with exit code $EXIT_CODE at $(date)" >> "$LOG_FILE"
fi

echo "" >> "$LOG_FILE"

exit $EXIT_CODE
EOF

chmod +x "${SCRIPT_DIR}/trigger.sh"

log_success "触发脚本已创建: ${SCRIPT_DIR}/trigger.sh"
log_info ""
log_info "========================================"
log_info "Cron 任务配置说明"
log_info "========================================"
log_info ""
log_info "你可以使用以下方式之一配置定时任务:"
log_info ""
log_info "方式 1: 系统 crontab (推荐)"
log_info "  运行: ./setup-cron.sh"
log_info ""
log_info "方式 2: OpenClaw Cron (需要 gateway 支持)"
log_info "  在 OpenClaw 中执行:"
log_info "  /cron add --name 'Git Commit Tracker' --schedule '0 20 * * *' --command '${SCRIPT_DIR}/trigger.sh'"
log_info ""
log_info "当前 Cron 任务列表:"
openclaw cron list 2>/dev/null || echo "  (OpenClaw Cron 不可用)"
