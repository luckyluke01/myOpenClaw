#!/usr/bin/env python3
"""CK Query Log Error Report - 直接执行查询 + 生成报告"""

import json
import subprocess
import sys
import os
import re
from datetime import datetime

# ==== 配置 ====
COOKIE = "__bid_n=18a458a319898889c254bc; sensorsdata2015jssdkcross=%7B%22distinct_id%22%3A%2218a458a314fb4f-0d84f39197ea168-26031c51-2073600-18a458a315056d%22%2C%22first_id%22%3A%22%22%2C%22props%22%3A%7B%22%24latest_traffic_source_type%22%3A%22%E7%9B%B8%E6%8E%A5%E6%B5%81%E9%87%8F%22%2C%22%24latest_search_keyword%22%3A%22%E6%9C%AA%E5%8F%96%E5%88%B0%E5%80%BC_%E7%9B%B4%E6%8E%A5%E6%89%93%E5%BC%80%22%2C%22%24latest_referrer%22%3A%22%22%7D%2C%22identities%22%3A%22eyIkaWRlbnRpdHlfY29va2llX2lkIjoiMThhNDU4YTMxNGZiNGYtMGQ4NGYzOTE5N2VhMTY4LTI2MDMxYzUxLTIwNzM2MDAtMThhNDU4YTMxNTA1NmQifQ%3D%3D%22%2C%22history_login_id%22%3A%7B%22name%22%3A%22%22%2C%22value%22%3A%22%22%7D%2C%22%24device_id%22%3A%2218a458a314fb4f-0d84f39197ea168-26031c51-2073600-18a458a315056d%22%7D; signbonree=0; Hm_lvt_da1dc33910d60fbb5d553a130d2b5c42=1773224725,1775741517; usernamebonree=citicbank; truenamebonree=kzx123"
API_URL = "https://macs.bonree.com/OneData/clickhouse/sql/query"

SQL_SUMMARY = """SELECT th, errorCodeToName(exception_code) AS exception_name, exception_code, cnt AS error_count, total_requests_in_hour, round(cnt / total_requests_in_hour, 4) AS ratio FROM ( SELECT toStartOfHour(event_time) AS th, exception_code, count() AS cnt, sum(count()) OVER (PARTITION BY toStartOfHour(event_time)) AS total_requests_in_hour FROM system.query_log_distributed_cluster_atomic WHERE event_time >= now() - INTERVAL 1 DAY AND query_kind = 'Select' AND initial_user = 'one' AND is_initial_query = 1 GROUP BY th, exception_code ) AS subquery WHERE exception_code <> 0 ORDER BY th DESC, exception_code;"""

SQL_SAMPLES = """SELECT exception_code, errorCodeToName(exception_code) AS exception_name, query, type, user, event_time FROM system.query_log_distributed_cluster_atomic WHERE event_time >= now() - INTERVAL 1 DAY AND query_kind = 'Select' AND initial_user = 'one' AND is_initial_query = 1 AND exception_code <> 0 ORDER BY event_time DESC LIMIT 200;"""

REPORT_DIR = "/mnt/f/one-space/titanmonitor/CKquery"
REPO_DIR = "/mnt/f/one-space/titanmonitor"


def do_query(sql, max_attempts=10):
    """执行 CK 查询，带重试逻辑"""
    payload = json.dumps({'sql': sql, 'nodeId': '', 'pageSize': 100, 'pageNum': 1})

    for attempt in range(1, max_attempts + 1):
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 请求尝试 #{attempt}")

        proc = subprocess.Popen(
            ['curl', '-s', '-w', '\n___HTTP_CODE:%{http_code}', '-X', 'POST',
             API_URL, '-H', f'Cookie: {COOKIE}', '-H', 'Content-Type: application/json', '-d', payload],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        stdout_data, stderr_data = proc.communicate(timeout=120)
        
        stdout = stdout_data.decode('utf-8', errors='replace')
        print(f"[DEBUG] stdout len={len(stdout)}, last40={repr(stdout[-40:])}")

        # 分离 HTTP code 和 body
        if '\n___HTTP_CODE:' in stdout:
            parts = stdout.rsplit('\n___HTTP_CODE:', 1)
            body = parts[0].strip()
            http_code = parts[1].strip()
        else:
            http_code = 'unknown'
            body = stdout

        print(f"[DEBUG] body first40={repr(body[:40])}, body len={len(body)}")
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] HTTP {http_code}")

        if http_code == '200':
            return body
        else:
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 请求失败 (HTTP {http_code})，3秒后重试...")
            if attempt < max_attempts:
                time.sleep(3)
            else:
                print(f"已达最大重试次数 ({max_attempts})，退出")
                sys.exit(1)


