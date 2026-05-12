#!/usr/bin/env python3
"""Gitee Forge 任务统计 - 多维度分析 + 智能总结"""

import argparse
import json
import urllib.request
import urllib.parse
from datetime import datetime
import sys
import re
from collections import Counter

API_URL = "https://gitee.ibr.net.cn/forge/api/search"
HEADERS = {
    "X-Parse-Application-Id": "Bonree",
    "Content-Type": "application/json",
}

FIELDS = ["Cascade1","EMT5TLTN","Text01","ancestors","assignee","createdAt",
    "createdBy","earlyWarning","field019","id","itemType","key",
    "rowId","status","workspace","field002","content","name"]

# 标题关键词映射
TITLE_KEYWORDS = {
    "bug/问题": ["bug", "问题", "修复", "错误", "异常", "故障", "缺陷"],
    "需求/功能": ["需求", "功能", "新增", "开发", "实现", "优化", "改进"],
    "性能/效率": ["性能", "效率", "慢", "卡顿", "优化", "提速", "吞吐量"],
    "测试/验证": ["测试", "验证", "验证", "回归", "用例"],
    "文档/整理": ["文档", "说明", "整理", "规范", "注释"],
    "监控/告警": ["监控", "告警", "报警", "阈值", "告警"],
    "数据/迁移": ["数据", "迁移", "同步", "导入", "导出"],
    "安全/权限": ["安全", "权限", "鉴权", "认证", "加密"],
}

# 描述关键词映射（识别问题类型）
DESC_KEYWORDS = {
    "数据库相关": ["sql", "数据库", "mysql", "oracle", "pg", "redis", "查询", "索引"],
    "API/接口": ["api", "接口", "http", "rpc", "调用", "请求"],
    "前端相关": ["前端", "ui", "页面", "组件", "vue", "react", "h5"],
    "后端服务": ["服务", "spring", "java", "node", "go", "微服务"],
    "配置/部署": ["部署", "配置", "环境", "docker", "k8s", "kubernetes"],
    "日志/排查": ["日志", "排查", "定位", "堆栈", "trace"],
}


def query_forge(start_date, end_date, token, max_items=1000):
    """查询 Forge API"""
    iql = f"'实际完成时间' >= '{start_date}' and '实际完成时间' <= '{end_date}' and '负责人' in [\"membersOf(数据底座能力部)\"]"
    
    all_items = []
    page_size = 200
    offset = 0
    
    while offset < max_items:
        data = {
            "iql": iql + " order by 创建时间 desc",
            "size": page_size,
            "from": offset,
            "execFieldBehaviors": True,
            "fields": FIELDS
        }
        
        req = urllib.request.Request(
            API_URL,
            data=json.dumps(data).encode(),
            headers={**HEADERS, "X-Parse-Session-Token": token},
            method="POST"
        )
        
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read().decode())
        
        items = result.get("payload", {}).get("items", [])
        if not items:
            break
            
        all_items.extend(items)
        offset += page_size
        
        if len(items) < page_size:
            break
            
        print(f"已获取 {len(all_items)} 条...", file=sys.stderr)
    
    return all_items


def get_hours(item):
    """获取工时 - 从 values.field019 中获取"""
    return float(item.get("values", {}).get("field019", 0) or 0)


def extract_title_keywords(name):
    """从标题提取关键词"""
    name_lower = name.lower() if name else ""
    matched = []
    for category, keywords in TITLE_KEYWORDS.items():
        for kw in keywords:
            if kw in name_lower:
                matched.append(category)
                break
    return matched if matched else ["其他"]


def extract_desc_keywords(desc):
    """从描述提取关键词"""
    if not desc:
        return ["其他"]
    desc_lower = desc.lower()
    matched = []
    for category, keywords in DESC_KEYWORDS.items():
        for kw in keywords:
            if kw in desc_lower:
                matched.append(category)
                break
    return matched if matched else ["其他"]


