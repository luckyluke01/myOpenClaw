# 🚀 Git Commit Tracker - 团队代码提交日报

自动追踪团队Git代码提交，生成日报并推送到 Obsidian 和飞书消息。

## ✨ 功能特性

- 📊 **每日统计** - 自动统计每人每天的代码提交量
- 🌿 **多分支支持** - 从 Obsidian 文件读取需要跟踪的分支
- 👥 **人员筛选** - 支持从 Obsidian 文件指定统计人员范围
- 📝 **Markdown报告** - 生成结构化的Markdown日报保存到Obsidian
- 📱 **飞书简报** - 自动推送摘要到飞书消息
- ⏰ **定时执行** - 每天20:00自动生成
- 📁 **空报告生成** - 即使无提交记录也生成空文档

## 📁 文件结构

```
git-commit-tracker/
├── README.md              # 本文件
├── install.sh             # 安装向导
├── config.template.sh     # 配置模板
├── config.sh              # 实际配置（从模板复制）
├── generate-report.sh     # 报告生成脚本
├── run.sh                 # 主控脚本
├── setup-cron.sh          # 定时任务配置
└── cron.log               # 定时任务日志
```

报告保存位置：
```
obsidian-vault/
├── 01-项目/
│   └── 在执行项目git分支汇总.md  ← 配置分支和人员
├── 05-日记/
│   └── git-reports/              ← 报告子目录
│       └── git-commit-YYYY-MM-DD.md
```

## 🚀 快速开始

### 1. 配置分支和人员

编辑 Obsidian 文件：`01-项目/在执行项目git分支汇总.md`

```markdown
# 在执行项目 Git 分支汇总

---

## 当前跟踪的分支

- 3.7.0.3-zh-1-guoqz
- 3.10.0.0-cmdb-guoqz
- 3.8.0.0-guoqz

---

## 统计人员范围（可选）

# 如果为空，则统计所有人员
# 如果指定人员，则只统计这些人的提交

- 张三
- 李四
```

### 2. 运行测试

```bash
cd /mnt/f/.openclaw/workspace/scripts/git-commit-tracker
./run.sh
```

### 3. 配置定时任务

```bash
./setup-cron.sh
```

## ⚙️ 配置说明

### Git仓库配置

编辑 `config.sh`:

```bash
# Git仓库本地路径
GIT_REPO_PATH="/path/to/your/repo"
```

### Obsidian 配置

```bash
# Obsidian Vault 路径
OBSIDIAN_VAULT_PATH="/mnt/f/.openclaw/workspace/obsidian-vault"

# 日报存放目录（相对于Vault根目录）
# 报告将保存到: 05-日记/git-reports/YYYY-MM-DD.md
OBSIDIAN_DAILY_DIR="05-日记"
REPORT_SUBDIR="git-reports"

# 分支列表文件路径
OBSIDIAN_BRANCH_FILE="01-项目/在执行项目git分支汇总.md"
```

### 飞书消息推送配置

```bash
# 飞书 Chat ID
FEISHU_CHAT_ID="ou_bccc4ada608b8339a67f9426c7e03301"
```

## 📝 Obsidian 配置文档格式

文件：`01-项目/在执行项目git分支汇总.md`

```markdown
# 在执行项目 Git 分支汇总

---

## 当前跟踪的分支

- main
- develop
- feature/new-api

---

## 统计人员范围（可选）

# 留空表示统计所有人员

- 张三
- 李四
```

## 📊 报告示例

### 有提交记录时

```markdown
# 📊 团队代码提交日报

**统计日期**: 2026-02-09
**生成时间**: 2026-02-10 20:00:00
**跟踪分支**: main develop
**统计人员**: 全部

---

## 📈 概览

| 指标 | 数值 |
|------|------|
| 总提交数 | 15 |
| 参与人数 | 3 |
| 涉及分支 | 2 |

---

## 🌿 分支提交统计

| 分支 | 提交数 |
|------|--------|
| main | 10 |
| develop | 5 |

---

## 👥 个人提交统计

| 成员 | 提交数 | Bug修复 | 功能开发 | 其他 |
|------|--------|---------|----------|------|
| 张三 | 6 | 2 | 3 | 1 |
| 李四 | 5 | 1 | 2 | 2 |

---

## 📝 详细提交列表

### 🐛 [Bug] fix: 修复登录问题 #456

- **作者**: 张三
- **分支**: main
- **时间**: 2026-02-09
- **Hash**: `a1b2c3d4`
- **关联**: bug-456
```

### 无提交记录时

```markdown
# 📊 团队代码提交日报

**统计日期**: 2026-02-09
**跟踪分支**: main develop
**统计人员**: 全部

---

## 📭 今日无提交记录

暂无代码提交数据。

---

*报告由 OpenClaw Git Commit Tracker 自动生成*
```

## 🔧 提交规范建议

为了准确识别Bug和需求：

- `fix:` / `bug:` / `修复:` - Bug修复
- `feat:` / `feature:` / `新增:` - 功能开发
- `docs:` - 文档更新
- `refactor:` - 代码重构
- `test:` - 测试相关
- `chore:` / `ci:` - 构建/CI

## 🐛 故障排除

### 问题：找不到 Git 仓库

**解决：**
1. 检查 `GIT_REPO_PATH` 配置
2. 确保路径指向 Git 仓库（包含 `.git` 目录）

### 问题：分支不存在

**解决：**
1. 检查 Obsidian 文件中的分支名称
2. 确保远程仓库有这些分支

### 问题：定时任务未执行

**解决：**
1. 检查 crontab：`crontab -l`
2. 查看日志：`cat cron.log`
3. 手动测试：`./run.sh`

## 📝 更新日志

### v1.3.0 (2026-02-10)
- ✨ 支持从 Obsidian 读取人员范围
- 📁 报告统一保存到子目录 `05-日记/git-reports/`
- 📄 空内容也生成报告文档

### v1.2.0 (2026-02-10)
- ✨ 支持从 Obsidian 文件读取分支列表
- 🔄 动态分支配置

### v1.1.0 (2026-02-10)
- ✨ 支持多分支统计
- 🔥 简化飞书推送

### v1.0.0 (2026-02-10)
- ✨ 初始版本

---

Made with ❤️ by OpenClaw
