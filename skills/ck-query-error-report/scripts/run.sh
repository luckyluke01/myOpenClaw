#!/bin/bash
# CK Query Log Error Report - 自动查询 + 报告生成 + Git提交
# 依赖: curl, python3, git

set -e

REPORT_DIR="/mnt/f/one-space/titanmonitor/CKquery"
REPO_DIR="/mnt/f/one-space/titanmonitor"
COOKIE="__bid_n=18a458a319898889c254bc; sensorsdata2015jssdkcross=%7B%22distinct_id%22%3A%2218a458a314fb4f-0d84f39197ea168-26031c51-2073600-18a458a315056d%22%2C%22first_id%22%3A%22%22%2C%22props%22%3A%7B%22%24latest_traffic_source_type%22%3A%22%E7%9B%B4%E6%8E%A5%E6%B5%81%E9%87%8F%22%2C%22%24latest_search_keyword%22%3A%22%E6%9C%AA%E5%8F%96%E5%88%B0%E5%80%BC_%E7%9B%B4%E6%8E%A5%E6%89%93%E5%BC%80%22%2C%22%24latest_referrer%22%3A%22%22%7D%2C%22identities%22%3A%22eyIkaWRlbnRpdHlfY29va2llX2lkIjoiMThhNDU4YTMxNGZiNGYtMGQ4NGYzOTE5N2VhMTY4LTI2MDMxYzUxLTIwNzM2MDAtMThhNDU4YTMxNTA1NmQifQ%3D%3D%22%2C%22history_login_id%22%3A%7B%22name%22%3A%22%22%2C%22value%22%3A%22%22%7D%2C%22%24device_id%22%3A%2218a458a314fb4f-0d84f39197ea168-26031c51-2073600-18a458a315056d%22%7D; signbonree=0; Hm_lvt_da1dc33910d60fbb5d553a130d2b5c42=1773224725,1775741517; usernamebonree=citicbank; truenamebonree=kzx123"
API_URL="https://macs.bonree.com/OneData/clickhouse/sql/query"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

SQL_SUMMARY='SELECT
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
    AND query_kind = '\''Select'\''
    AND initial_user = '\''one'\''
    AND is_initial_query = 1
  GROUP BY th, exception_code
) AS subquery
WHERE exception_code <> 0
ORDER BY th DESC, exception_code;'

SQL_SAMPLES='SELECT
  exception_code,
  errorCodeToName(exception_code) AS exception_name,
  query,
  user,
  event_time
FROM system.query_log_distributed_cluster_atomic
WHERE event_time >= now() - INTERVAL 1 DAY
  AND query_kind = '\''Select'\''
  AND initial_user = '\''one'\''
  AND is_initial_query = 1
  AND exception_code <> 0
ORDER BY event_time DESC
LIMIT 200'

DATE_LABEL=$(date +%Y-%m-%d)
TIMEZONE=$(date +%Z)
TIMESTAMP=$(date +%Y-%m-%d_%H-%M)

do_query() {
  local sql="$1"
  local attempt=0
  local max_attempts=10
  local http_code=""

  while [ $attempt -lt $max_attempts ]; do
    attempt=$((attempt + 1))
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] 请求尝试 #$attempt" >&2

    full_response=$(curl -s -w "\n___HTTP_CODE:%{http_code}" -X POST "$API_URL" \
      -H "Cookie: $COOKIE" \
      -H "Content-Type: application/json" \
      -d "$(python3 -c "import json,sys; print(json.dumps({'sql': '''$sql''', 'nodeId': '', 'pageSize': 100, 'pageNum': 1}))")")

    http_code=$(echo "$full_response" | grep -o "___HTTP_CODE:[0-9]*" | cut -d: -f2)
    body=$(echo "$full_response" | sed '/___HTTP_CODE:/d')

    if [ "$http_code" = "200" ]; then
      echo "[$(date '+%Y-%m-%d %H:%M:%S')] 请求成功 (HTTP 200)" >&2
      echo "$body"
      return 0
    else
      echo "[$(date '+%Y-%m-%d %H:%M:%S')] 请求失败 (HTTP $http_code)，3秒后重试..." >&2
      if [ $attempt -eq $max_attempts ]; then
        echo "已达最大重试次数 ($max_attempts)，退出" >&2
        exit 1
      fi
      sleep 3
    fi
  done
}

# 查询汇总数据
echo "=== 查询汇总数据 ==="
summary_body=$(do_query "$SQL_SUMMARY")

# 查询详细样例数据
echo "=== 查询详细样例数据 ==="
samples_body=$(do_query "$SQL_SAMPLES")

# 调用 Python 解析并生成报告
python3 "$SCRIPT_DIR/generate_report.py" "$summary_body" "$samples_body" "$DATE_LABEL" "$TIMEZONE" "$TIMESTAMP" "$http_code" "$attempt" "$REPORT_DIR"

# Git 提交
cd "$REPO_DIR"
git config --local user.email "openclaw@bonree.com" 2>/dev/null || true
git config --local user.name "OpenClaw Agent" 2>/dev/null || true

report_file="$REPORT_DIR/${DATE_LABEL}_ck_query_error_report.md"
if git diff --quiet "$report_file" 2>/dev/null; then
  echo "报告无变化，无需提交"
else
  git add "$report_file"
  git commit -m "CK query error report ${DATE_LABEL} ${TIMESTAMP#*_}"
  git push origin HEAD 2>/dev/null || echo "Git push 失败，请检查网络或仓库权限"
fi

echo "[$(date '+%Y-%m-%d %H:%M:%S')] 任务完成"
echo "报告路径：$report_file"
