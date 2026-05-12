#!/bin/bash
# Generate weekly summary report for Obsidian
# Usage: ./generate_weekly.sh

set -e

OBSIDIAN_VAULT="/mnt/f/obsidion/lukeguo"
BASE_DIR="$OBSIDIAN_VAULT/02-领域/临时记录"
REPORT_DIR="$BASE_DIR/周报汇总"
WEEK_NUMBER=$(date +%U)
YEAR=$(date +%Y)
REPORT_FILE="$REPORT_DIR/${YEAR}-W${WEEK_NUMBER}.md"
START_DATE=$(date -d "Monday -7 days" +%Y-%m-%d 2>/dev/null || date -v-7d +%Y-%m-%d)
END_DATE=$(date +%Y-%m-%d)

# 创建目录
mkdir -p "$REPORT_DIR"

# 统计数据
NOTE_COUNT=$(find "$BASE_DIR/日常笔记" -name "${START_DATE}*.md" -o -name "${END_DATE}*.md" 2>/dev/null | wc -l)
MEETING_COUNT=$(find "$BASE_DIR/会议记录" -name "${START_DATE}*.md" -o -name "${END_DATE}*.md" 2>/dev/null | wc -l)
THINKING_COUNT=$(find "$BASE_DIR/思考灵感" -name "${START_DATE}*.md" -o -name "${END_DATE}*.md" 2>/dev/null | wc -l)

# 获取待办事项
PENDING_COUNT=$(find "$BASE_DIR/待办事项" -name "*.md" -exec grep -c "^\- \[ \]" {} \; 2>/dev/null | awk '{sum+=$1} END {print sum}')

# 生成报告
cat > "$REPORT_FILE" <<EOF
# 第${WEEK_NUMBER}周汇总报告

**时间范围**: ${START_DATE} ~ ${END_DATE}
**生成时间**: $(date '+%Y-%m-%d %H:%M:%S')

---

## 📊 本周统计

| 类别 | 数量 |
|------|------|
| 日常笔记 | ${NOTE_COUNT} 篇 |
| 会议记录 | ${MEETING_COUNT} 篇 |
| 思考灵感 | ${THINKING_COUNT} 篇 |
| 待办事项 | ${PENDING_COUNT} 项 |

---

## 📝 日常笔记摘要

EOF

# 添加日常笔记摘要
if [ "$NOTE_COUNT" -gt 0 ]; then
    find "$BASE_DIR/日常笔记" -name "${START_DATE}*.md" -o -name "${END_DATE}*.md" 2>/dev/null | while read -r file; do
        echo "" >> "$REPORT_FILE"
        echo "### $(basename "$file" .md)" >> "$REPORT_FILE"
        echo "" >> "$REPORT_FILE"
        grep "^-" "$file" 2>/dev/null | head -10 >> "$REPORT_FILE"
    done
else
    echo "" >> "$REPORT_FILE"
    echo "*本周无日常笔记*" >> "$REPORT_FILE"
fi

cat >> "$REPORT_FILE" <<EOF

---

## 🤝 会议记录

EOF

# 添加会议记录
if [ "$MEETING_COUNT" -gt 0 ]; then
    find "$BASE_DIR/会议记录" -name "${START_DATE}*.md" -o -name "${END_DATE}*.md" 2>/dev/null | while read -r file; do
        echo "" >> "$REPORT_FILE"
        echo "### $(basename "$file" .md)" >> "$REPORT_FILE"
        echo "" >> "$REPORT_FILE"
        grep -E "时间|参与人|讨论要点|行动项" "$file" 2>/dev/null | head -10 >> "$REPORT_FILE"
    done
else
    echo "" >> "$REPORT_FILE"
    echo "*本周无会议记录*" >> "$REPORT_FILE"
fi

cat >> "$REPORT_FILE" <<EOF

---

## 💡 思考灵感

EOF

# 添加思考灵感
if [ "$THINKING_COUNT" -gt 0 ]; then
    find "$BASE_DIR/思考灵感" -name "${START_DATE}*.md" -o -name "${END_DATE}*.md" 2>/dev/null | while read -r file; do
        echo "" >> "$REPORT_FILE"
        echo "### $(basename "$file" .md)" >> "$REPORT_FILE"
        echo "" >> "$REPORT_FILE"
        head -10 "$file" 2>/dev/null | tail -8 >> "$REPORT_FILE"
    done
else
    echo "" >> "$REPORT_FILE"
    echo "*本周无思考灵感*" >> "$REPORT_FILE"
fi

cat >> "$REPORT_FILE" <<EOF

---

## ✅ 待办事项

### 进行中
EOF

# 添加进行中的待办事项
if [ -f "$BASE_DIR/待办事项/active.md" ]; then
    grep "^\- \[ \]" "$BASE_DIR/待办事项/active.md" 2>/dev/null >> "$REPORT_FILE"
else
    echo "*暂无进行中的待办事项*" >> "$REPORT_FILE"
fi

cat >> "$REPORT_FILE" <<EOF

---

*报告由 OpenClaw Personal Notes 自动生成*
EOF

echo "Generated: $REPORT_FILE"
