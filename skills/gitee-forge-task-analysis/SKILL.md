---
name: gitee-forge-task-analysis
description: 使用 Gitee Forge Search API 查询任务完成数据，提取工作项字段并按任务类型/标题/描述统计人力投入占比。触发条件：Gitee Forge 任务统计、实际完成时间查询、人力投入占比分析。
---

# Gitee Forge 任务统计与人效分析

## 概述

通过 Forge Search API 按「实际完成时间」查询任务，分页拉取全量数据，提取关键字段整理为表格，并基于任务标题、类型、描述统计人力投入占比。

## 何时使用

- 用户需要按时间段统计 Gitee Forge 已完成任务
- 需要导出任务明细表（创建人、工时、序列号、空间、描述、标题、类型）
- 需要分析哪些方面投入人力占比大

## 工具准备

### Python 脚本

脚本位置：`/mnt/f/one-space/newone/service/titan-query/scripts/fetch_gitee_forge_tasks.py`

### 环境配置

- **Session Token**: 需要用户登录 Gitee 后从浏览器获取
- 环境变量：`GITEE_SESSION_TOKEN`
- 或使用参数：`--token <token>`

## 使用方法

### 基本命令

```bash
python /mnt/f/one-space/newone/service/titan-query/scripts/fetch_gitee_forge_tasks.py \
  --start 2026-03-16 \
  --end 2026-03-22 \
  --token <your_session_token>
```

### 参数说明

| 参数 | 说明 | 必需 |
|------|------|------|
| `--start` | 开始日期 (实际完成时间)，格式 YYYY-MM-DD | 是 |
| `--end` | 结束日期 (实际完成时间)，格式 YYYY-MM-DD | 是 |
| `--token` | Gitee Session Token | 是 |
| `--output` | 输出目录 (默认当前目录) | 否 |

### 输出格式

统计报告保存到 Obsidian: `05-日记/每周任务追踪/YYYY-MM-DD-人员任务汇总.md`

包含两部分：
- **一、汇总统计** - 按人员/任务类型/空间的人力投入占比
- **二、明细数据** - 任务详情表（任务key、名称、负责人、工时、类型、空间、状态）

## API 配置

| 配置项 | 值 |
|--------|-----|
| URL | `https://gitee.ibr.net.cn/forge/api/search` |
| Method | POST |
| Content-Type | application/json |
| X-Parse-Application-Id | Bonree |
| X-Parse-Session-Token | 用户会话 Token |

## 请求体结构

```json
{
  "iql": "('实际完成时间' >= '{start_date}' and '实际完成时间' <= '{end_date}' and '负责人' in [\"membersOf(数据底座能力部)\"]) order by 创建时间 desc",
  "size": 200,
  "from": 0,
  "execFieldBehaviors": true,
  "fields": ["Cascade1","EMT5TLTN","Text01","ancestors","assignee","createdAt","createdBy","earlyWarning","field019","id","itemType","key","rowId","status","workspace","field002"]
}
```

## 字段映射

| API 字段 | 中文名 |
|----------|--------|
| createdBy | 创建人 |
| field019 | 已登记工时 |
| key | 任务序列号 |
| workspace | 任务所属空间 |
| field002 | 描述 |
| content | 描述内容 |
| name | 标题 |
| itemType | 任务类型 |

## 人力占比分析维度

- **按任务类型 (itemType)**：各类型任务数量/总工时占比
- **按标题关键词**：对 name 分词或匹配常见领域词（需求、bug、优化、文档等）
- **按描述 (field002)**：若描述含模块/项目名，可聚合统计

## 注意事项

- Session Token 会过期，需用户登录 Gitee 后从浏览器获取并更新
- 内网地址 `gitee.ibr.net.cn` 需在可访问环境运行
- 默认只查询"数据底座能力部"成员的任务
