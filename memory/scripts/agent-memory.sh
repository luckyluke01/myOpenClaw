#!/bin/bash
# agent-memory.sh - Agent 记忆自动学习脚本
# 使用方式: ./agent-memory.sh <agent-id> <memory-layer> <content>
# 示例: ./agent-memory.sh backend-architect medium "项目A: 架构设计中..."

MEMORY_BASE="/mnt/f/.openclaw/workspace/memory"
AGENT_ID="${1:-unknown}"
LAYER="${2:-session}"
CONTENT="${3:-}"

if [ -z "$CONTENT" ]; then
    echo "Usage: $0 <agent-id> <layer> <content>"
    exit 1
fi

TIMESTAMP=$(date "+%Y-%m-%d %H:%M")

case "$LAYER" in
    "long")
        DIR="$MEMORY_BASE/long-term"
        FILE="$DIR/${AGENT_ID}_long.md"
        echo "## [$TIMESTAMP] $AGENT_ID" >> "$FILE"
        echo "$CONTENT" >> "$FILE"
        echo "---" >> "$FILE"
        ;;
    "medium")
        DIR="$MEMORY_BASE/medium-term"
        FILE="$DIR/${AGENT_ID}_medium.md"
        echo "## [$TIMESTAMP] $AGENT_ID" >> "$FILE"
        echo "$CONTENT" >> "$FILE"
        echo "---" >> "$FILE"
        ;;
    "session")
        DIR="$MEMORY_BASE/sessions/active"
        FILE="$DIR/${AGENT_ID}_session.md"
        echo "## [$TIMESTAMP]" >> "$FILE"
        echo "$CONTENT" >> "$FILE"
        ;;
    "pattern")
        DIR="$MEMORY_BASE/patterns"
        FILE="$DIR/${AGENT_ID}_patterns.md"
        echo "## [$TIMESTAMP]" >> "$FILE"
        echo "$CONTENT" >> "$FILE"
        ;;
    *)
        echo "Invalid layer: $LAYER"
        exit 1
        ;;
esac

echo "[$(date)] $AGENT_ID memory updated ($LAYER)"