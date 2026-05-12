#!/bin/bash

# 待办检查脚本（简化版）
# 只读取 Obsidian 待办，不记录状态

VAULT="/mnt/f/obsidion/lukeguo"
TODO_FILE="$VAULT/02-领域/临时记录/待办事项/active.md"

# 获取待办事项数量
TODO_COUNT=$(grep -c "^- \[ \]" "$TODO_FILE" 2>/dev/null || echo 0)

echo "待办事项: $TODO_COUNT 个"

# 列出待办（可选，用于调试）
if [ "$TODO_COUNT" -gt 0 ]; then
    echo "---"
    grep "^- \[ \]" "$TODO_FILE" | sed 's/^- \[ \] //' | head -10
fi
