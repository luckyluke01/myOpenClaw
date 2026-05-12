---
name: ck-query-error-report
description: CK 查询日志异常统计自动执行。当需要自动执行 CK 查询错误报表（每日定时任务）、手动触发执行、或设置 cron 定时任务时激活。功能：从 ClickHouse 查询 system.query_log_distributed_cluster_atomic 生成近24小时错误报表，重试逻辑（最多10次/次），自动生成 Markdown 报告并提交到 Git 仓库。
---

# CK Query Log 错误报表 Skill

## 功能说明

自动查询 ClickHouse `system.query_log_distributed_cluster_atomic` 近24小时的异常查询，按小时汇总 error 记录，生成 Markdown 报表并提交到 Git 仓库。

## 脚本

```
scripts/run.sh
```

## 执行方式

### 手动执行

```bash
bash /mnt/f/.openclaw/workspace/skills/ck-query-error-report/scripts/run.sh
```

### 自动执行（定时任务）

- **执行时间：** 每天 21:05（GMT+8）
- **Cron 表达式：** `5 21 * * *`
- **Session 模式：** isolated（独立 session）
- **任务内容：** 执行 `run.sh`，完成后自动 git commit + push

> 定时任务由 OpenClaw cron 模块管理，无需手动干预。

## 输出

- **报表路径：** `/mnt/f/one-space/titanmonitor/CKquery/{YYYY-MM-DD}_ck_query_error_report.md`
- **Git 仓库：** `/mnt/f/one-space/titanmonitor`
- **Git 操作：** 自动 add → commit → push（如文件有变化）

## 重试逻辑

- 请求失败时（HTTP code ≠ 200），等待3秒后重试
- 最多尝试10次
- 任意一次成功即终止重试

## 依赖

- `curl`、`jq`、`git`（WSL/Linux 环境默认已有）
- API endpoint：`https://macs.bonree.com/OneData/clickhouse/sql/query`
- Cookie 已内置在脚本中
