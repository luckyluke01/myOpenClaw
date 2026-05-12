#!/usr/bin/env python3
"""
Gitee Forge Search API 任务拉取与人效分析
按实际完成时间分页查询，提取指定字段整理为表格，并统计人力投入占比。
"""

import argparse
import json
import os
import re
from datetime import datetime
from pathlib import Path

try:
    import requests
except ImportError:
    print("请先安装: pip install requests")
    exit(1)

try:
    import pandas as pd
except ImportError:
    print("请先安装: pip install pandas openpyxl")
    exit(1)

API_URL = "https://gitee.ibr.net.cn/forge/api/search"
HEADERS = {
    "X-Parse-Application-Id": "Bonree",
    "Content-Type": "application/json",
}
# 需要从请求中获取的字段（name 可能在根或 attributes 中）
REQUEST_FIELDS = [
    "Cascade1", "EMT5TLTN", "Text01", "ancestors", "assignee", "createdAt",
    "createdBy", "earlyWarning", "field019", "id", "itemType", "key",
    "rowId", "status", "workspace", "field002", "content", "name"
]
# 列顺序：key/标题(name) 优先展示，便于快速识别任务
FIELD_MAP = {
    "key": "任务序列号",
    "name": "标题",
    "itemType": "任务类型",
    "createdBy": "创建人",
    "field019": "已登记工时",
    "workspace": "任务所属空间",
    "field002": "描述",
    "content": "描述内容",
    "Text01": "标题内容",
}


def _normalize_desc(val):
    """整理描述/描述内容：从接口响应提取可读纯文本，去除 HTML/富文本结构。"""
    if val is None or val == "":
        return ""
    text = ""
    if isinstance(val, dict):
        text = val.get("text") or val.get("plainText") or val.get("value", "")
        if not text and isinstance(val.get("content"), list):
            parts = []
            for node in val.get("content", []):
                if isinstance(node, dict):
                    if "text" in node:
                        parts.append(str(node["text"]))
                    elif "content" in node:
                        for c in node.get("content", []):
                            if isinstance(c, dict) and "text" in c:
                                parts.append(str(c["text"]))
            text = "".join(parts)
        if not text:
            text = json.dumps(val, ensure_ascii=False)
    else:
        text = str(val)
    # 去除 HTML 标签
    text = re.sub(r"<[^>]+>", " ", text)
    for k, v in [("&nbsp;", " "), ("&lt;", "<"), ("&gt;", ">"), ("&amp;", "&"), ("&quot;", '"')]:
        text = text.replace(k, v)
    return re.sub(r"\s+", " ", text).strip()


def _get_attr(obj, key, default=""):
    """从对象中取值，支持 Gitee Forge 嵌套：values.field019, createdBy.nickname 等。"""
    if obj is None:
        return default
    val = obj.get(key)
    if val is None and key in ("field019", "field002", "content", "Text01"):
        vals = obj.get("values", {})
        val = vals.get(key) if isinstance(vals, dict) else None
    if val is not None and val != "":
        if isinstance(val, dict) and key not in ("content", "field002", "Text01"):
            return val.get("nickname") or val.get("label") or val.get("name") or val.get("value", default)
        if key in ("content", "field002", "Text01"):
            return _normalize_desc(val)
        return str(val).strip() if isinstance(val, str) else val
    # workspace / itemType 等对象取 name
    if key in ("workspace", "itemType") and val is None:
        sub = obj.get(key)
        if isinstance(sub, dict):
            return sub.get("name", default)
    # createdBy 为对象时取 nickname
    if key == "createdBy" and isinstance(val, dict):
        return val.get("nickname") or val.get("label", default)
    attrs = obj.get("attributes", {})
    if isinstance(attrs, dict):
        return attrs.get(key, default)
    return default


def _curl_cmd(url, headers, payload):
    """生成等价 curl 命令。"""
    body = json.dumps(payload, ensure_ascii=False)
    # 转义单引号供 shell 使用: ' -> '\''
    body_escaped = body.replace("'", "'\\''") if "'" in body else body
    lines = [f"curl -X POST '{url}' \\"]
    for k, v in headers.items():
        lines.append(f"  -H '{k}: {v}' \\")
    lines.append(f"  -d '{body_escaped}'")
    return "\n".join(lines)


