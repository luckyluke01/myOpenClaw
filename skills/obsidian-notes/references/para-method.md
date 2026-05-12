# PARA Method

PARA is a productivity framework by Tiago Forte for organizing digital information.

## The Four Categories

### 1. Projects
**Definition:** A series of tasks linked to a goal, with a deadline.

**Characteristics:**
- Has a clear goal/outcome
- Has a deadline or target date
- Can be completed

**Examples:**
- 港交所灾备v1上线
- 中行改代码优化
- 团队Q1培训计划

**Storage:** `01-Projects/`

---

### 2. Areas
**Definition:** A sphere of activity with a standard to be maintained over time.

**Characteristics:**
- Ongoing responsibility
- No specific deadline
- Requires regular attention
- Has a standard to maintain

**Examples:**
- 团队管理
- 技术能力提升
- 存储部门规划
- 客户维护

**Storage:** `02-Areas/`

---

### 3. Resources
**Definition:** A topic or theme of ongoing interest.

**Characteristics:**
- Reference material
- May be useful in the future
- Not currently actionable

**Examples:**
- 技术文档
- 会议记录模板
- 行业报告
- 学习笔记

**Storage:** `03-Resources/`

---

### 4. Archive
**Definition:** Inactive items from the other three categories.

**Characteristics:**
- Completed projects
- No longer relevant areas
- Outdated resources

**When to archive:**
- Project is completed
- Area is no longer your responsibility
- Resource is no longer relevant
- You haven't touched it in 3+ months

**Storage:** `04-Archive/`

---

## Decision Flowchart

```
New Item
    ↓
Has a goal and deadline?
    ↓ Yes → PROJECT
    ↓ No
Is it a responsibility to maintain?
    ↓ Yes → AREA
    ↓ No
Might be useful later?
    ↓ Yes → RESOURCE
    ↓ No → DELETE/ARCHIVE
```

## Weekly Review Process

1. **Process Inbox** (10 min)
   - Move each item to appropriate folder
   - Use decision flowchart above

2. **Review Projects** (15 min)
   - Check active projects
   - Update next actions
   - Archive completed ones

3. **Review Areas** (10 min)
   - Are standards being maintained?
   - Any new responsibilities?

4. **Clean Resources** (5 min)
   - Delete unused resources
   - Update useful ones

## Best Practices

1. **Start with action** — Organize based on what you're working on now
2. **Move fast** — Don't overthink categories
3. **Archive aggressively** — If not active, move it out
4. **Review weekly** — Keep the system current
5. **Use links** — Connect related items with `[[links]]`
