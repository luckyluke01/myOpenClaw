#!/bin/bash
# memory-pipeline.sh - 记忆层级自动更新脚本
# 每日运行一次，自动整理和升级记忆

MEMORY_BASE="/mnt/f/.openclaw/workspace/memory"

echo "=== Agent Memory Pipeline ==="
echo "Running: $(date)"

# 1. 清理过期的中期记忆（5天前）
echo "[1/4] 清理过期中期记忆..."
find "$MEMORY_BASE/medium-term" -name "*.md" -mtime +5 -delete 2>/dev/null

# 2. 重建中期记忆汇总（从各子目录聚合）
echo "[2/4] 汇总会话记忆..."
{
    echo "# Medium-term Memory Summary"
    echo ""
    echo "## 活跃项目"
    for f in "$MEMORY_BASE/medium-term/projects"/*.md; do
        [ -f "$f" ] && cat "$f"
    done
    echo ""
    echo "## 待办跟踪"
    for f in "$MEMORY_BASE/medium-term/tasks"/*.md; do
        [ -f "$f" ] && cat "$f"
    done
    echo ""
    echo "## 团队上下文"
    for f in "$MEMORY_BASE/medium-term/context"/*.md; do
        [ -f "$f" ] && cat "$f"
    done
    echo ""
    echo "## 联系人"
    for f in "$MEMORY_BASE/medium-term/contacts"/*.md; do
        [ -f "$f" ] && cat "$f"
    done
    echo ""
    echo "*最后更新：$(date '+%Y-%m-%d')*"
} > "$MEMORY_BASE/medium-term/summary.md"

# 3. 分析模式，升级到长期记忆
echo "[3/4] 分析模式..."
if [ -f "$MEMORY_BASE/medium-term/summary.md" ]; then
    # 检查重复出现的概念/习惯
    mkdir -p "$MEMORY_BASE/patterns"
    cat "$MEMORY_BASE/medium-term"/*.md 2>/dev/null | grep -oE "\[.*?\]" | sort | uniq -c | sort -rn | head -10 > "$MEMORY_BASE/patterns/frequency.md"
fi

# 4. 更新用户习惯总结
echo "[4/4] 更新习惯总结..."
echo "## User Habits Summary - $(date)" > "$MEMORY_BASE/long-term/habits/summary.md"
echo "" >> "$MEMORY_BASE/long-term/habits/summary.md"

# 汇总各 Agent 的使用情况
mkdir -p "$MEMORY_BASE/long-term/habits"
if [ -d "$MEMORY_BASE/sessions/active" ]; then
    for agent_dir in ~/.openclaw/agency-agents/*/; do
        if [ -d "$agent_dir" ]; then
            agent_name=$(basename "$agent_dir")
            count=$(grep -l "$agent_name" "$MEMORY_BASE/sessions/active"/*.md 2>/dev/null | wc -l || echo 0)
            if [ "$count" -gt 0 ]; then
                echo "- $agent_name: $count 次使用" >> "$MEMORY_BASE/long-term/habits/summary.md"
            fi
        fi
    done
fi

echo ""
echo "Memory pipeline completed!"