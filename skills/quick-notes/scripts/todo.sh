#!/bin/bash
# /todo handler - just record todo to OBS without thinking

CONTENT="$1"
VAULT="/mnt/f/obsidion/lukeguo"
TODO_FILE="$VAULT/02-领域/临时记录/待办事项/active.md"

# Get current date
DATE=$(date +%Y-%m-%d)

# Ensure directory exists
mkdir -p "$(dirname "$TODO_FILE")"

# Append todo to active.md
echo "- [ ] $CONTENT - $DATE" >> "$TODO_FILE"

echo "✅ 已记录待办: $CONTENT"