def fetch_page(session, session_token, start_date, end_date, from_offset, size=200, debug=False):
    iql = (
        f"('实际完成时间' >= '{start_date}' and '实际完成时间' <= '{end_date}' "
        "and '负责人' in [\"membersOf(数据底座能力部)\"]) order by 创建时间 desc"
    )
    payload = {
        "iql": iql,
        "size": size,
        "from": from_offset,
        "execFieldBehaviors": True,
        "fields": REQUEST_FIELDS,
    }
    headers = {**HEADERS, "X-Parse-Session-Token": session_token}

    if debug:
        print("\n" + "=" * 60 + "\n[curl 等价命令]\n" + "=" * 60)
        print(_curl_cmd(API_URL, headers, payload))
        print("=" * 60 + "\n")

    resp = session.post(API_URL, headers=headers, json=payload, timeout=60)
    resp.raise_for_status()
    data = resp.json()

    if debug:
        print("[响应] status:", resp.status_code)
        print("[响应] 顶层 keys:", list(data.keys()) if isinstance(data, dict) else type(data))
        if isinstance(data, dict):
            for k, v in data.items():
                if k in ("results", "hits"):
                    arr = v if k == "results" else (v.get("hits", []) if isinstance(v, dict) else [])
                    print(f"[响应] {k}: 数量={len(arr) if isinstance(arr, list) else 'N/A'}")
                    if arr and isinstance(arr, list) and len(arr) > 0:
                        print(f"[响应] 首条 keys: {list(arr[0].keys()) if isinstance(arr[0], dict) else type(arr[0])}")
                else:
                    print(f"[响应] {k}: {str(v)[:200]}")
        print()

    return data


def fetch_all(session_token, start_date, end_date, size=200, debug=False):
    """分页拉取全部结果。"""
    session = requests.Session()
    all_results = []
    from_offset = 0
    page_num = 0
    last_raw = None
    while True:
        page_num += 1
        if debug:
            print(f"\n>>> 第 {page_num} 页 (from={from_offset})")
        data = fetch_page(session, session_token, start_date, end_date, from_offset, size, debug=debug)
        last_raw = data
        # Gitee Forge API: { code: 0, payload: { count, items } }
        payload = data.get("payload") or {}
        results = payload.get("items") or data.get("results")
        if results is None:
            hits = data.get("hits")
            results = hits.get("hits", []) if isinstance(hits, dict) else []
        if results is None:
            results = data.get("data") or data.get("items") or []
        if not results:
            if debug and last_raw:
                dump_path = Path(__file__).parent / "gitee_debug_response.json"
                with open(dump_path, "w", encoding="utf-8") as f:
                    json.dump(last_raw, f, ensure_ascii=False, indent=2)
                print(f"[调试] 原始响应已保存到: {dump_path}")
            break
        if isinstance(results[0], dict) and "_source" in results[0]:
            results = [r.get("_source", r) for r in results]
        all_results.extend(results)
        if len(results) < size:
            break
        from_offset += size
    return all_results


def extract_row(item):
    row = {}
    for api_key, cn_name in FIELD_MAP.items():
        val = _get_attr(item, api_key)
        if isinstance(val, (dict, list)):
            val = json.dumps(val, ensure_ascii=False) if val else ""
        row[cn_name] = val if val is not None else ""
    return row


def build_table(results):
    rows = [extract_row(r) for r in results]
    return pd.DataFrame(rows)


def parse_hours(h):
    """解析已登记工时字段为数值。"""
    if h is None or h == "":
        return 0.0
    if isinstance(h, (int, float)):
        return float(h)
    s = str(h).strip()
    m = re.search(r"[\d.]+", s)
    return float(m.group(0)) if m else 0.0


