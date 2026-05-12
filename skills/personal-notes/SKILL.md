---
name: personal-notes
description: "Personal note-taking and task management using Obsidian. Captures daily notes, meetings, thoughts, todos. Commands: /note, /meeting, /thinking, /todo. Daily 21:00 reminders for pending issues. Weekly Sunday 20:00 summary reports. Location: 02-领域/临时记录"
---

# Personal Notes (Obsidian)

## Overview

A personal knowledge management system that captures daily notes, meeting records, and thoughts into Obsidian vault, with automated reminders and weekly summaries.

## Quick Start

### Commands

- `/note <content>` — General notes and observations
- `/meeting <content>` — Meeting records and action items
- `/thinking <content>` — Ideas, inspirations, random thoughts
- `/todo <content>` — Explicit to-do items, automatically marked as pending

### Directory Structure

All notes are stored in the Obsidian vault at `02-领域/临时记录/`:
- **日常笔记/** — Daily general notes (YYYY-MM-DD.md format)
- **会议记录/** — Meeting records with action items (YYYY-MM-DD-会议标题.md)
- **思考灵感/** — Ideas and inspirations (YYYY-MM-DD-主题.md)
- **待办事项/** — Active to-do items and task tracking
- **周报汇总/** — Weekly summary reports (YYYY-WXX.md)

## Workflow

### 1. Recording a Note

When user uses `/note`, `/meeting`, `/thinking`, or `/todo`:

1. Parse the command and content
2. Create or append to the corresponding file in Obsidian
3. For `/meeting` and `/todo`, automatically add to pending issues
4. For items containing "问题", "待办", "todo", add to pending issues
5. Format with timestamps and proper markdown

### 2. Daily Reminder (21:00)

Cron job runs daily at 21:00:
1. Read all pending issues from `02-领域/临时记录/待办事项/`
2. Send reminder message via Feishu to user `ou_bccc4ada608b8339a67f9426c7e03301`
3. Include issue count and brief list

### 3. Weekly Report (Sunday 20:00)

Cron job runs every Sunday at 20:00:
1. Aggregate all notes from the past week (7 days)
2. Categorize by type (notes, meetings, thoughts)
3. List resolved and pending items
4. Generate summary report in `02-领域/临时记录/周报汇总/`
5. Send via Feishu to user `ou_bccc4ada608b8339a67f9426c7e03301`

## File Format

### Daily Note (日常笔记/2026-02-12.md)

```markdown
# 2026-02-12 日常笔记

## 下午

- [14:30] 完成了代码审查工作
- [15:00] 与团队讨论新功能设计方案

## 晚间

- [18:00] 记录今日工作总结
```

### Meeting Record (会议记录/2026-02-12-产品评审会.md)

```markdown
# 产品评审会

**时间**: 2026-02-12 10:00-11:30
**参与人**: 产品、技术、设计

## 讨论要点
- 新功能优先级排序
- 技术可行性评估

## 行动项
- [ ] 张三：完成技术方案文档
- [ ] 李四：更新UI设计稿

**待办**: 是
```

### Thinking Note (思考灵感/2026-02-12-产品优化想法.md)

```markdown
# 产品优化想法

**时间**: 2026-02-12 16:45

## 用户流程改进
当前用户注册流程需要5步，可以简化为3步
- 去掉不必要的验证步骤
- 合并信息收集页面

**待办**: 否
```

### Todo Item (待办事项/active.md)

```markdown
# 待办事项

## 进行中

- [ ] 完成技术方案文档 - 2026-02-13
- [ ] 代码审查 - 2026-02-14

## 待安排

- [ ] 用户调研计划
- [ ] 性能优化方案
```

## Resources

### scripts/

- `scripts/add_note.sh` — Create or append note to Obsidian
- `scripts/get_pending.sh` — Extract pending issues
- `scripts/generate_weekly.sh` — Generate weekly summary

### Obsidian Path

- **Vault**: `/mnt/f/obsidion/lukeguo`
- **Base**: `02-领域/临时记录`
- **Notes**: `02-领域/临时记录/日常笔记`
- **Meetings**: `02-领域/临时记录/会议记录`
- **Thinking**: `02-领域/临时记录/思考灵感`
- **Todos**: `02-领域/临时记录/待办事项`
- **Weekly**: `02-领域/临时记录/周报汇总`

## Cron Jobs

### Daily Reminder (21:00)

```bash
# 每日21:00提醒待办事项
0 21 * * *  # Asia/Shanghai timezone
```

### Weekly Report (Sunday 20:00)

```bash
# 每周日20:00生成周报
0 20 * * 0  # Asia/Shanghai timezone
```

## Migration from Feishu

This skill has been migrated from Feishu to Obsidian. To migrate existing data:

1. Export Feishu document content
2. Parse and convert to Obsidian markdown format
3. Place files in corresponding directories
4. Update cron job configurations