def analyze_data(data_list):
    if not data_list:
        return 0, 0, 0, 0, []

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
    total_count = sum(s[1]["count"] for s in sorted_types)
    lines = ""
    for (name, code), stats in sorted_types:
        ratio = stats["count"] / total_count * 100 if total_count > 0 else 0
        severity = "⚠️ 需关注" if ratio >= 1 else "✅ 偶发"
        lines += f"| **{name}** | {code} | {len(stats['hours'])}小时 | {stats['count']} | {ratio:.1f}% | {severity} |\n"
    return lines


def extract_root_cause(exception_name, exception_message):
    text = f"{exception_name} {exception_message}"
    patterns = [
        (r'TYPE_MISMATCH', '类型不匹配'),
        (r'UNKNOWN_IDENTIFIER', '未知标识符'),
        (r'NO_COMMON_TYPE', '无公共类型'),
        (r'TABLE.*NOT.*EXIST', '表不存在'),
        (r'COLUMN.*NOT.*FOUND', '列不存在'),
        (r'MEMORY_LIMIT_EXCEEDED', '内存超限'),
        (r'TIMEOUT', '查询超时'),
        (r'SYNTAX_ERROR', '语法错误'),
        (r'CANNOT_PARSE', '无法解析'),
        (r'INVALID_VALUE', '无效值'),
    ]
    for pattern, label in patterns:
        if re.search(pattern, text, re.IGNORECASE):
            return label
    return "其他错误"


def build_samples_section(samples_list, sorted_types):
    if not samples_list:
        return "（暂无可用样例数据）\n"

    total_count = sum(s[1]["count"] for s in sorted_types)

    samples_by_code = {}
    for item in samples_list:
        code = item['exception_code']
        if code not in samples_by_code:
            samples_by_code[code] = []
        samples_by_code[code].append(item)

    section = ""
    for (name, code), stats in sorted_types:
        ratio = stats["count"] / total_count * 100 if total_count > 0 else 0
        if ratio < 1:
            continue

        section += f"### {name} (code={code})\n\n"
        section += f"| 序号 | 执行时间 | 用户 | SQL | 异常类型 |\n"
        section += f"|------|----------|------|-----|----------|\n"

        items = samples_by_code.get(code, [])
        for idx, item in enumerate(items[:3], 1):
            query = item.get('query', 'N/A')
            if len(query) > 200:
                query = query[:200] + "..."
            query = query.replace('|', '\\|').replace('\n', ' ').replace('\r', ' ')
            exception_type = item.get('type', 'N/A')
            event_time = item.get('event_time', 'N/A')
            user = item.get('user', 'N/A')
            section += f"| {idx} | {event_time} | {user} | {query} | {exception_type} |\n"

        section += "\n"
        section += f"**共 {len(items)} 条记录，以上仅展示最新3条**\n\n"

        root_causes = {}
        for item in items:
            rc = extract_root_cause(item.get('exception_name', ''), item.get('type', ''))
            root_causes[rc] = root_causes.get(rc, 0) + 1
        if root_causes:
            top_rc = max(root_causes, key=root_causes.get)
            section += f"**根因：** {top_rc}\n\n"

        if len(items) > 3:
            section += f"<!-- 剩余 {len(items)-3} 条记录已省略 -->\n\n"

    return section