def analyze_labor(table):
    """基于任务类型、标题、描述统计人力投入占比。"""
    report = []
    total_count = len(table)
    if total_count == 0:
        return report

    table = table.copy()
    table["_hours"] = table["已登记工时"].apply(parse_hours)
    total_hours = table["_hours"].sum() or 1.0

    # 1. 按任务类型
    by_type = table.groupby("任务类型", dropna=False).agg(
        count=("任务序列号", "count"),
        hours=("_hours", "sum"),
    ).reset_index()
    by_type["占比(数量)"] = (by_type["count"] / total_count * 100).round(1).astype(str) + "%"
    by_type["占比(工时)"] = (by_type["hours"] / total_hours * 100).round(1).astype(str) + "%"
    report.append(("按任务类型", by_type))

    # 2. 按标题关键词（标题 name + 标题内容）
    keywords = ["需求", "bug", "Bug", "优化", "文档", "重构", "开发", "测试", "联调"]
    title_col = table.get("标题", pd.Series([""] * len(table)))
    title_content_col = table.get("标题内容", pd.Series([""] * len(table)))
    table["_title_text"] = title_col.fillna("").astype(str) + " " + title_content_col.fillna("").astype(str)

    def classify_title(text):
        t = str(text or "")
        for kw in keywords:
            if kw in t:
                return kw
        return "其他"
    table["_kw"] = table["_title_text"].apply(classify_title)
    by_kw = table.groupby("_kw", dropna=False).agg(
        count=("任务序列号", "count"),
        hours=("_hours", "sum"),
    ).reset_index().rename(columns={"_kw": "关键词"})
    by_kw["占比(数量)"] = (by_kw["count"] / total_count * 100).round(1).astype(str) + "%"
    by_kw["占比(工时)"] = (by_kw["hours"] / total_hours * 100).round(1).astype(str) + "%"
    report.append(("按标题关键词", by_kw))

    # 3. 按描述内容关键词（描述 + 描述内容合并分析）
    desc_cols = ["描述", "描述内容"]
    table["_desc_text"] = ""
    for c in desc_cols:
        if c in table.columns:
            table["_desc_text"] = table["_desc_text"] + " " + table[c].fillna("").astype(str)
    def classify_desc(text):
        t = str(text or "")
        for kw in keywords:
            if kw in t:
                return kw
        return "其他"
    table["_desc_kw"] = table["_desc_text"].apply(classify_desc)
    by_desc = table.groupby("_desc_kw", dropna=False).agg(
        count=("任务序列号", "count"),
        hours=("_hours", "sum"),
    ).reset_index().rename(columns={"_desc_kw": "描述关键词"})
    by_desc["占比(数量)"] = (by_desc["count"] / total_count * 100).round(1).astype(str) + "%"
    by_desc["占比(工时)"] = (by_desc["hours"] / total_hours * 100).round(1).astype(str) + "%"
    report.append(("按描述内容关键词", by_desc))

    # 4. 按人员
    by_person = table.groupby("创建人", dropna=False).agg(
        count=("任务序列号", "count"),
        hours=("_hours", "sum"),
    ).reset_index().sort_values("hours", ascending=False)
    by_person["占比(数量)"] = (by_person["count"] / total_count * 100).round(1).astype(str) + "%"
    by_person["占比(工时)"] = (by_person["hours"] / total_hours * 100).round(1).astype(str) + "%"
    report.append(("按人员", by_person))

    return report


def generate_insights(table, total_hours):
    """生成智能分析文案。"""
    lines = []
    table = table.copy()
    table["_hours"] = table["已登记工时"].apply(parse_hours)

    # 按类型洞察
    by_type = table.groupby("任务类型", dropna=False)["_hours"].sum().sort_values(ascending=False)
    top_type = by_type.index[0] if len(by_type) > 0 else ""
    top_type_pct = (by_type.iloc[0] / total_hours * 100) if len(by_type) > 0 else 0
    lines.append(f"- **任务类型分布**：{top_type} 占比最高（约 {top_type_pct:.0f}% 工时），为本周主要投入方向。")

    # 按人员洞察
    by_person = table.groupby("创建人", dropna=False)["_hours"].sum().sort_values(ascending=False)
    if len(by_person) >= 2:
        top2 = list(by_person.index[:2])
        lines.append(f"- **人力集中度**：{top2[0]}、{top2[1]} 等前几位成员贡献了较大比例工时。")

    # 空间分布
    by_ws = table.groupby("任务所属空间", dropna=False)["任务序列号"].count()
    if len(by_ws) > 1:
        lines.append(f"- **空间覆盖**：任务分布在 {len(by_ws)} 个空间，可关注跨空间协同情况。")

    # 描述内容覆盖
    has_content = "描述内容" in table.columns and table["描述内容"].notna().any()
    has_desc = "描述" in table.columns and table["描述"].fillna("").str.strip().str.len().gt(0).any()
    if has_content or has_desc:
        fill_rate = (table.get("描述内容", pd.Series([""] * len(table))).fillna("").str.len().gt(0) | 
                     table.get("描述", pd.Series([""] * len(table))).fillna("").str.strip().str.len().gt(0)).sum()
        lines.append(f"- **描述完整性**：{fill_rate}/{len(table)} 条任务含描述或描述内容，可结合描述内容做更细粒度分析。")

    lines.append("- **建议**：可根据任务类型、人员分布及描述内容，评估资源倾斜与排期合理性。")

    return "\n".join(lines)


