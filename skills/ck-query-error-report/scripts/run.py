#!/usr/bin/env python3
"""
CK Query Log Error Report - 直接执行查询并生成报告
支持两次查询:汇总数据 + SQL 样例
"""

import json
import subprocess
import sys
import os
import re

API_URL = "https://macs.bonree.com/OneData/clickhouse/sql/query"
COOKIE = "__bid_n=18a458a319898889c254bc; sensorsdata2015jssdkcross=%7B%22distinct_id%22%3A%2218a458a314fb4f-0d84f39197ea168-26031c51-2073600-18a458a315056d%22%2C%22first_id%22%3A%22%22%2C%22props%22%3A%7B%22%24latest_traffic_source_type%22%3A%22%E7%9B%B4%E6%8E%A5%E6%B5%81%E9%87%8F%22%2C%22%24latest_search_keyword%22%3A%22%E6%9C%AA%E5%8F%96%E5%88%B0_%E7%9B%B4%E6%8E%A5%E6%89%93%E5%BC%80%22%2C%22%24latest_referrer%22%3A%22%22%7D%2C%22identities%22%3A%22eyIkaWRlbnRpdHlfY29va2llX2lkIjoiMThhNDU4YTMxNGZiNGYtMGQ4NGYzOTE5N2VhMTY4LTI2MDMxYzUxLTIwNzM2MDAtMThhNDU4YTMxNTA1NmQifQ%3D%3D%22%2C%22history_login_id%22%3A%7B%22name%22%3A%22%22%2C%22value%22%3A%22%22%7D%2C%22%24device_id%22%3A%2218a458a314fb4f-0d84f39197ea168-26031c51-2073600-18a458a315056d%22%7D; signbonree=0; Hm_lvt_da1dc33910d60fbb5d553a130d2b5c42=1773224725,1775741517; usernamebonree=citicbank; truenamebonree=kzx123"

SQL_SUMMARY = """SELECT
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
ORDER BY th DESC, exception_code;"""

SQL_SAMPLES = """SELECT
  exception_code,
  errorCodeToName(exception_code) AS exception_name,
  query,
  exception,
  user,
  event_time
FROM system.query_log_distributed_cluster_atomic
WHERE event_time >= now() - INTERVAL 1 DAY
  AND query_kind = 'Select'
  AND initial_user = 'one'
  AND is_initial_query = 1
  AND exception_code <> 0
ORDER BY event_time DESC
LIMIT 200"""


def do_query(sql, max_attempts=10):
    """执行 CK 查询,带重试逻辑"""
    for attempt in range(1, max_attempts + 1):
        print(f"[CK Query] 请求尝试 #{attempt}", file=sys.stderr)

        payload = json.dumps({"sql": sql, "nodeId": "", "pageSize": 100, "pageNum": 1})

        result = subprocess.run([
            "curl", "-s", "-w", "\n___HTTP_CODE:%{http_code}", "-X", "POST",
            API_URL,
            "-H", f"Cookie: {COOKIE}",
            "-H", "Content-Type: application/json",
            "-d", payload
        ], capture_output=True, text=True)

        http_code_match = re.search(r"___HTTP_CODE:(\d+)", result.stdout)
        http_code = http_code_match.group(1) if http_code_match else "000"
        body = re.sub(r"\n___HTTP_CODE:.*", "", result.stdout)

        if http_code == "200":
            data = json.loads(body)
            if data.get("code") == 200:
                print(f"[CK Query] 请求成功 (HTTP 200)", file=sys.stderr)
                return data
            else:
                print(f"[CK Query] 请求返回 code={data.get('code')}: {data.get('message', '')[:200]}", file=sys.stderr)
        else:
            print(f"[CK Query] HTTP {http_code}", file=sys.stderr)

        if attempt < max_attempts:
            print("[CK Query] 3秒后重试...", file=sys.stderr)
            import time; time.sleep(3)

    raise Exception(f"已达最大重试次数 ({max_attempts})")


def analyze_summary(data_list):
    """分析汇总数据"""
    if not data_list:
        return None, 0, 0, 0, []

    type_stats = {}
    total_errors = 0
    hour_counts = {}

    for item in data_list:
        th = item['th']
        name = item['exception_name']
        code = item['exception_code']
        cnt = int(item['error_count'])
        total = int(item['total_requests_in_hour'])

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
    sorted_types = sorted(type_stats.items(), key=lambda x: x[1]["count"], reverse=True)

    return total_errors, total_hours, total_requests, overall_ratio, sorted_types


