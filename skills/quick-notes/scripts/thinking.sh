#!/bin/bash
# /thinking handler - just record thinking to OBS without solutions

CONTENT="$1"
VAULT="/mnt/f/obsidion/lukeguo"
THINKING_DIR="$VAULT/02-领域/临时记录/思考灵感"

# Ensure directory exists
mkdir -p "$THINKING_DIR"

# Get current date for filename
DATE=$(date +%Y-%m-%d)
FILENAME="$THINKING_DIR/${DATE}.md"

# Create file with content if it doesn't exist, otherwise append
if [ ! -f "$FILENAME" ]; then
    echo "# 思考灵感 - $DATE" > "$FILENAME"
    echo "" >> "$FILENAME"
fi

echo "## $CONTENT" >> "$FILENAME"
echo "**时间**: $(date +%H:%M)" >> "$FILENAME"
echo "" >> "$FILENAME"

echo "✅ 已记录思考: $CONTENT"
