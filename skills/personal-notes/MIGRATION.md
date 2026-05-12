# Personal Notes 迁移指南

## 概述

Personal Notes 技能已从飞书文档迁移到 Obsidian。本指南说明如何使用新系统和迁移现有数据。

## 新系统架构

### 目录结构

```
02-领域/临时记录/
├── README.md           # 说明文档
├── 日常笔记/          # /note 命令记录
├── 会议记录/          # /meeting 命令记录
├── 思考灵感/          # /thinking 命令记录
├── 待办事项/          # /todo 命令记录
└── 周报汇总/          # 每周自动生成
```

### 文件命名规范

- **日常笔记**: `YYYY-MM-DD.md` - 每天一个文件，追加记录
- **会议记录**: `YYYY-MM-DD-会议标题.md` - 每次会议一个文件
- **思考灵感**: `YYYY-MM-DD-主题.md` - 每个思考一个文件
- **待办事项**: `active.md` - 活跃待办列表
- **周报汇总**: `YYYY-WXX.md` - 每周汇总报告

## 使用方式

### 命令

```bash
/note 这是一条日常笔记
/meeting 产品评审会，讨论新功能优先级
/thinking 关于用户流程优化的想法
/todo 完成技术方案文档
```

### 定时任务

- **每日 21:00** - 发送待办事项提醒
- **每周日 20:00** - 生成周报并发送

### 脚本说明

#### `add_note.sh`

添加笔记到 Obsidian

```bash
./add_note.sh <type> <content>
```

类型: `note`, `meeting`, `thinking`, `todo`

#### `get_pending.sh`

提取所有待办事项

```bash
./get_pending.sh
```

返回格式化的待办清单

#### `generate_weekly.sh`

生成本周汇总报告

```bash
./generate_weekly.sh
```

创建 `YYYY-WXX.md` 格式的周报

## 从飞书迁移数据

### 步骤

1. **导出飞书文档**

   访问飞书文档 `MZTSdJUfroZcHzx2ovOc5OVQnZF`，导出为 Markdown

2. **解析内容**

   将飞书文档的各个部分转换到对应的 Obsidian 文件

3. **创建文件**

   ```bash
   # 日常笔记 -> 日常笔记/YYYY-MM-DD.md
   # 会议记录 -> 会议记录/YYYY-MM-DD-会议标题.md
   # 思考笔记 -> 思考灵感/YYYY-MM-DD-主题.md
   # 待办事项 -> 待办事项/active.md
   ```

4. **更新时间戳**

   如果需要保留原始时间，修改文件名和内容中的时间戳

5. **验证迁移**

   运行 `get_pending.sh` 验证待办事项
   运行 `generate_weekly.sh` 验证周报生成

### 迁移脚本示例

```bash
#!/bin/bash
# 迁移飞书日常笔记到 Obsidian

# 假设导出的内容在 feishu_export.md
# 提取日常笔记部分
sed -n '/## Daily Notes/,/## Meetings/p' feishu_export.md | \
  grep "^-" | \
  sed 's/^\- \[\([^]]*\)\] /\1 | /' | \
  while IFS='|' read -r time content; do
    date=$(echo "$time" | cut -d' ' -f1)
    bash /mnt/f/.openclaw/workspace/skills/personal-notes/scripts/add_note.sh \
      "note" "$content" "$date"
  done
```

## 配置更新

### Obsidian Vault 路径

默认路径: `/mnt/f/obsidion/lukeguo`

如果需要修改，更新脚本中的 `OBSIDIAN_VAULT` 变量。

### Cron Jobs

更新现有的 cron jobs，让它们调用新的脚本：

```yaml
# 每日提醒
payload:
  kind: agentTurn
  message: |
    运行待办事项检查：
    bash /mnt/f/.openclaw/workspace/skills/personal-notes/scripts/get_pending.sh
    并发送结果到用户 ou_bccc4ada608b8339a67f9426c7e03301

# 周报生成
payload:
  kind: agentTurn
  message: |
    运行周报生成：
    bash /mnt/f/.openclaw/workspace/skills/personal-notes/scripts/generate_weekly.sh
    并发送结果到用户 ou_bccc4ada608b8339a67f9426c7e03301
```

## 优势对比

| 特性 | 飞书 | Obsidian |
|------|------|---------|
| 本地存储 | ❌ | ✅ |
| 离线访问 | ❌ | ✅ |
| Git 版本控制 | ❌ | ✅ |
| 链接和引用 | 有限 | ✅ 强大的双向链接 |
| 插件生态 | ❌ | ✅ 丰富的插件 |
| 搜索 | 基础 | ✅ 强大的全文搜索 |
| 多媒体支持 | ✅ | ✅ |
| 协作 | ✅ | ❌ (通过 Git) |

## 常见问题

### Q: 数据安全吗？

A: Obsidian 文件在本地，可以通过 Git 同步到 GitHub。数据完全在你控制下。

### Q: 如何备份？

A: 使用 Git 定期提交：
```bash
cd /mnt/f/obsidion/lukeguo
git add .
git commit -m "Backup: $(date)"
git push
```

### Q: 能和其他人协作吗？

A: 通过 Git 可以协作，或者使用 Obsidian Live Share 插件。

### Q: 可以回滚到飞书吗？

A: 可以。保留飞书文档作为备份，或者重新配置 skill 指向飞书。

## 下一步

1. ✅ 已创建 Obsidian 目录结构
2. ✅ 已创建 shell 脚本
3. ✅ 已测试脚本功能
4. ⏳ 待迁移飞书数据
5. ⏳ 待更新 cron job 配置
6. ⏳ 待验证定时任务

## 技术支持

如有问题，查看：
- `SKILL.md` - 技能文档
- `scripts/` - 脚本源码
- `references/` - 参考资料
