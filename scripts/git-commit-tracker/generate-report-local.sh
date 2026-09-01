#!/bin/bash
# Git Commit Tracker - 本地数据报告生成脚本
# 跳过 git fetch，直接使用本地数据

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_FILE="${SCRIPT_DIR}/config.sh"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# 加载配置
if [ -f "$CONFIG_FILE" ]; then
    source "$CONFIG_FILE"
    log_info "已加载配置文件"
else
    log_error "配置文件不存在: $CONFIG_FILE"
    exit 1
fi

OBSIDIAN_VAULT_PATH="${OBSIDIAN_VAULT_PATH:-/mnt/f/obsidion/lukeguo}"
OBSIDIAN_DAILY_DIR="${OBSIDIAN_DAILY_DIR:-05-日记}"
REPORT_SUBDIR="${REPORT_SUBDIR:-git-reports}"
REPORT_RANGE="${REPORT_RANGE:-yesterday}"

# 日期计算
if [ "$REPORT_RANGE" = "yesterday" ]; then
    REPORT_DATE=$(date -d yesterday +%Y-%m-%d)
    SINCE_DATE=$(date -d yesterday +%Y-%m-%d)
    UNTIL_DATE=$(date +%Y-%m-%d)
else
    REPORT_DATE=$(date +%Y-%m-%d)
    SINCE_DATE=$(date +%Y-%m-%d)
    UNTIL_DATE=$(date -d tomorrow +%Y-%m-%d)
fi

log_info "统计日期: $REPORT_DATE"
log_info "时间段: $SINCE_DATE 20:00 ~ $UNTIL_DATE 20:00"

# 跟踪分支
branches="*"
# 统计人员
authors="郭其政 王俊 王浩 邢雪杰 郭全德 姚成耀 敖晶 杨龙伟 黄志远 林家宇 王睿 施冠程 张翔 陈雪兵 王明超 冯泽 冯庆雨 王宏旭 杨宪亮"

# 输出目录
OUTPUT_DIR="${OBSIDIAN_VAULT_PATH}/${OBSIDIAN_DAILY_DIR}/${REPORT_SUBDIR}"
mkdir -p "$OUTPUT_DIR"

REPORT_FILE="${OUTPUT_DIR}/${REPORT_DATE}.md"

log_info "报告文件: $REPORT_FILE"

# 构建作者过滤
author_filter=""
for author in $authors; do
    if [ -z "$author_filter" ]; then
        author_filter="--author=$author"
    else
        author_filter="$author_filter --author=$author"
    fi
done

# 获取提交记录（跳过 fetch）
log_info "获取提交记录..."

cd "$GIT_REPO_PATH"

# 获取所有分支的提交
raw_commits=$(git log --all \
    --since="${SINCE_DATE} 20:00:00" \
    --until="${UNTIL_DATE} 20:00:00" \
    --format="%H|%an|%cd|%s" \
    --date=short \
    --no-merges \
    $author_filter 2>/dev/null || true)

if [ -z "$raw_commits" ]; then
    log_info "未获取到提交记录"
    # 尝试不使用作者过滤
    raw_commits=$(git log --all \
        --since="${SINCE_DATE} 20:00:00" \
        --until="${UNTIL_DATE} 20:00:00" \
        --format="%H|%an|%cd|%s" \
        --date=short \
        --no-merges 2>/dev/null || true)
fi

# 统计
total_commits=$(echo "$raw_commits" | grep -c "|" 2>/dev/null || true)
[ -z "$total_commits" ] && total_commits=0
unique_authors=$(echo "$raw_commits" | cut -d'|' -f2 | sort -u | grep -v "^$" | wc -l)

# 按作者统计
author_stats=$(echo "$raw_commits" | awk -F'|' '{print $2}' | sort | uniq -c | sort -rn)

# 按类型统计
feat_count=$(echo "$raw_commits" | grep -ciE "(feat|新增|功能)" 2>/dev/null || echo "0")
fix_count=$(echo "$raw_commits" | grep -ciE "(fix|bug|修复)" 2>/dev/null || echo "0")
docs_count=$(echo "$raw_commits" | grep -ciE "(docs|文档)" 2>/dev/null || echo "0")
refactor_count=$(echo "$raw_commits" | grep -ciE "(refactor|重构)" 2>/dev/null || echo "0")
other_count=$((total_commits - feat_count - fix_count - docs_count - refactor_count))
[ "$other_count" -lt 0 ] && other_count=0

# 生成报告
cat > "$REPORT_FILE" << EOF
---
title: "Git 提交日报 - ${REPORT_DATE}"
date: ${REPORT_DATE}
tags:
  - git
  - 日报
  - commit-tracker
---

# Git 提交日报

**日期**: ${REPORT_DATE}  
**时间段**: ${SINCE_DATE} 20:00 ~ ${UNTIL_DATE} 20:00

## 📊 统计概览

| 指标 | 数值 |
|------|------|
| 总提交数 | ${total_commits} |
| 提交人数 | ${unique_authors} |
| 功能开发 (feat) | ${feat_count} |
| Bug 修复 (fix) | ${fix_count} |
| 文档更新 (docs) | ${docs_count} |
| 代码重构 (refactor) | ${refactor_count} |
| 其他 | ${other_count} |

## 👥 人员提交统计

$(echo "$author_stats" | head -20 | awk '{printf "| %s | %d |\n", $2, $1}')

## 📝 提交详情

| 时间 | 作者 | 提交信息 |
|------|------|----------|
EOF

# 添加提交详情
echo "$raw_commits" | while IFS='|' read -r hash author date message; do
    if [ -n "$hash" ]; then
        short_hash=${hash:0:8}
        echo "| ${date} | ${author} | \`${short_hash}\` ${message} |" >> "$REPORT_FILE"
    fi
done

cat >> "$REPORT_FILE" << EOF

---
*由 Git Commit Tracker 自动生成*
EOF

log_success "报告已生成: $REPORT_FILE"

# 输出飞书简报
echo ""
echo "=== FEISHU_SUMMARY_START ==="
echo "📋 **Git 提交日报 - ${REPORT_DATE}**"
echo ""
echo "📊 统计: 共 ${total_commits} 次提交，${unique_authors} 人参与"
echo ""
echo "🔧 类型分布:"
echo "• 功能开发: ${feat_count}"
echo "• Bug 修复: ${fix_count}"
echo "• 文档更新: ${docs_count}"
echo "• 代码重构: ${refactor_count}"
echo "• 其他: ${other_count}"
echo ""
echo "👥 Top 贡献者:"
echo "$author_stats" | head -5 | while read count author; do
    echo "• ${author}: ${count} 次"
done
echo "=== FEISHU_SUMMARY_END ==="

echo ""
echo "Obsidian路径: $REPORT_FILE"
