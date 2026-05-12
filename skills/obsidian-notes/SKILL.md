---
name: obsidian-notes
description: Obsidian vault management for deep knowledge organization and Zettelkasten workflows. Use when user wants to manage Obsidian notes, sync with Feishu, organize knowledge base using PARA method, process daily notes, extract and manage todos, create MOC (Map of Content), or structure their vault. Triggers include mentions of Obsidian, vault organization, PARA, Zettelkasten, knowledge management, note-taking workflows, bidirectional linking, or syncing notes between systems.
---

# Obsidian Notes

Manage and organize Obsidian vault for deep knowledge work and long-term knowledge storage.

## Quick Start

### Supported Commands

| Command | Description |
|---------|-------------|
| `/obs-todo <task>` | Add todo to daily note |
| `/obs-note <content>` | Add to daily note |
| `/obs-meeting <content>` | Add meeting notes |
| `/obs-sync` | Sync Feishu pending todos to Obsidian |
| `/obs-query` | Query pending todos from Obsidian |

### Vault Structure (PARA Method)

```
vault/
├── 00-收件箱/              # 快速捕获
├── 01-项目/               # 有截止日期的活跃项目
├── 02-领域/               # 持续的责任领域
├── 03-资源/               # 参考资料
│   ├── 01-数据血缘/
│   ├── 02-数据平台/
│   ├── 03-数据库性能/
│   ├── 04-存储技术/
│   ├── 05-云原生/
│   └── 99-模板/
├── 04-归档/               # 已完成/不活跃的内容
├── 05-日记/               # 每日笔记 (YYYY-MM-DD.md)
└── 00-MOC.md              # 内容地图 (入口点)
```

## Workflows

### 1. Daily Capture → Weekly Organization

**Daily (in Feishu):**
- Use `/todo`, `/thinking`, `/meeting` for quick capture
- Don't worry about structure, just get it down

**Weekly (in Obsidian):**
1. Run `/obs-sync` to pull Feishu todos
2. Review `00-收件箱/` and process each item
3. Move items to appropriate 项目/领域
4. Update MOC links

### 2. Creating a Note

For project notes:
```markdown
---
date: 2026-02-08
type: project
status: active
---

# Project Name

## Goal
What are we trying to achieve?

## Context
Background information and [[related notes]]

## Tasks
- [ ] Task 1
- [ ] Task 2

## Resources
- [Resource A](link)

## Log
- 2026-02-08: Started project
```

### 3. Processing Inbox

Read each item in `00-收件箱/` and decide:
- **Project?** → Move to `01-项目/`
- **Area of responsibility?** → Move to `02-领域/`
- **Reference?** → Move to `03-资源/`
- **Done/No longer relevant?** → Move to `04-归档/`

### 4. Maintaining MOC

Update `00-MOC.md` with current priorities:
```markdown
# 内容地图

## 活跃项目
- [[港交所灾备项目]]
- [[中行改代码跟进]]

## 当前关注领域
- [[存储部门规划]]
- [[技术能力提升]]

## 最近笔记
- [[2026-02-08]]
```

## Resources

### scripts/
- `sync_feishu_to_obsidian.py` — Pull todos from Feishu doc to Obsidian daily notes
- `query_todos.py` — Extract all pending todos from Obsidian vault
- `create_daily_note.py` — Generate daily note template

### references/
- `para-method.md` — PARA organization methodology
- `vault-structure.md` — Detailed vault setup guide

## Best Practices

1. **Daily notes are for capture, not storage** — Process into proper notes weekly
2. **Use links liberally** — `[[note name]]` creates connections
3. **Keep MOC updated** — It's your entry point
4. **Archive aggressively** — If not active, move it out of the way
5. **Sync direction**: Feishu (capture) → Obsidian (organize)
6. **中文目录命名**: 所有目录统一使用中文命名，保持风格一致