def analyze(items):
    """多维度分析"""
    total_count = len(items)
    total_hours = sum(get_hours(item) for item in items)
    
    # 1. 按任务类型统计
    type_stats = {}
    for item in items:
        item_type = item.get("itemType", {}).get("name", "未知")
        hours = get_hours(item)
        if item_type not in type_stats:
            type_stats[item_type] = {"count": 0, "hours": 0.0, "keys": []}
        type_stats[item_type]["count"] += 1
        type_stats[item_type]["hours"] += hours
        type_stats[item_type]["keys"].append(item.get("key", ""))
    
    # 2. 按标题关键词统计
    title_stats = {}
    for item in items:
        name = item.get("name", "")
        hours = get_hours(item)
        for cat in extract_title_keywords(name):
            if cat not in title_stats:
                title_stats[cat] = {"count": 0, "hours": 0.0}
            title_stats[cat]["count"] += 1
            title_stats[cat]["hours"] += hours
    
    # 3. 按描述关键词统计
    desc_stats = {}
    for item in items:
        desc = item.get("field002", "") or ""
        hours = get_hours(item)
        for cat in extract_desc_keywords(desc):
            if cat not in desc_stats:
                desc_stats[cat] = {"count": 0, "hours": 0.0}
            desc_stats[cat]["count"] += 1
            desc_stats[cat]["hours"] += hours
    
    # 4. 按人员统计
    person_stats = {}
    for item in items:
        creator = item.get("createdBy", {}).get("nickname", item.get("createdBy", {}).get("username", "未知"))
        hours = get_hours(item)
        item_type = item.get("itemType", {}).get("name", "未知")
        
        if creator not in person_stats:
            person_stats[creator] = {"count": 0, "hours": 0.0, "types": [], "keys": []}
        person_stats[creator]["count"] += 1
        person_stats[creator]["hours"] += hours
        person_stats[creator]["types"].append(item_type)
        person_stats[creator]["keys"].append(item.get("key", ""))
    
    return {
        "total": {"count": total_count, "hours": total_hours},
        "type": type_stats,
        "title": title_stats,
        "desc": desc_stats,
        "person": person_stats
    }


def generate_summary(analysis):
    """生成智能总结"""
    total = analysis["total"]
    type_stats = analysis["type"]
    title_stats = analysis["title"]
    desc_stats = analysis["desc"]
    person_stats = analysis["person"]
    
    lines = []
    lines.append("## 📊 智能分析总结\n")
    
    # 整体情况
    lines.append("### 1. 整体概况")
    lines.append(f"- 总任务数: **{total['count']}** 个")
    lines.append(f"- 总登记工时: **{total['hours']:.1f}** 小时")
    lines.append(f"- 人均任务数: **{total['count'] / len(person_stats):.1f}** 个" if person_stats else "")
    lines.append(f"- 人均工时: **{total['hours'] / len(person_stats):.1f}** 小时" if person_stats and total['hours'] > 0 else "")
    lines.append("")
    
    # 任务类型分析
    lines.append("### 2. 任务类型分析")
    sorted_types = sorted(type_stats.items(), key=lambda x: -x[1]["count"])
    for t, d in sorted_types[:5]:
        pct = d["count"] / total["count"] * 100
        hour_pct = d["hours"] / total["hours"] * 100 if total["hours"] > 0 else 0
        lines.append(f"- {t}: {d['count']}个 ({pct:.1f}%), 工时{d['hours']:.1f}h ({hour_pct:.1f}%)")
    lines.append("")
    
    # 优化重点
    lines.append("### 3. 后续优化重点")
    
    # 问题类任务占比
    bug_count = sum(d["count"] for t, d in type_stats.items() if "bug" in t.lower() or "缺陷" in t)
    if bug_count / total["count"] > 0.3:
        lines.append(f"- ⚠️ Bug修复类任务占比较高 ({bug_count/total['count']*100:.1f}%)，建议加强测试覆盖")
    
    # 性能相关
    perf_count = title_stats.get("性能/效率", {}).get("count", 0)
    if perf_count > 5:
        lines.append(f"- 📈 性能优化类任务 {perf_count} 个，建议评估优化效果")
    
    # 文档类
    doc_count = title_stats.get("文档/整理", {}).get("count", 0)
    if doc_count / total["count"] < 0.05:
        lines.append(f"- 📝 文档类任务偏少 ({doc_count}个)，建议加强文档沉淀")
    
    # 潜在问题
    lines.append("\n### 4. 潜在问题")
    
    # 工时为0的任务
    zero_hour_tasks = sum(1 for p in person_stats.values() if p["hours"] == 0)
    if zero_hour_tasks > 0:
        lines.append(f"- ⚠️ 有 {zero_hour_tasks} 位成员工时为0")
    
    # 任务分布不均
    if person_stats:
        counts = [p["count"] for p in person_stats.values()]
        hours = [p["hours"] for p in person_stats.values()]
        if counts and max(counts) > sum(counts) / len(counts) * 3:
            lines.append(f"- ⚠️ **任务分布不均**: 最高 {max(counts)} 个，最低 {min(counts)} 个")
    
    # 事务性任务占比
    trans_count = sum(d["count"] for t, d in type_stats.items() if "事务" in t)
    if trans_count / total["count"] > 0.4:
        lines.append(f"- ⚠️ 事务性任务占比 {trans_count/total['count']*100:.1f}%，建议评估能否自动化")
    
    lines.append("")
    
    return "\n".join(lines)


