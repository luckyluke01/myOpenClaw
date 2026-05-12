#!/bin/bash
# Add note to Obsidian
# Usage: ./add_note.sh <type> <content>
# Types: note, meeting, thinking, todo

set -e

TYPE="$1"
CONTENT="$2"
OBSIDIAN_VAULT="/mnt/f/obsidion/lukeguo"
BASE_DIR="$OBSIDIAN_VAULT/02-领域/临时记录"
DATE=$(date +%Y-%m-%d)
TIME=$(date +%H:%M)

# 验证类型
case "$TYPE" in
    note|meeting|thinking|todo)
        ;;
    *)
        echo "Error: Invalid type. Must be: note, meeting, thinking, or todo"
        exit 1
        ;;
esac

# 确定目录和文件
case "$TYPE" in
    note)
        DIR="$BASE_DIR/日常笔记"
        FILE="$DIR/${DATE}.md"
        ;;
    meeting)
        DIR="$BASE_DIR/会议记录"
        # 从内容中提取会议标题（第一个句子）
        TITLE=$(echo "$CONTENT" | head -1 | cut -c1-20 | sed 's/[[:space:]]\+$//')
        FILE="$DIR/${DATE}-${TITLE}.md"
        ;;
    thinking)
        DIR="$BASE_DIR/思考灵感"
        # 从内容中提取主题（第一个句子）
        TITLE=$(echo "$CONTENT" | head -1 | cut -c1-20 | sed 's/[[:space:]]\+$//')
        FILE="$DIR/${DATE}-${TITLE}.md"
        ;;
    todo)
        DIR="$BASE_DIR/待办事项"
        FILE="$DIR/active.md"
        ;;
esac

# 创建目录
mkdir -p "$DIR"

# 根据类型处理
case "$TYPE" in
    note)
        # 追加到日常笔记
        if [ ! -f "$FILE" ]; then
            echo "# ${DATE} 日常笔记" > "$FILE"
            echo "" >> "$FILE"
        fi
        echo "- [${TIME}] ${CONTENT}" >> "$FILE"
        ;;
    meeting)
        # 创建会议记录
        echo "# 会议记录" > "$FILE"
        echo "" >> "$FILE"
        echo "**时间**: ${DATE} ${TIME}" >> "$FILE"
        echo "" >> "$FILE"
        echo "${CONTENT}" >> "$FILE"
        echo "" >> "$FILE"
        echo "**待办**: 是" >> "$FILE"
        ;;
    thinking)
        # 创建思考笔记
        echo "# 思考记录" > "$FILE"
        echo "" >> "$FILE"
        echo "**时间**: ${DATE} ${TIME}" >> "$FILE"
        echo "" >> "$FILE"
        echo "${CONTENT}" >> "$FILE"
        echo "" >> "$FILE"
        echo "**待办**: 否" >> "$FILE"
        ;;
    todo)
        # 添加到待办事项
        if [ ! -f "$FILE" ]; then
            echo "# 待办事项" > "$FILE"
            echo "" >> "$FILE"
            echo "## 进行中" >> "$FILE"
            echo "" >> "$FILE"
        fi
        echo "- [ ] ${CONTENT} - ${DATE}" >> "$FILE"
        ;;
esac

echo "Created/Updated: $FILE"