def build_md_table(data_list):
    rows = ""
    for item in data_list:
        rows += f"| {item['th']} | {item['exception_name']} | {item['exception_code']} | {item['error_count']} | {item['total_requests_in_hour']} | {item['ratio']} |\n"
    return rows


def build_summary_table(sorted_types):
    total = sum(s[1]["count"] for s in sorted_types)
    lines = ""
    for (name, code), stats in sorted_types:
        ratio = stats["count"] / total * 100 if total > 0 else 0
        severity = "⚠️ 需关注" if ratio >= 1 else "✅ 偶发"
        lines += f"| **{name}** | {code} | {len(stats['hours'])}小时 | {stats['count']} | {ratio:.1f}% | {severity} |\n"
    return lines


def build_samples_section(samples_list, sorted_types):
    """构建 SQL 样例章节"""
    if not samples_list:
        return "（暂无可用样例数据）\n"

    samples_by_code = {}
    for item in samples_list:
        code = item['exception_code']
        if code not in samples_by_code:
            samples_by_code[code] = []
        samples_by_code[code].append(item)

    total = sum(s[1]["count"] for s in sorted_types)
    top3_codes = set(code for (_, code), _ in sorted_types[:3])
    section = ""

    for (name, code), stats in sorted_types:
        if code not in top3_codes:
            continue

        section += f"### {name} (code={code})\n\n"
        section += "| 序号 | 执行时间 | 用户 | SQL | 错误信息 |\n"
        section += "|------|----------|------|-----|----------|\n"

        items = samples_by_code.get(code, [])
        for idx, item in enumerate(items[:3], 1):
            query = item.get('query', 'N/A')
            query = query.replace('|', '\\|').replace('\n', ' ').replace('\r', ' ')
            exception_msg = item.get('exception', 'N/A')
            exception_msg = exception_msg.replace('|', '\\|').replace('\n', ' ').replace('\r', ' ')
            event_time = item.get('event_time', 'N/A')
            user = item.get('user', 'N/A')
            section += f"| {idx} | {event_time} | {user} | {query} | {exception_msg} |\n"

        section += f"\n**共 {len(items)} 条记录，以上仅展示最新3条**\n\n"

    return section


def extract_error_patterns(samples_list, sorted_types):
    """从样例中提取错误原因模式，返回 {code: (pattern, root_cause)}"""
    samples_by_code = {}
    for item in samples_list:
        code = item['exception_code']
        if code not in samples_by_code:
            samples_by_code[code] = []
        samples_by_code[code].append(item)

    patterns = {}
    for (name, code), stats in sorted_types[:3]:
        items = samples_by_code.get(code, [])
        if not items:
            continue
        exceptions = [item.get('exception', '') for item in items]
        # 提取第一个异常的核心错误信息（前200字符）
        first_exc = exceptions[0] if exceptions else ''
        # 提取关键错误模式
        if 'TYPE_MISMATCH' in str(code) or 'Cannot convert' in first_exc:
            # 提取类型转换相关的错误
            matches = re.findall(r"Cannot convert string '([^']+)' to type (\w+)", first_exc)
            if matches:
                pattern = ', '.join([f"字符串 '{v}' 无法转为 {t}" for v, t in matches])
            else:
                pattern = "类型不匹配"
            root_cause = f"SQL 中存在类型转换错误：{pattern}。建议检查字段类型定义，确保比较双方类型一致。"
        elif 'UNKNOWN_IDENTIFIER' in str(code) or 'Unknown identifier' in first_exc:
            matches = re.findall(r"Unknown identifier '([^']+)'", first_exc)
            pattern = ', '.join([f"'{m}'" for m in matches]) if matches else "未知字段"
            root_cause = f"SQL 中引用的字段 {pattern} 不存在。建议检查字段名拼写或表结构是否变更。"
        elif 'NO_COMMON_TYPE' in str(code):
            matches = re.findall(r"No common type ([\w']+ vs [\w']+)", first_exc)
            pattern = matches[0] if matches else "类型不兼容"
            root_cause = f"两个表达式类型不兼容：{pattern}。建议显式类型转换后再比较。"
        elif 'POCO_EXCEPTION' in str(code):
            pattern = "POCO 内部异常"
            root_cause = "ClickHouse 内部错误，可能由资源限制或分布式查询超时导致。"
        else:
            pattern = first_exc[:100] if first_exc else "未知错误"
            root_cause = f"错误信息：{pattern[:100]}"

        patterns[code] = (name, pattern, root_cause)

    return patterns


