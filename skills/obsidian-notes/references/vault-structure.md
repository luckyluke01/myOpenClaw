# Vault Structure Guide

Complete guide for setting up an Obsidian vault with PARA method and Feishu integration.

## Initial Setup

### 1. Create Vault Folder Structure

```bash
vault/
├── 00-Inbox/           # Quick capture - empty daily
├── 01-Projects/        # Active projects
├── 02-Areas/           # Ongoing responsibilities
├── 03-Resources/       # Reference materials
├── 04-Archive/         # Completed items
├── 05-Daily/           # Daily notes (auto-created)
├── 99-System/          # Templates, MOC, etc.
│   ├── Templates/
│   └── 00-MOC.md
└── .obsidian/          # Obsidian config (auto)
```

### 2. Create Core Files

**00-MOC.md** (Map of Content):
```markdown
# Map of Content

## 🎯 Active Projects
<!-- Update weekly -->

## 📌 Current Focus
<!-- Update daily -->

## 🔥 Urgent
<!-- Update as needed -->

## 📚 Quick Links
- [[Project Template]]
- [[Meeting Template]]
- [[Daily Note Template]]

---
*Last updated: {{date}}*
```

### 3. Template Files

**Project Template** (`99-System/Templates/Project.md`):
```markdown
---
date: {{date}}
type: project
status: active
---

# {{title}}

## Goal
What are we trying to achieve?

## Deadline

## Context
Background information

## Tasks
- [ ] 

## Resources

## Log
- {{date}}: Created project
```

**Meeting Template** (`99-System/Templates/Meeting.md`):
```markdown
---
date: {{date}}
type: meeting
---

# {{title}}

**Date:** {{date}}  
**Attendees:** 

## Agenda

## Notes

## Action Items
- [ ] 

## Decisions

## Next Steps
```

## Feishu Integration Setup

### Option 1: Manual Sync
1. Weekly, copy Feishu todos to `05-Daily/`
2. Process into Projects/Areas
3. Archive Feishu items when done

### Option 2: Automated Sync
1. Run script: `python scripts/sync_feishu_to_obsidian.py`
2. Review imported items
3. Organize as needed

## Recommended Obsidian Plugins

### Essential
| Plugin | Purpose |
|--------|---------|
| **Templater** | Auto-generate templates |
| **Periodic Notes** | Daily/weekly/monthly notes |
| **Dataview** | Query notes dynamically |

### Optional
| Plugin | Purpose |
|--------|---------|
| **Calendar** | Visual calendar for daily notes |
| **Kanban** | Board view for projects |
| **Excalidraw** | Diagrams and sketches |

## Daily Workflow

### Morning (5 min)
1. Open today's daily note
2. Review MOC for priorities
3. Check pending todos

### Throughout day
1. Capture to Feishu (quick)
2. Or: Capture to Inbox (if on computer)

### Evening (10 min)
1. Review today's notes
2. Update MOC if priorities changed
3. Log any insights

## Weekly Review (30 min, Sunday)

1. **Sync** (5 min)
   - Run sync script for Feishu → Obsidian
   - Review imported items

2. **Process Inbox** (10 min)
   - Review `00-Inbox/`
   - Move to Projects/Areas/Resources/Archive

3. **Review Projects** (10 min)
   - Archive completed projects
   - Update active project tasks
   - Check for stalled projects

4. **Update MOC** (5 min)
   - Refresh project list
   - Update current focus

## Naming Conventions

### Files
- **Projects:** `Project Name.md` (Pascal Case)
- **Areas:** `Area Name.md` (Pascal Case)
- **Daily:** `YYYY-MM-DD.md` (ISO date)
- **Resources:** `descriptive-name.md` (kebab-case)

### Links
- Use `[[Note Name]]` for wiki links
- Use aliases for readability: `[[Note Name|display text]]`

## Tips for Success

1. **Start simple** — Don't over-structure at first
2. **Capture first, organize later** — Get it down, then sort
3. **Use the inbox** — Don't decide immediately, decide later
4. **Archive, don't delete** — You might need it again
5. **Weekly review is essential** — The system degrades without it
