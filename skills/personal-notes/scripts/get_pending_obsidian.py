#!/usr/bin/env python3
"""
Extract pending issues from Obsidian and send reminder via Feishu.
Usage: python get_pending_obsidian.py
"""

import subprocess
import sys
import re

# 获取Obsidian待办事项
OBSIDIAN_SCRIPT = "/mnt/f/.openclaw/workspace/skills/personal-notes/scripts/get_pending.sh"

try:
    # 执行shell脚本获取待办
    result = subprocess.run(
        OBSIDIAN_SCRIPT,
        capture_output=True,
        text=True,
        timeout=10
    )

    if result.returncode != 0:
        print(f"Error: {result.stderr}", file=sys.stderr)
        sys.exit(1)

    pending_content = result.stdout.strip()

    # 解析待办事项数量
    count_match = re.search(r'待办事项清单 \((\d+) 项\)', pending_content)
    pending_count = int(count_match.group(1)) if count_match else 0

    if pending_count == 0:
        message = "✅ 当前没有待办事项需要处理"
    else:
        # 提取所有待办行（以 -  开头的行）
        todo_lines = []
        for line in pending_content.split('\n'):
            if line.strip().startswith('-  '):
                todo_lines.append(line.strip())

        # 生成消息
        message = f"⏰ 每日提醒：您有 {pending_count} 个待办事项未处理\n\n"
        message += "📋 待办清单：\n\n"

        for i, item in enumerate(todo_lines[:10], 1):  # 最多显示10项
            # 清理行内容：去掉 "-  " 前缀
            clean_item = item[3:].strip()
            if clean_item:
                message += f"{i}. {clean_item}\n"

        if pending_count > 10:
            message += f"\n... 还有 {pending_count - 10} 项待办未显示"

        if todo_lines:
            # 获取前两项作为建议
            first_two = [line[3:].strip() for line in todo_lines[:2]]
            first_two = [item for item in first_two if item]

            if first_two:
                message += f"\n\n建议优先处理：{', '.join(first_two)}"

    # 输出消息内容
    print(message)

except subprocess.TimeoutExpired:
    print("Error: Script execution timed out", file=sys.stderr)
    sys.exit(1)
except Exception as e:
    print(f"Error: {str(e)}", file=sys.stderr)
    sys.exit(1)