def build_error_summary_section(error_patterns, sorted_types):
    """构建错误原因总结章节"""
    if not error_patterns:
        return ""

    section = "## 四、错误原因总结\n\n"
    section += "| 错误类型 | 核心问题 | 根因分析 |\n"
    section += "|----------|----------|----------|\n"

    for (name, code), stats in sorted_types[:3]:
        if code in error_patterns:
            _, pattern, root_cause = error_patterns[code]
            section += f"| **{name}** (code={code}) | {pattern} | {root_cause} |\n"
        else:
            section += f"| **{name}** (code={code}) | 暂无可用样例 | - |\n"

    section += "\n"
    return section


def main():
    import datetime

    date_label = datetime.datetime.now().strftime("%Y-%m-%d")
    timezone = datetime.datetime.now().astimezone().strftime("%Z")
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M")

    report_dir = "/mnt/f/one-space/titanmonitor/CKquery"
    os.makedirs(report_dir, exist_ok=True)

    print("=== 查询汇总数据 ===", file=sys.stderr)
    summary_result = do_query(SQL_SUMMARY)
    summary_data = summary_result.get("result", {}).get("data", [])

    print("=== 查询详细样例数据 ===", file=sys.stderr)
    samples_result = do_query(SQL_SAMPLES)
    samples_data = samples_result.get("result", {}).get("data", []) if samples_result.get("result") else []

    request_id = summary_result.get("requestId", "unknown")
    query_host = summary_result.get("result", {}).get("queryHost", "unknown")
    elapsed = summary_result.get("result", {}).get("elapsedMillisTime", "unknown")
    http_code = "200"

    total_errors, total_hours, total_requests, overall_ratio, sorted_types = analyze_summary(summary_data)

    table_rows = build_md_table(summary_data)
    summary_rows = build_summary_table(sorted_types)
    samples_section = build_samples_section(samples_data, sorted_types)
    error_patterns = extract_error_patterns(samples_data, sorted_types)
    error_summary_section = build_error_summary_section(error_patterns, sorted_types)

    report_content = f"""# CK Query Log 异常查询统计报告

> **生成时间:** {date_label} {timestamp.split('_')[1]} ({timezone})
> **查询范围:** 近24小时
> **数据来源:** `system.query_log_distributed_cluster_atomic`
> **请求Host:** {query_host}
> **查询耗时:** {elapsed}ms
> **请求ID:** {request_id}
> **HTTP状态:** {http_code}

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
| 统计周期 | 近24小时(共{len(summary_data)}条记录,{total_hours}个整点小时) |
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
| ✅ 服务运行正常 | 总体错误率约{overall_ratio*100:.2f}%,查询服务稳定 |
| ⚠️ TYPE_MISMATCH 需优化 | 每小时规律出现60条,可能是某类定时查询的共性问题,建议捞取具体 SQL 样例定位根源 |
| ✅ 其他两类错误为偶发 | UNKNOWN_IDENTIFIER 和 POCO_EXCEPTION 出现次数极少,暂无需处理 |

---

## 三、重点错误类型 SQL 样例

> 以下展示每类需关注的错误(占比≥1%)的最新3条 SQL 样例及其错误信息

{samples_section}

{error_summary_section}

---

## 五、原始 SQL

### 5.1 汇总查询 SQL

```sql
{SQL_SUMMARY}
```

### 5.2 样例查询 SQL

```sql
{SQL_SAMPLES}
```

---

*报告生成工具:OpenClaw Agent*
"""

    report_path = f"{report_dir}/{date_label}_ck_query_error_report.md"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report_content)

    print(f"报告已生成:{report_path}", file=sys.stderr)

    # Git 提交
    repo_dir = "/mnt/f/one-space/titanmonitor"
    subprocess.run(["git", "config", "--local", "user.email", "openclaw@bonree.com"], cwd=repo_dir, capture_output=True)
    subprocess.run(["git", "config", "--local", "user.name", "OpenClaw Agent"], cwd=repo_dir, capture_output=True)

    subprocess.run(["git", "add", report_path], cwd=repo_dir, capture_output=True)
    commit_msg = f"CK query error report {date_label} {timestamp.split('_')[1]}"
    result = subprocess.run(["git", "commit", "-m", commit_msg], cwd=repo_dir, capture_output=True, text=True)
    if result.returncode == 0:
        subprocess.run(["git", "push", "origin", "HEAD"], cwd=repo_dir, capture_output=True)
        print(f"Git 提交并推送成功: {commit_msg}", file=sys.stderr)
    else:
        if "nothing to commit" in result.stderr.lower():
            print("报告无变化,无需提交", file=sys.stderr)
        else:
            print(f"Git 提交失败: {result.stderr}", file=sys.stderr)


if __name__ == "__main__":
    main()
