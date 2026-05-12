#!/bin/bash
# 每日任务归档脚本 v2
# 每天20点自动将已完成的任务移动到 done 目录
# 如果没有已完成的任务，则不创建归档文件

VAULT="/mnt/f/obsidion/lukeguo"
TODO_DIR="$VAULT/02-领域/临时记录/待办事项"
ACTIVE_FILE="$TODO_DIR/active.md"
DONE_DIR="$TODO_DIR/done"

# 创建 done 目录（如果不存在）
mkdir -p "$DONE_DIR"

# 获取今天的日期
TODAY=$(date +%Y-%m-%d)
DONE_FILE="$DONE_DIR/${TODAY}.md"

# 检查 active.md 是否存在
if [ ! -f "$ACTIVE_FILE" ]; then
    echo "active.md 不存在，跳过归档"
    exit 0
fi

# 提取已完成的任务
COMPLETED_TASKS=$(grep -E "^\- \[x\]" "$ACTIVE_FILE" 2>/dev/null || true)

# 如果没有已完成的任务，不创建归档文件
if [ -z "$COMPLETED_TASKS" ]; then
    echo "没有已完成的任务，跳过归档"
    exit 0
fi

# 创建归档文件
echo "# 已完成任务 - $TODAY" > "$DONE_FILE"
echo "" >> "$DONE_FILE"
echo "$COMPLETED_TASKS" >> "$DONE_FILE"

# 从 active.md 中移除已完成的任务
sed -i '/^- \[x\]/d' "$ACTIVE_FILE"

echo "✅ 已完成任务已归档到 $DONE_FILE"
echo "已完成任务数量：$(echo "$COMPLETED_TASKS" | wc -l)"
