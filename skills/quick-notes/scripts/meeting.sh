#!/bin/bash
# /meeting handler - just record meeting content, organize but no solutions

CONTENT="$1"
VAULT="/mnt/f/obsidion/lukeguo"
MEETING_DIR="$VAULT/02-领域/临时记录/会议记录"

# Ensure directory exists
mkdir -p "$MEETING_DIR"

# Get current date for filename
DATE=$(date +%Y-%m-%d)
FILENAME="$MEETING_DIR/${DATE}.md"

# Create file with content
if [ ! -f "$FILENAME" ]; then
    echo "# 会议记录 - $DATE" > "$FILENAME"
    echo "" >> "$FILENAME"
fi

echo "## $CONTENT" >> "$FILENAME"
echo "**时间**: $(date +%Y-%m-%d %H:%M)" >> "$FILENAME"
echo "" >> "$FILENAME"

echo "✅ 已记录会议: $CONTENT"