def generate_report(analysis, start_date, end_date, items):
    """生成完整报告"""
    total = analysis["total"]
    type_stats = analysis["type"]
    title_stats = analysis["title"]
    desc_stats = analysis["desc"]
    person_stats = analysis["person"]
    
    report = []
    report.append(f"# 📊 Gitee Forge 任务统计报告")
    report.append(f"**统计周期**: {start_date} ~ {end_date}")
    report.append(f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report.append("")
    
    # 智能总结
    report.append(generate_summary(analysis))
    report.append("")
    
    # 按任务类型统计
    report.append("## 📋 按任务类型统计")
    report.append("| 类型 | 数量 | 数量占比 | 工时 | 工时占比 |")
    report.append("|------|------|----------|------|----------|")
    for t, d in sorted(type_stats.items(), key=lambda x: -x[1]["count"]):
        pct = d["count"] / total["count"] * 100 if total["count"] else 0
        hour_pct = d["hours"] / total["hours"] * 100 if total["hours"] > 0 else 0
        report.append(f"| {t} | {d['count']} | {pct:.1f}% | {d['hours']:.1f}h | {hour_pct:.1f}% |")
    report.append("")
    
    # 按标题关键词统计
    report.append("## 🏷️ 按标题关键词统计")
    report.append("| 关键词分类 | 数量 | 数量占比 | 工时 |")
    report.append("|------------|------|----------|------|")
    for t, d in sorted(title_stats.items(), key=lambda x: -x[1]["count"]):
        pct = d["count"] / total["count"] * 100 if total["count"] else 0
        report.append(f"| {t} | {d['count']} | {pct:.1f}% | {d['hours']:.1f}h |")
    report.append("")
    
    # 按描述关键词统计
    report.append("## 📝 按描述内容统计")
    report.append("| 描述分类 | 数量 | 数量占比 | 工时 |")
    report.append("|----------|------|----------|------|")
    for t, d in sorted(desc_stats.items(), key=lambda x: -x[1]["count"]):
        pct = d["count"] / total["count"] * 100 if total["count"] else 0
        report.append(f"| {t} | {d['count']} | {pct:.1f}% | {d['hours']:.1f}h |")
    report.append("")
    
    # 按人员统计
    report.append("## 👥 按人员统计")
    report.append("| 人员 | 任务数 | 数量占比 | 工时 | 工时占比 | 主要类型 |")
    report.append("|------|--------|----------|------|----------|----------|")
    for p, d in sorted(person_stats.items(), key=lambda x: -x[1]["hours"]):
        pct = d["count"] / total["count"] * 100 if total["count"] else 0
        hour_pct = d["hours"] / total["hours"] * 100 if total["hours"] > 0 else 0
        type_counter = Counter(d["types"])
        main_types = ", ".join([t for t, _ in type_counter.most_common(2)])
        report.append(f"| {p} | {d['count']} | {pct:.1f}% | {d['hours']:.1f}h | {hour_pct:.1f}% | {main_types[:20]} |")
    report.append("")
    
    # 人员明细表格
    report.append("## 📃 人员明细数据")
    report.append("| 人员 | 任务数 | 工时(h) | 开发任务 | 事务性任务 | 测试任务 | 调研任务 | 任务序列 |")
    report.append("|------|--------|---------|----------|------------|----------|----------|----------|")
    for p, d in sorted(person_stats.items(), key=lambda x: -x[1]["hours"]):
        types_count = Counter(d["types"])
        dev = types_count.get("开发任务", 0)
        trans = types_count.get("事务性任务", 0)
        test = types_count.get("测试任务", 0)
        research = types_count.get("调研任务", 0)
        keys_str = ", ".join(d["keys"][:5]) + ("..." if len(d["keys"]) > 5 else "")
        report.append(f"| {p} | {d['count']} | {d['hours']:.1f} | {dev} | {trans} | {test} | {research} | {keys_str} |")
    report.append("")
    
    # 原始明细数据表格
    report.append("## 📋 原始任务明细")
    report.append("| 任务序列 | 标题 | 任务类型 | 负责人 | 工时(h) | 任务空间 |")
    report.append("|----------|------|----------|--------|---------|----------|")
    for item in sorted(items, key=lambda x: -get_hours(x)):
        key = item.get("key", "")
        name = (item.get("name", "") or "")[:50]
        item_type = item.get("itemType", {}).get("name", "")
        creator = item.get("createdBy", {}).get("nickname", item.get("createdBy", {}).get("username", ""))
        hours = get_hours(item)
        workspace = item.get("workspace", {}).get("name", "")
        report.append(f"| {key} | {name} | {item_type} | {creator} | {hours} | {workspace} |")
    report.append("")
    
    return "\n".join(report)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--start", required=True)
    parser.add_argument("--end", required=True)
    parser.add_argument("--token", required=True)
    parser.add_argument("--output", default="")
    args = parser.parse_args()
    
    print(f"查询 {args.start} ~ {args.end} 任务...", file=sys.stderr)
    items = query_forge(args.start, args.end, args.token)
    print(f"共获取 {len(items)} 条任务", file=sys.stderr)
    
    # 分析
    analysis = analyze(items)
    
    # 生成报告
    report = generate_report(analysis, args.start, args.end, items)
    
    # 输出
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(report)
        print(f"报告已保存到: {args.output}", file=sys.stderr)
    else:
        print(report)


if __name__ == "__main__":
    main()