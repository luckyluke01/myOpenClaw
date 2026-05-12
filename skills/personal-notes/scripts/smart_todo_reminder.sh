#!/bin/bash

# 智能待办提醒脚本
# 只在待办事项有变化时发送提醒

VAULT="/mnt/f/obsidion/lukeguo"
TODO_FILE="$VAULT/02-领域/临时记录/待办事项/active.md"
STATE_FILE="/mnt/f/.openclaw/workspace/memory/heartbeat-state.json"

# 获取待办事项数量
CURRENT_COUNT=$(grep -c "^- \[ \]" "$TODO_FILE" 2>/dev/null || echo 0)
LAST_COUNT=$(python3 -c "
import json, os
state_file = '$STATE_FILE'
if os.path.exists(state_file):
    try:
        with open(state_file) as f:
            state = json.load(f)
        val = state.get('lastTodoCount', 0)
        print(val if isinstance(val, int) else 0)
    except:
        print(0)
else:
    print(0)
" 2>/dev/null)

# 检查待办事项是否有变化（新增或完成）
if [ "$CURRENT_COUNT" != "$LAST_COUNT" ]; then
    # 发送提醒
    if [ "$CURRENT_COUNT" -gt 0 ]; then
        # 提取待办列表
        PENDING_LIST=$(grep "^- \[ \]" "$TODO_FILE" | sed 's/^- \[ \] //' | sed 's/ - .*//' | head -5)

        # 发送飞书消息
        openclaw message send \
            --target ou_bccc4ada608b8339a67f9426c7e03301 \
            --message "⏰ 每日提醒：您有 ${CURRENT_COUNT} 个待办事项未处理

📋 待办清单：
${PENDING_LIST}" \
            --channel feishu

        # 更新状态
        python3 << EOF
import json
with open('$STATE_FILE', 'r') as f:
    state = json.load(f)
state['lastTodoCount'] = $CURRENT_COUNT
state['lastTodoReminder'] = $(date +%s)
with open('$STATE_FILE', 'w') as f:
    json.dump(state, f, indent=2)
EOF
    fi
fi
