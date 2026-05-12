#!/bin/bash
# Git Commit Tracker - 安装向导
# 引导用户完成初始配置

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# 颜色
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
NC='\033[0m'

echo -e "${CYAN}"
echo "  ╔═══════════════════════════════════════════════════════════╗"
echo "  ║                                                           ║"
echo "  ║    🚀 Git Commit Tracker - 团队代码提交日报系统            ║"
echo "  ║                                                           ║"
echo "  ╚═══════════════════════════════════════════════════════════╝"
echo -e "${NC}"

echo ""
echo "本向导将帮助你完成初始配置。"
echo ""

# 检查配置文件是否存在
CONFIG_FILE="${SCRIPT_DIR}/config.sh"
TEMPLATE_FILE="${SCRIPT_DIR}/config.template.sh"

if [ ! -f "$CONFIG_FILE" ]; then
    echo -e "${YELLOW}首次运行，正在创建配置文件...${NC}"
    cp "$TEMPLATE_FILE" "$CONFIG_FILE"
    echo -e "${GREEN}✓ 配置文件已创建: $CONFIG_FILE${NC}"
    echo ""
fi

# 提示用户编辑配置
echo -e "${BLUE}步骤 1: 配置 Git 仓库${NC}"
echo "----------------------------------------"
echo "请编辑配置文件，设置你的 Git 仓库路径:"
echo "  $CONFIG_FILE"
echo ""
echo "需要配置的项:"
echo "  • GIT_REPO_PATH - Git仓库的本地路径"
echo "  • OBSIDIAN_BRANCH_FILE - Obsidian分支列表文件路径"
echo "  • FEISHU_CHAT_ID - 飞书消息推送的Chat ID（可选）"
echo ""
echo "分支配置方式:"
echo "  1. 在 Obsidian 中编辑: 01-项目/在执行项目git分支汇总.md"
echo "  2. 每行添加一个分支名（如: - main）"
echo "  3. 脚本会自动读取该文件获取分支列表"
echo ""

read -p "按 Enter 继续..."

# 检查Git仓库
echo ""
echo -e "${BLUE}步骤 2: 验证 Git 仓库${NC}"
echo "----------------------------------------"

source "$CONFIG_FILE"

if [ ! -d "$GIT_REPO_PATH/.git" ]; then
    echo -e "${RED}✗ 无效的 Git 仓库路径: $GIT_REPO_PATH${NC}"
    echo ""
    echo "请确保:"
    echo "  1. 路径正确"
    echo "  2. 该目录是一个 Git 仓库"
    echo "  3. 你有权限访问该目录"
    echo ""
    echo "如果是远程仓库，请先克隆到本地:"
    echo "  git clone <repository-url> $GIT_REPO_PATH"
    echo ""
    exit 1
fi

echo -e "${GREEN}✓ Git 仓库路径有效${NC}"
echo "  仓库: $GIT_REPO_PATH"

# 检查Obsidian分支文件
BRANCH_FILE="${OBSIDIAN_VAULT_PATH}/${OBSIDIAN_BRANCH_FILE}"
if [ -f "$BRANCH_FILE" ]; then
    echo -e "${GREEN}✓ Obsidian 分支文件存在${NC}"
    echo "  路径: $BRANCH_FILE"
    echo "  内容预览:"
    grep '^- ' "$BRANCH_FILE" 2>/dev/null | head -5 | sed 's/^/    /'
else
    echo -e "${YELLOW}⚠ Obsidian 分支文件不存在${NC}"
    echo "  将创建默认文件: $BRANCH_FILE"
    mkdir -p "$(dirname "$BRANCH_FILE")"
    cat > "$BRANCH_FILE" << 'EOF'
# 在执行项目 Git 分支汇总

## 当前跟踪的分支
- main
- develop
EOF
    echo -e "${GREEN}✓ 已创建默认分支文件${NC}"
fi

# 验证Obsidian路径
echo ""
echo -e "${BLUE}步骤 3: 验证 Obsidian 配置${NC}"
echo "----------------------------------------"

if [ ! -d "$OBSIDIAN_VAULT_PATH" ]; then
    echo -e "${YELLOW}⚠ Obsidian Vault 路径不存在${NC}"
    echo "  路径: $OBSIDIAN_VAULT_PATH"
    echo ""
    echo "请选择操作:"
    echo "  1. 创建该目录"
    echo "  2. 跳过（稍后手动配置）"
    read -p "选择 (1/2): " choice
    
    if [ "$choice" = "1" ]; then
        mkdir -p "$OBSIDIAN_VAULT_PATH"
        mkdir -p "${OBSIDIAN_VAULT_PATH}/${OBSIDIAN_DAILY_DIR}"
        echo -e "${GREEN}✓ 目录已创建${NC}"
    fi
else
    echo -e "${GREEN}✓ Obsidian Vault 路径有效${NC}"
    echo "  路径: $OBSIDIAN_VAULT_PATH"
fi

# 飞书配置（可选）
echo ""
echo -e "${BLUE}步骤 4: 飞书消息推送配置 (可选)${NC}"
echo "----------------------------------------"

if [ -n "$FEISHU_CHAT_ID" ]; then
    echo -e "${GREEN}✓ 飞书 Chat ID 已配置${NC}"
    echo "  简报将推送到: $FEISHU_CHAT_ID"
else
    echo -e "${YELLOW}⚠ 飞书 Chat ID 未配置${NC}"
    echo "  日报将只保存到 Obsidian"
    echo ""
    echo "如需配置飞书消息推送:"
    echo "  1. 获取飞书 Chat ID（群聊ID: oc_xxx 或用户ID: ou_xxx）"
    echo "  2. 设置到 FEISHU_CHAT_ID"
fi

echo ""

# 设置权限
echo -e "${BLUE}步骤 5: 设置执行权限${NC}"
echo "----------------------------------------"
chmod +x "${SCRIPT_DIR}/"*.sh
echo -e "${GREEN}✓ 脚本已设置为可执行${NC}"

# 测试运行
echo ""
echo -e "${BLUE}步骤 6: 测试运行${NC}"
echo "----------------------------------------"
echo "是否现在测试运行一次？"
read -p "测试运行? (y/n): " test_run

if [ "$test_run" = "y" ]; then
    echo ""
    echo "正在测试..."
    cd "$SCRIPT_DIR" && /bin/bash "${SCRIPT_DIR}/run.sh"
fi

# 配置定时任务
echo ""
echo -e "${BLUE}步骤 7: 配置定时任务${NC}"
echo "----------------------------------------"
echo "是否配置每天20:00自动生成日报？"
read -p "配置定时任务? (y/n): " setup_cron

if [ "$setup_cron" = "y" ]; then
    /bin/bash "${SCRIPT_DIR}/setup-cron.sh" add
fi

# 完成
echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}    🎉 配置完成！${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "使用指南:"
echo "  • 手动运行: ${SCRIPT_DIR}/run.sh"
echo "  • 编辑配置: ${CONFIG_FILE}"
echo "  • 定时任务: ${SCRIPT_DIR}/setup-cron.sh"
echo "  • 查看日志: ${SCRIPT_DIR}/cron.log"
echo ""
echo "报告将保存到:"
echo "  • Obsidian: ${OBSIDIAN_VAULT_PATH}/${OBSIDIAN_DAILY_DIR}/"

if [ -n "$FEISHU_CHAT_ID" ]; then
    echo "  • 飞书消息: 简报将推送到 $FEISHU_CHAT_ID"
fi

echo ""
echo "如有问题，请查看 README.md 或联系管理员。"
echo ""
