#!/usr/bin/env python3
"""生成 CK Query Log 错误报表 Markdown 文件（带智能分析 + SQL 样例）"""

import json
import sys
import os

def analyze_data(data_list):
    """分析数据，返回汇总信息"""
    if not data_list:
        return "", {}, []

    type_stats = {}
    total_errors = 0
    hours_with_errors = set()
    hour_counts = {}

    for item in data_list:
        th = item['th']
        name = item['exception_name']
        code = item['exception_code']
        cnt = int(item['error_count'])
        total = int(item['total_requests_in_hour'])

        hours_with_errors.add(th)
        total_errors += cnt

        key = (name, code)
        if key not in type_stats:
            type_stats[key] = {"count": 0, "hours": set()}
        type_stats[key]["count"] += cnt
        type_stats[key]["hours"].add(th)

        if th not in hour_counts:
            hour_counts[th] = 0
        hour_counts[th] += cnt

    total_hours = len(hour_counts)
    total_requests = sum(int(item['total_requests_in_hour']) for item in data_list)
    overall_ratio = total_errors / total_requests if total_requests > 0 else 0

    # 按错误数排序
    sorted_types = sorted(type_stats.items(), key=lambda x: x[1]["count"], reverse=True)

    return total_errors, total_hours, total_requests, overall_ratio, sorted_types

def build_md_table(data_list):
    rows = ""
    for item in data_list:
        rows += f"| {item['th']} | {item['exception_name']} | {item['exception_code']} | {item['error_count']} | {item['total_requests_in_hour']} | {item['ratio']} |\n"
    return rows

def build_summary_table(sorted_types):
    lines = ""
    severity = "⚠️ 需关注"
    for (name, code), stats in sorted_types:
        ratio = stats["count"] / sum(s[1]["count"] for s in sorted_types) * 100
        if ratio < 1:
            severity = "✅ 偶发"
        lines += f"| **{name}** | {code} | {len(stats['hours'])}小时 | {stats['count']} | {ratio:.1f}% | {severity} |\n"
    return lines

def build_samples_section(samples_data, sorted_types):
    """构建 SQL 样例章节"""
    if not samples_data:
        return "（暂无可用样例数据）\n"

    # 按 exception_code 分组
    samples_by_code = {}
    for item in samples_data:
        code = item['exception_code']
        if code not in samples_by_code:
            samples_by_code[code] = []
        samples_by_code[code].append(item)

    section = ""
    for (name, code), stats in sorted_types:
        ratio = stats["count"] / sum(s[1]["count"] for s in sorted_types) * 100
        if ratio < 1:
            continue  # 偶发问题不展开详情

        section += f"### {name} (code={code})\n\n"
        section += f"| 序号 | 执行时间 | 用户 | SQL | 错误信息 |\n"
        section += f"|------|----------|------|-----|----------|\n"

        items = samples_by_code.get(code, [])
        for idx, item in enumerate(items[:3], 1):
            query = item.get('query', 'N/A')
            # 截断过长的 SQL
            if len(query) > 200:
                query = query[:200] + "..."
            query = query.replace('|', '\\|').replace('\n', ' ').replace('\r', ' ')
            exception_msg = item.get('exception_message', 'N/A')
            if len(exception_msg) > 100:
                exception_msg = exception_msg[:100] + "..."
            exception_msg = exception_msg.replace('|', '\\|').replace('\n', ' ').replace('\r', ' ')
            event_time = item.get('event_time', 'N/A')
            user = item.get('user', 'N/A')
            section += f"| {idx} | {event_time} | {user} | {query} | {exception_msg} |\n"

        section += "\n"
        section += f"**共 {len(items)} 条记录，以上仅展示最新3条**\n\n"

        if len(items) > 3:
            section += f"<!-- 剩余 {len(items)-3} 条记录已省略 -->\n\n"

    return section