def main():
    print("=== 查询汇总数据 ===")
    summary_body = do_query(SQL_SUMMARY)
    print(f"[DEBUG main] summary_body first50={repr(summary_body[:50])}, len={len(summary_body)}")

    print("\n=== 查询详细样例数据 ===")
    samples_body = do_query(SQL_SAMPLES)
    print(f"[DEBUG main] samples_body first50={repr(samples_body[:50])}, len={len(samples_body)}")

    try:
        summary_data = json.loads(summary_body)
    except json.JSONDecodeError as e:
        print(f"汇总数据 JSON 解析失败: {e}")
        print(f"原始内容 (前500字符): {summary_body[:500]}")
        sys.exit(1)

    try:
        samples_data = json.loads(samples_body)
    except json.JSONDecodeError as e:
        print(f"样例数据 JSON 解析失败: {e}")
        print(f"原始内容 (前500字符): {samples_body[:500]}")
        sys.exit(1)

    request_id = summary_data.get("requestId", "unknown")
    query_host = summary_data.get("result", {}).get("queryHost", "unknown")
    elapsed = summary_data.get("result", {}).get("elapsedMillisTime", "unknown")
    summary_list = summary_data.get("result", {}).get("data", [])

    samples_list = samples_data.get("result", {}).get("data", []) if samples_data.get("result") else []

    os.makedirs(REPORT_DIR, exist_ok=True)

    now = datetime.now()
    date_label = now.strftime("%Y-%m-%d")
    timezone = now.strftime("%Z")
    timestamp = now.strftime("%Y-%m-%d_%H-%M")
    time_part = timestamp.split('_', 1)[1]

    total_errors, total_hours, total_requests, overall_ratio, sorted_types = analyze_data(summary_list)

    table_rows = build_md_table(summary_list)
    summary_rows = build_summary_table(sorted_types)
    samples_section = build_samples_section(samples_list, sorted_types)

    focus_types = [(name, code) for (name, code), stats in sorted_types
                   if stats["count"] / sum(s[1]["count"] for s in sorted_types) * 100 >= 1]

    report_content = f"""# CK Query Log 异常查询统计报告

> **生成时间：** {date_label} {time_part} ({timezone})  
> **查询范围：** 近24小时  
> **数据来源：** `system.query_log_distributed_cluster_atomic`  
> **请求Host：** {query_host}  
> **查询耗时：** {elapsed}ms  
> **请求ID：** {request_id}

## 一、汇总统计

| 指标 | 值 |
|------|-----|
| 总错误数 | {total_errors} |
| 有错误的时段数 | {total_hours} |
| 总查询数 | {total_requests} |
| 错误率 | {overall_ratio*100:.2f}% |

### 按错误类型统计

| 错误类型 | 错误码 | 涉及时段 | 错误数 | 占比 | 状态 |
|----------|--------|----------|--------|------|------|
{summary_rows}

## 二、每小时错误明细

| 时间段 | 错误类型 | 错误码 | 错误数 | 总查询数 | 错误率 |
|--------|----------|--------|--------|----------|--------|
{table_rows}

## 三、SQL 样例（Top3 每类型）

{samples_section}

## 四、报告说明

- 查询条件：`query_kind='Select'`, `initial_user='one'`, `is_initial_query=1`, `exception_code<>0`
- 数据表：`system.query_log_distributed_cluster_atomic`
- 错误率 = 错误数 / 该小时总查询数
"""

    report_file = os.path.join(REPORT_DIR, f"{date_label}_ck_query_error_report.md")
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report_content)

    print(f"\n报告已生成: {report_file}")

    os.chdir(REPO_DIR)
    subprocess.run(['git', 'config', '--local', 'user.email', 'openclaw@bonree.com'], check=False)
    subprocess.run(['git', 'config', '--local', 'user.name', 'OpenClaw Agent'], check=False)

    result = subprocess.run(['git', 'diff', '--quiet', report_file], capture_output=True)
    if result.returncode == 0:
        print("报告无变化，无需提交")
    else:
        subprocess.run(['git', 'add', report_file], check=True)
        commit_msg = f"CK query error report {date_label} {time_part}"
        subprocess.run(['git', 'commit', '-m', commit_msg], check=True)
        push_result = subprocess.run(['git', 'push', 'origin', 'HEAD'], capture_output=True, text=True)
        if push_result.returncode == 0:
            print("Git 提交并推送成功")
        else:
            print(f"Git push 失败: {push_result.stderr}")

    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 任务完成")


if __name__ == '__main__':
    main()