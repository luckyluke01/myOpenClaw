#!/bin/bash
# Get pending issues from Obsidian
# Returns formatted list of pending items

set -e

OBSIDIAN_VAULT="/mnt/f/obsidion/lukeguo"
BASE_DIR="$OBSIDIAN_VAULT/02-领域/临时记录"
TODOS_FILE="$BASE_DIR/待办事项/active.md"

# 检查文件是否存在
if [ ! -f "$TODOS_FILE" ]; then
    echo "无待办事项"
    exit 0
fi

# 提取未完成的待办事项（包含 [ ] 或包含 "待办"、"问题"、"todo" 的内容）
PENDING_COUNT=$(grep -c "^\- \[ \]" "$TODOS_FILE" 2>/dev/null || echo "0")

if [ "$PENDING_COUNT" -eq 0 ]; then
    # 检查会议记录和思考笔记中的待办标记
    PENDING_COUNT=$(find "$BASE_DIR/会议记录" "$BASE_DIR/思考灵感" -name "*.md" -exec grep -l "待办.*是" {} \; 2>/dev/null | wc -l)
fi

if [ "$PENDING_COUNT" -eq 0 ]; then
    echo "无待办事项"
    exit 0
fi

# 输出待办事项列表
echo "待办事项清单 ($PENDING_COUNT 项):"
echo ""

# 从待办事项文件提取
if [ -f "$TODOS_FILE" ]; then
    echo "### 待办任务"
    grep "^\- \[ \]" "$TODOS_FILE" 2>/dev/null | sed 's/^\- \[ \]/- /'
fi

# 从会议记录提取待办
if [ -d "$BASE_DIR/会议记录" ]; then
    echo ""
    echo "### 会议行动项"
    find "$BASE_DIR/会议记录" -name "*.md" -exec grep -l "待办.*是" {} \; 2>/dev/null | while read -r file; do
        echo ""
        echo "$(basename "$file" .md):"
        grep -A2 "行动项\|待办" "$file" 2>/dev/null | grep -v "^--$" | head -5
    done
fi

# 从思考笔记提取待办
if [ -d "$BASE_DIR/思考灵感" ]; then
    echo ""
    echo "### 思考待办"
    find "$BASE_DIR/思考灵感" -name "*.md" -exec grep -l "待办.*是" {} \; 2>/dev/null | while read -r file; do
        echo ""
        echo "$(basename "$file" .md):"
        head -3 "$file" | tail -1
    done
fi
