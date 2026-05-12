#!/bin/bash
# Git Commit Tracker - 配置文件
# 复制此文件为 config.sh 并填写实际配置

# ============================================
# Git 仓库配置 (必填)
# ============================================

# Git仓库本地路径
GIT_REPO_PATH="/mnt/f/.openclaw/newone/"

# 跟踪的分支列表
# 设置为空或 "*" 表示获取所有分支（只按人员筛选）
# 设置具体分支名如 "main,dev" 表示只获取指定分支
GIT_BRANCHES=""

# Obsidian分支列表文件路径（相对于Vault根目录）
# 文件格式:
#   ## 当前跟踪的分支
#   - main
#   - develop
#
#   ## 统计人员范围（可选）
#   - 张三
#   - 李四
OBSIDIAN_BRANCH_FILE="01-项目/在执行项目git分支汇总.md"

# 默认分支（当Obsidian文件不存在或为空时使用）
DEFAULT_BRANCHES="main"

# ============================================
# Obsidian 配置 (必填)
# ============================================

# Obsidian Vault 路径
OBSIDIAN_VAULT_PATH="/mnt/f/obsidion/lukeguo"

# 日报存放目录（相对于Vault根目录）
# 报告将保存到: OBSIDIAN_DAILY_DIR/git-reports/YYYY-MM-DD.md
OBSIDIAN_DAILY_DIR="05-日记"

# 报告子目录名
REPORT_SUBDIR="git-reports"

# ============================================
# 飞书消息推送配置 (可选)
# ============================================

# 飞书 Chat ID（群聊ID或用户ID）
FEISHU_CHAT_ID="ou_bccc4ada608b8339a67f9426c7e03301"

# ============================================
# 报告配置 (可选)
# ============================================

# 报告时间范围: yesterday | today
REPORT_RANGE="yesterday"

# 统计的提交类型（用于分类显示）
COMMIT_TYPES=(
    "fix|Bug修复|^(fix|bug|修复|fix:|bugfix:|bug:)"
    "feat|功能开发|^(feat|feature|新增|功能|feat:|feature:)"
    "docs|文档更新|^(docs|doc|文档)"
    "refactor|代码重构|^(refactor|重构)"
    "test|测试相关|^(test|测试)"
    "chore|构建/CI|^(chore|构建|ci|CI)"
)

# ============================================
# 高级配置
# ============================================

# 是否排除合并提交
EXCLUDE_MERGES=true

# 是否统计代码行数
SHOW_LINE_STATS=true

# 是否显示详细提交列表
SHOW_COMMIT_DETAILS=true

# 简报模式（只显示统计，不显示详细列表）
SUMMARY_MODE=false