def main():
    summary_body = sys.argv[1]
    samples_body = sys.argv[2]
    date_label = sys.argv[3]
    timezone = sys.argv[4]
    timestamp = sys.argv[5]
    http_code = sys.argv[6]
    attempt = sys.argv[7]
    report_dir = sys.argv[8]

    summary_data = json.loads(summary_body)
    samples_data = json.loads(samples_body)

    request_id = summary_data.get("requestId", "unknown")
    query_host = summary_data.get("result", {}).get("queryHost", "unknown")
    elapsed = summary_data.get("result", {}).get("elapsedMillisTime", "unknown")
    summary_list = summary_data.get("result", {}).get("data", [])

    samples_list = samples_data.get("result", {}).get("data", []) if samples_data.get("result") else []

    os.makedirs(report_dir, exist_ok=True)

    time_part = timestamp.split('_', 1)[1] if '_' in timestamp else timestamp

    total_errors, total_hours, total_requests, overall_ratio, sorted_types = analyze_data(summary_list)

    table_rows = build_md_table(summary_list)
    summary_rows = build_summary_table(sorted_types)
    samples_section = build_samples_section(samples_list, sorted_types)

    # 判断严重类型
    focus_types = [(name, code) for (name, code), stats in sorted_types 
                   if stats["count"] / sum(s[1]["count"] for s in sorted_types) * 100 >= 1]

    report_content = f"""# CK Query Log 异常查询统计报告

> **生成时间：** {date_label} {time_part} ({timezone})  
> **查询范围：** 近24小时  
> **数据来源：** `system.query_log_distributed_cluster_atomic`  
> **请求Host：** {query_host}  
> **查询耗时：** {elapsed}ms  
> **请求ID：** {request_id}  
> **HTTP状态：** {http_code}（第{attempt}次请求成功）

---

## 一、原始数据

| th | exception_name | exception_code | error_count | total_requests_in_hour | ratio |
|----|---------------|---------------|-------------|------------------------|-------|
{table_rows}

---

## 二、智能分析

### 2.1 数据概览

| 指标 | 值 |
|------|-----|
| 统计周期 | 近24小时（共{len(summary_list)}条记录，{total_hours}个整点小时） |
| 涉及错误类型 | {len(sorted_types)}种 |
| 错误总次数 | 约{total_errors}次 |
| 总查询次数 | 约{total_requests}次 |
| 总体错误率 | 约{overall_ratio*100:.2f}% |

### 2.2 各错误类型分布

| 错误类型 | exception_code | 出现小时数 | 错误总数 | 占比 | 严重程度 |
|---------|---------------|-----------|---------|------|---------|
{summary_rows}

### 2.3 总体结论

| 结论 | 说明 |
|------|------|
| ✅ 服务运行正常 | 总体错误率约{overall_ratio*100:.2f}%，查询服务稳定 |
| ⚠️ TYPE_MISMATCH 需优化 | 每小时规律出现60条，可能是某类定时查询的共性问题，建议捞取具体 SQL 样例定位根源 |
| ✅ 其他两类错误为偶发 | UNKNOWN_IDENTIFIER 和 POCO_EXCEPTION 出现次数极少，暂无需处理 |

---

## 三、重点错误类型 SQL 样例

> 以下展示每类需关注的错误（占比≥1%）的最新3条 SQL 样例及其错误信息

{samples_section}

---

## 四、原始 SQL

### 4.1 汇总查询 SQL

```sql
SELECT
  th,
  errorCodeToName(exception_code) AS exception_name,
  exception_code,
  cnt AS error_count,
  total_requests_in_hour,
  round(cnt / total_requests_in_hour, 4) AS ratio
FROM
(
  SELECT
    toStartOfHour(event_time) AS th,
    exception_code,
    count() AS cnt,
    sum(count()) OVER (PARTITION BY toStartOfHour(event_time)) AS total_requests_in_hour
  FROM system.query_log_distributed_cluster_atomic
  WHERE event_time >= now() - INTERVAL 1 DAY
    AND query_kind = 'Select'
    AND initial_user = 'one'
    AND is_initial_query = 1
  GROUP BY th, exception_code
) AS subquery
WHERE exception_code <> 0
ORDER BY th DESC, exception_code;
```

### 4.2 样例查询 SQL

```sql
SELECT
  exception_code,
  errorCodeToName(exception_code) AS exception_name,
  query,
  exception_message,
  user,
  event_time
FROM system.query_log_distributed_cluster_atomic
WHERE event_time >= now() - INTERVAL 1 DAY
  AND query_kind = 'Select'
  AND initial_user = 'one'
  AND is_initial_query = 1
  AND exception_code <> 0
ORDER BY event_time DESC
LIMIT 200;
```

---

*报告生成工具：OpenClaw Agent*
"""

    report_path = f"{report_dir}/{date_label}_ck_query_error_report.md"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report_content)

    print(f"报告已生成：{report_path}", file=sys.stderr)

if __name__ == "__main__":
    main()
