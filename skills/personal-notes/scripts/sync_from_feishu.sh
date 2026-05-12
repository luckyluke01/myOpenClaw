#!/bin/bash
# Sync Feishu Personal Notes to Obsidian
# Usage: ./sync_from_feishu.sh

set -e

# 配置
FEISHU_DOC_TOKEN="MZTSdJUfroZcHzx2ovOc5OVQnZF"
OBSIDIAN_VAULT="/mnt/f/obsidion/lukeguo"
BASE_DIR="$OBSIDIAN_VAULT/02-领域/临时记录"

# 临时文件存储飞书内容
TEMP_FILE=$(mktemp)
TEMP_DIR=$(mktemp -d)

# 获取飞书文档内容
echo "正在从飞书读取文档..."
feishu_doc read "$FEISHU_DOC_TOKEN" 2>/dev/null | grep -A1000 '"content":' | \
  sed 's/.*"content": "\(.*\)".*/\1/' | \
  sed 's/\\n/\n/g' > "$TEMP_FILE"

echo "飞书文档内容已读取"

# 解析并同步内容
CURRENT_DATE=""
CURRENT_SECTION=""

while IFS= read -r line; do
    # 跳过标题
    if [[ "$line" =~ ^✅|💡 ]]; then
        continue
    fi

    # 检测章节标题
    if [[ "$line" =~ ^To-Do ]]; then
        CURRENT_SECTION="todo"
        continue
    elif [[ "$line" =~ ^Thinking ]]; then
        CURRENT_SECTION="thinking"
        continue
    fi

    # 解析日期和内容行
    if [[ "$line" =~ ^([0-9]{4}-[0-9]{2}-[0-9]{2})[[:space:]]([0-9]{2}:[0-9]{2})[[:space:]]—[[:space:]](.+)$ ]]; then
        DATE="${BASH_REMATCH[1]}"
        TIME="${BASH_REMATCH[2]}"
        CONTENT="${BASH_REMATCH[3]}"

        case "$CURRENT_SECTION" in
            todo)
                # 检查是否是待办事项
                if [[ "$CONTENT" =~ ^\[ \] ]]; then
                    # 去掉 [ ] 前缀
                    TODO_CONTENT=$(echo "$CONTENT" | sed 's/^\[ \][[:space:]]*//')
                    bash /mnt/f/.openclaw/workspace/skills/personal-notes/scripts/add_note.sh \
                      "todo" "$TODO_CONTENT" > /dev/null
                    echo "✓ 待办: $TODO_CONTENT"
                elif [[ "$CONTENT" =~ ^想法： ]]; then
                    # 想法归为思考
                    THINKING_CONTENT=$(echo "$CONTENT" | sed 's/^想法：//')
                    bash /mnt/f/.openclaw/workspace/skills/personal-notes/scripts/add_note.sh \
                      "thinking" "$THINKING_CONTENT" > /dev/null
                    echo "✓ 思考: $THINKING_CONTENT"
                fi
                ;;
            thinking)
                # 思考内容
                bash /mnt/f/.openclaw/workspace/skills/personal-notes/scripts/add_note.sh \
                  "thinking" "$CONTENT" > /dev/null
                echo "✓ 思考: $CONTENT"
                ;;
        fi
    fi
done < "$TEMP_FILE"

# 清理临时文件
rm -f "$TEMP_FILE"
rm -rf "$TEMP_DIR"

echo ""
echo "同步完成！"