def _last_week_range():
    """上周一至周日。"""
    from datetime import timedelta
    today = datetime.now().date()
    last_sun = today - timedelta(days=today.weekday() + 1)
    last_mon = last_sun - timedelta(days=6)
    return last_mon.strftime("%Y-%m-%d"), last_sun.strftime("%Y-%m-%d")


def main():
    parser = argparse.ArgumentParser(description="Gitee Forge 任务拉取与人效分析")
    parser.add_argument("--start", default=None, help="实际完成时间起始 YYYY-MM-DD")
    parser.add_argument("--end", default=None, help="实际完成时间结束 YYYY-MM-DD")
    parser.add_argument("--last-week", action="store_true", help="使用上周一至周日")
    parser.add_argument("--token", default=os.environ.get("GITEE_SESSION_TOKEN"), help="Session Token")
    parser.add_argument("-o", "--output-dir", default=None, help="输出目录（已废弃，用 --obsidian-dir）")
    parser.add_argument("--obsidian-dir", default=None, help="Obsidian 输出目录，如 F:\\obsidion\\lukeguo\\05-日记\\每周任务追踪")
    parser.add_argument("--debug", "-v", action="store_true", help="调试模式：输出 curl 命令及响应结构")
    args = parser.parse_args()

    if args.last_week:
        args.start, args.end = _last_week_range()
    if not args.start or not args.end:
        print("请指定 --start/--end 或使用 --last-week")
        exit(1)

    token = args.token
    if not token:
        print("请设置环境变量 GITEE_SESSION_TOKEN 或使用 --token 传入 Session Token")
        exit(1)

    obsidian_dir = Path(args.obsidian_dir) if args.obsidian_dir else None

    print("正在分页拉取数据...")
    results = fetch_all(token, args.start, args.end, debug=args.debug)
    print(f"共获取 {len(results)} 条记录")

    if not results:
        if args.debug:
            print("[调试] 未解析到结果，完整响应已在上方输出")
        print("无数据，退出")
        return

    df = build_table(results)
    total_hours = df["已登记工时"].apply(parse_hours).sum() or 1.0

    def df_to_md(t):
        h = "| " + " | ".join(str(c) for c in t.columns) + " |"
        sep = "| " + " | ".join("---" for _ in t.columns) + " |"
        rows = ["| " + " | ".join(str(v) for v in r) + " |" for r in t.values]
        return "\n".join([h, sep] + rows)

    # 构建报告：先统计分析，再明细
    report = []
    report.append(f"# 每周任务追踪 · {args.start} ~ {args.end}\n")
    report.append(f"> 数据来源：Gitee Forge · 数据底座能力部 · 共 {len(df)} 条 / 总工时 {total_hours:.0f}h\n")
    report.append("---\n")

    report.append("## 一、智能分析\n")
    report.append("### 1.1 统计汇总\n")
    for name, tbl in analyze_labor(df):
        report.append(f"**{name}**\n\n{df_to_md(tbl)}\n\n")
    report.append("### 1.2 洞察与建议\n")
    report.append(generate_insights(df, total_hours))
    report.append("\n\n---\n")

    report.append("## 二、明细信息\n")
    report.append(df_to_md(df))
    report.append("\n")

    content = "\n".join(report)

    if obsidian_dir:
        obsidian_dir.mkdir(parents=True, exist_ok=True)
        filename = f"每周任务追踪_{args.start}_{args.end}.md"
        out_path = obsidian_dir / filename
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"报告已保存至 Obsidian: {out_path}")
    else:
        out_dir = Path(args.output_dir or Path(__file__).parent)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        excel_path = out_dir / f"gitee_tasks_{ts}.xlsx"
        df.to_excel(excel_path, index=False, engine="openpyxl")
        md_path = out_dir / f"gitee_analysis_{ts}.md"
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"明细表: {excel_path}")
        print(f"分析报告: {md_path}")

    for name, tbl in analyze_labor(df):
        print(f"\n--- {name} ---\n{tbl.to_string(index=False)}")


if __name__ == "__main__":
    main()
